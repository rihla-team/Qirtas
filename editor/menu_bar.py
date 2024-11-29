from PyQt5.QtWidgets import QMenuBar,QAction, QFontDialog, QMessageBox
from PyQt5.QtGui import QKeySequence 
from editor.terminal_widget import ArabicTerminal
class ArabicMenuBar(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_menus()
        
    def setup_menus(self):
        # قائمة ملف
        file_menu = self.addMenu('ملف')
        
        open_action = QAction('فتح', self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.parent.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('حفظ', self)
        save_action.triggered.connect(self.parent.save_file)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        file_menu.addAction(save_action)
        
        save_as_action = QAction('حفظ باسم', self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.parent.save_file_as)
        file_menu.addAction(save_as_action)
        
        new_action = QAction('نافذة جديدة', self)
        new_action.setShortcut(QKeySequence("Ctrl+T"))
        new_action.triggered.connect(self.parent.new_file)
        file_menu.addAction(new_action)
        
        # إضافة فاصل
        file_menu.addSeparator()
        
        # إضافة قائمة الإعدادات
        settings_menu = self.addMenu('إعدادات')
        
        # إضافة خيار الحفظ التلقائي
        auto_save_action = QAction('الحفظ التلقائي', self)
        auto_save_action.setCheckable(True)
        auto_save_action.triggered.connect(self.toggle_auto_save)
        settings_menu.addAction(auto_save_action)
        
        # تحديث حالة الحفظ التلقائي من الإعدادات
        if hasattr(self.parent, 'settings_manager'):
            enabled = self.parent.settings_manager.get_setting('editor.auto_save.enabled', False)
            auto_save_action.setChecked(enabled)
            
        terminal_action = QAction('فتح موجه الاوامر', self)
        terminal_action.setShortcuts([QKeySequence("Ctrl+ذ"), QKeySequence("Ctrl+`")])
        terminal_action.triggered.connect(self.parent.add_terminal)
        settings_menu.addAction(terminal_action)       
        # قائمة تحرير
        edit_menu = self.addMenu('تحرير')
        
        undo_action = QAction('تراجع', self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(lambda: self.parent.tab_manager.get_current_editor().undo() 
                                    if self.parent.tab_manager.get_current_editor() else None)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction('إعادة', self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(lambda: self.parent.tab_manager.get_current_editor().redo() 
                                    if self.parent.tab_manager.get_current_editor() else None)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction('قص', self)
        cut_action.setShortcut(QKeySequence("Ctrl+X"))
        cut_action.triggered.connect(lambda: self.parent.get_current_editor().cut() if self.parent.get_current_editor() else None)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction('نسخ', self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_action.triggered.connect(lambda: self.parent.get_current_editor().copy() if self.parent.get_current_editor() else None)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction('لصق', self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(lambda: self.parent.get_current_editor().paste() if self.parent.get_current_editor() else None)
        edit_menu.addAction(paste_action)
        
        select_all_action = QAction('تحديد الكل', self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(lambda: self.parent.get_current_editor().selectAll() if self.parent.get_current_editor() else None)
        edit_menu.addAction(select_all_action)
        
        # إضافة فاصل
        edit_menu.addSeparator()
        

        
        # قائمة تنسيق
        format_menu = self.addMenu('تنسيق')
        
        # عريض
        bold_action = QAction('عريض', self)
        bold_action.setShortcut(QKeySequence.Bold)  # Ctrl+B
        bold_action.triggered.connect(lambda: self.parent.format_text('bold'))
        format_menu.addAction(bold_action)
        
        # مائل
        italic_action = QAction('مائل', self)
        italic_action.setShortcut(QKeySequence.Italic)  # Ctrl+I
        italic_action.triggered.connect(lambda: self.parent.format_text('italic'))
        format_menu.addAction(italic_action)
        
        # تسطير
        underline_action = QAction('تسطير', self)
        underline_action.setShortcut(QKeySequence.Underline)  # Ctrl+U
        underline_action.triggered.connect(lambda: self.parent.format_text('underline'))
        format_menu.addAction(underline_action)
        
        format_menu.addSeparator()
        
        font_action = QAction('اختيار الخط...', self)
        font_action.triggered.connect(self.show_font_dialog)
        format_menu.addAction(font_action)

        


    def toggle_auto_save(self, enabled):
        """تفعيل/تعطيل الحفظ التلقائي"""
        try:
            # تحديث الإعدادات
            if hasattr(self.parent, 'settings_manager'):
                self.parent.settings_manager.update_setting('editor.auto_save.enabled', enabled)
            
            # عرض رسالة في شريط الحالة
            status_message = "تم تفعيل الحفظ التلقائي" if enabled else "تم تعطيل الحفظ التلقائي"
            self.parent.statusBar().showMessage(status_message, 2000)
            
            # تحديث حالة AutoSaver
            if hasattr(self.parent, 'auto_saver'):
                self.parent.auto_saver.enabled = enabled
                
        except Exception as e:
            QMessageBox.warning(
                self.parent, 
                "خطأ", 
                f"حدث خطأ أثناء تحديث إعدادات الحفظ التلقائي: {str(e)}"
            )

    def show_font_dialog(self):
        """عرض نافذة اختيار الخط"""
        current_editor = self.parent.get_current_editor()
        if not current_editor:
            return
            
        font, ok = QFontDialog.getFont(self.parent.default_font, self)
        if ok:
            self.parent.default_font = font
            self.parent.settings_manager.save_font(font)
            current_editor.apply_font(font)

    def load_font_settings(self):
        """تحميل إعدادات الخط"""
        if self.parent and self.parent.get_current_editor():
            current_editor = self.parent.get_current_editor()
            font = self.parent.default_font
            current_editor.setFont(font)

    def _show_terminal_search(self):
        """عرض البحث في التيرمنال"""
        if hasattr(self.parent, 'terminal_container'):
            terminal = self.parent.terminal_container.findChild(ArabicTerminal)
            if terminal:
                terminal.show_search()