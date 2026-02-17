!pip install -q yt-dlp tqdm requests

from google.colab import drive
drive.mount('/content/drive')

import yt_dlp
from tqdm import tqdm
import subprocess
import os
import json
import requests

# --- ورودی دستی لینک ویدیو ---
url = input("لینک ویدیو رو اینجا وارد کن (مثلاً از یوتیوب، ok.ru، اینستاگرام و ... یا لینک مستقیم): ").strip()

if not url:
    print("خطا: لینک وارد نشده! دوباره اجرا کن و لینک رو وارد کن.")
else:
    print(f"لینک دریافت شد: {url}\n")

# نام فایل‌ها
input_filename = "original.mp4"
output_path = "/content/drive/MyDrive/Sharbate_Zoghal_Watermarked.mp4"
gif_filename = "fa.gif"
font_filename = "fa.ttf"

# تشخیص لینک مستقیم
direct_video_extensions = ['.mp4', '.mkv', '.webm', '.mov', '.avi', '.flv', '.wmv']
is_direct_link = any(url.lower().endswith(ext) for ext in direct_video_extensions)

# دانلود (همیشه به صورت محلی ذخیره می‌شود)
print("در حال دانلود ویدیو ...")

if is_direct_link:
    print("لینک مستقیم → دانلود با requests")
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        
        total_size = int(r.headers.get('content-length', 0))
        
        with open(input_filename, 'wb') as f, tqdm(
            desc="دانلود فایل مستقیم",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in r.iter_content(chunk_size=1024*1024):
                bar.update(len(chunk))
                f.write(chunk)
        print("دانلود مستقیم تمام شد!\n")
    except Exception as e:
        print(f"خطا در دانلود مستقیم: {e}")
        raise
else:
    print("لینک سایت ویدیو → دانلود با yt-dlp (حداکثر 720p)")
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
        'outtmpl': input_filename,
        'merge_output_format': 'mp4',
        'concurrent_fragment_downloads': 10,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("دانلود با موفقیت تموم شد!\n")
    except Exception as e:
        print(f"خطا در دانلود: {e}")
        print("لینک رو چک کن یا دوباره امتحان کن.")
        raise

# چک کردن وجود GIF و فونت
if not os.path.exists(gif_filename):
    print(f"خطا: فایل {gif_filename} پیدا نشد! در ریشه Colab آپلود کن.")
elif not os.path.exists(font_filename):
    print(f"خطا: فایل {font_filename} پیدا نشد! در ریشه Colab آپلود کن.")
else:
    print(f"فایل‌های {gif_filename} و {font_filename} پیدا شدن.\n")

# محاسبه مدت زمان ویدیو برای نوار پیشرفت
duration_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{input_filename}\""
duration = float(subprocess.check_output(duration_cmd, shell=True).strip())

# دریافت اطلاعات کدک ویدیوی اصلی
probe_cmd = [
    'ffprobe', '-v', 'quiet',
    '-select_streams', 'v:0',
    '-show_entries', 'stream=codec_name,bit_rate,width,height',
    '-of', 'json',
    input_filename
]

try:
    probe_result = subprocess.check_output(probe_cmd, stderr=subprocess.STDOUT)
    video_info = json.loads(probe_result)
    codec_name = video_info['streams'][0]['codec_name']
    original_bitrate = int(video_info['streams'][0].get('bit_rate', 0))
    
    print(f"اطلاعات ویدیوی اصلی:")
    print(f"- کدک: {codec_name}")
    print(f"- بیت ریت: {original_bitrate // 1000 if original_bitrate > 0 else 'نامشخص'} kbps")
    
    if original_bitrate > 0:
        target_bitrate = int(original_bitrate * 1.05)
        if original_bitrate > 3000000:
            crf_value = 20
        elif original_bitrate > 1500000:
            crf_value = 21
        else:
            crf_value = 22
        
        print(f"- بیت ریت هدف: {target_bitrate // 1000} kbps (5% افزایش)")
        print(f"- CRF انتخابی: {crf_value}")
    else:
        crf_value = 21
        print(f"- CRF انتخابی: {crf_value} (پیش‌فرض)")
        
except Exception as e:
    print(f"خطا در دریافت اطلاعات ویدیو: {e}")
    crf_value = 21
    print(f"استفاده از CRF پیش‌فرض: {crf_value}")

# پردازش با FFmpeg: GIF + متن با فونت دلخواه و کدورت 70%
print("\nدر حال اضافه کردن واترمارک (GIF بالا راست + متن پایین وسط با کدورت 70%)...")

ffmpeg_cmd = [
    'ffmpeg', '-i', input_filename,
    '-ignore_loop', '0', '-i', gif_filename,
    '-filter_complex',
    '[1:v]colorkey=0x000000:0.15:0.1[ckout];'
    '[ckout]scale=180:-1[logo];'
    '[0:v][logo]overlay=W-w-30:30:shortest=1[tmp];'
    '[tmp]drawtext='
    'fontfile=/content/' + font_filename + ':'
    'text=\'t.me/SeriesPlus1\':'
    'fontcolor=white@0.7:'
    'fontsize=40:'
    'shadowcolor=black@0.8:shadowx=2:shadowy=2:'
    'x=(w-text_w)/2:y=h-text_h-30'
    '[v]',
    '-map', '[v]', '-map', '0:a?',
    '-c:v', 'libx264',
    '-preset', 'faster',
    '-crf', str(crf_value),
    '-maxrate', f'{int(original_bitrate * 1.05)}' if original_bitrate > 0 else None,
    '-bufsize', f'{int(original_bitrate * 2.1)}' if original_bitrate > 0 else None,
    '-c:a', 'aac', '-b:a', '128k',
    '-movflags', '+faststart',
    '-y', output_path
]

ffmpeg_cmd = [arg for arg in ffmpeg_cmd if arg is not None]

process = subprocess.Popen(ffmpeg_cmd, stderr=subprocess.PIPE, universal_newlines=True)

with tqdm(total=duration, unit='s', desc="پردازش نهایی (GIF + متن)", colour='magenta') as pbar:
    for line in process.stderr:
        if 'time=' in line:
            time_str = line.split('time=')[1].split()[0]
            h, m, s = map(float, time_str.split(':'))
            current = h*3600 + m*60 + s
            pbar.n = min(current, duration)
            pbar.refresh()

process.wait()

# محاسبه حجم فایل‌ها
input_size = os.path.getsize(input_filename) / (1024*1024)  # MB
output_size = os.path.getsize(output_path) / (1024*1024)  # MB

print(f"\nحجم فایل ورودی: {input_size:.2f} MB")
print(f"حجم فایل خروجی: {output_size:.2f} MB")

if input_size > 0:
    size_increase = ((output_size - input_size) / input_size) * 100
    print(f"افزایش حجم: {size_increase:.1f}%")

print("\nعملیات با موفقیت تموم شد!")
print(f"فایل نهایی با واترمارک ذخیره شد:")
print(f"مسیر: {output_path}")
print("از Google Drive باز کن و پخش کن!")
