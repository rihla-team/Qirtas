from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QKeySequence

class ShortcutManager:
    def __init__(self, editor):
        self.editor = editor
        self.extension_shortcuts = {}
        self.registered_shortcuts = set()
        
    def setup_all_shortcuts(self):
        """إعداد جميع اختصارات لوحة المفاتيح"""
        self.setup_file_shortcuts()
        self.setup_edit_shortcuts()
        self.setup_format_shortcuts()
        self.setup_tools_shortcuts()
        self.setup_extension_shortcuts()
        

    def setup_file_shortcuts(self):
        """إعداد اختصارات الملفات"""
        def add_action_with_check(action, shortcut):
            shortcut_str = QKeySequence(shortcut).toString()
            if shortcut_str not in self.registered_shortcuts:
                action.setShortcut(QKeySequence(shortcut))
                self.editor.addAction(action)
                self.registered_shortcuts.add(shortcut_str)

        restore_tab_action = QAction(self.editor)
        restore_tab_action.triggered.connect(
            lambda: self.editor.tab_manager.restore_last_closed_tab()
        )
        add_action_with_check(restore_tab_action, "Ctrl+Shift+T")

    def setup_edit_shortcuts(self):
        """إعداد اختصارات التحرير"""
        def add_action_with_check(action, shortcut):
            shortcut_str = QKeySequence(shortcut).toString()
            if shortcut_str not in self.registered_shortcuts:
                action.setShortcut(QKeySequence(shortcut))
                self.editor.addAction(action)
                self.registered_shortcuts.add(shortcut_str)

        undo_action = QAction(self.editor)
        undo_action.triggered.connect(lambda: self.editor.tab_manager.get_current_editor().undo() 
                                    if self.editor.tab_manager.get_current_editor() else None)
        add_action_with_check(undo_action, QKeySequence.Undo)

        redo_action = QAction(self.editor)
        redo_action.triggered.connect(lambda: self.editor.tab_manager.get_current_editor().redo() 
                                    if self.editor.tab_manager.get_current_editor() else None)
        add_action_with_check(redo_action, QKeySequence.Redo)

        cut_action = QAction(self.editor)
        cut_action.triggered.connect(lambda: self.editor.get_current_editor().cut() if self.editor.get_current_editor() else None)
        add_action_with_check(cut_action, QKeySequence.Cut)

        copy_action = QAction(self.editor)
        copy_action.triggered.connect(lambda: self.editor.get_current_editor().copy() if self.editor.get_current_editor() else None)
        add_action_with_check(copy_action, QKeySequence.Copy)

        paste_action = QAction(self.editor)
        paste_action.triggered.connect(lambda: self.editor.get_current_editor().paste() if self.editor.get_current_editor() else None)
        add_action_with_check(paste_action, QKeySequence.Paste)

        select_all_action = QAction(self.editor)
        select_all_action.triggered.connect(lambda: self.editor.get_current_editor().selectAll() if self.editor.get_current_editor() else None)
        add_action_with_check(select_all_action, QKeySequence.SelectAll)

    def setup_format_shortcuts(self):
        """إعداد اختصارات التنسيق"""
        pass

    def setup_tools_shortcuts(self):
        """إعداد اختصارات الأدوات"""
        def add_action_with_check(action, shortcut):
            shortcut_str = QKeySequence(shortcut).toString()
            if shortcut_str not in self.registered_shortcuts:
                action.setShortcut(QKeySequence(shortcut))
                self.editor.addAction(action)
                self.registered_shortcuts.add(shortcut_str)

        search_action = QAction(self.editor)
        search_action.triggered.connect(self.editor.show_search_dialog)
        add_action_with_check(search_action, QKeySequence.Find)

        replace_action = QAction(self.editor)
        replace_action.triggered.connect(self.editor.show_replace_dialog)
        add_action_with_check(replace_action, "Ctrl+H")

        goto_action = QAction(self.editor)
        goto_action.triggered.connect(self.editor.goto_line)
        add_action_with_check(goto_action, "Ctrl+G")

    def setup_extension_shortcuts(self):
        """إعداد اختصارات الملحقات"""
        self.clear_extension_shortcuts()
        
        if hasattr(self.editor, 'extensions_manager'):
            for ext_id, extension in self.editor.extensions_manager.active_extensions.items():
                if hasattr(extension, 'get_shortcuts'):
                    try:
                        shortcuts = extension.get_shortcuts()
                        for shortcut_data in shortcuts:
                            shortcut = shortcut_data['shortcut']
                            callback = shortcut_data['callback']
                            
                            shortcut_str = QKeySequence(shortcut).toString()
                            if shortcut_str in self.registered_shortcuts:
                                continue
                            
                            action = QAction(self.editor)
                            action.setShortcut(QKeySequence(shortcut))
                            action.setObjectName(f"extension_{ext_id}_{shortcut}")
                            action.triggered.connect(callback)
                            self.editor.addAction(action)
                            
                            if ext_id not in self.extension_shortcuts:
                                self.extension_shortcuts[ext_id] = []
                            self.extension_shortcuts[ext_id].append(action)
                            self.registered_shortcuts.add(shortcut_str)
                            
                    except Exception as e:
                        print(f"خطأ في إعداد اختصارات الملحق {ext_id}: {str(e)}")
    def clear_extension_shortcuts(self):
        """إزالة جميع اختصارات الملحقات"""
        for ext_id, actions in self.extension_shortcuts.items():
            for action in actions:
                self.editor.removeAction(action)
                shortcut = action.shortcut().toString()
                if shortcut in self.registered_shortcuts:
                    self.registered_shortcuts.remove(shortcut)
        self.extension_shortcuts.clear()



