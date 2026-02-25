<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/43714a19-b904-4be1-9d64-553999757696

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## Python tests (content_os)

- Run Python tests from the `content_os` directory:
  - `cd content_os && python -m pytest -q`
- Running `pytest` from the repository root may fail due to import path differences.


## Unified operations runbook

- See [RUNBOOK.md](./RUNBOOK.md) for unified Node/Python/Publishing/SEO/CI execution steps.
