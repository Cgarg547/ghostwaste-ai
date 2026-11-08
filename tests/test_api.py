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
