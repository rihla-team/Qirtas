from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QKeySequence

class ShortcutManager:
    def __init__(self, editor):
        self.editor = editor
        
    def setup_all_shortcuts(self):
        """إعداد جميع اختصارات لوحة المفاتيح"""
        self.setup_file_shortcuts()
        self.setup_edit_shortcuts()
        self.setup_format_shortcuts()
        self.setup_tools_shortcuts()
        
    def setup_file_shortcuts(self):
        """إعداد اختصارات الملفات"""
        pass

    def setup_edit_shortcuts(self):
        """إعداد اختصارات التحرير"""
        undo_action = QAction(self.editor)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(lambda: self.editor.tab_manager.get_current_editor().undo() 
                                    if self.editor.tab_manager.get_current_editor() else None)
        self.editor.addAction(undo_action)

        redo_action = QAction(self.editor)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(lambda: self.editor.tab_manager.get_current_editor().redo() 
                                    if self.editor.tab_manager.get_current_editor() else None)
        self.editor.addAction(redo_action)

        cut_action = QAction(self.editor)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(lambda: self.editor.get_current_editor().cut() if self.editor.get_current_editor() else None)
        self.editor.addAction(cut_action)

        copy_action = QAction(self.editor)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(lambda: self.editor.get_current_editor().copy() if self.editor.get_current_editor() else None)
        self.editor.addAction(copy_action)

        paste_action = QAction(self.editor)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(lambda: self.editor.get_current_editor().paste() if self.editor.get_current_editor() else None)
        self.editor.addAction(paste_action)

        select_all_action = QAction(self.editor)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(lambda: self.editor.get_current_editor().selectAll() if self.editor.get_current_editor() else None)
        self.editor.addAction(select_all_action)

    def setup_format_shortcuts(self):
        """إعداد اختصارات التنسيق"""
        pass

    def setup_tools_shortcuts(self):
        """إعداد اختصارات الأدوات"""
        search_action = QAction(self.editor)
        search_action.setShortcut(QKeySequence.Find)
        search_action.triggered.connect(self.editor.show_search_dialog)
        self.editor.addAction(search_action)

        replace_action = QAction(self.editor)
        replace_action.setShortcut(QKeySequence("Ctrl+H"))
        replace_action.triggered.connect(self.editor.show_replace_dialog)
        self.editor.addAction(replace_action)

        goto_action = QAction(self.editor)
        goto_action.setShortcut(QKeySequence("Ctrl+G"))
        goto_action.triggered.connect(self.editor.goto_line)
        self.editor.addAction(goto_action)