from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QCheckBox, QInputDialog, QMessageBox)
from PyQt5.QtGui import QTextDocument

class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.last_match = None
        self.last_search = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('بحث')
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout()
        
        # حقل البحث
        search_layout = QHBoxLayout()
        search_label = QLabel('بحث عن:')
        self.search_input = QLineEdit()
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # خيارات البحث
        options_layout = QHBoxLayout()
        self.case_sensitive = QCheckBox('مطابقة حالة الأحرف')
        self.whole_words = QCheckBox('كلمات كاملة فقط')
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.whole_words)
        layout.addLayout(options_layout)
        
        # أزرار البحث
        buttons_layout = QHBoxLayout()
        find_next_btn = QPushButton('بحث عن التالي')
        find_prev_btn = QPushButton('بحث عن السابق')
        find_next_btn.clicked.connect(self.find_next)
        find_prev_btn.clicked.connect(self.find_previous)
        buttons_layout.addWidget(find_next_btn)
        buttons_layout.addWidget(find_prev_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
    def find(self, forward=True):
        """البحث عن النص"""
        text_edit = self.parent.get_current_editor()
        if not text_edit:
            return
            
        # الحصول على النص المراد البحث عنه
        search_text = self.search_input.text()
        if not search_text:
            return
            
        # تحديث آخر بحث
        self.last_search = search_text
            
        # تحديد خيارات البحث
        flags = QTextDocument.FindFlags()
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole_words.isChecked():
            flags |= QTextDocument.FindWholeWords
        if not forward:
            flags |= QTextDocument.FindBackward
            
        # البحث عن النص
        found = text_edit.find(search_text, flags)
        if not found:
            # إذا لم يتم العثور على النص، نعود إلى بداية/نهاية المستند
            cursor = text_edit.textCursor()
            cursor.movePosition(
                cursor.Start if forward else cursor.End
            )
            text_edit.setTextCursor(cursor)
            found = text_edit.find(search_text, flags)
            
            # إذا لم يتم العثور على النص، نعرض رسالة
            if not found:
                QMessageBox.information(
                    self,
                    "نتيجة البحث",
                    "لم يتم العثور على النص المطلوب"
                )
            
        return found
        
    def find_next(self):
        """البحث عن التطابق التالي"""
        return self.find(forward=True)
        
    def find_previous(self):
        """البحث عن التطابق السابق"""
        return self.find(forward=False)
        
class ReplaceDialog(SearchDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.add_replace_widgets()
        
    def add_replace_widgets(self):
        """إضافة عناصر الاستبدال"""
        # حقل الاستبدال
        replace_layout = QHBoxLayout()
        replace_label = QLabel('استبدال بـ:')
        self.replace_input = QLineEdit()
        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_input)
        
        # إضافة الحقل قبل أزرار البحث
        layout = self.layout()
        layout.insertLayout(2, replace_layout)
        
        # أزرار الاستبدال
        replace_buttons = QHBoxLayout()
        replace_btn = QPushButton('استبدال')
        replace_all_btn = QPushButton('استبدال الكل')
        replace_btn.clicked.connect(self.replace)
        replace_all_btn.clicked.connect(self.replace_all)
        replace_buttons.addWidget(replace_btn)
        replace_buttons.addWidget(replace_all_btn)
        
        # إضافة الأزرار
        layout.addLayout(replace_buttons)
        
        # تعديل حجم النافذة
        self.setFixedSize(400, 200)
        
    def replace(self):
        """استبدال النص المحدد"""
        text_edit = self.parent.get_current_editor()
        if not text_edit:
            return
            
        if text_edit.textCursor().hasSelection():
            text_edit.textCursor().insertText(self.replace_input.text())
            self.find_next()
            
    def replace_all(self):
        """استبدال كل التطابقات"""
        text_edit = self.parent.get_current_editor()
        if not text_edit:
            return
            
        cursor = text_edit.textCursor()
        cursor.beginEditBlock()
        
        cursor.movePosition(cursor.Start)
        text_edit.setTextCursor(cursor)
        
        found = True
        while found:
            found = self.find_next()
            if found:
                text_edit.textCursor().insertText(self.replace_input.text())
                
        cursor.endEditBlock()

class SearchManager:
    def __init__(self, editor):
        self.editor = editor
        self.search_dialog = None
        self.replace_dialog = None
        
    def show_search_dialog(self):
        """عرض نافذة البحث"""
        if not self.search_dialog:
            self.search_dialog = SearchDialog(self.editor)
        self.search_dialog.show()
        self.search_dialog.search_input.setFocus()
        
        # تحديد النص المحدد في المحرر تلقائياً
        current_editor = self.editor.tab_manager.get_current_editor()
        if current_editor and current_editor.textCursor().hasSelection():
            self.search_dialog.search_input.setText(current_editor.textCursor().selectedText())
            self.search_dialog.search_input.selectAll()

    def show_replace_dialog(self):
        """عرض نافذة البحث والاستبدال"""
        if not self.replace_dialog:
            self.replace_dialog = ReplaceDialog(self.editor)
        self.replace_dialog.show()
        self.replace_dialog.search_input.setFocus()

    def goto_line(self):
        """الانتقال إلى سطر محدد"""
        current_editor = self.editor.tab_manager.get_current_editor()
        if not current_editor:
            return
            
        line_number, ok = QInputDialog.getInt(
            self.editor,
            'انتقال إلى سطر',
            'رقم السطر:',
            value=current_editor.textCursor().blockNumber() + 1,
            min=1,
            max=current_editor.document().lineCount()
        )
        
        if ok:
            cursor = current_editor.textCursor()
            cursor.movePosition(cursor.Start)
            for _ in range(line_number - 1):
                cursor.movePosition(cursor.NextBlock)
            current_editor.setTextCursor(cursor)
            
            # تمرير المؤشر إلى متصف النافذة
            current_editor.ensureCursorVisible()
            
            # تمرير إلى أعلى قليلاً لتحسين الرؤية
            scrollbar = current_editor.verticalScrollBar()
            if scrollbar:
                current_value = scrollbar.value()
                target_value = max(0, current_value - current_editor.height() // 3)
                scrollbar.setValue(target_value)