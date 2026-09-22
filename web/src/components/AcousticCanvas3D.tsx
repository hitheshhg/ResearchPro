"use client";

import { useEffect, useRef, useImperativeHandle, forwardRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { Sector } from "@/types/telemetry";

export interface AcousticCanvas3DRef {
  triggerAcousticImpulse: (sector: Sector, angleDeg: number, intensity?: number) => void;
}

interface WaveArc {
  mesh: THREE.Mesh;
  material: THREE.MeshBasicMaterial;
  baseRadius: number;
  delayOffset: number;
  progress: number;
}

interface WavePacket {
  originX: number;
  originZ: number;
  dirVector: THREE.Vector3;
  facingAngle: number;
  arcs: WaveArc[];
  particles: THREE.Points;
  alive: boolean;
}

export const AcousticCanvas3D = forwardRef<AcousticCanvas3DRef>((_, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerImpulseRef = useRef<((sector: Sector, angleDeg: number, intensity: number) => void) | null>(null);

  useImperativeHandle(ref, () => ({
    triggerAcousticImpulse: (sector: Sector, angleDeg: number, intensity: number = 85) => {
      if (triggerImpulseRef.current) {
        triggerImpulseRef.current(sector, angleDeg, intensity);
      }
    },
  }));

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let animFrameId: number;

    // 1. Scene & Depth Fog
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x040507, 0.042);

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(0, 3.8, 6.4);

    // 3. WebGL Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    // 4. Orbit Controls (Smooth Inertia)
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 - 0.04;
    controls.minDistance = 3.2;
    controls.maxDistance = 14.0;
    controls.target.set(0, 0.1, 0);

    // 5. Cinematic Post-Processing: UnrealBloomPass
    const renderPass = new RenderPass(scene, camera);
    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(width, height),
      1.2,   // bloom strength
      0.75,  // bloom radius
      0.18   // bloom threshold
    );

    const composer = new EffectComposer(renderer);
    composer.addPass(renderPass);
    composer.addPass(bloomPass);

    // 6. Lighting
    const ambientLight = new THREE.AmbientLight(0x222E42, 1.4);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xF8FAFC, 1.8);
    keyLight.position.set(5, 12, 6);
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x38BDF8, 0.9);
    rimLight.position.set(-6, -4, -6);
    scene.add(rimLight);

    // 7. Minimalist Radar Floor
    const floorGroup = new THREE.Group();
    const ringGeo = new THREE.RingGeometry(3.6, 3.63, 80);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x38BDF8,
      transparent: true,
      opacity: 0.14,
      side: THREE.DoubleSide,
    });
    const radarRing = new THREE.Mesh(ringGeo, ringMat);
    radarRing.rotation.x = -Math.PI / 2;
    radarRing.position.y = -0.55;
    floorGroup.add(radarRing);

    // Subtle incidence tick lines (-45°, 0°, +45°)
    [-45, 0, 45].forEach((deg) => {
      const rad = (deg * Math.PI) / 180.0;
      const pts = [
        new THREE.Vector3(3.2 * Math.sin(rad), -0.55, -3.2 * Math.cos(rad)),
        new THREE.Vector3(3.9 * Math.sin(rad), -0.55, -3.9 * Math.cos(rad)),
      ];
      const tickGeo = new THREE.BufferGeometry().setFromPoints(pts);
      const tickMat = new THREE.LineBasicMaterial({
        color: deg === 0 ? 0x10B981 : deg > 0 ? 0x38BDF8 : 0x00F0FF,
        transparent: true,
        opacity: 0.45,
      });
      floorGroup.add(new THREE.Line(tickGeo, tickMat));
    });

    // Soft Contact Shadow
    const shadowCanvas = document.createElement("canvas");
    shadowCanvas.width = 128;
    shadowCanvas.height = 128;
    const sCtx = shadowCanvas.getContext("2d");
    if (sCtx) {
      const g = sCtx.createRadialGradient(64, 64, 12, 64, 64, 60);
      g.addColorStop(0, "rgba(0, 0, 0, 0.7)");
      g.addColorStop(0.5, "rgba(0, 0, 0, 0.25)");
      g.addColorStop(1, "rgba(0, 0, 0, 0)");
      sCtx.fillStyle = g;
      sCtx.fillRect(0, 0, 128, 128);
    }
    const shadowTex = new THREE.CanvasTexture(shadowCanvas);
    const shadowMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(3.2, 1.8),
      new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false })
    );
    shadowMesh.rotation.x = -Math.PI / 2;
    shadowMesh.position.set(0, -0.54, 0);
    floorGroup.add(shadowMesh);
    scene.add(floorGroup);

    // 8. Central 3D Minimalist Hardware Entity (ESP32 Acoustic Pod)
    const entityGroup = new THREE.Group();

    // Main Chassis: Matte basalt / obsidian rounded body
    const chassisGeo = new THREE.BoxGeometry(2.4, 0.22, 1.2);
    const chassisMat = new THREE.MeshStandardMaterial({
      color: 0x111622,
      roughness: 0.35,
      metalness: 0.45,
    });
    const chassis = new THREE.Mesh(chassisGeo, chassisMat);
    entityGroup.add(chassis);

    // Top Matte Faceplate
    const plateGeo = new THREE.BoxGeometry(2.32, 0.05, 1.12);
    const plateMat = new THREE.MeshStandardMaterial({
      color: 0x0D111A,
      roughness: 0.25,
      metalness: 0.6,
    });
    const plate = new THREE.Mesh(plateGeo, plateMat);
    plate.position.y = 0.12;
    entityGroup.add(plate);

    // Brushed Silver RF Shield
    const shieldGeo = new THREE.BoxGeometry(0.85, 0.1, 0.75);
    const shieldMat = new THREE.MeshStandardMaterial({
      color: 0x94A3B8,
      metalness: 0.92,
      roughness: 0.18,
    });
    const shield = new THREE.Mesh(shieldGeo, shieldMat);
    shield.position.set(-0.45, 0.18, 0);
    entityGroup.add(shield);

    // USB-C Connector
    const usbGeo = new THREE.BoxGeometry(0.3, 0.1, 0.24);
    const usbMat = new THREE.MeshStandardMaterial({ color: 0x64748B, metalness: 0.85, roughness: 0.2 });
    const usb = new THREE.Mesh(usbGeo, usbMat);
    usb.position.set(-1.22, 0.11, 0);
    entityGroup.add(usb);

    // Dual CNC Aluminum Microphone Capsules
    function buildMic(isLeft: boolean) {
      const g = new THREE.Group();
      const bodyGeo = new THREE.CylinderGeometry(0.13, 0.13, 0.28, 32);
      const bodyMat = new THREE.MeshStandardMaterial({ color: 0x1E293B, metalness: 0.8, roughness: 0.3 });
      g.add(new THREE.Mesh(bodyGeo, bodyMat));

      const capGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.06, 32);
      const capMat = new THREE.MeshStandardMaterial({ color: 0xEAB308, metalness: 0.95, roughness: 0.15 });
      const cap = new THREE.Mesh(capGeo, capMat);
      cap.position.y = 0.16;
      g.add(cap);

      const ringGeo = new THREE.TorusGeometry(0.14, 0.02, 16, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: isLeft ? 0x00F0FF : 0x38BDF8,
        transparent: true,
        opacity: 0.8,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 2;
      ring.position.y = 0.14;
      g.add(ring);
      return g;
    }

    const micLeft = buildMic(true);
    micLeft.position.set(-0.85, 0.14, 0.32);
    entityGroup.add(micLeft);

    const micRight = buildMic(false);
    micRight.position.set(0.85, 0.14, 0.32);
    entityGroup.add(micRight);

    // Micro-etched gold trace line
    const traceGeo = new THREE.BoxGeometry(1.7, 0.01, 0.04);
    const traceMat = new THREE.MeshStandardMaterial({ color: 0xF59E0B, metalness: 0.95, roughness: 0.1 });
    const trace = new THREE.Mesh(traceGeo, traceMat);
    trace.position.set(0, 0.15, 0.32);
    entityGroup.add(trace);

    // Onboard Cobalt Blue LED (GPIO 2)
    const ledLensGeo = new THREE.CylinderGeometry(0.065, 0.065, 0.05, 24);
    const ledLensMat = new THREE.MeshStandardMaterial({
      color: 0x00F0FF,
      emissive: 0x00F0FF,
      emissiveIntensity: 0.8,
      roughness: 0.1,
    });
    const blueLedMesh = new THREE.Mesh(ledLensGeo, ledLensMat);
    blueLedMesh.position.set(0.45, 0.17, -0.3);
    entityGroup.add(blueLedMesh);

    const blueLedLight = new THREE.PointLight(0x00F0FF, 0.8, 4.0);
    blueLedLight.position.set(0.45, 0.35, -0.3);
    entityGroup.add(blueLedLight);

    entityGroup.position.set(0, 0, 0);
    scene.add(entityGroup);

    // 9. Directional Source Beacons
    const beacons: Record<Sector, { group: THREE.Group; mesh: THREE.Mesh; light: THREE.PointLight }> = {
      LEFT: null as unknown as { group: THREE.Group; mesh: THREE.Mesh; light: THREE.PointLight },
      CENTER: null as unknown as { group: THREE.Group; mesh: THREE.Mesh; light: THREE.PointLight },
      RIGHT: null as unknown as { group: THREE.Group; mesh: THREE.Mesh; light: THREE.PointLight },
    };

    [
      { id: "LEFT" as Sector, angle: -45, color: 0x00F0FF },
      { id: "CENTER" as Sector, angle: 0, color: 0x10B981 },
      { id: "RIGHT" as Sector, angle: 45, color: 0x38BDF8 },
    ].forEach((s) => {
      const rad = (s.angle * Math.PI) / 180.0;
      const dist = 3.6;
      const x = dist * Math.sin(rad);
      const z = -dist * Math.cos(rad);

      const bGroup = new THREE.Group();
      bGroup.position.set(x, 0, z);

      const pMesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.12, 24, 24),
        new THREE.MeshStandardMaterial({
          color: s.color,
          emissive: s.color,
          emissiveIntensity: 1.4,
          roughness: 0.2,
        })
      );
      bGroup.add(pMesh);

      const pLight = new THREE.PointLight(s.color, 0.6, 2.5);
      bGroup.add(pLight);
      scene.add(bGroup);

      beacons[s.id] = { group: bGroup, mesh: pMesh, light: pLight };
    });

    // 10. Concentric "WiFi-Like" Sound Wave Engine
    const activeWavePackets: WavePacket[] = [];
    let targetTiltZ = 0;
    let targetTiltX = 0;
    let currentTiltZ = 0;
    let currentTiltX = 0;

    function triggerWifiWave(sector: Sector, angleDeg: number, intensity: number = 85) {
      const rad = (angleDeg * Math.PI) / 180.0;
      const startDist = 3.6;
      const originX = startDist * Math.sin(rad);
      const originZ = -startDist * Math.cos(rad);

      let waveColorHex = 0x38BDF8; // Azure (Right)
      if (angleDeg < -15) waveColorHex = 0x00F0FF; // Cyan (Left)
      else if (Math.abs(angleDeg) <= 15) waveColorHex = 0x10B981; // Emerald (Center)

      const dirVector = new THREE.Vector3(-originX, 0, -originZ).normalize();
      const facingAngle = Math.atan2(-dirVector.x, -dirVector.z);

      // 4 Cascading 3D Torus Arc Wavefronts (WiFi symbol geometry)
      const arcCount = 4;
      const arcMeshes: WaveArc[] = [];

      for (let i = 0; i < arcCount; i++) {
        const baseRadius = 0.55 + i * 0.45;
        const arcSpan = Math.PI * 0.44; // ~78 degrees curved arc
        const tubeRadius = 0.038;

        const torusGeo = new THREE.TorusGeometry(baseRadius, tubeRadius, 16, 54, arcSpan);
        const torusMat = new THREE.MeshBasicMaterial({
          color: waveColorHex,
          transparent: true,
          opacity: 0.95,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        });

        const arcMesh = new THREE.Mesh(torusGeo, torusMat);
        arcMesh.rotation.x = Math.PI / 2;
        arcMesh.rotation.z = facingAngle - arcSpan / 2;
        arcMesh.position.set(originX, 0.05, originZ);

        scene.add(arcMesh);
        arcMeshes.push({
          mesh: arcMesh,
          material: torusMat,
          baseRadius,
          delayOffset: i * 0.08,
          progress: -i * 0.14,
        });
      }

      // Shimmering Particle Spark Spray
      const pCount = 36;
      const pGeo = new THREE.BufferGeometry();
      const pPos = new Float32Array(pCount * 3);
      for (let i = 0; i < pCount; i++) {
        const pR = Math.random() * 0.6;
        const pTh = (Math.random() - 0.5) * 0.8;
        pPos[i * 3] = originX + pR * Math.cos(pTh);
        pPos[i * 3 + 1] = 0.05 + Math.random() * 0.3;
        pPos[i * 3 + 2] = originZ + pR * Math.sin(pTh);
      }
      pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
      const pMat = new THREE.PointsMaterial({
        color: waveColorHex,
        size: 0.05,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
      });
      const pPoints = new THREE.Points(pGeo, pMat);
      scene.add(pPoints);

      activeWavePackets.push({
        originX,
        originZ,
        dirVector,
        facingAngle,
        arcs: arcMeshes,
        particles: pPoints,
        alive: true,
      });

      // Beacon Flare
      const beacon = beacons[sector];
      if (beacon) {
        beacon.light.intensity = 3.5;
        beacon.mesh.scale.set(1.6, 1.6, 1.6);
        setTimeout(() => {
          beacon.light.intensity = 0.6;
          beacon.mesh.scale.set(1.0, 1.0, 1.0);
        }, 400);
      }

      // Flash Onboard Blue LED
      const peakBrightness = 1.0 + (intensity / 100.0) * 4.5;
      blueLedLight.intensity = peakBrightness;
      blueLedMesh.material.emissiveIntensity = 4.0;

      let step = 0;
      const fadeTimer = setInterval(() => {
        step++;
        blueLedLight.intensity = Math.max(0.8, blueLedLight.intensity - 0.2);
        blueLedMesh.material.emissiveIntensity = Math.max(0.8, blueLedMesh.material.emissiveIntensity - 0.18);
        if (step > 25) {
          clearInterval(fadeTimer);
          blueLedLight.intensity = 0.8;
          blueLedMesh.material.emissiveIntensity = 0.8;
        }
      }, 20);

      // Dynamic Bank/Tilt toward source
      if (angleDeg > 15) {
        targetTiltZ = -0.12;
        targetTiltX = 0.05;
      } else if (angleDeg < -15) {
        targetTiltZ = 0.12;
        targetTiltX = 0.05;
      } else {
        targetTiltZ = 0.0;
        targetTiltX = -0.08;
      }

      setTimeout(() => {
        targetTiltZ = 0.0;
        targetTiltX = 0.0;
      }, 1400);
    }

    triggerImpulseRef.current = triggerWifiWave;

    // 11. Animation Loop
    function animate() {
      animFrameId = requestAnimationFrame(animate);

      controls.update();

      const time = Date.now() * 0.002;

      // Entity floating levitation & banking interpolation
      entityGroup.position.y = Math.sin(time) * 0.05 + 0.02;
      currentTiltZ += (targetTiltZ - currentTiltZ) * 0.08;
      currentTiltX += (targetTiltX - currentTiltX) * 0.08;
      entityGroup.rotation.z = currentTiltZ;
      entityGroup.rotation.x = currentTiltX;

      const shadowScale = 1.0 - entityGroup.position.y * 0.8;
      shadowMesh.scale.set(shadowScale, shadowScale, shadowScale);

      // Waveform packet propagation
      for (let pIdx = activeWavePackets.length - 1; pIdx >= 0; pIdx--) {
        const packet = activeWavePackets[pIdx];
        let allDead = true;

        packet.arcs.forEach((arcObj) => {
          arcObj.progress += 0.018;
          if (arcObj.progress > 0 && arcObj.progress < 1.0) {
            allDead = false;
            const travelDist = arcObj.progress * 3.6;
            const currX = packet.originX + packet.dirVector.x * travelDist;
            const currZ = packet.originZ + packet.dirVector.z * travelDist;
            arcObj.mesh.position.set(currX, 0.05 + Math.sin(arcObj.progress * Math.PI) * 0.12, currZ);

            const scale = 1.0 + arcObj.progress * 1.4;
            arcObj.mesh.scale.set(scale, scale, scale);

            const fade = Math.sin(arcObj.progress * Math.PI);
            arcObj.material.opacity = Math.max(0, fade * 0.95);
          } else if (arcObj.progress >= 1.0) {
            arcObj.material.opacity = 0;
          } else {
            allDead = false;
          }
        });

        if (allDead) {
          packet.arcs.forEach((a) => scene.remove(a.mesh));
          scene.remove(packet.particles);
          activeWavePackets.splice(pIdx, 1);
        }
      }

      composer.render();
    }

    animate();

    // 12. Resize Handler
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth || window.innerWidth;
      const h = container.clientHeight || window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      composer.setSize(w, h);
      bloomPass.setSize(w, h);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animFrameId);
      window.removeEventListener("resize", handleResize);
      controls.dispose();
      renderer.dispose();
    };
  }, []);

  return <div ref={containerRef} className="canvas-container-3d" />;
});

AcousticCanvas3D.displayName = "AcousticCanvas3D";
