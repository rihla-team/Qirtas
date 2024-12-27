import os
import json
import requests
from PyQt5.QtCore import QObject, pyqtSignal
import logging
from .arabic_logger import log_in_arabic
import sys

# إعداد التسجيل باللغة العربية

class UpdateManager(QObject):
    update_available = pyqtSignal(str)  # إشارة عند توفر تحديث جديد
    update_progress = pyqtSignal(int)   # إشارة لتحديث شريط التقدم
    
    def __init__(self):
        super().__init__()
        self.settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'settings.json')
        self.current_version = self._get_current_version()
        self.github_repo = "rihla-team/Qirtas"  # تحديث المستودع الصحيح
        self.github_api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        self.user_agent = f"Qirtas-Editor/{self.current_version}"
        self.logger = logging.getLogger(__name__)
        
    def _get_current_version(self):
        """الحصول على الإصدار الحالي من ملف الإعدادات"""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get('app_version', '1.0.0')
        except Exception as e:
            log_in_arabic(self.logger, logging.ERROR, f"خطأ في قراءة الإصدار الحالي: {str(e)}")
        return '1.0.0'
    
    def check_for_updates(self):
        """التحقق من وجود تحديثات جديدة"""
        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': self.user_agent
            }
            
            # إولاً نتحقق من الوصول للمستودع نفسه
            repo_response = requests.get(f"https://api.github.com/repos/{self.github_repo}", headers=headers)
            
            if repo_response.status_code == 404:
                self.logger.error("المستودع غير موجود")
                return {
                    'error': 'repo_not_found',
                    'message': 'لا يمكن الوصول إلى المستودع'
                }
            
            # ثم نتحقق من وجود releases
            releases_response = requests.get(f"https://api.github.com/repos/{self.github_repo}/releases", headers=headers)
            
            if releases_response.status_code == 200:
                releases = releases_response.json()
                if not releases:  # لا يوجد releases
                    self.logger.info("لا يوجد إصدارات منشورة في المستودع")
                    return {
                        'error': 'no_releases',
                        'message': 'لا يوجد إصدارات منشورة في المستودع بعد'
                    }
                
                latest_release = releases[0]  # أحدث إصدار
                latest_version = latest_release['tag_name'].replace('v', '')
                
                if self._compare_versions(latest_version, self.current_version) > 0:
                    return {
                        'version': latest_version,
                        'description': latest_release['body'],
                        'download_url': latest_release['assets'][0]['browser_download_url'] if latest_release['assets'] else latest_release['zipball_url']
                    }
                else:
                    return {
                        'error': 'no_update',
                        'message': 'أنت تستخدم أحدث إصدار'
                    }
            
            return {
                'error': 'no_releases',
                'message': 'لا يوجد إصدارات منشورة في المستودع بعد'
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من التحديثات: {str(e)}")
            return {
                'error': 'general_error',
                'message': f'حدث خطأ أثناء التحقق من التحديثات: {str(e)}'
            }
    
    def _compare_versions(self, version1, version2):
        """مقارنة الإصدارات"""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            for i in range(max(len(v1_parts), len(v2_parts))):
                v1 = v1_parts[i] if i < len(v1_parts) else 0
                v2 = v2_parts[i] if i < len(v2_parts) else 0
                if v1 > v2:
                    return 1
                elif v1 < v2:
                    return -1
            return 0
        except ValueError:
            print("خطأ في تنسيق الإصدار")
            return 0
    
    def download_update(self, url, destination):
        """تنزيل التحديث"""
        try:
            # إضافة هيدرز للمصادقة
            headers = {
                'User-Agent': self.user_agent
            }
            
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    token = settings.get('extensions', {}).get('github_token')
                    if token:
                        headers['Authorization'] = f'token {token}'
            
            response = requests.get(url, stream=True, headers=headers)
            if response.status_code != 200:
                print(f"خطأ في التنزيل: {response.status_code}")
                return False
                
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            downloaded = 0
            
            # التأكد من وجود المجلد
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            with open(destination, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)
                    if total_size:
                        progress = int((downloaded / total_size) * 100)
                        self.update_progress.emit(progress)
            
            return True
        except Exception as e:
            print(f"خطأ في تنزيل التحديث: {str(e)}")
            return False 
    
    def update_file(self, file_path, new_content):
        """تحديث محتوى ملف في المجلد التنفيذي"""
        try:
            # الحصول على المسار الكامل للملف في مجلد التنفيذ
            exe_dir = os.path.dirname(sys.executable)
            target_path = os.path.join(exe_dir, file_path)
            
            # التأكد من وجود المجلد
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # كتابة المحتوى الجديد
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return True
        except Exception as e:
            print(f"خطأ في تحديث الملف: {str(e)}")
            return False 