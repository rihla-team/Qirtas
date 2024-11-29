from PyQt5.QtWidgets import QTextEdit, QWidget, QHBoxLayout, QMenu, QAction
from PyQt5.QtGui import QTextOption, QTextCharFormat, QColor, QTextFormat, QTextCursor, QKeySequence
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class ArabicTextEdit(QTextEdit):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_path = None  # إضافة متغير لتخزين مسار الملف
        self._font_update_in_progress = False
        
        # إنشاء الحاوية
        self.container = QWidget()
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        
        # إضافة المحرر للحاوية
        self.container_layout.addWidget(self)
        
        # إعداد المحرر
        self.setup_editor()
        
        # تطبيق الخط الافتراضي
        if hasattr(self.main_window, 'default_font'):
            self.apply_font_direct(self.main_window.default_font)
        
        # إضافة الإشارات
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.document().modificationChanged.connect(self._handle_modification_changed)
        self.document().contentsChange.connect(self._handle_contents_change)
        self.cursorPositionChanged.connect(self._handle_cursor_position_changed)
        self.textChanged.connect(self._handle_text_changed)
        
        # إعداد مؤقت لتحديث الخط
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self._handle_text_changed)
        
        # تفعيل قبول السحب والإفلات
        self.setAcceptDrops(True)

    def get_container(self):
        """الحصول على الحاوية الرئيسية"""
        return self.container

    def setup_editor(self):
        """إعداد المحرر"""
        # إعداد خيارات النص
        options = QTextOption()
        options.setTextDirection(Qt.RightToLeft)
        self.document().setDefaultTextOption(options)
        
        # تعيين نمط المحرر
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                padding: 0;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
        """)
        
        # إزالة هوامش المستند
        self.document().setDocumentMargin(0)

    def apply_font_direct(self, font):
        """تطبيق الخط مباشرة بدون تكرار"""
        if not font or self._font_update_in_progress:
            return
            
        self._font_update_in_progress = True
        try:
            # تعطيل الإشارات مؤقتاً
            self.document().blockSignals(True)
            
            # تطبيق الخط
            self.setFont(font)
            self.document().setDefaultFont(font)
            
            # تطبيق على النص المحدد فقط إذا كان هناك تحديد
            cursor = self.textCursor()
            if cursor.hasSelection():
                format = QTextCharFormat()
                format.setFont(font)
                cursor.mergeCharFormat(format)
                
        finally:
            self.document().blockSignals(False)
            self._font_update_in_progress = False

    def highlight_current_line(self):
        """تمييز السطر الحالي"""
        extraSelections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2d2d2d")  # لون خلفية السطر الحالي
            
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        
        self.setExtraSelections(extraSelections)

    def _handle_modification_changed(self, modified):
        """معالجة تغيير حالة التعديل"""
        editor_window = self.main_window
        
        current_index = editor_window.tab_manager.currentIndex()
        current_title = editor_window.tab_manager.tabText(current_index)
        
        # إزالة علامة * إذا كانت موجودة
        if current_title.endswith('*'):
            current_title = current_title[:-1]
            
        # إضافة علامة * إذا تم التعديل
        if modified:
            current_title += '*'
            # محاولة الحفظ التلقائي
            if hasattr(editor_window, 'auto_saver') and editor_window.auto_saver.enabled:
                editor_window.auto_saver.add_file_to_autosave(
                    editor_window.tab_manager.file_paths[self],
                    self
                )
                
        editor_window.tab_manager.setTabText(current_index, current_title)
        
    def _handle_contents_change(self, position, removed, added):
        """عالجة التغييرات في المحتوى"""
        if removed > 0 or added > 0:  # إذا تم إضافة أو حذف نص
            self.update_timer.start()
            
    def _handle_text_changed(self):
        """معالجة تغيير النص"""
        if not hasattr(self.main_window, 'default_font'):
            return
            
        # تجنب التحديث إذا كان الخط نفسه
        if self.main_window.default_font == self.font():
            return
            
        # تعطيل الإشارات مؤقتاً
        self.document().blockSignals(True)
        
        # تطبيق الخط
        self.setFont(self.main_window.default_font)
        self.document().setDefaultFont(self.main_window.default_font)
        
        # إعادة تفعيل الإشارات
        self.document().blockSignals(False)
        
        # تحديث الإحصائيات
        if hasattr(self.main_window, 'update_status'):
            self.main_window.update_status()
        
    def setPlainText(self, text):
        """تجاوز دالة setPlainText للحفاظ على الخط"""
        super().setPlainText(text)
        self.textChanged.emit()
        
    def clear(self):
        """تجاوز دالة clear للحفاظ على الخط"""
        super().clear()
        self.textChanged.emit()
        
    def insertPlainText(self, text):
        """تجاوز دالة insertPlainText للحفاظ على الخط"""
        super().insertPlainText(text)
        self.textChanged.emit()
        
    def _update_font(self):
        """تحديث الخط"""
        if not hasattr(self.main_window, 'default_font'):
            return
        
        font = self.main_window.default_font
        if font != self.font():
            self.setFont(font)
            self.document().setDefaultFont(font)
            
            # تطبيق على كل النص
            cursor = self.textCursor()
            cursor.select(QTextCursor.Document)
            format = QTextCharFormat()
            format.setFont(font)
            cursor.mergeCharFormat(format)
            self.setTextCursor(cursor)
            
            print(f"تم تحديث الخط إلى: {font.family()}, {font.pointSize()}")

    def update_font_settings(self, font):
        """تحديث إعدادات الخط"""
        print(f"تحديث خط المحرر إلى: {font.family()}, {font.pointSize()}")
        
        # تطبيق الخط على المحرر نفسه
        self.setFont(font)
        
        # تطبيق الخط على كل النص الموجود
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        
        format = QTextCharFormat()
        format.setFont(font)
        cursor.mergeCharFormat(format)
        
        # تعيين الخط الافتراضي للمستند
        self.document().setDefaultFont(font)
        
        # تحديث العرض
        self.viewport().update()
    def _handle_cursor_position_changed(self):
        """معالجة تغيير موقع المؤشر"""
        editor_window = self.main_window
        while not hasattr(editor_window, 'update_cursor_position') and editor_window.parent():
            editor_window = editor_window.parent()
        
        if hasattr(editor_window, 'update_cursor_position'):
            editor_window.update_cursor_position()

    def apply_font(self, font):
        """تطبيق الخط على المحرر والنص"""
        if not font:
            return
        
        self.setFont(font)
        self.document().setDefaultFont(font)
        
        # تطبيق على كل النص
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        format = QTextCharFormat()
        format.setFont(font)
        cursor.mergeCharFormat(format)

    def apply_font_direct(self, font):
        """تطبيق الخط مباشرة بدون تكرار"""
        if not font or font == self.font():
            return
        
        # تعطيل جميع الإشارات المتعلقة بالخط
        self.document().blockSignals(True)
        self.blockSignals(True)
        
        try:
            # تطبيق الخط على المحرر
            self.setFont(font)
            self.document().setDefaultFont(font)
            
            # تطبيق على كل النص
            cursor = self.textCursor()
            cursor.select(QTextCursor.Document)
            format = QTextCharFormat()
            format.setFont(font)
            cursor.mergeCharFormat(format)
            
        finally:
            # إعادة تفعيل الإشارات
            self.document().blockSignals(False)
            self.blockSignals(False)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """معالجة بداية عملية السحب"""
        mime_data = event.mimeData()
        
        # قبول الملفات النصية والنصوص العادية
        if mime_data.hasUrls() or mime_data.hasText():
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event):
        """معالجة حركة السحب"""
        event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        """معالجة عملية الإفلات"""
        mime_data = event.mimeData()
        
        # التعامل مع إفلات الملفات
        if mime_data.hasUrls():
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if file_path:
                    # التحقق من نوع الملف
                    if self._is_text_file(file_path):
                        # فتح الملف في تبويب جديد
                        editor = self.main_window.tab_manager.open_file(file_path)
                        if editor:
                            # تعيين مسار الملف وإطلاق إشارة file_dropped
                            editor.file_path = file_path
                            self.main_window.file_dropped.emit(file_path, editor)
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

    def contextMenuEvent(self, event):
        """إنشاء قائمة السياق عند النقر بزر الماوس الأيمن"""
        context_menu = QMenu(self)
        
        # إضافة الإجراءات الأساسية
        undo_action = QAction('تراجع', self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        undo_action.setEnabled(self.document().isUndoAvailable())
        context_menu.addAction(undo_action)

        redo_action = QAction('إعادة', self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.redo)
        redo_action.setEnabled(self.document().isRedoAvailable())
        context_menu.addAction(redo_action)

        context_menu.addSeparator()

        cut_action = QAction('قص', self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.cut)
        cut_action.setEnabled(self.textCursor().hasSelection())
        context_menu.addAction(cut_action)

        copy_action = QAction('نسخ', self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy)
        copy_action.setEnabled(self.textCursor().hasSelection())
        context_menu.addAction(copy_action)

        paste_action = QAction('لصق', self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste)
        paste_action.setEnabled(self.canPaste())
        context_menu.addAction(paste_action)

        delete_action = QAction('حذف', self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(lambda: self.textCursor().removeSelectedText())
        delete_action.setEnabled(self.textCursor().hasSelection())
        context_menu.addAction(delete_action)

        context_menu.addSeparator()

        select_all_action = QAction('تحديد الكل', self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(self.selectAll)
        context_menu.addAction(select_all_action)

        # إضافة قائمة فرعية للتنسيق
        format_menu = context_menu.addMenu('تنسيق')
        
        bold_action = QAction('عريض', self)
        bold_action.setShortcut(QKeySequence.Bold)
        bold_action.triggered.connect(lambda: self.main_window.format_text('bold'))
        format_menu.addAction(bold_action)

        italic_action = QAction('مائل', self)
        italic_action.setShortcut(QKeySequence.Italic)
        italic_action.triggered.connect(lambda: self.main_window.format_text('italic'))
        format_menu.addAction(italic_action)

        underline_action = QAction('تسطير', self)
        underline_action.setShortcut(QKeySequence.Underline)
        underline_action.triggered.connect(lambda: self.main_window.format_text('underline'))
        format_menu.addAction(underline_action)

        # إضافة قائمة فرعية للتشكيل
        diacritics_menu = context_menu.addMenu('تشكيل')
        
        diacritics = [
            ('َ', 'فتحة'),
            ('ُ', 'ضمة'),
            ('ِ', 'كسرة'),
            ('ْ', 'سكون'),
            ('ّ', 'شدة'),
            ('ً', 'تنوين فتح'),
            ('ٌ', 'تنوين ضم'),
            ('ٍ', 'تنوين كسر')
        ]

        for diacritic, name in diacritics:
            action = QAction(f'{name} ({diacritic})', self)
            action.triggered.connect(lambda checked, d=diacritic: self.add_diacritic(d))
            diacritics_menu.addAction(action)

        # إضافة خيار إزالة التشكيل
        remove_diacritics_action = QAction('إزالة كل التشكيل', self)
        remove_diacritics_action.triggered.connect(self.remove_all_diacritics)
        diacritics_menu.addAction(remove_diacritics_action)

        # عرض القائمة
        context_menu.exec_(event.globalPos())

    def add_diacritic(self, diacritic):
        """إضافة تشكيل للنص المحدد"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            new_text = ""
            for char in text:
                if char.isalpha() and '\u0600' <= char <= '\u06FF':  # التحقق من أن الحرف عربي
                    new_text += char + diacritic
                else:
                    new_text += char
            cursor.insertText(new_text)
        else:
            position = cursor.position()
            cursor.movePosition(cursor.Left)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor)
            char = cursor.selectedText()
            if char.isalpha() and '\u0600' <= char <= '\u06FF':
                cursor.insertText(char + diacritic)
            cursor.setPosition(position + 1)
            self.setTextCursor(cursor)

    def remove_all_diacritics(self):
        """إزالة جميع التشكيلات من النص المحدد"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            from tashaphyne.normalize import strip_tashkeel
            new_text = strip_tashkeel(text)
            cursor.insertText(new_text)


