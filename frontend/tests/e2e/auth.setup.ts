/**
 * Auth setup — runs once before all E2E tests.
 * Logs in as the test user and saves the browser storage state (cookies).
 */

import { test as setup, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const AUTH_FILE = "tests/e2e/.auth/user.json";

setup("authenticate", async ({ page }) => {
  // Ensure the .auth directory exists
  fs.mkdirSync(path.dirname(AUTH_FILE), { recursive: true });

  await page.goto("/login");

  // Fill login form using stable IDs (two "Sign In" buttons exist: tab switcher + submit)
  await page.locator("#login-username").fill(process.env.E2E_USERNAME ?? "testuser");
  await page.locator("#login-password").fill(process.env.E2E_PASSWORD ?? "Testpass123!");
  await page.locator('button[type="submit"]').click();

  // Wait for redirect to the chat page
  await expect(page).toHaveURL(/\/(chat|home|$)/, { timeout: 10_000 });

  // Save cookies/storage state for reuse
  await page.context().storageState({ path: AUTH_FILE });
});
