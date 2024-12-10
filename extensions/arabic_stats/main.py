from PyQt5.QtWidgets import QLabel
from utils.statistics_manager import StatisticsPlugin

class ArabicStatsPlugin(StatisticsPlugin):
    """إضافة لحساب إحصائيات النص العربي"""
    def __init__(self):
        super().__init__("arabic_stats", "إحصائيات النص العربي")
        
    def calculate_stats(self, text: str) -> dict:
        """حساب الإحصائيات العربية"""
        # حساب الأحرف العربية
        arabic_chars = len([c for c in text if '\u0600' <= c <= '\u06FF'])
        
        # حساب الكلمات العربية (بشكل تقريبي)
        arabic_words = len([w for w in text.split() if any('\u0600' <= c <= '\u06FF' for c in w)])
        
        return {
            'arabic_chars': arabic_chars,
            'arabic_words': arabic_words,
            'arabic_ratio': round(arabic_chars / len(text) * 100 if text else 0, 1)
        }
    
    def format_stat(self, key: str, value) -> str:
        """تنسيق عرض الإحصائية"""
        if key == 'arabic_ratio':
            return f"نسبة العربية: {value}%"
        elif key == 'arabic_chars':
            return f"الأحرف العربية: {value}"
        elif key == 'arabic_words':
            return f"الكلمات العربية: {value}"
        return f"{key}: {value}"

class Extension:
    """الإضافة الرئيسية"""
    def __init__(self, editor):
        self.editor = editor
        self.stats_plugin = None
        
        # إضافة الإضافة لمدير الإحصائيات
        if hasattr(editor, 'statistics_manager'):
            self.stats_plugin = ArabicStatsPlugin()
            editor.statistics_manager.add_plugin(self.stats_plugin)
    
    def get_menu_items(self):
        """إضافة عناصر القائمة"""
        return [{
            'name': 'تفعيل إحصائيات العربية',
            'callback': self.toggle_stats
        }]
    
    def toggle_stats(self):
        """تفعيل/تعطيل الإحصائيات"""
        if self.stats_plugin:
            self.stats_plugin.enabled = not self.stats_plugin.enabled
            # تحديث الإحصائيات
            current_editor = self.editor.get_current_editor()
            if current_editor:
                self.editor.statistics_manager.update_statistics(current_editor.toPlainText()) 