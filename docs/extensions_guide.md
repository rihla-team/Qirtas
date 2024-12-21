# دليل تطوير الإضافات لمحرر قِرطاس

## المحتويات
1. [مقدمة](#مقدمة)  
2. [هيكل الإضافة](#هيكل-الإضافة)  
3. [ملف التعريف](#ملف-التعريف)  
4. [البرمجة](#البرمجة)  
5. [واجهة المستخدم](#واجهة-المستخدم)  
6. [أمثلة عملية](#أمثلة-عملية)  
7. [أفضل الممارسات](#أفضل-الممارسات)  
8. [استكشاف الأخطاء وإصلاحها](#استكشاف-الأخطاء-وإصلاحها)  

---

## مقدمة

### ما هي الإضافات؟
الإضافات (Extensions) هي وحدات برمجية مستقلة تضيف وظائف جديدة لمحرر قِرطاس. يمكن للمطورين إنشاء إضافات لتوسيع قدرات المحرر وإضافة ميزات مخصصة.

### المتطلبات الأساسية
- معرفة بلغة Python.  
- فهم أساسيات **PyQt5**.  
- استخدام نسخة حديثة من محرر قِرطاس.  

---

## هيكل الإضافة

### الهيكل الأساسي
```
extensions/
└── my_extension/       # اسم الإضافة
    ├── manifest.json    # ملف التعريف
    ├── main.py          # الملف الرئيسي
    ├── resources/       # الموارد (اختياري)
    ├──── icons/           # الأيقونات
    ├──── styles/          # ملفات التنسيق
    ├── README.md        # توثيق الإضافة
```

---

## ملف التعريف

### مثال لملف `manifest.json`
```json
{
  "name": "اسم الإضافة",
  "version": "1.0.0",
  "description": "وصف مختصر للإضافة",
  "author": "اسم المطور",
  "email": "email@example.com",
  "website": "https://example.com",
  "main": "main.py",
  "min_app_version": "1.0.0",
  "requirements": [
    "package1>=1.0.0",
    "package2>=2.0.0"
  ],
  "permissions": [
    "filesystem",
    "network"
  ]
}
```

### الحقول الإلزامية
- `name`: اسم الإضافة.  
- `version`: رقم الإصدار.  
- `description`: وصف مختصر.  
- `main`: اسم ملف البداية.  

### الحقول الاختيارية
- `author`: اسم المطور.  
- `email`: البريد الإلكتروني.  
- `website`: الموقع الإلكتروني.  
- `min_app_version`: أقل إصدار مدعوم.  
- `requirements`: المكتبات المطلوبة.  
- `permissions`: الصلاحيات المطلوبة.  

---

## البرمجة

### الهيكل الأساسي للإضافة
```python
class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.setup()

    def setup(self):
        """إعداد الإضافة"""
        pass

    def get_menu_items(self):
        """تحديد عناصر القائمة"""
        return [
            {
                'name': 'اسم العنصر',
                'callback': self.my_function
            }
        ]

    def cleanup(self):
        """تنظيف الموارد عند إيقاف الإضافة"""
        pass
```

### أمثلة على الوظائف

#### الوصول للمحرر
```python
def my_function(self):
    # الحصول على المحرر الحالي
    current_editor = self.editor.get_current_editor()

    # الحصول على النص
    text = current_editor.toPlainText()

    # تحديث النص
    new_text = text.upper()
    current_editor.setPlainText(new_text)
```

#### إضافة زر لشريط الأدوات
```python
def add_toolbar_button(self):
    toolbar = self.editor.toolBar
    action = QAction(QIcon('icon.png'), 'اسم الزر', self.editor)
    action.triggered.connect(self.my_function)
    toolbar.addAction(action)
```

#### حفظ وتحميل الإعدادات
```python
def save_settings(self):
    settings = {'key': 'value'}
    self.editor.settings_manager.save_extension_settings('my_extension', settings)

def load_settings(self):
    settings = self.editor.settings_manager.get_extension_settings('my_extension')
    print(settings)
```

---

## واجهة المستخدم

### إضافة عناصر للقائمة
```python
def get_menu_items(self):
    return [
        {
            'name': 'العنصر الأول',
            'callback': self.function1,
            'shortcut': 'Ctrl+Shift+1'
        },
        {
            'name': 'العنصر الثاني',
            'callback': self.function2,
            'icon': 'path/to/icon.png'
        }
    ]
```

### إنشاء نافذة حوار مخصصة
```python
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        button = QPushButton('زر', self)
        layout.addWidget(button)
```

---

## أمثلة عملية

### إضافة بسيطة: عداد الكلمات
```python
class WordCounterExtension:
    def __init__(self, editor):
        self.editor = editor

    def get_menu_items(self):
        return [{
            'name': 'عدد الكلمات',
            'callback': self.count_words
        }]

    def count_words(self):
        editor = self.editor.get_current_editor()
        if not editor:
            return
        text = editor.toPlainText()
        word_count = len(text.split())
        QMessageBox.information(self.editor, 'عدد الكلمات', f'عدد الكلمات في النص: {word_count}')
```

---

## أفضل الممارسات

### التنظيم
1. قسم الكود إلى وحدات منطقية.  
2. استخدم التعليقات لتوضيح الكود.  
3. اتبع معايير **PEP 8** لتنسيق الكود.  

### الأداء
1. تجنب العمليات الثقيلة في الحلقة الرئيسية.  
2. استخدم الخيوط للعمليات الطويلة.  
3. نظف الموارد عند إيقاف الإضافة.  

### الأمان
1. تحقق من المدخلات.  
2. استخدم try/except للتعامل مع الأخطاء.  
3. لا تخزن بيانات حساسة بشكل غير آمن.  

---

## استكشاف الأخطاء وإصلاحها

### السجلات
```python
import logging

logger = logging.getLogger('my_extension')

def my_function():
    try:
        # العملية
        logger.info('تم التنفيذ بنجاح')
    except Exception as e:
        logger.error(f'حدث خطأ: {str(e)}')
```

### الأخطاء الشائعة
1. **عدم تحميل الإضافة**  
   - تحقق من `manifest.json`.  
   - تأكد من وجود جميع المتطلبات.  

2. **أخطاء واجهة المستخدم**  
   - تحقق من تسلسل العمليات.  
   - تأكد من تحديثات واجهة المستخدم في الخيط الرئيسي.  

3. **مشاكل الأداء**  
   - استخدم أدوات التتبع.  
   - قم بتحسين العمليات الثقيلة.  

---

## الدعم
- راجع [قسم المساعدة](https://example.com/help).  
- انضم إلى [مجتمع المطورين](https://example.com/community).  
- أبلغ عن [الأخطاء](https://example.com/issues).  