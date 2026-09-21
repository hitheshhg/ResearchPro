/**
 * ESP32 Acoustic DoA TinyML Dashboard Application
 * Real-time room simulation, DSP cross-correlation, int8 TFLite inference,
 * dual oscilloscope visualization, and hardware profiler.
 */

document.addEventListener("DOMContentLoaded", () => {
  // ============================================================================
  // 1. STATE & CONSTANTS
  // ============================================================================
  const SPEED_OF_SOUND = 343.0; // m/s
  const MIC_BASELINE = 0.10;   // 10 cm
  const FS = 16000;            // 16 kHz
  const ROOM_W_M = 5.0;
  const ROOM_H_M = 5.0;

  let state = {
    angleDeg: 0,
    distanceM: 1.50,
    signalType: "snap",
    snrDb: 25,
    rt60S: 0.20,
    audioEnabled: true,
    isStreaming: false,
    streamTimer: null,
    isDragging: false,
    wavefrontRadius: 0,
    wavefrontActive: false,
  };

  // Audio Context for stereo synthesis
  let audioCtx = null;

  // DOM Elements
  const canvasRoom = document.getElementById("canvas-room");
  const ctxRoom = canvasRoom.getContext("2d");
  const canvasOsc = document.getElementById("canvas-oscilloscope");
  const ctxOsc = canvasOsc.getContext("2d");
  const canvasNcc = document.getElementById("canvas-ncc");
  const ctxNcc = canvasNcc.getContext("2d");

  // Readouts & Controls
  const sliderAngle = document.getElementById("slider-angle");
  const sliderDistance = document.getElementById("slider-distance");
  const sliderSnr = document.getElementById("slider-snr");
  const sliderRt60 = document.getElementById("slider-rt60");
  const selectTransient = document.getElementById("select-transient");
  const chkAudio = document.getElementById("chk-audio");

  const valAngle = document.getElementById("val-angle");
  const valDist = document.getElementById("val-dist");
  const valSnr = document.getElementById("val-snr");
  const valRt60 = document.getElementById("val-rt60");

  const lblReadoutAngle = document.getElementById("lbl-readout-angle");
  const lblReadoutDist = document.getElementById("lbl-readout-dist");
  const lblReadoutTdoa = document.getElementById("lbl-readout-tdoa");

  const btnFirePulse = document.getElementById("btn-fire-pulse");
  const btnAutoStream = document.getElementById("btn-auto-stream");
  const btnRunBenchmark = document.getElementById("btn-run-benchmark");
  const btnReRunDsp = document.getElementById("btn-re-run-dsp");

  // Inference DOM Elements
  const predictedSectorText = document.getElementById("predicted-sector-text");
  const predictedConfidenceText = document.getElementById("predicted-confidence-text");
  const predictedLagText = document.getElementById("predicted-lag-text");
  const compassNeedle = document.getElementById("compass-needle");
  const probLeftText = document.getElementById("prob-left-text");
  const probCenterText = document.getElementById("prob-center-text");
  const probRightText = document.getElementById("prob-right-text");
  const probBarLeft = document.getElementById("prob-bar-left");
  const probBarCenter = document.getElementById("prob-bar-center");
  const probBarRight = document.getElementById("prob-bar-right");

  const valPeakLag = document.getElementById("val-peak-lag");
  const valPeakNcc = document.getElementById("val-peak-ncc");

  // Terminal
  const terminalBody = document.getElementById("terminal-body");

  // Modal
  const lightboxModal = document.getElementById("lightbox-modal");
  const modalImg = document.getElementById("modal-img");
  const modalTitle = document.getElementById("modal-title");
  const modalCloseBtn = document.getElementById("modal-close-btn");

  // ============================================================================
  // 2. ROOM ACOUSTIC MAPPING & COORDINATE SYSTEMS
  // ============================================================================
  // Center of room in meters is (2.5, 2.5). In Canvas coordinates:
  function getRoomPixelCoords(meterX, meterY) {
    const scale = canvasRoom.width / ROOM_W_M;
    return {
      x: meterX * scale,
      y: canvasRoom.height - (meterY * scale) // Flip Y so +Y is up (broadside)
    };
  }

  function getMeterCoordsFromPixel(pixelX, pixelY) {
    const scale = canvasRoom.width / ROOM_W_M;
    return {
      x: pixelX / scale,
      y: (canvasRoom.height - pixelY) / scale
    };
  }

  // Mic array center is at (2.5m, 1.8m) to leave room for sound sources above (+Y)
  const MIC_ARRAY_CENTER = { x: 2.5, y: 1.6 };

  function updateSourceFromAngleAndDistance() {
    const rad = (state.angleDeg * Math.PI) / 180.0;
    // Angle theta from +Y broadside:
    // Left (theta < 0) -> -X, Right (theta > 0) -> +X
    const srcX = MIC_ARRAY_CENTER.x + state.distanceM * Math.sin(rad);
    const srcY = MIC_ARRAY_CENTER.y + state.distanceM * Math.cos(rad);
    state.sourceMeterPos = { x: srcX, y: srcY };
  }

  function updateAngleAndDistance(srcX, srcY) {
    const dx = srcX - MIC_ARRAY_CENTER.x;
    const dy = srcY - MIC_ARRAY_CENTER.y;
    let dist = Math.sqrt(dx * dx + dy * dy);
    dist = Math.max(0.4, Math.min(3.0, dist));
    
    // Angle in degrees from +Y
    let angle = (Math.atan2(dx, dy) * 180.0) / Math.PI;
    angle = Math.max(-90, Math.min(90, angle));

    state.angleDeg = Math.round(angle);
    state.distanceM = parseFloat(dist.toFixed(2));
    updateSourceFromAngleAndDistance();

    // Update UI controls
    sliderAngle.value = state.angleDeg;
    sliderDistance.value = state.distanceM;
    valAngle.textContent = `${state.angleDeg}°`;
    valDist.textContent = `${state.distanceM.toFixed(2)} m`;
    lblReadoutAngle.textContent = `${state.angleDeg}°`;
    lblReadoutDist.textContent = `${state.distanceM.toFixed(2)} m`;

    const delta_t = (MIC_BASELINE * Math.sin((state.angleDeg * Math.PI) / 180.0)) / SPEED_OF_SOUND;
    lblReadoutTdoa.textContent = `${(delta_t * 1e6).toFixed(1)} μs`;

    // Highlight matching preset button
    document.querySelectorAll(".preset-btn").forEach(btn => btn.classList.remove("active"));
    if (state.angleDeg === -45) document.getElementById("btn-preset-left").classList.add("active");
    else if (state.angleDeg === 0) document.getElementById("btn-preset-center").classList.add("active");
    else if (state.angleDeg === 45) document.getElementById("btn-preset-right").classList.add("active");
  }

  // ============================================================================
  // 3. CANVAS DRAWING ROUTINES
  // ============================================================================
  function drawRoom() {
    const w = canvasRoom.width;
    const h = canvasRoom.height;
    ctxRoom.clearRect(0, 0, w, h);

    // Background Room Grid
    ctxRoom.strokeStyle = "rgba(51, 65, 85, 0.25)";
    ctxRoom.lineWidth = 1;
    const gridSize = w / 10;
    for (let x = 0; x <= w; x += gridSize) {
      ctxRoom.beginPath();
      ctxRoom.moveTo(x, 0);
      ctxRoom.lineTo(x, h);
      ctxRoom.stroke();
    }
    for (let y = 0; y <= h; y += gridSize) {
      ctxRoom.beginPath();
      ctxRoom.moveTo(0, y);
      ctxRoom.lineTo(w, y);
      ctxRoom.stroke();
    }

    const micCenterPx = getRoomPixelCoords(MIC_ARRAY_CENTER.x, MIC_ARRAY_CENTER.y);

    // Angular Sectors Field (Cones)
    drawAngularSector(micCenterPx, -55, -35, "rgba(239, 68, 68, 0.08)", "rgba(239, 68, 68, 0.3)", "LEFT");
    drawAngularSector(micCenterPx, -10, 10, "rgba(16, 185, 129, 0.08)", "rgba(16, 185, 129, 0.3)", "CENTER");
    drawAngularSector(micCenterPx, 35, 55, "rgba(56, 189, 248, 0.08)", "rgba(56, 189, 248, 0.3)", "RIGHT");

    // Distance Range Arcs (1m, 2m, 3m)
    const scale = w / ROOM_W_M;
    [1.0, 2.0, 3.0].forEach(r => {
      ctxRoom.strokeStyle = "rgba(148, 163, 184, 0.15)";
      ctxRoom.setLineDash([4, 4]);
      ctxRoom.beginPath();
      ctxRoom.arc(micCenterPx.x, micCenterPx.y, r * scale, -Math.PI, 0);
      ctxRoom.stroke();
      ctxRoom.setLineDash([]);
      ctxRoom.fillStyle = "rgba(148, 163, 184, 0.4)";
      ctxRoom.font = "10px JetBrains Mono";
      ctxRoom.fillText(`${r}m`, micCenterPx.x + 8, micCenterPx.y - r * scale + 12);
    });

    // Draw Wavefront Animation from sound source
    const srcPx = getRoomPixelCoords(state.sourceMeterPos.x, state.sourceMeterPos.y);
    if (state.wavefrontActive) {
      for (let ring = 0; ring < 3; ring++) {
        const r = (state.wavefrontRadius + ring * 28) % 240;
        const alpha = Math.max(0, 1.0 - r / 240);
        ctxRoom.strokeStyle = `rgba(0, 229, 255, ${alpha * 0.7})`;
        ctxRoom.lineWidth = 2;
        ctxRoom.beginPath();
        ctxRoom.arc(srcPx.x, srcPx.y, r, 0, Math.PI * 2);
        ctxRoom.stroke();
      }
    }

    // Acoustic Line of Sight Path from Source to Microphone Center
    ctxRoom.strokeStyle = "rgba(0, 229, 255, 0.4)";
    ctxRoom.lineWidth = 1.5;
    ctxRoom.setLineDash([3, 3]);
    ctxRoom.beginPath();
    ctxRoom.moveTo(srcPx.x, srcPx.y);
    ctxRoom.lineTo(micCenterPx.x, micCenterPx.y);
    ctxRoom.stroke();
    ctxRoom.setLineDash([]);

    // Draw Dual MAX9814 Microphone Array
    const micBaselinePx = (MIC_BASELINE / 2.0) * scale;
    const micLeftPx = { x: micCenterPx.x - micBaselinePx, y: micCenterPx.y };
    const micRightPx = { x: micCenterPx.x + micBaselinePx, y: micCenterPx.y };

    // Baseline Mounting Bar
    ctxRoom.strokeStyle = "#475569";
    ctxRoom.lineWidth = 4;
    ctxRoom.beginPath();
    ctxRoom.moveTo(micLeftPx.x - 6, micLeftPx.y);
    ctxRoom.lineTo(micRightPx.x + 6, micRightPx.y);
    ctxRoom.stroke();

    // Mic Left (Cyan)
    drawMicrophoneSensor(micLeftPx.x, micLeftPx.y, "#00E5FF", "Mic L (CH34)");
    // Mic Right (Magenta)
    drawMicrophoneSensor(micRightPx.x, micRightPx.y, "#D946EF", "Mic R (CH35)");

    // Array Center Label
    ctxRoom.fillStyle = "#94A3B8";
    ctxRoom.font = "9px JetBrains Mono";
    ctxRoom.textAlign = "center";
    ctxRoom.fillText("d = 10 cm", micCenterPx.x, micCenterPx.y + 18);

    // Draw Acoustic Source Emitter (Draggable)
    drawSoundSource(srcPx.x, srcPx.y);
  }

  function drawAngularSector(center, degStart, degEnd, fillStyle, strokeStyle, label) {
    const scale = canvasRoom.width / ROOM_W_M;
    const r = 3.2 * scale;
    // Map degrees from +Y to standard canvas angles:
    // angle canvas = -Math.PI / 2 + deg * Math.PI / 180
    const a1 = -Math.PI / 2 + (degStart * Math.PI) / 180.0;
    const a2 = -Math.PI / 2 + (degEnd * Math.PI) / 180.0;

    ctxRoom.fillStyle = fillStyle;
    ctxRoom.strokeStyle = strokeStyle;
    ctxRoom.lineWidth = 1;
    ctxRoom.beginPath();
    ctxRoom.moveTo(center.x, center.y);
    ctxRoom.arc(center.x, center.y, r, a1, a2);
    ctxRoom.closePath();
    ctxRoom.fill();
    ctxRoom.stroke();

    // Label
    const midAngle = (a1 + a2) / 2.0;
    const lblR = r * 0.88;
    const lx = center.x + lblR * Math.cos(midAngle);
    const ly = center.y + lblR * Math.sin(midAngle);
    ctxRoom.fillStyle = strokeStyle;
    ctxRoom.font = "bold 9px JetBrains Mono";
    ctxRoom.textAlign = "center";
    ctxRoom.textBaseline = "middle";
    ctxRoom.fillText(label, lx, ly);
  }

  function drawMicrophoneSensor(x, y, color, label) {
    ctxRoom.fillStyle = color;
    ctxRoom.beginPath();
    ctxRoom.arc(x, y, 6, 0, Math.PI * 2);
    ctxRoom.fill();
    ctxRoom.strokeStyle = "#FFFFFF";
    ctxRoom.lineWidth = 1.5;
    ctxRoom.stroke();

    ctxRoom.fillStyle = color;
    ctxRoom.font = "9px Outfit";
    ctxRoom.textAlign = "center";
    ctxRoom.fillText(label, x, y + 14);
  }

  function drawSoundSource(x, y) {
    // Pulse glow
    ctxRoom.fillStyle = "rgba(0, 229, 255, 0.2)";
    ctxRoom.beginPath();
    ctxRoom.arc(x, y, 16, 0, Math.PI * 2);
    ctxRoom.fill();

    // Outer ring
    ctxRoom.strokeStyle = "#00E5FF";
    ctxRoom.lineWidth = 2;
    ctxRoom.beginPath();
    ctxRoom.arc(x, y, 10, 0, Math.PI * 2);
    ctxRoom.stroke();

    // Center Core
    ctxRoom.fillStyle = "#FFFFFF";
    ctxRoom.beginPath();
    ctxRoom.arc(x, y, 5, 0, Math.PI * 2);
    ctxRoom.fill();

    // Label
    ctxRoom.fillStyle = "#F1F5F9";
    ctxRoom.font = "bold 10px Outfit";
    ctxRoom.textAlign = "center";
    ctxRoom.fillText("SOURCE", x, y - 14);
  }

  // ============================================================================
  // 4. OSCILLOSCOPE & NCC VISUALIZATIONS
  // ============================================================================
  function drawOscilloscope(leftWaveform, rightWaveform) {
    const w = canvasOsc.width;
    const h = canvasOsc.height;
    ctxOsc.clearRect(0, 0, w, h);

    // Draw Grid
    ctxOsc.strokeStyle = "rgba(51, 65, 85, 0.3)";
    ctxOsc.lineWidth = 1;
    for (let x = 0; x <= w; x += 40) {
      ctxOsc.beginPath();
      ctxOsc.moveTo(x, 0);
      ctxOsc.lineTo(x, h);
      ctxOsc.stroke();
    }
    for (let y = 0; y <= h; y += 32) {
      ctxOsc.beginPath();
      ctxOsc.moveTo(0, y);
      ctxOsc.lineTo(w, y);
      ctxOsc.stroke();
    }

    // DC Bias Baseline (y ~ 1550 in 12-bit ADC -> around h/2)
    const midY = h / 2;
    ctxOsc.strokeStyle = "rgba(148, 163, 184, 0.25)";
    ctxOsc.setLineDash([2, 4]);
    ctxOsc.beginPath();
    ctxOsc.moveTo(0, midY);
    ctxOsc.lineTo(w, midY);
    ctxOsc.stroke();
    ctxOsc.setLineDash([]);

    if (!leftWaveform || !rightWaveform) return;

    // Draw Mic Left (Cyan)
    drawWaveformChannel(leftWaveform, "#00E5FF", midY, 1.8);
    // Draw Mic Right (Magenta)
    drawWaveformChannel(rightWaveform, "#D946EF", midY, 1.8);
  }

  function drawWaveformChannel(data, color, midY, scaleY) {
    const n = data.length;
    const stepX = canvasOsc.width / (n - 1);
    const mean = 1550.0;

    ctxOsc.strokeStyle = color;
    ctxOsc.lineWidth = 1.6;
    ctxOsc.beginPath();

    for (let i = 0; i < n; i++) {
      const val = data[i] - mean;
      // Invert Y for canvas
      const py = midY - (val * (canvasOsc.height / 3500.0) * scaleY);
      const px = i * stepX;
      if (i === 0) ctxOsc.moveTo(px, py);
      else ctxOsc.lineTo(px, py);
    }
    ctxOsc.stroke();
  }

  function drawNccSpectrum(lags, features, peakLag) {
    const w = canvasNcc.width;
    const h = canvasNcc.height;
    ctxNcc.clearRect(0, 0, w, h);

    // Background Grid
    ctxNcc.strokeStyle = "rgba(51, 65, 85, 0.3)";
    ctxNcc.lineWidth = 1;
    const midY = h / 2; // NCC = 0 line

    ctxNcc.beginPath();
    ctxNcc.moveTo(0, midY);
    ctxNcc.lineTo(w, midY);
    ctxNcc.stroke();

    if (!features || features.length === 0) return;

    const barWidth = (w / features.length) * 0.7;
    const stepX = w / features.length;

    // Draw bars
    for (let i = 0; i < features.length; i++) {
      const lag = lags[i];
      const val = features[i]; // in range [-1.0, 1.0]
      const px = i * stepX + stepX / 2;
      const barH = val * (h / 2.3);
      const py = midY - barH;

      const isPeak = (lag === peakLag);

      if (isPeak) {
        ctxNcc.fillStyle = "#00E5FF";
        ctxNcc.shadowColor = "rgba(0, 229, 255, 0.6)";
        ctxNcc.shadowBlur = 10;
      } else {
        ctxNcc.fillStyle = val >= 0 ? "rgba(59, 130, 246, 0.75)" : "rgba(239, 68, 68, 0.5)";
        ctxNcc.shadowBlur = 0;
      }

      ctxNcc.fillRect(px - barWidth / 2, Math.min(midY, py), barWidth, Math.abs(barH));
      ctxNcc.shadowBlur = 0;

      // Draw lag labels for -15, -10, -5, 0, +5, +10, +15
      if (lag % 5 === 0) {
        ctxNcc.fillStyle = isPeak ? "#00E5FF" : "#64748B";
        ctxNcc.font = isPeak ? "bold 9px JetBrains Mono" : "8px JetBrains Mono";
        ctxNcc.textAlign = "center";
        ctxNcc.fillText(`${lag > 0 ? '+' : ''}${lag}`, px, h - 4);
      }
    }

    // Callout on peak lag
    const peakIdx = lags.indexOf(peakLag);
    if (peakIdx >= 0) {
      const px = peakIdx * stepX + stepX / 2;
      const val = features[peakIdx];
      const py = midY - val * (h / 2.3);

      ctxNcc.fillStyle = "#FFFFFF";
      ctxNcc.font = "bold 10px JetBrains Mono";
      ctxNcc.textAlign = "center";
      ctxNcc.fillText(`τ=${peakLag} (${val.toFixed(2)})`, px, py > midY ? py + 14 : py - 6);
    }
  }

  // ============================================================================
  // 5. STEREO WEB AUDIO SYNTHESIZER
  // ============================================================================
  function playStereoTransient(angleDeg, sigType) {
    if (!state.audioEnabled) return;
    try {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === "suspended") {
        audioCtx.resume();
      }

      // Stereo panner (-1.0 left to +1.0 right)
      const panner = audioCtx.createStereoPanner();
      const panVal = Math.sin((angleDeg * Math.PI) / 180.0);
      panner.pan.value = Math.max(-1.0, Math.min(1.0, panVal));

      const now = audioCtx.currentTime;
      const masterGain = audioCtx.createGain();
      masterGain.gain.setValueAtTime(0.3, now);

      if (sigType === "snap") {
        // High frequency bandpass transient with sharp exponential envelope
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(2800, now);
        osc.frequency.exponentialRampToValueAtTime(1200, now + 0.04);

        gain.gain.setValueAtTime(1.0, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

        osc.connect(gain);
        gain.connect(panner);
        panner.connect(audioCtx.destination);

        osc.start(now);
        osc.stop(now + 0.06);
      } else if (sigType === "chirp") {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(1000, now);
        osc.frequency.exponentialRampToValueAtTime(3800, now + 0.08);

        gain.gain.setValueAtTime(0.6, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);

        osc.connect(gain);
        gain.connect(panner);
        panner.connect(audioCtx.destination);

        osc.start(now);
        osc.stop(now + 0.09);
      } else {
        // Hand clap / noise burst
        const bufferSize = audioCtx.sampleRate * 0.07;
        const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
          data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (audioCtx.sampleRate * 0.015));
        }
        const noise = audioCtx.createBufferSource();
        noise.buffer = buffer;
        noise.connect(panner);
        panner.connect(audioCtx.destination);
        noise.start(now);
      }
    } catch (e) {
      console.warn("Audio playback not permitted yet:", e);
    }
  }

  // ============================================================================
  // 6. API INTERFACE & SIMULATION TRIGGER
  // ============================================================================
  async function triggerSimulation() {
    state.wavefrontActive = true;
    state.wavefrontRadius = 5;

    // Audio cue
    playStereoTransient(state.angleDeg, state.signalType);

    try {
      const payload = {
        angle_deg: state.angleDeg,
        distance_m: state.distanceM,
        signal_type: state.signalType,
        snr_db: state.snrDb,
        rt60_s: state.rt60S
      };

      const res = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      updateInferenceUI(data);
    } catch (err) {
      console.error("Simulation API error:", err);
      logTerminal(`Simulation error: ${err.message}`, "error");
    }
  }

  function updateInferenceUI(data) {
    const inf = data.inference;
    const dsp = data.dsp;
    const wave = data.waveforms;
    const prof = data.profiling;

    // 1. Compass Needle & Sector Callout
    compassNeedle.style.transform = `rotate(${state.angleDeg}deg)`;
    predictedSectorText.textContent = inf.predicted_sector;
    predictedConfidenceText.textContent = `${inf.confidence_percent}%`;
    predictedLagText.textContent = `τ = ${dsp.peak_lag}`;

    // Color glow based on sector
    predictedSectorText.className = "callout-value";
    if (inf.predicted_sector.includes("LEFT")) {
      predictedSectorText.classList.add("sector-left-glow");
    } else if (inf.predicted_sector.includes("RIGHT")) {
      predictedSectorText.classList.add("sector-right-glow");
    } else {
      predictedSectorText.classList.add("sector-center-glow");
    }

    // 2. Probability Distribution Bars
    const probs = inf.sector_probabilities;
    probLeftText.textContent = `${probs.LEFT}%`;
    probCenterText.textContent = `${probs.CENTER}%`;
    probRightText.textContent = `${probs.RIGHT}%`;

    probBarLeft.style.width = `${probs.LEFT}%`;
    probBarCenter.style.width = `${probs.CENTER}%`;
    probBarRight.style.width = `${probs.RIGHT}%`;

    // 3. Oscilloscope & NCC Spectrum
    drawOscilloscope(wave.left_channel, wave.right_channel);
    drawNccSpectrum(dsp.lags, dsp.ncc_features, dsp.peak_lag);

    valPeakLag.textContent = dsp.peak_lag;
    valPeakNcc.textContent = data.physics.peak_ncc_correlation.toFixed(3);

    // 4. Profiler stats
    document.getElementById("prof-total-lat").textContent = `${prof.esp32_benchmarks.esp32_total_latency_ms.toFixed(2)} ms`;
    document.getElementById("prof-dsp-lat").textContent = `${prof.esp32_benchmarks.esp32_dsp_ncc_us.toFixed(2)} μs`;
    document.getElementById("prof-tflm-lat").textContent = `${prof.esp32_benchmarks.esp32_tflm_inference_us.toFixed(1)} μs`;
    document.getElementById("prof-throughput").textContent = `${(prof.esp32_benchmarks.dsp_throughput_inferences_per_sec / 1000).toFixed(1)} k`;
  }

  // ============================================================================
  // 7. TERMINAL & BENCHMARK RUNNER
  // ============================================================================
  function logTerminal(msg, type = "normal") {
    const line = document.createElement("div");
    line.className = `term-line ${type}`;
    line.textContent = `> ${msg}`;
    terminalBody.appendChild(line);
    terminalBody.scrollTop = terminalBody.scrollHeight;
  }

  async function executeDspBenchmark() {
    logTerminal("Invoking native C++ benchmark harness (test_dsp.exe)...", "info");
    try {
      const res = await fetch("/api/run-dsp-benchmark");
      const data = await res.json();
      if (data.status === "success") {
        const lines = data.stdout.trim().split("\n");
        lines.forEach(l => {
          if (l.includes("PASSED")) logTerminal(l, "success");
          else if (l.includes("Execution Time")) logTerminal(l, "highlight");
          else if (l.trim()) logTerminal(l, "normal");
        });
      } else {
        logTerminal(`Benchmark failed with code ${data.exit_code}: ${data.stderr}`, "error");
      }
    } catch (err) {
      logTerminal(`Execution error: ${err.message}`, "error");
    }
  }

  // ============================================================================
  // 8. EVENT LISTENERS & USER INTERACTION
  // ============================================================================
  // Angle Slider
  sliderAngle.addEventListener("input", (e) => {
    updateAngleAndDistanceByAngle(parseInt(e.target.value));
  });

  function updateAngleAndDistanceByAngle(angle) {
    state.angleDeg = angle;
    valAngle.textContent = `${angle}°`;
    lblReadoutAngle.textContent = `${angle}°`;
    updateSourceFromAngleAndDistance();
    drawRoom();
    triggerSimulation();
  }

  // Distance Slider
  sliderDistance.addEventListener("input", (e) => {
    state.distanceM = parseFloat(e.target.value);
    valDist.textContent = `${state.distanceM.toFixed(2)} m`;
    lblReadoutDist.textContent = `${state.distanceM.toFixed(2)} m`;
    updateSourceFromAngleAndDistance();
    drawRoom();
    triggerSimulation();
  });

  // SNR & RT60
  sliderSnr.addEventListener("input", (e) => {
    state.snrDb = parseFloat(e.target.value);
    valSnr.textContent = `${state.snrDb} dB`;
    triggerSimulation();
  });

  sliderRt60.addEventListener("input", (e) => {
    state.rt60S = parseFloat(e.target.value);
    valRt60.textContent = `${state.rt60S.toFixed(2)} s`;
    triggerSimulation();
  });

  selectTransient.addEventListener("change", (e) => {
    state.signalType = e.target.value;
    triggerSimulation();
  });

  chkAudio.addEventListener("change", (e) => {
    state.audioEnabled = e.target.checked;
  });

  // Presets
  document.getElementById("btn-preset-left").addEventListener("click", () => {
    updateAngleAndDistanceByAngle(-45);
  });
  document.getElementById("btn-preset-center").addEventListener("click", () => {
    updateAngleAndDistanceByAngle(0);
  });
  document.getElementById("btn-preset-right").addEventListener("click", () => {
    updateAngleAndDistanceByAngle(45);
  });
  document.getElementById("btn-preset-random").addEventListener("click", () => {
    const rAngle = Math.floor(Math.random() * 110 - 55);
    updateAngleAndDistanceByAngle(rAngle);
  });

  // Action Buttons
  btnFirePulse.addEventListener("click", () => {
    triggerSimulation();
  });

  btnAutoStream.addEventListener("click", () => {
    state.isStreaming = !state.isStreaming;
    if (state.isStreaming) {
      btnAutoStream.classList.add("active");
      btnAutoStream.innerHTML = '<span class="pulsing-record-dot"></span> Streaming Active...';
      logTerminal("Continuous acoustic telemetry streaming engaged.", "info");
      state.streamTimer = setInterval(() => {
        // Small angular jitter around sector
        const r = Math.random();
        let targetAngle = 0;
        if (r < 0.33) targetAngle = Math.floor(Math.random() * 20 - 55); // Left
        else if (r < 0.66) targetAngle = Math.floor(Math.random() * 20 - 10); // Center
        else targetAngle = Math.floor(Math.random() * 20 + 35); // Right
        
        updateAngleAndDistanceByAngle(targetAngle);
      }, 700);
    } else {
      btnAutoStream.classList.remove("active");
      btnAutoStream.innerHTML = '<span class="pulsing-record-dot"></span> Auto Continuous Stream';
      clearInterval(state.streamTimer);
      state.streamTimer = null;
      logTerminal("Continuous acoustic telemetry stopped.", "normal");
    }
  });

  btnRunBenchmark.addEventListener("click", executeDspBenchmark);
  btnReRunDsp.addEventListener("click", executeDspBenchmark);

  // Mouse Interaction on 2D Room Canvas (Click / Drag sound emitter)
  function handleRoomPointer(e) {
    const rect = canvasRoom.getBoundingClientRect();
    const px = (e.clientX - rect.left) * (canvasRoom.width / rect.width);
    const py = (e.clientY - rect.top) * (canvasRoom.height / rect.height);
    const meterCoords = getMeterCoordsFromPixel(px, py);
    updateAngleAndDistance(meterCoords.x, meterCoords.y);
    drawRoom();
  }

  canvasRoom.addEventListener("mousedown", (e) => {
    state.isDragging = true;
    handleRoomPointer(e);
  });

  window.addEventListener("mousemove", (e) => {
    if (state.isDragging) {
      handleRoomPointer(e);
    }
  });

  window.addEventListener("mouseup", () => {
    if (state.isDragging) {
      state.isDragging = false;
      triggerSimulation();
    }
  });

  // Touch Support
  canvasRoom.addEventListener("touchstart", (e) => {
    state.isDragging = true;
    if (e.touches.length > 0) handleRoomPointer(e.touches[0]);
    e.preventDefault();
  }, { passive: false });

  canvasRoom.addEventListener("touchmove", (e) => {
    if (state.isDragging && e.touches.length > 0) {
      handleRoomPointer(e.touches[0]);
    }
    e.preventDefault();
  }, { passive: false });

  canvasRoom.addEventListener("touchend", () => {
    state.isDragging = false;
    triggerSimulation();
  });

  // Lightbox Modal for Publication Figures
  document.querySelectorAll(".thumb-card").forEach(card => {
    card.addEventListener("click", () => {
      const fig = card.getAttribute("data-fig");
      const title = card.getAttribute("data-title");
      modalImg.src = `/report_assets/${fig}`;
      modalTitle.textContent = title;
      lightboxModal.style.display = "flex";
    });
  });

  modalCloseBtn.addEventListener("click", () => {
    lightboxModal.style.display = "none";
  });

  lightboxModal.addEventListener("click", (e) => {
    if (e.target === lightboxModal) lightboxModal.style.display = "none";
  });

  // Animation Loop for Wavefront Pulses
  function animationLoop() {
    if (state.wavefrontActive) {
      state.wavefrontRadius += 4;
      if (state.wavefrontRadius > 260) {
        state.wavefrontActive = false;
      }
      drawRoom();
    }
    requestAnimationFrame(animationLoop);
  }

  // ============================================================================
  // 9. INITIALIZATION
  // ============================================================================
  updateSourceFromAngleAndDistance();
  drawRoom();
  drawOscilloscope([], []);
  drawNccSpectrum([], [], 0);
  animationLoop();

  // Initial simulation run to populate widgets
  setTimeout(() => {
    triggerSimulation();
    logTerminal("Acoustic DoA System online. Model: int8 TFLite (2.89 KB).", "success");
    logTerminal("Initialized 5x5m acoustic shoe-box room model (T60 = 0.20s).", "info");
  }, 300);
});
