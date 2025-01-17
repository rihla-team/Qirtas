"""
محرر رحلة - شريط القوائم العربي
============================

هذا الملف يحتوي على تعريف شريط القوائم العربي للمحرر.
يوفر واجهة مستخدم عربية كاملة مع اختصارات لوحة المفاتيح.

المميزات:
--------
- قوائم عربية كاملة
- اختصارات لوحة مفاتيح قياسية
- دعم كامل للغة العربية
- قابلية التخصيص والتوسيع
- إدارة فعالة للذاكرة

الفئات:
------
- ArabicMenuBar: الفئة الرئيسية لشريط القوائم العربي

التبعيات:
--------
- PyQt5.QtWidgets: مكتبة واجهة المستخدم الرسومية
- PyQt5.QtGui: مكتبة العناصر الرسومية
- PyQt5.QtCore: المكتبة الأساسية
- editor.terminal_widget: الطرفية العربية
- editor.settings_dialog: نافذة الإعدادات
"""
try:
    from PyQt5.QtWidgets import QMenuBar, QAction, QFontDialog, QMessageBox, QPushButton
    from PyQt5.QtGui import QKeySequence, QIcon
    from PyQt5.QtCore import Qt
    from editor.settings_dialog import SettingsDialog
    from functools import partial
    from utils.arabic_logger import log_in_arabic
    import logging
except Exception as e:
    try:
        import logging
        logger = logging.getLogger(__name__)
        log_in_arabic(logger, logging.ERROR, f"خطأ في استيراد الموديلات: {e}")
    except Exception as e:
        print(f"خطأ في استيراد الموديلات: {e}")
    
class ArabicMenuBar(QMenuBar):
    """
    شريط القوائم العربي للمحرر
    
    يوفر هذا الصف واجهة مستخدم عربية كاملة مع قوائم واختصارات لوحة مفاتيح.
    يدعم جميع العمليات الأساسية مثل فتح وحفظ الملفات، التحرير، والتنسيق.

    السمات:
    -------
    SHORTCUTS : dict
        قاموس يحتوي على الاختصارات الشائعة المستخدمة في التطبيق
        
    MENU_ITEMS : dict
        قاموس يحتوي على تعريف جميع عناصر القوائم مع اختصاراتها

    المتغيرات:
    ----------
    parent : QWidget
        النافذة الأم التي يتبع لها شريط القوائم
        
    _menus : dict
        قاموس لتخزين القوائم المنشأة للوصول السريع
    """

    # تعريف الاختصارات الشائعة
    SHORTCUTS = {
        'terminal': [QKeySequence("Ctrl+ذ"), QKeySequence("Ctrl+`")],
        'sidebar': 'Ctrl+L',
    }

    # تعريف عناصر القوائم
    MENU_ITEMS = {
        'file': [
            ('فتح', 'Ctrl+O', 'open_file'),
            ('حفظ', 'Ctrl+S', 'save_file'),
            ('حفظ باسم', 'Ctrl+Shift+S', 'save_file_as'),
            ('نافذة جديدة', 'Ctrl+N', 'new_file'),
            ('فتح مجلد...', 'Ctrl+K', 'open_folder'),
        ],
        'edit': [
            ('تراجع', QKeySequence.Undo, 'undo'),
            ('إعادة', QKeySequence.Redo, 'redo'),
            ('قص', QKeySequence.Cut, 'cut'),
            ('نسخ', QKeySequence.Copy, 'copy'),
            ('لصق', QKeySequence.Paste, 'paste'),
            ('تحديد الكل', QKeySequence.SelectAll, 'selectAll'),
        ],
        'format': [
            ('عريض', QKeySequence.Bold, 'bold'),
            ('مائل', QKeySequence.Italic, 'italic'),
            ('تسطير', QKeySequence.Underline, 'underline'),
        ],
        'alignment': [
            ('محاذاة لليمين', 'Ctrl+Shift+R', 'align_right'),
            ('محاذاة لليسار', 'Ctrl+Shift+L', 'align_left'),
            ('توسيط', 'Ctrl+Shift+E', 'align_center'),
            ('ضبط', 'Ctrl+Shift+J', 'align_justify'),
        ]
    }

    def __init__(self, parent=None):
        """
        تهيئة شريط القوائم
        
        المعاملات:
        ---------
        parent : QWidget, optional
            النافذة الأم التي يتبع لها شريط القوائم (الافتراضي: None)
        """
        super().__init__(parent)
        self.parent = parent
        self._menus = {}  # تخزين القوائم للوصول السريع
        self.setup_menus()

    def create_action(self, text, shortcut=None, callback=None, checkable=False, icon=None):
        """
        إنشاء إجراء جديد مع الخصائص المحددة
        
        المعاملات:
        ---------
        text : str
            نص الإجراء الذي سيظهر في القائمة
        shortcut : str or QKeySequence, optional
            اختصار لوحة المفاتيح للإجراء
        callback : callable, optional
            الدالة التي سيتم تنفيذها عند تفعيل الإجراء
        checkable : bool, optional
            هل الإجراء قابل للتحديد (الافتراضي: False)
        icon : str, optional
            مسار الأيقونة للإجراء
            
        يُرجع:
        ------
        QAction
            كائن الإجراء المنشأ
        """
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut if isinstance(shortcut, (QKeySequence, str)) else QKeySequence(shortcut))
        if callback:
            action.triggered.connect(callback)
        if checkable:
            action.setCheckable(True)
        if icon:
            action.setIcon(QIcon(icon))
        return action

    def create_menu(self, title):
        """
        إنشاء قائمة جديدة وتخزينها
        
        المعاملات:
        ---------
        title : str
            عنوان القائمة
            
        يُرجع:
        ------
        QMenu
            كائن القائمة المنشأة
        """
        menu = self.addMenu(title)
        self._menus[title] = menu
        return menu

    def get_menu(self, title):
        """
        الحصول على قائمة موجودة أو إنشاء واحدة جديدة
        
        المعاملات:
        ---------
        title : str
            عنوان القائمة
            
        يُرجع:
        ------
        QMenu
            كائن القائمة الموجودة أو الجديدة
        """
        return self._menus.get(title) or self.create_menu(title)

    def get_editor_action(self, method_name):
        """
        إنشاء دالة callback للمحرر مع التحقق من وجود المحرر
        
        المعاملات:
        ---------
        method_name : str
            اسم الدالة في المحرر
            
        يُرجع:
        ------
        callable
            دالة callback جاهزة للاستخدام
        """
        return partial(self._execute_editor_action, method_name)

    def _execute_editor_action(self, method_name):
        """
        تنفيذ إجراء المحرر بعد التحقق من وجوده
        
        المعاملات:
        ---------
        method_name : str
            اسم الدالة المراد تنفيذها
        """
        editor = self.parent.get_current_editor()
        if editor and hasattr(editor, method_name):
            getattr(editor, method_name)()

    def get_format_action(self, format_type):
        """
        إنشاء دالة callback للتنسيق
        
        المعاملات:
        ---------
        format_type : str
            نوع التنسيق المطلوب
            
        يُرجع:
        ------
        callable
            دالة callback جاهزة للاستخدام
        """
        return partial(self._execute_format_action, format_type)

    def _execute_format_action(self, format_type):
        """
        تنفيذ إجراء التنسيق
        
        المعاملات:
        ---------
        format_type : str
            نوع التنسيق المراد تطبيقه
        """
        if self.parent:
            self.parent.format_text(format_type)

    def setup_file_menu(self):
        """
        إعداد قائمة الملف
        
        تقوم هذه الدالة بإنشاء وإعداد قائمة الملف مع جميع إجراءاتها
        مثل فتح وحفظ الملفات وإضافة الطرفية والشريط الجانبي
        """
        file_menu = self.create_menu('ملف')
        
        # إضافة الإجراءات الرئيسية
        for text, shortcut, method in self.MENU_ITEMS['file']:
            file_menu.addAction(self.create_action(text, shortcut, partial(getattr(self.parent, method))))
            
        file_menu.addSeparator()
        
        # إضافة إجراء الطرفية
        terminal_action = self.create_action('فتح موجه الاوامر', None, self.parent.add_terminal)
        terminal_action.setShortcuts(self.SHORTCUTS['terminal'])
        file_menu.addAction(terminal_action)
        
        # إضافة إجراء الشريط الجانبي
        self.toggle_sidebar_action = self.create_action(
            ' الشريط الجانبي', 
            self.SHORTCUTS['sidebar'],
            self.parent.sidebar_manager.toggle_sidebar,
            checkable=True
        )
        self.toggle_sidebar_action.setChecked(True)
        file_menu.addAction(self.toggle_sidebar_action)

    def setup_edit_menu(self):
        """
        إعداد قائمة التحرير
        
        تقوم هذه الدالة بإنشاء وإعداد قائمة التحرير مع جميع إجراءاتها
        مثل التراجع والإعادة والقص والنسخ واللصق
        """
        edit_menu = self.create_menu('تحرير')
        
        for text, shortcut, method in self.MENU_ITEMS['edit']:
            edit_menu.addAction(self.create_action(text, shortcut, self.get_editor_action(method)))
            
        edit_menu.addSeparator()

    def setup_format_menu(self):
        """
        إعداد قائمة التنسيق
        
        تقوم هذه الدالة بإنشاء وإعداد قائمة التنسيق مع جميع إجراءاتها
        مثل تنسيق النص والمحاذاة واختيار الخط
        """
        format_menu = self.create_menu('تنسيق')
        
        # إضافة أزرار التنسيق
        for text, shortcut, format_type in self.MENU_ITEMS['format']:
            format_menu.addAction(self.create_action(text, shortcut, self.get_format_action(format_type)))
            
        # إضافة قائمة المحاذاة
        alignment_menu = format_menu.addMenu('محاذاة')
        for text, shortcut, align_type in self.MENU_ITEMS['alignment']:
            alignment_menu.addAction(self.create_action(text, shortcut, self.get_format_action(align_type)))
        
        format_menu.addSeparator()
        format_menu.addAction(self.create_action('اختيار الخط...', callback=self.show_font_dialog))

    def setup_menus(self):
        """
        إعداد جميع القوائم
        
        تقوم هذه الدالة بإعداد جميع القوائم في شريط القوائم
        وإضافة زر الإعدادات
        """
        self.setup_file_menu()
        self.setup_edit_menu()
        self.setup_format_menu()
        self.setup_settings_button()

    def setup_settings_button(self):
        """
        إعداد زر الإعدادات
        
        تقوم هذه الدالة بإنشاء وإعداد زر الإعدادات في الزاوية
        """
        settings_button = QPushButton(self)
        settings_button.setIcon(QIcon('resources/icons/settings.png'))
        settings_button.setToolTip('الإعدادات')
        settings_button.clicked.connect(self.show_settings)
        self.setCornerWidget(settings_button, Qt.TopRightCorner)
        
    def show_settings(self):
        """
        عرض نافذة الإعدادات
        
        تقوم هذه الدالة بعرض نافذة الإعدادات وإدارة الأخطاء
        """
        try:
            dialog = SettingsDialog(self.parent)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء فتح الإعدادات: {str(e)}")

    def show_font_dialog(self):
        """
        عرض نافذة اختيار الخط
        
        تقوم هذه الدالة بعرض نافذة اختيار الخط وتطبيق الخط المختار
        """
        current_editor = self.parent.get_current_editor()
        if not current_editor:
            return
            
        font, ok = QFontDialog.getFont(self.parent.default_font, self)
        if ok:
            self.parent.default_font = font
            self.parent.settings_manager.save_font(font)
            current_editor.apply_font(font)

    def load_font_settings(self):
        """
        تحميل إعدادات الخط
        
        تقوم هذه الدالة بتحميل وتطبيق إعدادات الخط على المحرر الحالي
        """
        current_editor = self.parent.get_current_editor()
        if current_editor:
            current_editor.setFont(self.parent.default_font)



        