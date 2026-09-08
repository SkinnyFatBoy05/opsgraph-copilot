import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const assetRoot = process.env.OPSGRAPH_SHOWCASE_OUTPUT
  ? path.resolve(process.env.OPSGRAPH_SHOWCASE_OUTPUT)
  : path.resolve("../design/exports");
const rawDirectory = path.join(assetRoot, "raw-apple-capture");
const rawVideo = path.join(assetRoot, "OpsGraph_LinkedIn_Showcase_Apple_raw.webm");

const publicConfig = {
  profile: "aws-demo",
  model_provider: "fake",
  domains: ["bankops", "awardlens"],
  local_ingestion_enabled: false,
  max_tool_calls: 6,
  synthetic_only: true,
};

await fs.mkdir(rawDirectory, { recursive: true });
await fs.rm(rawVideo, { force: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  colorScheme: "light",
  deviceScaleFactor: 1,
  recordVideo: { dir: rawDirectory, size: { width: 1440, height: 1000 } },
  viewport: { width: 1440, height: 1000 },
});
const page = await context.newPage();
await page.route("**/api/v1/config", (route) => route.fulfill({ json: publicConfig }));

const flowIntro = await fs.readFile(new URL("./flow-intro.html", import.meta.url), "utf8");
await page.setContent(flowIntro, { waitUntil: "load" });
await page.waitForTimeout(10000);

await page.goto("http://127.0.0.1:5173", { waitUntil: "networkidle" });
await page.waitForTimeout(1800);

await page.getByRole("button", { name: "Run analysis" }).click();
await page.getByText("Completed", { exact: true }).waitFor();
await page.waitForTimeout(3600);

await page.getByRole("tab", { name: "Agent trace" }).click();
await page.getByText("evidence_verifier", { exact: true }).waitFor();
await page.waitForTimeout(2800);

await page.getByRole("button", { name: "AwardLens AU" }).click();
await page.waitForTimeout(900);
await page.getByRole("button", { name: "Load demo payroll" }).click();
await page.getByRole("heading", { name: "Audit results" }).waitFor();
await page.waitForTimeout(3900);

await page.getByRole("button", { name: "Evaluations" }).click();
await page.getByText("Release gate", { exact: true }).waitFor();
await page.waitForTimeout(4400);

const video = page.video();
await page.close();
await context.close();
await browser.close();

if (!video) throw new Error("Playwright did not create a video artifact.");
await fs.copyFile(await video.path(), rawVideo);
