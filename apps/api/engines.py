"""Deterministic forecast, simulation and constrained planning primitives."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from math import ceil
from statistics import mean
from typing import Iterable
import numpy as np
from ortools.linear_solver import pywraplp

def moving_average(values: list[float], horizon: int, window: int = 7) -> list[float]:
    if not values or horizon < 1: raise ValueError("History and a positive horizon are required")
    estimate = mean(values[-window:]); return [round(estimate, 3)] * horizon

def seasonal_naive(values: list[float], horizon: int, season: int = 7) -> list[float]:
    if len(values) < season: return moving_average(values, horizon)
    return [round(values[-season + i % season], 3) for i in range(horizon)]

def metrics(actual: list[float], predicted: list[float]) -> dict[str, float | None]:
    if len(actual) != len(predicted) or not actual: raise ValueError("Equal non-empty series required")
    errors=np.array(predicted)-np.array(actual); actual_a=np.array(actual)
    return {"mae":round(float(np.mean(np.abs(errors))),4),"rmse":round(float(np.sqrt(np.mean(errors**2))),4),"bias":round(float(np.mean(errors)),4),"wape":round(float(np.sum(np.abs(errors))/np.sum(np.abs(actual_a))*100),4) if np.sum(np.abs(actual_a)) else None}

def rolling_origin_backtest(values:list[float], initial_train:int=7)->dict:
    """Leakage-free one-step rolling-origin comparison of deterministic baselines."""
    if len(values)<=initial_train: raise ValueError("Need more observations than initial training window")
    actual=[]; moving=[]; seasonal=[]
    for cutoff in range(initial_train,len(values)):
        train=values[:cutoff];actual.append(values[cutoff])
        moving.append(moving_average(train,1)[0]);seasonal.append(seasonal_naive(train,1)[0])
    scores={"moving_average":metrics(actual,moving),"seasonal_naive":metrics(actual,seasonal)}
    selected=min(scores,key=lambda model:scores[model]["mae"] if scores[model]["mae"] is not None else float("inf"))
    return {"points":len(actual),"models":scores,"selected_model":selected,"actual":actual}

@dataclass
class Batch: id:str; ingredient:str; quantity_kg:float; use_by_days:int; unit_cost:float
@dataclass
class SimulationResult:
    expected_waste_kg:float; waste_probability:float; stockout_probability:float; cost_at_risk:float; p10_kg:float; p90_kg:float; seed:int; trials:int

def monte_carlo_risk(batches: Iterable[Batch], daily_demand: dict[str,float], horizon_days:int=7, trials:int=500, seed:int=42, demand_cv:float=.2)->SimulationResult:
    """Expiry-safe FEFO demand simulation. All random draws are seeded and reproducible."""
    batches=list(batches); rng=np.random.default_rng(seed); waste=[]; stockouts=[]; costs=[]
    for _ in range(trials):
        available={b.id:b.quantity_kg for b in batches}; shortage=False
        for day in range(horizon_days):
            for ing, base in daily_demand.items():
                need=max(0,rng.normal(base, max(.01,base*demand_cv)))
                choices=sorted((b for b in batches if b.ingredient.lower()==ing.lower() and b.use_by_days>day),key=lambda b:b.use_by_days)
                for b in choices:
                    used=min(need,available[b.id]);available[b.id]-=used;need-=used
                    if need<=0:break
                shortage|=need>1e-8
        at_risk=sum(available[b.id] for b in batches if b.use_by_days<=horizon_days)
        waste.append(at_risk); costs.append(sum(available[b.id]*b.unit_cost for b in batches if b.use_by_days<=horizon_days)); stockouts.append(shortage)
    a=np.array(waste);return SimulationResult(round(float(a.mean()),3),round(float(np.mean(a>0)),3),round(float(np.mean(stockouts)),3),round(float(np.mean(costs)),2),round(float(np.quantile(a,.1)),3),round(float(np.quantile(a,.9)),3),seed,trials)

def optimize_purchase(available_kg:float, demand_kg:float, unit_cost:float, min_order_kg:float=0, max_order_kg:float=1000, shortage_penalty:float=20, waste_penalty:float=2)->dict:
    """LP purchase recommendation. It transparently balances surplus, shortage and cost."""
    if min(available_kg,demand_kg,unit_cost,min_order_kg,max_order_kg,shortage_penalty,waste_penalty)<0 or min_order_kg>max_order_kg: raise ValueError("Invalid optimization inputs")
    solver=pywraplp.Solver.CreateSolver("GLOP")
    if not solver: raise RuntimeError("OR-Tools GLOP solver unavailable")
    order=solver.NumVar(0,max_order_kg,"order"); shortage=solver.NumVar(0,solver.infinity(),"shortage"); surplus=solver.NumVar(0,solver.infinity(),"surplus")
    solver.Add(available_kg+order+shortage-surplus==demand_kg)
    if min_order_kg>0: # Avoid unsupported binary choice: this local model assumes an order is needed when min is configured.
        solver.Add(order>=min_order_kg)
    solver.Minimize(unit_cost*order+shortage_penalty*shortage+waste_penalty*surplus)
    status=solver.Solve(); names={solver.OPTIMAL:"optimal",solver.FEASIBLE:"feasible"}
    return {"status":names.get(status,"infeasible"),"recommended_order_kg":round(order.solution_value(),3) if status in names else None,"expected_shortage_kg":round(shortage.solution_value(),3) if status in names else None,"expected_surplus_kg":round(surplus.solution_value(),3) if status in names else None,"objective":round(solver.Objective().Value(),3) if status in names else None,"assumptions":["Single-ingredient linear purchase planning", "Recommendation only; manager approval required", "No order executes through this API"]}
