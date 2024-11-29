from PyQt5.QtWidgets import (QDockWidget, QTreeView, QFileSystemModel, 
                           QMenu, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QDir
import os, shutil

class ProjectManagerWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("مدير المشاريع", parent)
        self.editor = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.tree = QTreeView()
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        
        # إعداد عرض الملفات
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(""))
        self.tree.setColumnWidth(0, 250)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.doubleClicked.connect(self.open_file)
        
        self.setWidget(self.tree)
    
    def open_file(self, index):
        """فتح الملف المحدد في المحرر"""
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            try:
                # التحقق من نوع الملف
                if file_path.endswith(('.py', '.txt', '.md', '.json')):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # التحقق من وجود دالة فتح التبويب
                    if hasattr(self.editor, 'create_new_tab'):
                        self.editor.create_new_tab(file_path, content)
                    elif hasattr(self.editor, 'open_file'):
                        self.editor.open_file(file_path)
                    else:
                        QMessageBox.critical(
                            self,
                            "خطأ",
                            "لا يمكن فتح الملف: الدالة غير موجودة"
                        )
                else:
                    QMessageBox.warning(
                        self,
                        "تنبيه",
                        "نوع الملف غير مدعوم"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    f"حدث خطأ أثناء فتح الملف:\n{str(e)}"
                )

    def show_context_menu(self, position):
        """عرض القائمة السياقية"""
        menu = QMenu()
        
        # الحصول على المسار المحدد
        index = self.tree.indexAt(position)
        file_path = self.model.filePath(index)
        
        # إضافة خيارات القائمة
        new_file = menu.addAction("ملف جديد")
        new_folder = menu.addAction("مجلد جديد")
        menu.addSeparator()
        rename = menu.addAction("إعادة تسمية")
        delete = menu.addAction("حذف")
        
        # تنفيذ الإجراء المحدد
        action = menu.exec_(self.tree.viewport().mapToGlobal(position))
        
        if action == new_file:
            self.create_new_file(file_path)
        elif action == new_folder:
            self.create_new_folder(file_path)
        elif action == rename:
            self.rename_item(file_path)
        elif action == delete:
            self.delete_item(file_path)
            
    def create_new_file(self, path):
        """إنشاء ملف جديد"""
        name, ok = QInputDialog.getText(self, "ملف جديد", "اسم الملف:")
        if ok and name:
            file_path = os.path.join(path, name)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل إنشاء الملف:\n{str(e)}")
                
    def create_new_folder(self, path):
        """إنشاء مجلد جديد"""
        name, ok = QInputDialog.getText(self, "مجلد جديد", "اسم المجلد:")
        if ok and name:
            try:
                os.makedirs(os.path.join(path, name))
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل إنشاء المجلد:\n{str(e)}")
                
    def rename_item(self, path):
        """إعادة تسمية عنصر"""
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(
            self, 
            "إعادة تسمية",
            "الاسم الجديد:",
            text=old_name
        )
        if ok and new_name:
            try:
                new_path = os.path.join(os.path.dirname(path), new_name)
                os.rename(path, new_path)
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل إعادة التسمية:\n{str(e)}")
                
    def delete_item(self, path):
        """حذف عنصر"""
        msg = "هل أنت متأكد من حذف هذا العنصر؟"
        if QMessageBox.question(self, "تأكيد الحذف", msg) == QMessageBox.Yes:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{str(e)}")

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.project_manager = None
        
    def get_menu_items(self):
        return [{
            'name': 'عرض مدير المشاريع',
            'callback': self.toggle_project_manager
        }]
        
    def toggle_project_manager(self):
        if not self.project_manager:
            self.project_manager = ProjectManagerWidget(self.editor)
            self.editor.addDockWidget(Qt.LeftDockWidgetArea, self.project_manager)
        else:
            self.project_manager.setVisible(not self.project_manager.isVisible())