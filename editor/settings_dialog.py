from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QWidget, QLabel, QCheckBox, QComboBox, QSpinBox,
                           QPushButton, QGroupBox, QMessageBox,
                           QTextEdit)
from PyQt5.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("الإعدادات")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setup_ui()
        self.load_current_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # إنشاء التبويبات
        self.tab_widget = QTabWidget()
        
        # تبويب الإعدادات العامة
        general_tab = QWidget()
        self.setup_general_tab(general_tab)
        self.tab_widget.addTab(general_tab, "عام")
        
        # تبويب المظهر
        appearance_tab = QWidget()
        self.setup_appearance_tab(appearance_tab)
        self.tab_widget.addTab(appearance_tab, "المظهر")
        
        # إضافة تبويب التحديثات
        updates_tab = QWidget()
        self.setup_updates_tab(updates_tab)
        self.tab_widget.addTab(updates_tab, "التحديثات")
        
        layout.addWidget(self.tab_widget)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        cancel_btn = QPushButton("إلغاء")
        
        save_btn.clicked.connect(self.save_settings)
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)

    def setup_general_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        # إعدادات التبويبات
        tabs_group = QGroupBox("إعدادات التبويبات")
        tabs_layout = QVBoxLayout()
        
        # خيار تحريك التبويبات
        self.movable_tabs_checkbox = QCheckBox("السماح بتحريك التبويبات")
        tabs_layout.addWidget(self.movable_tabs_checkbox)
        
        # خيار أزرار التمرير
        self.scroll_buttons_checkbox = QCheckBox("إظهار أزرار التمرير")
        tabs_layout.addWidget(self.scroll_buttons_checkbox)
        
        # طريقة قطع النص الطويل
        tabs_layout.addWidget(QLabel("طريقة قطع النص الطويل:"))
        self.elide_mode_combo = QComboBox()
        self.elide_mode_combo.addItems(["في الوسط", "من اليمين", "من اليسار", "بدون قطع"])
        tabs_layout.addWidget(self.elide_mode_combo)
        
        # عدد التبويبات المغلقة المحفوظة
        tabs_layout.addWidget(QLabel("عدد التبويبات المغلقة المحفوظة:"))
        self.max_closed_tabs_spin = QSpinBox()
        self.max_closed_tabs_spin.setRange(0, 50)
        tabs_layout.addWidget(self.max_closed_tabs_spin)
        
        tabs_group.setLayout(tabs_layout)
        layout.addWidget(tabs_group)
        
        # إعدادات الحفظ التلقائي
        autosave_group = QGroupBox("الحفظ التلقائي")
        autosave_layout = QVBoxLayout()
        
        self.autosave_checkbox = QCheckBox("تفعيل الحفظ التلقائي")
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(1, 99999999)
        self.autosave_interval.setSuffix(" ثانية")
        
        autosave_layout.addWidget(self.autosave_checkbox)
        autosave_layout.addWidget(QLabel("الفاصل الزمني للحفظ:"))
        autosave_layout.addWidget(self.autosave_interval)
        
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)
        
        # إعدادات التفاف النص
        text_wrap_group = QGroupBox("التفاف النص")
        text_wrap_layout = QVBoxLayout()
        
        self.word_wrap_checkbox = QCheckBox("تفعيل التفاف النص")
        text_wrap_layout.addWidget(self.word_wrap_checkbox)
        
        text_wrap_group.setLayout(text_wrap_layout)
        layout.addWidget(text_wrap_group)
        
        layout.addStretch()

    def setup_appearance_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        # إعدادات السمة
        theme_group = QGroupBox("السمة")
        theme_layout = QVBoxLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["فاتح", "داكن"])
        
        theme_layout.addWidget(QLabel("السمة:"))
        theme_layout.addWidget(self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        layout.addStretch()

    def setup_updates_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        # معلومات الإصدر
        version_group = QGroupBox("معلومات الإصدار")
        version_layout = QVBoxLayout()
        
        current_version = self.parent.settings_manager.get_setting('app_version', '1.0.0')
        version_label = QLabel(f"الإصدار الحالي: {current_version}")
        version_layout.addWidget(version_label)
        
        # زر التحقق من التحديثات
        check_updates_btn = QPushButton("التحقق من التحديثات")
        check_updates_btn.clicked.connect(self.check_for_updates)
        version_layout.addWidget(check_updates_btn)
        
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)
        
        # إعدادات التحديث التلقائي
        auto_update_group = QGroupBox("التحديث التلقائي")
        auto_update_layout = QVBoxLayout()
        
        self.auto_update_checkbox = QCheckBox("تفعيل التحديث التلقائي")
        self.update_interval_combo = QComboBox()
        self.update_interval_combo.addItems(["يومياً", "أسبوعياً", "شهرياً"])
        
        auto_update_layout.addWidget(self.auto_update_checkbox)
        auto_update_layout.addWidget(QLabel("فترة التحقق من التحديثات:"))
        auto_update_layout.addWidget(self.update_interval_combo)
        
        auto_update_group.setLayout(auto_update_layout)
        layout.addWidget(auto_update_group)
        
        layout.addStretch()

    def load_current_settings(self):
        """تحميل الإعدادات الحالية"""
        settings = self.parent.settings_manager.load_settings()
        
        # تحميل إعدادات التبويبات
        tabs_settings = settings.get('tabs', {})
        self.movable_tabs_checkbox.setChecked(tabs_settings.get('movable', True))
        self.scroll_buttons_checkbox.setChecked(tabs_settings.get('scroll_buttons', True))
        
        elide_mode = tabs_settings.get('elide_mode', 'middle')
        elide_mode_text = {
            'middle': 'في الوسط',
            'right': 'من اليمين',
            'left': 'من اليسار',
            'none': 'بدون قطع'
        }.get(elide_mode, 'في الوسط')
        self.elide_mode_combo.setCurrentText(elide_mode_text)
        
        self.max_closed_tabs_spin.setValue(tabs_settings.get('max_closed_tabs', 10))
        
        # تحميل إعدادات الحفظ التلقائي
        self.autosave_checkbox.setChecked(
            settings.get('editor', {}).get('auto_save', {}).get('enabled', False)
        )
        self.autosave_interval.setValue(
            settings.get('editor', {}).get('auto_save', {}).get('interval', 5)
        )
        
        # تحميل إعدادات السمة
        self.theme_combo.setCurrentText(
            'داكن' if settings.get('editor', {}).get('theme') == 'dark' else 'فاتح'
        )
        
        # تحميل إعدادات التحديث التلقائي
        updates_settings = settings.get('updates', {})
        self.auto_update_checkbox.setChecked(updates_settings.get('auto_check', True))
        self.update_interval_combo.setCurrentText(updates_settings.get('check_interval', 'يومياً'))

        # تحميل إعدادات التفاف النص
        self.word_wrap_checkbox.setChecked(
            settings.get('editor', {}).get('word_wrap', False)
        )

    def save_settings(self):
        """حفظ الإعدادات"""
        settings = self.parent.settings_manager.load_settings()
        
        # حفظ إعدادات التبويبات
        if 'tabs' not in settings:
            settings['tabs'] = {}
        
        settings['tabs']['movable'] = self.movable_tabs_checkbox.isChecked()
        settings['tabs']['scroll_buttons'] = self.scroll_buttons_checkbox.isChecked()
        
        elide_mode_map = {
            'في الوسط': 'middle',
            'من اليمين': 'right',
            'من اليسار': 'left',
            'بدون قطع': 'none'
        }
        settings['tabs']['elide_mode'] = elide_mode_map[self.elide_mode_combo.currentText()]
        settings['tabs']['max_closed_tabs'] = self.max_closed_tabs_spin.value()
        
        # حفظ إعدادات الحفظ التلقائي
        if 'editor' not in settings:
            settings['editor'] = {}
        if 'auto_save' not in settings['editor']:
            settings['editor']['auto_save'] = {}
            
        settings['editor']['auto_save']['enabled'] = self.autosave_checkbox.isChecked()
        settings['editor']['auto_save']['interval'] = self.autosave_interval.value()
        
        # حفظ إعدادات التفاف النص
        settings['editor']['word_wrap'] = self.word_wrap_checkbox.isChecked()
        
        # حفظ إعدادات السمة
        settings['editor']['theme'] = 'dark' if self.theme_combo.currentText() == 'داكن' else 'light'
        
        # حفظ الإعدادات
        self.parent.settings_manager.save_settings(settings)
        
        # استخدام دالة initialize_settings لتطبيق الإعدادات
        self.parent.initialize_settings()
        
        self.parent.statusBar().showMessage("تم حفظ الإعدادات بنجاح", 2000)
        self.accept()

    def apply_settings(self, settings):
        """تطبيق الإعدادات الجديدة"""
        # تطبيق إعدادات التبويبات
        tabs_settings = settings.get('tabs', {})
        tab_manager = self.parent.tab_manager
        
        tab_manager.setMovable(tabs_settings.get('movable', True))
        tab_manager.setUsesScrollButtons(tabs_settings.get('scroll_buttons', True))
        
        elide_mode_map = {
            'middle': Qt.ElideMiddle,
            'right': Qt.ElideRight,
            'left': Qt.ElideLeft,
            'none': Qt.ElideNone
        }
        tab_manager.setElideMode(elide_mode_map[tabs_settings.get('elide_mode', 'middle')])
        tab_manager.max_closed_tabs = tabs_settings.get('max_closed_tabs', 10)
        
        # تطبيق إعدادات الحفظ التلقائي
        if hasattr(self.parent, 'auto_saver'):
            self.parent.auto_saver.enabled = settings['editor']['auto_save']['enabled']
            self.parent.auto_saver.interval = settings['editor']['auto_save']['interval']
        
        # تطبيق إعدادات التحديث التلقائي
        if hasattr(self.parent, 'update_manager'):
            self.parent.setup_auto_update_timer(settings['updates'])
        
        # تطبيق السمة
        if hasattr(self.parent, 'apply_theme'):
            self.parent.apply_theme(settings['editor']['theme'])
        
        # تطبيق التفاف النص على جميع المحررات المفتوحة
        word_wrap = settings['editor'].get('word_wrap', False)
        for i in range(self.parent.tab_manager.count()):
            editor = self.parent.tab_manager.widget(i).findChild(QTextEdit)
            if editor:
                editor.setLineWrapMode(
                    QTextEdit.WidgetWidth if word_wrap else QTextEdit.NoWrap
                )

    def check_for_updates(self):
        """التحقق من وجود تحديثات"""
        update_info = self.parent.update_manager.check_for_updates()
        
        if update_info:
            if 'error' in update_info:
                # عرض رسالة الخطأ
                QMessageBox.warning(
                    self,
                    "خطأ في التحديث",
                    update_info['message'],
                    QMessageBox.Ok
                )
            else:
                # عرض معلومات التحديث
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("تحديث متوفر")
                msg.setText(f"تم العثور على إصدار جديد: {update_info['version']}")
                msg.setDetailedText(update_info['description'])
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
        else:
            QMessageBox.information(self, "التحديثات", "أنت تستخدم أحدث إصدار")

    def closeEvent(self, event):
        """عند إغلاق النافذة"""
        # إعادة تحميل الإعدادات الأصلية
        self.load_current_settings()
        event.accept()

