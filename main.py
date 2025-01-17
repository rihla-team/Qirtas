# main.py
try:
    import sys
    import os
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt, pyqtSignal, QObject
    from editor.text_editor import ArabicEditor
    from utils.extensions_manager import ExtensionsManager
    from utils.arabic_logger import log_in_arabic, setup_arabic_logging
    import logging
except Exception as e:
    print(f"خطأ في تحميل المكتبات: {e}")
    sys.exit(1)
    
formatter = setup_arabic_logging()
if not formatter:
    print("تحذير: فشل في إعداد نظام التسجيل العربي")

logger = logging.getLogger(__name__)
def main():
    try:
        app = QApplication(sys.argv)
        app_version = "1.0.0"

        # تحميل التنسيق
        try:
            if hasattr(sys, '_MEIPASS'):
                style_path = os.path.join(sys._MEIPASS, 'resources', 'styles', 'style.qss')
            else:
                style_path = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'style.qss')    
        
            with open(style_path, 'r', encoding='utf-8') as style_file:
                style = style_file.read()
                app.setStyleSheet(style)
                log_in_arabic(logger, logging.INFO, "تم تحميل ملف التنسيق بنجاح")
        except FileNotFoundError:
            log_in_arabic(logger, logging.ERROR, f"لم يتم العثور على ملف التنسيق في المسار: {style_path}")
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تحميل ملف التنسيق: {e}")

        app.setLayoutDirection(Qt.RightToLeft)

        editor = ArabicEditor()
        editor.setWindowTitle("قِرطاس")
        log_in_arabic(logger, logging.INFO, "تم إنشاء المحرر بنجاح")

        # إضافة مدير الإضافات
        extensions_manager = ExtensionsManager(editor)
        editor.extensions_manager = extensions_manager
        log_in_arabic(logger, logging.INFO, "تم تهيئة مدير الإضافات")
        
        editor.show()
        log_in_arabic(logger, logging.INFO, "تم عرض المحرر")
        
        return app.exec_()
    except Exception as e:
        log_in_arabic(logger, logging.ERROR, f"خطأ في تهيئة المحرر: {e}")
        return 1

class FileManager(QObject):
    file_opened = pyqtSignal(str, object)
    file_dropped = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__ + ".FileManager")
    
    def _create_editor(self):
        try:
            editor = ArabicEditor()
            log_in_arabic(self.logger, logging.INFO, "تم إنشاء محرر جديد")
            return editor
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في إنشاء محرر جديد: {e}")
            return None
    
    def open_file(self, file_path):
        try:
            editor = self._create_editor()
            if editor:
                self.file_opened.emit(file_path, editor)
                log_in_arabic(self.logger, logging.INFO, f"تم فتح الملف: {file_path}")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في فتح الملف: {e}")

    def handle_file_drop(self, file_path):
        try:
            editor = self._create_editor()
            if editor:
                self.file_dropped.emit(file_path, editor)
                log_in_arabic(self.logger, logging.INFO, f"تم استقبال الملف: {file_path}")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في معالجة الملف المسحوب: {e}")
    
if __name__ == '__main__':
    exit_code = main()
    if exit_code == 0:
        log_in_arabic(logger, logging.INFO, "تم إغلاق البرنامج بنجاح")
    else:
        log_in_arabic(logger, logging.ERROR, "تم إغلاق البرنامج بسبب خطأ")