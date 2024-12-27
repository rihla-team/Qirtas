import logging
from PyQt5.QtWidgets import  QTextEdit, QSplitter, QMenu, QHBoxLayout, QLineEdit, QPushButton, QShortcut, QLabel, QDialog, QTabWidget 
from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtGui import QTextCursor, QFont, QColor, QKeySequence, QTextCharFormat, QTextDocument, QTextBlockFormat
from PyQt5.QtWidgets import QVBoxLayout , QCheckBox, QMessageBox
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.output import create_output
from prompt_toolkit.input import create_input
import os
import platform
import pyperclip  # تأكد من تثبيت هذه المكتبة: pip install pyperclip
import json
from datetime import datetime
import locale
import sys
from pathlib import Path
import subprocess
from terminal_tools import *
from utils.arabic_logger import setup_arabic_logging
import logging
setup_arabic_logging()
# تعيين ترميز النظام
if sys.platform.startswith('win'):
    # Windows
    os.system('chcp 65001')

class ArabicTerminal(QTextEdit):
    """
    موجه الأوامر  عربي متكامل
    
    الميزات:
    - دعم كامل للغة العربية
    - إكمال تلقائي للأوامر
    - تاريخ الأوامر
    - تنسيق ملون
    - دعم المجلدات والملفات
    
    المتطلبات:
    - PyQt5
    - Python 3.6+
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.load_commands()
        self.setup_terminal()
        self.process = None
        self.command_history = []
        self.history_index = -1
        self.history_limit = 1000  # الحد الأقصى للتاريخ
        # تحديد مسار الملف في نفس مجلد البرنامج
        self.history_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.terminal_history')
        self.current_command = ""
        self.prompt_symbol = "$"  # رمز موجه الأوامر
        self.current_directory = os.getcwd()
        self.logger = logging.getLogger('ArabicTerminal')
        # تعريف الألوان باستخدام QColor
        self.colors = {
            'prompt': QColor('#98C379'), # لون موني
            'input': QColor('#61AFEF'), # لون سماوي
            'output': QColor('#ABB2BF'), # لون ابيض
            'error': QColor('#E06C75'), # لون احمر
            'suggestion': QColor('#C678DD'), # لون ارجواني
            'header': QColor('#E5C07B'), # لون اصفر
            'separator': QColor('#4B5263'), # لون اسود
            'number': QColor('#61AFEF'), # لون رقم
            'command': QColor('#98C379'), # لون موني
            'description': QColor('#ABB2BF'), # لون ابيض
            'category': QColor('#56B6C2'), # لون ازرق
            'internal_command': QColor('#E5C07B'), # لون اصفر
            'path': QColor('#56B6C2'), # لون ازرق
            'stats': QColor('#E5C07B'), # لون اصفر
            'file': QColor('#98C379'), # لون موني
            'folder': QColor('#56B6C2'), # لون ازرق
            'info': QColor('#E5C07B'), # لون اصفر
            'response': QColor('#61AFEF'), # لون سماوي
            'success': QColor('#98C379'), # لون موني
            'warning': QColor('#E5C07B'), # لون اصفر
            'unit': QColor('#E5C07B'), # لون اصفر
            'rates': QColor('#E5C07B'), # لون اصفر
        }
        
        # إعداد النمط
        self.setup_style()
        
        # إعداد المالج
        self.setup_process()
        
        # طباعة الترحيب
        self.print_welcome_message()
        self.display_prompt()

        # تعطيل القائمة المنبثقة الافتراضية
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.handle_right_click)

        locale.setlocale(locale.LC_ALL, '')
        sys.stdout.reconfigure(encoding='utf-8')

        # إضافة ألوان جديدة للتاريخ
        self.colors.update({
            'number': '#61AFEF',      # لون رقم الأمر
            'command': '#98C379',     # لون الأمر
            'description': '#ABB2BF', # لون الوصف
            'header': '#E5C07B',      # لون العنوان
        })
        
        # تهيئة قائمة التاريخ
        self.command_history = []
        self.history_index = -1

        # إنشاء نافذة البحث
        self.search_widget = TerminalSearchWidget(self)
        
        # استخدام اختصار مختلف للموجه الأوامر  - Ctrl+Shift+F
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        self.search_shortcut.activated.connect(self.show_search)

        self.load_tools()

        self.load_history()
        self.history_index = len(self.command_history)

    def setup_terminal(self):
        """إعداد موجه الأوامر """
        self.setReadOnly(False)
        self.setAcceptRichText(False)
        self.setFont(QFont("Consolas", 10))
        
        # تعيين اتجاه النص للموجه الأوامر  بالكامل
        self.setLayoutDirection(Qt.RightToLeft)
        
        # تعيين محاذاة النص إلى اليمين
        document = self.document()
        option = document.defaultTextOption()
        option.setTextDirection(Qt.RightToLeft)
        document.setDefaultTextOption(option)
        
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: none;
                padding: 5px;
            }
        """)
        
        # إعداد prompt-toolkit
        self.session = PromptSession()
        self.output = create_output()
        self.input = create_input()

    def setup_style(self):
        """إعداد النمط"""
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: none;
                padding: 5px;
            }
        """)

    def setup_process(self):
        """إعداد معالج الأوامر"""
        if hasattr(self, 'process') and self.process is not None:
            self.process.kill()
            self.process.waitForFinished()
        
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.process_finished)
        
        if platform.system() == "Windows":
            self.shell = "cmd.exe"
            self.shell_args = ["/c"]
        else:
            self.shell = "/bin/bash"
            self.shell_args = ["-c"]

    def print_welcome_message(self):
        """طباعة رسالة الترحيب"""
        welcome = "مرحباً بك في موجه الأوامر العربي\n"
        welcome += f"نظام التشغيل: {platform.system()}\n"
        welcome += f"المسار الحالي: {self.current_directory}\n"
        self.append_text(welcome, self.colors['output'])

    def display_prompt(self):
        """عرض موجه الأوامر"""
        current_path = os.getcwd()
        formatted_path = self.format_path(current_path)
        # إضافة سطر جديد فقط إذا لم يكن السطر الحالي فارغاً
        if self.toPlainText() and not self.toPlainText().endswith('\n'):
            self.append_text('\n')
        self.append_text(f"{formatted_path}  $ ", self.colors['prompt'])

    def format_path(self, path):
        """تنسيق المسار للعرض"""
        # تحويل الباك سلاش إلى فورورد سلاش
        path = path.replace('\\', '/')
        
        try:
            # تحويل المسار إى مسار نسبي إذا كان ضمن مجلد المشروع
            project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            if path.startswith(project_dir):
                path = os.path.relpath(path, project_dir)
                path = path.replace('\\', '/')
                
            # تقسيم المسار إلى أجزاء
            parts = path.split('/')
            
            # عكس ترتيب الأجزاء العربية فقط
            formatted_parts = []
            for part in parts:
                # التحقق إذا كان الجزء يحتوي على روف عربية
                if any('\u0600' <= c <= '\u06FF' for c in part):
                    # عكس اتجاه النص العربي
                    formatted_parts.append(f"\u202B{part}\u202C")
                else:
                    # إبقاء النص الإنجليزي كما هو
                    formatted_parts.append(part)
                    
            # إعادة تجميع المسار مع علامات التوجيه
            path = '/'.join(formatted_parts)
            
            # إافة علامات التوجيه للمسار كاملاً
            path = f"\u202B{path}\u202C"
                
        except:
            pass
        
        return path

    def get_prompt_position(self):
        """الحصول على موضع نهاية موجه الأوامر"""
        block = self.document().lastBlock()
        text = block.text()
        prompt_pos = text.find(self.prompt_symbol)
        if prompt_pos >= 0:
            return block.position() + prompt_pos + len(self.prompt_symbol) + 1
        return block.position()

    def append_text(self, text, color=None):
        """إضافة نص مع تنسق"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # إنشاء تنسيق للنص
        format = QTextCharFormat()
        if color:
            # التأكد من أن color هو كائن QColor
            if isinstance(color, str):
                color = QColor(color)
            format.setForeground(color)
        
        # إنشاء تنسيق للفقرة
        block_format = QTextBlockFormat()
        block_format.setLayoutDirection(Qt.RightToLeft)
        
        # تطبيق التنسيق
        cursor.setBlockFormat(block_format)
        cursor.insertText(text, format)
        
        # تحريك المؤشر إلى نهاية النص
        self.setTextCursor(cursor)
        
    def clear_current_line(self):
        """مسح السطر الحالي"""
        cursor = self.textCursor()
        # الانتقال إلى بداية السطر
        cursor.movePosition(QTextCursor.StartOfLine)
        # تحديد النص حتى نهاية السطر
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        # حذف النص المحدد
        cursor.removeSelectedText()
        # عرض موجه الأوامر
        self.display_prompt()

    def keyPressEvent(self, event):
        """معالجة أحداث المفاتيح"""
        cursor = self.textCursor()
        prompt_pos = self.get_prompt_position()
        
        # منع الكتابة خارج السطر الحالي
        if cursor.position() < self.get_prompt_position():
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
        
        if event.key() == Qt.Key.Key_Tab:
            current_command = self.get_current_command()
            if current_command:
                completed_command = self.auto_complete(current_command)
                if completed_command:
                    # حذف الأمر الالي
                    cursor = self.textCursor()
                    cursor.movePosition(QTextCursor.End)
                    for _ in range(len(current_command)):
                        cursor.deletePreviousChar()
                    # إضافة الأمر المكتمل
                    self.append_text(completed_command, self.colors['input'])
            return
                        # معالجة الأسهم
        if event.key() == Qt.Key_Left:
            # السماح بالتحرك لليسار فقط إذا كنا بعد موجه الأوامر
            if cursor.position() > prompt_pos:
                cursor.movePosition(QTextCursor.Left)
                self.setTextCursor(cursor)
            return
        elif event.key() == Qt.Key_Right:
            # السماح بالتحرك لليمين حتى نهاية السطر
            cursor.movePosition(QTextCursor.Right)
            self.setTextCursor(cursor)
            return
        elif event.key() == Qt.Key_Up:
            # التنقل في تاريخ الأوامر لأعلى
            if self.history_index > 0:
                self.history_index -= 1
                self._show_history_command()
            return
        elif event.key() == Qt.Key_Down:
            # التنقل في تاريخ الأوامر للأسفل
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self._show_history_command()
            elif self.history_index == len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self.clear_current_line()
            return
        
        # معالجة Ctrl+C
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
            if self.process and self.process.state() == QProcess.Running:
                self.process.kill()
                self.append_text("\n^C\n", self.colors['error'])
                self.display_prompt()
                return
            elif self.textCursor().hasSelection():
                self.copy()
                return
                
        # معالجة الأسهم
        if event.key() in [Qt.Key_Left, Qt.Key_Right]:
            cursor = self.textCursor()
            # السماح بالتحرك فقط بعد موجه الأوامر
            if cursor.position() >= self.get_prompt_position():
                if event.key() == Qt.Key_Left:
                    cursor.movePosition(QTextCursor.Left)
                else:
                    cursor.movePosition(QTextCursor.Right)
                    self.setTextCursor(cursor)
                return
        # منع Ctrl+A
        if event.matches(QKeySequence.SelectAll):
            return
        
        # منع Ctrl+X
        if event.matches(QKeySequence.Cut):
            return
        
        # منع Ctrl+Z
        if event.matches(QKeySequence.Undo):
            return
        
        # معالجة مفتاح Enter
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            command = self.get_current_command()
            if command:
                # تنفيذ الأمر إذا كان غير فارغ
                self.execute_command(command)
                self.command_history.append(command)
                self.history_index = len(self.command_history)
            else:
                # إذا كان الأمر فارغاً، نضيف سطر جديد مع موجه الأوامر
                self.append_text("\n")
                self.display_prompt()
            return
        
        elif event.key() == Qt.Key_Up:
            self._navigate_history('up')
            return
        
        elif event.key() == Qt.Key_Down:
            self._navigate_history('down')
            return
        
        elif event.key() == Qt.Key_Left:
            # السماح بالتنقل لليسار فقط بعد موجه الأوامر
            if cursor.position() <= self.get_prompt_position():
                return
            
        elif event.key() == Qt.Key_Backspace:
            # منع الحذف قبل موجه الأوامر
            if cursor.position() <= self.get_prompt_position():
                return
            
        # السماح بـ Ctrl+C للنسخ
        if event.matches(QKeySequence.Copy):
            self.copy()
            return
        
        # السماح ب Ctrl+V للصق
        if event.matches(QKeySequence.Paste):
            self.paste_at_cursor()
            return
        # معالجة باقي المفاتيح
        super().keyPressEvent(event)

    def get_current_command(self):
        """الحصول على الأمر الحالي"""
        text = self.toPlainText()
        lines = text.split('\n')
        if lines:
            last_line = lines[-1]
            prompt_pos = last_line.rfind(self.prompt_symbol)
            if prompt_pos >= 0:
                return last_line[prompt_pos + len(self.prompt_symbol):].strip()
        return ""

    def execute_command(self, command):
        """تنفيذ الأمر"""
        if not command.strip():
            return
        
        # إضافة الأمر للتاريخ
        self._add_to_history(command)
        
        # تقسيم الأمر إلى أجزاء
        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # قاموس الأوامر المدمجة
        builtin_commands = {
            "cd": lambda: self.change_directory(" ".join(args)),
            "انتقل": lambda: self.change_directory(" ".join(args)),
            "اذهب": lambda: self.change_directory(" ".join(args)),
            "سجل": self.show_history,
            "تاريخ": self.show_history,
            "تاريخ_الاوامر": self.show_history,
            "clear": self.clear_terminal,
            "cls": self.clear_terminal,
            "مسح": self.clear_terminal,
            "تنظيف": self.clear_terminal,
            "مساعدة": self.display_arabic_help,
            "اوامر": self.display_arabic_help,
            "أوامر": self.display_arabic_help,
            "تعليمات": self.display_arabic_help,
            "الاوامر": self.display_arabic_help,
            "ls": lambda: self.list_directory_arabic(" ".join(args) or "."),
            "dir": lambda: self.list_directory_arabic(" ".join(args) or "."),
            "عرض": lambda: self.list_directory_arabic(" ".join(args) or "."),
            "قائمة": lambda: self.list_directory_arabic(" ".join(args) or ".")
        }
        
        # التحقق من الأوامر المدمجة أولاً
        if cmd in builtin_commands:
            builtin_commands[cmd]()
            self.display_prompt()
            return
        
        # التحقق من الأدوات المخصصة
        if cmd in self.tools:
            self.tools[cmd].execute(args)
            self.display_prompt()
            return
        
        # البحث عن الأمر في ملف الأوامر
        found_command = None
        for command_key, info in self.commands.items():
            if cmd == command_key or cmd in info.get('arabic', []):
                found_command = command_key
                break
                
        if found_command:
            try:
                self.setup_process()
                os_type = "windows" if platform.system().lower() == "windows" else "linux"
                system_cmd = self.commands[found_command][os_type]
                
                # تجميع الأمر الكامل
                full_command = f"{system_cmd} {' '.join(args)}"
                
                # معالجة خاصة لأوامر معينة في Windows
                if platform.system() == "Windows":
                    if full_command.lower().startswith(("dir", "ls")):
                        full_command = "powershell.exe -Command Get-ChildItem"
                    
                self.process.start(self.shell, self.shell_args + [full_command])
                
            except Exception as e:
                self.append_text(f"\nخطأ في تنفيذ الأمر: {str(e)}\n", self.colors['error'])
        else:
            self.append_text(f"\nالأمر غير معروف: {cmd}\n", self.colors['error'])
            self.display_prompt()

    def _add_to_history(self, command):
        """إضافة أمر إلى التاريخ"""
        command_entry = {
            'command': command,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        }
        
        # تجنب تكرار نفس الأمر في نفس الثانية
        if self.command_history and isinstance(self.command_history[-1], dict):
            last_entry = self.command_history[-1]
            if (last_entry['command'] == command and 
                abs(datetime.strptime(last_entry['timestamp'], '%Y-%m-%d %H:%M:%S.%f') - 
                    datetime.strptime(command_entry['timestamp'], '%Y-%m-%d %H:%M:%S.%f')).total_seconds() < 1):
                return
        
        # إضافة وحفظ الأمر في التاريخ
        self.command_history.append(command_entry)
        if len(self.command_history) > self.history_limit:
            self.command_history = self.command_history[-self.history_limit:]
        self.history_index = len(self.command_history)
        
        # حفظ التاريخ في الملف
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.command_history, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"خطأ في حفظ التاريخ: {str(e)}")

    def handle_output(self):
        """تحسين معالج مخرجات الأمر"""
        try:
            while self.process.bytesAvailable():
                data = self.process.readAll()
                try:
                    text = bytes(data).decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text = bytes(data).decode('cp1256')
                    except:
                        text = bytes(data).decode('utf-8', errors='replace')
                
                # عرض المخرجات مباشرة بدون إضافة موجه الأوامر
                if text.strip():
                    self.append_text("    " + text, self.colors['output'])
                    
        except Exception as e:
            self.append_text(f"\nخطأ في معالجة المخرجات: {str(e)}\n", self.colors['error'])

    def process_finished(self, exit_code, exit_status):
        """معالجة انتهاء تنفيذ الأمر"""
        if exit_code != 0:
            self.append_text(f"\nانتهى التنفيذ مع رمز الخروج: {exit_code}\n", self.colors['error'])
        else:
            self.append_text("\nتم الانتهاء بنجاح\n", self.colors['output'])
        self.display_prompt()

    def change_directory(self, path):
        """تغيير المجلد الحالي"""
        try:
            # تنظيف المسار وإزالة علامات التنصيص إذا وجدت
            path = path.strip()
            if path.startswith('"') and path.endswith('"'):
                path = path[1:-1]
            
            # إذا كان المسار فارغاً
            if not path:
                self.append_text("\nخطأ: يجب تحديد اسم المجلد\n", self.colors['error'])
                return
            
            # تحويل المسار إلى مسار مطلق
            try:
                abs_path = os.path.abspath(path)
            except Exception:
                self.append_text(f"\nخطأ: المسار '{path}' غير صالح\n", self.colors['error'])
                return
            
            # التحقق من وجود المجلد
            try:
                if not os.path.exists(abs_path):
                    self.append_text(f"\nخطأ: المجلد '{path}' غير موجود\n", self.colors['error'])
                    return
            except PermissionError:
                self.append_text("\nخطأ: ليس لديك صلاحية للوصول إلى هذا امجلد\n", self.colors['error'])
                return
            except Exception:
                self.append_text(f"\nخطأ: لا يمكن التحقق من وجود المجلد '{path}'\n", self.colors['error'])
                return
            
            if not os.path.isdir(abs_path):
                self.append_text(f"\nخطأ: '{path}' ليس مجلداً\n", self.colors['error'])
                return
            
            # تغيير المجلد
            try:
                os.chdir(abs_path)
                self.current_directory = abs_path
                self.append_text(f"\nتم الانتقال إلى: {self.format_path(abs_path)}\n", self.colors['output'])
            except PermissionError:
                self.append_text("\nخطأ: ليس لديك صلاحية للدخول إلى هذا المجلد\n", self.colors['error'])
            except FileNotFoundError:
                self.append_text(f"\nخطأ: المجلد '{path}' غير موجود\n", self.colors['error'])
            except NotADirectoryError:
                self.append_text(f"\nخطأ: '{path}' ليس مجلداً\n", self.colors['error'])
            except OSError as e:
                if e.errno == 2:  # المجلد غير موجود
                    self.append_text(f"\nخطأ: المجلد '{path}' غير موجود\n", self.colors['error'])
                elif e.errno == 3:  # المسار غير موجود
                    self.append_text(f"\nخطأ: المسار '{path}' غير موجود\n", self.colors['error'])
                elif e.errno == 5:  # رفض الوصول
                    self.append_text("\nخطأ: ليس لديك صلاحية للدخول إلى هذا المجلد\n", self.colors['error'])
                elif e.errno == 22:  # اسم غير صالح
                    self.append_text(f"\nخطأ: اسم المجلد '{path}' غير صالح\n", self.colors['error'])
                else:
                    self.append_text("\nخطأ: لا يمكن الدخول إلى هذا المجلد\n", self.colors['error'])
            except Exception:
                self.append_text("\nخطأ: حدث خطأ غير متوقع أثناء تغيير المجلد\n", self.colors['error'])
                
        except Exception:
            self.append_text("\nخطأ: حدث خطأ غير متوقع\n", self.colors['error'])

    def _navigate_history(self, direction):
        """التنقل في تاريخ الأوامر"""
        if not self.command_history:
            return

        # حفظ الأمر الحالي عند بدء التصفح
        if self.history_index == len(self.command_history):
            self.current_command = self.get_current_command()

        if direction == 'up' and self.history_index > 0:
            self.history_index -= 1
            self._show_history_command()
        elif direction == 'down' and self.history_index < len(self.command_history):
            self.history_index += 1
            if self.history_index == len(self.command_history):
                self._show_command(self.current_command)
            else:
                self._show_history_command()

    def _show_history_command(self):
        """عرض الأمر من التاريخ"""
        if 0 <= self.history_index < len(self.command_history):
            command_entry = self.command_history[self.history_index]
            # استخراج الأمر من القاموس إذا كان القاموس
            command = command_entry['command'] if isinstance(command_entry, dict) else command_entry
            self._show_command(command)

    def _show_command(self, command):
        """عرض الأمر في سطر الأوامر"""
        # التأكد من أن الأمر نص وليس قاموس
        if isinstance(command, dict):
            command = command.get('command', '')
        
        cursor = self.textCursor()
        # مسح النص الحالي من موضع prompt إلى نهاية السطر
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        # عضافة prompt جديد
        self.display_prompt()
        # إضافة الأمر
        self.append_text(command, self.colors['input'])

    def show_history(self):
        """عرض تاريخ الأوامر"""
        if not self.command_history:
            self.append_text("\nلا يوجد تاريخ أوامر\n", self.colors['error'])
            return

        self.append_text("\n═══════ تاريخ الأوامر ═══════\n", self.colors['header'])
        
        # عرض الأوامر بترتيب تصاعدي مع أرقامها
        for i, entry in enumerate(self.command_history, 1):
            number = f"{i:3d}"
            self.append_text(f"\n{number}  ", self.colors['number'])
            
            if isinstance(entry, dict):
                command = entry['command']
                # عرض التوقيت بدون الميلي ثانية للتبسيط
                timestamp = entry['timestamp'].split('.')[0]
                self.append_text(f"[{timestamp}] ", self.colors['info'])
            else:
                command = entry
                self.append_text(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ", self.colors['info'])
                
            self.append_text(f"{command}", self.colors['command'])
            
            # إضافة الوصف إذا كان متوفراً
            description = self._get_command_description(command.split()[0])
            if description:
                self.append_text(f" - {description}", self.colors['description'])
        
        self.append_text("\n\n", self.colors['output'])
        self.display_prompt()

    def _get_command_description(self, cmd):
        """الحصول على وصف الأمر"""
        cmd = cmd.lower()
        for command_info in self.commands.values():
            if (cmd in command_info.get('arabic', []) or 
                cmd == command_info.get('windows') or 
                cmd == command_info.get('linux')):
                return command_info.get('description', '')
        return ''

    def clear_history(self):
        """مسح تاريخ الأوامر"""
        self.command_history.clear()
        self.history_index = -1
        # مسح ملف التاريخ
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            self.append_text("\nتم مسح تاريخ الأوامر\n", self.colors['success'])
        except Exception as e:
            self.append_text(f"\nخطأ في مسح ملف التاريخ: {str(e)}\n", self.colors['error'])

    def split_terminal(self):
        """تقسيم موجه الأوامر """
        splitter = QSplitter(Qt.Horizontal)
        new_terminal = ArabicTerminal(self.parent)
        splitter.addWidget(self)
        splitter.addWidget(new_terminal)
        
        if hasattr(self.parent, 'terminal_layout'):
            self.parent.terminal_layout.addWidget(splitter)

    def handle_right_click(self, position):
        """معالجة النقر بالزر الأيمن"""
        # لا نحتاج لهذه الدالة بعد الآن
        pass

    def paste_at_cursor(self):
        """لصق النص في موضع المؤشر"""
        cursor = self.textCursor()
        if cursor.position() >= self.get_prompt_position():
            try:
                text = pyperclip.paste()
                if text:
                    # تنظيف النص من الأحرف غير المرغوب فيها
                    text = text.replace('\r', '')
                    # تقسيم النص إلى أسطر للتعامل مع النصوص متعددة اأسطر
                    lines = text.split('\n')
                    
                    # لصق السطر الأول في الموضع الحالي
                    cursor.insertText(lines[0])
                    
                    # إذا كان هناك المزيد من الأسطر
                    if len(lines) > 1:
                        for line in lines[1:]:
                            # إضافة سطر جديد وموجه الأوامر
                            cursor.insertText('\n')
                            # إضافة موجه الأوامر الجديد
                            self.display_prompt()
                            # إضافة النص
                            cursor.insertText(line)
                
            except Exception as e:
                print(f"خطأ في اللصق: {str(e)}")

    def mousePressEvent(self, event):
        """معالجة أحداث الضغط بالماوس"""
        if event.button() == Qt.RightButton:
            cursor = self.textCursor()
            if cursor.hasSelection():
                # نسخ النص المحدد فقط
                selected_text = cursor.selectedText()
                pyperclip.copy(selected_text)
            else:
                # لصق لنص في نهاية السطر الحالي
                cursor = QTextCursor(self.document())
                cursor.movePosition(QTextCursor.End)
                self.setTextCursor(cursor)
                self.paste_at_cursor()
            return
        
        # السماح بتحديد النص
        if event.button() == Qt.LeftButton:
            super().mousePressEvent(event)
            # نحرك المؤشر إلى النهاية فقط إذا كان النقر في نهاية النص
            cursor = self.textCursor()
            if not cursor.hasSelection() and cursor.position() == self.document().characterCount():
                cursor.movePosition(QTextCursor.End)
                self.setTextCursor(cursor)

    def mouseDoubleClickEvent(self, event):
        """السماح بالنقر المزدوج لتحديد الكلمات"""
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        """السماح تحريك الماوس للتحديد"""
        super().mouseMoveEvent(event)

    def focusInEvent(self, event):
        """عند التركيز على موجه الأوامر """
        # نحرك المؤشر إلى النهاية فقط إذا لم يكن هناك تحديد
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
        super().focusInEvent(event)

    def contextMenuEvent(self, event):
        """منع ظهور القائمة المنبثقة"""
        event.accept()

    def createStandardContextMenu(self, position=None):
        """تجاوز إنشاء القائمة المنبثقة لقياية"""
        # إرجاع قائمة فارغة لمنع ظهور القائمة الافتراضية
        return QMenu(self)

    def canInsertFromMimeData(self, source):
        """التحكم في إمكانية اللصق"""
        # السماح باللصق فقط في نهاية النص وبعد موجه الأوامر
        cursor = self.textCursor()
        return cursor.position() >= self.get_prompt_position()

    def insertFromMimeData(self, source):
        """التحكم في عملية اللصق"""
        if self.canInsertFromMimeData(source):
            text = source.text()
            if text:
                # تنظيف النص من الأحرف غير المرغوب فيها
                text = text.replace('\r', '')
                
                # إضافة النص مع المحاذاة لليين
                cursor = self.textCursor()
                block_format = QTextBlockFormat()
                block_format.setLayoutDirection(Qt.RightToLeft)
                
                cursor.setBlockFormat(block_format)
                cursor.insertText(text)

    def wheelEvent(self, event):
        """معالجة حدث عجلة الماوس"""
        # السماح بالتميير العاد
        super().wheelEvent(event)

    def load_commands(self):
        """تحميل قائمة الأوامر من المف"""
        try:
            with open('resources/command.json', 'r', encoding='utf-8') as f:
                self.commands = json.load(f)
                # إضافة أمر شغيل
        except Exception as e:
            self.commands = {}
            print(f"خطأ في تحميل ملف الأوامر: {str(e)}")

    def display_commands(self):
        """عرض قائمة الأوامر المتاحة"""
        self.append_text("\n=== الأوامر المتاحة ===\n", self.colors['prompt'])
        
        # تجميع الأوامر حسب الوظيفة
        for cmd, info in self.commands.items():
            # عرض الأمر باللغة الإنجليزية
            command_text = f"\n{cmd}"
            
            # إضافة الأوامر العربية المقابلة
            arabic_commands = info.get('arabic', [])
            if arabic_commands:
                command_text += f" ({' / '.join(arabic_commands)})"
                
            # إضافة وصف الأمر
            description = info.get('description', '')
            command_text += f"\n    {description}\n"
            
            # عرض الأمر مع تنسيق
            self.append_text(command_text, self.colors['output'])
        
        self.append_text("\n", self.colors['output'])
        self.display_prompt()

    def display_arabic_help(self):
        """عرض المساعدة باللغة العربية"""
        help_text = "\n=== الأوامر المتاحة في موجه الأوامر العربي ===\n\n"
        
        # تجميع الأوامر حسب التصيف
        categories = {}
        for cmd_name, cmd_info in self.commands.items():
            category = cmd_info.get('category', 'أخرى')
            if category not in categories:
                categories[category] = []
            categories[category].append((cmd_name, cmd_info))
        
        # عرض الأوامر حسب التصنيف
        for category, commands in categories.items():
            help_text += f"\n{category}:\n" + "=" * 30 + "\n"
            
            for cmd_name, cmd_info in commands:
                # الأم الأساسي
                help_text += f"\n{cmd_name}"
                
                # الأمر في ويندوز/لينكس
                os_type = "windows" if platform.system().lower() == "windows" else "linux"
                system_cmd = cmd_info.get(os_type, cmd_name)
                if system_cmd != cmd_name:
                    help_text += f" ({system_cmd})"
                
                # المرادفات العربية
                arabic_aliases = cmd_info.get('arabic', [])
                if arabic_aliases:
                    help_text += f"\n    المرادفات: {' / '.join(arabic_aliases)}"
                
                # الصف
                description = cmd_info.get('description', '')
                if description:
                    help_text += f"\n    الوصف: {description}"
                
                help_text += "\n"
        
        # إضافة ملاحظات إضافية
        help_text += "\n\nملاحظات:\n"
        help_text += "- يمكنك استخدام الأوامر باللغة العربية أو الإنجليزية\n"
        help_text += "- استخدم السهم لأعلى وأسفل للتنقل بين الأوامر السابقة\n"
        help_text += "- يمكنك استخدام الأمر 'مساعدة' أو 'help' لعرض هذه القائمة\n"
        help_text += "- يمكنك الضغط على 'Tab' للإكمال التلقائي للأوامر\n"
        self.append_text(help_text, self.colors['output'])
        self.display_prompt()

    def auto_complete(self, partial_command):
        """تحسين الإكمال التلقائي مع عرض الأوامر العربية"""
        if not partial_command:
            return None
        
        command_matches = []
        
        parts = partial_command.split(None, 1)
        cmd = parts[0].lower()
        path = parts[1] if len(parts) > 1 else ''
        
        # التحقق مما إذا كان الإدخال عربياً
        is_arabic_input = any('\u0600' <= c <= '\u06FF' for c in cmd)
        
        # البحث في الأوامر من ملف command.json
        for command_name, info in self.commands.items():
            arabic_commands = info.get('arabic', [])
            
            # البحث في الأوامر العربية
            if is_arabic_input:
                for arabic_cmd in arabic_commands:
                    if arabic_cmd.startswith(cmd):
                        match_info = {
                            'command': arabic_cmd,
                            'description': info['description'],
                            'category': info.get('category', '')
                        }
                        if match_info not in command_matches:
                            command_matches.append(match_info)
            # البحث في الأوامر الإنجليزية
            else:
                if command_name.startswith(cmd):
                    match_info = {
                        'command': command_name,
                        'description': info['description'],
                        'category': info.get('category', '')
                    }
                    if match_info not in command_matches:
                        command_matches.append(match_info)
        
        # إذا وجدنا مطابقات
        if command_matches and not path:
            if len(command_matches) == 1:
                command = command_matches[0]['command']
                if command == cmd or command.startswith(cmd + cmd[0]):
                    return None
                return command
            else:
                # عرض الاقتراحات مع التصنيف
                self.append_text("\n", self.colors['output'])
                
                # تنظيم الأوامر حسب التصنيف
                categories = {}
                for match in command_matches:
                    category = match['category']
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(match)
                
                # عرض الأوامر مرتبة حسب التصنيف
                for category, commands in categories.items():
                    self.append_text(f"\n{category}:\n", self.colors['header'])
                    self.append_text("─" * 50 + "\n", self.colors['separator'])
                    
                    max_length = max(len(cmd['command']) for cmd in commands)
                    
                    for cmd_info in sorted(commands, key=lambda x: x['command']):
                        padding = " " * (max_length - len(cmd_info['command']) + 2)
                        self.append_text(cmd_info['command'], self.colors['suggestion'])
                        self.append_text(padding, self.colors['output'])
                        self.append_text(f"{cmd_info['description']}\n", self.colors['output'])
                
                self.display_prompt()
                self.append_text(cmd, self.colors['input'])
                
                # تحسين البحث عن البادئة المشتركة
                common_commands = [m['command'] for m in command_matches]
                common = self.find_common_prefix(common_commands)
                if common and len(common) > len(cmd) and not common.startswith(cmd + cmd[0]):
                    return common
                
                return None
        
        # التحقق من وع دعم الملفات للأمر
        support_type = None
        for command, info in self.commands.items():
            if cmd == command or cmd in info.get('arabic', []):
                support_type = info.get('support_files_or_folders_nor', 'none')
                break
        
        # إذا كان الأمر يدعم إكمال المسارات
        if support_type != 'none':
            # إضاف مسافة في نهاية الأمر إذا لم تكن موجودة
            if not partial_command.endswith(' ') and not path:
                return partial_command + ' '
            
            completed_path = self.complete_path(path.strip(), partial_command, support_type)
            if completed_path:
                # إذا كان المسار فارغاً، نضيف مسافة قبل المسار المكتمل
                if not path:
                    return f"{cmd} {completed_path}"
                else:
                    return f"{cmd} {completed_path}"
        
        return None

    def complete_path(self, partial_path, full_command, support_type='folders'):
        """إمل المسار"""
        try:
            base_dir = os.getcwd()
            
            # إذا كان المسار فارغاً، نعرض كل الملفات والمجلدات
            if not partial_path:
                items = os.listdir(base_dir)
            else:
                # تحديد المجلد الأساسي والجزء المراد إكماله
                if os.path.isabs(partial_path):
                    base = os.path.dirname(partial_path)
                    partial = os.path.basename(partial_path)
                else:
                    base = os.path.join(base_dir, os.path.dirname(partial_path))
                    partial = os.path.basename(partial_path)
                
                if not os.path.exists(base):
                    base = base_dir
                
                items = os.listdir(base)
            
            # البحث عن المطابقات
            matches = []
            for item in items:
                if item.startswith('.'):
                    continue
                    
                full_path = os.path.join(base_dir, item)
                
                # التحقق من نوع العنصر والدعم المطوب
                if support_type == 'folders' and not os.path.isdir(full_path):
                    continue
                elif support_type == 'files' and not os.path.isfile(full_path):
                    continue
                
                # التحقق من المطابقة
                if not partial_path or item.lower().startswith(partial_path.lower()):
                    if os.path.isdir(full_path):
                        matches.append(item + '/')
                    else:
                        matches.append(item)
            
            if len(matches) == 0:
                return None
            elif len(matches) == 1:
                return matches[0]
            else:
                # عرض المطابقات
                suggestion_color = QColor('#61AFEF')  # للمجلدات
                file_color = QColor('#98C379')       # للملفات
                output_color = QColor('#ABB2BF')     # للنص العادي
                
                self.append_text("\n", output_color)
                for match in sorted(matches):
                    # استخدام لون مختلف للجلدات والملفات
                    color = suggestion_color if match.endswith('/') else file_color
                    self.append_text(match + "\n", color)
                
                self.display_prompt()
                self.append_text(full_command, self.colors['input'])
                
                # إرجاع البادئة المشتركة
                common = self.find_common_prefix(matches)
                if common:
                    return common
                    
                return None
                
        except Exception as e:
            print(f"Error in complete_path: {e}")
            return None

    def find_common_prefix(self, strings):
        """إيجاد أطول بادئة مشتركة"""
        if not strings:
            return ""
        if len(strings) == 1:
            return strings[0]
        
        # تحويل المجموعة إلى قائمة مرتبة
        strings = sorted(strings)
        
        # أذ أقصر طول من السلاسل
        shortest = min(len(s) for s in strings)
        
        # البحث عن أطول بادئة مشتركة
        for i in range(shortest):
            char = strings[0][i]
            if not all(s[i] == char for s in strings):
                return strings[0][:i]
        
        # إذا وصلنا إلى هنا، نرجع أقصر سلسلة
        return strings[0][:shortest]

    def clear_terminal(self):
        """مسح محتوى موجه الأوامر """
        self.clear()  # مسح المحتوى
        self.display_prompt()  # عرض موجه الأوامر الجديد
    
    def clear(self):
        """مسح كل المحتوى"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.removeSelectedText()
        cursor.clearSelection()
        self.setTextCursor(cursor)

    def list_directory_arabic(self, path='.'):
        """تحسين عرض محتويات المجلد"""
        try:
            directory = Path(path).resolve()
            
            # تجميع المعلومات مرة واحدة
            items_info = []
            total_files = 0
            total_folders = 0
            total_size = 0
            
            # استخدام generator بدل القوائم
            for item in directory.iterdir():
                try:
                    stats = item.stat()
                    is_dir = item.is_dir()
                    
                    if is_dir:
                        total_folders += 1
                        item_type = "📁 مجلد"
                        # حساب حجم المجلد بشكل تراكمي
                        dir_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                        total_size += dir_size
                        size = self._format_size(dir_size)
                        color = self.colors['folder']
                    else:
                        total_files += 1
                        total_size += stats.st_size
                        item_type = "📄 ملف"
                        size = self._format_size(stats.st_size)
                        color = self.colors['file']
                    
                    items_info.append({
                        'type': item_type,
                        'name': f"{item.name}{'/' if is_dir else ''}",
                        'size': size,
                        'date': datetime.fromtimestamp(stats.st_mtime),
                        'color': color
                    })
                    
                except Exception:
                    continue
            
            # عرض المعلومات المجمعة
            self._display_directory_info(directory, items_info, total_files, total_folders, total_size)
            
        except Exception as e:
            self.append_text(f"\nخطأ: {str(e)}\n", self.colors['error'])

    def _format_size(self, size):
        """تنسيق حجم الملف - تم فصلها لتحسين الأداء"""
        if size < 1024:
            return f"{size} ب"
        elif size < 1024 * 1024:
            return f"{size/1024:.0f} ك.ب"
        return f"{size/(1024*1024):.1f} م.ب"

    def _display_directory_info(self, directory, items_info, total_files, total_folders, total_size):
        """عرض معلومات المجلد - تم فصلها لتحسين الأداء"""
        # عرض المسار
        self.append_text("\n المسار: ", self.colors['header'])
        self.append_text(f"{directory}\n", self.colors['path'])
        
        # عرض الفاصل
        separator = "─" * 80 + "\n"
        self.append_text(separator, self.colors['separator'])
        
        # عرض العناوين
        headers = " {:<15} {:<20} {:<15} {:<30}\n".format(
            "النوع", "تاريخ التعديل", "الحجم", "الاسم"
        )
        self.append_text(headers, self.colors['header'])
        self.append_text(separator, self.colors['separator'])
        
        # عرض العناصر
        for item in sorted(items_info, key=lambda x: (x['type'] != "📁 مجلد", x['name'])):
            arabic_date = item['date'].strftime('%I:%M %p %Y/%m/%d').replace('AM', 'ص').replace('PM', 'م')
            output_line = " {:<12} {:<25} {:<12} {:<30}\n".format(
                item['type'],
                arabic_date,
                item['size'],
                item['name']
            )
            self.append_text(output_line, item['color'])
            
        # عرض الإحصائيات
        self.append_text(separator, self.colors['separator'])
        self.append_text("إحصائيات المجلد:\n", self.colors['stats'])
        self.append_text(f"عدد المجلدات: {total_folders}\n", self.colors['stats'])
        self.append_text(f"عدد الملفات: {total_files}\n", self.colors['stats'])
        self.append_text(f"الحجم الإجمالي: {self._format_size(total_size)}\n", self.colors['stats'])
        
        # عرض تفاصيل المجلدات الفرعية
        # جمع إحصائات المجلدات الفرعية
        total_subdir_files = 0
        total_subdir_folders = 0
        
        for item in items_info:
            if item['type'] == "📁 مجلد":
                try:
                    path = os.path.join(directory, item['name'])
                    total_subdir_files += len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
                    total_subdir_folders += len([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
                except (PermissionError, OSError):
                    continue
        
        # عرض الإحصائيات المجمعة للمجلدات الفرعية
        self.append_text("\nإحصائيات المجلدات الفرعية:\n", self.colors['folder'])
        self.append_text(f"  - إجمالي المجلدت الفرعية: {total_subdir_folders}\n", self.colors['stats'])
        self.append_text(f"  - إجمالي الملفات في المجلدات الفرعية: {total_subdir_files}\n", self.colors['stats'])
        self.append_text(separator, self.colors['separator'])

        self.display_prompt()
        
    def show_search(self):
        """إظهار نافذة البحث"""
        if not hasattr(self, 'search_dialog'):
            self.search_dialog = TerminalSearchWidget(self)
        
        self.search_dialog.show()
        self.search_dialog.search_input.setFocus()
        
        # تحديد النص المحدد تلقائياً
        if self.textCursor().hasSelection():
            self.search_dialog.search_input.setText(self.textCursor().selectedText())
            self.search_dialog.search_input.selectAll()

    def _enable_interactive_mode(self, args):
        """تمكين الوضع التفاعلي للبرامج في ويندوز"""
        # تعيين خيارات إنشاء العملية لتمكين الوضع التفاعلي
        args.flags |= 0x00000010  # CREATE_NEW_CONSOLE

    def load_tools(self):
        """تحميل الأدوات العربية من ملف command.json"""
        with open('resources/command.json', 'r', encoding='utf-8') as f:
            commands = json.load(f)
        
        self.tools = {
            'تحويل': UnitConverter(self)
        }
        for command_name, command_info in commands.items():
            tool_name = command_info.get('tool')
            if tool_name:
                tool_class = globals().get(tool_name)
                if tool_class:
                    for arabic_name in command_info.get('arabic', []):
                        self.tools[arabic_name] = tool_class(self)
                        

    def save_history(self):
        """حفظ تاريخ الأوامر في ملف"""
        try:
            # تحويل كل الإدخالات إلى النسق الصحيح
            cleaned_history = []
            
            for entry in self.command_history:
                if isinstance(entry, dict):
                    cleaned_history.append(entry)
                else:
                    cleaned_history.append({
                        'command': entry,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    })
            
            # تحديث التاريخ مع الحفاظ على الحد الأقصى
            self.command_history = cleaned_history[-self.history_limit:]
            
            # حفظ في الملف
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.command_history, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
                
        except Exception as e:
            print(f"خطأ في حفظ التاريخ: {str(e)}")

    def load_history(self):
        """تحميل تاريخ الأوامر من الملف"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    loaded_history = json.load(f)
                    self.command_history = []
                    
                    # تحويل كل الإدخالات إلى النسق الصحيح
                    for entry in loaded_history:
                        if isinstance(entry, str):
                            # تحويل النصوص القديمة إلى قواميس
                            self.command_history.append({
                                'command': entry,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                            })
                        else:
                            # إضافة القواميس كما هي
                            self.command_history.append(entry)
                    
                    self.logger.info(f"تم تحميل {len(self.command_history)} أمر من التاريخ")
            else:
                self.command_history = []
                
        except Exception as e:
            self.logger.error(f"خطأ في تحميل التاريخ: {str(e)}")
            self.command_history = []

class TerminalSearchWidget(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.last_match = None
        self.last_search = None
        self.init_ui()
        self.apply_styles()
        
    def init_ui(self):
        self.setWindowTitle('بحث في موجه الأوامر')
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)  # هوامش متناسقة
        layout.setSpacing(10)
        
        # حقل البحث
        search_layout = QHBoxLayout()
        search_label = QLabel('بحث عن:')
        self.search_input = QLineEdit()
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # خيارات البحث
        options_layout = QHBoxLayout()
        self.case_sensitive = QCheckBox('مطابقة حالة الأحرف')
        self.whole_words = QCheckBox('كلمات كاملة فقط')
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.whole_words)
        layout.addLayout(options_layout)
        
        # أزرار البحث
        buttons_layout = QHBoxLayout()
        find_next_btn = QPushButton('بحث عن التالي')
        find_prev_btn = QPushButton('بحث عن السابق')
        find_next_btn.clicked.connect(self.find_next)
        find_prev_btn.clicked.connect(self.find_previous)
        buttons_layout.addWidget(find_next_btn)
        buttons_layout.addWidget(find_prev_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)

    def apply_styles(self):
        # تنسيق نافذة الحوار
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: #ffffff;
                border-radius: 8px;
            }
            
            QLabel {
                color: #ffffff;
            }
            
            QLineEdit {
                background-color: #212121;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px;
                min-height: 24px;
            }
            
            QLineEdit:hover {
                border: 1px solid #054229;
            }
            
            QCheckBox {
                color: #ffffff;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #333333;
                border-radius: 3px;
                background-color: #212121;
            }
            
            QCheckBox::indicator:checked {
                background-color: #054229;
                border: 1px solid #054229;
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
        """)
        
    def find(self, forward=True):
        """البحث عن النص"""
        text = self.parent.toPlainText()
        if not text:
            return
            
        # الحصول على النص المراد البحث عنه
        search_text = self.search_input.text()
        if not search_text:
            return
            
        # تحديث آخر بحث
        self.last_search = search_text
            
        # تحديد خيارات البحث
        flags = QTextDocument.FindFlags()
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole_words.isChecked():
            flags |= QTextDocument.FindWholeWords
        if not forward:
            flags |= QTextDocument.FindBackward
            
        # البحث عن النص
        found = self.parent.find(search_text, flags)
        if not found:
            # إذا لم يتم العثور على النص، نعود إلى بداية/نهاية المستند
            cursor = self.parent.textCursor()
            cursor.movePosition(
                cursor.Start if forward else cursor.End
            )
            self.parent.setTextCursor(cursor)
            found = self.parent.find(search_text, flags)
            
            # إذا لم يتم العثور على النص، نعرض رسالة
            if not found:
                QMessageBox.information(
                    self,
                    "نتيجة البحث",
                    "لم يتم العثور على النص المطلوب"
                )
            
        return found
        
    def find_next(self):
        """البحث عن التطابق التالي"""
        return self.find(forward=True)
        
    def find_previous(self):
        """البحث عن التطابق السابق"""
        return self.find(forward=False)
        


class TerminalTabWidget(QTabWidget):
    """مدير تبويبات موجه الأوامر """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.close_tab)
        
        # إضافة زر إضافة تبويب جديد
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setFixedSize(25, 25)
        self.add_tab_button.clicked.connect(self.add_new_terminal)
        self.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)
        
        # إضافة التبويب الأول
        self.add_new_terminal()
        
        # تطبيق النمط
        self.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #1a1a1a;
            }
            QTabBar::tab {
                background: #2d2d2d;
                color: #ffffff;
                padding: 5px 10px;
                border: none;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #054229;
            }
            QTabBar::close-button {
                image: url(resources/icons/close.png);
            }
            QPushButton {
                background: #2d2d2d;
                color: #ffffff;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #404040;
            }
        """)

    def add_new_terminal(self):
        """إضافة تبويب موجه الأوامر  جديد"""
        terminal = ArabicTerminal(self.parent)
        index = self.addTab(terminal, f"موجه الأوامر {self.count() + 1}")
        self.setCurrentIndex(index)
        terminal.setFocus()
        return terminal

    def close_tab(self, index):
        """إغلاق تبويب"""
        if self.count() > 1:
            self.removeTab(index)
        else:
            # إخفاء موجه الأوامر  بدلاً من إغلاقه إذا كان التبويب الأخير
            self.parent.toggle_terminal(False)

    def get_current_terminal(self):
        """الحصول على موجه الأوامر  الحالي"""
        return self.currentWidget()

    def closeEvent(self, event):
        """حفظ التاريخ عند إغلاق البرنامج"""
        try:
            self.save_history()
            print("تم حفظ التاريخ عند الإغلاق")
        except Exception as e:
            print(f"خطأ في حفظ التاريخ عند الإغلاق: {str(e)}")
        super().closeEvent(event)