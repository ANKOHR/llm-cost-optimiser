import json
import time
from llm_cost_optimiser.cli import main
from llm_cost_optimiser.fixtures import generate, fixture_records

def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    start = time.perf_counter()
    assert main(['fixtures', '--out', 'demo']) == 0
    assert main(['run', '--input', 'demo']) == 0
    assert main(['report', '--format', 'md']) == 0
    assert time.perf_counter() - start < 5
    assert 'Provenance:' in capsys.readouterr().out

def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'empty').mkdir()
    assert main(['run', '--input', 'empty']) == 0
    assert main(['report']) == 0
    assert 'Records: 0' in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / 'bad.jsonl').write_text('# comment\n{bad')
    assert main(['run', '--input', str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert 'ParseError' in error and 'bad.jsonl' in error and 'line 2' in error

def test_determinism_byte_identical(tmp_path):
    generate(tmp_path / 'demo')
    state = tmp_path / 'state.json'
    args = ['run', '--input', str(tmp_path / 'demo'), '--state', str(state)]
    assert main(args) == 0
    original = state.read_bytes()
    assert main(args) == 0
    assert state.read_bytes() == original
    report = tmp_path / 'report.md'
    args = ['report', '--state', str(state), '--out', str(report)]
    assert main(args) == 0
    original = report.read_bytes()
    assert main(args) == 0
    assert report.read_bytes() == original

def test_cli_smoke_all_subcommands(tmp_path, monkeypatch):
    import pytest
    monkeypatch.chdir(tmp_path)
    for command in ('fixtures', 'run', 'report', 'route', 'audit'):
        with pytest.raises(SystemExit) as exc:
            main([command, '--help'])
        assert exc.value.code == 0
    generate('demo')
    for command in ('run', 'route', 'audit'):
        assert main([command, '--input', 'demo']) == 0
    for fmt in ('md', 'json'):
        assert main(['report', '--format', fmt]) == 0

def test_handles_unicode_and_long_inputs(tmp_path, capsys):
    record = fixture_records(1)[0]
    record['id'] = '中文 café ' + 'x'*9000
    record['description'] = r'C:\Users\henry\输入.json'
    (tmp_path / 'real.json').write_text(json.dumps([record], ensure_ascii=False), encoding='utf-8')
    assert main(['route', '--input', str(tmp_path)]) == 0
    assert '中文 café' in capsys.readouterr().out

def test_missing_input_and_atomic_write_failure(tmp_path, capsys):
    assert main(['run', '--input', str(tmp_path / 'missing')]) == 2
    assert 'MissingInput' in capsys.readouterr().err
    generate(tmp_path / 'demo')
    state = tmp_path / 'state.json'
    assert main(['run', '--input', str(tmp_path / 'demo'), '--state', str(state)]) == 0
    target = tmp_path / 'blocked'
    target.mkdir()
    assert main(['report', '--state', str(state), '--out', str(target)]) == 2
    assert 'FileError' in capsys.readouterr().err
    assert sorted(p.name for p in tmp_path.iterdir()) == ['blocked', 'demo', 'state.json']

def test_schema_error_has_file_line_field(tmp_path, capsys):
    (tmp_path / 'bad.json').write_text('{"id":"x"}')
    assert main(['audit', '--input', str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert 'SchemaError' in error and 'bad.json' in error and 'line 1' in error and 'fields' in error
