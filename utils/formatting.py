from PyQt5.QtGui import QFont, QTextCharFormat

class TextFormatter:
    ARABIC_TEMPLATES = {
        'رسالة رسمية': """بسم الله الرحمن الرحيم

التاريخ: 
الموافق:
الموضوع:

السيد/ة المحترم/ة

تحية طيبة وبعد،

نص الرسالة

وتفضلوا بقبول فائق الاحترام والتقدير،

المرسل:
التوقيع:
""",
        'مقال': """العنوان:

المقدمة:


صلب الموضوع:


الخاتمة:

""",
        'تقرير': """بسم الله الرحمن الرحيم

عنوان التقرير:
التاريخ:
إعداد:

مقدمة:

محتوى التقرير:
1-
2-
3-

التوصيات:

الخاتمة:
""",
        'محضر اجتماع': """محضر اجتماع

التاريخ:
الوقت:
المكان:

الحاضرون:
1-
2-
3-

جدول الأعمال:
1-
2-
3-

القرارات والتوصيات:
1-
2-
3-

توقيع رئيس الاجتماع:
توقيع أمين السر:
"""
    }
    
    def __init__(self, editor):
        self.editor = editor

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
        char_format = cursor.charFormat()
        
        # منع تحديث الخط التلقائي مؤقتاً
        current_editor.document().blockSignals(True)
        
        if format_type == 'bold':
            if char_format.fontWeight() == QFont.Bold:
                char_format.setFontWeight(QFont.Normal)
            else:
                char_format.setFontWeight(QFont.Bold)
        elif format_type == 'italic':
            char_format.setFontItalic(not char_format.fontItalic())
        elif format_type == 'underline':
            char_format.setFontUnderline(not char_format.fontUnderline())
        elif format_type == 'size' and size is not None:
            char_format.setFontPointSize(size)
        
        if cursor.hasSelection():
            cursor.mergeCharFormat(char_format)
        else:
            current_editor.setCurrentCharFormat(char_format)
        
        current_editor.setFocus()
        
        # إعادة تفعيل الإشارات
        current_editor.document().blockSignals(False)