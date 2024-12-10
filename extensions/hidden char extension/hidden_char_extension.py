from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QTextCursor

class HiddenCharExtension:
    def __init__(self, editor):
        # محاولة الحصول على المحرر الفعلي الذي يدعم textCursor
        self.editor = editor
        self.setup_action()

    def _get_text_editor(self, editor):
        """الحصول على المحرر الفعلي الذي يدعم textCursor."""
        if hasattr(editor, 'textCursor'):
            return editor
        elif hasattr(editor, 'get_current_editor'):
            # محاولة الحصول على المحرر الحالي من ArabicEditor
            current_editor = editor.get_current_editor()
            if hasattr(current_editor, 'textCursor'):
                return current_editor
        raise TypeError("المحرر يجب أن يكون كائنًا يدعم textCursor")

    def setup_action(self):
        """إعداد الإجراء والاختصار."""
        action = QAction("إضافة حرف خفي", self.editor)
        action.triggered.connect(self.insert_hidden_char)
        self.editor.addAction(action)

    def insert_hidden_char(self):
        """إدراج حرف خفي في الموضع المحدد أو في نهاية السطر."""
        current_editor = self.editor.get_current_editor()
        if not current_editor:
            return
        cursor = current_editor.textCursor()
        if cursor.hasSelection():
            # إدراج الحرف الخفي في الموضع المحدد
            cursor.insertText('\u200E')
        else:
            # إدراج الحرف الخفي في نهاية السطر الحالي
            cursor.movePosition(QTextCursor.EndOfLine)
            cursor.insertText('\u200E')
    def settings_menu(self):
        pass
class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.hidden_char_extension = HiddenCharExtension(editor)

    def get_menu_items(self):
        return [
            {'name': 'اعدادات إضافة حرف خفي', 'callback': self.hidden_char_extension.settings_menu}
        ]
    def get_context_menu_items(self):
        return [
            {'name': 'إضافة حرف خفي', 'callback': self.hidden_char_extension.insert_hidden_char, 'shortcut': 'Ctrl+Q'}
        ]
    def get_shortcuts(self):
        return [
            {'shortcut': 'Ctrl+Q', 'callback': self.hidden_char_extension.insert_hidden_char}
        ]

