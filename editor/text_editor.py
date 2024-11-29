from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, 
                           QWidget, QFileDialog, QMessageBox, QAction,
                           QStatusBar,QFontDialog, QMenu, QSplitter, QHBoxLayout, QPushButton, QLabel)  
import os
from PyQt5.QtCore import Qt, pyqtSignal
from .menu_bar import ArabicMenuBar
from utils.theme_manager import ThemeManager
from utils.printer import DocumentPrinter
from utils.pdf_exporter import PDFExporter
from utils.arabic_corrections import ArabicCorrector
from utils.tashkeel import ArabicDiacritics
from utils.setup_shortcuts import ShortcutManager
from utils.text_tools import TextTools
from utils.formatting import TextFormatter
from .settings_manager import SettingsManager
from .tab_manager import TabManager
from utils.auto_save import AutoSaver
from .text_widget import ArabicTextEdit
from utils.statistics_manager import StatisticsManager
from .search_dialog import SearchManager
from .terminal_widget import  TerminalTabWidget
class ArabicEditor(QMainWindow):
    # تعريف الإشارات في بداية الكلاس
    file_opened = pyqtSignal(str, object)
    file_dropped = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        
        # تحميل الخط مرة واحدة عند البداية
        self.default_font = self.settings_manager.get_font()
        
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
        
        # إنشاء الحاوية المركزية
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # إنشاء التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # إضافة شريط القوائم
        self.menu_bar = ArabicMenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # إنشاء مقسم عمودي للمحرر والتيرمنال
        self.main_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(self.main_splitter)
        
        # إضافة مدير التبويبات إلى المقسم
        self.tab_manager = TabManager(self)
        self.main_splitter.addWidget(self.tab_manager)
        
        # إنشاء حاوية التيرمنال (مخفية في البداية)
        self.terminal_container = QWidget()
        self.terminal_container.setVisible(False)
        self.terminal_layout = QVBoxLayout(self.terminal_container)
        self.terminal_layout.setContentsMargins(0, 0, 0, 0)
        self.terminal_layout.setSpacing(0)
        
        # إضافة شريط عنوان التيرمنال
        terminal_header = QWidget()
        terminal_header.setStyleSheet("background-color: #2D2D2D;")
        header_layout = QHBoxLayout(terminal_header)
        header_layout.setContentsMargins(5, 2, 5, 2)
        
        # إضافة عنوان التيرمنال
        terminal_title = QLabel("التيرمنال")
        terminal_title.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(terminal_title)
        
        # إضافة أزرار التحكم
        controls_layout = QHBoxLayout()
        split_btn = QPushButton("تقسيم")
        split_btn.clicked.connect(self.split_terminal)
        minimize_btn = QPushButton("_")
        minimize_btn.clicked.connect(lambda: self.toggle_terminal(False))
        close_btn = QPushButton("×")
        close_btn.clicked.connect(lambda: self.toggle_terminal(False))
        
        for btn in [split_btn, minimize_btn, close_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #ffffff;
                    padding: 2px 8px;
                }
                QPushButton:hover {
                    background: #404040;
                }
            """)
            controls_layout.addWidget(btn)
        
        header_layout.addLayout(controls_layout)
        self.terminal_layout.addWidget(terminal_header)
        
        # إضافة حاوية التيرمنال إلى المقسم
        self.main_splitter.addWidget(self.terminal_container)
        
        # تعيين النسب الافتراضية للمقسم
        self.main_splitter.setStretchFactor(0, 7)  # المحرر
        self.main_splitter.setStretchFactor(1, 3)  # التيرمنال
        
        # إضافة شريط الحالة
        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)
        
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
        export_pdf_action = QAction('تصدير بي دي اف', self)
        export_pdf_action.triggered.connect(self.export_pdf)
        tools_menu.addAction(export_pdf_action)
        
        tools_menu = self.menuBar().findChild(QMenu, 'أدوات')
        if tools_menu:
            terminal_action = QAction('فتح التيرمنال', self)
            terminal_action.setShortcut('Ctrl+T')
            terminal_action.triggered.connect(self.add_terminal)
            tools_menu.addAction(terminal_action)
        
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

    def open_file(self, file_path):
        """فتح ملف"""
        if file_path:
            self.tab_manager.open_file(file_path)
            self.file_opened.emit(file_path, self.get_current_editor())

    def save_file(self):
        """حفظ الملف الحالي"""
        current_editor = self.tab_manager.get_current_editor()
        if not current_editor:
            return False
            
        # التحقق من وجود مسار للملف
        if hasattr(current_editor, 'file_path') and current_editor.file_path:
            file_path = current_editor.file_path
        else:
            return self.save_file_as()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(current_editor.toPlainText())
            current_editor.document().setModified(False)
            self.statusBar().showMessage(f"تم الحفظ: {file_path}", 2000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ الملف: {str(e)}")
            return False

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
                
                # إنشاء مربع حوار مخصص
                msg_box = QMessageBox()
                msg_box.setWindowTitle("تنبيه")
                msg_box.setText(f"هناك تغييرات غير محفوظة في {file_name}. هل تريد حفظها؟")
                
                # إضافة الأزرار المعربة
                save_button = msg_box.addButton("حفظ", QMessageBox.AcceptRole)
                discard_button = msg_box.addButton("تجاهل", QMessageBox.DestructiveRole)
                cancel_button = msg_box.addButton("إلغاء", QMessageBox.RejectRole)
                
                msg_box.exec_()
                
                clicked_button = msg_box.clickedButton()
                
                if clicked_button == save_button:
                    # تفعيل التبويب الحالي
                    self.tab_manager.setCurrentIndex(index)
                    if not self.save_file():
                        event.ignore()
                        return
                elif clicked_button == cancel_button:
                    event.ignore()
                    return
                # في حالة تجاهل، نستمر في الحلقة
        
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
            
    def add_terminal(self):
        """إضافة تيرمنال جديد"""
        # التحقق من وجود تيرمنال مفتوح
        if hasattr(self, 'terminal_container') and self.terminal_container.isVisible():
            # إضافة تبويب جديد إذا كان التيرمنال موجوداً
            if hasattr(self, 'terminal_tabs'):
                self.terminal_tabs.add_new_terminal()
            return
        
        # إنشاء حاوية التيرمنال إذا لم تكن موجودة
        if not hasattr(self, 'terminal_container'):
            self.terminal_container = QWidget()
            self.terminal_layout = QVBoxLayout(self.terminal_container)
            self.terminal_layout.setContentsMargins(0, 0, 0, 0)
            self.terminal_layout.setSpacing(0)
            self.main_splitter.addWidget(self.terminal_container)
        
        # إزالة أي تيرمنالات قديمة
        for i in reversed(range(self.terminal_layout.count())):
            widget = self.terminal_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
                self.terminal_layout.removeWidget(widget)
        
        # إنشاء مدير التبويبات
        self.terminal_tabs = TerminalTabWidget(self)
        self.terminal_layout.addWidget(self.terminal_tabs)
        
        # إظهار التيرمنال
        self.toggle_terminal(True)
        
        return self.terminal_tabs.get_current_terminal()

    def toggle_terminal(self, show=None):
        """إظهار/إخفاء التيرمنال"""
        if not hasattr(self, 'terminal_container'):
            if show:
                self.add_terminal()
            return
        
        if show is None:
            show = not self.terminal_container.isVisible()
        
        self.terminal_container.setVisible(show)
        
        # إعادة ضبط أحجام المقسم
        if show:
            sizes = self.main_splitter.sizes()
            total = sum(sizes)
            self.main_splitter.setSizes([int(total * 0.7), int(total * 0.3)])
        else:
            self.main_splitter.setSizes([1, 0])

    def split_terminal(self):
        """تقسيم التيرمنال"""
        if hasattr(self, 'terminal_tabs'):
            self.terminal_tabs.add_new_terminal()

    def load_font_settings(self):

        """تحميل إعدادات الخط"""
        if self.parent and self.parent.get_current_editor():
            current_editor = self.parent.get_current_editor()
            font = self.parent.default_font
        
        