import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

await mkdir('../design/screenshots', { recursive: true });
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:5173');
  await page.getByRole('button', { name: 'Run analysis' }).click();
  await page.getByText('Completed', { exact: true }).waitFor();
  await page.screenshot({ path: '../design/screenshots/bankops-live.png', fullPage: true });
  await page.getByRole('button', { name: 'AwardLens AU' }).click();
  await page.getByRole('button', { name: 'Load demo payroll' }).click();
  await page.getByRole('heading', { name: 'Audit results' }).waitFor();
  await page.screenshot({ path: '../design/screenshots/awardlens-live.png', fullPage: true });
} finally { await browser.close(); }
