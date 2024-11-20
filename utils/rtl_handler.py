from PyQt5.QtCore import Qt
import arabic_reshaper
from bidi.algorithm import get_display

class RTLHandler:
    @staticmethod
    def process_text(text):
        # معالجة النص العربي وتشكيله بشكل صحيح
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    
    @staticmethod
    def handle_mixed_text(text):
        # التعامل مع النصوص المختلطة (عربي، لاتيني، أرقام)
        parts = []
        current_part = ''
        current_direction = None
        
        for char in text:
            if char.isalpha():
                direction = 'rtl' if '\u0600' <= char <= '\u06FF' else 'ltr'
            else:
                direction = current_direction or 'neutral'
                
            if direction != current_direction and current_part:
                parts.append((current_part, current_direction))
                current_part = ''
                
            current_part += char
            current_direction = direction
            
        if current_part:
            parts.append((current_part, current_direction))
            
        return parts