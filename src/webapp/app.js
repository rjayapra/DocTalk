// State
let currentJobId = null;
let pollingInterval = null;

// DOM Elements
const generateForm = document.getElementById('generate-form');
const generateBtn = document.getElementById('generate-btn');
const statusSection = document.getElementById('status-section');
const statusTitle = document.getElementById('status-title');
const statusMessage = document.getElementById('status-message');
const playerSection = document.getElementById('player-section');
const audioPlayer = document.getElementById('audio-player');
const playerTitle = document.getElementById('player-title');
const recentList = document.getElementById('recent-list');

// Initialize app on page load
document.addEventListener('DOMContentLoaded', () => {
    loadRecentJobs();
    setupFormHandler();
    setupPlayButtonDelegation();
});

// Helper: Get job title (prefer job.title, fallback to URL-derived name)
function getJobTitle(job) {
    if (job.title && job.title.trim()) {
        return job.title.trim();
    }
    // Fallback to URL-based title
    return job.url ? new URL(job.url).pathname.split('/').pop() : 'Podcast';
}

// Setup event delegation for play buttons
function setupPlayButtonDelegation() {
    recentList.addEventListener('click', (e) => {
        const playButton = e.target.closest('.btn-play');
        if (!playButton || playButton.disabled) return;
        
        const audioUrl = playButton.dataset.audioUrl;
        const title = playButton.dataset.title;
        
        if (audioUrl && title) {
            playPodcast(audioUrl, title);
        }
    });
}

// Form submission handler
function setupFormHandler() {
    generateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(generateForm);
        const url = formData.get('url');
        const style = formData.get('style');
        const title = formData.get('title');
        
        await generatePodcast(url, style, title);
    });
}

// Generate podcast
async function generatePodcast(url, style, title) {
    try {
        // Disable form
        setFormLoading(true);
        hideError();
        hidePlayer();
        
        // Show status section
        showStatus('Submitting request...', 'Preparing your podcast generation');
        
        // Build request body
        const body = { url, style };
        if (title && title.trim()) {
            body.title = title.trim();
        }
        
        // Make API call
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Request failed: ${response.statusText}`);
        }
        
        const job = await response.json();
        currentJobId = job.id;
        
        // Start polling
        updateStatus(job);
        startPolling(job.id);
        
    } catch (error) {
        console.error('Generation error:', error);
        showError(`Failed to generate podcast: ${error.message}`);
        hideStatus();
        setFormLoading(false);
    }
}

// Poll job status
function startPolling(jobId) {
    // Clear any existing interval
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Poll every 3 seconds
    pollingInterval = setInterval(async () => {
        try {
            const job = await fetchJobStatus(jobId);
            updateStatus(job);
            
            // Stop polling if job is complete or failed
            if (job.status === 'completed' || job.status === 'failed') {
                clearInterval(pollingInterval);
                pollingInterval = null;
                setFormLoading(false);
                
                if (job.status === 'completed') {
                    showPlayer(job);
                    loadRecentJobs(); // Refresh recent list
                } else {
                    showError(`Podcast generation failed: ${job.error || 'Unknown error'}`);
                    hideStatus();
                }
            }
        } catch (error) {
            console.error('Polling error:', error);
            clearInterval(pollingInterval);
            pollingInterval = null;
            showError(`Failed to check job status: ${error.message}`);
            hideStatus();
            setFormLoading(false);
        }
    }, 3000);
}

// Fetch job status
async function fetchJobStatus(jobId) {
    const response = await fetch(`/jobs/${jobId}`);
    
    if (!response.ok) {
        throw new Error(`Failed to fetch job status: ${response.statusText}`);
    }
    
    return await response.json();
}

// Update status display
function updateStatus(job) {
    const statusMessages = {
        queued: {
            title: 'Queued',
            message: 'Your podcast is in the queue and will start processing soon',
        },
        processing: {
            title: 'Processing',
            message: 'Generating your podcast... This may take a few minutes',
        },
        completed: {
            title: 'Completed',
            message: 'Your podcast is ready!',
        },
        failed: {
            title: 'Failed',
            message: 'Podcast generation failed',
        },
    };
    
    const status = statusMessages[job.status] || statusMessages.queued;
    showStatus(status.title, status.message);
}

// Show status section
function showStatus(title, message) {
    statusTitle.textContent = title;
    statusMessage.textContent = message;
    statusSection.classList.remove('hidden');
}

// Hide status section
function hideStatus() {
    statusSection.classList.add('hidden');
}

// Show audio player
function showPlayer(job) {
    if (!job.audio_url) {
        console.error('No audio URL in job');
        return;
    }
    
    // Set audio source
    audioPlayer.src = job.audio_url;
    
    // Set title using helper
    const title = getJobTitle(job);
    playerTitle.textContent = `${title} (${job.style || 'conversation'})`;
    
    // Show player
    playerSection.classList.remove('hidden');
    
    // Hide status
    hideStatus();
    
    // Auto-play
    audioPlayer.play().catch(err => {
        console.log('Auto-play prevented:', err);
    });
}

// Hide audio player
function hidePlayer() {
    playerSection.classList.add('hidden');
    audioPlayer.pause();
    audioPlayer.src = '';
}

// Play podcast from recent list
function playPodcast(audioUrl, title) {
    audioPlayer.src = audioUrl;
    playerTitle.textContent = title;
    playerSection.classList.remove('hidden');
    
    // Scroll to player
    playerSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Auto-play
    audioPlayer.play().catch(err => {
        console.log('Auto-play prevented:', err);
    });
}

// Load recent jobs
async function loadRecentJobs() {
    try {
        const response = await fetch('/jobs?limit=20');
        
        if (!response.ok) {
            throw new Error(`Failed to load recent jobs: ${response.statusText}`);
        }
        
        const jobs = await response.json();
        renderRecentJobs(jobs);
        
    } catch (error) {
        console.error('Failed to load recent jobs:', error);
        recentList.innerHTML = `
            <div class="loading-placeholder">
                <p>⚠️ Failed to load recent podcasts</p>
            </div>
        `;
    }
}

// Render recent jobs
function renderRecentJobs(jobs) {
    if (!jobs || jobs.length === 0) {
        recentList.innerHTML = `
            <div class="loading-placeholder">
                <p>No podcasts yet. Generate your first one above!</p>
            </div>
        `;
        return;
    }
    
    recentList.innerHTML = jobs.map(job => createPodcastCard(job)).join('');
}

// Create podcast card HTML
function createPodcastCard(job) {
    const title = getJobTitle(job);
    const timestamp = formatTimestamp(job.created_at);
    const statusClass = `status-${job.status}`;
    const statusLabel = job.status.charAt(0).toUpperCase() + job.status.slice(1);
    
    const playButtonHtml = job.status === 'completed' && job.audio_url
        ? `<button class="btn-play" data-audio-url="${escapeHtml(job.audio_url)}" data-title="${escapeHtml(title)}">▶️ Play</button>`
        : `<button class="btn-play" disabled>Not Available</button>`;
    
    return `
        <div class="podcast-card">
            <div class="podcast-card-header">
                <h3 class="podcast-card-title">${escapeHtml(title)}</h3>
                <span class="podcast-status ${statusClass}">${statusLabel}</span>
            </div>
            <div class="podcast-card-meta">
                <div>Style: ${escapeHtml(job.style || 'conversation')}</div>
                <div>${timestamp}</div>
            </div>
            <div class="podcast-card-actions">
                ${playButtonHtml}
            </div>
        </div>
    `;
}

// Format timestamp
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown time';
    
    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        
        return date.toLocaleDateString();
    } catch (error) {
        return 'Unknown time';
    }
}

// Show error message
function showError(message) {
    // Remove existing error if any
    hideError();
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.id = 'error-message';
    errorDiv.textContent = message;
    
    generateForm.parentNode.appendChild(errorDiv);
}

// Hide error message
function hideError() {
    const existingError = document.getElementById('error-message');
    if (existingError) {
        existingError.remove();
    }
}

// Set form loading state
function setFormLoading(loading) {
    generateBtn.disabled = loading;
    
    const btnText = generateBtn.querySelector('.btn-text');
    if (loading) {
        btnText.textContent = 'Generating...';
    } else {
        btnText.textContent = 'Generate Podcast';
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
});
