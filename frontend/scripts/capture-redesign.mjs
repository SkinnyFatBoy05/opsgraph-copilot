import { chromium } from "@playwright/test";
import path from "node:path";

const output = path.resolve("../design/screenshots");
const publicConfig = {
  profile: "aws-demo",
  model_provider: "fake",
  domains: ["bankops", "awardlens"],
  local_ingestion_enabled: false,
  max_tool_calls: 6,
  synthetic_only: true,
};

async function preparePage(context) {
  const page = await context.newPage();
  await page.route("**/api/v1/config", (route) => route.fulfill({ json: publicConfig }));
  await page.goto("http://127.0.0.1:5173", { waitUntil: "networkidle" });
  return page;
}

const browser = await chromium.launch({ headless: true });

const desktop = await browser.newContext({
  colorScheme: "light",
  deviceScaleFactor: 1,
  reducedMotion: "reduce",
  viewport: { width: 1440, height: 1080 },
});
const desktopPage = await preparePage(desktop);

await desktopPage.getByRole("button", { name: "Run analysis" }).click();
await desktopPage.getByText("Completed", { exact: true }).waitFor();
await desktopPage.screenshot({ path: path.join(output, "bankops-live.png") });

await desktopPage.getByRole("button", { name: "AwardLens AU" }).click();
await desktopPage.getByRole("button", { name: "Load demo payroll" }).click();
await desktopPage.getByRole("heading", { name: "Audit results" }).waitFor();
await desktopPage.waitForTimeout(450);
await desktopPage.screenshot({ path: path.join(output, "awardlens-live.png") });

await desktopPage.getByRole("button", { name: "Evaluations" }).click();
await desktopPage.getByText("Release gate", { exact: true }).waitFor();
await desktopPage.waitForTimeout(450);
await desktopPage.screenshot({ path: path.join(output, "evaluations-live.png") });
await desktop.close();

const mobile = await browser.newContext({
  colorScheme: "light",
  deviceScaleFactor: 1,
  isMobile: true,
  reducedMotion: "reduce",
  viewport: { width: 430, height: 932 },
});
const mobilePage = await preparePage(mobile);
await mobilePage.getByRole("button", { name: "Run analysis" }).click();
await mobilePage.getByText("Completed", { exact: true }).waitFor();
await mobilePage.screenshot({ path: path.join(output, "bankops-mobile.png") });
await mobile.close();

await browser.close();
