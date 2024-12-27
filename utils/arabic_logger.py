import logging
import os
import sys
from datetime import datetime
import tempfile
import json
import gzip
from pathlib import Path

class ArabicFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        # تحميل الترجمات من ملف JSON
        translations_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'translations.json')
        with open(translations_path, 'r', encoding='utf-8') as f:
            translations_data = json.load(f)
        
        # دمج كل القواميس في قاموس واحد
        self.translations = {}
        self.translations.update(translations_data['log_levels'])
        self.translations.update(translations_data['loggers'])
        self.translations.update(translations_data['common_messages'])
        self.translations.update(translations_data['extension_store_messages'])

    def format(self, record):
        record.levelname = self.translations.get(record.levelname, record.levelname)
        record.name = self.translations.get(record.name, record.name)
        
        if isinstance(record.msg, str):
            for eng, ar in self.translations.items():
                record.msg = record.msg.replace(eng, ar)
        
        record.asctime = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = super().format(record)
        
        if record.levelname in ['خطأ', 'تحذير', 'حرج']:
            formatted_msg = f"\n{'='*50}\n{formatted_msg}\n{'='*50}"
        elif "تم تحميل" in formatted_msg or "تم تفعيل" in formatted_msg:
            formatted_msg = f"\n{formatted_msg}"
            
        return formatted_msg

    def register_translations(self, new_translations: dict):
        """تسجيل ترجمات جديدة"""
        self.translations.update(new_translations)

def get_log_path():
    """تحديد مسار ملف السجلات"""
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(__file__))
    
    # إنشاء مجلد السجلات إذا لم يكن موجوداً
    logs_dir = os.path.join(base_path, 'سجلات')
    try:
        os.makedirs(logs_dir, exist_ok=True)
    except Exception:
        return os.path.join(base_path, 'سجلات.log')
        
    return os.path.join(logs_dir, 'سجلات.log')

class LogCompressor:
    """نظام ضغط وإدارة ملفات السجل"""
    
    def __init__(self, log_path: str, max_size_mb: int = 10, max_backup_count: int = 5):
        self.log_path = Path(log_path)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_backup_count = max_backup_count
        self._lock = False
        
        # إنشاء مجلد المضغوطات
        self.compressed_dir = self.log_path.parent / 'مضغوطات'
        try:
            self.compressed_dir.mkdir(exist_ok=True)
        except Exception:
            # إذا فشل إنشاء المجلد، استخدم المجلد الأصلي
            self.compressed_dir = self.log_path.parent

    def get_compressed_path(self, backup_number: int) -> Path:
        """الحصول على مسار الملف المضغوط"""
        return self.compressed_dir / f"{self.log_path.stem}.{backup_number}.gz"

    def compress_log(self, source_path: Path, backup_number: int) -> Path:
        """ضغط ملف السجل إلى ملف gzip"""
        compressed_path = self.get_compressed_path(backup_number)
        try:
            with open(source_path, 'rb') as src:
                content = src.read()
                with gzip.open(compressed_path, 'wb') as dst:
                    dst.write(content)
            return compressed_path
        except Exception:
            return None

    def rotate_logs(self):
        """تدوير وضغط ملفات السجل القديمة"""
        if self._lock or not self.log_path.exists():
            return
        
        try:
            # التحقق من حجم الملف
            current_size = self.log_path.stat().st_size
            if current_size < self.max_size_bytes:
                return

            self._lock = True
            
            # قراءة محتوى الملف الحالي
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                return

            # حذف أقدم نسخة إذا وجدت
            oldest_backup = self.get_compressed_path(self.max_backup_count)
            try:
                if oldest_backup.exists():
                    oldest_backup.unlink()
            except Exception:
                pass

            # تحريك النسخ المضغوطة القديمة
            for i in range(self.max_backup_count - 1, 0, -1):
                current = self.get_compressed_path(i)
                if current.exists():
                    try:
                        new_name = self.get_compressed_path(i + 1)
                        current.rename(new_name)
                    except Exception:
                        continue

            # ضغط المحتوى الحالي
            try:
                with gzip.open(self.get_compressed_path(1), 'wb') as f:
                    f.write(content.encode('utf-8'))
            except Exception:
                pass

            # إفراغ الملف الحالي
            try:
                with open(self.log_path, 'w', encoding='utf-8') as f:
                    f.write('')
            except Exception:
                pass

        finally:
            self._lock = False

class CompressedFileHandler(logging.FileHandler):
    """معالج ملفات السجل مع دعم الضغط التلقائي"""
    
    def __init__(self, filename, mode='a', encoding=None, delay=False, 
                 max_size_mb=10, max_backup_count=5):
        super().__init__(filename, mode, encoding, delay)
        self.compressor = LogCompressor(filename, max_size_mb, max_backup_count)
        self._last_check = 0
        self._check_interval = 1  # ثانية واحدة بين عمليات الفحص

    def emit(self, record):
        """كتابة السجل مع فحص حجم الملف"""
        try:
            if self.stream is None:
                self.stream = self._open()
            
            # فحص الحجم بشكل دوري
            current_time = datetime.now().timestamp()
            if current_time - self._last_check >= self._check_interval:
                self.compressor.rotate_logs()
                self._last_check = current_time
            
            super().emit(record)
            
        except Exception:
            self.handleError(record)

def setup_arabic_logging(max_size_mb=10, max_backup_count=5):
    """
    إعداد التسجيل باللغة العربية مع دعم الضغط
    
    المعاملات:
        max_size_mb: الحجم الأقصى لملف السجل بالميجابايت
        max_backup_count: عدد النسخ الاحتياطية المضغوطة
    """
    try:
        formatter = ArabicFormatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
        
        try:
            log_path = get_log_path()
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            file_handler = CompressedFileHandler(
                log_path,
                encoding='utf-8',
                max_size_mb=max_size_mb,
                max_backup_count=max_backup_count
            )
        except (PermissionError, OSError):
            temp_log_path = os.path.join(tempfile.gettempdir(), 'سجلات.log')
            file_handler = CompressedFileHandler(
                temp_log_path,
                encoding='utf-8',
                max_size_mb=max_size_mb,
                max_backup_count=max_backup_count
            )
        
        file_handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        root_logger.addHandler(file_handler)
        return formatter
        
    except Exception as e:
        with open(os.path.join(tempfile.gettempdir(), 'سجلات.log'), 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()} - خطأ في إعداد التسجيل: {str(e)}\n")
        return None

def log_in_arabic(logger, level, msg, *args, **kwargs):
    """تسجيل رسالة باللغة العربية"""
    try:
        formatter = logger.handlers[0].formatter if logger.handlers else None
        if formatter and isinstance(formatter, ArabicFormatter):
            translated_msg = msg
            for eng, ar in formatter.translations.items():
                translated_msg = translated_msg.replace(eng, ar)
            logger.log(level, translated_msg, *args, **kwargs)
        else:
            logger.log(level, msg, *args, **kwargs)
    except:
        logger.log(level, msg, *args, **kwargs)