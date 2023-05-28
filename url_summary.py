#!/usr/bin/env python3

# This works very well with TheBloke's vicuna-13B-1.1-GPTQ-4bit-128g and koala-13B-GPTQ-4bit-128g

# Load the environment variables from the .env file
from dotenv import load_dotenv
load_dotenv()

import sys
import re
import argparse
from requests import get
import openai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from bs4 import BeautifulSoup
import pysbd

seg = pysbd.Segmenter(language='en', clean=True) # text is dirty, clean it up.


parser = argparse.ArgumentParser(
            prog='url_summary.py',
            description='Summarize URLs, including YouTube transcriptions',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('url', help="URL of the site to summarize (including YouTube transcriptions)")
parser.add_argument('-p', '--progress', action='store_true', default=False, help="Show percentage progress")
parser.add_argument('-S', '--no_stream', action='store_true', default=False, help="Don't output text as it's created")
parser.add_argument('-x', '--executive_summary', action='store_true', default=False, help="Include an Executive Summary")
parser.add_argument('-X', '--executive_summary_only', action='store_true', default=False, help="Only output the Executive Summary")
parser.add_argument('-t', '--tldr', action='store_true', default=False, help="Include a TL;DR")
parser.add_argument('-T', '--tldr_only', action='store_true', default=False, help="Only output a TL;DR")
parser.add_argument('-b', '--max_size', action='store', default=5000, type=int, help="The maximum size (in characters) to summarize at once.")

args = parser.parse_args()


# not useful for most use cases.
# Experiment failed successfully.
def time_chunk_transcript(video_id: str) -> list | None:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
    except TranscriptsDisabled:
        # The video doesn't have a transcript
        return None
        
    t_list = [ (x['text'], x['start'], x['duration']) for x in transcript ]

    ret = []

    t, s, d = t_list.pop(0)
    e = s + d

    for text, start, duration in t_list:
        if start <= e: # overlapping
            #print("+", end='')
            t += ' ' + text
            e = start + duration
        else: # a pause
            #print(f"\npause of: {start - e} sec")
            ret.extend([t])
            t = ''
            e = start + duration

    if t:
        ret.extend([t])

    return ret


# https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
def get_url_html(url: str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'}

    return get(url, headers=headers).content


def get_url_text(url: str) -> list:
    html = get_url_html(url)
    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    return seg.segment(text)


def extract_youtube_video_id(url: str) -> str | None:
    """
    Extract the video ID from the URL
    https://www.youtube.com/watch?v=XXX -> XXX
    https://youtu.be/XXX -> XXX
    """
    found = re.search(r"(?:youtu\.be\/|watch\?v=)([\w-]+)", url)
    if found:
        return found.group(1)
    return None


def get_video_transcript(video_id: str) -> list | None:
    """
    Fetch the transcript of the provided YouTube video
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
    except TranscriptsDisabled:
        # The video doesn't have a transcript
        return None
    
    return [line["text"] for line in transcript]


def openai_edit(instruction: str, text: str) -> str:
    response = openai.Edit.create(
        model="gpt-3.5-turbo",
        instruction=instruction,
        input=text,
    )
    
    return response.choices[0].text

def openai_completion(prompt: str) -> str:
    response = openai.Completion.create(
        model="gpt-3.5-turbo",
        prompt=prompt,
    )
    
    return response.choices[0].text

# arbitrary cut, should fit in 2k context with instructions
def summarize_large_text(text_list: list, max_size = args.max_size, stream = False, progress = False) -> str:
    txts = [] # chunks of near <= max_size
    para = '' # buffer

    for s in text_list:
        s_len = len(s)
        if para and len(para) + s_len > max_size:
            txts.append(para)
            para = ''
    
        if s_len <= max_size:
            para += s + '\n'
        else:
            if para:
                txts.append(para)
                para = ''

            # big chunk, no natural breaks... break it up on words at least
            # for youtube transcripts and web pages this is rarely hit
            #print("Breaking big texts...", file=sys.stderr)
            cut = s_len // max_size
            chunk = s_len // (cut + 1)
            i = 0
            while i < s_len:
                if s_len - i <= chunk:
                    txts.append('… ' + s[i:] + ' …')
                    break
                clip_i = s.find(' ', i + chunk)
                # if clip_i - i >> max_size, clamp clip_i
                txts.append('… ' + s[i:clip_i] + ' …')
                i = clip_i + 1

    # left overs
    if para:
        txts.append(para)

    summaries = []
    txts_len = len(txts)

    for n, t in enumerate(txts):
        if progress:
            print('\rWorking... {:.0f}%'.format(100.0 * n / txts_len), end = '', file=sys.stderr, flush=True)

        sum = openai_edit("List the key points from the following text as a bulleted list. Be as concise as possible.", t)
        
        if stream:
            print(sum, flush=True)

        summaries.append(sum)

    if progress:
        print('\rFinished! 100%', file=sys.stderr, flush=True)

    return '\n'.join(summaries)

def summarize_url(url: str, max_size = args.max_size, stream = False, progress = False) -> str:
    """
    Summarize the provided url
    """
    text_list = [ f"No text found for this url: {url}" ]

    # handle Youtube Videos
    video_id = extract_youtube_video_id(url)
    if video_id is not None:
        # Fetch the video transcript
        text_list = get_video_transcript(video_id)

        # If no transcript is found, return an error message
        if not text_list:
            return f"No English transcript found for this video: {url}"
    else:
        # Fetch the url text
        text_list = get_url_text(url)

    # Generate the summary
    summary = summarize_large_text(text_list, max_size=max_size, stream=stream, progress=progress)

    # Return the summary
    return summary


if __name__ == '__main__':
    if args.executive_summary_only:
        args.no_stream = True

    if args.tldr_only:
        args.executive_summary_only = False # force one or the other
        args.no_stream = True
        args.tldr = True

    summary = summarize_url(args.url, progress=args.progress, stream= not args.no_stream)

    if args.no_stream and not (args.executive_summary_only or args.tldr_only):
        print(summary)
    
    if args.executive_summary or args.executive_summary_only or args.tldr or args.tldr_only:
        if not (args.executive_summary_only or args.tldr_only):
            print('\nExecutive Summary')

        # if summary too large, maybe break into a list and summarize again.
        while len(summary) > args.max_size:
            summary = summarize_large_text(summary.split('\n'), max_size=args.max_size, stream=False, progress=args.progress)

        exec_summary = openai_edit("An executive summary of the following text.", summary)
    
        if not args.tldr_only:
            print(exec_summary)

        if args.tldr:
            tldr = openai_completion(exec_summary + "\n\nTL;DR\n")
            if not args.tldr_only:
                print('\nTL;DR')
            print(tldr)
