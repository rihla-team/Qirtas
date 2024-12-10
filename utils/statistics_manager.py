from PyQt5.QtWidgets import QLabel, QStatusBar
from PyQt5.QtCore import QObject, pyqtSignal
import json
import os

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
    
    def __init__(self, status_bar: QStatusBar):
        super().__init__()
        self.status_bar = status_bar
        self.stats_labels = {}
        self.plugins = []  # قائمة الإضافات
        self.language_names = self._load_language_names()
        self.setup_statistics()
        
    def _load_language_names(self):
        """تحميل أسماء اللغات من الملف"""
        try:
            file_path = os.path.join('resources', 'language_names.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"خطأ في تحميل أسماء اللغات: {str(e)}")
            return {}
            
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
        
    def setup_statistics(self):
        """إعداد مؤشرات الإحصائيات"""
        default_stats = {
            'cursor': {'label': "سطر: 1 | عمود: 1", 'permanent': False},
            'chars': {'label': "الأحرف: 0", 'permanent': True},
            'words': {'label': "الكلمات: 0", 'permanent': True},
            'lines': {'label': "الأسطر: 0", 'permanent': True},
            'file_type': {'label': "النوع: نص عادي", 'permanent': True}
        }
        
        for stat_id, stat_info in default_stats.items():
            label = QLabel(stat_info['label'])
            label.setStyleSheet("padding: 0 10px;")
            
            if stat_info['permanent']:
                self.status_bar.addPermanentWidget(label)
            else:
                self.status_bar.addWidget(label)
                
            self.stats_labels[stat_id] = label
    
    def update_statistics(self, text: str = None, cursor_info: dict = None, file_type: str = None):
        """تحديث جميع الإحصائيات"""
        try:
            stats = {}
            
            if text is not None:
                text = text or ""
                # الإحصائيات الأساسية
                stats.update({
                    'chars': len(text),
                    'words': len([word for word in text.split() if word.strip()]),
                    'lines': text.count('\n') + 1 if text else 1
                })
                
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
                        print(f"خطأ في إضافة {plugin.name}: {str(e)}")
                
                # تحديث المؤشرات الأساسية
                self._update_basic_labels(stats)
            
            # تحديث موقع المؤشر
            if cursor_info and 'cursor' in self.stats_labels:
                cursor_text = f"سطر: {cursor_info.get('line', 1)} | عمود: {cursor_info.get('column', 1)}"
                self.stats_labels['cursor'].setText(cursor_text)
                stats['cursor'] = cursor_info
                
            # تحديث نوع الملف
            if file_type is not None and 'file_type' in self.stats_labels:
                # استخدام الاسم العربي من القاموس
                arabic_name = self.language_names.get(file_type, "نص عادي")
                self.stats_labels['file_type'].setText(f"النوع: {arabic_name}")
                stats['file_type'] = arabic_name
                
            if stats:
                self.statistics_changed.emit(stats)
                
        except Exception as e:
            print(f"خطأ في تحديث الإحصائيات: {str(e)}")
            
    def _update_basic_labels(self, stats):
        """تحديث المؤشرات الأساسية"""
        if 'chars' in stats and 'chars' in self.stats_labels:
            self.stats_labels['chars'].setText(f"الأحرف: {stats['chars']}")
        if 'words' in stats and 'words' in self.stats_labels:
            self.stats_labels['words'].setText(f"الكلمات: {stats['words']}")
        if 'lines' in stats and 'lines' in self.stats_labels:
            self.stats_labels['lines'].setText(f"الأسطر: {stats['lines']}")