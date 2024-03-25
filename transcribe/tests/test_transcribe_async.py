import pytest
import asyncio
import transcribe.transcribe_async as ta

def test__transcribe_urls():
  dir_name = 'transcripts_temp/template_interviews'

  # audio_urls = {
  #   'spacewalk 1': "https://dpgr.am/spacewalk.wav",
  #   'spacewalk 2': "https://dpgr.am/spacewalk.wav",
  #   'spacewalk 3': "https://dpgr.am/spacewalk.wav",
  #   'spacewalk 4': "https://dpgr.am/spacewalk.wav",
  #   'spacewalk 5': "https://dpgr.am/spacewalk.wav",
  # }
  audio_urls = {
    "template research interview 3.mp4":
    '4e72f777-d179-452e-8629-8ef4d76f54ad',
    "template research interview 2.mp4":
    'cb9f1ff5-178f-4c46-977d-0940fc8a9b13',
    "template research interview 4.mp4":
    '9e26f983-d3fc-438f-988d-c1c2a93bf755',
    "template research interview 5.mp4":
    '44b8d19b-531a-4947-b075-05315a2ade90',
    "template research interview 1.mp4":
    'ecdefe35-563b-4b48-8f80-f891b8303a0d',
  }
  for key in audio_urls.keys():
    audio_urls[key] = f'https://insightflow-test.s3.us-east-2.amazonaws.com/{audio_urls[key]}'

  response = ta.transcribe_urls(audio_urls)

  for _, transcript in response.items():
    assert 'results' in transcript
    assert 'captions' in transcript


