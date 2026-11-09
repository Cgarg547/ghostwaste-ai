'use client';

import { useEffect, useState, type ReactNode } from 'react';
import {
  DataPanel,
  EmptyState,
  ResponsiveDataTable,
  SectionHeader,
  StatCard,
  StatusBadge,
} from './primitives';

const fmt = (value: unknown, digits = 1) => Number(value || 0).toFixed(digits);
const shortDate = (value: string) => new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

function CountUp({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { setDisplay(value); return; }
    let start: number | undefined;
    let frame = 0;
    const tick = (now: number) => {
      start ??= now;
      const progress = Math.min(1, (now - start) / 620);
      setDisplay(value * (1 - Math.pow(1 - progress, 3)));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);
  return <>{new Intl.NumberFormat(undefined, { maximumFractionDigits: suffix ? 1 : 0 }).format(display)}{suffix}</>;
}

export function NavIcon({ index }: { index: number }) {
  const paths = [
    <><path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v9h13v-9M9 19v-5h6v5"/></>,
    <><path d="M4 7.5h16M6 4.5h12l1 15H5l1-15Z"/><path d="M9 10v6m6-6v6"/></>,
    <><path d="M4 18V6m0 12h16"/><path d="m6 15 4-4 3 2 6-7"/><path d="M16 6h3v3"/></>,
    <><path d="M12 3 4.5 6v5c0 4.7 3.1 8 7.5 10 4.4-2 7.5-5.3 7.5-10V6L12 3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></>,
    <><path d="M4 19V5m0 14h16"/><path d="M7 16l4-5 3 2 5-7"/></>,
    <><path d="M12 3v4m0 10v4M3 12h4m10 0h4"/><circle cx="12" cy="12" r="5"/><path d="m10 12 1.4 1.4L14.5 10"/></>,
    <><path d="M4 19V5m0 14h16"/><path d="M7 15h3V9H7zm6 0h3V5h-3zm6 0h2v-4h-2z"/></>,
    <><circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.3 1-1.4 2.4-1.6-.6a7.6 7.6 0 0 1-1.4.8l-.3 1.7h-2.8l-.3-1.7a7.6 7.6 0 0 1-1.4-.8l-1.6.6-1.4-2.4 1.3-1a7.2 7.2 0 0 1 0-1.7l-1.3-1 1.4-2.4 1.6.6a7.6 7.6 0 0 1 1.4-.8l.3-1.7h2.8l.3 1.7a7.6 7.6 0 0 1 1.4.8l1.6-.6 1.4 2.4-1.3 1a7.2 7.2 0 0 1-.1 1.6Z"/></>,
  ];
  return <svg className="nav-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[index] || paths[0]}</svg>;
}

export function OverviewDashboard({ dash, forecast, scenario, children, onForecast, onRadar, onOptimization, onInventory, onApproval }: any) {
  const alerts = dash.expiry_alerts || [];
  const pending = dash.pending_decisions || [];
  return <>
    <section className="overview-hero">
      <div className="hero-copy">
        <p className="eyebrow">FOOD INTELLIGENCE · {dash.date_context === 'synthetic_demo' ? 'SYNTHETIC DEMO' : 'LOCAL OPERATIONS'}</p>
        <h2>Make every ingredient count.</h2>
        <p>Bring inventory, demand forecasts and expiry signals into one clear operating view. Explore modeled scenarios before making a decision.</p>
        <div className="hero-actions"><button onClick={onForecast}>Open demand forecast</button><button className="hero-secondary" onClick={onOptimization}>Explore optimization</button></div>
        <span className="hero-context">{forecast ? `Selected persisted run · ${forecast.menu_item}` : 'No forecast selected'} · {dash.as_of || 'date unavailable'}</span>
      </div>
      <div className="hero-art" aria-label="Original illustrated produce still life">
        <span className="orbit orbit-one" aria-hidden="true"/><span className="orbit orbit-two" aria-hidden="true"/>
        <img src="/hero-produce.svg" alt="A detailed still life of fresh greens, tomato, citrus, avocado, carrot and herbs" />
        <div className="hero-signal signal-forecast"><i aria-hidden="true">⌁</i><span>Forecast<br/><b>{forecast ? 'Selected run' : 'Awaiting data'}</b></span></div>
        <div className="hero-signal signal-expiry"><i aria-hidden="true">◷</i><span>Expiry<br/><b>{alerts.length ? `${alerts.length} batches` : 'No alerts'}</b></span></div>
        <div className="hero-signal signal-optimize"><i aria-hidden="true">✦</i><span>Optimize<br/><b>{scenario ? 'Scenario ready' : 'Review first'}</b></span></div>
        <div className="hero-readout"><small>INVENTORY ON HAND</small><b>{fmt(dash.inventory_kg)} kg</b><span>{dash.batches || 0} saved batches</span></div>
      </div>
      <div className="hero-footnote"><span className="signal-dot"/> Local data · no supplier contact or orders</div>
    </section>

    <section className="cards overview-kpis" aria-label="Inventory and action summary">
      <StatCard label="Ingredients" value={<CountUp value={Number(dash.ingredients || 0)} />} detail="Saved in catalog" tone="green" />
      <StatCard label="Stock on hand" value={<CountUp value={Number(dash.inventory_kg || 0)} suffix=" kg" />} detail={`${dash.batches || 0} inventory batches`} tone="lime" />
      <StatCard label="Expiry attention" value={<CountUp value={Number(dash.expiry_attention_kg || 0)} suffix=" kg" />} detail={`${alerts.length} batches near or past use-by`} tone="amber" />
      <StatCard label="Pending review" value={<CountUp value={Number(dash.pending_approvals || 0)} />} detail="Approval-only recommendations" tone="green" />
    </section>

    <section className="operating-flow" aria-label="GhostWaste workflow">
      <SectionHeader title="From signal to decision" description="A reviewable workflow. Estimates stay labeled as modeled until measured in operations." />
      <div className="flow-steps">
        <FlowStep n="01" title="Inventory" detail="Manage batches & use-by dates" icon="inventory" onClick={onInventory}/>
        <span className="flow-connector" aria-hidden="true"><i/><b>›</b></span>
        <FlowStep n="02" title="Forecast" detail="Plan from persisted sales" icon="forecast" onClick={onForecast}/>
        <span className="flow-connector" aria-hidden="true"><i/><b>›</b></span>
        <FlowStep n="03" title="Optimize" detail="Compare constrained plans" icon="optimize" onClick={onOptimization}/>
        <span className="flow-connector" aria-hidden="true"><i/><b>›</b></span>
        <FlowStep n="04" title="Approve" detail="Review before any action" icon="approve" onClick={onApproval}/>
      </div>
    </section>

    <div className="dashboard-grid">
      <DataPanel title="Expiry priorities" description={`Inventory facts within the dashboard horizon · as of ${dash.as_of || '—'}`} actions={<button className="text-button" onClick={onRadar}>Open Waste Radar <span aria-hidden="true">↗</span></button>}>
        {alerts.length ? <ResponsiveDataTable headers={['Ingredient','Quantity','Use-by','Priority']} rows={alerts.slice(0, 6).map((row: any) => [row.ingredient, `${fmt(row.quantity_kg)} kg`, row.use_by, <StatusBadge key={row.id} tone={row.days < 0 ? 'danger' : row.days <= 1 ? 'warning' : 'neutral'}>{row.days < 0 ? `${Math.abs(row.days)}d past` : `${row.days}d`}</StatusBadge>])} /> : <EmptyState title="No near-term expiry alerts" description="No positive-quantity batches are inside the current three-day dashboard window. This is an inventory alert, not a waste forecast."/>}
      </DataPanel>
      <DataPanel title="Decisions waiting" description="Manager review only. GhostWaste will not place orders or contact suppliers.">
        {pending.length ? <div className="decision-list">{pending.slice(0, 4).map((item: any) => <article className="decision-row" key={item.id}><div><StatusBadge tone="warning">Pending</StatusBadge><b>{item.title}</b></div><strong>{fmt(item.estimated_kg)} kg</strong></article>)}</div> : <EmptyState title="No pending decisions" description="Run a saved forecast scenario to create recommendations for review."/>}
      </DataPanel>
    </div>

    <div className="dashboard-grid lower-grid">
      <DataPanel title="Live planning context" description={scenario ? `Saved scenario ${scenario.id.slice(0, 8)} · ${scenario.inputs?.as_of || 'date unavailable'} · seed ${scenario.seed}. Simulated output, not observed savings.` : 'Select a saved forecast and run its workflow to create a persisted, reproducible planning scenario.'}>
        {children}
      </DataPanel>
      <section className="quick-actions"><p className="eyebrow">QUICK ACCESS</p><h2>Continue planning</h2><button onClick={onForecast}><span>↗</span><b>Review demand forecast</b><small>History, model metrics and planning range</small></button><button onClick={onOptimization}><span>⌁</span><b>Compare purchase plans</b><small>Supplier and shortage constraints</small></button></section>
    </div>
  </>;
}

function FlowStep({ n, title, detail, icon, onClick }: { n: string; title: string; detail: string; icon: string; onClick: () => void }) {
  const paths: Record<string, ReactNode> = {
    inventory: <><path d="M4 7.5h16M6 4.5h12l1 15H5l1-15Z"/><path d="M9 10v6m6-6v6"/></>,
    forecast: <><path d="M4 18V6m0 12h16"/><path d="m6 15 4-4 3 2 6-7"/><path d="M16 6h3v3"/></>,
    optimize: <><path d="M4 19V5m0 14h16"/><path d="M7 16l4-5 3 2 5-7"/><circle cx="19" cy="6" r="2"/></>,
    approve: <><path d="M12 3 4.5 6v5c0 4.7 3.1 8 7.5 10 4.4-2 7.5-5.3 7.5-10V6L12 3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></>,
  };
  return <button type="button" className="flow-step" onClick={onClick} aria-label={`Step ${n}: open ${title}`}><span className="flow-number">{n}</span><span className="flow-icon"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[icon]}</svg></span><b>{title}</b><small>{detail}</small></button>;
}

export function ForecastWorkspace({ runs, forecast, onSelect, salesForm, forecastContent, forecastAction }: { runs: any[]; forecast: any; onSelect: (id: string) => void; salesForm: ReactNode; forecastContent: ReactNode; forecastAction: ReactNode }) {
  return <div className="route-stack">
    <DataPanel title="Forecast workspace" description="Select a persisted forecast run. Historical observations and projections are drawn from saved sales and prediction records.">
      <label className="select-field"><span>Persisted forecast run</span><select aria-label="Select persisted forecast run" value={forecast?.id || ''} onChange={event => onSelect(event.target.value)}><option value="">Select a forecast</option>{runs.map(run => <option key={run.id} value={run.id}>{run.menu_item} · {run.model} · {new Date(run.created_at).toLocaleDateString()}</option>)}</select></label>
      <div className="forecast-action-slot">{forecastAction}</div>
    </DataPanel>
    <div className="forecast-layout"><div>{forecast ? forecastContent : <EmptyState title="No forecast selected" description="Load synthetic demo data or generate a persisted run from enough recorded sales."/>}</div><aside className="forecast-side"><p className="eyebrow">ADD OBSERVED INPUTS</p><h2>Record daily sales</h2><p>Sales entries are saved to the local database and can support future forecasts.</p>{salesForm}</aside></div>
  </div>;
}

export function ForecastCreateForm({ go, busy }: { go: (menu: string, horizon: number, initialTrain: number) => void; busy: boolean }) {
  const [menu, setMenu] = useState('');
  const [horizon, setHorizon] = useState(7);
  const [initialTrain, setInitialTrain] = useState(7);
  return <form className="compact-forecast-form" onSubmit={event => { event.preventDefault(); go(menu.trim(), horizon, initialTrain); }}>
    <div><label htmlFor="forecast-menu">Menu item</label><input id="forecast-menu" required maxLength={120} value={menu} onChange={event => setMenu(event.target.value)} placeholder="Use the menu item in sales history"/></div>
    <div className="forecast-form-numbers"><label>Horizon (days)<input type="number" min="1" max="30" value={horizon} onChange={event => setHorizon(Number(event.target.value))}/></label><label>Initial history (days)<input type="number" min="3" value={initialTrain} onChange={event => setInitialTrain(Number(event.target.value))}/></label></div>
    <button disabled={busy || !menu.trim()}>Generate & save forecast</button>
    <small>Uses the saved chronological sales history for this menu item.</small>
  </form>;
}

export function ForecastTimeSeries({ sales, predictions }: { sales: any[]; predictions: any[] }) {
  const [tip, setTip] = useState<any>();
  const history = sales.slice(-20).map(point => ({ date: point.sold_on, value: Number(point.quantity), kind: 'Historical demand' }));
  const future = predictions.map(point => { const value = Number(point.quantity); return { date: point.date, value, low: point.low == null ? value : Number(point.low), high: point.high == null ? value : Number(point.high), kind: 'Forecast demand' }; });
  const points: any[] = [...history, ...future];
  const observedMax = Math.max(0, ...points.map(point => point.high ?? point.value));
  const max = observedMax > 0 ? observedMax * 1.12 : 1;
  const width = 800, height = 310, left = 58, right = 18, top = 22, bottom = 36;
  const plotWidth = width - left - right, plotHeight = height - top - bottom;
  const xAt = (index: number) => left + index * plotWidth / Math.max(1, points.length - 1);
  const yAt = (value: number) => top + plotHeight - value / max * plotHeight;
  const coordinates = (items: any[], offset = 0) => items.map((point, index) => `${xAt(index + offset)},${yAt(point.value)}`).join(' ');
  const firstForecastLine = history.length ? `${xAt(history.length - 1)},${yAt(history[history.length - 1].value)} ` : '';
  const forecastLine = future.length ? firstForecastLine + coordinates(future, history.length) : '';
  const upper = future.map((point, index) => `${xAt(history.length + index)},${yAt(point.high ?? point.value)}`);
  const lower = [...future].reverse().map((point, index) => `${xAt(history.length + future.length - index - 1)},${yAt(point.low ?? point.value)}`);
  const band = upper.length ? upper.concat(lower).join(' ') : '';
  const ticks = [max, max / 2, 0];
  const dateLabel = (date: string) => new Date(`${date}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  return <div className="timeseries" onMouseLeave={() => setTip(undefined)}>
    <div className="chart-legend"><span><i className="legend historical"/>Historical demand</span><span><i className="legend predicted"/>Forecast demand</span><span><i className="legend interval"/>Planning interval</span><small>servings / day</small></div>
    {points.length ? <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Historical and forecast daily servings with saved planning bounds">
      {ticks.map((tick, index) => <g key={index}><line x1={left} x2={width - right} y1={yAt(tick)} y2={yAt(tick)} className="chart-grid"/><text x={left - 10} y={yAt(tick) + 4} textAnchor="end" className="chart-axis-label">{Math.round(tick)}</text></g>)}
      <line x1={left} x2={left} y1={top} y2={height - bottom} className="chart-grid"/>
      {band && <polygon points={band} className="planning-band"/>}
      {history.length > 1 && <polyline points={coordinates(history)} className="history-line"/>}
      {future.length > 0 && <polyline points={forecastLine} className="forecast-line"/>}
      {points.map((point, index) => {
        const pointId = `${point.kind}-${point.date}`;
        const description = `${point.kind}, ${dateLabel(point.date)}, ${fmt(point.value)} servings per day${point.low != null ? `, saved planning bounds ${fmt(point.low)} to ${fmt(point.high)} servings per day` : ''}`;
        return <circle key={pointId} data-chart-point={pointId} cx={xAt(index)} cy={yAt(point.value)} r="5" className={point.kind[0] === 'H' ? 'history-dot' : 'forecast-dot'} tabIndex={0} role="img" aria-label={description} aria-describedby={tip && `${tip.kind}-${tip.date}` === pointId ? 'forecast-chart-tooltip' : undefined} onMouseEnter={() => setTip(point)} onFocus={() => setTip(point)} onBlur={() => setTip(undefined)}/>;
      })}
      {points.length > 0 && <><text x={xAt(0)} y={height - 8} textAnchor="start" className="chart-axis-label">{dateLabel(points[0].date)}</text><text x={xAt(points.length - 1)} y={height - 8} textAnchor="end" className="chart-axis-label">{dateLabel(points[points.length - 1].date)}</text></>}
    </svg> : <div className="chart-empty">No persisted sales or prediction points are available for this forecast.</div>}
    {tip && <div id="forecast-chart-tooltip" className="chart-tooltip" role="status" aria-live="polite"><b>{dateLabel(tip.date)}</b><span>{tip.kind}: {fmt(tip.value)} servings / day</span>{tip.low != null && <span>Saved planning bounds: {fmt(tip.low)}–{fmt(tip.high)}</span>}</div>}
  </div>;
}

export function WasteRadarWorkspace({ dashboard, scenario, output, forecastId, onRun }: any) {
  const risk = output?.risk;
  const simulation = output?.monte_carlo;
  const risks = risk?.risks || [];
  const alerts = dashboard.expiry_alerts || [];
  const hasScenario = Boolean(scenario && output);
  const modeledZero = hasScenario && Number(simulation?.expected_waste_kg) === 0 && Number(risk?.total_at_risk_kg) === 0;
  return <div className="route-stack">
    <section className="route-hero radar-hero"><div><p className="eyebrow">INVENTORY FACTS + MODELED SCENARIO</p><h2>Separate expiry attention from forecast risk.</h2><p>Proximity alerts are observed batch dates. Waste probability and quantity are seeded model estimates from the selected saved forecast.</p></div><button onClick={onRun} disabled={!forecastId}>Run / restore selected scenario</button></section>
    <section className="risk-separation">
      <DataPanel title="Expiry attention" description={`Observed inventory facts · dashboard date ${dashboard.as_of || '—'}`}>
        {alerts.length ? <div className="priority-list">{alerts.map((item: any) => <article key={item.id}><span className="priority-icon" aria-hidden="true">!</span><div><b>{item.ingredient}</b><small>{item.quantity_kg} kg · use-by {item.use_by}</small></div><StatusBadge tone={item.days < 0 ? 'danger' : item.days <= 1 ? 'warning' : 'neutral'}>{item.days < 0 ? `${Math.abs(item.days)} days past` : `${item.days} days`}</StatusBadge></article>)}</div> : <EmptyState title="No expiry attention in this window" description="The dashboard reports no positive batches within three days. This does not imply zero food waste."/>}
      </DataPanel>
      <DataPanel title="Simulated forecast risk" description={hasScenario ? `Saved scenario ${scenario.id.slice(0, 8)} · as of ${scenario.inputs?.as_of || '—'} · ${simulation?.trials ?? scenario.inputs?.trials ?? '—'} trials · seed ${simulation?.seed ?? scenario.seed}.` : 'A scenario is required before model-based waste-risk values are available.'}>
        {hasScenario ? <div className="sim-summary"><div><small>EXPECTED WASTE</small><b>{fmt(simulation?.expected_waste_kg)} kg</b></div><div><small>WASTE PROBABILITY</small><b>{simulation?.waste_probability == null ? '—' : `${Math.round(simulation.waste_probability * 100)}%`}</b></div><div><small>COST AT RISK</small><b>${fmt(risk?.total_potential_cost)}</b></div><p>Simulated outcomes only. These figures are not observed waste or guaranteed savings.</p>{modeledZero && <div className="zero-risk-explanation"><b>No waste estimated for this scenario.</b><span>Under this saved demand, date and FEFO allocation, the model estimated no unsold inventory. This does not mean actual waste is zero or indicate that food is safe.</span></div>}</div> : <EmptyState title="No saved risk scenario" description="Select a persisted forecast, then run or restore its linked scenario to calculate a seeded estimate."/>}
      </DataPanel>
    </section>
    {hasScenario && <DataPanel title="Ingredient drivers" description="Deterministic FEFO expiry exposure by ingredient, alongside the separate Monte Carlo estimate above.">
      {risks.some((item: any) => Number(item.at_risk_kg) > 0) ? <ResponsiveDataTable headers={['Ingredient','Batch','Expiry exposure','Expiry context','Potential cost']} rows={risks.filter((item: any) => Number(item.at_risk_kg) > 0).map((item: any) => [item.ingredient, String(item.batch_id).slice(0, 8), `${fmt(item.at_risk_kg)} kg`, `${item.days_until_use_by} days to use-by`, `$${fmt(item.potential_cost)}`])}/> : <EmptyState title={modeledZero ? 'No positive expiry exposure in this scenario' : 'No ingredient risk rows returned'} description={modeledZero ? 'The deterministic FEFO calculation found no batch-level expiry exposure for this forecast and scenario date.' : 'Review the saved scenario inputs and inventory records.'}/>}
      {risk?.assumptions?.length > 0 && <div className="assumption-list"><b>Risk assumptions</b><ul>{risk.assumptions.map((assumption: string) => <li key={assumption}>{assumption}</li>)}</ul></div>}
    </DataPanel>}
  </div>;
}

export function OptimizationWorkspace({ scenario, output, forecastId, onRun }: any) {
  const plan = output?.optimization;
  const items = plan?.items || [];
  const base = Number(plan?.baseline_shortage_kg || 0);
  const optimized = Number(plan?.optimized_shortage_kg || 0);
  const maximum = Math.max(base, optimized, .001);
  const maxOrder = Math.max(.001, ...items.map((item: any) => Number(item.order_kg || 0)));
  return <div className="route-stack">
    <section className="route-hero optimization-hero"><div><p className="eyebrow">CONSTRAINED PLANNING · HUMAN APPROVAL REQUIRED</p><h2>Compare service risk before reviewing a purchase proposal.</h2><p>Orders remain recommendations. Lead times, supplier limits, available stock and storage are shown from the persisted scenario.</p></div><button onClick={onRun} disabled={!forecastId}>Run / restore planning scenario</button></section>
    {plan ? <>
      <section className="comparison-panel"><div className="comparison-copy"><p className="eyebrow">BASELINE VS OPTIMIZED</p><h2>Shortage trade-off</h2><p>Both quantities use the same saved forecast demand and inventory snapshot.</p></div><div className="comparison-bars"><CompareBar label="Baseline shortage" value={base} max={maximum} tone="baseline"/><CompareBar label="Optimized shortage" value={optimized} max={maximum} tone="optimized"/></div><StatusBadge tone={plan.status === 'optimal' ? 'success' : 'warning'}>{plan.status || 'Status unavailable'}</StatusBadge></section>
      <DataPanel title="Ingredient purchase plan" description={`Scenario ${scenario?.id?.slice(0, 8) || '—'} · ${plan.diagnostics?.solver || 'solver details unavailable'} · no orders are executed.`}>
        {items.length ? <div className="purchase-list">{items.map((item: any) => <article className="purchase-item" key={item.ingredient}><div className="purchase-title"><div><b>{item.ingredient}</b><small>{item.supplier || 'No eligible priced supplier'}</small></div><StatusBadge tone={item.purchase_unavailable || item.lead_time_blocks_order ? 'warning' : 'success'}>{item.purchase_unavailable ? 'No supplier price' : item.lead_time_blocks_order ? 'Lead time blocks' : item.order_activated ? 'Minimum order' : 'Available'}</StatusBadge></div><div className="purchase-track" aria-label={`Recommended order ${fmt(item.order_kg)} kilograms`}><em style={{ width: `${Math.min(100, Number(item.order_kg || 0) / maxOrder * 100)}%` }}/></div><div className="purchase-meta"><span>Recommended <b>{fmt(item.order_kg)} kg</b></span><span>Shortage <b>{fmt(item.shortage_kg)} kg</b></span><span>Lead time <b>{item.lead_time_blocks_order ? 'Outside horizon' : 'Within horizon'}</b></span><span>Supplier minimum <b>{item.minimum_order_kg == null ? '—' : `${fmt(item.minimum_order_kg)} kg`}</b></span></div></article>)}</div> : <EmptyState title="No ingredient purchase rows" description="The solver returned no purchasable items for this scenario."/>}
        <div className="constraint-summary"><span>Storage capacity <b>{plan.diagnostics?.storage_capacity_kg == null ? '—' : `${fmt(plan.diagnostics.storage_capacity_kg)} kg`}</b></span><span>Projected surplus <b>{fmt(plan.diagnostics?.storage_surplus_kg)} kg</b></span><span>Preparation capacity <b>{plan.diagnostics?.preparation_capacity_hours == null ? 'Not configured' : `${fmt(plan.diagnostics.preparation_capacity_hours)} hours`}</b></span></div>
        <p className="disclaimer">{plan.warning || output.warning || 'Planning estimates require manager approval. No purchase or payment is made.'}</p>
      </DataPanel>
    </> : <EmptyState title="No optimization scenario selected" description="Run or restore a scenario linked to the selected persisted forecast to compare constrained plans."/>}
  </div>;
}

function CompareBar({ label, value, max, tone }: { label: string; value: number; max: number; tone: string }) { return <div className={`compare-bar ${tone}`}><div><span>{label}</span><b>{fmt(value)} kg</b></div><i><em style={{ width: `${Math.max(value > 0 ? 3 : 0, value / max * 100)}%` }}/></i></div>; }

export function ActionCenterWorkspace({ recommendations, busy, onDecision }: any) {
  const pending = recommendations.filter((item: any) => item.status === 'pending');
  const resolved = recommendations.filter((item: any) => item.status !== 'pending');
  return <div className="route-stack">
    <section className="route-hero action-hero"><div><p className="eyebrow">HUMAN-IN-THE-LOOP</p><h2>Every recommendation waits for your decision.</h2><p>Approvals and rejections are recorded locally for audit. Approval does not place an order, change inventory or contact a supplier.</p></div><div className="action-count"><b>{pending.length}</b><span>pending review</span></div></section>
    <DataPanel title="Needs your review" description="Review quantities and context before recording a decision.">
      {pending.length ? <div className="approval-grid">{pending.map((item: any) => <article className="approval-card" key={item.id}><div className="approval-heading"><StatusBadge tone="warning">Pending</StatusBadge><small>Recommendation {item.id.slice(0, 8)}</small></div><h3>{item.title}</h3><div className="approval-quantity"><b>{fmt(item.estimated_kg)} kg</b><span>planning quantity</span></div><p>Context: persisted local scenario proposal. Review linked Waste Radar and optimization details before acting.</p><div className="approval-actions"><button disabled={busy} onClick={() => onDecision(item, 'accepted')}>Approve locally</button><button className="secondary" disabled={busy} onClick={() => onDecision(item, 'rejected')}>Reject</button></div></article>)}</div> : <EmptyState title="Queue is clear" description="There are no pending recommendations. New proposals appear after a saved scenario completes."/>}
    </DataPanel>
    <DataPanel title="Decision history" description="Persisted recommendation status, including accepted and rejected proposals.">
      {resolved.length ? <ResponsiveDataTable headers={['Recommendation','Planning quantity','Decision','Recorded']} rows={resolved.map((item: any) => [item.title, `${fmt(item.estimated_kg)} kg`, <StatusBadge key={item.id} tone={item.status === 'accepted' ? 'success' : 'neutral'}>{item.status}</StatusBadge>, item.created_at ? new Date(item.created_at).toLocaleString() : '—'])}/> : <EmptyState title="No decisions recorded yet" description="Accepted or rejected recommendations will be listed here."/>}
    </DataPanel>
  </div>;
}

export function AnalyticsWorkspace({ scenarios, runs, forecast }: any) {
  const models = forecast?.evaluation?.models || forecast?.metrics || {};
  const names = Object.keys(models);
  const metricNames = ['mae', 'rmse', 'wape', 'bias'];
  const scenarioOutcomes = scenarios.map((scenario: any) => ({ scenario, waste: scenario.outputs?.monte_carlo?.expected_waste_kg, shortage: scenario.outputs?.optimization?.optimized_shortage_kg }));
  const maxWaste = Math.max(.001, ...scenarioOutcomes.map((item: any) => Number(item.waste || 0)));
  const maxShortage = Math.max(.001, ...scenarioOutcomes.map((item: any) => Number(item.shortage || 0)));
  return <div className="route-stack">
    <section className="analytics-banner"><div><p className="eyebrow">PERSISTED EVIDENCE</p><h2>Evidence before impact claims.</h2><p>Saved scenario estimates are simulations. No observed restaurant savings are reported here.</p></div><div className="evidence-stats"><span><b>{scenarios.length}</b> scenarios</span><span><b>{runs.length}</b> forecast runs</span></div></section>
    <DataPanel title="Forecast model comparison" description={forecast ? `Persisted evaluation for ${forecast.menu_item} · lower error is better for MAE/RMSE/WAPE; bias is directional.` : 'Select a persisted forecast run with saved evaluation metrics to compare candidates.'}>
      {names.length ? <div className="model-compare">{names.map(name => <article key={name}><div><b>{name.replaceAll('_', ' ')}</b><StatusBadge tone={name === forecast?.model ? 'success' : 'neutral'}>{name === forecast?.model ? 'Selected' : 'Compared'}</StatusBadge></div><dl>{metricNames.map(metric => <div key={metric}><dt>{metric.toUpperCase()}</dt><dd>{models[name]?.[metric] == null ? '—' : metric === 'wape' ? `${models[name][metric]}%` : models[name][metric]}</dd></div>)}</dl></article>)}</div> : <EmptyState title="No persisted model comparison" description="Model results will appear when the selected forecast includes chronological evaluation metrics."/>}
    </DataPanel>
    <DataPanel title="Persisted scenario outcomes" description="Saved simulated waste and optimized shortage outputs only. This visual compares records; it does not imply measured savings or a probability distribution.">
      {scenarioOutcomes.some((item: any) => item.waste != null || item.shortage != null) ? <div className="scenario-visuals">{scenarioOutcomes.filter((item: any) => item.waste != null || item.shortage != null).slice(0, 8).map((item: any) => <article key={item.scenario.id}><div className="scenario-visual-heading"><b>{String(item.scenario.forecast_run_id).slice(0, 8)}</b><small>{item.scenario.inputs?.as_of || 'Date unavailable'} · seed {item.scenario.seed}</small></div>{item.waste != null && <ScenarioBar label="Expected waste · simulated" value={Number(item.waste)} maximum={maxWaste} tone="waste"/>}{item.shortage != null && <ScenarioBar label="Optimized shortage" value={Number(item.shortage)} maximum={maxShortage} tone="shortage"/>}</article>)}</div> : <EmptyState title="No scenario outcome metrics available" description="Persisted risk and optimization outputs are required before this comparison can be drawn."/>}
    </DataPanel>
    <DataPanel title="Scenario evidence timeline" description="Most recent saved scenarios, with the date context, seed and trial count used to reproduce the simulation.">
      {scenarios.length ? <div className="timeline-list">{scenarios.map((item: any) => <article key={item.id}><div className="timeline-mark"/><div className="timeline-body"><div><b>Risk + optimization scenario</b><StatusBadge tone="neutral">Simulated</StatusBadge></div><p>Forecast <code>{String(item.forecast_run_id || '').slice(0, 8)}</code> · as of {item.inputs?.as_of || '—'} · seed {item.seed} · {item.inputs?.trials ?? '—'} trials</p><small>{item.created_at ? new Date(item.created_at).toLocaleString() : 'Timestamp unavailable'}</small></div></article>)}</div> : <EmptyState title="No saved scenarios yet" description="Persisted workflow runs will appear here; the page does not estimate missing impact values."/>}
    </DataPanel>
  </div>;
}

function ScenarioBar({ label, value, maximum, tone }: { label: string; value: number; maximum: number; tone: string }) { return <div className={`scenario-bar ${tone}`}><div><span>{label}</span><b>{fmt(value)} kg</b></div><i><em style={{ width: `${Math.min(100, value / maximum * 100)}%` }}/></i></div>; }

export function InventoryWorkspace({ ingredients, batches, forms, csv, onExport }: any) {
  const composition = ingredients.map((ingredient: any) => ({ name: ingredient.name, quantity: batches.filter((batch: any) => batch.ingredient === ingredient.name).reduce((sum: number, batch: any) => sum + Number(batch.quantity_kg || 0), 0) })).filter((row: any) => row.quantity > 0).sort((a: any, b: any) => b.quantity - a.quantity);
  const max = Math.max(1, ...composition.map((row: any) => row.quantity));
  const today = new Date().toISOString().slice(0, 10);
  const expiry = [...batches].sort((a: any, b: any) => String(a.use_by).localeCompare(String(b.use_by))).slice(0, 8);
  return <div className="route-stack">
    <section className="inventory-summary"><div><p className="eyebrow">INVENTORY LEDGER</p><h2>Know what is on hand and what needs attention.</h2><p>Saved quantities are shown in canonical kilograms. Use-by dates are surfaced without inferring food safety.</p></div>{onExport}</section>
    <div className="inventory-grid"><DataPanel title="Stock composition" description="Persisted batch quantities by ingredient.">{composition.length ? <div className="composition-list">{composition.map((row: any) => <div key={row.name}><div><b>{row.name}</b><span>{fmt(row.quantity)} kg</span></div><i><em style={{ width: `${row.quantity / max * 100}%` }}/></i></div>)}</div> : <EmptyState title="Inventory is empty" description="Create an ingredient and batch to see saved stock composition."/>}</DataPanel>
      <DataPanel title="Nearest use-by dates" description="Batches sorted by persisted use-by date; past dates are visibly marked.">{expiry.length ? <div className="expiry-timeline">{expiry.map((batch: any) => { const past = batch.use_by < today; return <article key={batch.id}><span className={past ? 'timeline-date past' : 'timeline-date'}>{shortDate(batch.use_by)}</span><div><b>{batch.ingredient}</b><small>{fmt(batch.quantity_kg)} kg · received {batch.received_on}</small></div><StatusBadge tone={past ? 'danger' : 'neutral'}>{past ? 'Past date' : 'Use-by'}</StatusBadge></article>; })}</div> : <EmptyState title="No batches recorded" description="Saved inventory batches will appear by use-by date."/>}</DataPanel></div>
    <DataPanel title="Add inventory records" description="Create the ingredient catalog entry first, then add a dated batch. Quantities remain API-validated."><div className="forms inventory-forms">{forms}</div></DataPanel>
    <DataPanel title="Import from CSV" description="Upload a validated inventory file. Import is atomic; review API validation feedback before correcting rejected rows.">{csv}</DataPanel>
    <DataPanel title="Saved inventory batches" description="Persisted batch records. No inventory is silently allocated or removed here.">{batches.length ? <ResponsiveDataTable headers={['Ingredient','On hand','Received','Use-by','Unit cost']} rows={batches.map((batch: any) => [batch.ingredient, `${fmt(batch.quantity_kg)} kg`, batch.received_on, batch.use_by, `$${fmt(batch.unit_cost)}`])}/> : <EmptyState title="No inventory batches" description="Create a batch or import a validated CSV to populate this ledger."/>}</DataPanel>
  </div>;
}

export function DataSettingsWorkspace({ suppliers, recipes, supplierForms, recipeForms }: any) {
  return <div className="route-stack">
    <section className="route-hero settings-hero"><div><p className="eyebrow">DATA & SYSTEM SETTINGS</p><h2>Keep the operating model grounded in your records.</h2><p>Recipes link sales forecasts to ingredient demand. Supplier links provide planning constraints only; there is no purchasing integration.</p></div><div className="settings-count"><b>{recipes.length}</b><small>saved recipes</small><b>{suppliers.length}</b><small>saved suppliers</small></div></section>
    <DataPanel title="Supplier directory" description="Supplier lead times and order minimums support local scenario planning only.">
      <div className="forms settings-forms">{supplierForms}</div>
      {suppliers.length ? <ResponsiveDataTable headers={['Supplier','Lead time','Minimum order','Linked ingredients']} rows={suppliers.map((supplier: any) => [supplier.name, `${supplier.lead_days} days`, `${fmt(supplier.minimum_order_kg)} kg`, (supplier.ingredients || []).map((ingredient: any) => ingredient.ingredient).join(', ') || 'No linked ingredients'])}/> : <EmptyState title="No suppliers recorded" description="Supplier records stay local and do not trigger contact or orders."/>}
    </DataPanel>
    <DataPanel title="Recipe catalog" description="Saved recipe ingredient quantities support demand translation. Missing links remain visible as missing data.">
      <div className="forms settings-forms">{recipeForms}</div>
      {recipes.length ? <div className="recipe-grid">{recipes.map((recipe: any) => <article key={recipe.id}><div className="recipe-mark" aria-hidden="true">✳</div><div><b>{recipe.name}</b><small>Yield {recipe.yield_servings} servings</small><p>{(recipe.ingredients || []).map((ingredient: any) => `${ingredient.ingredient} · ${fmt(ingredient.quantity_kg)} kg`).join('  /  ') || 'No ingredient associations saved.'}</p></div></article>)}</div> : <EmptyState title="No recipes recorded" description="Create a recipe, then link ingredients and per-yield quantities."/>}
    </DataPanel>
    <DataPanel title="Data provenance" description="This local application displays persisted records. Any seeded demo content is synthetic and modeled outcomes are simulations; neither represents observed restaurant savings."><span className="provenance-chip">Local SQLite · API-backed records</span></DataPanel>
  </div>;
}
