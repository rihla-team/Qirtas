# utils/sidebar_manager.py
try:
    from PyQt5.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, 
                           QToolBar, QStackedWidget, QAction, QLayout)
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import Qt, QSize, pyqtSlot, pyqtSignal
    import os
    from .arabic_logger import setup_arabic_logging, log_in_arabic
    import logging
    from typing import Dict
    from functools import lru_cache
except Exception as e:
    logger = logging.getLogger(__name__)
    log_in_arabic(logger, logging.ERROR, f"خطأ في استيراد المكتبات: {e}")

formatter = setup_arabic_logging()
logger = logging.getLogger(__name__)

class SidebarManager(QWidget):
    view_changed = pyqtSignal(QWidget)
    
    ICON_SIZE = QSize(16, 16)
    
    TOOLBAR_STYLE = """
        QToolBar {
            spacing: 4px;
            background: transparent;
            border: none;
        }
        QToolBar::separator {
            background-color: #555555;
            width: 1px;
            height: 16px;
            margin: 3px;
        }
        QToolButton {
            border: none;
            padding: 4px;
        }
        QToolButton:hover {
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
        }
        QToolButton:checked {
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 2px;
        }
        QToolBarExtension, QToolBar::handle {
            image: none;
            width: 0;
            margin: 0;
            padding: 0;
            border: none;
            background: none;
        }
        QDockWidget {
            border: none;
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
        }
        QDockWidget::title {
            border: none;
            text-align: left;
            background: transparent;
            padding: 0px;
        }
    """
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self._views: Dict[str, dict] = {}
        self._icon_cache: Dict[str, QIcon] = {}
        self._current_widget = None
        self._setup_ui()
        
    def _setup_ui(self):
        try:
            # إعداد النافذة القابلة للإرساء
            self.sidebar = QDockWidget(self.editor)
            self.sidebar.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
            self.sidebar.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            self.editor.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
            self.sidebar.setTitleBarWidget(QWidget())
            
            # إعداد الحاوية والتخطيط
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            self.sidebar.setWidget(container)
            
            # إعداد شريط الأدوات
            self.toolbar = QToolBar()
            self.toolbar.setOrientation(Qt.Horizontal)
            self.toolbar.setIconSize(self.ICON_SIZE)
            self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
            self.toolbar.setContextMenuPolicy(Qt.NoContextMenu)
            self.toolbar.setMovable(False)
            self.toolbar.setFloatable(False)
            self.toolbar.setAllowedAreas(Qt.TopToolBarArea)
            self.toolbar.setStyleSheet(self.TOOLBAR_STYLE)
            layout.addWidget(self.toolbar)
            
            # إعداد منطقة المحتوى
            self.content = QStackedWidget()
            layout.addWidget(self.content)
            
            # ربط الإشارات
            self.view_changed.connect(self._on_view_changed)
            log_in_arabic(logger, logging.INFO, "تم إعداد واجهة الشريط الجانبي بنجاح")
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في إعداد واجهة الشريط الجانبي: {str(e)}")
            raise
        
    @pyqtSlot()
    def setup_sidebar(self):
        try:
            if not hasattr(self.editor, 'extensions_manager'):
                log_in_arabic(logger, logging.WARNING, "مدير الإضافات غير متوفر")
                return
                
            self.clear_views()
            self._load_extensions()
            log_in_arabic(logger, logging.INFO, "تم إعداد الشريط الجانبي بنجاح")
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في إعداد الشريط الجانبي: {str(e)}")
    
    @lru_cache(maxsize=128)
    def _get_icon_path(self, extension_id: str, icon_name: str) -> str:
        try:
            base_path = os.path.dirname(self.editor.extensions_manager.extensions[extension_id]['path'])
            for path in [
                os.path.join(base_path, icon_name),
                os.path.join(base_path, 'resources', 'icons', icon_name),
                os.path.join(base_path, extension_id, icon_name)
            ]:
                if os.path.exists(path):
                    log_in_arabic(logger, logging.DEBUG, f"تم العثور على الأيقونة في: {path}")
                    return path
            log_in_arabic(logger, logging.WARNING, f"لم يتم العثور على الأيقونة: {icon_name}")
            return ""
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في البحث عن مسار الأيقونة: {str(e)}")
            return ""
    
    def _load_icon(self, extension_id: str, icon_path: str) -> QIcon:
        try:
            if icon_path in self._icon_cache:
                return self._icon_cache[icon_path]
                
            path = self._get_icon_path(extension_id, icon_path)
            if path:
                icon = QIcon(path)
                self._icon_cache[icon_path] = icon
                log_in_arabic(logger, logging.DEBUG, f"تم تحميل الأيقونة: {icon_path}")
                return icon
                
            return QIcon()
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تحميل الأيقونة: {str(e)}")
            return QIcon()
    
    def _load_extensions(self):
        try:
            loaded_count = 0
            for ext_id, extension in self.editor.extensions_manager.active_extensions.items():
                if not hasattr(extension, 'get_sidebar_items'):
                    continue
                    
                try:
                    items = extension.get_sidebar_items()
                    for item in items:
                        self._add_view(ext_id, item)
                        loaded_count += 1
                except Exception as e:
                    log_in_arabic(logger, logging.ERROR, f"خطأ في تحميل عناصر الملحق {ext_id}: {str(e)}")
                    
            log_in_arabic(logger, logging.INFO, f"تم تحميل {loaded_count} عنصر من الملحقات")
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تحميل الملحقات: {str(e)}")
                
    def _add_view(self, extension_id: str, item: dict):
        try:
            if item.get('type') == 'separator':
                self.toolbar.addSeparator()
                return
                
            widget = item['widget']
            view_id = f"{extension_id}_{widget.__class__.__name__}_{id(widget)}"
            
            if view_id in self._views:
                log_in_arabic(logger, logging.DEBUG, f"العنصر موجود مسبقاً: {view_id}")
                return
                
            # إضافة العنصر للمحتوى
            self.content.addWidget(widget)
            widget.hide()
            
            # إضافة الفواصل
            if item.get('add_separator_before', False):
                self.toolbar.addSeparator()
            
            # إنشاء وإعداد الإجراء
            action = QAction(self.toolbar)
            if 'icon' in item:
                icon = item['icon']
                if isinstance(icon, str):
                    icon = self._load_icon(extension_id, icon)
                action.setIcon(icon)
                
            if 'tooltip' in item:
                action.setToolTip(item['tooltip'])
                
            action.setCheckable(True)
            action.triggered.connect(lambda checked, w=widget: self.view_changed.emit(w))
            self.toolbar.addAction(action)
            
            # تخزين العنصر
            self._views[view_id] = {
                'widget': widget,
                'action': action,
                'extension_id': extension_id
            }
            
            if item.get('add_separator_after', False):
                self.toolbar.addSeparator()
            
            # تحديد العنصر الأول كنشط
            if len(self._views) == 1:
                action.setChecked(True)
                self.view_changed.emit(widget)
                
            log_in_arabic(logger, logging.DEBUG, f"تم إضافة عنصر جديد: {view_id}")
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في إضافة العنصر: {str(e)}")
            
    def clear_views(self):
        try:
            if not self._views:
                return
                
            count = len(self._views)
            self.toolbar.clear()
            for view in self._views.values():
                if view['widget'].parent() == self.content:
                    self.content.removeWidget(view['widget'])
                    
            self._views.clear()
            self._current_widget = None
            log_in_arabic(logger, logging.INFO, f"تم مسح {count} عنصر من الشريط الجانبي")
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في مسح العناصر: {str(e)}")
        
    @pyqtSlot(QWidget)
    def _on_view_changed(self, widget: QWidget):
        try:
            if not widget or widget == self._current_widget:
                return
                
            for view in self._views.values():
                is_current = view['widget'] == widget
                view['action'].setChecked(is_current)
                view['widget'].setVisible(is_current)
                
            self._current_widget = widget
            self.content.setCurrentWidget(widget)
            log_in_arabic(logger, logging.DEBUG, f"تم تغيير العرض إلى: {widget.__class__.__name__}")
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تغيير العرض: {str(e)}")
        

    @pyqtSlot()
    def toggle_sidebar(self):
        try:
            is_visible = self.sidebar.isVisible()
            self.sidebar.setVisible(not is_visible)
            log_in_arabic(logger, logging.DEBUG, "تم إخفاء الشريط الجانبي" if is_visible else "تم إظهار الشريط الجانبي")
        except Exception as e:
            log_in_arabic(logger, logging.ERROR, f"خطأ في تبديل حالة الشريط الجانبي: {str(e)}")
