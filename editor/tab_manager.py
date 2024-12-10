from PyQt5.QtWidgets import QTabWidget, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QDrag
from .text_widget import ArabicTextEdit
import os

class TabManager(QTabWidget):
    editor_text_changed = pyqtSignal()
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_paths = {}  # قاموس لتخزين مسارات الملفات
        self.untitled_count = 0  # عداد للملفات الجديدة
        self.closed_tabs = []  # قائمة للتبويبات المغلقة
        self.max_closed_tabs = 10  # العدد الأقصى للتبويبات المغلقة المحفوظة
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.tab_changed)
        self.setMovable(True)
        self.setAcceptDrops(True)
        
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
        try:
            # التحقق من نوع الملف
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                QMessageBox.warning(
                    self,
                    "خطأ",
                    "يمكن فتح الملفات النصية فقط"
                )
                return None
            
            # إنشاء تبويب جديد
            editor = self.new_tab()
            editor.setPlainText(content)
            
            # تعيين مسار الملف للمحرر
            editor.file_path = file_path
            self.file_paths[editor] = file_path
            
            # تحديث عنوان التبويب
            current_index = self.currentIndex()
            self.setTabText(current_index, os.path.basename(file_path))
            
            # إعادة تعيين حالة التعديل
            editor.document().setModified(False)
            
            # إطلاق إشارة file_dropped في النافذة الرئيسية
            if hasattr(self.main_window, 'file_dropped'):
                self.main_window.file_dropped.emit(file_path, editor)
            
            # تفعيل الحفظ التلقائي
            if hasattr(self.main_window, 'auto_saver') and self.main_window.auto_saver.enabled:
                self.main_window.auto_saver.add_file_to_autosave(file_path, editor)
            
            return editor
            
        except Exception as e:
            QMessageBox.critical(self.parent, "خطأ", f"حدث خطأ أثناء فتح الملف: {str(e)}")
            return None
        
    def close_tab(self, index):
        """إغلاق التبويب"""
        # حفظ معلومات التبويب قبل إغلاقه
        editor = self.widget(index).findChild(ArabicTextEdit)
        if editor:
            tab_info = {
                'text': editor.toPlainText(),
                'file_path': self.file_paths.get(editor),
                'tab_name': self.tabText(index),
                'cursor_position': editor.textCursor().position()
            }
            self.closed_tabs.append(tab_info)
            
            # حذف أقدم تبويب إذا تجاوزنا الحد الأقصى
            if len(self.closed_tabs) > self.max_closed_tabs:
                self.closed_tabs.pop(0)
        
        if editor in self.file_paths:
            del self.file_paths[editor]
        
        self.removeTab(index)
        
    def restore_last_closed_tab(self):
        """استعادة آخر تبويب مغلق"""
        if not self.closed_tabs:
            return
            
        tab_info = self.closed_tabs.pop()
        editor = self.new_tab(tab_info['file_path'])
        
        if editor:
            editor.setPlainText(tab_info['text'])
            
            # استعادة موضع المؤشر
            cursor = editor.textCursor()
            cursor.setPosition(tab_info['cursor_position'])
            editor.setTextCursor(cursor)
            
            # تحديث عنوان التبويب
            current_index = self.currentIndex()
            self.setTabText(current_index, tab_info['tab_name'])
        
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
        
    def mousePressEvent(self, event):
        """معالجة الضغط على الماوس لبدء عملية السحب"""
        if event.button() == Qt.LeftButton:
            tab_index = self.tabBar().tabAt(event.pos())
            if tab_index >= 0:
                # بدء عملية السحب
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(self.tabText(tab_index))
                mime_data.setData("application/x-tab-index", str(tab_index).encode())
                drag.setMimeData(mime_data)
                
                # تنفيذ عملية السحب
                drag.exec_(Qt.MoveAction)
                
        super().mousePressEvent(event)
        
    def dragEnterEvent(self, event):
        """معالجة بداية عملية السحب"""
        mime_data = event.mimeData()
        
        # قبول الملفات والتبويبات
        if mime_data.hasUrls() or mime_data.hasFormat("application/x-tab-index"):
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """معالجة عملية الإفلات"""
        mime_data = event.mimeData()
        
        # التعامل مع إفلات التبويبات
        if mime_data.hasFormat("application/x-tab-index"):
            source_index = int(mime_data.data("application/x-tab-index").data())
            target_pos = self.tabBar().tabAt(event.pos())
            
            if target_pos >= 0 and source_index != target_pos:
                # نقل التبويب إلى الموقع الجديد
                self.moveTab(source_index, target_pos)
                
        # التعامل مع إفلات الملفات
        elif mime_data.hasUrls():
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if file_path:
                    # التحقق من نوع الملف
                    if self._is_text_file(file_path):
                        # فتح الملف في تبويب جديد
                        editor = self.main_window.tab_manager.open_file(file_path)
                        if editor:
                            # تعيين مسار الملف مباشرة
                            editor.file_path = file_path
                    else:
                        from PyQt5.QtWidgets import QMessageBox
                        QMessageBox.warning(
                            self,
                            "خطأ",
                            "يمكن فتح الملفات النصية فقط"
                        )
                        
        # التعامل مع إفلات النص
        elif mime_data.hasText():
            cursor = self.cursorForPosition(event.pos())
            cursor.insertText(mime_data.text())
            
        event.acceptProposedAction()
        
    def _is_text_file(self, file_path):
        """التحقق مما إذا كان الملف نصياً"""
        try:
            # محاولة قراءة الملف كنص
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # قراءة جزء صغير للتحقق
            return True
        except UnicodeDecodeError:
            return False
        except Exception:
            return False
