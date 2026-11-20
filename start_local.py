"""Explicit local launcher; credentials remain in process memory."""
import argparse
import ast
import os
from pathlib import Path
import runpy
import sys


def read_key(path):
    for line in path.read_text().splitlines():
        name, separator, value = line.strip().removeprefix('export ').partition('=')
        if separator and name.strip() == 'GEMINI_API_KEY':
            value = value.strip()
            key = ast.literal_eval(value) if value.startswith(('"', "'")) else value.split(' #', 1)[0].strip()
            if isinstance(key, str) and key.strip():
                return key.strip()
    raise ValueError('missing_key')


def main():
    parser = argparse.ArgumentParser(description='Start local Karmolab; AI requires explicit opt-in.')
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--ai', action='store_true')
    parser.add_argument('--key-file', type=Path)
    parser.add_argument('--model', default='gemini-3.1-flash-lite')
    parser.add_argument('--daily-limit', type=int, default=2)
    args = parser.parse_args()
    os.environ['KARMOLAB_AI_ENABLED'] = '0'
    if args.ai:
        if not 1 <= args.daily_limit <= 20:
            parser.error('Daily limit must be between 1 and 20.')
        try:
            key = read_key(args.key_file) if args.key_file else os.environ.get('GEMINI_API_KEY')
            if not key:
                raise ValueError('missing_key')
        except (OSError, ValueError, SyntaxError):
            parser.error('Could not load the saved key. Key values are never printed.')
        os.environ.update(GEMINI_API_KEY=key, KARMOLAB_AI_ENABLED='1',
                          KARMOLAB_GEMINI_MODEL=args.model,
                          KARMOLAB_AI_DAILY_LIMIT=str(args.daily_limit))
    sys.argv = ['run.py', '--port', str(args.port)]
    runpy.run_path(str(Path(__file__).with_name('run.py')), run_name='__main__')

if __name__ == '__main__':
    main()
