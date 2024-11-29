import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor, QTextCharFormat
from editor.text_editor import ArabicEditor
from utils.extensions_manager import ExtensionsManager



def main():
    app = QApplication(sys.argv)
    
    # تحميل التنسيق
    style_path = os.path.join(os.path.dirname(__file__), 'resources', 'style.qss')
    try:
        with open(style_path, 'r', encoding='utf-8') as style_file:
            style = style_file.read()
            app.setStyleSheet(style)
    except Exception as e:
        print(f"خطأ في تحميل ملف التنسيق: {e}")
    
    app.setLayoutDirection(Qt.RightToLeft)
    
    editor = ArabicEditor()
    editor.setWindowTitle("قِرطاس")
    
    # إضافة مدير الإضافات
    extensions_manager = ExtensionsManager(editor)
    editor.extensions_manager = extensions_manager
    
    editor.show()
    sys.exit(app.exec_())

class FileManager(QObject):
    file_opened = pyqtSignal(str, object)
    file_dropped = pyqtSignal(str, object)
    
    def open_file(self, file_path):
        editor = self._create_editor()
        # ... كود فتح الملف ...
        self.file_opened.emit(file_path, editor)

    def handle_file_drop(self, file_path):
        editor = self._create_editor()
        # ... كود معالجة الملف المسحوب ...
        self.file_dropped.emit(file_path, editor)

if __name__ == '__main__':
    main()