import subprocess
import os
import logging

def extract_keyframes(video_path: str, output_dir: str, max_frames: int = 6) -> list:
    """Extracts keyframes from a video using ffmpeg."""
    if not os.path.exists(video_path):
        return []
    
    os.makedirs(output_dir, exist_ok=True)
    output_pattern = os.path.join(output_dir, "frame_%03d.jpg")
    
    # ffmpeg command to extract keyframes (I-frames)
    # -vf "select='eq(pict_type,PICT_TYPE_I)'" extracts only I-frames
    # -vsync vfr ensures we don't get duplicate frames if there are few I-frames
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"select='eq(pict_type,PICT_TYPE_I)',scale=1280:-1",
        "-vsync", "vfr",
        "-q:v", "2",
        "-frames:v", str(max_frames),
        output_pattern,
        "-y"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        frames = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.startswith("frame_")]
        return sorted(frames)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.warning(f"FFmpeg extraction failed for {video_path}: {e}")
        return []
