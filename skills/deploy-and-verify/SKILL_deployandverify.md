---
name: deploy-and-verify
description: Comprehensive guide for deploying the ChaiMCP stack locally to Kind and remotely to GitHub Pages, followed by automated browser-based verification. Use this skill when the user wants to "deploy", "release", "ship", or "verify" the latest changes to the application.
---

# Deploy and Verify

## Overview

This skill standardizes the deployment and verification process for the ChaiMCP application. It covers:
1.  **Local Deployment**: Building and deploying to a local Kind cluster with automated testing.
2.  **Remote Deployment**: Pushing to GitHub to trigger CI/CD pipelines.
3.  **Verification**: Using a browser agent to validate the live application and generated reports.

## Prerequisites

-   Docker running
-   Kind cluster (`higgs-cluster`) active
-   `kubectl` configured
-   Python 3.10+ in `.venv`

## Workflow

### 1. Local Deployment (Kind)

The `deploy_local.sh` script automates the test-build-deploy loop.

```bash
./deploy_local.sh
```

**What it does:**
1.  Runs Unit Tests (`generate_report.py`). **ABORTS** if tests fail.
2.  Builds Docker image `chaimcp:latest`.
3.  Loads image into `higgs-cluster`.
4.  Applies Kubernetes manifests (Infrastructure & Application).
5.  Restarts the `chaimcp` deployment to pick up changes.

### 2. Remote Deployment (GitHub Pages)

Push changes to the `main` branch to trigger the GitHub Actions pipeline.

```bash
git add .
git commit -m "feat: Your descriptive commit message"
git push origin main
```

**What it does:**
1.  Triggers `.github/workflows/deploy.yml`.
2.  Sets up Python & Node environment.
3.  Runs Unit Tests & Generates `test_report.html`.
4.  Builds the static site.
5.  Deploys artifacts (including the test report) to GitHub Pages.

### 3. Verification & Recording

After deployment, use the **Browser Subagent** to verify the live sites.

**Tool Call:** `browser_subagent`

**Task Description:**
> "Navigate to https://mcpch.ai/, https://mcpch.ai/docs.html, and https://mcpch.ai/test_report.html. Verify that the pages load correctly, the SEO meta tags are present (view-source), and the Test Report shows a 100% pass rate. Take screenshots of each page."

**Verification Checklist:**
-   [ ] **Home Page**: Check for "Brewed for Blockchain" text and correct meta tags.
-   [ ] **Docs Page**: Ensure documentation loads.
-   [ ] **Test Report**: Confirm 100% Pass Rate and visuals.
-   [ ] **Recording**: The browser subagent automatically records the session. Embed this recording in the "Walkthrough" artifact if confirming success to the user.

## Troubleshooting

-   **Tests Fail**: Check `test_report.html` locally or in the console output. Fix the code before deploying.
-   **Kind Deployment Fails**: Ensure `higgs-cluster` is running (`kind get clusters`).
-   **Remote Deploy Fails**: Check GitHub Actions "Actions" tab for logs.

