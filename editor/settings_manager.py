# editor/settings_manager.py
try:
    import json
    from pathlib import Path
    from PyQt5.QtGui import QFont
    from datetime import datetime
    from functools import lru_cache
    from typing import Dict, Any, Optional
    from utils.arabic_logger import log_in_arabic, setup_arabic_logging
    import logging
except Exception as e:
    try:
        import logging
        logger = logging.getLogger(__name__)
        log_in_arabic(logger, logging.ERROR, f"خطأ في تحميل المكتبات: {e}")
    except Exception as e:
        print(f"خطأ في تحميل المكتبات: {e}")
formatter = setup_arabic_logging()
        
class SettingsManager:
    STYLE_FILES = ['style.qss', 'sidebar.qss', 'extension_manager.qss']
    DEFAULT_FONT = {
        "family": "Arial",
        "size": 12,
        "bold": False,
        "italic": False,
        "underline": False
    }

    def __init__(self):
        try:
            base_dir = Path(__file__).parent.parent
            self.settings_file = base_dir / 'resources' / 'settings.json'
            self.styles_dir = base_dir / 'resources' / 'styles'
            self.logger = logging.getLogger(__name__)
            self.app_version = self._get_app_version()
            self._settings_cache: Optional[Dict[str, Any]] = None
            self.initialize_settings()
            self.logger.info("تم تهيئة مدير الإعدادات بنجاح")
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة مدير الإعدادات: {str(e)}")
            raise

    def initialize_settings(self) -> None:
        """تهيئة الإعدادات"""
        try:
            if not self.settings_file.exists() or self.settings_file.stat().st_size == 0:
                self.logger.info("إنشاء ملف إعدادات جديد")
                self._save_settings_to_file(self.create_default_settings())
            self._settings_cache = self.load_settings()
            self.logger.info("تم تهيئة الإعدادات بنجاح")
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة الإعدادات: {str(e)}")
            self._settings_cache = self.create_default_settings()
            self._save_settings_to_file(self._settings_cache)

    def load_settings(self) -> Dict[str, Any]:
        """تحميل الإعدادات"""
        try:
            if self._settings_cache:
                return self._settings_cache

            current_settings = json.loads(self.settings_file.read_text(encoding='utf-8').strip() or '{}')
            validated_settings = self.validate_and_update_settings(current_settings)
            self.logger.info("تم تحميل الإعدادات بنجاح")
            return validated_settings
        except Exception as e:
            self.logger.error(f"خطأ في تحميل الإعدادات: {str(e)}")
            return self.create_default_settings()

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """حفظ الإعدادات"""
        try:
            validated_settings = self.validate_and_update_settings(settings)
            if self._save_settings_to_file(validated_settings):
                self._settings_cache = validated_settings
                self.logger.info("تم حفظ الإعدادات بنجاح")
                return True
            return False
        except Exception as e:
            self.logger.error(f"خطأ في حفظ الإعدادات: {str(e)}")
            return False

    @lru_cache(maxsize=1)
    def _get_app_version(self) -> str:
        """الحصول على إصدار التطبيق"""
        try:
            main_file = self.settings_file.parent.parent / 'Main.py'
            content = main_file.read_text(encoding='utf-8')
            if version_line := next((line for line in content.splitlines() if 'app_version' in line and '=' in line), None):
                version = version_line.split('=')[1].strip().strip('"\'')
                self.logger.info(f"تم العثور على إصدار التطبيق: {version}")
                return version
        except Exception as e:
            self.logger.error(f"خطأ في قراءة إصدار التطبيق: {str(e)}")
        return "1.0.0"

    def get_setting(self, path: str, default: Any = None) -> Any:
        """الحصول على إعداد معين"""
        try:
            value = self._settings_cache or self.load_settings()
            for key in path.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError) as e:
            self.logger.warning(f"لم يتم العثور على الإعداد {path}, استخدام القيمة الافتراضية")
            return default
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الإعداد {path}: {str(e)}")
            return default

    def set_setting(self, path: str, value: Any) -> bool:
        """تعيين قيمة إعداد معين"""
        try:
            settings = self._settings_cache or self.load_settings()
            current = settings
            *keys, last_key = path.split('.')
            
            for key in keys:
                current = current.setdefault(key, {})
            current[last_key] = value
            
            success = self.save_settings(settings)
            if success:
                self.logger.info(f"تم تحديث الإعداد {path} بنجاح")
            return success
        except Exception as e:
            self.logger.error(f"خطأ في تعيين الإعداد {path}: {str(e)}")
            return False

    def validate_and_update_settings(self, current_settings: Dict[str, Any]) -> Dict[str, Any]:
        """التحقق من صحة الإعدادات وتحديثها"""
        try:
            settings = current_settings.copy()
            settings['app_version'] = self.app_version
            default_settings = self.create_default_settings()
            
            def update_dict_recursively(current: Dict[str, Any], default: Dict[str, Any]) -> None:
                try:
                    for key, value in default.items():
                        if key not in current:
                            current[key] = value
                        elif isinstance(value, dict) and isinstance(current[key], dict):
                            update_dict_recursively(current[key], value)
                except Exception as e:
                    self.logger.error(f"خطأ في تحديث القاموس: {str(e)}")
            
            update_dict_recursively(settings, default_settings)
            self.logger.info("تم التحقق من صحة الإعدادات وتحديثها")
            return settings
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من صحة الإعدادات: {str(e)}")
            return default_settings

    def get_font(self) -> QFont:
        """الحصول على الخط المحفوظ"""
        try:
            font_settings = self.get_setting('font', self.DEFAULT_FONT)
            font = QFont(
                font_settings.get('family', self.DEFAULT_FONT['family']),
                font_settings.get('size', self.DEFAULT_FONT['size'])
            )
            font.setBold(font_settings.get('bold', self.DEFAULT_FONT['bold']))
            font.setItalic(font_settings.get('italic', self.DEFAULT_FONT['italic']))
            font.setUnderline(font_settings.get('underline', self.DEFAULT_FONT['underline']))
            self.logger.info(f"تم تحميل الخط: {font.family()}, {font.pointSize()}")
            return font
        except Exception as e:
            self.logger.error(f"خطأ في تحميل الخط: {str(e)}")
            return QFont()

    def save_font(self, font: QFont) -> bool:
        """حفظ الخط"""
        try:
            success = self.set_setting('font', {
                'family': font.family(),
                'size': font.pointSize(),
                'bold': font.bold(),
                'italic': font.italic(),
                'underline': font.underline()
            })
            if success:
                self.logger.info(f"تم حفظ الخط: {font.family()}, {font.pointSize()}")
            return success
        except Exception as e:
            self.logger.error(f"خطأ في حفظ الخط: {str(e)}")
            return False

    @lru_cache(maxsize=2)
    def apply_theme(self, theme: str = 'light') -> str:
        """تطبيق النمط المحدد"""
        try:
            style_dir = self.styles_dir if theme == 'dark' else self.styles_dir / 'light'
            style_contents = []
            
            for file in self.STYLE_FILES:
                try:
                    file_path = style_dir / file
                    if file_path.exists():
                        style_contents.append(file_path.read_text(encoding='utf-8'))
                except Exception as e:
                    self.logger.error(f"خطأ في قراءة ملف النمط {file}: {str(e)}")
            
            if style_contents:
                self.logger.info(f"تم تطبيق النمط {theme} بنجاح")
                return '\n'.join(style_contents)
            else:
                self.logger.warning(f"لم يتم العثور على ملفات النمط {theme}")
                return ''
        except Exception as e:
            self.logger.error(f"خطأ في تطبيق النمط {theme}: {str(e)}")
            return ''

    def _save_settings_to_file(self, settings: Dict[str, Any]) -> bool:
        """حفظ الإعدادات إلى ملف"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            self.settings_file.write_text(
                json.dumps(settings, indent=4, ensure_ascii=False),
                encoding='utf-8'
            )
            self.logger.info("تم حفظ الإعدادات في الملف بنجاح")
            return True
        except Exception as e:
            self.logger.error(f"خطأ في حفظ الإعدادات في الملف: {str(e)}")
            return False

    def create_default_settings(self) -> Dict[str, Any]:
        """إنشاء الإعدادات الافتراضية"""
        try:
            current_time = datetime.now().timestamp()
            default_settings = {
                "app_version": self.app_version,
                "updates": {
                    "auto_check": True,
                    "check_interval": "يومياً",
                    "last_check": current_time
                },
                "editor": {
                    "auto_save": {"enabled": True, "interval": 30},
                    "theme": "light",
                    "word_wrap": True
                },
                "font": self.DEFAULT_FONT.copy(),
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
            self.logger.info("تم إنشاء الإعدادات الافتراضية بنجاح")
            return default_settings
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء الإعدادات الافتراضية: {str(e)}")
            # إرجاع إعدادات أساسية جداً في حالة الخطأ
            return {
                "app_version": "1.0.0",
                "editor": {"theme": "light"},
                "font": self.DEFAULT_FONT.copy()
            }