from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, 
                           QWidget, QFileDialog, QMessageBox, QAction,
                           QStatusBar,QFontDialog, QTextEdit, QSplitter, QHBoxLayout, QPushButton, QLabel,QToolBar, QDockWidget, QStackedWidget, QProgressDialog
                           )  
from PyQt5.QtGui import QTextCharFormat
import os
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from .menu_bar import ArabicMenuBar
from utils.printer import DocumentPrinter
from utils.pdf_exporter import PDFExporter
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
from utils.extensions_manager import ExtensionsManager
from utils.sidebar_manager import SidebarManager
from utils.update_manager import UpdateManager
from utils.file_watcher import FileWatcher
class ArabicEditor(QMainWindow):
    # تعريف الإشارات في بداية الكلاس
    file_opened = pyqtSignal(str, object)
    file_dropped = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        # إضافة مدير التحديثات
        self.update_manager = UpdateManager()
        self.settings_manager = SettingsManager()
        
        # ربط إشارة التحديث المتوفر
        self.update_manager.update_available.connect(self.show_update_notification)
        
        # تهيئة مدير الاختصارات قبل تحميل الملحقات
        self.shortcut_manager = ShortcutManager(self)
        
        # تهيئة مدير الشريط الجانبي
        self.sidebar_manager = SidebarManager(self)
        QTimer.singleShot(100, self._setup_sidebar)
        
        # ثم تهيئة مدير الملحقات
        self.extensions_manager = ExtensionsManager(self)
        
        # باقي التهيئة
        self.init_ui()
        
        # إعداد الاختصارات مرة واحدة فقط بعد تحميل كل شيء
        QTimer.singleShot(100, self._setup_shortcuts)
        
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
        self.auto_saver.enabled = True  # تفعيل الحفظ التلقائي افتراضياً
        
        # باقي التهيئة
        self.search_dialog = None
        self.replace_dialog = None
        self.text_formatter = TextFormatter(self)
        self.current_file = None
        self.auto_correct_enabled = False
        self.text_tools = TextTools(self)
        self.printer = DocumentPrinter(self)
        self.search_manager = SearchManager(self)
        
        # تهيئة الواجهة
        self.init_ui()
        self.shortcut_manager.setup_all_shortcuts()
        
        # تطبيق الخط عند بدء التشغيل
        self.apply_font_settings()
        
        # إضافة مراقبة الملفات
        self.file_watcher = FileWatcher()
        self.initialize_settings()
        # ربط إشارات المراقبة مع المحرر
        self.file_watcher.content_changed.connect(self._on_external_content_changed)
        
    def _setup_shortcuts(self):
        """إعداد الاختصارات مرة واحدة"""
        if not hasattr(self, '_shortcuts_setup'):
            self.shortcut_manager.setup_all_shortcuts()
            self._shortcuts_setup = True
    def _setup_sidebar(self):
        """إعداد الشريط الجانبي مرة واحدة"""
        if not hasattr(self, '_sidebar_setup'):
            self.sidebar_manager.setup_sidebar()
            self._sidebar_setup = True
        
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
        split_btn = QPushButton("تقسم")
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
        
        # تحديث طريقة ربط الإشارات
        self.tab_manager.currentChanged.connect(self.on_tab_changed)
        
        # تحديث الإحصائيات الأولية
        self.update_status()
        
        # إضافة قائمة لأدوات
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

            
        # التصحيح التلقائي

        # تصدير PDF
        export_pdf_action = QAction('تصدير بي دي اف', self)
        export_pdf_action.triggered.connect(self.export_pdf)
        tools_menu.addAction(export_pdf_action)
        
        editor_menu = self.menuBar().addMenu('المحرر')
        
        new_text_action = QAction('محرر نصي جديد', self)
        new_text_action.setShortcut('Ctrl+MN')
        new_text_action.triggered.connect(lambda: self.tab_manager.new_tab("text"))
        editor_menu.addAction(new_text_action)
        
        new_scintilla_action = QAction('محرر Scintilla جديد', self)
        new_scintilla_action.setShortcut('Ctrl+Alt+S')
        new_scintilla_action.triggered.connect(lambda: self.tab_manager.new_tab("scintilla"))
        editor_menu.addAction(new_scintilla_action)


        # محاذاة النص

        
    def init_status_bar(self):
        """تهيئة شريط الحالة"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # إضافة تصنيف لنوع الملف
        self.file_type_label = QLabel("نوع الملف: نص عادي")
        self.file_type_label.setStyleSheet("padding: 0 10px;")
        self.statusBar.addPermanentWidget(self.file_type_label)
        
    def connect_editor_signals(self, editor):
        """ربط إشارات المحرر"""
        editor.cursorPositionChanged.connect(self.update_cursor_position)
        editor.textChanged.connect(self.handle_text_changed)
        
    def update_file_type(self, file_type):
        """تحديث نوع الملف في شريط الحالة"""
        self.file_type_label.setText(f"نوع الملف: {file_type}")
        
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

    def open_file(self, file_path=None):
        """فتح ملف"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                'اختر ملفاً',
                '',
                'كل الملفات (*);;ملفات نصية (*.txt);;ملفات أصلة (*.py);;ملفات جافاسكريبت (*.js);;ملفات اتش تي ام ال (*.html);;ملفات سي اس اس (*.css);;ملفات جسون (*.json);;ملفات ماركداون (*.md);;ملفات اكس ام ال (*.xml);;ملفات يامل (*.yml);;ملفات الاستعلامات المهيكلة (*.sql)'
            )
        
        if file_path:
            try:
                # قراءة الملف وتحديد نوع نهاية الأسطر
                with open(file_path, 'rb') as file:  # قراءة الملف في الوضع الثنائي
                    content = file.read()
                
                # تحديد الترميز
                encoding = 'utf-8'
                try:
                    content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        content.decode('utf-8-sig')
                        encoding = 'utf-8-sig'
                    except UnicodeDecodeError:
                        encoding = 'utf-16'
                
                # تحديد نوع نهاية الأسطر
                text = content.decode(encoding)
                if '\r\n' in text:
                    line_ending = '\r\n'
                elif '\r' in text:
                    line_ending = '\r'
                else:
                    line_ending = '\n'
                
                # تحديث المؤشرات في شريط الحالة
                self.statistics_manager.current_encoding = encoding
                self.statistics_manager.current_line_ending = line_ending
                self.statistics_manager.encoding_label.setText(encoding)
                ending_text = "CRLF" if line_ending == "\r\n" else "LF" if line_ending == "\n" else "CR"
                self.statistics_manager.line_ending_label.setText(ending_text)
                
                # إنشاء محرر جديد وتحميل المحتوى
                editor = self.create_editor()
                editor.setPlainText(text)
                editor.file_path = file_path
                
                # إضافة التبويب الديد
                file_name = os.path.basename(file_path)
                index = self.tab_manager.addTab(editor, file_name)
                self.tab_manager.setCurrentIndex(index)
                
                return True
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "طأ",
                    f"حدث خطأ أثناء فتح الملف: {str(e)}"
                )
                return False

    def _format_size(self, size):
        """تنسيق حجم الملف"""
        for unit in ['بايت', 'ك.ب', 'م.ب', 'ج.ب']:
            if size < 1024:
                return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} ت.ب"    

    def _is_text_file(self, file_path):
        """التحقق مما إذا كان الملف نصياً"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # قراءة جزء صغير للتحقق
            return True
        except UnicodeDecodeError:
            return False
        except Exception:
            return False

    def save_file(self):
        """فظ الملف لحالي"""
        current_editor = self.tab_manager.get_current_editor()
        if not current_editor:
            return False
        
        if hasattr(current_editor, 'file_path') and current_editor.file_path:
            file_path = current_editor.file_path
        else:
            return self.save_file_as()
        
        try:
            # الحصول على النص والإعدادات
            text = current_editor.toPlainText()
            
            # الحصول على نوع نهاية الأسطر من StatisticsManager
            line_ending = getattr(self.statistics_manager, 'current_line_ending', '\n')
            encoding = getattr(self.statistics_manager, 'current_encoding', 'UTF-8')
            
            # تحويل كل نهايات الأسطر إلى النوع المطلوب
            text = text.replace('\r\n', '\n')  # تحويل كل CRLF إلى LF أولاً
            text = text.replace('\r', '\n')    # تحويل كل CR إلى LF
            if line_ending != '\n':
                text = text.replace('\n', line_ending)  # تحوي إلى نوع نهاية الأسطر المطلوب
            
            # حفظ الملف مع الترميز المحدد
            with open(file_path, 'wb') as file:
                # تحويل النص إلى بايتات مع الترميز المحدد
                content = text.encode(encoding)
                file.write(content)
            
            current_editor.document().setModified(False)
            self.statusBar().showMessage(f"تم الحفظ: {file_path}", 2000)
            
            # تحديث مؤشرات شريط الحالة
            if hasattr(self, 'statistics_manager'):
                ending_text = "CRLF" if line_ending == "\r\n" else "LF" if line_ending == "\n" else "CR"
                self.statistics_manager.line_ending_label.setText(ending_text)
                self.statistics_manager.encoding_label.setText(encoding)
            
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء حفظ الملف: {str(e)}"
            )
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
            # قراءة النص من المحرر
            text = current_editor.toPlainText()
            
            # الحصول على إعدادات الترميز ونهاية الأسطر
            line_ending = getattr(self.statistics_manager, 'current_line_ending', '\n')
            encoding = getattr(self.statistics_manager, 'current_encoding', 'UTF-8')
            
            # قراءة الملف الحالي إذا كان موجوداً لمعرفة نوع نهاية الأسطر
            if os.path.exists(file_name):
                with open(file_name, 'rb') as file:
                    content = file.read()
                    if b'\r\n' in content:
                        line_ending = '\r\n'
                    elif b'\n' in content:
                        line_ending = '\n'
            
            # تحويل النص إلى بايتات مع نهاية الأسطر المناسبة
            lines = text.split('\n')
            binary_content = line_ending.join(lines).encode(encoding)
            
            # حفظ الملف كبيانات ثنائية
            with open(file_name, 'wb') as file:
                file.write(binary_content)
                
            current_editor.document().setModified(False)
            self.statusBar().showMessage(f"تم الحفظ: {file_name}", 2000)
            
            # تحديث مؤشرات شريط الحالة
            if hasattr(self, 'statistics_manager'):
                ending_text = "CRLF" if line_ending == "\r\n" else "LF"
                self.statistics_manager.line_ending_label.setText(ending_text)
                self.statistics_manager.encoding_label.setText(encoding)
                
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ الملف: {str(e)}")
            return False

    def show_search_dialog(self):
        """عرض نافذة ابحث"""
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
        """البحث عن التطابق الساق"""
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
        """تطبيق تنسيق عربي محد��"""
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
                
                # إنشاء مربع حار مخصص
                msg_box = QMessageBox()
                msg_box.setWindowTitle("تنبيه")
                msg_box.setText(f"هناك تغييرات غير مفوظة في {file_name}. هل تريد حفظها؟")
                
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
        
        # إنشاء مدير اتبويبات
        self.terminal_tabs = TerminalTabWidget(self)
        self.terminal_layout.addWidget(self.terminal_tabs)
        
        # إظهار التيرمنال
        self.toggle_terminal(True)
        
        return self.terminal_tabs.get_current_terminal()

    def toggle_terminal(self, show=None):
        """إظهر/إخفاء التيرمنال"""
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
        

    def show_font_dialog(self):
        """عرض مربع حوار اختيار الخط"""
        current_editor = self.tab_manager.get_current_editor()
        if not current_editor:
            return
        
        font, ok = QFontDialog.getFont(current_editor.font(), self)
        if ok:
            # تطبيق الخط على النص المحدد
            cursor = current_editor.textCursor()
            if cursor.hasSelection():
                char_format = QTextCharFormat()
                char_format.setFont(font)
                cursor.mergeCharFormat(char_format)
            else:
                # تطبيق الخط على المحرر بأكمله
                current_editor.setFont(font)
            
            # حفظ الخط كخط افتراضي
            self.default_font = font
            
            # تحديث شريط الحالة
            self.status_bar.showMessage(f"تم تغيير الخط إلى {font.family()} - {font.pointSize()}", 2000)

    def on_tab_changed(self, index):
        """معالجة تغيير التبويب النشط"""
        # إلغاء ربط الإشارات من المحرر السابق
        if hasattr(self, '_last_editor'):
            try:
                self._last_editor.textChanged.disconnect(self.update_status)
                self._last_editor.cursorPositionChanged.disconnect(self.update_status)
            except:
                pass
        
        # ربط الإشارات مع المحرر الجديد
        current_editor = self.tab_manager.get_current_editor()
        if current_editor:
            current_editor.textChanged.connect(self.update_status)
            current_editor.cursorPositionChanged.connect(self.update_status)
            self._last_editor = current_editor
        
        # تحديث الإحصائيات
        self.update_status()

    def show_update_notification(self, version):
        """عرض إشعار عند توفر تحديث جديد"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("تحديث جديد متوفر")
        msg.setText(f"تم العثور على إصدار جديد: {version}")
        msg.setInformativeText("هل تريد تنزيل التحديث الآن؟")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        if msg.exec_() == QMessageBox.Yes:
            self.download_update(version)
    
    def download_update(self, version):
        """تنزيل وتثبيت التحديث"""
        # إنشاء نافذة التقدم
        progress = QProgressDialog("جاري تنزيل التحديث...", "إلغاء", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        
        def update_progress(value):
            progress.setValue(value)
        
        self.update_manager.update_progress.connect(update_progress)
        
        # تنزيل التحديث
        destination = os.path.join(os.path.dirname(__file__), f"update_{version}.zip")
        if self.update_manager.download_update(version, destination):
            QMessageBox.information(self, "اكتمل التنزيل", 
                                  "تم تنزيل التحديث بنجاح. سيتم تثبيته عند إعادة تشغيل التطبيق.")

    def setup_auto_update_timer(self, update_settings):
        """إعداد مؤقت التحديث التلقائي"""
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()
        
        if update_settings.get('auto_check', True):
            self.update_timer = QTimer(self)
            self.update_timer.timeout.connect(self.check_for_updates)
            
            # تحديد الفترة بالمللي ثانية (مع مراعاة الحد الأقصى)
            interval_map = {
                'يومياً': 86400000,     # يوم (24 ساعة)
                'أسبوعياً': 604800000,  # أسبوع (7 أيام)
                'شهرياً': 2147483647    # أقصى قيمة مسموح بها (حوالي 24.8 يوم)
            }
            
            check_interval = update_settings.get('check_interval', 'يومياً')
            interval = interval_map.get(check_interval, 86400000)
            
            # إذا كان الفاصل شهرياً، نقوم بتقسيم الفترة إلى أجزاء
            if check_interval == 'شهرياً':
                # نضبط المؤقت ليعمل ل أسبوع بدلاً من كل شهر
                interval = 604800000  # أسبوع
                
            self.update_timer.start(interval)
            
            # التحقق من التحديثات مباشرة عند التفعيل
            QTimer.singleShot(1000, self.check_for_updates)  # تأخير بسيط قبل الفحص الأول

    def check_for_updates(self):
        """التحقق من وجود تحديثات جديدة"""
        try:
            update_info = self.update_manager.check_for_updates()
            if update_info and isinstance(update_info, dict):
                if 'error' in update_info:
                    # عرض رسالة الخطأ للمستخدم
                    QMessageBox.information(self, 'التحديثات', update_info['message'])
                elif 'version' in update_info:
                    # عرض إشعار التحديث
                    self.show_update_notification(update_info['version'])
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من التحديثات: {str(e)}")
            QMessageBox.warning(self, 'خطأ', 'حدث خطأ أثناء التحقق من التحديثات')

    def _handle_external_file_change(self, file_path):
        """معالجة التغييرات الخادجية في الملف"""
        current_editor = self.tab_manager.get_current_editor()
        if not current_editor:
            return

        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "تم تعديل الملف",
            "تم تعديل الملف من خارج المحرر.\nهل تريد إعادة تحميله؟",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    current_editor.setPlainText(content)
                    current_editor.document().setModified(False)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "خطأ",
                    f"حدث خطأ أثناء إعادة تحميل الملف:\n{str(e)}"
                )

    def _on_external_content_changed(self, file_path, new_content):
        """معالجة التغييرات الخارجية في الملف"""
        current_editor = self.tab_manager.get_current_editor()
        if current_editor and not current_editor.document().isModified():
            current_editor.setPlainText(new_content)
            current_editor.document().setModified(False)

    def initialize_settings(self):
        """تهيئة وتطبيق الإعدادات عند بدء التشغيل"""
        settings = self.settings_manager.load_settings()
        
        # تطبيق إعدادات التبويبات
        tabs_settings = settings.get('tabs', {})
        self.tab_manager.setMovable(tabs_settings.get('movable', True))
        self.tab_manager.setUsesScrollButtons(tabs_settings.get('scroll_buttons', True))
        
        elide_mode_map = {
            'middle': Qt.ElideMiddle,
            'right': Qt.ElideRight,
            'left': Qt.ElideLeft,
            'none': Qt.ElideNone
        }
        self.tab_manager.setElideMode(elide_mode_map[tabs_settings.get('elide_mode', 'middle')])
        self.tab_manager.max_closed_tabs = tabs_settings.get('max_closed_tabs', 10)
        
        # تطبيق إعدادات الحفظ التلقائي
        if hasattr(self, 'auto_saver'):
            auto_save_settings = settings.get('editor', {}).get('auto_save', {})
            self.auto_saver.enabled = auto_save_settings.get('enabled', False)
            self.auto_saver.interval = auto_save_settings.get('interval', 5)
        
        # تطبيق إعدادات التحديث التلقائي
        if hasattr(self, 'update_manager'):
            self.setup_auto_update_timer(settings.get('updates', {}))
        
        # تطبيق السمة
        theme = settings.get('editor', {}).get('theme', 'light')
        if hasattr(self, 'apply_theme'):
            self.apply_theme(theme)
        
        # تطبيق التفاف النص
        word_wrap = settings.get('editor', {}).get('word_wrap', False)
        for i in range(self.tab_manager.count()):
            editor = self.tab_manager.widget(i).findChild(QTextEdit)
            if editor:
                editor.setLineWrapMode(
                    QTextEdit.WidgetWidth if word_wrap else QTextEdit.NoWrap
                )

    def open_folder(self):
        """فتح مجلد في المحرر"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            'اختر مجلداً',
            '',
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder_path:
            # إرسال إشارة إلى مدير الملفات الجانبي
            if hasattr(self, 'extensions_manager'):
                for ext_id, extension in self.extensions_manager.active_extensions.items():
                    if hasattr(extension, 'on_folder_open'):
                        extension.on_folder_open(folder_path)