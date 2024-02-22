#!/usr/bin/env python3
# transcribe-video.py
import os
from dotenv import load_dotenv
from typing import Union

from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

load_dotenv()
API_KEY = os.getenv("DG_API_KEY")

# Configure Deepgram options for audio analysis
OPTIONS = PrerecordedOptions(
  model="nova-2",
  smart_format=True,
  diarize=True,
  # topics=True,
  language="en",
)


def transcribe(url: str, dest_json: str | None = None) -> str:
  """
  Transcribe audio from source file to destination json.
  
  :param url: the URL of the audio (or video) file to read.
  :param dest_json: the file to write the transcript to.
  :returns dest_json: the file to which the transcript was written.
  """
  try:
    deepgram = DeepgramClient(API_KEY)
    audio_url = { 'url': url }

    # Call the transcribe_file method with the text payload and options
    response = deepgram.listen.prerecorded.v("1").transcribe_url(audio_url, OPTIONS)

    # Write the response to the sample audio file
    if dest_json is None:
       print(os.path.splitext(os.path.split(audio_url)[1])[0] + '.json')
       dest_json = "dest.json"

    with open(dest_json, 'w') as f:
      print(response.to_json(indent=2), file=f)

  except Exception as e:
    print(f"Exception: {e}")
  
  return dest_json

def transcribe_local(audio_file: str, dest_json: str | None = None) -> str:
  """
  Transcribe audio from source file to destination json.
  
  :param audio_file: the name of the audio file to read.
  :param dest_json: the file to write the transcript to.
  :returns dest_json: the file to which the transcript was written.
  """
  try:
    # STEP 1: Create a Deepgram client using the API key
    deepgram = DeepgramClient(API_KEY)

    with open(audio_file, "rb") as file:
      buffer_data = file.read()

    payload: FileSource = { "buffer": buffer_data }

    # Call the transcribe_file method with the text payload and options
    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, OPTIONS)

    if dest_json is None:
       dest_json = os.path.splitext(os.path.split(audio_file)[1])[0] + '.json'

    # write response to destination file
    with open(dest_json, 'w') as f:
      print(response.to_json(indent=2), file=f)

  except Exception as e:
    print(f"Exception: {e}")
  
  return dest_json

def main():
  # Path to the audio file
  AUDIO_FILE = "sample_audio/internet-boring.mp3"
  TRANSCRIPT_DEST = "sample_transcripts/internet-boring.json"
  transcribe_local(AUDIO_FILE, TRANSCRIPT_DEST)


if __name__ == "__main__":
    main()

