import wx
import wx.stc as stc
import wx.aui as aui
import os
import keyword
import builtins
import jedi

class PythonSTC(stc.StyledTextCtrl):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist + dir(builtins)))
        self.file_path = None
        self.setup_styles()
        self.setup_margins()
        self.setup_auto_comp()

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

class PythonEditor(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='Python Editor')
        self.SetSize(1200, 800)
        self.aui_manager = aui.AuiManager()
        self.aui_manager.SetManagedWindow(self)
        self.create_ui()
        self.bind_events()
        self.aui_manager.Update()

    def create_ui(self):
        self.create_menu()
        self.create_toolbar()
        self.create_notebook()
        self.create_file_tree()

    def create_menu(self):
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
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
        menubar.Append(file_menu, '文件')
        self.SetMenuBar(menubar)

    def create_toolbar(self):
        toolbar = self.CreateToolBar()
        tools = [
            (wx.ID_NEW, '新建', wx.ART_NEW),
            (wx.ID_OPEN, '打开', wx.ART_FILE_OPEN),
            (wx.ID_SAVE, '保存', wx.ART_FILE_SAVE),
        ]
        for id, label, art in tools:
            toolbar.AddTool(id, label, wx.ArtProvider.GetBitmap(art, wx.ART_TOOLBAR))
        toolbar.Realize()

    def create_notebook(self):
        self.notebook = aui.AuiNotebook(self)
        self.aui_manager.AddPane(self.notebook, aui.AuiPaneInfo().CenterPane().Name("notebook_content"))

    def create_file_tree(self):
        self.file_tree = wx.TreeCtrl(self, style=wx.TR_DEFAULT_STYLE)
        self.aui_manager.AddPane(self.file_tree, aui.AuiPaneInfo().Left().Layer(1).BestSize((200, -1)).Caption("文件树"))
        self.populate_file_tree()

    def populate_file_tree(self):
        self.file_tree.DeleteAllItems()
        root = self.file_tree.AddRoot("项目")
        self.add_directory_to_tree(os.getcwd(), root)

    def add_directory_to_tree(self, path, parent):
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    child = self.file_tree.AppendItem(parent, item)
                    self.add_directory_to_tree(item_path, child)
                elif item.endswith('.py'):
                    self.file_tree.AppendItem(parent, item)
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

if __name__ == '__main__':
    app = wx.App()
    frame = PythonEditor()
    frame.Show()
    app.MainLoop()
