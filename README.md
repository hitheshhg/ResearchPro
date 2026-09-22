# ResearchPro: Real-Time Acoustic Direction of Arrival (DoA) TinyML Platform

An end-to-end edge-computing system for real-time acoustic Direction of Arrival (DoA) estimation using dual microphones, sub-millisecond Normalized Cross-Correlation (NCC) DSP, on-chip quantized int8 TinyML neural inference on ESP32, and an ultra-minimalist 3D spatial visualizer built with Next.js and Three.js.

---

## System Architecture

```
                                      ACOUSTIC TRANSIENT
                                   (Clap / Whistle / Snap)
                                             │
                                             ▼
                          ┌─────────────────────────────────────┐
                          │    2x MAX9814 Microphones (10 cm)    │
                          │   Left: GPIO 34  |  Right: GPIO 35  │
                          └──────────────────┬──────────────────┘
                                             │ Analog Signals
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ESP32 DUAL-CORE SOC                                    │
│                                                                                        │
│  [Hardware ADC]       Direct ESP-IDF register sampling (adc1_get_raw @ 16 kHz)         │
│                                            │                                           │
│  [DSP Pipeline]       Zero-Mean Normalized Cross-Correlation (ZNCC) (Lags [-15, +15])  │
│                       Execution time: ~215 µs                                          │
│                                            │                                           │
│  [TinyML Engine]      Quantized int8 Multi-Layer Perceptron (31 -> 16 -> 3)            │
│                       Execution time: ~50 µs                                           │
│                                            │                                           │
│  [Hardware Feedback]  Onboard Blue LED (GPIO 2) PWM intensity modulation & onset flash │
│                                            │                                           │
│  [UART Stream]        115200 baud JSON telemetry output over USB                       │
└────────────────────────────────────────────┬───────────────────────────────────────────┘
                                             │ USB Serial (COM3)
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND (server.py)                               │
│  • Non-blocking hardware serial bridge                                                 │
│  • Low-latency WebSocket broadcaster (ws://localhost:8000/ws/live-telemetry)           │
└────────────────────────────────────────────┬───────────────────────────────────────────┘
                                             │ Live WebSocket Telemetry
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          NEXT.JS 16 & THREE.JS 3D WEB APP                              │
│  • Central 3D Minimalist Hardware Entity (basalt/obsidian chassis, dual CNC mic ports) │
│  • Onboard Cobalt Blue LED (GPIO 2) real-time intensity tracking                       │
│  • Concentric 3D "WiFi-Like" curved sound wave arcs radiating from incident direction   │
│  • Cinematic Bloom Post-Processing (UnrealBloomPass)                                   │
│  • Swiss Nagra audio intensity meter and telemetry cockpit                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Hardware Configuration & Wiring

| Component | Pin / Signal | ESP32 GPIO | Description |
| :--- | :--- | :--- | :--- |
| **Microphone Left** (MAX9814) | `OUT` | **GPIO 34** | ADC1 Channel 6 (Left acoustic channel) |
| **Microphone Right** (MAX9814) | `OUT` | **GPIO 35** | ADC1 Channel 7 (Right acoustic channel) |
| **Microphone VDD** | `VDD` | **3.3V** | Power supply (filtered 3.3V) |
| **Microphone GND** | `GND` | **GND** | System common ground |
| **Microphone GAIN** | `GAIN` | **GND / Unconnected** | 50 dB (GND) or 60 dB (unconnected) |
| **Onboard Blue LED** | `Anode` | **GPIO 2** | Dynamic PWM volume modulation |

> [!NOTE]
> Ensure a physical acoustic baseline distance of **$d = 10\text{ cm}$** between the centers of the two microphone capsules.

---

## Mathematical Foundations

### 1. Acoustic Time Difference of Arrival (TDoA)
Given acoustic baseline $d = 0.10\text{ m}$ and speed of sound $c = 343\text{ m/s}$, the continuous time delay $\tau$ for an incidence angle $\theta$ relative to broadside is:

$$\tau = \frac{d \cdot \sin(\theta)}{c}$$

At sampling rate $F_s = 16,000\text{ Hz}$ ($T_s = 62.5\text{ }\mu\text{s}$), the discrete sample lag $k$ is:

$$k = \text{round}\left(\frac{F_s \cdot d \cdot \sin(\theta)}{c}\right)$$

- **Left ($-45^\circ$)**: $\tau \approx -206\text{ }\mu\text{s} \implies k = +3.3\text{ samples}$ (Left leads Right)
- **Center ($0^\circ$)**: $\tau = 0\text{ }\mu\text{s} \implies k = 0\text{ samples}$ (Synchronous arrival)
- **Right ($+45^\circ$)**: $\tau \approx +206\text{ }\mu\text{s} \implies k = -3.3\text{ samples}$ (Right leads Left)

### 2. Zero-Mean Normalized Cross-Correlation (ZNCC)
For zero-mean signals $x[n]$ (Left) and $y[n]$ (Right) over a $N = 256$ sample window, the normalized spatial correlation at discrete lag $k \in [-15, +15]$ is:

$$R_{xy}[k] = \frac{\sum_{n} x[n] \cdot y[n+k]}{\sqrt{\sum_{n} x^2[n] \cdot \sum_{n} y^2[n]}}$$

This produces a **31-dimensional feature vector** completely invariant to signal amplitude, ambient volume, and DC bias drift.

---

## Edge AI Model Architecture

- **Topology**: Dense(31) $\rightarrow$ Dense(16, ReLU) $\rightarrow$ Dense(3, Softmax)
- **Quantization**: Fully quantized 8-bit integer (`int8`) TensorFlow Lite model
- **Flash Footprint**: 2.89 KB
- **SRAM Footprint**: 2.83 KB
- **Inference Latency**: ~50 microseconds on ESP32 @ 240 MHz

---

## Performance Benchmarks

| Metric | Target | Measured on ESP32 |
| :--- | :--- | :--- |
| **ADC Sampling Latency** | $< 20\text{ }\mu\text{s}$ | **$9.0\text{ }\mu\text{s}$** per channel (ESP-IDF direct ADC) |
| **31-Point ZNCC DSP Latency** | $< 500\text{ }\mu\text{s}$ | **$215\text{ }\mu\text{s}$** (Loop unrolled) |
| **TinyML Neural Inference** | $< 150\text{ }\mu\text{s}$ | **$50.0\text{ }\mu\text{s}$** |
| **Total Pipeline Latency** | $< 1.0\text{ ms}$ | **$0.28\text{ ms}$** (post-acquisition) |
| **Classification Accuracy** | $> 95\%$ | **$97.5\%$** on synthetic & verified claps |

---

## Quickstart Guide

### 1. Flash the ESP32 Firmware
```bash
# Compile firmware
arduino-cli compile --fqbn esp32:esp32:esp32 esp32_doa_firmware

# Flash to ESP32 on COM3
arduino-cli upload -p COM3 --fqbn esp32:esp32:esp32 esp32_doa_firmware
```

### 2. Start the Hardware Telemetry Bridge
```bash
# Activate Python virtual environment and run server
.\.venv\Scripts\python.exe server.py
```
*Server runs on `http://localhost:8000` and streams live telemetry over `ws://localhost:8000/ws/live-telemetry`.*

### 3. Start the Next.js 3D Web Application
```bash
cd web
npm install
npm run dev -- -p 3000
```
*Open **`http://localhost:3000`** in your browser.*

---

## License & Credits
Developed as part of the **Acoustic TinyML Research Internship**. All hardware drivers, DSP routines, and neural network weights are open source.
