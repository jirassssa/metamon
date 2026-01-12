import { test, expect } from "@playwright/test";

test.describe("Portfolio Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/portfolio");
  });

  test("shows connect wallet message when not connected", async ({ page }) => {
    await expect(page.getByText(/Connect Your Wallet/i)).toBeVisible();
  });

  test("displays wallet connection prompt", async ({ page }) => {
    await expect(
      page.getByText(/Connect your wallet to view your portfolio/i)
    ).toBeVisible();
  });
});

test.describe("Portfolio Page - Navigation", () => {
  test("navbar has portfolio link", async ({ page }) => {
    await page.goto("/");
    const portfolioLink = page.getByRole("link", { name: /Portfolio/i });
    await expect(portfolioLink).toBeVisible();
    await portfolioLink.click();
    await expect(page).toHaveURL(/\/portfolio/);
  });
});
