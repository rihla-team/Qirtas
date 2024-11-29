import json
import os
from PyQt5.QtGui import QFont

class SettingsManager:
    def __init__(self):
        self.settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
        
    def get_setting(self, path, default=None):
        """الحصول على إعداد معين باستخدام المسار النقطي"""
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
    
    def load_settings(self):
        """تحميل الإعدادات من الملف"""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_settings(self, settings):
        """حفظ الإعدادات في الملف"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

    def get_font(self):
        """الحصول على الخط المحفوظ"""
        settings = self.load_settings()
        font_settings = settings.get('font', {
            'family': 'Consolas',
            'size': 13,
            'bold': False,
            'italic': False,
            'underline': False
        })
        
        font = QFont(font_settings['family'], font_settings['size'])
        font.setBold(font_settings['bold'])
        font.setItalic(font_settings['italic'])
        font.setUnderline(font_settings['underline'])
        
        return font

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