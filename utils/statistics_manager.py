from PyQt5.QtWidgets import QLabel, QStatusBar, QMenu, QAction
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import QObject, pyqtSignal, Qt
import json
import os
import re
from functools import lru_cache
import pathlib
from utils.arabic_logger import setup_arabic_logging, log_in_arabic
import logging

# إعداد التسجيل العربي
formatter = setup_arabic_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class StatisticsPlugin:
    """الفئة الأساسية لإضافات الإحصائيات"""
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.enabled = True
    
    def calculate_stats(self, text: str) -> dict:
        """حساب إحصائيات إضافية"""
        return {}
    
    def format_stat(self, key: str, value) -> str:
        """تنسيق عرض الإحصائية"""
        return f"{key}: {value}"

class StatisticsManager(QObject):
    statistics_changed = pyqtSignal(dict)
    file_settings_changed = pyqtSignal(dict)
    
    def __init__(self, status_bar: QStatusBar):
        super().__init__()
        self.status_bar = status_bar
        self.stats_labels = {}
        self.plugins = []
        self._cache = {}  # تخزين مؤقت للإحصائيات
        self._word_pattern = re.compile(r'\S+')  # نمط للكلمات
        self.language_names = self._load_language_names()
        self.code_patterns = self._load_code_patterns()
        
        # أنظمة التخزين المؤقت المحسنة
        self._file_type_cache = {}  # تخزين مؤقت لأنواع الملفات حسب المسار
        self._content_type_cache = {}  # تخزين مؤقت لأنواع الملفات حسب المحتوى
        self._extension_type_cache = {}  # تخزين مؤقت لأنواع الملفات حسب الامتداد
        self._editor_file_types = {}  # تخزين نوع الملف لكل محرر
        self._editor_file_paths = {}  # تخزين مسار الملف لكل محرر
        self._current_editor = None  # المحرر الحالي
        
        # حجم الذاكرة المؤقتة
        self._max_cache_size = 1000
        
        # إعداد المؤشرات الأساسية
        self.setup_statistics()
        self.setup_statistics_widgets()

    @lru_cache(maxsize=1)
    def _load_language_names(self):
        """تحميل أسماء اللغات من الملف مع تخزين مؤقت"""
        try:
            file_path = os.path.join('resources', 'language_names.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                log_in_arabic(logger, logging.INFO, f"تم تحميل أسماء اللغات من: {file_path}")
                return json.load(f)
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تحميل أسماء اللغات: {str(e)}")
            return {}

    @lru_cache(maxsize=1)
    def _load_code_patterns(self):
        """تحميل أنماط اللغات البرمجية من الملف مع تخزين مؤقت"""
        try:
            file_path = os.path.join('resources', 'code_patterns.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                log_in_arabic(logger, logging.INFO, f"تم تحميل أنماط اللغات البرمجية من: {file_path}")
                return json.load(f)
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تحميل أنماط اللغات البرمجية: {str(e)}")
            return {}

    def _calculate_basic_stats(self, text: str) -> dict:
        """حساب الإحصائيات الأساسية بشكل أسرع"""
        if not text:
            return {'chars': 0, 'words': 0, 'lines': 1}
            
        # حساب الإحصائيات الأساسية بشكل أسرع
        chars = len(text)
        words = len(self._word_pattern.findall(text))
        lines = text.count('\n') + 1
        
        return {'chars': chars, 'words': words, 'lines': lines}

    def add_plugin(self, plugin: StatisticsPlugin):
        """إضافة إضافة جديدة"""
        if isinstance(plugin, StatisticsPlugin):
            self.plugins.append(plugin)
            # إنشاء مؤشر جديد للإضافة
            label = QLabel()
            label.setStyleSheet("padding: 0 10px;")
            self.status_bar.addPermanentWidget(label)
            self.stats_labels[plugin.name] = label
    
    def remove_plugin(self, plugin_name: str):
        """إزالة إضافة"""
        if plugin_name in self.stats_labels:
            # إزالة المؤشر من شريط الحالة
            self.status_bar.removeWidget(self.stats_labels[plugin_name])
            del self.stats_labels[plugin_name]
        self.plugins = [p for p in self.plugins if p.name != plugin_name]
        
    def _detect_file_type_by_content(self, content: str) -> str:
        """التعرف على نوع الملف من محتواه"""
        if not content:
            return 'Text'

        # تقسيم المحتوى إلى أسطر
        lines = content.split('\n')[:50]  # فحص أول 50 سطر فقط
        
        # عداد لكل لغة
        language_scores = {lang: 0 for lang in self.code_patterns.keys()}
        
        # فحص كل سطر
        for line in lines:
            for lang, patterns in self.code_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        language_scores[lang] += 1
        
        # اختيار اللغة مع أعلى نتيجة
        max_score = max(language_scores.values())
        if max_score > 0:
            for lang, score in language_scores.items():
                if score == max_score:
                    return lang.capitalize()
        
        return 'Text'

    def _get_extension_type(self, ext: str) -> str:
        """الحصول على نوع الملف من الامتداد مع التخزين المؤقت"""
        if ext in self._extension_type_cache:
            return self._extension_type_cache[ext]
            
        file_type = self.language_names.get(ext)
        if file_type:
            self._extension_type_cache[ext] = file_type
            
        return file_type

    def _get_content_type(self, content: str) -> str:
        """الحصول على نوع الملف من المحتوى مع التخزين المؤقت"""
        # استخدام هاش المحتوى كمفتاح للتخزين المؤقت
        content_hash = hash(content[:1000])  # استخدام أول 1000 حرف فقط للهاش
        
        if content_hash in self._content_type_cache:
            return self._content_type_cache[content_hash]
            
        detected_type = self._detect_file_type_by_content(content)
        if detected_type != 'Text':
            self._content_type_cache[content_hash] = detected_type
            
            # تنظيف الذاكرة المؤقتة إذا كانت كبيرة جداً
            if len(self._content_type_cache) > self._max_cache_size:
                # حذف نصف العناصر الأقدم
                keys_to_remove = list(self._content_type_cache.keys())[:self._max_cache_size//2]
                for key in keys_to_remove:
                    del self._content_type_cache[key]
                    
        return detected_type

    def _detect_file_type(self, file_path: str = None, content: str = None) -> str:
        """التعرف على نوع الملف من امتداده أو محتواه مع التخزين المؤقت"""
        # التحقق من التخزين المؤقت للملف
        if file_path and file_path in self._file_type_cache:
            return self._file_type_cache[file_path]

        detected_type = None
        
        # الأولوية الأولى: التعرف من الامتداد
        if file_path:
            ext = pathlib.Path(file_path).suffix.lower().lstrip('.')
            # التحقق من الامتداد في التخزين المؤقت
            if ext in self._extension_type_cache:
                detected_type = self._extension_type_cache[ext]
            # التحقق من الامتداد في قائمة اللغات
            elif ext in self.language_names:
                detected_type = self.language_names[ext]
                self._extension_type_cache[ext] = detected_type
                return detected_type  # إرجاع النوع مباشرة إذا تم التعرف عليه من الامتداد
        
        # الأولوية الثانية: التعرف من اسم الملف
        if not detected_type and file_path:
            name = pathlib.Path(file_path).name
            if name in self.language_names:
                detected_type = self.language_names[name]
        
        # الأولوية الثالثة: التعرف من المحتوى
        if not detected_type and content:
            detected_type = self._get_content_type(content)
        
        # استخدام النوع الافتراضي إذا لم يتم التعرف على النوع
        detected_type = detected_type or self.language_names.get("Text", "نص عادي")
        
        # تخزين النوع في الذاكرة المؤقتة للملف
        if file_path:
            self._file_type_cache[file_path] = detected_type
            
            # تنظيف الذاكرة المؤقتة إذا كانت كبيرة جداً
            if len(self._file_type_cache) > self._max_cache_size:
                # حذف نصف العناصر الأقدم
                keys_to_remove = list(self._file_type_cache.keys())[:self._max_cache_size//2]
                for key in keys_to_remove:
                    del self._file_type_cache[key]
        
        return detected_type

    def set_current_editor(self, editor):
        """تعيين المحرر الحالي وتحديث نوع الملف"""
        if editor == self._current_editor:
            return  # لا داعي للتحديث إذا كان نفس المحرر
            
        self._current_editor = editor
        if editor:
            # تحديث نوع الملف للمحرر الحالي
            file_type = self._editor_file_types.get(editor)
            if file_type and 'file_type' in self.stats_labels:
                self.stats_labels['file_type'].setText(f"نوع الملف: {file_type}")
                log_in_arabic(logger, logging.INFO, f"تم استعادة نوع الملف من الذاكرة: {file_type}")

    def update_file_type(self, file_path: str = None, content: str = None):
        """تحديث نوع الملف في شريط الحالة"""
        if not self._current_editor:
            return None

        # التحقق مما إذا كان الملف قد تم تحليله من قبل
        if self._current_editor in self._editor_file_types:
            stored_path = self._editor_file_paths.get(self._current_editor)
            if stored_path == file_path:  # نفس الملف، لا داعي لإعادة التحليل
                file_type = self._editor_file_types[self._current_editor]
                if 'file_type' in self.stats_labels:
                    arabic_name = self.language_names.get(file_type, file_type)
                    self.stats_labels['file_type'].setText(f"نوع الملف: {arabic_name}")
                log_in_arabic(logger, logging.INFO, f"استخدام نوع الملف المخزن: {file_type}")
                return file_type

        # تحليل نوع الملف للمرة الأولى أو عند تغيير المسار
        detected_type = self._detect_file_type(file_path, content)
        if detected_type:
            # تخزين نوع الملف ومساره للمحرر الحالي
            self._editor_file_types[self._current_editor] = detected_type
            self._editor_file_paths[self._current_editor] = file_path
            
            if 'file_type' in self.stats_labels:
                arabic_name = self.language_names.get(detected_type, detected_type)
                self.stats_labels['file_type'].setText(f"نوع الملف: {arabic_name}")
            log_in_arabic(logger, logging.INFO, f"تم تحديد نوع الملف: {detected_type}")
        
        return detected_type

    def remove_editor(self, editor):
        """إزالة المحرر وبياناته عند إغلاق التبويب"""
        if editor in self._editor_file_types:
            del self._editor_file_types[editor]
        if editor in self._editor_file_paths:
            del self._editor_file_paths[editor]
        if editor in self._file_type_cache:
            del self._file_type_cache[editor]
        if self._current_editor == editor:
            self._current_editor = None
        log_in_arabic(logger, logging.INFO, "تم إزالة بيانات المحرر")

    def update_statistics(self, text: str = None, cursor_info: dict = None, file_type: str = None):
        """تحديث جميع الإحصائيات مع تخزين مؤقت"""
        try:
            stats = {}
            
            # تحديث نوع الملف فقط إذا تم تمريره
            if file_type and self._current_editor:
                detected_type = self._detect_file_type(file_type)
                self._editor_file_types[self._current_editor] = detected_type
                if 'file_type' in self.stats_labels:
                    self.stats_labels['file_type'].setText(f"نوع الملف: {detected_type}")
                stats['file_type'] = detected_type
            
            if text is not None:
                # التحقق من التخزين المؤقت
                cache_key = hash(text)
                if cache_key in self._cache:
                    stats = self._cache[cache_key]
                else:
                    # حساب الإحصائيات الأساسية
                    stats = self._calculate_basic_stats(text)
                    
                    # إحصائيات الإضافات
                    for plugin in [p for p in self.plugins if p.enabled]:
                        try:
                            plugin_stats = plugin.calculate_stats(text)
                            if plugin_stats:
                                for key, value in plugin_stats.items():
                                    formatted_value = plugin.format_stat(key, value)
                                    if plugin.name in self.stats_labels:
                                        self.stats_labels[plugin.name].setText(formatted_value)
                                    stats[f"{plugin.name}_{key}"] = value
                        except Exception as e:
                            log_in_arabic(logger, logging.ERROR, f"خطأ في إضافة {plugin.name}: {str(e)}")
                    
                    # تخزين النتائج في الذاكرة المؤقتة
                    self._cache[cache_key] = stats
                    
                    # تنظيف الذاكرة المؤقتة إذا كانت كبيرة جداً
                    if len(self._cache) > 1000:
                        self._cache.clear()
                
                # تحديث المؤشرات الأساسية
                self._update_basic_labels(stats)
            
            # تحديث موقع المؤشر
            if cursor_info and 'cursor' in self.stats_labels:
                cursor_text = f"سطر: {cursor_info.get('line', 1)} | عمود: {cursor_info.get('column', 1)}"
                self.stats_labels['cursor'].setText(cursor_text)
                stats['cursor'] = cursor_info

        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تحديث الإحصائيات: {str(e)}")
            
    def _update_basic_labels(self, stats):
        """تحديث المؤشرات الأساسية"""
        if 'chars' in stats and 'chars' in self.stats_labels:
            self.stats_labels['chars'].setText(f"الأحرف: {stats['chars']}")
        if 'words' in stats and 'words' in self.stats_labels:
            self.stats_labels['words'].setText(f"الكلمات: {stats['words']}")
        if 'lines' in stats and 'lines' in self.stats_labels:
            self.stats_labels['lines'].setText(f"الأسطر: {stats['lines']}")
    
    def setup_statistics_widgets(self):
        """إعداد مؤشرات الإحصائيات في شريط الحالة"""
        # إنشاء المؤشرات القابلة للنقر
        self.encoding_label = QLabel("UTF-8", self.status_bar)
        self.encoding_label.setStyleSheet("""
            QLabel { 
                padding: 0 10px; 
                color: #666;
                border-right: 1px solid #666;
            }
            QLabel:hover { 
                color: #fff;
                background-color: #444;
            }
        """)
        self.encoding_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.encoding_label.mousePressEvent = lambda e: self.show_encodings_menu(e)
        
        self.line_ending_label = QLabel("LF", self.status_bar)
        self.line_ending_label.setStyleSheet("""
            QLabel { 
                padding: 0 10px; 
                color: #666;
                border-right: 1px solid #666;
            }
            QLabel:hover { 
                color: #fff;
                background-color: #444;
            }
        """)
        self.line_ending_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.line_ending_label.mousePressEvent = lambda e: self.show_line_endings_menu(e)
        
        # إضافة المؤشرات للشريط
        self.status_bar.addPermanentWidget(self.line_ending_label)
        self.status_bar.addPermanentWidget(self.encoding_label)

    def show_encodings_menu(self, event):
        """عرض قائمة الترميزات"""
        menu = QMenu()
        encodings = [
            ("صيغة التحويل الموحد-8", "UTF-8"),
            ("صيغة التحويل الموحد-8 مع BOM", "UTF-8-SIG"),
            ("صيغة التحويل الموحد-16 الصغيرة", "UTF-16"),
            ("صيغة التحويل الموحد-16 الكبيرة", "utf-16-be"),
            ("صيغة التحويل الموحد-32 الصغيرة", "utf-32-le"),
            ("صيغة التحويل الموحد-32 الكبيرة", "utf-32-be")
        ]
        
        for name, encoding in encodings:
            action = QAction(name, menu)
            action.setCheckable(True)
            action.setChecked(self.current_encoding == encoding if hasattr(self, 'current_encoding') else encoding == "UTF-8")
            action.triggered.connect(lambda checked, e=encoding: self.change_file_encoding(e))
            menu.addAction(action)
        
        menu.exec_(self.encoding_label.mapToGlobal(event.pos()))

    def show_line_endings_menu(self, event):
        """عرض قائمة نهايات الأسطر"""
        menu = QMenu()
        line_endings = [
            ("ويندوز (سي إر إل في - سطر جديد + ��رجاع الحامل)", "\r\n"),
            ("يونكس (ال اف - سطر جديد)", "\n"),
            ("ماك (ال ار - إرجاع الحامل)", "\r")
        ]
        
        for name, ending in line_endings:
            action = QAction(name, menu)
            action.setCheckable(True)
            action.setChecked(self.current_line_ending == ending if hasattr(self, 'current_line_ending') else ending == "\n")
            action.triggered.connect(lambda checked, e=ending: self.change_line_ending(e))
            menu.addAction(action)
        
        menu.exec_(self.line_ending_label.mapToGlobal(event.pos()))

    def change_file_encoding(self, encoding):
        """تغيير ترميز الملف"""
        self.current_encoding = encoding
        self.encoding_label.setText(encoding)
        self.file_settings_changed.emit({
            'encoding': encoding,
            'line_ending': getattr(self, 'current_line_ending', '\n')
        })

    def change_line_ending(self, ending):
        """تغيير نوع نهاية الأسطر"""
        self.current_line_ending = ending
        ending_text = "CRLF" if ending == "\r\n" else "LF" if ending == "\n" else "CR"
        self.line_ending_label.setText(ending_text)
        self.file_settings_changed.emit({
            'encoding': getattr(self, 'current_encoding', 'UTF-8'),
            'line_ending': ending
        })

    def setup_statistics(self):
        """إعداد مؤشرات الإحصائيات الأساسية"""
        default_stats = {
            'cursor': {'label': "سطر: 1 | عمود: 1", 'permanent': False},
            'chars': {'label': "الأحرف: 0", 'permanent': True},
            'words': {'label': "الكلمات: 0", 'permanent': True},
            'lines': {'label': "الأسطر: 0", 'permanent': True},
            'file_type': {'label': "نوع الملف: نص عادي", 'permanent': True},
        }
        
        for stat_id, stat_info in default_stats.items():
            label = QLabel(stat_info['label'])
            label.setStyleSheet("padding: 0 10px;")
            
            if stat_info['permanent']:
                self.status_bar.addPermanentWidget(label)
            else:
                self.status_bar.addWidget(label)
                
            self.stats_labels[stat_id] = label

    def clear_caches(self):
        """تنظيف جميع الذواكر المؤقتة"""
        self._file_type_cache.clear()
        self._content_type_cache.clear()
        self._extension_type_cache.clear()
        self._editor_file_types.clear()
        self._editor_file_paths.clear()
        self._cache.clear()
        log_in_arabic(logger, logging.INFO, "تم تنظيف جميع الذواكر المؤقتة")