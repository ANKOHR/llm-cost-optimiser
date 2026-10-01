"""Pure routing. Supplied quality is evidence, never a predicted guarantee."""
from decimal import Decimal, InvalidOperation
from datetime import date

class SchemaError(ValueError):
    """A named input contract violation."""

def number(value, field, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise SchemaError(f"{field}: expected numeric value")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise SchemaError(f"{field}: invalid number") from None
    if not result.is_finite() or result < 0 or (maximum is not None and result > maximum):
        raise SchemaError(f"{field}: outside permitted range")
    if result > Decimal('1000000000') or result.as_tuple().exponent < -6:
        raise SchemaError(f"{field}: maximum 1 billion and six decimal places")
    return result

def label(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 10000:
        raise SchemaError(f"{field}: expected nonempty string up to 10000 characters")
    if chr(0x2014) in value or any(ord(c) < 32 for c in value):
        raise SchemaError(f"{field}: prohibited control character or em dash")
    return value

def validate(record):
    if not isinstance(record, dict):
        raise SchemaError('record: expected object')
    required = {'id', 'synthetic', 'min_quality', 'candidates', 'baseline', 'evidence'}
    missing = required - record.keys()
    extra = record.keys() - required - {'observed_on', 'description'}
    if missing or extra:
        raise SchemaError(f"fields: missing {sorted(missing)}, unknown {sorted(extra)}")
    label(record['id'], 'id')
    if type(record['synthetic']) is not bool:
        raise SchemaError('synthetic: expected boolean')
    if record['evidence'] not in ('measured', 'hypothetical'):
        raise SchemaError('evidence: expected measured or hypothetical')
    number(record['min_quality'], 'min_quality', Decimal(1))
    if 'description' in record:
        label(record['description'], 'description')
    if 'observed_on' in record:
        try:
            observed = date.fromisoformat(record['observed_on'])
        except (ValueError, TypeError):
            raise SchemaError('observed_on: expected ISO date') from None
        # Fixed contract cutoff preserves reproducibility, including on future runs.
        if observed > date(2026, 9, 30):
            raise SchemaError('observed_on: after evidence cutoff 2026-09-30')
    candidates = record['candidates']
    if not isinstance(candidates, list) or len(candidates) > 1000:
        raise SchemaError('candidates: expected list of at most 1000')
    names = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != {'model', 'cost', 'quality'}:
            raise SchemaError('candidates: expected model, cost, quality fields')
        name = label(candidate['model'], 'model')
        if name in names:
            raise SchemaError('model: duplicate')
        names.add(name)
        number(candidate['cost'], 'cost')
        number(candidate['quality'], 'quality', Decimal(1))
    if record['baseline'] is not None and record['baseline'] not in names:
        raise SchemaError('baseline: must name a candidate or be null')
    return record

def select(record):
    validate(record)
    eligible = [c for c in record['candidates'] if number(c['quality'], 'quality') >= number(record['min_quality'], 'min_quality')]
    chosen = min(eligible, key=lambda c: (number(c['cost'], 'cost'), c['model'])) if eligible else None
    baseline = next((c for c in record['candidates'] if c['model'] == record['baseline']), None)
    delta = number(baseline['cost'], 'cost') - number(chosen['cost'], 'cost') if baseline and chosen else None
    kind = 'synthetic' if record['synthetic'] else record['evidence']
    return {'id': record['id'], 'selected': chosen['model'] if chosen else None,
            'cost': str(number(chosen['cost'], 'cost')) if chosen else None,
            'status': 'selected' if chosen else 'infeasible', 'provenance': kind,
            'baseline_delta': str(delta) if delta is not None else None}

def optimise(records):
    seen = set()
    rows = []
    for record in records:
        validate(record)
        if record['id'] in seen:
            raise SchemaError('id: duplicate ' + record['id'])
        seen.add(record['id'])
        rows.append(select(record))
    rows.sort(key=lambda r: r['id'])
    totals = {}
    for kind in ('synthetic', 'measured', 'hypothetical'):
        subset = [r for r in rows if r['provenance'] == kind]
        totals[kind] = {'records': len(subset), 'selected_cost': str(sum((Decimal(r['cost']) for r in subset if r['cost'] is not None), Decimal(0))),
                        'baseline_comparisons': sum(r['baseline_delta'] is not None for r in subset),
                        'baseline_delta': str(sum((Decimal(r['baseline_delta']) for r in subset if r['baseline_delta'] is not None), Decimal(0)))}
    return {'records': len(rows), 'selected': sum(r['selected'] is not None for r in rows),
            'infeasible': sum(r['selected'] is None for r in rows), 'totals': totals, 'decisions': rows}
