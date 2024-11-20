from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from .text_widget import ArabicTextEdit
import os

class TabManager(QTabWidget):
    editor_text_changed = pyqtSignal()
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_paths = {}  # قاموس لتخزين مسارات الملفات
        self.untitled_count = 0  # عداد للملفات الجديدة
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.tab_changed)
        
    def new_tab(self, file_path=None):
        """إنشاء تبويب جديد"""
        editor = ArabicTextEdit(self.main_window)
        
        # تطبيق الخط الافتراضي مباشرة
        if hasattr(self.main_window, 'default_font'):
            editor.apply_font_direct(self.main_window.default_font)
        
        container = editor.get_container()
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    editor.setPlainText(f.read())
                self.file_paths[editor] = file_path
                tab_name = os.path.basename(file_path)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"خطأ في فتح الملف: {str(e)}")
                return None
        else:
            self.untitled_count += 1
            tab_name = f"مستند {self.untitled_count}"
            self.file_paths[editor] = None
        
        index = self.addTab(container, tab_name)
        self.setCurrentIndex(index)
        editor.setFocus()
        return editor
        
    def get_file_path(self, index):
        """الحصول على مسار الملف للتبويب المحدد"""
        return self.file_paths.get(index)
        
    def set_file_path(self, index, file_path):
        """تعيين مسار الملف للتبويب المحدد"""
        self.file_paths[index] = file_path
        
    def open_file(self, file_path):
        """فتح ملف في تبويب جديد"""
        # التحقق مما إذا كان الملف مفتوحاً بالفعل
        for index, path in self.file_paths.items():
            if path == file_path:
                self.setCurrentIndex(index)
                return self.widget(index).findChild(ArabicTextEdit)
        
        editor = self.new_tab(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                editor.setPlainText(file.read())
            self.setTabText(self.currentIndex(), os.path.basename(file_path))
            self.file_paths[self.currentIndex()] = file_path
            editor.document().setModified(False)
            return editor
        except Exception as e:
            self.close_tab(self.currentIndex())
            QMessageBox.critical(self.main_window, "خطأ", f"خطأ في فتح الملف: {str(e)}")
            return None
        
    def close_tab(self, index):
        """إغلاق التبويب"""
        if index in self.file_paths:
            del self.file_paths[index]  # حذف مسار الملف عند إغلاق التبويب
        super().removeTab(index)
        
        # إنشاء تبويب جديد إذا لم يتبق أي تبويبات
        if self.count() == 0:
            self.new_tab()
            
    def tab_changed(self, index):
        """معالجة تغيير التبويب النشط"""
        if index >= 0:
            text_edit = self.widget(index).findChild(ArabicTextEdit)
            if text_edit:
                text_edit.setFocus()
                # تحديث العنوان والحالة في النافذة الرئيسية
                if hasattr(self.main_window, 'update_window_title'):
                    self.main_window.update_window_title(self.tabText(index))
                    
    def get_current_editor(self):
        """الحصول على المحرر النشط حالياً"""
        current_widget = self.currentWidget()
        if current_widget:
            # البحث عن ArabicTextEdit داخل التبويب الحالي
            return current_widget.findChild(ArabicTextEdit)
        return None
