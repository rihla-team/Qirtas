from PyQt5.QtWidgets import (QMainWindow, QTextEdit, QVBoxLayout, 
                           QWidget, QFileDialog, QMessageBox, QAction,
                           QStatusBar, QLabel, QInputDialog, QFontDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QTextOption, QKeySequence, QTextCursor,QTextCharFormat
from .menu_bar import ArabicMenuBar
from utils.theme_manager import ThemeManager
from utils.printer import DocumentPrinter
from .search_dialog import SearchDialog, ReplaceDialog
from utils.pdf_exporter import PDFExporter
from utils.arabic_corrections import ArabicCorrector
from utils.tashkeel import ArabicDiacritics
from utils.setup_shortcuts import ShortcutManager
from utils.text_tools import TextTools
from utils.formatting import TextFormatter
from PyQt5.QtCore import QSettings
import os
from .settings_manager import SettingsManager
from .tab_manager import TabManager
from utils.auto_save import AutoSaver
from .text_widget import ArabicTextEdit
from utils.statistics_manager import StatisticsManager
from .search_dialog import SearchManager
class ArabicEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        
        # تحميل الخط مرة واحدة عند البداية
        self.default_font = self.settings_manager.get_font()
        print(f"تم تحميل الخط الافتراضي: {self.default_font.family()}, {self.default_font.pointSize()}")
        
        # إنشاء tab_manager
        self.tab_manager = TabManager(self)
        self.setCentralWidget(self.tab_manager)
        
        # تطبيق الخط بعد إنشاء التبويب الأول
        self.new_file()
        
        # تطبيق الخط مباشرة على المحرر الحالي
        current_editor = self.tab_manager.get_current_editor()
        if current_editor:
            current_editor.apply_font_direct(self.default_font)
        
        # ثم إنشاء auto_saver
        self.auto_saver = AutoSaver(self)
        
        # باقي التهيئة
        self.search_dialog = None
        self.replace_dialog = None
        self.text_formatter = TextFormatter(self)
        self.current_file = None
        self.auto_correct_enabled = False
        self.auto_corrector = ArabicCorrector(self)
        self.text_tools = TextTools(self)
        self.theme_manager = ThemeManager()
        self.printer = DocumentPrinter(self)
        self.shortcut_manager = ShortcutManager(self)
        self.search_manager = SearchManager(self)
        
        # تهيئة الواجهة
        self.init_ui()
        self.shortcut_manager.setup_all_shortcuts()
        
        # تطبيق الخط عند بدء التشغيل
        self.apply_font_settings()
        
    def init_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle('محرر النصوص العربي')
        self.setGeometry(100, 100, 800, 600)
        
        # إنشاء مدير التبويب
        self.tab_manager = TabManager(self)
        
        # إضافة شريط القوائم
        self.menu_bar = ArabicMenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # إعداد الواجهة الرئيسية
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tab_manager)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # إضافة شريط الحالة
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # إنشاء مدير الإحصائيات
        self.statistics_manager = StatisticsManager(self.status_bar)
        
        # ربط تحديث الإحصائيات
        self.tab_manager.currentChanged.connect(self.update_status)
        
        # تحديث الإحصائيات الأولية
        self.update_status()

        # إضافة قائمة الأدوات
        tools_menu = self.menuBar().addMenu('أدوات')
        
        # إضافة القوالب
        templates_menu = tools_menu.addMenu('قوالب')
        templates = [
            'رسالة رسمية',
            'مقال',
            'تقرير',
            'محضر اجتماع'
        ]
        
        for template in templates:
            action = QAction(template, self)
            action.triggered.connect(
                lambda checked, t=template: self.insert_template(t)
            )
            templates_menu.addAction(action)

        # إضافة الأدوات العربية
        arabic_tools = tools_menu.addMenu('أدوت عربية')
        
        # تحويل الأرقام
        numbers_menu = arabic_tools.addMenu('تحويل الأرقام')
        to_arabic = QAction('تحويل إلى أرقام عربية', self)
        to_arabic.triggered.connect(lambda: self.convert_numbers('arabic'))
        numbers_menu.addAction(to_arabic)
        
        to_english = QAction('تحويل إلى أرقام إنجليزية', self)
        to_english.triggered.connect(lambda: self.convert_numbers('english'))
        numbers_menu.addAction(to_english)
                
        # التشكيل
        diacritics = ArabicDiacritics()
        diacritics_menu = arabic_tools.addMenu('تشكيل')
        for diacritic, name in diacritics.diacritics_buttons:
            action = QAction(f'{name} ({diacritic})', self)
            action.triggered.connect(
                lambda checked, d=diacritic: self.add_diacritic(d)
            )
            diacritics_menu.addAction(action)
            
        # التصحيح التلقائي
        auto_correct = QAction('تصحيح تلقائي', self)
        auto_correct.setCheckable(True)
        auto_correct.triggered.connect(self.toggle_auto_correct)
        arabic_tools.addAction(auto_correct)
        
        # تصدير PDF
        export_pdf_action = QAction('تصدير PDF', self)
        export_pdf_action.triggered.connect(self.export_pdf)
        tools_menu.addAction(export_pdf_action)
        
    def update_status(self):
        """تحديث إحصائيات النص في شريط الحالة"""
        current_editor = self.get_current_editor()
        if not current_editor:
            self.statistics_manager.update_statistics("", {
                'line': 1,
                'column': 1
            })
            return
        
        text = current_editor.toPlainText()
        cursor = current_editor.textCursor()
        cursor_info = {
            'line': cursor.blockNumber() + 1,
            'column': cursor.columnNumber() + 1
        }
        
        self.statistics_manager.update_statistics(text, cursor_info)

    def get_current_editor(self):
        """الحصول لى المحرر النش حالياً"""
        return self.tab_manager.get_current_editor()

    def new_file(self):
        self.tab_manager.new_tab()

    def open_file(self):
        """فتح ملف"""
        file_name, _ = QFileDialog.getOpenFileName(self, "فتح ملف", "", 
                                                 "كل الملفات (*);;ملفات نصية (*.txt)")
        if file_name:
            self.tab_manager.open_file(file_name)

    def save_file(self):
        """حفظ الملف الحالي"""
        current_tab_index = self.tab_manager.currentIndex()
        current_file = self.tab_manager.get_file_path(current_tab_index)
        
        if not current_file:
            return self.save_file_as()
        
        return self._save_to_file(current_file)

    def save_file_as(self):
        """حفظ الملف باسم جديد"""
        file_name, _ = QFileDialog.getSaveFileName(self, "حفظ الملف", "", 
                                                 "كل الملفات (*);;ملفات نصية (*.txt)")
        if file_name:
            current_tab_index = self.tab_manager.currentIndex()
            self.tab_manager.set_file_path(current_tab_index, file_name)
            if self._save_to_file(file_name):
                self.tab_manager.setTabText(current_tab_index, os.path.basename(file_name))
                return True
        return False

    def _save_to_file(self, file_name):
        """حفظ المحتوى إلى ملف"""
        current_editor = self.get_current_editor()
        if not current_editor:
            return False
        
        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(current_editor.toPlainText())
            current_editor.document().setModified(False)
            self.statusBar().showMessage(f"تم الحفظ: {file_name}", 2000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ الملف: {str(e)}")
            return False

    def show_search_dialog(self):
        """عرض نافذة البحث"""
        self.search_manager.show_search_dialog()

    def show_replace_dialog(self):
        """عرض نافذة البحث والاستبدال"""
        self.search_manager.show_replace_dialog()

    def goto_line(self):
        """الانتقال إلى سطر محدد"""
        self.search_manager.goto_line()

    def find_next(self):
        """البحث عن التطابق التلي"""
        if self.search_dialog and self.search_dialog.last_search:
            self.search_dialog.find()

    def find_previous(self):
        """البحث عن التطابق السابق"""
        if self.search_dialog and self.search_dialog.last_search:
            self.search_dialog.find(backward=True)

    def export_pdf(self):
        if not self.current_file:
            file_name, _ = QFileDialog.getSaveFileName(self, 
                "حفظ كملف PDF", "", 
                "ملفات PDF (*.pdf)")
        else:
            file_name = self.current_file.replace('.txt', '.pdf')
            
        if file_name:
            if not file_name.endswith('.pdf'):
                file_name += '.pdf'
            PDFExporter.export_to_pdf(self.tab_manager.get_current_editor().toPlainText(), file_name)
            QMessageBox.information(self, "تم التصدير", 
                                  "تم تصدير الملف بنجاح إلى PDF")

    def toggle_auto_correct(self, enabled):
        """تفعيل/عطيل التصحيح التلقائي"""
        self.auto_corrector.toggle(enabled)

    def convert_numbers(self, to_type):
        """تحويل الأرقام بين العربية والإنجليزية"""
        self.text_tools.convert_numbers(to_type)

    def add_diacritic(self, diacritic):
        """إضافة تشكيل للنص المحدد"""
        current_editor = self.tab_manager.get_current_editor()
        if not current_editor:
            return
        
        cursor = current_editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(text + diacritic)

    def insert_template(self, template):
        """إدراج قالب نص"""
        current_editor = self.tab_manager.get_current_editor()
        if not current_editor:
            return
        
        if hasattr(self.text_formatter, 'ARABIC_TEMPLATES'):
            template_text = self.text_formatter.ARABIC_TEMPLATES.get(template, '')
            if template_text:
                cursor = current_editor.textCursor()
                cursor.insertText(template_text)
                current_editor.setFocus()

    def apply_arabic_format(self, size, bold=False):
        """تطبيق تنسيق عربي محدد"""
        self.text_formatter.format_text('size', size=size)
        if bold:
            self.text_formatter.format_text('bold')

    def apply_font_settings(self):
        """تطبيق إعدادات الخط على المحرر"""
        if not hasattr(self, 'default_font'):
            return
            
        current_editor = self.get_current_editor()
        if current_editor:
            current_editor.apply_font_direct(self.default_font)

    def update_cursor_position(self):
        """تحديث موقع المؤشر في شريط الحالة"""
        current_editor = self.get_current_editor()
        if not current_editor:
            return
        
        cursor = current_editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        
        cursor_info = {
            'line': line,
            'column': column
        }
        
        self.statistics_manager.update_statistics(cursor_info=cursor_info)

    def format_text(self, format_type):
        """تنسيق النص المحدد"""
        self.text_formatter.format_text(format_type)

    def closeEvent(self, event):
        """معالجة إغلاق النافذة"""
        # التحقق من جميع التبويبات المفتوحة
        for index in range(self.tab_manager.count()):
            text_edit = self.tab_manager.widget(index).findChild(ArabicTextEdit)
            if text_edit and text_edit.document().isModified():
                file_name = self.tab_manager.tabText(index)
                reply = QMessageBox.question(
                    self,
                    "حفظ التغييرات",
                    f"هناك تغييرات غير محفوظة في {file_name}. هل تريد حفظها؟",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    # تفعيل التبويب الحالي
                    self.tab_manager.setCurrentIndex(index)
                    if not self.save_file():
                        event.ignore()
                        return
                elif reply == QMessageBox.Cancel:
                    event.ignore()
                    return
        
        event.accept()

    def maybe_save(self):
        """التحقق من حفظ التغييرات قبل الإغلاق"""
        current_editor = self.tab_manager.get_current_editor()
        if not current_editor:
            return True
        
        if not current_editor.document().isModified():
            return True
        
        from PyQt5.QtWidgets import QMessageBox
        ret = QMessageBox.warning(
            self,
            "محرر رحلة",
            "تم تعديل المستند.\nهل تريد حفظ التغييرات؟",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        
        if ret == QMessageBox.Save:
            # حفظ الملف
            if hasattr(self, 'save_file'):
                return self.save_file()
            return True
        elif ret == QMessageBox.Cancel:
            return False
        
        return True

    def change_font(self):
        """تغيير خط المحرر"""
        current_font = self.settings_manager.get_font()
        font, ok = QFontDialog.getFont(current_font, self)
        
        if ok:
            self.default_font = font
            self.settings_manager.save_font(font)
            
            # تطبيق على جميع المحررات المفتوحة
            for i in range(self.tab_manager.count()):
                editor = self.tab_manager.widget(i).findChild(ArabicTextEdit)
                if editor:
                    editor.apply_font_direct(font)
            