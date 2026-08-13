import { expect, test } from "@playwright/test";

test("runs a grounded BankOps hybrid investigation", async ({ page }, testInfo) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Bank Operations Copilot" })).toBeVisible();

  await page.getByRole("button", { name: "Run analysis" }).click();

  await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  if (testInfo.project.name.startsWith("mobile")) {
    await page.getByRole("tab", { name: "Evidence" }).click();
  }
  await expect(page.getByRole("heading", { name: "Evidence" })).toBeVisible();
  await expect(page.getByRole("table")).toBeVisible();
  await page.getByRole("tab", { name: "Agent trace" }).click();
  await expect(page.getByText("evidence_verifier", { exact: true })).toBeVisible();
});

test("keeps mobile controls and details accessible", async ({ page }, testInfo) => {
  test.skip(!testInfo.project.name.startsWith("mobile"), "Mobile-only responsive assertion");
  await page.goto("/");

  await expect(page.getByRole("button", { name: "Bank Operations" })).toBeVisible();
  await expect(page.getByRole("button", { name: "AwardLens AU" })).toBeVisible();
  await page.getByRole("button", { name: "Run analysis" }).click();
  await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Evidence" }).click();
  await expect(page.getByRole("heading", { name: "Evidence" })).toBeVisible();
});
