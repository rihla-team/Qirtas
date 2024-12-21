import json
import os
from PyQt5.QtGui import QFont
from datetime import datetime
import time
import sys

class SettingsManager:
    def __init__(self):
        self.settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
        self.app_version = self.get_app_version()
        
        # التأكد من وجود المجلد والملف
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        
        # تحميل أو إنشاء الإعدادات وتحديث الإصدار إذا لزم الأمر
        self.initialize_settings()

    def initialize_settings(self):
        """تهيئة الإعدادات والتحقق من الإصدار"""
        try:
            if not os.path.exists(self.settings_file) or os.path.getsize(self.settings_file) == 0:
                # إنشاء ملف جديد مع الإعدادات الافتراضية
                default_settings = self.create_default_settings()
                self._save_settings_to_file(default_settings)
            else:
                # تحميل الإعدادات الحالية والتحقق من الإصدار
                current_settings = self.load_settings()
                if current_settings.get('app_version') != self.app_version:
                    # تحديث الإصدار وحفظ الإعدادات
                    current_settings['app_version'] = self.app_version
                    self._save_settings_to_file(current_settings)
                    print(f"تم تحديث إصدار التطبيق إلى: {self.app_version}")
        except Exception as e:
            print(f"خطأ في تهيئة الإعدادات: {str(e)}")
            # إنشاء ملف جديد في حالة حدوث خطأ
            default_settings = self.create_default_settings()
            self._save_settings_to_file(default_settings)

    def load_settings(self):
        """تحميل الإعدادات"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    raise ValueError("ملف الإعدادات فارغ")
                
                current_settings = json.loads(content)
                
                # التحقق من الإصدار وتحديثه إذا كان مختلفاً
                if current_settings.get('app_version') != self.app_version:
                    current_settings['app_version'] = self.app_version
                    self._save_settings_to_file(current_settings)
                    print(f"تم تحديث إصدار التطبيق إلى: {self.app_version}")
                
                # دمج مع الإعدادات الافتراضية للتأكد من وجود جميع الخيارات
                default_settings = self.create_default_settings()
                return self.validate_and_update_settings(current_settings, default_settings)
                
        except Exception as e:
            print(f"خطأ في تحميل الإعدادات: {str(e)}")
            return self.create_default_settings()

    def save_settings(self, settings):
        """حفظ الإعدادات"""
        try:
            # تحديث الإصدار قبل الحفظ
            settings['app_version'] = self.app_version
            
            validated_settings = self.validate_and_update_settings(
                settings, 
                self.create_default_settings()
            )
            return self._save_settings_to_file(validated_settings)
        except Exception as e:
            print(f"خطأ في حفظ الإعدادات: {str(e)}")
            return False

    def get_app_version(self):
        """الحصول على إصدار التطبيق من Main.py"""
        try:
            main_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Main.py')
            with open(main_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # البحث عن متغير إصدار التطبيق
                for line in content.split('\n'):
                    if 'app_version' in line and '=' in line:
                        version = line.split('=')[1].strip().strip('"\'')
                        return version
        except Exception as e:
            print(f"خطأ في قراءة إصدار التطبيق: {str(e)}")
        return "1.0.0"  # القيمة الافتراضية

    def create_default_settings(self):
        """إنشاء الإعدادات الافتراضية"""
        current_time = datetime.now().timestamp()
        return {
            "app_version": self.app_version,  # فقط في المستوى الرئيسي
            "updates": {
                "auto_check": True,
                "check_interval": "يومياً",
                "last_check": current_time
            },
            "editor": {
                "auto_save": {
                    "enabled": True,
                    "interval": 30
                },
                'theme': 'light',
                "word_wrap": True
            },
            'font': {
                'family': 'Arial',
                'size': 12,
                'bold': False,
                'italic': False,
                'underline': False
            },
            "extensions": {
                "auto_update": True,
                "update_interval": "يومياً",
                "update_time": "00:00",
                "github_token": "",
                "enabled": {},
                "disabled": []
            },
            "tabs": {
                "movable": True,
                "scroll_buttons": True,
                "elide_mode": "none",
                "max_closed_tabs": 10
            }
        }
        # حفظ الإعدادات الافتراضية
    def get_setting(self, path, default=None):
        """لحصول على إعداد معين باستخدام المسار النقطي"""
        settings = self.load_settings()
        keys = path.split('.')
        value = settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_setting(self, path, value):
        """تعيين قيمة إعداد معين باستخدام المسار النقطي"""
        settings = self.load_settings()
        keys = path.split('.')
        current = settings
        
        # التنقل عبر المسار وإنشاء القواميس إذا لم تكن موجودة
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        
        # تعيين القيمة
        current[keys[-1]] = value
        self.save_settings(settings)
    
    def validate_and_update_settings(self, current_settings, default_settings):
        """التحقق من صحة الإعدادات وتحديثها"""
        settings = current_settings.copy()
        
        # تحديث الإصدار فقط في المستوى الرئيسي
        settings['app_version'] = self.app_version
        
        # حذف app_version من الأقسام الفرعية إذا وجدت
        def remove_version_recursively(d):
            if isinstance(d, dict):
                if 'app_version' in d and d is not settings:  # تجنب حذف الإصدار الرئيسي
                    del d['app_version']
                for value in d.values():
                    remove_version_recursively(value)
        
        remove_version_recursively(settings)
        
        # التحقق من وجود جميع المفاتيح الأساسية
        for key, value in default_settings.items():
            if key not in settings:
                settings[key] = value
            elif isinstance(value, dict) and isinstance(settings[key], dict):
                # دمج الإعدادات الفرعية دون إضافة app_version
                settings[key].update({
                    k: v for k, v in value.items()
                    if k != 'app_version' and k not in settings[key]
                })
        
        return settings

    def save_font(self, font):
        """حفظ الخط"""
        font_settings = {
            'family': font.family(),
            'size': font.pointSize(),
            'bold': font.bold(),
            'italic': font.italic(),
            'underline': font.underline()
        }
        self.set_setting('font', font_settings)
        print(f"حفظ الخط: {font.family()}, {font.pointSize()}")

    def update_setting(self, key, value):
        """تحديث إعداد معين"""
        try:
            settings = self.load_settings()
            # تحديث القيمة في الإعدادات
            current = settings
            keys = key.split('.')
            
            # الوصول إلى العنصر الأخير في المسار
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # تحديث القيمة
            current[keys[-1]] = value
            
            # حفظ الإعدادات
            self.save_settings(settings)
            return True
            
        except Exception as e:
            print(f"خطأ في تحديث الإعدادات: {str(e)}")
            return False

    def apply_theme(self, theme='light'):
        """تطبيق النمط المحدد"""
        try:
            # تحديد مسار مجلد الأنماط
            if theme == 'dark':
                style_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'styles')
            else:
                style_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'styles', 'light')
            
            # قراءة ملفات الأنماط
            style_files = ['style.qss', 'sidebar.qss', 'extension_manager.qss']
            combined_style = ''
            
            for file in style_files:
                file_path = os.path.join(style_dir, file)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        combined_style += f.read() + '\n'
            
            return combined_style
        except Exception as e:
            print(f"خطأ في تحميل النمط: {str(e)}")
            return ''

    def get_font(self):
        """الحصول على الخط المحفوظ"""
        settings = self.load_settings()
        font_settings = settings.get('font', {
            'family': 'Arial',
            'size': 12,
            'bold': False,
            'italic': False,
            'underline': False
        })
        
        # إنشاء كائن الخط مع التحقق من وجود كل الخصائص
        font = QFont(
            font_settings.get('family', 'Arial'),
            font_settings.get('size', 12)
        )
        
        # تعيين الخصائص الإضافية مع قيم افتراضية
        font.setBold(font_settings.get('bold', False))
        font.setItalic(font_settings.get('italic', False))
        font.setUnderline(font_settings.get('underline', False))
        
        return font

    def _save_settings_to_file(self, settings):
        """حفظ الإعدادات إلى ملف"""
        try:
            # التحقق من صحة الإعدادات قبل الحفظ
            validated_settings = self.validate_and_update_settings(
                settings, 
                self.create_default_settings()
            )
            
            # التأكد من وجود المجلد
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(validated_settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"خطأ في حفظ الإعدادات: {str(e)}")
            return False