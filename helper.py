from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def fetch_youtube_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()

        transcript_list = api.list(video_id)

        transcript = transcript_list.find_transcript(["en"])

        fetched_snippets = transcript.fetch()

        text = " ".join([snippet.text for snippet in fetched_snippets])

        return text

    except (TranscriptsDisabled, NoTranscriptFound):
        print("Transcript not available.")
        return ""

    except Exception as e:
        print(f"Transcript fetch failed: {str(e)}")
        return ""
