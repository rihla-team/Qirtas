from PyQt5.QtWidgets import QLabel, QStatusBar
from PyQt5.QtCore import QObject, pyqtSignal

class StatisticsManager(QObject):
    statistics_changed = pyqtSignal(dict)
    
    def __init__(self, status_bar: QStatusBar):
        super().__init__()
        self.status_bar = status_bar
        self.stats_labels = {}
        self.setup_statistics()
        
    def setup_statistics(self):
        """إعداد مؤشرات الإحصائيات"""
        # تعريف الإحصائيات الافتراضية
        default_stats = {
            'cursor': {'label': "سطر: 1 | عمود: 1", 'permanent': False},
            'chars': {'label': "الأحرف: 0", 'permanent': True},
            'words': {'label': "الكلمات: 0", 'permanent': True},
            'lines': {'label': "الأسطر: 0", 'permanent': True}
        }
        
        # إنشاء وإضافة المؤشرات
        for stat_id, stat_info in default_stats.items():
            label = QLabel(stat_info['label'])
            label.setStyleSheet("padding: 0 10px;")
            
            if stat_info['permanent']:
                self.status_bar.addPermanentWidget(label)
            else:
                self.status_bar.addWidget(label)
                
            self.stats_labels[stat_id] = label
    
    def update_statistics(self, text: str = "", cursor_info: dict = None):
        """تحديث جميع الإحصائيات"""
        stats = {}
        
        # حساب إحصائيات النص
        if text is not None:
            # تجنب الأخطاء عند النص الفارغ
            text = text or ""
            stats.update({
                'chars': len(text),
                'words': len([word for word in text.split() if word.strip()]),
                'lines': text.count('\n') + 1 if text else 1
            })
            
            # تحديث مؤشرات النص
            self.stats_labels['chars'].setText(f"الأحرف: {stats['chars']}")
            self.stats_labels['words'].setText(f"الكلمات: {stats['words']}")
            self.stats_labels['lines'].setText(f"الأسطر: {stats['lines']}")
        
        # تحديث موقع المؤشر
        if cursor_info:
            cursor_text = f"سطر: {cursor_info.get('line', 1)} | عمود: {cursor_info.get('column', 1)}"
            self.stats_labels['cursor'].setText(cursor_text)
            stats['cursor'] = cursor_info
            
        # إرسال إشارة بالتغييرات
        self.statistics_changed.emit(stats)
    
    def add_custom_statistic(self, stat_id: str, label: str, permanent: bool = True):
        """إضافة مؤشر إحصائيات مخصص"""
        if stat_id not in self.stats_labels:
            label_widget = QLabel(label)
            label_widget.setStyleSheet("padding: 0 10px;")
            
            if permanent:
                self.status_bar.addPermanentWidget(label_widget)
            else:
                self.status_bar.addWidget(label_widget)
                
            self.stats_labels[stat_id] = label_widget
            
    def update_custom_statistic(self, stat_id: str, value: str):
        """تحديث قيمة مؤشر مخصص"""
        if stat_id in self.stats_labels:
            self.stats_labels[stat_id].setText(value)