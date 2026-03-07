/**
 * E2E tests for the 6 critical user flows.
 * Auth state is pre-loaded from auth.setup.ts — no need to log in again.
 */

import { test, expect } from "@playwright/test";

// ── 1. Chat core loop ─────────────────────────────────────────────────────────

test("sends a message and receives a response", async ({ page }) => {
  await page.goto("/");

  const input = page.getByPlaceholder(/ask anything/i);
  await input.fill("What is a business rule in ServiceNow?");
  await input.press("Enter");

  // Thinking indicator appears while waiting
  await expect(page.getByText(/thinking|analyzing/i)).toBeVisible({ timeout: 5_000 });

  // Response appears (give LLM up to 30s)
  await expect(page.locator('[data-testid="message-bubble"]').last()).toBeVisible({
    timeout: 30_000,
  });
});

// ── 2. New conversation clears chat ───────────────────────────────────────────

test("new conversation button clears the message list", async ({ page }) => {
  await page.goto("/");

  // Send one message first
  await page.getByPlaceholder(/ask anything/i).fill("Hello");
  await page.getByPlaceholder(/ask anything/i).press("Enter");
  await page.waitForTimeout(2_000);

  // Click "New Chat" in the header — this calls newConversation() which clears state
  await page.locator('[data-testid="new-chat-btn"]').click();

  // Input should be empty and no messages visible
  await expect(page.getByPlaceholder(/ask anything/i)).toHaveValue("");
  const bubbles = page.locator('[data-testid="message-bubble"]');
  await expect(bubbles).toHaveCount(0);
});

// ── 3. Load a past conversation ───────────────────────────────────────────────

test("clicking a past conversation loads its messages", async ({ page }) => {
  await page.goto("/");

  // There should be at least one conversation in the sidebar from previous tests
  const convItem = page.locator('[data-testid="conversation-item"]').first();
  const count = await convItem.count();
  if (count === 0) {
    test.skip();
    return;
  }

  await convItem.click();

  // At least one message bubble should appear
  await expect(page.locator('[data-testid="message-bubble"]').first()).toBeVisible({
    timeout: 5_000,
  });
});

// ── 4. Instance badge reflects settings ───────────────────────────────────────

test("instance badge updates after saving settings", async ({ page }) => {
  await page.goto("/settings");

  // Find the instance URL field and fill it
  const urlField = page.getByLabel(/instance url|platform url/i);
  await urlField.fill("https://dev12345.service-now.com");

  await page.getByRole("button", { name: /save/i }).click();
  await expect(page.getByText(/saved|success/i)).toBeVisible({ timeout: 5_000 });

  // Go back to chat and verify badge
  await page.goto("/");
  await expect(page.getByText(/instance.*connected/i)).toBeVisible({ timeout: 5_000 });
});

// ── 5. Credit balance visible in sidebar ─────────────────────────────────────

test("credit balance is shown in the sidebar", async ({ page }) => {
  await page.goto("/");

  // Credits badge uses the Zap icon — look for the credits text
  const creditBadge = page.getByText(/credits/i).first();
  await expect(creditBadge).toBeVisible({ timeout: 5_000 });
});

// ── 6. Out-of-credits shows friendly error, not crash ────────────────────────

test("out-of-credits message is user-friendly", async ({ page, request }) => {
  // Drain the test user's credits via API (set balance to 0 by checking current approach)
  // This test is advisory — skip if we can't easily drain credits in E2E context
  // Instead, verify the error message text exists in the DOM when a 402 occurs
  // by intercepting the network response

  await page.goto("/");

  // Intercept the chat endpoint and force a 402
  await page.route("**/api/chat/message", (route) => {
    route.fulfill({
      status: 402,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Insufficient credits" }),
    });
  });

  await page.getByPlaceholder(/ask anything/i).fill("Will I get a nice error?");
  await page.getByPlaceholder(/ask anything/i).press("Enter");

  // Friendly error message should appear, not a blank screen or stack trace
  await expect(
    page.getByText(/run out of credits|insufficient credits|contact.*administrator/i)
  ).toBeVisible({ timeout: 5_000 });
});
