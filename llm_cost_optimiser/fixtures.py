"""Synthetic planted cases. No randomness or inferred performance."""
import json
from pathlib import Path

def fixture_records(count=200):
    records = []
    for i in range(count):
        case = i % 4
        records.append({'id': f'task-{i:03}', 'synthetic': True, 'evidence': 'hypothetical',
                        'min_quality': '0.8', 'baseline': 'premium',
                        'candidates': [{'model': 'economy', 'cost': '1', 'quality': ['0.9', '0.7', '0.7', '0.8'][case]},
                                       {'model': 'premium', 'cost': '3', 'quality': ['0.95', '0.9', '0.6', '0.9'][case]}]})
    return records

def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    data = '# SYNTHETIC fixture: illustrative costs and supplied quality, not measurements\n'
    data += ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in fixture_records())
    (out / 'records.jsonl').write_text(data, encoding='utf-8')
    expected = {'synthetic': True, 'label': 'SYNTHETIC hand-computed expectations', 'records': 200,
                'selected': 150, 'infeasible': 50, 'selected_cost': '250', 'baseline_delta': '200',
                'baseline_comparisons': 150,
                'infeasible_ids': [f'task-{i:03}' for i in range(2, 200, 4)]}
    (out / 'expectations.json').write_text(json.dumps(expected, indent=2, sort_keys=True) + '\n', encoding='utf-8')
