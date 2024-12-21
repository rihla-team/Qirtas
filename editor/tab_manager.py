from PyQt5.QtWidgets import QTabWidget, QMessageBox, QMenu, QAction, QTabBar
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QDrag
from .text_widget import ArabicTextEdit
import os
import subprocess

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
        
        # تعديل تلميح زر الإغلاق
        close_button = self.tabBar().tabButton(0, QTabBar.RightSide)
        if close_button:
            close_button.setToolTip("إغلاق التبويب")
            
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.tab_changed)
        self.setMovable(True)
        self.setAcceptDrops(True)
        self.setUsesScrollButtons(True)
        self.setElideMode(Qt.ElideMiddle)
        self.setDocumentMode(True)
        
     
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
        self.update_close_button_tooltip(index)
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
            # التحقق من وجود الملف في التبويبات المفتوحة
            for i in range(self.count()):
                editor = self.widget(i).findChild(ArabicTextEdit)
                if editor and self.file_paths.get(editor) == file_path:
                    # الانتقال إلى التبويب الموجود
                    self.setCurrentIndex(i)
                    editor.setFocus()
                    return editor

            editor = self.new_tab()
            if editor:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    editor.setPlainText(content)
                
                editor.file_path = file_path
                self.file_paths[editor] = file_path
                current_index = self.currentIndex()
                self.setTabText(current_index, os.path.basename(file_path))
                editor.document().setModified(False)
                
                # إضافة الملف للمراقبة
                if hasattr(self.main_window, 'file_watcher'):
                    self.main_window.file_watcher.add_file(file_path, editor)
                
                # تفعيل الحفظ التلقائي
                if hasattr(self.main_window, 'auto_saver'):
                    self.main_window.auto_saver.add_file_to_autosave(file_path, editor)
                
                return editor
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء فتح الملف: {str(e)}",
                QMessageBox.Ok
            )
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
        
        # إزالة الملف من المراقبة
        file_path = self.file_paths.get(editor)
        if file_path and hasattr(self.main_window, 'file_watcher'):
            self.main_window.file_watcher.remove_file(file_path)
        
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
                f.read(1024)  # قراءة جزء صغير لتحقق
            return True
        except UnicodeDecodeError:
            return False
        except Exception:
            return False
        
    def contextMenuEvent(self, event):
        """معالجة حد�� النقر بزر الماوس الأيمن"""
        tab_bar = self.tabBar()
        tab_index = tab_bar.tabAt(event.pos())
        
        if tab_index >= 0:
            editor = self.widget(tab_index).findChild(ArabicTextEdit)
            file_path = self.file_paths.get(editor)
            
            context_menu = QMenu(self)
            
            # إجراءات الملف
            save_action = QAction("حفظ", self)
            save_as_action = QAction("حفظ باسم", self)
            reload_action = QAction("إعادة تحميل من القرص", self)
            
            # إجراءات التبويب
            rename_action = QAction("إعادة تسمية", self)
            duplicate_action = QAction("تكرار التبويب", self)
            open_location_action = QAction("فتح موقع الملف", self)
            copy_path_action = QAction("نسخ مسار الملف", self)
            
            # إجراءات الإغلاق
            close_action = QAction("إغلاق", self)
            close_others_action = QAction("إغلاق التبويبات الأخرى", self)
            close_all_action = QAction("إغلاق الكل", self)
            
            # تعطيل بعض الإجراءات إذا كان الملف غير محفوظ
            if not file_path:
                open_location_action.setEnabled(False)
                copy_path_action.setEnabled(False)
                reload_action.setEnabled(False)
            
            # ربط الإجراءات بالدوال
            save_action.triggered.connect(lambda: self.main_window.save_file())
            save_as_action.triggered.connect(lambda: self.main_window.save_file_as())
            reload_action.triggered.connect(lambda: self.reload_tab(tab_index))
            rename_action.triggered.connect(lambda: self.rename_tab(tab_index))
            duplicate_action.triggered.connect(lambda: self.duplicate_tab(tab_index))
            open_location_action.triggered.connect(lambda: self.open_file_location(file_path))
            copy_path_action.triggered.connect(lambda: self.copy_file_path(file_path))
            close_action.triggered.connect(lambda: self.close_tab(tab_index))
            close_others_action.triggered.connect(lambda: self.close_other_tabs(tab_index))
            close_all_action.triggered.connect(self.close_all_tabs)
            
            # إضافة الإجراءات للقائمة
            context_menu.addAction(save_action)
            context_menu.addAction(save_as_action)
            if file_path:
                context_menu.addAction(reload_action)
            
            context_menu.addSeparator()
            context_menu.addAction(rename_action)
            context_menu.addAction(duplicate_action)
            
            if file_path:
                context_menu.addAction(open_location_action)
                context_menu.addAction(copy_path_action)
            
            context_menu.addSeparator()
            context_menu.addAction(close_action)
            context_menu.addAction(close_others_action)
            context_menu.addAction(close_all_action)
            
            # عرض القائمة
            context_menu.exec_(event.globalPos())
    
    def rename_tab(self, index):
        """إعادة تسمية التبويب"""
        from PyQt5.QtWidgets import QInputDialog
        
        current_name = self.tabText(index)
        new_name, ok = QInputDialog.getText(
            self,
            "إعادة تسمية",
            "أدخل الاسم الجديد:",
            text=current_name
        )
        
        if ok and new_name:
            editor = self.widget(index).findChild(ArabicTextEdit)
            if editor and editor in self.file_paths and self.file_paths[editor]:
                old_path = self.file_paths[editor]
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                
                try:
                    # التأكد من عدم وجود ملف بنفس الاسم
                    if os.path.exists(new_path):
                        QMessageBox.warning(
                            self,
                            "خطأ",
                            "يوجد ملف بنفس الاسم بالفعل!"
                        )
                        return
                    
                    # إعادة تسمية الملف الفعلي
                    os.rename(old_path, new_path)
                    
                    # تحديث مسار الملف في القاموس
                    self.file_paths[editor] = new_path
                    
                    # تحديث اسم التبويب
                    self.setTabText(index, new_name)
                    
                    # تحديث عنوان النافذة الرئيسية
                    if hasattr(self.main_window, 'update_window_title'):
                        self.main_window.update_window_title(new_name)
                        
                except OSError as e:
                    QMessageBox.warning(
                        self,
                        "خطأ",
                        f"حدث خطأ أثناء إعادة تسمية الملف: {str(e)}"
                    )
            else:
                # إذا كان الملف غير محفوظ، نقوم فقط بتغيير اسم التبويب
                self.setTabText(index, new_name)
                if hasattr(self.main_window, 'update_window_title'):
                    self.main_window.update_window_title(new_name)
    
    def open_file_location(self, file_path):
        """فتح موقع الملف في مستكشف الملفات"""
        if file_path:
            try:
                folder_path = os.path.dirname(os.path.abspath(file_path))
                if os.name == 'nt':  # Windows
                    os.startfile(folder_path)
                elif os.name == 'posix':  # macOS and Linux
                    if os.path.exists('/usr/bin/xdg-open'):  # Linux
                        subprocess.run(['xdg-open', folder_path])
                    else:  # macOS
                        subprocess.run(['open', folder_path])
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء فتح موقع الملف: {str(e)}")
    
    def copy_file_path(self, file_path):
        """نسخ مسار الملف إلى الحافظة"""
        if file_path:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(file_path)
    
    def close_other_tabs(self, keep_index):
        """إغلاق جميع التبويبات ما عدا التبويب المحدد"""
        for i in range(self.count() - 1, -1, -1):
            if i != keep_index:
                self.close_tab(i)
    
    def close_all_tabs(self):
        """إغلاق جميع التبويبات"""
        for i in range(self.count() - 1, -1, -1):
            self.close_tab(i)
    
    def update_close_button_tooltip(self, index):
        """تحديث تلميح زر الإغلاق للتبويب"""
        close_button = self.tabBar().tabButton(index, QTabBar.RightSide)
        if close_button:
            close_button.setToolTip("إغلاق التبويب")
    
    def duplicate_tab(self, index):
        """تكرار التبويب الحالي"""
        editor = self.widget(index).findChild(ArabicTextEdit)
        if editor:
            # إنشاء تبويب جديد
            new_editor = self.new_tab()
            if new_editor:
                # نسخ المحتوى
                new_editor.setPlainText(editor.toPlainText())
                
                # نسخ مسار الملف إذا كان موجوداً
                file_path = self.file_paths.get(editor)
                if file_path:
                    new_name = f"نسخة من {os.path.basename(file_path)}"
                else:
                    new_name = f"نسخة من {self.tabText(index)}"
                
                # تحديث عنوان التبويب الجديد
                current_index = self.currentIndex()
                self.setTabText(current_index, new_name)
    
    def reload_tab(self, index):
        """إعادة تحميل محتوى الملف من القرص"""
        editor = self.widget(index).findChild(ArabicTextEdit)
        file_path = self.file_paths.get(editor)
        
        if editor and file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    editor.setPlainText(content)
                editor.document().setModified(False)
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "خطأ",
                    f"حدث خطأ أثناء إعادة تحميل الملف: {str(e)}"
                )
