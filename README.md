# Summarize URL's or files (including YouTube video's via transcripts) using an OpenAI compatible API

Use it for free with any OpenAI API chat completion API server.

## Details

- Multilingual summaries of urls and local files (including PDFs, Word docs, etc.)
- Uses [trafilatura](https://github.com/adbar/trafilatura) for state of the art text extraction from html and efficient downloads
- Uses [YouTube Transcripts API](https://github.com/jdepoix/youtube-transcript-api) including translated transcriptions
- Uses [pySBD (Python Sentence Boundary Disambiguation)](https://github.com/nipunsadvilkar/pySBD) for intelligent sentence breaks and text cleaning - optional
- Uses [textract](https://github.com/deanmalmgren/textract) for text extraction from MANY files types - optional, some file types may require additional dependencies or packages to be installed.
- You can pipe the output to your favorite Text-to-Speech application, like [openedai-speech](https://github.com/matatonic/openedai-speech)

## Latest Updates

Sep 15, 2024
- fix extra headers arg

Aug 28, 2024:
- Code cleanup & updates, updated requirements.txt
- multilingual support
- add support for YouTube Transcription translations
- URL support for images, pdfs, csv's, any file type supported by textract
- real text streaming of summaries
- drop support for /completion API and TL;DR.

### Installation

```
pip install -r requirements.txt
```

### Usage

```
usage: summary.py [-h] [-l LANGUAGE] [-m MODEL] [-p] [-S] [-x] [-X] [-M MAX_NEW_TOKENS] [-b MAX_SIZE] url

Summarize URLs or files, including YouTube videos via transcriptions

positional arguments:
  url                   URL or file to summarize (including YouTube videos via transcriptions)

options:
  -h, --help            show this help message and exit
  -l LANGUAGE, --language LANGUAGE
                        Set the language used for subtitles, web requests and text parsing (os default) (default: en)
  -m MODEL, --model MODEL
                        Set the large language model to use for summary (default: gpt-3.5-turbo)
  -p, --progress        Show percentage progress (default: False)
  -S, --no_stream       Don't output text as it's created (default: False)
  -x, --executive_summary
                        Include an Executive Summary (default: False)
  -X, --executive_summary_only
                        Only output the Executive Summary (default: False)
  -M MAX_NEW_TOKENS, --max_new_tokens MAX_NEW_TOKENS
                        Max new tokens to generate at once (default: 2048)
  -b MAX_SIZE, --max_size MAX_SIZE
                        The maximum size (in characters) to summarize at once (default: 5000)
```

## Example

Example: Quantum Computing Explained (10 min) - https://www.youtube.com/watch?v=jHoEjvuPoB8
(output quality is highly dependent on model quality)

```
$ python summary.py -x https://www.youtube.com/watch?v=jHoEjvuPoB8
```
 - Quantum computers are not the next generation of supercomputers but a distinct technology.
- Understanding quantum computing requires knowledge of quantum mechanics.
- Richard Feynman proposed the idea of quantum computers in the 1980s to simulate quantum systems.
- Quantum physics is based on amplitudes, which are complex numbers and differ from classical probabilities.
- Qubits are the basic units of quantum computing and can exist in superposition, a combination of 0 and 1.
- Superposition allows quantum computers to process vast amounts of data.
- Entanglement relates qubits in superposition, affecting their final outcomes.
 - Quantum entanglement refers to unique correlations among parts of a quantum system.
- Describing highly entangled states with classical bits is extremely resource-intensive.
- Measuring a quantum system collapses it into a classical state.
- Interference is used to extract meaningful answers from quantum systems.
- Designing quantum algorithms is difficult and has seen few major breakthroughs.
- Quantum computers are most likely useful for exploring physics and may have unforeseen applications.



Title: Fundamentals of Quantum Computing

Quantum computers represent a unique technology, distinct from traditional supercomputers, and require an understanding of quantum mechanics. Proposed by Richard Feynman in the 1980s, quantum computing leverages principles such as superposition and entanglement to process vast amounts of data. Qubits, the basic units, can exist in a combination of 0 and 1, and their entanglement creates unique correlations that are resource-intensive to describe classically. Measuring a quantum system collapses it into a classical state, and interference is used to extract meaningful answers. Designing quantum algorithms is challenging, with few major breakthroughs so far. Quantum computers are expected to be particularly useful for exploring physics and may have unforeseen applications.

```
# use a large context and get the executive summary in one step, use the french translation
$ python summary.py -X https://www.youtube.com/watch?v=jHoEjvuPoB8 -b 100000 -l fr
```

 Les ordinateurs quantiques : Promesse et Défis

Les ordinateurs quantiques, souvent présentés comme la technologie de l'avenir, ne sont pas simplement des superordinateurs améliorés, mais des outils fondamentalement différents. Pour comprendre leur potentiel, il est crucial de saisir la physique quantique sous-jacente, notamment le concept d'amplitudes. Dans les années 1980, Richard Feynman a imaginé l'idée d'un ordinateur quantique pour simuler des systèmes quantiques, reconnaissant que les ordinateurs classiques ne pouvaient pas suivre leur complexité croissante. Les qubits, unités de calcul de base de l'informatique quantique, peuvent exister en superposition, permettant de stocker et de manipuler de grandes quantités de données. L'intrication quantique et l'interférence sont des phénomènes clés qui distinguent les ordinateurs quantiques des classiques. Bien que des avancées aient été réalisées dans les algorithmes quantiques, leur conception reste complexe. Les applications pratiques à court terme sont incertaines, mais les physiciens voient dans l'informatique quantique un moyen passionnant d'explorer la physique. Les applications les plus importantes des ordinateurs quantiques pourraient encore être inconnues.

```
# Summarize the text from an image file (requires textract)
python summary.py https://w0.peakpx.com/wallpaper/167/700/HD-wallpaper-zen-quotes-black-sayings-buddha.jpg 
```

- Keep your mouth shut and your eyes open
- Be strong enough to focus on what truly matters
