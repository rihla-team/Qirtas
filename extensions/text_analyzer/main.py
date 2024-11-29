import re
from collections import Counter
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QLabel, QTextBrowser, QPushButton, QProgressBar
from PyQt5.QtCore import Qt, QTimer
import arabic_reshaper
from bidi.algorithm import get_display

class TextAnalyzer:
    """محلل النص العربي"""
    
    def __init__(self):
        # قائمة الكلمات الشائعة في اللغة العربية
        self.common_words = set(['في', 'من', 'على', 'إلى', 'عن', 'مع', 'هذا', 'التي', 'الذي'])
        
    def analyze_text(self, text):
        """تحليل النص وإرجاع الإحصائيات"""
        if not text.strip():
            return None
            
        stats = {
            'chars': self._analyze_chars(text),
            'words': self._analyze_words(text),
            'sentences': self._analyze_sentences(text),
            'readability': self._analyze_readability(text),
            'suggestions': self._get_suggestions(text)
        }
        
        return stats
        
    def _analyze_chars(self, text):
        """تحليل الأحرف"""
        chars = Counter(text)
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        
        return {
            'total': len(text),
            'arabic': arabic_chars,
            'most_common': chars.most_common(5),
            'spaces': text.count(' '),
            'special': sum(1 for c in text if not c.isalnum() and c != ' ')
        }
        
    def _analyze_words(self, text):
        """تحليل الكلمات"""
        words = re.findall(r'\b\w+\b', text)
        word_count = Counter(words)
        
        return {
            'total': len(words),
            'unique': len(set(words)),
            'most_common': word_count.most_common(5),
            'avg_length': sum(len(w) for w in words) / len(words) if words else 0
        }
        
    def _analyze_sentences(self, text):
        """تحليل الجمل"""
        sentences = re.split('[.!؟]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            'total': len(sentences),
            'avg_length': sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0,
            'longest': max(sentences, key=len) if sentences else '',
            'shortest': min(sentences, key=len) if sentences else ''
        }
        
    def _analyze_readability(self, text):
        """تحليل سهولة القراءة"""
        words = len(re.findall(r'\b\w+\b', text))
        sentences = len(re.split('[.!؟]', text))
        complex_words = sum(1 for w in re.findall(r'\b\w+\b', text) if len(w) > 6)
        
        if sentences == 0:
            return {'score': 0, 'level': 'غير محدد'}
            
        # حساب مؤشر سهولة القراءة
        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (complex_words / words)
        
        # تحديد المستوى
        if score > 90:
            level = 'سهل جداً'
        elif score > 80:
            level = 'سهل'
        elif score > 70:
            level = 'متوسط'
        else:
            level = 'معقد'
            
        return {'score': round(score, 2), 'level': level}
        
    def _get_suggestions(self, text):
        """تقديم اقتراحات لتحسين النص"""
        suggestions = []
        
        # التحقق من طول الجمل
        sentences = re.split('[.!؟]', text)
        long_sentences = [s for s in sentences if len(s.split()) > 20]
        if long_sentences:
            suggestions.append({
                'type': 'warning',
                'message': f'يوجد {len(long_sentences)} جمل طويلة. حاول تقسيمها لتحسين القراءة.'
            })
            
        # التحقق من تكرار الكلمات
        words = re.findall(r'\b\w+\b', text)
        word_count = Counter(words)
        repeated = [w for w, c in word_count.items() if c > 3 and w not in self.common_words]
        if repeated:
            suggestions.append({
                'type': 'info',
                'message': f'الكلمات التالية متكررة: {", ".join(repeated)}. حاول استخدام مرادفات.'
            })
            
        return suggestions


class AnalysisDialog(QDialog):
    """نافذة عرض نتائج التحليل"""
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.analyzer = TextAnalyzer()
        self.setup_ui()
        
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تحليل النص")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # إضافة شريط التقدم
        self.progress = QProgressBar(self)
        layout.addWidget(self.progress)
        
        # إضافة التبويبات
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # إضافة زر الإغلاق
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        # بدء التحليل
        QTimer.singleShot(100, self.start_analysis)
        
    def start_analysis(self):
        """بدء عملية التحليل"""
        self.progress.setRange(0, 5)
        self.progress.setValue(0)
        
        # تحليل النص
        stats = self.analyzer.analyze_text(self.text)
        if not stats:
            return
            
        # إنشاء التبويبات
        self.create_chars_tab(stats['chars'])
        self.progress.setValue(1)
        
        self.create_words_tab(stats['words'])
        self.progress.setValue(2)
        
        self.create_sentences_tab(stats['sentences'])
        self.progress.setValue(3)
        
        self.create_readability_tab(stats['readability'])
        self.progress.setValue(4)
        
        self.create_suggestions_tab(stats['suggestions'])
        self.progress.setValue(5)
        
    def create_chars_tab(self, stats):
        """إنشاء تبويب الأحرف"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        content = f"""
        <h3>إحصائيات الأحرف</h3>
        <p>العدد الكلي: {stats['total']}</p>
        <p>الأحرف العربية: {stats['arabic']}</p>
        <p>المسافات: {stats['spaces']}</p>
        <p>العلامات الخاصة: {stats['special']}</p>
        
        <h4>الأحرف الأكثر تكراراً:</h4>
        <ul>
        {''.join(f'<li>{char}: {count} مرة</li>' for char, count in stats['most_common'])}
        </ul>
        """
        
        browser = QTextBrowser()
        browser.setHtml(content)
        layout.addWidget(browser)
        
        self.tabs.addTab(tab, "الأحرف")
        
    def create_words_tab(self, stats):
        """إنشاء تبويب الكلمات"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        content = f"""
        <h3>إحصائيات الكلمات</h3>
        <p>العدد الكلي: {stats['total']}</p>
        <p>الكلمات الفريدة: {stats['unique']}</p>
        <p>متوسط طول الكلمة: {stats['avg_length']:.1f} حرف</p>
        
        <h4>الكلمات الأكثر تكراراً:</h4>
        <ul>
        {''.join(f'<li>{word}: {count} مرة</li>' for word, count in stats['most_common'])}
        </ul>
        """
        
        browser = QTextBrowser()
        browser.setHtml(content)
        layout.addWidget(browser)
        
        self.tabs.addTab(tab, "الكلمات")
        
    def create_sentences_tab(self, stats):
        """إنشاء تبويب الجمل"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        content = f"""
        <h3>إحصائيات الجمل</h3>
        <p>العدد الكلي: {stats['total']}</p>
        <p>متوسط طول الجملة: {stats['avg_length']:.1f} كلمة</p>
        
        <h4>أطول جملة:</h4>
        <p>{stats['longest']}</p>
        
        <h4>أقصر جملة:</h4>
        <p>{stats['shortest']}</p>
        """
        
        browser = QTextBrowser()
        browser.setHtml(content)
        layout.addWidget(browser)
        
        self.tabs.addTab(tab, "الجمل")
        
    def create_readability_tab(self, stats):
        """إنشاء تبويب سهولة القراءة"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        content = f"""
        <h3>سهولة القراءة</h3>
        <p>الدرجة: {stats['score']}</p>
        <p>المستوى: {stats['level']}</p>
        
        <h4>تفسير النتيجة:</h4>
        <ul>
            <li>90+ : سهل جداً - مناسب للقراء المبتدئين</li>
            <li>80-90: سهل - مناسب للقراءة العامة</li>
            <li>70-80: متوسط - مناسب للقراء المتوسطين</li>
            <li>أقل من 70: معقد - قد يحتاج إلى تبسيط</li>
        </ul>
        """
        
        browser = QTextBrowser()
        browser.setHtml(content)
        layout.addWidget(browser)
        
        self.tabs.addTab(tab, "سهولة القراءة")
        
    def create_suggestions_tab(self, suggestions):
        """إنشاء تبويب الاقتراحات"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        content = "<h3>اقتراحات التحسين</h3>"
        
        if not suggestions:
            content += "<p>لا توجد اقتراحات للتحسين.</p>"
        else:
            content += "<ul>"
            for suggestion in suggestions:
                icon = "⚠️" if suggestion['type'] == 'warning' else "ℹ️"
                content += f"<li>{icon} {suggestion['message']}</li>"
            content += "</ul>"
        
        browser = QTextBrowser()
        browser.setHtml(content)
        layout.addWidget(browser)
        
        self.tabs.addTab(tab, "اقتراحات")


class Extension:
    """الإضافة الرئيسية"""
    
    def __init__(self, editor):
        self.editor = editor
        
    def get_menu_items(self):
        return [
            {
                'name': 'تحليل النص',
                'callback': self.analyze_text
            }
        ]
        
    def analyze_text(self):
        """تحليل النص الحالي"""
        current_editor = self.editor.get_current_editor()
        if not current_editor:
            return
            
        text = current_editor.toPlainText()
        dialog = AnalysisDialog(text, self.editor)
        dialog.exec_()