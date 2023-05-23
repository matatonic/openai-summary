# URL Summaries

Summarize URL's (including youtube video transcripts) using an OpenAI compatible API.

Use it for free with: https://github.com/oobabooga/text-generation-webui/tree/main/extensions/openai (shameless self plug!)

Heavily "inspired" by various blog posts and stackexchange comments.
It's a quick and dirty hack, but it kinda works. I wrote it to pipe (|) to a text-to-speech (tts) application. It uses the 'Edits' interface for OpenAI - which doesn't get enough credit for how great it is.

Included as a bonus toy is the edits.py app, which is a thin command line wrapper around the Edits interface.

```
./edits.py Summarize the following README.md < README.md 
```
This repository provides a Python script that summarizes URLs using OpenAI's text-generation web UI. The script takes a URL as input and outputs a summary of the content in the form of a list of bullet points. The author also includes a bonus "thin command line wrapper around the Edits interface" called edits.py for users who want to use the OpenAI extension. There are examples included to demonstrate how the script works, including a summary of a YouTube video on quantum computing and another on Cacio e Pepe pasta.


### Usage

```
python3 url_summary.py https://www.youtube.com/watch?v=XXX
python3 url_summary.py https://youtu.be/XXX
python3 url_summary.py <some other url with text>
```

## Examples

Example: Quantum Computing Explained (10 min) - https://www.youtube.com/watch?v=jHoEjvuPoB8
```
$ python3 url_summary.py https://www.youtube.com/watch?v=jHoEjvuPoB8
```
* Quantum computer located inside a refrigerator at near-absolute temperatures.
* Promise of revolutionizing lives with turbo-charged computation.
* Not the next generation of supercomputers but something else entirely.
* Requires understanding of fundamental physics of quantum computing.
* Richard Feynman proposed the idea of a quantum computer in the 1980s.
* Classical computers cannot handle the exponential increase in computation required by quantum systems.
* Feynman's idea was to create a tool made of quantum elements to study quantum phenomena.
* Amplitudes in quantum mechanics differ from classical probability in that they are complex numbers.
* Qubits are the basic computational units in quantum computing, storing information in a state of superposition.
* Superposition allows quantum computers to store and manipulate vast amounts of data compared to classical computers.
* Entanglement occurs when two or more qubits are in a state of superposition and their final outcomes are mathematically related.
* A quantum computer requires more classical bits than there are atoms in the known universe when expanded to include 500 entangled qubits.
* Measuring information from qubits collapses their state, making it impossible to obtain an output without losing information.
* Interference is used to extract an answer from a quantum system that is not a random outcome of probability.
* Deterministic sequences of qubit gates can be created to harness interference and increase the probability of finding the correct answer.
* Designing quantum algorithms is challenging because scientists themselves do not know in advance which answer is the right one.
* Quantum computers have potential applications in fields such as cybersecurity and search optimization, but their most important application may be exploring the deep structure of the world.

Example: About Cacio e Pepe pasta. (10 min) - https://www.youtube.com/watch?v=Ng7GWl57nQM

```
$ python3 url_summary.py https://www.youtube.com/watch?v=Ng7GWl57nQM
```
* Cacio e Pepe is a pasta dish made with cheese and pepper.
* It is considered the most important pasta dish in Italian cuisine.
* The dish is difficult to master but has a unique texture and taste.
* Ingredients include pasta (usually made with thick spaghetti), pecorino cheese, black pepper, and water.
* To create the desired texture, the cheese needs to be melted and mixed with the other ingredients.
* Stabilizing the emulsion is key to achieving the creamy consistency of Cacio e Pepe.
