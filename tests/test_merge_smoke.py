"""
Smoke test cho merge_segments (video_utils.py).

Vì sao có test này: ffmpeg 8/9 (macOS Martin Riedl, Windows gyan) ĐÃ BỎ
`-filter_complex_script` — build cũ chạy được, build mới crash khâu ghép cuối
làm hỏng TOÀN BỘ video. Test này chạy đúng code-path đó với ffmpeg thật của
môi trường CI (không mock) để bắt sớm mọi regression tương tự:
  - dựng 3 đoạn video tổng hợp (color + tone) bằng ffmpeg
  - gọi merge_segments()
  - xác nhận file ra tồn tại, có cả video+audio, độ dài đúng ~3 giây

Chạy trực tiếp:  python -m tests.test_merge_smoke
"""
import os
import shutil
import subprocess
import sys
import tempfile

# Chạy được kể cả khi gọi "python tests/test_merge_smoke.py"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_utils import find_binary, merge_segments, ffprobe_duration


def _make_segment(ffmpeg, path, color, freq, dur=1.0, w=320, h=240, fps=30):
    """Dựng 1 đoạn video ngắn có cả hình và tiếng bằng ffmpeg."""
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c={color}:s={w}x{h}:r={fps}:d={dur}",
        "-f", "lavfi", "-i", f"sine=frequency={freq}:sample_rate=44100:duration={dur}",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k",
        "-shortest", path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _has_stream(ffprobe, path, kind):
    out = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", kind,
         "-show_entries", "stream=codec_type",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    return bool(out.stdout.strip())


def main():
    ffmpeg = find_binary("ffmpeg") or shutil.which("ffmpeg")
    ffprobe = find_binary("ffprobe") or shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        print("[SKIP] không thấy ffmpeg/ffprobe trong môi trường")
        return 0

    # In version để log CI thấy rõ đang test trên ffmpeg nào (giúp truy nguyên
    # khi có regression theo phiên bản).
    subprocess.run([ffmpeg, "-version"], check=False)

    with tempfile.TemporaryDirectory() as tmp:
        segs = []
        for i, (color, freq) in enumerate([("red", 220), ("green", 440), ("blue", 880)]):
            p = os.path.join(tmp, f"seg_{i:03d}.mp4")
            _make_segment(ffmpeg, p, color, freq, dur=1.0)
            segs.append(p)

        out = os.path.join(tmp, "merged.mp4")
        # Gọi hàm THẬT của app — chính là chỗ trước đây dùng
        # `-filter_complex_script` và crash trên ffmpeg 8/9.
        # Console Windows mặc định cp1252 — dấu tiếng Việt trong log của
        # merge_segments sẽ ném UnicodeEncodeError. Bọc print để test khỏi
        # chết vì i/o log (không liên quan tới lỗi mình muốn bắt).
        def safe_log(msg):
            try:
                print(msg)
            except UnicodeEncodeError:
                print(msg.encode("ascii", "replace").decode("ascii"))

        merge_segments(
            segs, out, ffmpeg=ffmpeg, ffprobe=ffprobe,
            durations=[1.0, 1.0, 1.0], target_fps=30, log=safe_log,
        )

        assert os.path.exists(out), "merge_segments không tạo được file ra"
        assert os.path.getsize(out) > 1000, "file ghép rỗng bất thường"
        assert _has_stream(ffprobe, out, "v"), "file ghép thiếu video stream"
        assert _has_stream(ffprobe, out, "a"), "file ghép thiếu audio stream"
        dur = ffprobe_duration(out, ffprobe)
        assert 2.5 <= dur <= 3.5, f"độ dài file ghép sai: {dur:.3f}s (kỳ vọng ~3s)"

    print("[OK] merge smoke test PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
