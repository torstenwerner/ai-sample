# Summarizes a YouTube video in file final-summary.md.
# Writes additional files transcript.txt, summary.md, and title.md.
# Caches the transcripts in the sqlite database youtube-transcript.db.

from youtube_summarizer import YouTubeSummarizer

# specify YouTube video id
YouTubeSummarizer("4Bdc55j80l8").summarize()
