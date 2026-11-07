"""カルーセル画像(1080x1350)を縦長動画(1080x1920)のリールにする。
使い方: python scripts/make_reel.py images/posts/<フォルダ> [1枚あたりの秒数=3]
出力: 同じフォルダの reel.mp4(音なし、H.264)。上下は背景色で埋める。
"""
import subprocess
import sys
from pathlib import Path

folder = Path(sys.argv[1])
sec = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
slides = sorted(folder.glob("s*.png"), key=lambda p: int(p.stem[1:]))
if not slides:
    sys.exit("s1.png などが見つかりません")
lst = folder / "reel_list.txt"
with lst.open("w") as f:
    for p in slides:
        f.write(f"file '{p.resolve()}'\nduration {sec}\n")
    f.write(f"file '{slides[-1].resolve()}'\n")
out = folder / "reel.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                "-vf", "scale=1080:1350,pad=1080:1920:0:285:color=0x071a33,format=yuv420p,fps=30",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", str(out)], check=True)
lst.unlink()
print(out)
