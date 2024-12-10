import json
import os
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtWidgets import QAction, QMenu, QDialog, QVBoxLayout, QLabel, QRadioButton, QPushButton, QMessageBox, QSpinBox
from PyQt5.QtGui import QCursor
import arabic_reshaper
from bidi.algorithm import get_display
from PyQt5.QtCore import QObject, pyqtSignal

class TextProcessor(QObject):
    finished = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        
    def process(self, text, direction, process_func):
        result = process_func(text)
        self.finished.emit(result)

class ReverseTextExtension:
    def __init__(self, editor):
        self.editor = editor
        self.direction = 'right_to_left'
        self.settings_file = os.path.join(os.path.dirname(__file__), 'settings.json')
        self.load_settings()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.text_processor = TextProcessor()
        self.text_processor.finished.connect(self._on_processing_finished)
        self.setup_action()
        self.current_cursor = None

    def setup_action(self):
        action = QAction('عكس النص', self.editor)
        action.triggered.connect(self.reverse_text)
        self.editor.addAction(action)

    def reverse_text(self):
        current_editor = self.editor.get_current_editor()
        if not current_editor:
            return

        cursor = current_editor.textCursor()
        if cursor.hasSelection():
            self.current_cursor = cursor
            text = cursor.selectedText()
            # استخدام المعالج في مسار منفصل
            self.executor.submit(
                self.text_processor.process,
                text,
                self.direction,
                self.process_text
            )

    def _on_processing_finished(self, result):
        if self.current_cursor:
            self.current_cursor.insertText(result)
            self.current_cursor = None

    def process_text(self, text):
        # تقسيم النص إلى أسطر
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # معالجة كل سطر على حدة
            if self.direction == 'right_to_left':
                processed_line = self.reverse_right_to_left(line)
            else:
                processed_line = self.reverse_left_to_right(line)
            processed_lines.append(processed_line)
        
        # إعادة دمج الأسطر مع الحفاظ على التنسيق
        return '\n'.join(processed_lines)

    def reverse_right_to_left(self, text):
        # تحديد النمط العربي باستخدام التعبير النمطي
        import re
        pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+'
        
        def replace_arabic(match):
            arabic_text = match.group(0)
            reshaped_text = arabic_reshaper.reshape(arabic_text)
            return get_display(reshaped_text)
        
        # استبدال النصوص العربية فقط
        return re.sub(pattern, replace_arabic, text)

    def reverse_left_to_right(self, text):
        # نفس المنطق السابق ولكن مع عكس الكلمات من اليسار لليمين
        import re
        pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+'
        
        def replace_arabic(match):
            arabic_text = match.group(0)
            words = arabic_text.split()
            reversed_words = ' '.join(reversed(words))
            reshaped_text = arabic_reshaper.reshape(reversed_words)
            return get_display(reshaped_text)
        
        return re.sub(pattern, replace_arabic, text)

    def set_direction(self, direction):
        self.direction = direction
        self.save_settings()

    def settings_menu(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def save_settings(self):
        settings = {
            'direction': self.direction,
            'max_workers': self.max_workers
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except IOError as e:
            QMessageBox.critical(self.editor, "خطأ", f"فشل في حفظ الإعدادات: {str(e)}")

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.direction = settings.get('direction', 'right_to_left')
                    self.max_workers = settings.get('max_workers', 4)
            except (IOError, json.JSONDecodeError) as e:
                QMessageBox.critical(self.editor, "خطأ", f"فشل في تحميل الإعدادات: {str(e)}")
        else:
            self.max_workers = 4


class SettingsDialog(QDialog):
    def __init__(self, extension, parent=None):
        super().__init__(parent)
        self.extension = extension
        self.setWindowTitle("إعدادات عكس النص")
        layout = QVBoxLayout(self)

        self.right_to_left_radio = QRadioButton("عكس النص: اليمين لليسار")
        self.left_to_right_radio = QRadioButton("عكس النص: اليسار لليمين")

        layout.addWidget(QLabel("اختر اتجاه النص:"))
        layout.addWidget(self.right_to_left_radio)
        layout.addWidget(self.left_to_right_radio)

        if self.extension.direction == 'right_to_left':
            self.right_to_left_radio.setChecked(True)
        else:
            self.left_to_right_radio.setChecked(True)

        layout.addWidget(QLabel("عدد العمال:"))
        self.workers_spinbox = QSpinBox()
        self.workers_spinbox.setRange(1, 10)
        self.workers_spinbox.setValue(self.extension.max_workers)
        layout.addWidget(self.workers_spinbox)

        save_button = QPushButton("حفظ")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

    def save_settings(self):
        if self.right_to_left_radio.isChecked():
            self.extension.set_direction('right_to_left')
        else:
            self.extension.set_direction('left_to_right')
        
        self.extension.max_workers = self.workers_spinbox.value()
        self.extension.executor = ThreadPoolExecutor(max_workers=self.extension.max_workers)
        self.extension.save_settings()
        self.accept()

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.reverse_text_extension = ReverseTextExtension(editor)

    def get_menu_items(self):
        return [
            {'name': 'اعدادات عكس النصوص', 'callback': self.reverse_text_extension.settings_menu}
        ]

    def get_context_menu_items(self):
        return [
            {
                'name': 'عكس النص المحدد',
                'callback': self.reverse_text_extension.reverse_text,
                'shortcut': 'Ctrl+R',
            }
        ]

    def get_shortcuts(self):
        return [
            {'shortcut': 'Ctrl+R', 'callback': self.reverse_text_extension.reverse_text}
        ]
