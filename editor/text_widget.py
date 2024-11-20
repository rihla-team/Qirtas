from PyQt5.QtWidgets import QTextEdit, QWidget, QHBoxLayout
from PyQt5.QtGui import QTextOption, QTextCharFormat, QPainter, QColor, QTextFormat, QTextBlockFormat, QTextCursor
from PyQt5.QtCore import Qt, QTimer, QRect, QSize
from PyQt5.QtGui import QFont, QPen , QTextDocument

class ArabicTextEdit(QTextEdit):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
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
        while not hasattr(editor_window, 'auto_saver') and editor_window.parent():
            editor_window = editor_window.parent()
        
        if not hasattr(editor_window, 'auto_saver'):
            return
        
        current_index = editor_window.tab_manager.currentIndex()
        current_title = editor_window.tab_manager.tabText(current_index)
        
        # إزالة علامة * إذا كانت موجودة
        if current_title.endswith('*'):
            current_title = current_title[:-1]
            
        # إضافة علامة * إذا تم التعديل
        if modified:
            current_title += '*'
            # محاولة الحفظ التلقائي
            if editor_window.auto_saver.enabled:
                QTimer.singleShot(1000, editor_window.auto_saver.perform_auto_save)
                
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


