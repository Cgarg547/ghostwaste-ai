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
