#!/usr/bin/env python3
# transcribe-video.py
import os
from dotenv import load_dotenv
import asyncio
import httpx
from datetime import datetime

from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
    PrerecordedResponse
)

TRANSCRIPT_FILE = 'transcripts'

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


async def _transcribe_url(url: str) -> PrerecordedResponse:
  """
  Given the deepgram client, transcribe audio from source file into a 
  persistent dict.
  
  :param url: the URL of the audio (or video) file to read.
  :returns response: the transcript contents.
  """
  print(f"transcribing {url}")

  client = DeepgramClient(API_KEY)
  timeout = httpx.Timeout(10.0, read=500.0)

  data = (
    await client.listen.asyncprerecorded.v("1")
    .transcribe_url({'url': url}, OPTIONS, timeout=timeout)
  )
  return data


async def _transcribe_local(audio_file: str) -> PrerecordedResponse:
  """
  Transcribe audio from source file.
  
  :param client: the Deepgram client.
  :param audio_file: the name of the audio file to read.
  :returns data: the transcript data written as a dict.
  """
  with open(audio_file, "rb") as file:
    buffer_data = file.read()

  print(f'done reading {audio_file}. sending to Deepgram client')

  payload: FileSource = { "buffer": buffer_data }

  client = DeepgramClient(API_KEY)
  timeout = httpx.Timeout(10.0, read=500.0)

  data = (
    client.listen.asyncprerecorded.v("1")
    .transcribe_file(payload, OPTIONS, timeout=timeout)
  )
  return data


async def _transcribe_urls(audio_urls : dict[str, str], target_dir : str = 'transcripts'):
  if not os.path.isdir(target_dir):
    os.makedirs(target_dir)

  tasks : list[asyncio.TaskGroup] = []
  start = datetime.now()
  print(f"Beginning transcription at {start}")

  async with asyncio.TaskGroup() as tg:
    for name, audio_url in audio_urls.items():
      t = tg.create_task(
        _transcribe_url(audio_url)
      )
      tasks.append((name, t))

  end = datetime.now()

  print(f"end time: {end}\ntotal transcribe time: {end - start}")
  print(f"writing files into {target_dir}")

  for (name, task) in tasks:
    data = task.result()
    
    with open(f'{target_dir}/{name}.json', 'w') as file:
      print(data.to_json(indent=2), file=file)

def transcribe_urls(audio_urls : dict[str, str], target_dir : str = 'transcripts'):
  asyncio.run(_transcribe_urls(audio_urls, target_dir))


async def main():
  dir_name = 'transcripts_temp/template_interviews'

  # audio_urls = {
  #   'spacewalk 1': "https://dpgr.am/spacewalk.wav",
  #   'spacewalk 2': "https://dpgr.am/spacewalk.wav",
  #   'spacewalk 3': "https://dpgr.am/spacewalk.wav",
  #   'spacewalk 4': "https://dpgr.am/spacewalk.wav",
  #   'spacewalk 5': "https://dpgr.am/spacewalk.wav",
  # }
  audio_urls = {
    "template research interview 3":
    '4e72f777-d179-452e-8629-8ef4d76f54ad',
    "template research interview 2":
    'cb9f1ff5-178f-4c46-977d-0940fc8a9b13',
    "template research interview 4":
    '9e26f983-d3fc-438f-988d-c1c2a93bf755',
    "template research interview 5":
    '44b8d19b-531a-4947-b075-05315a2ade90',
    "template research interview 1":
    'ecdefe35-563b-4b48-8f80-f891b8303a0d',
  }
  for key in audio_urls.keys():
    audio_urls[key] = f'https://insightflow-test.s3.us-east-2.amazonaws.com/{audio_urls[key]}.mp4'

  asyncio.run(_transcribe_urls(audio_urls, dir_name))

if __name__ == "__main__":
  main()

