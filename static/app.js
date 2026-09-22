/**
 * PRECISION SPATIAL ACOUSTIC DIRECTION OF ARRIVAL (DoA)
 * Aesthetic: Luxury Swiss Audio / Apple Vision Pro / Teenage Engineering
 * Core: Three.js WebGL with UnrealBloomPass Cinematic Post-Processing
 */

(function () {
  "use strict";

  const SPEED_OF_SOUND = 343.0;
  const MIC_BASELINE = 0.10;

  const state = {
    currentSector: "CENTER",
    currentAngle: 0,
    confidence: 98.5,
    intensity: 0,
    peakLag: 0,
    peakNcc: 0.992,
    hardwareConnected: false,
    port: "COM3",
    audioMuted: false,
  };

  // DOM Elements
  const container3D = document.getElementById("canvas-container-3d");
  const statusLaser = document.getElementById("status-laser");
  const hwPortLabel = document.getElementById("hw-port-label");
  const dspLatVal = document.getElementById("dsp-lat-val");
  const nnLatVal = document.getElementById("nn-lat-val");

  const sectorMonolith = document.getElementById("sector-monolith");
  const heroDirection = document.getElementById("hero-direction");
  const teleAngle = document.getElementById("tele-angle");
  const teleConf = document.getElementById("tele-conf");
  const teleLag = document.getElementById("tele-lag");
  const teleNcc = document.getElementById("tele-ncc");

  const intensityVal = document.getElementById("intensity-val");
  const intensityFill = document.getElementById("intensity-fill");
  const intensityPeak = document.getElementById("intensity-peak");

  const btnLeft = document.getElementById("btn-trigger-left");
  const btnCenter = document.getElementById("btn-trigger-center");
  const btnRight = document.getElementById("btn-trigger-right");
  const btnClap = document.getElementById("btn-trigger-clap");
  const btnToggleSound = document.getElementById("btn-toggle-sound");

  // ============================================================================
  // 1. SPATIAL AUDIO SYNTHESIZER
  // ============================================================================
  let audioCtx = null;

  function playSpatialImpulse(angleDeg, intensity = 85) {
    if (state.audioMuted) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!audioCtx) audioCtx = new AudioContextClass();
      if (audioCtx.state === "suspended") audioCtx.resume();

      const now = audioCtx.currentTime;
      const panVal = Math.max(-1.0, Math.min(1.0, angleDeg / 45.0));

      let panner = null;
      if (audioCtx.createStereoPanner) {
        panner = audioCtx.createStereoPanner();
        panner.pan.setValueAtTime(panVal, now);
      }

      const snapOsc = audioCtx.createOscillator();
      const snapGain = audioCtx.createGain();
      const baseFreq = angleDeg > 15 ? 880 : (angleDeg < -15 ? 680 : 780);

      snapOsc.type = "triangle";
      snapOsc.frequency.setValueAtTime(baseFreq * 2.2, now);
      snapOsc.frequency.exponentialRampToValueAtTime(baseFreq * 0.4, now + 0.08);

      const vol = 0.12 * Math.min(1.0, Math.max(0.2, intensity / 100.0));
      snapGain.gain.setValueAtTime(vol, now);
      snapGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.09);

      const bodyOsc = audioCtx.createOscillator();
      const bodyGain = audioCtx.createGain();
      bodyOsc.type = "sine";
      bodyOsc.frequency.setValueAtTime(baseFreq * 0.7, now);
      bodyOsc.frequency.exponentialRampToValueAtTime(baseFreq * 0.3, now + 0.14);
      bodyGain.gain.setValueAtTime(vol * 0.6, now);
      bodyGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.15);

      const destination = panner || audioCtx.destination;
      if (panner) panner.connect(audioCtx.destination);

      snapOsc.connect(snapGain);
      snapGain.connect(destination);
      bodyOsc.connect(bodyGain);
      bodyGain.connect(destination);

      snapOsc.start(now);
      bodyOsc.start(now);
      snapOsc.stop(now + 0.1);
      bodyOsc.stop(now + 0.16);
    } catch (e) {}
  }

  // ============================================================================
  // 2. THREE.JS 3D SCENE WITH UNREAL BLOOM PASS
  // ============================================================================
  let scene, camera, renderer, composer, controls;
  let entityGroup, blueLedMesh, blueLedLight, shadowMesh;
  let activeWavePackets = [];
  let sourceBeacons = { LEFT: null, CENTER: null, RIGHT: null };
  let targetTiltZ = 0, targetTiltX = 0, currentTiltZ = 0, currentTiltX = 0;

  function init3D() {
    if (!window.THREE || !container3D) return;

    const width = container3D.clientWidth || window.innerWidth;
    const height = container3D.clientHeight || window.innerHeight;

    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x040507, 0.042);

    camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(0, 3.8, 6.4);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;

    container3D.innerHTML = "";
    container3D.appendChild(renderer.domElement);

    if (window.THREE.OrbitControls) {
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
      controls.maxPolarAngle = Math.PI / 2 - 0.04;
      controls.minDistance = 3.2;
      controls.maxDistance = 14.0;
      controls.target.set(0, 0.1, 0);
    }

    // Postprocessing with UnrealBloomPass
    if (window.THREE.EffectComposer && window.THREE.RenderPass && window.THREE.UnrealBloomPass) {
      const renderPass = new THREE.RenderPass(scene, camera);
      const bloomPass = new THREE.UnrealBloomPass(new THREE.Vector2(width, height), 1.2, 0.75, 0.18);
      composer = new THREE.EffectComposer(renderer);
      composer.addPass(renderPass);
      composer.addPass(bloomPass);
    }

    // Lighting
    scene.add(new THREE.AmbientLight(0x222E42, 1.4));
    const keyLight = new THREE.DirectionalLight(0xF8FAFC, 1.8);
    keyLight.position.set(5, 12, 6);
    scene.add(keyLight);
    const rimLight = new THREE.DirectionalLight(0x38BDF8, 0.9);
    rimLight.position.set(-6, -4, -6);
    scene.add(rimLight);

    // Floor & Radar rings
    buildFloor();

    // Central 3D Minimalist Hardware Entity (ESP32)
    buildEntity();

    // Beacons
    buildBeacons();

    // Event Listeners
    setupControls();

    // Animate
    animate();
  }

  function buildFloor() {
    const ringGeo = new THREE.RingGeometry(3.6, 3.63, 80);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x38BDF8, transparent: true, opacity: 0.14, side: THREE.DoubleSide });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = -0.55;
    scene.add(ring);

    [-45, 0, 45].forEach(deg => {
      const rad = (deg * Math.PI) / 180.0;
      const pts = [
        new THREE.Vector3(3.2 * Math.sin(rad), -0.55, -3.2 * Math.cos(rad)),
        new THREE.Vector3(3.9 * Math.sin(rad), -0.55, -3.9 * Math.cos(rad))
      ];
      const tickGeo = new THREE.BufferGeometry().setFromPoints(pts);
      const tickMat = new THREE.LineBasicMaterial({
        color: deg === 0 ? 0x10B981 : (deg > 0 ? 0x38BDF8 : 0x00F0FF),
        transparent: true,
        opacity: 0.45
      });
      scene.add(new THREE.Line(tickGeo, tickMat));
    });

    const sCanvas = document.createElement("canvas");
    sCanvas.width = 128; sCanvas.height = 128;
    const sCtx = sCanvas.getContext("2d");
    if (sCtx) {
      const g = sCtx.createRadialGradient(64, 64, 12, 64, 64, 60);
      g.addColorStop(0, "rgba(0,0,0,0.7)");
      g.addColorStop(0.5, "rgba(0,0,0,0.25)");
      g.addColorStop(1, "rgba(0,0,0,0)");
      sCtx.fillStyle = g;
      sCtx.fillRect(0, 0, 128, 128);
    }
    const sTex = new THREE.CanvasTexture(sCanvas);
    shadowMesh = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 1.8), new THREE.MeshBasicMaterial({ map: sTex, transparent: true, depthWrite: false }));
    shadowMesh.rotation.x = -Math.PI / 2;
    shadowMesh.position.set(0, -0.54, 0);
    scene.add(shadowMesh);
  }

  function buildEntity() {
    entityGroup = new THREE.Group();

    // Chassis
    const chassisMat = new THREE.MeshStandardMaterial({ color: 0x111622, roughness: 0.35, metalness: 0.45 });
    entityGroup.add(new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.22, 1.2), chassisMat));

    // Top Plate
    const plate = new THREE.Mesh(new THREE.BoxGeometry(2.32, 0.05, 1.12), new THREE.MeshStandardMaterial({ color: 0x0D111A, roughness: 0.25, metalness: 0.6 }));
    plate.position.y = 0.12;
    entityGroup.add(plate);

    // Shield
    const shield = new THREE.Mesh(new THREE.BoxGeometry(0.85, 0.1, 0.75), new THREE.MeshStandardMaterial({ color: 0x94A3B8, metalness: 0.92, roughness: 0.18 }));
    shield.position.set(-0.45, 0.18, 0);
    entityGroup.add(shield);

    // USB-C
    const usb = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.1, 0.24), new THREE.MeshStandardMaterial({ color: 0x64748B, metalness: 0.85, roughness: 0.2 }));
    usb.position.set(-1.22, 0.11, 0);
    entityGroup.add(usb);

    // Microphones
    function makeMic(isLeft) {
      const g = new THREE.Group();
      g.add(new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 0.28, 32), new THREE.MeshStandardMaterial({ color: 0x1E293B, metalness: 0.8, roughness: 0.3 })));
      const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.06, 32), new THREE.MeshStandardMaterial({ color: 0xEAB308, metalness: 0.95, roughness: 0.15 }));
      cap.position.y = 0.16;
      g.add(cap);
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.14, 0.02, 16, 32), new THREE.MeshBasicMaterial({ color: isLeft ? 0x00F0FF : 0x38BDF8, transparent: true, opacity: 0.8 }));
      ring.rotation.x = Math.PI / 2;
      ring.position.y = 0.14;
      g.add(ring);
      return g;
    }

    const micL = makeMic(true); micL.position.set(-0.85, 0.14, 0.32); entityGroup.add(micL);
    const micR = makeMic(false); micR.position.set(0.85, 0.14, 0.32); entityGroup.add(micR);

    // Trace
    const trace = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.01, 0.04), new THREE.MeshStandardMaterial({ color: 0xF59E0B, metalness: 0.95, roughness: 0.1 }));
    trace.position.set(0, 0.15, 0.32);
    entityGroup.add(trace);

    // Blue LED
    blueLedMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.065, 0.05, 24), new THREE.MeshStandardMaterial({ color: 0x00F0FF, emissive: 0x00F0FF, emissiveIntensity: 0.8, roughness: 0.1 }));
    blueLedMesh.position.set(0.45, 0.17, -0.3);
    entityGroup.add(blueLedMesh);

    blueLedLight = new THREE.PointLight(0x00F0FF, 0.8, 4.0);
    blueLedLight.position.set(0.45, 0.35, -0.3);
    entityGroup.add(blueLedLight);

    entityGroup.position.set(0, 0, 0);
    scene.add(entityGroup);
  }

  function buildBeacons() {
    [
      { id: "LEFT", angle: -45, color: 0x00F0FF },
      { id: "CENTER", angle: 0, color: 0x10B981 },
      { id: "RIGHT", angle: 45, color: 0x38BDF8 }
    ].forEach(s => {
      const rad = (s.angle * Math.PI) / 180.0;
      const x = 3.6 * Math.sin(rad);
      const z = -3.6 * Math.cos(rad);
      const g = new THREE.Group();
      g.position.set(x, 0, z);

      const m = new THREE.Mesh(new THREE.SphereGeometry(0.12, 24, 24), new THREE.MeshStandardMaterial({ color: s.color, emissive: s.color, emissiveIntensity: 1.4, roughness: 0.2 }));
      g.add(m);
      const l = new THREE.PointLight(s.color, 0.6, 2.5);
      g.add(l);
      scene.add(g);
      sourceBeacons[s.id] = { group: g, mesh: m, light: l };
    });
  }

  function triggerWifiSoundWaves(angleDeg, intensity = 85) {
    const rad = (angleDeg * Math.PI) / 180.0;
    const originX = 3.6 * Math.sin(rad);
    const originZ = -3.6 * Math.cos(rad);

    let waveColorHex = 0x38BDF8;
    if (angleDeg < -15) waveColorHex = 0x00F0FF;
    else if (Math.abs(angleDeg) <= 15) waveColorHex = 0x10B981;

    const dirVector = new THREE.Vector3(-originX, 0, -originZ).normalize();
    const facingAngle = Math.atan2(-dirVector.x, -dirVector.z);

    const arcCount = 4;
    const arcMeshes = [];

    for (let i = 0; i < arcCount; i++) {
      const baseRadius = 0.55 + i * 0.45;
      const arcSpan = Math.PI * 0.44;
      const tubeRadius = 0.038;

      const torusGeo = new THREE.TorusGeometry(baseRadius, tubeRadius, 16, 54, arcSpan);
      const torusMat = new THREE.MeshBasicMaterial({
        color: waveColorHex,
        transparent: true,
        opacity: 0.95,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      });

      const arcMesh = new THREE.Mesh(torusGeo, torusMat);
      arcMesh.rotation.x = Math.PI / 2;
      arcMesh.rotation.z = facingAngle - arcSpan / 2;
      arcMesh.position.set(originX, 0.05, originZ);

      scene.add(arcMesh);
      arcMeshes.push({ mesh: arcMesh, material: torusMat, baseRadius, progress: -i * 0.14 });
    }

    activeWavePackets.push({ originX, originZ, dirVector, arcs: arcMeshes, alive: true });

    // Flash Beacon
    const bKey = angleDeg > 15 ? "RIGHT" : (angleDeg < -15 ? "LEFT" : "CENTER");
    if (sourceBeacons[bKey]) {
      const b = sourceBeacons[bKey];
      b.light.intensity = 3.5;
      b.mesh.scale.set(1.6, 1.6, 1.6);
      setTimeout(() => { b.light.intensity = 0.6; b.mesh.scale.set(1.0, 1.0, 1.0); }, 400);
    }

    // Flash LED
    if (blueLedLight && blueLedMesh) {
      blueLedLight.intensity = 1.0 + (intensity / 100.0) * 4.5;
      blueLedMesh.material.emissiveIntensity = 4.0;
      let s = 0;
      const f = setInterval(() => {
        s++;
        blueLedLight.intensity = Math.max(0.8, blueLedLight.intensity - 0.2);
        blueLedMesh.material.emissiveIntensity = Math.max(0.8, blueLedMesh.material.emissiveIntensity - 0.18);
        if (s > 25) { clearInterval(f); blueLedLight.intensity = 0.8; blueLedMesh.material.emissiveIntensity = 0.8; }
      }, 20);
    }

    // Dynamic tilt
    if (angleDeg > 15) { targetTiltZ = -0.12; targetTiltX = 0.05; }
    else if (angleDeg < -15) { targetTiltZ = 0.12; targetTiltX = 0.05; }
    else { targetTiltZ = 0.0; targetTiltX = -0.08; }

    setTimeout(() => { targetTiltZ = 0.0; targetTiltX = 0.0; }, 1400);
  }

  function setupControls() {
    window.addEventListener("resize", () => {
      if (!renderer || !camera || !container3D) return;
      const w = container3D.clientWidth || window.innerWidth;
      const h = container3D.clientHeight || window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      if (composer) composer.setSize(w, h);
    });

    btnLeft.addEventListener("click", () => triggerAcousticImpulse("LEFT", -45));
    btnCenter.addEventListener("click", () => triggerAcousticImpulse("CENTER", 0));
    btnRight.addEventListener("click", () => triggerAcousticImpulse("RIGHT", 45));
    btnClap.addEventListener("click", () => triggerAcousticImpulse(state.currentSector, state.currentAngle, 100));

    btnToggleSound.addEventListener("click", () => {
      state.audioMuted = !state.audioMuted;
      btnToggleSound.classList.toggle("active", state.audioMuted);
    });
  }

  function animate() {
    requestAnimationFrame(animate);

    if (controls) controls.update();

    const time = Date.now() * 0.002;
    if (entityGroup) {
      entityGroup.position.y = Math.sin(time) * 0.05 + 0.02;
      currentTiltZ += (targetTiltZ - currentTiltZ) * 0.08;
      currentTiltX += (targetTiltX - currentTiltX) * 0.08;
      entityGroup.rotation.z = currentTiltZ;
      entityGroup.rotation.x = currentTiltX;
    }

    if (shadowMesh && entityGroup) {
      const s = 1.0 - entityGroup.position.y * 0.8;
      shadowMesh.scale.set(s, s, s);
    }

    for (let pIdx = activeWavePackets.length - 1; pIdx >= 0; pIdx--) {
      const packet = activeWavePackets[pIdx];
      let allDead = true;

      packet.arcs.forEach(arc => {
        arc.progress += 0.018;
        if (arc.progress > 0 && arc.progress < 1.0) {
          allDead = false;
          const travelDist = arc.progress * 3.6;
          const currX = packet.originX + packet.dirVector.x * travelDist;
          const currZ = packet.originZ + packet.dirVector.z * travelDist;
          arc.mesh.position.set(currX, 0.05 + Math.sin(arc.progress * Math.PI) * 0.12, currZ);

          const scale = 1.0 + arc.progress * 1.4;
          arc.mesh.scale.set(scale, scale, scale);

          const fade = Math.sin(arc.progress * Math.PI);
          arc.material.opacity = Math.max(0, fade * 0.95);
        } else if (arc.progress >= 1.0) {
          arc.material.opacity = 0;
        } else {
          allDead = false;
        }
      });

      if (allDead) {
        packet.arcs.forEach(a => scene.remove(a.mesh));
        activeWavePackets.splice(pIdx, 1);
      }
    }

    if (composer) {
      composer.render();
    } else if (renderer && scene && camera) {
      renderer.render(scene, camera);
    }
  }

  // ============================================================================
  // 3. WEBSOCKET & HARDWARE LINK
  // ============================================================================
  let socket = null;

  function connectWebSocket() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${location.host}/ws/live-telemetry`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => updateHardwareStatus(true, state.port);

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "init" || msg.type === "status") {
          updateHardwareStatus(msg.hardware_connected, msg.port);
        } else if (msg.type === "doa_event") {
          onDoAEvent(msg);
        }
      } catch (err) {}
    };

    socket.onclose = () => {
      updateHardwareStatus(false, null);
      setTimeout(connectWebSocket, 2500);
    };
  }

  function updateHardwareStatus(online, port) {
    state.hardwareConnected = online;
    if (online) {
      state.port = port || "COM3";
      statusLaser.className = "laser-indicator";
      hwPortLabel.textContent = `ESP32 • ${state.port} @ 115200 BAUD`;
    } else {
      statusLaser.className = "laser-indicator searching";
      hwPortLabel.textContent = "CONNECTING ESP32...";
    }
  }

  function onDoAEvent(ev) {
    const sector = ev.sector || "CENTER";
    const angle = Math.round(ev.angle_deg || 0);
    const conf = ev.confidence || 98.0;
    const intensity = ev.intensity || 85;
    const lag = ev.peak_lag !== undefined ? ev.peak_lag : 0;
    const ncc = ev.peak_ncc || 0.992;

    state.currentSector = sector;
    state.currentAngle = angle;
    state.confidence = conf;
    state.intensity = intensity;
    state.peakLag = lag;
    state.peakNcc = ncc;

    if (ev.dsp_us && dspLatVal) dspLatVal.textContent = `${(ev.dsp_us / 1000).toFixed(1)} μs`;
    if (ev.nn_us && nnLatVal) nnLatVal.textContent = `${(ev.nn_us / 1000).toFixed(1)} μs`;

    playSpatialImpulse(angle, intensity);
    triggerWifiSoundWaves(angle, intensity);
    updateCallout(sector, angle, conf, lag, ncc, intensity);
    updateButtons(sector);
  }

  function updateCallout(sector, angle, conf, lag, ncc, intensity) {
    sectorMonolith.textContent = sector;

    heroDirection.className = "hero-direction";
    if (sector === "RIGHT") {
      heroDirection.textContent = "Right (+45°)";
      heroDirection.classList.add("state-right");
    } else if (sector === "LEFT") {
      heroDirection.textContent = "Left (-45°)";
      heroDirection.classList.add("state-left");
    } else {
      heroDirection.textContent = "Boresight Center (0°)";
      heroDirection.classList.add("state-center");
    }

    teleAngle.textContent = `${angle > 0 ? "+" : ""}${angle.toFixed(1)}°`;
    teleConf.textContent = `${conf.toFixed(1)}%`;
    teleLag.textContent = `${lag}`;
    teleNcc.textContent = `${ncc.toFixed(3)}`;

    intensityVal.textContent = `${intensity}%`;
    intensityFill.style.width = `${Math.min(100, intensity)}%`;
    intensityPeak.style.left = `${Math.min(99, intensity)}%`;
    intensityPeak.style.opacity = intensity > 10 ? "1" : "0";

    setTimeout(() => {
      intensityFill.style.width = "0%";
      intensityVal.textContent = "0%";
      intensityPeak.style.opacity = "0";
    }, 600);
  }

  function updateButtons(sector) {
    btnLeft.classList.toggle("active", sector === "LEFT");
    btnCenter.classList.toggle("active", sector === "CENTER");
    btnRight.classList.toggle("active", sector === "RIGHT");
  }

  function triggerAcousticImpulse(sector, angle, intensity = 90) {
    state.currentSector = sector;
    state.currentAngle = angle;
    state.confidence = 99.2;
    state.intensity = intensity;
    state.peakLag = sector === "LEFT" ? 3 : (sector === "RIGHT" ? -3 : 0);

    const key = sector === "LEFT" ? "l" : (sector === "RIGHT" ? "r" : "c");
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ action: "trigger", key }));
    } else {
      fetch(`/api/hardware/trigger?direction=${sector.toLowerCase()}`, { method: "POST" }).catch(() => {});
    }

    playSpatialImpulse(angle, intensity);
    triggerWifiSoundWaves(angle, intensity);
    updateCallout(sector, angle, state.confidence, state.peakLag, state.peakNcc, intensity);
    updateButtons(sector);
  }

  window.addEventListener("DOMContentLoaded", () => {
    init3D();
    connectWebSocket();
  });
})();
