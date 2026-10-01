"""Local file CLI with atomic output and named failures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from .core import SchemaError, optimise
from .fixtures import generate
from .report import render

class ParseError(ValueError):
    pass

def read_inputs(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"MissingInput: {directory}; use lco fixtures --out demo")
    records, inputs = [], []
    for path in sorted(directory.iterdir()):
        if path.name == 'expectations.json':
            continue
        if path.suffix not in ('.jsonl', '.json'):
            raise SchemaError(f'{path}: field format: only JSON and JSONL supported')
        raw = path.read_bytes()
        try:
            content = raw.decode('utf-8-sig')
        except UnicodeError:
            raise ParseError(f'{path}: line 1: invalid UTF-8') from None
        inputs.append({'file': path.name, 'sha256': hashlib.sha256(raw).hexdigest()})
        if path.suffix == '.jsonl':
            entries = [(line_no, line) for line_no, line in enumerate(content.splitlines(), 1) if line.strip() and not line.startswith('#')]
        else:
            entries = [(1, content)]
        for line_no, text in entries:
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ParseError(f'{path}: line {line_no + exc.lineno - 1}: {exc.msg}') from None
            batch = value if path.suffix == '.json' and isinstance(value, list) else [value]
            for record in batch:
                try:
                    from .core import validate
                    validate(record)
                except SchemaError as exc:
                    raise SchemaError(f'{path}: line {line_no}: {exc}') from None
                records.append(record)
    return records, inputs

def atomic_write(path, text):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=path.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)

def main(argv=None):
    parser = argparse.ArgumentParser(description='Route using explicit supplied quality and cost evidence. No model calls.')
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('fixtures', help='Generate 200 labelled synthetic records', epilog='Example: lco fixtures --out demo')
    p.add_argument('--out', required=True)
    for command, help_text in [('run', 'Optimise all records and save computed results'), ('route', 'Print per-task eligible cheapest model decisions'), ('audit', 'Validate evidence and summarise infeasible tasks')]:
        p = subs.add_parser(command, help=help_text, description=help_text, epilog=f'Example: lco {command} --input demo')
        p.add_argument('--input', required=True)
        if command == 'run':
            p.add_argument('--state', default='.lco/result.json')
    p = subs.add_parser('report', help='Render provenance and computed results', epilog='Example: lco report --format md')
    p.add_argument('--format', choices=['md', 'json'], default='md')
    p.add_argument('--state', default='.lco/result.json')
    p.add_argument('--out')
    args = parser.parse_args(argv)
    try:
        if args.command == 'fixtures':
            generate(args.out)
            print('Generated 200 SYNTHETIC records with hypothetical costs and quality.')
        elif args.command == 'report':
            path = Path(args.state)
            if not path.is_file():
                raise FileNotFoundError(f'MissingInput: {path}; use lco run --input demo')
            result = json.loads(path.read_text(encoding='utf-8'))
            output = render(result, args.format)
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end='')
        else:
            records, inputs = read_inputs(args.input)
            result = optimise(records)
            result['inputs'] = inputs
            if args.command == 'run':
                atomic_write(args.state, json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
                print(f"Computed {result['records']} records. Synthetic and hypothetical figures are illustrative; measured inputs are user-declared. State: {args.state}")
            else:
                print(render(result, 'json'), end='')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        name = type(exc).__name__ if isinstance(exc, (SchemaError, ParseError)) else 'FileError' if isinstance(exc, OSError) else 'SchemaError'
        print(f'{name}: {exc}', file=__import__('sys').stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
