from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtGui import QTextDocument
from .syntax_highlighter import CodeHighlighter

class DocumentPrinter:
    def __init__(self, parent=None):
        self.parent = parent
        self.printer = QPrinter()
        
    def print_document(self, text):
        """طباعة المستند على الطابعة"""
        dialog = QPrintDialog(self.printer, self.parent)
        if dialog.exec_() == QPrintDialog.Accepted:
            document = QTextDocument()
            document.setPlainText(text)
            document.print_(self.printer)
            
    @staticmethod
    def export_to_pdf(text, filename):
        """تصدير المستند إلى ملف PDF"""
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        
        document = QTextDocument()
        document.setPlainText(text)
        
        # تطبيق تلوين الشيفرة البرمجية
        
        document.print_(printer)

# اسم مستعار للفئة للحفاظ على التوافقية مع الكود القديم
PDFExporter = DocumentPrinter