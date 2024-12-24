import json
import os
import shutil
from pathlib import Path
import semver #pip install semver
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QTextEdit, QComboBox, QPushButton, QLabel, QHBoxLayout, QCheckBox, QGridLayout, QMessageBox

class ExtensionCreator(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إنشاء إضافة جديدة")
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)
        self.icon_path = None
        self.setup_ui()
        self.setup_styles()
        
    def setup_styles(self):
        """تعيين الأنماط والتصميم"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #333333;
                border-radius: 6px;
                margin-top: 12px;
                background-color: #212121;
                color: #ffffff;
            }
            QGroupBox::title {
                color: #ffffff;
                subcontrol-position: top center;
                padding: 5px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #212121;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #333333;
                border-radius: 4px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #054229;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #054229;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 90px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #065435;
            }
            QPushButton:pressed {
                background-color: #043821;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: url(resources/icons/down-arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #212121;
                color: #ffffff;
                selection-background-color: #054229;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 14px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
                border-radius: 7px;
            }
            .required {
                color: #e74c3c;
            }
        """)

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout()
        
        # المعلومات الأساسية
        basic_group = QGroupBox("المعلومات الأساسية")
        basic_layout = QFormLayout()
        
        # تعيين أحجام حقول الإدخال
        self.name_input = QLineEdit()
        self.name_input.setMinimumHeight(40)
        self.name_input.setMinimumWidth(400)
        
        self.id_input = QLineEdit()
        self.id_input.setMinimumHeight(40)
        self.id_input.setMinimumWidth(400)
        
        self.version_input = QLineEdit()
        self.version_input.setMinimumHeight(40)
        self.version_input.setMinimumWidth(400)
        self.version_input.setPlaceholderText("1.0.0")
        
        self.author_input = QLineEdit()
        self.author_input.setMinimumHeight(40)
        self.author_input.setMinimumWidth(400)
        
        # تعيين المسافات بين العناصر
        basic_layout.setSpacing(15)
        basic_layout.setContentsMargins(20, 20, 20, 20)
        
        # إضافة العناصر مع تنسيق التسميات
        basic_layout.addRow(QLabel("اسم الإضافة *"), self.name_input)
        basic_layout.addRow(QLabel("معرف الإضافة *"), self.id_input)
        basic_layout.addRow(QLabel("الإصدار *"), self.version_input)
        basic_layout.addRow(QLabel("المطور"), self.author_input)
        
        basic_group.setLayout(basic_layout)
        
        # التوافق والمتطلبات
        compatibility_group = QGroupBox()
        compatibility_layout = QVBoxLayout()
        
        # نظام التشغيل
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("أنظمة التشغيل المدعومة:"))
        
        self.windows_check = QCheckBox("ويندوز")
        self.windows_check.setChecked(True)
        self.linux_check = QCheckBox("لينكس")
        self.macos_check = QCheckBox("ماك")
        
        platform_layout.addWidget(self.windows_check)
        platform_layout.addWidget(self.linux_check)
        platform_layout.addWidget(self.macos_check)
        compatibility_layout.addLayout(platform_layout)
        
        # إصدار التطبيق
        version_layout = QGridLayout()
        version_layout.addWidget(QLabel("إصدار التطبيق:"), 0, 0)
        
        self.min_version = QLineEdit()
        self.min_version.setPlaceholderText("1.0.0")
        version_layout.addWidget(QLabel("الحد الأدنى"), 1, 0)
        version_layout.addWidget(self.min_version, 1, 1)
        
        self.max_version = QLineEdit()
        self.max_version.setPlaceholderText("2.0.0")
        version_layout.addWidget(QLabel("الحد الأقصى"), 1, 2)
        version_layout.addWidget(self.max_version, 1, 3)
        
        compatibility_layout.addLayout(version_layout)
        
        # المتطلبات
        self.requirements_input = QTextEdit()
        self.requirements_input.setPlaceholderText("أدخل المتطلبات (كل متطلب في سطر)\nمثال:\npyqt5>=5.15.0\nrequests>=2.25.0")
        self.requirements_input.setMaximumHeight(100)
        compatibility_layout.addWidget(QLabel("المتطلبات:"))
        compatibility_layout.addWidget(self.requirements_input)
        
        compatibility_group.setLayout(compatibility_layout)
        
        # الوصف والفئة
        description_group = QGroupBox()
        description_layout = QVBoxLayout()
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("وصف الإضافة...")
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "تحرير النص",
            "تنسيق",
            "ترجمة",
            "أدوات",
            "تحسينات",
            "أخرى"
        ])
        
        description_layout.addWidget(self.description_input)
        description_layout.addWidget(QLabel("الفئة:"))
        description_layout.addWidget(self.category_combo)
        description_group.setLayout(description_layout)
        
        # إضافة كل المجموعات
        layout.addWidget(basic_group)
        layout.addWidget(compatibility_group)
        layout.addWidget(description_group)
        
        # أزرار التحكم
        buttons = QHBoxLayout()
        create_btn = QPushButton("إنشاء")
        create_btn.clicked.connect(self.create_extension)

        
        buttons.addStretch()
        buttons.addWidget(create_btn)
        layout.addLayout(buttons)
        
        self.setLayout(layout)

    def create_manifest(self):
        """إنشاء محتوى ملف manifest.json"""
        manifest = {
            "name": self.name_input.text(),
            "id": self.id_input.text(),
            "version": self.version_input.text() or "1.0.0",
            "description": self.description_input.toPlainText(),
            "author": self.author_input.text() or "غير معروف",
            "category": self.category_combo.currentText(),
            "main": "main.py",
            "icon": "icon.png",
            "platform": {
                "windows": self.windows_check.isChecked(),
                "linux": self.linux_check.isChecked(),
                "macos": self.macos_check.isChecked()
            },
            "app_version": {
                "min": self.min_version.text() or "1.0.0",
                "max": self.max_version.text() or "2.0.0"
            },
            "requirements": [
                req.strip() 
                for req in self.requirements_input.toPlainText().split('\n')
                if req.strip()
            ]
        }
        return manifest

    def validate_inputs(self):
        """التحقق من صحة المدخلات"""
        if not self.name_input.text():
            QMessageBox.warning(self, "خطأ", "يجب إدخال اسم الإضافة")
            return False
        
        if not self.id_input.text():
            QMessageBox.warning(self, "خطأ", "يجب إدخال معرف الإضافة")
            return False
        
        # التحقق من صحة الإصدارات
        try:
            if self.min_version.text():
                semver.VersionInfo.parse(self.min_version.text())
            if self.max_version.text():
                semver.VersionInfo.parse(self.max_version.text())
            if self.version_input.text():
                semver.VersionInfo.parse(self.version_input.text())
        except ValueError:
            QMessageBox.warning(self, "خطأ", "صيغة الإصدار غير صحيحة. يجب أن تكون بالشكل: X.Y.Z")
            return False
        
        # التحقق من اختيار نظام تشغيل واحد على الأقل
        if not any([
            self.windows_check.isChecked(),
            self.linux_check.isChecked(),
            self.macos_check.isChecked()
        ]):
            QMessageBox.warning(self, "خطأ", "يجب اختيار نظام تشغيل واحد على الأقل")
            return False
        
        return True

    def create_extension(self):
        """إنشاء الإضافة مع التحقق من الأخطاء والتنظيم"""
        if not self.validate_inputs():
            return
        
        try:
            extension_dir = self.get_extensions_dir() / self.id_input.text()
            
            # التحقق من وجود الإضافة
            if extension_dir.exists():
                response = QMessageBox.question(
                    self,
                    "تأكيد",
                    "يوجد إضافة بنفس المعرف. هل تريد استبدالها؟",
                    QMessageBox.Yes | QMessageBox.No
                )
                if response == QMessageBox.No:
                    return
                shutil.rmtree(extension_dir)
            
            # إنشاء المجلد والملفات
            extension_dir.mkdir(parents=True)
            self._create_extension_files(extension_dir)
            
            response = QMessageBox.question(
                self,
                "تم بنجاح",
                "تم إنشاء الإضافة بنجاح. هل تريد إنشاء إضافة أخرى؟",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if response == QMessageBox.Yes:
                # إعادة تعيين الحقول
                self.reset_form()
            else:
                self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إنشاء الإضافة:\n{str(e)}")

    def get_extensions_dir(self):
        """إنشاء والحصول على مسار مجلد الإضافات"""
        # المسار الافتراضي للإضافات في مجلد التطبيق
        base_dir = Path(__file__).parent.parent
        extensions_dir = base_dir / "extensions"
        
        # إنشاء المجلد إذا لم يكن موجوداً
        if not extensions_dir.exists():
            try:
                extensions_dir.mkdir(parents=True)
                # إنشاء ملف __init__.py
                (extensions_dir / "__init__.py").touch()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    f"فشل إنشاء مجلد الإضافات:\n{str(e)}"
                )
                return None
        
        return extensions_dir

    def create_main_file(self, extension_dir):
        """إنشاء ملف main.py مع قالب أساسي وتوثيق"""
        template = f'''"""
{self.name_input.text()}
{"=" * len(self.name_input.text())}

{self.description_input.toPlainText()}

معلومات الإضافة:
---------------
- المطور: {self.author_input.text()}
- الإصدار: {self.version_input.text()}
- الفئة: {self.category_combo.currentText()}
"""

from typing import Optional


class Extension:
    """فئة الإضافة الرئيسية"""
    
    def __init__(self, editor):
        self.name: str = "{self.name_input.text()}"
        self.version: str = "{self.version_input.text()}"
        self.description: str = "{self.description_input.toPlainText()}"
        self._initialized: bool = False
    
    def initialize(self) -> None:
        """تهيئة الإضافة وإعداد الموارد المطلوبة
        
        يتم استدعاء هذه الدالة عن تفعيل الإضافة
        """
        if not self._initialized:
            # قم بإضافة كود التهيئة هنا
            self._initialized = True
    
    def cleanup(self) -> None:
        """تنظيف الموارد وإيقاف الإضافة
        
        يتم استدعاء هذه الدالة عند إيقاف الإضافة
        """
        if self._initialized:
            # قم بإضافة كود التنظيف هنا
            self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """التحقق من حالة تهيئة الإضافة"""
        return self._initialized
'''
        with open(extension_dir / "main.py", "w", encoding="utf-8") as f:
            f.write(template)

    def create_readme(self, extension_dir):
        """إنشاء ملف README.md مع توثيق شامل"""
        template = f'''# {self.name_input.text()}

{self.description_input.toPlainText()}

## معلومات الإضافة
- **الإصدار**: {self.version_input.text()}
- **المطور**: {self.author_input.text()}
- **الفئة**: {self.category_combo.currentText()}

## المتطلبات
{self._format_requirements()}

## التثبيت
1. قم بتحميل الإضافة إلى مجلد الإضافات
2. أكد من تثبيت المتطلبات المذكورة أعلاه
3. أعد تشغيل التطبيق
4. فعّل الإضافة من مدير الإضافات

## الاستخدام
[قم بإضافة تعليمات استخدام الإضافة هنا]

## المساهمة
نرحب بمساهماتكم! يرجى اتباع الخطوات التالية:
1. انسخ المستودع (Fork)
2. أنشئ فرعاً جديداً (`git checkout -b feature/amazing-feature`)
3. ثبّت تغييراتك (`git commit -m 'إضافة ميزة رائعة'`)
4. ارفع التغييرات (`git push origin feature/amazing-feature`)
5. افتح طلب دمج (Pull Request)

## الترخيص
هذه الإضافة مرخصة تحت رخصة MIT. راجع ملف `LICENSE` للمزيد من المعلومات.

## الدعم
إذا واجهت أي مشكلة أو لديك اقتراح، يرجى فتح issue في صفحة المشروع.
'''
        with open(extension_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(template)

    def _format_requirements(self) -> str:
        """تنسيق المتطلبات للعرض في README"""
        requirements = self.requirements_input.toPlainText().strip().split('\n')
        if not requirements or not requirements[0]:
            return "- Python 3.6+\n- PyQt5"
        return "\n".join(f"- {req}" for req in requirements)

    def get_default_save_path(self):
        """الحصول على مسار الحفظ الافتراضي"""
        extensions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'extensions')
        if not os.path.exists(extensions_dir):
            os.makedirs(extensions_dir)
        return extensions_dir

    def create_templates_group(self):
        group = QGroupBox("قوالب التطوير")
        layout = QVBoxLayout()
        
        # قائمة القوالب
        self.template_combo = QComboBox()
        templates = {
            "empty": "إضافة فارغة",
            "text_processor": "معالج نصوص",
            "ui_extension": "إضافة واجهة مستخدم",
            "analyzer": "أداة تحليل",
            "converter": "محول بيانات",
            "api_client": "واجهة API"
        }
        self.template_combo.addItems(templates.values())
        self.template_combo.currentIndexChanged.connect(self.update_template_preview)
        
        # معاينة القالب
        self.template_preview = QTextEdit()
        self.template_preview.setReadOnly(True)
        self.template_preview.setMaximumHeight(150)
        
        layout.addWidget(QLabel("اختر قالباً:"))
        layout.addWidget(self.template_combo)
        layout.addWidget(QLabel("معاينة:"))
        layout.addWidget(self.template_preview)
        
        group.setLayout(layout)
        return group

    def create_components_group(self):
        group = QGroupBox("المكونات الإضافية")
        layout = QVBoxLayout()
        
        self.add_menu_cb = QCheckBox("إضافة قائمة")
        self.add_toolbar_cb = QCheckBox("إضافة شريط أدوات")
        self.add_settings_cb = QCheckBox("إضافة نافذة إعدادات")
        self.add_shortcuts_cb = QCheckBox("إضافة اختصارات لوحة المفاتيح")
        self.add_context_menu_cb = QCheckBox("إضافة قائمة سياقية")
        self.add_api_docs_cb = QCheckBox("إضافة توثيق API")
        
        for cb in [self.add_menu_cb, self.add_toolbar_cb, self.add_settings_cb,
                   self.add_shortcuts_cb, self.add_context_menu_cb, self.add_api_docs_cb]:
            layout.addWidget(cb)
        
        group.setLayout(layout)
        return group

    def update_template_preview(self):
        template_name = self.template_combo.currentText()
        preview_text = self.get_template_preview(template_name)
        self.template_preview.setText(preview_text)
        
        # تحدث الخيارات المقترحة بناءً على القالب
        self.update_suggested_components(template_name)

    def update_suggested_components(self, template_name):
        # إعادة تعيين جميع الخيارات
        for cb in [self.add_menu_cb, self.add_toolbar_cb, self.add_settings_cb,
                   self.add_shortcuts_cb, self.add_context_menu_cb, self.add_api_docs_cb]:
            cb.setChecked(False)
        
        # تحديد الخيارات المناسبة للقالب
        if template_name == "معالج نصوص":
            self.add_menu_cb.setChecked(True)
            self.add_toolbar_cb.setChecked(True)
            self.add_shortcuts_cb.setChecked(True)
        elif template_name == "أداة تحليل":
            self.add_menu_cb.setChecked(True)
            self.add_settings_cb.setChecked(True)
        elif template_name == "واجهة API":
            self.add_settings_cb.setChecked(True)
            self.add_api_docs_cb.setChecked(True)

    def get_template_preview(self, template_name):
        """الحصول على معاينة القالب المحدد"""
        templates = {
            "إضافة فارغة": """class Extension:
    def __init__(self, editor):
        self.name = "إضافة جديدة"
        self._initialized = False
    
    def initialize(self):
        if not self._initialized:
            # قم بإضافة كود التهيئة هنا
            self._initialized = True""",
            
            "معالج نصوص": """class Extension:
    def __init__(self, editor):
        self.name = "معالج النصوص"
        self.menu_items = []
        self.setup_menu()
    
    def setup_menu(self):
        self.menu_items.append({
            'name': 'معالجة النص',
            'callback': self.process_text
        })
    
    def process_text(self, text):
        # معالجة النص هنا
        return text.upper()""",
            
            "أداة تحليل": """class Extension:
    def __init__(self, editor):
        self.name = "محلل البيانات"
        self.settings = {}
        self.load_settings()
    
    def analyze_data(self, data):
        # تحليل البيانات هنا
        results = {}
        return results""",
            
            "محول بيانات": """class Extension:
    def __init__(self, editor):
        self.name = "محول البيانات"
        self.supported_formats = ['json', 'xml', 'csv']
    
    def convert(self, data, from_format, to_format):
        if from_format not in self.supported_formats:
            raise ValueError("تنسيق غير مدعوم")
        # تحويل البيانات هنا""",
            
            "واجهة API": """class Extension:
    def __init__(self, editor):
        self.name = "واجهة API"
        self.base_url = "https://api.example.com"
        self.settings = self.load_settings()
    
    async def fetch_data(self, endpoint):
        # جلب البيانات من API
        url = f"{self.base_url}/{endpoint}"
        # اتكمال الكود هنا"""
        }
        
        return templates.get(template_name, "# قالب غير متوفر")

    def _create_extension_files(self, extension_dir):
        """إنشاء ملفات الإضافة الأساسية"""
        try:
            # إنشاء الملفات الأساسية
            self.create_manifest(extension_dir)
            self.create_main_file(extension_dir)
            self.create_readme(extension_dir)
            
            # نسخ الأيقونة إذا تم تحديدها
            if hasattr(self, 'icon_path') and self.icon_path:
                icon_dest = extension_dir / "icon.png"
                shutil.copy2(self.icon_path, icon_dest)
            
            # إنشاء مجلد الموارد
            resources_dir = extension_dir / "resources"
            resources_dir.mkdir(exist_ok=True)
            
            # إنشاء ملف __init__.py
            (extension_dir / "__init__.py").touch()
            
            # إنشاء المكونات الإضافية المحددة
            if self.add_menu_cb.isChecked():
                self._create_menu_template(extension_dir)
            
            if self.add_toolbar_cb.isChecked():
                self._create_toolbar_template(extension_dir)
                
            if self.add_settings_cb.isChecked():
                self._create_settings_template(extension_dir)
                
            if self.add_api_docs_cb.isChecked():
                self._create_api_docs(extension_dir)
                
        except Exception as e:
            raise Exception(f"فشل إنشاء ملفات الإضافة: {str(e)}")

    def _create_menu_template(self, extension_dir):
        """إنشاء قالب القائمة"""
        menu_code = """
        def get_menu_items(self):
            \"\"\"إرجاع عناصر القائمة\"\"\"
            return [
                {
                    'name': 'اسم العنصر',
                    'callback': self.menu_action,
                    'shortcut': 'Ctrl+Shift+X'  # اختياري
                }
            ]
            
        def menu_action(self):
            \"\"\"تنفيذ إجراء القائمة\"\"\"
            # أضف الكود هنا
            pass
        """
        
        # إضافة الكود إلى الملف الرئيسي
        main_file = extension_dir / "main.py"
        with open(main_file, 'a', encoding='utf-8') as f:
            f.write(menu_code)

    def _create_toolbar_template(self, extension_dir):
        """إنشاء قالب شريط الأدوات"""
        toolbar_code = """
        def get_toolbar_items(self):
            \"\"\"إرجاع عناصر شريط الأدوات\"\"\"
            return [
                {
                    'name': 'اسم الأداة',
                    'icon': 'path/to/icon.png',
                    'tooltip': 'تلميح الأداة',
                    'callback': self.toolbar_action
                }
            ]
            
        def toolbar_action(self):
            \"\"\"تنفيذ إجراء شريط الأدوات\"\"\"
            # أضف الكود هنا
            pass
        """
        
        main_file = extension_dir / "main.py"
        with open(main_file, 'a', encoding='utf-8') as f:
            f.write(toolbar_code)

    def _create_settings_template(self, extension_dir):
        """إنشاء قالب الإعدادات"""
        # إنشاء ملف الإعدادات الافتراضية
        settings = {
            "enabled": True,
            "options": {
                "option1": "قيمة 1",
                "option2": "قيمة 2"
            }
        }
        
        settings_file = extension_dir / "settings.json"
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        
        # إضافة دوال الإعدادات للملف الرئيسي
        settings_code = """
        def load_settings(self):
            \"\"\"تحميل إعدادات الإضافة\"\"\"
            settings_file = Path(__file__).parent / "settings.json"
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
            
        def save_settings(self, settings):
            \"\"\"حفظ إعدادات الإضافة\"\"\"
            settings_file = Path(__file__).parent / "settings.json"
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        """
        
        main_file = extension_dir / "main.py"
        with open(main_file, 'a', encoding='utf-8') as f:
            f.write(settings_code)

    def _create_api_docs(self, extension_dir):
        """إنشاء توثيق API"""
        docs_dir = extension_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        api_docs = f"""# توثيق API الإضافة

## الدوال العامة

### `initialize()`
تهيئة الإضافة وإعداد الموارد المطلوبة.

### `cleanup()`
تنظيف الموارد وإيقاف الإضافة.

## الواجهات البرمجية

### القائمة
- `get_menu_items()`: إرجاع عناصر القائمة

### شريط الأدوات
- `get_toolbar_items()`: إرجاع عناصر شريط الأدوات

### الإعدادات
- `load_settings()`: تحميل إعدادات الإضافة
- `save_settings(settings)`: حفظ إعدادات الإضافة
"""
        
        api_file = docs_dir / "api.md"
        with open(api_file, 'w', encoding='utf-8') as f:
            f.write(api_docs)

    def reset_form(self):
        """إعادة تعيين حقول النموذج"""
        self.name_input.clear()
        self.id_input.clear()
        self.version_input.setText("1.0.0")
        self.author_input.clear()
        self.description_input.clear()
        self.requirements_input.clear()
        self.template_combo.setCurrentIndex(0)
        
        # إعادة تعيين الخيارات
        for cb in [self.add_menu_cb, self.add_toolbar_cb, 
                   self.add_settings_cb, self.add_api_docs_cb]:
            cb.setChecked(False)
        
        # إعادة تعيين الأيقونة
        self.icon_preview.clear()
        if hasattr(self, 'icon_path'):
            delattr(self, 'icon_path')
        
        # تركيز على حقل الاسم
        self.name_input.setFocus()

    def _create_main_template(self, extension_dir):
        """إنشاء قالب الملف الرئيسي"""
        main_code = '''"""
{name}
{separator}

{description}
"""
import os
from pathlib import Path

class Extension:
    """فئة الإضافة الرئيسية"""
    
    def __init__(self):
        """تهيئة الإضافة"""
        self.name = "{name}"
        self.version = "{version}"
        self.description = "{description}"
        self._initialized = False
        self.editor = None
    
    def set_editor(self, editor):
        """تعيين المحرر"""
        self.editor = editor
    
    def initialize(self):
        """تهيئة الإضافة وإعداد الموارد المطلوبة"""
        if not self._initialized and self.editor:
            # قم بإضافة كود التهيئة هنا
            self._initialized = True
    
    def cleanup(self):
        """تنظيف الموارد وإيقاف الإضافة"""
        if self._initialized:
            # قم بإضافة كود التنظيف هنا
            self._initialized = False
'''.format(
            name=self.name_input.text(),
            separator="=" * len(self.name_input.text()),
            description=self.description_input.toPlainText(),
            version=self.version_input.text()
        )
        
        main_file = extension_dir / "main.py"
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(main_code)
