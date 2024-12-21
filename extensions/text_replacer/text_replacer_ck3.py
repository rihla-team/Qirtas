from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog, QMessageBox , QAction

import re
import os

class TextReplacerExtension:
    def __init__(self, editor):
        self.editor = editor
        self.setup_action()

    def setup_action(self):
        action = QAction('استبدال النصوص', self.editor)
        action.triggered.connect(self.show_dialog)
        self.editor.addAction(action)

    def show_dialog(self):
        dialog = QDialog(self.editor)
        dialog.setWindowTitle("استبدال النصوص")
        layout = QVBoxLayout(dialog)

        # منطقة النصوص
        layout.addWidget(QLabel("ألصق النصوص هنا:"))
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        # زر تحميل الملف
        load_btn = QPushButton("تحميل ملف")
        load_btn.clicked.connect(self.load_file)
        layout.addWidget(load_btn)

        # زر استبدال النصوص
        replace_btn = QPushButton("استبدال النصوص")
        replace_btn.clicked.connect(self.replace_texts)
        layout.addWidget(replace_btn)

        dialog.setLayout(layout)
        dialog.resize(600, 400)
        dialog.exec_()

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self.editor, "اختر ملف")
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.text_edit.setPlainText(content)

    def replace_texts(self):
        """استبدال النصوص في المحرر"""
        new_texts = self.text_edit.toPlainText()
        new_dict = self.parse_texts(new_texts)
        
        
        if not new_dict:
            QMessageBox.warning(
                self.editor,
                "تحذير",
                "لم يتم العثور على أي نصوص صالحة للاستبدال"
            )
            return

        current_editor = self.editor.get_current_editor()
        if not current_editor:
            return

        original_text = current_editor.toPlainText()
        original_lines = original_text.splitlines()
        replaced_count = 0
        
        failed_replacements = []
        replaced_keys = set()

        # استبدال القيم
        replaced_lines = []
        for line_number, line in enumerate(original_lines, 1):
            if not line.strip() or line.strip().startswith('#'):
                replaced_lines.append(line)
                continue
            
            # تحديث النمط ليتطابق مع أي رقم
            match = re.match(r'^(\s*)([\w-]+(?::\d+)?|[\w-]+:)(\s*)"([^"]+)"(.*)$', line)
            if match:
                spaces_before = match.group(1)
                key = match.group(2)
                spaces_mid = match.group(3)
                old_value = match.group(4)
                rest = match.group(5)
                
                search_key = key
                if ':' in key:
                    if not re.search(r':\d+$', key):
                        # إذا كان المعرف ينتهي بـ : فقط، نضيف 0
                        base_key = key.rstrip(':')
                        search_key = f"{base_key}:0"
                else:
                    # إذا لم يكن هناك : على الإطلاق
                    search_key = f"{key}:0"
                
                if search_key in new_dict:
                    if not re.search(r':\d+$', key):
                        key = search_key
                    new_line = f'{spaces_before}{key}{spaces_mid}"{new_dict[search_key]}"{rest}'
                    replaced_lines.append(new_line)
                    replaced_count += 1
                    replaced_keys.add(search_key)
                else:
                    # نحاول البحث عن المعرف مع أي رقم
                    base_key = key.split(':')[0] if ':' in key else key
                    for dict_key in new_dict:
                        if dict_key.startswith(f"{base_key}:"):
                            new_line = f'{spaces_before}{dict_key}{spaces_mid}"{new_dict[dict_key]}"{rest}'
                            replaced_lines.append(new_line)
                            replaced_count += 1
                            replaced_keys.add(dict_key)
                            break
                    else:
                        replaced_lines.append(line)
            else:
                replaced_lines.append(line)

        # التحقق من المعرفات التي لم يتم استبدالها
        for key, value in new_dict.items():
            if key not in replaced_keys:
                failed_replacements.append({
                    'key': key,
                    'value': value,
                    'reason': 'لم يتم العثور على المعرف في الملف الأصلي'
                })

        # إعادة بناء النص وإنشاء التقرير
        replaced_text = '\n'.join(replaced_lines)
        current_editor.setPlainText(replaced_text)
        
        if failed_replacements:
            report_path = os.path.join(os.path.dirname(__file__), 'failed_replacements_report.txt')
            try:
                with open(report_path, 'w', encoding='utf-8') as report_file:
                    report_file.write("تقرير المعرفات التي فشل استبدالها:\n")
                    report_file.write("=====================================\n\n")
                    for item in failed_replacements:
                        report_file.write(f"المعرف: {item['key']}\n")
                        report_file.write(f"القيمة: {item['value']}\n")
                        report_file.write(f"السبب: {item['reason']}\n")
                        report_file.write("-------------------------------------\n")
                
                message = f"تم استبدال {replaced_count} من النصوص بنجاح\n"
                message += f"فشل استبدال {len(failed_replacements)} معرف من النصوص الملصقة\n"
                message += f"يمكنك مراجعة التقرير في:\n{report_path}"
                
                QMessageBox.information(self.editor, "تم", message)
            except Exception as e:
                QMessageBox.warning(
                    self.editor,
                    "تحذير",
                    f"تم استبدال النصوص بنجاح لكن حدث خطأ أثناء إنشاء التقرير: {str(e)}"
                )
        else:
            QMessageBox.information(
                self.editor, 
                "تم",
                f"تم استبدال {replaced_count} من النصوص بنجاح"
            )

    def parse_texts(self, text):
        """تحليل النصوص واستخراج المعرفات والقيم"""
        result = {}
        lines = text.splitlines()
        
        for line in lines:
            # تجاهل الأسطر الفارغة والتعليقات
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # تحديث النمط ليشمل أي رقم بعد النقطتين
            match = re.search(r'([\w-]+:\d+)\s*"([^"]+)"', line)
            if match:
                key = match.group(1)  # نحتفظ بالمعرف كاملاً مع الرقم
                value = match.group(2)
                result[key] = value
                continue
            
            # النمط الثاني للمعرفات بدون رقم
            match = re.search(r'([\w-]+):\s*"([^"]+)"', line)
            if match:
                key = match.group(1)
                value = match.group(2)
                # نضيف :0 فقط إذا لم يكن هناك رقم
                result[f"{key}:0"] = value
                
        return result

class Extension:
    def __init__(self, editor):
        self.editor = editor
        self.text_replacer_extension = TextReplacerExtension(editor)

    def get_menu_items(self):
        return [
            {'name': 'استبدال النصوص', 'callback': self.text_replacer_extension.show_dialog}
        ] 
        
    def get_shortcuts(self):
        return [
            {'shortcut': 'Ctrl+Shift+Q', 'callback': self.text_replacer_extension.show_dialog}
        ]
