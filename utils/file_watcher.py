from PyQt5.QtCore import QObject, QFileSystemWatcher, pyqtSignal, QTimer, QTime
import os
import difflib

class FileWatcher(QObject):
    content_changed = pyqtSignal(str, str, list)  # file_path, content, changes

    def __init__(self):
        super().__init__()
        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self._handle_file_changed)
        self.watched_files = {}
        self.update_timer = QTimer()
        self.update_timer.setInterval(1000)  # تحديث كل ثانية
        self.update_timer.timeout.connect(self._check_files)
        self.update_timer.start()
        self.pending_updates = {}
        self.last_update_time = {}
        self.typing_timer = QTimer()
        self.typing_timer.setInterval(1000)  # فترة انتظار بعد آخر كتابة
        self.typing_timer.setSingleShot(True)
        self.is_typing = False

    def _get_file_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception:
            return None

    def _calculate_changes(self, old_content, new_content):
        """حساب التغييرات بين النصين"""
        if old_content == new_content:
            return []
            
        differ = difflib.Differ()
        diff = list(differ.compare(old_content.splitlines(True), new_content.splitlines(True)))
        return diff

    def _check_files(self):
        """فحص الملفات للتغييرات"""
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        
        for file_path in list(self.watched_files.keys()):
            if not os.path.exists(file_path):
                continue
                
            try:
                current_mtime = os.path.getmtime(file_path)
                last_check = self.watched_files[file_path]['last_modified']
                
                # تجاهل التحديثات المتكررة خلال ثانية واحدة
                if current_mtime > last_check and (
                    file_path not in self.last_update_time or 
                    current_time - self.last_update_time.get(file_path, 0) > 1000
                ):
                    current_content = self._get_file_content(file_path)
                    if not current_content:
                        continue
                        
                    old_content = self.watched_files[file_path]['content']
                    if current_content != old_content:
                        changes = self._calculate_changes(old_content, current_content)
                        if changes:
                            self._queue_update(file_path, current_content, current_mtime, changes)
                            
            except Exception as e:
                print(f"خطأ في فحص الملف {file_path}: {str(e)}")

    def _queue_update(self, file_path, content, mtime, changes):
        """وضع التحديث في قائمة الانتظار"""
        editor = self.watched_files[file_path]['editor']
        
        if not self._should_update_file(file_path, editor):
            return
            
        self.pending_updates[file_path] = {
            'content': content,
            'mtime': mtime,
            'changes': changes
        }
        # تطبيق التحديث بعد تأخير قصير
        QTimer.singleShot(500, lambda: self._apply_pending_update(file_path))

    def _apply_pending_update(self, file_path):
        """تطبيق التحديث المعلق"""
        if file_path not in self.pending_updates:
            return
            
        update = self.pending_updates.pop(file_path)
        editor = self.watched_files[file_path]['editor']
        
        if not editor or editor.document().isModified():
            return
            
        # حفظ موضع المؤشر الحالي
        cursor = editor.textCursor()
        current_position = cursor.position()
        
        # تطبيق التحديث
        editor.blockSignals(True)
        editor.setPlainText(update['content'])
        editor.blockSignals(False)
        
        # استعادة موضع المؤشر
        cursor.setPosition(min(current_position, len(update['content'])))
        editor.setTextCursor(cursor)
        
        # تحديث المعلومات المخزنة
        self.watched_files[file_path].update({
            'content': update['content'],
            'last_modified': update['mtime']
        })
        
        self.last_update_time[file_path] = QTime.currentTime().msecsSinceStartOfDay()
        self.content_changed.emit(file_path, update['content'], update['changes'])

    def _handle_file_changed(self, file_path):
        """معالجة إشارة تغيير الملف"""
        if file_path in self.watched_files:
            # إعادة إضافة المسار للمراقبة
            if os.path.exists(file_path):
                self.watcher.addPath(file_path)
                self._check_files()

    def add_file(self, file_path, editor):
        """إضافة ملف للمراقبة"""
        if os.path.exists(file_path):
            self.watched_files[file_path] = {
                'editor': editor,
                'last_modified': os.path.getmtime(file_path),
                'content': self._get_file_content(file_path)
            }
            self.watcher.addPath(file_path)
            
            # ربط إشارة تغيير النص
            editor.textChanged.connect(lambda: self._on_text_changed(editor))
            self.typing_timer.timeout.connect(self._on_typing_timeout)

    def _on_text_changed(self, editor):
        """معالجة تغيير النص في المحرر"""
        self.is_typing = True
        self.typing_timer.stop()
        self.typing_timer.start()
        
    def _on_typing_timeout(self):
        """يتم استدعاؤها عند انتهاء فترة الكتابة"""
        self.is_typing = False

    def _should_update_file(self, file_path, editor):
        """التحقق من إمكانية تحديث الملف"""
        if not editor or editor.document().isModified():
            return False
            
        # التحقق من عدم الكتابة حالياً
        if self.is_typing:
            return False
            
        # التحقق من الفترة الزمنية منذ آخر تحديث
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        last_update = self.last_update_time.get(file_path, 0)
        if current_time - last_update < 1000:  # تجنب التحديثات المتكررة خلال ثانية
            return False
            
        return True