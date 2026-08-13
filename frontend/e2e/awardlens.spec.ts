import { expect, test } from "@playwright/test";

test("loads the AwardLens demo and runs a grounded findings question", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "AwardLens AU" }).click();
  await expect(page.getByRole("heading", { name: "AwardLens AU" })).toBeVisible();

  await page.getByRole("button", { name: "Load demo payroll" }).click();
  await expect(page.getByRole("heading", { name: "Audit results" })).toBeVisible();
  await expect(page.getByText("Manual review", { exact: true }).first()).toBeVisible();

  await page.getByRole("button", { name: "Ask AwardLens" }).click();
  await expect(page.getByText("Completed", { exact: true })).toBeVisible();
  await expect(page.getByText(/guarded read-only query returned/i)).toBeVisible();
});
