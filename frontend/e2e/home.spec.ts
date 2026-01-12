import { test, expect } from "@playwright/test";

test.describe("Home Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("displays hero section with title", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /MetamonMarket/i })
    ).toBeVisible();
  });

  test("displays feature cards", async ({ page }) => {
    await expect(page.getByText(/Copy Elite Traders/i)).toBeVisible();
    await expect(page.getByText(/Smart Risk Management/i)).toBeVisible();
  });

  test("has navigation links", async ({ page }) => {
    await expect(page.getByRole("link", { name: /Leaderboard/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /Portfolio/i })).toBeVisible();
  });

  test("browse traders button navigates to leaderboard", async ({ page }) => {
    await page.getByRole("link", { name: /Browse Traders/i }).first().click();
    await expect(page).toHaveURL(/\/leaderboard/);
  });

  test("displays stats section", async ({ page }) => {
    await expect(page.getByText(/Total Volume/i)).toBeVisible();
    await expect(page.getByText(/Active Traders/i)).toBeVisible();
  });
});
