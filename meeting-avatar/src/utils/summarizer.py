from transformers import pipeline

class Summarizer:
    def __init__(self, model="sshleifer/distilbart-cnn-12-6"):
        self.pipeline = pipeline("summarization", model=model)

    def summarize(self, text, max_length=150):
        if not text:
            return ""
        out = self.pipeline(text, max_length=max_length, min_length=30, do_sample=False)
        return out[0]["summary_text"]