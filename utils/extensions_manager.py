import shutil
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QWidget, QPushButton, QCheckBox,
                           QTabWidget, QTextBrowser, QGroupBox, QGridLayout,
                           QLineEdit, QMenu, QAction, QMessageBox,QApplication,
                            QToolButton, QComboBox,
                           QMainWindow, QProgressDialog, QTimeEdit, QFileDialog,QFrame )
from PyQt5.QtCore import Qt, QTimer,QTime
from PyQt5.QtGui import  QPixmap,  QIcon
import os
import json
import logging
import importlib.util
import sys
from .extension_store import ExtensionStore
import requests
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
import base64
from datetime import datetime, timedelta
import semver
from PyQt5.QtCore import QSettings
import zipfile
from .arabic_logger import setup_arabic_logging
import asyncio
import aiohttp
import subprocess
import pkg_resources

setup_arabic_logging()

class ExtensionManagerDialog(QMainWindow):
    _instance = None  # متغير ثابت لحفظ النسخة الوحيدة
    
    @classmethod
    def get_instance(cls, extensions_manager):
        """الحصول على نسخة وحيدة من النافذة"""
        if cls._instance is None:
            cls._instance = cls(extensions_manager)
        return cls._instance

    def __init__(self, extensions_manager):
        super().__init__()
        # تعيين النافذة كمستقلة
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose, False)  # منع حذف النافذة عند الإغلاق
        self.extensions_manager = extensions_manager
        self.checkboxes = {}
        self.extension_widgets = {}
        self.store = ExtensionStore()
        
        # إعداد النافذة
        self.setWindowTitle("مدير الإضافات")
        self.setMinimumSize(900, 700)
        try:
            self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icons', 'extensions.png')))
        except Exception as e:
            pass  # تجاهل أي خطأ في تحميل الأيقونة
        
        # إضافة متغيرات للتتبع
        self.current_filter = "الكل"
        self.search_text = ""
        self.sort_order = "name_asc"
        
        self.setup_style()
        self.setup_ui()
        
        # تحديث تلقائي
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.update_log)
        self.log_timer.start(5000)
        
        # حفظ حالة النافذة
        self.settings = QSettings('Qirtas', 'ExtensionManager')
        self.restore_window_state()
        

    def setup_style(self):
        """إعداد نمط النافذة"""
        try:
            style_path = os.path.join('resources', 'styles', 'extension_manager.qss')
            if os.path.exists(style_path):
                with open(style_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
                    self.extensions_manager.log_message(f"تم تحميل ملف التنسيق: {style_path}")
            else:
                self.extensions_manager.log_message(f"ملف التنسيق غير موجود: {style_path}", "WARNING")
        except Exception as e:
            self.extensions_manager.log_message(f"خطأ في تحميل ملف التنسيق: {str(e)}", "ERROR")

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # إنشاء widget مركزي
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # إنشاء status_label أولاً
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                color: #155724;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                padding: 5px;
                border-radius: 4px;
            }
        """)
        self.update_status()  # تحديث حالة النص
        
        # إضافة status_label في الأعلى
        layout.addWidget(self.status_label)
        
        # إنشاء مجموعة التبويب
        self.tab_widget = QTabWidget()
        
        # تبويب الإضافات المثبتة
        installed_tab = QWidget()
        self.setup_installed_tab(installed_tab)
        self.tab_widget.addTab(installed_tab, "الإضافات المثبتة")
        
        # تبويب متجر الإضافات
        store_tab = QWidget()
        self.setup_store_tab(store_tab)
        self.tab_widget.addTab(store_tab, "متجر الإضافات")
        
        # تبويب الإحصائيات والسجل
        stats_tab = QWidget()
        self.setup_stats_tab(stats_tab)
        self.tab_widget.addTab(stats_tab, "الإحصائيات والسجل")
        
        #تبويب الاعدادات المتقدمة
        advanced_tab = QWidget()
        self.setup_advanced_tab(advanced_tab)
        self.tab_widget.addTab(advanced_tab, "الاعدادات المتقدمة")
        
        #تبويب إنشاء إضافة جد��دة
        create_tab = QWidget()
        self.setup_create_extension_tab(create_tab)
        self.tab_widget.addTab(create_tab, "إنشاء إضافة")
        
        layout.addWidget(self.tab_widget)
        
        # أزرار التحكم
        buttons = QHBoxLayout()
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.close)
        buttons.addStretch()
        buttons.addWidget(close_btn)
        
        layout.addLayout(buttons)
        
        # تعيين الـ widget المركزي
        self.setCentralWidget(central_widget)

    def setup_create_extension_tab(self, tab):
        """إعداد تبويب إنشاء إضافة"""
        from .extension_creator import ExtensionCreator
        creator = ExtensionCreator(self)
        layout = QVBoxLayout()
        layout.addWidget(creator)
        tab.setLayout(layout)

    def show_extension_creator(self):
        """عرض نافذة إ��شاء إضافة جديدة"""
        from .extension_creator import ExtensionCreator
        creator = ExtensionCreator(self)
        if creator.exec_() == QDialog.Accepted:
            self.refresh_extensions()  # تحديث قائمة الإضافات بعد الإنشاء

    def setup_store_tab(self, tab):
        """إعداد تبويب متجر الإضافات"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # شريط البحث والتحديث
        top_layout = QHBoxLayout()
        
        # زر التحديث
        refresh_btn = QPushButton("تحديث")
        try:
            refresh_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icons', 'refresh.png')))
        except Exception as e:
            pass  # تجاهل أي خطأ في تحميل الأيقونة
        refresh_btn.clicked.connect(self.load_store_extensions)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #054229;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #065435;
            }
        """)
        top_layout.addWidget(refresh_btn)
        
        # حقل البحث
        store_search = QLineEdit()
        store_search.setPlaceholderText("ابحث عن إضافات جديدة...")
        store_search.setStyleSheet("""
            QLineEdit {
                background-color: #212121;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
               }
            QLineEdit:focus {
                border: 1px solid #054229;
            }
        """)
        top_layout.addWidget(store_search)
        layout.addLayout(top_layout)
        
        # منطقة التمرير للإضافات
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1a1a1a;
                border: none;
                border-radius: 8px;
            }
        """)
        
        # حاوية الإضافات
        self.store_widget = QWidget()
        self.store_layout = QVBoxLayout()
        self.store_layout.setSpacing(10)
        self.store_layout.setAlignment(Qt.AlignTop)
        self.store_widget.setLayout(self.store_layout)
        
        scroll.setWidget(self.store_widget)
        layout.addWidget(scroll)
        
        tab.setLayout(layout)
        
        # تحميل الإضافات عند فتح التبويب
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """معالجة تغيير التبويب"""
        if self.tab_widget.tabText(index) == "متجر الإضافات":
            self.load_store_extensions()
    def show_extension_creator(self):
        """الانتقال إلى تبويب إنشاء إضافة جديدة"""
        # البحث عن تبويب إنشاء إضافة
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "إنشاء إضافة":
                # تغيير التبويب الحالي
                self.tab_widget.setCurrentIndex(i)
                break
    def load_store_extensions(self):
        """تحميل وعرض الإضافات المتوفرة في المتجر"""
        # مسح العناصر السابقة
        for i in reversed(range(self.store_layout.count())):
            widget = self.store_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # إضافة مؤشر التحميل
        loading_label = QLabel("جاري تحميل الإضافات...")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("""
            QLabel {
                color: #888888;
                padding: 20px;
                font-size: 14px;
            }
        """)
        self.store_layout.addWidget(loading_label)
        QApplication.processEvents()
        
        try:
            # جلب الإضافات
            extensions = self.store.get_available_extensions(force_refresh=True)
            
            # إزالة مؤشر التحميل
            loading_label.setParent(None)
            
            if extensions:
                # تجميع الإضافات حسب الإصدار
                version_groups = {}
                for ext in extensions:
                    version = ext.get('version', 'غير محدد')
                    if version not in version_groups:
                        version_groups[version] = []
                    version_groups[version].append(ext)
                
                # إنشاء مجموعات للإصدارات
                for version, exts in sorted(version_groups.items(), reverse=True):
                    # إنشاء عنوان للإصدار
                    version_label = QLabel(f"الإصدار {version}")
                    version_label.setStyleSheet("""
                        QLabel {
                            color: #ffffff;
                            background-color: #054229;
                            padding: 10px;
                            border-radius: 4px;
                            font-weight: bold;
                            margin-top: 15px;
                        }
                    """)
                    self.store_layout.addWidget(version_label)
                    
                    # إضافة الإضافات لهذا الإصدار
                    for ext in exts:
                        ext_widget = self.create_store_extension_widget(ext)
                        self.store_layout.addWidget(ext_widget)
                    
                    # إضافة خط فاصل
                    line = QFrame()
                    line.setFrameShape(QFrame.HLine)
                    line.setStyleSheet("background-color: #333333;")
                    self.store_layout.addWidget(line)
            else:
                # إنشاء رسالة عدم وجود إضافات مع تصميم جذاب
                no_ext_widget = QWidget()
                no_ext_layout = QVBoxLayout()
                
                # أيقونة
                icon_label = QLabel()
                icon_label.setPixmap(QIcon(os.path.join('resources', 'icons', 'store.png')).pixmap(64, 64))
                icon_label.setAlignment(Qt.AlignCenter)
                no_ext_layout.addWidget(icon_label)
                
                # رسالة رئيسية
                msg_label = QLabel("لا توجد إضافات متاحة حالياً لهذا الإصدار")
                msg_label.setAlignment(Qt.AlignCenter)
                msg_label.setStyleSheet("""
                    QLabel {
                        color: #888888;
                        font-size: 16px;
                        font-weight: bold;
                        margin: 10px;
                    }
                """)
                no_ext_layout.addWidget(msg_label)
                
                # رسالة فرعية
                sub_msg = QLabel("يمكنك إنشاء إضافة جديدة أو الانتظار حتى تتوفر إضافات جديدة")
                sub_msg.setAlignment(Qt.AlignCenter)
                sub_msg.setWordWrap(True)
                sub_msg.setStyleSheet("""
                    QLabel {
                        color: #666666;
                        font-size: 14px;
                    }
                """)
                no_ext_layout.addWidget(sub_msg)
                
                # زر إنشاء إضافة جديدة
                create_btn = QPushButton("إنشاء إضافة جديدة")
                create_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #054229;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 4px;
                        margin-top: 15px;
                    }
                    QPushButton:hover {
                        background-color: #065435;
                    }
                """)
                create_btn.clicked.connect(self.show_extension_creator)
                no_ext_layout.addWidget(create_btn)
                
                no_ext_widget.setLayout(no_ext_layout)
                self.store_layout.addWidget(no_ext_widget)
        
        except Exception as e:
            # إزالة مؤشر التحميل
            loading_label.setParent(None)
            
            # إظهار رسالة الخطأ
            error_widget = QWidget()
            error_layout = QVBoxLayout()
            
            error_icon = QLabel()
            error_icon.setPixmap(QIcon(os.path.join('resources', 'icons', 'error.png')).pixmap(48, 48))
            error_icon.setAlignment(Qt.AlignCenter)
            error_layout.addWidget(error_icon)
            
            error_msg = QLabel(f"حدث خطأ أثناء تحميل الإضافات:\n{str(e)}")
            error_msg.setAlignment(Qt.AlignCenter)
            error_msg.setStyleSheet("""
                QLabel {
                    color: #ff4444;
                    padding: 20px;
                    font-size: 14px;
                }
            """)
            error_layout.addWidget(error_msg)
            
            retry_btn = QPushButton("إعادة المحاو��ة")
            retry_btn.clicked.connect(self.load_store_extensions)
            retry_btn.setStyleSheet("""
                QPushButton {
                    background-color: #054229;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #065435;
                }
            """)
            error_layout.addWidget(retry_btn)
            
            error_widget.setLayout(error_layout)
            self.store_layout.addWidget(error_widget)

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
        
        # إضافة مجموعة النسخ الاحتياطي
        backup_group = QGroupBox("النسخ الاحتياطي والاستعادة")
        backup_layout = QVBoxLayout()
        
        # أزرار النسخ الاحتياطي والاستعادة
        backup_btn = QPushButton("إنشاء نسخة احتياطية")
        backup_btn.clicked.connect(self.create_backup)
        
        restore_btn = QPushButton("استعادة من نسخة احتياطية")
        restore_btn.clicked.connect(self.restore_from_backup)
        
        backup_layout.addWidget(backup_btn)
        backup_layout.addWidget(restore_btn)
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # مجموعة التحديث التلقائي
        auto_update_group = QGroupBox("إعدادات التحديث التلقائي")
        auto_update_layout = QVBoxLayout()
        
        # خيار تفعيل التحديث التلقائي
        self.auto_update_checkbox = QCheckBox("تفعيل التحديث التلقائي")
        auto_update_layout.addWidget(self.auto_update_checkbox)
        
        # فترة التحديث
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("فترة التحديث:"))
        self.update_interval_combo = QComboBox()
        self.update_interval_combo.addItems(["كل ساعة", "يومياً", "أسبوعياً", "شهرياً"])
        interval_layout.addWidget(self.update_interval_combo)
        interval_layout.addStretch()
        auto_update_layout.addLayout(interval_layout)
        
        # وقت التحديث
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("وقت التحديث:"))
        self.update_time_edit = QTimeEdit()
        self.update_time_edit.setDisplayFormat("hh:mm")
        time_layout.addWidget(self.update_time_edit)
        time_layout.addStretch()
        auto_update_layout.addLayout(time_layout)
        
        auto_update_group.setLayout(auto_update_layout)
        layout.addWidget(auto_update_group)
        
        # إ��دادات أخرى...
        settings_group = QGroupBox("إعدادات عامة")
        settings_layout = QVBoxLayout()
        

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # إعدادات جيت هاب
        github_group = QGroupBox("إعدادات جيت هاب")
        github_layout = QVBoxLayout()
        
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("رمز جيت هاب :"))
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        token_layout.addWidget(self.token_input)
        
        # زر اختبار الرمز
        test_token_btn = QPushButton("اختبار الرمز")
        test_token_btn.clicked.connect(self.test_github_token)
        token_layout.addWidget(test_token_btn)
        
        github_layout.addLayout(token_layout)
        github_group.setLayout(github_layout)
        layout.addWidget(github_group)
        
        # أزرار التحكم
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("حفظ الإعدادات")
        save_btn.clicked.connect(self.save_advanced_settings)
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        tab.setLayout(layout)
        
        # تحميل الإعدادات المحفوظة
        self.load_advanced_settings()

    def test_github_token(self):
        """اختبار رمز جيت هاب"""
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال الرمز أولاً")
            return
        
        # إنشاء ن��فذة تقدم العملية
        progress = QProgressDialog("جاري اختبار الرمز...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            # اختبار الرمز باستخدا�� جيت هاب API
            headers = {'Authorization': f'token {token}'}
            response = requests.get('https://api.github.com/rate_limit', headers=headers)
            
            if response.status_code == 200:
                rate_data = response.json()['rate']
                remaining = rate_data['remaining']
                limit = rate_data['limit']
                reset_time = datetime.fromtimestamp(rate_data['reset']).strftime('%H:%M:%S')
                
                # إنشاء رسالة مفصلة
                message = (
                    "✅ تم التحقق من الرمز بنجاح\n\n"
                    f"📊 الطلبات المتبقية: {remaining}/{limit}\n"
                    f"🕒 يتم إعادة تعيين الحد في: {reset_time}"
                )
                
                # تحديد لون الرسالة بناءً على عدد الطلبات المتبقية
                if remaining < 100:
                    message = f"⚠️ {message}\n\n⚠️ تحذير: عدد الطلبات المتبقية منخفض!"
                
                QMessageBox.information(self, "نتيجة اختبار الرمز", message)
            else:
                error_msg = response.json().get('message', 'خطأ غير معروف')
                QMessageBox.warning(
                    self, 
                    "خطأ", 
                    f"❌ فشل التحقق من الرمز:\n{error_msg}"
                )
        
        except Exception as e:
            QMessageBox.critical(
                self, 
                "خطأ", 
                f"❌ حدث خطأ أثناء اختبار الرمز:\n{str(e)}"
            )
        
        finally:
            progress.close()

    def save_advanced_settings(self):
        """حفظ الإعدادات المتقدمة"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
            
            # قراءة الإعدادات الحالية
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
                
            # إنشاء قسم الإضافات إذا لم يكن موجوداً
            if 'extensions' not in settings:
                settings['extensions'] = {}
                
            # تحديث الإعدادات
            settings['extensions'].update({
                'auto_update': self.auto_update_checkbox.isChecked(),
                'update_interval': self.update_interval_combo.currentText(),
                'update_time': self.update_time_edit.time().toString("hh:mm"),
                'github_token': self.token_input.text().strip()
            })
            
            # حفظ الإعدادات في الملف
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
                
            QMessageBox.information(self, "نجاح", "تم حفظ الإعدادات بنجاح")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ الإعدادات: {str(e)}")

    def load_advanced_settings(self):
        """تحميل الإعدادات المتقدمة"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                extensions_settings = settings.get('extensions', {})
                
                # تحميل الإعدادات العامة
                self.auto_update_checkbox.setChecked(extensions_settings.get('auto_update', False))
                self.update_interval_combo.setCurrentText(extensions_settings.get('update_interval', 'يومياً'))
                self.update_time_edit.setTime(QTime.fromString(extensions_settings.get('update_time', '00:00'), "hh:mm"))
                
                # تحميل الرمز
                github_token = settings.get('github_token') or extensions_settings.get('github_token', '')
                self.token_input.setText(github_token)
                
                # تحميل حالة الإضافات
                enabled_dict = extensions_settings.get('enabled', {})
                for ext_id, is_enabled in enabled_dict.items():
                    if not is_enabled and ext_id in self.extensions_manager.active_extensions:
                        self.extensions_manager.deactivate_extension(ext_id)
                    elif is_enabled and ext_id not in self.extensions_manager.active_extensions:
                        self.extensions_manager.activate_extension(ext_id)
                
                    
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل الإعدادات: {str(e)}")

    def setup_auto_update_timer(self, settings):
        """إعداد مؤقت التحديث التلقائي"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        if settings.get('auto_update', False):
            self.update_timer = QTimer(self)
            self.update_timer.timeout.connect(self.check_for_updates)
            
            # تحديد الفترة بالمللي ثانية
            interval_map = {
                'كل ساعة': 3600000,  # ساعة
                'يومياً': 86400000,   # يوم
                'أسبوعياً': 604800000,  # أسبوع
                'شهرياً': 2592000000  # شهر (30 يوم)
            }
            
            interval = interval_map.get(settings.get('update_interval', 'يومياً'), 86400000)
            self.update_timer.start(interval)

    def create_enhanced_status_bar(self):
        """إنشاء شريط الة محسن"""
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
        failed_extensions = []
        
        for ext_id in list(self.extensions_manager.active_extensions):
            try:
                if self.extensions_manager.deactivate_extension(ext_id):
                    success_count += 1
                    if ext_id in self.checkboxes:
                        self.checkboxes[ext_id].setChecked(False)
                    self.update_extension_status(ext_id)
            except:
                # تجميع أسماء الإضافات التي فشل تعطيلها فقط
                pass        
        self.update_status()
        self.filter_extensions()

        # عرض رسالة واحدة مبسطة
        if failed_extensions:
            QMessageBox.warning(
                self,
                "تحذير",
                f"تم تعطيل {success_count} إضافة بنجاح\n"
                f"تعذر تعطيل الإضافات التالية:\n• " + "\n�� ".join(failed_extensions)
            )
        else:
            QMessageBox.information(
                self,
                "تم",
                f"تم تعطيل {success_count} إضافة بنجاح"
            )

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
        # إزالة التخطيط القديم إذا وجد
        if tab.layout():
            QWidget().setLayout(tab.layout())
        
        layout = QVBoxLayout()
        
        # شريط الأدوات ��لعلوي
        toolbar = QHBoxLayout()
        
        # تصفية ��سب الحالة
        filter_label = QLabel("عرض:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["الكل", "نشط", "معطل"])
        self.filter_combo.currentTextChanged.connect(self.filter_extensions)
        
        # أزرار الإجراءات
        refresh_btn = QPushButton()
        try:
            refresh_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icons', 'refresh.png')))
        except Exception as e:
            pass  # تجاهل أي خطأ في تحميل الأيقونة
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
        
        # تعيين التخطيط الجديد
        tab.setLayout(layout)

    def create_extension_widget(self, ext_id, ext_data):
        """إنشاء واجهة الإضافة"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # معلومات اإضافة
        manifest = ext_data['manifest']
        
        # أيقونة الإضافة
        icon_label = QLabel()
        try:
            icon_path = os.path.join(ext_data['path'], 'icon.png')
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pixmap)
            else:
                default_icon = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icons', 'extension.png')).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(default_icon)
        except Exception as e:
            pass  # تجاهل أي خطأ في تحميل الأيقونة
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
        try:
            info_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icons', 'info.png')))
        except Exception as e:
            pass  # تجاهل أي خطأ في تحميل الأيقونة
        info_btn.clicked.connect(lambda: self.show_extension_details(ext_id))
        
        # زر الإعدادات
        settings_btn = QToolButton()
        try:
            settings_btn.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'icons', 'folder.png')))
        except Exception as e:
            pass  # تجاهل أي خطأ في تحميل الأيقونة
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

    def update_status(self, message="", is_error=False):
        """تحديث حالة النافذة"""
        if not message:
            # سالة افتراضية إذا لم يتم تمرير رسالة
            active_count = len(self.extensions_manager.active_extensions)
            total_count = len(self.extensions_manager.extensions)
            message = f"الإضافات النشطة: {active_count}/{total_count}"
        
        self.status_label.setText(message)
        if is_error:
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #721c24;
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    padding: 5px;
                    border-radius: 4px;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #155724;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    padding: 5px;
                    border-radius: 4px;
                }
            """)

    def on_extension_toggle(self, ext_id, state):
        """معالجة تغيير حالة الإضافة"""
        try:
            if ext_id not in self.checkboxes:
                return
            
            checkbox = self.checkboxes[ext_id]
            if not checkbox or checkbox.parent() is None:
                del self.checkboxes[ext_id]
                return
            
            if state == Qt.Checked:
                # التحقق من المتطلبات قبل التفعيل
                ext_data = self.extensions_manager.extensions.get(ext_id)
                if ext_data and 'manifest' in ext_data:
                    requirements = ext_data['manifest'].get('requirements', [])
                    if requirements:
                        # سؤال المستخدم عن تثبيت المتطلبات
                        reply = QMessageBox.question(
                            self,
                            "تثبيت المتطلبات",
                            f"تحتاج هذه الإضافة إلى المكتبات التالية:\n- " + "\n- ".join(requirements) + "\n\nهل تريد تثبيتها الآن؟",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        
                        if reply == QMessageBox.Yes:
                            if not self.install_required_packages(requirements):
                                checkbox.setChecked(False)
                                return
                        else:
                            checkbox.setChecked(False)
                            return
                
                # محاولة تفعيل الإضافة
                success = self.extensions_manager.activate_extension(ext_id)
                if not success:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
                    QMessageBox.warning(self, "خطأ", f"فشل تفعيل الإضافة {ext_id}")
                    return
            else:
                success = self.extensions_manager.deactivate_extension(ext_id)
                if not success:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(True)
                    checkbox.blockSignals(False)
                    QMessageBox.warning(self, "خطأ", f"فشل تعطيل الإضافة {ext_id}")
                    return
            
            self.update_extension_status(ext_id)
            self.update_status()
            self.filter_extensions()
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تغيير حالة الإضافة: {str(e)}")
            if ext_id in self.checkboxes and self.checkboxes[ext_id].parent() is not None:
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
            
            # التحقق من الإصدار الأحدث في المتجر
            store_url = f"{self.store.base_url}/contents/store/extensions/{ext_id}/manifest.json"
            response = requests.get(store_url, headers=self.store.headers)
            
            if response.status_code == 200:
                content = base64.b64decode(response.json()['content']).decode('utf-8')
                store_manifest = json.loads(content)
                store_version = store_manifest.get('version', '0.0.0')
                
                # مقارنة الإصدارات باستخدام semver
                try:
                    current_ver = semver.VersionInfo.parse(current_version)
                    store_ver = semver.VersionInfo.parse(store_version)
                    return store_ver > current_ver
                except ValueError:
                    self.logger.error(f"صيغة إصدار غير صالحة للإضافة {ext_id}")
                    return False
                
            return False
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من تحديثات الإضافة {ext_id}: {str(e)}")
            return False

    def update_memory_usage(self):
        """تحديث معلومات استخدام الذاكرة"""
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # تحويل إلى ميجابايت
            self.memory_label.setText(f"استخدام الذاكرة: {memory_usage:.1f} MB")
        except:
            self.memory_label.setText("ستخدام الذاكرة: غير متاح")

    def check_for_updates(self):
        """التحقق من وجود تحديثات للإضافات"""
        try:
            updates_available = 0
            for ext_id in self.extensions:
                if self.needs_update(ext_id):
                    updates_available += 1
                    # تحديث حالة الإضافة في الواجهة
                    if ext_id in self.extension_widgets:
                        widget = self.extension_widgets[ext_id]
                        update_btn = widget.findChild(QPushButton, f"update_btn_{ext_id}")
                        if update_btn:
                            update_btn.setEnabled(True)
                            update_btn.setText("تحديث متوفر")
                            update_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            
            self.updates_label.setText(f"التحديثات: {updates_available} متاحة")
            return updates_available
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من التحديثات: {str(e)}")
            return 0

    def show_extension_settings(self, ext_id):
        """عرض إعدادات الإضافة"""
        extension = self.extensions_manager.active_extensions.get(ext_id)
        if extension and hasattr(extension, 'show_settings'):
            extension.show_settings()
    
    def show_extension_details(self, ext_id):
        """عرض تفاصيل الإضافة"""
        try:
            # الحصول على معلومات الإضافة
            ext_data = self.extensions_manager.extensions.get(ext_id)
            if not ext_data:
                QMessageBox.warning(self, "خطأ", "لم يتم العثور على معلومات الإضافة")
                return
            
            manifest = ext_data.get('manifest', {})
            
            # إنشاء نص التفاصيل مع تنسيق HTML
            details = f"""
            <div style='background-color: #212121; padding: 16px; border-radius: 8px;'>
                <h3 style='margin-bottom: 16px;'>{manifest.get('name', 'غير معروف')}</h3>
                <p><b>المعرف:</b> {manifest.get('id', 'غير معروف')}</p>
                <p><b>الإصدار:</b> {manifest.get('version', 'غير معروف')}</p>
                <p><b>متوافق مع:</b> {manifest.get('app_version', {}).get('min', 'غير معروف')} - {manifest.get('app_version', {}).get('max', 'غير معروف')}</p>
                <p><b>الوصف:</b> {manifest.get('description', 'لا يوجد وصف')}</p>
                <p><b>المطور:</b> {manifest.get('author', 'غير معروف')}</p>
                <p><b>التصنيف:</b> {manifest.get('category', 'غير مصنف')}</p>
            """
            
            # إضافة المتطلبات إذا وجدت
            requires = manifest.get('requires', {})
            if requires:
                details += "<div style='margin-top: 12px;'><p><b>المتطلبات:</b></p><ul>"
                for pkg, version in requires.items():
                    details += f"<li>{pkg} {version}</li>"
                details += "</ul></div>"
                
            # إضافة حالة التفعيل مع لون مناسب
            is_active = ext_id in self.extensions_manager.active_extensions
            status_color = "#4CAF50" if is_active else "#f44336"
            status_text = "مفعلة" if is_active else "معطلة"
            details += f"<p><b>الحالة:</b> <span style='color: {status_color};'>{status_text}</span></p></div>"
            
            # إنشاء وتخصيص نافذة التفاصيل
            msg = QMessageBox(self)
            msg.setObjectName("ExtensionDetails")
            msg.setWindowTitle("تفاصيل الإضافة")
            msg.setTextFormat(Qt.RichText)
            msg.setText(details)
            msg.setIcon(QMessageBox.Information)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1a1a1a;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
            msg.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء عرض التفاصيل:\n{str(e)}")

    def update_log(self):
        """تحديث سجل الأضافات"""
        try:
            log_path = "سجلات.log"  # مسار الملف مباشرة في المجلد الرئيسي
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_content = f.readlines()
                    # عرض آخر 100 سطر فط
                    log_content = log_content[-100:]
                    self.log_browser.setText(''.join(log_content))
                    # تحريك المؤشر إلى النهاية
                    scrollbar = self.log_browser.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
            else:
                self.log_browser.setText("لا يوجد ملف سجل")
        except Exception as e:
            self.log_browser.setText(f"خطأ في قراءة السجل: {str(e)}")
    

    
    def save_and_close(self):
        """حفظ التغييرات وإغلاق النافذة"""
        try:
            # حفظ حالة تفعيل الإضافات
            enabled = {}
            disabled = []
            
            for ext_id, checkbox in self.checkboxes.items():
                if checkbox.isChecked():
                    enabled[ext_id] = True
                else:
                    disabled.append(ext_id)
            
            # حفظ الإعدادات
            self.extensions_manager.save_extension_settings(enabled, disabled)
            
            # إغلاق النافذة
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ الإعدادات:\n{str(e)}")

    def setup_stats_tab(self, tab):
        """إعداد تبويب الإحصائيات والسجل"""
        layout = QVBoxLayout()
        
        # إحصائيات عامة
        stats_group = QGroupBox("إحصائيات عامة")
        stats_layout = QGridLayout()
        
        # حساب الإحصائيات
        total_count = len(self.extensions_manager.extensions)
        active_count = len(self.extensions_manager.active_extensions)
        
        # عرض الإحصائيات
        stats_layout.addWidget(QLabel("إجمالي الإضافات:"), 0, 0)
        stats_layout.addWidget(QLabel(str(total_count)), 0, 1)
        
        stats_layout.addWidget(QLabel("الإضافات النشطة:"), 1, 0)
        stats_layout.addWidget(QLabel(f"<span style='color: green;'>{active_count}</span>"), 1, 1)
        
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # سجل الأحداث
        log_group = QGroupBox("سجل الأحداث")
        log_layout = QVBoxLayout()
        
        # إنشاء مربع النص للسجل
        self.log_browser = QTextBrowser()
        self.log_browser.setReadOnly(True)
        self.log_browser.setMinimumHeight(200)
        
        # تعريب القائمة السياقية للسجل
        self.log_browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.log_browser.customContextMenuRequested.connect(self.show_log_context_menu)
        
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

    def show_log_context_menu(self, position):
        """عرض القائمة السياقية للسجل"""
        menu = QMenu()
        
        # إضافة الإجراءات المعربة
        copy_action = menu.addAction("نسخ")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.log_browser.copy)
        
        copy_link_action = menu.addAction("نسخ رابط الموقع")
        copy_link_action.triggered.connect(lambda: self.copy_log_link(self.log_browser.textCursor()))
        
        select_all_action = menu.addAction("تحديد الكل")
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.log_browser.selectAll)
        
        # عرض القائمة
        menu.exec_(self.log_browser.mapToGlobal(position))

    def clear_log(self):
        """مسح محتوى ملف السجل"""
        try:
            log_path = "سجلات.log"
            # مسح محتوى الملف
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("")  # كتابة ملف فارغ
            
            # مسح محتوى اعرض
            self.log_browser.clear()
            
            # إضافة رسالة تأكيد
            self.log_browser.setText("تم مسح السجل بنجاح")
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل مسح السجل: {str(e)}")





    def refresh_extensions(self):
        """تحديث قائمة الإضافات المثبتة"""
        try:
            self.extensions_manager.log_message("بدء تحديث الإضافات...")
            
            previously_active = set(self.extensions_manager.active_extensions.keys())
            self.extensions_manager.discover_extensions()
            
            activated_count = 0
            for ext_id in previously_active:
                if ext_id in self.extensions_manager.extensions and ext_id not in self.extensions_manager.active_extensions:
                    if self.extensions_manager.activate_extension(ext_id):
                        activated_count += 1
                        
            self.extensions_manager.log_message(f"تم تحديث {activated_count} إضافة بنجاح")
            self.setup_installed_tab(self.tab_widget.widget(0))
            
        except Exception as e:
            self.extensions_manager.log_message(f"خطأ في تحديث الإضافات: {str(e)}", "ERROR")
    def update_store_view(self, extensions):
        """تحديث عرض المتجر بقائمة الإضافات المحددة مع دعم التحميل المتدرج"""
        try:
            # مسح العناصر السابقة
            for i in reversed(range(self.store_layout.count())):
                widget = self.store_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
                
            # إنشاء ويدجت للتمرير
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # إنشاء الويدجت الرئيسي
            container = QWidget()
            container.setObjectName("StoreContainer")
            layout = QVBoxLayout(container)
            
            # إضافة حقل البحث
            search_layout = QHBoxLayout()
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("البحث في الإضافات...")
            self.search_input.textChanged.connect(lambda: self.filter_extensions(extensions))
            search_layout.addWidget(self.search_input)
            
            # إضافة قائمة التصفية
            self.filter_combo = QComboBox()
            self.filter_combo.addItems(["الكل", "مثبتة", "غير مثبتة", "تحتاج تحديث"])
            self.filter_combo.currentTextChanged.connect(lambda: self.filter_extensions(extensions))
            search_layout.addWidget(self.filter_combo)
            
            layout.addLayout(search_layout)
            
            # إنشاء مخزن مؤقت للويدجت
            self.extension_widgets = {}
            
            # تحميل أول 20 إضافة فقط
            self.current_page = 0
            self.items_per_page = 20
            self.all_extensions = extensions
            
            # إضافة الإضافات الأولية
            self.load_more_extensions(layout)
            
            # إضافة زر "تحميل المزيد"
            self.load_more_btn = QPushButton("تحميل المزيد")
            self.load_more_btn.clicked.connect(lambda: self.load_more_extensions(layout))
            layout.addWidget(self.load_more_btn)
            
            scroll_area.setWidget(container)
            self.store_layout.addWidget(scroll_area)
            
            # إضافة مراقب التمرير للتحميل التلقائي
            scroll_area.verticalScrollBar().valueChanged.connect(
                lambda value: self.check_scroll_position(value, scroll_area, layout)
            )
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحديث عرض المتجر:\n{str(e)}")

    def check_scroll_position(self, value, scroll_area, layout):
        """التحقق من موضع التمرير وتحميل المزيد من الإضافات عند الحاجة"""
        if value >= scroll_area.verticalScrollBar().maximum() * 0.8:
            self.load_more_extensions(layout)

    def load_more_extensions(self, layout):
        """تحميل المزيد من الإضافات"""
        try:
            start_idx = self.current_page * self.items_per_page
            end_idx = start_idx + self.items_per_page
            current_extensions = self.filter_current_extensions()[start_idx:end_idx]
            
            if not current_extensions:
                self.load_more_btn.setVisible(False)
                return
                
            for ext in current_extensions:
                if ext['id'] not in self.extension_widgets:
                    widget = self.create_store_extension_widget(ext)
                    self.extension_widgets[ext['id']] = widget
                    layout.insertWidget(layout.count() - 1, widget)
            
            self.current_page += 1
            
        except Exception as e:
            print(f"خطأ في تحميل الإضافات: {str(e)}")

    def filter_extensions(self, extensions=None):
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

    def filter_current_extensions(self):
        """تصفية الإضافات الحالية حسب معايير البحث والفلتر"""
        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()
        
        filtered_extensions = []
        for ext in self.all_extensions:
            # تطبيق البحث
            if search_text and not (
                search_text in ext['name'].lower() or 
                search_text in ext.get('description', '').lower() or
                search_text in ext.get('author', '').lower()
            ):
                continue
            
            # تطبيق الفلتر
            is_installed = ext['id'] in self.extensions_manager.extensions
            needs_update = False
            
            if is_installed:
                installed_version = self.extensions_manager.extensions[ext['id']].get('manifest', {}).get('version', '0.0.0')
                store_version = ext.get('version', '0.0.0')
                needs_update = self.compare_versions(installed_version, store_version) < 0
            
            if filter_type == "مثبتة" and not is_installed:
                continue
            elif filter_type == "غير مثبتة" and is_installed:
                continue
            elif filter_type == "تحتاج تحديث" and not needs_update:
                continue
                
            filtered_extensions.append(ext)
        
        return filtered_extensions

    def create_store_extension_widget(self, extension):
        """إنشاء عنصر واجهة لإضافة في المتجر"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #212121;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
            QWidget:hover {
                border: 1px solid #054229;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #054229;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 90px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #065435;
            }
            QPushButton:pressed {
                background-color: #043821;
            }
            QPushButton#updateBtn {
                background-color: #FFA000;
            }
            QPushButton#updateBtn:hover {
                background-color: #FFB300;
            }
            QPushButton#updateBtn:pressed {
                background-color: #FF8F00;
            }
        """)
        
        layout = QHBoxLayout()
        
        # الأيقونة
        icon_label = QLabel()
        if 'icon' in extension and extension['icon']:
            icon_url = f"{self.store.raw_base_url}/store/extensions/{extension['id']}/{extension['icon']}"
            try:
                response = requests.get(icon_url)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    icon_label.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except:
                icon_label.setText("🧩")
        else:
            icon_label.setText("🧩")
        
        icon_label.setFixedSize(48, 48)
        layout.addWidget(icon_label)
        
        # معلومات الإضافة
        info_layout = QVBoxLayout()
        name_label = QLabel(f"<b>{extension['name']}</b>")
        name_label.setStyleSheet("font-size: 14px;")
        
        desc_label = QLabel(extension.get('description', ''))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #aaaaaa;")
        
        version_label = QLabel(f"الإصدار: {extension.get('version', '1.0.0')}")
        version_label.setStyleSheet("color: #888888; font-size: 11px;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        info_layout.addWidget(version_label)
        layout.addLayout(info_layout, stretch=1)
        
        # أزرار التحكم
        buttons_layout = QVBoxLayout()
        
        # التحقق من حالة التثبيت والإصدار
        is_installed = extension['id'] in self.extensions_manager.extensions
        needs_update = False
        
        if is_installed:
            installed_version = self.extensions_manager.extensions[extension['id']].get('manifest', {}).get('version', '0.0.0')
            store_version = extension.get('version', '0.0.0')
            needs_update = self.compare_versions(installed_version, store_version) < 0
            
            if needs_update:
                # زر التحديث
                update_btn = QPushButton("تحديث متوفر")
                update_btn.setObjectName("updateBtn")
                update_btn.setToolTip(f"تحديث من {installed_version} إلى {store_version}")
                update_btn.clicked.connect(lambda: self.install_extension(extension['id']))
                buttons_layout.addWidget(update_btn)
            else:
                # زر تم التثبيت (معطل)
                install_btn = QPushButton("مثبتة")
                install_btn.setEnabled(False)
                install_btn.setStyleSheet("background-color: #424242;")
                buttons_layout.addWidget(install_btn)
        else:
            # زر التثبيت
            install_btn = QPushButton("تثبيت")
            install_btn.clicked.connect(lambda: self.install_extension(extension['id']))
            buttons_layout.addWidget(install_btn)
        
        # زر التفاصيل
        details_btn = QPushButton("التفاصيل")
        details_btn.clicked.connect(lambda: self.show_store_extension_details(extension))
        buttons_layout.addWidget(details_btn)
        
        layout.addLayout(buttons_layout)
        widget.setLayout(layout)
        return widget

    def compare_versions(self, version1, version2):
        """مقارنة إصدارين وإرجاع -1 إذا كان الأول أقدم، 0 إذا كانا متساويين، 1 إذا كان الأول أحدث"""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # إكمال الأجزاء الناقصة بأصفار
            while len(v1_parts) < 3:
                v1_parts.append(0)
            while len(v2_parts) < 3:
                v2_parts.append(0)
            
            for i in range(3):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1
            return 0
        except:
            return 0


    def update_cache(self):
        """تحديث ملف الكاش"""
        try:
            cache_path = os.path.join(os.path.dirname(__file__), '..', 'cache', 'store_cache.json')
            if os.path.exists(cache_path):
                # قراءة الكاش الحالي
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # تحديث معلومات الإضافات المثبتة
                for ext in cache_data:
                    if ext['id'] in self.extensions_manager.extensions:
                        # حذف معلومات الإصدار من الكاش
                        if 'version' in ext:
                            del ext['version']
                
                # حفظ الكاش المحدث
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            logging.error(f"خطأ في تحديث الكاش: {str(e)}")

    def toggle_token_visibility(self):
        """تبديل إظهار/إخف�� الرمز"""
        if self.token_input.echoMode() == QLineEdit.Password:
            self.token_input.setEchoMode(QLineEdit.Normal)
        else:
            self.token_input.setEchoMode(QLineEdit.Password)

    def open_github_token_page(self):
        """فتح صفحة إنشاء رمز جيت هاب"""
        url = "https://github.com/settings/tokens/new?description=Qirtas%20Extension%20Store&scopes=repo"
        QDesktopServices.openUrl(QUrl(url))

    def validate_token(self, token):
        """التحقق من صلاحية الرمز"""
        try:
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get('https://api.github.com/rate_limit', headers=headers)
            
            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                QMessageBox.warning(self, "تحذير", 
                    "الرمز غير صالح أو تم إلغاؤه.\n"
                    "يرجى إنشاء رمز جديد."
                )
            return False
        except Exception as e:
            QMessageBox.critical(self, "خطأ", 
                f"حدث خطأ في التحقق من الرمز:\n{str(e)}"
            )
            return False

    def save_token(self, token):
        """حفظ الرمز بشكل آمن"""
        try:
            # التحقق من صلاحية الرمز قبل حفظه
            if not self.validate_token(token):
                return False
            
            # تشفير الرمز قبل حفظه (مكن استخدام مكتبة cryptography)
            # هذا مثال بسيط، يفضل استخدام تشفير أقوى
            encoded_token = base64.b64encode(token.encode()).decode()
            
            settings = {
                'github_token': encoded_token,
                'last_validated': datetime.now().isoformat()
            }
            
            settings_path = os.path.join(os.path.dirname(__file__), 'secure_settings.json')
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            return True
        except Exception as e:
            QMessageBox.critical(self, "خطأ", 
                f"فشل حفظ الرمز:\n{str(e)}"
            )
            return False

    def show_store_extension_details(self, extension_data):
        """عرض تفاصيل الإضافة من المتجر"""
        try:
            # إنشاء نص التفاصيل مع تنسيق HTML
            details = f"""
            <div style='background-color: #212121; padding: 16px; border-radius: 8px;'>
                <h3 style='margin-bottom: 16px;'>{extension_data['name']}</h3>
                <p><b>المعرف:</b> {extension_data['id']}</p>
                <p><b>الإصدار:</b> {extension_data['version']}</p>
                <p><b>متوافق مع:</b> {extension_data['app_version']['min']} - {extension_data['app_version']['max']}</p>
                <p><b>الوصف:</b> {extension_data['description']}</p>
                <p><b>المطور:</b> {extension_data['author']}</p>
                <p><b>التصنيف:</b> {extension_data['category']}</p>
            """
            
            # إضافة المتطلبات إذا وجدت
            if 'requires' in extension_data and extension_data['requires']:
                details += "<div style='margin-top: 12px;'><p><b>المتطلبات:</b></p><ul>"
                for pkg, version in extension_data['requires'].items():
                    details += f"<li>{pkg} {version}</li>"
                details += "</ul></div>"
                
            # إضافة حالة التثبيت مع لون مناسب
            is_installed = extension_data['id'] in self.extensions_manager.extensions
            status_color = "#4CAF50" if is_installed else "#f44336"
            status_text = "مثبتة" if is_installed else "غير مثبتة"
            details += f"<p><b>الحالة:</b> <span style='color: {status_color};'>{status_text}</span></p></div>"
            
            # إنشاء وتخصيص نافذة التفاصيل
            msg = QMessageBox(self)
            msg.setObjectName("ExtensionDetails")
            msg.setWindowTitle("تفاصيل الإضافة")
            msg.setTextFormat(Qt.RichText)
            msg.setText(details)
            msg.setIcon(QMessageBox.Information)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1a1a1a;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
            msg.exec_()
            
        except KeyError as e:
            QMessageBox.warning(self, "خطأ", f"بيانات الإضافة غير مكتملة: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء عرض التفاصيل:\n{str(e)}")

    def refresh_store_view(self):
        """تحديث عرض المتجر"""
        try:
            # إعادة تحميل قائمة الإضافات
            self.extensions_manager.discover_extensions()
            
            # قراءة بيانات المتجر من الكاش
            cache_path = os.path.join(os.path.dirname(__file__), '..', 'cache', 'store_cache.json')
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    current_store_data = json.load(f)
            else:
                current_store_data = []
                
            self.update_store_view(current_store_data)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحديث العرض:\n{str(e)}")

    def closeEvent(self, event):
        """حدث إغلاق النافذة"""
        # حفظ حالة النافذة
        self.save_window_state()
        event.accept()

    def show_dialog(self):
        """عرض النافذة"""
        self.show()
        self.raise_()
        self.activateWindow()

    def save_window_state(self):
        """حفظ حالة وموقع النافذة"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())

    def restore_window_state(self):
        """استعادة حالة وموقع النافذة"""
        if self.settings.value('geometry'):
            self.restoreGeometry(self.settings.value('geometry'))
        if self.settings.value('windowState'):
            self.restoreState(self.settings.value('windowState'))

    def create_backup(self):
        """إنشاء نسخة احتياطية من الإضافات"""
        try:
            from datetime import datetime
            import tempfile
            import time
            
            # إنشاء مسار مؤقت في مجلد التطبيق
            temp_backup_dir = os.path.join(os.path.dirname(self.extensions_manager.extensions_dir), 'temp_backup')
            os.makedirs(temp_backup_dir, exist_ok=True)
            
            # إنشاء اسم الملف بالتاريخ والوقت
            backup_name = f"extensions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            backup_path = QFileDialog.getSaveFileName(
                self, 
                "حفظ النسخة الاحتياطية",
                backup_name,
                "Zip files (*.zip)"
            )[0]
            
            if backup_path:
                # إنشاء مسار مؤقت للملف المضغوط
                temp_zip_path = os.path.join(temp_backup_dir, 'temp_' + os.path.basename(backup_path))
                
                # إنشاء ملف الإعدادات
                settings_data = {
                    'active_extensions': list(self.extensions_manager.active_extensions.keys()),
                    'disabled_extensions': list(getattr(self.extensions_manager, 'disabled_extensions', []))
                }
                
                # حفظ الإعدادات في الملف المؤقت
                settings_path = os.path.join(temp_backup_dir, 'backup_settings.json')
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings_data, f, ensure_ascii=False, indent=4)
                
                try:
                    # إنشاء الملف المضغوط في المسار المؤقت
                    with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        # إضافة الإضافات
                        for ext_id in self.extensions_manager.extensions:
                            ext_path = os.path.join(self.extensions_manager.extensions_dir, ext_id)
                            if os.path.exists(ext_path):
                                for root, _, files in os.walk(ext_path):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        arcname = os.path.relpath(
                                            file_path, 
                                            self.extensions_manager.extensions_dir
                                        )
                                        try:
                                            zipf.write(file_path, arcname)
                                        except Exception as e:
                                            print(f"تعذر إضافة الملف {file}: {str(e)}")
                        
                        # إضافة ملف الإعدادات
                        zipf.write(settings_path, 'backup_settings.json')
                    
                    # محاولة نقل الملف المضغوط إلى الوجهة النهائية
                    max_attempts = 3
                    attempt = 0
                    success = False
                    
                    while attempt < max_attempts and not success:
                        try:
                            if os.path.exists(backup_path):
                                os.remove(backup_path)
                            shutil.move(temp_zip_path, backup_path)
                            success = True
                        except Exception as e:
                            attempt += 1
                            if attempt < max_attempts:
                                time.sleep(1)  # انتظار ثانية قبل المحاولة التالية
                    
                    if success:
                        QMessageBox.information(self, "تم", "تم إنشاء النسخة الاحتياطية بنجاح")
                    else:
                        raise Exception("تعذر نقل الملف المضغوط إلى الوجهة النهائية")
                    
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "خطأ",
                        f"حدث خطأ أثناء إنشاء النسخة الاحتياطية:\n{str(e)}"
                    )
                
                finally:
                    # تنظيف الملفات المؤقتة
                    try:
                        if os.path.exists(settings_path):
                            os.remove(settings_path)
                        if os.path.exists(temp_zip_path):
                            os.remove(temp_zip_path)
                        if os.path.exists(temp_backup_dir):
                            shutil.rmtree(temp_backup_dir)
                    except:
                        pass
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء إنشاء النسخة الاحتياطية:\n{str(e)}"
            )

    def restore_from_backup(self):
        """استعادة الإضافات من نسخة احتياطية"""
        try:
            backup_path = QFileDialog.getOpenFileName(
                self,
                "اختر ملف النسخة الاحتياطية",
                "",
                "Zip files (*.zip)"
            )[0]
            
            if backup_path:
                # تأكيد الاستعادة
                reply = QMessageBox.warning(
                    self,
                    "تأكيد الاستعادة",
                    "سيتم استبدال جميع الإضافات الحالية. هل تريد المتابعة؟",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # إيقاف جميع الإضافات النشطة
                    for ext_id in list(self.extensions_manager.active_extensions.keys()):
                        self.extensions_manager.deactivate_extension(ext_id)
                    
                    # استخراج الملفات
                    with zipfile.ZipFile(backup_path, 'r') as zipf:
                        # قراءة الإعدادات
                        settings_data = json.loads(zipf.read('backup_settings.json'))
                        
                        # حذف المجلد الحالي وإنشاء مجلد جديد
                        shutil.rmtree(self.extensions_manager.extensions_dir)
                        os.makedirs(self.extensions_manager.extensions_dir)
                        
                        # استخراج الملفات
                        zipf.extractall(self.extensions_manager.extensions_dir)
                    
                    # تحديث الإعدادات
                    self.extensions_manager.disabled_extensions = set(settings_data['disabled_extensions'])
                    
                    # إعادة اكتشاف وتحميل الإضافات
                    self.extensions_manager.discover_extensions()
                    self.extensions_manager.load_active_extensions()
                    
                    # تحديث الواجهة
                    self.refresh_extensions()
                    
                    QMessageBox.information(self, "تم", "تمت استعادة النسخة الاحتياطية بنجاح")
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء استعادة النسخة الاحتياطية:\n{str(e)}")






    def refresh_extensions(self):
        """تحديث قائمة الإضافات المثبتة"""
        self.extensions_manager.discover_extensions()
        self.extensions_manager.load_active_extensions()
        self.setup_installed_tab(self.tab_widget.widget(0))  # تحديث تبويب الإضافات المثتة فقط

    def update_store_view(self, extensions):
        """تحديث عرض المتجر بقائمة الإضافات المحددة"""
        try:
            # مسح العناصر السابقة
            for i in reversed(range(self.store_layout.count())):
                widget = self.store_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            
            # إضافة الإضافات الجديدة
            for ext in extensions:
                ext_widget = self.create_store_extension_widget(ext)
                self.store_layout.addWidget(ext_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحديث عرض المتجر:\n{str(e)}")

    def create_store_extension_widget(self, extension):
        """إنشاء عنصر واجهة لإضافة في المتجر"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #212121;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
            QWidget:hover {
                border: 1px solid #054229;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #054229;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 90px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #065435;
            }
            QPushButton:pressed {
                background-color: #043821;
            }
            QPushButton#updateBtn {
                background-color: #FFA000;
            }
            QPushButton#updateBtn:hover {
                background-color: #FFB300;
            }
            QPushButton#updateBtn:pressed {
                background-color: #FF8F00;
            }
        """)
        
        layout = QHBoxLayout()
        
        # الأيقونة
        icon_label = QLabel()
        if 'icon' in extension and extension['icon']:
            icon_url = f"{self.store.raw_base_url}/store/extensions/{extension['id']}/{extension['icon']}"
            try:
                response = requests.get(icon_url)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    icon_label.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except:
                icon_label.setText("🧩")
        else:
            icon_label.setText("🧩")
        
        icon_label.setFixedSize(48, 48)
        layout.addWidget(icon_label)
        
        # معلومات الإضافة
        info_layout = QVBoxLayout()
        name_label = QLabel(f"<b>{extension['name']}</b>")
        name_label.setStyleSheet("font-size: 14px;")
        
        desc_label = QLabel(extension.get('description', ''))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #aaaaaa;")
        
        version_label = QLabel(f"الإصدار: {extension.get('version', '1.0.0')}")
        version_label.setStyleSheet("color: #888888; font-size: 11px;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        info_layout.addWidget(version_label)
        layout.addLayout(info_layout, stretch=1)
        
        # أزرار التحكم
        buttons_layout = QVBoxLayout()
        
        # التحقق من حالة التثبيت والإصدار
        is_installed = extension['id'] in self.extensions_manager.extensions
        needs_update = False
        
        if is_installed:
            installed_version = self.extensions_manager.extensions[extension['id']].get('manifest', {}).get('version', '0.0.0')
            store_version = extension.get('version', '0.0.0')
            needs_update = self.compare_versions(installed_version, store_version) < 0
            
            if needs_update:
                # زر التحديث
                update_btn = QPushButton("تحديث متوفر")
                update_btn.setObjectName("updateBtn")
                update_btn.setToolTip(f"تحديث من {installed_version} إلى {store_version}")
                update_btn.clicked.connect(lambda: self.install_extension(extension['id']))
                buttons_layout.addWidget(update_btn)
            else:
                # زر تم التثبيت (معطل)
                install_btn = QPushButton("مثبتة")
                install_btn.setEnabled(False)
                install_btn.setStyleSheet("background-color: #424242;")
                buttons_layout.addWidget(install_btn)
        else:
            # زر التثبيت
            install_btn = QPushButton("تثبيت")
            install_btn.clicked.connect(lambda: self.install_extension(extension['id']))
            buttons_layout.addWidget(install_btn)
        
        # زر التفاصيل
        details_btn = QPushButton("التفاصيل")
        details_btn.clicked.connect(lambda: self.show_store_extension_details(extension))
        buttons_layout.addWidget(details_btn)
        
        layout.addLayout(buttons_layout)
        widget.setLayout(layout)
        return widget

    def compare_versions(self, version1, version2):
        """مقارنة إصدارين وإرجاع -1 إذا كان الأول أقدم، 0 إذا كانا متساويين، 1 إذا كان الأول أحدث"""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # إكمال الأجزاء الناقصة بأصفار
            while len(v1_parts) < 3:
                v1_parts.append(0)
            while len(v2_parts) < 3:
                v2_parts.append(0)
            
            for i in range(3):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1
            return 0
        except:
            return 0

    def install_extension(self, ext_id):
        """تثبت أو تحديث إضافة من المتجر"""
        try:
            # إظهار شريط التقدم
            progress = QProgressDialog("جار تثبيت الإضافة...", None, 0, 100, self)
            progress.setWindowTitle("تثبيت الإضافة")
            progress.setWindowModality(Qt.WindowModal)
            progress.setCancelButton(None)
            progress.setValue(0)
            
            # قراءة التوكن من ملف الإعدادات
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    github_token = settings.get('extensions', {}).get('github_token')
                    if not github_token:
                        raise Exception("لم يتم العثور على توكن GitHub في الإعدادات")
            except Exception as e:
                raise Exception(f"خطأ في قراءة ملف الإعدادات: {str(e)}")
            
            # تحضير الهيدرز مع التوكن
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {github_token}',
                'User-Agent': 'Qirtas-Extension-Store'
            }
            
            progress.setValue(10)
            progress.setLabelText("جار التحقق من المتطلبات...")
            
            # التحقق من manifest.json
            try:
                manifest_url = f"{self.store.raw_base_url}/store/extensions/{ext_id}/manifest.json"
                manifest_response = requests.get(manifest_url, headers=headers)
                manifest_response.raise_for_status()
                manifest_content = manifest_response.json()
            except requests.exceptions.RequestException as e:
                if manifest_response.status_code == 403:
                    raise Exception("خطأ في الوصول: تأكد من صلاحية توكن GitHub")
                elif manifest_response.status_code == 404:
                    raise Exception("لم يتم العثور على ملف manifest.json")
                else:
                    raise Exception(f"خطأ في الوصول إلى manifest.json: {str(e)}")
        
            
            # التحقق من المتطلبات وتثبيتها
            if 'requirements' in manifest_content and manifest_content['requirements']:
                progress.close()
                reply = QMessageBox.question(
                    self,
                    "تثبيت المتطلبات",
                    f"تحتاج هذه الإضافة إلى المكتبات التالية:\n- " + "\n- ".join(manifest_content['requirements']) + "\n\nهل تريد تثبيتها الآن؟",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    if not self.install_required_packages(manifest_content['requirements']):
                        raise Exception("فشل في تثبيت المتطلبات المطلوبة")
                else:
                    raise Exception("تم إلغاء التثبيت من قبل المستخدم")
                
                progress = QProgressDialog("جار تثبيت الإضافة...", None, 0, 100, self)
                progress.setWindowTitle("تثبيت الإضافة")
                progress.setWindowModality(Qt.WindowModal)
                progress.setCancelButton(None)
                progress.setValue(20)
            
            # جلب محتويات الإضافة
            progress.setLabelText("جار تنزيل ملفات الإضافة...")
            api_url = f"{self.store.base_url}/contents/store/extensions/{ext_id}"
            try:
                response = requests.get(api_url, headers=headers)
                response.raise_for_status()
                contents = response.json()
            except requests.exceptions.RequestException as e:
                if response.status_code == 403:
                    raise Exception("خطأ في الوصول: تأكد من صلاحية توكن GitHub")
                elif response.status_code == 404:
                    raise Exception("لم يتم العثور على مجلد الإضافة")
                else:
                    raise Exception(f"خطأ في جلب محتويات الإضافة: {str(e)}")
            
            # إنشاء مجلد الإضافة
            extensions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'extensions')
            ext_dir = os.path.join(extensions_dir, ext_id)
            os.makedirs(ext_dir, exist_ok=True)
            
            # تنزيل الملفات
            total_files = len([item for item in contents if item['type'] == 'file'])
            for i, item in enumerate(contents):
                if item['type'] == 'file':
                    progress_value = 30 + (60 * i // total_files)
                    progress.setValue(progress_value)
                    progress.setLabelText(f"جار تنزيل: {item['name']}")
                    
                    try:
                        file_url = f"{self.store.raw_base_url}/store/extensions/{ext_id}/{item['name']}"
                        file_response = requests.get(file_url, headers=headers)
                        file_response.raise_for_status()
                        
                        file_path = os.path.join(ext_dir, item['name'])
                        with open(file_path, 'wb') as f:
                            f.write(file_response.content)
                    except requests.exceptions.RequestException as e:
                        raise Exception(f"فشل في تنزيل الملف {item['name']}: {str(e)}")
            
            # إكمال التثبيت
            progress.setValue(90)
            progress.setLabelText("جار إكمال التثبيت...")
            
            # تحديث وتفعيل الإضافة
            self.update_cache()
            if hasattr(self.extensions_manager, 'scan_extensions'):
                self.extensions_manager.scan_extensions()
            
            if ext_id not in getattr(self.extensions_manager, 'disabled_extensions', []):
                if hasattr(self.extensions_manager, 'activate_extension'):
                    self.extensions_manager.activate_extension(ext_id)
            
            progress.setValue(100)
            progress.close()
            
            QMessageBox.information(self, "تم", "تم تثبيت الإضافة بنجاح")
            
            # تحديث الواجهة
            self.refresh_store_view()
            self.refresh_extensions()
            
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تثبيت الإضافة:\n{str(e)}")
            if 'ext_dir' in locals() and os.path.exists(ext_dir):
                import shutil
                shutil.rmtree(ext_dir, ignore_errors=True)

    def update_cache(self):
        """تحديث ملف الكاش"""
        try:
            cache_path = os.path.join(os.path.dirname(__file__), '..', 'cache', 'store_cache.json')
            if os.path.exists(cache_path):
                # قراءة الكاش الحالي
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                # تحديث معلومات الإضافات المثبتة
                for ext in cache_data:
                    if ext['id'] in self.extensions_manager.extensions:
                        # حذف معلومات الإصدار من الكاش
                        if 'version' in ext:
                            del ext['version']
                
                # حفظ الكاش المحدث
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            logging.error(f"خطأ في تحديث الكاش: {str(e)}")

    def toggle_token_visibility(self):
        """تبديل إظهار/إخفء الرمز"""
        if self.token_input.echoMode() == QLineEdit.Password:
            self.token_input.setEchoMode(QLineEdit.Normal)
        else:
            self.token_input.setEchoMode(QLineEdit.Password)

    def open_github_token_page(self):
        """فتح صفحة إنشاء رمز جيت هاب"""
        url = "https://github.com/settings/tokens/new?description=Qirtas%20Extension%20Store&scopes=repo"
        QDesktopServices.openUrl(QUrl(url))

    def validate_token(self, token):
        """التحقق من صلاحية الرمز"""
        try:
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get('https://api.github.com/rate_limit', headers=headers)
            
            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                QMessageBox.warning(self, "تحذير", 
                    "الرمز غير صالح أو تم إلغاؤه.\n"
                    "يرجى إنشاء رمز جديد."
                )
            return False
        except Exception as e:
            QMessageBox.critical(self, "خطأ", 
                f"حدث خطأ في التحقق من الرمز:\n{str(e)}"
            )
            return False

    def save_token(self, token):
        """حفظ الرمز بشكل آمن"""
        try:
            # التحقق من صلاحية الرمز قبل حفظه
            if not self.validate_token(token):
                return False
            
            # تشفير الرمز قبل حفظه (مكن استخدام مكتبة cryptography)
            # هذا مثال بسيط، يفضل استخدام تشفير أقوى
            encoded_token = base64.b64encode(token.encode()).decode()
            
            settings = {
                'github_token': encoded_token,
                'last_validated': datetime.now().isoformat()
            }
            
            settings_path = os.path.join(os.path.dirname(__file__), 'secure_settings.json')
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            return True
        except Exception as e:
            QMessageBox.critical(self, "خطأ", 
                f"فشل حفظ الرمز:\n{str(e)}"
            )
            return False

    def show_store_extension_details(self, extension_data):
        """عرض تفاصيل الإضافة من المتجر"""
        try:
            # إنشاء نص التفاصيل مع تنسيق HTML
            details = f"""
            <div style='background-color: #212121; padding: 16px; border-radius: 8px;'>
                <h3 style='margin-bottom: 16px;'>{extension_data['name']}</h3>
                <p><b>المعرف:</b> {extension_data['id']}</p>
                <p><b>الإصدار:</b> {extension_data['version']}</p>
                <p><b>متوافق مع:</b> {extension_data['app_version']['min']} - {extension_data['app_version']['max']}</p>
                <p><b>الوصف:</b> {extension_data['description']}</p>
                <p><b>المطور:</b> {extension_data['author']}</p>
                <p><b>التصنيف:</b> {extension_data['category']}</p>
            """
            
            # إضافة المتطلبات إذا وجدت
            if 'requires' in extension_data and extension_data['requires']:
                details += "<div style='margin-top: 12px;'><p><b>المتطلبات:</b></p><ul>"
                for pkg, version in extension_data['requires'].items():
                    details += f"<li>{pkg} {version}</li>"
                details += "</ul></div>"
                
            # إضافة حالة التثبيت مع لون مناسب
            is_installed = extension_data['id'] in self.extensions_manager.extensions
            status_color = "#4CAF50" if is_installed else "#f44336"
            status_text = "مثبتة" if is_installed else "غير مثبتة"
            details += f"<p><b>الحالة:</b> <span style='color: {status_color};'>{status_text}</span></p></div>"
            
            # إنشاء وتخصيص نافذة التفاصيل
            msg = QMessageBox(self)
            msg.setObjectName("ExtensionDetails")
            msg.setWindowTitle("تفاصيل الإضافة")
            msg.setTextFormat(Qt.RichText)
            msg.setText(details)
            msg.setIcon(QMessageBox.Information)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1a1a1a;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
            msg.exec_()
            
        except KeyError as e:
            QMessageBox.warning(self, "خطأ", f"بيانات الإضافة غير مكتملة: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء عرض التفاصيل:\n{str(e)}")

    def refresh_store_view(self):
        """تحديث عرض المتجر"""
        try:
            # إعادة تحميل قائمة الإضافات
            self.extensions_manager.discover_extensions()
            
            # قراءة بيانات المتجر من الكاش
            cache_path = os.path.join(os.path.dirname(__file__), '..', 'cache', 'store_cache.json')
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    current_store_data = json.load(f)
            else:
                current_store_data = []
                
            self.update_store_view(current_store_data)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحديث العرض:\n{str(e)}")

    def closeEvent(self, event):
        """حدث إغلاق النافذة"""
        # حفظ حالة النافذة
        self.save_window_state()
        event.accept()

    def show_dialog(self):
        """عرض النافذة"""
        self.show()
        self.raise_()
        self.activateWindow()

    def save_window_state(self):
        """حفظ حالة وموقع النافذة"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())

    def restore_window_state(self):
        """استعادة حالة وموقع النافذة"""
        if self.settings.value('geometry'):
            self.restoreGeometry(self.settings.value('geometry'))
        if self.settings.value('windowState'):
            self.restoreState(self.settings.value('windowState'))

    def install_required_packages(self, requirements):
        """تثبيت المكتبات المطلوبة للإضافة"""
        try:
            progress = QProgressDialog(self)
            progress.setWindowTitle("تثبيت المتطلبات")
            progress.setLabelText("جاري تثبيت المكتبات المطلوبة...")
            progress.setMinimum(0)
            progress.setMaximum(len(requirements) * 100)
            progress.setCancelButton(None)
            progress.setWindowModality(Qt.WindowModal)
            
            # الحصول على مسار البيئة الافتراضية أو مسار التطبيق
            if hasattr(sys, '_MEIPASS'): 
                try:
                    python_path = os.path.join(sys._MEIPASS, 'python')
                    site_packages = os.path.join(sys._MEIPASS, 'lib', 'site-packages')
                except Exception as e:
                    print(f"خطأ في الحصول على مسار البيئة الافتراضية: {str(e)}")
                    return False
                
            else:
                try:
                    python_path = sys.executable
                    site_packages = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib', 'site-packages')
                except Exception as e:
                    print(f"خطأ في الحصول على مسار البيئة الافتراضية: {str(e)}")
                    return False
            
            os.makedirs(site_packages, exist_ok=True)
            try:
                for i, package in enumerate(requirements):
                    base_progress = i * 100
                    progress.setValue(base_progress)
                    progress.setLabelText(f"جاري تثبيت {package}...")
                    
                    try:
                        # تحديد الأمر المناسب بناءً على نوع التشغيل
                        if hasattr(sys, '_MEIPASS'):
                            # في حالة التشغيل من خلال PyInstaller
                            pip_command = [
                                sys.executable, "-m", "pip", "install",
                                package,
                                "--target", site_packages,
                                "--upgrade",
                                "--no-cache-dir",
                                "--no-deps"  # تجنب تثبيت التبعيات لتفادي المشاكل مع PyInstaller
                            ]
                        else:
                            # في حالة التشغيل العادي
                            pip_command = [
                                python_path, "-m", "pip", "install",
                                package,
                                f"--target={site_packages}",
                                "--upgrade",
                                "--no-cache-dir"
                            ]
                            
                        process = subprocess.Popen(
                            pip_command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True,
                            bufsize=1
                        )
                    except Exception as e:
                        print(f"خطأ في إنشاء عملية pip: {str(e)}")
                        return False
            except Exception as e:
                print(f"خطأ في إنشاء عملية pip: {str(e)}")
                return False
            try:
                    # تتبع تقدم التثبيت
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            # تحديث حالة التقدم بناءً على مخرجات pip
                            if "Collecting" in output:
                                progress.setLabelText(f"جاري تحميل {package}...")
                                progress.setValue(base_progress + 25)
                            elif "Downloading" in output:
                                progress.setLabelText(f"جاري تنزيل {package}...")
                                progress.setValue(base_progress + 50)
                            elif "Installing" in output:
                                progress.setLabelText(f"جاري تثبيت {package}...")
                                progress.setValue(base_progress + 75)
                    
                    # التحقق من نجاح التثبيت
                    if process.returncode != 0:
                        _, stderr = process.communicate()
                        raise Exception(f"فشل تثبيت {package}:\n{stderr}")
                    
                    # إضافة مسار المكتبات إلى sys.path
                    if site_packages not in sys.path:
                        sys.path.append(site_packages)
                    
                    progress.setValue(base_progress + 100)
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تثبيت {package}:\n{str(e)}")
                return False
            
            progress.setValue(progress.maximum())
            progress.close()
            QMessageBox.information(self, "تم", "تم تثبيت جميع المكتبات بنجاح")
            return True
            
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(self, "خطأ", f"حدث خطأ عام:\n{str(e)}")
            return False




class ExtensionsManager:
    def __init__(self, editor):
        self.editor = editor
        self.extensions = {}
        self.active_extensions = {}
        self.disabled_extensions = set()
        self.incompatible_extensions = set()
        self.app_version = getattr(editor, 'app_version', '1.0.0')
        self.platform = self.get_current_platform()
        self.file_access_restrictions = False
        self.network_restrictions = False
        self.system_restrictions = False
        self.monitoring_enabled = False
        self.extensions_menu = None
        
        self.extensions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'extensions')
        if not os.path.exists(self.extensions_dir):
            os.makedirs(self.extensions_dir)
        
        # إعداد التسجيل باللغة العربية
        setup_arabic_logging()
        self.logger = logging.getLogger('ExtensionsManager')
        
        self.load_extension_settings()
        self.discover_extensions()
        self.load_active_extensions()
        self.setup_menu()
        
    def log_message(self, message, level="INFO"):
        """تسجيل رسالة في ملف السجل"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp} - ExtensionsManager - {level} - {message}\n"
            
            with open('سجلات.log', 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"خطأ في كتابة السجل: {str(e)}")
    def setup_menu(self):
        """إعداد قائمة الإضافات"""
        if not hasattr(self.editor, 'menuBar'):
            return
        
        # البحث عن قائمة الأدوات
        tools_menu = None
        for action in self.editor.menuBar().actions():
            if action.text() == 'أدوات':
                tools_menu = action.menu()
                # إزالة القائمة القديمة للإضافات إن وجدت
                for action in tools_menu.actions():
                    if action.text() == 'إضافات':
                        tools_menu.removeAction(action)
                break
        
        if not tools_menu:
            tools_menu = self.editor.menuBar().addMenu('أدوات')
        
        # إنشاء قائمة فرعية جديدة للإضافات
        self.extensions_menu = QMenu('إضافات', tools_menu)
        tools_menu.addMenu(self.extensions_menu)
        
        # إضافة إجراء إدارة الإضافات
        manage_action = QAction('إدارة الإضافات', self.extensions_menu)
        manage_action.triggered.connect(self.show_extension_manager)
        self.extensions_menu.addAction(manage_action)
        
        # إضافة فاصل
        self.extensions_menu.addSeparator()
        
        # إضافة الإضافات النشطة للقائمة
        for ext_id, extension in self.active_extensions.items():
            if hasattr(extension, 'get_menu_items'):
                menu_items = extension.get_menu_items()
                if menu_items:
                    # إنشاء قائمة فرعية للإضافة إذا كان لديها أكثر من عنصر
                    if len(menu_items) > 1:
                        ext_menu = QMenu(self.extensions[ext_id]['manifest'].get('name', ext_id), self.extensions_menu)
                        for item in menu_items:
                            action = QAction(item['name'], ext_menu)
                            action.triggered.connect(item['callback'])
                            if 'shortcut' in item:
                                action.setShortcut(item['shortcut'])
                            ext_menu.addAction(action)
                        self.extensions_menu.addMenu(ext_menu)
                    else:
                        # إضافة عنصر واحد مباشرة للقائمة
                        item = menu_items[0]
                        action = QAction(item['name'], self.extensions_menu)
                        action.triggered.connect(item['callback'])
                        if 'shortcut' in item:
                            action.setShortcut(item['shortcut'])
                        self.extensions_menu.addAction(action)

    def get_current_platform(self):
        """تحديد نظام التشغيل الحالي"""
        import platform
        system = platform.system().lower()
        return {
            'windows': 'windows',
            'linux': 'linux',
            'darwin': 'macos'
        }.get(system, 'unknown')

    def check_compatibility(self, manifest):
        """التحقق من توافق الإضافة"""
        try:
            # التحقق من توافق نظام التشغيل
            platforms = manifest.get('platform', {})
            if not platforms.get(self.platform, False):
                return False, f"الإضافة غير متوافقة مع نظام {self.platform}"

            # التحقق من إصدار التطبيق
            app_version = manifest.get('app_version', {})
            min_version = app_version.get('min', '0.0.0')
            max_version = app_version.get('max', '999.999.999')

            if not (semver.VersionInfo.parse(min_version) <= 
                   semver.VersionInfo.parse(self.app_version) <= 
                   semver.VersionInfo.parse(max_version)):
                return False, f"الإضافة تتطلب إصدار تطبيق بين {min_version} و {max_version}"

            return True, ""
        except Exception as e:
            return False, f"خطأ في التحقق من التوافق: {str(e)}"

    def discover_extensions(self):
        """اكتشاف الإضافات المتوفرة مع التحقق من التوافق"""
        self.extensions.clear()
        self.incompatible_extensions.clear()

        for ext_folder in os.listdir(self.extensions_dir):
            ext_path = os.path.join(self.extensions_dir, ext_folder)
            
            if not os.path.isdir(ext_path):
                continue
                
            manifest_path = os.path.join(ext_path, 'manifest.json')
            if not os.path.exists(manifest_path):
                continue
                
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                # التحقق من التوافق
                is_compatible, reason = self.check_compatibility(manifest)
                
                if is_compatible:
                    self.extensions[ext_folder] = {
                        'manifest': manifest,
                        'path': ext_path,
                        'instance': None
                    }
                else:
                    self.incompatible_extensions.add(ext_folder)
                    self.logger.warning(f"الإضافة {ext_folder} غير متوافقة: {reason}")
                    
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
                    self.logger.error(f"خطأ في تحميل اإضافة {ext_id}: {str(e)}")

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
        """دالة لعرض مدير الإضافات"""
        dialog = ExtensionManagerDialog.get_instance(self)
        dialog.show_dialog()

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
            
            # تحويل enabled من قائمة إلى قاموس
            enabled_dict = {}
            for ext_id in enabled:
                enabled_dict[ext_id] = True
            
            # تحديث إعدادات الإضافات مع الحفاظ على الهيكل الصحيح
            if 'extensions' not in settings:
                settings['extensions'] = {}
            
            settings['extensions']['enabled'] = enabled_dict
            settings['extensions']['disabled'] = disabled
            
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
        try:
            if ext_id in self.active_extensions:
                extension = self.active_extensions[ext_id]
                
                # 1. استدع��ء دالة التنظيف في الإضافة
                if hasattr(extension, 'cleanup'):
                    extension.cleanup()
                
                # 2. إزالة أي عناصر واجهة مستخدم أضافتها الإضافة
                if hasattr(extension, 'remove_ui_elements'):
                    extension.remove_ui_elements()
                
                # 3. إقاف أي مؤقتات أو عمليات خلفية
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
                
                # 7. تحديث القائمة فقط إذا كانت الإضافة تحتوي على عناصر قائمة
                if hasattr(extension, 'get_menu_items'):
                    self.setup_menu()
                
                return True
        except Exception as e:
            self.logger.error(f"خطأ في إيقاف الإضافة {ext_id}: {str(e)}")
        return False

    def activate_extension(self, ext_id):
        """تفعيل إضافة محددة"""
        try:
            # التحقق من وجود الإضافة
            if ext_id not in self.extensions:
                raise Exception("الإضافة غير موجودة")
                
            # التحقق من أن الإضافة ليست مفعلة بالفعل
            if ext_id in self.active_extensions and self.active_extensions[ext_id]:
                return True
                
            # 2. تحميل الإضافة
            ext_data = self.extensions[ext_id]
            main_module = os.path.join(ext_data['path'], ext_data['manifest'].get('main', 'main.py'))
            
            if not os.path.exists(main_module):
                raise Exception(f"ملف الإضافة الرئيسي غير موجود: {main_module}")
            
            # 3. تحميل نظيف للموديول
            module_name = f"extensions.{ext_id}.main"
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            spec = importlib.util.spec_from_file_location(module_name, main_module)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 4. إنش��ء نسخة من الإضافة بشكل مرن
            try:
                # محاولة إنشاء الإضافة مع المحرر
                extension = module.Extension(self.editor)
            except TypeError:
                try:
                    # محاولة إنشاء الإضافة بدون ��سائط
                    extension = module.Extension()
                    # تعيين المحرر بعد الإنشاء إذا كانت الدالة موجودة
                    if hasattr(extension, 'set_editor'):
                        extension.set_editor(self.editor)
                except Exception as e:
                    raise Exception(f"شل إنشاء الإضافة: {str(e)}")
            
            # 5. تهيئة الإضافة
            if hasattr(extension, 'initialize'):
                extension.initialize()
            
            # 6. تخزين النسخة
            ext_data['instance'] = extension
            self.active_extensions[ext_id] = extension
            
            
            # 8. تحديث القائمة فقط إذا كانت الإضافة تحتوي على عناصر قائمة
            if hasattr(extension, 'get_menu_items'):
                self.setup_menu()
            
            # إضافة هذا الجزء بعد تفعيل الملحق
            if hasattr(self.editor, 'shortcut_manager'):
                self.editor.shortcut_manager.setup_extension_shortcuts()
            
            return True
        except Exception as e:
            self.log_message(f"فشل تفعيل الإضافة {ext_id}: {str(e)}", "ERROR")
            return False

    def get_context_menu_items(self):
        """الحصول على عناصر القائمة السياقية من الإضافات النشطة"""
        menu_items = []
        
        # التحقق من وجود إضافات نشطة
        if not hasattr(self, 'active_extensions'):
            return menu_items
        
        # جمع عناصر القائمة من كل إضافة نشطة
        for ext_id, extension in self.active_extensions.items():
            if hasattr(extension, 'get_context_menu_items'):
                try:
                    items = extension.get_context_menu_items()
                    if items:
                        menu_items.extend(items)
                except Exception as e:
                    print(f"خطأ في الحصول على عناصر القائمة من الإضافة {ext_id}: {str(e)}")
        
        return menu_items

    def create_context_menu_action(self, item, parent):
        """إنشاء إجرء للقائمة السياقية"""
        action = QAction(item['name'], parent)
        
        if 'shortcut' in item:
            action.setShortcut(item['shortcut'])
            
        if 'icon' in item:
            action.setIcon(item['icon'])
            
        if 'callback' in item:
            action.triggered.connect(item['callback'])
            
        if 'enabled' in item:
            action.setEnabled(item['enabled'])
            
        return action

 
