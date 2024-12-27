"""
أدوات النظام
"""

from .base_tool import TerminalTool
import psutil
import platform
import datetime
import sys
import os
import locale
import socket
import getpass
import subprocess
from colorama import init, Fore, Back, Style, AnsiToWin32

init(strip=True, convert=True)  # تهيئة colorama مع إزالة الرموز غير المرغوبة

class SystemInfo(TerminalTool):
    def __init__(self, terminal):
        super().__init__(terminal)
        self.name = "معلومات"
        self.description = "عرض معلومات تفصيلية عن النظام"
        self.usage = "معلومات [رقم_الخيار] [--مساعدة/--اوامر]"
        self.category = "نظام"
        
        # تهيئة المخرجات الملونة
        self.output = AnsiToWin32(sys.stdout)
        
    def write_colored(self, text, color):
        """كتابة نص ملون"""
        self.output.write(color + text + Style.RESET_ALL)
        
    def print_section(self, title):
        """طباعة عنوان القسم"""
        width = 80
        separator = "═" * width
        title_line = f" {title} ".center(width, "═")
        
        return f"\n{title_line}\n{separator}\n"
        
    def format_output(self, title, value, style='normal'):
        """تنسيق المخرجات"""
        return f"{title}: {value}\n"
        
    def show_menu(self):
        """عرض قائمة الخيارات"""
        menu = """
اختر نوع المعلومات التي تريد عرضها:
1. معلومات النظام الأساسية
2. معلومات الشبكة
3. معلومات المعالج
4. معلومات الذاكرة
5. معلومات القرص
6. وقت التشغيل
7. معلومات بايثون
8. معلومات المستخدم
9. معلومات الشاشة
10. معلومات الأجهزة
11. معلومات الأداء
12. معلومات الأمان
13. التطبيقات المثبتة
14. صحة النظام
15. كل المعلومات
0. خروج

الخيارات المتاحة:
--مساعدة, --اوامر    عرض هذه المساعدة
"""
        self.terminal.append_text(menu, self.terminal.colors['header'])        
    def get_system_info(self):
        """معلومات النظام الأساسية"""
        info = f"\n=== معلومات النظام الأساسية ===\n"
        
        # تحديد نوع نظام التشغيل بشكل صحيح
        os_type = platform.system()
        if os_type == 'Windows':
            windows_version = platform.win32_ver()
            info += f"نظام التشغيل: ويندوز  {windows_version[0]}\n"
            info += f"إصدار النظام: {windows_version[1]}\n"
            info += f"نوع الإصدار: {windows_version[2]}\n"
        elif os_type == 'Linux':
            # للأنظمة التي تعتمد على Linux
            try:
                with open('/etc/os-release') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('PRETTY_NAME='):
                            distro = line.split('=')[1].strip().replace('"', '')
                            info += f"نظام التشغيل: {distro}\n"
                            break
            except:
                info += f"نظام التشغيل: لينكس {platform.release()}\n"
        elif os_type == 'Darwin':
            info += f"نظام التشغيل: ماك أوس {platform.mac_ver()[0]}\n"
        else:
            info += f"نظام التشغيل: {os_type} {platform.release()}\n"
        
        # معلومات المعمارية
        arch = platform.architecture()
        machine = platform.machine()
        info += f"معمارية النظام: {arch[0]} ({machine})\n"
        
        # معلومات المعالج
        processor = platform.processor() or "غير معروف"
        info += f"نوع المعالج: {processor}\n"
        
        # معلومات اللغة والترميز
        try:
            system_lang = locale.getdefaultlocale()
            info += f"لغة النظام: {system_lang[0] or 'غير معروف'}\n"
            info += f"ترميز النظام: {system_lang[1] or 'غير معروف'}\n"
        except:
            info += "لغة النظام: غير معروف\n"
            info += "ترميز النظام: غير معروف\n"
        
        # معلومات المستخدم والجهاز
        try:
            info += f"اسم المستخدم: {os.getlogin()}\n"
        except:
            try:
                info += f"اسم المستخدم: {os.environ.get('USERNAME', 'غير معروف')}\n"
            except:
                info += "اسم المستخدم: غير معروف\n"
                
        info += f"اسم الجهاز: {platform.node()}\n"
        
        # معلومات بايثون
        info += f"إصدار بايثون: {sys.version.split()[0]}\n"
        info += f"مسار بايثون: {sys.executable}\n"
        
        # معلومات المجلد الحالي
        info += f"المجلد الحالي: {os.getcwd()}\n"
        
        # معلومات الوقت والمنطقة الزمنية
        try:
            import time
            info += f"المنطقة الزمنية: {time.tzname[0]}\n"
        except:
            info += "المنطقة الزمنية: غير معروف\n"
        
        return info
        
    def get_network_info(self):
        """معلومات الشبكة"""
        info = f"\n=== معلومات الشبكة ===\n"
        try:
            hostname = socket.gethostname()
            info += f"اسم المضيف: {hostname}\n"
            info += f"عنوان ب.ا المحلي: {socket.gethostbyname(hostname)}\n"
        except:
            pass
            
        for interface, addresses in psutil.net_if_addrs().items():
            info += f"\nواجهة الشبكة: {interface}\n"
            for addr in addresses:
                if addr.family == 2:  # IPv4
                    info += f"عنوان ب.ا_4: {addr.address}\n"
                    info += f"قناع الشبكة: {addr.netmask}\n"
                elif addr.family == 23:  # IPv6
                    info += f"عنوان ب.ا_6: {addr.address}\n"
                    
        # إحصائيات الشبكة
        net_io = psutil.net_io_counters()
        info += f"\nإحصائيات الشبكة:\n"
        info += f"البيانات المستلمة: {net_io.bytes_recv / (1024**2):.2f} ميجابايت\n"
        info += f"البيانات المرسلة: {net_io.bytes_sent / (1024**2):.2f} ميجابايت\n"
        return info
        
    def get_cpu_info(self):
        """معلومات المعالج"""
        info = f"\n=== معلومات المعالج ===\n"
        info += f"نوع المعالج: {platform.processor()}\n"
        info += f"عدد المعالجات المنطقية: {psutil.cpu_count()}\n"
        info += f"عدد المعالجات الفعلية: {psutil.cpu_count(logical=False)}\n"
        
        # تفاصيل استخدام المعالج
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            info += f"التردد الحالي: {cpu_freq.current:.2f} ميجاهيرتز\n"
            info += f"الحد الأدنى للتردد: {cpu_freq.min:.2f} ميجاهيرتز\n"
            info += f"الحد الأقصى للتردد: {cpu_freq.max:.2f} ميجاهيرتز\n"
            
        # استخدام المعالج لكل نواة
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True)):
            info += f"استدام النواة {i+1}: {percentage}%\n"
            
        return info
        
    def get_memory_info(self):
        """معلومات الذاكرة"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        info = f"\n=== معلومات الذاكرة ===\n"
        info += f"الذاكرة الكلية: {mem.total / (1024**3):.2f} ج.ب\n"
        info += f"الذاكرة المستخدمة: {mem.used / (1024**3):.2f} ج.ب\n"
        info += f"الذاكرة المتاحة: {mem.available / (1024**3):.2f} ج.ب\n"
        info += f"نسبة الاستخدام: {mem.percent}%\n"
        
        # إضافة معلومات الذاكرة المخبأة فقط إذا كانت متوفرة
        if hasattr(mem, 'cached'):
            info += f"الذاكرة المخبأة: {mem.cached / (1024**3):.2f} ج.ب\n"

        # معلومات إضافية عن الذاكرة
        if hasattr(mem, 'buffers'):
            info += f"الذاكرة المؤقتة: {mem.buffers / (1024**3):.2f} ج.ب\n"
        
        if hasattr(mem, 'shared'):
            info += f"الذاكرة المشتركة: {mem.shared / (1024**3):.2f} ج.ب\n"
        
        # معلومات ذاكرة التبديل
        info += f"\n=== ذاكرة التبديل (Swap) ===\n"
        info += f"المساحة الكلية: {swap.total / (1024**3):.2f} ج.ب\n"
        info += f"المساحة المستخدمة: {swap.used / (1024**3):.2f} ج.ب\n"
        info += f"المساحة المتاحة: {swap.free / (1024**3):.2f} ج.ب\n"
        info += f"نسبة الاستخدام: {swap.percent}%\n"
        
        # معلومات إضافية عن الذاكرة
        info += f"\n=== تفاصيل إضافية ===\n"
        info += f"عدد صفحات الذاكرة المستخدمة: {psutil.Process().memory_info().pagefile}\n"
        info += f"الذاكرة الفعلية المستخدمة: {psutil.Process().memory_info().rss / (1024**3):.2f} ج.ب\n"
        
        # حساب معدل استخدام الذاكرة
        try:
            memory_usage = []
            for _ in range(3):  # قياس 3 مرات
                memory_usage.append(psutil.Process().memory_percent())
            avg_memory = sum(memory_usage) / len(memory_usage)
            info += f"متوسط استخدام الذاكرة: {avg_memory:.2f}%\n"
        except:
            pass
        
        return info
        
    def get_disk_info(self):
        """معلومات القرص"""
        info = f"\n=== معلومات القرص ===\n"
        
        # معلومات الأقراص
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                info += f"\nالقرص: {partition.device}\n"
                info += f"نقطة التحميل: {partition.mountpoint}\n"
                info += f"نوع الملفات: {partition.fstype}\n"
                info += f"خيارات: {partition.opts}\n"
                info += f"المساحة الكلية: {usage.total / (1024**3):.2f} ج.ب\n"
                info += f"المساحة المستخدمة: {usage.used / (1024**3):.2f} ج.ب\n"
                info += f"المساحة المتاحة: {usage.free / (1024**3):.2f} ج.ب\n"
                info += f"نسبة الاستخدام: {usage.percent}%\n"
            except:
                continue
                
        # إحصائيات I/O
        disk_io = psutil.disk_io_counters()
        if disk_io:
            info += f"\nإحصائيات القراءة/الكتابة:\n"
            info += f"عدد عمليات القراءة: {disk_io.read_count}\n"
            info += f"عدد عمليات الكتابة: {disk_io.write_count}\n"
            info += f"حجم البيانات المقروءة: {disk_io.read_bytes / (1024**3):.2f} ج.ب\n"
            info += f"حجم البيانات المكتوبة: {disk_io.write_bytes / (1024**3):.2f} ج.ب\n"
        
        return info
        
    def get_boot_time(self):
        """وقت التشغيل"""
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        
        info = f"\n=== وقت التشغيل ===\n"
        info += f"تاريخ بدء التشغيل: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        info += f"مدة التشغيل: {uptime}\n"
        info += f"الأيام: {uptime.days}\n"
        info += f"الساعات: {uptime.seconds // 3600}\n"
        info += f"الدقائق: {(uptime.seconds % 3600) // 60}\n"
        info += f"الثواني: {uptime.seconds % 60}\n"
        return info
        
    def get_python_info(self):
        """معلومات بايثون"""
        info = f"\n=== معلومات بايثون ===\n"
        info += f"إدار بايثون: {sys.version}\n"
        info += f"مسار بايثون: {sys.executable}\n"
        info += f"مسار المكتبات: {sys.prefix}\n"
        info += f"ترميز الملفات: {sys.getfilesystemencoding()}\n"
        info += f"الوحدات المحملة: {len(sys.modules)}\n"
        info += f"المنصة: {sys.platform}\n"
        return info
        
    def get_user_info(self):
        """معلومات المستخدم"""
        info = f"\n=== معلومات المستخدم ===\n"
        info += f"اسم المستخدم: {getpass.getuser()}\n"
        info += f"المجلد الرئيسي: {os.path.expanduser('~')}\n"
        info += f"المجلد الحالي: {os.getcwd()}\n"
        info += f"المتغيرات البيئية:\n"
        for key, value in os.environ.items():
            info += f"  {key}: {value}\n"
        return info
        
    def get_display_info(self):
        """معلومات الشاشة"""
        info = f"\n=== معلومات الشاشة ===\n"
        if sys.platform.startswith('win'):
            try:
                import win32api
                from win32api import GetSystemMetrics
                import win32con
                import win32gui

                # الحصول على معلومات جميع الشاشات
                monitors = win32api.EnumDisplayMonitors()
                info += f"عدد الشاشات: {len(monitors)}\n"

                for i, monitor in enumerate(monitors, 1):
                    # الحصول على معلومات الشاشة
                    monitor_info = win32api.GetMonitorInfo(monitor[0])
                    
                    # الحصول على اسم الشاشة
                    device = monitor_info['Device']
                    
                    # حساب الأبعاد
                    rect = monitor_info['Monitor']
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    # الحصول على معدل التحديث
                    device_mode = win32api.EnumDisplaySettings(device, win32con.ENUM_CURRENT_SETTINGS)
                    refresh_rate = device_mode.DisplayFrequency
                    
                    info += f"\nالشاشة {i}:\n"
                    info += f"الجهاز: {device}\n"
                    info += f"العرض: {width} بكسل\n"
                    info += f"الارتفاع: {height} بكسل\n"
                    info += f"معدل التحديث: {refresh_rate} هرتز\n"
                    info += f"الموقع: ({rect[0]}, {rect[1]}) إلى ({rect[2]}, {rect[3]})\n"
                    
            except Exception as e:
                info += f"لم يتم العثور على معلومات الشاشة: {str(e)}\n"
        else:
            try:
                # محاولة الحصول على معلومات الشاشة في Linux
                import subprocess
                
                xrandr = subprocess.check_output(['xrandr']).decode()
                displays = [line for line in xrandr.split('\n') if ' connected ' in line]
                
                info += f"عدد الشاشات: {len(displays)}\n"
                
                for i, display in enumerate(displays, 1):
                    parts = display.split()
                    name = parts[0]
                    resolution = next((p for p in parts if 'x' in p), 'غير معروف')
                    refresh = next((p.rstrip('*+') for p in parts if 'هيرتز' in p), 'غير معروف')
                    
                    info += f"\nالشاشة {i}:\n"
                    info += f"الاسم: {name}\n"
                    info += f"الدقة: {resolution}\n"
                    info += f"معدل التحديث: {refresh}\n"
                    
            except:
                info += "معلومات الشاشة غير متوفرة لهذا النظام\n"
        return info
        
    def get_hardware_info(self):
        """معلومات الأجهزة"""
        info = f"\n=== معلومات الأجهزة ===\n"
        if sys.platform.startswith('win'):
            try:
                # استخدام r-string لتجنب مكلة الـ backslash
                output = subprocess.check_output('wmic cpu get name', shell=True).decode()
                processor = output.split('\n')[1].strip()
                info += f"المعالج: {processor}\n"
                
                output = subprocess.check_output('wmic bios get serialnumber', shell=True).decode()
                serial = output.split('\n')[1].strip()
                info += f"الرقم التسلسلي: {serial}\n"
                
                output = subprocess.check_output('wmic baseboard get product', shell=True).decode()
                motherboard = output.split('\n')[1].strip()
                info += f"اللوحة الأم: {motherboard}\n"
                
                # إضافة معلومات إضافية
                output = subprocess.check_output('wmic memorychip get capacity', shell=True).decode()
                memory_modules = [int(x) for x in output.split('\n')[1:-1] if x.strip()]
                total_memory = sum(memory_modules) / (1024**3)
                info += f"الذاكرة المثبتة: {total_memory:.2f} GB\n"
                info += f"عدد وحدات الذاكرة: {len(memory_modules)}\n"
                
            except Exception as e:
                info += f"لم يتم العثور على معلومات الأجهزة: {str(e)}\n"
        else:
            try:
                # للأنظمة الأخرى مثل Linux
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            info += f"المعالج: {line.split(':')[1].strip()}\n"
                            break
                
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if 'MemTotal' in line:
                            memory = int(line.split()[1]) / (1024**2)
                            info += f"الذاكرة الكلية: {memory:.2f} ج.ب\n"
                            break
            except:
                info += "معلومات الأجهزة غير متوفرة لهذا النظام\n"
        
        return info
        
    def get_performance_info(self):
        """معلومات الأدء"""
        info = f"\n=== معلومات الأداء ===\n"
        info += f"استخدام المعالج: {psutil.cpu_percent()}%\n"
        info += f"استخدام الذاكرة: {psutil.virtual_memory().percent}%\n"
        info += f"استخدام القرص: {psutil.disk_usage('/').percent}%\n"
        
        # العمليات النشطة
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
                
        # ترتيب العمليات حسب استخدام المعالج
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        info += f"\nأعلى 5 عمليات استخداماً للمعالج:\n"
        for i, proc in enumerate(processes[:5]):
            info += f"{i+1}. {proc['name']}: CPU {proc['cpu_percent']}%, MEM {proc['memory_percent']:.1f}%\n"
            
        return info
        
    def get_security_info(self):
        """معلومات الأمان"""
        info = self.print_section("معلومات الأمان")
        
        # معلومات جدار الحماية
        if sys.platform.startswith('win'):
            try:
                output = subprocess.check_output('netsh advfirewall show allprofiles state', shell=True).decode('utf-8', errors='ignore')
                firewall_state = "مفعل" if "ON" in output else "معطل"
                info += self.format_output("جدار الحماية", firewall_state, 'value' if firewall_state == "مفعل" else 'error')
            except:
                info += self.format_output("جدار الحماية", "غير معروف", 'warning')
        
        # معلومات مضاد الفيروسات
        try:
            import wmi
            w = wmi.WMI()
            antivirus = w.Win32_Product(Name="Windows Defender")
            if antivirus:
                info += self.format_output("مضاد الفيروسات", "Windows Defender مثبت")
        except:
            info += self.format_output("مضاد الفيروسات", "غير معروف", 'warning')
        
        return info
        
    def get_installed_apps(self):
        """معلومات التطبيقات المثبتة"""
        info = self.print_section("التطبيقات المثبتة")
        
        if sys.platform.startswith('win'):
            try:
                import winreg
                apps = []
                
                # فحص التطبيقات المثبتة
                keys = [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
                ]
                
                for key_path in keys:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey = winreg.OpenKey(key, subkey_name)
                                try:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                    apps.append((name, version))
                                except:
                                    continue
                            except:
                                continue
                    except:
                        continue
                    
                # ترتيب لتطبيقات أبجدياً
                apps.sort(key=lambda x: x[0].lower())
                
                # عرض التطبيقات
                info += self.format_output("عدد التطبيقات المثبتة", str(len(apps)))
                info += "\nأهم التطبيقات المثبتة:\n"
                for name, version in apps[:20]:  # عرض أول 20 تطبيق فقط
                    info += self.format_output(f"• {name}", f"الإصدار: {version}")
                    
            except Exception as e:
                info += self.format_output("خطأ", f"لم يمكن قراءة التطبيقات المثبتة: {str(e)}", 'error')
        
        return info
        
    def get_system_health(self):
        """معلومات صحة النظام"""
        output = []
        
        try:
            output.append(self.print_section("تقرير صحة النظام"))
            
            # حالة الموارد الأساسية
            output.append(self.print_section("حالة الموارد الأساسية"))
            
            # المعالج
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()
            status = (
                'ممتاز' if cpu_percent < 50 
                else 'جيد' if cpu_percent < 80 
                else 'مرتفع'
            )
            output.append(
                self.format_output(
                    "المعالج",
                    f"{status} (استخدام: {cpu_percent:.1f}% | تردد: {cpu_freq.current:.0f}MHz | أنوية: {cpu_count})"
                )
            )
            
            # الذاكرة
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            mem_status = (
                'ممتاز' if memory.percent < 60
                else 'جيد' if memory.percent < 80
                else 'منخفض'
            )
            output.append(
                self.format_output(
                    "الذاكرة",
                    f"{mem_status} (متاح: {memory.available/1024**3:.1f}GB | مستخدم: {memory.used/1024**3:.1f}GB | "
                    f"إجمالي: {memory.total/1024**3:.1f}GB)"
                )
            )
            output.append(
                self.format_output(
                    "الذاكرة الافتراضية",
                    f"مستخدم: {swap.used/1024**3:.1f}GB | إجمالي: {swap.total/1024**3:.1f}GB"
                )
            )
            
            # حالة التخزين
            output.append(self.print_section("حالة التخزين"))
            
            for partition in psutil.disk_partitions():
                try:
                    if 'fixed' not in partition.opts:
                        continue
                        
                    disk = psutil.disk_usage(partition.mountpoint)
                    disk_status = (
                        'ممتاز' if disk.percent < 70
                        else 'جيد' if disk.percent < 85
                        else 'منخفض'
                    )
                    
                    drive_name = partition.device.replace('\\', '')
                    output.append(
                        self.format_output(
                            "القرص " + drive_name,
                            f"{disk_status} (متاح: {disk.free/1024**3:.1f}GB | مستخدم: {disk.used/1024**3:.1f}GB | "
                            f"إجمالي: {disk.total/1024**3:.1f}GB | نوع: {partition.fstype})"
                        )
                    )
                except:
                    continue
            
            # حالة الشبكة
            output.append(self.print_section("حالة الشبكة"))
            
            net_io = psutil.net_io_counters()
            output.append(
                self.format_output(
                    "الشبكة",
                    f"تم الاستلام: {net_io.bytes_recv/1024**2:.1f}MB | تم الإرسال: {net_io.bytes_sent/1024**2:.1f}MB"
                )
            )
            
            # العمليات النشطة
            output.append(self.print_section("العمليات النشطة"))
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] > 0:
                        processes.append(pinfo)
                except:
                    continue
            
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            for i, proc in enumerate(processes[:5], 1):
                output.append(
                    self.format_output(
                        f"{i}. {proc['name']}",
                        f"معالج: {proc['cpu_percent']:.1f}% | ذاكرة: {proc['memory_percent']:.1f}%"
                    )
                )
            
            # التوصيات
            output.append(self.print_section("التوصيات والتحسينات"))
            
            if cpu_percent > 80:
                output.append(self.format_output("", "• يُنصح بإغلاق بعض التطبيقات لتخفيف الحمل على المعالج"))
            
            if memory.percent > 80:
                output.append(self.format_output("", "• يُنصح بتحرير بعض الذاكرة العشوائية"))
                output.append(self.format_output("", "• حاول إغلاق التطبيقات غير المستخدمة"))
            
            if swap.percent > 80:
                output.append(self.format_output("", "• يُنصح بزيادة حجم ملف الذاكرة الافتراضية"))
            
            for partition in psutil.disk_partitions():
                try:
                    if 'fixed' in partition.opts:
                        disk = psutil.disk_usage(partition.mountpoint)
                        if disk.percent > 85:
                            drive_name = partition.device.replace('\\', '')
                            output.append(
                                self.format_output(
                                    "",
                                    f"• يُنصح بتحرير مساحة على القرص {drive_name}"
                                )
                            )
                except:
                    continue
            
            # معلومات إضافية
            output.append(self.print_section("معلومات إضافية"))
            
            # وقت التشغيل
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time
            output.append(
                self.format_output(
                    "وقت التشغيل",
                    f"{uptime.days} يوم, {uptime.seconds//3600} ساعة, {(uptime.seconds//60)%60} دقيقة"
                )
            )
            
            # درجة الحرارة (إذا كانت متاحة)
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            output.append(
                                self.format_output(
                                    f"درجة حرارة {name}",
                                    f"{entry.current:.1f}°C"
                                )
                            )
            except:
                pass
            
        except Exception as e:
            output.append(self.format_output("خطأ", str(e)))
        
        return "".join(output)
        
    def execute(self, args):
        """تنفيذ الأداة"""
        if not args:
            self.show_menu()
            return
            
        try:
            choice = int(args[0])
        except:
            self.show_menu()
            return
            
        info = ""
        if choice == 1:
            info = self.get_system_info()
        elif choice == 2:
            info = self.get_network_info()
        elif choice == 3:
            info = self.get_cpu_info()
        elif choice == 4:
            info = self.get_memory_info()
        elif choice == 5:
            info = self.get_disk_info()
        elif choice == 6:
            info = self.get_boot_time()
        elif choice == 7:
            info = self.get_python_info()
        elif choice == 8:
            info = self.get_user_info()
        elif choice == 9:
            info = self.get_display_info()
        elif choice == 10:
            info = self.get_hardware_info()
        elif choice == 11:
            info = self.get_performance_info()
        elif choice == 12:
            info = self.get_security_info()
        elif choice == 13:
            info = self.get_installed_apps()
        elif choice == 14:
            info = self.get_system_health()
        elif choice == 15:
            info = (self.get_system_info() + self.get_network_info() +
                   self.get_cpu_info() + self.get_memory_info() +
                   self.get_disk_info() + self.get_boot_time() +
                   self.get_python_info() + self.get_user_info() +
                   self.get_display_info() + self.get_hardware_info() +
                   self.get_performance_info() + self.get_security_info() +
                   self.get_installed_apps() + self.get_system_health())
        elif choice == 0:
            return
        else:
            self.show_menu()
            return
            
        self.terminal.append_text(info, self.terminal.colors['output'])
