from PyQt5.QtWidgets import QTextEdit

class ArabicCorrector:
    CORRECTIONS = {
        'إسم': 'اسم',
        'إبن': 'ابن',
        'الذى': 'الذي',
        'هذه': 'هذه',
        'عليهى': 'عليه',
        'الى': 'إلى',
        'فى': 'في',
        'علي': 'على',
    }
    
    HAMZA_CORRECTIONS = {
        'ا': 'أ',  # في بداية الكلمة
        'اسلام': 'إسلام',
        'امة': 'أمة',
    }
    
    def __init__(self, editor):
        self.editor = editor
        self.enabled = False
        self._connected_editor = None

    def toggle(self, enabled):
        """تفعيل/تعطيل التصحيح التلقائي"""
        self.enabled = enabled
        current_editor = self.editor.get_current_editor()
        
        # فصل الإشارة من المحرر السابق إذا وجد
        if self._connected_editor:
            try:
                self._connected_editor.textChanged.disconnect(self.correct_text)
            except TypeError:
                pass
        
        if enabled and current_editor:
            current_editor.textChanged.connect(self.correct_text)
            self._connected_editor = current_editor
        
        status = "مفعل" if enabled else "معطل"
        if hasattr(self.editor, 'status_bar'):
            self.editor.status_bar.showMessage(f"التصحيح التلقائي: {status}", 2000)

    def correct_text(self):
        """تصحيح النص تلقائياً"""
        if not self.enabled:
            return
            
        current_editor = self.editor.get_current_editor()
        if not current_editor:
            return
            
        cursor = current_editor.textCursor()
        if cursor.position() == 0:
            return
            
        current_position = cursor.position()
        
        cursor.select(cursor.WordUnderCursor)
        word = cursor.selectedText()
        
        # تصحيح الكلمات الشائعة
        if word in self.CORRECTIONS:
            corrected_word = self.CORRECTIONS[word]
            cursor.insertText(corrected_word)
            
        # تصحيح الهمزات
        elif word in self.HAMZA_CORRECTIONS:
            corrected_word = self.HAMZA_CORRECTIONS[word]
            cursor.insertText(corrected_word)
            
        # إعادة المؤشر إلى موضعه
        if word in self.CORRECTIONS or word in self.HAMZA_CORRECTIONS:
            new_position = current_position + (len(corrected_word) - len(word))
            cursor.setPosition(min(new_position, len(current_editor.toPlainText())))
            current_editor.setTextCursor(cursor)