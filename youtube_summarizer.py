import json
import os
import sqlite3

import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeSummarizer:
    """
    Summarizes transcripts of YouTube videos.
    """
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

    def __init__(self, video_id: str):
        """
        :param video_id: identifies the video at YouTube
        """
        self.video_id = video_id
        self.language = None
        self.conn = None
        self.cursor = None
        self.transcript_text = None
        self.summary_text = None
        self.title_text = None
        self.target_dir = os.environ["TARGET_DIRECTORY"]

    def open_database(self):
        db_path = f"{self.target_dir}/youtube-transcript.db"
        self.conn = sqlite3.connect(db_path)
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
            self.transcript_text = row[2]
        else:
            transcript = self.fetch_youtube_transcript()
            if transcript is not None:
                self.language = transcript.language_code
                entries = transcript.fetch()
                self.transcript_text = " ".join(entry["text"] for entry in entries)
                self.cursor.execute("INSERT INTO transcript VALUES (?, ?, ?)",
                                    (self.video_id, self.language, self.transcript_text))
                self.conn.commit()
            else:
                raise Exception("transcript not found")
        self.conn.close()

    def summarize_text(self, input_text: str, prompt_selector: str):
        prefix = self.prompts[self.language][prompt_selector]
        prompt = f":{prefix}\n\n{input_text}"

        label_request = " After the summary list 3 labels that categorizes the text." if prompt_selector == "summary" else ""

        request = {
            "model": self.model,
            "messages": [
                {
                    "role": "developer",
                    "content": f"You are summarizing video transcripts. You answer with the summary only and do not mention the source.{label_request}"
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
        return json_result.get("choices")[0].get("message").get("content")

    def write_final_summary(self):
        full_summary = f"# Summarizing YouTube videos\n\nvideo URL: https://www.youtube.com/watch?v={self.video_id}\n\n## Title\n\n{self.title_text}\n\n## Summary\n\n{self.summary_text}"

        output_path = f"{self.target_dir}/final-summary.md"
        with open(output_path, "w") as final_summary_file:
            final_summary_file.write(full_summary)

    def summarize(self):
        """
        Summarizes the transcript and writes it into a file final-summary.md.
        """
        self.fetch_transcript()
        self.summary_text = self.summarize_text(self.transcript_text, "summary")
        self.title_text = self.summarize_text(self.summary_text, "title")
        self.write_final_summary()

    def jsonSummary(self):
        """
        Returns a JSON string with fields language, title and summary.
        """
        self.summarize()

        summary_dict = {
            "language": self.language,
            "title": self.title_text,
            "summary": self.summary_text
        }

        return json.dumps(summary_dict)
