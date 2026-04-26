import sys, os, subprocess
sys.path.append('backend')
import imageio_ffmpeg

ffmpeg    = imageio_ffmpeg.get_ffmpeg_exe()
story_id  = 'story_66657af1'
list_path = os.path.abspath('storage/videos/concat.txt')

scene_files = sorted([
    os.path.abspath('storage/videos/' + story_id + '_scene_0' + str(i) + '.mp4')
    for i in range(1, 5)
])

with open(list_path, 'w') as f:
    for p in scene_files:
        f.write("file '" + p.replace('\\', '/') + "'\n")

print('Concat file contents:')
print(open(list_path).read())

output = os.path.abspath('storage/videos/' + story_id + '_final.mp4')

cmd = [
    ffmpeg, '-y',
    '-f', 'concat', '-safe', '0',
    '-i', list_path,
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
    '-c:a', 'aac', '-b:a', '128k',
    '-movflags', '+faststart',
    output
]

result = subprocess.run(cmd, capture_output=True, text=True)
print('Return code:', result.returncode)

if result.returncode == 0:
    size = os.path.getsize(output) / (1024 * 1024)
    print('Final video:', output)
    print('Size:', round(size, 2), 'MB')
else:
    print('FFmpeg error:')
    print(result.stderr[-600:])
