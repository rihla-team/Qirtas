import json
import os
import requests
import time
import semver

class ExtensionStore:
    def __init__(self):
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
        """الحصول على إصدار التطبيق"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get('app_version', '1.0.0')
        except Exception:
            pass
        return '1.0.0'

    def get_available_extensions(self, force_refresh=False):
        """جلب قائمة الإضافات المتوفرة"""
        try:
            # التحقق من الكاش أولاً إذا لم يكن التحديث إجبارياً
            if not force_refresh:
                cached_data = self.get_cached_data()
                if cached_data:
                    return self.filter_compatible_extensions(cached_data)

            # التحقق من حد الطلبات
            rate_limit = self.check_rate_limit()
            if not rate_limit['allowed']:
                return self.handle_rate_limit(rate_limit['reset_time'])

            # جلب قائمة الإضافات من GitHub
            response = requests.get(f"{self.base_url}/contents/store/extensions", headers=self.headers)
            
            if response.status_code == 200:
                extensions = self.process_extensions_response(response.json())
                self.update_cache(extensions)
                return self.filter_compatible_extensions(extensions)
            else:
                print(f"خطأ في جلب الإضافات: {response.status_code}")
                return []

        except Exception as e:
            print(f"خطأ في جلب الإضافات: {str(e)}")
            return []

    def filter_compatible_extensions(self, extensions):
        """تصفية الإضافات المتوافقة فقط"""
        compatible = []
        for ext in extensions:
            # التحقق من توافق نظام التشغيل
            platforms = ext.get('platform', {})
            if not platforms.get(self.platform, False):
                continue

            # التحقق من إصدار التطبيق
            app_version = ext.get('app_version', {})
            min_version = app_version.get('min', '0.0.0')
            max_version = app_version.get('max', '999.999.999')

            try:
                if (semver.VersionInfo.parse(min_version) <= 
                    semver.VersionInfo.parse(self.app_version) <= 
                    semver.VersionInfo.parse(max_version)):
                    compatible.append(ext)
            except ValueError:
                continue

        return compatible

    def load_token(self):
        """تحميل التوكن من ملف الإعدادات"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get('github_token')
        except Exception as e:
            print(f"خطأ في تحميل التوكن: {str(e)}")
        return None

    def create_headers(self):
        """إنشاء هيدرز الطلبات مع التوكن"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Qirtas-Extension-Store'
        }
        if self.token:
            headers['Authorization'] = f'token {self.token}'
            print("تم تطبيق التوكن بنجاح")
        else:
            print("لم يتم العثور على توكن")
        return headers

    def update_token(self, token):
        """تحديث التوكن وحفظه"""
        try:
            # التحقق من صحة التوكن
            test_headers = {
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {token}'
            }
            response = requests.get('https://api.github.com/rate_limit', headers=test_headers)
            
            if response.status_code == 200:
                # حفظ التوكن في الإعدادات
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
                print("التوكن غير صالح")
                return False
                
        except Exception as e:
            print(f"خطأ في تحديث التوكن: {str(e)}")
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
        """جلب البيانات من الكاش"""
        try:
            cache_file = os.path.join(self.cache_dir, "store_cache.json")
            if os.path.exists(cache_file):
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < self.cache_timeout:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
            return None
        except Exception as e:
            print(f"خطأ في قراءة الكاش: {str(e)}")
            return None

    def update_cache(self, data):
        """تحديث الكاش"""
        try:
            cache_file = os.path.join(self.cache_dir, "store_cache.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"خطأ في تحديث الكاش: {str(e)}")

    def process_extensions_response(self, response_data):
        """معالجة البيانات المستلمة من GitHub"""
        extensions = []
        for item in response_data:
            try:
                if item['type'] == 'dir':
                    manifest_url = f"{self.raw_base_url}/store/extensions/{item['name']}/manifest.json"
                    manifest_response = requests.get(manifest_url, headers=self.headers)
                    
                    if manifest_response.status_code == 200:
                        manifest = manifest_response.json()
                        manifest['id'] = item['name']
                        extensions.append(manifest)
                        
            except Exception as e:
                print(f"خطأ في معالجة الإضافة {item.get('name', '')}: {str(e)}")
                continue
                
        return extensions