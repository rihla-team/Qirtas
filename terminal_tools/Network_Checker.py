import speedtest
import socket
import psutil
import subprocess
from datetime import datetime
from .base_tool import TerminalTool
import time
from PyQt5.QtCore import pyqtSignal, QObject,Qt, QThread
import threading
import subprocess
from ping3 import ping
import os

class SpeedTestThread(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)

    def run(self):
        try:
            self.progress.emit("جاري تهيئة اختبار السرعة...\n")
            
            # إنشاء كائن Speedtest
            st = speedtest.Speedtest()
            
            self.progress.emit("جاري البحث عن أفضل خادم...\n")
            st.get_best_server()
            
            self.progress.emit("جاري قياس سرعة التنزيل...\n")
            download_speed = st.download() / 1_000_000  # تحويل إلى ميجابت/ثانية
            
            self.progress.emit("جاري قياس سرعة الرفع...\n")
            upload_speed = st.upload() / 1_000_000  # تحويل إلى ميجابت/ثانية
            
            self.progress.emit("جاري قياس زمن الاستجابة...\n")
            ping = st.results.ping
            
            self.finished.emit({
                'download': download_speed,
                'upload': upload_speed,
                'ping': ping
            })
            
        except Exception as e:
            self.progress.emit(f"فشل في فحص السرعة: {str(e)}\n")

class NetworkQualityChecker(TerminalTool, QObject):
    update_terminal_signal = pyqtSignal(str, str)  # تعريف الإشارة لتحديث الواجهة

    def __init__(self, terminal):
        super().__init__(terminal)
        QObject.__init__(self)  # تأكد من استدعاء مُنشئ QObject
        self.name = "فحص الشبكة"
        self.description = "أداة لفحص جودة الشبكة وعرض التفاصيل والاختبارات المتقدمة"
        self.usage = ("فحص الشبكة [--مساعدة | --سرعة | --معلومات | --اختبار-الخادم | "
                      "--عرض-الخوادم | --عرض-جميع-الشبكات | --فحص-الاتصال <خادم> | "
                      "--تفاصيل | --تاريخ | --إعادة-الاتصال | --تشخيص]")
        self.category = "الشبكة"
        self.update_terminal_signal.connect(self.update_terminal)  # توصيل الإشارة بدالة التحديث
        self.original_key_press_event = self.terminal.keyPressEvent  # حفظ معالج الأحداث الأصلي
        self.speed_thread = None

    def update_terminal(self, text, color):
        self.terminal.append_text(text, self.terminal.colors[color])

    def execute(self, args):
        save_output = "--حفظ" in args or "-ح" in args
        output = ""

        if "--مساعدة" in args or "-م" in args:
            output = self.show_help()
        elif "--سرعة" in args or "-س" in args:
            output = self.check_speed()
        elif "--معلومات" in args or "-ع" in args:
            output = self.check_connection_info()
        elif "--اختبار-الخادم" in args or "-خ" in args:
            output = self.test_best_server()
        elif "--عرض-الخوادم" in args or "-ق" in args:
            output = self.list_best_servers()
        elif "--عرض-جميع-الشبكات" in args or "-ش" in args:
            output = self.list_all_networks()
        elif "--فحص-الاتصال" in args or "-ف" in args:
            output = self.ping_server(args)
        elif "--تفاصيل" in args or "-ت" in args:
            output = self.show_detailed_info()
        elif "--تاريخ" in args or "-ر" in args:
            output = self.log_results()
        elif "--إعادة-الاتصال" in args or "-ا" in args:
            output = self.reset_network()
        elif "--تشخيص" in args or "-ص" in args:
            output = self.run_diagnostics()
        elif "--مراقبة" in args or "-مق" in args:
            self.monitor_network(save_to_file=save_output)
        else:
            output = self.check_speed()
            output = self.check_connection_info()

        if save_output and output:
            with open("سجل_الشبكة.txt", "a", encoding="utf-8") as log_file:
                log_file.write(output)
                self.terminal.append_text("تم حفظ النتائج في سجل_الشبكة.txt\n", self.terminal.colors['success'])

    def check_speed(self):
        self.terminal.append_text("\n--- فحص سرعة الإنترنت ---\n", self.terminal.colors['header'])
        output = "\n--- فحص سرعة الإنترنت ---\n"
        
        self.speed_thread = SpeedTestThread()
        self.speed_thread.progress.connect(self.handle_speed_progress)
        self.speed_thread.finished.connect(self.handle_speed_results)
        self.speed_thread.start()
        
        return output
        
    def handle_speed_progress(self, message):
        self.terminal.append_text(message, self.terminal.colors['info'])
        
    def handle_speed_results(self, results):
        output = f"""
سرعة التنزيل: {results['download']:.2f} ميجابت/ثانية
سرعة الرفع: {results['upload']:.2f} ميجابت/ثانية
زمن الاستجابة: {results['ping']:.2f} مللي ثانية
"""
        self.terminal.append_text(output, self.terminal.colors['success'])

    def check_connection_info(self):
        self.terminal.append_text("\n--- معلومات الاتصال ---\n", self.terminal.colors['header'])
        output = "\n--- معلومات الاتصال ---\n"
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            host_text = f"اسم المضيف: {hostname}\n"
            ip_text = f"عنوان ب.ا المحلي: {local_ip}\n"
            self.terminal.append_text(host_text, self.terminal.colors['output'])
            self.terminal.append_text(ip_text, self.terminal.colors['output'])
            output += host_text + ip_text

            net_io = psutil.net_io_counters()
            recv_text = f"البيانات المستلمة: {net_io.bytes_recv / (1024**2):.2f} ميجابايت\n"
            sent_text = f"البيانات المرسلة: {net_io.bytes_sent / (1024**2):.2f} ميجابايت\n"
            self.terminal.append_text(recv_text, self.terminal.colors['output'])
            self.terminal.append_text(sent_text, self.terminal.colors['output'])
            output += recv_text + sent_text
        except Exception as e:
            error_text = f"خطأ في معلومات الاتصال: {str(e)}\n"
            self.terminal.append_text(error_text, self.terminal.colors['error'])
            output += error_text
        return output

    def test_best_server(self):
        self.terminal.append_text("\n--- أفضل خادم متاح ---\n", self.terminal.colors['header'])
        output = "\n--- أفضل خادم متاح ---\n"
        try:
            st = speedtest.Speedtest()
            best = st.get_best_server()
            best_server_text = f"الخادم الأفضل: {best['host']} ({best['country']})\n"
            self.terminal.append_text(best_server_text, self.terminal.colors['output'])
            output += best_server_text
        except Exception as e:
            error_text = f"خطأ في اختبار الخادم: {str(e)}\n"
            self.terminal.append_text(error_text, self.terminal.colors['error'])
            output += error_text
        return output

    def list_best_servers(self):
        self.terminal.append_text("\n--- قائمة أفضل الخوادم ---\n", self.terminal.colors['header'])
        output = "\n--- قائمة أفضل الخوادم ---\n"
        try:
            st = speedtest.Speedtest()
            servers = st.get_servers()
            best_servers = sorted(servers.keys())[:5]
            for server in best_servers:
                server_text = f"الخادم: {server}\n"
                self.terminal.append_text(server_text, self.terminal.colors['output'])
                output += server_text
        except Exception as e:
            error_text = f"خطأ في عرض الخوادم: {str(e)}\n"
            self.terminal.append_text(error_text, self.terminal.colors['error'])
            output += error_text
        return output

    def list_all_networks(self):
        self.terminal.append_text("\n--- جميع الشبكات المتصلة ---\n", self.terminal.colors['header'])
        output = "\n--- جميع الشبكات المتصلة ---\n"
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                interface_text = f"واجهة الشبكة: {interface}\n"
                self.terminal.append_text(interface_text, self.terminal.colors['output'])
                output += interface_text
                for addr in addrs:
                    addr_text = f" - {addr.address}\n"
                    self.terminal.append_text(addr_text, self.terminal.colors['output'])
                    output += addr_text
        except Exception as e:
            error_text = f"خطأ في عرض الشبكات: {str(e)}\n"
            self.terminal.append_text(error_text, self.terminal.colors['error'])
            output += error_text
        return output

    def ping_server(self, args):
        self.terminal.append_text("\n--- فحص الاتصال بالخادم ---\n", self.terminal.colors['header'])
        output = "\n--- فحص الاتصال بالخادم ---\n"
        try:
            if "--فحص-الاتصال" in args:
                index = args.index("--فحص-الاتصال")
                server = args[index + 1] if len(args) > index + 1 else "8.8.8.8"
            elif "-ف" in args:
                index = args.index("-ف")
                server = args[index + 1] if len(args) > index + 1 else "8.8.8.8"
            else:
                server = "8.8.8.8"
            
            result = subprocess.run(["ping", "-n", "4", server], capture_output=True, text=True)
            
            # تعريب النصوص
            output += result.stdout.replace("Pinging", "جارٍ فحص الاتصال بـ")
            output = output.replace("with 32 bytes of data:", "بـ 32 بايت من البيانت:")
            output = output.replace("Reply from", "الرد من")
            output = output.replace("bytes", "بايت")
            output = output.replace("Approximate round trip times in milli-seconds:", "الوقت التقريبي للرحلة ذهابًا وإيابًا بالمللي ثانية:")
            output = output.replace("time", "الوقت")
            output = output.replace("TTL", "وقت البقاء")
            output = output.replace("Ping statistics for", "إحصائيات الفحص لـ")
            output = output.replace("Packets", "الحزم")
            output = output.replace("Sent", "المرسلة")
            output = output.replace("Received", "المستلمة")
            output = output.replace("Lost", "المفقودة")
            output = output.replace("(0% loss)", "(0% فقدان)")
            output = output.replace("Minimum", "الحد الأدنى")
            output = output.replace("Maximum", "الحد الأقصى")
            output = output.replace("Average", "المتوسط")
            output = output.replace("ms", "م.ث")
            
            # تقسيم النصوص وتلوين الردود والإحصائيات
            lines = output.splitlines()
            for line in lines:
                if "الرد من" in line:
                    self.terminal.append_text(line + "\n", self.terminal.colors['response'])
                elif "إحصائيات الفحص" in line or "الوقت التقريبي للرحلة" in line:
                    self.terminal.append_text(line + "\n", self.terminal.colors['stats'])
                else:
                    self.terminal.append_text(line + "\n", self.terminal.colors['output'])
        except Exception as e:
            error_text = f"خطأ في فحص الاتصال: {str(e)}\n"
            self.terminal.append_text(error_text, self.terminal.colors['error'])
            output += error_text
        return output

    def show_detailed_info(self):
        self.terminal.append_text("\n--- تفاصيل الشبكة ---\n", self.terminal.colors['header'])
        output = "\n--- تفاصيل الشبكة ---\n"
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                interface_text = f"واجهة الشبكة: {interface}\n"
                self.terminal.append_text(interface_text, self.terminal.colors['output'])
                output += interface_text
                for addr in addrs:
                    addr_text = f" - {addr.family}: {addr.address}\n"
                    self.terminal.append_text(addr_text, self.terminal.colors['output'])
                    output += addr_text
        except Exception as e:
            error_text = f"خطأ في عرض التفاصيل: {str(e)}\n"
            self.terminal.append_text(error_text, self.terminal.colors['error'])
            output += error_text
        return output

    def log_results(self):
        self.terminal.append_text("\n--- ت��جيل النتائج ---\n", self.terminal.colors['header'])
        output = "\n--- تسجيل النتائج ---\n"
        try:
            net_io = psutil.net_io_counters()

            with open("سجل_الشبكة.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"تاريخ: {datetime.now()}\n")
                log_file.write(f"اسم المضيف: {socket.gethostname()}\n")
                log_file.write(f"عنوان ب.ا: {socket.gethostbyname(socket.gethostname())}\n\n")
                log_file.write(f"البيانات المستلمة: {net_io.bytes_recv / (1024**2):.2f} ميجابايت\n")
                log_file.write(f"البيانات المرسلة: {net_io.bytes_sent / (1024**2):.2f} ميجابايت\n")
                log_file.write("\n")

            self.terminal.append_text("تم تسجيل النتائج في سجل_الشبكة.txt\n", self.terminal.colors['success'])
            output += "تم تسجيل النتائج في سجل_الشبكة.txt\n"
        except Exception as e:
            error_text = f"خطأ في تسجيل النتائج: {str(e)}\n"
            self.terminal.append_text(error_text, self.terminal.colors['error'])
            output += error_text
        return output

    def reset_network(self):
        self.terminal.append_text("\n--- إعادة الاتصال ---\n", self.terminal.colors['header'])
        output = "\n--- إعادة الاتصال ---\n"
        try:
            subprocess.run(["sudo", "systemctl", "restart", "networking"], check=True)
            success_text = "تمت إعاد تعيين الشبكة بنجاح.\n"
            self.terminal.append_text(success_text, self.terminal.colors['success'])
            output += success_text
        except Exception as e:
            error_text = f"خطأ في إعادة الاتصال: {str(e)}\n"
            self.terminal.append_text(error_text, self.terminal.colors['error'])
            output += error_text
        return output

    def run_diagnostics(self):
        self.terminal.append_text("\n--- تشخيص شامل للشبكة ---\n", self.terminal.colors['header'])
        output = "\n--- تشخيص شامل للشبكة ---\n"
        output += self.check_speed()
        output += self.check_connection_info()
        output += self.test_best_server()
        output += self.list_all_networks()
        return output

    def show_help(self):
        self.terminal.append_text("\n--- ديل الاستخدام: فحص الشبكة ---\n", self.terminal.colors['header'])
        help_text = """
استخدام الأداة:
  فحص_الشبكة [خيارات]

الخيارات المتاحة:
  -م, --مساعدة            عرض هذا الدليل.
  -س, --سرعة              فحص سرعة الإنترنت (تنزيل ورفع).
  -ع, --معلومات           عرض معلومات الاتصال الأاسية (اسم لمضيف وعنوان ب.ا المحلي).
  -خ, --اختبار-الخادم     عرض أفضل خادم متاح لاختبار السرعة.
  -ق, --عرض-الخوادم        عرض قائمة بأفضل 5 خوادم متوفرة.
  -ش, --عرض-جميع-الشبكات   عر جميع اجهة الشبكة المتصلة على الجهاز وعناوين ب.ا الخاصة بها.
  -ف, --فحص-الاتصال <خادم> اختبار إمكانية الاتصال بدم معين باستخدام Ping (افتراضي: 8.8.8.8).
  -ت, --تفاصيل            عرض تفاصيل أعمق عن اجهزة الشبكة مثل عنوان MAC وسرعة الشبكة.
  -ر, --تاريخ             تسجيل نتائج الاختبارات وحظها في ملف (سجل_الشبكة.txt).
  -ا, --إعادة-الاتصال      إعادة تعيين الشبكة (فصل ثم إعادة الاتصل).
  -, --تشخيص             تفيذ تحليل شامل يشمل جميع الخصاص السابقة.
  -مق, --مراقبة             مراقبة الشبكة بحي يتم عرض الحزم المستقبلة المرسلة بشكل مباشر في التيرمنال.
  -ح, --حفظ               حفظ النتائج في مف (سجل_الشبكة.txt).

أمثلة:
  فحص الشبكة -س
  فحص الشبكة -ع
  فحص الشبكة -ف مثال.شبكة
  فحص الشبكة -ر
"""

        self.terminal.append_text(help_text, self.terminal.colors['output'])

    def monitor_network(self, save_to_file=False):

        def network_monitoring():
            self.update_terminal_signal.emit("\n--- مراقبة الشبكة ---\n", 'header')
            output = "\n--- مراقبة الشبكة ---\n"
            self.monitoring = True
            try:
                prev_net_io = psutil.net_io_counters()
                self.update_terminal_signal.emit("اضغط ENTER للخروج من المراقبة.\n", 'info')
                output += "اضغط ENTER للخروج من المراقبة.\n"

                while self.monitoring:
                    net_io = psutil.net_io_counters()
                    bytes_sent = net_io.bytes_sent - prev_net_io.bytes_sent
                    bytes_recv = net_io.bytes_recv - prev_net_io.bytes_recv
                    packets_sent = net_io.packets_sent - prev_net_io.packets_sent
                    packets_recv = net_io.packets_recv - prev_net_io.packets_recv
                    errin = net_io.errin - prev_net_io.errin
                    errout = net_io.errout - prev_net_io.errout
                    dropin = net_io.dropin - prev_net_io.dropin
                    dropout = net_io.dropout - prev_net_io.dropout

                    send_speed = bytes_sent / 1024  # kB
                    recv_speed = bytes_recv / 1024  # kB

                    total_packets = packets_sent + packets_recv
                    packet_loss_rate = ((dropin + dropout) / total_packets * 100) if total_packets > 0 else 0

                    zaman_istijaba = self.get_average_ping('8.8.8.8', attempts=1)
                    zaman_istijaba_motawasit = self.get_average_ping('8.8.8.8', attempts=5)

                    status_text = f"""
======================================================
البيانات المرسلة: {bytes_sent / 1024:.2f} كيلوبايت ({packets_sent} حزمة)
البيانات المرسلة بالميجابايت: {bytes_sent / (1024*1024):.2f} ميجابايت
معدل نقل البيانات المرسلة: {(bytes_sent / 1024) / 60:.2f} يلوبايت/دقيقة
متوسط حجم الحزمة المرسلة: {(bytes_sent / packets_sent) if packets_sent > 0 else 0:.2f} بايت/حزمة
عنوان IP المرسل: {psutil.net_connections()[0].laddr.ip if psutil.net_connections() else 'غير متوفر'}
المنفذ المرسل: {psutil.net_connections()[0].laddr.port if psutil.net_connections() else 'غير متوفر'}

البيانات المستلمة: {bytes_recv / 1024:.2f} كيلوبايت ({packets_recv} حزمة) 
البيانات المستلمة بالميجابايت: {bytes_recv / (1024*1024):.2f} ميجابايت
معدل نقل البيانات المستلمة: {(bytes_recv / 1024) / 60:.2f} كيلوبايت/دقيقة
متوسط حجم الحزمة المستلمة: {(bytes_recv / packets_recv) if packets_recv > 0 else 0:.2f} بايت/حزمة
عنوان IP المستلم: {psutil.net_connections()[0].raddr.ip if psutil.net_connections() and psutil.net_connections()[0].raddr else 'غير متوفر'}
المنفذ المستلم: {psutil.net_connections()[0].raddr.port if psutil.net_connections() and psutil.net_connections()[0].raddr else 'غير متوفر'}

سرعة الإرسال: {send_speed:.2f} كيلوبايت/ثانية
سرعة الإرسال بالميجابت: {send_speed / 1024 * 8:.2f} ميجابت/ثانية
معدل الإرسال بالحزم: {packets_sent / 60:.2f} حزمة/دقيقة
بروتوكول الإرسال: {psutil.net_connections()[0].type if psutil.net_connections() else 'غير متوفر'}

سرعة الاستقبال: {recv_speed:.2f} كيلوبايت/ثانية  
سرعة الاستقبال بالميجابت: {recv_speed / 1024 * 8:.2f} ميجابت/ثانية
معدل الاستقبال بالحزم: {packets_recv / 60:.2f} حزمة/دقيقة
حالة الاتصال: {psutil.net_connections()[0].status if psutil.net_connections() else 'غير متوفر'}

زمن الاستجابة: {zaman_istijaba:.2f} مللي ثانية
زمن الاستجابة المتوسط: {zaman_istijaba_motawasit:.2f} مللي ثانية

معدل إعادة الإرسال:
عدد الحزم المعاد إرسالها: {net_io.retransmits if hasattr(net_io, 'retransmits') else 'غير متوفر'}
نسبة إعادة الإرسال: {(net_io.retransmits / packets_sent * 100) if hasattr(net_io, 'retransmits') and packets_sent > 0 else 0:.2f}%

نوع الاتصال: {psutil.net_if_addrs()[list(psutil.net_if_addrs().keys())[0]][0].address if psutil.net_if_addrs() else 'غير متوفر'}
الوقت منذ آخر اتصال: {datetime.now() - datetime.fromtimestamp(psutil.boot_time()) if psutil.boot_time() else 'غير متوفر'}

توقعات استخدام البيانات:
استهلاك البيانات المتوقع (ساعة): {(bytes_sent + bytes_recv) / 1024 * 60:.2f} كيلوبايت
استهلاك البيانات المتوقع (يوم): {(bytes_sent + bytes_recv) / 1024 * 60 * 24:.2f} كيلوبايت
استهلاك البيانات المتوقع (شهر): {(bytes_sent + bytes_recv) / 1024 * 60 * 24 * 30:.2f} كيلوبايت

أخطاء الاستقبال: {errin} خطأ
نسبة أخطاء الاستقبال: {(errin / packets_recv * 100) if packets_recv > 0 else 0:.2f}%
تصنيف أخطاء الاستقبال: {"منخفض" if errin < 10 else "متوسط" if errin < 50 else "مرتفع"}

تقارير الأمان:
عدد المنافذ المفتوحة: {len([conn for conn in psutil.net_connections() if conn.status == 'LISTEN'])}
المنافذ المفتوحة: {', '.join([str(conn.laddr.port) for conn in psutil.net_connections() if conn.status == 'LISTEN']) or 'لا يوجد'}
الاتصالات النشطة: {len([conn for conn in psutil.net_connections() if conn.status == 'ESTABLISHED'])}
الاتصالات المشبوهة: {len([conn for conn in psutil.net_connections() if conn.raddr and conn.raddr.ip.startswith(('192.168', '10.', '172.16'))])}
حالة جدار الحماية: {self.check_firewall_status()}
مستوى التشفير: {"قوي" if any(conn.type == 'SOCK_STREAM' for conn in psutil.net_connections()) else "ضعيف"}
تنبيهات أمنية: {"يوجد اتصالات مشبوهة" if len([conn for conn in psutil.net_connections() if conn.raddr and conn.raddr.ip.startswith(('192.168', '10.', '172.16'))]) > 0 else "لا يوجد تنبيهات"}
عدد محاولات الاتصال الفاشلة: {len([conn for conn in psutil.net_connections() if conn.status == 'CLOSE_WAIT'])}
البروتوكولات المستخدمة: {', '.join(set([str(conn.type) for conn in psutil.net_connections()]))}
المنافذ عالية الخطورة: {', '.join([str(conn.laddr.port) for conn in psutil.net_connections() if conn.laddr.port in [21, 22, 23, 25, 53, 139, 445, 3389]])}
عدد الاتصالات المشفرة: {len([conn for conn in psutil.net_connections() if conn.type == 'SOCK_STREAM' and conn.status == 'ESTABLISHED'])}
مستوى الأمان العام: {"مرتفع" if os.system("netsh advfirewall show allprofiles state") == 0 and len([conn for conn in psutil.net_connections() if conn.laddr.port in [21, 22, 23, 25, 53, 139, 445, 3389]]) == 0 else "متوسط" if os.system("netsh advfirewall show allprofiles state") == 0 else "منخفض"}
توصيات الأمان: {"لا توجد مشاكل" if os.system("netsh advfirewall show allprofiles state") == 0 and len([conn for conn in psutil.net_connections() if conn.laddr.port in [21, 22, 23, 25, 53, 139, 445, 3389]]) == 0 else "يرجى تفعيل جدار الحماية وإغلاق المنافذ غير المستخدمة"}
تحليل التهديدات:
عدد محاولات DDoS المكتشفة: {len([conn for conn in psutil.net_connections() if conn.status == 'ESTABLISHED' and sum(1 for c in psutil.net_connections() if c.raddr and c.raddr.ip == conn.raddr.ip) > 100]) if psutil.net_connections() else 0}
نوع الهجوم المحتمل: {"هجوم DDoS" if len([conn for conn in psutil.net_connections() if conn.status == 'ESTABLISHED' and sum(1 for c in psutil.net_connections() if c.raddr and c.raddr.ip == conn.raddr.ip) > 100]) > 0 else "هجوم التصيد" if len([conn for conn in psutil.net_connections() if conn.laddr.port in [25, 587, 465]]) > 0 else "لا يوجد تهديد مكتشف"}
مستوى خطورة التهديد: {"مرتفع" if len([conn for conn in psutil.net_connections() if conn.status == 'ESTABLISHED' and sum(1 for c in psutil.net_connections() if c.raddr and c.raddr.ip == conn.raddr.ip) > 100]) > 0 else "متوسط" if len([conn for conn in psutil.net_connections() if conn.laddr.port in [25, 587, 465]]) > 0 else "منخفض"}
عناوين IP المشبوهة: {', '.join(set([conn.raddr.ip for conn in psutil.net_connections() if conn.raddr and sum(1 for c in psutil.net_connections() if c.raddr and c.raddr.ip == conn.raddr.ip) > 50])) or 'لا يوجد'}
نشاط الشبكة غير الطبيعي: {"مرتفع" if packets_recv > 10000 or packets_sent > 10000 else "طبيعي"}
توصيات الأمان الفورية: {"إيقاف الخدمة فوراً وتحديث إعدادات جدار الحماية" if len([conn for conn in psutil.net_connections() if conn.status == 'ESTABLISHED' and sum(1 for c in psutil.net_connections() if c.raddr and c.raddr.ip == conn.raddr.ip) > 100]) > 0 else "مراقبة النشاط" if packets_recv > 10000 or packets_sent > 10000 else "لا يوجد إجراء مطلوب"}
تحليل الأخطاء المتقدم:
أخطاء HTTP: {len([conn for conn in psutil.net_connections() if conn.laddr.port == 80 and conn.status == 'CLOSE_WAIT'])}
أخطاء FTP: {len([conn for conn in psutil.net_connections() if conn.laddr.port == 21 and conn.status == 'CLOSE_WAIT'])}
أخطاء DNS: {len([conn for conn in psutil.net_connections() if conn.laddr.port == 53 and conn.status == 'CLOSE_WAIT'])}
أخطاء موارد النظام: {"نعم" if psutil.virtual_memory().percent > 90 or psutil.cpu_percent() > 90 else "لا"}
مشاكل تعريفات الشبكة: {"نعم" if packet_loss_rate > 20 and errin + errout > 100 else "لا"}
أخطاء بروتوكول TCP: {len([conn for conn in psutil.net_connections() if conn.type == 'SOCK_STREAM' and conn.status == 'CLOSE_WAIT'])}
أخطاء بروتوكول UDP: {len([conn for conn in psutil.net_connections() if conn.type == 'SOCK_DGRAM' and conn.status == 'CLOSE_WAIT'])}

تحليل التهديدات المتقدم:
محاولات اختراق SSH: {len([conn for conn in psutil.net_connections() if conn.laddr.port == 22 and conn.status == 'SYN_RECV'])}
هجمات Man-in-the-Middle المحتملة: {"محتمل" if any(conn.type == 'SOCK_RAW' for conn in psutil.net_connections()) else "غير محتمل"}
محاولات التصيد: {len([conn for conn in psutil.net_connections() if conn.laddr.port in [25, 587, 465] and conn.status == 'ESTABLISHED'])}
نشاط برمجيات ضارة محتمل: {"مرتفع" if len([conn for conn in psutil.net_connections() if conn.raddr and conn.raddr.port in [6666, 6667, 6668, 6669]]) > 0 else "منخفض"}
اتصالات مشبوهة بالخارج: {len([conn for conn in psutil.net_connections() if conn.raddr and not conn.raddr.ip.startswith(('192.168', '10.', '172.16', '127.'))])}
محاولات فحص المنافذ: {"نعم" if len(set([conn.laddr.port for conn in psutil.net_connections()])) > 100 else "لا"}

توصيات أمنية استباقية:
تحديثات مطلوبة: {self.check_updates_status()}
فحص الفيروسات: {"مطلوب" if len([conn for conn in psutil.net_connections() if conn.raddr and conn.raddr.port in [6666, 6667, 6668, 6669]]) > 0 else "غير مطلوب حالياً"}
تدابير وقائية موصى بها:
- {"تحديث دار الحماية" if len([conn for conn in psutil.net_connections() if conn.laddr.port in [21, 22, 23]]) > 0 else ""}
- {"تفعيل التشفير للمنافذ المفتوحة" if len([conn for conn in psutil.net_connections() if conn.status == 'LISTEN']) > 10 else ""}
- {"مراجعة سياسات الأمان" if len([conn for conn in psutil.net_connections() if conn.raddr and not conn.raddr.ip.startswith(('192.168', '10.', '172.16', '127.'))]) > 5 else ""}
- {"تفعيل نظام كشف التطفل" if packet_loss_rate > 10 or errin + errout > 50 else ""}

إجراءات فورية مطلوبة:
{"إغلاق المنافذ غير المستخدمة" if len([conn for conn in psutil.net_connections() if conn.status == 'LISTEN']) > 20 else ""}
{"تحديث برامج الأمان" if len([conn for conn in psutil.net_connections() if conn.raddr and conn.raddr.port in [6666, 6667, 6668, 6669]]) > 0 else ""}
{"فحص شامل للنظام" if packet_loss_rate > 20 and errin + errout > 100 else ""}
جدول المراقبة الدورية:
فحص المنافذ: كل 6 ساعات
تحديث قواعد جدار الحماية: أسبوعياً
فحص البرمجيات الضارة: يومياً
مراجعة سجلات الأمان: كل 12 ساعة

البروتوكولات الأمنية:
بروتوكول SSL/TLS: {"مفعل" if any(conn.laddr.port in [443, 8443] for conn in psutil.net_connections()) else "غير مفعل"}
إصدار SSL/TLS: {"TLSv1.3" if any(conn.laddr.port == 443 for conn in psutil.net_connections()) else "TLSv1.2" if any(conn.laddr.port == 8443 for conn in psutil.net_connections()) else "غير متوفر"}
مستوى التشفير SSL: {"عالي (256-bit)" if any(conn.laddr.port == 443 for conn in psutil.net_connections()) else "متوسط (128-bit)" if any(conn.laddr.port == 8443 for conn in psutil.net_connections()) else "غير متوفر"}
شهادات SSL: {"صالحة" if any(conn.laddr.port in [443, 8443] for conn in psutil.net_connections()) else "غير متوفرة"}
حالة HTTPS: {"مفعل" if any(conn.laddr.port == 443 for conn in psutil.net_connections()) else "غير مفعل"}
بروتوكول SSH: {"مفعل" if any(conn.laddr.port == 22 for conn in psutil.net_connections()) else "غير مفعل"}
بروتوكول IPSec: {"مفعل" if any(conn.type == 'SOCK_RAW' for conn in psutil.net_connections()) else "غير مفعل"}
تقييم الأمان: {"ممتاز" if any(conn.laddr.port in [443, 8443] for conn in psutil.net_connections()) and not any(conn.laddr.port in [21, 23] for conn in psutil.net_connections()) else "متوسط" if any(conn.laddr.port == 22 for conn in psutil.net_connections()) else "ضعيف"}
مؤشر الخطورة الإجمالي: {"مرتفع" if len([conn for conn in psutil.net_connections() if conn.raddr and conn.raddr.port in [6666, 6667, 6668, 6669]]) > 0 or packet_loss_rate > 20 else "متوسط" if len([conn for conn in psutil.net_connections() if conn.status == 'LISTEN']) > 20 else "منخفض"}

أخطاء الإرسال: {errout} خطأ
نسبة أخطاء الإرسال: {(errout / packets_sent * 100) if packets_sent > 0 else 0:.2f}%
تصنيف أخطاء الإرسال: {"منخفض" if errout < 10 else "متوسط" if errout < 50 else "مرتفع"}

الحزم المفقودة (استقبال): {dropin} حزمة
نسبة فقد حزم الاستقبال: {(dropin / packets_recv * 100) if packets_recv > 0 else 0:.2f}%

الحزم المفقودة (إرسال): {dropout} حزمة
نسبة فقد حزم الإرسال: {(dropout / packets_sent * 100) if packets_sent > 0 else 0:.2f}%

معدل فقد الحزم الإجمالي: {packet_loss_rate:.2f}%
تصنيف فقد الحزم: {"متاز" if packet_loss_rate < 1 else "جيد" if packet_loss_rate < 5 else "متوسط" if packet_loss_rate < 10 else "ضعيف"}

تحسينات الأداء المقترحة:
تحسين السرعة: {"تحديث برامج تشغيل بطاقة الشبكة" if packet_loss_rate > 5 else "لا يلزم تحسين"}
تحسين الاستقرار: {"ضبط إعدادات جهاز التوجيه" if errin + errout > 10 else "لا يلزم تحسين"}
تحسين الأمان: {"تفعيل جدار الحماية وتحديث إعداداته" if os.system("netsh advfirewall show allprofiles state") != 0 else "لا يلزم تحسين"}

توصيات تحسين الأداء:
- تحديث برامج تشغيل بطاقة الشبكة {""if packet_loss_rate > 5 else "لا يلزم تحسين"}
- ضبط إعدادات DNS {""if packet_loss_rate > 5 else "لا يلزم تحسين"}
- تنظيف ذاكرة التخزين المؤقت للشبكة {""if packet_loss_rate > 5 else "لا يلزم تحسين"}
- إعادة تشغيل جهاز التوجيه تغيير قناة الواي فاي {""if packet_loss_rate > 5 else "لا يلزم تحسين"} 
- تحديث البرامج الثابتة لجهاز التوجيه {""if errin + errout > 10 else "لا يلزم تحسين"}
- تفعيل جدار الحماية {""if os.system("netsh advfirewall show allprofiles state") != 0 else "لا يلزم تحسين"}
- تحديث إعدادات الأمان {""if os.system("netsh advfirewall show allprofiles state") != 0 else "لا يلزم تحسين"}
- مراجعة المنافذ المفتوحة {""if os.system("netsh advfirewall show allprofiles state") != 0 else "لا يلزم تحسين"}

مستوى أولوية التحسينات: {"عالي" if packet_loss_rate > 10 or errin + errout > 50 else "متوسط" if packet_loss_rate > 5 or errin + errout > 10 else "منخفض"}
الوقت المقدر للتنفيذ: {"30-60 دقيقة" if packet_loss_rate > 10 or errin + errout > 50 else "15-30 دقيقة" if packet_loss_rate > 5 or errin + errout > 10 else "5-15 دقيقة"}
التأثير المتوقع: {"تحسن كبير في الأداء" if packet_loss_rate > 10 or errin + errout > 50 else "تحسن متوسط" if packet_loss_rate > 5 or errin + errout > 10 else "تحسن طفيف"}

حالة الشبكة: {"جيدة" if errin + errout == 0 else "تحتاج مراجعة"}
التقييم العام: {"ممتاز" if packet_loss_rate < 1 and errin + errout == 0 else "جيد" if packet_loss_rate < 5 and errin + errout < 10 else "متوسط" if packet_loss_rate < 10 and errin + errout < 50 else "ضعيف"}
======================================================
"""
                    self.update_terminal_signal.emit(status_text, 'output')
                    output += status_text

                    if save_to_file:
                        with open("سجل_الشبكة.txt", "a", encoding="utf-8") as f:
                            f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(status_text)

                    prev_net_io = net_io
                    time.sleep(1)

            except Exception as e:
                error_text = f"خطأ في مراقبة الشبكة: {str(e)}\n"
                self.update_terminal_signal.emit(error_text, 'error')
                output += error_text

        # حفظ معالج الأحداث الأصلي
        original_key_press_event = self.terminal.keyPressEvent

        def custom_key_press_event(event):
            if event.key() in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_C] and event.modifiers() == Qt.ControlModifier or event.key() == Qt.Key_Escape:
                self.stop_monitoring()
                self.terminal.display_prompt()
            else:
                super(self.terminal.__class__, self.terminal).keyPressEvent(event)

        self.terminal.keyPressEvent = custom_key_press_event
        monitoring_thread = threading.Thread(target=network_monitoring)
        monitoring_thread.start()
        return "تم بنجاح تشغي مراقبة الشبكة. اضغط ENTER أو Ctrl+C لإيقاف المراقبة.\n"

    def stop_monitoring(self):
        self.monitoring = False
        self.update_terminal_signal.emit("تم إيقاف مراقبة الشبكة.\n", 'success')
        # إعادة تعيين معالج الأحداث الأصلي
        self.terminal.keyPressEvent = self.original_key_press_event

    def get_average_ping(self, host, attempts=5):
        total_time = 0
        successful_pings = 0
        for _ in range(attempts):
            response_time = ping(host)
            if response_time is not None:
                total_time += response_time
                successful_pings += 1
        return (total_time / successful_pings) if successful_pings > 0 else None

    def check_firewall_status(self):
        try:
            result = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles", "state"],
                capture_output=True,
                text=True
            )
            return "مفعل" if result.returncode == 0 else "غير مفعل"
        except Exception:
            return "غير معروف"

    def check_updates_status(self):
        try:
            result = subprocess.run(
                ["wmic", "qfe", "list", "brief", "/format:table"],
                capture_output=True,
                text=True
            )
            return "نعم" if result.returncode != 0 else "لا"
        except Exception:
            return "غير معروف"


