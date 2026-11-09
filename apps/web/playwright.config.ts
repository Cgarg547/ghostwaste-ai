import { defineConfig } from '@playwright/test';

const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:13001',
    browserName: 'chromium',
    launchOptions: { executablePath: chrome, args: ['--no-sandbox'] },
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'cd ../.. && .venv/bin/python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 18001',
      url: 'http://127.0.0.1:18001/health',
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: 'NEXT_DIST_DIR=.next-e2e BACKEND_ORIGIN=http://127.0.0.1:18001 npm run dev -- --hostname 127.0.0.1 --port 13001',
      url: 'http://127.0.0.1:13001',
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
