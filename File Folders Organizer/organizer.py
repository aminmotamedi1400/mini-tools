import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import hashlib
import json

class FileOrganizer:
    def __init__(self, source_path, destination_path, mode='copy'):
        self.source = Path(source_path).resolve()
        self.dest = Path(destination_path).resolve()
        self.mode = mode  # 'copy' یا 'move'
        
        # فایل‌های سیستمی که باید نادیده گرفته بشن
        self.ignored_files = {
            'thumbs.db', 'desktop.ini', '.ds_store', 
            '.spotlight-v100', '.trashes', '.fseventsd',
            'albumartsmall.jpg', 'folder.jpg'
        }
        
        # پسوندهای کامل برای هر دسته
        self.categories = {
            'Photos': [
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
                '.heic', '.heif',           # آیفون
                '.raw', '.cr2', '.cr3',     # کانن
                '.nef', '.nrw',             # نیکون
                '.arw', '.srf', '.sr2',     # سونی
                '.dng',                     # Adobe
                '.orf',                     # المپوس
                '.rw2',                     # پاناسونیک
                '.pef',                     # پنتاکس
                '.webp', '.ico', '.svg'
            ],
            'Videos': [
                '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', 
                '.m4v', '.3gp', '.3g2', '.mts', '.m2ts', '.vob', '.ogv',
                '.mpg', '.mpeg', '.ts', '.divx', '.rm', '.rmvb'
            ],
            'Documents': [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.txt', '.rtf', '.odt', '.ods', '.odp', '.csv', '.md',
                '.epub', '.mobi', '.djvu', '.xps'
            ],
            'Music': [
                '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma',
                '.opus', '.aiff', '.ape', '.alac', '.mid', '.midi'
            ],
            'Archives': [
                '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
                '.iso', '.cab', '.lzh', '.arj'
            ],
            'Software': [
                '.exe', '.msi', '.dmg', '.apk', '.deb', '.rpm', '.app',
                '.bat', '.cmd', '.sh', '.jar'
            ],
            'Code': [
                '.py', '.js', '.html', '.css', '.java', '.cpp', '.c',
                '.h', '.php', '.rb', '.go', '.rs', '.swift', '.kt',
                '.json', '.xml', '.yaml', '.yml', '.sql', '.ipynb'
            ],
        }
        
        # آمار
        self.stats = {
            'total': 0,
            'processed': 0,
            'copied': 0,
            'duplicates': 0,
            'skipped': 0,
            'errors': 0,
            'no_exif': 0,
            'invalid_date': 0,
            'corrupted': 0  # فایل‌های خراب
        }
        
        # برای تشخیص تکراری
        self.file_hashes = {}
        
        # برای ذخیره گزارش خطاها
        self.error_log = []
        
        # فولدرهای خراب که باید اسکیپ بشن
        self.corrupted_paths = []
        
        # محدوده تاریخ معتبر (1990 تا سال آینده)
        self.min_valid_year = 1990
        self.max_valid_year = datetime.now().year + 1
        
        # حداکثر سایز فایل برای hash کامل (100MB)
        self.max_hash_size = 100 * 1024 * 1024
        
        # تنظیم logging
        self._setup_logging()

    def _setup_logging(self):
        """تنظیم سیستم لاگ"""
        log_file = self.dest / 'organizer_log.txt'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def safe_scandir(self, path):
        """
        اسکن امن فولدر با مدیریت فولدرهای خراب
        """
        try:
            return list(os.scandir(path))
        except PermissionError:
            self.logger.warning(f"⚠️  دسترسی رد شد: {path}")
            return []
        except OSError as e:
            # خطای corruption یا unreadable
            if e.winerror in [1392, 87]:  # corrupted یا invalid parameter
                self.logger.error(f"💥 فولدر خراب: {path}")
                self.corrupted_paths.append(str(path))
                self.stats['corrupted'] += 1
            else:
                self.logger.error(f"❌ خطای سیستم در {path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ خطای غیرمنتظره در {path}: {e}")
            return []

    def safe_rglob(self, root_path):
        """
        اسکن بازگشتی امن با مدیریت فولدرهای خراب
        """
        all_files = []
        dirs_to_scan = [root_path]
        
        while dirs_to_scan:
            current_dir = dirs_to_scan.pop(0)
            
            # اسکن امن فولدر
            entries = self.safe_scandir(current_dir)
            
            for entry in entries:
                try:
                    entry_path = Path(entry.path)
                    
                    if entry.is_file(follow_symlinks=False):
                        all_files.append(entry_path)
                    elif entry.is_dir(follow_symlinks=False):
                        # اضافه کردن به لیست فولدرهای برای اسکن
                        dirs_to_scan.append(entry_path)
                        
                except PermissionError:
                    self.logger.debug(f"⚠️  دسترسی رد شد: {entry.path}")
                    continue
                except OSError as e:
                    if e.winerror == 1392:
                        self.logger.warning(f"💥 فایل/فولدر خراب: {entry.path}")
                        self.stats['corrupted'] += 1
                    else:
                        self.logger.warning(f"⚠️  خطا در خواندن: {entry.path} - {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"⚠️  خطای غیرمنتظره: {entry.path} - {e}")
                    continue
        
        return all_files

    def get_file_hash(self, filepath, quick=False):
        """
        محاسبه hash فایل برای تشخیص تکراری
        quick=True: فقط اول و آخر فایل رو hash می‌کنه (سریع‌تر)
        """
        hasher = hashlib.md5()
        try:
            file_size = filepath.stat().st_size
            
            with open(filepath, 'rb') as f:
                # برای فایل‌های بزرگ، فقط اول و آخر رو بخون
                if quick or file_size > self.max_hash_size:
                    # اول فایل
                    hasher.update(f.read(65536))
                    # سایز فایل
                    hasher.update(str(file_size).encode())
                    # آخر فایل
                    if file_size > 65536:
                        f.seek(-65536, 2)
                        hasher.update(f.read(65536))
                else:
                    # hash کامل
                    for chunk in iter(lambda: f.read(65536), b""):
                        hasher.update(chunk)
            
            return hasher.hexdigest()
        except PermissionError:
            self.logger.warning(f"دسترسی رد شد: {filepath}")
            return None
        except OSError as e:
            if e.winerror == 1392:
                self.logger.warning(f"💥 فایل خراب: {filepath}")
                self.stats['corrupted'] += 1
            return None
        except Exception as e:
            self.logger.warning(f"خطا در hash: {filepath} - {e}")
            return None

    def get_photo_date(self, filepath):
        """
        استخراج تاریخ از EXIF عکس
        برمی‌گردونه: (datetime, has_valid_exif)
        """
        exif_date = None
        
        try:
            with Image.open(filepath) as image:
                exif_data = image._getexif()
                
                if exif_data:
                    # اول DateTimeOriginal رو چک کن
                    date_tags = ['DateTimeOriginal', 'DateTimeDigitized', 'DateTime']
                    
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag in date_tags and value:
                            try:
                                # فرمت‌های مختلف تاریخ
                                for fmt in ['%Y:%m:%d %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S']:
                                    try:
                                        exif_date = datetime.strptime(str(value).strip(), fmt)
                                        break
                                    except ValueError:
                                        continue
                                
                                if exif_date:
                                    # بررسی معتبر بودن تاریخ
                                    if self.min_valid_year <= exif_date.year <= self.max_valid_year:
                                        return exif_date, True
                                    else:
                                        self.stats['invalid_date'] += 1
                                        self.logger.debug(f"تاریخ نامعتبر در EXIF: {exif_date} - {filepath.name}")
                                        exif_date = None
                            except Exception:
                                continue
        except PermissionError:
            self.logger.warning(f"دسترسی رد شد: {filepath}")
        except OSError as e:
            if e.winerror == 1392:
                self.logger.warning(f"💥 فایل خراب: {filepath}")
                self.stats['corrupted'] += 1
        except Exception as e:
            self.logger.debug(f"خطا در خواندن EXIF: {filepath.name} - {e}")
        
        # اگر EXIF نداشت یا نامعتبر بود
        self.stats['no_exif'] += 1
        return None, False

    def get_video_date(self, filepath):
        """
        استخراج تاریخ از metadata ویدیو
        برمی‌گردونه: (datetime, has_valid_metadata)
        """
        try:
            # استفاده از تاریخ modification فایل
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            
            # بررسی معتبر بودن
            if self.min_valid_year <= mtime.year <= self.max_valid_year:
                return mtime, False  # False چون از metadata واقعی نیست
        except OSError as e:
            if e.winerror == 1392:
                self.logger.warning(f"💥 فایل خراب: {filepath}")
                self.stats['corrupted'] += 1
        except Exception as e:
            self.logger.debug(f"خطا در خواندن تاریخ ویدیو: {filepath.name} - {e}")
        
        return None, False

    def get_category(self, file_path):
        """تشخیص دسته فایل"""
        ext = file_path.suffix.lower()
        
        for category, extensions in self.categories.items():
            if ext in extensions:
                return category
        
        return 'Others'

    def is_valid_file(self, file_path):
        """بررسی اینکه فایل باید پردازش بشه یا نه"""
        # فایل‌های سیستمی
        if file_path.name.lower() in self.ignored_files:
            return False, "فایل سیستمی"
        
        # فایل‌های مخفی (شروع با نقطه)
        if file_path.name.startswith('.'):
            return False, "فایل مخفی"
        
        # فایل‌های خیلی کوچک (احتمالاً خراب یا بی‌فایده)
        try:
            if file_path.stat().st_size < 100:  # کمتر از 100 بایت
                return False, "فایل خیلی کوچک"
        except OSError as e:
            if e.winerror == 1392:
                return False, "فایل خراب"
            return False, "خطا در خواندن سایز"
        except:
            return False, "خطا در خواندن سایز"
        
        # symbolic link
        try:
            if file_path.is_symlink():
                return False, "لینک symbolic"
        except:
            pass
        
        return True, ""

    def get_destination_folder(self, file_path, category):
        """تعیین فولدر مقصد برای فایل"""
        
        if category == 'Photos':
            photo_date, has_exif = self.get_photo_date(file_path)
            
            if photo_date and has_exif:
                year = photo_date.strftime('%Y')
                month = photo_date.strftime('%Y-%m')
                return self.dest / 'Photos' / year / month, f"📅 EXIF: {photo_date.strftime('%Y-%m-%d')}"
            else:
                return self.dest / 'Photos' / 'Unknown_Date', "📁 بدون EXIF"
        
        elif category == 'Videos':
            video_date, has_metadata = self.get_video_date(file_path)
            
            if video_date:
                year = video_date.strftime('%Y')
                return self.dest / 'Videos' / year, f"📅 {video_date.strftime('%Y-%m-%d')}"
            else:
                return self.dest / 'Videos' / 'Unknown_Date', "📁 بدون تاریخ"
        
        else:
            return self.dest / category, ""

    def check_disk_space(self, file_path):
        """بررسی فضای کافی دیسک"""
        try:
            file_size = file_path.stat().st_size
            free_space = shutil.disk_usage(self.dest).free
            
            # حداقل 100MB فضای آزاد + سایز فایل
            min_required = file_size + (100 * 1024 * 1024)
            
            if free_space < min_required:
                return False
            return True
        except:
            return True  # اگه نتونست چک کنه، ادامه بده

    def safe_copy(self, source, destination):
        """کپی امن فایل با بررسی خطاها"""
        try:
            # ساخت فولدر مقصد
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # کپی با حفظ metadata
            if self.mode == 'move':
                shutil.move(str(source), str(destination))
            else:
                shutil.copy2(str(source), str(destination))
            
            # بررسی صحت کپی
            if destination.exists():
                if destination.stat().st_size == source.stat().st_size:
                    return True, ""
                else:
                    destination.unlink()  # حذف فایل ناقص
                    return False, "سایز فایل مقصد مطابقت ندارد"
            else:
                return False, "فایل مقصد ایجاد نشد"
                
        except PermissionError:
            return False, "دسترسی رد شد"
        except OSError as e:
            if e.winerror == 1392:
                return False, "فایل خراب (corrupted)"
            elif "name too long" in str(e).lower() or e.errno == 63:
                return False, "نام فایل خیلی طولانی"
            return False, f"خطای سیستم: {e}"
        except Exception as e:
            return False, f"خطا: {e}"

    def get_unique_filename(self, dest_folder, filename):
        """ایجاد نام یکتا برای فایل"""
        dest_file = dest_folder / filename
        
        if not dest_file.exists():
            return dest_file
        
        stem = dest_file.stem
        suffix = dest_file.suffix
        counter = 1
        
        # حداکثر 1000 تلاش
        while counter < 1000:
            new_name = f"{stem}_{counter}{suffix}"
            dest_file = dest_folder / new_name
            if not dest_file.exists():
                return dest_file
            counter += 1
        
        # اگه 1000 تا تکراری بود، از timestamp استفاده کن
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return dest_folder / f"{stem}_{timestamp}{suffix}"

    def organize_file(self, file_path):
        """پردازش و مرتب‌سازی یک فایل"""
        self.stats['processed'] += 1
        
        # بررسی اعتبار فایل
        is_valid, skip_reason = self.is_valid_file(file_path)
        if not is_valid:
            if skip_reason == "فایل خراب":
                self.logger.warning(f"💥 فایل خراب: {file_path}")
            else:
                self.logger.debug(f"⏭️  نادیده: {file_path.name} ({skip_reason})")
            self.stats['skipped'] += 1
            return False
        
        # بررسی فضای دیسک
        if not self.check_disk_space(file_path):
            self.logger.error("❌ فضای دیسک کافی نیست!")
            self.stats['errors'] += 1
            return False
        
        # تشخیص دسته
        category = self.get_category(file_path)
        
        # تعیین فولدر مقصد
        dest_folder, date_info = self.get_destination_folder(file_path, category)
        
        # محاسبه hash برای تشخیص تکراری
        file_hash = self.get_file_hash(file_path, quick=True)
        
        if file_hash:
            if file_hash in self.file_hashes:
                original = self.file_hashes[file_hash]
                self.logger.info(f"⚠️  تکراری: {file_path.name} (مشابه: {Path(original).name})")
                self.stats['duplicates'] += 1
                return False
        
        # ایجاد نام یکتا
        dest_file = self.get_unique_filename(dest_folder, file_path.name)
        
        # کپی فایل
        success, error_msg = self.safe_copy(file_path, dest_file)
        
        if success:
            if file_hash:
                self.file_hashes[file_hash] = str(dest_file)
            
            relative_dest = dest_file.relative_to(self.dest)
            info_str = f" [{date_info}]" if date_info else ""
            self.logger.info(f"✅ {file_path.name} → {relative_dest}{info_str}")
            self.stats['copied'] += 1
            return True
        else:
            self.logger.error(f"❌ {file_path.name}: {error_msg}")
            self.error_log.append({
                'file': str(file_path),
                'error': error_msg,
                'time': datetime.now().isoformat()
            })
            self.stats['errors'] += 1
            return False

    def scan_and_organize(self):
        """اسکن و مرتب‌سازی تمام فایل‌ها"""
        
        # بررسی مسیرها
        if not self.source.exists():
            self.logger.error(f"❌ مسیر مبدا وجود ندارد: {self.source}")
            return
        
        # ساخت فولدر مقصد
        self.dest.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("=" * 70)
        self.logger.info("🚀 شروع مرتب‌سازی فایل‌ها")
        self.logger.info("=" * 70)
        self.logger.info(f"📁 مسیر مبدا: {self.source}")
        self.logger.info(f"📁 مسیر مقصد: {self.dest}")
        self.logger.info(f"⚙️  حالت: {'انتقال (Move)' if self.mode == 'move' else 'کپی (Copy)'}")
        self.logger.info("")
        
        # پیدا کردن تمام فایل‌ها با اسکن امن
        self.logger.info("🔍 در حال اسکن فایل‌ها (با مدیریت فولدرهای خراب)...")
        
        all_files = self.safe_rglob(self.source)
        
        self.stats['total'] = len(all_files)
        
        self.logger.info(f"📊 تعداد کل فایل‌ها: {self.stats['total']}")
        if self.stats['corrupted'] > 0:
            self.logger.warning(f"💥 فولدر/فایل خراب یافت شد: {self.stats['corrupted']}")
        self.logger.info("=" * 70)
        
        if self.stats['total'] == 0:
            self.logger.info("⚠️  هیچ فایلی پیدا نشد!")
            return
        
        # پردازش فایل‌ها
        start_time = datetime.now()
        
        for idx, file_path in enumerate(all_files, 1):
            # نمایش پیشرفت
            progress = (idx / self.stats['total']) * 100
            print(f"\r[{idx}/{self.stats['total']}] ({progress:.1f}%) ", end='', flush=True)
            
            try:
                self.organize_file(file_path)
            except Exception as e:
                self.logger.error(f"❌ خطای غیرمنتظره در {file_path.name}: {e}")
                self.stats['errors'] += 1
        
        print()  # خط جدید بعد از progress bar
        
        # محاسبه زمان
        elapsed = datetime.now() - start_time
        
        # نمایش آمار نهایی
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("✨ مرتب‌سازی تمام شد!")
        self.logger.info("=" * 70)
        self.logger.info(f"⏱️  زمان: {elapsed}")
        self.logger.info("")
        self.logger.info("📊 آمار نهایی:")
        self.logger.info(f"   • کل فایل‌ها: {self.stats['total']}")
        self.logger.info(f"   • کپی/انتقال شده: {self.stats['copied']}")
        self.logger.info(f"   • تکراری: {self.stats['duplicates']}")
        self.logger.info(f"   • نادیده گرفته شده: {self.stats['skipped']}")
        self.logger.info(f"   • بدون EXIF (عکس): {self.stats['no_exif']}")
        self.logger.info(f"   • تاریخ نامعتبر: {self.stats['invalid_date']}")
        self.logger.info(f"   • فایل/فولدر خراب: {self.stats['corrupted']}")
        self.logger.info(f"   • خطا: {self.stats['errors']}")
        self.logger.info("")
        
        # نمایش لیست فولدرهای خراب
        if self.corrupted_paths:
            self.logger.warning("💥 فولدرهای خراب که اسکیپ شدند:")
            for path in self.corrupted_paths:
                self.logger.warning(f"   • {path}")
            self.logger.info("")
        
        # ذخیره گزارش
        self._save_report()

    def _save_report(self):
        """ذخیره گزارش کامل"""
        report = {
            'source': str(self.source),
            'destination': str(self.dest),
            'mode': self.mode,
            'stats': self.stats,
            'corrupted_paths': self.corrupted_paths,
            'errors': self.error_log,
            'timestamp': datetime.now().isoformat()
        }
        
        report_file = self.dest / 'organizer_report.json'
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.logger.info(f"📄 گزارش ذخیره شد: {report_file}")
        except Exception as e:
            self.logger.warning(f"⚠️  خطا در ذخیره گزارش: {e}")
        
        # ذخیره لیست فولدرهای خراب
        if self.corrupted_paths:
            corrupted_file = self.dest / 'corrupted_paths.txt'
            try:
                with open(corrupted_file, 'w', encoding='utf-8') as f:
                    f.write("فولدرها و فایل‌های خراب:\n")
                    f.write("=" * 50 + "\n\n")
                    for path in self.corrupted_paths:
                        f.write(f"{path}\n")
                self.logger.info(f"💥 لیست فولدرهای خراب ذخیره شد: {corrupted_file}")
            except Exception as e:
                self.logger.warning(f"⚠️  خطا در ذخیره لیست خرابی‌ها: {e}")


# ========== استفاده ==========
if __name__ == "__main__":
    
    # ⚙️ تنظیمات - اینجا رو تغییر بده
    SOURCE = r"F:\aks"                   # مسیر هارد شلوغ
    DESTINATION = r"F:\Organized"        # مسیر مقصد مرتب
    MODE = 'copy'                        # 'copy' یا 'move'
    
    # اجرا
    print("🚀 شروع مرتب‌سازی...")
    print("💡 فولدرهای خراب اسکیپ می‌شوند و گزارش می‌شوند\n")
    
    organizer = FileOrganizer(SOURCE, DESTINATION, mode=MODE)
    organizer.scan_and_organize()
    
    print("\n✅ کار تمام شد!")
    print(f"📄 گزارش کامل در: {DESTINATION}\\organizer_log.txt")
    if organizer.corrupted_paths:
        print(f"💥 لیست فولدرهای خراب در: {DESTINATION}\\corrupted_paths.txt")