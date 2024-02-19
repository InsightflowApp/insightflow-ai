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

def transcribe(audio_file: str, dest_json: str | None = None) -> str:
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

    payload: FileSource = {
      "buffer": buffer_data,
    }

    # STEP 2: Configure Deepgram options for audio analysis
    options = PrerecordedOptions(
      model="nova-2",
      smart_format=True,
      diarize=True,
      topics=True,
      language="en",
    )

    # STEP 3: Call the transcribe_file method with the text payload and options
    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)

    # STEP 4: Write the response to the sample audio file
    if dest_json is None:
       dest_json = os.path.splitext(audio_file)[0] + '_transcript.json'

    with open(dest_json, 'w') as f:
      print(response.to_json(indent=2), file=f)

  except Exception as e:
    print(f"Exception: {e}")
  
  return dest_json


def main():
  # Path to the audio file
  AUDIO_FILE = "sample_audio/internet-boring.mp3"
  TRANSCRIPT_DEST = "sample_transcripts/internet-boring.json"
  transcribe(AUDIO_FILE, TRANSCRIPT_DEST)


if __name__ == "__main__":
    main()

