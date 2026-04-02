#!/usr/bin/env python3
"""Convert straight quotes to Unicode curly quotes in scratch.txt note prose."""
import sys

SCRATCH = 'output/scratch.txt'

def is_prose_line(line):
    s = line.strip()
    if not s:
        return False
    if s.startswith('---'):
        return False
    if s.startswith('rc://'):
        return False
    # Skip Hebrew-heavy lines (>30% chars in Hebrew Unicode ranges)
    hebrew = sum(1 for c in s if '\u0590' <= c <= '\u05ff' or '\ufb1d' <= c <= '\ufb4f')
    if hebrew > len(s) * 0.3:
        return False
    return True

def smart_double_quotes(text):
    result = []
    open_next = True
    for i, c in enumerate(text):
        if c == '"':
            result.append('\u201c' if open_next else '\u201d')
            open_next = not open_next
        else:
            result.append(c)
            if c in ' \t\n\r([{':
                open_next = True
    return ''.join(result)

def smart_single_quotes(text):
    result = []
    for i, c in enumerate(text):
        if c == "'":
            prev = text[i - 1] if i > 0 else ' '
            nxt = text[i + 1] if i + 1 < len(text) else ' '
            if prev.isalpha():
                result.append('\u2019')  # apostrophe / closing
            elif nxt.isalpha() or nxt.isdigit():
                result.append('\u2018')  # opening
            else:
                result.append('\u2019')
        else:
            result.append(c)
    return ''.join(result)

def process(text):
    lines = text.split('\n')
    out = []
    for line in lines:
        if is_prose_line(line):
            line = smart_double_quotes(line)
            line = smart_single_quotes(line)
        out.append(line)
    return '\n'.join(out)

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else SCRATCH
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    result = process(content)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f'Curly quotes applied to {path}')
