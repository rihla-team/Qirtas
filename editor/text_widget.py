from PyQt5.QtWidgets import QTextEdit, QWidget, QHBoxLayout, QMenu, QAction, QFileDialog, QMessageBox
from PyQt5.QtGui import QTextOption, QTextCharFormat, QColor, QTextCursor, QKeySequence
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from utils.syntax_highlighter import CodeHighlighter
import os

class ArabicTextEdit(QTextEdit):
    file_type_changed = pyqtSignal(str)  # إشارة عند تغيير نوع الملف

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.file_path = None

        # إنشاء الحاوية
        self.container = QWidget()
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.addWidget(self)

        # إعدادات المحرر
        self.setup_editor()
        self.setup_signals_and_timers()

        # تخصيص التمييز اللغوي
        self.highlighter = CodeHighlighter(self.document())
        self._file_type_update_timer = QTimer()
        self._file_type_update_timer.setSingleShot(True)
        self._file_type_update_timer.setInterval(5000) 
        
        
    def setup_editor(self):
        """إعدادات المحرر الأساسية."""
        options = QTextOption()
        options.setTextDirection(Qt.RightToLeft)  # تثبيت الاتجاه من اليمين إلى اليسار
        self.document().setDefaultTextOption(options)

        self.setCurrentCharFormat(QTextCharFormat())
        self.setAcceptRichText(True)

    def setup_signals_and_timers(self):
        """إعداد الإشارات والمؤقتات."""
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self.on_text_changed)

        # مؤقت تحسين الذاكرة
        self.memory_timer = QTimer()
        self.memory_timer.setInterval(300000)  # كل 5 دقائق
        self.memory_timer.timeout.connect(self.optimize_memory)
        self.memory_timer.start()

        # مؤقت تحديث نوع الملف
        self._file_type_update_timer = QTimer()
        self._file_type_update_timer.setSingleShot(True)
        self._file_type_update_timer.setInterval(5000)
        self._file_type_update_timer.timeout.connect(self.update_file_type)

    def highlight_current_line(self):
        """تمييز السطر الحالي."""
        if self.isReadOnly():
            return

        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor("#2d2d2d"))
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def optimize_memory(self):
        """تحسين استخدام الموارد."""
        self.document().clearUndoRedoStacks()
        self.document().setUndoRedoEnabled(False)
        self.document().setUndoRedoEnabled(True)

    def start_timer(self, timer):
        """تشغيل مؤقت محدد."""
        if not timer.isActive():
            timer.start()

    def add_diacritic(self, diacritic):
        """إضافة تشكيل للنص المحدد."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            new_text = ''.join(
                char + diacritic if char.isalpha() and '؀' <= char <= 'ۿ' else char
                for char in text
            )
            cursor.insertText(new_text)
        else:
            cursor.insertText(diacritic)

    def remove_all_diacritics(self):
        """إزالة جميع التشكيلات."""
        from tashaphyne.normalize import strip_tashkeel
        cursor = self.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(strip_tashkeel(text))

    def update_file_type(self):
        """تحديث نوع الملف."""
        file_type = self.highlighter.get_file_type()
        self.file_type_changed.emit(file_type)

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
        
        alignment_menu = format_menu.addMenu('محاذاة')
        
        right_align = QAction('محاذاة لليمين', self)
        right_align.setShortcut('Ctrl+Shift+R')
        right_align.triggered.connect(lambda: self.main_window.format_text('align_right'))
        alignment_menu.addAction(right_align)

        # محاذاة لليسار
        left_align = QAction('محاذاة لليسار', self)
        left_align.setShortcut('Ctrl+Shift+L')
        left_align.triggered.connect(lambda: self.main_window.format_text('align_left'))
        alignment_menu.addAction(left_align)

        # توسيط
        center_align = QAction('توسيط', self)
        center_align.setShortcut('Ctrl+Shift+E')
        center_align.triggered.connect(lambda: self.main_window.format_text('align_center'))
        alignment_menu.addAction(center_align)

        # ضبط
        justify_align = QAction('ضبط', self)
        justify_align.setShortcut('Ctrl+Shift+J')
        justify_align.triggered.connect(lambda: self.main_window.format_text('align_justify'))
        alignment_menu.addAction(justify_align)

        # إضافة قائمة فرعية للتشكيل
        diacritics_menu = context_menu.addMenu('تشكيل')
        
        # قائمة الحركات الأساسية
        basic_marks = diacritics_menu.addMenu('الحركات الأساسية')
        basic_marks_list = [
            ('َ', 'فتحة'),
            ('ُ', 'ضمة'),
            ('ِ', 'كسرة'),
            ('ْ', 'سكون'),
            ('ّ', 'شدة'),
        ]

        # قائمة التنوين
        tanween_menu = diacritics_menu.addMenu('علامات التنوين')
        tanween_list = [
            ('ً', 'تنوين فتح'),
            ('ٌ', 'تنوين ضم'),
            ('ٍ', 'تنوين كسر'),
        ]

        # قائمة الهمزات - مع إضافات
        hamza_menu = diacritics_menu.addMenu('الهمزات')
        hamza_list = [
            ('ٔ', 'همزة فوق'),
            ('ٕ', 'همزة تحت'),
            ('ء', 'همزة منفردة'),
            ('أ', 'همزة على الألف'),
            ('إ', 'همزة تحت الألف'),
            ('ؤ', 'همزة على الواو'),
            ('ئ', 'همزة على الياء'),
        ]

        # قائمة المدود - مع إضافات
        madd_menu = diacritics_menu.addMenu('علامات المد')
        madd_list = [
            ('ٓ', 'إشارة مد'),
            ('ـ', 'شريط مطول'),
            ('ۤ', 'علامة المد المتصل'),
            ('ۥ', 'علامة المد المنفصل'),
            ('ۦ', 'علامة المد اللازم'),
            ('ۧ', 'علامة المد العارض للسكون'),
            ('ۨ', 'علامة المد الصلة'),
            ('آ', 'ألف ممدودة'),
            ('ٱ', 'ألف الوصل'),
        ]

        # قائمة علامات الوقف - مع إضافات
        waqf_menu = diacritics_menu.addMenu('علامات الوقف')
        waqf_list = [
            ('ۖ', 'وقف - الوصل أولى'),
            ('ۗ', 'وقف - الوقف أولى'),
            ('ۘ', 'وقف لازم'),
            ('ۙ', 'ممنوع الوقف'),
            ('ۚ', 'جائز الوقف'),
            ('ۛ', 'وقف معانقة'),
            ('ۜ', 'وقف مع سكت'),
            ('۠', 'علامة الوقف اللازم'),
            ('ۡ', 'علامة السكتة الخفيفة'),
            ('؞', 'علامة وقف التام'),
            ('؟', 'علامة الوقف الاختياري'),
            ('٪', 'علامة الوقف المؤقت'),
        ]

        # قائمة العلامات الصوتية - مع إضافات
        phonetic_menu = diacritics_menu.addMenu('العلامات الصوتية')
        phonetic_list = [
            ('۪', 'علامة التفخيم'),
            ('۫', 'علامة الترقيق'),
            ('۬', 'علامة الإمالة'),
            ('ۭ', 'علامة الإشمام'),
            ('ۮ', 'علامة الإخفاء'),
            ('ۯ', 'علامة الإدغام'),
            ('ۢ', 'علامة الإقلاب'),
            ('ۣ', 'علامة الإظهار'),
            ('͗', 'علامة التسهيل'),
            ('͑', 'علامة التحقيق'),
            ('᷄', 'علامة النبر القوي'),
            ('᷅', 'علامة النبر الضعيف'),
            ('᷆', 'علامة النبر المتوسط'),
            ('᷇', 'علامة النبر المنخفض'),
            ('᷈', 'علامة النبر المتغير'),
            ('᷉', 'علامة النبر الصاعد'),
        ]

        # قائمة الرموز الخاصة - مع إضافات
        special_menu = diacritics_menu.addMenu('رموز خاصة')
        special_list = [
            ('۝', 'رمز نهاية الآية'),
            ('۞', 'رمز بداية السورة'),
            ('۩', 'رمز السجدة'),
            ('ٰ', 'ألف خنجرية'),
            ('﷽', 'البسملة'),
            ('﷼', 'رمز الريال'),
            ('؎', 'رمز الصلاة على النبي'),
            ('؏', 'رمز عليه السلام'),
            ('۞', 'رمز الحزب'),
            ('۩', 'رمز السجدة'),
            ('ﷺ', 'صلى الله عليه وسلم'),
            ('ﷻ', 'جل جلاله'),
            ('ﷲ', 'لفظ الجلالة'),
            ('﴾', 'قوس قرآني أيمن'),
            ('﴿', 'قوس قرآني أيسر'),
        ]

        # قائمة الحركات المقلوبة - مع إضافات
        inverted_menu = diacritics_menu.addMenu('الحركات المقلوبة')
        inverted_list = [
            ('ٖ', 'كسرة مقلوبة'),
            ('ٗ', 'ضمة مقلوبة'),
            ('٘', 'فتحة مقلوبة'),
            ('ٙ', 'تنوين مقلوب'),
            ('ٚ', 'سكون مقلوب'),
        ]

        # قائمة جديدة: علامات التجويد
        tajweed_menu = diacritics_menu.addMenu('علامات التجويد')
        tajweed_list = [
            ('۟', 'علامة الإدغام الشفوي'),
            ('۠', 'علامة الإدغام المتماثل'),
            ('ۡ', 'علامة الإدغام المتجانس'),
            ('ۢ', 'علامة الإدغام المتقارب'),
            ('ۤ', 'علامة المد الطبيعي'),
            ('ۧ', 'علامة القلقلة'),
            ('ۨ', 'علامة التفخيم المطلق'),
        ]

        # قائمة جديدة: علامات الضبط المصحفي
        mushaf_menu = diacritics_menu.addMenu('علامات الضبط المصحفي')
        mushaf_list = [
            ('۽', 'علامة الروم'),
            ('۾', 'علامة الإشمام'),
            ('ۿ', 'علامة التسهيل'),
            ('ٜ', 'علامة التخفيف'),
            ('ٝ', 'علامة التثقيل'),
            ('ٞ', 'علامة التوسط'),
        ]

        # دالة مساعدة لإضافة العناصر إلى القائمة
        def add_menu_items(menu, items):
            for mark, name in items:
                action = QAction(f'{name} ({mark})', self)
                action.triggered.connect(lambda checked, d=mark: self.add_diacritic(d))
                menu.addAction(action)

        # إضافة جميع العناصر إلى القوائم الفرعية
        add_menu_items(basic_marks, basic_marks_list)
        add_menu_items(tanween_menu, tanween_list)
        add_menu_items(hamza_menu, hamza_list)
        add_menu_items(madd_menu, madd_list)
        add_menu_items(waqf_menu, waqf_list)
        add_menu_items(phonetic_menu, phonetic_list)
        add_menu_items(special_menu, special_list)
        add_menu_items(inverted_menu, inverted_list)
        add_menu_items(tajweed_menu, tajweed_list)
        add_menu_items(mushaf_menu, mushaf_list)

        # إضافة خيار إزالة التشكيل في نهاية القائمة الرئيسية
        diacritics_menu.addSeparator()
        remove_diacritics_action = QAction('إزالة كل التشكيل', self)
        remove_diacritics_action.triggered.connect(self.remove_all_diacritics)
        diacritics_menu.addAction(remove_diacritics_action)
        if hasattr(self.main_window, 'extensions_manager'):
            extension_items = self.main_window.extensions_manager.get_context_menu_items()
            
            if extension_items:
                context_menu.addSeparator()
                extensions_menu = {}
                
                for item in extension_items:
                    ext_id = item.get('extension_id', '')
                    
                    # تحقق من وجود معرف الملحق قبل استخدامه
                    if ext_id and ext_id in self.main_window.extensions_manager.extensions:
                        if ext_id not in extensions_menu:
                            ext_name = self.main_window.extensions_manager.extensions[ext_id]['manifest'].get('name', ext_id)
                            extensions_menu[ext_id] = context_menu.addMenu(ext_name)
                        
                        action = self.main_window.extensions_manager.create_context_menu_action(item, extensions_menu[ext_id])
                        extensions_menu[ext_id].addAction(action)
                    
        # عرض القائمة
        context_menu.exec_(event.globalPos())
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
            
    def get_container(self):
        """إرجاع الحاوية التي تحتوي على المحرر."""
        return self.container
    def apply_font(self, font):
        """تطبيق الخط على المحرر و��لنص."""
        if not font:
            return

        # تطبيق الخط على المحرر
        self.setFont(font)
        self.document().setDefaultFont(font)

        # تطبيق على كل النص
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        format = QTextCharFormat()
        format.setFont(font)
        cursor.mergeCharFormat(format)

    def load_file_with_hidden_char(self, file_path):
        """تحميل الملف وإضافة حرف خفي بعد علامات التنصيص في نهاية السطر."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # إضافة الحرف الخفي بعد علامات التنصيص في نهاية السطر
            modified_content = self.add_hidden_char_after_quotes(content)
            self.setPlainText(modified_content)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل الملف: {str(e)}")

    def add_hidden_char_after_quotes(self, text):
        """إضافة حرف خفي بعد علامات التنصيص في نهاية السطر."""
        lines = text.split('\n')
        modified_lines = []
        for line in lines:
            if line.strip().endswith('"'):
                line += '\u200E'  # إضافة الحرف الخفي
            modified_lines.append(line)
        return '\n'.join(modified_lines)

    def on_text_changed(self):
        """معالجة التغييرات في النص."""
        text = self.toPlainText()
        modified_text = self.add_hidden_char_after_quotes(text)
        if text != modified_text:
            self.blockSignals(True)  # منع الإشارات لتجنب التكرار
            self.setPlainText(modified_text)
            self.blockSignals(False)
        self.start_timer(self._file_type_update_timer)
