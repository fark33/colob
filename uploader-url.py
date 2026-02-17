!pip install -q yt-dlp tqdm

from google.colab import drive
drive.mount('/content/drive')

import yt_dlp
from tqdm import tqdm
import os
import re

# مسیر ذخیره نهایی در Google Drive
output_folder = "/content/drive/MyDrive/Downloaded_Videos"
os.makedirs(output_folder, exist_ok=True)

# ── ورودی لینک ──
url = input("لینک ویدیو را وارد کنید (یوتیوب، اینستاگرام، آپارات، ok.ru و ...): ").strip()

if not url:
    print("هیچ لینکی وارد نشده! اجرا را متوقف می‌کنم.")
    raise SystemExit

print(f"\nلینک: {url}\n")

# تنظیمات yt-dlp برای لیست کردن فرمت‌ها
ydl_opts_list = {
    'quiet': True,
    'no_warnings': True,
    'simulate': True,           # دانلود نکن، فقط اطلاعات
    'listformats': True,        # این باعث نمایش فرمت‌ها می‌شود ولی ما خودمان می‌خوانیم
}

# برای گرفتن اطلاعات فرمت‌ها به صورت ساختاریافته
ydl_opts_info = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
}

print("در حال بررسی کیفیت‌های موجود ...")

with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
    try:
        info = ydl.extract_info(url, download=False)
    except Exception as e:
        print("\nخطا در دریافت اطلاعات ویدیو:")
        print(e)
        print("لینک را چک کنید یا بعداً امتحان کنید.")
        raise SystemExit

# فیلتر کردن فقط فرمت‌های ویدیویی (دارای video codec)
formats = []
video_formats = []

if 'requested_formats' in info:
    # بعضی سایت‌ها (مثل یوتیوب) فرمت‌های جداگانه audio/video دارند
    for f in info.get('requested_formats', []):
        if f.get('vcodec') != 'none':
            video_formats.append(f)
elif 'formats' in info:
    for f in info['formats']:
        if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
            video_formats.append(f)

if not video_formats:
    print("هیچ فرمت ویدیویی مناسبی پیدا نشد.")
    raise SystemExit

print("\n" + "="*70)
print("کیفیت‌های موجود (فقط ویدیو + صدا ترکیب شده):")
print("-"*70)

for i, f in enumerate(video_formats, 1):
    format_id = f.get('format_id', '---')
    resolution = f.get('resolution') or f"{f.get('width','?')}x{f.get('height','?')}"
    fps = f.get('fps', '?')
    ext = f.get('ext', 'unknown')
    filesize = f.get('filesize') or f.get('filesize_approx')
    size_str = f"{filesize/1024/1024:.1f} MiB" if filesize else "نامشخص"
    
    tbr = f.get('tbr')
    bitrate_str = f"~{tbr:.0f}kbps" if tbr else ""
    
    print(f"{i:2d} | {format_id:>6} | {resolution:>9} | {fps:>2}fps | {ext:>4} | {size_str:>12} | {bitrate_str}")

print("="*70)

# انتخاب توسط کاربر
while True:
    try:
        choice = input("\nشماره کیفیت مورد نظر را وارد کنید (مثلاً 3): ").strip()
        idx = int(choice) - 1
        if 0 <= idx < len(video_formats):
            selected_format = video_formats[idx]
            break
        else:
            print(f"لطفاً عددی بین 1 تا {len(video_formats)} وارد کنید.")
    except ValueError:
        print("لطفاً فقط عدد وارد کنید.")

# نام فایل خروجی
title = re.sub(r'[^\w\s-]', '', info.get('title', 'video').strip())
title = title[:100]  # جلوگیری از نام خیلی بلند
extension = selected_format.get('ext', 'mp4')
output_filename = f"{title}.{extension}"
output_path = os.path.join(output_folder, output_filename)

print(f"\nفایل انتخابی: {output_filename}")
print(f"ذخیره در: {output_path}\n")

# تنظیمات دانلود واقعی
ydl_opts_download = {
    'format': selected_format['format_id'],
    'outtmpl': output_path,
    'continuedl': True,
    'retries': 10,
    'fragment_retries': 10,
    'concurrent_fragment_downloads': 8,   # افزایش سرعت دانلود قطعه‌ای
}

print("شروع دانلود ... (مستقیم به Google Drive)\n")

with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
    try:
        ydl.download([url])
    except Exception as e:
        print("\nخطا در دانلود:")
        print(e)
        print("می‌توانید دوباره اجرا کنید یا فرمت دیگری انتخاب کنید.")
        raise

print("\n" + "═"*60)
print("دانلود با موفقیت به پایان رسید!")
print(f"فایل در Google Drive شما ذخیره شد:")
print(output_path)
print("═"*60)
