from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel
from PyQt5.QtCore import Qt
from pygments.styles import get_all_styles , get_style_by_name
import json
import os

class ThemeSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("اختيار المظهر")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        # إضافة عنوان
        title = QLabel("اختر مظهر التلوين:")
        title.setAlignment(Qt.AlignRight)
        layout.addWidget(title)
        
        # قائمة المظاهر
        self.theme_combo = QComboBox()
        self.load_themes()
        layout.addWidget(self.theme_combo)
        
        # زر التطبيق
        apply_btn = QPushButton("تطبيق")
        apply_btn.clicked.connect(self.apply_theme)
        layout.addWidget(apply_btn)
        
        self.setLayout(layout)
        
    def load_themes(self):
        try:
            # الحصول على جميع المظاهر المتاحة من Pygments
            available_themes = list(get_all_styles())
            
            # قراءة المظهر الحالي من الإعدادات
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                current_theme = settings.get('editor', {}).get('syntax_highlighting', {}).get('theme', 'monokai')
                
            # إضافة المظاهر للقائمة المنسدلة
            self.theme_combo.addItems(available_themes)
            
            # تحديد المظهر الحالي
            try:
                current_index = available_themes.index(current_theme)
                self.theme_combo.setCurrentIndex(current_index)
            except ValueError:
                # إذا لم يتم العثور على المظهر الحالي، نستخدم monokai كافتراضي
                default_index = available_themes.index('monokai')
                self.theme_combo.setCurrentIndex(default_index)
                
        except Exception as e:
            print(f"خطأ في تحميل المظاهر: {str(e)}")
            # إضافة بعض المظاهر الافتراضية في حالة الخطأ
            default_themes = ['monokai', 'default', 'emacs', 'vim']
            self.theme_combo.addItems(default_themes)
            
    def apply_theme(self):
        """تطبيق المظهر المحدد"""
        selected_theme = self.theme_combo.currentText()
        try:
            # تحديث المحرر الحالي
            if hasattr(self.parent, 'tab_manager'):
                current_editor = self.parent.tab_manager.currentWidget()
                if current_editor and hasattr(current_editor, 'highlighter'):
                    # تطبيق المظهر مباشرة
                    current_editor.highlighter.style = get_style_by_name(selected_theme)
                    current_editor.highlighter._format_cache.clear()
                    current_editor.highlighter.rehighlight()
                    
                    # تحديث جميع علامات التبويب المفتوحة
                    for i in range(self.parent.tab_manager.count()):
                        editor = self.parent.tab_manager.widget(i)
                        if editor and hasattr(editor, 'highlighter') and editor != current_editor:
                            editor.highlighter.style = get_style_by_name(selected_theme)
                            editor.highlighter._format_cache.clear()
                            editor.highlighter.rehighlight()
            
            # حفظ في الإعدادات
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            if 'editor' not in settings:
                settings['editor'] = {}
            if 'syntax_highlighting' not in settings['editor']:
                settings['editor']['syntax_highlighting'] = {}
            
            settings['editor']['syntax_highlighting']['theme'] = selected_theme
            
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            print(f"تم تطبيق المظهر {selected_theme} بنجاح")
            self.close()
            
        except Exception as e:
            print(f"خطأ في تطبيق المظهر: {str(e)}")

