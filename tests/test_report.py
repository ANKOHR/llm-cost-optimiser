import json
from llm_cost_optimiser.core import optimise
from llm_cost_optimiser.fixtures import fixture_records, generate
from llm_cost_optimiser.report import render

def test_report_matches_ground_truth_exact(tmp_path):
    generate(tmp_path)
    expected = json.loads((tmp_path / 'expectations.json').read_text())
    result = json.loads(render(optimise(fixture_records())))['result']
    for key in ('records', 'selected', 'infeasible'):
        assert result[key] == expected[key]
    for key in ('selected_cost', 'baseline_delta', 'baseline_comparisons'):
        assert result['totals']['synthetic'][key] == expected[key]

def test_report_zero_false_positives():
    result = optimise(fixture_records())
    found = [r['id'] for r in result['decisions'] if r['status'] == 'infeasible']
    assert found == [f'task-{i:03}' for i in range(2, 200, 4)]

def test_report_carries_provenance_banner():
    for fmt in ('md', 'json'):
        text = render(optimise([]), fmt)
        assert 'Provenance:' in text and 'real inputs' in text and 'synthetic' in text

def test_hypothetical_figures_labelled():
    record = fixture_records(1)[0]
    record['synthetic'] = False
    result = optimise([record])
    assert result['totals']['measured']['records'] == 0
    assert result['totals']['hypothetical']['selected_cost'] == '1'
    for fmt in ('md', 'json'):
        assert 'hypothetical' in render(result, fmt)

def test_no_em_dashes_in_outputs():
    for fmt in ('md', 'json'):
        assert chr(0x2014) not in render(optimise(fixture_records()), fmt)
