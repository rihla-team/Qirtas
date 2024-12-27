from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import json
import os

class TextFormatter:
    def __init__(self, editor):
        self.editor = editor
        self.load_templates()
        
    def load_templates(self):
        """تحميل القوالب من ملف JSON"""
        try:
            templates_path = os.path.join('resources', 'arabic_templates.json')
            with open(templates_path, 'r', encoding='utf-8') as f:
                self.ARABIC_TEMPLATES = json.load(f)
        except Exception as e:
            print(f"خطأ في تحميل القوالب: {e}")
            self.ARABIC_TEMPLATES = {}

    def insert_template(self, template):
        """إدراج قالب نصي"""
        current_editor = self.editor.tab_manager.get_current_editor()
        if not current_editor:
            return
            
        template_text = self.ARABIC_TEMPLATES.get(template, '')
        if template_text:
            cursor = current_editor.textCursor()
            cursor.insertText(template_text)
            current_editor.setFocus()

    def format_text(self, format_type, size=None):
        """تنسيق النص المحدد"""
        current_editor = self.editor.tab_manager.get_current_editor()
        if not current_editor:
            return
        
        cursor = current_editor.textCursor()
        
        # منع تحديث الخط التلقائي مؤقتاً
        current_editor.document().blockSignals(True)
        
        if format_type == 'bold':
            char_format = cursor.charFormat()
            if char_format.fontWeight() == QFont.Bold:
                char_format.setFontWeight(QFont.Normal)
            else:
                char_format.setFontWeight(QFont.Bold)
            cursor.mergeCharFormat(char_format)
        
        elif format_type == 'italic':
            char_format = cursor.charFormat()
            char_format.setFontItalic(not char_format.fontItalic())
            cursor.mergeCharFormat(char_format)
        
        elif format_type == 'underline':
            char_format = cursor.charFormat()
            char_format.setFontUnderline(not char_format.fontUnderline())
            cursor.mergeCharFormat(char_format)
        
        elif format_type == 'size' and size is not None:
            char_format = cursor.charFormat()
            char_format.setFontPointSize(size)
            cursor.mergeCharFormat(char_format)
        
        elif format_type.startswith('align_'):
            block_format = cursor.blockFormat()
            if format_type == 'align_right':
                block_format.setAlignment(Qt.AlignRight)
            elif format_type == 'align_left':
                block_format.setAlignment(Qt.AlignLeft)
            elif format_type == 'align_center':
                block_format.setAlignment(Qt.AlignCenter)
            elif format_type == 'align_justify':
                block_format.setAlignment(Qt.AlignJustify)
            cursor.mergeBlockFormat(block_format)
        
        current_editor.setTextCursor(cursor)
        current_editor.setFocus()
        
        # إعادة تفعيل الإشارات
        current_editor.document().blockSignals(False)