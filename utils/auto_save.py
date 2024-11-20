from PyQt5.QtCore import QObject
import os
import traceback

class AutoSaver(QObject):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.enabled = False
        
        if hasattr(editor, 'settings_manager'):
            enabled = editor.settings_manager.get_setting('editor.auto_save.enabled')
            self.enabled = bool(enabled) if enabled is not None else False
        
    def perform_auto_save(self):
        """تنفيذ عملية الحفظ التلقائي للملف الحالي"""
        if not self.enabled:
            return False
            
        try:
            current_editor = self.editor.tab_manager.get_current_editor()
            if not current_editor:
                return False
                
            current_tab_index = self.editor.tab_manager.currentIndex()
            current_file = self.editor.tab_manager.get_file_path(current_tab_index)
            
            if not current_file:
                return False
                
            # نتأكد من وجود المجلد
            save_dir = os.path.dirname(current_file)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                
            with open(current_file, 'w', encoding='utf-8') as f:
                f.write(current_editor.toPlainText())
                
            current_editor.document().setModified(False)
            
            # تحديث عنوان التبويب
            current_title = self.editor.tab_manager.tabText(current_tab_index)
            if current_title.endswith('*'):
                self.editor.tab_manager.setTabText(current_tab_index, current_title[:-1])
                
            self.editor.statusBar().showMessage(f"تم الحفظ التلقائي: {os.path.basename(current_file)}", 1000)
            return True
            
        except Exception as e:
            self.editor.statusBar().showMessage(f"خطأ في الحفظ التلقائي: {str(e)}", 3000)
            return False