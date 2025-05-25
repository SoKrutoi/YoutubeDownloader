# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
# ВОЗМОЖНО НЕ РАБОТАЕТ
# MAY NOT WORKING
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
import os
import subprocess
import math

input_file = "input.mp4"
output_folder = "output"
os.makedirs(output_folder, exist_ok=True)

chunk_duration = 300

def get_video_duration(filename):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

duration = get_video_duration(input_file)
num_chunks = math.ceil(duration / chunk_duration)

for i in range(num_chunks):
    start_time = i * chunk_duration
    output_path = os.path.join(output_folder, f"Видео_{i + 1}.mp4")
    cmd = [
        "ffmpeg",
        "-ss", str(start_time),
        "-i", input_file,
        "-t", str(chunk_duration),
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd)

print("✅ Готово! Видео разрезано.")