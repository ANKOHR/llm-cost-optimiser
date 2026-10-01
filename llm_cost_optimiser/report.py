"""Reports distinguish synthetic, real measured and hypothetical evidence."""
import json
BANNER = ('Provenance: synthetic = labelled illustrative fixtures; measured = real inputs entered by the user with user-declared measurements; hypothetical = real inputs with illustrative figures. No independent measurement or model prediction is performed.')

def render(result, fmt='json'):
    envelope = {'provenance_banner': BANNER, 'inputs': result.get('inputs', []), 'result': result}
    if fmt == 'json':
        return json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    lines = ['# LLM Cost Optimiser', '', BANNER, '', f"Records: {result['records']}; selected: {result['selected']}; infeasible: {result['infeasible']}", '',
             'All costs are supplied decimal currency units. Baseline deltas may be negative. No time savings are measured.', '']
    for kind, totals in result['totals'].items():
        lines.append(f"{kind}: records={totals['records']}, selected cost={totals['selected_cost']}, baseline comparisons={totals['baseline_comparisons']}, baseline delta={totals['baseline_delta']}")
    lines += ['', 'Input files: ' + json.dumps(result.get('inputs', []), ensure_ascii=False), '', 'Decisions (explicit input evidence):', '']
    lines += [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in result['decisions']]
    return '\n'.join(lines) + '\n'
