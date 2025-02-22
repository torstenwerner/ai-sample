# Summarizes a YouTube video in file final-summary.md.
# Writes additional files transcript.txt, summary.md, and title.md.
# Caches the transcripts in the sqlite database youtube-transcript.db.

import json
import sqlite3

import requests
from youtube_transcript_api import YouTubeTranscriptApi

# Some constants you might want to adapt.
# The most important is the YouTube video id and the language code:
video_id = "qwLAs_K0aeA"
language = "de"
model = "llama3.1"
max_transcript_length = 8 * 1024
max_summary_length = 1024
prompts = {
    "en": {
        "summary": "Summarize the following text. Output the summary only.",
        "title": "Summarize the following text as one sentence. Output the summary only."
    },
    "de": {
        "summary": "Fasse den folgenden Text zusammen. Antworte nur mit der Zusammenfassung.",
        "title": "Fasse den folgenden Text in einem Satz zusammen. Antworte nur mit der Zusammenfassung."
    }
}


def open_database():
    conn = sqlite3.connect('youtube-transcript.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcript (
            id TEXT NOT NULL,
            transcript TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn, cursor


def fetch_youtube_transcript():
    conn, cursor = open_database()
    cursor.execute("SELECT t.id, t.transcript FROM transcript t where t.id = ?", (video_id,))
    row = cursor.fetchone()
    if row is not None:
        full_text = row[1]
    else:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        full_text = " ".join(entry["text"] for entry in transcript)
        cursor.execute("INSERT INTO transcript VALUES (?, ?)", (video_id, full_text))
        conn.commit()
    with open("transcript.txt", "w") as output_file:
        output_file.write(full_text)
    conn.close()


def summarize_text(input_filename, prompt_selector, output_filename):
    with open(input_filename, "r") as input_file:
        input_text = input_file.read(max_transcript_length)

    url = "http://localhost:11434/api/generate"

    prefix = prompts[language][prompt_selector]
    prompt = f":{prefix}\n\n{input_text}"

    request = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_summary_length
        }
    }

    response = requests.post(url, json=request)
    response.raise_for_status()

    json_result = json.loads(response.text)
    summary_text = json_result.get("response", "").strip()
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


fetch_youtube_transcript()
summarize_text("transcript.txt", "summary", "summary.md")
summarize_text("summary.md", "title", "title.md")
write_final_summary()
