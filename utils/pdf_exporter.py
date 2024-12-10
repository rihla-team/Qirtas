from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument
from .syntax_highlighter import CodeHighlighter

class PDFExporter:
    @staticmethod
    def export_to_pdf(text, filename):
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        
        document = QTextDocument()
        document.setPlainText(text)
        
        highlighter = CodeHighlighter(document)
        # استخدام highlighter لتطبيق التلوين على المستند
        
        document.print_(printer)