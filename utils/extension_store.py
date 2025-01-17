import json
import os
import requests
import time
import semver
import asyncio
import aiohttp
import logging
from functools import lru_cache, wraps
from utils.arabic_logger import setup_arabic_logging, log_in_arabic
# إعداد المسجل
logger = logging.getLogger(__name__)
formatter = setup_arabic_logging()

def timed_lru_cache(seconds: int, maxsize: int = 128):
    """منفذ مخصص للكاش مع دعم وقت انتهاء الصلاحية"""
    def wrapper_decorator(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = seconds
        func.expiration = time.time() + seconds

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if time.time() >= func.expiration:
                func.cache_clear()
                func.expiration = time.time() + func.lifetime
            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_decorator

class ExtensionStore:
    def __init__(self):
        logger.info("بدء تهيئة متجر الإضافات")
        self.base_url = "https://api.github.com/repos/rihla-team/qirtas-extensions"
        self.raw_base_url = "https://raw.githubusercontent.com/rihla-team/qirtas-extensions/main"
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
        self.cache_timeout = 3600
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.platform = self.get_current_platform()
        self.app_version = self.get_app_version()
        
        self.token = self.load_token()
        self.headers = self.create_headers()
        self.memory_cache = {}
        
        self.default_icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'resources', 
            'icons', 
            'extension_default.png'
        )
        self.icon_cache = {}
        logger.info("تم تهيئة متجر الإضافات بنجاح")

    def get_current_platform(self):
        """تحديد نظام التشغيل الحالي"""
        import platform
        system = platform.system().lower()
        return {
            'windows': 'windows',
            'linux': 'linux',
            'darwin': 'macos'
        }.get(system, 'unknown')

    def get_app_version(self):
        """الحصول على إصدار التطبيق من ملف الإعدادات"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    version = settings.get('app_version', '1.0.0')
                    if not version:  # إذا كان الإصدار فارغاً
                        logger.warning("لم يتم العثور على إصدار في ملف الإعدادات")
                        return '1.0.0'
                    return version
        except Exception as e:
            logger.error(f"خطأ في قراءة الإصدار من ملف الإعدادات: {str(e)}")
        return '1.0.0'

    async def _fetch_icon(self, session, ext_name):
        """جلب أيقونة الإضافة مع التعامل مع الحالات الخاصة"""
        try:
            # جلب الاسم العربي من الكاش إذا كان موجوداً
            display_name = self.memory_cache.get(ext_name, {}).get('name', ext_name)
            
            if ext_name in self.icon_cache:
                logger.debug(f"استخدام الأيقونة المخزنة مؤقتاً للإضافة '{display_name}'")
                return self.icon_cache[ext_name]

            url = f"{self.raw_base_url}/store/extensions/{ext_name}/icon.png"
            async with session.get(url) as response:
                if response.status == 200:
                    logger.debug(f"تم جلب أيقونة الإضافة '{display_name}' بنجاح")
                    icon_data = await response.read()
                    self.icon_cache[ext_name] = icon_data
                    return icon_data
                else:
                    logger.debug(f"استخدام الأيقونة الافتراضية للإضافة '{display_name}'")
                    if os.path.exists(self.default_icon_path):
                        with open(self.default_icon_path, 'rb') as f:
                            default_icon = f.read()
                            self.icon_cache[ext_name] = default_icon
                            return default_icon
        except Exception as e:
            logger.error(f"خطأ في جلب أيقونة الإضافة '{display_name}': {str(e)}")
        return None

    async def _fetch_manifest(self, session, ext_name):
        """جلب ملف manifest.json لإضافة واحدة مع الأيقونة"""
        url = f"{self.raw_base_url}/store/extensions/{ext_name}/manifest.json"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    data['id'] = ext_name
                    
                    # حفظ الاسم العربي في الكاش للاستخدام لاحقاً
                    self.memory_cache[ext_name] = data
                    display_name = data.get('name', ext_name)
                    
                    icon_data = await self._fetch_icon(session, ext_name)
                    if icon_data:
                        icon_path = os.path.join(self.cache_dir, f"{ext_name}_icon.png")
                        with open(icon_path, 'wb') as f:
                            f.write(icon_data)
                        data['icon_path'] = icon_path
                    else:
                        data['icon_path'] = self.default_icon_path
                    
                    logger.debug(f"تم جلب ملف التعريف للإضافة '{display_name}' بنجاح")
                    return data
        except json.JSONDecodeError as e:
            logger.error(f"خطأ في تحليل JSON للإضافة '{ext_name}': {str(e)}")
        except Exception as e:
            logger.error(f"خطأ في جلب ملف التعريف للإضافة '{ext_name}': {str(e)}")
        return None

    async def _fetch_manifests_batch(self, ext_names, batch_size=10):
        """جلب مجموعة ن ملفات manifest.json بشكل متوازي"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = []
            results = []
            
            # تقسيم الطلبات إلى مجموعات
            for i in range(0, len(ext_names), batch_size):
                batch = ext_names[i:i + batch_size]
                batch_tasks = [self._fetch_manifest(session, name) for name in batch]
                # تنفيذ المجموعة
                batch_results = await asyncio.gather(*batch_tasks)
                results.extend([r for r in batch_results if r is not None])
                
                # تأخير قصير بين المجموعات لتجنب تجاوز حد الطلبات
                if i + batch_size < len(ext_names):
                    await asyncio.sleep(0.5)
            
            return results

    def process_extensions_response(self, response_data):
        """معالجة البيانات المستلمة من GitHub"""
        ext_dirs = [item['name'] for item in response_data if item['type'] == 'dir']
        
        # إنشاء حلقة غير متزامنة جديدة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # تنفيذ الطلبات على دفعات
            extensions = loop.run_until_complete(
                self._fetch_manifests_batch(ext_dirs, batch_size=5)
            )
            return extensions
        finally:
            loop.close()

    @timed_lru_cache(seconds=3600, maxsize=1)
    def get_available_extensions(self, force_refresh=False):
        """جلب قائمة الإضافات المتوفرة"""
        try:
            if not force_refresh:
                cached_data = self.get_cached_data()
                if cached_data:
                    logger.info("تم استخدام البيانات المخزنة مؤقتاً للإضافات")
                    return self.filter_compatible_extensions(cached_data)

            rate_limit = self.check_rate_limit()
            if not rate_limit['allowed']:
                logger.warning("تم تجاوز حد الطلبات")
                return self.handle_rate_limit(rate_limit['reset_time'])

            logger.info("جاري جلب قائمة الإضافات المتوفرة")
            response = requests.get(
                f"{self.base_url}/contents/store/extensions",
                headers=self.headers
            )
            
            if response.status_code == 200:
                extensions = self.process_extensions_response(response.json())
                self.update_cache(extensions)
                logger.info(f"تم جلب {len(extensions)} إضافة بنجاح")
                return self.filter_compatible_extensions(extensions)
            
            logger.error(f"فشل في جلب قائمة الإضافات: {response.status_code}")
            return []

        except Exception as e:
            logger.error(f"خطأ في جلب الإضافات: {str(e)}")
            return []

    def filter_compatible_extensions(self, extensions):
        """تصفية الإضافات المتوافقة"""
        compatible = []
        for ext in extensions:
            platforms = ext.get('platform', {})
            display_name = ext.get('name', ext.get('id', 'إضافة غير معروفة'))  # استخدام الاسم العربي أو المعرف كاحتياطي
            
            if not platforms.get(self.platform, False):
                logger.debug(f"الإضافة '{display_name}' غير متوافقة مع النظام {self.platform}")
                continue

            app_version = ext.get('app_version', {})
            min_version = app_version.get('min', '0.0.0')
            max_version = app_version.get('max', '999.999.999')

            try:
                if (semver.VersionInfo.parse(min_version) <= 
                    semver.VersionInfo.parse(self.app_version) <= 
                    semver.VersionInfo.parse(max_version)):
                    compatible.append(ext)
                    logger.debug(f"الإضافة '{display_name}' متوافقة")
                else:
                    logger.debug(f"الإضافة '{display_name}' غير متوافقة مع إصدار التطبيق {self.app_version}")
            except ValueError:
                logger.warning(f"خطأ في التحقق من إصدار الإضافة '{display_name}'")
                continue

        logger.info(f"تم العثور على {len(compatible)} إضافة متوافقة")
        return compatible

    def load_token(self):
        """تحميل توكن GitHub من الإعدادات"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    token = settings.get('extensions', {}).get('github_token', '')
                    if not token:
                        logger.warning("لم يتم العثور على توكن جيت هاب في الإعدادات")
                    return token
        except Exception as e:
            logger.error(f"خطأ في تحميل توكن جيت هاب: {str(e)}")
        return ''

    def create_headers(self):
        """إنشاء ترويسات الطلبات"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': f'Qirtas-Editor/{self.app_version}'
        }
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        return headers

    def update_token(self, token):
        """تحديث الرمز وحفظه"""
        try:
            # التحقق من صحة الرمز
            test_headers = {
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {token}'
            }
            response = requests.get('https://api.github.com/rate_limit', headers=test_headers)
            
            if response.status_code == 200:
                # حفظ الرمز في الإعدادات
                settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
                settings = {}
                if os.path.exists(settings_path):
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                
                settings['github_token'] = token
                os.makedirs(os.path.dirname(settings_path), exist_ok=True)
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4)
                
                # تحديث الهيدرز
                self.token = token
                self.headers = self.create_headers()
                
                # مسح الكاش لتحديث البيانات
                self.clear_cache()
                return True
            else:
                print("الرمز غير صالح")
                return False
                
        except Exception as e:
            print(f"خطأ في تحديث الرمز: {str(e)}")
            return False

    def download_extension(self, extension_id):
        """تحميل إضافة محددة ن GitHub"""
        try:
            # جلب محتويات مجلد الإضافة
            response = requests.get(f"{self.base_url}/contents/store/{extension_id}")
            if response.status_code == 200:
                extension_path = os.path.join("extensions", extension_id)
                os.makedirs(extension_path, exist_ok=True)
                
                # تحميل كل ملف في الإضافة
                for item in response.json():
                    if item['type'] == 'file':
                        file_url = item['download_url']
                        file_content = requests.get(file_url).content
                        
                        file_path = os.path.join(extension_path, item['name'])
                        with open(file_path, 'wb') as f:
                            f.write(file_content)
                return True
            return False
        except Exception as e:
            print(f"خطأ في تحميل الإضافة: {str(e)}")
            return False

    def get_extension_details(self, extension_id):
        """جلب تفاصيل إضافة محددة"""
        try:
            manifest_url = f"{self.raw_base_url}/store/{extension_id}/manifest.json"
            response = requests.get(manifest_url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"خطأ في جلب تفاصيل الإضافة: {str(e)}")
            return None

    def search_extensions(self, query):
        """بحث محسن في الإضافات"""
        try:
            # استخدام الكاش في الذاكرة
            if 'extensions' in self.memory_cache:
                extensions = self.memory_cache['extensions']
            else:
                extensions = self.get_available_extensions()
            
            query = query.lower()
            results = []
            
            # تحسين البحث مع الأولوية
            for ext in extensions:
                score = 0
                name = ext['name'].lower()
                desc = ext.get('description', '').lower()
                
                # مطابقة دقيقة للاسم
                if query == name:
                    score += 100
                # مطابقة جزئية للاسم
                elif query in name:
                    score += 50
                # مطابقة في الوصف
                if query in desc:
                    score += 25
                    
                if score > 0:
                    results.append((ext, score))
            
            # ترتيب النتائج حسب الأهمية
            results.sort(key=lambda x: x[1], reverse=True)
            return [ext for ext, _ in results]
            
        except Exception as e:
            print(f"خطأ في البحث: {str(e)}")
            return []

    def get_featured_extensions(self):
        """جلب الإضافات المميزة"""
        try:
            # جلب قائمة الإضافات المميزة من ملف خاص
            featured_url = f"{self.raw_base_url}/store/featured.json"
            response = requests.get(featured_url)
            if response.status_code == 200:
                featured_ids = response.json()
                # جلب تفاصيل الإضافات المميزة
                return [
                    ext for ext in self.get_available_extensions()
                    if ext['id'] in featured_ids
                ]
            return []
        except Exception as e:
            print(f"خطأ في جلب الإضافات المميزة: {str(e)}")
            return []

    def get_categories(self):
        """جلب تصنيفات الإضافات"""
        try:
            # جلب التصنيفات من ملف خاص
            categories_url = f"{self.raw_base_url}/store/categories.json"
            response = requests.get(categories_url)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"خطأ في جلب التصنيفات: {str(e)}")
            return []

    def clear_cache(self):
        """مسح الكاش"""
        try:
            cache_file = os.path.join(self.cache_dir, "store_cache.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
            return True
        except Exception as e:
            print(f"خطأ في مسح الكاش: {str(e)}")
            return False

    def update_headers(self, token=None):
        """تحديث هيدرز الطلبات"""
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Qirtas-Extension-Store'
        }
        if token:
            self.headers['Authorization'] = f'token {token}'

    def check_rate_limit(self):
        """التحقق من حد الطلبات المتبقي"""
        try:
            response = requests.get('https://api.github.com/rate_limit', headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                remaining = data['resources']['core']['remaining']
                reset_time = data['resources']['core']['reset']
                
                return {
                    'allowed': remaining > 0,
                    'remaining': remaining,
                    'reset_time': reset_time
                }
            return {
                'allowed': False,
                'remaining': 0,
                'reset_time': time.time() + 3600
            }
        except Exception as e:
            print(f"خطأ في التحقق من حد الطلبات: {str(e)}")
            return {
                'allowed': True,  # نسمح بالمحاولة في حالة الخطأ
                'remaining': 1,
                'reset_time': time.time() + 3600
            }

    def handle_rate_limit(self, reset_time):
        """معالجة تجاوز حد الطلبات"""
        # حساب الوقت المتبقي
        wait_time = reset_time - time.time()
        minutes = int(wait_time / 60)
        
        print(f"تجاوز حد الطلبات. يرجى الانتظار {minutes} دقيقة.")
        
        # محاولة استخدام الكاش
        cached_data = self.get_cached_data()
        if cached_data:
            print("جاري استخدام البيانات المخزنة...")
            return cached_data
        return []

    def get_cached_data(self):
        """جلب البيانات من الكاش مع التحقق من الصلاحية"""
        try:
            cache_file = os.path.join(self.cache_dir, "store_cache.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                # التحقق من عمر الكاش
                if time.time() - cache_data['timestamp'] < self.cache_timeout:
                    return cache_data['extensions']
            return None
        except Exception as e:
            print(f"خطأ في قراءة الكاش: {str(e)}")
            return None

    def update_cache(self, data):
        """تحديث الكاش مع إضافة timestamp"""
        try:
            cache_data = {
                'timestamp': time.time(),
                'extensions': data
            }
            cache_file = os.path.join(self.cache_dir, "store_cache.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"خطأ في تحديث الكاش: {str(e)}")

    def get_extension_icon(self, extension_id):
        """الحصول على مسار أيقونة الإضافة"""
        # التحقق من وجود الأيقونة في الكاش
        icon_path = os.path.join(self.cache_dir, f"{extension_id}_icon.png")
        if os.path.exists(icon_path):
            return icon_path
            
        # إرجاع الأيقونة الافتراضية
        return self.default_icon_path