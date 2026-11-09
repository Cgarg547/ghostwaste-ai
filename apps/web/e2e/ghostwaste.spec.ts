import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';

const token = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

async function apiPost(request: APIRequestContext, path: string, data?: unknown) {
  const response = await request.post(`/api${path}`, data === undefined ? {} : { data });
  expect(response.ok(), `${path}: ${await response.text()}`).toBeTruthy();
  return response.json();
}

async function createForecast(request: APIRequestContext, name: string, series: number[]) {
  const ingredient = await apiPost(request, '/ingredients', { name: `${name} ingredient`, storage_category: 'chilled' });
  const recipe = await apiPost(request, '/recipes', { name, yield_servings: 1 });
  await apiPost(request, `/recipes/${recipe.id}/ingredients`, { ingredient_id: ingredient.id, quantity_kg: 0.01 });
  for (let index = 0; index < series.length; index++) {
    await apiPost(request, '/sales', { menu_item: name, sold_on: `2026-10-${String(index + 1).padStart(2, '0')}`, quantity: series[index] });
  }
  const run = await apiPost(request, `/forecasts/${encodeURIComponent(name)}`, { horizon: 4, initial_train: 5 });
  const workflow = await apiPost(request, `/workflows/forecast/${run.id}`, { as_of: '2026-11-08', horizon_days: 4, trials: 50, seed: 731, storage_capacity_kg: 20 });
  return { run, scenarioId: workflow.scenario_id };
}

async function gotoSection(page: Page, label: string) {
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: label }).click();
}

test('restaurant setup through approval persists in the isolated database', async ({ page, request }) => {
  test.setTimeout(120_000);
  const suffix = token();
  const greens = `E2E greens ${suffix}`;
  const tomato = `E2E tomato ${suffix}`;
  const menu = `E2E market salad ${suffix}`;

  await page.goto('/');
  await gotoSection(page, 'Inventory');
  await page.getByRole('textbox', { name: 'Ingredient name' }).fill(greens);
  await page.getByRole('button', { name: 'Save ingredient' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Ingredient created locally.' })).toBeVisible();
  await page.getByRole('textbox', { name: 'Ingredient name' }).fill(tomato);
  await page.getByRole('button', { name: 'Save ingredient' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Ingredient created locally.' })).toBeVisible();

  for (const ingredient of [greens, tomato]) {
    const form = page.locator('form.formbox').filter({ hasText: 'Create inventory batch' });
    await form.getByLabel('Ingredient').selectOption({ label: ingredient });
    await form.getByLabel('Quantity (kg)').fill('0.1');
    await form.getByLabel('Unit cost').fill('2.5');
    await form.getByLabel('Received on').fill('2026-10-20');
    await form.getByLabel('Use-by').fill('2026-11-20');
    await form.getByRole('button', { name: 'Save batch' }).click();
    await expect(page.getByRole('status').filter({ hasText: 'Inventory batch saved locally.' })).toBeVisible();
  }

  await gotoSection(page, 'Data & settings');
  const supplier = `E2E farm ${suffix}`;
  const supplierForm = page.locator('form.formbox').filter({ hasText: 'Create supplier' });
  await supplierForm.getByLabel('Supplier name').fill(supplier);
  await supplierForm.getByLabel('Lead time (days)').fill('0');
  await supplierForm.getByLabel('Supplier minimum (kg)').fill('0');
  await supplierForm.getByRole('button', { name: 'Save supplier' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Supplier created locally.' })).toBeVisible();

  for (const ingredient of [greens, tomato]) {
    const form = page.locator('form.formbox').filter({ hasText: 'Link supplier ingredient' });
    await form.getByLabel('Supplier').selectOption({ label: supplier });
    await form.getByLabel('Ingredient').selectOption({ label: ingredient });
    await form.getByLabel('Purchase unit cost').fill('2.5');
    await form.getByRole('button', { name: 'Save supplier link' }).click();
    await expect(page.getByRole('status').filter({ hasText: 'Supplier ingredient link saved.' })).toBeVisible();
  }

  const recipeForm = page.locator('form.formbox').filter({ hasText: 'Create recipe' });
  await recipeForm.getByLabel('Recipe / menu item').fill(menu);
  await recipeForm.getByLabel('Recipe yield (servings)').fill('1');
  await recipeForm.getByRole('button', { name: 'Save recipe' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Recipe created locally.' })).toBeVisible();
  for (const ingredient of [greens, tomato]) {
    const form = page.locator('form.formbox').filter({ hasText: 'Link ingredient to recipe' });
    await form.locator('select').nth(0).selectOption({ label: menu });
    await form.locator('select').nth(1).selectOption({ label: ingredient });
    await form.getByLabel('Quantity per recipe (kg)').fill('0.01');
    await form.getByRole('button', { name: 'Save recipe link' }).click();
    await expect(page.getByRole('status').filter({ hasText: 'Recipe ingredient link saved.' })).toBeVisible();
  }

  await gotoSection(page, 'Forecasting');
  const salesForm = page.locator('form.formbox').filter({ hasText: 'Record daily sales' });
  for (let day = 1; day <= 12; day++) {
    await salesForm.getByLabel('Menu item').fill(menu);
    await salesForm.getByLabel('Sale date').fill(`2026-10-${String(day).padStart(2, '0')}`);
    await salesForm.getByLabel('Quantity sold').fill(String(12 + (day % 4)));
    await salesForm.getByRole('button', { name: 'Record sales' }).click();
    await expect(page.getByRole('status').filter({ hasText: 'Daily sales recorded locally.' })).toBeVisible();
  }
  const forecastForm = page.locator('form.compact-forecast-form');
  await forecastForm.getByLabel('Menu item').fill(menu);
  await forecastForm.getByRole('button', { name: 'Generate & save forecast' }).click();
  await expect(page.getByText(`Selected persisted forecast: ${menu}`)).toBeVisible();
  await expect(page.locator('.timeseries [data-chart-point]')).toHaveCount(19);

  await gotoSection(page, 'Waste Radar');
  await page.getByRole('button', { name: 'Run / restore selected scenario' }).click();
  await expect(page.getByText(/Saved scenario/)).toBeVisible();
  const scenarios = await (await request.get('/api/risk-scenarios')).json();
  const selectedRunId = await page.evaluate(() => localStorage.getItem('ghostwaste:selectedForecastId'));
  const linked = scenarios.find((item: any) => item.forecast_run_id === selectedRunId);
  expect(linked).toBeTruthy();
  expect(linked.outputs.provenance).toBe('simulated_forecast_recipe_inventory');
  expect(linked.outputs.optimization.status).toBe('optimal');

  await gotoSection(page, 'Action Center');
  const cards = page.locator('.approval-card');
  await expect(cards).toHaveCount(2);
  const recommendationIds = await cards.locator('.approval-heading small').allTextContents();
  await cards.nth(0).getByRole('button', { name: 'Approve locally' }).click();
  await page.getByRole('alertdialog').getByRole('button', { name: 'Approve locally' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Approval recorded locally.' })).toBeVisible();
  await gotoSection(page, 'Action Center');
  await page.locator('.approval-card').first().getByRole('button', { name: 'Reject' }).click();
  await page.getByRole('alertdialog').getByRole('button', { name: 'Reject locally' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Rejection recorded locally.' })).toBeVisible();

  const savedRecommendations = await (await request.get('/api/recommendations')).json();
  const ids = recommendationIds.map(text => text.replace('Recommendation ', ''));
  const decisions = savedRecommendations.filter((item: any) => ids.some((id: string) => item.id.startsWith(id)));
  expect(decisions.map((item: any) => item.status).sort()).toEqual(['accepted', 'rejected']);
  const audit = await (await request.get('/api/audit-events')).json();
  expect(audit.some((item: any) => item.event_type === 'recommendation_accepted')).toBeTruthy();
  expect(audit.some((item: any) => item.event_type === 'recommendation_rejected')).toBeTruthy();
});

test('rapid switching keeps forecast chart, metrics and linked scenario aligned', async ({ page, request }) => {
  const runA = await createForecast(request, `Switch A ${token()}`, [4, 8, 5, 9, 6, 10, 7, 11, 8, 12, 9, 13]);
  const runB = await createForecast(request, `Switch B ${token()}`, [25, 23, 22, 21, 18, 16, 15, 12, 10, 8, 7, 5]);
  await page.goto('/forecasting');
  const selector = page.getByRole('combobox', { name: 'Select persisted forecast run' });
  await expect.poll(() => selector.locator('option').count()).toBeGreaterThanOrEqual(3);
  await page.route('**/api/sales?menu_item=*', async route => {
    if (route.request().url().includes(encodeURIComponent(runA.run.menu_item))) {
      await new Promise(resolve => setTimeout(resolve, 900));
    }
    await route.continue();
  });
  await selector.selectOption(runA.run.id);
  await selector.selectOption(runB.run.id);
  await expect(page.getByText(`Selected persisted forecast: ${runB.run.menu_item}`)).toBeVisible();
  const modelText = String(runB.run.model).replaceAll('_', ' ');
  await expect(page.locator('.forecastMeta')).toContainText(modelText);
  const selectedMetric = runB.run.evaluation.models[runB.run.model].mae;
  await expect(page.locator('[aria-label="Selected model evaluation"]')).toContainText(String(selectedMetric));
  const points = page.locator('.timeseries [data-chart-point]');
  await expect(points).toHaveCount(16);
  await expect(points.first()).toHaveAttribute('aria-label', /Historical demand,.*25\.0 servings per day/);
  await expect(points.last()).toHaveAttribute('aria-label', /Forecast demand/);
  await expect.poll(() => page.evaluate(() => localStorage.getItem('ghostwaste:selectedScenarioId'))).toBe(runB.scenarioId);
  await page.waitForTimeout(1000);
  await expect(page.getByText(`Selected persisted forecast: ${runB.run.menu_item}`)).toBeVisible();
  await expect(page.locator('[aria-label="Selected model evaluation"]')).toContainText(String(selectedMetric));
  await gotoSection(page, 'Waste Radar');
  await expect(page.getByText(`Saved scenario ${runB.scenarioId.slice(0, 8)}`)).toBeVisible();
  expect((await (await request.get(`/api/risk-scenarios/${runB.scenarioId}`)).json()).forecast_run_id).toBe(runB.run.id);
});

test('all 13 routes fit exact desktop, tablet and mobile widths with reduced motion', async ({ page }) => {
  test.setTimeout(90_000);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const evidence = process.env.GHOSTWASTE_E2E_EVIDENCE_DIR;
  if (evidence) mkdirSync(evidence, { recursive: true });
  const widths=(process.env.GHOSTWASTE_E2E_WIDTHS || '390,768,1024,1280,1440,1600').split(',').map(Number);
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of ['/', '/inventory', '/forecasting', '/waste-radar', '/optimization', '/actions', '/analytics', '/settings', '/assistant', '/scenario-studio', '/impact-studio', '/use-first', '/daily-plan']) {
      await page.goto(route);
      await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible();
      const overflow = await page.evaluate(() => ({ body: document.body.scrollWidth, viewport: window.innerWidth }));
      expect(overflow.body, `${route} at ${width}px has horizontal overflow`).toBeLessThanOrEqual(overflow.viewport);
      const reducedMotion = await page.evaluate(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
      expect(reducedMotion).toBeTruthy();
      const contrast = await page.evaluate(() => {
        const luminance = (color: string) => {
          const channels = color.match(/[\d.]+/g)?.slice(0, 3).map(Number) || [0, 0, 0];
          const linear = channels.map(value => { const channel = value / 255; return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4; });
          return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2];
        };
        const result: Record<string, number> = {};
        for (const selector of ['h1', '.sub']) {
          const element = document.querySelector(selector);
          if (!element) continue;
          const foreground = getComputedStyle(element).color;
          let ancestor: Element | null = element;
          let background = 'rgb(247, 250, 247)';
          while (ancestor) {
            const candidate = getComputedStyle(ancestor).backgroundColor;
            if (candidate !== 'rgba(0, 0, 0, 0)' && candidate !== 'transparent') { background = candidate; break; }
            ancestor = ancestor.parentElement;
          }
          const a = luminance(foreground), b = luminance(background);
          result[selector] = (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
        }
        return result;
      });
      expect(contrast.h1, `${route} heading contrast`).toBeGreaterThanOrEqual(4.5);
      expect(contrast['.sub'], `${route} description contrast`).toBeGreaterThanOrEqual(4.5);
      if (route === '/forecasting') {
        const chart = page.locator('.timeseries');
        if (await chart.count()) {
          const clipping = await chart.evaluate(element => element.scrollWidth <= element.clientWidth + 1);
          expect(clipping, `forecast chart clipped at ${width}px`).toBeTruthy();
        }
      }
      // Viewport capture is deliberate: 78 full-page captures made the isolated
      // smoke run exceed its bounded execution window without adding layout signal.
      if (evidence) await page.screenshot({ path: join(evidence, `chrome-${width}-${route === '/' ? 'overview' : route.slice(1).replaceAll('/', '-')}.png`) });
    }
  }
});

test('keyboard focus exposes the same forecast point tooltip as pointer hover', async ({ page, request }) => {
  const { run } = await createForecast(request, `Accessible chart ${token()}`, [3, 5, 4, 8, 6, 9, 8, 10, 9, 11, 10, 12]);
  await page.goto('/forecasting');
  const selector = page.getByRole('combobox', { name: 'Select persisted forecast run' });
  await selector.selectOption(run.id);
  await selector.focus();
  let pointId: string | null = null;
  for (let index = 0; index < 40 && pointId === null; index++) {
    await page.keyboard.press('Tab');
    pointId = await page.evaluate(() => {
      const value = document.activeElement?.getAttribute('data-chart-point');
      return value?.startsWith('Forecast demand') ? value : null;
    });
  }
  expect(pointId, 'keyboard tab order should reach a forecast point').toBeTruthy();
  const point = page.locator(`[data-chart-point="${pointId}"]`);
  await expect(point).toBeFocused();
  await expect(page.locator('#forecast-chart-tooltip')).toContainText('Forecast demand');
  await expect(point).toHaveAttribute('aria-describedby', 'forecast-chart-tooltip');
  const accessibility = await point.evaluate(element => {
    const style = getComputedStyle(element);
    return { label: element.getAttribute('aria-label'), filter: style.filter, outline: style.outlineStyle };
  });
  expect(accessibility.label).toMatch(/saved planning bounds/);
  expect(accessibility.filter).toContain('drop-shadow');
  await point.hover();
  await expect(page.locator('#forecast-chart-tooltip')).toContainText('Saved planning bounds');
});

test('intelligence workspaces calculate locally and preserve browser task state', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Load demo data' }).click();
  await gotoSection(page, 'AI Assistant');
  await page.getByRole('button', { name: 'Which ingredients should I use first?' }).click();
  await expect(page.getByText('GhostWaste Intelligence').last()).toBeVisible();
  await gotoSection(page, 'Scenario Studio');
  await page.getByRole('button', { name: 'Run simulation' }).click();
  await expect(page.getByText(/EPHEMERAL/)).toBeVisible();
  await gotoSection(page, 'Use-First Planner');
  await expect(page.getByText('Smart Use-First Planner')).toBeVisible();
  await gotoSection(page, 'Impact Studio');
  await page.getByRole('button', { name: 'Compare baseline and lower-demand plan' }).click();
  await expect(page.getByText(/Compatible seeded Monte Carlo/)).toBeVisible();
  await gotoSection(page, 'Daily Action Plan');
  const task = page.locator('.action-item input[type=checkbox]').first();
  if (await task.count()) { await task.check(); await page.reload(); await expect(task).toBeChecked(); await task.uncheck(); await page.reload(); await expect(task).not.toBeChecked(); }
});

test('daily action plan degrades safely when browser storage is blocked', async ({ page }) => {
  await page.addInitScript(() => Object.defineProperty(window, 'localStorage', { configurable: true, get: () => { throw new DOMException('blocked', 'SecurityError'); } }));
  await page.goto('/daily-plan');
  await expect(page.getByText('Browser storage is unavailable; task checks will not survive refresh.')).toBeVisible();
});
