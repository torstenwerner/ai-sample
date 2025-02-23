# Summarizes a YouTube video in file final-summary.md.
# Writes additional files transcript.txt, summary.md, and title.md.
# Caches the transcripts in the sqlite database youtube-transcript.db.

from youtube_summarizer import YouTubeSummarizer

# specify YouTube video id
video_id = "bZzyPscbtI8"

summarizer = YouTubeSummarizer(video_id)
summarizer.fetch_transcript()
summarizer.summarize_text("transcript.txt", "summary", "summary.md")
summarizer.summarize_text("summary.md", "title", "title.md")
summarizer.write_final_summary()
