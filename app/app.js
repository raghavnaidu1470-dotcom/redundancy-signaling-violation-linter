/**
 * Interactive Client Application for Multimedia Cognitive Linter
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const videoPlayer = document.getElementById("video-player");
  const currentVideoTitle = document.getElementById("current-video-title");
  const violationsList = document.getElementById("violations-list");
  const violationCountBadge = document.getElementById("violation-count-badge");
  const timelineTrack = document.getElementById("timeline-track");
  const timelineTrackWrapper = document.getElementById("timeline-track-wrapper");
  const timelinePlayhead = document.getElementById("timeline-playhead");
  const timelineCurrentTime = document.getElementById("timeline-current-time");
  const timelineTotalTime = document.getElementById("timeline-total-time");
  const progressContainer = document.getElementById("progress-container");
  const progressStatusText = document.getElementById("progress-status-text");

  // Tab buttons
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  // Sample tab
  const sampleSelect = document.getElementById("sample-select");
  const btnLoadSample = document.getElementById("btn-load-sample");

  // Upload tab
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const btnBrowse = document.getElementById("btn-browse");
  const selectedFileName = document.getElementById("selected-file-name");
  const uploadDuration = document.getElementById("upload-duration");
  const btnRunUpload = document.getElementById("btn-run-upload");

  // URL tab
  const urlInput = document.getElementById("url-input");
  const urlDuration = document.getElementById("url-duration");
  const btnRunUrl = document.getElementById("btn-run-url");

  let currentViolations = [];
  let selectedUploadFile = null;

  // -------------------------------------------------------------
  // 1. Tab Switching
  // -------------------------------------------------------------
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });

  // -------------------------------------------------------------
  // 2. Load Pre-indexed Samples
  // -------------------------------------------------------------
  async function fetchSamples() {
    try {
      const response = await fetch("/api/samples");
      if (!response.ok) throw new Error("Failed to load samples");
      const data = await response.json();

      sampleSelect.innerHTML = "";
      if (!data.samples || data.samples.length === 0) {
        sampleSelect.innerHTML = '<option value="" disabled>No benchmark samples found</option>';
        return;
      }

      data.samples.forEach(sample => {
        const option = document.createElement("option");
        option.value = sample.stem;
        option.textContent = `${sample.title} (${sample.violations_count} potential violations)`;
        sampleSelect.appendChild(option);
      });

      // Automatically load the first sample by default
      if (data.samples.length > 0) {
        loadSample(data.samples[0].stem);
      }
    } catch (err) {
      sampleSelect.innerHTML = `<option value="" disabled>Error: ${err.message}</option>`;
    }
  }

  async function loadSample(stem) {
    if (!stem) return;
    showProgress("Loading pre-analyzed sample results...");

    try {
      const response = await fetch(`/api/results?video=${encodeURIComponent(stem)}`);
      if (!response.ok) throw new Error("Failed to load results");
      const result = await response.json();

      // Set video source
      videoPlayer.src = `/media/video?stem=${encodeURIComponent(stem)}`;
      currentVideoTitle.textContent = stem;

      renderViolations(result.violations || []);
    } catch (err) {
      alert(`Could not load sample: ${err.message}`);
    } finally {
      hideProgress();
    }
  }

  btnLoadSample.addEventListener("click", () => {
    const stem = sampleSelect.value;
    loadSample(stem);
  });

  // -------------------------------------------------------------
  // 3. Dropzone & File Upload
  // -------------------------------------------------------------
  btnBrowse.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("click", (e) => {
    if (e.target !== btnBrowse) fileInput.click();
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  function handleFileSelected(file) {
    selectedUploadFile = file;
    selectedFileName.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
    btnRunUpload.disabled = false;
  }

  btnRunUpload.addEventListener("click", async () => {
    if (!selectedUploadFile) return;

    showProgress("Uploading and analyzing video (audio transcription + slide OCR + semantic linter)...");
    const formData = new FormData();
    formData.append("file", selectedUploadFile);
    formData.append("duration", uploadDuration.value);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      if (!response.ok || result.error) {
        throw new Error(result.error || "Analysis failed");
      }

      if (result.temp_media_path) {
        videoPlayer.src = `/media/video?path=${encodeURIComponent(result.temp_media_path)}`;
      }
      currentVideoTitle.textContent = `${result.video} (first ${result.duration}s)`;
      renderViolations(result.violations || []);
    } catch (err) {
      alert(`Error during analysis: ${err.message}`);
    } finally {
      hideProgress();
    }
  });

  // -------------------------------------------------------------
  // 4. URL Analysis
  // -------------------------------------------------------------
  btnRunUrl.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) {
      alert("Please enter a valid video URL.");
      return;
    }

    showProgress("Downloading target video clip with yt-dlp...");
    try {
      const response = await fetch("/api/analyze-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url,
          duration: parseFloat(urlDuration.value),
        }),
      });

      const result = await response.json();
      if (!response.ok || result.error) {
        throw new Error(result.error || "Analysis failed");
      }

      if (result.temp_media_path) {
        videoPlayer.src = `/media/video?path=${encodeURIComponent(result.temp_media_path)}`;
      }
      currentVideoTitle.textContent = `Online: ${result.video} (first ${result.duration}s)`;
      renderViolations(result.violations || []);
    } catch (err) {
      alert(`Error analyzing URL: ${err.message}`);
    } finally {
      hideProgress();
    }
  });

  // -------------------------------------------------------------
  // 5. Render Violations & Custom Timeline
  // -------------------------------------------------------------
  function renderViolations(violations) {
    currentViolations = violations;
    violationCountBadge.textContent = `${violations.length} Potential`;

    if (violations.length === 0) {
      violationsList.innerHTML = `
        <div class="empty-state">
          <p class="empty-title">No Redundancy Violations Found</p>
          <p class="empty-subtitle">Spoken speech and on-screen slide text maintain distinct channels without redundant overlap in this segment.</p>
        </div>`;
      renderTimelineMarkers();
      return;
    }

    violationsList.innerHTML = "";
    violations.forEach((v, index) => {
      const card = document.createElement("div");
      card.className = "violation-card";
      card.id = `card-${index}`;
      card.setAttribute("data-start", v.start_time);
      card.setAttribute("data-end", v.end_time);

      const startTimeStr = formatTime(v.start_time);
      const endTimeStr = formatTime(v.end_time);
      const scorePct = (v.score * 100).toFixed(1);

      card.innerHTML = `
        <div class="violation-card-top">
          <span class="time-badge">${startTimeStr} - ${endTimeStr}</span>
          <span class="score-badge">Cosine Sim: ${v.score.toFixed(3)} (${scorePct}%)</span>
        </div>
        <div class="violation-label">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
          Potential Redundancy
        </div>
        <div class="violation-grid">
          <div>
            <p class="violation-column-title">Spoken Narration</p>
            <p class="violation-text">${escapeHtml(v.spoken_text || "(Silence)")}</p>
          </div>
          <div>
            <p class="violation-column-title">On-Screen Text</p>
            <p class="violation-text">${escapeHtml(v.onscreen_text || "(No Slide Text)")}</p>
          </div>
        </div>
      `;

      // Click to seek video!
      card.addEventListener("click", () => {
        seekVideo(v.start_time);
      });

      violationsList.appendChild(card);
    });

    renderTimelineMarkers();
  }

  function seekVideo(seconds) {
    videoPlayer.currentTime = seconds;
    videoPlayer.play().catch(() => {});
  }

  function renderTimelineMarkers() {
    timelineTrack.innerHTML = "";
    const duration = videoPlayer.duration || (currentViolations.length > 0 ? currentViolations[currentViolations.length - 1].end_time + 10 : 60);

    currentViolations.forEach((v) => {
      const marker = document.createElement("div");
      marker.className = "timeline-marker";
      const left = (v.start_time / duration) * 100;
      const width = Math.max(((v.end_time - v.start_time) / duration) * 100, 1.2);
      marker.style.left = `${Math.min(left, 98)}%`;
      marker.style.width = `${width}%`;
      marker.title = `Potential Redundancy: ${formatTime(v.start_time)} - ${formatTime(v.end_time)}`;

      marker.addEventListener("click", (e) => {
        e.stopPropagation();
        seekVideo(v.start_time);
      });

      timelineTrack.appendChild(marker);
    });
  }

  // Click on timeline track background to seek
  timelineTrackWrapper.addEventListener("click", (e) => {
    const rect = timelineTrackWrapper.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    const duration = videoPlayer.duration || 60;
    seekVideo(ratio * duration);
  });

  // -------------------------------------------------------------
  // 6. Video Event Listeners (Playback Synchronization)
  // -------------------------------------------------------------
  videoPlayer.addEventListener("loadedmetadata", () => {
    timelineTotalTime.textContent = formatTime(videoPlayer.duration || 0);
    renderTimelineMarkers();
  });

  videoPlayer.addEventListener("timeupdate", () => {
    const currentTime = videoPlayer.currentTime;
    const duration = videoPlayer.duration || 1;

    timelineCurrentTime.textContent = formatTime(currentTime);

    // Update playhead
    const pct = Math.min(100, Math.max(0, (currentTime / duration) * 100));
    timelinePlayhead.style.left = `${pct}%`;

    // Highlight current active card
    highlightActiveCard(currentTime);
  });

  function highlightActiveCard(time) {
    const cards = document.querySelectorAll(".violation-card");
    cards.forEach(card => {
      const start = parseFloat(card.getAttribute("data-start"));
      const end = parseFloat(card.getAttribute("data-end"));
      if (time >= start && time <= end) {
        if (!card.classList.contains("active-playback")) {
          card.classList.add("active-playback");
          card.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      } else {
        card.classList.remove("active-playback");
      }
    });
  }

  // -------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------
  function showProgress(message) {
    progressStatusText.textContent = message;
    progressContainer.classList.remove("hidden");
  }

  function hideProgress() {
    progressContainer.classList.add("hidden");
  }

  function formatTime(sec) {
    const totalSeconds = Math.max(0, Math.floor(sec));
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // Initial Load
  fetchSamples();
});
