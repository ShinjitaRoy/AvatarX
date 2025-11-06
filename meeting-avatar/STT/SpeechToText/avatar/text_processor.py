"""
Text processing module for summarization and NLP tasks.
"""

import os
import nltk
from typing import List, Optional
from transformers import pipeline
from . import config

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')


class TextProcessor:
    def __init__(self):
        """Initialize the text processor with the summarization model.

        If an OpenAI API key is available and `USE_CHATGPT` is enabled in
        config, the class will prefer ChatGPT for summarization and fall
        back to the local transformers pipeline on failure.
        """
        # Local summarizer pipeline (kept for fallback and offline usage)
        try:
            self.summarizer = pipeline(
                "summarization",
                model=config.SUMMARIZATION_MODEL,
                device=-1  # CPU, use 0 for GPU if available
            )
        except Exception as e:
            print(f"Warning: could not initialize local summarizer pipeline: {e}")
            self.summarizer = None

        # Try to import OpenAI if requested/available
        self.use_openai = config.USE_CHATGPT or bool(os.getenv("OPENAI_API_KEY"))
        self.openai = None
        if self.use_openai:
            try:
                import openai
                self.openai = openai
                # Let openai library pick up API key from environment or user config
                if not getattr(self.openai, 'api_key', None):
                    self.openai.api_key = os.getenv("OPENAI_API_KEY")
            except Exception as e:
                print(f"Warning: OpenAI library not available: {e}")
                self.openai = None

    def summarize_text(self, text: str) -> Optional[str]:
        """
        Generate a summary of the input text.

        Behavior:
        - If OpenAI (ChatGPT) is available and enabled, use it for a higher-quality
          summarization.
        - Otherwise fall back to the local transformers summarizer.

        Args:
            text (str): Input text to summarize

        Returns:
            str: Summarized text or None if failed
        """
        try:
            # Normalize whitespace
            text = ' '.join(text.split())

            # If text is short, just return it unchanged
            if len(text.split()) < 50:
                return text

            # Use OpenAI/ChatGPT when available
            if self.openai:
                try:
                    # Prepare prompt
                    system_prompt = (
                        "You are an expert meeting summarizer that creates detailed, well-structured summaries. "
                        "Focus on capturing key decisions, action items, and important discussion points. "
                        "Structure the output with clear sections and bullet points."
                    )
                    user_prompt = (
                        "Create a comprehensive meeting summary with the following structure:\n"
                        "1. Main Topics Discussed (bullet points)\n"
                        "2. Key Decisions Made (if any)\n"
                        "3. Action Items and Assignments (if any)\n"
                        "4. Important Discussion Points\n"
                        "5. Next Steps (if mentioned)\n\n"
                        "Meeting Content:\n" + text
                    )

                    # Use ChatCompletion API (openai.ChatCompletion.create) for compatibility
                    response = self.openai.ChatCompletion.create(
                        model=config.OPENAI_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=config.OPENAI_TEMPERATURE,
                        max_tokens=1000,  # Increased for more detailed summaries
                    )

                    # Extract content
                    choices = response.get("choices") or []
                    if choices:
                        summary_text = choices[0].get("message", {}).get("content") or choices[0].get("text")
                        if summary_text:
                            return summary_text.strip()
                except Exception as e:
                    print(f"OpenAI summarization failed, falling back: {e}")

            # Fallback to local summarizer
            if self.summarizer:
                try:
                    summary = self.summarizer(
                        text,
                        max_length=config.SUMMARY_MAX_LENGTH,
                        min_length=config.SUMMARY_MIN_LENGTH,
                        do_sample=False
                    )
                    return summary[0]['summary_text']
                except Exception as e:
                    print(f"Error in local text summarization: {str(e)}")

            # If nothing else worked, return the original text
            return text

        except Exception as e:
            print(f"Error in text summarization: {str(e)}")
            return None
    
    def get_key_sentences(self, text: str, num_sentences: int = 3) -> List[str]:
        """
        Extract key sentences from text using NLTK.
        
        Args:
            text (str): Input text
            num_sentences (int): Number of key sentences to extract
            
        Returns:
            List[str]: List of key sentences
        """
        try:
            sentences = nltk.sent_tokenize(text)
            if len(sentences) <= num_sentences:
                return sentences
            
            # Simple extraction based on sentence position
            # You can implement more sophisticated methods here
            return sentences[:num_sentences]
        except Exception as e:
            print(f"Error in key sentence extraction: {str(e)}")
            return []
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Cleaned text
        """
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Add more cleaning steps as needed
        return text.strip()