import json
import os
import sqlite3

import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeSummarizer:
    # Some constants you might want to adapt.
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

    def __init__(self, video_id):
        self.video_id = video_id
        self.language = None
        self.conn = None
        self.cursor = None

    def open_database(self):
        self.conn = sqlite3.connect('youtube-transcript.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcript (
                id TEXT PRIMARY KEY NOT NULL,
                language TEXT NOT NULL,
                transcript TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def fetch_youtube_transcript(self):
        transcripts = YouTubeTranscriptApi.list_transcripts(self.video_id)
        for transcript in transcripts:
            if transcript.is_generated and transcript.language_code in ['en', 'de']:
                return transcript

    def fetch_transcript(self):
        self.open_database()
        self.cursor.execute("SELECT t.id, t.language, t.transcript FROM transcript t where t.id = ?", (self.video_id,))
        row = self.cursor.fetchone()
        if row is not None:
            self.language = row[1]
            full_text = row[2]
        else:
            transcript = self.fetch_youtube_transcript()
            if transcript is not None:
                self.language = transcript.language_code
                entries = transcript.fetch()
                full_text = " ".join(entry["text"] for entry in entries)
                self.cursor.execute("INSERT INTO transcript VALUES (?, ?, ?)", (self.video_id, self.language, full_text))
                self.conn.commit()
            else:
                raise Exception("transcript not found")
        with open("transcript.txt", "w") as output_file:
            output_file.write(full_text)
        self.conn.close()

    def summarize_text(self, input_filename, prompt_selector, output_filename):
        with open(input_filename, "r") as input_file:
            input_text = input_file.read(self.max_transcript_length)

        prefix = self.prompts[self.language][prompt_selector]
        prompt = f":{prefix}\n\n{input_text}"

        request = {
            "model": self.model,
            "messages": [
                {
                    "role": "developer",
                    "content": "You are summarizing video transcripts. You answer with the summary only and do not mention the source."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "store": False
        }

        api_key = os.getenv("OPENAI_API_KEY")
        response = requests.post(self.url, json=request, headers={"Authorization": f"Bearer {api_key}"})
        response.raise_for_status()

        json_result = json.loads(response.text)
        summary_text = json_result.get("choices")[0].get("message").get("content")
        with open(output_filename, "w") as output_file:
            output_file.write(summary_text)

    def write_final_summary(self):
        with open("summary.md", "r") as summary_file:
            summary_text = summary_file.read()
        with open("title.md", "r") as title_file:
            title_text = title_file.read()
        full_summary = f"# Summarizing YouTube videos\n\nvideo URL: https://www.youtube.com/watch?v={self.video_id}\n\n## Title\n\n{title_text}\n\n## Summary\n\n{summary_text}"
        with open("final-summary.md", "w") as final_summary_file:
            final_summary_file.write(full_summary)

    def summarize(self):
        self.fetch_transcript()
        self.summarize_text("transcript.txt", "summary", "summary.md")
        self.summarize_text("summary.md", "title", "title.md")
        self.write_final_summary()
