# Summarize URL's or files (including YouTube video's via transcripts) using an OpenAI compatible API

Use it for free with any OpenAI API chat completion API server.

## Details

- Uses [textract](https://github.com/deanmalmgren/textract) for PDF text extraction (and other files) - optional
- Uses [trafilatura](https://github.com/adbar/trafilatura) for state of the art text extraction from html and efficient downloads - optional
- Uses [pySBD (Python Sentence Boundary Disambiguation)](https://github.com/nipunsadvilkar/pySBD) for intelligent sentence breaks and text cleaning
- Supports the YouTube Transcripts API
- Pipe the output to your favorite Text-to-Speech application, like [openedai-speech](https://github.com/matatonic/openedai-speech)

## Latest Updates

- Jun 19, 2024: Use [trafilatura](https://github.com/adbar/trafilatura) for downloading and text extraction from html (optional)

### Installation

```
pip install -r requirements.txt
```

### Usage

```
usage: summary.py [-h] [-p] [-S] [-x] [-X] [-t] [-T] [-b MAX_SIZE] url

Summarize URLs or files, including YouTube videos via transcriptions

positional arguments:
  url                   URL or file to summarize (including YouTube videos via transcriptions)

options:
  -h, --help            show this help message and exit
  -p, --progress        Show percentage progress (default: False)
  -S, --no_stream       Don't output text as it's created (default: False)
  -x, --executive_summary
                        Include an Executive Summary (default: False)
  -X, --executive_summary_only
                        Only output the Executive Summary (default: False)
  -t, --tldr            Include a TL;DR (this uses a completion model, not chat) (default: False)
  -T, --tldr_only       Only output a TL;DR (this uses a completion model, not chat) (default: False)
  -b MAX_SIZE, --max_size MAX_SIZE
                        The maximum size (in characters) to summarize at once. (default: 5000)

```

## Example

Example: Quantum Computing Explained (10 min) - https://www.youtube.com/watch?v=jHoEjvuPoB8
(output quality is highly dependent on model quality)

```
$ python summary.py -x -t https://www.youtube.com/watch?v=jHoEjvuPoB8
```
*   Quantum computers are based on the principles of quantum mechanics, which allows them to perform operations on large amounts of data simultaneously.
*   The key difference between classical and quantum computers lies in their ability to handle complex data structures and perform parallel computations.
*   Quantum computers use quantum states (qubits) instead of classical bits to represent and process data. Qubits can exist in multiple states simultaneously, allowing for faster processing speeds compared to classical computers.
*   Quantum computers rely on the properties of quantum mechanics such as superposition and entanglement to perform computations.
*   Quantum entanglement is the correlation between particles in a quantum system that is different from classical correlations.
*   To describe highly entangled states using ordinary bits, it requires a large number of classical bits, making it expensive.
*   Interference is used to extract an answer from a quantum system without collapsing its state.
*   The most important application of quantum computers may not be known until a quantum computer is available to experiment with.

Executive Summary

Quantum computers have the potential to revolutionize computing by leveraging the principles of quantum mechanics to perform calculations on large amounts of data simultaneously. They differ from classical computers in their ability to handle complex data structures and perform parallel computations. Quantum computers use qubits instead of classical bits to store and process information, allowing for much faster processing speeds. However, they require specialized hardware and software, and the complexity of quantum systems makes them difficult to program. One way to overcome this challenge is through interference, whereby the quantum system's state is manipulated without collapsing it. While the applications of quantum computers are still unknown, they hold great promise for solving problems that classical computers cannot tackle efficiently.

TL;DR

Quantum Computers: A type of computer that uses quantum-mechanical phenomena such as superposition and entanglement to perform operations on data. They can solve certain types of problems much faster than classical computers but are currently limited by their complexity and lack of standardization.

```
# use a large context and get the executive summary in one step
$ python summary.py -X -b 100000 https://www.youtube.com/watch?v=jHoEjvuPoB8
```
Quantum computers are a nascent technology with the potential to revolutionize various fields. They operate based on quantum mechanics, specifically the concept of amplitudes, which are complex numbers that govern the probability of subatomic particles' behavior. Qubits, the basic unit of quantum computing, can exist in a superposition of 0 and 1, allowing quantum computers to store and manipulate vast amounts of data. Entanglement between qubits further enhances their computational power, but measuring them collapses their state, making it challenging to extract useful information. Scientists have developed quantum algorithms that use interference to boost the probability of obtaining correct answers. While there have been breakthroughs in quantum algorithms with potential applications in cybersecurity and search optimization, the most significant applications of quantum computers are yet to be discovered.

