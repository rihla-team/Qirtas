from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QPushButton, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import json
import os
import requests
from urllib.parse import urljoin
import base64

class ExtensionStore:
    def __init__(self):
        # معلومات المستودع على GitHub
        self.owner = "lub"  # اسم المستخدم أو المنظمة
        self.repo = "rehla-extensions"  # اسم المستودع
        self.branch = "main"
        self.base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        self.raw_base_url = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{self.branch}"
        
        # مجلد الكاش المحلي
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".extension_store_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_available_extensions(self):
        """جلب قائمة الإضافات المتوفرة من GitHub"""
        try:
            # محاولة جلب القائمة من الكاش
            cache_file = os.path.join(self.cache_dir, "store_cache.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

            # إلب محتويات المجلد store من GitHub
            response = requests.get(f"{self.base_url}/contents/store")
            if response.status_code == 200:
                extensions = []
                for item in response.json():
                    if item['type'] == 'dir':  # البحث عن المجلدات فقط
                        # جلب ملف manifest.json لكل إضافة
                        manifest_url = f"{self.raw_base_url}/store/{item['name']}/manifest.json"
                        manifest_response = requests.get(manifest_url)
                        if manifest_response.status_code == 200:
                            manifest = manifest_response.json()
                            manifest['id'] = item['name']
                            extensions.append(manifest)

                # حفظ في الكاش
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(extensions, f, ensure_ascii=False, indent=4)
                return extensions
            return []
        except Exception as e:
            print(f"خطأ في جلب قائمة الإضافات: {str(e)}")
            return []

    def download_extension(self, extension_id):
        """تحميل إضافة محددة من GitHub"""
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
        """البحث عن إضافات"""
        try:
            extensions = self.get_available_extensions()
            # البحث المحلي في الإضافات المتوفرة
            return [
                ext for ext in extensions
                if query.lower() in ext['name'].lower() or
                   query.lower() in ext.get('description', '').lower()
            ]
        except Exception as e:
            print(f"خطأ في البحث عن الإضافات: {str(e)}")
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