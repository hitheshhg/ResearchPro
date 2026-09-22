# Sound Direction Estimation using Machine Learning and TinyML
### Minimalist 3D Spatial Acoustic Radar Interface

> **Author:** Hithesh H G (USN: `NNM23CS084`) — Dept. of Computer Science & Engineering (CSE)  
> **Guide:** Dr. Keerthana B Chigateri  
> **Institution:** NMAM Institute of Technology, Nitte (Deemed to be University)  
> **Programme:** Summer Research Internship Programme (SRIP 2025–26)  

A high-performance, minimalist 3D interface for real-time acoustic Direction of Arrival (DoA) estimation, powered by Next.js 16, Three.js, and UnrealBloomPass.

## Architecture

- **Framework**: Next.js 16 (App Router / TypeScript)
- **3D Graphics**: Three.js WebGL with `EffectComposer`, `RenderPass`, and `UnrealBloomPass`
- **Design System**: Luxury Swiss Audio / Apple Vision Pro dark glass aesthetics
- **Real-Time Telemetry**: WebSocket client connecting to `ws://localhost:8000/ws/live-telemetry`
- **Spatial Audio**: Web Audio API stereo-panned acoustic transient synthesizer

## Key Features

1. **Central 3D Hardware Entity**:
   - Sculpted matte basalt/obsidian chassis with dual CNC aluminum microphone capsules.
   - Onboard Cobalt Blue LED (GPIO 2) with real-time acoustic intensity modulation.
   - Soft ground contact shadow and organic floating levitation.
   - Dynamic real-time banking/tilt toward incoming sound incidence.

2. **Concentric "WiFi-Like" Sound Wave Arcs**:
   - 3D curved Torus arc wavefronts rippling from the sound origin toward the entity:
     - Right (+45°): Electric azure arcs sweeping from the right.
     - Left (-45°): Neon cyan arcs sweeping from the left.
     - Center (0°): Radiant emerald arcs sweeping from the front.
   - Accompanied by expanding particle spark trails and contact flash.

3. **Luxury Cockpit & Swiss Nagra Intensity Station**:
   - Micro-telemetry: Incident angle, confidence percentage, acoustic lag ($\tau$), peak NCC correlation.
   - Real-time audio pressure meter mirroring physical ESP32 GPIO 2 Blue LED.
   - Interactive action dock with custom SVG curved WiFi waves.

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev -- -p 3000

# Build production bundle
npm run build
```

Open [http://localhost:3000](http://localhost:3000) in your browser.
