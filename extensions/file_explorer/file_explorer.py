from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeView, QLabel, 
                           QHBoxLayout, QPushButton, QToolButton, QBoxLayout, QStyle, QApplication, QMenu, QLineEdit, QMessageBox, QInputDialog, QProgressDialog, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QTimer, QAbstractItemModel, QModelIndex, QUrl, QMimeData, QFile, QIODevice, QPropertyAnimation, QObject, pyqtSignal, QItemSelectionModel
from PyQt5.QtGui import QIcon
import os
import shutil
from extensions.file_explorer.search_widget import SearchWidget
class FileSystemItem(QObject):
    def __init__(self, name, path, is_dir=False):
        super().__init__()
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.children = []
        self.parent = None
        self.icon = None
        self.loaded = False

class CustomFileSystemModel(QAbstractItemModel):
    itemDropped = pyqtSignal()
    
    def __init__(self, root_path, widget=None):
        super().__init__()
        self.widget = widget
        self.setup_icons()
        self.root_item = FileSystemItem("", root_path, True)
        self.root_item.icon = self.folder_icon
        self.load_children(self.root_item)
    
    def setup_icons(self):
        """تحميل الأيقونات"""
        try:
            extension_path = os.path.dirname(__file__)
            icons_path = os.path.join(extension_path, 'resources', 'icons')
            
            # تحميل الأيقونات المخصصة
            folder_icon_path = os.path.join(icons_path, 'folder.png')
            file_icon_path = os.path.join(icons_path, 'file.png')
            
            if os.path.exists(folder_icon_path):
                self.folder_icon = QIcon(folder_icon_path)
            else:
                # استخدام الأيقونات الافتراضية للنظام
                style = QApplication.style()
                self.folder_icon = style.standardIcon(QStyle.SP_DirIcon)
                
            if os.path.exists(file_icon_path):
                self.file_icon = QIcon(file_icon_path)
            else:
                # استخدام الأيقونات الافتراضية للنظام
                style = QApplication.style()
                self.file_icon = style.standardIcon(QStyle.SP_FileIcon)
                
        except Exception as e:
            print(f"خطأ في تحميل الأيقونات: {e}")
            # استخدام الأيقونات الافتراضية للنظام
            style = QApplication.style()
            self.folder_icon = style.standardIcon(QStyle.SP_DirIcon)
            self.file_icon = style.standardIcon(QStyle.SP_FileIcon)

    def load_children(self, item):
        """تحميل محتويات المجلد بشكل كسول"""
        if item.loaded:
            return
            
        try:
            if not os.path.isdir(item.path):
                return
            
            entries = os.listdir(item.path)
            # ترتيب العناصر: المجلدات أولاً ثم الملفات
            dirs = []
            files = []
            for entry in entries:
                full_path = os.path.join(item.path, entry)
                is_dir = os.path.isdir(full_path)
                child = FileSystemItem(entry, full_path, is_dir)
                child.parent = item
                child.icon = self.folder_icon if is_dir else self.file_icon
                
                if is_dir:
                    dirs.append(child)
                else:
                    files.append(child)
            
            # دمج المجلدات والملفات مع الحفاظ على الترتيب الأبجدي
            item.children = sorted(dirs, key=lambda x: x.name.lower()) + \
                           sorted(files, key=lambda x: x.name.lower())
            
            item.loaded = True
        except Exception as e:
            print(f"خطأ في تحميل المجلد {item.path}: {e}")

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.children[row]
        return self.createIndex(row, column, child_item)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if parent_item == self.root_item:
            return QModelIndex()

        # البحث عن موقع الأب في قائمة أطفال الجد
        if parent_item.parent:
            row = parent_item.parent.children.index(parent_item)
        else:
            row = 0

        return self.createIndex(row, 0, parent_item)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
            if not parent_item.loaded:
                self.load_children(parent_item)

        return len(parent_item.children)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DisplayRole:
            return item.name
        elif role == Qt.DecorationRole:
            return item.icon
        
        return None

    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return default_flags | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def mimeTypes(self):
        return ['text/uri-list']

    def mimeData(self, indexes):
        urls = []
        for index in indexes:
            if index.isValid():
                item = index.internalPointer()
                urls.append(QUrl.fromLocalFile(item.path))
                
        mimeData = QMimeData()
        mimeData.setUrls(urls)
        return mimeData

    def canDropMimeData(self, data, action, row, column, parent):
        return data.hasUrls()

    def dropMimeData(self, data, action, row, column, parent):
        if not data.hasUrls():
            return False

        if parent.isValid():
            target_item = parent.internalPointer()
            target_path = target_item.path if target_item.is_dir else os.path.dirname(target_item.path)
        else:
            target_path = self.root_item.path

        if self.widget:
            self.widget.handle_drop(data.urls(), target_path)
            self.itemDropped.emit()
        return True

class CollapsibleHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.is_collapsed = False
        
        # إعداد مؤقت لإخفاء الأزرار
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_buttons)
        
        # تطبيق ملف التنسيق
        style_path = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'explorer.qss')
        with open(style_path, 'r', encoding='utf-8') as style_file:
            self.setStyleSheet(style_file.read())
        
        # إخفاء الأزرار في البداية
        self.hide_buttons()

    def setup_ui(self):
        # الحاوية الرئيسية
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # حاوية العنوان
        title_container = QWidget()
        layout = QHBoxLayout(title_container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setDirection(QBoxLayout.RightToLeft)
                # تحديد مسار الأيقونات
        extension_path = os.path.dirname(__file__)
        icons_path = os.path.join(extension_path, 'resources', 'icons')
        
        # حاوية الأزرار
        self.buttons_widget = QWidget()
        self.buttons_widget.hide()  # إخفاء الأزرار في البداية
        self.action_buttons = QHBoxLayout(self.buttons_widget)
        self.action_buttons.setContentsMargins(0, 0, 0, 0)
        self.action_buttons.setSpacing(2)
        self.action_buttons.setDirection(QBoxLayout.RightToLeft)
        
        # إنشاء الأزرار
        self.search_btn = QToolButton()
        self.search_btn.setIcon(QIcon(os.path.join(icons_path, 'search.png')))
        self.search_btn.setToolTip("بحث")
        
        self.search_btn.clicked.connect(self.toggle_search)
        
        self.new_file_btn = QToolButton()
        self.new_file_btn.setIcon(QIcon(os.path.join(icons_path, 'new-file.png')))
        self.new_file_btn.setToolTip("ملف جديد")
        self.new_file_btn.clicked.connect(self.create_new_file_clicked)
        
        self.new_folder_btn = QToolButton()
        self.new_folder_btn.setIcon(QIcon(os.path.join(icons_path, 'new-folder.png')))
        self.new_folder_btn.setToolTip("مجلد جديد")
        self.new_folder_btn.clicked.connect(self.create_new_folder_clicked)
        
        self.refresh_btn = QToolButton()
        self.refresh_btn.setIcon(QIcon(os.path.join(icons_path, 'refresh.png')))
        self.refresh_btn.setToolTip("تحديث")
        self.refresh_btn.clicked.connect(self.refresh_clicked)
        
        # إضافة الأزرار
        self.action_buttons.addWidget(self.refresh_btn)
        self.action_buttons.addWidget(self.new_folder_btn)
        self.action_buttons.addWidget(self.new_file_btn)
        self.action_buttons.addWidget(self.search_btn)
        
        # زر التوسيع/الطي
        self.collapse_btn = QToolButton()
        self.collapse_btn.setIcon(QIcon(os.path.join(icons_path, 'chevron-down.png')))
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self.collapse_btn)
        
        self.title_label = QLabel("المستكشف")
        
        # إضافة العناصر للتخطيط
        layout.addWidget(self.buttons_widget)
        layout.addStretch()
        layout.addWidget(self.title_label)
        
        # إاوية البحث
        self.search_container = QWidget()
        search_layout = QHBoxLayout(self.search_container)
        search_layout.setContentsMargins(5, 2, 5, 2)
        search_layout.setSpacing(0)
        
        # إنشاء حقل البحث
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("بحث...")
        self.search_box.textChanged.connect(self.filter_items)
        
        search_layout.addWidget(self.search_box)
        self.search_container.hide()  # إخفاء حاوية البحث في البداية
        
        # إضافة الحاويات للتخطيط الرئيسي
        main_layout.addWidget(title_container)
        main_layout.addWidget(self.search_container)
        
        # إعداد التخطيط النهائي
        final_layout = QVBoxLayout(self)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.setSpacing(0)
        final_layout.addWidget(main_container)
        
        # إعداد مؤقت لإخفاء الأزرار
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_buttons)

    def create_new_file_clicked(self):
        """معالج النقر على زر إنشاء ملف جديد"""
        if hasattr(self.parent(), 'model') and hasattr(self.parent().model, 'root_item'):
            root_path = self.parent().model.root_item.path
            self.parent().create_new_file(root_path)

    def create_new_folder_clicked(self):
        """معالج النقر على زر إنشاء مجلد جديد"""
        if hasattr(self.parent(), 'model') and hasattr(self.parent().model, 'root_item'):
            root_path = self.parent().model.root_item.path
            self.parent().create_new_folder(root_path)

    def refresh_clicked(self):
        """معالج النقر على زر التحديث"""
        if hasattr(self.parent(), 'refresh_view'):
            self.parent().refresh_view()

    def enterEvent(self, event):
        """عند دخول المؤشر"""
        self.show_buttons()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """عند خروج المؤشر"""
        self.hide_timer.start(300)  # تأخير 300 مللي ثانية
        super().leaveEvent(event)

    def show_buttons(self):
        """إظهار الأزرار"""
        self.hide_timer.stop()
        self.buttons_widget.show()

    def hide_buttons(self):
        """إخفاء الأزرار"""
        self.buttons_widget.hide()


    def set_folder_name(self, name):
        self.title_label.setText(name)

    def toggle_search(self):
        """تبديل ظهور/إخفاء حقل البحث"""
        if self.search_container.isHidden():
            self.search_container.show()
            self.search_box.setFocus()
        else:
            self.search_container.hide()
            self.search_box.clear()

    def filter_items(self, text):
        """تصفية العناصر بناءً على نص البحث"""
        if hasattr(self.parent(), 'tree'):
            tree = self.parent().tree
            model = tree.model()
            if not model:
                return
                
            if not text:
                # إظهار كل العناصر
                self.show_all_items(tree.rootIndex())
            else:
                # إخفاء/إظهار العناصر حسب نص البحث
                self.filter_tree_items(tree.rootIndex(), text.lower())

    def show_all_items(self, parent):
        """إظهار جميع العناصر في الشجرة"""
        if not parent.isValid():
            return
            
        model = self.parent().tree.model()
        for row in range(model.rowCount(parent)):
            index = model.index(row, 0, parent)
            self.parent().tree.setRowHidden(row, parent, False)
            if model.hasChildren(index):
                self.show_all_items(index)

    def filter_tree_items(self, parent, text):
        """تصفية عناصر الشجرة بشكل تكراري"""
        if not parent.isValid():
            return
            
        model = self.parent().tree.model()
        for row in range(model.rowCount(parent)):
            index = model.index(row, 0, parent)
            item_text = model.data(index, Qt.DisplayRole).lower()
            
            # إظهار/إخفاء العنصر حسب نص البحث
            matches = text in item_text
            self.parent().tree.setRowHidden(row, parent, not matches)
            
            # البحث في العناصر الفرعية
            if model.hasChildren(index):
                self.filter_tree_items(index, text)

    def toggle_collapse(self):
        """تبديل حالة الطي/التوسيع"""
        self.is_collapsed = not self.is_collapsed
        
        # تغيير الأيقونة حسب الحالة
        icon_name = 'chevron-left.png' if self.is_collapsed else 'chevron-down.png'
        self.collapse_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'resources', 'icons', icon_name)))
        
        # إخفاء/إظهار شجرة الملفات
        if hasattr(self.parent(), 'tree'):
            self.parent().tree.setAnimated(True)
            self.parent().tree.setVisible(not self.is_collapsed)
            if self.is_collapsed:
                self.parent().setMaximumHeight(self.height())
            else:
                self.parent().setMaximumHeight(16777215)

class FileExplorerWidget(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setup_ui()
        
        # إعداد السحب والإفلات
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QTreeView.DragDrop)
        
        # إنشاء مؤشر التقدم للنقل
        self.progress_animation = None
        
        # ربط الإشارات
        self.tree.doubleClicked.connect(self.on_double_click)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # تطبيق ملف التنسيق
        style_path = os.path.join(os.path.dirname(__file__), 'resources', 'styles', 'explorer.qss')
        with open(style_path, 'r', encoding='utf-8') as style_file:
            self.setStyleSheet(style_file.read())

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.header = CollapsibleHeader(self)
        layout.addWidget(self.header)
        
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setLayoutDirection(Qt.RightToLeft)
        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.setIndentation(20)
        self.tree.setStyleSheet("""

            QTreeView::branch:has-siblings:adjoins-item {
                border-image: url(resources/icons/branch-more.png) 0;
            }
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url(resources/icons/branch-end.png) 0;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: none;
                image: url(resources/icons/chevron-left.png);
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none;
                image: url(resources/icons/chevron-down.png);
            }
        """)
        
        layout.addWidget(self.tree)
        self.tree.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree.expanded.connect(self.on_item_expanded)
        self.tree.collapsed.connect(self.on_item_collapsed)

    def set_folder(self, folder_path):
        """تعيين المجلد المفتوح"""
        try:
            self.model = CustomFileSystemModel(folder_path, self)
            self.tree.setModel(self.model)
            # التأكد من تعيين نموذج التحديد
            if not self.tree.selectionModel():
                self.tree.setSelectionModel(QItemSelectionModel(self.model))
            self.model.itemDropped.connect(self.refresh_view)
            folder_name = os.path.basename(folder_path)
            self.header.set_folder_name(folder_name)
        except Exception as e:
            QMessageBox.warning(
                self,
                'خطأ',
                f'فشل في تعيين المجلد: {str(e)}'
            )

    def show_context_menu(self, position):
        """عرض قائمة السياق"""
        # التحقق من وجود نموذج البيانات وselectionModel
        if not self.tree.model() or not self.tree.selectionModel():
            return
        
        try:
            index = self.tree.indexAt(position)
            selected_indexes = self.tree.selectionModel().selectedIndexes()
            
            # إنشاء القائمة
            menu = QMenu(self)
            
            # إضافة خيارات التحديد دائماً في بداية القائمة
            select_menu = menu.addMenu("تحديد")
            select_all = select_menu.addAction("تحديد الكل")
            select_all.triggered.connect(lambda: self.tree.selectAll())
            
            deselect_all = select_menu.addAction("إلغاء تحديد الكل")
            deselect_all.triggered.connect(lambda: self.tree.clearSelection())
            
            invert_selection = select_menu.addAction("عكس التحديد")
            invert_selection.triggered.connect(self.invert_selection)
            
            menu.addSeparator()

            if index.isValid():
                try:
                    item = index.internalPointer()
                    if not item or not hasattr(item, 'path'):
                        return
                    
                    if os.path.isfile(item.path):
                        open_action = menu.addAction("فتح")
                        open_containing = menu.addAction("فتح موقع الملف")
                        menu.addSeparator()
                    else:
                        open_containing = menu.addAction("فتح في المستكشف")
                        menu.addSeparator()
                    
                    # قائمة التحرير
                    cut_action = menu.addAction("قص")
                    copy_action = menu.addAction("نسخ")
                    paste_action = menu.addAction("لصق")
                    menu.addSeparator()
                    
                    rename_action = menu.addAction("إعادة تسمية")
                    delete_action = menu.addAction("حذف")
                    menu.addSeparator()
                    
                    if os.path.isdir(item.path):
                        new_file = menu.addAction("ملف جديد")
                        new_folder = menu.addAction("مجلد جديد")
                        menu.addSeparator()
                        
                        expand_all = menu.addAction("توسيع الكل")
                        collapse_all = menu.addAction("طي الكل")
                        menu.addSeparator()
                    
                    copy_path = menu.addAction("نسخ المسار")
                    
                    # تعطيل عملية اللصق إذا لم يكن هناك محتوى في الحافظة
                    paste_action.setEnabled(QApplication.clipboard().mimeData().hasUrls())
                    
                    action = menu.exec_(self.tree.viewport().mapToGlobal(position))
                    
                    if action:
                        if os.path.isfile(item.path) and action == open_action:
                            self.on_double_click(index)
                        elif action == open_containing:
                            self.open_containing_folder(item.path)
                        elif action == cut_action:
                            self.cut_items(selected_indexes if selected_indexes else [index])
                        elif action == copy_action:
                            self.copy_items(selected_indexes if selected_indexes else [index])
                        elif action == paste_action:
                            self.paste_items(item.path)
                        elif action == rename_action:
                            self.rename_item(index)
                        elif action == delete_action:
                            self.delete_items(selected_indexes if selected_indexes else [index])
                        elif action == copy_path:
                            QApplication.clipboard().setText(item.path)
                        elif os.path.isdir(item.path):
                            if action == new_file:
                                self.create_new_file(item.path)
                            elif action == new_folder:
                                self.create_new_folder(item.path)
                            elif action == expand_all:
                                self.tree.expandAll()
                            elif action == collapse_all:
                                self.tree.collapseAll()
                            
                except RuntimeError:
                    # تجاهل الأخطاء المتعلقة بالكائنات المحذوفة
                    return
                
            else:
                # قائمة عندما لا يتم تحديد أي عنصر
                new_file = menu.addAction("ملف جديد")
                new_folder = menu.addAction("مجلد جديد")
                paste_action = menu.addAction("لصق")
                menu.addSeparator()
                
                expand_all = menu.addAction("توسيع الكل")
                collapse_all = menu.addAction("طي الكل")
                menu.addSeparator()
                
                refresh_action = menu.addAction("تحديث")
                
                paste_action.setEnabled(QApplication.clipboard().mimeData().hasUrls())
                
                action = menu.exec_(self.tree.viewport().mapToGlobal(position))
                
                if action:
                    if action == new_file:
                        self.create_new_file(self.model.root_item.path)
                    elif action == new_folder:
                        self.create_new_folder(self.model.root_item.path)
                    elif action == paste_action:
                        self.paste_items(self.model.root_item.path)
                    elif action == refresh_action:
                        self.refresh_view()
                    elif action == expand_all:
                        self.tree.expandAll()
                    elif action == collapse_all:
                        self.tree.collapseAll()
                    
        except Exception as e:
            print(f"خطأ في عرض القائمة السياقية: {str(e)}")

    def open_containing_folder(self, path):
        """فتح المجلد الذي يحتوي على الملف في مستكشف النظام"""
        import subprocess
        import platform
        
        try:
            system = platform.system()
            
            if system == "Windows":
                # استخدام explorer.exe مع المسار الكامل
                path = os.path.normpath(path)  # تنسيق المسار للويندوز
                if os.path.isfile(path):
                    subprocess.run(['explorer', '/select,', path], shell=True)
                else:
                    subprocess.run(['explorer', path], shell=True)
                    
            elif system == "Darwin":  # macOS
                if os.path.isfile(path):
                    subprocess.run(['open', '-R', path])
                else:
                    subprocess.run(['open', path])
                    
            else:  # Linux
                # استخدام xdg-open للمجلد الحاوي
                if os.path.isfile(path):
                    path = os.path.dirname(path)
                
                # محاولة استخدام مستكشفات الملفات الشائعة
                file_managers = [
                    ['xdg-open', path],
                    ['nautilus', path],
                    ['dolphin', path],
                    ['nemo', path],
                    ['thunar', path]
                ]
                
                for fm in file_managers:
                    try:
                        subprocess.run(fm)
                        break
                    except FileNotFoundError:
                        continue
                        
        except Exception as e:
            QMessageBox.warning(
                self, 
                'خطأ',
                f'فشل فتح المجلد: {str(e)}\nالمسار: {path}'
            )

    def cut_items(self, indexes):
        """قص العناصر المحددة"""
        self.copy_items(indexes)
        self._cut_items = [index.internalPointer().path for index in indexes if index.internalPointer() and hasattr(index.internalPointer(), 'path')]

    def copy_items(self, indexes):
        """نسخ العناصر المحددة"""
        if not indexes:
            return
        
        # تجميع العناصر الصالحة
        valid_items = []
        for index in indexes:
            item = index.internalPointer()
            if item and hasattr(item, 'path') and os.path.exists(item.path):
                valid_items.append(item)
        
        if not valid_items:
            return
        
        try:
            # إنشاء قائمة URLs للعناصر الصالحة
            urls = [QUrl.fromLocalFile(item.path) for item in valid_items]
            mime_data = QMimeData()
            mime_data.setUrls(urls)
            QApplication.clipboard().setMimeData(mime_data)
            self._cut_items = []  # مسح قائمة العناصر المقصوصة
            
            # إظهار رسالة نجاح صغيرة
            if len(valid_items) == 1:
                self.show_status_message(f"تم نسخ: {valid_items[0].name}")
            else:
                self.show_status_message(f"تم نسخ {len(valid_items)} عنصر")
            
        except Exception as e:
            QMessageBox.warning(
                self,
                'خطأ في النسخ',
                f'حدث خطأ أثناء نسخ العناصر: {str(e)}'
            )

    def paste_items(self, target_path):
        """لصق العناصر من الحافظة"""
        mime_data = QApplication.clipboard().mimeData()
        if not mime_data.hasUrls():
            return
        
        try:
            for url in mime_data.urls():
                source_path = url.toLocalFile()
                if not os.path.exists(source_path):
                    continue
                
                basename = os.path.basename(source_path)
                destination = os.path.join(target_path, basename)
                
                # التحقق من وجود الملف
                if os.path.exists(destination):
                    reply = QMessageBox.question(
                        self,
                        'تأكيد',
                        f'الملف "{basename}" موجود بالفعل. هل تريد استبداله؟',
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        continue
                
                # نقل أو نسخ الملف
                if hasattr(self, '_cut_items') and source_path in self._cut_items:
                    shutil.move(source_path, destination)
                else:
                    if os.path.isdir(source_path):
                        shutil.copytree(source_path, destination, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source_path, destination)
            
            # مسح قائمة العناصر المقصوصة بعد النقل
            if hasattr(self, '_cut_items'):
                self._cut_items = []
            
            self.refresh_view()
            
        except Exception as e:
            QMessageBox.warning(self, 'خطأ', f'فشل نقل/نسخ الملفات: {str(e)}')

    def rename_item(self, index):
        """إعادة تسمية عنصر"""
        if not index.isValid():
            return
            
        item = index.internalPointer()
        if not item or not hasattr(item, 'path'):
            return
        
        old_name = item.name
        new_name, ok = QInputDialog.getText(
            self, 
            'إعادة تسمية',
            'الاسم الجديد:',
            text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            try:
                old_path = item.path
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                
                # التحقق من وجود الملف
                if os.path.exists(new_path):
                    reply = QMessageBox.question(
                        self,
                        'تأكيد',
                        'الملف موجود بالفعل. هل تريد استبداله؟',
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
                
                os.rename(old_path, new_path)
                self.refresh_view()
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    'خطأ',
                    f'فشل إعادة التسمية: {str(e)}'
                )

    def delete_items(self, indexes):
        """حذف عنصر أو مجموعة عناصر"""
        if not indexes:
            return
        
        # تجميع العناصر الصالحة للحذف
        items = []
        errors = []
        
        for index in indexes:
            item = index.internalPointer()
            if item and hasattr(item, 'path'):
                try:
                    # التحقق من وجود الملف قبل إضافته للقائمة
                    if os.path.exists(item.path):
                        items.append(item)
                    else:
                        errors.append(f"الملف غير موجود: {item.name}")
                except Exception as e:
                    errors.append(f"خطأ في الوصول للملف {item.name}: {str(e)}")
        
        if not items:
            if errors:
                QMessageBox.warning(
                    self,
                    'خطأ في الحذف',
                    "لا يمكن حذف الملفات:\n" + "\n".join(errors)
                )
            return
        
        # إعداد رسالة التأكيد
        if len(items) == 1:
            message = f'هل أنت متأكد من حذف "{items[0].name}"؟'
        else:
            items_str = "\n".join([f"- {item.name}" for item in items[:10]])
            if len(items) > 10:
                items_str += f"\n... و {len(items) - 10} عناصر أخرى"
            message = f'هل أنت متأكد من حذف العناصر التالية؟\n\n{items_str}'
        
        reply = QMessageBox.question(
            self,
            'تأكيد الحذف',
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # إنشاء نافذة التقدم فقط إذا كان هناك أكثر من عنصر
            progress = None
            if len(items) > 1:
                progress = QProgressDialog(
                    "جاري حذف العناصر...",
                    "إلغاء",
                    0,
                    len(items),
                    self
                )
                progress.setWindowModality(Qt.WindowModal)
                progress.setMinimumDuration(0)
            
            deleted_count = 0
            delete_errors = []
            
            try:
                for i, item in enumerate(items):
                    if progress and progress.wasCanceled():
                        break
                    
                    if progress:
                        progress.setLabelText(f"جاري حذف: {item.name}")
                    
                    try:
                        # التحقق مرة أخرى من وجود الملف قبل الحذف
                        if not os.path.exists(item.path):
                            delete_errors.append(f"الملف غير موجود: {item.name}")
                            continue
                        
                        if os.path.isdir(item.path):
                            shutil.rmtree(item.path)
                        else:
                            os.remove(item.path)
                        deleted_count += 1
                    except PermissionError:
                        delete_errors.append(f"لا توجد صلاحيات كافية لحذف: {item.name}")
                    except Exception as e:
                        delete_errors.append(f"فشل حذف {item.name}: {str(e)}")
                    
                    if progress:
                        progress.setValue(i + 1)
                        QApplication.processEvents()
                    
            finally:
                if progress:
                    progress.close()
                
                # تحديث العرض وإظهار النتيجة
                if deleted_count > 0:
                    self.refresh_view()
                    if deleted_count == len(items):
                        self.show_status_message(f"تم حذف {deleted_count} من {len(items)} عنصر")
                    elif len(items) > 1:
                        self.show_status_message(f"تم حذف {deleted_count} من {len(items)} عنصر")
                
                # عرض الأخطاء إن وجدت
                if delete_errors:
                    error_message = "\n".join(delete_errors)
                    self.show_status_message(f"حدثت الأخطاء التالية:\n{error_message}")

    def filter_items(self, text):
        if not text:
            # إظهار كل العناصر
            for i in range(self.tree.model().rowCount()):
                self.tree.setRowHidden(i, QModelIndex(), False)
            return
            
        # البحث في العناصر
        for i in range(self.tree.model().rowCount()):
            index = self.tree.model().index(i, 0)
            item = self.tree.model().data(index, Qt.DisplayRole)
            if text.lower() in item.lower():
                self.tree.setRowHidden(i, QModelIndex(), False)
            else:
                self.tree.setRowHidden(i, QModelIndex(), True)

    def refresh_view(self):
        """تحديث عرض شجرة الملفات"""
        try:
            if hasattr(self, 'model') and self.model:
                current_path = self.model.root_item.path
                if os.path.exists(current_path):
                    self.set_folder(current_path)
                else:
                    QMessageBox.warning(
                        self,
                        'خطأ',
                        f'المجلد غير موجود: {current_path}'
                    )
        except Exception as e:
            QMessageBox.warning(
                self,
                'خطأ في التحديث',
                f'حدث خطأ أثناء تحديث العرض: {str(e)}'
            )
    
    def iter_items(self):
        """تكرار جميع العناصر في النموذج"""
        def recurse(parent):
            for row in range(self.model.rowCount(parent)):
                index = self.model.index(row, 0, parent)
                yield index
                if self.model.hasChildren(index):
                    yield from recurse(index)
        
        yield from recurse(QModelIndex())

    def on_double_click(self, index):
        """معالجة النقر المزدوج على عنصر"""
        if not index.isValid():
            return
        
        item = index.internalPointer()
        if item and hasattr(item, 'path'):
            try:
                if os.path.isfile(item.path):
                    # فتح الملف في المحرر
                    self.editor.tab_manager.open_file(item.path)
                    
                elif os.path.isdir(item.path):
                    current_state = self.tree.isExpanded(index)
                    self.tree.setExpanded(index, not current_state)
                    
                    if not current_state:
                        model = self.tree.model()
                        if hasattr(model, 'load_children'):
                            model.load_children(item)
                            
            except Exception as e:
                QMessageBox.warning(self, 'خطأ', f'حدث خطأ أثناء فتح العنصر: {str(e)}')

    def create_new_file(self, parent_path):
        """إنشاء ملف جديد بنمط   """
        name, ok = QInputDialog.getText(self, 'ملف جديد', 'اسم الملف أو المسار:')
        if ok and name:
            try:
                # معالجة المسار المتداخل
                file_path = os.path.join(parent_path, name)
                
                # إنشاء المجلدات الوسيطة إذا كانت موجودة في المسار
                directory = os.path.dirname(file_path)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                
                # التحقق من وجود الملف
                if os.path.exists(file_path):
                    reply = QMessageBox.question(
                        self,
                        'تأكيد',
                        'الملف موجود بالفعل. هل تريد استبداله؟',
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
                
                # إنشاء الملف مع معالجة الامتدادات المختلفة
                with open(file_path, 'w', encoding='utf-8') as f:
                    # إضافة محتوى اتراضي حسب نوع الملف
                    extension = os.path.splitext(file_path)[1].lower()
                    if extension == '.html':
                        f.write('<!DOCTYPE html>\n<html>\n<head>\n    <title></title>\n</head>\n<body>\n\n</body>\n</html>')
                    elif extension == '.py':
                        f.write('#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\n')
                    elif extension == '.js':
                        f.write('// JavaScript\n')
                    elif extension == '.css':
                        f.write('/* CSS */\n')
                
                # تحديث العرض
                self.refresh_view()
                
                # فتح الملف الجديد في المحرر
                self.editor.tab_manager.new_tab(file_path)
                
            except Exception as e:
                QMessageBox.warning(self, 'خطأ', f'فشل إنشاء الملف: {str(e)}')

    def create_new_folder(self, parent_path):
        """إنشاء مجلد جديد بنمط   """
        name, ok = QInputDialog.getText(self, 'مجلد جديد', 'اسم المجلد أو المسار:')
        if ok and name:
            try:
                # معالة المسار المتداخل
                folder_path = os.path.join(parent_path, name)
                
                # التحقق من وجود المجلد
                if os.path.exists(folder_path):
                    reply = QMessageBox.question(
                        self,
                        'تأكيد',
                        'المجلد موجود بالفعل. هل تريد استبداله؟',
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
                    elif reply == QMessageBox.Yes:
                        import shutil
                        shutil.rmtree(folder_path)
                
                # إنشاء المجلد والمجلدات الوسيطة
                os.makedirs(folder_path)
                
                # تحديث العرض
                self.refresh_view()
                
            except Exception as e:
                QMessageBox.warning(self, 'خطأ', f'فشل إنشاء المجلد: {str(e)}')

    def toggle_search(self):
        """تبديل ظهور/إخفاء حقل البحث"""
        if self.search_box.isHidden():
            self.search_box.show()
            self.search_box.setFocus()
        else:
            self.search_box.hide()
            self.search_box.clear()  # مسح محتوى البحث عند الإخفاء

    def on_item_expanded(self, index):
        """معالجة توسيع المجلد"""
        if not index.isValid():
            return
        
        item = index.internalPointer()
        if item and hasattr(item, 'path') and os.path.isdir(item.path):
            # تحميل محتويات المجلد إذا لم تكن محملة
            model = self.tree.model()
            if hasattr(model, 'load_children'):
                model.load_children(item)

    def on_item_collapsed(self, index):
        """معالجة طي المجلد"""
        if not index.isValid():
            return
        
        model = self.tree.model()
        if not model:
            return
        
        try:
            # تجنب الوصول المباشر للكائن
            row = index.row()
            parent = index.parent()
            
            # إعادة إنشاء المؤشر
            new_index = model.index(row, 0, parent)
            if not new_index.isValid():
                return
            
            # تحديث النموذج
            model.beginResetModel()
            try:
                item = new_index.internalPointer()
                if item and hasattr(item, 'loaded'):
                    item.loaded = False
                    item.children = []
            except:
                pass
            finally:
                model.endResetModel()
            
        except Exception as e:
            print(f"خطأ في معالجة طي المجلد: {str(e)}")
            return

    def reset_loaded_state(self, item):
        """إعادة تعيين حالة التحميل للمجلد وجميع أطفاله بشكل تكراري"""
        try:
            if not item:
                return
            
            if hasattr(item, 'loaded'):
                item.loaded = False
            
            if hasattr(item, 'children'):
                for child in item.children:
                    try:
                        if child and hasattr(child, 'is_dir') and child.is_dir:
                            self.reset_loaded_state(child)
                    except RuntimeError:
                        continue
                    
        except RuntimeError:
            # الكائن تم حذفه
            return

    def dragEnterEvent(self, event):
        """معالجة بدء السحب"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # إضافة تأثير بصري عند السحب
            self.tree.setStyleSheet(self.tree.styleSheet() + """
                QTreeView {
                    border: 2px dashed #308cc6;
                }
            """)

    def dragLeaveEvent(self, event):
        """معالجة مغادرة السحب"""
        # إزالة التأثير البصري
        self.tree.setStyleSheet(self.tree.styleSheet().replace("""
                QTreeView {
                    border: 2px dashed #308cc6;
                }
            """, ""))

    def dropEvent(self, event):
        """معالجة الإفلات"""
        if event.mimeData().hasUrls():
            # إزالة التأثير البصري
            self.dragLeaveEvent(event)
            
            urls = event.mimeData().urls()
            drop_index = self.tree.indexAt(event.pos())
            
            if drop_index.isValid():
                target_item = drop_index.internalPointer()
                target_path = target_item.path if target_item.is_dir else os.path.dirname(target_item.path)
            else:
                # إذا تم الإفلات في منطقة فارغة، استخدم المجلد الجذر
                target_path = self.model.root_item.path if hasattr(self, 'model') else ""
            
            self.handle_drop(urls, target_path)
            event.acceptProposedAction()

    def handle_drop(self, urls, target_path):
        """معالجة عملية النقل/النسخ"""
        if not target_path or not urls:
            return
            
        total_files = len(urls)
        processed_files = 0
        
        # إنشاء نافذة التقدم
        progress = QProgressDialog("جاري نقل الملفات...", "إلغاء", 0, total_files, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            for url in urls:
                if progress.wasCanceled():
                    break
                    
                source_path = url.toLocalFile()
                if not os.path.exists(source_path):
                    continue
                    
                basename = os.path.basename(source_path)
                destination = os.path.join(target_path, basename)
                
                if os.path.exists(destination):
                    reply = QMessageBox.question(
                        self,
                        'تأكيد',
                        f'الملف "{basename}" موجود بالفعل. هل تريد استبداله؟',
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        continue
                
                try:
                    if os.path.isdir(source_path):
                        shutil.copytree(source_path, destination, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source_path, destination)
                    
                    processed_files += 1
                    progress.setValue(processed_files)
                    
                except Exception as e:
                    QMessageBox.warning(self, 'خطأ', f'فشل نقل/نسخ الملف {basename}: {str(e)}')
            

                
        finally:
            progress.close()
            self.refresh_view()

    def invert_selection(self):
        """عكس التحديد الحالي"""
        model = self.tree.model()
        if not model:
            return
        
        selection_model = self.tree.selectionModel()
        if not selection_model:
            return
        
        # الحصول على كل العناصر في النموذج
        all_indexes = []
        def collect_indexes(parent=QModelIndex()):
            for row in range(model.rowCount(parent)):
                index = model.index(row, 0, parent)
                all_indexes.append(index)
                if model.hasChildren(index):
                    collect_indexes(index)
        
        collect_indexes()
        
        # عكس التحديد لكل عنصر
        for index in all_indexes:
            if selection_model.isSelected(index):
                selection_model.select(index, QItemSelectionModel.Deselect)
            else:
                selection_model.select(index, QItemSelectionModel.Select)

    def delete_multiple_items(self, indexes):
        """حذف مجموعة من العناصر المحددة"""
        items = [index.internalPointer() for index in indexes]
        items_count = len(items)
        
        # رسالة تأكيد مع عدد العناصر
        reply = QMessageBox.question(
            self,
            'تأكيد الحذف الجماعي',
            f'هل أنت متأكد من حذف {items_count} عنصر؟',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # إنشاء نافذة تقدم العملية
            progress = QProgressDialog(
                "جاري حذف العناصر...",
                "إلغاء",
                0,
                items_count,
                self
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            deleted_count = 0
            errors = []
            
            try:
                for i, item in enumerate(items):
                    if progress.wasCanceled():
                        break
                        
                    try:
                        if os.path.isdir(item.path):
                            shutil.rmtree(item.path)
                        else:
                            os.remove(item.path)
                        deleted_count += 1
                    except Exception as e:
                        errors.append(f"فشل حذف {item.name}: {str(e)}")
                        
                    progress.setValue(i + 1)
                    
            finally:
                progress.close()
                
                # عرض نتيجة العملية
                if deleted_count > 0:
                    self.refresh_view()
                    if deleted_count == items_count:
                        self.show_status_message(f'تم حذف {deleted_count} من {items_count} عنصر')
                    else:
                        self.show_status_message(f'تم حذف {deleted_count} من {items_count} عنصر')
                
                # عرض الأخطاء إن وجدت
                if errors:
                    error_message = "\n".join(errors)
                    self.show_status_message(f'حدثت الأخطاء التالية:\n{error_message}')

    def cut_multiple_items(self, indexes):
        """قص مجموعة من العناصر المحددة"""
        items = [index.internalPointer() for index in indexes]
        self.copy_multiple_items(indexes)
        self._cut_items = [item.path for item in items]

    def copy_multiple_items(self, indexes):
        """نسخ مجموعة من العناصر المحددة"""
        items = [index.internalPointer() for index in indexes]
        urls = [QUrl.fromLocalFile(item.path) for item in items]
        mime_data = QMimeData()
        mime_data.setUrls(urls)
        QApplication.clipboard().setMimeData(mime_data)
        self._cut_items = []  # مسح قائمة العناصر المقصوصة

    def show_status_message(self, message, duration=2000):
        """إظهار رسالة حالة مؤقتة"""
        status_label = QLabel(message, self)
        status_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        status_label.adjustSize()
        
        # وضع الرسالة في أسفل النافذة
        pos = self.rect().bottomRight()
        status_label.move(
            pos.x() - status_label.width() - 10,
            pos.y() - status_label.height() - 10
        )
        status_label.show()
        
        # إخفاء الرسالة بعد المدة المحددة
        QTimer.singleShot(duration, status_label.deleteLater)

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.explorer = FileExplorerWidget(editor)
        self.search = SearchWidget(editor)
    def get_sidebar_items(self):
        return [{
            'widget': self.explorer,
            'icon': 'folder.png',
            'tooltip': 'مستكشف الملفات'
        },
        {
            'widget': self.search,
            'icon': 'resources/icons/search.png',
            'tooltip': 'البحث'
        }]
        
    def on_folder_open(self, folder_path):
        """معالجة فتح مجلد جديد"""
        self.editor.current_folder = folder_path
        self.explorer.set_folder(folder_path)