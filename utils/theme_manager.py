class ThemeManager:
    THEMES = {
        'داكن': {
            'background': '#1e1e1e',
            'foreground': '#ffffff',
            'selection': '#404040',
            'cursor': '#ffffff'
        },
        'فاتح': {
            'background': '#ffffff',
            'foreground': '#000000',
            'selection': '#b4d5fe',
            'cursor': '#000000'
        },
        'أزرق داكن': {
            'background': '#1e2127',
            'foreground': '#abb2bf',
            'selection': '#3e4451',
            'cursor': '#528bff'
        }
    }
    
    @staticmethod
    def apply_theme(editor, theme_name):
        if theme_name in ThemeManager.THEMES:
            theme = ThemeManager.THEMES[theme_name]
            editor.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {theme['background']};
                    color: {theme['foreground']};
                    selection-background-color: {theme['selection']};
                }}
            """)