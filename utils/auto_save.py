from PyQt5.QtCore import QObject, QTimer
import os

class AutoSavePlugin:
    """الفئة الأساسية للإضافات"""
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.enabled = True
    
    def before_save(self, file_path, content):
        """تنفيذ قبل الحفظ"""
        return content
    
    def after_save(self, file_path):
        """تنفيذ بعد الحفظ"""
        pass

class AutoSaver(QObject):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.enabled = False
        self.files_to_save = {}
        self.plugins = []  # قائمة الإضافات
        
        if hasattr(editor, 'settings_manager'):
            enabled = editor.settings_manager.get_setting('editor.auto_save.enabled')
            self.enabled = bool(enabled) if enabled is not None else False
        
        self.editor.file_opened.connect(self._handle_file_opened)
        self.editor.file_dropped.connect(self._handle_file_dropped)
    
    def add_plugin(self, plugin: AutoSavePlugin):
        """إضافة إضافة جديدة"""
        if isinstance(plugin, AutoSavePlugin):
            self.plugins.append(plugin)
    
    def remove_plugin(self, plugin_name: str):
        """إزالة إضافة"""
        self.plugins = [p for p in self.plugins if p.name != plugin_name]
    
    def _handle_file_opened(self, file_path, editor):
        """معالجة الملفات المفتوحة عن طريق القائمة أو Ctrl+O"""
        if self.enabled and file_path:
            self.add_file_to_autosave(file_path, editor)
    
    def _handle_file_dropped(self, file_path, editor):
        """معالجة الملفات المفتوحة عن طريق السحب والإفلات"""
        if self.enabled and file_path:
            self.add_file_to_autosave(file_path, editor)
    
    def add_file_to_autosave(self, file_path, editor):
        """إضافة ملف للحفظ التلقائي"""
        if self.enabled and file_path:
            self.files_to_save[editor] = file_path
            # ربط إشارة تغيير المحتوى مع الحفظ التلقائي
            editor.document().contentsChanged.connect(
                lambda: self.schedule_auto_save(editor)
            )
            # حفظ الملف مباشرة عند إضافته
            self.perform_auto_save()
    
    def schedule_auto_save(self, editor):
        """جدولة الحفظ التلقائي بعد تغيير المحتوى"""
        if self.enabled and editor in self.files_to_save:
            QTimer.singleShot(1000, lambda: self.save_file(editor))
    
    def save_file(self, editor):
        """حفظ الملف مع تطبيق الإضافات"""
        if not self.enabled or editor not in self.files_to_save:
            return
            
        file_path = self.files_to_save[editor]
        try:
            content = editor.toPlainText()
            
            # تطبيق إضافات ما قبل الحفظ
            for plugin in [p for p in self.plugins if p.enabled]:
                try:
                    content = plugin.before_save(file_path, content)
                except Exception as e:
                    print(f"خطأ في الإضافة {plugin.name}: {str(e)}")
            
            # حفظ الملف
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            editor.document().setModified(False)
            
            # تطبيق إضافات ما بعد الحفظ
            for plugin in [p for p in self.plugins if p.enabled]:
                try:
                    plugin.after_save(file_path)
                except Exception as e:
                    print(f"خطأ في الإضافة {plugin.name}: {str(e)}")
                    
        except Exception as e:
            if hasattr(self.editor, 'statusBar'):
                self.editor.statusBar().showMessage(f"خطأ في الحفظ التلقائي: {str(e)}", 3000)
    
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
                
            with open(current_file, 'w') as f:
                f.write(current_editor.toPlainText())
                
            current_editor.document().setModified(False)
            
            # تحديث عنوان التبويب
            current_title = self.editor.tab_manager.tabText(current_tab_index)
            if current_title.endswith('*'):
                self.editor.tab_manager.setTabText(current_tab_index, current_title[:-1])
                
            return True
            
        except Exception as e:
            self.editor.statusBar().showMessage(f"خطأ في الحفظ التلقائي: {str(e)}", 3000)
            return False