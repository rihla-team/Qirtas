from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtGui import QTextDocument

class DocumentPrinter:
    def __init__(self, parent=None):
        self.parent = parent
        self.printer = QPrinter()
        
    def print_document(self, text):
        dialog = QPrintDialog(self.printer, self.parent)
        if dialog.exec_() == QPrintDialog.Accepted:
            document = QTextDocument()
            document.setPlainText(text)
            document.print_(self.printer)