import wx
import wx.stc as stc
import wx.aui as aui
import os
import keyword
import builtins
import jedi
import wx.lib.agw.customtreectrl as ctc

class PythonSTC(stc.StyledTextCtrl):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist + dir(builtins)))
        self.file_path = None
        self.setup_styles()
        self.setup_margins()
        self.setup_auto_comp()
        self.setup_folding()  # 新增折叠功能
        self.setup_indentation()  # 新增自动缩进

    def setup_styles(self):
        styles = [
            (stc.STC_STYLE_DEFAULT, "face:Courier New,size:10"),
            (stc.STC_P_DEFAULT, "fore:#000000"),
            (stc.STC_P_COMMENTLINE, "fore:#008000,italic"),
            (stc.STC_P_NUMBER, "fore:#008080"),
            (stc.STC_P_STRING, "fore:#800080"),
            (stc.STC_P_CHARACTER, "fore:#800080"),
            (stc.STC_P_WORD, "fore:#000080,bold"),
            (stc.STC_P_TRIPLE, "fore:#800080"),
            (stc.STC_P_TRIPLEDOUBLE, "fore:#800080"),
            (stc.STC_P_CLASSNAME, "fore:#0000FF,bold"),
            (stc.STC_P_DEFNAME, "fore:#008080,bold"),
            (stc.STC_P_OPERATOR, "bold"),
            (stc.STC_P_IDENTIFIER, ""),
            (stc.STC_P_COMMENTBLOCK, "fore:#008000,italic"),
            (stc.STC_P_STRINGEOL, "fore:#000000,back:#E0C0E0,eolfilled"),
        ]
        self.StyleClearAll()
        for style, spec in styles:
            self.StyleSetSpec(style, spec)

    def setup_margins(self):
        self.SetMarginType(0, stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(0, 30)

    def setup_auto_comp(self):
        self.AutoCompSetIgnoreCase(True)
        self.AutoCompSetAutoHide(False)
        self.AutoCompSetDropRestOfWord(True)
        self.Bind(wx.EVT_CHAR, self.on_char)

    def on_char(self, event):
        key = event.GetKeyCode()
        if key in [ord('.'), ord('(')] or chr(key).isalnum():
            wx.CallAfter(self.show_auto_comp)
        event.Skip()

    def show_auto_comp(self):
        current_line = self.GetCurrentLine()
        current_pos = self.GetCurrentPos()
        line_pos = current_pos - self.PositionFromLine(current_line)
        
        script = jedi.Script(self.GetText(), path=self.file_path)
        completions = script.complete(current_line + 1, line_pos)
        
        if completions:
            auto_comp_list = [f"{c.name}?{c.type}" for c in completions]
            self.AutoCompShow(0, " ".join(auto_comp_list))

    def set_file_path(self, path):
        self.file_path = path

    def setup_folding(self):
        # 设置折叠标记
        self.SetProperty("fold", "1")
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        # 设置折叠标记样式
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_BOXMINUS)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_BOXPLUS)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARK_VLINE)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL, stc.STC_MARK_LCORNER)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND, stc.STC_MARK_BOXPLUSCONNECTED)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED)
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER)

        # 绑定折叠事件
        self.Bind(stc.EVT_STC_MARGINCLICK, self.on_margin_click)

    def setup_indentation(self):
        self.SetIndent(4)
        self.SetTabWidth(4)
        self.SetUseTabs(False)
        self.SetTabIndents(True)
        self.SetBackSpaceUnIndents(True)
        self.SetIndentationGuides(stc.STC_IV_LOOKBOTH)

    def on_margin_click(self, event):
        if event.GetMargin() == 2:
            line_clicked = self.LineFromPosition(event.GetPosition())
            if self.GetFoldLevel(line_clicked) & stc.STC_FOLDLEVELHEADERFLAG:
                self.ToggleFold(line_clicked)

class PythonEditor(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='Python Editor')
        self.SetSize(1200, 800)
        self.aui_manager = aui.AuiManager()
        self.aui_manager.SetManagedWindow(self)
        self.init_file_tree_icons()
        self.create_ui()
        self.bind_events()
        self.aui_manager.Update()
        self.find_data = wx.FindReplaceData()

    def init_file_tree_icons(self):
        # 创建图像列表
        il = wx.ImageList(16, 16)
        self.folder_idx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16)))
        self.folder_open_idx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_OTHER, (16, 16)))
        self.file_idx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16)))
        self.file_tree_il = il

    def create_ui(self):
        self.create_menu()
        self.create_toolbar()
        self.create_notebook()
        self.create_file_tree()

    def create_menu(self):
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        edit_menu = wx.Menu()
        menu_items = [
            (wx.ID_NEW, '新建', self.on_new),
            (wx.ID_OPEN, '打开', self.on_open),
            (wx.ID_SAVE, '保存', self.on_save),
            (wx.ID_SAVEAS, '另存为', self.on_save_as),
            (None, None, None),
            (wx.ID_EXIT, '退出', self.on_exit),
        ]
        for id, label, handler in menu_items:
            if id is None:
                file_menu.AppendSeparator()
            else:
                item = file_menu.Append(id, label)
                self.Bind(wx.EVT_MENU, handler, item)
        
        # 添加编辑菜单项
        edit_items = [
            (wx.ID_FIND, '查找', self.on_find),
            (wx.ID_REPLACE, '替换', self.on_replace),
        ]
        for id, label, handler in edit_items:
            item = edit_menu.Append(id, label)
            self.Bind(wx.EVT_MENU, handler, item)

        menubar.Append(file_menu, '文件')
        menubar.Append(edit_menu, '编辑')
        
        self.SetMenuBar(menubar)

    def create_toolbar(self):
        toolbar = self.CreateToolBar()
        toolbar.SetToolBitmapSize((24, 24))  # 将图标大小从 16x16 增加到 24x24

        tools = [
            (wx.ID_NEW, '新建', wx.ART_NEW, '创建新文件'),
            (wx.ID_OPEN, '打开', wx.ART_FILE_OPEN, '打开文件'),
            (wx.ID_SAVE, '保存', wx.ART_FILE_SAVE, '保存当前文件'),
            (wx.ID_SAVEAS, '另存为', wx.ART_FILE_SAVE_AS, '另存为新文件'),
            (None, None, None, None),  # 分隔符
            (wx.ID_CUT, '剪切', wx.ART_CUT, '剪切选中内容'),
            (wx.ID_COPY, '复制', wx.ART_COPY, '复制选中内容'),
            (wx.ID_PASTE, '粘贴', wx.ART_PASTE, '粘贴内容'),
            (None, None, None, None),  # 分隔符
            (wx.ID_UNDO, '撤销', wx.ART_UNDO, '撤销上一步操作'),
            (wx.ID_REDO, '重做', wx.ART_REDO, '重做上一步操作'),
            (None, None, None, None),  # 分隔符
            (wx.ID_FIND, '查找', wx.ART_FIND, '查找文本'),
            (wx.ID_REPLACE, '替换', wx.ART_FIND_AND_REPLACE, '查找并替换文本'),
        ]

        for id, label, art, tooltip in tools:
            if id is None:
                toolbar.AddSeparator()
            else:
                tool = toolbar.AddTool(id, label, wx.ArtProvider.GetBitmap(art, wx.ART_TOOLBAR, (24, 24)))
                tool.SetShortHelp(tooltip)  # 设置鼠标悬停时的提示信息
                self.Bind(wx.EVT_TOOL, self.on_tool, id=id)

        toolbar.Realize()

    def on_tool(self, event):
        id = event.GetId()
        if id == wx.ID_NEW:
            self.on_new(event)
        elif id == wx.ID_OPEN:
            self.on_open(event)
        elif id == wx.ID_SAVE:
            self.on_save(event)
        elif id == wx.ID_SAVEAS:
            self.on_save_as(event)
        elif id == wx.ID_CUT:
            self.on_cut(event)
        elif id == wx.ID_COPY:
            self.on_copy(event)
        elif id == wx.ID_PASTE:
            self.on_paste(event)
        elif id == wx.ID_UNDO:
            self.on_undo(event)
        elif id == wx.ID_REDO:
            self.on_redo(event)
        elif id == wx.ID_FIND:
            self.on_find(event)
        elif id == wx.ID_REPLACE:
            self.on_replace(event)
        else:
            wx.MessageBox(f"功能 '{event.GetEventObject().GetToolShortHelp(id)}' 尚未实现", 
                          "提示", wx.OK | wx.ICON_INFORMATION)

    def create_notebook(self):
        self.notebook = aui.AuiNotebook(self)
        self.aui_manager.AddPane(self.notebook, aui.AuiPaneInfo().CenterPane().Name("notebook_content"))

    def create_file_tree(self):
        self.file_tree = ctc.CustomTreeCtrl(self, style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.TR_MULTIPLE)
        self.file_tree.SetImageList(self.file_tree_il)
        self.aui_manager.AddPane(self.file_tree, aui.AuiPaneInfo().Left().Layer(1).BestSize((200, -1)).Caption("文件树"))
        self.populate_file_tree()

    def populate_file_tree(self):
        self.file_tree.DeleteAllItems()
        root = self.file_tree.AddRoot("项目")
        self.add_directory_to_tree(os.getcwd(), root)
        self.file_tree.Expand(root)

    def add_directory_to_tree(self, path, parent):
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    child = self.file_tree.AppendItem(parent, item, image=self.folder_idx)
                    self.file_tree.SetItemImage(child, self.folder_open_idx, wx.TreeItemIcon_Expanded)
                    self.add_directory_to_tree(item_path, child)
                elif item.endswith('.py'):
                    self.file_tree.AppendItem(parent, item, image=self.file_idx)
        except PermissionError:
            pass

    def bind_events(self):
        self.file_tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_file_activated)

    def on_new(self, event):
        editor = PythonSTC(self.notebook)
        self.notebook.AddPage(editor, "Untitled", select=True)

    def on_open(self, event):
        dlg = wx.FileDialog(self, "打开文件", wildcard="Python files (*.py)|*.py", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.open_file(dlg.GetPath())
        dlg.Destroy()

    def open_file(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        editor = PythonSTC(self.notebook)
        editor.SetText(content)
        editor.set_file_path(path)
        self.notebook.AddPage(editor, os.path.basename(path), select=True)

    def on_save(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor.file_path:
            self.save_file(editor, editor.file_path)
        else:
            self.on_save_as(event)

    def on_save_as(self, event):
        editor = self.notebook.GetCurrentPage()
        dlg = wx.FileDialog(self, "保存文件", wildcard="Python files (*.py)|*.py", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            self.save_file(editor, dlg.GetPath())
        dlg.Destroy()

    def save_file(self, editor, path):
        with open(path, 'w', encoding='utf-8') as file:
            file.write(editor.GetText())
        editor.set_file_path(path)
        self.notebook.SetPageText(self.notebook.GetSelection(), os.path.basename(path))

    def on_exit(self, event):
        self.Close()

    def on_file_activated(self, event):
        item = event.GetItem()
        path = self.get_item_path(item)
        if os.path.isfile(path):
            self.open_file(path)

    def get_item_path(self, item):
        path = self.file_tree.GetItemText(item)
        parent = self.file_tree.GetItemParent(item)
        while parent != self.file_tree.GetRootItem():
            path = os.path.join(self.file_tree.GetItemText(parent), path)
            parent = self.file_tree.GetItemParent(parent)
        return os.path.join(os.getcwd(), path)

    def on_find(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor:
            dlg = wx.FindReplaceDialog(self, self.find_data, "查找")
            dlg.Bind(wx.EVT_FIND, self.on_find_next)
            dlg.Bind(wx.EVT_FIND_NEXT, self.on_find_next)
            dlg.Show()

    def on_replace(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor:
            dlg = wx.FindReplaceDialog(self, self.find_data, "替换", wx.FR_REPLACEDIALOG)
            dlg.Bind(wx.EVT_FIND, self.on_find_next)
            dlg.Bind(wx.EVT_FIND_NEXT, self.on_find_next)
            dlg.Bind(wx.EVT_FIND_REPLACE, self.on_replace_text)
            dlg.Bind(wx.EVT_FIND_REPLACE_ALL, self.on_replace_all)
            dlg.Show()

    def on_find_next(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor:
            find_string = self.find_data.GetFindString()
            start = editor.GetSelectionEnd()
            pos = editor.FindText(start, editor.GetTextLength(), find_string, event.GetFlags())
            if pos != -1:
                # 检查 pos 是否为元组
                if isinstance(pos, tuple):
                    start, end = pos
                else:
                    start, end = pos, pos + len(find_string)
                editor.SetSelection(start, end)
            else:
                wx.MessageBox(f"找不到 '{find_string}'", "查找结果", wx.OK | wx.ICON_INFORMATION)

    def on_replace_text(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor:
            find_string = self.find_data.GetFindString()
            replace_string = self.find_data.GetReplaceString()
            selection = editor.GetSelectedText()
            if selection == find_string:
                editor.ReplaceSelection(replace_string)
                self.on_find_next(event)
            else:
                self.on_find_next(event)

    def on_replace_all(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor:
            find_string = self.find_data.GetFindString()
            replace_string = self.find_data.GetReplaceString()
            text = editor.GetText()
            new_text = text.replace(find_string, replace_string)
            editor.SetText(new_text)

    def on_cut(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor:
            editor.Cut()

    def on_copy(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor:
            editor.Copy()

    def on_paste(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor:
            editor.Paste()

    def on_undo(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor:
            editor.Undo()

    def on_redo(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor:
            editor.Redo()

if __name__ == '__main__':
    app = wx.App()
    frame = PythonEditor()
    frame.Show()
    app.MainLoop()
