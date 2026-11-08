"""GhostWaste local demo API — synthetic results are not food-safety advice."""
from __future__ import annotations
from datetime import date, datetime, timedelta
import csv
import os
import json
from io import StringIO
from typing import Literal
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from apps.api.engines import Batch as SimBatch, monte_carlo_risk, optimize_purchase, optimize_multi_ingredient, moving_average, seasonal_naive, lightgbm_forecast, rolling_origin_backtest

db_path=os.environ.get("GHOSTWASTE_DB_PATH","./data/ghostwaste.db")
os.makedirs(os.path.dirname(db_path) or ".",exist_ok=True)
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
class IngredientDB(Base):
    __tablename__="ingredients"; id:Mapped[str]=mapped_column(String,primary_key=True); name:Mapped[str]=mapped_column(String,unique=True,index=True); unit:Mapped[str]=mapped_column(String,default="kg"); storage_category:Mapped[str]=mapped_column(String,default="chilled"); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); batches:Mapped[list["BatchDB"]]=relationship(back_populates="ingredient")
class BatchDB(Base):
    __tablename__="inventory_batches"; id:Mapped[str]=mapped_column(String,primary_key=True); ingredient_id:Mapped[str]=mapped_column(ForeignKey("ingredients.id"),index=True); quantity_kg:Mapped[float]=mapped_column(Float); unit_cost:Mapped[float]=mapped_column(Float); received_on:Mapped[date]=mapped_column(Date); use_by:Mapped[date]=mapped_column(Date,index=True); ingredient:Mapped[IngredientDB]=relationship(back_populates="batches")
class DailySaleDB(Base):
    __tablename__="daily_sales"; id:Mapped[int]=mapped_column(Integer,primary_key=True); menu_item:Mapped[str]=mapped_column(String,index=True); sold_on:Mapped[date]=mapped_column(Date,index=True); quantity:Mapped[float]=mapped_column(Float)
class RecommendationDB(Base):
    __tablename__="recommendations"; id:Mapped[str]=mapped_column(String,primary_key=True); title:Mapped[str]=mapped_column(String); status:Mapped[str]=mapped_column(String,default="pending",index=True); estimated_kg:Mapped[float]=mapped_column(Float,default=0); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class AuditEventDB(Base):
    __tablename__="audit_events"; id:Mapped[int]=mapped_column(Integer,primary_key=True); event_type:Mapped[str]=mapped_column(String,index=True); detail:Mapped[str]=mapped_column(String); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class SupplierDB(Base):
    __tablename__="suppliers"; id:Mapped[str]=mapped_column(String,primary_key=True); name:Mapped[str]=mapped_column(String,unique=True,index=True); lead_days:Mapped[int]=mapped_column(Integer,default=0); minimum_order_kg:Mapped[float]=mapped_column(Float,default=0)
class RecipeDB(Base):
    __tablename__="recipes"; id:Mapped[str]=mapped_column(String,primary_key=True); name:Mapped[str]=mapped_column(String,unique=True,index=True); yield_servings:Mapped[float]=mapped_column(Float,default=1)
class RecipeIngredientDB(Base):
    __tablename__="recipe_ingredients"; id:Mapped[int]=mapped_column(Integer,primary_key=True); recipe_id:Mapped[str]=mapped_column(ForeignKey("recipes.id"),index=True); ingredient_id:Mapped[str]=mapped_column(ForeignKey("ingredients.id"),index=True); quantity_kg:Mapped[float]=mapped_column(Float)
class ConsumptionEventDB(Base):
    __tablename__="consumption_events"; id:Mapped[str]=mapped_column(String,primary_key=True); batch_id:Mapped[str]=mapped_column(ForeignKey("inventory_batches.id"),index=True); quantity_kg:Mapped[float]=mapped_column(Float); occurred_on:Mapped[date]=mapped_column(Date); note:Mapped[str]=mapped_column(String,default="")
class WasteEventDB(Base):
    __tablename__="waste_events"; id:Mapped[str]=mapped_column(String,primary_key=True); batch_id:Mapped[str]=mapped_column(ForeignKey("inventory_batches.id"),index=True); quantity_kg:Mapped[float]=mapped_column(Float); occurred_on:Mapped[date]=mapped_column(Date); reason:Mapped[str]=mapped_column(String)
class ForecastRunDB(Base):
    __tablename__="forecast_runs"; id:Mapped[str]=mapped_column(String,primary_key=True); menu_item:Mapped[str]=mapped_column(String,index=True); model:Mapped[str]=mapped_column(String); metrics_json:Mapped[str]=mapped_column(String); predictions_json:Mapped[str]=mapped_column(String); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class ForecastPredictionDB(Base):
    __tablename__="forecast_predictions"; id:Mapped[int]=mapped_column(Integer,primary_key=True); forecast_run_id:Mapped[str]=mapped_column(ForeignKey("forecast_runs.id"),index=True); predicted_for:Mapped[date]=mapped_column(Date,index=True); quantity:Mapped[float]=mapped_column(Float); low:Mapped[float]=mapped_column(Float); high:Mapped[float]=mapped_column(Float)

class BatchInput(BaseModel):
    id:str; ingredient:str=Field(min_length=1,max_length=120); quantity_kg:float=Field(ge=0); use_by:date; unit_cost:float=Field(ge=0); received_on:date|None=None
class Demand(BaseModel): ingredient:str; expected_daily_kg:float=Field(ge=0)
class Scenario(BaseModel):
    batches:list[BatchInput]=Field(max_length=500); demand:list[Demand]=Field(max_length=500); as_of:date; reduction_fraction:float=Field(default=0,ge=0,le=1)
    @model_validator(mode="after")
    def validate_unique(self):
        if len({b.id for b in self.batches}) != len(self.batches): raise ValueError("Batch IDs must be unique")
        if len({d.ingredient.lower() for d in self.demand}) != len(self.demand): raise ValueError("Demand ingredients must be unique")
        return self
class Risk(BaseModel): batch_id:str; ingredient:str; at_risk_kg:float; potential_cost:float; days_until_use_by:int
class Result(BaseModel): provenance:Literal["synthetic_scenario"]="synthetic_scenario"; risks:list[Risk]; total_at_risk_kg:float; total_potential_cost:float; assumptions:list[str]
class IngredientIn(BaseModel): name:str=Field(min_length=1,max_length=120); unit:Literal["kg"]="kg"; storage_category:Literal["ambient","chilled","frozen"]="chilled"
class BatchCreate(BaseModel): ingredient_id:str; quantity_kg:float=Field(gt=0); unit_cost:float=Field(ge=0); received_on:date; use_by:date
class SaleIn(BaseModel): menu_item:str=Field(min_length=1); sold_on:date; quantity:float=Field(ge=0)
class DecisionIn(BaseModel): decision:Literal["accepted","rejected"]; reason:str=Field(default="",max_length=500)
class SupplierIn(BaseModel): name:str=Field(min_length=1,max_length=120); lead_days:int=Field(default=0,ge=0,le=365); minimum_order_kg:float=Field(default=0,ge=0)
class RecipeIn(BaseModel): name:str=Field(min_length=1,max_length=120); yield_servings:float=Field(gt=0)
class RecipeIngredientIn(BaseModel): ingredient_id:str; quantity_kg:float=Field(gt=0)
class StockEventIn(BaseModel): quantity_kg:float=Field(gt=0); occurred_on:date; note:str=Field(default="",max_length=250); reason:str=Field(default="",max_length=120)
class InventoryCsvIn(BaseModel): csv_text:str=Field(min_length=1,max_length=1_000_000)
class RiskSimulationIn(BaseModel):
    batches:list[BatchInput]; demand:list[Demand]; as_of:date; horizon_days:int=Field(default=7,ge=1,le=30); trials:int=Field(default=500,ge=50,le=5000); seed:int=42
class PurchaseOptimizeIn(BaseModel):
    available_kg:float=Field(ge=0); demand_kg:float=Field(ge=0); unit_cost:float=Field(ge=0); min_order_kg:float=Field(default=0,ge=0); max_order_kg:float=Field(default=1000,gt=0); shortage_penalty:float=Field(default=20,ge=0); waste_penalty:float=Field(default=2,ge=0)
class MultiPlanItem(BaseModel): ingredient:str; available_kg:float=Field(ge=0); demand_kg:float=Field(ge=0); unit_cost:float=Field(ge=0); lead_days:int=Field(default=0,ge=0); max_order_kg:float=Field(default=1000,ge=0); shortage_penalty:float=Field(default=20,ge=0); waste_penalty:float=Field(default=2,ge=0)
class MultiOptimizeIn(BaseModel): items:list[MultiPlanItem]=Field(min_length=1,max_length=100); horizon_days:int=Field(default=7,ge=1,le=90); storage_capacity_kg:float=Field(ge=0)
class ForecastRunIn(BaseModel): horizon:int=Field(default=7,ge=1,le=30); initial_train:int=Field(default=7,ge=3,le=365)
def db_session():
    db=SessionLocal()
    try: yield db
    finally: db.close()
def fefo_risk(s:Scenario)->Result:
    demand={d.ingredient.lower():d.expected_daily_kg for d in s.demand}; risks=[]
    for name in {b.ingredient.lower() for b in s.batches}:
        # Allocate cumulative demand to batches ordered by expiry (FEFO).
        rate=demand.get(name,0); allocated=0.0
        for b in sorted((x for x in s.batches if x.ingredient.lower()==name),key=lambda x:x.use_by):
            days=(b.use_by-s.as_of).days; capacity=max(0,days)*rate-allocated; consumed=min(b.quantity_kg,max(0,capacity)) if days>0 else 0
            allocated+=consumed; risk=round(max(0,b.quantity_kg-consumed)*(1-s.reduction_fraction),3)
            risks.append(Risk(batch_id=b.id,ingredient=b.ingredient,at_risk_kg=risk,potential_cost=round(risk*b.unit_cost,2),days_until_use_by=days))
    return Result(risks=risks,total_at_risk_kg=round(sum(x.at_risk_kg for x in risks),3),total_potential_cost=round(sum(x.potential_cost for x in risks),2),assumptions=["Synthetic inputs; no real restaurant outcome or food-safety decision","FEFO allocation across batches with constant daily ingredient demand","Use-by is a hard boundary; expired batches are never allocated","No supplier arrivals or uncertainty in this deterministic local demo"])

app=FastAPI(title="GhostWaste API",version="0.2.0")
auto_schema=os.environ.get("GHOSTWASTE_AUTO_SCHEMA","true").lower()=="true"
if auto_schema: Base.metadata.create_all(engine)
@app.on_event("startup")
def setup():
    if auto_schema: Base.metadata.create_all(engine)
@app.get("/health")
def health(): return {"status":"ok","version":"0.2.0","storage":"local SQLite"}
@app.post("/scenario",response_model=Result)
def scenario(s:Scenario): return fefo_risk(s)
@app.post("/risk/simulate")
def simulate_risk(data:RiskSimulationIn):
    result=monte_carlo_risk([SimBatch(b.id,b.ingredient,b.quantity_kg,(b.use_by-data.as_of).days,b.unit_cost) for b in data.batches],{d.ingredient:d.expected_daily_kg for d in data.demand},data.horizon_days,data.trials,data.seed)
    return {"provenance":"synthetic_scenario","result":result.__dict__,"explanation":"Monte Carlo FEFO simulation with seeded demand uncertainty. Expired batches are never allocated."}
@app.post("/optimization/purchase")
def optimize(data:PurchaseOptimizeIn):
    try: return {"provenance":"synthetic_scenario","result":optimize_purchase(**data.model_dump())}
    except ValueError as e: raise HTTPException(422,str(e))
@app.post("/optimization/multi-ingredient")
def optimize_multi(data:MultiOptimizeIn):
    try:return {"provenance":"synthetic_scenario","result":optimize_multi_ingredient([x.model_dump() for x in data.items],data.horizon_days,data.storage_capacity_kg)}
    except ValueError as e: raise HTTPException(422,str(e))
@app.get("/ingredients")
def ingredients(db:Session=Depends(db_session)): return [{"id":x.id,"name":x.name,"unit":x.unit,"storage_category":x.storage_category} for x in db.scalars(select(IngredientDB).order_by(IngredientDB.name))]
@app.post("/ingredients",status_code=201)
def create_ingredient(data:IngredientIn,db:Session=Depends(db_session)):
    if db.scalar(select(IngredientDB).where(IngredientDB.name==data.name.strip())): raise HTTPException(409,"Ingredient already exists")
    x=IngredientDB(id=str(uuid4()),**data.model_dump()); db.add(x);db.commit();return {"id":x.id,**data.model_dump()}
@app.get("/batches")
def batches(db:Session=Depends(db_session)): return [{"id":x.id,"ingredient":x.ingredient.name,"quantity_kg":x.quantity_kg,"unit_cost":x.unit_cost,"received_on":x.received_on,"use_by":x.use_by} for x in db.scalars(select(BatchDB).join(BatchDB.ingredient).order_by(BatchDB.use_by))]
@app.post("/batches",status_code=201)
def create_batch(data:BatchCreate,db:Session=Depends(db_session)):
    if data.use_by<data.received_on: raise HTTPException(422,"Use-by date cannot precede received date")
    if not db.get(IngredientDB,data.ingredient_id): raise HTTPException(404,"Ingredient not found")
    x=BatchDB(id=str(uuid4()),**data.model_dump());db.add(x);db.commit();return {"id":x.id,**data.model_dump()}
def safe_csv(value:object)->str:
    value=str(value)
    return "'"+value if value[:1] in ("=","+","-","@") else value
UNIT_TO_KG={"kg":1.0,"g":0.001,"lb":0.45359237,"oz":0.028349523125}
def to_kg(quantity:float,unit:str)->float:
    if unit.lower() not in UNIT_TO_KG: raise ValueError(f"unsupported unit {unit}")
    return round(quantity*UNIT_TO_KG[unit.lower()],6)
@app.get("/inventory/export.csv")
def export_inventory(db:Session=Depends(db_session)):
    stream=StringIO(); writer=csv.writer(stream);writer.writerow(["batch_id","ingredient","quantity_kg","unit_cost","received_on","use_by"])
    for b in db.scalars(select(BatchDB).join(BatchDB.ingredient).order_by(BatchDB.use_by)):
        writer.writerow([safe_csv(b.id),safe_csv(b.ingredient.name),b.quantity_kg,b.unit_cost,b.received_on,b.use_by])
    return Response(stream.getvalue(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=ghostwaste-inventory.csv"})
@app.post("/inventory/import")
def import_inventory(data:InventoryCsvIn,db:Session=Depends(db_session)):
    try:
        rows=list(csv.DictReader(StringIO(data.csv_text)))
    except csv.Error as e: raise HTTPException(422,f"Invalid CSV: {e}")
    required={"ingredient","quantity_kg","unit_cost","received_on","use_by","storage_category"}
    if not rows or not rows[0] or not required.issubset(rows[0]): raise HTTPException(422,"CSV requires ingredient, quantity_kg, unit_cost, received_on, use_by, storage_category")
    staged=[]
    try:
        for i,row in enumerate(rows,2):
            name=row["ingredient"].strip()
            if not name or name[0] in "=+-@": raise ValueError(f"row {i}: unsafe or missing ingredient")
            quantity=to_kg(float(row["quantity_kg"]),row.get("unit","kg")); cost=float(row["unit_cost"]); received=date.fromisoformat(row["received_on"]); use_by=date.fromisoformat(row["use_by"]); category=row["storage_category"].strip()
            if quantity<=0 or cost<0 or use_by<received or category not in {"ambient","chilled","frozen"}: raise ValueError(f"row {i}: invalid values")
            staged.append((name,quantity,cost,received,use_by,category))
    except (ValueError,KeyError) as e: raise HTTPException(422,f"CSV validation failed: {e}")
    try:
        imported=skipped=0
        for name,quantity,cost,received,use_by,category in staged:
            ingredient=db.scalar(select(IngredientDB).where(IngredientDB.name==name))
            if not ingredient:
                ingredient=IngredientDB(id=str(uuid4()),name=name,unit="kg",storage_category=category);db.add(ingredient);db.flush()
            duplicate=db.scalar(select(BatchDB).where(BatchDB.ingredient_id==ingredient.id,BatchDB.quantity_kg==quantity,BatchDB.unit_cost==cost,BatchDB.received_on==received,BatchDB.use_by==use_by))
            if duplicate: skipped+=1;continue
            db.add(BatchDB(id=str(uuid4()),ingredient_id=ingredient.id,quantity_kg=quantity,unit_cost=cost,received_on=received,use_by=use_by));imported+=1
        db.add(AuditEventDB(event_type="inventory_import",detail=f"{imported} imported; {skipped} duplicates skipped"));db.commit()
    except Exception:
        db.rollback();raise HTTPException(409,"Import rolled back; no inventory was changed")
    return {"imported_batches":imported,"skipped_duplicates":skipped,"provenance":"csv_user_input"}
@app.get("/suppliers")
def suppliers(db:Session=Depends(db_session)): return [{"id":x.id,"name":x.name,"lead_days":x.lead_days,"minimum_order_kg":x.minimum_order_kg} for x in db.scalars(select(SupplierDB).order_by(SupplierDB.name))]
@app.post("/suppliers",status_code=201)
def create_supplier(data:SupplierIn,db:Session=Depends(db_session)):
    if db.scalar(select(SupplierDB).where(SupplierDB.name==data.name.strip())): raise HTTPException(409,"Supplier already exists")
    x=SupplierDB(id=str(uuid4()),**data.model_dump());db.add(x);db.commit();return {"id":x.id,**data.model_dump()}
@app.post("/recipes",status_code=201)
def create_recipe(data:RecipeIn,db:Session=Depends(db_session)):
    if db.scalar(select(RecipeDB).where(RecipeDB.name==data.name.strip())): raise HTTPException(409,"Recipe already exists")
    x=RecipeDB(id=str(uuid4()),**data.model_dump());db.add(x);db.commit();return {"id":x.id,**data.model_dump()}
@app.post("/recipes/{recipe_id}/ingredients",status_code=201)
def add_recipe_ingredient(recipe_id:str,data:RecipeIngredientIn,db:Session=Depends(db_session)):
    if not db.get(RecipeDB,recipe_id) or not db.get(IngredientDB,data.ingredient_id): raise HTTPException(404,"Recipe or ingredient not found")
    x=RecipeIngredientDB(recipe_id=recipe_id,**data.model_dump());db.add(x);db.commit();return {"id":x.id,"recipe_id":recipe_id,**data.model_dump()}
def record_stock_event(batch_id:str,data:StockEventIn,event_type:str,db:Session):
    batch=db.get(BatchDB,batch_id)
    if not batch: raise HTTPException(404,"Batch not found")
    if event_type=="consumption":
        if batch.quantity_kg<data.quantity_kg: raise HTTPException(409,"Insufficient stock; negative inventory prevented")
        batch.quantity_kg-=data.quantity_kg;x=ConsumptionEventDB(id=str(uuid4()),batch_id=batch_id,quantity_kg=data.quantity_kg,occurred_on=data.occurred_on,note=data.note)
    else:
        if batch.quantity_kg<data.quantity_kg: raise HTTPException(409,"Waste exceeds available stock")
        batch.quantity_kg-=data.quantity_kg;x=WasteEventDB(id=str(uuid4()),batch_id=batch_id,quantity_kg=data.quantity_kg,occurred_on=data.occurred_on,reason=data.reason or "unspecified")
    db.add(x);db.add(AuditEventDB(event_type=event_type,detail=f"{batch_id}: {data.quantity_kg} kg"));db.commit();return {"batch_id":batch_id,"remaining_kg":batch.quantity_kg,"event_id":x.id}
@app.post("/batches/{batch_id}/consume")
def consume(batch_id:str,data:StockEventIn,db:Session=Depends(db_session)): return record_stock_event(batch_id,data,"consumption",db)
@app.post("/batches/{batch_id}/waste")
def waste(batch_id:str,data:StockEventIn,db:Session=Depends(db_session)): return record_stock_event(batch_id,data,"waste",db)
@app.post("/sales",status_code=201)
def create_sale(data:SaleIn,db:Session=Depends(db_session)):
    x=DailySaleDB(**data.model_dump());db.add(x);db.commit();return {"id":x.id,**data.model_dump()}
@app.get("/forecast/{menu_item}")
def forecast(menu_item:str,horizon:int=7,db:Session=Depends(db_session)):
    if not 1<=horizon<=30: raise HTTPException(422,"Horizon must be 1–30 days")
    history=list(db.scalars(select(DailySaleDB).where(DailySaleDB.menu_item==menu_item).order_by(DailySaleDB.sold_on)))
    if not history: raise HTTPException(404,"No sales history for menu item")
    values=[x.quantity for x in history]; prediction=round(sum(values[-7:])/min(7,len(values)),2); start=history[-1].sold_on+timedelta(days=1)
    return {"provenance":"observed_local_demo_sales","model":"moving_average_7_or_less","training_points":len(values),"predictions":[{"date":str(start+timedelta(days=i)),"quantity":prediction,"low":round(max(0,prediction*.7),2),"high":round(prediction*1.3,2)} for i in range(horizon)],"limitations":"Baseline only; chronological backtesting required before operational use."}
@app.post("/forecasts/{menu_item}",status_code=201)
def create_forecast_run(menu_item:str,data:ForecastRunIn,db:Session=Depends(db_session)):
    history=list(db.scalars(select(DailySaleDB).where(DailySaleDB.menu_item==menu_item).order_by(DailySaleDB.sold_on)))
    values=[x.quantity for x in history]
    if len(values)<=data.initial_train: raise HTTPException(422,"Insufficient chronological sales history")
    evaluation=rolling_origin_backtest(values,data.initial_train); model=evaluation["selected_model"]
    predicted=(moving_average(values,data.horizon) if model=="moving_average" else seasonal_naive(values,data.horizon) if model=="seasonal_naive" else lightgbm_forecast(values,data.horizon))
    width=evaluation["interval_half_width"];start=history[-1].sold_on+timedelta(days=1); forecasts=[{"date":str(start+timedelta(days=i)),"quantity":q,"low":round(max(0,q-width),2),"high":round(q+width,2)} for i,q in enumerate(predicted)]
    run=ForecastRunDB(id=str(uuid4()),menu_item=menu_item,model=model,metrics_json=json.dumps(evaluation["models"]),predictions_json=json.dumps(forecasts));db.add(run);db.flush()
    for item in forecasts: db.add(ForecastPredictionDB(forecast_run_id=run.id,predicted_for=date.fromisoformat(item["date"]),quantity=item["quantity"],low=item["low"],high=item["high"]))
    db.commit()
    return {"id":run.id,"menu_item":menu_item,"model":model,"training_points":len(values),"evaluation":evaluation,"predictions":forecasts,"provenance":"local_demo_sales","limitations":"Baseline models only; results are not restaurant pilot metrics."}
@app.get("/forecasts/{menu_item}/history")
def forecast_history(menu_item:str,db:Session=Depends(db_session)):
    return [{"id":x.id,"model":x.model,"metrics":json.loads(x.metrics_json),"predictions":json.loads(x.predictions_json),"created_at":x.created_at} for x in db.scalars(select(ForecastRunDB).where(ForecastRunDB.menu_item==menu_item).order_by(ForecastRunDB.created_at.desc()))]
@app.get("/forecasts/{run_id}/ingredient-demand")
def ingredient_demand(run_id:str,db:Session=Depends(db_session)):
    run=db.get(ForecastRunDB,run_id)
    if not run: raise HTTPException(404,"Forecast run not found")
    recipe=db.scalar(select(RecipeDB).where(RecipeDB.name==run.menu_item))
    if not recipe: raise HTTPException(404,"No recipe named for this menu item")
    servings=sum(x["quantity"] for x in json.loads(run.predictions_json))
    rows=list(db.scalars(select(RecipeIngredientDB).where(RecipeIngredientDB.recipe_id==recipe.id)))
    demands=[]
    for row in rows:
        ingredient=db.get(IngredientDB,row.ingredient_id)
        demands.append({"ingredient":ingredient.name,"required_kg":round(servings/recipe.yield_servings*row.quantity_kg,4)})
    return {"forecast_run_id":run_id,"recipe":recipe.name,"forecast_servings":servings,"ingredient_demand":demands,"provenance":"forecast_plus_recipe","assumptions":["Recipe name equals menu item", "Recipe yield is fixed", "All ingredient quantities are canonical kilograms"]}
@app.post("/recommendations/from-scenario")
def recommend(s:Scenario,db:Session=Depends(db_session)):
    result=fefo_risk(s); items=[]
    for risk in result.risks:
        if risk.at_risk_kg>0:
            x=RecommendationDB(id=str(uuid4()),title=f"Review FEFO use of {risk.ingredient} batch {risk.batch_id}",estimated_kg=risk.at_risk_kg);db.add(x);items.append({"id":x.id,"title":x.title,"estimated_kg":x.estimated_kg,"status":"pending"})
    db.add(AuditEventDB(event_type="recommendations_generated",detail=f"{len(items)} synthetic scenario recommendations"));db.commit();return {"recommendations":items,"provenance":"synthetic_scenario","warning":"Manager approval required; no external action is executed."}
@app.post("/recommendations/{recommendation_id}/decision")
def decide(recommendation_id:str,data:DecisionIn,db:Session=Depends(db_session)):
    x=db.get(RecommendationDB,recommendation_id)
    if not x: raise HTTPException(404,"Recommendation not found")
    x.status=data.decision;db.add(AuditEventDB(event_type="recommendation_"+data.decision,detail=f"{recommendation_id}: {data.reason}"));db.commit();return {"id":x.id,"status":x.status,"reason":data.reason}
