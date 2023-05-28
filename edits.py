#!/usr/bin/env python3

# ./edits.py Translate the following text to French < README.txt
# ./edits.py Fix the bugs in the following python code < buggy.py
# etc.


import sys
import openai

response = openai.Edit.create(
    model="gpt-3.5-turbo",
    instruction=' '.join(sys.argv[1:]),
    input=sys.stdin.read(),
)

print(response.choices[0].text)

