#!/usr/bin/env python3
# transcribe-video.py
import os
from dotenv import load_dotenv
import asyncio
import httpx
from datetime import datetime
from pathlib import Path

from os import PathLike

import json

from deepgram_captions import DeepgramConverter, webvtt
from deepgram import DeepgramClient, PrerecordedOptions, FileSource, PrerecordedResponse

TRANSCRIPT_FILE = "transcripts"

load_dotenv()
API_KEY = os.getenv("DG_API_KEY")

# Configure Deepgram options for audio analysis
OPTIONS = PrerecordedOptions(
    diarize=True,
    filler_words=False,
    language="en",
    model="nova-2",
    smart_format=True,
    # topics=True,
    utterances=True,
)


def transcribe_urls(
    audio_urls: dict[str, str], target_dir: PathLike | None = None
) -> dict:
    results = dict()
    asyncio.run(_transcribe_urls(audio_urls, results))

    if target_dir is not None:
        write_transcripts(target_dir, results)

    return results


async def _transcribe_urls(
    audio_urls: dict[str, str],
    result_dict: dict,
):
    """
    transcribe given URLs and place resulting dict response into
    result_dict[audio_url_key]
    """

    tasks: list[asyncio.TaskGroup] = []
    start = datetime.now()
    print(f"Beginning transcription at {start}")

    for name, audio_url in audio_urls.items():
        t = asyncio.create_task(_transcribe_url(audio_url))
        tasks.append((name, t))

    # async with asyncio.TaskGroup() as tg:
    #   for name, audio_url in audio_urls.items():
    #     t = tg.create_task(
    #       _transcribe_url(audio_url)
    #     )
    #     tasks.append((name, t))

    for _, task in tasks:
        await task

    end = datetime.now()

    print(f"end time: {end}\ntotal transcribe time: {end - start}")
    # TODO delete
    print("writing transcripts into result dict")

    for name, task in tasks:
        result = task.result()
        # print(result)
        if result is not None:
            result_dict[name] = result.to_dict()
            transcription = DeepgramConverter(result)
            result_dict[name]["captions"] = webvtt(transcription)
        else:
            result_dict[name] = {"captions": ""}


async def _transcribe_url(url: str) -> PrerecordedResponse:
    """
    Given a URL, transcribe audio from source file into a persistent dict.

    :param url: the URL of the audio (or video) file to read.
    :returns response: the transcript contents.
    """
    print(f"transcribing {url}")

    client = DeepgramClient(API_KEY)
    timeout = httpx.Timeout(10.0, read=500.0)

    data = await client.listen.asyncprerecorded.v("1").transcribe_url(
        {"url": url}, OPTIONS, timeout=timeout
    )

    return data


async def _transcribe_local(audio_file: PathLike) -> PrerecordedResponse:
    """
    Transcribe audio from source file.

    :param client: the Deepgram client.
    :param audio_file: the name of the audio file to read.
    :returns data: the transcript data written as a dict.
    """
    with open(audio_file, "rb") as file:
        buffer_data = file.read()

    print(f"done reading {audio_file}. sending to Deepgram client")

    payload: FileSource = {"buffer": buffer_data}

    client = DeepgramClient(API_KEY)
    timeout = httpx.Timeout(10.0, read=500.0)

    data = client.listen.asyncprerecorded.v("1").transcribe_file(
        payload, OPTIONS, timeout=timeout
    )
    return data


def write_transcripts(target_dir, file_contents):
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)

    for name, data in file_contents:
        filepath = Path(target_dir) / f"{name}"
        with open(filepath, "w") as file:
            file.write(json.dumps(data, indent=2))
