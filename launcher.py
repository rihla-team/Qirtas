import os
import sys
import subprocess
import logging
import importlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

def setup_logging():
    os.makedirs('سجلات', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join('سجلات', 'المنفذ.log'), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

class DependencyCache:
    """فئة للتعامل مع التخزين المؤقت لحالة المكتبات"""
    CACHE_FILE = os.path.join('سجلات', 'dependencies_cache.json')
    CACHE_VALIDITY = timedelta(days=7)  # تمديد صلاحية التخزين المؤقت إلى 7 أيام

    @classmethod
    def load_cache(cls):
        try:
            if os.path.exists(cls.CACHE_FILE):
                with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    if datetime.fromisoformat(cache['timestamp']) + cls.CACHE_VALIDITY > datetime.now():
                        return cache['packages']
        except:
            pass
        return {}

    @classmethod
    def save_cache(cls, packages):
        try:
            os.makedirs('سجلات', exist_ok=True)  # تأكد من وجود المجلد
            cache = {
                'timestamp': datetime.now().isoformat(),
                'packages': packages
            }
            with open(cls.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False)  # استخدام ensure_ascii=False للدعم الكامل للغة العربية
        except:
            pass

def get_python_path():
    """الحصول على مسار Python من التخزين المؤقت أو البحث عنه"""
    # إذا كان البرنامج يعمل كـ EXE، نبحث عن Python في النظام
    if getattr(sys, 'frozen', False):
        # البحث عن Python في المسارات المحتملة
        possible_paths = [
            r"C:\Python39\python.exe",
            r"C:\Python310\python.exe",
            r"C:\Python311\python.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe",
        ]
        
        # توسيع متغيرات البيئة
        expanded_paths = [os.path.expandvars(path) for path in possible_paths]
        
        # البحث عن أول نسخة Python صالحة
        for path in expanded_paths:
            if os.path.exists(path):
                try:
                    subprocess.run([path, '--version'], capture_output=True, check=True)
                    # حفظ المسار الصحيح
                    try:
                        os.makedirs('سجلات', exist_ok=True)
                        with open(os.path.join('سجلات', 'python_path.txt'), 'w', encoding='utf-8') as f:
                            f.write(path)
                    except:
                        pass
                    return path
                except:
                    continue
        
        # إذا لم نجد Python، نرجع None
        return None
    
    # إذا كان البرنامج يعمل من الكود المصدري
    cache_file = os.path.join('سجلات', 'python_path.txt')
    
    # محاولة قراءة المسار من التخزين المؤقت
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                path = f.read().strip()
                if os.path.exists(path):
                    try:
                        subprocess.run([path, '--version'], capture_output=True, check=True)
                        return path
                    except:
                        pass
        except:
            pass
    
    # استخدام المسار الحالي إذا كان صالحاً
    current_python = sys.executable
    if not current_python.endswith('.exe'):  # تأكد من أنه ليس EXE
        try:
            subprocess.run([current_python, '--version'], capture_output=True, check=True)
            # حفظ المسار الصحيح
            try:
                os.makedirs('سجلات', exist_ok=True)
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(current_python)
            except:
                pass
            return current_python
        except:
            pass
    
    return None

def get_installed_packages():
    """الحصول على قائمة المكتبات المثبتة"""
    try:
        python_exe = get_python_path()
        if not python_exe:
            return {}
            
        result = subprocess.run(
            [python_exe, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            return {pkg['name'].lower(): pkg['version'] for pkg in json.loads(result.stdout)}
        return {}
        
    except Exception as e:
        logging.getLogger(__name__).error(f"خطأ في الحصول على قائمة المكتبات: {str(e)}")
        return {}

def is_package_installed(package_name, installed_packages):
    """التحقق من وجود المكتبة وإصدارها"""
    try:
        if '>=' in package_name:
            name, required_version = package_name.split('>=')
        elif '==' in package_name:
            name, required_version = package_name.split('==')
        else:
            name = package_name
            required_version = None
        
        name = name.strip().lower()
        
        if name not in installed_packages:
            return False
            
        if required_version:
            try:
                from packaging import version
                installed_version = installed_packages[name]
                return version.parse(installed_version) >= version.parse(required_version)
            except:
                return False
        return True
    except:
        return False

def install_package(args):
    """تثبيت حزمة واحدة"""
    python_exe, package, logger = args
    try:
        logger.info(f"جاري تثبيت {package}...")
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "--upgrade", package],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"تم تثبيت {package} بنجاح")
        return True, package
    except subprocess.CalledProcessError as e:
        logger.error(f"فشل في تثبيت {package}: {e.stderr}")
        return False, package
    except Exception as e:
        logger.error(f"خطأ غير متوقع في تثبيت {package}: {str(e)}")
        return False, package

def check_and_install_dependencies(logger):
    """التحقق من وجود المكتبات المطلوبة وتثبيتها"""
    # إذا كان البرنامج يعمل كـ EXE، تخطي التحقق من المكتبات
    if getattr(sys, 'frozen', False):
        return True
        
    requirements_file = 'requirements.txt'
    if not os.path.exists(requirements_file):
        logger.warning("ملف requirements.txt غير موجود")
        return True
    
    try:
        # تحميل التخزين المؤقت
        cache = DependencyCache.load_cache()
        if cache:
            # التحقق من صحة التخزين المؤقت
            installed = get_installed_packages()
            if all(pkg in installed for pkg in cache):
                logger.info("جميع المكتبات مثبتة ومحدثة")
                return True
        
        # قراءة المتطلبات
        with open(requirements_file, 'r', encoding='utf-8') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        python_exe = get_python_path()
        if not python_exe:
            logger.error("لم يتم العثور على Python لتثبيت المكتبات")
            return False
        
        # تثبيت المكتبات الأساسية أولاً
        core_packages = ["pip", "setuptools", "wheel"]
        installed = get_installed_packages()
        
        for package in core_packages:
            if package not in installed:
                try:
                    logger.info(f"تثبيت {package}...")
                    subprocess.run(
                        [python_exe, "-m", "pip", "install", "--upgrade", package],
                        check=True,
                        capture_output=True
                    )
                except Exception as e:
                    logger.error(f"فشل في تثبيت {package}: {str(e)}")
                    return False
        
        # تحديث قائمة المكتبات المثبتة
        installed = get_installed_packages()
        
        # تثبيت المكتبات المطلوبة
        packages_to_install = [
            req for req in requirements
            if not is_package_installed(req, installed)
        ]
        
        if not packages_to_install:
            logger.info("جميع المكتبات مثبتة مسبقاً")
            DependencyCache.save_cache(installed)
            return True
        
        logger.info(f"جاري تثبيت {len(packages_to_install)} مكتبة...")
        success = True
        
        # تثبيت المكتبات بشكل متوازي
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(install_package, (python_exe, package, logger))
                for package in packages_to_install
            ]
            
            for future in as_completed(futures):
                result, package = future.result()
                if not result:
                    success = False
        
        if success:
            # تحديث التخزين المؤقت
            installed = get_installed_packages()
            DependencyCache.save_cache(installed)
            logger.info("تم تثبيت جميع المكتبات بنجاح")
            return True
            
        logger.error("فشل في تثبيت بعض المكتبات")
        return False
    
    except Exception as e:
        logger.error(f"حدث خطأ أثناء التحقق من المكتبات: {str(e)}")
        return False

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # الحصول على المسار الحالي للبرنامج
        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # تحديد مسار الملف الرئيسي
        main_script = os.path.join(current_dir, 'main.py')
        
        if not os.path.exists(main_script):
            logger.error(f"لم يتم العثور على الملف الرئيسي: {main_script}")
            input("اضغط Enter للخروج...")
            return
        
        # إنشاء الملفات الضرورية إذا لم تكن موجودة
        os.makedirs('سجلات', exist_ok=True)
        python_path_file = os.path.join('سجلات', 'python_path.txt')
        if not os.path.exists(python_path_file):
            python_exe = sys.executable
            try:
                with open(python_path_file, 'w', encoding='utf-8') as f:
                    f.write(python_exe)
                logger.info(f"تم إنشاء ملف python_path.txt بنجاح")
            except Exception as e:
                logger.error(f"فشل في إنشاء ملف python_path.txt: {str(e)}")
                # في حالة الفشل، نستخدم المسار الحالي مباشرة
                python_exe = sys.executable
        
        # التحقق من المكتبات وتثبيتها
        if not check_and_install_dependencies(logger):
            logger.error("فشل في التحقق من المكتبات المطلوبة")
            input("اضغط Enter للخروج...")
            return
        
        # تشغيل البرنامج الرئيسي
        logger.info("جاري تشغيل البرنامج...")
        python_exe = get_python_path() or sys.executable
        
        # تشغيل البرنامج مرة واحدة فقط وإغلاق launcher مباشرة
        try:
            # استخدام Popen بدلاً من run للسماح بإغلاق launcher
            process = subprocess.Popen([python_exe, main_script])
            # الخروج مباشرة من البرنامج
            sys.exit(0)
        except KeyboardInterrupt:
            logger.info("تم إيقاف البرنامج بواسطة المستخدم")
        except Exception as e:
            logger.error(f"فشل في تشغيل البرنامج: {str(e)}")
            input("اضغط Enter للخروج...")
        
    except Exception as e:
        logger.error(f"حدث خطأ غير متوقع: {str(e)}")
    
    input("اضغط Enter للخروج...")

if __name__ == '__main__':
    main()
