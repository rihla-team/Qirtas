import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from editor.text_editor import ArabicEditor

def main():
    app = QApplication(sys.argv)
    
    # تحديد مسار ملف التنسيق
    style_path = os.path.join(os.path.dirname(__file__), 'resources', 'style.qss')
    
    # تحميل ملف التنسيق
    try:
        with open(style_path, 'r', encoding='utf-8') as style_file:
            style = style_file.read()
            app.setStyleSheet(style)
    except Exception as e:
        print(f"خطأ في تحميل ملف التنسيق: {e}")
    
    # تعيين اتجاه التطبيق من اليمين لليسار
    app.setLayoutDirection(Qt.RightToLeft)
    
    editor = ArabicEditor()
    editor.setWindowTitle("قِرطاس")
    editor.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 
    
    
    
    
    