# Summarizes a text file

import json

import requests
from youtube_transcript_api import YouTubeTranscriptApi


def fetch_youtube_transcript(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    full_text = " ".join(entry["text"] for entry in transcript)
    with open("transcript.txt", "w") as output_file:
        output_file.write(full_text)


def summarize_text(input_filename, prompt, output_filename):
    with open(input_filename, "r") as input_file:
        input_text = input_file.read()

    url = "http://localhost:11434/api/generate"
    model = "llama3.2"
    prompt = f":{prompt}\n\n{input_text}"
    max_length = 1024

    request = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_length
        }
    }

    response = requests.post(url, json=request)
    response.raise_for_status()

    json_result = json.loads(response.text)
    summary_text = json_result.get("response", "").strip()
    with open(output_filename, "w") as output_file:
        output_file.write(summary_text)


# fetch_youtube_transcript("KcSXcpluDe4")
summarize_text("transcript.txt", "Summarize the following text", "summary1.md")
summarize_text("summary1.md", "Summarize the following text as one sentence. Output the summary only.", "summary2.md")
