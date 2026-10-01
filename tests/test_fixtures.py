import json
from llm_cost_optimiser.fixtures import generate
from llm_cost_optimiser.cli import read_inputs

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    assert (tmp_path / 'records.jsonl').read_text().startswith('# SYNTHETIC')
    records, _ = read_inputs(tmp_path)
    assert len(records) == 200
    assert all(r['synthetic'] is True for r in records)
    assert json.loads((tmp_path / 'expectations.json').read_text())['synthetic'] is True
