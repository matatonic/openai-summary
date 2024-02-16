#!/usr/bin/env python
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
try:
    import textract
except:
    pass

client = openai.OpenAI()

import pysbd

seg = pysbd.Segmenter(language='en', clean=True) # text is dirty, clean it up.

# https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
def get_url_html(url: str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'}

    return get(url, headers=headers).content

def get_html_text(html: str) -> list:
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

# TODO: Use Time gaps to make natural breaks
def get_video_transcript(video_id: str) -> list | None:
    """
    Fetch the transcript of the provided YouTube video
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
    except TranscriptsDisabled:
        # The video doesn't have a transcript
        return None
    
    return seg.segment(' '.join([line["text"] for line in transcript]))

def get_url_text(url: str) -> list:
    text_list = [ f"No text found for this url: {url}" ]

    # handle Youtube Videos
    video_id = extract_youtube_video_id(url)
    if video_id:
        # Fetch the video transcript
        text_list = get_video_transcript(video_id)

        # If no transcript is found, return an error message
        if not text_list:
            return f"No English transcript found for this video: {url}"
    else:
        # Fetch the url text
        html = get_url_html(url)
        text_list = get_html_text(html)

    return text_list


def get_file_text(filename: str) -> list:
    text = textract.process(filename).decode()
    return seg.segment(text)


#def get_file_text(filename: str) -> list:
#    text_list = [ f"No text found for this file: {filename}" ]
#
#    if '.htm' in filename.lower():
#        with open(filename, 'r') as f:
#            text_list = get_html_text(f.read())
#    elif '.pdf' in filename.lower():
#        with open(filename, 'r') as f:
#            text_list = get_pdf_text(f.read())
#    else:
#        with open(filename, 'r') as f:
#            text_list = seg.segment(f.read())
#
#    return text_list


def openai_edit(instruction: str, text: str, max_tokens: int = 2048) -> str:
    # edit is deprecated, fake it.
    # Fake system message also
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{'role': 'user', 'content': instruction}, {'role': 'assistant', 'content': 'OK'}, {'role': 'user', 'content': text} ],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    
    return response.choices[0].message.content

def openai_completion(prompt: str, max_tokens: int, stop = ['</s>']) -> str:
    response = client.completions.create(
        model="gpt-3.5-turbo",
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.2,
        stop=stop,
    )
    #print(response.choices[0])
    return response.choices[0].text

# organize text into paragraphs or logical chunks of a max size
# trying for fairly uniform sized chunks
def chunk_large_text(text_list: list, max_size: int) -> list[str]:
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

    return txts

def summarize_large_text(text_list: list, max_size: int, stream = False, progress = False) -> str:

    txts = chunk_large_text(text_list, max_size)

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

def parse_args(arguments):
    parser = argparse.ArgumentParser(
                prog='summary.py',
                description='Summarize URLs or files, including YouTube videos via transcriptions',
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('url', help="URL or file to summarize (including YouTube videos via transcriptions)")
    parser.add_argument('-p', '--progress', action='store_true', default=False, help="Show percentage progress")
    parser.add_argument('-S', '--no_stream', action='store_true', default=False, help="Don't output text as it's created")
    parser.add_argument('-x', '--executive_summary', action='store_true', default=False, help="Include an Executive Summary")
    parser.add_argument('-X', '--executive_summary_only', action='store_true', default=False, help="Only output the Executive Summary")
    parser.add_argument('-t', '--tldr', action='store_true', default=False, help="Include a TL;DR")
    parser.add_argument('-T', '--tldr_only', action='store_true', default=False, help="Only output a TL;DR")
    parser.add_argument('-b', '--max_size', action='store', default=5000, type=int, help="The maximum size (in characters) to summarize at once.")

    return parser.parse_args(arguments)

def main():
    args = parse_args(sys.argv[1:])
    #args = parse_args(['https://www.youtube.com/watch?v=3yHWM8TG-nU', '-b', '10000000000', '-T', ])

    if args.executive_summary_only:
        args.tldr_only = False # force one or the other
        args.tldr = False
        args.executive_summary = True

    if args.tldr_only:
        args.executive_summary_only = False # force one or the other
        args.executive_summary = False
        args.tldr = True

    text_list = [ "No text found" ]

    if args.url.lower().startswith('http'):
        text_list = get_url_text(args.url)
    else:
        text_list = get_file_text(args.url)

    # Summarize as bullet points
    if not (args.executive_summary_only or args.tldr_only):
        summary = summarize_large_text(text_list, max_size=args.max_size, stream= not args.no_stream, progress=args.progress)
        if args.no_stream:
            print(summary)
    else:
        summary = '\n'.join(text_list)

    # Executive/TL;DR
    if args.executive_summary or args.tldr:
        # if summary too large, maybe break into a list and summarize again.
        if len(summary) > args.max_size:
            
            # Don't stream intermediate results
            stream = args.no_stream
            args.no_stream = True

            while len(summary) > args.max_size:
                summary = summarize_large_text(summary.split('\n'), max_size=args.max_size, stream=False, progress=args.progress)

            args.no_stream = stream

        if args.executive_summary:
            if not args.executive_summary_only:
                print('\nExecutive Summary')
            exec_summary = openai_edit("Write an executive summary of the following text.", summary, max_tokens=args.max_size)
            print(exec_summary)

        if args.tldr:
            tldr = openai_completion(summary + "\n\nTL;DR\n", stop=["\n\n", "</s>"], max_tokens=args.max_size)
            if not args.tldr_only:
                print('\nTL;DR')
            print(tldr)

if __name__ == '__main__':
    main()
