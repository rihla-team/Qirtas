"""
محرر النصوص - وحدة البحث والاستبدال
=================================

هذه الوحدة تحتوي على الفئات المسؤولة عن وظائف البحث والاستبدال في المحرر.
تتضمن نافذة البحث ونافذة البحث والاستبدال، بالإضافة إلى مدير البحث.
"""
try:    
    import logging

    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QLineEdit, QPushButton, QCheckBox, QInputDialog, QMessageBox
    )
    from PyQt5.QtGui import QTextDocument
    from PyQt5.QtCore import pyqtSignal

    from utils.arabic_logger import setup_arabic_logging, log_in_arabic
except Exception as e:
    logger = logging.getLogger(__name__)
    log_in_arabic(logger, logging.ERROR, f"خطأ في استيراد المكتبات: {e}")
# إعداد التسجيل العربي
formatter = setup_arabic_logging()
logger = logging.getLogger(__name__)

# إضافة ترجمات خاصة بوحدة البحث
if formatter:
    formatter.register_translations({
        'SearchDialog': 'نافذة البحث',
        'SearchManager': 'مدير البحث',
        'search_dialog': 'نافذة البحث',
        'Failed to initialize search dialog': 'فشل في تهيئة نافذة البحث',
        'Failed to setup UI': 'فشل في إعداد واجهة المستخدم',
        'Failed to create search section': 'فشل في إنشاء قسم البحث',
        'Failed to create options section': 'فشل في إنشاء قسم الخيارات',
        'Failed to create buttons section': 'فشل في إنشاء قسم الأزرار',
        'Failed to create input field': 'فشل في إنشاء حقل الإدخال',
        'Failed to create button': 'فشل في إنشاء الزر',
        'Failed to connect signals': 'فشل في ربط الإشارات',
        'Failed to perform search': 'فشل في تنفيذ البحث',
        'Failed to perform replace': 'فشل في تنفيذ الاستبدال',
        'Failed to perform replace all': 'فشل في تنفيذ استبدال الكل',
        'Failed to show dialog': 'فشل في عرض نافذة الحوار',
        'Failed to go to line': 'فشل في الانتقال إلى السطر',
        'editor.search_dialog': 'محرر النصوص - وحدة البحث والاستبدال'
    })

class SearchError(Exception):
    """استثناء خاص بأخطاء البحث"""
    pass

class SearchDialog(QDialog):
    """نافذة البحث والاستبدال في المحرر.
    
    تتيح هذه النافذة للمستخدم البحث عن نص في المحرر والاستبدال إذا تم تفعيل خيار الاستبدال.
    
    Signals:
        searchRequested (str, bool, bool, bool): إشارة تُطلق عند طلب البحث
            - نص البحث
            - البحث للأمام
            - مطابقة حالة الأحرف
            - البحث عن كلمات كاملة
        replaceRequested (str, str): إشارة تُطلق عند طلب الاستبدال
            - نص البحث
            - نص الاستبدال
    """
    
    # الإشارات
    searchRequested = pyqtSignal(str, bool, bool, bool)
    replaceRequested = pyqtSignal(str, str)

    def __init__(self, parent=None, is_replace: bool = False):
        """تهيئة نافذة البحث.
        
        Args:
            parent: النافذة الأم
            is_replace (bool): هل هي نافذة استبدال
        """
        try:
                super().__init__(parent)
                self.parent = parent
                self.is_replace = is_replace
                
                # إعداد النافذة
                self._setup_ui()
                self._connect_signals()
                
                log_in_arabic(logger, logging.INFO, f"تم تهيئة {'نافذة البحث والاستبدال' if is_replace else 'نافذة البحث'} بنجاح")
                
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تهيئة نافذة البحث: {str(e)}")
            raise SearchError("فشل في تهيئة نافذة البحث") from e
        
    def _setup_ui(self):
        """إعداد واجهة المستخدم."""
        try:
            # إعداد النافذة
            self.setWindowTitle('بحث واستبدال' if self.is_replace else 'بحث')
            self.setFixedSize(400, 200 if self.is_replace else 150)
            
            # التخطيط الرئيسي
            layout = QVBoxLayout(self)
            layout.setSpacing(10)
            layout.setContentsMargins(15, 15, 15, 15)
            
            # إنشاء العناصر
            self._create_search_section(layout)
            self._create_options_section(layout)
            self._create_buttons_section(layout)
            
        except Exception as e:
            logger.error(f"خطأ في إعداد واجهة المستخدم: {str(e)}")
            raise SearchError("فشل في إعداد واجهة المستخدم") from e

    def _create_search_section(self, layout: QVBoxLayout):
        """إنشاء قسم البحث والاستبدال.
        
        Args:
            layout: التخطيط الرئيسي
        """
        try:
        # حقل البحث
            self.search_input = self._create_input_field('بحث عن:', layout)
            self.search_input.setMinimumWidth(250)
            
            # حقل الاستبدال
            if self.is_replace:
                self.replace_input = self._create_input_field('استبدال بـ:', layout)
                self.replace_input.setMinimumWidth(250)
            else:
                self.replace_input = None
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء قسم البحث: {str(e)}")
            raise SearchError("فشل في إنشاء قسم البحث") from e

    def _create_options_section(self, layout: QVBoxLayout):
        """إنشاء قسم خيارات البحث.
        
        Args:
            layout: التخطيط الرئيسي
        """
        try:
                options = QHBoxLayout()
                options.setSpacing(20)
            
        # خيارات البحث
                self.case_sensitive = QCheckBox('مطابقة حالة الأحرف')
                self.whole_words = QCheckBox('كلمات كاملة فقط')
                
                options.addWidget(self.case_sensitive)
                options.addWidget(self.whole_words)
                options.addStretch()
                
                layout.addLayout(options)
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء قسم الخيارات: {str(e)}")
            raise SearchError("فشل في إنشاء قسم الخيارات") from e

    def _create_buttons_section(self, layout: QVBoxLayout):
        """إنشاء قسم الأزرار.
        
        Args:
            layout: التخطيط الرئيسي
        """
        try:
        # أزرار البحث
            search_buttons = QHBoxLayout()
            search_buttons.setSpacing(10)
            
            search_buttons.addWidget(
                self._create_button('بحث عن التالي', lambda: self._do_search(True))
            )
            search_buttons.addWidget(
                self._create_button('بحث عن السابق', lambda: self._do_search(False))
            )
            
            layout.addLayout(search_buttons)

            # أزرار الاستبدال
            if self.is_replace:
                replace_buttons = QHBoxLayout()
                replace_buttons.setSpacing(10)
                
                replace_buttons.addWidget(
                    self._create_button('استبدال', self._do_replace)
                )
                replace_buttons.addWidget(
                    self._create_button('استبدال الكل', self._do_replace_all)
                )
                
                layout.addLayout(replace_buttons)
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء قسم الأزرار: {str(e)}")
            raise SearchError("فشل في إنشاء قسم الأزرار") from e

    def _create_input_field(self, label_text: str, parent_layout: QVBoxLayout) -> QLineEdit:
        """إنشاء حقل إدخال مع تسمية.
        
        Args:
            label_text (str): نص التسمية
            parent_layout: التخطيط الأب
            
        Returns:
            QLineEdit: حقل الإدخال
        """
        try:
            container = QHBoxLayout()
            container.setSpacing(10)
            
            # إنشاء حقل الإدخال
            input_field = QLineEdit()
            input_field.setPlaceholderText(label_text.replace(':', ''))
            
            # إضافة التسمية وحقل الإدخال
            label = QLabel(label_text)
            label.setMinimumWidth(80)
            
            container.addWidget(label)
            container.addWidget(input_field)
            
            parent_layout.addLayout(container)
            return input_field
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء حقل الإدخال: {str(e)}")
            raise SearchError("فشل في إنشاء حقل الإدخال") from e

    def _create_button(self, text: str, callback) -> QPushButton:
        """إنشاء زر.
        
        Args:
            text (str): نص الزر
            callback: الدالة التي ستنفذ عند النقر
            
        Returns:
            QPushButton: الزر
        """
        try:
            btn = QPushButton(text)
            btn.setMinimumWidth(120)
            btn.clicked.connect(callback)
            return btn
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء الزر: {str(e)}")
            raise SearchError("فشل في إنشاء الزر") from e

    def _connect_signals(self):
        """ربط الإشارات بالدوال."""
        try:
            # ربط مفتاح الإدخال
            self.search_input.returnPressed.connect(lambda: self._do_search(True))
            if self.replace_input:
                self.replace_input.returnPressed.connect(self._do_replace)
                
        except Exception as e:
            logger.error(f"خطأ في ربط الإشارات: {str(e)}")
            raise SearchError("فشل في ربط الإشارات") from e

    def _do_search(self, forward: bool = True) -> bool:
        """تنفيذ البحث.
        
        Args:
            forward (bool): البحث للأمام
            
        Returns:
            bool: نجاح البحث
        """
        try:
            # التحقق من النص
            text = self.search_input.text().strip()
            if not text:
                log_in_arabic(logger, logging.WARNING, "محاولة بحث بدون نص")
                self._show_error("يجب إدخال نص للبحث")
                return False
                
            # الحصول على المحرر
            text_edit = self.parent.get_current_editor()
            if not text_edit:
                log_in_arabic(logger, logging.WARNING, "محاولة بحث بدون محرر نشط")
                self._show_error("لا يوجد محرر نشط")
                return False

            # إعداد خيارات البحث
            flags = QTextDocument.FindFlags()
            if self.case_sensitive.isChecked():
                flags |= QTextDocument.FindCaseSensitively
            if self.whole_words.isChecked():
                flags |= QTextDocument.FindWholeWords
            if not forward:
                flags |= QTextDocument.FindBackward
                
                # تنفيذ البحث
                if not text_edit.find(text, flags):
                    cursor = text_edit.textCursor()
                    cursor.movePosition(cursor.Start if forward else cursor.End)
                    text_edit.setTextCursor(cursor)
                        
                if not text_edit.find(text, flags):
                    log_in_arabic(logger, logging.INFO, f"لم يتم العثور على النص: {text}")
                    self._show_info("لم يتم العثور على النص المطلوب")
                    return False
                        
                log_in_arabic(logger, logging.INFO, f"تم العثور على النص: {text}")
                return True
            
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تنفيذ البحث: {str(e)}")
            self._show_error("حدث خطأ أثناء البحث")
            return False

    def _do_replace(self):
        """تنفيذ الاستبدال."""
        try:
            if not self.is_replace:
                return
                
            text_edit = self.parent.get_current_editor()
            if not text_edit:
                    log_in_arabic(logger, logging.WARNING, "محاولة استبدال بدون محرر نشط")
                    self._show_error("لا يوجد محرر نشط")
                    return

            if not text_edit.textCursor().hasSelection():
                    log_in_arabic(logger, logging.WARNING, "محاولة استبدال بدون تحديد نص")
                    self._show_error("يجب تحديد نص للاستبدال")
                    return

            # تنفيذ الاستبدال
            old_text = text_edit.textCursor().selectedText()
            new_text = self.replace_input.text()
            text_edit.textCursor().insertText(new_text)
            log_in_arabic(logger, logging.INFO, f"تم استبدال النص '{old_text}' بـ '{new_text}'")
            
            self._do_search(True)
            
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تنفيذ الاستبدال: {str(e)}")
            self._show_error("حدث خطأ أثناء الاستبدال")

    def _do_replace_all(self):
        """تنفيذ استبدال الكل."""
        try:
            if not self.is_replace:
                return
                
            text_edit = self.parent.get_current_editor()
            if not text_edit:
                    log_in_arabic(logger, logging.WARNING, "محاولة استبدال الكل بدون محرر نشط")
                    self._show_error("لا يوجد محرر نشط")
                    return
                
                # بدء عملية الاستبدال
            cursor = text_edit.textCursor()
            cursor.beginEditBlock()
        
            try:
                original_position = cursor.position()
                cursor.movePosition(cursor.Start)
                text_edit.setTextCursor(cursor)
        
                search_text = self.search_input.text()
                replace_text = self.replace_input.text()
                count = 0
                
                while self._do_search(True):
                    text_edit.textCursor().insertText(replace_text)
                    count += 1

                log_in_arabic(logger, logging.INFO, 
                            f"تم استبدال {count} من النصوص '{search_text}' بـ '{replace_text}'")
                self._show_info(f"تم استبدال {count} من النصوص المطابقة")
                
                cursor.setPosition(original_position)
                text_edit.setTextCursor(cursor)
                
            finally:
                cursor.endEditBlock()
            
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تنفيذ استبدال الكل: {str(e)}")
            self._show_error("حدث خطأ أثناء استبدال الكل")

    def _show_error(self, message: str):
        """عرض رسالة خطأ."""
        QMessageBox.critical(self, "خطأ", message)

    def _show_info(self, message: str):
        """عرض رسالة معلومات."""
        QMessageBox.information(self, "معلومات", message)


class SearchManager:
    """مدير البحث والاستبدال في المحرر.
    
    يتحكم هذا المدير في نوافذ البحث والاستبدال ويوفر واجهة موحدة للتعامل معها.
    """
    
    def __init__(self, editor):
        """تهيئة مدير البحث.
        
        Args:
            editor: المحرر الرئيسي
        """
        try:
            self.editor = editor
            self._dialogs = {}
                
        except Exception as e:
            logger.error(f"خطأ في تهيئة مدير البحث: {str(e)}")
            raise SearchError("فشل في تهيئة مدير البحث") from e

    def _get_dialog(self, is_replace: bool) -> SearchDialog:
        """الحصول على نافذة الحوار المناسبة.
        
        Args:
            is_replace (bool): هل المطلوب نافذة استبدال
            
        Returns:
            SearchDialog: نافذة الحوار
        """
        try:
            dialog_type = 'replace' if is_replace else 'search'
            
            if dialog_type not in self._dialogs:
                dialog = SearchDialog(self.editor, is_replace)
                self._dialogs[dialog_type] = dialog
                
            return self._dialogs[dialog_type]
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على نافذة الحوار: {str(e)}")
            raise SearchError("فشل في الحصول على نافذة الحوار") from e

    def _show_dialog(self, is_replace: bool = False):
        """عرض نافذة الحوار.
        
        Args:
            is_replace (bool): هل المطلوب نافذة استبدال
        """
        try:
            # الحصول على النافذة وعرضها
            dialog = self._get_dialog(is_replace)
            dialog.show()
            dialog.search_input.setFocus()

            # تعبئة النص المحدد تلقائياً
            if editor := self.editor.tab_manager.get_current_editor():
                if selected_text := editor.textCursor().selectedText():
                    dialog.search_input.setText(selected_text)
                    dialog.search_input.selectAll()
                    
        except Exception as e:
            logger.error(f"خطأ في عرض نافذة الحوار: {str(e)}")
            QMessageBox.critical(self.editor, "خطأ", "فشل في عرض نافذة البحث")
        
    def show_search_dialog(self):
        """عرض نافذة البحث."""
        try:
            self._show_dialog(False)
        except Exception as e:
            logger.error(f"خطأ في عرض نافذة البحث: {str(e)}")
            QMessageBox.critical(self.editor, "خطأ", "فشل في عرض نافذة البحث")

    def show_replace_dialog(self):
        """عرض نافذة البحث والاستبدال."""
        try:
            self._show_dialog(True)
        except Exception as e:
            logger.error(f"خطأ في عرض نافذة الاستبدال: {str(e)}")
            QMessageBox.critical(self.editor, "خطأ", "فشل في عرض نافذة الاستبدال")

    def goto_line(self):
        """الانتقال إلى سطر محدد."""
        try:
            # الحصول على المحرر الحالي
            if not (editor := self.editor.tab_manager.get_current_editor()):
                QMessageBox.warning(self.editor, "تنبيه", "لا يوجد محرر نشط")
                return
            
            # الحصول على معلومات السطر
            current_line = editor.textCursor().blockNumber() + 1
            max_lines = editor.document().lineCount()

            # عرض مربع حوار لإدخال رقم السطر
            line_number, ok = QInputDialog.getInt(
                self.editor,
                'انتقال إلى سطر',
                'رقم السطر:',
                    value=current_line,
                min=1,
                    max=max_lines
            )
        
            # الانتقال إلى السطر المحدد
            if ok:
                    cursor = editor.textCursor()
                    cursor.movePosition(cursor.Start)
                    cursor.movePosition(cursor.NextBlock, n=line_number-1)
                    editor.setTextCursor(cursor)
                    editor.centerCursor()
                
        except Exception as e:
            logger.error(f"خطأ في الانتقال إلى السطر: {str(e)}")
            QMessageBox.critical(self.editor, "خطأ", "فشل في الانتقال إلى السطر المحدد")