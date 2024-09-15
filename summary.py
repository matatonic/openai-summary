#!/usr/bin/env python
# Load the environment variables from the .env file
import dotenv
dotenv.load_dotenv()

import argparse
import locale
import os
import re
import requests
import sys
import tempfile

import openai
import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import pysbd

try:
    import textract
    has_textract = True
except ImportError:
    #print("textract not installed, using basic text extraction for files")
    has_textract = False

client = openai.OpenAI()
seg = None
SUMMARY_TASK = "Summary Instructions:\n- List the key points from the following text\n- Use a bulleted list in plain text format, no markdown, no other text\n- Be as concise as possible\n- Respond in the language of the text."
EXEC_SUMMARY_TASK = "Instructions:\nWrite an executive summary of the following text, include a title. Output only plain text format, no markdown. Respond in the language of the text."

# claude-3.5-sonnet made these mapping tables, it's unverified.
language_data = {
    'af': {'region': 'ZA', 'charset': 'ISO-8859-1,utf-8'},
    'am': {'region': 'ET'},
    'ar': {'region': 'SA'},
    'as': {'region': 'IN', 'charset': 'ISO-8859-1,utf-8'},
    'az': {'region': 'AZ'},
    'be': {'region': 'BY'},
    'bg': {'region': 'BG'},
    'bn': {'region': 'BD'},
    'bs': {'region': 'BA'},
    'ca': {'region': 'ES', 'charset': 'ISO-8859-1,utf-8'},
    'cs': {'region': 'CZ'},
    'cy': {'region': 'GB'},
    'da': {'region': 'DK'},
    'de': {'region': 'DE'},
    'el': {'region': 'GR'},
    'en': {'region': 'US'},
    'es': {'region': 'ES'},
    'et': {'region': 'EE'},
    'fa': {'region': 'IR'},
    'fi': {'region': 'FI'},
    'fr': {'region': 'FR', 'charset': 'ISO-8859-1,utf-8'},
    'gu': {'region': 'IN'},
    'he': {'region': 'IL'},
    'hi': {'region': 'IN'},
    'hr': {'region': 'HR'},
    'hu': {'region': 'HU'},    
    'hy': {'region': 'AM'},
    'id': {'region': 'ID'},
    'is': {'region': 'IS'},
    'it': {'region': 'IT'},
    'ja': {'region': 'JP', 'charset': 'Shift_JIS,utf-8'},
    'ka': {'region': 'GE'},
    'kk': {'region': 'KZ'},
    'km': {'region': 'KH'},
    'kn': {'region': 'IN'},
    'ko': {'region': 'KR'},
    'lo': {'region': 'LA'},
    'lt': {'region': 'LT'},
    'lv': {'region': 'LV'},
    'mk': {'region': 'MK'},
    'ml': {'region': 'IN'},
    'mn': {'region': 'MN'},
    'mr': {'region': 'IN'},
    'ms': {'region': 'MY'},
    'nb': {'region': 'NO'},
    'ne': {'region': 'NP'},
    'nl': {'region': 'NL'},
    'nn': {'region': 'NO'},
    'or': {'region': 'IN'},
    'pa': {'region': 'IN'},
    'pl': {'region': 'PL'},
    'ps': {'region': 'AF'},
    'pt': {'region': 'BR'},
    'ro': {'region': 'RO'},
    'ru': {'region': 'RU', 'charset': 'ISO-8859-5,utf-8'},
    'sd': {'region': 'IN'},
    'si': {'region': 'LK'},
    'sk': {'region': 'SK'},
    'sl': {'region': 'SI'},
    'sq': {'region': 'AL'},
    'sr': {'region': 'RS'},
    'sv': {'region': 'SE'},
    'sw': {'region': 'KE'},
    'ta': {'region': 'IN'},
    'te': {'region': 'IN'},
    'tg': {'region': 'TJ'},
    'th': {'region': 'TH'},
    'tk': {'region': 'TM'},
    'tr': {'region': 'TR'},
    'uk': {'region': 'UA'},
    'ur': {'region': 'PK'},
    'uz': {'region': 'UZ'},
    'vi': {'region': 'VN'},
    'zh': {'region': 'CN', 'charset': 'GB2312,utf-8'}
}

iso_1_to_iso_2 = {
    'aa': 'aar', 'ab': 'abk', 'af': 'afr', 'ak': 'aka', 'sq': 'alb', 'am': 'amh',
    'ar': 'ara', 'an': 'arg', 'hy': 'arm', 'as': 'asm', 'av': 'ava', 'ae': 'ave',
    'ay': 'aym', 'az': 'aze', 'ba': 'bak', 'bm': 'bam', 'eu': 'baq', 'be': 'bel',
    'bn': 'ben', 'bh': 'bih', 'bi': 'bis', 'bo': 'bod', 'bs': 'bos', 'br': 'bre',
    'bg': 'bul', 'my': 'bur', 'ca': 'cat', 'cs': 'ces', 'ch': 'cha', 'ce': 'che',
    'zh': 'chi', 'cu': 'chu', 'cv': 'chv', 'kw': 'cor', 'co': 'cos', 'cr': 'cre',
    'cy': 'cym', 'da': 'dan', 'de': 'deu', 'dv': 'div', 'nl': 'dut', 'dz': 'dzo',
    'el': 'ell', 'en': 'eng', 'eo': 'epo', 'et': 'est', 'ee': 'ewe', 'fo': 'fao',
    'fa': 'fas', 'fj': 'fij', 'fi': 'fin', 'fr': 'fra', 'fy': 'fry', 'ff': 'ful',
    'ka': 'geo', 'gd': 'gla', 'ga': 'gle', 'gl': 'glg', 'gv': 'glv', 'gn': 'grn',
    'gu': 'guj', 'ht': 'hat', 'ha': 'hau', 'he': 'heb', 'hz': 'her', 'hi': 'hin',
    'ho': 'hmo', 'hr': 'hrv', 'hu': 'hun', 'ig': 'ibo', 'is': 'ice', 'io': 'ido',
    'ii': 'iii', 'iu': 'iku', 'ie': 'ile', 'ia': 'ina', 'id': 'ind', 'ik': 'ipk',
    'it': 'ita', 'jv': 'jav', 'ja': 'jpn', 'kl': 'kal', 'kn': 'kan', 'ks': 'kas',
    'kr': 'kau', 'kk': 'kaz', 'km': 'khm', 'ki': 'kik', 'rw': 'kin', 'ky': 'kir',
    'kv': 'kom', 'kg': 'kon', 'ko': 'kor', 'kj': 'kua', 'ku': 'kur', 'lo': 'lao',
    'la': 'lat', 'lv': 'lav', 'li': 'lim', 'ln': 'lin', 'lt': 'lit', 'lb': 'ltz',
    'lu': 'lub', 'lg': 'lug', 'mk': 'mac', 'mh': 'mah', 'ml': 'mal', 'mi': 'mao',
    'mr': 'mar', 'ms': 'may', 'mg': 'mlg', 'mt': 'mlt', 'mn': 'mon', 'na': 'nau',
    'nv': 'nav', 'nr': 'nbl', 'nd': 'nde', 'ng': 'ndo', 'ne': 'nep', 'nn': 'nno',
    'nb': 'nob', 'no': 'nor', 'ny': 'nya', 'oc': 'oci', 'oj': 'oji', 'or': 'ori',
    'om': 'orm', 'os': 'oss', 'pa': 'pan', 'pi': 'pli', 'pl': 'pol', 'pt': 'por',
    'ps': 'pus', 'qu': 'que', 'rm': 'roh', 'ro': 'ron', 'rn': 'run', 'ru': 'rus',
    'sg': 'sag', 'sa': 'san', 'si': 'sin', 'sk': 'slk', 'sl': 'slv', 'se': 'sme',
    'sm': 'smo', 'sn': 'sna', 'sd': 'snd', 'so': 'som', 'st': 'sot', 'es': 'spa',
    'sc': 'srd', 'sr': 'srp', 'ss': 'ssw', 'su': 'sun', 'sw': 'swa', 'sv': 'swe',
    'ty': 'tah', 'ta': 'tam', 'tt': 'tat', 'te': 'tel', 'tg': 'tgk', 'tl': 'tgl',
    'th': 'tha', 'ti': 'tir', 'to': 'ton', 'tn': 'tsn', 'ts': 'tso', 'tk': 'tuk',
    'tr': 'tur', 'tw': 'twi', 'ug': 'uig', 'uk': 'ukr', 'ur': 'urd', 'uz': 'uzb',
    've': 'ven', 'vi': 'vie', 'vo': 'vol', 'wa': 'wln', 'wo': 'wol', 'xh': 'xho',
    'yi': 'yid', 'yo': 'yor', 'za': 'zha', 'zu': 'zul'
}

def request_headers(language_code = 'en'):
    generic_headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'none',
        'Connection': 'keep-alive'
    }

    lang_data = language_data.get(language_code, language_data.get('en'))
    region = lang_data.get('region', 'US') # sorry, but the internet be like that
    charset = lang_data.get('charset', 'UTF-8')

    generic_headers['Accept-Language'] = f"{language_code}-{region},{language_code};q=0.8"
    generic_headers['Accept-Charset'] = f"{charset};q=0.7,*;q=0.3"

    return generic_headers

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
def get_video_transcript(video_id: str, language: str) -> str | None:
    """
    Fetch the transcript of the provided YouTube video
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        return ' '.join([line["text"] for line in transcript])

    except NoTranscriptFound:
        # find one that can work and translate it
        try:
            for tr in YouTubeTranscriptApi.list_transcripts(video_id):
                if tr.is_translatable:
                    try:
                        transcript = tr.translate(language).fetch()
                        return ' '.join([line["text"] for line in transcript])
                    except:
                        pass
        except:
            pass

    except TranscriptsDisabled:
        pass
        # The video doesn't have a transcript
    
    return None

def get_url_text(url: str, language: str) -> str:
    # handle Youtube Videos
    video_id = extract_youtube_video_id(url)
    if video_id:
        # Fetch the video transcript
        text = get_video_transcript(video_id, language)

        # If no transcript is found, return an error message
        if not text:
            return f"No '{language}' transcript found for this video: {url}"
    else:
        # Fetch the head, and determine the filetype
        headers = request_headers(language)
        response = requests.get(url, headers=headers)

        if response.status_code == 200 and 'text/' in response.headers['content-type']:
            text = trafilatura.extract(response.content, output_format='txt', target_language=language)
        else:
            # without textract this will suck.
            
            # get filename form headers
            try:
                filename = response.headers['Content-Disposition'].split('filename=')[1].strip('"')
            except:
                # or from url
                filename = os.path.basename(url).split('?')[0]

            try:
                fd, tmp_filename = tempfile.mkstemp(suffix=filename)
                os.write(fd, response.content)
                text = get_file_text(tmp_filename, language)
            finally:
                os.unlink(tmp_filename)
                pass

    return text

def get_file_text(filename: str, language: str) -> str:
    if '.htm' in filename.lower():
        with open(filename, 'r') as f:
            text = trafilatura.extract(f.read(), output_format='txt', target_language=language)
    elif has_textract:
        text = textract.process(filename, language=iso_1_to_iso_2.get(language)).decode()
    else:
        with open(filename, 'r') as f:
            text = f.read()

    return text

def openai_edit(instruction: str, text: str, stream: bool, max_new_tokens: int = 2048, model: str = 'gpt-3.5-turbo') -> str:
    # edit is deprecated, fake it.
    response = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': f"{instruction}\n\n```text\n{text}\n```\n" }],
        temperature=0.2,
        max_tokens=max_new_tokens,
        stream=stream,
    )
    
    if stream:
        texts = []
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end='', flush=True)
                texts.extend([content])
    
        print('', flush=True)
        return ''.join(texts)
    else:
        return response.choices[0].message.content

# organize text into paragraphs or logical chunks of a max size
# trying for fairly uniform sized chunks
def chunk_large_text(text_list: list, max_size: int) -> list[str]:
    txts = [] # chunks of near <= max_size
    para = '' # buffer

    for s in text_list:
        s_len = len(s)
        if para and len(para) + s_len > max_size:
            txts.extend([para])
            para = ''
    
        if s_len <= max_size:
            para += s + '\n'
        else:
            if para:
                txts.extend([para])
                para = ''

            # big chunk, no natural breaks... break it up on words at least
            # for youtube transcripts and web pages this is rarely hit
            #print("Breaking big texts...", file=sys.stderr)
            cut = s_len // max_size
            chunk = s_len // (cut + 1)
            i = 0
            while i < s_len:
                if s_len - i <= chunk:
                    txts.extend(['… ' + s[i:] + ' …'])
                    break
                clip_i = s.find(' ', i + chunk)
                # if clip_i - i >> max_size, clamp clip_i
                txts.extend(['… ' + s[i:clip_i] + ' …'])
                i = clip_i + 1

    # left overs
    if para:
        txts.extend([para])

    return txts

def summarize_large_text(text: str, max_size: int, stream = False, progress = False, max_new_tokens = 2048, model: str = 'gpt-3.5-turbo') -> str:
    try:
        text_list = seg.segment(text)
    except:
        text_list = [ t.strip() for t in text.split('\n') ]

    txts = chunk_large_text(text_list, max_size)

    summaries = []
    txts_len = len(txts)

    for n, t in enumerate(txts):
        if progress:
            print('\rWorking... {:.0f}%'.format(100.0 * n / txts_len), end = '', file=sys.stderr, flush=True)

        summary = openai_edit(SUMMARY_TASK, t, stream=stream, max_new_tokens=max_new_tokens, model=model)
        summaries.extend([summary])

    if progress:
        print('\rFinished! 100%', file=sys.stderr, flush=True)

    return '\n'.join(summaries)

def parse_args(arguments):

    lang, _ = locale.getdefaultlocale()
    lang_default = os.environ.get('LANG', lang if lang else 'en').split('_')[0]

    parser = argparse.ArgumentParser(
                prog='summary.py',
                description='Summarize URLs or files, including YouTube videos via transcriptions',
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('url', help="URL or file to summarize (including YouTube videos via transcriptions)")
    parser.add_argument('-l', '--language', default=lang_default, help="Set the language used for subtitles, web requests and text parsing (os default)") #, choices=list(pysbd.languages.LANGUAGE_CODES.keys()))
    parser.add_argument('-m', '--model', default='gpt-3.5-turbo', help="Set the large language model to use for summary")
    parser.add_argument('-p', '--progress', action='store_true', default=False, help="Show percentage progress")
    parser.add_argument('-S', '--no_stream', action='store_true', default=False, help="Don't output text as it's created")
    parser.add_argument('-x', '--executive_summary', action='store_true', default=False, help="Include an Executive Summary")
    parser.add_argument('-X', '--executive_summary_only', action='store_true', default=False, help="Only output the Executive Summary")
    parser.add_argument('-M', '--max_new_tokens', default=2048, help="Max new tokens to generate at once")
    parser.add_argument('-b', '--max_size', action='store', default=5000, type=int, help="The maximum size (in characters) to summarize at once")

    return parser.parse_args(arguments)

def main():
    global seg

    args = parse_args(sys.argv[1:])
    #args = parse_args(['https://www.youtube.com/watch?v=3yHWM8TG-nU', '-b', '10000000000', '-X', ])

    if args.executive_summary_only:
        args.executive_summary = True

    try:
        seg = pysbd.Segmenter(language=args.language, clean=True) # text is dirty, clean it up.
    except:
        pass # try to ignore this and continue on.

    full_text = "No text found"
    summary = None

    if args.url.lower().startswith('http'):
        full_text = get_url_text(args.url, language=args.language)
    else:
        full_text = get_file_text(args.url, language=args.language)

    # Summarize as bullet points
    if not args.executive_summary_only:
        summary = summarize_large_text(full_text, max_size=args.max_size, stream=not args.no_stream, progress=args.progress, max_new_tokens=args.max_new_tokens, model=args.model)
        if args.no_stream:
            print(summary, flush=True) # print the full summary points

    # Executive Summary
    if args.executive_summary:
        if len(full_text) > args.max_size:
            # if the full content is too large, summarize the summary
            if summary is not None:
                full_text = summary

            # while the summary is too large, keep summarizing it
            while len(full_text) > args.max_size:
                summary = summarize_large_text(full_text, max_size=args.max_size, stream=False, progress=args.progress, max_new_tokens=args.max_new_tokens, model=args.model)
                if len(summary) >= len(full_text):
                    print("\nWARNING: Unable to reduce final summary size, final results may be truncated or fail, aborting any further reduction.\n", file=sys.stderr)
                    break
                full_text = summary

        print('', flush=True)
        exec_summary = openai_edit(EXEC_SUMMARY_TASK, full_text, stream=not args.no_stream, max_new_tokens=args.max_new_tokens, model=args.model)
        if args.no_stream:
            print(exec_summary, flush=True) # print the executive summary

if __name__ == '__main__':
    main()
