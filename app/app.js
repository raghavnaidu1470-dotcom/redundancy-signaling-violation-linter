/**
 * Cognitive Signal Lab — Multi-Modal Attention & Redundancy Linter
 * Frontend Controller with Oscilloscope Background, Waveform Synthesizer & Scrubbing Playhead
 */

document.addEventListener("DOMContentLoaded", () => {
  // -------------------------------------------------------------
  // DOM References
  // -------------------------------------------------------------
  const videoPlayer = document.getElementById("video-player");
  const currentVideoTitle = document.getElementById("current-video-title");
  const violationsList = document.getElementById("violations-list");
  const violationCountBadge = document.getElementById("violation-count-badge");

  // Dual-Track Timeline
  const audioWaveformCanvas = document.getElementById("audio-waveform-canvas");
  const timelineTrackWrapper = document.getElementById("timeline-track-wrapper");
  const timelineTrack = document.getElementById("timeline-track");
  const timelinePlayhead = document.getElementById("timeline-playhead");
  const laserTag = document.getElementById("laser-tag");
  const timelineCurrentTime = document.getElementById("timeline-current-time");
  const timelineTotalTime = document.getElementById("timeline-total-time");

  // Progress Radar
  const progressContainer = document.getElementById("progress-container");
  const progressStatusText = document.getElementById("progress-status-text");

  // Console Tabs
  const consoleTabs = document.querySelectorAll(".console-tab");
  const tabPanels = document.querySelectorAll(".tab-panel");

  // Input Panel 1: Benchmark Samples
  const sampleSelect = document.getElementById("sample-select");
  const btnLoadSample = document.getElementById("btn-load-sample");

  // Input Panel 2: Dropzone
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const btnBrowse = document.getElementById("btn-browse");
  const selectedFileName = document.getElementById("selected-file-name");
  const uploadDuration = document.getElementById("upload-duration");
  const btnRunUpload = document.getElementById("btn-run-upload");

  // Input Panel 3: URL Analyzer
  const urlInput = document.getElementById("url-input");
  const urlDuration = document.getElementById("url-duration");
  const btnRunUrl = document.getElementById("btn-run-url");

  // App State
  let currentViolations = [];
  let selectedUploadFile = null;
  let isScrubbing = false;

  // -------------------------------------------------------------
  // 1. Ambient Background Oscilloscope Animation (Canvas)
  // -------------------------------------------------------------
  initAmbientOscilloscope();

  function initAmbientOscilloscope() {
    const bgCanvas = document.getElementById("bg-canvas");
    if (!bgCanvas) return;

    const ctx = bgCanvas.getContext("2d");
    let width, height;
    let animFrameId;
    let phase = 0;

    // Check reduced motion preference
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Sparse Particle / Neuron Network Nodes
    const particleCount = 28;
    const particles = [];

    function resizeCanvas() {
      width = bgCanvas.width = window.innerWidth;
      height = bgCanvas.height = window.innerHeight;

      if (particles.length === 0) {
        for (let i = 0; i < particleCount; i++) {
          particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            radius: Math.random() * 2 + 1,
            pulseOffset: Math.random() * Math.PI * 2,
            isViolating: Math.random() > 0.7,
          });
        }
      }
    }

    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    function render(timestamp) {
      if (prefersReducedMotion) return;

      ctx.clearRect(0, 0, width, height);
      phase += 0.012;

      // 1. Draw drifting dual-waveform (Audio amplitude + Cognitive signal)
      drawDualWaveform(ctx, width, height, phase);

      // 2. Draw sparse particle neural network
      drawNeuralNodes(ctx, width, height, phase, particles);

      animFrameId = requestAnimationFrame(render);
    }

    if (!prefersReducedMotion) {
      animFrameId = requestAnimationFrame(render);
    }

    // Pause animation when tab is not visible to save GPU cycles
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        cancelAnimationFrame(animFrameId);
      } else if (!prefersReducedMotion) {
        animFrameId = requestAnimationFrame(render);
      }
    });
  }

  function drawDualWaveform(ctx, width, height, phase) {
    const centerY1 = height * 0.38;
    const centerY2 = height * 0.68;

    // Channel 1: Auditory Sine Envelope (Electric Cyan)
    ctx.beginPath();
    ctx.strokeStyle = "rgba(0, 229, 255, 0.22)";
    ctx.lineWidth = 1.6;

    for (let x = 0; x < width; x += 3) {
      const freq1 = 0.0035;
      const freq2 = 0.011;
      const y = centerY1 +
        Math.sin(x * freq1 + phase) * 35 +
        Math.sin(x * freq2 - phase * 1.5) * 15 +
        Math.sin(x * 0.0008 + phase * 0.5) * 20;

      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Channel 2: Cognitive Attention Flow (Vivid Magenta / Violet)
    ctx.beginPath();
    ctx.strokeStyle = "rgba(255, 45, 149, 0.18)";
    ctx.lineWidth = 1.4;

    for (let x = 0; x < width; x += 3) {
      const freq1 = 0.0042;
      const freq2 = 0.008;
      const y = centerY2 +
        Math.cos(x * freq1 - phase * 0.8) * 30 +
        Math.sin(x * freq2 + phase * 1.2) * 18 +
        Math.cos(x * 0.0012 + phase) * 15;

      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  function drawNeuralNodes(ctx, width, height, phase, particles) {
    // Update and draw particles
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      const pulse = Math.sin(phase * 2 + p.pulseOffset) * 0.5 + 0.5;
      const color = p.isViolating
        ? `rgba(255, 45, 149, ${0.15 + pulse * 0.35})`
        : `rgba(0, 229, 255, ${0.15 + pulse * 0.35})`;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius * (1 + pulse * 0.3), 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      // Draw faint connections to near neighbors
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 130) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(0, 229, 255, ${(1 - dist / 130) * 0.08})`;
          ctx.lineWidth = 0.8;
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.stroke();
        }
      }
    }
  }

  // -------------------------------------------------------------
  // 2. Track 1: Audio Waveform Canvas Generator
  // -------------------------------------------------------------
  function renderAudioWaveform() {
    if (!audioWaveformCanvas) return;

    const ctx = audioWaveformCanvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = audioWaveformCanvas.getBoundingClientRect();

    audioWaveformCanvas.width = rect.width * dpr;
    audioWaveformCanvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    ctx.clearRect(0, 0, width, height);

    const barWidth = 3;
    const barGap = 2;
    const totalBars = Math.floor(width / (barWidth + barGap));
    const duration = videoPlayer.duration || 60;

    // Draw baseline audio activity bars
    for (let i = 0; i < totalBars; i++) {
      const x = i * (barWidth + barGap);
      const timeAtBar = (i / totalBars) * duration;

      // Check if this time slot intersects any flagged redundancy or signaling moment
      let isHot = false;
      for (const v of currentViolations) {
        if (timeAtBar >= v.start_time && timeAtBar <= v.end_time) {
          isHot = true;
          break;
        }
      }

      // Procedural amplitude with variation
      const pseudoNoise = (Math.sin(i * 0.37) * 0.5 + 0.5) * (Math.cos(i * 0.12) * 0.5 + 0.5);
      let barHeight = Math.max(4, pseudoNoise * (height * 0.75));

      if (isHot) {
        barHeight = Math.min(height - 4, barHeight * 1.5 + 8);
        ctx.fillStyle = "rgba(0, 229, 255, 0.85)";
        ctx.shadowColor = "#00e5ff";
        ctx.shadowBlur = 4;
      } else {
        ctx.fillStyle = "rgba(0, 229, 255, 0.28)";
        ctx.shadowBlur = 0;
      }

      const y = (height - barHeight) / 2;
      ctx.fillRect(x, y, barWidth, barHeight);
    }
    ctx.shadowBlur = 0;
  }

  // -------------------------------------------------------------
  // 3. Tab Switching
  // -------------------------------------------------------------
  consoleTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      consoleTabs.forEach(t => t.classList.remove("active"));
      tabPanels.forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetPanelId = tab.getAttribute("data-tab");
      const targetPanel = document.getElementById(targetPanelId);
      if (targetPanel) {
        targetPanel.classList.add("active");
      }
    });
  });

  // -------------------------------------------------------------
  // 4. Load Pre-indexed Samples
  // -------------------------------------------------------------
  async function fetchSamples() {
    try {
      const response = await fetch("/api/samples");
      if (!response.ok) throw new Error("Failed to load benchmark corpus");
      const data = await response.json();

      sampleSelect.innerHTML = "";
      if (!data.samples || data.samples.length === 0) {
        sampleSelect.innerHTML = '<option value="" disabled>No benchmark samples found</option>';
        return;
      }

      data.samples.forEach(sample => {
        const option = document.createElement("option");
        option.value = sample.stem;
        option.textContent = `${sample.title} (${sample.violations_count} flags)`;
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
    showProgress("MOUNTING BENCHMARK SIGNAL TELEMETRY...");

    try {
      const response = await fetch(`/api/results?video=${encodeURIComponent(stem)}`);
      if (!response.ok) throw new Error("Failed to load results for sample");
      const result = await response.json();

      // Set video source
      videoPlayer.src = `/media/video?stem=${encodeURIComponent(stem)}`;
      currentVideoTitle.textContent = stem;

      renderViolations(result.violations || []);
    } catch (err) {
      alert(`Could not load benchmark sample: ${err.message}`);
    } finally {
      hideProgress();
    }
  }

  btnLoadSample.addEventListener("click", () => {
    const stem = sampleSelect.value;
    loadSample(stem);
  });

  // -------------------------------------------------------------
  // 5. Dropzone & File Upload
  // -------------------------------------------------------------
  btnBrowse.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropzone.addEventListener("click", () => fileInput.click());

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
    selectedFileName.textContent = `MOUNTED: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
    btnRunUpload.disabled = false;
  }

  btnRunUpload.addEventListener("click", async () => {
    if (!selectedUploadFile) return;

    showProgress("PERFORMING MULTI-CHANNEL COGNITIVE SCAN (ASR + OCR + LINTER)...");
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
      currentVideoTitle.textContent = `${result.video} [SCAN: ${result.duration}s]`;
      renderViolations(result.violations || []);
    } catch (err) {
      alert(`Error during cognitive scan: ${err.message}`);
    } finally {
      hideProgress();
    }
  });

  // -------------------------------------------------------------
  // 6. URL Analysis (YouTube / Web Streams)
  // -------------------------------------------------------------
  btnRunUrl.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) {
      alert("Please enter a valid lecture video URL.");
      return;
    }

    showProgress("ACQUIRING REMOTE STREAM VIA YT-DLP PIPELINE...");
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
      currentVideoTitle.textContent = `STREAM: ${result.video} [SCAN: ${result.duration}s]`;
      renderViolations(result.violations || []);
    } catch (err) {
      alert(`Error analyzing URL: ${err.message}`);
    } finally {
      hideProgress();
    }
  });

  // -------------------------------------------------------------
  // 7. Render Violations & Dual-Track Timeline
  // -------------------------------------------------------------
  function renderViolations(violations) {
    currentViolations = violations;
    violationCountBadge.textContent = `${violations.length} FLAGS`;

    if (violations.length === 0) {
      violationsList.innerHTML = `
        <div class="standby-screen">
          <div class="standby-radar">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </div>
          <p class="standby-title">NO ATTENTION CONFLICTS DETECTED</p>
          <p class="standby-desc">Spoken speech and visual elements maintain separate, harmonious channels without redundant cognitive overload.</p>
        </div>`;
      renderTimelineMarkers();
      renderAudioWaveform();
      return;
    }

    violationsList.innerHTML = "";
    violations.forEach((v, index) => {
      const card = document.createElement("div");
      const isSignaling = v.violation_type === "unsignaled_thematic_shift" || v.type === "signaling";
      
      card.className = `violation-card ${isSignaling ? "type-signaling-card" : ""}`;
      card.id = `card-${index}`;
      card.setAttribute("data-start", v.start_time);
      card.setAttribute("data-end", v.end_time);

      const startTimeStr = formatTime(v.start_time);
      const endTimeStr = formatTime(v.end_time);

      const scoreValue = v.score !== undefined ? v.score : (v.shift_score !== undefined ? v.shift_score : 0.25);
      const scorePct = Math.min(100, Math.max(0, (scoreValue * 100))).toFixed(1);

      const titleLabel = isSignaling ? "Signaling Shift" : "Redundancy Violation";
      const iconSvg = isSignaling
        ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>`
        : `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;

      const durationSec = Math.max(0.5, (v.end_time - v.start_time)).toFixed(1);

      card.innerHTML = `
        <div class="violation-card-top">
          <span class="time-badge" title="Timestamp: ${startTimeStr} to ${endTimeStr} (${durationSec}s)">
            <svg class="time-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            <span class="time-range-text">${startTimeStr} <span class="time-arrow">➔</span> ${endTimeStr}</span>
            <span class="time-dur-tag">${durationSec}s</span>
          </span>
          <div class="score-badge-wrap">
            <div class="score-bar-bg" title="Cosine Similarity: ${scorePct}%">
              <div class="score-bar-fill" style="width: ${scorePct}%;"></div>
            </div>
            <span class="score-badge">${scorePct}%</span>
          </div>
        </div>
        <div class="violation-label ${isSignaling ? "label-signaling" : ""}">
          ${iconSvg}
          ${titleLabel}
        </div>
        <div class="violation-grid">
          <div class="column-audio">
            <p class="violation-column-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path></svg>
              Spoken Narration
            </p>
            <div class="violation-text">${formatSpokenText(v.spoken_text)}</div>
          </div>
          <div class="column-slide">
            <p class="violation-column-title">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
              On-Screen Slide / Chalkboard
            </p>
            <div class="violation-text">${formatSlideText(v.onscreen_text || v.static_onscreen_text)}</div>
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
    renderAudioWaveform();
  }

  function seekVideo(seconds) {
    if (isNaN(seconds)) return;
    videoPlayer.currentTime = seconds;
    videoPlayer.play().catch(() => {});
  }

  // -------------------------------------------------------------
  // 8. Track 2: Violation Markers Rendering
  // -------------------------------------------------------------
  function renderTimelineMarkers() {
    timelineTrack.innerHTML = "";
    const duration = videoPlayer.duration || (currentViolations.length > 0 ? currentViolations[currentViolations.length - 1].end_time + 10 : 60);

    currentViolations.forEach((v) => {
      const marker = document.createElement("div");
      const isSignaling = v.violation_type === "unsignaled_thematic_shift" || v.type === "signaling";
      marker.className = `timeline-marker ${isSignaling ? "type-signaling" : "type-redundancy"}`;

      const left = (v.start_time / duration) * 100;
      const width = Math.max(((v.end_time - v.start_time) / duration) * 100, 1.4);

      marker.style.left = `${Math.min(left, 98.6)}%`;
      marker.style.width = `${width}%`;
      marker.title = `${isSignaling ? "Signaling Shift" : "Redundancy"}: ${formatTime(v.start_time)} - ${formatTime(v.end_time)}`;

      marker.addEventListener("click", (e) => {
        e.stopPropagation();
        seekVideo(v.start_time);
      });

      timelineTrack.appendChild(marker);
    });
  }

  // -------------------------------------------------------------
  // 9. Timeline Scrubbing & Interactive Seek
  // -------------------------------------------------------------
  function scrubToEvent(e) {
    const rect = timelineTrackWrapper.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    const duration = videoPlayer.duration || 60;
    const targetTime = ratio * duration;

    // Move laser playhead immediately
    timelinePlayhead.style.left = `${ratio * 100}%`;
    laserTag.textContent = formatTime(targetTime);
    timelineCurrentTime.textContent = formatTime(targetTime);

    seekVideo(targetTime);
  }

  timelineTrackWrapper.addEventListener("mousedown", (e) => {
    isScrubbing = true;
    scrubToEvent(e);
  });

  window.addEventListener("mousemove", (e) => {
    if (isScrubbing) {
      scrubToEvent(e);
    }
  });

  window.addEventListener("mouseup", () => {
    isScrubbing = false;
  });

  // Touch Support for Timeline Scrubbing
  timelineTrackWrapper.addEventListener("touchstart", (e) => {
    isScrubbing = true;
    if (e.touches.length > 0) scrubToEvent(e.touches[0]);
  }, { passive: true });

  window.addEventListener("touchmove", (e) => {
    if (isScrubbing && e.touches.length > 0) {
      scrubToEvent(e.touches[0]);
    }
  }, { passive: true });

  window.addEventListener("touchend", () => {
    isScrubbing = false;
  });

  // -------------------------------------------------------------
  // 10. Playback Synchronization Listeners
  // -------------------------------------------------------------
  videoPlayer.addEventListener("loadedmetadata", () => {
    timelineTotalTime.textContent = formatTime(videoPlayer.duration || 0);
    renderTimelineMarkers();
    renderAudioWaveform();
  });

  videoPlayer.addEventListener("timeupdate", () => {
    if (isScrubbing) return; // Don't fight manual drag

    const currentTime = videoPlayer.currentTime;
    const duration = videoPlayer.duration || 1;

    timelineCurrentTime.textContent = formatTime(currentTime);

    // Update playhead & laser tag
    const pct = Math.min(100, Math.max(0, (currentTime / duration) * 100));
    timelinePlayhead.style.left = `${pct}%`;
    laserTag.textContent = formatTime(currentTime);

    // Highlight current active anomaly card
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

  // Window resize handler for waveform canvas
  window.addEventListener("resize", () => {
    renderAudioWaveform();
  });

  // -------------------------------------------------------------
  // 11. Helpers
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

  function formatSlideText(text) {
    if (!text || !text.trim()) {
      return '<span class="slide-empty-note">[Visual Demonstration / Diagram — No Slide Text Displayed]</span>';
    }

    // Clean common OCR noise symbols
    let cleaned = text.replace(/[\~\|\_\\\^\*\<\>\{\}\[\]\=\+\#\$\%\@]+/g, " ");
    const rawLines = cleaned.split("\n").map(l => l.trim()).filter(l => l.length > 0);

    if (rawLines.length === 0) {
      return '<span class="slide-empty-note">[Visual Demonstration / Diagram — No Slide Text Displayed]</span>';
    }

    const cleanLines = [];
    for (const line of rawLines) {
      const tokens = line.split(/\s+/).filter(tok => {
        const cleanTok = tok.replace(/[^a-zA-Z0-9]/g, "");
        if (cleanTok.length === 1 && !['a', 'i', 'A', 'I'].includes(cleanTok) && !/[0-9]/.test(cleanTok)) {
          return false;
        }
        return cleanTok.length > 0;
      });
      if (tokens.length > 0) {
        cleanLines.push(tokens.join(" "));
      }
    }

    if (cleanLines.length === 0) {
      return '<span class="slide-empty-note">[Handwritten Blackboard — Low Optical Contrast]</span>';
    }

    // Check if tokens are meaningful words
    const allWords = cleanLines.join(" ").split(/\s+/).filter(w => w.length >= 2 && /[a-zA-Z]/.test(w));
    if (allWords.length < 2) {
      return `<div class="slide-low-conf"><span class="slide-empty-note">[Blackboard Handwriting Fragment]</span><span class="slide-text-preview">${escapeHtml(cleanLines.join(" "))}</span></div>`;
    }

    return cleanLines.map(line => `
      <div class="slide-line">
        <span class="slide-bullet">›</span>
        <span class="slide-line-content">${escapeHtml(line)}</span>
      </div>
    `).join("");
  }

  function formatSpokenText(text) {
    if (!text || !text.trim()) {
      return '<span class="slide-empty-note">(Silence)</span>';
    }
    return `<span class="audio-quote">"${escapeHtml(text.trim())}"</span>`;
  }

  // Initial load
  fetchSamples();
});
