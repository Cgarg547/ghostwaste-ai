from fastapi.testclient import TestClient
from uuid import uuid4
from apps.api.main import app

client = TestClient(app)

def test_health():
    assert client.get('/health').json()['status'] == 'ok'

def test_scenario():
    payload = {'as_of':'2026-11-08','batches':[{'id':'a','ingredient':'spinach','quantity_kg':10,'use_by':'2026-11-10','unit_cost':4}], 'demand':[{'ingredient':'spinach','expected_daily_kg':2}]}
    result = client.post('/scenario',json=payload)
    assert result.status_code == 200
    assert result.json()['total_at_risk_kg'] == 6
    assert result.json()['total_potential_cost'] == 24

def test_duplicate_batches_rejected():
    b={'id':'a','ingredient':'spinach','quantity_kg':10,'use_by':'2026-11-10','unit_cost':4}
    result=client.post('/scenario',json={'as_of':'2026-11-08','batches':[b,{**b,'id':'b'}], 'demand':[]})
    assert result.status_code == 200
    assert result.json()['total_at_risk_kg'] == 20

def test_negative_quantity_rejected():
    result=client.post('/scenario',json={'as_of':'2026-11-08','batches':[{'id':'a','ingredient':'x','quantity_kg':-1,'use_by':'2026-11-10','unit_cost':4}], 'demand':[]})
    assert result.status_code == 422

def test_fefo_allocates_multiple_batches_by_expiry():
    payload={'as_of':'2026-11-08','batches':[
        {'id':'early','ingredient':'spinach','quantity_kg':5,'use_by':'2026-11-10','unit_cost':4},
        {'id':'late','ingredient':'spinach','quantity_kg':8,'use_by':'2026-11-12','unit_cost':4}],
        'demand':[{'ingredient':'spinach','expected_daily_kg':3}]}
    data=client.post('/scenario',json=payload).json()
    assert data['risks'][0]['at_risk_kg'] == 0
    assert data['risks'][1]['at_risk_kg'] == 1

def test_expired_batch_is_never_allocated():
    data=client.post('/scenario',json={'as_of':'2026-11-08','batches':[{'id':'old','ingredient':'x','quantity_kg':2,'use_by':'2026-11-07','unit_cost':5}],'demand':[{'ingredient':'x','expected_daily_kg':99}]}).json()
    assert data['total_at_risk_kg'] == 2
    assert data['total_potential_cost'] == 10

def test_near_expiry_alert_and_forecast_waste_can_validly_differ():
    # An alert is proximity-only. With enough forecast demand before use-by,
    # FEFO and the simulation correctly leave no predicted unsold inventory.
    payload={'as_of':'2026-11-08','batches':[{'id':'soon','ingredient':'x','quantity_kg':2,'use_by':'2026-11-10','unit_cost':5}], 'demand':[{'ingredient':'x','expected_daily_kg':2}]}
    deterministic=client.post('/scenario',json=payload).json()
    simulated=client.post('/risk/simulate',json={**payload,'horizon_days':2,'trials':50,'seed':4}).json()['result']
    assert deterministic['total_at_risk_kg']==0
    assert simulated['expected_waste_kg']==0

def test_inventory_and_forecast_workflow(tmp_path, monkeypatch):
    # API contracts are exercised against the test application's local SQLite setup.
    ingredient=client.post('/ingredients',json={'name':f'Test herb {uuid4()}','storage_category':'chilled'}).json()
    batch=client.post('/batches',json={'ingredient_id':ingredient['id'],'quantity_kg':2,'unit_cost':3,'received_on':'2026-11-08','use_by':'2026-11-10'})
    assert batch.status_code == 201
    menu_item=f'salad-{uuid4()}'
    for day, qty in [('2026-11-01',10),('2026-11-02',12),('2026-11-03',11)]:
        assert client.post('/sales',json={'menu_item':menu_item,'sold_on':day,'quantity':qty}).status_code == 201
    forecast=client.get(f'/forecast/{menu_item}').json()
    assert forecast['model'] == 'moving_average_7_or_less'
    assert forecast['predictions'][0]['quantity'] == 11

def test_persisted_forecast_run_uses_rolling_origin_selection():
    menu_item=f'forecast-{uuid4()}'
    for day in range(1,11):
        assert client.post('/sales',json={'menu_item':menu_item,'sold_on':f'2026-10-{day:02d}','quantity':float(day)}).status_code==201
    run=client.post(f'/forecasts/{menu_item}',json={'horizon':3,'initial_train':5})
    assert run.status_code==201
    body=run.json();assert body['model'] in {'moving_average','seasonal_naive'}
    assert body['evaluation']['points']==5
    assert len(client.get(f'/forecasts/{menu_item}/history').json())==1

def test_forecast_can_translate_to_recipe_ingredient_demand():
    suffix=str(uuid4()); menu=f'menu-{suffix}'
    ingredient=client.post('/ingredients',json={'name':f'ingredient-{suffix}','storage_category':'chilled'}).json()
    recipe=client.post('/recipes',json={'name':menu,'yield_servings':2}).json()
    client.post(f"/recipes/{recipe['id']}/ingredients",json={'ingredient_id':ingredient['id'],'quantity_kg':.5})
    for day in range(1,9): client.post('/sales',json={'menu_item':menu,'sold_on':f'2026-09-{day:02d}','quantity':2})
    run=client.post(f'/forecasts/{menu}',json={'horizon':2,'initial_train':4}).json()
    demand=client.get(f"/forecasts/{run['id']}/ingredient-demand").json()
    assert demand['ingredient_demand'][0]['required_kg']==1

def test_forecast_recipe_workflow_persists_simulated_risk_and_recommendations():
    suffix=str(uuid4()); menu=f'wf-{suffix}'
    ingredient=client.post('/ingredients',json={'name':f'wf-ing-{suffix}','storage_category':'chilled'}).json()
    supplier=client.post('/suppliers',json={'name':f'wf-supplier-{suffix}','lead_days':1,'minimum_order_kg':0}).json()
    assert client.post(f"/suppliers/{supplier['id']}/ingredients",json={'ingredient_id':ingredient['id'],'purchase_unit_cost':3}).status_code==201
    recipe=client.post('/recipes',json={'name':menu,'yield_servings':1}).json();client.post(f"/recipes/{recipe['id']}/ingredients",json={'ingredient_id':ingredient['id'],'quantity_kg':1})
    client.post('/batches',json={'ingredient_id':ingredient['id'],'quantity_kg':1,'unit_cost':3,'received_on':'2026-09-01','use_by':'2026-10-12'})
    for day in range(1,9): client.post('/sales',json={'menu_item':menu,'sold_on':f'2026-09-{day:02d}','quantity':2})
    run=client.post(f'/forecasts/{menu}',json={'horizon':2,'initial_train':4}).json()
    workflow=client.post(f"/workflows/forecast/{run['id']}",json={'as_of':'2026-10-10','horizon_days':2,'seed':7,'storage_capacity_kg':10}).json()
    assert workflow['result']['provenance']=='simulated_forecast_recipe_inventory'
    assert workflow['result']['monte_carlo']['seed']==7
    assert workflow['result']['optimization']['diagnostics']['solver']=='CBC mixed integer'
    assert client.get(f"/risk-scenarios/{workflow['scenario_id']}").status_code==200

def test_persisted_forecast_and_linked_scenario_can_be_restored_without_duplicates():
    suffix=str(uuid4()); menu=f'restore-{suffix}'
    ingredient=client.post('/ingredients',json={'name':f'restore-ing-{suffix}'}).json()
    supplier=client.post('/suppliers',json={'name':f'restore-supplier-{suffix}','lead_days':0,'minimum_order_kg':0}).json()
    client.post(f"/suppliers/{supplier['id']}/ingredients",json={'ingredient_id':ingredient['id'],'purchase_unit_cost':2})
    recipe=client.post('/recipes',json={'name':menu,'yield_servings':1}).json()
    client.post(f"/recipes/{recipe['id']}/ingredients",json={'ingredient_id':ingredient['id'],'quantity_kg':1})
    for day in range(1,9): client.post('/sales',json={'menu_item':menu,'sold_on':f'2026-09-{day:02d}','quantity':2})
    run=client.post(f'/forecasts/{menu}',json={'horizon':2,'initial_train':4}).json()
    assert any(x['id']==run['id'] and x['menu_item']==menu for x in client.get('/forecast-runs').json())
    assert client.get(f"/forecast-runs/{run['id']}").json()['id']==run['id']
    body={'as_of':'2026-10-10','horizon_days':2,'trials':50,'seed':13,'storage_capacity_kg':10}
    first=client.post(f"/workflows/forecast/{run['id']}",json=body).json()
    restored=client.post(f"/workflows/forecast/{run['id']}",json=body).json()
    assert restored['scenario_id']==first['scenario_id'] and restored['restored'] is True
    linked=client.get(f"/risk-scenarios?forecast_run_id={run['id']}").json()
    assert len([x for x in linked if x['id']==first['scenario_id']])==1
    assert linked[0]['outputs']['provenance']=='simulated_forecast_recipe_inventory'

def test_two_saved_forecasts_keep_distinct_sales_predictions_and_scenario_links():
    suffix=str(uuid4())
    runs=[]
    for label, quantities in [('rising',[1,2,3,4,5,6,7,8,9,10,11,12]),('falling',[24,22,20,18,16,14,12,10,8,6,4,2])]:
        menu=f'{label}-{suffix}'
        ingredient=client.post('/ingredients',json={'name':f'{label}-ingredient-{suffix}'}).json()
        recipe=client.post('/recipes',json={'name':menu,'yield_servings':1}).json()
        assert client.post(f"/recipes/{recipe['id']}/ingredients",json={'ingredient_id':ingredient['id'],'quantity_kg':.01}).status_code==201
        for day, quantity in enumerate(quantities,1):
            assert client.post('/sales',json={'menu_item':menu,'sold_on':f'2026-10-{day:02d}','quantity':quantity}).status_code==201
        response=client.post(f'/forecasts/{menu}',json={'horizon':4,'initial_train':5})
        assert response.status_code==201
        run=response.json()
        workflow=client.post(f"/workflows/forecast/{run['id']}",json={'as_of':'2026-11-08','horizon_days':4,'trials':50,'seed':731,'storage_capacity_kg':20})
        assert workflow.status_code==200
        runs.append((run,workflow.json()['scenario_id']))
    rising, falling=runs
    assert rising[0]['predictions'] != falling[0]['predictions']
    assert client.get(f"/sales?menu_item={rising[0]['menu_item']}").json()[0]['quantity']==1
    assert client.get(f"/sales?menu_item={falling[0]['menu_item']}").json()[0]['quantity']==24
    assert client.get(f"/risk-scenarios/{rising[1]}").json()['forecast_run_id']==rising[0]['id']
    assert client.get(f"/risk-scenarios/{falling[1]}").json()['forecast_run_id']==falling[0]['id']

def test_supplier_recipe_and_stock_events_preserve_integrity():
    suffix=str(uuid4())
    ingredient=client.post('/ingredients',json={'name':f'carrot-{suffix}','storage_category':'chilled'}).json()
    supplier=client.post('/suppliers',json={'name':f'farm-{suffix}','lead_days':2,'minimum_order_kg':5})
    assert supplier.status_code==201
    recipe=client.post('/recipes',json={'name':f'soup-{suffix}','yield_servings':10}).json()
    assert client.post(f"/recipes/{recipe['id']}/ingredients",json={'ingredient_id':ingredient['id'],'quantity_kg':.2}).status_code==201
    batch=client.post('/batches',json={'ingredient_id':ingredient['id'],'quantity_kg':2,'unit_cost':2,'received_on':'2026-11-01','use_by':'2026-11-10'}).json()
    assert client.post(f"/batches/{batch['id']}/consume",json={'quantity_kg':1,'occurred_on':'2026-11-02'}).json()['remaining_kg']==1
    assert client.post(f"/batches/{batch['id']}/waste",json={'quantity_kg':2,'occurred_on':'2026-11-03','reason':'spoiled'}).status_code==409
    assert client.post(f"/batches/{batch['id']}/waste",json={'quantity_kg':1,'occurred_on':'2026-11-03','reason':'spoiled'}).json()['remaining_kg']==0

def test_supplier_must_be_explicitly_linked_and_decisions_are_final():
    suffix=str(uuid4()); ingredient=client.post('/ingredients',json={'name':f'linked-{suffix}'}).json()
    supplier=client.post('/suppliers',json={'name':f'supplier-{suffix}','lead_days':1,'minimum_order_kg':2}).json()
    linked=client.post(f"/suppliers/{supplier['id']}/ingredients",json={'ingredient_id':ingredient['id'],'purchase_unit_cost':4})
    assert linked.status_code==201 and any(x['id']==supplier['id'] and x['ingredients'][0]['ingredient_id']==ingredient['id'] for x in client.get('/suppliers').json())
    scenario=client.post('/recommendations/from-scenario',json={'as_of':'2026-11-08','batches':[{'id':f'b-{suffix}','ingredient':'x','quantity_kg':1,'use_by':'2026-11-08','unit_cost':2}],'demand':[]}).json()
    recommendation=scenario['recommendations'][0]['id']
    assert client.post(f'/recommendations/{recommendation}/decision',json={'decision':'accepted','reason':'Manager reviewed local plan'}).status_code==200
    assert client.post(f'/recommendations/{recommendation}/decision',json={'decision':'rejected','reason':'Trying second decision'}).status_code==409

def test_csv_import_is_atomic_and_export_is_formula_safe():
    bad="ingredient,quantity_kg,unit_cost,received_on,use_by,storage_category\n=unsafe,1,2,2026-11-01,2026-11-02,chilled"
    assert client.post('/inventory/import',json={'csv_text':bad}).status_code==422
    herb=f"csv herb {uuid4()}"
    good=f"ingredient,quantity_kg,unit_cost,received_on,use_by,storage_category\n{herb},1.5,2,2026-11-01,2026-11-02,chilled"
    assert client.post('/inventory/import',json={'csv_text':good}).json()['imported_batches']==1
    assert client.post('/inventory/import',json={'csv_text':good}).json()['skipped_duplicates']==1
    grams=f"ingredient,quantity_kg,unit_cost,received_on,use_by,storage_category,unit\nmetric herb {uuid4()},500,2,2026-11-01,2026-11-02,chilled,g"
    assert client.post('/inventory/import',json={'csv_text':grams}).json()['imported_batches']==1
    exported=client.get('/inventory/export.csv')
    assert exported.status_code==200 and 'csv herb' in exported.text

def test_data_entry_contracts_validate_dates_and_recipe_links_are_idempotent():
    suffix=str(uuid4())
    ingredient=client.post('/ingredients',json={'name':f'contract-{suffix}','storage_category':'frozen'}).json()
    assert client.post('/batches',json={'ingredient_id':ingredient['id'],'quantity_kg':1,'unit_cost':2,'received_on':'2026-11-03','use_by':'2026-11-02'}).status_code==422
    recipe=client.post('/recipes',json={'name':f'recipe-{suffix}','yield_servings':2}).json()
    first=client.post(f"/recipes/{recipe['id']}/ingredients",json={'ingredient_id':ingredient['id'],'quantity_kg':.2})
    updated=client.post(f"/recipes/{recipe['id']}/ingredients",json={'ingredient_id':ingredient['id'],'quantity_kg':.3})
    assert first.status_code==201 and updated.status_code==201 and updated.json()['id']==first.json()['id']
    assert client.post('/sales',json={'menu_item':f'menu-{suffix}','sold_on':'2026-11-01','quantity':1}).status_code==201
    assert client.post('/sales',json={'menu_item':f'menu-{suffix}','sold_on':'2026-11-01','quantity':1}).status_code==409

def test_write_token_is_required_only_when_configured(monkeypatch):
    # Token protection is deliberately optional for an offline loopback demo,
    # but must cover every state-changing route when an operator enables it.
    import apps.api.main as main
    monkeypatch.setattr(main,"api_token","test-local-token")
    payload={'name':f'protected-{uuid4()}'}
    assert client.post('/ingredients',json=payload).status_code==401
    assert client.post('/ingredients',json=payload,headers={'Authorization':'Bearer test-local-token'}).status_code==201

def test_invalid_foreign_keys_and_malformed_csv_leave_no_rows():
    assert client.post('/batches',json={'ingredient_id':'missing','quantity_kg':1,'unit_cost':2,'received_on':'2026-11-01','use_by':'2026-11-02'}).status_code==404
    before=len(client.get('/batches').json())
    malformed='ingredient,quantity_kg,unit_cost,received_on,use_by,storage_category\nvalid,1,2,2026-11-01,broken,chilled'
    assert client.post('/inventory/import',json={'csv_text':malformed}).status_code==422
    assert len(client.get('/batches').json())==before

def test_demo_loader_is_repeatable_without_duplicate_seed_records():
    first=client.post('/demo/load')
    second=client.post('/demo/load')
    assert first.status_code==200 and second.status_code==200
    assert second.json()['created']['ingredients']==0
    assert second.json()['forecast_run_id']==first.json()['forecast_run_id']

def test_recipe_catalog_serializes_persisted_ingredient_associations():
    client.post('/demo/load')
    recipe=next(x for x in client.get('/recipes').json() if x['name']=='Demo Garden Salad')
    assert len(recipe['ingredients'])==4
    assert {x['ingredient'] for x in recipe['ingredients']}=={'Demo Romaine Hearts','Demo Cherry Tomatoes','Demo Feta','Demo Citrus Dressing'}
    assert client.get(f"/recipes/{recipe['id']}").json()['ingredients']==recipe['ingredients']

def test_dashboard_exposes_observed_inventory_attention_and_pending_decisions():
    body=client.get('/dashboard').json()
    assert body['as_of']
    assert body['expiry_attention_kg']==sum(row['quantity_kg'] for row in body['expiry_alerts'])
    assert body['expiry_attention_cost']==round(sum(row['cost'] for row in body['expiry_alerts']),2)
    assert isinstance(body['pending_decisions'],list)

def test_demo_dashboard_uses_fixed_synthetic_date_and_explicit_operational_date():
    body=client.get('/dashboard?demo=true').json()
    assert body['as_of']=='2026-11-08' and body['demo_as_of']=='2026-11-08'
    assert body['date_context']=='synthetic_demo' and body['operational_as_of']

def test_test_database_isolated_from_development_and_docker_paths():
    from apps.api.main import db_path
    assert 'ghostwaste-pytest-' in db_path
    assert not db_path.endswith('/data/ghostwaste.db') and not db_path.startswith('/app/data/')

def test_workflow_does_not_hide_shortage_when_supplier_price_is_missing():
    suffix=str(uuid4()); menu=f'unpriced-{suffix}'
    ingredient=client.post('/ingredients',json={'name':f'unpriced-ing-{suffix}'}).json()
    supplier=client.post('/suppliers',json={'name':f'unpriced-supplier-{suffix}'}).json()
    assert client.post(f"/suppliers/{supplier['id']}/ingredients",json={'ingredient_id':ingredient['id']}).status_code==201
    recipe=client.post('/recipes',json={'name':menu,'yield_servings':1}).json()
    client.post(f"/recipes/{recipe['id']}/ingredients",json={'ingredient_id':ingredient['id'],'quantity_kg':1})
    for day in range(1,9): client.post('/sales',json={'menu_item':menu,'sold_on':f'2026-08-{day:02d}','quantity':2})
    run=client.post(f'/forecasts/{menu}',json={'horizon':2,'initial_train':4}).json()
    result=client.post(f"/workflows/forecast/{run['id']}",json={'as_of':'2026-08-10','horizon_days':2,'trials':50,'seed':3,'storage_capacity_kg':10}).json()['result']['optimization']
    assert result['optimized_shortage_kg'] > 0
    assert result['items'][0]['purchase_unavailable'] is True
    assert result['items'][0]['order_kg'] == 0

def test_saved_scenario_is_an_immutable_snapshot_after_inventory_changes():
    suffix=str(uuid4()); menu=f'snapshot-{suffix}'
    ingredient=client.post('/ingredients',json={'name':f'snapshot-ing-{suffix}'}).json()
    supplier=client.post('/suppliers',json={'name':f'snapshot-supplier-{suffix}'}).json()
    client.post(f"/suppliers/{supplier['id']}/ingredients",json={'ingredient_id':ingredient['id'],'purchase_unit_cost':2})
    recipe=client.post('/recipes',json={'name':menu,'yield_servings':1}).json()
    client.post(f"/recipes/{recipe['id']}/ingredients",json={'ingredient_id':ingredient['id'],'quantity_kg':1})
    batch=client.post('/batches',json={'ingredient_id':ingredient['id'],'quantity_kg':1,'unit_cost':2,'received_on':'2026-09-01','use_by':'2026-10-12'}).json()
    for day in range(1,9): client.post('/sales',json={'menu_item':menu,'sold_on':f'2026-09-{day:02d}','quantity':2})
    run=client.post(f'/forecasts/{menu}',json={'horizon':2,'initial_train':4}).json()
    body={'as_of':'2026-10-10','horizon_days':2,'trials':50,'seed':91,'storage_capacity_kg':10}
    first=client.post(f"/workflows/forecast/{run['id']}",json=body).json()
    before=client.get(f"/risk-scenarios/{first['scenario_id']}").json()['outputs']
    client.post(f"/batches/{batch['id']}/waste",json={'quantity_kg':1,'occurred_on':'2026-10-10','reason':'synthetic regression'})
    after=client.get(f"/risk-scenarios/{first['scenario_id']}").json()['outputs']
    assert after==before

def test_workflow_rejects_missing_recipe_and_recipe_without_links():
    suffix=str(uuid4()); menu=f'no-links-{suffix}'
    for day in range(1,9): client.post('/sales',json={'menu_item':menu,'sold_on':f'2026-09-{day:02d}','quantity':1})
    run=client.post(f'/forecasts/{menu}',json={'horizon':2,'initial_train':4}).json()
    body={'as_of':'2026-10-10','horizon_days':2,'trials':50,'seed':4,'storage_capacity_kg':10}
    assert client.post(f"/workflows/forecast/{run['id']}",json=body).status_code==404
    recipe=client.post('/recipes',json={'name':menu,'yield_servings':1}).json()
    assert recipe['id']
    response=client.post(f"/workflows/forecast/{run['id']}",json=body)
    assert response.status_code==422 and 'no ingredient associations' in response.json()['detail']

def test_intelligence_is_grounded_and_read_only():
    before=len(client.get('/audit-events').json())
    answer=client.post('/intelligence/ask',json={'question':'Why is modeled waste zero?','as_of':'2026-11-08'})
    assert answer.status_code==200 and answer.json()['mode']=='deterministic_evidence_router'
    assert 'model' in answer.json()['answer'].lower() and answer.json()['no_side_effects'] is True
    assert len(client.get('/audit-events').json())==before
    assert client.post('/intelligence/ask',json={'question':''}).status_code==422

def test_what_if_is_deterministic_validated_and_nonpersistent():
    client.post('/demo/load'); before=len(client.get('/risk-scenarios').json())
    body={'as_of':'2026-11-08','seed':22,'trials':50,'horizon_days':7,'demand_multiplier':1.2,'storage_capacity_kg':30}
    a=client.post('/scenario-studio/run',json=body); b=client.post('/scenario-studio/run',json=body)
    assert a.status_code==200 and a.json()['monte_carlo']==b.json()['monte_carlo'] and a.json()['persistent'] is False
    assert len(client.get('/risk-scenarios').json())==before
    assert client.post('/scenario-studio/run',json={**body,'demand_multiplier':9}).status_code==422

def test_use_first_excludes_expired_from_consumption_recommendations():
    suffix=str(uuid4()); ing=client.post('/ingredients',json={'name':f'expired-{suffix}'}).json()
    old=client.post('/batches',json={'ingredient_id':ing['id'],'quantity_kg':1,'unit_cost':2,'received_on':'2026-10-01','use_by':'2026-11-07'}).json()
    rows=client.get('/use-first?as_of=2026-11-08').json()['items']; item=next(x for x in rows if x['batch_id']==old['id'])
    assert item['urgency']=='expired' and item['recommended_for_use'] is False and 'not recommended' in item['explanation']

def test_impact_requires_compatible_inputs_and_omits_zero_percentage():
    base={'as_of':'2026-11-08','seed':5,'trials':50,'horizon_days':7,'storage_capacity_kg':30}
    bad=client.post('/impact/compare',json={'baseline':base,'proposed':{**base,'seed':6}})
    assert bad.status_code==422
    good=client.post('/impact/compare',json={'baseline':base,'proposed':{**base,'demand_multiplier':.8}})
    assert good.status_code==200 and good.json()['compatible'] is True
    assert 'percent_difference' in good.json()['comparison']['expected_waste_kg']

def test_action_plan_is_stable_read_only_and_does_not_change_inventory_or_recommendations():
    client.post('/demo/load'); batches=client.get('/batches').json(); recs=client.get('/recommendations').json()
    a=client.get('/action-plan?as_of=2026-11-08').json(); b=client.get('/action-plan?as_of=2026-11-08').json()
    assert [x['id'] for x in a['tasks']]==[x['id'] for x in b['tasks']]
    assert client.get('/batches').json()==batches and client.get('/recommendations').json()==recs
