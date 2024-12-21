from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                           QTreeWidget, QTreeWidgetItem, QLabel, QPushButton,
                           QToolButton, QProgressBar, QMenu, QMessageBox, QApplication, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt5.QtGui import QIcon, QColor, QDesktopServices
import os

class SearchThread(QThread):
    """فئة للبحث في خلفية البرنامج"""
    result_found = pyqtSignal(str, int, str, str)  # المسار، رقم السطر، النص، السياق
    finished = pyqtSignal()
    progress = pyqtSignal(int)  # للتقدم

    def __init__(self, root_path, search_text, options=None):
        super().__init__()
        self.root_path = root_path
        self.search_text = search_text
        self.options = options or {}
        self.running = True
        
        # قائمة المجلدات المتجاهلة
        self.ignored_dirs = set()  # مجموعة فارغة

    def stop(self):
        self.running = False

    def _is_text_file(self, file_path):
        """التحقق مما إذا كان الملف نصياً"""
        try:
            # قراءة أول 1024 بايت من الملف
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                
            # محاولة فك ترميز البيانات كنص
            chunk.decode('utf-8')
            return True
        except:
            return False

    def run(self):
        try:
            print(f"بدء البحث عن: {self.search_text} في {self.root_path}")
            
            for root, dirs, files in os.walk(self.root_path):
                if not self.running:
                    break
                    
                # تجاهل المجلدات المحددة
                dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
                
                for file in files:
                    if not self.running:
                        break
                        
                    try:
                        file_path = os.path.join(root, file)
                        
                        # تجاهل الملفات غير النصية
                        if not self._is_text_file(file_path):
                            continue
                            
                        
                        # تجاهل الملفات الكبيرة
                        if os.path.getsize(file_path) > 1024 * 1024:  # 1MB
                            continue
                            
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines, 1):
                                if self.search_text.lower() in line.lower():
                                    context = self._get_context(lines, i)
                                    self.result_found.emit(file_path, i, line.strip(), context)

                            
                    except (UnicodeDecodeError, IOError) as e:
                        continue
                        
        except Exception as e:
            print(f"خطأ في البحث: {str(e)}")
        finally:
            print("انتهى البحث")
            self.finished.emit()

    def _is_valid_file(self, filename):
        """التحقق من صلاحية الملف للبحث"""
        # السماح بجميع الملفات
        return True

    def _get_context(self, lines, current_line, context_lines=2):
        """الحصول على سياق النص حول السطر المطابق"""
        start = max(0, current_line - context_lines - 1)
        end = min(len(lines), current_line + context_lines)
        return ''.join(lines[start:end]).strip()

class SearchWidget(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.search_thread = None
        self.setup_ui()
        self.load_style()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        extension_path = os.path.dirname(__file__)
        icons_path = os.path.join(extension_path, 'resources', 'icons')
        
        # حاوية البحث والاستبدال
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(5, 5, 5, 5)
        search_layout.setSpacing(2)

        # ==== شريط البحث ====
        search_bar = QHBoxLayout()
        
        # حقل البحث
        search_input_container = QHBoxLayout()
        search_input_container.setSpacing(2)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("البحث في الملفات...")
        self.search_input.textChanged.connect(self.start_search)
        
        # ززرار البحث الأساسية
        self.case_sensitive_btn = QPushButton("أ ﺄ")
        self.case_sensitive_btn.setCheckable(True)
        self.case_sensitive_btn.setToolTip("مطابقة حالة الأحرف")
        
        self.whole_word_btn = QPushButton("[]")
        self.whole_word_btn.setCheckable(True)
        self.whole_word_btn.setToolTip("كلمة كاملة")
        
        self.regex_btn = QPushButton(".*")
        self.regex_btn.setCheckable(True)
        self.regex_btn.setToolTip("تعبير نمطي")
        
        search_input_container.addWidget(self.search_input)
        search_input_container.addWidget(self.case_sensitive_btn)
        search_input_container.addWidget(self.whole_word_btn)
        search_input_container.addWidget(self.regex_btn)
        
        # زر الاستبدال
        self.toggle_replace_btn = QPushButton("⇄")
        self.toggle_replace_btn.setCheckable(True)
        self.toggle_replace_btn.setToolTip("إظهار الاستبدال")
        self.toggle_replace_btn.clicked.connect(self.toggle_replace)
        
        search_bar.addLayout(search_input_container)
        search_bar.addWidget(self.toggle_replace_btn)

        # ==== شريط الاستبدال ====
        replace_bar = QHBoxLayout()
        
        # حقل الاستبدال
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("استبدال بـ...")
        self.replace_input.setVisible(False)
        
        # أزرار الاستبدال
        replace_buttons = QHBoxLayout()
        replace_buttons.setSpacing(2)
        
        self.replace_btn = QPushButton("استبدال")
        self.replace_btn.setVisible(False)
        self.replace_btn.clicked.connect(self.replace_selected)
        
        self.replace_all_btn = QPushButton("استبدال الكل")
        self.replace_all_btn.setVisible(False)
        self.replace_all_btn.clicked.connect(self.replace_all)
        
        replace_buttons.addWidget(self.replace_btn)
        replace_buttons.addWidget(self.replace_all_btn)
        
        replace_bar.addWidget(self.replace_input)
        replace_bar.addLayout(replace_buttons)

        # ==== شريط الخيارات ====
        options_bar = QHBoxLayout()
        options_bar.setSpacing(2)
        
        # خيارات العرض
        self.show_context_btn = QPushButton("السياق")
        self.show_context_btn.setCheckable(True)
        self.show_context_btn.setChecked(True)
        
        self.show_line_numbers_btn = QPushButton("#")
        self.show_line_numbers_btn.setCheckable(True)
        self.show_line_numbers_btn.setChecked(True)
        self.show_line_numbers_btn.setToolTip("عرض أرقام الأسطر")
        
        # إيارات التصفية
        filter_buttons = QHBoxLayout()
        filter_buttons.setSpacing(2)
        
        self.include_files_btn = QPushButton("تضمين")
        self.include_files_btn.clicked.connect(self.set_include_files)
        self.include_files_btn.setToolTip("تحديد الملفات المضمنة")
        
        self.exclude_files_btn = QPushButton("استبعاد")
        self.exclude_files_btn.clicked.connect(self.set_exclude_files)
        self.exclude_files_btn.setToolTip("تحديد الملفات المستبعدة")
        
        filter_buttons.addWidget(self.include_files_btn)
        filter_buttons.addWidget(self.exclude_files_btn)
        
        options_bar.addWidget(self.show_context_btn)
        options_bar.addWidget(self.show_line_numbers_btn)
        options_bar.addStretch()
        options_bar.addLayout(filter_buttons)

        # إضافة كل الأشرطة
        search_layout.addLayout(search_bar)
        search_layout.addLayout(replace_bar)
        search_layout.addLayout(options_bar)

        # شجرة النتائج
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["النتائج"])
        self.results_tree.setIndentation(20)
        self.results_tree.itemDoubleClicked.connect(self.open_result)
        self.results_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_tree.customContextMenuRequested.connect(self.show_context_menu)

        # إضافة الحاويات الرئيسية
        layout.addWidget(search_container)
        layout.addWidget(self.results_tree)

    def load_style(self):
        """تحميل ملف التنسيق"""
        try:
            style_path = os.path.join(
                os.path.dirname(__file__),
                'resources',
                'styles',
                'search_widget.qss'
            )
            if os.path.exists(style_path):
                with open(style_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"خطأ في تحميل ملف التنسيق: {e}")

    def start_search(self):
        search_text = self.search_input.text()
        
        # مسح النتائج السابقة
        self.results_tree.clear()
        
        if not search_text or len(search_text) < 2:
            return

        current_folder = getattr(self.editor, 'current_folder', None)
        if not current_folder:
            return

        # إيقاف البحث السابق
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop()
            self.search_thread.wait()

        # تكوين خيارات البحث
        search_options = {
            'case_sensitive': self.case_sensitive_btn.isChecked(),
            'whole_word': self.whole_word_btn.isChecked(),
            'regex': self.regex_btn.isChecked(),
            'show_context': self.show_context_btn.isChecked(),
            'show_line_numbers': self.show_line_numbers_btn.isChecked(),
            'include_patterns': getattr(self, '_include_patterns', ''),
            'exclude_patterns': getattr(self, '_exclude_patterns', '')
        }

        # بدء بحث جديد
        self.search_thread = SearchThread(current_folder, search_text, search_options)
        self.search_thread.result_found.connect(self.add_result)
        self.search_thread.finished.connect(lambda: None)
        self.search_thread.start()

    def add_result(self, file_path, line_number, line_text, context):
        # إنشاء عنصر الملف إذا لم يكن موجوداً
        file_name = os.path.basename(file_path)
        file_items = self.results_tree.findItems(file_name, Qt.MatchExactly)
        
        if not file_items:
            file_item = QTreeWidgetItem([file_name])
            file_item.setToolTip(0, file_path)
            self.results_tree.addTopLevelItem(file_item)
        else:
            file_item = file_items[0]

        # تحضير نص النتيجة
        if self.show_line_numbers_btn.isChecked():
            result_text = f"السطر {line_number}: {line_text}"
        else:
            result_text = line_text

        # إنشاء عنصر النتيجة
        result_item = QTreeWidgetItem([result_text])
        result_item.setData(0, Qt.UserRole, {
            'file_path': file_path,
            'line_number': line_number,
            'line_text': line_text,
            'context': context
        })

        # إضافة السياق إذا كان مفعلاً
        if self.show_context_btn.isChecked() and context:
            context_item = QTreeWidgetItem([context])
            context_item.setForeground(0, QColor(128, 128, 128))  # لون رمادي للسياق
            result_item.addChild(context_item)

        file_item.addChild(result_item)
        file_item.setExpanded(True)
        result_item.setExpanded(True)

    def _highlight_match(self, text, search_text):
        """تمييز النص المطابق"""
        if not search_text:
            return text
            
        try:
            if self.regex_action.isChecked():
                import re
                pattern = re.compile(search_text, 0 if self.case_sensitive_action.isChecked() else re.IGNORECASE)
                return pattern.sub(lambda m: f'<b>{m.group()}</b>', text)
            else:
                if not self.case_sensitive_action.isChecked():
                    index = text.lower().find(search_text.lower())
                else:
                    index = text.find(search_text)
                    
                if index >= 0:
                    return f"{text[:index]}<b>{text[index:index+len(search_text)]}</b>{text[index+len(search_text):]}"
        except:
            pass
            
        return text

    def goto_line(self, line_number):
        """الانتقال إلى سطر محدد"""
        
        current_tab = self.editor.tab_manager.currentWidget()
        if current_tab and hasattr(current_tab, 'editor'):
            editor = current_tab.editor
            
            # إنشاء مؤشر نصي
            cursor = editor.textCursor()
            
            # الانتقال إلى بداية المستند
            cursor.movePosition(cursor.Start)
            
            # التحرك للسطر المطلوب
            for _ in range(line_number - 1):
                if not cursor.movePosition(cursor.NextBlock):
                    print("لا يمكن التحرك إلى السطر التالي")  # لتصحيح
                    break
            
            
            # تعيين المؤشر الجديد
            editor.setTextCursor(cursor)
            
            # تركيز على المحرر
            editor.setFocus()
        else:
            pass

    def open_result(self, item):
        data = item.data(0, Qt.UserRole)
        if data:
            file_path = data['file_path']
            line_number = data['line_number']
            
            
            # فتح الملف وانتظار الحميل
            if self.editor.tab_manager.open_file(file_path):
                # إضافة تأخير صغير للتأكد من اكتمال تحميل الملف
                QTimer.singleShot(100, lambda: self._after_file_open(line_number))

    def _after_file_open(self, line_number):
        """التنفيذ بعد فتح الملف"""
        current_tab = self.editor.tab_manager.currentWidget()
        if current_tab:
            
            # محاولة الوصول إلى المحرر بعدة طرق
            editor = None
            
            # البحث عن الأبناء من نوع ArabicTextEdit
            for child in current_tab.children():
                if type(child).__name__ == 'ArabicTextEdit':
                    editor = child
                    break
            
            if editor:
                
                # إنشاء مؤشر نصي
                cursor = editor.textCursor()
                
                # الانتقال إلى بداية المستند
                cursor.movePosition(cursor.Start)
                
                # التحرك للسطر المطلوب
                for _ in range(line_number - 1):
                    if not cursor.movePosition(cursor.NextBlock):
                        break
                
                
                # تعيين المؤشر الجديد
                editor.setTextCursor(cursor)
                
                # تركيز على المحرر
                editor.setFocus()
        else:
            QMessageBox.warning("لم يتم العثور على التبويب الحالي")

    def stop_search(self):
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop()
            self.search_thread.wait() 

    def show_context_menu(self, position):
        item = self.results_tree.itemAt(position)
        if not item:
            return

        menu = QMenu()
        
        # فتح الملف
        open_action = menu.addAction("فتح الملف")
        open_action.triggered.connect(lambda: self.open_result(item))
        
        # فتح المجلد
        if file_path := item.data(0, Qt.UserRole):
            open_folder_action = menu.addAction("فتح المجلد")
            open_folder_action.triggered.connect(
                lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(file_path['file_path'])))
            )
        
        menu.addSeparator()
        
        # نسخ
        copy_action = menu.addAction("نسخ")
        copy_action.triggered.connect(lambda: self.copy_result(item))
        
        # نسخ كل النتائج
        copy_all_action = menu.addAction("نسخ الكل")
        copy_all_action.triggered.connect(self.copy_all_results)
        
        menu.exec_(self.results_tree.viewport().mapToGlobal(position))

    def copy_result(self, item):
        """نسخ النتيجة المحددة"""
        data = item.data(0, Qt.UserRole)
        if data:
            text = f"{data['file_path']}:{data['line_number']}: {data['line_text']}"
            QApplication.clipboard().setText(text)

    def copy_all_results(self):
        """نسخ جميع النتائج"""
        all_results = []
        for i in range(self.results_tree.topLevelItemCount()):
            file_item = self.results_tree.topLevelItem(i)
            file_path = file_item.toolTip(0)
            
            for j in range(file_item.childCount()):
                result_item = file_item.child(j)
                data = result_item.data(0, Qt.UserRole)
                if data:
                    text = f"{file_path}:{data['line_number']}: {data['line_text']}"
                    all_results.append(text)
        
        if all_results:
            QApplication.clipboard().setText('\n'.join(all_results))

    def set_include_files(self):
        """تحديد أنماط الملفات المضمنة"""
        text, ok = QInputDialog.getText(
            self,
            "تضمين الملفات",
            "أدخل امتدادات الملفات (مثال: *.py;*.txt):",
            text=getattr(self, '_include_patterns', '')
        )
        if ok and text:
            self._include_patterns = text
            self.start_search()

    def set_exclude_files(self):
        """تحديد أنماط الملفات المستبعدة"""
        text, ok = QInputDialog.getText(
            self,
            "استبعاد الملفات",
            "أدخل امتدادات الملفات (مثال: *.pyc;*.log):",
            text=getattr(self, '_exclude_patterns', '')
        )
        if ok and text:
            self._exclude_patterns = text
            self.start_search()

    def toggle_replace(self):
        """إظهار/إخفاء شريط الاستبدال"""
        is_visible = self.toggle_replace_btn.isChecked()
        self.replace_input.setVisible(is_visible)
        self.replace_btn.setVisible(is_visible)
        self.replace_all_btn.setVisible(is_visible)

    def replace_selected(self):
        """استبدال النص في العنصر المحدد"""
        selected_items = self.results_tree.selectedItems()
        if not selected_items:
            return
            
        search_text = self.search_input.text()
        replace_text = self.replace_input.text()
        
        for item in selected_items:
            data = item.data(0, Qt.UserRole)
            if not data:
                continue
                
            file_path = data['file_path']
            line_number = data['line_number']
            
            self._replace_in_file(file_path, line_number, search_text, replace_text)
        
        # تحديث البحث
        self.start_search()

    def replace_all(self):
        """استبدال كل النتائج"""
        reply = QMessageBox.question(
            self,
            "تأكيد الاستبدال",
            "هل أنت متأكد من استبدال كل النتائج؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        search_text = self.search_input.text()
        replace_text = self.replace_input.text()
        
        # جمع كل النتائج
        replacements = []
        for i in range(self.results_tree.topLevelItemCount()):
            file_item = self.results_tree.topLevelItem(i)
            for j in range(file_item.childCount()):
                result_item = file_item.child(j)
                data = result_item.data(0, Qt.UserRole)
                if data:
                    replacements.append((data['file_path'], data['line_number']))
        
        # تنفيذ الاستبدال
        for file_path, line_number in replacements:
            self._replace_in_file(file_path, line_number, search_text, replace_text)
        
        # تحديث البحث
        self.start_search()

    def _replace_in_file(self, file_path, line_number, search_text, replace_text):
        """استبدال النص في ملف محدد"""
        try:
            # قراءة الملف
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # التأكد من صحة رقم السطر
            if 1 <= line_number <= len(lines):
                # استبدال النص في السطر المحدد
                line = lines[line_number - 1]
                
                # تطبيق خيارات البحث
                if self.regex_btn.isChecked():
                    import re
                    flags = 0 if self.case_sensitive_btn.isChecked() else re.IGNORECASE
                    new_line = re.sub(search_text, replace_text, line, flags=flags)
                else:
                    if self.whole_word_btn.isChecked():
                        import re
                        pattern = r'\b' + re.escape(search_text) + r'\b'
                        flags = 0 if self.case_sensitive_btn.isChecked() else re.IGNORECASE
                        new_line = re.sub(pattern, replace_text, line, flags=flags)
                    else:
                        if not self.case_sensitive_btn.isChecked():
                            new_line = self._replace_case_insensitive(line, search_text, replace_text)
                        else:
                            new_line = line.replace(search_text, replace_text)
                
                lines[line_number - 1] = new_line
                
                # حفظ التغييرات
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                    
        except Exception as e:
            QMessageBox.warning(
                self,
                "خطأ في الاستبدال",
                f"حدث خطأ أثناء الاستبدال في الملف {file_path}:\n{str(e)}"
            )
  
    def _replace_case_insensitive(self, text, search_text, replace_text):
        """استبدال النص بدون حساسية الأحرف"""
        result = ''
        i = 0
        while i < len(text):
            if text[i:i+len(search_text)].lower() == search_text.lower():
                result += replace_text
                i += len(search_text)
            else:
                result += text[i]
                i += 1
        return result