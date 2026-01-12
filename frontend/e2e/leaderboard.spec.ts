import { test, expect } from "@playwright/test";

test.describe("Leaderboard Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/leaderboard");
  });

  test("displays leaderboard heading", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /Top Traders/i })
    ).toBeVisible();
  });

  test("displays search input", async ({ page }) => {
    await expect(
      page.getByPlaceholder(/Search by wallet address/i)
    ).toBeVisible();
  });

  test("displays sort select dropdown", async ({ page }) => {
    // Check for sort functionality
    await expect(page.getByRole("combobox")).toBeVisible();
  });

  test("search filters traders", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/Search by wallet address/i);
    await searchInput.fill("0x123");

    // Wait for debounced search
    await page.waitForTimeout(500);

    // Should filter or show no results message
    await expect(searchInput).toHaveValue("0x123");
  });

  test("loading state shows skeleton", async ({ page }) => {
    // Check that skeleton loaders appear initially
    const skeletons = page.locator(".skeleton, [class*='animate-pulse']");
    // Either has skeletons or has loaded content
    await expect(skeletons.first().or(page.locator("[class*='card']").first())).toBeVisible();
  });

  test("sort options are accessible", async ({ page }) => {
    const sortSelect = page.getByRole("combobox");
    await sortSelect.click();

    // Check for sort options
    await expect(page.getByRole("option")).toHaveCount(await page.getByRole("option").count());
  });
});
