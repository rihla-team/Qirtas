from tashaphyne.normalize import strip_tashkeel, strip_tatweel # PIP install tashaphyne

class ArabicDiacritics:
    def __init__(self):
        self.setup_diacritics()
        
    def setup_diacritics(self):
        self.diacritics_buttons = [
            ('َ', 'فتحة'),
            ('ُ', 'ضمة'),
            ('ِ', 'كسرة'),
            ('ْ', 'سكون'),
            ('ّ', 'شدة'),
            ('ً', 'تنوين فتح'),
            ('ٌ', 'تنوين ضم'),
            ('ٍ', 'تنوين كسر'),
        ]
    
    def add_diacritic(self, text, diacritic, position):
        """إضافة تشكيل في موضع محدد"""
        return text[:position] + diacritic + text[position:]
    
    def remove_diacritics(self, text):
        """إزالة جميع التشكيلات"""
        return strip_tashkeel(text)