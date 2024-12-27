try:
    from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QWidget, QLabel, QCheckBox, QComboBox, QSpinBox,
                            QPushButton, QGroupBox, QMessageBox,
                            )
    from functools import lru_cache
    from typing import Dict, List, Any, Tuple
    import logging
    from utils.arabic_logger import log_in_arabic
except Exception as e:
    log_in_arabic(logging.ERROR, f"خطأ في استيراد المكتبات: {str(e)}")

class SettingsDialog(QDialog):
    """نافذة الإعدادات الرئيسية للتطبيق"""
    
    # الثوابت
    WINDOW_MIN_SIZE: Tuple[int, int] = (600, 400)
    DEFAULT_VERSION: str = '1.0.0'
    AUTOSAVE_MAX: int = 99999999
    MAX_CLOSED_TABS: int = 50
    STATUS_MESSAGE_TIMEOUT: int = 2000
    
    # قواميس التحويل
    ELIDE_MODES: Dict[str, str] = {
        'في الوسط': 'middle',
        'من اليمين': 'right',
        'من اليسار': 'left',
        'بدون قطع': 'none'
    }
    
    THEME_MODES: Dict[str, str] = {
        'فاتح': 'light',
        'داكن': 'dark'
    }
    
    UPDATE_INTERVALS: List[str] = ["يومياً", "أسبوعياً", "شهرياً"]
    
    def __init__(self, parent=None):
        """تهيئة نافذة الإعدادات"""
        try:
            super().__init__(parent)
            self.parent = parent
            self._settings_cache: Dict[str, Any] = {}
            self.logger = logging.getLogger(__name__)
            log_in_arabic(self.logger, logging.INFO, "بدء تهيئة نافذة الإعدادات")
            self._setup_window()
            self.setup_ui()
            self.load_current_settings()
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في تهيئة نافذة الإعدادات: {str(e)}")
            raise
    
    def _setup_window(self) -> None:
        """إعداد خصائص النافذة"""
        try:
            self.setWindowTitle("الإعدادات")
            self.setMinimumSize(*self.WINDOW_MIN_SIZE)
            log_in_arabic(self.logger, logging.DEBUG, "تم إعداد خصائص النافذة")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في إعداد خصائص النافذة: {str(e)}")
            raise
        
    def setup_ui(self) -> None:
        """إعداد واجهة المستخدم"""
        try:
            layout = QVBoxLayout(self)
            self.tab_widget = QTabWidget()
            self._create_tabs(layout)
            self._create_buttons(layout)
            log_in_arabic(self.logger, logging.DEBUG, "تم إعداد واجهة المستخدم")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في إعداد واجهة المستخدم: {str(e)}")
            raise

    def _create_tabs(self, layout: QVBoxLayout) -> None:
        """إنشاء التبويبات"""
        try:
            tabs: Dict[str, callable] = {
                "عام": self.setup_general_tab,
                "المظهر": self.setup_appearance_tab,
                "التحديثات": self.setup_updates_tab
            }
            
            for tab_name, setup_func in tabs.items():
                try:
                    tab = QWidget()
                    setup_func(tab)
                    self.tab_widget.addTab(tab, tab_name)
                    log_in_arabic(self.logger, logging.DEBUG, f"تم إنشاء تبويب {tab_name}")
                except Exception as e:
                    log_in_arabic(self.logger, logging.ERROR, f"خطأ في إنشاء تبويب {tab_name}: {str(e)}")
                    raise
            
            layout.addWidget(self.tab_widget)
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في إنشاء التبويبات: {str(e)}")
            raise

    def _create_buttons(self, layout: QVBoxLayout) -> None:
        """إنشاء أزرار التحكم"""
        try:
            buttons_layout = QHBoxLayout()
            buttons: List[Tuple[str, callable]] = [
                ("حفظ", self.save_settings),
                ("إلغاء", self.reject)
            ]
            
            for btn_text, slot in buttons:
                try:
                    btn = QPushButton(btn_text)
                    btn.clicked.connect(slot)
                    buttons_layout.addWidget(btn)
                    log_in_arabic(self.logger, logging.DEBUG, f"تم إنشاء زر {btn_text}")
                except Exception as e:
                    log_in_arabic(self.logger, logging.ERROR, f"خطأ في إنشاء زر {btn_text}: {str(e)}")
                    raise
            
            buttons_layout.insertStretch(0, 1)
            layout.addLayout(buttons_layout)
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في إنشاء أزرار التحكم: {str(e)}")
            raise

    @staticmethod
    def create_group(title: str, widgets: List[Any]) -> QGroupBox:
        """إنشاء مجموعة إعدادات"""
        try:
            group = QGroupBox(title)
            layout = QVBoxLayout()
            
            for widget in widgets:
                if isinstance(widget, (list, tuple)):
                    layout.addWidget(QLabel(widget[0]))
                    layout.addWidget(widget[1])
                else:
                    layout.addWidget(widget)
            
            group.setLayout(layout)
            return group
        except Exception as e:
            logging.getLogger(__name__).error(f"خطأ في إنشاء مجموعة {title}: {str(e)}")
            raise

    def _create_controls(self) -> None:
        """إنشاء جميع عناصر التحكم"""
        try:
            # التبويبات
            self.movable_tabs_checkbox = QCheckBox("السماح بتحريك التبويبات")
            self.scroll_buttons_checkbox = QCheckBox("إظهار أزرار التمرير")
            self.elide_mode_combo = QComboBox()
            self.elide_mode_combo.addItems(self.ELIDE_MODES.keys())
            self.max_closed_tabs_spin = QSpinBox()
            self.max_closed_tabs_spin.setRange(0, self.MAX_CLOSED_TABS)
            
            # الحفظ التلقائي
            self.autosave_checkbox = QCheckBox("تفعيل الحفظ التلقائي")
            self.autosave_interval = QSpinBox()
            self.autosave_interval.setRange(1, self.AUTOSAVE_MAX)
            self.autosave_interval.setSuffix(" ثانية")
            
            # التفاف النص
            self.word_wrap_checkbox = QCheckBox("تفعيل التفاف النص")
            
            # السمة
            self.theme_combo = QComboBox()
            self.theme_combo.addItems(self.THEME_MODES.keys())
            
            # التحديث التلقائي
            self.auto_update_checkbox = QCheckBox("تفعيل التحديث التلقائي")
            self.update_interval_combo = QComboBox()
            self.update_interval_combo.addItems(self.UPDATE_INTERVALS)
            
            log_in_arabic(self.logger, logging.DEBUG, "تم إنشاء جميع عناصر التحكم")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في إنشاء عناصر التحكم: {str(e)}")
            raise

    def setup_general_tab(self, tab: QWidget) -> None:
        """إعداد تبويب الإعدادات العامة"""
        try:
            layout = QVBoxLayout(tab)
            self._create_controls()
            
            groups = [
                ("إعدادات التبويبات", [
                    self.movable_tabs_checkbox,
                    self.scroll_buttons_checkbox,
                    ["طريقة قطع النص الطويل:", self.elide_mode_combo],
                    ["عدد التبويبات المغلقة المحفوظة:", self.max_closed_tabs_spin]
                ]),
                ("الحفظ التلقائي", [
                    self.autosave_checkbox,
                    ["الفاصل الزمني للحفظ:", self.autosave_interval]
                ]),
                ("التفاف النص", [self.word_wrap_checkbox])
            ]
            
            for title, widgets in groups:
                try:
                    layout.addWidget(self.create_group(title, widgets))
                    log_in_arabic(self.logger, logging.DEBUG, f"تم إنشاء مجموعة {title}")
                except Exception as e:
                    log_in_arabic(self.logger, logging.ERROR, f"خطأ في إنشاء مجموعة {title}: {str(e)}")
                    raise
                
            layout.addStretch()
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في إعداد تبويب الإعدادات العامة: {str(e)}")
            raise

    def setup_appearance_tab(self, tab: QWidget) -> None:
        """إعداد تبويب المظهر"""
        try:
            layout = QVBoxLayout(tab)
            layout.addWidget(self.create_group("السمة", [["السمة:", self.theme_combo]]))
            layout.addStretch()
            log_in_arabic(self.logger, logging.DEBUG, "تم إعداد تبويب المظهر")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في إعداد تبويب المظهر: {str(e)}")
            raise

    def setup_updates_tab(self, tab: QWidget) -> None:
        """إعداد تبويب التحديثات"""
        try:
            layout = QVBoxLayout(tab)
            
            version = self._get_cached_setting('app_version', self.DEFAULT_VERSION)
            version_label = QLabel(f"الإصدار الحالي: {version}")
            check_updates_btn = QPushButton("التحقق من التحديثات")
            check_updates_btn.clicked.connect(self.check_for_updates)
            
            layout.addWidget(self.create_group("معلومات الإصدار", [version_label, check_updates_btn]))
            layout.addWidget(self.create_group("التحديث التلقائي", [
                self.auto_update_checkbox,
                ["فترة التحقق من التحديثات:", self.update_interval_combo]
            ]))
            layout.addStretch()
            log_in_arabic(self.logger, logging.DEBUG, "تم إعداد تبويب التحديثات")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في إعداد تبويب التحديثات: {str(e)}")
            raise

    @lru_cache(maxsize=128)
    def _get_cached_setting(self, key: str, default: Any) -> Any:
        """الحصول على إعداد من الذاكرة المؤقتة"""
        try:
            if key not in self._settings_cache:
                self._settings_cache[key] = self.parent.settings_manager.get_setting(key, default)
            return self._settings_cache[key]
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في الحصول على الإعداد {key}: {str(e)}")
            return default

    def load_current_settings(self) -> None:
        """تحميل الإعدادات الحالية"""
        try:
            settings = self.parent.settings_manager.load_settings()
            self._settings_cache = settings
            
            self._load_tabs_settings(settings.get('tabs', {}))
            self._load_editor_settings(settings.get('editor', {}))
            self._load_updates_settings(settings.get('updates', {}))
            log_in_arabic(self.logger, logging.INFO, "تم تحميل الإعدادات الحالية")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في تحميل الإعدادات: {str(e)}")
            raise

    def _load_tabs_settings(self, tabs_settings: Dict[str, Any]) -> None:
        """تحميل إعدادات التبويبات"""
        try:
            self.movable_tabs_checkbox.setChecked(tabs_settings.get('movable', True))
            self.scroll_buttons_checkbox.setChecked(tabs_settings.get('scroll_buttons', True))
            
            elide_mode = tabs_settings.get('elide_mode', 'middle')
            self._set_combo_by_value(self.elide_mode_combo, self.ELIDE_MODES, elide_mode)
            self.max_closed_tabs_spin.setValue(tabs_settings.get('max_closed_tabs', 10))
            log_in_arabic(self.logger, logging.DEBUG, "تم تحميل إعدادات التبويبات")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في تحميل إعدادات التبويبات: {str(e)}")
            raise

    def _load_editor_settings(self, editor_settings: Dict[str, Any]) -> None:
        """تحميل إعدادات المحرر"""
        try:
            auto_save = editor_settings.get('auto_save', {})
            self.autosave_checkbox.setChecked(auto_save.get('enabled', False))
            self.autosave_interval.setValue(auto_save.get('interval', 5))
            self.word_wrap_checkbox.setChecked(editor_settings.get('word_wrap', False))
            
            theme = editor_settings.get('theme', 'light')
            self._set_combo_by_value(self.theme_combo, self.THEME_MODES, theme)
            log_in_arabic(self.logger, logging.DEBUG, "تم تحميل إعدادات المحرر")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في تحميل إعدادات المحرر: {str(e)}")
            raise

    def _load_updates_settings(self, updates_settings: Dict[str, Any]) -> None:
        """تحميل إعدادات التحديث"""
        try:
            self.auto_update_checkbox.setChecked(updates_settings.get('auto_check', True))
            self.update_interval_combo.setCurrentText(updates_settings.get('check_interval', 'يومياً'))
            log_in_arabic(self.logger, logging.DEBUG, "تم تحميل إعدادات التحديث")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في تحميل إعدادات التحديث: {str(e)}")
            raise

    @staticmethod
    def _set_combo_by_value(combo: QComboBox, mapping: Dict[str, str], value: str) -> None:
        """تعيين قيمة القائمة المنسدلة"""
        try:
            for ui_text, mapped_value in mapping.items():
                if mapped_value == value:
                    combo.setCurrentText(ui_text)
                    break
        except Exception as e:
            logging.getLogger(__name__).error(f"خطأ في تعيين قيمة القائمة المنسدلة: {str(e)}")
            raise

    def save_settings(self) -> None:
        """حفظ الإعدادات"""
        try:
            settings = self._settings_cache.copy()
            
            settings.update({
                'tabs': self._get_tabs_settings(),
                'editor': self._get_editor_settings(),
                'updates': self._get_updates_settings()
            })
            
            self.parent.settings_manager.save_settings(settings)
            self.parent.initialize_settings()
            self.parent.statusBar().showMessage("تم حفظ الإعدادات بنجاح", self.STATUS_MESSAGE_TIMEOUT)
            log_in_arabic(self.logger, logging.INFO, "تم حفظ الإعدادات بنجاح")
            self.accept()
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في حفظ الإعدادات: {str(e)}")
            QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء حفظ الإعدادات")
            raise

    def _get_tabs_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات التبويبات"""
        try:
            return {
                'movable': self.movable_tabs_checkbox.isChecked(),
                'scroll_buttons': self.scroll_buttons_checkbox.isChecked(),
                'elide_mode': self.ELIDE_MODES[self.elide_mode_combo.currentText()],
                'max_closed_tabs': self.max_closed_tabs_spin.value()
            }
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في الحصول على إعدادات التبويبات: {str(e)}")
            raise

    def _get_editor_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات المحرر"""
        try:
            return {
                'auto_save': {
                    'enabled': self.autosave_checkbox.isChecked(),
                    'interval': self.autosave_interval.value()
                },
                'word_wrap': self.word_wrap_checkbox.isChecked(),
                'theme': self.THEME_MODES[self.theme_combo.currentText()]
            }
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في الحصول على إعدادات المحرر: {str(e)}")
            raise

    def _get_updates_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات التحديث"""
        try:
            return {
                'auto_check': self.auto_update_checkbox.isChecked(),
                'check_interval': self.update_interval_combo.currentText()
            }
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في الحصول على إعدادات التحديث: {str(e)}")
            raise

    def check_for_updates(self) -> None:
        """التحقق من وجود تحديثات"""
        try:
            update_info = self.parent.update_manager.check_for_updates()
            
            if not update_info:
                QMessageBox.information(self, "التحديثات", "أنت تستخدم أحدث إصدار")
                log_in_arabic(self.logger, logging.INFO, "لا توجد تحديثات جديدة")
                return
                
            if 'error' in update_info:
                QMessageBox.warning(self, "خطأ في التحديث", update_info['message'])
                log_in_arabic(self.logger, logging.WARNING, f"خطأ في التحديث: {update_info['message']}")
                return
            
            self._show_update_dialog(update_info)
            log_in_arabic(self.logger, logging.INFO, f"تم العثور على تحديث جديد: {update_info['version']}")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في التحقق من التحديثات: {str(e)}")
            QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء التحقق من التحديثات")
            raise

    def _show_update_dialog(self, update_info: Dict[str, str]) -> None:
        """عرض نافذة التحديث"""
        try:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("تحديث متوفر")
            msg.setText(f"تم العثور على إصدار جديد: {update_info['version']}")
            msg.setDetailedText(update_info['description'])
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في عرض نافذة التحديث: {str(e)}")
            raise

    def closeEvent(self, event: Any) -> None:
        """عند إغلاق النافذة"""
        try:
            self.load_current_settings()
            event.accept()
            log_in_arabic(self.logger, logging.INFO, "تم إغلاق نافذة الإعدادات")
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ عند إغلاق النافذة: {str(e)}")
            event.accept()  # نقبل الإغلاق حتى في حالة الخطأ

