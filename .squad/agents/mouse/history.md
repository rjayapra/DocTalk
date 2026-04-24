# Mouse — History

## Project Context
- **Project:** DocTalk — Azure Docs Podcast Generator
- **Stack:** Python 3.10+, FastAPI, Azure OpenAI, Azure Speech, Azure Container Apps, Bicep, AZD
- **User:** rjayaprakash
- **Role:** Frontend Developer — building the web interface for podcast generation and playback

## Learnings

### 2026-04-24 — Webapp Frontend Implementation

- **Completed:** Full webapp build with `src/webapp/index.html`, `src/webapp/style.css`, `src/webapp/app.js`
- **Form UI:** URL input field with placeholder, style dropdown (Conversation/Lecture), submit button
- **Status display:** Real-time job status feedback with visual indicators (queued → scraping → generating_script → synthesizing → completed)
- **Audio player:** Native HTML5 `<audio>` element with controls; auto-populates when job completes with SAS URL from API response
- **Polling mechanism:** `setInterval` at 3-second intervals on `GET /jobs/{job_id}` until status is `completed` or `failed`
- **Error handling:** Graceful error messages displayed to user when job fails
- **Reset button:** "Generate Another" button to clear form and restart flow
- **Responsive design:** Mobile-first CSS with flexbox/grid; works on small screens (320px) and large displays
- **Accessibility:** WCAG AA color contrast, keyboard navigation support, semantic HTML
- **Dark mode:** CSS `prefers-color-scheme: dark` for automatic light/dark theme support

### Frontend Architecture (2025-01-24)
- **Tech stack:** Vanilla HTML/CSS/JS — no frameworks, build tools, or Node.js required
- **File location:** All webapp files in `src/webapp/` directory (index.html, style.css, app.js)
- **Serving:** FastAPI serves static files via StaticFiles mount at `/app` route
- **API integration:** Same-origin API calls to `/generate`, `/jobs/{id}`, `/jobs` endpoints
- **Job polling:** Uses `setInterval` with 3-second intervals on `/jobs/{job_id}` until status is completed/failed
- **Audio playback:** HTML5 `<audio>` element with SAS URLs from Azure Blob Storage

### Design System
- **Primary color:** Azure blue #0078D4 for branding consistency
- **Theme support:** CSS variables + `prefers-color-scheme: dark` for automatic dark/light mode
- **Typography:** System font stack (-apple-system, BlinkMacSystemFont, 'Segoe UI', ...)
- **Layout:** Card-based design with flexbox/grid for responsive behavior
- **Animations:** Smooth transitions, loading spinners, and slide-down effects for status updates

### User Experience Patterns
- **Status feedback:** Real-time polling with animated spinner shows job progress (queued → processing → completed)
- **Error handling:** User-friendly error messages with visual indicators
- **Recent podcasts:** Auto-loads on page load, refreshes after generation completes
- **Audio player:** Appears prominently when podcast is ready, supports auto-play (with fallback)
- **Mobile-first:** Responsive grid collapses to single column on mobile devices

### 2025-01-24 — Bug Fixes: Podcast Titles & Playback
- **Title display fix:** Implemented `getJobTitle(job)` helper that prioritizes `job.title` from API over URL-derived names
- **Custom podcast names:** Added optional "Podcast Name" text input field to generation form; included in POST /generate body
- **Play button fix (CRITICAL):** Replaced inline `onclick` handlers with event delegation using `data-audio-url` and `data-title` attributes
  - Previous approach: `onclick="playPodcast('${escapeHtml(url)}', ...)"` corrupted SAS URLs (& → &amp; broke query params)
  - New approach: Event delegation on `recentList` container reads raw data attributes, avoiding escaping issues
  - Ensures Azure Blob Storage SAS URLs with `&`, `?`, `=` characters work correctly
- **Pattern established:** Always use data attributes + event delegation for dynamic content with complex string values (URLs, JSON, etc.)

