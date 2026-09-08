import json
import re
import tempfile
from functools import lru_cache
from pathlib import Path

import whisper
import yt_dlp
from django.conf import settings
from google import genai
from google.genai import types

from .models import Question, Quiz


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

GEMINI_MODEL = 'gemini-3.6-flash'

QUIZ_PROMPT = (
    'Create a quiz with exactly 10 multiple-choice questions from the '
    'transcript below. Every question needs exactly 4 answer options, and '
    '"answer" must match one of those options word for word. Add a short '
    'title and a one-sentence description. Write everything in the same '
    'language as the transcript.\n\nTranscript:\n{transcript}'
)

QUIZ_SCHEMA = {
    'type': 'object',
    'properties': {
        'title': {'type': 'string'},
        'description': {'type': 'string'},
        'questions': {
            'type': 'array',
            'minItems': 10,
            'maxItems': 10,
            'items': {
                'type': 'object',
                'properties': {
                    'question_title': {'type': 'string'},
                    'question_options': {
                        'type': 'array',
                        'minItems': 4,
                        'maxItems': 4,
                        'items': {'type': 'string'},
                    },
                    'answer': {'type': 'string'},
                },
                'required': ['question_title', 'question_options', 'answer'],
            },
        },
    },
    'required': ['title', 'description', 'questions'],
}

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


@lru_cache(maxsize=1)
def get_gemini_client():
    """Creates the Gemini client once and reuses it."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_quiz_data(transcript):
    """Asks Gemini for a ten-question quiz and returns it as a dict."""
    response = get_gemini_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=QUIZ_PROMPT.format(transcript=transcript),
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema=QUIZ_SCHEMA,
        ),
    )
    return json.loads(response.text)


def save_quiz(owner, watch_url, data):
    """Stores a generated quiz together with its questions."""
    quiz = Quiz.objects.create(
        owner=owner,
        title=data['title'],
        description=data['description'],
        video_url=watch_url,
    )
    for item in data['questions']:
        Question.objects.create(quiz=quiz, **item)
    return quiz


def create_quiz_from_url(owner, url):
    """Runs the full pipeline and returns the stored quiz."""
    watch_url = build_watch_url(extract_video_id(url))
    with tempfile.TemporaryDirectory() as tmp:
        audio_path = download_audio(watch_url, tmp)
        transcript = transcribe_audio(audio_path)
    data = generate_quiz_data(transcript)
    return save_quiz(owner, watch_url, data)