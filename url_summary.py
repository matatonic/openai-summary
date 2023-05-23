#!/usr/bin/env python3

# Load the environment variables from the .env file
from dotenv import load_dotenv
load_dotenv()

import sys
import re
from requests import get
import openai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from bs4 import BeautifulSoup


def get_url_html(url: str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'}

    return get(url, headers=headers).content

# https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
def get_url_text(url: str) -> str:
    html = get_url_html(url)
    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text


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


def get_video_transcript(video_id: str) -> str | None:
    """
    Fetch the transcript of the provided YouTube video
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
    except TranscriptsDisabled:
        # The video doesn't have a transcript
        return None

    text = " ".join([line["text"] for line in transcript])
    return text


def generate_summary(text: str) -> str:
    """
    Generate a summary of the provided text using OpenAI API
    """

    # Use GPT to generate a summary
    instruction = "List the key points from the following text as a bulleted list. Be as concise as possible."
    response = openai.Edit.create(
        model="gpt-3.5-turbo",
        instruction=instruction,
        input=text,
    )

    # Return the generated summary
    return response.choices[0].text

# 6000 chars arbitrary cut, should fit in 2k context with instructions
def summarize_large_text(text: str, max_size = 6000) -> str:
    if len(text) <= max_size:
        summary = generate_summary(text)
        print(summary, flush=True)
        return summary

    txts = []
    para = ''

    for s in text.split('. '):
        s_len = len(s)
        if para and len(para) + s_len > max_size:
            txts.append(para)
            para = ''
    
        if s_len <= max_size:
            para += s + '.\n'
        else:
            if para:
                txts.append(para)
                para = ''

            # big chunk, no natural breaks... cut it up
            cut = s_len // max_size
            chunk = s_len // (cut + 1)
            i = 0
            while i < s_len:
                if s_len - i <= chunk:
                    txts.append('… ' + s[i:] + ' …')
                    break
                clip_i = s.find(' ', i + chunk)
                # if clip_i - i >> 4096, clamp clip_i
                txts.append('… ' + s[i:clip_i] + ' …')
                i = clip_i + 1

    # left overs
    if para: txts.append(para)

    summaries = []
    txts_len = len(txts)

    for n, t in enumerate(txts):
        sum = generate_summary(t)
        # Print as we go or %
        #print('\r{:.0f}%'.format(100.0 * n / txts_len), end = '', file=sys.stderr, flush=True)
        print(sum)
        if sum and sum[-1] == '.': sum = sum[:-1]
        summaries.append(sum)

    #print('\r100%', file=sys.stderr, flush=True)
    # recursive until it's less than 4K
    #return summarize_large_text('. '.join(summaries))
    return '\n'.join(summaries)

def summarize_url(url: str) -> str:
    """
    Summarize the provided url
    """
    text = f"No text found for this url: {url}"

    # handle Youtube Videos
    video_id = extract_youtube_video_id(url)
    if video_id is not None:
        # Fetch the video transcript
        text = get_video_transcript(video_id)

        # If no transcript is found, return an error message
        if not text:
            return f"No English transcript found for this video: {url}"
    else:
        # Fetch the url text
        text = get_url_text(url)

    # Generate the summary
    summary = summarize_large_text(text)

    # Return the summary
    return summary


if __name__ == '__main__':
    url = sys.argv[1]
    summary = summarize_url(url)
    #print(summary)
