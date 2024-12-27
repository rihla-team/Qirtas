from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import QRegularExpression
from collections import OrderedDict

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self._block_cache = OrderedDict()
        self._cache_size = 1000

        # إعداد قواعد التلوين
        self.highlighting_rules = [
            (r'""".*?"""', self.format('comment')),
            (r"'''.*?'''", self.format('comment')),
            (r'f"[^"\\]*(\\.[^"\\]*)*"', self.format('string')),
            (r"f'[^'\\]*(\\.[^'\\]*)*'", self.format('string')),
            (r'\bQ[A-Za-z]+\b', self.format('class')),
            (r'\b(self|from|import|class|def|return|and|or|not|if|elif|else|try|except|finally|for|while|in|is|lambda|None|True|False)\b',
             self.format('keyword')),
            (r'\b[A-Za-z0-9_]+(?=\()', self.format('function')),
            (r'\.[A-Za-z0-9_]+\b', self.format('attribute')),
            (r'"[^"\\]*(\\.[^"\\]*)*"', self.format('string')),
            (r"'[^'\\]*(\\.[^'\\]*)*'", self.format('string')),
            (r'#[^\n]*', self.format('comment')),
            (r'\b[0-9]+\b', self.format('number')),
            (r'[\+\-\*\/\=\<\>\!\%\&\|\^\~\(\)\[\]\{\}\,\.\:]', self.format('operator')),
        ]

        # تجميع التعابير النمطية
        self._compiled_rules = [
            (QRegularExpression(pattern), fmt) for pattern, fmt in self.highlighting_rules
        ]

    def format(self, token_type):
        """إنشاء تنسيق حسب نوع الرمز"""
        text_format = QTextCharFormat()
        if token_type == 'keyword':
            text_format.setForeground(QColor("#4EC9B0"))
            text_format.setFontWeight(QFont.Bold)
        elif token_type == 'class':
            text_format.setForeground(QColor("#E8BF6A"))
        elif token_type == 'function':
            text_format.setForeground(QColor("#9CDCFE"))
            text_format.setFontWeight(QFont.Bold)
        elif token_type == 'attribute':
            text_format.setForeground(QColor("#9CDCFE"))
        elif token_type == 'string':
            text_format.setForeground(QColor("#CE9178"))
        elif token_type == 'comment':
            text_format.setForeground(QColor("#608B4E"))
            text_format.setFontItalic(True)
        elif token_type == 'number':
            text_format.setForeground(QColor("#B5CEA8"))
        elif token_type == 'operator':
            text_format.setForeground(QColor("#D4D4D4"))
        else:
            text_format.setForeground(QColor("#D4D4D4"))
        return text_format

    def highlightBlock(self, text):
        """تلوين كتلة نصية"""
        if not self.enabled or not text:
            return        
        block_number = self.currentBlock().blockNumber()
        cached_formats = self._get_cached_formats(block_number)
        if cached_formats:
            for start, length, format in cached_formats:
                self.setFormat(start, length, format)
            return
        
        formats = []
        for pattern, format in self._compiled_rules:
            match_iter = pattern.globalMatch(text)
            while match_iter.hasNext():
                match = match_iter.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, format)
                formats.append((start, length, format))
        
        self._cache_block(block_number, formats)

    def _get_cached_formats(self, block_number):
        """الحصول على التنسيقات المخزنة مؤقتًا"""
        return self._block_cache.get(block_number, None)

    def _cache_block(self, block_number, formats):
        """تخزين التنسيقات مؤقتًا"""
        if len(self._block_cache) >= self._cache_size:
            items_to_remove = self._cache_size // 10
            for _ in range(items_to_remove):
                self._block_cache.popitem(last=False)
        self._block_cache[block_number] = formats

    def rehighlight(self):
        """إعادة تلوين المستند"""
        self._block_cache.clear()
        super().rehighlight()
        
