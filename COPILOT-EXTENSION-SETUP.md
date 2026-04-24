# DocTalk Copilot Extension — Setup Guide

Register DocTalk as a GitHub Copilot Extension to stream podcast generation directly from Copilot Chat.

---

## Prerequisites

Before you start, you'll need:

- **GitHub Account** — Personal or org account with access to create GitHub Apps
- **GitHub Copilot** — Enabled in VS Code or on github.com
- **Admin or Developer access** to your GitHub account/organization
- **Deployed API endpoint** — `https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io`

---

## Step 1: Create a GitHub App

### 1.1 Navigate to GitHub Settings

1. Go to **GitHub Settings** → **Developer settings** → **[GitHub Apps](https://github.com/settings/apps)**
2. Click **"New GitHub App"**

### 1.2 Configure App Details

Fill in the following fields:

| Field | Value | Notes |
|-------|-------|-------|
| **GitHub App name** | `DocTalk` (or `docktalk-{your-username}` if taken) | Avoid spaces; use hyphens |
| **Homepage URL** | `https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io` | Must match deployed endpoint |
| **Webhook** | Leave **unchecked** | Not needed for Copilot Extensions |
| **Callback URL** | (leave blank if not using OAuth flow) | For hackathon, not required |
| **User authorization callback URL** | (optional) | Skip for this demo |
| **Setup URL** | (optional) | Skip for this demo |

### 1.3 Permissions & Scope

For a Copilot Extension (agent), minimal permissions are needed:

- **Repository permissions** — None (read-only by default)
- **Organization permissions** — None
- **User permissions** — None
- **Account permissions** — None

> **Why minimal?** DocTalk only reads public Microsoft Learn URLs and submits jobs — it doesn't need repo access.

### 1.4 Get Your Credentials

After creating the app, you'll see:

- **App ID** — Note this down
- **Client ID** — Available under "About" (copy and save)
- **Client Secret** — Generate one under "Client secrets" (save securely)
- **Private key** — Generate a PEM key under "Private keys" (save securely; not needed for hackathon)
- **Webhook secret** — (optional, not used here)

**Save these values safely** — you'll need the Client ID and Client Secret if setting up OAuth flows later.

---

## Step 2: Configure as a Copilot Extension

### 2.1 Set the Inference Description

In your GitHub App settings:

1. Scroll to **"Copilot Agent"** section (if visible) or skip to Step 3 if not available yet
2. Set **Agent Type**: `Agent`
3. Set **Agent Inference Description**:
   ```
   Convert Azure documentation pages into engaging podcast audio. 
   Supports single-narrator summary or two-host conversational discussion. 
   Submit Microsoft Learn URLs and stream podcast generation status.
   ```

> **Note**: If the Copilot Agent section isn't visible, it may appear after GitHub enables it for your app. You can configure it after installation.

### 2.2 Copilot Chat Endpoint Configuration

Your app's agent endpoint is:

```
https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/copilot/agent
```

This endpoint:
- **GET /copilot/agent** — Returns agent metadata (name, description, version)
- **POST /copilot/agent** — Accepts Copilot chat messages and streams SSE responses

---

## Step 3: Install the GitHub App

### 3.1 Install on Your Account or Organization

1. Go back to your GitHub App page
2. Under **"Install App"** (left sidebar), click **"Install"**
3. Select your **personal account** or **organization** where you'll use DocTalk
4. Grant **All repositories** (or limit to specific repos if preferred)
5. Confirm the installation

### 3.2 Authorize Copilot Chat Access

1. In VS Code or github.com, open **Copilot Chat**
2. Use the settings/menu to enable extensions for your account
3. DocTalk should now appear in your available extensions/agents

---

## Step 4: Test the Extension

### 4.1 Open Copilot Chat

**VS Code:**
- Click the Copilot Chat icon (sidebar)
- Or press `Ctrl+Shift+I` (Windows/Linux) / `Cmd+Shift+I` (Mac)

**github.com:**
- Open any repo or issue
- Click "Copilot" → "Copilot Chat"

### 4.2 Test the Help Command

Type in the chat:

```
@doctalk help
```

**Expected response:**
```
DocTalk Copilot Extension — Convert Azure docs into podcast audio

Usage:
  @doctalk help                             Show this help message
  @doctalk generate <url>                   Generate a podcast from a Microsoft Learn URL
  @doctalk generate <url> --style single    Generate single-narrator summary
  @doctalk generate <url> --style conversation  Two-host conversation (default)
  @doctalk status <job_id>                  Check job status

Example:
  @doctalk generate https://learn.microsoft.com/en-us/azure/container-apps/overview
```

### 4.3 Test Podcast Generation

Type in the chat:

```
@doctalk generate https://learn.microsoft.com/en-us/azure/container-apps/overview
```

**Expected behavior:**
1. Copilot Chat shows: `🎙️ Submitting podcast generation job...`
2. After ~2–5 seconds, you'll see streaming SSE messages:
   ```
   Extracting content from Microsoft Learn page...
   Generating podcast script using Azure OpenAI...
   Synthesizing audio with Azure Speech Services...
   Processing voice #1 (Alex)...
   Processing voice #2 (Sam)...
   Finalizing podcast MP3...
   ✅ Podcast ready: https://...(blob storage URL)
   ```

### 4.4 Try Other Examples

**Single-narrator mode:**
```
@doctalk generate https://learn.microsoft.com/en-us/azure/functions/functions-overview --style single
```

**Check job status:**
```
@doctalk status {job_id}
```

---

## Step 5: Troubleshooting

### Issue: `403 Forbidden` or `Unauthorized`

**Cause**: Missing or invalid `X-GitHub-Token` header.

**Solution**:
- Ensure Copilot Chat is authenticated with GitHub
- Log out and log in again in VS Code
- Check that the GitHub App is installed on your account

### Issue: No response or timeout

**Cause**: API endpoint is slow or unreachable.

**Solution**:
- Verify the endpoint is live: `curl https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/health`
- Check Azure Container Apps logs for errors
- Ensure your network doesn't block the endpoint

### Issue: "Agent not found" or extension doesn't appear

**Cause**: GitHub App not installed or Copilot Chat not refreshed.

**Solution**:
- Reinstall the GitHub App (uninstall and reinstall)
- Restart VS Code or refresh github.com
- Wait 1–2 minutes for GitHub to sync the app

### Issue: Extension appears but doesn't respond

**Cause**: POST endpoint not configured correctly.

**Solution**:
- Verify the endpoint URL is: `https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/copilot/agent`
- Check that the API is running: `curl -X POST https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/copilot/agent -H "Content-Type: application/json" -d '{"message": "help"}'`

### Issue: Podcast generation fails with "Invalid URL"

**Cause**: URL is not a Microsoft Learn page or is not public.

**Solution**:
- Ensure the URL is from `learn.microsoft.com`
- Test with the example: `https://learn.microsoft.com/en-us/azure/container-apps/overview`
- Some pages may require authentication; try a different page

---

## Demo Script (2 minutes)

Use this script for the hackathon demo:

### Setup (30 seconds)
1. Open VS Code with Copilot Chat enabled
2. Show the GitHub App installed: Settings → Extensions → DocTalk is listed
3. Open Copilot Chat pane (Ctrl+Shift+I)

### Demo Flow (90 seconds)

**Narration**: *"Today, we're introducing DocTalk — a Copilot Extension that converts Azure documentation into podcast audio, so you can learn on the go."*

**Action 1** (30 seconds):
```
Type: @doctalk help
Show: The help menu appears, listing all available commands
Narration: "DocTalk is now integrated directly into Copilot Chat. 
           Here are the commands we support — help, generate with options, and status checks."
```

**Action 2** (60 seconds):
```
Type: @doctalk generate https://learn.microsoft.com/en-us/azure/container-apps/overview
Show: Live SSE streaming messages as the podcast is generated:
      - Extracting content...
      - Generating script...
      - Synthesizing audio...
      - Final MP3 link
      
Narration: "Now we're generating a podcast from the Container Apps overview page. 
           Behind the scenes, DocTalk is scraping the docs, using Azure OpenAI to write 
           a conversational script with two hosts (Alex and Sam), and then synthesizing 
           audio with Azure Speech Services.
           
           The entire process streams back to Copilot Chat in real time, so you can 
           see exactly what's happening."
```

### Closing (optional, 30 seconds)
```
Download the MP3: Click the blob storage URL in the final message
Play it: Show the podcast audio in action (optional, if time permits)
Narration: "The result is a professional-sounding podcast that you can download 
           and listen to offline. Perfect for learning while commuting or exercising."
```

---

## What's Happening Under the Hood

When you type `@doctalk generate <url>` in Copilot Chat:

1. **Copilot Chat** → Sends your message to the GitHub App's registered endpoint
2. **DocTalk API** (POST /copilot/agent) → Validates the request, extracts the URL
3. **API** → Submits a podcast generation job to the Azure Queue
4. **API** → Opens a **Server-Sent Events (SSE)** stream back to Copilot Chat
5. **Worker** (async) → Scrapes the page, generates the script, synthesizes audio
6. **Worker** → Sends progress updates to the SSE stream (extracted, script done, audio done, etc.)
7. **Copilot Chat** → Displays each SSE message as it arrives
8. **Blob Storage** → Stores the final MP3 file
9. **SSE Stream** → Closes with a link to the generated podcast

---

## Security Notes

### For the Hackathon Demo

- **Auth**: The API checks that `X-GitHub-Token` header is present (value doesn't matter for hackathon)
- **No validation**: For the demo, we don't validate the token (GitHub will inject it)
- **Production**: Before shipping, implement JWT validation to confirm the token came from GitHub

### Authentication Flow (Prod)

1. GitHub injects `X-GitHub-Token` header with a JWT
2. DocTalk API validates the JWT using GitHub's public key
3. Token includes user info, app ID, and expiration
4. If invalid, return 401 Unauthorized

---

## Next Steps

1. **Install the GitHub App** on your personal account or org (Step 3)
2. **Test the extension** in Copilot Chat (Step 4)
3. **Run the demo script** during the hackathon (Demo Script section)
4. **Collect feedback** on user experience, speed, and audio quality
5. **Iterate** based on feedback before production release

---

## Questions?

- **API Issues?** Check Azure Container Apps logs
- **GitHub App Issues?** Review GitHub Developer settings
- **Copilot Chat Integration?** Check your GitHub account's Copilot settings

Good luck with the hackathon! 🎙️✨
