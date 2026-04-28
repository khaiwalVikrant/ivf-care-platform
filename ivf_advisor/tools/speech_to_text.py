"""Speech-to-text transcription using Google Cloud Speech-to-Text API."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: str, language_code: str = "en-IN") -> Optional[str]:
    """Transcribe an audio file to text using Google Cloud Speech-to-Text."""
    from google.cloud import speech  # type: ignore

    client = speech.SpeechClient()

    with open(audio_path, "rb") as f:
        audio_content = f.read()

    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
        language_code=language_code,
        alternative_language_codes=["hi-IN", "en-US"] if language_code == "en-IN" else ["en-IN"],
        enable_automatic_punctuation=True,
        audio_channel_count=1,
    )

    response = client.recognize(config=config, audio=audio)

    if not response.results:
        return None

    transcript = " ".join(
        result.alternatives[0].transcript
        for result in response.results
        if result.alternatives
    )
    return transcript.strip() or None


def transcribe_audio_bytes(audio_bytes: bytes, language_code: str = "en-IN") -> Optional[str]:
    """Transcribe raw audio bytes to text.

    Args:
        audio_bytes: Raw audio bytes (WAV format).
        language_code: BCP-47 language code.

    Returns:
        Transcribed text string, or None if transcription failed.
    """
    try:
        from google.cloud import speech  # type: ignore

        client = speech.SpeechClient()

        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_code,
            alternative_language_codes=["hi-IN", "en-US"] if language_code == "en-IN" else ["en-IN"],
            enable_automatic_punctuation=True,
            model="latest_long",
        )

        response = client.recognize(config=config, audio=audio)

        if not response.results:
            return None

        transcript = " ".join(
            result.alternatives[0].transcript
            for result in response.results
            if result.alternatives
        )
        return transcript.strip() or None

    except Exception as exc:
        logger.error("Speech transcription failed: %s", exc)
        return None
