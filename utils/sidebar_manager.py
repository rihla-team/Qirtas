from PyQt5.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, 
                           QToolBar, QStackedWidget, QAction)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt,QSize
import os
from  .arabic_logger import setup_arabic_logging

setup_arabic_logging()
class SidebarManager:
    def __init__(self, editor):
        self.editor = editor
        self.views = {}  # تخزين العناصر
        self.registered_views = set()  # لتتبع العناصر المسجلة
        self.icon_cache = {}  
    def setup_sidebar(self):
        """إعداد النافذة الجانبية"""
        self.setup_dock_widget()
        self.setup_container()
        self.setup_toolbar()
        self.setup_content()

        self.setup_extensions_views()
        self.load_style()
        
    def setup_dock_widget(self):
        """إعداد النافذة القابلة للإرساء"""
        self.sidebar = QDockWidget(self.editor)
        self.sidebar.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.sidebar.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.editor.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
        self.sidebar.setTitleBarWidget(QWidget()) # إخفاء شريط العنوان
        
    def setup_container(self):
        """إعداد الحاوية الرئيسية"""
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0,0,0,0)
        self.sidebar.setWidget(self.container)
        
    def setup_toolbar(self):
        """إعداد شريط الأدوات"""
        self.toolbar = QToolBar()
        # تغيير التوجيه إلى أفقي
        self.toolbar.setOrientation(Qt.Horizontal)
        # إضافة خصائص لتحسين المظهر
        self.toolbar.setIconSize(QSize(16, 16))  # حجم الأيقونات
        self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)  # عرض الأيقونات فقط
        
        # تطبيق التنسيق مباشرة على شريط الأدوات
        self.toolbar.setStyleSheet("""
            QToolBar::separator {
                background-color: white;
                width: 1px;
                height: 16px;
                margin: 3px;
            }
        """)
        
        # إضافة خط فاصل
        self.toolbar.addSeparator()
        
        self.layout.addWidget(self.toolbar)
        
    def setup_content(self):
        """إعداد منطقة المحتوى"""
        self.content = QStackedWidget()
        self.layout.addWidget(self.content)
        
    def setup_extensions_views(self):
        """إعداد عناصر الملحقات"""
        self.clear_views()
        
        if hasattr(self.editor, 'extensions_manager'):
            for ext_id, extension in self.editor.extensions_manager.active_extensions.items():
                if hasattr(extension, 'get_sidebar_items'):
                    try:
                        items = extension.get_sidebar_items()
                        for item in items:
                            self.register_view(
                                ext_id,
                                item['widget'],
                                item.get('icon'),
                                item.get('tooltip')
                            )
                    except Exception as e:
                        self.editor.extensions_manager.log_message(f"خطأ في تحميل عناصر الشريط الجانبي من الملحق {ext_id}: {str(e)}", "ERROR")
                        
    def register_view(self, extension_id: str, widget: QWidget, icon=None, tooltip=None):
        """تسجيل عنصر في الشريط الجانبي"""
        view_id = f"{extension_id}_{widget.__class__.__name__}_{id(widget)}"
        
        self.content.addWidget(widget)
        
        if len(self.views) > 0 and len(self.views) % 3 == 0:
            self.toolbar.addSeparator()
        
        icon_obj = None
        if icon:
            if isinstance(icon, str):
                possible_paths = [
                    os.path.join(os.path.dirname(self.editor.extensions_manager.extensions[extension_id]['path']), icon),
                    os.path.join(os.path.dirname(self.editor.extensions_manager.extensions[extension_id]['path']), 'resources', 'icons', icon),
                    os.path.join(os.path.dirname(self.editor.extensions_manager.extensions[extension_id]['path']), extension_id, icon)
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        icon_obj = QIcon(path)
                        self.editor.extensions_manager.log_message(f"تم تحميل الأيقونة من: {path}")
                        break
                
                if not icon_obj:
                    self.editor.extensions_manager.log_message(
                        f"لم يتم العثور على الأيقونة: {icon} للإضافة {extension_id}", "WARNING")
                    icon_obj = QIcon()  # أيقونة فارغة كبديل
            elif isinstance(icon, QIcon):
                icon_obj = icon
        
        action = QAction(self.toolbar)
        if icon_obj:
            action.setIcon(icon_obj)
        if tooltip:
            action.setToolTip(tooltip)
        action.setCheckable(True)
        action.triggered.connect(lambda checked: self.show_view(widget))
        self.toolbar.addAction(action)
        
        self.views[view_id] = {
            'widget': widget,
            'action': action,
            'extension_id': extension_id
        }
        
        if len(self.views) == 1:
            action.setChecked(True)
            self.show_view(widget)
        
    def create_view_action(self, widget, icon=None, tooltip=None):
        """إنشاء إجراء للعرض"""
        action = QAction(self.toolbar)
        if icon:
            action.setIcon(icon)
        if tooltip:
            action.setToolTip(tooltip)
        action.setCheckable(True)
        action.triggered.connect(lambda: self.show_view(widget))
        self.toolbar.addAction(action)
        return action
        
    def clear_views(self):
        """إزالة جميع العناصر"""
        self.toolbar.clear()
        for view in self.views.values():
            self.content.removeWidget(view['widget'])
        self.views.clear()
        self.registered_views.clear()
        
    def show_view(self, widget):
        """عرض العنصر المحدد"""
        if not widget:
            return
        
        for view in self.views.values():
            view['action'].setChecked(view['widget'] == widget)
            if view['widget'] != widget:
                view['widget'].hide()
            
        widget.show()
        self.content.setCurrentWidget(widget)
        
    def load_style(self):
        """تحميل ملف التنسيق"""
        try:
            if not hasattr(self, 'sidebar'):
                self.editor.extensions_manager.log_message("لم يتم إنشاء الشريط الجانبي بعد", "WARNING")
                return
                
            style_path = os.path.join('resources', 'styles', 'sidebar.qss')
            if os.path.exists(style_path):
                with open(style_path, 'r', encoding='utf-8') as f:
                    style = f.read()
                    self.editor.extensions_manager.log_message(f"تم تحميل ملف التنسيق: {style_path}")
                    
                # إضافة تنسيق للخط الفاصل
                additional_style = """
                QToolBar::separator {
                    background-color: white;
                    width: 1px;
                    height: 16px;
                    margin: 3px;
                }
                """
                style += additional_style
                    
                # تطبيق التنسيق
                self.sidebar.setStyleSheet(style)
                self.container.setObjectName("SidebarContainer")
            else:
                self.editor.extensions_manager.log_message(f"ملف التنسيق غير موجود: {style_path}", "WARNING")
                
        except Exception as e:
            self.editor.extensions_manager.log_message(f"خطأ في تحميل ملف التنسيق: {str(e)}", "ERROR")
        
    def toggle_sidebar(self):
        """إخفاء/إظهار النافذة لجانبية"""
        if self.sidebar.isVisible():
            self.sidebar.hide()
        else:
            self.sidebar.show()
