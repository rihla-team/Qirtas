import logging
import os
import sys
from datetime import datetime

class ArabicFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.translations = {
            # مستويات السجل
            'DEBUG': 'تصحيح',
            'INFO': 'معلومات',
            'WARNING': 'تحذير',
            'ERROR': 'خطأ',
            'CRITICAL': 'حرج',
            'Popen': 'تشغيل عملية',
            'git.cmd': 'أمر جيت',
            
            # أسماء المسجلات
            'ExtensionsManager': 'مدير الإضافات',
            'UpdateManager': 'مدير التحديثات',
            'git.cmd': 'أمر جيت',
            'urllib3.connectionpool': 'مجمع اتصالات مكتبة الروابط الشبكية 3',
            'utils.extension_store': 'متجر الإضافات',  # إضافة ترجمة جديدة
            'ArabicTerminal': 'مدير الإضافات',
            'update_manager': 'مدير التحديثات',
            'terminal_widget': 'مدير الإضافات',
            'utils.update_manager': 'مدير التحديثات',
            'utils.extension_store': 'متجر الإضافات',

            # رسائل شائعة
            'Starting new HTTPS connection': 'بدء اتصال بروتوكول النص التشعبي الآمن جديد',
            'Starting new HTTPS connection (1)': 'بدء اتصال بروتوكول النص التشعبي الآمن جديد (1)',
            'GET': 'طلب استعلام',
            'Extension loaded': 'تم تحميل الإضافة',
            'Extension activated': 'تم تفعيل الإضافة',
            'Extension deactivated': 'تم تعطيل الإضافة',
            'Loading style file': 'تم تحميل ملف التنسيق',
            'Popen': 'تشغيل عملية',
            'git version': 'إصدار جيت',
            'universal_newlines': 'أسطر جديدة عالمية',
            'shell': 'صدفة',
            'istream': 'مجرى الإدخال',
            'cwd': 'مجلد العمل الحالي',
            
            # رسائل متجر الإضافات
            'Using proactor': 'استخدام المعالج',
            'IocpProactor': 'معالج النظام',
            'asyncio': 'المزامنة التلقائية'
        }

    def format(self, record):
        # ترجمة مستوى السجل
        record.levelname = self.translations.get(record.levelname, record.levelname)
        
        # ترجمة اسم المسجل
        record.name = self.translations.get(record.name, record.name)
        
        # معالجة الرسالة
        if isinstance(record.msg, str):
            # ترجمة الرسائل المعروفة
            msg = record.msg
            for eng, ar in self.translations.items():
                msg = msg.replace(eng, ar)
                        
            record.msg = msg

        # تنسيق التاريخ والوقت
        record.asctime = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # إضافة مسافات للتنسيق
        formatted_msg = super().format(record)
        
        # إضافة خط فاصل للأخطاء والتحذيرات
        if record.levelname in ['خطأ', 'تحذير', 'حرج']:
            formatted_msg = f"\n{'='*50}\n{formatted_msg}\n{'='*50}"
        
        # إضافة مسافة بين السجلات المتعلقة بالإضافات
        if "تم تحميل" in formatted_msg or "تم تفعيل" in formatted_msg:
            formatted_msg = f"\n{formatted_msg}"
            
        return formatted_msg

    def register_translations(self, new_translations: dict):
        """تسجيل ترجمات جديدة"""
        self.translations.update(new_translations)

def get_log_path():
    """تحديد مسار ملف السجلات بناءً على نوع التشغيل"""
    if getattr(sys, 'frozen', False):
        # إذا كان التطبيق EXE
        application_path = os.path.dirname(sys.executable)
        return os.path.join(application_path, 'سجلات.log')
    else:
        # إذا كان التطبيق في وضع التطوير
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'سجلات.log')

def ensure_log_directory():
    """التأكد من وجود مجلد السجلات"""
    log_path = get_log_path()
    log_dir = os.path.dirname(log_path)
    
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception as e:
            # في حالة فشل إنشاء المجلد، استخدم المجلد المؤقت
            import tempfile
            return os.path.join(tempfile.gettempdir(), 'سجلات.log')
    
    return log_path

def setup_arabic_logging():
    """إعداد التسجيل باللغة العربية"""
    try:
        # إنشاء المنسق العربي
        formatter = ArabicFormatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        
        # تحديد مسار ملف السجلات
        log_file = ensure_log_directory()
        
        # إعداد معالج الملف مع التعامل مع الأخطاء
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        except PermissionError:
            # في حالة عدم وجود صلاحيات، استخدم المجلد المؤقت
            import tempfile
            temp_log = os.path.join(tempfile.gettempdir(), 'سجلات.log')
            file_handler = logging.FileHandler(temp_log, encoding='utf-8')
        
        file_handler.setFormatter(formatter)
        
        # إعداد المسجل الرئيسي
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # إزالة جميع المعالجات القديمة
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # إضافة المعالج الجديد
        root_logger.addHandler(file_handler)
        
        return formatter
        
    except Exception as e:
        # في حالة حدوث أي خطأ، نقوم بتسجيل الخطأ في المجلد المؤقت
        import tempfile
        error_log = os.path.join(tempfile.gettempdir(), 'error.log')
        with open(error_log, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()} - خطأ في إعداد التسجيل: {str(e)}\n")
        return None

def get_arabic_formatter():
    """الحصول على منسق السجلات العربية"""
    try:
        return logging.getLogger().handlers[0].formatter
    except:
        return None

def log_in_arabic(logger, level, msg, *args, **kwargs):
    """تسجيل رسالة باللغة العربية"""
    try:
        formatter = get_arabic_formatter()
        if formatter:
            translated_msg = msg
            for eng, ar in formatter.translations.items():
                translated_msg = translated_msg.replace(eng, ar)
            logger.log(level, translated_msg, *args, **kwargs)
    except:
        # في حالة فشل التسجيل، نستخدم التسجيل العادي
        logger.log(level, msg, *args, **kwargs)