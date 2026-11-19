"""
Test chống DÙNG LẠI NHẦM đoạn cũ + ghép khi đoạn lệch kích thước (video_utils.py).

Vì sao có test này: chạy 2 video KHÁC NHAU cùng tên '1.mp4' vào cùng thư mục output
thì bản cũ coi đoạn của video trước là "đã tồn tại, bỏ qua" -> ghép trộn nội dung 2
video, và ffmpeg chết vì concat lệch kích thước:
  'Input link in0:v0 parameters (size 360x640 ...) do not match ... (576x768 ...)'
Test dựng đúng tình huống đó bằng ffmpeg thật (không mock):
  1. video A (576x768) rồi video B (360x640) cùng tên -> B phải cắt lại, reset=True
  2. chạy lại đúng B -> dùng lại đoạn, reset=False
  3. 1 đoạn đã xử lý lệch kích thước -> merge_segments vẫn ghép ra đúng kích thước gốc

Chạy trực tiếp:  python tests/test_resume_guard.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_utils import (find_binary, split_video, merge_segments,
                         ffprobe_duration, _detect_size)


def _make_video(ffmpeg, path, w, h, dur, color):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run([
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c={color}:s={w}x{h}:r=30:d={dur}",
        "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=44100:duration={dur}",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", path,
    ], check=True, capture_output=True)


def _quiet(_msg):
    pass


def main():
    ffmpeg, ffprobe = find_binary("ffmpeg"), find_binary("ffprobe")
    if not ffmpeg or not ffprobe:
        print("[SKIP] không có ffmpeg/ffprobe")
        return 0

    tmp = tempfile.mkdtemp(prefix="tnt_resume_")
    try:
        seg_root = os.path.join(tmp, "out", "segments")
        a = os.path.join(tmp, "a", "1.mp4")
        b = os.path.join(tmp, "b", "1.mp4")
        _make_video(ffmpeg, a, 576, 768, 9, "red")
        _make_video(ffmpeg, b, 360, 640, 10, "blue")

        split_video(a, seg_root, 4, ffmpeg, ffprobe, log=_quiet)
        rec = split_video(b, seg_root, 4, ffmpeg, ffprobe, log=_quiet)
        assert rec["reset"], "video khác cùng tên phải bị cắt lại (reset=True)"
        sizes = {_detect_size(s["file"], ffprobe) for s in rec["segments"]}
        assert sizes == {(360, 640)}, f"còn đoạn của video cũ: {sizes}"

        again = split_video(b, seg_root, 4, ffmpeg, ffprobe, log=_quiet)
        assert not again["reset"], "chạy lại đúng video thì phải dùng lại đoạn cũ"

        segs = [s["file"] for s in rec["segments"]]
        proc = list(segs)
        bad = os.path.join(tmp, "out", "processed", "1", "1_000.mp4")
        _make_video(ffmpeg, bad, 576, 768, 4.5, "green")
        proc[0] = bad
        out = os.path.join(tmp, "out", "final.mp4")
        merge_segments(
            proc, out, ffmpeg=ffmpeg, ffprobe=ffprobe, log=_quiet,
            durations=[s["dur"] for s in rec["segments"]],
            starts=[s["start"] for s in rec["segments"]],
            source_path=rec["source"], target_fps=rec["fps"], audio_files=segs,
        )
        assert _detect_size(out, ffprobe) == (360, 640), "ghép ra sai kích thước gốc"
        dur = ffprobe_duration(out, ffprobe)
        assert 9.5 <= dur <= 10.5, f"độ dài file ghép sai: {dur:.3f}s (kỳ vọng ~10s)"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("[OK] resume guard test PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
