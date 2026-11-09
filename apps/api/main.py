"""GhostWaste local demo API — synthetic results are not food-safety advice."""
from __future__ import annotations
from datetime import date, datetime, timedelta
import csv
import os
import json
import hmac
from io import StringIO
from pathlib import Path
from typing import Literal
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from apps.api.engines import Batch as SimBatch, monte_carlo_risk, optimize_purchase, optimize_multi_ingredient, moving_average, seasonal_naive, lightgbm_forecast, rolling_origin_backtest, independent_interval_coverage

DEMO_DATE=date(2026,11,8)
staging_mode=os.environ.get("GHOSTWASTE_STAGING_MODE","false").lower() in {"1","true","yes"}
if staging_mode:
    required={"GHOSTWASTE_DB_PATH":os.environ.get("GHOSTWASTE_DB_PATH",""),"GHOSTWASTE_API_TOKEN":os.environ.get("GHOSTWASTE_API_TOKEN","")}
    missing=[name for name,value in required.items() if not value]
    if missing: raise RuntimeError(f"Staging configuration missing: {', '.join(missing)}")
    if os.environ.get("GHOSTWASTE_AUTO_SCHEMA","false").lower()=="true": raise RuntimeError("Staging requires reviewed Alembic migrations; auto schema is disabled.")
    if os.environ.get("GHOSTWASTE_ENABLE_DOCS","false").lower()=="true": raise RuntimeError("Staging API docs must be disabled.")
def _database_path():
    """Select SQLite storage while refusing development and Docker stores in tests."""
    configured=os.environ.get("GHOSTWASTE_DB_PATH")
    testing=os.environ.get("GHOSTWASTE_TESTING","").lower() in {"1","true","yes"}
    if testing and not configured: raise RuntimeError("Tests require GHOSTWASTE_DB_PATH before application import.")
    resolved=Path(configured or "./data/ghostwaste.db").expanduser().resolve()
    protected={Path("./data/ghostwaste.db").resolve(),Path("/app/data/ghostwaste.db").resolve()}
    # Test harnesses must use an explicitly namespaced temporary parent.  This
    # permits both pytest and the standalone browser E2E runner while refusing
    # development and Docker locations.
    safe_test_parent=("ghostwaste-pytest-" in str(resolved.parent) or "ghostwaste-e2e-" in str(resolved.parent))
    if testing and (resolved in protected or "/app/data/" in f"{resolved}/" or not safe_test_parent):
        raise RuntimeError(f"Refusing protected database path during tests: {resolved}")
    resolved.parent.mkdir(parents=True,exist_ok=True)
    return str(resolved)
db_path=_database_path()
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(connection, _):
    # SQLite does not enforce declared relationships unless this is enabled for
    # every connection.  API validation remains friendlier, while this protects
    # against orphaned rows from any future code path.
    connection.execute("PRAGMA foreign_keys=ON")
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
class IngredientDB(Base):
    __tablename__="ingredients"; id:Mapped[str]=mapped_column(String,primary_key=True); name:Mapped[str]=mapped_column(String,unique=True,index=True); unit:Mapped[str]=mapped_column(String,default="kg"); storage_category:Mapped[str]=mapped_column(String,default="chilled"); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); batches:Mapped[list["BatchDB"]]=relationship(back_populates="ingredient")
class BatchDB(Base):
    __tablename__="inventory_batches"; id:Mapped[str]=mapped_column(String,primary_key=True); ingredient_id:Mapped[str]=mapped_column(ForeignKey("ingredients.id"),index=True); quantity_kg:Mapped[float]=mapped_column(Float); unit_cost:Mapped[float]=mapped_column(Float); received_on:Mapped[date]=mapped_column(Date); use_by:Mapped[date]=mapped_column(Date,index=True); ingredient:Mapped[IngredientDB]=relationship(back_populates="batches")
class DailySaleDB(Base):
    __tablename__="daily_sales"
    __table_args__=(UniqueConstraint("menu_item","sold_on",name="uq_daily_sales_menu_item_sold_on"),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True); menu_item:Mapped[str]=mapped_column(String,index=True); sold_on:Mapped[date]=mapped_column(Date,index=True); quantity:Mapped[float]=mapped_column(Float)
class RecommendationDB(Base):
    __tablename__="recommendations"; id:Mapped[str]=mapped_column(String,primary_key=True); title:Mapped[str]=mapped_column(String); status:Mapped[str]=mapped_column(String,default="pending",index=True); estimated_kg:Mapped[float]=mapped_column(Float,default=0); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class AuditEventDB(Base):
    __tablename__="audit_events"; id:Mapped[int]=mapped_column(Integer,primary_key=True); event_type:Mapped[str]=mapped_column(String,index=True); detail:Mapped[str]=mapped_column(String); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class SupplierDB(Base):
    __tablename__="suppliers"; id:Mapped[str]=mapped_column(String,primary_key=True); name:Mapped[str]=mapped_column(String,unique=True,index=True); lead_days:Mapped[int]=mapped_column(Integer,default=0); minimum_order_kg:Mapped[float]=mapped_column(Float,default=0)
class SupplierIngredientDB(Base):
    """Explicit availability and price; a supplier is never inferred for an ingredient."""
    __tablename__="supplier_ingredients"; id:Mapped[int]=mapped_column(Integer,primary_key=True); supplier_id:Mapped[str]=mapped_column(ForeignKey("suppliers.id"),index=True); ingredient_id:Mapped[str]=mapped_column(ForeignKey("ingredients.id"),index=True); purchase_unit_cost:Mapped[float|None]=mapped_column(Float,nullable=True)
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
class RiskScenarioDB(Base):
    __tablename__="risk_scenarios"; id:Mapped[str]=mapped_column(String,primary_key=True); forecast_run_id:Mapped[str]=mapped_column(ForeignKey("forecast_runs.id"),index=True); seed:Mapped[int]=mapped_column(Integer); inputs_json:Mapped[str]=mapped_column(String); outputs_json:Mapped[str]=mapped_column(String); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

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
class DecisionIn(BaseModel): decision:Literal["accepted","rejected"]; reason:str=Field(min_length=3,max_length=500)
class SupplierIn(BaseModel): name:str=Field(min_length=1,max_length=120); lead_days:int=Field(default=0,ge=0,le=365); minimum_order_kg:float=Field(default=0,ge=0)
class SupplierIngredientIn(BaseModel): ingredient_id:str; purchase_unit_cost:float|None=Field(default=None,ge=0)
class RecipeIn(BaseModel): name:str=Field(min_length=1,max_length=120); yield_servings:float=Field(gt=0)
class RecipeIngredientIn(BaseModel): ingredient_id:str; quantity_kg:float=Field(gt=0)
class StockEventIn(BaseModel): quantity_kg:float=Field(gt=0); occurred_on:date; note:str=Field(default="",max_length=250); reason:str=Field(default="",max_length=120)
class InventoryCsvIn(BaseModel): csv_text:str=Field(min_length=1,max_length=1_000_000)
class RiskSimulationIn(BaseModel):
    batches:list[BatchInput]; demand:list[Demand]; as_of:date; horizon_days:int=Field(default=7,ge=1,le=30); trials:int=Field(default=500,ge=50,le=5000); seed:int=42
class PurchaseOptimizeIn(BaseModel):
    available_kg:float=Field(ge=0); demand_kg:float=Field(ge=0); unit_cost:float=Field(ge=0); min_order_kg:float=Field(default=0,ge=0); max_order_kg:float=Field(default=1000,gt=0); shortage_penalty:float=Field(default=20,ge=0); waste_penalty:float=Field(default=2,ge=0)
class MultiPlanItem(BaseModel): ingredient:str=Field(min_length=1,max_length=120); supplier:str|None=None; available_kg:float=Field(ge=0); demand_kg:float=Field(ge=0); unit_cost:float=Field(ge=0); lead_days:int=Field(default=0,ge=0); min_order_kg:float=Field(default=0,ge=0); max_order_kg:float=Field(default=1000,ge=0); prep_hours_per_kg:float=Field(default=0,ge=0); shortage_penalty:float=Field(default=20,ge=0); waste_penalty:float=Field(default=2,ge=0)
class MultiOptimizeIn(BaseModel): items:list[MultiPlanItem]=Field(min_length=1,max_length=100); horizon_days:int=Field(default=7,ge=1,le=90); storage_capacity_kg:float=Field(ge=0); preparation_capacity_hours:float|None=Field(default=None,ge=0)
class ForecastRunIn(BaseModel): horizon:int=Field(default=7,ge=1,le=30); initial_train:int=Field(default=7,ge=3,le=365)
class WorkflowIn(BaseModel): as_of:date; horizon_days:int=Field(default=7,ge=1,le=30); trials:int=Field(default=500,ge=50,le=5000); seed:int=42; storage_capacity_kg:float=Field(default=1000,ge=0); preparation_capacity_hours:float|None=Field(default=None,ge=0)
class StudioIn(BaseModel):
    """Ephemeral what-if inputs.  This model deliberately has no persistence path."""
    as_of:date=DEMO_DATE; horizon_days:int=Field(default=7,ge=1,le=30); seed:int=Field(default=42); trials:int=Field(default=200,ge=50,le=2000)
    demand_multiplier:float=Field(default=1,ge=0,le=3); shelf_life_days_delta:int=Field(default=0,ge=-14,le=30)
    inventory_multiplier:float=Field(default=1,ge=0,le=3); planned_purchase_multiplier:float=Field(default=1,ge=0,le=3)
    lead_time_days_delta:int=Field(default=0,ge=0,le=30); storage_capacity_kg:float=Field(default=30,ge=0,le=10000)
    preparation_capacity_hours:float|None=Field(default=None,ge=0,le=10000); forecast_run_id:str|None=None
class AssistantIn(BaseModel): question:str=Field(min_length=1,max_length=600); scenario_id:str|None=None; as_of:date=DEMO_DATE
class ImpactCompareIn(BaseModel): baseline:StudioIn; proposed:StudioIn
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

def _recipe_requirements(db:Session, run_id:str|None, horizon:int)->dict[str,float]:
    """Forecast/recipe demand if available; otherwise a transparent zero-demand plan."""
    if not run_id: return {}
    run=db.get(ForecastRunDB,run_id)
    if not run: raise HTTPException(404,"Forecast run not found")
    recipe=db.scalar(select(RecipeDB).where(RecipeDB.name==run.menu_item))
    if not recipe: raise HTTPException(422,"Selected forecast has no matching recipe")
    servings=sum(x["quantity"] for x in json.loads(run.predictions_json)[:horizon])
    links=list(db.scalars(select(RecipeIngredientDB).where(RecipeIngredientDB.recipe_id==recipe.id)))
    return {db.get(IngredientDB,x.ingredient_id).name:round(servings/recipe.yield_servings*x.quantity_kg,4) for x in links}

def studio_calculation(data:StudioIn, db:Session)->dict:
    """Runs the existing FEFO, Monte Carlo and CBC engines without writing records."""
    inventory=list(db.scalars(select(BatchDB).join(BatchDB.ingredient)))
    requirements=_recipe_requirements(db,data.forecast_run_id,data.horizon_days)
    demand={k:v/data.horizon_days*data.demand_multiplier for k,v in requirements.items()}
    batches=[]
    for b in inventory:
        adjusted_use_by=b.use_by+timedelta(days=data.shelf_life_days_delta)
        batches.append(BatchInput(id=b.id,ingredient=b.ingredient.name,quantity_kg=round(b.quantity_kg*data.inventory_multiplier,4),unit_cost=b.unit_cost,use_by=adjusted_use_by,received_on=b.received_on))
    risk=fefo_risk(Scenario(batches=batches,demand=[Demand(ingredient=k,expected_daily_kg=v) for k,v in demand.items()],as_of=data.as_of))
    simulation=monte_carlo_risk([SimBatch(x.id,x.ingredient,x.quantity_kg,(x.use_by-data.as_of).days,x.unit_cost) for x in batches],demand,data.horizon_days,data.trials,data.seed).__dict__
    items=[]
    for ingredient, total_demand in requirements.items():
        available=sum(x.quantity_kg for x in batches if x.ingredient==ingredient and x.use_by>=data.as_of)
        ing=db.scalar(select(IngredientDB).where(IngredientDB.name==ingredient))
        links=list(db.scalars(select(SupplierIngredientDB).where(SupplierIngredientDB.ingredient_id==ing.id,SupplierIngredientDB.purchase_unit_cost.is_not(None)))) if ing else []
        link=min(links,key=lambda x:(x.purchase_unit_cost,x.supplier_id),default=None)
        supplier=db.get(SupplierDB,link.supplier_id) if link else None
        if supplier and link:
            items.append({"ingredient":ingredient,"supplier":supplier.name,"available_kg":available,"demand_kg":total_demand*data.demand_multiplier,"unit_cost":link.purchase_unit_cost,"lead_days":supplier.lead_days+data.lead_time_days_delta,"min_order_kg":supplier.minimum_order_kg,"max_order_kg":1000*data.planned_purchase_multiplier})
    plan=optimize_multi_ingredient(items,data.horizon_days,data.storage_capacity_kg,data.preparation_capacity_hours) if items else {"status":"infeasible","items":[],"warning":"No forecast-linked recipe with priced supplier inputs was available."}
    return {"scenario_id":f"ephemeral-{data.seed}-{data.as_of.isoformat()}","persistent":False,"provenance":"synthetic_ephemeral_what_if","as_of":str(data.as_of),"horizon_days":data.horizon_days,"seed":data.seed,"inputs":data.model_dump(mode="json"),"requirements_kg":requirements,"risk":risk.model_dump(),"monte_carlo":simulation,"optimization":plan,"assumptions":["Read-only calculation; no scenario, recommendation, purchase, or inventory record was created.","Shelf-life adjustment is a planning assumption, not food-safety advice.","Synthetic results are model outputs, not observed savings."]}

app=FastAPI(title="GhostWaste API",version="0.3.0",docs_url="/docs" if os.environ.get("GHOSTWASTE_ENABLE_DOCS","true").lower()=="true" else None)
allowed_hosts=[x.strip() for x in os.environ.get("GHOSTWASTE_ALLOWED_HOSTS","").split(",") if x.strip()]
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=allowed_hosts)
allowed_origins=[x.strip() for x in os.environ.get("GHOSTWASTE_CORS_ORIGINS","").split(",") if x.strip()]
if allowed_origins:
    app.add_middleware(CORSMiddleware,allow_origins=allowed_origins,allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["Authorization","Content-Type"])
api_token=os.environ.get("GHOSTWASTE_API_TOKEN","")
@app.middleware("http")
async def local_demo_access(request:Request,call_next):
    """Optional token makes the same image safe to put behind a local proxy.
    No credential is invented or embedded; unset means loopback/demo mode only.
    """
    public_health = request.url.path in {"/health", "/ready"} and request.method in {"GET", "HEAD"}
    requires_token = (
        staging_mode and not public_health
    ) or (
        not staging_mode and request.method not in {"GET", "HEAD", "OPTIONS"}
    )
    if api_token and requires_token:
        supplied=request.headers.get("authorization","").removeprefix("Bearer ")
        if not hmac.compare_digest(supplied,api_token): return Response("Unauthorized",status_code=401)
    return await call_next(request)
auto_schema=os.environ.get("GHOSTWASTE_AUTO_SCHEMA","true").lower()=="true"
if auto_schema: Base.metadata.create_all(engine)
@app.on_event("startup")
def setup():
    if auto_schema: Base.metadata.create_all(engine)
@app.get("/health")
def health(): return {"status":"ok","version":"0.3.0","storage":"local SQLite","access_mode":"token-protected" if api_token else "local-demo (set GHOSTWASTE_API_TOKEN to protect writes)"}

@app.get("/ready")
def ready(db:Session=Depends(db_session)):
    """Readiness is side-effect free and validates local SQLite connectivity."""
    try: db.execute(select(IngredientDB.id).limit(1))
    except Exception as exc: raise HTTPException(503,"Database is not ready") from exc
    return {"status":"ready","storage":"local SQLite"}

@app.post("/scenario-studio/run")
def run_scenario_studio(data:StudioIn,db:Session=Depends(db_session)):
    return studio_calculation(data,db)

@app.get("/use-first")
def use_first(as_of:date=DEMO_DATE,horizon_days:int=7,forecast_run_id:str|None=None,db:Session=Depends(db_session)):
    requirements=_recipe_requirements(db,forecast_run_id,horizon_days)
    daily={k:v/horizon_days for k,v in requirements.items()}
    rows=[]
    for batch in db.scalars(select(BatchDB).join(BatchDB.ingredient).order_by(BatchDB.use_by)):
        days=(batch.use_by-as_of).days
        # Expired stock is reported for attention but is never a use recommendation.
        expiry_factor=max(0,min(1,(horizon_days-days+1)/max(1,horizon_days)))
        forecast=min(batch.quantity_kg, daily.get(batch.ingredient.name,0)*max(0,min(horizon_days,days)))
        exposure=max(0,batch.quantity_kg-forecast)
        urgency="expired" if days<0 else "today" if days<=1 else "soon" if days<=3 else "later"
        rank=(0 if days<0 else 1, days, -exposure)
        recipes=[r.name for r in db.scalars(select(RecipeDB).join(RecipeIngredientDB).where(RecipeIngredientDB.ingredient_id==batch.ingredient_id))]
        rows.append({"batch_id":batch.id,"ingredient":batch.ingredient.name,"quantity_kg":round(batch.quantity_kg,3),"unit":"kg","use_by":str(batch.use_by),"days_until_use_by":days,"forecasted_consumption_kg":round(forecast,3),"estimated_unconsumed_kg":round(exposure,3),"urgency":urgency,"recommended_for_use":days>=0,"rank":rank,"recipes":recipes,"explanation":"Expired batch — review under local food-safety procedures; it is not recommended for consumption." if days<0 else f"FEFO priority: use-by is in {days} day(s); forecast-linked demand can consume {round(forecast,2)} kg before then."})
    rows.sort(key=lambda x:x.pop("rank"))
    return {"as_of":str(as_of),"horizon_days":horizon_days,"forecast_run_id":forecast_run_id,"items":rows,"provenance":"inventory_fefo_forecast_planning","safety_notice":"Operational planning support only; this is not a food-safety certification."}

@app.get("/action-plan")
def action_plan(as_of:date=DEMO_DATE,forecast_run_id:str|None=None,db:Session=Depends(db_session)):
    planner=use_first(as_of,7,forecast_run_id,db)
    tasks=[]
    for item in planner["items"]:
        if item["urgency"] in {"today","soon"}:
            priority="critical" if item["urgency"]=="today" else "high"
            tasks.append({"id":f"use-first:{item['batch_id']}","title":f"Review {item['ingredient']} batch first","ingredient":item["ingredient"],"priority":priority,"quantity_kg":item["quantity_kg"],"unit":"kg","time_horizon":"today" if priority=="critical" else "next 3 days","reason":item["explanation"],"source":"Use-First Planner","scenario_id":forecast_run_id,"suggested":True})
    for rec in db.scalars(select(RecommendationDB).where(RecommendationDB.status=="pending")):
        tasks.append({"id":f"recommendation:{rec.id}","title":rec.title,"ingredient":None,"priority":"high","quantity_kg":rec.estimated_kg,"unit":"kg","time_horizon":"review before ordering","reason":"Existing approval-only recommendation requires manager review.","source":"Recommendations","scenario_id":None,"suggested":True})
    tasks.sort(key=lambda x:({"critical":0,"high":1,"medium":2,"low":3}[x["priority"]],x["title"]))
    return {"as_of":str(as_of),"tasks":tasks,"provenance":"read_only_suggested_plan","notice":"Checking a task in the browser records local planning state only; it does not execute an operation, change inventory, or approve a recommendation."}

@app.post("/impact/compare")
def impact_compare(data:ImpactCompareIn,db:Session=Depends(db_session)):
    # Same snapshot/date/horizon/seed methodology is required for an impact claim.
    b,p=data.baseline,data.proposed
    compatible=(b.as_of==p.as_of and b.horizon_days==p.horizon_days and b.seed==p.seed and b.trials==p.trials and b.forecast_run_id==p.forecast_run_id)
    if not compatible: raise HTTPException(422,"Impact comparison requires matching as_of date, forecast source, horizon, seed, and trial count.")
    baseline,proposed=studio_calculation(b,db),studio_calculation(p,db)
    def change(key:str):
        before=float(baseline["monte_carlo"].get(key,0));after=float(proposed["monte_carlo"].get(key,0));return {"baseline":before,"proposed":after,"absolute_difference":round(after-before,3),"percent_difference":round((after-before)/before*100,2) if before else None}
    return {"compatible":True,"baseline":baseline,"proposed":proposed,"comparison":{"expected_waste_kg":change("expected_waste_kg"),"expected_shortage_probability":change("stockout_probability"),"waste_cost":change("cost_at_risk")},"methodology":"Compatible seeded Monte Carlo FEFO calculations on the same current inventory snapshot. Differences are simulated planning estimates, not observed savings or food rescued."}

@app.post("/intelligence/ask")
def intelligence_ask(data:AssistantIn,db:Session=Depends(db_session)):
    """Small deterministic intent router; never calls a model or mutates state."""
    q=data.question.lower(); planner=use_first(data.as_of,7,None,db); risky=[x for x in planner["items"] if x["urgency"] in {"today","soon"}]
    source={"page":"/use-first","label":"Use-First Planner"}
    if any(w in q for w in ["use first","attention","reduce waste","tomorrow"]):
        names=", ".join(x["ingredient"] for x in risky[:3]) or "no non-expired near-term batches"
        answer=f"Prioritize {names}. Ranking uses FEFO expiry dates and available forecast-linked demand; expired batches are shown for review but never recommended for consumption."
    elif "zero" in q and "waste" in q:
        answer="Modeled waste can be zero when the seeded FEFO simulation allocates forecast demand before each use-by boundary. That is a model result, not proof that no physical waste occurred.";source={"page":"/waste-radar","label":"Waste Radar"}
    elif any(w in q for w in ["optimizer","recommend","purchase","kg"]):
        answer="Purchase quantities come from the constrained CBC optimizer using forecast-linked ingredient demand, available eligible inventory, explicit supplier price/minimum, lead time, and storage capacity. It creates no order and needs manager review.";source={"page":"/impact-studio","label":"Impact Studio"}
    elif any(w in q for w in ["demand","forecast","uncertainty"]):
        answer="Forecasts are selected by rolling-origin backtesting from recorded sales. Planning ranges reflect historical residual error and are not guarantees of demand.";source={"page":"/forecasting","label":"Forecasting"}
    elif "roma" in q or "expiry" in q or "risk" in q:
        answer="Near-expiry risk is driven by the batch use-by date, quantity remaining, and forecast demand that can be allocated before that boundary. Open the planner for batch-level evidence."
    else:
        answer="I can explain use-first priorities, expiry risk, forecast uncertainty, simulated waste, and constrained purchase recommendations. Choose a suggested prompt for a grounded answer."
    return {"answer":answer,"mode":"deterministic_evidence_router","source":source,"as_of":str(data.as_of),"synthetic_data":True,"no_side_effects":True}

@app.get("/dashboard")
def dashboard(demo:bool=False,as_of:date|None=None,db:Session=Depends(db_session)):
    """Small, read-only rollup for the operational overview."""
    operational_as_of=date.today(); effective_as_of=DEMO_DATE if demo else (as_of or operational_as_of); all_batches=list(db.scalars(select(BatchDB).join(BatchDB.ingredient).order_by(BatchDB.use_by)))
    alerts=[{"id":b.id,"ingredient":b.ingredient.name,"quantity_kg":b.quantity_kg,"use_by":str(b.use_by),"days":(b.use_by-effective_as_of).days,"cost":round(b.quantity_kg*b.unit_cost,2)} for b in all_batches if b.quantity_kg>0 and b.use_by<=effective_as_of+timedelta(days=3)]
    pending=list(db.scalars(select(RecommendationDB).where(RecommendationDB.status=="pending").order_by(RecommendationDB.created_at.desc()).limit(5)))
    return {"as_of":str(effective_as_of),"date_context":"synthetic_demo" if demo else "operational","demo_as_of":str(DEMO_DATE),"operational_as_of":str(operational_as_of),"ingredients":db.query(IngredientDB).count(),"batches":len(all_batches),
            "pending_approvals":db.query(RecommendationDB).filter(RecommendationDB.status=="pending").count(),
            "pending_decisions":[{"id":x.id,"title":x.title,"estimated_kg":x.estimated_kg,"created_at":x.created_at} for x in pending],
            "inventory_kg":round(sum(b.quantity_kg for b in all_batches),2),"expiry_alerts":alerts,
            "expiry_attention_kg":round(sum(x["quantity_kg"] for x in alerts),2),"expiry_attention_cost":round(sum(x["cost"] for x in alerts),2),
            "latest_forecasts":[{"id":x.id,"menu_item":x.menu_item,"model":x.model,"created_at":x.created_at} for x in db.scalars(select(ForecastRunDB).order_by(ForecastRunDB.created_at.desc()).limit(6))]}

@app.post("/demo/load")
def load_demo_data(db:Session=Depends(db_session)):
    """Add a fixed demo dataset without deleting, updating, or duplicating user records.

    The names are deliberately namespaced and every insert is guarded by its natural
    key. Repeated calls therefore return the same usable demo, while arbitrary
    SQLite records and Docker volumes remain untouched.
    """
    created={"ingredients":0,"batches":0,"sales":0,"suppliers":0,"links":0,"recipes":0,"recipe_links":0,"forecast_runs":0}
    ingredient_specs=[("Demo Romaine Hearts","chilled"),("Demo Cherry Tomatoes","chilled"),("Demo Feta","chilled"),("Demo Citrus Dressing","chilled")]
    ingredients={}
    for name, category in ingredient_specs:
        row=db.scalar(select(IngredientDB).where(IngredientDB.name==name))
        if not row:
            row=IngredientDB(id=str(uuid4()),name=name,unit="kg",storage_category=category);db.add(row);db.flush();created["ingredients"]+=1
        ingredients[name]=row
    supplier=db.scalar(select(SupplierDB).where(SupplierDB.name=="Demo Market Cooperative"))
    if not supplier:
        supplier=SupplierDB(id=str(uuid4()),name="Demo Market Cooperative",lead_days=2,minimum_order_kg=2);db.add(supplier);db.flush();created["suppliers"]+=1
    prices={"Demo Romaine Hearts":5.2,"Demo Cherry Tomatoes":4.8,"Demo Feta":12.5,"Demo Citrus Dressing":8.0}
    for name, ingredient in ingredients.items():
        if not db.scalar(select(SupplierIngredientDB).where(SupplierIngredientDB.supplier_id==supplier.id,SupplierIngredientDB.ingredient_id==ingredient.id)):
            db.add(SupplierIngredientDB(supplier_id=supplier.id,ingredient_id=ingredient.id,purchase_unit_cost=prices[name]));created["links"]+=1
    batches=[("Demo Romaine Hearts",7.5,5.2,"2026-11-06","2026-11-10"),("Demo Cherry Tomatoes",6.0,4.8,"2026-11-05","2026-11-11"),("Demo Feta",3.0,12.5,"2026-11-03","2026-11-15"),("Demo Citrus Dressing",2.5,8.0,"2026-11-01","2026-11-18")]
    for name, qty, cost, received, use_by in batches:
        ing=ingredients[name]; received_d=date.fromisoformat(received); use_by_d=date.fromisoformat(use_by)
        existing=db.scalar(select(BatchDB).where(BatchDB.ingredient_id==ing.id,BatchDB.quantity_kg==qty,BatchDB.unit_cost==cost,BatchDB.received_on==received_d,BatchDB.use_by==use_by_d))
        if not existing: db.add(BatchDB(id=str(uuid4()),ingredient_id=ing.id,quantity_kg=qty,unit_cost=cost,received_on=received_d,use_by=use_by_d));created["batches"]+=1
    menu="Demo Garden Salad"
    recipe=db.scalar(select(RecipeDB).where(RecipeDB.name==menu))
    if not recipe:
        recipe=RecipeDB(id=str(uuid4()),name=menu,yield_servings=1);db.add(recipe);db.flush();created["recipes"]+=1
    recipe_quantities={"Demo Romaine Hearts":.18,"Demo Cherry Tomatoes":.12,"Demo Feta":.05,"Demo Citrus Dressing":.04}
    for name, qty in recipe_quantities.items():
        if not db.scalar(select(RecipeIngredientDB).where(RecipeIngredientDB.recipe_id==recipe.id,RecipeIngredientDB.ingredient_id==ingredients[name].id)):
            db.add(RecipeIngredientDB(recipe_id=recipe.id,ingredient_id=ingredients[name].id,quantity_kg=qty));created["recipe_links"]+=1
    sales=[28,31,29,34,38,42,36,32,35,39,44,47,41,37]
    start=date(2026,10,25)
    for offset, qty in enumerate(sales):
        sold=start+timedelta(days=offset)
        if not db.scalar(select(DailySaleDB).where(DailySaleDB.menu_item==menu,DailySaleDB.sold_on==sold)):
            db.add(DailySaleDB(menu_item=menu,sold_on=sold,quantity=qty));created["sales"]+=1
    db.commit()
    run=db.scalar(select(ForecastRunDB).where(ForecastRunDB.menu_item==menu).order_by(ForecastRunDB.created_at.desc()))
    if not run:
        # Uses the same persisted forecast algorithm as the normal UI flow.
        run_body=create_forecast_run(menu,ForecastRunIn(horizon=7,initial_train=7),db)
        run_id=run_body["id"];created["forecast_runs"]+=1
    else: run_id=run.id
    return {"message":"Demo data is ready. Existing SQLite records were not changed.","created":created,"forecast_run_id":run_id,"menu_item":menu,"provenance":"deterministic_synthetic_demo"}
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
    try:return {"provenance":"synthetic_scenario","result":optimize_multi_ingredient([x.model_dump() for x in data.items],data.horizon_days,data.storage_capacity_kg,data.preparation_capacity_hours)}
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
def suppliers(db:Session=Depends(db_session)):
    return [{"id":x.id,"name":x.name,"lead_days":x.lead_days,"minimum_order_kg":x.minimum_order_kg,"ingredients":[{"ingredient_id":a.ingredient_id,"ingredient":db.get(IngredientDB,a.ingredient_id).name,"purchase_unit_cost":a.purchase_unit_cost} for a in db.scalars(select(SupplierIngredientDB).where(SupplierIngredientDB.supplier_id==x.id))]} for x in db.scalars(select(SupplierDB).order_by(SupplierDB.name))]
@app.post("/suppliers",status_code=201)
def create_supplier(data:SupplierIn,db:Session=Depends(db_session)):
    if db.scalar(select(SupplierDB).where(SupplierDB.name==data.name.strip())): raise HTTPException(409,"Supplier already exists")
    x=SupplierDB(id=str(uuid4()),**data.model_dump());db.add(x);db.commit();return {"id":x.id,**data.model_dump()}
@app.post("/suppliers/{supplier_id}/ingredients",status_code=201)
def link_supplier_ingredient(supplier_id:str,data:SupplierIngredientIn,db:Session=Depends(db_session)):
    if not db.get(SupplierDB,supplier_id): raise HTTPException(404,"Supplier not found")
    if not db.get(IngredientDB,data.ingredient_id): raise HTTPException(404,"Ingredient not found")
    existing=db.scalar(select(SupplierIngredientDB).where(SupplierIngredientDB.supplier_id==supplier_id,SupplierIngredientDB.ingredient_id==data.ingredient_id))
    if existing:
        existing.purchase_unit_cost=data.purchase_unit_cost; db.commit(); return {"id":existing.id,"supplier_id":supplier_id,**data.model_dump()}
    x=SupplierIngredientDB(supplier_id=supplier_id,**data.model_dump());db.add(x);db.commit();return {"id":x.id,"supplier_id":supplier_id,**data.model_dump()}
@app.post("/recipes",status_code=201)
def create_recipe(data:RecipeIn,db:Session=Depends(db_session)):
    if db.scalar(select(RecipeDB).where(RecipeDB.name==data.name.strip())): raise HTTPException(409,"Recipe already exists")
    x=RecipeDB(id=str(uuid4()),**data.model_dump());db.add(x);db.commit();return {"id":x.id,**data.model_dump()}
def serialize_recipe(recipe: RecipeDB, db: Session):
    """Recipe and its persisted ingredient associations for API/UI consumers."""
    links = list(db.scalars(select(RecipeIngredientDB).where(
        RecipeIngredientDB.recipe_id == recipe.id
    ).order_by(RecipeIngredientDB.id)))
    return {"id": recipe.id, "name": recipe.name, "yield_servings": recipe.yield_servings,
            "ingredients": [{"id": link.id, "ingredient_id": link.ingredient_id,
                             "ingredient": db.get(IngredientDB, link.ingredient_id).name,
                             "quantity_kg": link.quantity_kg} for link in links]}

@app.get("/recipes")
def recipes(db:Session=Depends(db_session)):
    return [serialize_recipe(x, db) for x in db.scalars(select(RecipeDB).order_by(RecipeDB.name))]

@app.get("/recipes/{recipe_id}")
def recipe(recipe_id: str, db: Session = Depends(db_session)):
    row = db.get(RecipeDB, recipe_id)
    if not row: raise HTTPException(404, "Recipe not found")
    return serialize_recipe(row, db)
@app.post("/recipes/{recipe_id}/ingredients",status_code=201)
def add_recipe_ingredient(recipe_id:str,data:RecipeIngredientIn,db:Session=Depends(db_session)):
    if not db.get(RecipeDB,recipe_id) or not db.get(IngredientDB,data.ingredient_id): raise HTTPException(404,"Recipe or ingredient not found")
    existing=db.scalar(select(RecipeIngredientDB).where(RecipeIngredientDB.recipe_id==recipe_id,RecipeIngredientDB.ingredient_id==data.ingredient_id))
    if existing:
        existing.quantity_kg=data.quantity_kg; db.commit()
        return {"id":existing.id,"recipe_id":recipe_id,**data.model_dump()}
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
    if db.scalar(select(DailySaleDB).where(DailySaleDB.menu_item==data.menu_item.strip(),DailySaleDB.sold_on==data.sold_on)): raise HTTPException(409,"A sale already exists for this menu item and date")
    x=DailySaleDB(**data.model_dump());db.add(x)
    try: db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,"A sale already exists for this menu item and date")
    return {"id":x.id,**data.model_dump()}
@app.get("/sales")
def sales(menu_item:str|None=None,db:Session=Depends(db_session)):
    query=select(DailySaleDB).order_by(DailySaleDB.sold_on)
    if menu_item: query=query.where(DailySaleDB.menu_item==menu_item)
    return [{"menu_item":x.menu_item,"sold_on":str(x.sold_on),"quantity":x.quantity} for x in db.scalars(query)]
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
    if len(values)>data.initial_train+3: evaluation["independent_interval_evaluation"]=independent_interval_coverage(values,data.initial_train,3)
    predicted=(moving_average(values,data.horizon) if model=="moving_average" else seasonal_naive(values,data.horizon) if model=="seasonal_naive" else lightgbm_forecast(values,data.horizon))
    width=evaluation["interval_half_width"];start=history[-1].sold_on+timedelta(days=1); forecasts=[{"date":str(start+timedelta(days=i)),"quantity":q,"low":round(max(0,q-width),2),"high":round(q+width,2)} for i,q in enumerate(predicted)]
    run=ForecastRunDB(id=str(uuid4()),menu_item=menu_item,model=model,metrics_json=json.dumps(evaluation["models"]),predictions_json=json.dumps(forecasts));db.add(run);db.flush()
    for item in forecasts: db.add(ForecastPredictionDB(forecast_run_id=run.id,predicted_for=date.fromisoformat(item["date"]),quantity=item["quantity"],low=item["low"],high=item["high"]))
    db.commit()
    return {"id":run.id,"menu_item":menu_item,"model":model,"training_points":len(values),"evaluation":evaluation,"predictions":forecasts,"provenance":"local_demo_sales","limitations":"Baseline models only; results are not restaurant pilot metrics."}

def serialize_forecast_run(run:ForecastRunDB):
    """Return the same complete contract for a newly-created or restored run."""
    return {"id":run.id,"menu_item":run.menu_item,"model":run.model,
            "metrics":json.loads(run.metrics_json),"predictions":json.loads(run.predictions_json),
            "created_at":run.created_at,"provenance":"local_demo_sales",
            "limitations":"Baseline models only; results are not restaurant pilot metrics."}

@app.get("/forecast-runs")
def forecast_runs(db:Session=Depends(db_session)):
    """Persisted runs are deliberately listable so a browser selection can be validated."""
    return [serialize_forecast_run(x) for x in db.scalars(select(ForecastRunDB).order_by(ForecastRunDB.created_at.desc()))]

@app.get("/forecast-runs/{run_id}")
def forecast_run(run_id:str,db:Session=Depends(db_session)):
    run=db.get(ForecastRunDB,run_id)
    if not run: raise HTTPException(404,"Forecast run not found")
    return serialize_forecast_run(run)
@app.get("/forecasts/{menu_item}/history")
def forecast_history(menu_item:str,db:Session=Depends(db_session)):
    return [serialize_forecast_run(x) for x in db.scalars(select(ForecastRunDB).where(ForecastRunDB.menu_item==menu_item).order_by(ForecastRunDB.created_at.desc()))]
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
def recipe_workflow(run_id:str,data:WorkflowIn,db:Session):
    run=db.get(ForecastRunDB,run_id)
    if not run: raise HTTPException(404,"Forecast run not found")
    recipe=db.scalar(select(RecipeDB).where(RecipeDB.name==run.menu_item))
    if not recipe: raise HTTPException(404,"No recipe named for this menu item")
    recipe_links=list(db.scalars(select(RecipeIngredientDB).where(RecipeIngredientDB.recipe_id==recipe.id)))
    if not recipe_links: raise HTTPException(422,"Recipe has no ingredient associations")
    input_data={"as_of":str(data.as_of),"horizon_days":data.horizon_days,"trials":data.trials,"storage_capacity_kg":data.storage_capacity_kg,"preparation_capacity_hours":data.preparation_capacity_hours}
    # A route refresh must not create a second simulation or a second approval card.
    # Same run + same explicit inputs and seed restores the persisted scenario instead.
    for existing in db.scalars(select(RiskScenarioDB).where(RiskScenarioDB.forecast_run_id==run_id, RiskScenarioDB.seed==data.seed).order_by(RiskScenarioDB.created_at.desc())):
        if json.loads(existing.inputs_json)==input_data:
            return {"scenario_id":existing.id,"forecast_run_id":run_id,"recipe":run.menu_item,
                    "result":json.loads(existing.outputs_json),"recommendations":[],"restored":True}
    servings=sum(x["quantity"] for x in json.loads(run.predictions_json)); requirements={}
    for ri in recipe_links:
        ingredient=db.get(IngredientDB,ri.ingredient_id);requirements[ingredient.name]=servings/recipe.yield_servings*ri.quantity_kg
    inventory=list(db.scalars(select(BatchDB).join(BatchDB.ingredient)))
    batches=[BatchInput(id=b.id,ingredient=b.ingredient.name,quantity_kg=b.quantity_kg,use_by=b.use_by,unit_cost=b.unit_cost,received_on=b.received_on) for b in inventory]
    # Aggregate horizon demand into daily rate for expiry-safe FEFO allocation.
    scenario=Scenario(batches=batches,demand=[Demand(ingredient=k,expected_daily_kg=v/data.horizon_days) for k,v in requirements.items()],as_of=data.as_of)
    risk=fefo_risk(scenario)
    items=[]
    for ingredient,demand_kg in requirements.items():
        relevant=[b for b in inventory if b.ingredient.name==ingredient and b.use_by>=data.as_of]
        available=sum(b.quantity_kg for b in relevant)
        ingredient_row=db.scalar(select(IngredientDB).where(IngredientDB.name==ingredient))
        # Only an explicit ingredient link is eligible.  Select deterministically
        # (lowest known unit price, then supplier id) rather than accidentally
        # borrowing a constraint from an unrelated supplier.
        links=list(db.scalars(select(SupplierIngredientDB).where(
            SupplierIngredientDB.ingredient_id==ingredient_row.id,
            SupplierIngredientDB.purchase_unit_cost.is_not(None)
        )))
        link=min(links, key=lambda row: (row.purchase_unit_cost, row.supplier_id), default=None)
        supplier=db.get(SupplierDB,link.supplier_id) if link else None
        # An unlinked supplier or unknown purchase price cannot produce a purchase recommendation.
        if supplier and link and link.purchase_unit_cost is not None:
            items.append({"ingredient":ingredient,"available_kg":available,"demand_kg":demand_kg,"unit_cost":link.purchase_unit_cost,"lead_days":supplier.lead_days,"min_order_kg":supplier.minimum_order_kg,"supplier":supplier.name,"max_order_kg":1000})
    plan=optimize_multi_ingredient(items,data.horizon_days,data.storage_capacity_kg,data.preparation_capacity_hours) if items else {"status":"infeasible","items":[],"warning":"No ingredients have an assigned supplier with a known purchase price; no purchase recommendation was calculated."}
    # Keep unavailable inputs visible in totals.  Omitting them made the
    # optimized shortage look better than it was, even though no order could be
    # recommended without an explicit priced supplier relationship.
    eligible={x["ingredient"] for x in items}
    unavailable=[]
    for ingredient,demand_kg in requirements.items():
        if ingredient not in eligible:
            available=sum(b.quantity_kg for b in inventory if b.ingredient.name==ingredient and b.use_by>=data.as_of)
            shortage=max(0, demand_kg-available)
            unavailable.append({"ingredient":ingredient,"supplier":None,"order_kg":0,"shortage_kg":round(shortage,3),"surplus_kg":round(max(0,available-demand_kg),3),"lead_time_blocks_order":False,"minimum_order_kg":None,"order_activated":False,"purchase_unavailable":True})
    if unavailable:
        plan["items"]=plan.get("items",[])+unavailable
        plan["baseline_shortage_kg"]=round(sum(max(0, requirements[name]-sum(b.quantity_kg for b in inventory if b.ingredient.name==name and b.use_by>=data.as_of)) for name in requirements),3)
        plan["optimized_shortage_kg"]=round(sum(row["shortage_kg"] for row in plan["items"]),3)
        plan["warning"]="Some ingredients have no explicitly linked supplier with a known price; their shortages remain unmet and no purchase recommendation was calculated."
    simulation=monte_carlo_risk([SimBatch(b.id,b.ingredient.name,b.quantity_kg,(b.use_by-data.as_of).days,b.unit_cost) for b in inventory],{k:v/data.horizon_days for k,v in requirements.items()},data.horizon_days,data.trials,data.seed).__dict__
    output={"risk":risk.model_dump(),"monte_carlo":simulation,"optimization":plan,"requirements_kg":requirements,
            "scenario_as_of":str(data.as_of),"horizon_days":data.horizon_days,
            "provenance":"simulated_forecast_recipe_inventory",
            "warning":"Simulated planning output; no purchase or food-safety action is executed."}
    record=RiskScenarioDB(id=str(uuid4()),forecast_run_id=run_id,seed=data.seed,inputs_json=json.dumps(input_data),outputs_json=json.dumps(output));db.add(record)
    recommendations=[]
    for row in plan.get("items",[]):
        if row["order_kg"]>0 or row["shortage_kg"]>0:
            r=RecommendationDB(id=str(uuid4()),title=f"Review {row['ingredient']}: order {row['order_kg']} kg; shortage {row['shortage_kg']} kg",estimated_kg=row["order_kg"]);db.add(r);recommendations.append({"id":r.id,"title":r.title,"status":"pending"})
    db.add(AuditEventDB(event_type="workflow_simulated",detail=f"forecast {run_id}, scenario {record.id}"));db.commit()
    return {"scenario_id":record.id,"forecast_run_id":run_id,"recipe":recipe.name,"result":output,"recommendations":recommendations}
@app.post("/workflows/forecast/{run_id}")
def run_workflow(run_id:str,data:WorkflowIn,db:Session=Depends(db_session)): return recipe_workflow(run_id,data,db)
@app.get("/risk-scenarios/{scenario_id}")
def risk_scenario(scenario_id:str,db:Session=Depends(db_session)):
    x=db.get(RiskScenarioDB,scenario_id)
    if not x: raise HTTPException(404,"Risk scenario not found")
    return {"id":x.id,"forecast_run_id":x.forecast_run_id,"seed":x.seed,"inputs":json.loads(x.inputs_json),"outputs":json.loads(x.outputs_json),"provenance":"simulated_forecast_recipe_inventory"}
@app.get("/risk-scenarios")
def risk_scenarios(forecast_run_id:str|None=None,db:Session=Depends(db_session)):
    query=select(RiskScenarioDB).order_by(RiskScenarioDB.created_at.desc())
    if forecast_run_id: query=query.where(RiskScenarioDB.forecast_run_id==forecast_run_id)
    return [{"id":x.id,"forecast_run_id":x.forecast_run_id,"seed":x.seed,"created_at":x.created_at,
             "inputs":json.loads(x.inputs_json),"outputs":json.loads(x.outputs_json),
             "provenance":"simulated_forecast_recipe_inventory"} for x in db.scalars(query)]
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
    if x.status!="pending": raise HTTPException(409,"Recommendation already has a final decision")
    x.status=data.decision;db.add(AuditEventDB(event_type="recommendation_"+data.decision,detail=f"{recommendation_id}: {data.reason}"));db.commit();return {"id":x.id,"status":x.status,"reason":data.reason}
@app.get("/recommendations")
def recommendations(db:Session=Depends(db_session)): return [{"id":x.id,"title":x.title,"status":x.status,"estimated_kg":x.estimated_kg,"created_at":x.created_at} for x in db.scalars(select(RecommendationDB).order_by(RecommendationDB.created_at.desc()))]
@app.get("/audit-events")
def audit_events(db:Session=Depends(db_session)): return [{"id":x.id,"event_type":x.event_type,"detail":x.detail,"created_at":x.created_at} for x in db.scalars(select(AuditEventDB).order_by(AuditEventDB.created_at.desc()).limit(100))]
