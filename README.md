# Quizly Backend

REST API for Quizly, an app that turns a YouTube video into a quiz. The backend
downloads the audio track of a video, transcribes it locally with Whisper and
sends the transcript to Gemini, which writes ten multiple-choice questions with
four options each.

Built with Django and the Django REST Framework. Authentication uses JWT stored
in HTTP-only cookies, so the frontend never touches the tokens itself.

## Requirements

Two of these are system packages and are **not** installed by pip:

- **Python 3.12**
- **FFmpeg** — required by Whisper and by the audio extraction step
- **Deno** — yt-dlp needs a JavaScript runtime to resolve YouTube media URLs.
  Without it downloads of newer videos fail.
- A **Gemini API key**, free of charge at https://aistudio.google.com/apikey

On macOS both system packages come from Homebrew:

```bash
brew install ffmpeg deno
```

On Debian or Ubuntu:

```bash
sudo apt install ffmpeg
curl -fsSL https://deno.land/install.sh | sh
```

## Setup

```bash
git clone https://github.com/MarcelHaessler/backend.Quizly.git
cd backend.Quizly
python3.12 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

Installing the requirements pulls in PyTorch and takes a while, roughly one
gigabyte of disk space.

Copy the example environment file and add your own key:

```bash
cp .env.example .env
```

```
GEMINI_API_KEY=your_key_here
```

Create the database and an admin account:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Start the server:

```bash
python manage.py runserver
```

The API is then available at http://127.0.0.1:8000/api/ and the admin panel at
http://127.0.0.1:8000/admin/.

The first quiz you create downloads the Whisper model, about 140 MB. This
happens once and is cached in `~/.cache/whisper`.

## Frontend

The frontend is a separate project. Serve it with its own folder as the web
root, for example with the Live Server extension in VS Code. It links its assets
and redirects absolutely (`/assets/...`, `/pages/login.html`), so serving a
parent folder results in 404s.

The allowed origins are ports 5500 and 5501 on localhost. If your server uses a
different port, add it to `CORS_ALLOWED_ORIGINS` in `core/settings.py`.

## Authentication

Login returns two cookies, `access_token` and `refresh_token`. Both are
HTTP-only, so JavaScript cannot read them. Every request to a protected endpoint
must be sent with `credentials: "include"`; an `Authorization` header is not
used.

Logging out puts the refresh token on a blacklist. Old tokens stay unusable
after that, even if someone copied them beforehand.

## Endpoints

All paths are prefixed with `/api/`.

| Method | Path | Description |
| --- | --- | --- |
| POST | `register/` | Creates an account |
| POST | `login/` | Validates credentials and sets both cookies |
| POST | `logout/` | Blacklists the refresh token and clears the cookies |
| POST | `token/refresh/` | Issues a new access token |
| POST | `quizzes/` | Creates a quiz from a YouTube URL |
| GET | `quizzes/` | Lists the quizzes of the logged-in user |
| GET | `quizzes/<id>/` | Returns a single quiz |
| PATCH | `quizzes/<id>/` | Changes title and description |
| DELETE | `quizzes/<id>/` | Deletes a quiz and its questions |

Creating a quiz takes between 20 seconds and a few minutes, depending on the
length of the video. The request is answered only when the quiz is finished.

Any YouTube link works as input, including short `youtu.be` links and share
links with tracking parameters. The backend reduces them to the canonical
`watch?v=` form before storing them. Links that are not YouTube are rejected
with a 400.

Quizzes are private. Reading, changing or deleting a quiz that belongs to
someone else returns a 403.

## Project structure

```
core/                Django project, settings and root URLs
auth_app/            Registration, login, logout, token refresh
  api/
    authentication.py  Reads the JWT from the cookie
    serializers.py     Registration and its validation
    urls.py            Routes for the auth endpoints
    utils.py           Cookie helpers and the login response body
    views.py           The four auth endpoints
quiz_app/            Quizzes and the generation pipeline
  models.py          Quiz and Question
  admin.py           Admin panel, questions editable inside a quiz
  utils.py           Download, transcription, Gemini, storage
  api/
    permissions.py     Owner check
    serializers.py     Quiz output and URL input
    urls.py            Routes for the quiz endpoints
    views.py           The quiz endpoints
```

The pipeline lives in `quiz_app/utils.py` rather than in a view, because it does
not deal with requests or responses. Views only take a request apart and put an
answer together.

## Notes

Audio files are written to a temporary directory that is removed as soon as the
transcript exists, so nothing accumulates on disk.

Whisper runs on the CPU and uses the `base` model. The model name is a constant
in `quiz_app/utils.py` and can be swapped for a larger one if the transcripts
are not accurate enough.

The Gemini call uses a response schema, which is why the answers always contain
exactly ten questions with exactly four options.
