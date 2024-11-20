from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument

class PDFExporter:
    @staticmethod
    def export_to_pdf(text, filename):
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        
        document = QTextDocument()
        document.setPlainText(text)
        document.print_(printer)