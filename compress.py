!pip install -q yt-dlp tqdm requests

from google.colab import drive
drive.mount('/content/drive')

import yt_dlp
from tqdm import tqdm
import subprocess
import os
import requests

# ── ورودی لینک ویدیو ──
url = input("لینک ویدیو رو اینجا وارد کن: ").strip()

if not url:
    print("خطا: لینک وارد نشده!")
else:
    print(f"لینک دریافت شد: {url}\n")

# نام فایل‌ها
input_filename = "original.mp4"
output_path = "/content/drive/MyDrive/Compressed_Video_480p_x265_4MBmin.mp4"

# تشخیص لینک مستقیم
direct_video_extensions = ['.mp4', '.mkv', '.webm', '.mov', '.avi', '.flv', '.wmv']
is_direct_link = any(url.lower().endswith(ext) for ext in direct_video_extensions)

# مرحله ۱: دانلود ویدیو
print("در حال دانلود ویدیو ...")

if is_direct_link:
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        with open(input_filename, 'wb') as f, tqdm(
            desc="دانلود مستقیم",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in r.iter_content(chunk_size=1024*1024):
                bar.update(len(chunk))
                f.write(chunk)
        print("دانلود تمام شد!\n")
    except Exception as e:
        print(f"خطا در دانلود مستقیم: {e}")
        raise
else:
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
        'outtmpl': input_filename,
        'merge_output_format': 'mp4',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("دانلود با yt-dlp انجام شد!\n")
    except Exception as e:
        print(f"خطا در دانلود: {e}")
        raise

# مرحله ۲: استخراج مدت زمان برای نوار پیشرفت
try:
    duration_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{input_filename}\""
    duration = float(subprocess.check_output(duration_cmd, shell=True).strip())
except Exception as e:
    print(f"خطا در گرفتن مدت زمان: {e}")
    duration = 0

# مرحله ۳: فشرده‌سازی با FFmpeg - هدف ≈ ۴ MB در دقیقه + سرعت بیشتر
print("\nدر حال تبدیل به 480p با libx265 ...")
print("تنظیمات: CRF 22.5 + maxrate 520k + صدا 88k + threads 0 (سرعت بهینه)")
print("توجه: preset medium + threads 0 معمولاً بهترین تعادل سرعت و کیفیت را می‌دهد")

ffmpeg_cmd = [
    'ffmpeg', '-i', input_filename,
    '-c:v', 'libx265',
    '-preset', 'medium',
    '-crf', '22.5',                    # کیفیت خوب – اگر حجم زیاد شد → 24 یا 25
    '-maxrate', '520k',                # سقف بیت‌ریت ویدیو
    '-bufsize', '1040k',               # بافر ≈ ۲ برابر maxrate
    '-threads', '0',                   # ← اضافه شد: بهینه‌ترین تعداد thread (ffmpeg خودش مدیریت می‌کند)
    '-vf', 'scale=854:480:force_original_aspect_ratio=decrease,pad=854:480:(ow-iw)/2:(oh-ih)/2',
    '-c:a', 'aac',
    '-b:a', '88k',
    '-movflags', '+faststart',
    '-y', output_path
]

process = subprocess.Popen(ffmpeg_cmd, stderr=subprocess.PIPE, universal_newlines=True)

with tqdm(total=duration, unit='s', desc="پردازش ویدیو (x265)", colour='green') as pbar:
    for line in process.stderr:
        if 'time=' in line:
            try:
                time_str = line.split('time=')[1].split()[0]
                h, m, s = map(float, time_str.split(':'))
                current = h*3600 + m*60 + s
                pbar.n = min(current, duration)
                pbar.refresh()
            except:
                pass

process.wait()

# مرحله ۴: گزارش نهایی
try:
    input_size = os.path.getsize(input_filename) / (1024*1024)
    output_size = os.path.getsize(output_path) / (1024*1024)

    print(f"\nحجم فایل اولیه: {input_size:.2f} MB")
    print(f"حجم فایل فشرده (480p x265): {output_size:.2f} MB")
    
    if input_size > 0:
        reduction = ((input_size - output_size) / input_size) * 100
        print(f"میزان کاهش حجم: {reduction:.1f}%")
    
    if duration > 0:
        size_per_min = output_size / (duration / 60)
        print(f"حجم میانگین در دقیقه: {size_per_min:.2f} MB/min")
except:
    print("\nخطا در محاسبه حجم فایل‌ها")

print(f"\nفایل نهایی ذخیره شد در: {output_path}")
print("نکته: پخش H.265 روی دستگاه‌های خیلی قدیمی ممکنه مشکل داشته باشه")
