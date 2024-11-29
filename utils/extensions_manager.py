from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QWidget, QPushButton, QCheckBox,
                           QTabWidget, QTextBrowser, QGroupBox, QGridLayout,
                           QLineEdit, QMenu, QAction, QMessageBox, QProgressBar,
                           QStyle, QToolButton, QTextEdit, QComboBox, QFormLayout,
                           QFileDialog)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QColor, QImage
import os
import json
import logging
import importlib.util
import sys
from .extension_creator import ExtensionCreatorDialog
import uuid
from .extension_store import ExtensionStore

class ExtensionManagerDialog(QDialog):
    def __init__(self, extensions_manager):
        super().__init__()
        self.extensions_manager = extensions_manager
        self.checkboxes = {}
        self.extension_widgets = {}
        self.store = ExtensionStore()  # إنشاء كائن المتجر
        
        # إعداد النافذة
        self.setWindowTitle("مدير الإضافات")
        self.setMinimumSize(900, 700)
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DialogHelpButton))
        
        # إضافة متغيرات جديدة للتتبع
        self.current_filter = "الكل"
        self.search_text = ""
        self.sort_order = "name_asc"  # ترتيب افتراضي
        
        self.setup_style()
        self.setup_ui()
        
        # تحديث تلقائي
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.update_log)
        self.log_timer.start(5000)

    def setup_style(self):
        """إعداد النمط والألوان"""


    def setup_ui(self):
        """إعداد واجهة المستخدم الرئيسية"""
        # إزالة أي تخطيط سابق
        if self.layout():
            old_layout = self.layout()
            for i in reversed(range(old_layout.count())):
                old_layout.itemAt(i).widget().setParent(None)
            QWidget().setLayout(old_layout)
        
        main_layout = QVBoxLayout()
        
        # التبويبات
        self.tab_widget = QTabWidget()
        
        # إنشاء التبويبات
        installed_tab = QWidget()
        store_tab = QWidget()
        stats_tab = QWidget()
        advanced_tab = QWidget()
        create_extension_tab = QWidget()
        
        # إضافة التبويبات
        self.tab_widget.addTab(installed_tab, "الإضافات المثبتة")
        self.tab_widget.addTab(store_tab, "متجر الإضافات")
        self.tab_widget.addTab(stats_tab, "الإحصائيات والسجل")
        self.tab_widget.addTab(advanced_tab, "إعدادات متقدمة")
        self.tab_widget.addTab(create_extension_tab, "إنشاء إضافة")
        
        # إعداد محتوى كل تبويب
        self.setup_installed_tab(installed_tab)
        self.setup_store_tab(store_tab)
        self.setup_stats_tab(stats_tab)
        self.setup_advanced_tab(advanced_tab)
        self.setup_create_extension_tab(create_extension_tab)
        
        main_layout.addWidget(self.tab_widget)
        
        # شريط الحالة
        status_bar = self.create_enhanced_status_bar()
        main_layout.addLayout(status_bar)
        
        self.setLayout(main_layout)


    def setup_store_tab(self, tab):
        """إعداد تبويب متجر الإضافات"""
        layout = QVBoxLayout()
        
        # شريط البحث في المتجر
        store_search = QLineEdit()
        store_search.setPlaceholderText("ابحث عن إضافات جديدة...")
        store_search.textChanged.connect(self.search_store)
        layout.addWidget(store_search)
        
        # عرض الإضافات المتاحة
        scroll = QScrollArea()
        self.store_widget = QWidget()
        self.store_layout = QVBoxLayout()
        
        # جلب وعرض الإضافات المتوفرة
        self.load_store_extensions()
        
        self.store_widget.setLayout(self.store_layout)
        scroll.setWidget(self.store_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        tab.setLayout(layout)

    def load_store_extensions(self):
        """تحميل وعرض الإضافات المتوفرة في المتجر"""
        # مسح العناصر السابقة
        for i in reversed(range(self.store_layout.count())):
            self.store_layout.itemAt(i).widget().setParent(None)
        
        # جلب الإضافات المتوفرة
        extensions = self.store.get_available_extensions()
        
        # عرض الإضافات
        for ext in extensions:
            ext_widget = self.create_store_extension_widget(ext)
            self.store_layout.addWidget(ext_widget)

    def search_store(self, query):
        """البحث في المتجر"""
        if query:
            extensions = self.store.search_extensions(query)
        else:
            extensions = self.store.get_available_extensions()
        
        # تحديث العرض
        self.update_store_view(extensions)

    def setup_advanced_tab(self, tab):
        """إعداد تبويب الإعدادات المتقدمة"""
        layout = QVBoxLayout()
        
        # إعدادات التحديث التلقائي
        update_group = QGroupBox("التحديث التلقائي")
        update_layout = QVBoxLayout()
        
        self.auto_update_checkbox = QCheckBox("تفعيل التحديث التلقائي للإضافات")
        self.update_interval_combo = QComboBox()
        self.update_interval_combo.addItems(["يومياً", "أسبوعياً", "شهرياً"])
        
        update_layout.addWidget(self.auto_update_checkbox)
        update_layout.addWidget(QLabel("فترة التحديث:"))
        update_layout.addWidget(self.update_interval_combo)
        update_group.setLayout(update_layout)
        
        # إعدادات التشغيل
        startup_group = QGroupBox("إعدادات التشغيل")
        startup_layout = QVBoxLayout()
        
        self.load_disabled_checkbox = QCheckBox("تحميل الإضافات المعطلة عند التشغيل")
        self.safe_mode_checkbox = QCheckBox("وضع الأمان (تعطيل جميع الإضافات)")
        
        startup_layout.addWidget(self.load_disabled_checkbox)
        startup_layout.addWidget(self.safe_mode_checkbox)
        startup_group.setLayout(startup_layout)
        
        # أزرار الحفظ
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("حفظ الإعدادات")
        save_button.clicked.connect(self.save_advanced_settings)
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_button)
        
        layout.addWidget(update_group)
        layout.addWidget(startup_group)
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        tab.setLayout(layout)
        
        # تحميل الإعدادات الحالية
        self.load_advanced_settings()

    def create_enhanced_status_bar(self):
        """إنشاء شريط حالة محسن"""
        status_bar = QHBoxLayout()
        
        # معلومات الإضافات
        self.status_label = QLabel()
        self.update_status()
        
        # معلومات الذاكرة
        self.memory_label = QLabel()
        self.update_memory_usage()
        
        # معلومات التحديثات
        self.updates_label = QLabel()
        self.check_for_updates()
        
        # تحديث دوري للمعلومات
        timer = QTimer(self)
        timer.timeout.connect(self.update_memory_usage)
        timer.timeout.connect(self.check_for_updates)
        timer.start(10000)  # تحديث كل 10 ثواني
        
        status_bar.addWidget(self.status_label)
        status_bar.addStretch()
        status_bar.addWidget(self.memory_label)
        status_bar.addWidget(self.updates_label)
        
        return status_bar

    def enable_all_extensions(self):
        """تفعيل جميع الإضافات"""
        success_count = 0
        fail_count = 0
        
        for ext_id in self.extensions_manager.extensions:
            if ext_id not in self.extensions_manager.active_extensions:
                try:
                    if self.extensions_manager.activate_extension(ext_id):
                        success_count += 1
                        if ext_id in self.checkboxes:
                            self.checkboxes[ext_id].setChecked(True)
                        self.update_extension_status(ext_id)
                except Exception as e:
                    fail_count += 1
                    logging.error(f"فشل تفعيل الإضافة {ext_id}: {str(e)}")
        
        self.update_status()
        self.filter_extensions()  # تحديث العرض
        
        # عرض نتيجة العملية
        if fail_count == 0:
            QMessageBox.information(self, "نجح", f"تم تفعيل {success_count} إضافة بنجاح")
        else:
            QMessageBox.warning(self, "تحذير", 
                              f"تم تفعيل {success_count} إضافة بنجاح\n"
                              f"فشل تفعيل {fail_count} إضافة")

    def disable_all_extensions(self):
        """تعطيل جميع الإضافات"""
        success_count = 0
        fail_count = 0
        
        for ext_id in list(self.extensions_manager.active_extensions):  # نسخة من القائمة
            try:
                if self.extensions_manager.deactivate_extension(ext_id):
                    success_count += 1
                    if ext_id in self.checkboxes:
                        self.checkboxes[ext_id].setChecked(False)
                    self.update_extension_status(ext_id)
            except Exception as e:
                fail_count += 1
                logging.error(f"فشل تعطيل الإضافة {ext_id}: {str(e)}")
        
        self.update_status()
        self.filter_extensions()  # تحديث العرض
        
        # عرض نتيجة العملية
        if fail_count == 0:
            QMessageBox.information(self, "نجاح", f"تم تعطيل {success_count} إضافة بنجاح")
        else:
            QMessageBox.warning(self, "تحذير", 
                              f"تم تعطيل {success_count} إضافة بنجاح\n"
                              f"فشل تعطيل {fail_count} إضافة")

    def sort_extensions(self, sort_type):
        """ترتيب الإضافات"""
        extensions_list = []
        for ext_id, ext_data in self.extensions_manager.extensions.items():
            name = ext_data['manifest'].get('name', ext_id)
            extensions_list.append((ext_id, name, ext_data))
        
        # ترتيب القائمة
        if sort_type == "الاسم تصاعدياً":
            extensions_list.sort(key=lambda x: x[1])
        elif sort_type == "الاسم تنازلياً":
            extensions_list.sort(key=lambda x: x[1], reverse=True)
        elif sort_type == "الحالة":
            extensions_list.sort(key=lambda x: x[0] in self.extensions_manager.active_extensions, reverse=True)
        
        # إعادة ترتيب الـ widgets
        for i, (ext_id, _, _) in enumerate(extensions_list):
            if ext_id in self.extension_widgets:
                widget = self.extension_widgets[ext_id]
                self.extensions_layout.removeWidget(widget)
                self.extensions_layout.insertWidget(i, widget)

    def setup_installed_tab(self, tab):
        """إعداد تبويب الإضافات المثبتة"""
        layout = QVBoxLayout()
        
        # شريط الأدوات العلوي
        toolbar = QHBoxLayout()
        
        # تصفية حسب الحالة
        filter_label = QLabel("عرض:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["الكل", "نشط", "معطل"])
        self.filter_combo.currentTextChanged.connect(self.filter_extensions)
        
        # أزرار الإجراءات
        refresh_btn = QPushButton()
        refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        refresh_btn.setToolTip("تحديث")
        refresh_btn.clicked.connect(self.refresh_extensions)
        
        enable_all_btn = QPushButton("تفعيل الكل")
        enable_all_btn.clicked.connect(self.enable_all_extensions)
        
        disable_all_btn = QPushButton("تعطيل الكل")
        disable_all_btn.clicked.connect(self.disable_all_extensions)
        
        # إضافة العناصر إلى شريط الأدوات
        toolbar.addWidget(filter_label)
        toolbar.addWidget(self.filter_combo)
        toolbar.addStretch()
        toolbar.addWidget(disable_all_btn)
        toolbar.addWidget(enable_all_btn)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # منطقة الإضافات
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # حاوية الإضافات
        extensions_container = QWidget()
        self.extensions_layout = QVBoxLayout(extensions_container)
        self.extensions_layout.setSpacing(1)
        self.extensions_layout.setContentsMargins(0, 0, 0, 0)
        
        # إضافة الإضافات
        self.extension_widgets = {}  # إعادة تعيين القاموس
        for ext_id, ext_data in self.extensions_manager.extensions.items():
            ext_widget = self.create_extension_widget(ext_id, ext_data)
            self.extension_widgets[ext_id] = ext_widget
            self.extensions_layout.addWidget(ext_widget)
        
        self.extensions_layout.addStretch()
        scroll.setWidget(extensions_container)
        layout.addWidget(scroll)
        
        tab.setLayout(layout)

    def create_extension_widget(self, ext_id, ext_data):
        """إنشاء واجهة الإضافة"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # معلومات الإضافة
        manifest = ext_data['manifest']
        
        # أيقونة الإضافة
        icon_label = QLabel()
        icon_path = os.path.join(ext_data['path'], 'icon.png')
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setPixmap(self.style().standardIcon(QStyle.SP_FileIcon).pixmap(24, 24))
        layout.addWidget(icon_label)
        
        # معلومات الإضافة
        info_layout = QVBoxLayout()
        name_label = QLabel(f"<b>{manifest.get('name', ext_id)}</b>")
        desc_label = QLabel(manifest.get('description', ''))
        desc_label.setWordWrap(True)
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        
        # معلومات إضافية
        meta_layout = QHBoxLayout()
        version_label = QLabel(f"الإصدار: {manifest.get('version', '1.0.0')}")
        author_label = QLabel(f"المطور: {manifest.get('author', 'غير معروف')}")
        meta_layout.addWidget(version_label)
        meta_layout.addWidget(author_label)
        info_layout.addLayout(meta_layout)
        
        layout.addLayout(info_layout, stretch=1)
        
        # أزرار التحكم
        controls_layout = QHBoxLayout()
        
        # زر المعلومات
        info_btn = QToolButton()
        info_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogInfoView))
        info_btn.clicked.connect(lambda: self.show_extension_details(ext_id))
        
        # زر الإعدادات
        settings_btn = QToolButton()
        settings_btn.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        settings_btn.clicked.connect(lambda: os.startfile(self.extensions_manager.extensions[ext_id]['path']))
        
        # زر التفعيل
        toggle_btn = QCheckBox("تفعيل")
        toggle_btn.setChecked(ext_id in self.extensions_manager.active_extensions)
        toggle_btn.stateChanged.connect(lambda state: self.on_extension_toggle(ext_id, state))
        self.checkboxes[ext_id] = toggle_btn
        
        controls_layout.addWidget(info_btn)
        controls_layout.addWidget(settings_btn)
        controls_layout.addWidget(toggle_btn)
        
        layout.addLayout(controls_layout)
        
        widget.setLayout(layout)
        return widget

    def filter_by_status(self, status):
        """تصفية الإضافات حسب الحالة"""
        for ext_id, widget in self.extension_widgets.items():
            if status == "الكل":
                widget.show()
            elif status == "نشط" and ext_id in self.extensions_manager.active_extensions:
                widget.show()
            elif status == "معطل" and ext_id not in self.extensions_manager.active_extensions:
                widget.show()
            else:
                widget.hide()

    def update_status(self):
        """تحديث شريط الحالة"""
        total = len(self.extensions_manager.extensions)
        active = len(self.extensions_manager.active_extensions)
        self.status_label.setText(
            f"الإضافات: {total} إجمالي, {active} نشط, {total - active} معطل"
        )

    def on_extension_toggle(self, ext_id, state):
        """معالجة تغيير حالة الإضافة"""
        try:
            if state == Qt.Checked:
                success = self.extensions_manager.activate_extension(ext_id)
                if not success:
                    self.checkboxes[ext_id].setChecked(False)
                    QMessageBox.warning(self, "خطأ", f"فشل تفعيل الإضافة {ext_id}")
                    return
            else:
                success = self.extensions_manager.deactivate_extension(ext_id)
                if not success:
                    self.checkboxes[ext_id].setChecked(True)
                    QMessageBox.warning(self, "خطأ", f"فشل تعطيل الإضافة {ext_id}")
                    return
            
            # تحديث واجهة المستخدم
            self.update_extension_status(ext_id)
            self.update_status()
            self.filter_extensions()  # تطبيق التصفية بعد تغيير الحالة
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تغيير حالة الإضافة: {str(e)}")
            # إعادة الحالة السابقة
            self.checkboxes[ext_id].setChecked(ext_id in self.extensions_manager.active_extensions)

    def update_extension_status(self, ext_id):
        """تحديث حالة الإضافة في واجهة المستخدم"""
        if ext_id in self.extension_widgets:
            widget = self.extension_widgets[ext_id]
            # البحث عن تسمية الحالة في الـ widget
            for child in widget.findChildren(QLabel):
                if '●' in child.text():  # علامة الحالة
                    if ext_id in self.extensions_manager.active_extensions:
                        child.setText('<span style="color: green;">● نشط</span>')
                    else:
                        child.setText('<span style="color: gray;"> معطل</span>')
                    break

    def filter_extensions(self):
        """تصفية الإضافات حسب الحالة"""
        filter_status = self.filter_combo.currentText()
        
        for ext_id, widget in self.extension_widgets.items():
            is_active = ext_id in self.extensions_manager.active_extensions
            
            if filter_status == "الكل":
                widget.setVisible(True)
            elif filter_status == "نشط":
                widget.setVisible(is_active)
            elif filter_status == "معطل":
                widget.setVisible(not is_active)

    def needs_update(self, ext_id):
        """التحقق مما إذا كانت الإضافة تحتاج إلى تحديث"""
        try:
            ext_data = self.extensions_manager.extensions[ext_id]
            current_version = ext_data['manifest'].get('version', '0.0.0')
            # هنا يمكن إضافة منطق للتحقق من الإصدار الأحدث
            # مثلاً من خلال الاتصال بمستودع الإضافات
            return False
        except:
            return False

    def update_memory_usage(self):
        """تحديث معلومات استخدام الذاكرة"""
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # تحويل إلى ميجابايت
            self.memory_label.setText(f"استخدام الذاكرة: {memory_usage:.1f} MB")
        except:
            self.memory_label.setText("استخدام الذاكرة: غير متاح")

    def check_for_updates(self):
        """التحقق من وجود تحديثات للإضافات"""
        updates_available = 0
        for ext_id, ext_data in self.extensions_manager.extensions.items():
            if self.needs_update(ext_id):
                updates_available += 1
        self.updates_label.setText(f"التحديثات: {updates_available} متاحة")

    def save_advanced_settings(self):
        """حفظ الإعدادات المتقدمة"""
        settings = {
            'auto_update': self.auto_update_checkbox.isChecked(),
            'update_interval': self.update_interval_combo.currentText(),
            'load_disabled': self.load_disabled_checkbox.isChecked(),
            'safe_mode': self.safe_mode_checkbox.isChecked()
        }
        
        try:
            settings_path = os.path.join(os.path.dirname(__file__), 'extension_settings.json')
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "نجاح", "تم حفظ الإعدادات بنجاح")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء حفظ الإعدادات: {str(e)}")

    def load_advanced_settings(self):
        """تحميل الإعدادات المتقدمة"""
        try:
            settings_path = os.path.join(os.path.dirname(__file__), 'extension_settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.auto_update_checkbox.setChecked(settings.get('auto_update', False))
                self.update_interval_combo.setCurrentText(settings.get('update_interval', 'يومياً'))
                self.load_disabled_checkbox.setChecked(settings.get('load_disabled', False))
                self.safe_mode_checkbox.setChecked(settings.get('safe_mode', False))
        except:
            pass

    def show_extension_settings(self, ext_id):
        """عرض إعدادات الإضافة"""
        extension = self.extensions_manager.active_extensions.get(ext_id)
        if extension and hasattr(extension, 'show_settings'):
            extension.show_settings()
    
    def show_extension_details(self, ext_id):
        """عرض تفاصيل الإضافة"""
        ext_data = self.extensions_manager.extensions[ext_id]
        manifest = ext_data['manifest']
        
        details = QDialog(self)
        details.setWindowTitle(f"تفاصيل الإضافة - {manifest.get('name', ext_id)}")
        layout = QVBoxLayout()
        
        text = QTextBrowser()
        text.setHtml(f"""
            <h2>{manifest.get('name', ext_id)}</h2>
            <p><b>الوصف:</b> {manifest.get('description', '')}</p>
            <p><b>الإصدار:</b> {manifest.get('version', '1.0.0')}</p>
            <p><b>المطور:</b> {manifest.get('author', 'غير معروف')}</p>
            <p><b>البريد الإلكتروني:</b> {manifest.get('email', '')}</p>
            <p><b>المتطلبات:</b></p>
            <ul>
                {''.join(f'<li>{req}</li>' for req in manifest.get('requirements', []))}
            </ul>
        """)
        
        layout.addWidget(text)
        
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(details.close)
        layout.addWidget(close_btn)
        
        details.setLayout(layout)
        details.exec_()
    
    def update_log(self):
        """تحديث سجل الأضافات"""
        try:
            log_path = "extensions.log"  # مسار الملف مباشرة في المجلد الرئيسي
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_content = f.readlines()
                    # عرض آخر 100 سطر فقط
                    log_content = log_content[-100:]
                    self.log_browser.setText(''.join(log_content))
                    # تحريك المؤشر إلى النهاية
                    scrollbar = self.log_browser.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
            else:
                self.log_browser.setText("لا يوجد ملف سجل")
        except Exception as e:
            self.log_browser.setText(f"خطأ في قراءة السجل: {str(e)}")
    

    
    def save_settings(self):
        """حفظ إعدادات الإضافات"""
        enabled = {}
        disabled = []
        
        for ext_id, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                enabled[ext_id] = True
            else:
                disabled.append(ext_id)
        
        try:
            self.extensions_manager.save_extension_settings(enabled, disabled)
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء حفظ الإعدادات: {str(e)}")

    def setup_stats_tab(self, tab):
        """إعداد تبويب الإحصائيات والسجل"""
        layout = QVBoxLayout()
        
        # إحصائيات عامة
        stats_group = QGroupBox("إحصائيات عامة")
        stats_layout = QGridLayout()
        
        # حساب الإحصائيات
        total_count = len(self.extensions_manager.extensions)
        active_count = len(self.extensions_manager.active_extensions)
        disabled_count = total_count - active_count
        
        # عرض الإحصائيات
        stats_layout.addWidget(QLabel("إجمالي الإضافات:"), 0, 0)
        stats_layout.addWidget(QLabel(str(total_count)), 0, 1)
        
        stats_layout.addWidget(QLabel("الإضافات النشطة:"), 1, 0)
        stats_layout.addWidget(QLabel(f"<span style='color: green;'>{active_count}</span>"), 1, 1)
        
        stats_layout.addWidget(QLabel("الإضافات المعطلة:"), 2, 0)
        stats_layout.addWidget(QLabel(f"<span style='color: gray;'>{disabled_count}</span>"), 2, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # سجل الأحداث
        log_group = QGroupBox("سجل الأحداث")
        log_layout = QVBoxLayout()
        
        # إنشاء مربع النص للسجل
        self.log_browser = QTextBrowser()
        self.log_browser.setReadOnly(True)
        self.log_browser.setMinimumHeight(200)
        
        # أزرار التحكم
        controls = QHBoxLayout()
        
        refresh_log_btn = QPushButton("تحديث")
        refresh_log_btn.clicked.connect(self.update_log)
        
        clear_log_btn = QPushButton("مسح")
        clear_log_btn.clicked.connect(self.clear_log)
        
        controls.addWidget(refresh_log_btn)
        controls.addWidget(clear_log_btn)
        controls.addStretch()
        
        log_layout.addWidget(self.log_browser)
        log_layout.addLayout(controls)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        tab.setLayout(layout)
        
        # تحديث السجل الأولي
        self.update_log()

    def clear_log(self):
        """مسح محتوى ملف السجل"""
        try:
            log_path = "extensions.log"
            # مسح محتوى الملف
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("")  # كتابة ملف فارغ
            
            # مسح محتوى العرض
            self.log_browser.clear()
            
            # إضافة رسالة تأكيد
            self.log_browser.setText("تم مسح السجل بنجاح")
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل مسح السجل: {str(e)}")

    def setup_create_extension_tab(self, tab):
        """إعداد تبويب إنشاء إضافة"""
        main_layout = QVBoxLayout()
        
        # مجموعة معلومات الإضافة
        info_group = QGroupBox("معلومات الإضافة")
        form = QFormLayout()
        
        # إنشاء عناصر الإدخال
        self.name_input = QLineEdit()
        self.id_input = QLineEdit()
        self.id_input.setReadOnly(True)
        self.version_input = QLineEdit("1.0.0")
        self.author_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        
        self.name_input.textChanged.connect(self.generate_unique_id)
        
        form.addRow("اسم الإضافة:", self.name_input)
        form.addRow("معرف الإضافة:", self.id_input)
        form.addRow("الإصدار:", self.version_input)
        form.addRow("المطور:", self.author_input)
        form.addRow("الوصف:", self.description_input)
        
        # نوع الإضافة
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "محلل نصوص",
            "أداة تحرير",
            "إضافة مخصصة"
        ])
        form.addRow("نوع الإضافة:", self.type_combo)
        
        info_group.setLayout(form)
        main_layout.addWidget(info_group)
        
        # مجموعة الأيقونة
        icon_group = QGroupBox("أيقونة الإضافة")
        icon_layout = QHBoxLayout()
        
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.set_default_icon()
        
        icon_buttons = QVBoxLayout()
        choose_icon_btn = QPushButton("اختيار أيقونة")
        choose_icon_btn.clicked.connect(self.choose_icon)
        reset_icon_btn = QPushButton("إعادة تعيين")
        reset_icon_btn.clicked.connect(self.set_default_icon)
        
        icon_buttons.addWidget(choose_icon_btn)
        icon_buttons.addWidget(reset_icon_btn)
        
        icon_layout.addWidget(self.icon_label)
        icon_layout.addLayout(icon_buttons)
        icon_group.setLayout(icon_layout)
        
        main_layout.addWidget(icon_group)
        
        # زر الإنشاء
        create_btn = QPushButton("إنشاء الإضافة")
        create_btn.clicked.connect(self.create_extension)
        main_layout.addWidget(create_btn)
        
        main_layout.addStretch()
        
        # تعيين التخطيط للتبويب
        tab.setLayout(main_layout)

    def generate_unique_id(self):
        """توليد معرف فريد من اسم الإضافة"""
        name = self.name_input.text().strip()
        if name:
            # تحويل الاسم إلى معرف صالح
            base_name = name.lower()
            base_name = ''.join(c if c.isalnum() else '_' for c in base_name)
            base_name = base_name.strip('_')
            
            # إنشاء UUID فريد
            unique_uuid = str(uuid.uuid4())[:20]
            
            # دمج UUID مع اسم الإضافة
            unique_id = f"{unique_uuid}-{base_name}"
            
            # التأكد من عدم وجود المعرف
            while unique_id in self.extensions_manager.extensions:
                unique_uuid = str(uuid.uuid4())[:20]
                unique_id = f"{unique_uuid}-{base_name}"
            
            self.id_input.setText(unique_id)

    def create_extension(self):
        """إنشاء الإضافة"""
        if not all([self.name_input.text(), self.id_input.text(), 
                   self.version_input.text()]):
            QMessageBox.warning(self, "خطأ", "يرجى ملء جميع الحقول المطلوبة")
            return

        try:
            # تحديد مسار الإضافة في مجلد الإضافات
            extensions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'extensions')
            os.makedirs(extensions_dir, exist_ok=True)
            ext_path = os.path.join(extensions_dir, self.id_input.text())

            if os.path.exists(ext_path):
                QMessageBox.warning(self, "خطأ", "يوجد إضافة بنفس المعرف")
                return

            os.makedirs(ext_path)

            # نسخ الأيقونة
            if hasattr(self, 'icon_path') and self.icon_path:
                icon_dest = os.path.join(ext_path, "icon.png")
                image = QImage(self.icon_path)
                image.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation).save(icon_dest)

            # إنشاء الملفات
            self.create_manifest(ext_path)
            self.create_main_file(ext_path)
            self.create_readme(ext_path)

            QMessageBox.information(self, "نجاح", "تم إنشاء الإضافة بنجاح!")
            self.refresh_extensions()
            
            # مسح الحقول
            self.name_input.clear()
            self.version_input.setText("1.0.0")
            self.author_input.clear()
            self.description_input.clear()
            self.set_default_icon()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إنشاء الإضافة:\n{str(e)}")

    def set_default_icon(self):
        """تعيين الأيقونة الافتراضية"""
        self.icon_label.setText("لا توجد أيقونة")
        self.icon_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #999;
                border-radius: 5px;
                color: #999;
            }
        """)
        self.icon_path = None

    def choose_icon(self):
        """اختيار أيقونة للإضافة"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر أيقونة",
            "",
            "الصور (*.png *.jpg *.jpeg *.ico);;كل الملفات (*.*)"
        )
        
        if file_path:
            try:
                pixmap = QPixmap(file_path)
                pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                self.icon_label.setPixmap(pixmap)
                self.icon_label.setStyleSheet("")
                self.icon_path = file_path
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"فشل تحميل الأيقونة: {str(e)}")

    def create_manifest(self, ext_path):
        """إنشاء ملف manifest.json"""
        manifest = {
            "name": self.name_input.text(),
            "id": self.id_input.text(),
            "version": self.version_input.text(),
            "author": self.author_input.text(),
            "description": self.description_input.toPlainText(),
            "type": self.type_combo.currentText(),
            "main": "main.py",
            "icon": "icon.png" if hasattr(self, 'icon_path') and self.icon_path else None
        }
        
        with open(os.path.join(ext_path, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=4)

    def create_main_file(self, ext_path):
        """إنشاء الملف الرئيسي للإضافة"""
        template = f'''"""
{self.name_input.text()}
{self.description_input.toPlainText()}

المطور: {self.author_input.text()}
الإصدار: {self.version_input.text()}
"""

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.name = "{self.name_input.text()}"
        
    def initialize(self):
        """تهيئة الإضافة"""
        pass
        
    def cleanup(self):
        """تنظيف الإضافة عند إيقافها"""
        pass
'''
        with open(os.path.join(ext_path, "main.py"), "w", encoding="utf-8") as f:
            f.write(template)

    def create_readme(self, ext_path):
        """إنشاء ملف README.md"""
        template = f'''# {self.name_input.text()}

{self.description_input.toPlainText()}

## معلومات الإضافة
- الإصدار: {self.version_input.text()}
- المطور: {self.author_input.text()}
- النوع: {self.type_combo.currentText()}

## المتطلبات
- Python 3.6+
- PyQt5

## التثبيت
1. انسخ مجلد الإضافة إلى مجلد الإضافات
2. أعد تشغيل البرنامج
3. فعّل الإضافة من مدير الإضافات

## الاستخدام
[اكتب هنا تعليمات استخدام الإضافة]

## الترخيص
[اكتب هنا معلومات الترخيص]
'''
        with open(os.path.join(ext_path, "README.md"), "w", encoding="utf-8") as f:
            f.write(template)


    def refresh_extensions(self):
        """تحديث قائمة الإضافات"""
        # تحديث قائمة الإضافات المك��شفة
        self.extensions_manager.discover_extensions()  # تصحيح اسم الدالة
        
        # إعادة إنشاء محتوى التبويب الحالي
        current_tab = self.tab_widget.currentWidget()
        current_index = self.tab_widget.currentIndex()
        
        # إنشاء تبويب جديد
        new_tab = QWidget()
        
        # إعادة إنشاء محتوى التبويب حسب نوعه
        if current_index == 0:  # الإضافات المثبتة
            self.setup_installed_tab(new_tab)
        elif current_index == 1:  # متجر الإضافات
            self.setup_store_tab(new_tab)
        elif current_index == 2:  # الإحصائيات
            self.setup_stats_tab(new_tab)
        elif current_index == 3:  # الإعدادات المتقدمة
            self.setup_advanced_tab(new_tab)
        elif current_index == 4:  # إنشاء إضافة
            self.setup_create_extension_tab(new_tab)
        
        # استبدال التبويب القديم بالجديد
        self.tab_widget.removeTab(current_index)
        self.tab_widget.insertTab(current_index, new_tab, self.tab_widget.tabText(current_index))
        self.tab_widget.setCurrentIndex(current_index)
class ExtensionsManager:
    def __init__(self, editor):
        self.editor = editor
        self.extensions = {}  # جميع الإضافات المتوفرة
        self.active_extensions = {}  # الإضافات النشطة فقط
        self.disabled_extensions = []
        self.extensions_menu = None
        self.extensions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'extensions')
        
        # إنشاء مجلد الإضافات إذا لم يكن موجوداً
        if not os.path.exists(self.extensions_dir):
            os.makedirs(self.extensions_dir)
            
        # إعداد التسجيل
        logging.basicConfig(filename='extensions.log', level=logging.INFO)
        self.logger = logging.getLogger('ExtensionsManager')
        
        self.load_extension_settings()
        self.discover_extensions()  # اكتشاف جميع الإضافات المتوفرة
        self.load_active_extensions()  # تحميل الإضافات النشطة فقط
        self.setup_menu()

    def discover_extensions(self):
        """اكتشاف جميع الإضافات المتوفرة وقراءة معلوماتها"""
        self.extensions.clear()
        for ext_folder in os.listdir(self.extensions_dir):
            ext_path = os.path.join(self.extensions_dir, ext_folder)
            
            if not os.path.isdir(ext_path):
                continue
                
            manifest_path = os.path.join(ext_path, 'manifest.json')
            if not os.path.exists(manifest_path):
                continue
                
            try:
                # قرءة ملف التعريف
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                self.extensions[ext_folder] = {
                    'manifest': manifest,
                    'path': ext_path,
                    'instance': None
                }
                
            except Exception as e:
                self.logger.error(f"خطأ في قراءة معلومات الإضافة {ext_folder}: {str(e)}")

    def load_active_extensions(self):
        """تحميل الإضافات النشطة فقط"""
        self.active_extensions.clear()
        for ext_id, ext_data in self.extensions.items():
            if ext_id not in self.disabled_extensions:
                try:
                    main_module = os.path.join(ext_data['path'], ext_data['manifest'].get('main', 'main.py'))
                    if os.path.exists(main_module):
                        spec = importlib.util.spec_from_file_location(ext_id, main_module)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # إنشاء نسخة من الإضافة
                        extension = module.Extension(self.editor)
                        ext_data['instance'] = extension
                        self.active_extensions[ext_id] = extension
                        
                        self.logger.info(f"تم تحميل الإضافة: {ext_data['manifest'].get('name', ext_id)}")
                
                except Exception as e:
                    self.logger.error(f"خطأ في تحميل الإضافة {ext_id}: {str(e)}")

    def setup_menu(self):
        """إعداد قائمة الإضافات"""
        if not hasattr(self.editor, 'menuBar'):
            return
            
        # إزالة القائمة القديمة إذا كانت موجودة
        if self.extensions_menu:
            self.editor.menuBar().removeAction(self.extensions_menu.menuAction())
        
        # إنشاء قائمة جديدة
        self.extensions_menu = self.editor.menuBar().addMenu('إضافات')
        
        # إضافة زر مدير الإضافات
        manage_action = QAction('مدير الإضافات', self.editor)
        manage_action.triggered.connect(self.show_extension_manager)
        self.extensions_menu.addAction(manage_action)
        self.extensions_menu.addSeparator()
        
        # إضافة الإضافات النشطة للقائمة
        for ext_id, extension in self.active_extensions.items():
            if ext_id in self.extensions:
                manifest = self.extensions[ext_id]['manifest']
                if hasattr(extension, 'get_menu_items'):
                    menu_items = extension.get_menu_items()
                    if menu_items:
                        ext_menu = QMenu(manifest.get('name', ext_id), self.editor)
                        for item in menu_items:
                            action = QAction(item['name'], self.editor)
                            action.triggered.connect(item['callback'])
                            ext_menu.addAction(action)
                        self.extensions_menu.addMenu(ext_menu)

    def reload_extensions(self):
        """إعادة تحميل الإضافات"""
        # إيقاف جمع الإضافات النشطة
        for ext_id in list(self.active_extensions.keys()):
            self.deactivate_extension(ext_id)
        
        # إعادة اتشاف وتحميل الإضافات
        self.discover_extensions()
        self.load_active_extensions()
        self.setup_menu()

    def load_extension_settings(self):
        """تحميل إعدادات الإضافات من ملف الإعدادات"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    extensions_settings = settings.get('extensions', {})
                    self.disabled_extensions = extensions_settings.get('disabled', [])
            else:
                # إنشاء ملف الإعدادات إذا لم يكن موجوداً
                default_settings = {
                    "extensions": {
                        "enabled": {},
                        "disabled": []
                    }
                }
                os.makedirs(os.path.dirname(settings_path), exist_ok=True)
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(default_settings, f, indent=4)
                self.disabled_extensions = []
                
        except Exception as e:
            self.logger.error(f"خطأ في تحميل إعدادات الإضافات: {str(e)}")
            self.disabled_extensions = []

    def show_extension_manager(self):
        """عرض نافذة مدير الإضافات"""
        dialog = ExtensionManagerDialog(self)
        dialog.exec_()

    def save_extension_settings(self, enabled, disabled):
        """حفظ إعدادات الإضافات وتطبيقها مباشرة"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
            
            # قراءة الإعدادات الحالية
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            # تحديث إعدادات الإضافات
            settings['extensions'] = {
                'enabled': enabled,
                'disabled': disabled
            }
            
            # إيقاف الإضافات المعطلة
            for ext_id in disabled:
                if ext_id in self.active_extensions:
                    self.deactivate_extension(ext_id)
            
            # تفعيل الإضافات المفعلة
            for ext_id in enabled:
                if ext_id not in self.active_extensions and ext_id in self.extensions:
                    self.activate_extension(ext_id)
            
            # حفظ الإعدادات في الملف
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            self.disabled_extensions = disabled
            
            # إعادة بناء القائمة
            self.setup_menu()
            
            self.logger.info("تم حفظ وتطبيق إعدادات الإضافات بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في حفظ إعدادات الإضافات: {str(e)}")
            raise

    def deactivate_extension(self, ext_id):
        """إيقاف تشغيل إضافة محددة بشكل كامل"""
        if ext_id in self.active_extensions:
            try:
                extension = self.active_extensions[ext_id]
                
                # 1. استدعاء دالة التنظيف في الإضافة
                if hasattr(extension, 'cleanup'):
                    extension.cleanup()
                
                # 2. إزالة أي عناصر واجهة مستخدم أضافتها الإضافة
                if hasattr(extension, 'remove_ui_elements'):
                    extension.remove_ui_elements()
                
                # 3. إيقاف أي مؤقتات أو عمليات خلفية
                if hasattr(extension, 'stop_background_tasks'):
                    extension.stop_background_tasks()
                
                # 4. فصل أي إشارات (signals) مرتبطة
                if hasattr(extension, 'disconnect_signals'):
                    extension.disconnect_signals()
                
                # 5. إزالة الإضافة من الذاكرة
                del self.active_extensions[ext_id]
                if ext_id in self.extensions:
                    self.extensions[ext_id]['instance'] = None
                
                # 6. إزالة الموديول من sys.modules لضمان إعادة تحميله بشكل نظيف
                module_name = f"extensions.{ext_id}.main"
                if module_name in sys.modules:
                    del sys.modules[module_name]
                
                # 7. تحديث القائمة
                self.setup_menu()
                
                self.logger.info(f"تم إيقاف الإضافة بشكل كامل: {ext_id}")
                return True
            except Exception as e:
                self.logger.error(f"خطأ في إيقاف الإضافة {ext_id}: {str(e)}")
        return False

    def activate_extension(self, ext_id):
        """تفعيل إضافة محددة"""
        if ext_id in self.extensions and ext_id not in self.active_extensions:
            try:
                # 1. تحميل الإضافة
                ext_data = self.extensions[ext_id]
                main_module = os.path.join(ext_data['path'], ext_data['manifest'].get('main', 'main.py'))
                
                if os.path.exists(main_module):
                    # 2. تحميل نظيف للموديول
                    module_name = f"extensions.{ext_id}.main"
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                    
                    spec = importlib.util.spec_from_file_location(module_name, main_module)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    # 3. إنشاء نسخة جديدة من الإضافة
                    extension = module.Extension(self.editor)
                    
                    # 4. تهيئة الإضافة
                    if hasattr(extension, 'initialize'):
                        extension.initialize()
                    
                    ext_data['instance'] = extension
                    self.active_extensions[ext_id] = extension
                    
                    # 5. تحديث القائمة
                    self.setup_menu()
                    
                    self.logger.info(f"تم تفعيل الإضافة: {ext_id}")
                    return True
                
            except Exception as e:
                self.logger.error(f"خطأ في تفعيل الإضافة {ext_id}: {str(e)}")
                # إظهار رسالة الخطأ للمستخدم
                QMessageBox.warning(None, "خطأ", f"فشل تفعيل الإضافة {ext_id}:\n{str(e)}")
        return False
