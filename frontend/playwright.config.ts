import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ["html", { outputFolder: "../test-reports/playwright", open: "never" }],
    ["list"],
  ],
  use: {
    baseURL: "http://localhost:3000",
    // Store auth state between tests
    storageState: "tests/e2e/.auth/user.json",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    // Setup project: logs in and saves cookie state
    {
      name: "setup",
      testMatch: "**/auth.setup.ts",
      use: { storageState: undefined },
    },
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
      dependencies: ["setup"],
    },
  ],
  // Start backend + frontend before tests
  webServer: [
    {
      command: "uvicorn api.main:app --port 8000",
      url: "http://127.0.0.1:8000/docs",
      cwd: "..",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: "npm run dev",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
