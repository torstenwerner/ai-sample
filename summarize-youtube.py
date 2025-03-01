# Summarizes a YouTube video in file final-summary.md.
# Writes additional files transcript.txt, summary.md, and title.md.
# Caches the transcripts in the sqlite database youtube-transcript.db.

from youtube_summarizer import YouTubeSummarizer

# specify YouTube video id
summarizer = YouTubeSummarizer("dMcZPkYUBxU")
summarizer.summarize()
#print(summarizer.jsonSummary())
