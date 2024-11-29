from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QTextEdit, QPushButton, QFileDialog,
                           QMessageBox, QFormLayout, QComboBox, QGroupBox)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import os
import json
import shutil

class ExtensionCreatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إنشاء إضافة جديدة")
        self.setMinimumSize(600, 400)
        self.icon_path = None  # لتخزين مسار الأيقونة
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # مجموعة الأيقونة
        icon_group = QGroupBox("أيقونة الإضافة")
        icon_layout = QHBoxLayout()
        
        # عرض الأيقونة
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.set_default_icon()
        
        # أزرار التحكم بالأيقونة
        icon_buttons = QVBoxLayout()
        choose_icon_btn = QPushButton("اختيار أيقونة")
        choose_icon_btn.clicked.connect(self.choose_icon)
        reset_icon_btn = QPushButton("إعادة تعيين")
        reset_icon_btn.clicked.connect(self.set_default_icon)
        
        icon_buttons.addWidget(choose_icon_btn)
        icon_buttons.addWidget(reset_icon_btn)
        
        icon_layout.addWidget(self.icon_label)
        icon_layout.addLayout(icon_buttons)
        icon_group.setLayout(icon_layout)
        
        layout.addWidget(icon_group)

        # معلومات الإضافة الأساسية
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.id_input = QLineEdit()
        self.version_input = QLineEdit("1.0.0")
        self.author_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)

        form.addRow("اسم الإضافة:", self.name_input)
        form.addRow("معرف الإضافة:", self.id_input)
        form.addRow("الإصدار:", self.version_input)
        form.addRow("المطور:", self.author_input)
        form.addRow("الوصف:", self.description_input)

        # نوع الإضافة
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "محلل نصوص",
            "أداة تحرير",
            "إضافة مخصصة"
        ])
        form.addRow("نوع الإضافة:", self.type_combo)

        # مجلد الحفظ
        save_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        browse_btn = QPushButton("اختيار المجلد")
        browse_btn.clicked.connect(self.browse_directory)
        save_layout.addWidget(self.path_input)
        save_layout.addWidget(browse_btn)
        form.addRow("مسار الحفظ:", save_layout)

        layout.addLayout(form)

        # أزرار التحكم
        buttons = QHBoxLayout()
        create_btn = QPushButton("إنشاء الإضافة")
        create_btn.clicked.connect(self.create_extension)
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addStretch()
        buttons.addWidget(create_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addStretch()
        layout.addLayout(buttons)
        
        self.setLayout(layout)

    def set_default_icon(self):
        """تعيين الأيقونة الافتراضية"""
        self.icon_label.setText("لا توجد أيقونة")
        self.icon_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #999;
                border-radius: 5px;
                color: #999;
            }
        """)
        self.icon_path = None

    def choose_icon(self):
        """اختيار أيقونة للإضافة"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر أيقونة",
            "",
            "الصور (*.png *.jpg *.jpeg *.ico);;كل الملفات (*.*)"
        )
        
        if file_path:
            try:
                # تحميل وتحجيم الصورة
                pixmap = QPixmap(file_path)
                pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                self.icon_label.setPixmap(pixmap)
                self.icon_label.setStyleSheet("")
                self.icon_path = file_path
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"فشل تحميل الأيقونة: {str(e)}")

    def create_extension(self):
        """إنشاء الإضافة"""
        # التحقق من المدخلات
        if not all([self.name_input.text(), self.id_input.text(), 
                   self.version_input.text(), self.path_input.text()]):
            QMessageBox.warning(self, "خطأ", "يرجى ملء جميع الحقول المطلوبة")
            return

        try:
            # إنشاء مجلد الإضافة
            ext_path = os.path.join(self.path_input.text(), self.id_input.text())
            os.makedirs(ext_path, exist_ok=True)

            # نسخ الأيقونة إذا تم اختيارها
            if self.icon_path:
                icon_dest = os.path.join(ext_path, "icon.png")
                # تحويل وحفظ الأيقونة كملف PNG
                image = QImage(self.icon_path)
                image.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation).save(icon_dest)

            # إنشاء ملف manifest.json
            manifest = {
                "name": self.name_input.text(),
                "id": self.id_input.text(),
                "version": self.version_input.text(),
                "author": self.author_input.text(),
                "description": self.description_input.toPlainText(),
                "type": self.type_combo.currentText(),
                "main": "main.py",
                "icon": "icon.png" if self.icon_path else None
            }
            
            with open(os.path.join(ext_path, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=4)

            # إنشاء الملفات الأخرى
            self.create_main_file(ext_path)
            self.create_readme(ext_path, manifest)

            QMessageBox.information(self, "نجاح", "تم إنشاء الإضافة بنجاح!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إنشاء الإضافة:\n{str(e)}")

    def create_main_file(self, ext_path):
        """إنشاء الملف الرئيسي للإضافة"""
        template = f'''"""
{self.name_input.text()}
{self.description_input.toPlainText()}

المطور: {self.author_input.text()}
الإصدار: {self.version_input.text()}
"""

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.name = "{self.name_input.text()}"
        
    def initialize(self):
        """تهيئة الإضافة"""
        pass
        
    def cleanup(self):
        """تنظيف الإضافة عند إيقافها"""
        pass
'''
        with open(os.path.join(ext_path, "main.py"), "w", encoding="utf-8") as f:
            f.write(template)

    def create_readme(self, ext_path, manifest):
        """إنشاء ملف README.md"""
        template = f'''# {manifest["name"]}

{manifest["description"]}

## معلومات الإضافة
- الإصدار: {manifest["version"]}
- المطور: {manifest["author"]}
- النوع: {manifest["type"]}

## المتطلبات
- Python 3.6+
- PyQt5

## التثبيت
1. انسخ مجلد الإضافة إلى مجلد الإضافات
2. أعد تشغيل البرنامج
3. فعّل الإضافة من مدير الإضافات

## الاستخدام
[اكتب هنا تعليمات استخدام الإضافة]

## الترخيص
[اكتب هنا معلومات الترخيص]
'''
        with open(os.path.join(ext_path, "README.md"), "w", encoding="utf-8") as f:
            f.write(template)

    def browse_directory(self):
        """اختيار مجلد الحفظ"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "اختر مجلد الحفظ",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            # التحقق من وجود مجلد extensions
            if not os.path.basename(directory) == "extensions":
                # إذا لم يكن المجلد المحدد هو extensions، نقوم بإنشاء مسار داخله
                directory = os.path.join(directory, "extensions")
                # إنشاء المجلد إذا لم يكن موجوداً
                os.makedirs(directory, exist_ok=True)
            
            self.path_input.setText(directory)