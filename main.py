import wx
import wx.stc as stc
import wx.aui as aui
import os
import keyword
import builtins
import jedi
import wx.lib.agw.customtreectrl as ctc
import subprocess
import wx.lib.newevent

AutoSaveEvent, EVT_AUTOSAVE = wx.lib.newevent.NewEvent()

class PythonSTC(stc.StyledTextCtrl):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist + dir(builtins)))
        self.file_path = None
        self.setup_styles()
        self.set_theme("light")  # Default to light theme
        self.setup_margins()
        self.setup_auto_comp()
        self.setup_folding()  # 新增折叠功能
        self.setup_indentation()  # 新增自动缩进
        self.Bind(stc.EVT_STC_CHANGE, self.on_text_changed)
        self.is_modified = False

    def setup_styles(self):
        # This method will now be used to set up base styles
        pass

    def set_theme(self, theme):
        self.theme = theme
        if theme == "light":
            self.set_light_theme()
        else:
            self.set_dark_theme()

    def set_light_theme(self):
        styles = [
            (stc.STC_STYLE_DEFAULT, "face:Courier New,size:10,fore:#000000,back:#FFFFFF"),
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
        self.SetCaretForeground("#000000")
        self.SetSelBackground(True, "#C0C0C0")
        
        # 添加行号栏和缩进指南的颜色设置
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "fore:#2B91AF,back:#FFFFFF")
        self.SetIndentationGuides(stc.STC_IV_LOOKBOTH)
        self.StyleSetForeground(stc.STC_STYLE_INDENTGUIDE, "#D3D3D3")

    def set_dark_theme(self):
        styles = [
            (stc.STC_STYLE_DEFAULT, "face:Consolas,size:10,fore:#D4D4D4,back:#1E1E1E"),
            (stc.STC_P_DEFAULT, "fore:#D4D4D4"),
            (stc.STC_P_COMMENTLINE, "fore:#6A9955,italic"),
            (stc.STC_P_NUMBER, "fore:#B5CEA8"),
            (stc.STC_P_STRING, "fore:#CE9178"),
            (stc.STC_P_CHARACTER, "fore:#CE9178"),
            (stc.STC_P_WORD, "fore:#569CD6,bold"),
            (stc.STC_P_TRIPLE, "fore:#CE9178"),
            (stc.STC_P_TRIPLEDOUBLE, "fore:#CE9178"),
            (stc.STC_P_CLASSNAME, "fore:#4EC9B0,bold"),
            (stc.STC_P_DEFNAME, "fore:#DCDCAA,bold"),
            (stc.STC_P_OPERATOR, "fore:#D4D4D4"),
            (stc.STC_P_IDENTIFIER, "fore:#9CDCFE"),
            (stc.STC_P_COMMENTBLOCK, "fore:#6A9955,italic"),
            (stc.STC_P_STRINGEOL, "fore:#CE9178,back:#3F3F3F,eolfilled"),
        ]
        self.StyleClearAll()
        for style, spec in styles:
            self.StyleSetSpec(style, spec)
        
        # 设置默认背景色
        self.SetBackgroundColour(wx.Colour(30, 30, 30))  # 深灰色背景
        
        self.SetCaretForeground("#D4D4D4")
        self.SetSelBackground(True, "#264F78")
        self.SetSelForeground(True, "#D4D4D4")
        
        # 设置行号栏的颜色
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "fore:#858585,back:#1E1E1E")
        
        # 设置缩进指南的颜色
        self.SetIndentationGuides(stc.STC_IV_LOOKBOTH)
        self.StyleSetForeground(stc.STC_STYLE_INDENTGUIDE, "#3F3F3F")

        # 设置折叠标记的颜色
        for marker in [stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARKNUM_FOLDER,
                       stc.STC_MARKNUM_FOLDERSUB, stc.STC_MARKNUM_FOLDERTAIL,
                       stc.STC_MARKNUM_FOLDEREND, stc.STC_MARKNUM_FOLDEROPENMID,
                       stc.STC_MARKNUM_FOLDERMIDTAIL]:
            self.MarkerSetForeground(marker, "#D4D4D4")
            self.MarkerSetBackground(marker, "#3F3F3F")

        # 设置空白字符的颜色
        self.SetWhitespaceForeground(True, "#3F3F3F")
        self.SetWhitespaceBackground(True, "#1E1E1E")

        # 禁用边缘线
        self.SetEdgeColour(wx.Colour(30, 30, 30))
        self.SetEdgeMode(stc.STC_EDGE_NONE)

        # 确保没有额外的样式导致白色出现
        self.StyleSetBackground(stc.STC_STYLE_DEFAULT, "#1E1E1E")
        for style in range(32):  # Scintilla 使用 32 种基本样式
            self.StyleSetBackground(style, "#1E1E1E")

        # 刷新显示
        self.Refresh()

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
            auto_comp_list = [f"{c.name}?{c.type}\t{c.docstring().split('.')[0]}" for c in completions]
            self.AutoCompShow(0, "\n".join(auto_comp_list))
            self.AutoCompSetTypeSeparator(63)  # ASCII for '?'
            self.AutoCompSetSeparator(10)  # ASCII for '\n'

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

    def on_text_changed(self, event):
        if not self.is_modified:
            self.is_modified = True
            wx.CallAfter(self.update_title)

    def update_title(self):
        index = self.GetParent().GetPageIndex(self)
        if index != -1:
            title = self.GetParent().GetPageText(index)
            if not title.endswith('*'):
                self.GetParent().SetPageText(index, title + '*')

class PythonEditor(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='Python Editor')
        self.SetSize(1200, 800)
        self.aui_manager = aui.AuiManager()
        self.aui_manager.SetManagedWindow(self)
        self.init_file_tree_icons()
        self.show_line_numbers = True
        self.create_ui()
        self.bind_events()
        self.aui_manager.Update()
        self.find_data = wx.FindReplaceData()
        self.auto_save_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_auto_save_timer, self.auto_save_timer)
        self.auto_save_timer.Start(300000)  # 每5分钟自动保存一次
        self.Bind(EVT_AUTOSAVE, self.on_auto_save)
        self.current_theme = "light"

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
        run_menu = wx.Menu()  # 新增运行菜单
        view_menu = wx.Menu()
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

        # 添加运行菜单项
        run_items = [
            (wx.ID_ANY, '运行当前文件', self.on_run_file),  # 使用 wx.ID_ANY 替代 wx.NewId()
        ]
        for id, label, handler in run_items:
            item = run_menu.Append(id, label)
            self.Bind(wx.EVT_MENU, handler, item)

        self.line_numbers_item = view_menu.AppendCheckItem(wx.ID_ANY, "显示行号")
        self.line_numbers_item.Check(self.show_line_numbers)
        self.Bind(wx.EVT_MENU, self.on_toggle_line_numbers, self.line_numbers_item)

        # Add theme toggle item
        self.theme_item = view_menu.AppendCheckItem(wx.ID_ANY, "深色主题")
        self.Bind(wx.EVT_MENU, self.on_toggle_theme, self.theme_item)

        menubar.Append(file_menu, '文件')
        menubar.Append(edit_menu, '编辑')
        menubar.Append(run_menu, '运行')  # 添加运行菜单
        menubar.Append(view_menu, "视图")
        
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
            (None, None, None, None),  # 分隔符
            (wx.ID_ANY, '运行', 'run.png', '运行当前文件'),  # 使用自定义图标
        ]

        self.run_tool_id = None
        for id, label, art, tooltip in tools:
            if id is None:
                toolbar.AddSeparator()
            else:
                if isinstance(art, str) and art.endswith('.png'):
                    # 加载自定义图标
                    bitmap = wx.Bitmap(art, wx.BITMAP_TYPE_PNG)
                else:
                    bitmap = wx.ArtProvider.GetBitmap(art, wx.ART_TOOLBAR, (24, 24))
                
                if bitmap.IsOk():
                    tool = toolbar.AddTool(id, label, bitmap, tooltip)
                else:
                    # 如果获取不到合适的图标，使用一个默认的文本按钮
                    tool = toolbar.AddTool(id, label, wx.NullBitmap, tooltip)
                if label == '运行':
                    self.run_tool_id = tool.GetId()
                self.Bind(wx.EVT_TOOL, self.on_tool, id=tool.GetId())

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
        elif id == self.run_tool_id:
            self.on_run_file(event)
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
        if not self.show_line_numbers:
            editor.SetMarginWidth(0, 0)
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
        editor.is_modified = False
        index = self.notebook.GetPageIndex(editor)
        title = self.notebook.GetPageText(index)
        if title.endswith('*'):
            self.notebook.SetPageText(index, title[:-1])

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

    def on_run_file(self, event):
        editor = self.notebook.GetCurrentPage()
        if editor and editor.file_path:
            self.run_python_file(editor.file_path)
        else:
            wx.MessageBox("请先保存文件", "错误", wx.OK | wx.ICON_ERROR)

    def run_python_file(self, file_path):
        try:
            result = subprocess.run(['python', file_path], capture_output=True, text=True)
            output = result.stdout + result.stderr
            
            # 创建输出窗口
            output_window = wx.Frame(self, title="运行结果")
            output_text = wx.TextCtrl(output_window, style=wx.TE_MULTILINE | wx.TE_READONLY)
            output_text.SetValue(output)
            output_window.Show()
        except Exception as e:
            wx.MessageBox(f"运行错误: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def on_toggle_line_numbers(self, event):
        self.show_line_numbers = not self.show_line_numbers
        for i in range(self.notebook.GetPageCount()):
            editor = self.notebook.GetPage(i)
            if self.show_line_numbers:
                editor.SetMarginWidth(0, 30)
            else:
                editor.SetMarginWidth(0, 0)

    def on_toggle_theme(self, event):
        is_dark = self.theme_item.IsChecked()
        theme = "dark" if is_dark else "light"
        self.current_theme = theme
        for i in range(self.notebook.GetPageCount()):
            editor = self.notebook.GetPage(i)
            editor.set_theme(theme)
        # 更新文件树的颜色
        self.update_file_tree_colors()

    def update_file_tree_colors(self):
        if self.current_theme == "dark":
            self.file_tree.SetBackgroundColour("#1E1E1E")
            self.file_tree.SetForegroundColour("#D4D4D4")
        else:
            self.file_tree.SetBackgroundColour(wx.NullColour)
            self.file_tree.SetForegroundColour(wx.NullColour)
        self.file_tree.Refresh()

    def on_auto_save_timer(self, event):
        wx.PostEvent(self, AutoSaveEvent())

    def on_auto_save(self, event):
        for i in range(self.notebook.GetPageCount()):
            editor = self.notebook.GetPage(i)
            if editor.file_path:
                self.save_file(editor, editor.file_path)
        print("自动保存完成")

if __name__ == '__main__':
    app = wx.App()
    frame = PythonEditor()
    frame.Show()
    app.MainLoop()
