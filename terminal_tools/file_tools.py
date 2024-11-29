"""
أدوات التعامل مع الملفات
"""

from .base_tool import TerminalTool
import os
import shutil

class FileCopy(TerminalTool):
    def __init__(self, terminal):
        super().__init__(terminal)
        self.name = "نسخ"
        self.description = "نسخ ملف أو مجلد إلى وجهة محددة"
        self.usage = "نسخ <المصدر> <الوجهة> [--اجباري/-ا]"
        self.category = "ملفات"
        
    def execute(self, args):
        # التحقق من وجود طلب المساعدة
        if "--مساعدة" in args or "--اوامر" in args:
            self.show_help()
            return
            
        force = False
        if '--اجباري' in args or '-ا' in args:
            force = True
            args = [arg for arg in args if arg not in ['--اجباري', '-ا']]
            
        if len(args) != 2:
            self.show_help()
            return
            
        source, dest = args
        
        if not os.path.exists(source):
            self.terminal.append_text(f"\nخطأ: المصدر '{source}' غير موجود\n", 
                                    self.terminal.colors['error'])
            return
            
        if not os.access(source, os.R_OK):
            self.terminal.append_text(f"\nخطأ: لا تملك صلاحية قراءة '{source}'\n",
                                    self.terminal.colors['error'])
            return
            
        try:
            total_size = self._get_size(source)
            if total_size > 1024*1024*100:
                response = self.terminal.prompt_yes_no(
                    f"حجم المحتوى كبير ({self._format_size(total_size)}). هل تريد المتابعة؟"
                )
                if not response:
                    return

            if os.path.isfile(source):
                self._copy_file(source, dest, force)
            elif os.path.isdir(source):
                self._copy_directory(source, dest, force)
                
        except PermissionError:
            self.terminal.append_text(f"\nخطأ: لا تملك الصلاحيات الكافية\n",
                                    self.terminal.colors['error'])
        except Exception as e:
            self.terminal.append_text(f"\nخطأ: {str(e)}\n", 
                                    self.terminal.colors['error'])

    def _copy_file(self, source, dest, force=False):
        if os.path.exists(dest) and not force:
            response = self.terminal.prompt_yes_no(
                f"الملف '{dest}' موجود بالفعل. هل تريد استبداله؟"
            )
            if not response:
                return
                
        shutil.copy2(source, dest)
        self.terminal.append_text(
            f"\nتم نسخ الملف: {source} إلى {dest}\n",
            self.terminal.colors['success']
        )

    def _copy_directory(self, source, dest, force=False):
        if os.path.exists(dest):
            if not force:
                response = self.terminal.prompt_yes_no(
                    f"المجلد '{dest}' موجود بالفعل. هل تريد استبداله؟"
                )
                if not response:
                    return
            shutil.rmtree(dest)
            
        shutil.copytree(source, dest)
        self.terminal.append_text(
            f"\nتم نسخ المجلد: {source} إلى {dest}\n",
            self.terminal.colors['success']
        )

    def _get_size(self, path):
        if os.path.isfile(path):
            return os.path.getsize(path)
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def _format_size(self, size):
        for unit in ['ب', 'ك.ب', 'م.ب', 'ج.ب', 'ت.ب']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ب.ب"

class FileMove(TerminalTool):
    def __init__(self, terminal):
        super().__init__(terminal)
        self.name = "نقل"
        self.description = "نقل ملف أو مجلد إلى وجهة محددة"
        self.usage = "نقل <المصدر> <الوجهة>"
        self.category = "ملفات"
        
    def execute(self, args):
        # التحقق من وجود طلب المساعدة
        if "--مساعدة" in args or "--اوامر" in args:
            self.show_help()
            return
            
        if len(args) != 2:
            self.show_help()
            return
            
        source, dest = args
        if not os.path.exists(source):
            self.terminal.append_text(f"\nخطأ: المصدر '{source}' غير موجود\n", 
                                    self.terminal.colors['error'])
            return
            
        try:
            if os.path.exists(dest):
                response = self.terminal.prompt_yes_no(f"'{dest}' موجود بالفعل. هل تريد استبداله؟")
                if not response:
                    return
                    
            shutil.move(source, dest)
            self.terminal.append_text(f"\nتم نقل: {source} إلى {dest}\n",
                                   self.terminal.colors['output'])
        except Exception as e:
            self.terminal.append_text(f"\nخطأ: {str(e)}\n", self.terminal.colors['error'])

    def prompt_yes_no(self, message):
        while True:
            response = input(f"{message} (نعم/لا): ").strip().lower()
            if response in ['نعم', 'ن', 'y', 'yes']:
                return True
            if response in ['لا', 'ل', 'n', 'no']:
                return False