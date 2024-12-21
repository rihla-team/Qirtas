import sys
import os
import shutil
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                            QHeaderView, QStyle, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

class BackupManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.source_path = r"G:\My File\Lub\3- مشاريع\1 -  فريق رحله\2- ادوات الفريق\الكود المصدري\3- محرر رحلة"
        self.backup_path = r"G:\My File\Lub\3- مشاريع\1 -  فريق رحله\2- ادوات الفريق\الكود المصدري\نسخ احتياطي\3- محرر رحلة"
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("مدير النسخ الاحتياطي - محرر رحلة")
        self.setGeometry(100, 100, 800, 600)
        
        # إنشاء الويدجت الرئيسي
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # إنشاء زر النسخ الاحتياطي
        self.backup_button = QPushButton("إنشاء نسخة احتياطية جديدة")
        self.backup_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.backup_button.clicked.connect(self.create_backup)
        
        # إنشاء جدول النسخ الاحتياطية
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["رقم النسخة", "التاريخ", "الحجم", "عدد الملفات", "المسار"])
        
        # تعديل عرض الأعمدة
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # رقم النسخة
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # التاريخ
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # الحجم
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # عدد الملفات
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # المسار
        
        # تعديل نمط الجدول
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #3498db;
                border: none;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #2c3e50;
            }
        """)
        
        # تطبيق النمط الداكن
        self.apply_dark_theme()
        
        # إضافة الويدجت إلى التخطيط
        layout.addWidget(self.backup_button)
        layout.addWidget(self.table)
        main_widget.setLayout(layout)
        
        # تحديث قائمة النسخ الاحتياطية
        self.update_backup_list()
        
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QTableWidget {
                background-color: #34495e;
                color: white;
                gridline-color: #7f8c8d;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 5px;
                border: 1px solid #7f8c8d;
            }
            QLabel {
                color: white;
            }
        """)
        
    def get_folder_size(self, folder_path):
        total_size = 0
        file_count = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
                file_count += 1
        return total_size, file_count
        
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
        
    def update_backup_list(self):
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)
            
        folders = [d for d in os.listdir(self.backup_path) 
                if os.path.isdir(os.path.join(self.backup_path, d))]
        
        # ترتيب المجلدات بناءً على رقم النسخة بشكل تصاعدي
        folders.sort(key=lambda x: int(x.split('-')[0]) if x.split('-')[0].isdigit() else 0, reverse=False)
        
        self.table.setRowCount(len(folders))
        
        for row, folder in enumerate(folders):
            folder_path = os.path.join(self.backup_path, folder)
            size, file_count = self.get_folder_size(folder_path)
            
            try:
                backup_num = folder.split('-')[0]
                date_str = '-'.join(folder.split('-')[1:])
                
                # إنشاء عناصر الجدول
                num_item = QTableWidgetItem(str(backup_num))
                date_item = QTableWidgetItem(date_str)
                size_item = QTableWidgetItem(self.format_size(size))
                files_item = QTableWidgetItem(str(file_count))
                path_item = QTableWidgetItem(folder_path)
                
                # محاذاة النص إلى اليمين
                num_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                date_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                files_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                path_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # إضافة العناصر إلى ا��جدول
                self.table.setItem(row, 0, num_item)
                self.table.setItem(row, 1, date_item)
                self.table.setItem(row, 2, size_item)
                self.table.setItem(row, 3, files_item)
                self.table.setItem(row, 4, path_item)
                
            except Exception as e:
                print(f"خطأ في معالجة المجلد {folder}: {str(e)}")
            
    def get_next_backup_number(self):
        folders = [d for d in os.listdir(self.backup_path) 
                  if os.path.isdir(os.path.join(self.backup_path, d))]
        
        numbers = []
        for folder in folders:
            try:
                num = int(folder.split('-')[0])
                numbers.append(num)
            except:
                continue
                
        return max(numbers) + 1 if numbers else 1
        
    def create_backup(self):
        try:
            next_number = self.get_next_backup_number()
            current_time = datetime.datetime.now()
            folder_name = f"{next_number}-{current_time.strftime('%Y_%m_%d_%H_%M')}"
            new_backup_path = os.path.join(self.backup_path, folder_name)
            
            shutil.copytree(self.source_path, new_backup_path)
            
            self.update_backup_list()
            
            QMessageBox.information(
                self,
                "نجاح",
                f"تم إنشاء النسخة الاحتياطية رقم {next_number} بنجاح"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ أثناء إنشاء النسخة الاحتياطية:\n{str(e)}"
            )

def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    window = BackupManager()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()