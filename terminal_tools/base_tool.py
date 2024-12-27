"""
الصنف الأساسي لجميع الأدوات
"""
class TerminalTool:
    def __init__(self, terminal):
        self.terminal = terminal
        self.name = ""
        self.description = ""
        self.usage = ""
        self.category = ""
        
    def execute(self, args):
        """تنفيذ الأداة"""
        # التحقق من وجود طلب المساعدة
        if "--مساعدة" in args or "--اوامر" in args:
            self.show_help()
            return
            
        raise NotImplementedError("يجب تنفيذ هذه الدالة في الصنف الفرعي")
        
    def show_help(self):
        """عرض المساعدة"""
        self.terminal.append_text(f"\nالأداة: {self.name}\n", self.terminal.colors['header'])
        self.terminal.append_text(f"الوصف: {self.description}\n", self.terminal.colors['description'])
        self.terminal.append_text(f"الاستخدام: {self.usage}\n", self.terminal.colors['command'])
        self.terminal.append_text("\nالخيارات المتاحة:\n", self.terminal.colors['header'])
        self.terminal.append_text("  --مساعدة, --اوامر    عرض هذه المساعدة\n", self.terminal.colors['command'])