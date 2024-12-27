try:        
    from PyQt5.QtWidgets import QTabWidget, QMessageBox, QMenu, QAction, QTabBar
    from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
    from PyQt5.QtGui import QDrag
    from .text_widget import ArabicTextEdit
    import os
    import subprocess
    from utils.arabic_logger import setup_arabic_logging, log_in_arabic
    import logging
    from datetime import datetime
    import difflib
    from PyQt5.QtCore import QTimer
    import re

    # إعداد اللوج
    formatter = setup_arabic_logging()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

except Exception as e:
    try:
        formatter = setup_arabic_logging()
        logger = logging.getLogger(__name__)
        log_in_arabic(logger, logging.ERROR, f"خطأ في تحميل المكتبات: {e}")
    except Exception as e:
        print(f"خطأ في تحميل المكتبات: {e}")

class TabManager(QTabWidget):
    """مدير التبويبات الرئيسي للمحرر."""
    
    editor_text_changed = pyqtSignal()
    
    def __init__(self, main_window):
        try:
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
            
            # إضافة قائمة لحفظ تاريخ التغييرات
            self.undo_stack = []
            self.redo_stack = []
            self.max_history = 100  # عدد التغييرات المحفوظة
            
            # قاموس لتخزين أنواع الملفات
            self.file_types = {}
            
            log_in_arabic(logger, logging.INFO, "تم تهيئة مدير التبويبات بنجاح")
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تهيئة مدير التبويبات: {e}")

    def detect_file_type(self, file_path=None, content=None):
        """التعرف على نوع الملف من امتداده ومحتواه"""
        try:
            if file_path:
                # التعرف من امتداد الملف
                ext = os.path.splitext(file_path)[1].lower()
                
                # قاموس الامتدادات المعروفة
                extensions = {
                    '.py': 'Python',
                    '.js': 'JavaScript',
                    '.html': 'HTML',
                    '.css': 'CSS',
                    '.java': 'Java',
                    '.cpp': 'C++',
                    '.c': 'C',
                    '.cs': 'C#',
                    '.php': 'PHP',
                    '.rb': 'Ruby',
                    '.go': 'Go',
                    '.rs': 'Rust',
                    '.ts': 'TypeScript',
                    '.json': 'JSON',
                    '.xml': 'XML',
                    '.yaml': 'YAML',
                    '.yml': 'YAML',
                    '.md': 'Markdown',
                    '.sql': 'SQL',
                    '.sh': 'Bash',
                    '.ps1': 'PowerShell',
                    '.txt': 'Text'
                }
                
                if ext in extensions:
                    return extensions[ext]
                
            # إذا لم يتم التعرف من الامتداد، نحاول التعرف من المحتوى
            if content:
                # التعرف على Python
                if re.search(r'^#!.*python|^from\s+[\w.]+\s+import|^import\s+[\w.]+', content, re.M):
                    return 'Python'
                
                # التعرف على HTML
                if re.search(r'<!DOCTYPE html>|<html|<head|<body', content, re.I):
                    return 'HTML'
                
                # التعرف على JavaScript
                if re.search(r'function\s+\w+\s*\(|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=', content):
                    return 'JavaScript'
                
                # التعرف على CSS
                if re.search(r'{\s*[\w-]+\s*:\s*[^}]+}', content):
                    return 'CSS'
                
                # التعرف على JSON
                if content.strip().startswith('{') and content.strip().endswith('}'):
                    try:
                        import json
                        json.loads(content)
                        return 'JSON'
                    except:
                        pass
            
            # إذا لم نتمكن من التعرف على النوع
            return 'Text'
            
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في التعرف على نوع الملف: {str(e)}")
            return 'Text'

    def update_file_type(self, editor, file_path=None):
        """تحديث نوع الملف في شريط الحالة"""
        try:
            content = editor.toPlainText()
            file_type = self.detect_file_type(file_path, content)
            
            # تخزين نوع الملف
            self.file_types[editor] = file_type
            
            # تحديث شريط الحالة
            if hasattr(self.main_window, 'statistics_manager'):
                self.main_window.statistics_manager.update_statistics(
                    text=content,
                    file_type=file_type
                )
            
            log_in_arabic(logger, logging.INFO, f"تم تحديث نوع الملف: {file_type}")
            
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تحديث نوع الملف: {str(e)}")

    def new_tab(self, file_path=None):
        """إنشاء تبويب جديد."""
        try:
            editor = ArabicTextEdit(self.main_window)
            
            # تطبيق الخط مباشرة
            try:
                if hasattr(self.main_window, 'default_font'):
                    editor.apply_font_direct(self.main_window.default_font)
            except Exception as e:
                log_in_arabic(logger, logging.ERROR, f"خطأ في تطبيق الخط: {e}")
            
            container = editor.get_container()
            
            if file_path:
                try:
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"الملف غير موجود: {file_path}")
                        
                    # قراءة الملف بشكل أكثر كفاءة
                    with open(file_path, 'r', encoding='utf-8', buffering=16384) as f:
                        content = f.read()
                        editor.setPlainText(content)
                    
                    editor.file_path = file_path
                    self.file_paths[editor] = file_path
                    tab_name = os.path.basename(file_path)
                    
                    # تحديث نوع الملف
                    self.update_file_type(editor, file_path)
                    
                except Exception as e:
                    QMessageBox.warning(self, "خطأ", f"خطأ في فتح الملف: {str(e)}")
                    return None
            else:
                self.untitled_count += 1
                tab_name = f"مستند {self.untitled_count}"
                editor.file_path = None
                self.file_paths[editor] = None
                
                # تحديث نوع الملف للملف الجديد
                self.update_file_type(editor)

            # تجميع عمليات التبويب معاً
            try:
                index = self.addTab(container, tab_name)
                self.update_close_button_tooltip(index)
                self.setCurrentIndex(index)
            except Exception as e:
                log_in_arabic(logger, logging.ERROR, f"خطأ في إضافة التبويب: {str(e)}")
                return None

            # تأجيل إعداد الإشارات حتى اكتمال التهيئة
            try:
                editor.textChanged.connect(lambda: self.on_text_changed(editor))
                editor.setFocus()
            except Exception as e:
                log_in_arabic(logger, logging.ERROR, f"خطأ في إعداد الإشارات: {str(e)}")
            
            log_in_arabic(logger, logging.INFO, f"تم إنشاء تبويب جديد: {tab_name}")
            return editor
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ غير متوقع في إنشاء تبويب جديد: {e}")
            QMessageBox.critical(self, "خطأ", f"خطأ غير متوقع: {str(e)}")
            return None

    def on_text_changed(self, editor):
        """معالجة تغيير النص في المحرر"""
        self.editor_text_changed.emit()
        # تحديث نوع الملف عند تغيير المحتوى
        self.update_file_type(editor, self.file_paths.get(editor))

    def tab_changed(self, index):
        """معالجة تغيير التبويب النشط"""
        if index >= 0:
            editor = self.widget(index).findChild(ArabicTextEdit)
            if editor:
                editor.setFocus()
                # تحديث نوع الملف للتبويب الجديد
                self.update_file_type(editor, self.file_paths.get(editor))
                # تحديث العنوان والحالة في النافذة الرئيسية
                if hasattr(self.main_window, 'update_window_title'):
                    self.main_window.update_window_title(self.tabText(index))

    def get_file_path(self, index):
        """الحصول على مسار الملف للتبويب المحدد"""
        return self.file_paths.get(index)
        
    def set_file_path(self, editor_or_index, file_path):
        """تعيين مسار الملف بشكل أسرع"""
        try:
            if isinstance(editor_or_index, int):
                editor = self.widget(editor_or_index).findChild(ArabicTextEdit)
            else:
                editor = editor_or_index
            
            if not editor:
                return
            
            self.file_paths[editor] = file_path
            editor.file_path = file_path
            
            # تحسين البحث عن التبويب
            try:
                for i in range(self.count()):
                    widget = self.widget(i)
                    if widget and widget.findChild(ArabicTextEdit) == editor:
                        self.setTabText(i, os.path.basename(file_path))
                        break
            except Exception as e:
                log_in_arabic(logger, logging.ERROR, f"خطأ في تحديث عنوان التبويب: {str(e)}")
            
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تعيين مسار الملف: {str(e)}")

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
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        editor.setPlainText(content)
                
                # تحديث مسار الملف وإعداد المراقبة
                self.set_file_path(editor, file_path)
                editor.document().setModified(False)
                
                # إضافة الملف للمراقبة
                if hasattr(self.main_window, 'file_watcher'):
                    self.main_window.file_watcher.add_file(file_path, editor)
                
                # تفعيل الحفظ التلقائي
                if hasattr(self.main_window, 'auto_saver'):
                    self.main_window.auto_saver.add_file_to_autosave(file_path, editor)
                
                log_in_arabic(logger, logging.INFO, f"تم فتح الملف بنجاح: {file_path}")
                return editor
                
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في فتح الملف: {e}")
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء فتح الملف: {str(e)}",
                QMessageBox.Ok
            )
            return None
        
    def close_tab(self, index):
        """إغلاق التبويب بشكل أسرع"""
        try:
            widget = self.widget(index)
            if not widget:
                log_in_arabic(logger, logging.WARNING, f"محاولة إغلاق تبويب غير موجود: {index}")
                return
            
            editor = widget.findChild(ArabicTextEdit)
            if not editor:
                log_in_arabic(logger, logging.WARNING, "لم يتم العثور على المحرر في التبويب")
                return

            try:
                # التحقق من التغييرات غير المحفوظة
                if editor.document().isModified():
                    msg_box = QMessageBox()
                    msg_box.setWindowTitle("تنبيه")
                    msg_box.setText("هناك تغييرات غير محفوظة. هل تريد حفظ التغييرات؟")
                    
                    # إضافة الأزرار المعربة
                    save_button = msg_box.addButton("حفظ", QMessageBox.AcceptRole)
                    discard_button = msg_box.addButton("تجاهل", QMessageBox.DestructiveRole) 
                    cancel_button = msg_box.addButton("إلغاء", QMessageBox.RejectRole)
                    
                    msg_box.exec_()
                    
                    clicked_button = msg_box.clickedButton()
                    
                    if clicked_button == save_button and not self.main_window.save_file():
                        return
                    elif clicked_button == cancel_button:
                        return
            except Exception as e:
                log_in_arabic(logger, logging.ERROR, f"خطأ في التحقق من التغييرات: {e}")

            try:
                # تجميع معلومات التبويب مرة واحدة
                file_path = self.file_paths.get(editor)
                tab_info = {
                    'text': editor.toPlainText(),
                    'file_path': file_path,
                    'tab_name': self.tabText(index),
                    'cursor_position': editor.textCursor().position()
                }
                
                # إدارة التبويبات المغلقة
                self.closed_tabs.append(tab_info)
                if len(self.closed_tabs) > self.max_closed_tabs:
                    self.closed_tabs.pop(0)
            except Exception as e:
                log_in_arabic(logger, logging.ERROR, f"خطأ في حفظ معلومات التبويب: {str(e)}")
            
            try:
                # إزالة المراقبة بشكل آمن
                if file_path and hasattr(self.main_window, 'file_watcher'):
                    watcher = self.main_window.file_watcher
                    if hasattr(watcher, 'remove_file'):
                        watcher.remove_file(file_path)
                    elif hasattr(watcher, 'removePath'):
                        watcher.removePath(file_path)
            except Exception:
                pass

            try:
                # تنظيف الموارد
                if editor in self.file_paths:
                    del self.file_paths[editor]
                
                self.removeTab(index)
            except Exception as e:
                log_in_arabic(logger, logging.ERROR, f"خطأ في إزالة التبويب: {str(e)}")
            
            log_in_arabic(logger, logging.INFO, f"تم إغلاق التبويب بنجاح: {self.tabText(index)}")
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ غير متوقع في إغلاق التبويب: {e}")
        
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
            log_in_arabic
            return False
        except Exception:
            return False
            
    def contextMenuEvent(self, event):
        """معالجة حدث النقر بزر الماوس الأيمن"""
        try:
            tab_bar = self.tabBar()
            tab_index = tab_bar.tabAt(event.pos())
            
            if tab_index >= 0:
                editor = self.widget(tab_index).findChild(ArabicTextEdit)
                file_path = self.file_paths.get(editor)
                
                context_menu = QMenu(self)
                try:    
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
                except Exception as e:
                    log_in_arabic(logger, logging.ERROR, f"خطأ في إعداد الإجراءات: {str(e)}")
                    return
                
                # تعطيل بعض الإجراءات إذا كان الملف غير محفوظ
                if not file_path:
                    open_location_action.setEnabled(False)
                    copy_path_action.setEnabled(False)
                    reload_action.setEnabled(False)
                    
                
                try:
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
                except Exception as e:
                    log_in_arabic(logger, logging.ERROR, f"خطأ في ربط الإجراءات: {str(e)}")
                    return
                
                try:
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
                except Exception as e:
                    log_in_arabic(logger, logging.ERROR, f"خطأ في إضافة الإجراءات للقائمة: {str(e)}")
                    
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في إعداد القائمة السياقية: {str(e)}")
            
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
                log_in_arabic(logger, logging.INFO, f"إعادة تسمية التبويب: {current_name} إلى {new_name}")
                
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
                    log_in_arabic(logger, logging.INFO, f"تم إعادة تسمية التبويب: {current_name} إلى {new_name}")
                        
                except OSError as e:
                    QMessageBox.warning(
                        self,
                        "خطأ",
                        f"حدث خطأ أثناء إعادة تسمية الملف: {str(e)}"
                    )
                    log_in_arabic(logger, logging.ERROR, f"حدث خطأ أثناء إعادة تسمية الملف: {str(e)}")
            else:
                # إذا كان الملف غير محفوظ، نقوم فقط بتغيير اسم التبويب
                self.setTabText(index, new_name)
                if hasattr(self.main_window, 'update_window_title'):
                    self.main_window.update_window_title(new_name)
                log_in_arabic(logger, logging.INFO, f"تم إعادة تسمية التبويب: {current_name} إلى {new_name}")

    def open_file_location(self, file_path):
        """فتح موقع الملف في مستكشف الملفات"""
        if file_path:
            try:
                folder_path = os.path.dirname(os.path.abspath(file_path))
                if os.name == 'nt':  # Windows
                    os.startfile(folder_path)
                    log_in_arabic(logger, logging.INFO, f"تم فتح موقع الملف: {folder_path}")
                elif os.name == 'posix':  # macOS and Linux
                    if os.path.exists('/usr/bin/xdg-open'):  # Linux
                        subprocess.run(['xdg-open', folder_path])
                    else:  # macOS
                        subprocess.run(['open', folder_path])
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء فتح موقع الملف: {str(e)}")
                log_in_arabic(logger, logging.ERROR, f"حدث خطأ أثناء فتح موقع الملف: {str(e)}")

    def copy_file_path(self, file_path):
        """نسخ مسار الملف إلى الحافظة"""
        if file_path:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(file_path)
            log_in_arabic(logger, logging.INFO, f"تم نسخ مسار الملف: {file_path}")
    
    def close_other_tabs(self, keep_index):
        """إغلاق جميع التبويبات ما عدا التبويب المحدد"""
        for i in range(self.count() - 1, -1, -1):
            if i != keep_index:
                self.close_tab(i)
                log_in_arabic(logger, logging.INFO, f"تم إغلاق التبويب: {i}")

    def close_all_tabs(self):
        """إغلاق جميع التبويبات"""
        for i in range(self.count() - 1, -1, -1):
            self.close_tab(i)
            log_in_arabic(logger, logging.INFO, f"تم إغلاق التبويبات: {i}")

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
                
                # نسخ ��سار الملف إذا كان موجوداً
                file_path = self.file_paths.get(editor)
                if file_path:
                    new_name = f"نسخة من {os.path.basename(file_path)}"
                    log_in_arabic(logger, logging.INFO, f"تم إنشاء تبويب جديد: {new_name}")
                else:
                    new_name = f"نسخة من {self.tabText(index)}"
                    log_in_arabic(logger, logging.INFO, f"تم إنشاء تبويب جديد: {new_name}")
                
                # تحديث عنوان التبويب الجديد
                current_index = self.currentIndex()
                self.setTabText(current_index, new_name)
                log_in_arabic(logger, logging.INFO, f"تم تحديث عنوان التبويب: {new_name}")

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
                log_in_arabic(logger, logging.INFO, f"تم إعادة تحميل الملف: {file_path}")

            except Exception as e:
                QMessageBox.warning(
                    self,
                    "خطأ",
                    f"حدث خطأ أثناء إعادة تحميل الملف: {str(e)}"
                )

    def get_current_editor(self):
        """الحصول على المحرر النشط حالياً"""
        try:
            current_widget = self.currentWidget()
            if current_widget:
                editor = current_widget.findChild(ArabicTextEdit)
                return editor
            return None
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في الحصول على المحرر الحالي: {e}")
            return None

