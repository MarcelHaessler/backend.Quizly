import re
from functools import lru_cache
from pathlib import Path

import whisper
import yt_dlp


AUDIO_OPTIONS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }],
    'quiet': True,
    'noplaylist': True,
    'noprogress': True,
}

YOUTUBE_ID_PATTERN = re.compile(
    r'(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/)|youtu\.be/)'
    r'([A-Za-z0-9_-]{11})'
)

WHISPER_MODEL_NAME = 'base'

def extract_video_id(url):
    """Returns the 11-character YouTube video id, or None if there is none."""
    match = YOUTUBE_ID_PATTERN.search(url)
    return match.group(1) if match else None


def build_watch_url(video_id):
    """Returns the canonical watch URL for a video id."""
    return f'https://www.youtube.com/watch?v={video_id}'


def download_audio(watch_url, target_dir):
    """Downloads the audio track of a YouTube video as an MP3 file."""

    options = dict(AUDIO_OPTIONS, outtmpl=str(Path(target_dir) / 'audio.%(ext)s'))

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([watch_url])
    return Path(target_dir) / 'audio.mp3'


@lru_cache(maxsize=1)
def get_whisper_model():
    """Loads the Whisper model once and keeps it in memory."""
    return whisper.load_model(WHISPER_MODEL_NAME)


def transcribe_audio(audio_path):
    """Returns the spoken text of an audio file as a single string."""
    result = get_whisper_model().transcribe(str(audio_path))
    return result['text'].strip()