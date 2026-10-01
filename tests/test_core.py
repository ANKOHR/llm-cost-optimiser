import copy
import pytest
from llm_cost_optimiser.core import optimise, select, SchemaError
from llm_cost_optimiser.fixtures import fixture_records

def test_fixture_ground_truth_matches_hand_computed():
    result = optimise(fixture_records())
    assert (result['records'], result['selected'], result['infeasible']) == (200, 150, 50)
    assert result['totals']['synthetic'] == {'records': 200, 'selected_cost': '250', 'baseline_comparisons': 150, 'baseline_delta': '200'}
    for i, row in enumerate(result['decisions']):
        assert row['selected'] == ['economy', 'premium', None, 'economy'][i % 4]

@pytest.mark.parametrize('field,value', [('min_quality', '-1'), ('min_quality', 'NaN'), ('min_quality', True), ('observed_on', '2099-01-01'), ('id', 'x'*10001), ('unexpected', 3)])
def test_rejects_adversarial_values(field, value):
    record = fixture_records(1)[0]
    record[field] = value
    with pytest.raises(SchemaError):
        optimise([record])

@pytest.mark.parametrize('cost', ['-1', 'Infinity', '1000000001', '0.0000001'])
def test_rejects_bad_cost(cost):
    record = fixture_records(1)[0]
    record['candidates'][0]['cost'] = cost
    with pytest.raises(SchemaError):
        select(record)

def test_duplicate_ids_and_models():
    record = fixture_records(1)[0]
    with pytest.raises(SchemaError, match='duplicate'):
        optimise([record, record])
    record['candidates'].append(copy.deepcopy(record['candidates'][0]))
    with pytest.raises(SchemaError, match='duplicate'):
        select(record)

def test_corrupted_ground_truth_changes_computation():
    records = fixture_records()
    original = optimise(records)
    records[0]['candidates'][0]['quality'] = '0.1'
    changed = optimise(records)
    assert changed['decisions'][0]['selected'] == 'premium'
    assert changed['totals']['synthetic']['selected_cost'] == '252'
    assert original != changed

def test_tie_break_baseline_absent_and_negative_delta():
    record = fixture_records(1)[0]
    record['candidates'][1]['cost'] = '1'
    assert select(record)['selected'] == 'economy'
    record['baseline'] = None
    assert select(record)['baseline_delta'] is None
    record['baseline'] = 'economy'
    record['candidates'][0]['quality'] = '0.1'
    record['candidates'][1]['cost'] = '3'
    assert select(record)['baseline_delta'] == '-2'
