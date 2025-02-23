# Summarizes a YouTube video in file final-summary.md.
# Writes additional files transcript.txt, summary.md, and title.md.
# Caches the transcripts in the sqlite database youtube-transcript.db.

import json
import os
import sqlite3

import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

# Some constants you might want to adapt.
# The most important is the YouTube video id and the language code:
video_id = "NKYxdzSNqzE"
# Ollama
# url = "http://localhost:11434/v1/chat/completions"
# OpenAI
url = "https://api.openai.com/v1/chat/completions"
# LM Studio
# url = "http://localhost:1234/v1/chat/completions"
# model = "llama3.1"
# model = "llama3.2"
model = "gpt-4o-mini"
# model = "mistral-nemo-instruct-2407"
# model = "deepseek-r1-distill-qwen-1.5b"
max_transcript_length = 16 * 1024
# max_summary_length = 1024
prompts = {
    "en": {
        "summary": "",
        "title": "Summarize as one sentence:"
    },
    "de": {
        "summary": "Fasse in deutscher Sprache zusammen.",
        "title": "Fasse in einem Satz in deutscher Sprache zusammen."
    }
}

load_dotenv()
global language


def open_database():
    conn = sqlite3.connect('youtube-transcript.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcript (
            id TEXT NOT NULL,
            language TEXT NOT NULL,
            transcript TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn, cursor


def fetch_youtube_transcript():
    transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
    for transcript in transcripts:
        if transcript.is_generated and transcript.language_code in ['en', 'de']:
            return transcript


def fetch_transcript():
    conn, cursor = open_database()
    cursor.execute("SELECT t.id, t.language, t.transcript FROM transcript t where t.id = ?", (video_id,))
    row = cursor.fetchone()
    global language
    if row is not None:
        language = row[1]
        full_text = row[2]
    else:
        transcript = fetch_youtube_transcript()
        if transcript is not None:
            language = transcript.language_code
            entries = transcript.fetch()
            full_text = " ".join(entry["text"] for entry in entries)
            cursor.execute("INSERT INTO transcript VALUES (?, ?, ?)", (video_id, language, full_text))
            conn.commit()
        else:
            raise Exception("transcript not found")
    with open("transcript.txt", "w") as output_file:
        output_file.write(full_text)
    conn.close()


def summarize_text(input_filename, prompt_selector, output_filename):
    with open(input_filename, "r") as input_file:
        input_text = input_file.read(max_transcript_length)

    prefix = prompts[language][prompt_selector]
    prompt = f":{prefix}\n\n{input_text}"

    request = {
        "model": model,
        "messages": [
            {
                "role": "developer",
                "content": "You are summarizing video transcripts. You answer with the summary only and do not mention the source."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    api_key = os.getenv("OPENAI_API_KEY")
    response = requests.post(url, json=request, headers={"Authorization": f"Bearer {api_key}"})
    response.raise_for_status()

    json_result = json.loads(response.text)
    summary_text = json_result.get("choices")[0].get("message").get("content")
    with open(output_filename, "w") as output_file:
        output_file.write(summary_text)


def write_final_summary():
    with open("summary.md", "r") as summary_file:
        summary_text = summary_file.read()
    with open("title.md", "r") as title_file:
        title_text = title_file.read()
    full_summary = f"# Summarizing YouTube videos\n\nvideo URL: https://www.youtube.com/watch?v={video_id}\n\n## Title\n\n{title_text}\n\n## Summary\n\n{summary_text}"
    with open("final-summary.md", "w") as final_summary_file:
        final_summary_file.write(full_summary)


fetch_transcript()
summarize_text("transcript.txt", "summary", "summary.md")
summarize_text("summary.md", "title", "title.md")
write_final_summary()
