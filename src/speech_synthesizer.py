"""Synthesize podcast audio from scripts using Azure Speech Service."""

import re
import os
import time
import tempfile
import azure.cognitiveservices.speech as speechsdk

from .config import Config

# Neural voices for natural-sounding speech
VOICES = {
    "narrator": "en-US-AndrewMultilingualNeural",
    "alex": "en-US-AndrewMultilingualNeural",
    "sam": "en-US-EmmaMultilingualNeural",
}


def synthesize_single_narrator(script: str, output_path: str) -> str:
    """Synthesize a single-narrator script to an MP3 file."""
    ssml = _build_single_ssml(script)
    return _synthesize_ssml(ssml, output_path)


def synthesize_conversation(script: str, output_path: str) -> str:
    """Synthesize a two-host conversation script to an MP3 file.

    Handles Azure Speech's 50 voice element limit by merging consecutive
    same-speaker lines and chunking into multiple synthesis calls.
    """
    segments = _parse_conversation_segments(script)

    if len(segments) <= 48:
        ssml = _build_conversation_ssml_from_segments(segments)
        return _synthesize_ssml(ssml, output_path)

    # Split into chunks of ≤48 voice elements, synthesize each, then concatenate
    chunks = [segments[i:i + 48] for i in range(0, len(segments), 48)]
    temp_files = []
    temp_dir = tempfile.mkdtemp(prefix="podcast_")
    try:
        for idx, chunk in enumerate(chunks):
            temp_path = os.path.join(temp_dir, f"part{idx}.mp3")
            ssml = _build_conversation_ssml_from_segments(chunk)
            _synthesize_ssml(ssml, temp_path)
            temp_files.append(temp_path)

        _concatenate_mp3(temp_files, output_path)
        return output_path
    finally:
        # Speech SDK may hold file locks briefly; retry cleanup
        for f in temp_files:
            for attempt in range(3):
                try:
                    if os.path.exists(f):
                        os.remove(f)
                    break
                except OSError:
                    time.sleep(0.5)
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass


def _get_speech_config() -> speechsdk.SpeechConfig:
    """Create speech config using key or token auth."""
    if Config.AZURE_SPEECH_KEY:
        return speechsdk.SpeechConfig(
            subscription=Config.AZURE_SPEECH_KEY,
            region=Config.AZURE_SPEECH_REGION,
        )
    else:
        from azure.identity import DefaultAzureCredential
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        auth_token = f"aad#{Config.AZURE_SPEECH_RESOURCE_ID}#{token.token}" if Config.AZURE_SPEECH_RESOURCE_ID else token.token
        return speechsdk.SpeechConfig(
            auth_token=auth_token,
            region=Config.AZURE_SPEECH_REGION,
        )


def _synthesize_ssml(ssml: str, output_path: str) -> str:
    """Synthesize SSML to an audio file."""
    speech_config = _get_speech_config()
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
    )

    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )

    result = synthesizer.speak_ssml_async(ssml).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return output_path
    elif result.reason == speechsdk.ResultReason.Canceled:
        details = result.cancellation_details
        raise RuntimeError(
            f"Speech synthesis canceled: {details.reason}. "
            f"Error: {details.error_details}"
        )
    else:
        raise RuntimeError(f"Speech synthesis failed: {result.reason}")


def _build_single_ssml(script: str) -> str:
    """Build SSML for single narrator."""
    escaped = _escape_xml(script)
    return f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
    xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
  <voice name="{VOICES['narrator']}">
    <mstts:express-as style="chat">
      <prosody rate="0%">
        {escaped}
      </prosody>
    </mstts:express-as>
  </voice>
</speak>"""


def _parse_conversation_segments(script: str) -> list[dict]:
    """Parse script into segments, merging consecutive same-speaker lines."""
    lines = script.strip().split("\n")
    segments = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^(Alex|Sam)\s*:\s*(.+)$", line, re.IGNORECASE)
        if match:
            speaker = match.group(1).lower()
            text = match.group(2).strip()
        else:
            speaker = "narrator"
            text = line

        # Merge with previous segment if same speaker
        if segments and segments[-1]["speaker"] == speaker:
            segments[-1]["text"] += " " + text
        else:
            segments.append({"speaker": speaker, "text": text})

    return segments


def _build_conversation_ssml_from_segments(segments: list[dict]) -> str:
    """Build SSML from parsed segments (each becomes one voice element)."""
    ssml_parts = []
    for seg in segments:
        voice = VOICES.get(seg["speaker"], VOICES["narrator"])
        text = _escape_xml(seg["text"])
        ssml_parts.append(
            f'  <voice name="{voice}">'
            f'<mstts:express-as style="chat">'
            f'<prosody rate="0%">{text}</prosody>'
            f"</mstts:express-as>"
            f"</voice>"
        )

    body = "\n".join(ssml_parts)
    return f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
    xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
{body}
</speak>"""


def _concatenate_mp3(input_files: list[str], output_path: str) -> None:
    """Concatenate MP3 files by appending binary data."""
    with open(output_path, "wb") as out:
        for f in input_files:
            with open(f, "rb") as inp:
                out.write(inp.read())


def _build_conversation_ssml(script: str) -> str:
    """Build SSML for two-host conversation with voice switching."""
    segments = _parse_conversation_segments(script)
    return _build_conversation_ssml_from_segments(segments)


def _escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
