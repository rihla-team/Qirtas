from typing import Dict, List
import ast
import os
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTextBrowser, QPushButton, 
                            QComboBox, QHBoxLayout, QTreeWidget, QTreeWidgetItem, 
                            QSplitter, QLabel, QWidget, QTabWidget, QFileDialog, QMessageBox, QPlainTextEdit, QLineEdit)
from PyQt5.QtCore import Qt, QRegExp  # أضفنا QRegExp هنا
from PyQt5.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtCore import QProcess
import git

class CodeDocumenter:
    """أداة لتوثيق وشرح الكود"""
    
    def __init__(self, editor):
        self.editor = editor
        self.docs_cache = {}
        
    def analyze_file(self, file_path: str) -> Dict:
        """تحليل ملف وإنشاء توثيق له"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # جمع كل الدوال في الفئات
            class_methods = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_methods.add(item.name)
            
            return {
                'classes': self._analyze_classes(tree),
                'functions': self._analyze_functions(tree, class_methods),
                'imports': self._analyze_imports(tree),
                'file_path': file_path,
                'summary': self._generate_file_summary(tree)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_classes(self, tree: ast.AST) -> List[Dict]:
        """تحليل الفئات في الكود"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            'name': item.name,
                            'docstring': ast.get_docstring(item) or 'لا يوجد توثيق',
                            'args': [arg.arg for arg in item.args.args],
                            'line': item.lineno
                        })
                
                classes.append({
                    'name': node.name,
                    'docstring': ast.get_docstring(node) or 'لا يوجد توثيق',
                    'methods': methods,
                    'line': node.lineno
                })
        return classes
    
    def _analyze_functions(self, tree: ast.AST, class_methods: set) -> List[Dict]:
        """تحليل الدوال في الكود"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # تجاهل الدوال الموجودة في الفئات
                if node.name not in class_methods:
                    functions.append({
                        'name': node.name,
                        'docstring': ast.get_docstring(node) or 'لا يوجد توثيق',
                        'args': [arg.arg for arg in node.args.args],
                        'line': node.lineno
                    })
        return functions
    
    def _analyze_imports(self, tree: ast.AST) -> List[str]:
        """تحليل الاستيرادات في الكود"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(name.name for name in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(f"{node.module}.{node.names[0].name}")
        return imports
    
    def _generate_file_summary(self, tree: ast.AST) -> str:
        """إنشاء ملخص للملف"""
        classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        return f"يحتوي الملف على {classes} فئة و {functions} دالة"
    
    def get_extension_api_docs(self) -> Dict:
        """توثيق واجهة برمجة الإضافات"""
        return {
            'editor': {
                'methods': {
                    'get_current_editor()': {
                        'description': 'الحصول على المحرر النصي الحالي',
                        'returns': 'QTextEdit - كائن المحرر النصي'
                    },
                    'get_selected_text()': {
                        'description': 'الحصول على النص المحدد',
                        'returns': 'str - النص المحدد'
                    },
                    'insert_text(text)': {
                        'description': 'إدراج نص في الموضع الحالي',
                        'params': {'text': 'النص المراد إدراجه'}
                    }
                },
                'properties': {
                    'menuBar': 'شريط القوائم',
                    'statusBar': 'شريط الحالة'
                },
                'signals': {
                    'text_changed': 'يتم إطلاقها عند تغيير النص',
                    'file_saved': 'يتم إطلاقها عند حفظ الملف'
                }
            }
        }

class PythonHighlighter(QSyntaxHighlighter):
    """ملون الأكواد البرمجية"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # تعريف الألوان والأنماط
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#FF6B6B"))  # أحمر فاتح للكلمات المفتاحية
        keyword_format.setFontWeight(QFont.Bold)
        
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#98C379"))  # أخضر للنصوص
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#5C6370"))  # رمادي للتعليقات
        comment_format.setFontItalic(True)
        
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#61AFEF"))  # أزرق للدوال
        
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#E5C07B"))  # أصفر للفئات
        class_format.setFontWeight(QFont.Bold)
        
        # الكلمات المفتاحية في Python
        keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None',
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True',
            'try', 'while', 'with', 'yield', 'self'
        ]
        
        # إضافة قواعد التلوين
        for word in keywords:
            pattern = f'\\b{word}\\b'
            self.highlighting_rules.append((pattern, keyword_format))
        
        # تلوين النصوص
        self.highlighting_rules.extend([
            # النصوص المزدوجة
            (r'"[^"\\]*(\\.[^"\\]*)*"', string_format),
            (r"'[^'\\]*(\\.[^'\\]*)*'", string_format),
            
            # التعليقات
            (r'#[^\n]*', comment_format),
            
            # الدوال
            (r'\bdef\s+(\w+)', function_format),
            
            # الفئات
            (r'\bclass\s+(\w+)', class_format),
        ])
        
    def highlightBlock(self, text):
        """تطبيق التلوين على النص"""
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

class InteractiveDocViewer(QDialog):
    """نافذة عرض التوثيق التفاعلي"""
    
    def __init__(self, documenter, parent=None):
        super().__init__(parent)
        self.documenter = documenter
        self.setup_ui()
        self.load_extensions_manager_docs()
        
        # إضافة ملون الأكواد
        self.highlighter = PythonHighlighter(self.details_browser.document())
        
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("الدليل التفاعلي للمطورين")
        self.resize(1200, 800)
        
        main_layout = QVBoxLayout(self)
        
        # إنشاء شريط التبويب
        tab_widget = QTabWidget()
        
        # تبويب شرح الكود
        code_tab = QWidget()
        code_layout = QVBoxLayout(code_tab)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # شجرة العناصر
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("عناصر الكود")
        self.tree.setMinimumWidth(300)
        self.tree.itemClicked.connect(self.show_element_details)
        
        # منطقة التفاصيل
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        self.details_title = QLabel()
        self.details_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        
        details_layout.addWidget(self.details_title)
        details_layout.addWidget(self.details_browser)
        
        splitter.addWidget(self.tree)
        splitter.addWidget(details_widget)
        
        code_layout.addWidget(splitter)
        
        # تبويب واجهة برمجة الإضافات
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)
        
        self.api_browser = QTextBrowser()
        self.api_browser.setOpenExternalLinks(True)
        api_layout.addWidget(self.api_browser)
        
        # إضافة البويبات
        tab_widget.addTab(code_tab, "شرح الكود")
        tab_widget.addTab(api_tab, "واجهة برمجة الإضافات")
        
        main_layout.addWidget(tab_widget)
        
        # تحميل التوثيق
        self.load_api_docs()

    def show_element_details(self, item: QTreeWidgetItem, column: int):
        """عرض تفاصيل العنصر المحدد"""
        text = item.text(0)
        self.details_title.setText(text)
        
        # المتغيرات
        if text == "editor - المحرر الرئيسي":
            self.show_editor_details()
        elif text == "extensions - قاموس الإضافات":
            self.show_extensions_details()
        elif text == "extensions_dir - مجلد الإضافات":
            self.show_extensions_dir_details()
            
        # الدوال الأساسية
        if text == "__init__ - تهيئة المدير":
            self.show_init_details()
        elif text == "load_extensions - تحميل الإضافات":
            self.show_load_extensions_details()
        elif text == "setup_menu - إعداد القائمة":
            self.show_setup_menu_details()
        
        # الأمثلة العملية
        elif text == "1- إضافة بسيطة":
            self.show_simple_extension_example()
        elif text == "2- إضافة مع واجهة مستخدم":
            self.show_gui_extension_example()
        elif text == "3- إضافة مع إعدادات":
            self.show_settings_extension_example()
        elif text == "4- إضافة متعددة اللغات":
            self.show_multilingual_extension_example()
        elif text == "5- إضافة تعمل مع الملفات":
            self.show_file_extension_example()
        elif text == "6- إضافة مع اختصارات لوحة المفاتيح":
            self.show_shortcut_extension_example()
        
        # أفضل الممارسات
        elif text == "هيكلة اكود":
            self.show_code_structure_practices()
        elif text == "التعامل مع الأخطاء":
            self.show_error_handling_practices()
        elif text == "الأداء":
            self.show_performance_practices()
        elif text == "الأمان":
            self.show_security_practices()
        elif text == "التوثيق":
            self.show_documentation_practices()
        
        # استكشاف الأخطاء
        elif text == "مشاكل شائعة":
            self.show_common_issues()
        elif text == "التصحيح والاختبار":
            self.show_debugging_testing()
        elif text == "السجلات والتتبع":
            self.show_logging_tracing()
        elif text == "7- التعديل على موجة الأوامر":
            self.show_terminal_extension_example()
        elif text =="8- إضافة أوامر في موجة الأوامر":    
            self.show_terminal_addcommand_example()
        elif text == "9- إضافة محلل نصوص":
            self.show_parser_extension_example()
        elif text == "10- إضافة مدير المشاريع":
            self.show_project_manager_example()
        elif text == "11- إضافة Git":
            self.show_git_extension_example()

    def load_extensions_manager_docs(self):
        """تحميل توثيق مدير الإضافات"""
        # إنشاء شجرة العناصر
        main_item = QTreeWidgetItem(["مدير الإضافات (ExtensionsManager)"])
        
        # إضافة الدوال الرئيسية
        methods = QTreeWidgetItem(["الدوال الأساسية"])
        methods.addChild(QTreeWidgetItem(["__init__ - تهيئة المدير"]))
        methods.addChild(QTreeWidgetItem(["load_extensions - تحميل الإضافات"]))
        methods.addChild(QTreeWidgetItem(["setup_menu - إعداد القائمة"]))
        main_item.addChild(methods)
        
        # إضافة المتغيرات
        vars = QTreeWidgetItem(["المتغيرات"])
        vars.addChild(QTreeWidgetItem(["editor - المحرر الرئيسي"]))
        vars.addChild(QTreeWidgetItem(["extensions - قاموس الإضافات"]))
        vars.addChild(QTreeWidgetItem(["extensions_dir - مجلد الإضافات"]))
        main_item.addChild(vars)
        
        # إضافة الأمثلة العملية
        examples = QTreeWidgetItem(["أمثلة عملية"])
        examples.addChild(QTreeWidgetItem(["1- إضافة بسيطة"]))
        examples.addChild(QTreeWidgetItem(["2- إضافة مع واجهة مستخدم"]))
        examples.addChild(QTreeWidgetItem(["3- إضافة مع إعدادات"]))
        examples.addChild(QTreeWidgetItem(["4- إضافة متعددة اللغات"]))
        examples.addChild(QTreeWidgetItem(["5- إضافة تعمل مع الملفات"]))
        examples.addChild(QTreeWidgetItem(["6- إضافة مع اختصارات لوحة المفاتيح"]))
        examples.addChild(QTreeWidgetItem(["7- التعديل على موجة الأوامر"]))
        examples.addChild(QTreeWidgetItem(["8- إضافة أوامر في موجة الأوامر"]))
        examples.addChild(QTreeWidgetItem(["9- إضافة محلل نصوص"]))
        examples.addChild(QTreeWidgetItem(["10- إضافة مدير المشاريع"]))
        examples.addChild(QTreeWidgetItem(["11- إضافة Git"]))
        main_item.addChild(examples)
        
        # إضافة أفضل الممارسات
        best_practices = QTreeWidgetItem(["أفضل الممارسات   "])
        best_practices.addChild(QTreeWidgetItem(["هيكلة الكود"]))
        best_practices.addChild(QTreeWidgetItem(["التعامل مع الأخطاء"]))
        best_practices.addChild(QTreeWidgetItem(["الأداء"]))
        best_practices.addChild(QTreeWidgetItem(["الأمان"]))
        best_practices.addChild(QTreeWidgetItem(["التوثيق"]))
        main_item.addChild(best_practices)
        
        # إضافة استكشاف الأخطاء وإصلاحها
        troubleshooting = QTreeWidgetItem(["استكشاف الأخطاء"])
        troubleshooting.addChild(QTreeWidgetItem(["مشاكل شائعة"]))
        troubleshooting.addChild(QTreeWidgetItem(["التصحيح والاختبار"]))
        troubleshooting.addChild(QTreeWidgetItem(["السجلات والتتبع"]))
        main_item.addChild(troubleshooting)
        
        self.tree.addTopLevelItem(main_item)
        main_item.setExpanded(True)
        
    def show_init_details(self):
        """عرض تفاصيل دالة التهيئة"""
        html = """
        <h3>دالة التهيئة __init__</h3>
        <pre>
def __init__(self, editor):
    self.editor = editor
    self.extensions = {}
    self.extensions_menu = None
    self.extensions_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'extensions'
    )
    
    # إنشاء مجلد الإضافات إذا لم يكن موجوداً
    if not os.path.exists(self.extensions_dir):
        os.makedirs(self.extensions_dir)
        
    # إعداد التسجيل
    logging.basicConfig(filename='extensions.log', level=logging.INFO)
    self.logger = logging.getLogger('ExtensionsManager')
</pre>
        <p><b>الشرح:</b></p>
        <ul>
            <li>تهيئة المتغيرات الأساسية</li>
            <li>إنشاء مجلد الإضافات</li>
            <li>إعداد نظام التسجيل</li>
        </ul>
        """
        self.details_browser.setHtml(html)
        
    def show_load_extensions_details(self):
        """عرض تفاصيل تحميل الإضافات"""
        html = """
        <h3>تحميل الإضافات</h3>
        <pre>
def load_extensions(self):
    for ext_folder in os.listdir(self.extensions_dir):
        ext_path = os.path.join(self.extensions_dir, ext_folder)
        
        if not os.path.isdir(ext_path):
            continue
            
        manifest_path = os.path.join(ext_path, 'manifest.json')
        if not os.path.exists(manifest_path):
            continue
            
        try:
            # قراءة ملف التعريف
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # تحميل الإضافة
            main_module = os.path.join(ext_path, manifest.get('main', 'main.py'))
            if os.path.exists(main_module):
                spec = importlib.util.spec_from_file_location(ext_folder, main_module)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                extension = module.Extension(self.editor)
                self.extensions[ext_folder] = {
                    'instance': extension,
                    'manifest': manifest
                }
        except Exception as e:
            self.logger.error(f"خطأ في تحميل الإضافة {ext_folder}: {str(e)}")
</pre>
        """
        self.details_browser.setHtml(html)
        
    def show_setup_menu_details(self):
        """عرض تفاصيل إعداد القائمة"""
        html = """
        <h3>إعداد قائمة الإضافات</h3>
        <pre>
def setup_menu(self):
    if not hasattr(self.editor, 'menuBar'):
        return
        
    # إضافة قائمة الإضافات
    self.extensions_menu = self.editor.menuBar().addMenu('إضافات')
    
    # إضافة الإضافات المحملة للقائمة
    for ext_id, ext_data in self.extensions.items():
        manifest = ext_data['manifest']
        extension = ext_data['instance']
        
        if hasattr(extension, 'get_menu_items'):
            menu_items = extension.get_menu_items()
            if menu_items:
                ext_menu = QMenu(manifest.get('name', ext_id), self.editor)
                for item in menu_items:
                    action = QAction(item['name'], self.editor)
                    action.triggered.connect(item['callback'])
                    ext_menu.addAction(action)
                self.extensions_menu.addMenu(ext_menu)
</pre>
        """
        self.details_browser.setHtml(html)
        
    def show_simple_extension_example(self):
        """عرض مثال لإضافة بسيطة"""
        html = """
        <h3>مثال: إضافة بسيطة</h3>
        <p>هذا مثال لإضافة بسيطة تقوم بإضافة عنصر قائمة:</p>
        <pre>
# main.py
class Extension:
    def __init__(self, editor):
        self.editor = editor
    
    def get_menu_items(self):
        return [{
            'name': 'مرحباً',
            'callback': self.say_hello
        }]
    
    def say_hello(self):
        QMessageBox.information(
            self.editor,
            'تحية',
            'مرحباً بك في الإضافة!'
        )
</pre>
        """
        self.details_browser.setHtml(html)
        
    def show_gui_extension_example(self):
        """عرض مثال لإضافة مع واجهة مستخدم"""
        html = """
        <h3>مثال: إضافة مع واجهة مستخدم</h3>
        <pre>
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('مرحباً بك!'))
        btn = QPushButton('موافق')
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.dialog = None
    
    def get_menu_items(self):
        return [{
            'name': 'فتح النافذة',
            'callback': self.show_dialog
        }]
    
    def show_dialog(self):
        if not self.dialog:
            self.dialog = MyDialog(self.editor)
        self.dialog.show()
</pre>
        """
        self.details_browser.setHtml(html)
        
    def show_settings_extension_example(self):
        """عرض مثال لإضافة مع إعدادات"""
        html = """
        <h3>مثال: إضافة مع إعدادات</h3>
        <pre>
import json
import os

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.settings_file = os.path.join(
            os.path.dirname(__file__),
            'settings.json'
        )
        self.settings = self.load_settings()
    
    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)
</pre>
        """
        self.details_browser.setHtml(html)
        
    def show_multilingual_extension_example(self):
        """عرض مثال لإضافة متعددة اللغات"""
        html = """
        <h3>مثال: إضافة متعددة اللغات</h3>
        <pre>
import json
import os

class Translator:
    def __init__(self, locale_dir):
        self.locale_dir = locale_dir
        self.current_language = 'ar'
        self.messages = {}
        self.load_messages()
    
    def load_messages(self):
        messages_file = os.path.join(
            self.locale_dir, 
            self.current_language, 
            'messages.json'
        )
        if os.path.exists(messages_file):
            with open(messages_file, 'r', encoding='utf-8') as f:
                self.messages = json.load(f)
    
    def set_language(self, lang):
        self.current_language = lang
        self.load_messages()
    
    def get(self, key, default=''):
        return self.messages.get(key, default)
</pre>

        <h4>locale/ar/messages.json:</h4>
        <pre>
{
    "menu_item": "العنصر",
    "dialog_title": "العنوان",
    "button_ok": "موافق",
    "button_cancel": "إلغاء"
}
        </pre>

        <h4>main.py:</h4>
        <pre>
import os
from .translator import Translator

class Extension:
    def __init__(self, editor):
        self.editor = editor
        locale_dir = os.path.join(os.path.dirname(__file__), 'locale')
        self.translator = Translator(locale_dir)
    
    def get_menu_items(self):
        return [
            {
                'name': self.translator.get('menu_item'),
                'callback': self.show_dialog
            }
        ]
    
    def show_dialog(self):
        # استخدام الترجمات في الواجهة
        title = self.translator.get('dialog_title')
        ok_text = self.translator.get('button_ok')
        cancel_text = self.translator.get('button_cancel')
</pre>
        """
        self.details_browser.setHtml(html)
        
    def load_api_docs(self):
        """تحميل توثيق واجهة برمجة الإضافات"""
        html = """
        <h2>واجهة برمجة الإضافات</h2>
        
        <h3>الكائنات المتاحة</h3>
        <ul>
            <li><code>self.editor</code>: المحرر الرئيسي</li>
            <li><code>self.editor.get_current_editor()</code>: المحرر النصي الحالي</li>
            <li><code>self.editor.menuBar()</code>: شريط القوائم</li>
        </ul>
        
        <h3>الدوال المطلوبة</h3>
        <ul>
            <li><code>__init__(self, editor)</code>: دالة التهيئة</li>
            <li><code>get_menu_items(self)</code>: تحديد عناصر القائمة</li>
        </ul>
        
        <h3>الدوال المساعدة</h3>
        <ul>
            <li><code>editor.get_selected_text()</code>: الحصول على النص المحدد</li>
            <li><code>editor.insert_text(text)</code>: إدراج نص</li>
            <li><code>editor.get_current_line()</code>: الحصول على السطر الحالي</li>
        </ul>
        
        <h3>الإشارات المتاحة</h3>
        <ul>
            <li><code>editor.text_changed</code>: عند تغيير النص</li>
            <li><code>editor.selection_changed</code>: عند تغيير التحديد</li>
            <li><code>editor.file_saved</code>: عند حفظ الملف</li>
        </ul>
        """
        self.api_browser.setHtml(html)

    def show_common_issues(self):
        """عرض المشاكل الشائعة وحلولها"""
        html = """
        <h3>المشاكل الشائعة وحلولها</h3>
        
        <h4>1. مشاكل تحميل الإضافة</h4>
        <table border="1" cellpadding="5">
            <tr>
                <th>المشكلة</th>
                <th>السبب المحتمل</th>
                <th>الحل</th>
            </tr>
            <tr>
                <td>الإضافة لا تظهر في القائمة</td>
                <td>
                    - خطأ في manifest.json<br>
                    - خطأ في اسم الملف الرئيسي<br>
                    - مشكلة في هيكل المجلد
                </td>
                <td>
                    - تأكد من صحة manifest.json<br>
                    - تأكد من وجود main.py<br>
                    - تحقق من هيكل المجلد
                </td>
            </tr>
            <tr>
                <td>خطأ عند تحميل الإضافة</td>
                <td>
                    - مكتبات مفقودة<br>
                    - أخطاء في الكود<br>
                    - تعارض في الإصدارات
                </td>
                <td>
                    - تثبيت المكتبات المطلوبة<br>
                    - مراجعة سجل الأخاء<br>
                    - التحقق من التوافق
                </td>
            </tr>
        </table>

        <h4>2. مشاكل في التنفيذ</h4>
        <table border="1" cellpadding="5">
            <tr>
                <th>المشكلة</th>
                <th>السبب المحتمل</th>
                <th>الحل</th>
            </tr>
            <tr>
                <td>عدم استجابة الإضافة</td>
                <td>
                    - مشكلة في الواجهة<br>
                    - عمليات طويلة<br>
                    - تسرب في الذاكرة
                </td>
                <td>
                    - استخدام QThread<br>
                    - إضافة مؤشر التحميل<br>
                    - تحسين إدارة الذاكرة
                </td>
            </tr>
            <tr>
                <td>أخطاء في حفظ الإعدادات</td>
                <td>
                    - مشاكل في الصلاحيات<br>
                    - مسار غير صحيح<br>
                    - تنسيق غير صالح
                </td>
                <td>
                    - التحقق من الصلاحيات<br>
                    - استخدام المسار الصحيح<br>
                    - التحقق من صحة البيانات
                </td>
            </tr>
        </table>

        <h4>3. نصائح عامة للتصحيح</h4>
        <ul>
            <li>استخدم try/except لمعالجة الأخطاء المتوقعة</li>
            <li>أضف رسائل تصحيح مفصلة في السجلات</li>
            <li>تحقق من سجل الأخطاء بانتظام</li>
            <li>اختبر الإضافة في بيئات مختلفة</li>
            <li>استخدم أدوات التصحيح مثل pdb أو المصحح المدمج في IDE</li>
            <li>قم بتوثيق الأخطاء المعروفة وحلولها</li>
        </ul>

        <h4>4. أفضل الممارسات للوقاية من المشاكل</h4>
        <ul>
            <li>اتبع معايير كتابة الكود PEP 8</li>
            <li>قم بتنظيم الكود في وحدات منطقية</li>
            <li>اكتب اختبارات وحدة للوظائف الأساسية</li>
            <li>استخدم نظام إصدارات للتحكم في الكود</li>
            <li>قم بتحديث التوثيق بانتظام</li>
            <li>راجع الكود بشكل دوري</li>
        </ul>

        <h4>5. موارد إضافية</h4>
        <ul>
            <li><a href="https://docs.python.org/3/tutorial/errors.html">توثيق Python للأخطاء والاستثناءات</a></li>
            <li><a href="https://doc.qt.io/qt-5/debug.html">دليل تصحيح Qt</a></li>
            <li><a href="https://www.python.org/dev/peps/pep-0008/">PEP 8 -- دليل نمط كود Python</a></li>
        </ul>
        """
        self.details_browser.setHtml(html)

    def show_error_handling_practices(self):
        """عرض أفضل ممارسات التعامل مع الأخطاء"""
        html = """
        <h3>أفضل ممارسات التعامل مع الأخطاء</h3>
        <pre>
class Extension:
    def safe_operation(self):
        try:
            # محاولة تنفيذ لعملية
            result = self.process_data()
            
        except FileNotFoundError as e:
            # معالجة خطأ عدم وجود الملف
            self.logger.error(f"الملف غير موجود: {e}")
            self.show_error_dialog("لم يتم العثور على الملف المطلوب")
            
        except PermissionError:
            # معالجة خطأ الصلاحيات
            self.logger.error("خطأ في الصلاحيات")
            self.show_error_dialog("لا توجد صلاحيات كافية")
            
        except Exception as e:
            # معالجة الأخطاء غير المتوقعة
            self.logger.critical(f"خطأ غير متوقع: {e}")
            self.show_error_dialog("حدث خطأ غير متوقع")
            
        else:
            # تنفيذ في حالة عدم وجود أخطاء
            self.logger.info("تم تنفيذ العملية بنجاح")
            return result
            
        finally:
            # تنظيف الموارد
            self.cleanup_resources()
</pre>
        """
        self.details_browser.setHtml(html)

    def show_debugging_testing(self):
        """عرض معلومات التصحيح والاختبار"""
        html = """
        <h3>التصحيح والاختبار</h3>
        
        <h4>1. تصحيح الأخطاء</h4>
        <pre>
import logging

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.logger = logging.getLogger(__name__)
        
    def debug_action(self):
        try:
            # تنفيذ العملية
            result = self.process_data()
            self.logger.info(f"تم التنفيذ بنجاح: {result}")
        except Exception as e:
            self.logger.error(f"خطأ: {str(e)}")
            # معالجة الخطأ
        </pre>

        <h4>2. اختبار الإضافة</h4>
        <pre>
import unittest

class TestExtension(unittest.TestCase):
    def setUp(self):
        self.editor = MockEditor()
        self.extension = Extension(self.editor)
    
    def test_basic_functionality(self):
        result = self.extension.process_data()
        self.assertIsNotNone(result)
    
    def test_error_handling(self):
        with self.assertRaises(ValueError):
            self.extension.invalid_action()
</pre>
        """
        self.details_browser.setHtml(html)

    def show_logging_tracing(self):
        """عرض معلومات السجلات والتتبع"""
        html = """
        <h3>السجلات والتتبع</h3>
        
        <h4>1. إعداد نظام السجلات</h4>
        <pre>
import logging
import os

def setup_logging(extension_name):
    logger = logging.getLogger(extension_name)
    logger.setLevel(logging.DEBUG)
    
    # إشاء مجلد للسجلات
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # إداد ملف السجل
    log_file = os.path.join(log_dir, f'{extension_name}.log')
    handler = logging.FileHandler(log_file, encoding='utf-8')
    
    # تنسيق السجل
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
</pre>

        <h4>2. استخدام السجلات</h4>
        <pre>
class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.logger = setup_logging('my_extension')
        
    def some_action(self):
        self.logger.info('بدء العملية')
        try:
            # تنفيذ العملية
            self.logger.debug('تفاصيل التنفيذ')
        except Exception as e:
            self.logger.error(f'خطأ: {str(e)}')
            raise
</pre>

        <h4>3. مستويات السجلات</h4>
        <ul>
            <li><code>DEBUG</code>: معلومات تفصيلية للتصحيح</li>
            <li><code>INFO</code>: معلومات عامة عن سير العمل</li>
            <li><code>WARNING</code>: تحذيرات لا تؤثر على التشغيل</li>
            <li><code>ERROR</code>: أخطاء تؤثر على وظيفة معينة</li>
            <li><code>CRITICAL</code>: أخطاء خطيرة تؤثر على النظام</li>
        </ul>
        """
        self.details_browser.setHtml(html)

    def show_code_structure_practices(self):
        """عرض أفضل ممارسات هيكلة الكود"""
        html = """
        <h3>أفضل ممارسات هيكلة الكود</h3>
        
        <h4>1. تنظيم الملفات</h4>
        <pre>
my_extension/
    ├── __init__.py
    ├── main.py
    ├── manifest.json
    ├── utils/
    │   ├── __init__.py
    │   └── helpers.py
    ├── ui/
    │   ├── __init__.py
    │   └── dialogs.py
    └── locale/
        ├── ar/
        │   └── messages.json
        └── en/
            └── messages.json
</pre>

        <h4>2. فصل المسؤوليات</h4>
        <ul>
            <li>فصل المنطق البرمجي عن واجهة المستخدم</li>
            <li>تجميع الدوال المساعدة في وحدات منفصلة</li>
            <li>فصل النصوص والترجمات في ملفات خاصة</li>
        </ul>

        <h4>3. نمط الكود</h4>
        <ul>
            <li>اتباع معايير PEP 8</li>
            <li>استخدام أسماء وصفية للمتغيرات والدوال</li>
            <li>كتابة تعليقات توضيحية للكود</li>
            <li>توثيق الدوال والفئات</li>
        </ul>
        """
        self.details_browser.setHtml(html)

    def show_performance_practices(self):
        """عرض أفضل ممارسات الأداء"""
        html = """
        <h3>أفضل ممارسات الأداء</h3>
        
        <h4>1. تحسين استخدام الموارد</h4>
        <ul>
            <li>تجنب العمليات الثيلة في الخيط الرئيسي</li>
            <li>استخدام QThread للعمليات الطويلة</li>
            <li>تحرير الموارد بعد الانتهاء منها</li>
        </ul>

        <h4>2. تحسين الذاكرة</h4>
        <ul>
            <li>استخدام التخزين المؤقت للبيانات المتكررة</li>
            <li>��جنب تسرب الذاكرة</li>
            <li>استخدام الموارد بحكمة</li>
        </ul>
        """
        self.details_browser.setHtml(html)

    def show_security_practices(self):
        """عرض أفضل ممارسات الأمان"""
        html = """
        <h3>أفضل ممارسات الأمان</h3>
        
        <h4>1. التحقق من المدخلات</h4>
        <ul>
            <li>التحقق من صحة جميع المدخلات</li>
            <li>تنظيف البيانات قبل معالجتها</li>
            <li>استخدام التشفير عند الحاجة</li>
        </ul>

        <h4>2. إدارة الملفات</h4>
        <ul>
            <li>التحقق من صلاحيات الوصول</li>
            <li>استخدام مسارات آمنة</li>
            <li>تجنب تنفيذ الكود غير الموثوق</li>
        </ul>
        """
        self.details_browser.setHtml(html)

    def show_documentation_practices(self):
        """عرض أفضل ممارسات التوثيق"""
        html = """
        <h3>أفضل ممارسات التوثيق</h3>
        
        <h4>1. توثيق الكود</h4>
        <ul>
            <li>كتابة docstrings للفئات والدوال</li>
            <li>شرح المنطق المعقد</li>
            <li>توثيق التغييرات المهمة</li>
        </ul>

        <h4>2. توثيق المستخدم</h4>
        <ul>
            <li>كتابة دليل المستخدم</li>
            <li>توثيق كيفية التثبيت والإعداد</li>
            <li>شرح الميزات والوظائف</li>
        </ul>
        """
        self.details_browser.setHtml(html)

    def show_file_extension_example(self):
        """عرض مثال لإضافة تعمل مع الملفات"""
        html = """
        <h3>مثال: إضافة تعمل مع الملفات</h3>
        <pre>
import os
from PyQt5.QtWidgets import QFileDialog

class Extension:
    def __init__(self, editor):
        self.editor = editor
        
    def get_menu_items(self):
        return [{
            'name': 'فتح ملف',
            'callback': self.open_file
        }, {
            'name': 'حفظ ملف',
            'callback': self.save_file
        }]
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.editor,
            'اختر ملفاً',
            '',
            'Text Files (*.txt);;All Files (*.*)'
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.editor.get_current_editor().setText(content)
            except Exception as e:
                self.show_error_dialog(f"خطأ في فتح الملف: {str(e)}")
    
    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self.editor,
            'حفظ الملف',
            '',
            'Text Files (*.txt);;All Files (*.*)'
        )
        
        if file_path:
            try:
                content = self.editor.get_current_editor().toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                self.show_error_dialog(f"خطأ في حفظ الملف: {str(e)}")
    
    def show_error_dialog(self, message):
        QMessageBox.critical(self.editor, 'خطأ', message)
        </pre>
        """
        self.details_browser.setHtml(html)

    def show_shortcut_extension_example(self):
        """عرض مثال لإضافة تعمل مع اختصارات لوحة المفاتيح"""
        html = """
        <h3>مثال: إضافة مع اختصارات لوحة المفاتيح</h3>
        <pre>
from PyQt5.QtWidgets import QAction, QMessageBox
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        # إنشاء الإجراءات مع اختصارات لوحة المفاتيح
        self.format_action = QAction('تنسيق النص', self.editor)
        self.format_action.setShortcut(QKeySequence('Ctrl+Shift+F'))
        self.format_action.triggered.connect(self.format_text)
        
        self.comment_action = QAction('إضافة تعليق', self.editor)
        self.comment_action.setShortcut(QKeySequence('Ctrl+K'))
        self.comment_action.triggered.connect(self.toggle_comment)
        
        # إضافة الإجراءات إلى المحرر
        self.editor.addAction(self.format_action)
        self.editor.addAction(self.comment_action)
    
    def get_menu_items(self):
        return [{
            'name': 'تنسيق النص',
            'callback': self.format_text,
            'shortcut': 'Ctrl+Shift+F'
        }, {
            'name': 'إضافة/إزالة تعليق',
            'callback': self.toggle_comment,
            'shortcut': 'Ctrl+K'
        }]
    
    def format_text(self):
        editor = self.editor.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            selected_text = cursor.selectedText()
            
            if selected_text:
                # تنفيذ التنسيق على النص المحدد
                formatted_text = self.format_code(selected_text)
                cursor.insertText(formatted_text)
            else:
                QMessageBox.information(
                    self.editor,
                    'تنبيه',
                    'الرجاء تحديد النص المراد تنسيقه'
                )
    
    def toggle_comment(self):
        editor = self.editor.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            
            # حفظ الموضع الحالي
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            
            # تحديد الأسطر كاملة
            cursor.setPosition(start)
            cursor.movePosition(cursor.StartOfLine)
            cursor.setPosition(end, cursor.KeepAnchor)
            cursor.movePosition(cursor.EndOfLine, cursor.KeepAnchor)
            
            text = cursor.selectedText()
            lines = text.split('\u2029')  # فاصل الأسطر في Qt
            
            # إضافة أو إزالة التعليقات
            commented = all(line.strip().startswith('#') for line in lines if line.strip())
            new_lines = []
            
            for line in lines:
                if commented:
                    # إزالة التعليق
                    if line.strip().startswith('#'):
                        new_lines.append(line.replace('#', '', 1).lstrip())
                    else:
                        new_lines.append(line)
                else:
                    # إضافة تعليق
                    if line.strip():
                        new_lines.append('# ' + line)
                    else:
                        new_lines.append(line)
            
            # استبدال النص
            new_text = '\n'.join(new_lines)
            cursor.insertText(new_text)
    
    def format_code(self, text):
        # مثال بسيط للتنسيق - يمكن استخدام مكتبة black أو autopep8
        lines = text.split('\n')
        formatted_lines = []
        indent = 0
        
        for line in lines:
            stripped = line.strip()
            
            # تعديل المسافات البادئة
            if stripped.endswith(':'):
                formatted_lines.append('    ' * indent + stripped)
                indent += 1
            elif stripped.startswith(('return', 'break', 'continue')):
                indent = max(0, indent - 1)
                formatted_lines.append('    ' * indent + stripped)
            else:
                formatted_lines.append('    ' * indent + stripped)
        
        return '\n'.join(formatted_lines)
</pre>

        <p><b>الميزات الرئيسية:</b></p>
        <ul>
            <li>إضافة اختصارات لوحة المفاتيح للوظائف المتكررة</li>
            <li>دعم تنسيق الكود تلقائياً</li>
            <li>إضافة وإزالة التعليقات بسهولة</li>
            <li>التكامل مع واجهة المستخدم والقوائم</li>
        </ul>

        <p><b>ملاحظات:</b></p>
        <ul>
            <li>استخدام QAction لإنشاء الاختصارات</li>
            <li>دعم تحديد النص المتعدد الأسطر</li>
            <li>معالجة حالات خاصة مثل الأسطر الفارغة</li>
            <li>إمكانية التخصيص والتوسيع</li>
        </ul>
        """
        self.details_browser.setHtml(html)

    def show_editor_details(self):
        """عرض تفاصيل متغير المحرر"""
        html = """
        <h3 style="color: #61AFEF;">المحرر الرئيسي (editor)</h3>
        <p>كائن المحرر الرئيسي الذي يتم تمريره للإضافة عند تهيئتها. يوفر واجهة برمجية للتفاعل مع المحرر.</p>
        
        <h4 style="color: #98C379;">الخصائص الأساسية:</h4>
        <pre><code class="python">
# الحصول على المحرر النصي الحالي
editor = self.editor.get_current_editor()

# الوصول إلى شريط القوائم
menu_bar = self.editor.menuBar()

# الوصول إلى شريط الحالة
status_bar = self.editor.statusBar()
        </code></pre>
        
        <h4 style="color: #98C379;">التعامل مع النص:</h4>
        <pre><code class="python">
# الحصول على النص المحدد
selected_text = editor.get_selected_text()

# إدراج نص في الموضع الحالي
editor.insert_text("نص جديد")

# الحصول على السطر الحالي
current_line = editor.get_current_line()

# استبدال النص المحدد
editor.replace_selected_text("النص الجديد")

# الحصول على رقم السطر الحالي
line_number = editor.get_current_line_number()
        </code></pre>

        <h4 style="color: #98C379;">التعامل مع الملفات:</h4>
        <pre><code class="python">
# الحصول على مسار الملف الحالي
current_file = editor.get_current_file_path()

# حفظ الملف
editor.save_file()

# فتح ملف
editor.open_file("path/to/file.txt")

# إنشاء ملف جديد
editor.new_file()
        </code></pre>

        <h4 style="color: #98C379;">التعامل مع الواجهة:</h4>
        <pre><code class="python">
# إضافة عنصر إلى شريط الأدوات
toolbar = editor.addToolBar("اسم الشريط")
action = QAction("عمل جديد", editor)
toolbar.addAction(action)

# إضافة قائمة جديدة
menu = editor.menuBar().addMenu("قائمة جديدة")
menu.addAction(action)

# تحديث شريط الحالة
editor.statusBar().showMessage("رسالة جديدة")
        </code></pre>

        <h4 style="color: #98C379;">الإشارات المتاحة:</h4>
        <pre><code class="python">
# الاشتراك في إشارة تغيير النص
editor.text_changed.connect(self.on_text_changed)

# الاشتراك في إشارة تغيير التحديد
editor.selection_changed.connect(self.on_selection_changed)

# الاشتراك في إشارة حفظ الملف
editor.file_saved.connect(self.on_file_saved)

def on_text_changed(self):
    print("تم تغيير النص")

def on_selection_changed(self):
    print("تم تغيير التحديد")

def on_file_saved(self, file_path):
    print(f"تم حفظ الملف: {file_path}")
        </code></pre>

        <h4 style="color: #E5C07B;">أمثلة عملية:</h4>
        
        <h5>1. إضافة زر إلى شريط الأدوات:</h5>
        <pre><code class="python">
class MyExtension:
    def __init__(self, editor):
        self.editor = editor
        self.setup_toolbar()
    
    def setup_toolbar(self):
        # إنشاء شريط أدوات
        toolbar = self.editor.addToolBar("أدواتي")
        
        # إضافة زر
        action = QAction(QIcon("icon.png"), "تنسيق", self.editor)
        action.setStatusTip("تنسيق النص المحدد")
        action.triggered.connect(self.format_text)
        toolbar.addAction(action)
        </code></pre>

        <h5>2. إضافة ميزة البحث:</h5>
        <pre><code class="python">
class SearchExtension:
    def __init__(self, editor):
        self.editor = editor
        self.setup_search()
    
    def setup_search(self):
        # إضافة شريط البحث
        search_bar = QLineEdit()
        self.editor.addToolBarWidget(search_bar)
        search_bar.textChanged.connect(self.search_text)
    
    def search_text(self, text):
        editor = self.editor.get_current_editor()
        if editor and text:
            # تنفيذ البحث
            cursor = editor.document().find(text)
            if not cursor.isNull():
                editor.setTextCursor(cursor)
        </code></pre>

        <h5>3. حفظ وتحميل الإعدادات:</h5>
        <pre><code class="python">
class ConfigurableExtension:
    def __init__(self, editor):
        self.editor = editor
        self.settings = QSettings('MyApp', 'MyExtension')
        self.load_settings()
    
    def load_settings(self):
        # تحميل الإعدادات
        self.font_size = self.settings.value('font_size', 12)
        self.theme = self.settings.value('theme', 'light')
    
    def save_settings(self):
        # حفظ الإعدادات
        self.settings.setValue('font_size', self.font_size)
        self.settings.setValue('theme', self.theme)
        </code></pre>

        <h4 style="color: #E5C07B;">ملاحظات هامة:</h4>
        <ul>
            <li>تأكد من التحقق من وجود المحرر قبل استخدام خصائصه</li>
            <li>استخدم try/except لمعالجة الأخطاء المحتملة</li>
            <li>قم بتنظيف الموارد عند إغلاق الإضافة</li>
            <li>وثق الكود بشكل جيد</li>
            <li>اختبر الإضافة في مختلف السيناريوهات</li>
        </ul>
        """
        self.details_browser.setHtml(html)

    def show_terminal_extension_example(self):
        """عرض مثال لتحسين وتعديل الطرفية"""
        html = '''
        <h3>مثال: تحسين الطرفية العربية</h3>
        <pre><code class="python">
    # تعديل الفئة ArabicTerminal الموجودة
    class ArabicTerminal(QTextEdit):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent = parent
            
            # إضافة المزيد من الألوان والأنماط
            self.colors.update({
                'command': QColor("#61AFEF"),  # أزرق للأوامر
                'path': QColor("#98C379"),     # أخضر للمسارات
                'warning': QColor("#E5C07B"),  # أصفر للتحذيرات
                'success': QColor("#98C379"),  # أخضر للنجاح
                'system': QColor("#C678DD"),   # بنفسجي لرسائل النظام
            })
            
            # إضافة دعم للإكمال التلقائي المتقدم
            self.completions = {
                'git': ['add', 'commit', 'push', 'pull', 'status', 'log'],
                'npm': ['install', 'start', 'build', 'test', 'run'],
                'python': ['-m', '-c', '-V', '--version'],
            }
            
            # إضافة دعم للتاريخ المتقدم
            self.command_history_file = Path.home() / '.terminal_history'
            self.load_command_history()
            
            self.setup_terminal()
            self.setup_shortcuts()

        def setup_shortcuts(self):
            """إعداد اختصارات لوحة المفاتيح"""
            shortcuts = {
                'Ctrl+L': self.clear_screen,
                'Ctrl+K': self.clear_current_line,
                'Ctrl+U': self.clear_to_start,
                'Ctrl+W': self.delete_word,
                'Alt+B': self.move_word_backward,
                'Alt+F': self.move_word_forward,
                'Ctrl+R': self.search_history,
            }
            
            for key, callback in shortcuts.items():
                QShortcut(QKeySequence(key), self, activated=callback)

        def execute_command(self, command):
            """تنفيذ الأمر مع دعم إضافي"""
            # حفظ الأمر في التاريخ
            self.add_to_history(command)
            
            # معالجة الأوامر الخاصة
            if command.startswith('git'):
                self.handle_git_command(command)
            elif command.startswith('cd'):
                self.handle_cd_command(command)
            elif command == 'clear':
                self.clear_screen()
            else:
                # تنفيذ الأمر العادي
                super().execute_command(command)

        def handle_git_command(self, command):
            """معالجة أوامر Git"""
            try:
                # تنفيذ أمر Git
                process = subprocess.Popen(
                    command.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                output, error = process.communicate()
                
                if output:
                    self.append_text(output, self.colors['success'])
                if error:
                    self.append_text(error, self.colors['error'])
                    
            except Exception as e:
                self.append_text(f"خطأ: {str(e)}", self.colors['error'])

        def search_history(self):
            """البحث في تاريخ الأوامر"""
            dialog = TerminalSearchWidget(self)
            dialog.exec_()

        def add_to_history(self, command):
            """إضافة أمر إلى التاريخ مع الوقت"""
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            entry = f"{timestamp} | {command}\\n"
            
            with open(self.command_history_file, 'a', encoding='utf-8') as f:
                f.write(entry)

        def load_command_history(self):
            """تحميل تاريخ الأوامر"""
            try:
                if self.command_history_file.exists():
                    with open(self.command_history_file, 'r', encoding='utf-8') as f:
                        self.command_history = f.readlines()
                else:
                    self.command_history = []
            except Exception as e:
                self.command_history = []
                print(f"خطأ في تحميل التاريخ: {str(e)}")

        def format_output(self, text, command_type=None):
            """تنسيق المخرجات حسب نوع الأمر"""
            if command_type == 'git':
                # تنسيق خاص لمخرجات Git
                if 'modified:' in text:
                    return text.replace('modified:', '🔄 تم التعديل:')
                elif 'new file:' in text:
                    return text.replace('new file:', '✨ ملف جديد:')
                elif 'deleted:' in text:
                    return text.replace('deleted:', '❌ تم الحذف:')
            return text
    </code></pre>

    <h4>التحسينات المضافة:</h4>
    <ul>
        <li>دعم متقدم للإكمال التلقائي</li>
        <li>تاريخ أوامر محسن مع الوقت</li>
        <li>اختصارات لوحة مفاتيح إضافية</li>
        <li>معالجة خاصة لأوامر Git</li>
        <li>تنسيق محسن للمخرجات</li>
        <li>ألوان وأنماط إضافية</li>
        <li>بحث متقدم في التاريخ</li>
    </ul>

    <h4>كيفية الاستخدام:</h4>
    <ol>
        <li>نسخ الدوال الجديدة إلى الفئة ArabicTerminal الموجودة</li>
        <li>تحديث __init__ لإضافة الميزات الجديدة</li>
        <li>إضافة الملفات والموارد المطلوبة</li>
    </ol>
            '''
        self.details_browser.setHtml(html)

    def show_git_extension_example(self):
        """عرض مثال لإضافة Git"""
        html = """
        <h3>مثال: إضافة Git</h3>
        <pre><code class="python">
import git
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PyQt5.QtCore import Qt

class GitExtension:
    def __init__(self, editor):
        self.editor = editor
        self.repo = None
        self.setup_git_panel()
        
    def setup_git_panel(self):
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['الملف', 'الحالة'])
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        dock = self.editor.addDockWidget('Git', self.tree)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        
        self.load_repo()
        
    def load_repo(self):
        try:
            self.repo = git.Repo(self.editor.project_path)
            self.refresh_status()
        except git.InvalidGitRepositoryError:
            self.tree.clear()
            QTreeWidgetItem(self.tree, ['لا يوجد مستودع Git'])
    
    def refresh_status(self):
        self.tree.clear()
        if not self.repo:
            return
            
        # إضافة الملفات المتغيرة
        for item in self.repo.index.diff(None):
            status = 'تم التعديل'
            if item.new_file:
                status = 'ملف جديد'
            elif item.deleted_file:
                status = 'تم الحذف'
                
            QTreeWidgetItem(self.tree, [item.a_path, status])
    
    def show_context_menu(self, position):
        menu = QMenu()
        commit = menu.addAction('Commit')
        push = menu.addAction('Push')
        pull = menu.addAction('Pull')
        
        action = menu.exec_(self.tree.mapToGlobal(position))
        
        if action == commit:
            self.commit_changes()
        elif action == push:
            self.push_changes()
        elif action == pull:
            self.pull_changes()
        </code></pre>
        """
        self.details_browser.setHtml(html)

    def show_parser_extension_example(self):
        """عرض مثال لإضافة محلل نصوص"""
        html = """
        <h3>مثال: إضافة محلل نصوص</h3>
        <pre><code class="python">
from PyQt5.QtWidgets import QDockWidget, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
import ast

class CodeParser:
    def __init__(self, editor):
        self.editor = editor
        self.setup_ui()
        
    def setup_ui(self):
        # إنشاء شجرة لعرض هيكل الكود
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['العنصر', 'النوع', 'السطر'])
        
        # إنشاء نافذة جانبية
        dock = QDockWidget('محلل الكود', self.editor)
        dock.setWidget(self.tree)
        self.editor.addDockWidget(Qt.RightDockWidgetArea, dock)
        
        # ربط حدث تغيير النص
        self.editor.textChanged.connect(self.parse_code)
    
    def parse_code(self):
        '''تحليل الكود وعرض هيكله'''
        self.tree.clear()
        text = self.editor.toPlainText()
        
        try:
            # تحليل الكود باستخدام ast
            tree = ast.parse(text)
            
            # إضافة الفئات
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_item = QTreeWidgetItem(self.tree)
                    class_item.setText(0, node.name)
                    class_item.setText(1, 'فئة')
                    class_item.setText(2, str(node.lineno))
                    
                    # إضافة الدوال داخل الفئة
                    for method in [n for n in node.body if isinstance(n, ast.FunctionDef)]:
                        method_item = QTreeWidgetItem(class_item)
                        method_item.setText(0, method.name)
                        method_item.setText(1, 'دالة')
                        method_item.setText(2, str(method.lineno))
                
                # إضافة الدوال العامة
                elif isinstance(node, ast.FunctionDef):
                    if node.parent_field != 'body':  # تجنب الدوال داخل الفئات
                        func_item = QTreeWidgetItem(self.tree)
                        func_item.setText(0, node.name)
                        func_item.setText(1, 'دالة')
                        func_item.setText(2, str(node.lineno))
                
                # إضافة المتغيرات العامة
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_item = QTreeWidgetItem(self.tree)
                            var_item.setText(0, target.id)
                            var_item.setText(1, 'متغير')
                            var_item.setText(2, str(node.lineno))
        
        except SyntaxError:
            error_item = QTreeWidgetItem(self.tree)
            error_item.setText(0, 'خطأ في الكود')
            error_item.setText(1, 'خطأ')
    
    def get_menu_items(self):
        '''إضافة عناصر القائمة'''
        return [{
            'name': 'تحليل الكود',
            'callback': self.parse_code
        }]

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.parser = CodeParser(editor)
    
    def get_menu_items(self):
        return self.parser.get_menu_items()
        </code></pre>
        """
        self.details_browser.setHtml(html)

    def show_project_manager_example(self):
        """عرض مثال لإضافة مدير المشاريع"""
        html = """
        <h3>مثال: إضافة مدير المشاريع</h3>
        <pre><code class="python">
from PyQt5.QtWidgets import (QTreeView, QFileSystemModel, QDockWidget, 
                            QMenu, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QDir
import os
import shutil

class ProjectManager:
    def __init__(self, editor):
        self.editor = editor
        self.project_path = None
        self.setup_ui()
        
    def setup_ui(self):
        # إنشاء نموذج نظام الملفات
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        
        # إنشاء شجرة الملفات
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # إخفاء الأعمدة غير المطلوبة
        self.tree.hideColumn(1)  # الحجم
        self.tree.hideColumn(2)  # النوع
        self.tree.hideColumn(3)  # التاريخ
        
        # إنشاء نافذة جانبية
        self.dock = QDockWidget('المشروع', self.editor)
        self.dock.setWidget(self.tree)
        self.editor.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        
        # ربط حدث النقر المزدوج
        self.tree.doubleClicked.connect(self.open_file)
    
    def open_project(self, path):
        '''فتح مشروع'''
        self.project_path = path
        self.tree.setRootIndex(self.model.index(path))
        self.dock.setWindowTitle(f'المشروع: {os.path.basename(path)}')
    
    def open_file(self, index):
        '''فتح ملف عند النقر المزدوج'''
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.editor.open_file(path)
    
    def show_context_menu(self, position):
        '''عرض القائمة السياقية'''
        menu = QMenu()
        
        # إضافة عناصر القائمة
        new_file = menu.addAction('ملف جديد')
        new_folder = menu.addAction('مجلد جديد')
        menu.addSeparator()
        rename = menu.addAction('إعادة تسمية')
        delete = menu.addAction('حذف')
        
        # تنفيذ الإجراء المحدد
        action = menu.exec_(self.tree.mapToGlobal(position))
        
        if action == new_file:
            self.create_file()
        elif action == new_folder:
            self.create_folder()
        elif action == rename:
            self.rename_item()
        elif action == delete:
            self.delete_item()
    
    def create_file(self):
        '''إنشاء ملف جديد'''
        index = self.tree.currentIndex()
        dir_path = self.model.filePath(index)
        if not os.path.isdir(dir_path):
            dir_path = os.path.dirname(dir_path)
            
        name, ok = QInputDialog.getText(self.editor, 'ملف جديد', 'اسم الملف:')
        if ok and name:
            file_path = os.path.join(dir_path, name)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('')
                self.editor.open_file(file_path)
            except Exception as e:
                QMessageBox.critical(self.editor, 'خطأ', str(e))
    
    def create_folder(self):
        '''إنشاء مجلد جديد'''
        index = self.tree.currentIndex()
        dir_path = self.model.filePath(index)
        if not os.path.isdir(dir_path):
            dir_path = os.path.dirname(dir_path)
            
        name, ok = QInputDialog.getText(self.editor, 'مجلد جديد', 'اسم المجلد:')
        if ok and name:
            try:
                os.makedirs(os.path.join(dir_path, name))
            except Exception as e:
                QMessageBox.critical(self.editor, 'خطأ', str(e))
    
    def rename_item(self):
        '''إعادة تسمية عنصر'''
        index = self.tree.currentIndex()
        path = self.model.filePath(index)
        old_name = os.path.basename(path)
        
        name, ok = QInputDialog.getText(self.editor, 'إعادة تسمية', 
                                      'الاسم الجديد:', text=old_name)
        if ok and name and name != old_name:
            new_path = os.path.join(os.path.dirname(path), name)
            try:
                os.rename(path, new_path)
            except Exception as e:
                QMessageBox.critical(self.editor, 'خطأ', str(e))
    
    def delete_item(self):
        '''حذف عنصر'''
        index = self.tree.currentIndex()
        path = self.model.filePath(index)
        
        reply = QMessageBox.question(self.editor, 'تأكيد الحذف',
                                   f'هل أنت متأكد من حذف "{os.path.basename(path)}"؟',
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
            except Exception as e:
                QMessageBox.critical(self.editor, 'خطأ', str(e))

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.project_manager = ProjectManager(editor)
    
    def get_menu_items(self):
        return [{
            'name': 'فتح مشروع',
            'callback': self.open_project
        }]
    
    def open_project(self):
        path = QFileDialog.getExistingDirectory(
            self.editor,
            'اختر مجلد المشروع',
            '',
            QFileDialog.ShowDirsOnly
        )
        if path:
            self.project_manager.open_project(path)
        </code></pre>
        """
        self.details_browser.setHtml(html)

    def show_terminal_addcommand_example(self):
        """عرض مثال لتحسين وتعديل الطرفية"""
        html = '''
        <h3>مثال: إضافة أوامر مخصصة للطرفية</h3>
        
        <h4>1. هيكل ملف command.json:</h4>
        <pre><code class="json">
    {
        "metadata": {
            "version": "1.0",
            "language": ["ar", "en"],
            "author": "اسم المؤلف",
            "description": "وصف الملف"
        },
        
        // أمر نظام عادي
        "ls": {
            "windows": "dir",           // الأمر في نظام ويندوز
            "linux": "ls",             // الأمر في نظام لينكس
            "description": "عرض محتويات المجلد",
            "arabic": ["عرض", "قائمة"], // الكلمات المفتاحية العربية
            "category": "إدارة الملفات",
            "support_files_or_folders_nor": "files_or_folders"  // نوع الدعم
        },
        
        // أمر مخصص
        "نسخ_ملف": {
            "windows": "copy",
            "linux": "cp",
            "description": "نسخ ملف أو مجلد",
            "arabic": ["نسخ", "انسخ"],
            "category": "إدارة الملفات",
            "support_files_or_folders_nor": "files_or_folders",
            "internal_command": true,   // تحديد أنه أمر مخصص
            "tool": "FileCopy"         // اسم الأداة المستخدمة
        }
    }
    </code></pre>

        <h4>2. إضافة معالج الأمر المخصص:</h4>
        <pre><code class="python">
    class ArabicTerminal(QTextEdit):
        def register_custom_commands(self):
            """تسجيل الأوامر المخصصة"""
            self.custom_handlers = {
                'نسخ_ملف': self.handle_file_copy,
                'تحويل_وحدات': self.handle_unit_conversion,
                'فحص_شبكة': self.handle_network_check,
                'ترجمة': self.handle_translation  # أمر جديد للترجمة
            }
            
            # إنشاء الأدوات المساعدة
            self.unit_converter = UnitConverter()
            self.translator = ArabicTranslator()
        
        def handle_translation(self, args):
            """معالج الترجمة"""
            if len(args) < 2:
                self.append_text("الاستخدام: ترجمة <النص> <اللغة>", self.colors['error'])
                return
                
            text = ' '.join(args[:-1])
            target_lang = args[-1]
            
            try:
                result = self.translator.translate(text, target_lang)
                self.append_text(f"الترجمة: {result}", self.colors['success'])
            except Exception as e:
                self.append_text(f"خطأ في الترجمة: {str(e)}", self.colors['error'])
    </code></pre>

        <h4>3. إضافة الأدوات المساعدة:</h4>
        <pre><code class="python">
    class ArabicTranslator:
        """أداة الترجمة"""
        def __init__(self):
            self.supported_langs = {
                'en': 'الإنجليزية',
                'ar': 'العربية',
                'fr': 'الفرنسية',
                'es': 'الإسبانية'
            }
            
        def translate(self, text, target_lang):
            """ترجمة النص"""
            try:
                from googletrans import Translator
                translator = Translator()
                result = translator.translate(text, dest=target_lang)
                return result.text
            except Exception as e:
                raise Exception(f"خطأ في الترجمة: {str(e)}")
        
        def get_supported_languages(self):
            """الحصول على قائمة اللغات المدعومة"""
            return self.supported_langs
    </code></pre>

        <h4>4. إضافة الأمر في command.json:</h4>
        <pre><code class="json">
    {
        "ترجمة": {
            "windows": "translate",
            "linux": "translate",
            "description": "ترجمة نص إلى لغة أخرى",
            "arabic": ["ترجم", "ترجمة", "حول"],
            "category": "أدوات النصوص",
            "support_files_or_folders_nor": "none",
            "internal_command": true,
            "tool": "ArabicTranslator"
        }
    }
    </code></pre>

        <h4>أنواع الأوامر المدعومة:</h4>
        <ul>
            <li>أوامر النظام العادية: تنفذ مباشرة على نظام التشغيل</li>
            <li>أوامر مخصصة: تحتاج إلى معالج خاص وأداة مساعدة</li>
            <li>أوامر مركبة: تجمع بين عدة أوامر</li>
            <li>أوامر مع معاملات: تقبل معاملات إضافية</li>
        </ul>

        <h4>أنواع الدعم للملفات والمجلدات:</h4>
        <ul>
            <li>files: يدعم الملفات فقط</li>
            <li>folders: يدعم المجلدات فقط</li>
            <li>files_or_folders: يدعم كليهما</li>
            <li>none: لا يتعامل مع الملفات</li>
        </ul>

        <h4>خطوات إضافة أمر جديد:</h4>
        <ol>
            <li>تحديد نوع الأمر (عادي أو مخصص)</li>
            <li>إضافة تعريف الأمر في command.json</li>
            <li>إنشاء معالج للأمر إذا كان مخصصاً</li>
            <li>إضافة الأدوات المساعدة إذا لزم الأمر</li>
            <li>تسجيل المعالج في register_custom_commands</li>
            <li>اختبار الأمر والتأكد من عمله</li>
        </ol>
        '''
        self.details_browser.setHtml(html)