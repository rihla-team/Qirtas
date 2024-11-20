from PyQt5.QtGui import QFont

class NumberConverter:
    ARABIC_NUMBERS = '٠١٢٣٤٥٦٧٨٩'
    ENGLISH_NUMBERS = '0123456789'
    
    @staticmethod
    def to_arabic(text):
        trans = str.maketrans(NumberConverter.ENGLISH_NUMBERS, 
                            NumberConverter.ARABIC_NUMBERS)
        return text.translate(trans)
    
    @staticmethod
    def to_english(text):
        trans = str.maketrans(NumberConverter.ARABIC_NUMBERS, 
                            NumberConverter.ENGLISH_NUMBERS)
        return text.translate(trans)
class TextFormatter:
    def __init__(self, editor):
        self.editor = editor

    def insert_template(self, template):
        """إدراج قالب نصي"""
        cursor = self.editor.text_edit.textCursor()
        cursor.insertText(template)
        self.editor.status_bar.showMessage("تم إدراج القالب", 2000)

    def apply_arabic_format(self, size, bold=False):
        """تطبيق تنسيق عربي محدد"""
        cursor = self.editor.text_edit.textCursor()
        if cursor.hasSelection():
            # تطبيق التنسيق على النص المحدد
            format = cursor.charFormat()
            format.setFontPointSize(size)
            if bold:
                format.setFontWeight(QFont.Bold)
            else:
                format.setFontWeight(QFont.Normal)
            cursor.mergeCharFormat(format)
        else:
            # تغيير التنسيق الافتراضي للكتابة الجديدة
            format = self.editor.text_edit.currentCharFormat()
            format.setFontPointSize(size)
            if bold:
                format.setFontWeight(QFont.Bold)
            else:
                format.setFontWeight(QFont.Normal)
            self.editor.text_edit.setCurrentCharFormat(format)
        
        self.editor.text_edit.setFocus()
        self.editor.status_bar.showMessage(f"تم تطبيق التنسيق: حجم {size}" + (" عريض" if bold else ""), 2000)

class TextTools:
    def __init__(self, editor):
        self.editor = editor
        self.number_converter = NumberConverter()

    def convert_numbers(self, to_type):
        """تحويل الأرقام في النص"""
        current_editor = self.editor.get_current_editor()
        if not current_editor:
            return
            
        text = current_editor.toPlainText()
        cursor = current_editor.textCursor()
        
        # حفظ موضع المؤشر
        position = cursor.position()
        
        # تحويل النص
        if to_type == 'arabic':
            new_text = self.number_converter.to_arabic(text)
        else:
            new_text = self.number_converter.to_english(text)
            
        # تحديث النص
        current_editor.setPlainText(new_text)
        
        # استعادة موضع المؤشر
        cursor.setPosition(position)
        current_editor.setTextCursor(cursor)

    def add_diacritic(self, diacritic):
        """إضافة تشكيل للنص المحدد"""
        current_editor = self.editor.get_current_editor()
        if not current_editor:
            return
        
        cursor = current_editor.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            text = cursor.selectedText()
            
            # إضافة التشكيل لكل حرف محدد
            new_text = ""
            for char in text:
                if char.isalpha():  # التأكد من أن الحرف عربي
                    new_text += char + diacritic
                else:
                    new_text += char
                    
            cursor.insertText(new_text)
        else:
            position = cursor.position()
            cursor.movePosition(cursor.Left)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor)
            char = cursor.selectedText()
            
            if char.isalpha():  # التأكد من أن الحرف عربي
                cursor.insertText(char + diacritic)
                
            cursor.setPosition(position + 1)
            current_editor.setTextCursor(cursor)