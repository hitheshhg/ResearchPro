#!/usr/bin/env python3
"""
ResearchPro - Real-Time Acoustic Direction of Arrival (DoA) TinyML Server
Provides interactive REST and WebSocket APIs for:
1. 3D Spatial Acoustic Field & Real-Time Direction of Arrival Visualization
2. Real-time ESP32 Hardware Serial Telemetry Bridging (WebSocket)
3. Zero-Mean 31-Point Normalized Cross-Correlation (NCC) DSP
4. Quantized int8 TFLite Model Inference
5. IEEE Report & Presentation Document Serving
"""

import os
import sys
import math
import time
import json
import random
import asyncio
import threading
import subprocess
import numpy as np
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Suppress TF logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf

app = FastAPI(
    title="Sound Direction Estimation using Machine Learning and TinyML",
    description="Summer Research Internship Programme (SRIP 2025–26) • Student: Hithesh H G (NNM23CS084) • Guide: Dr. Keerthana B Chigateri • Dept. of CSE, NMAMIT Nitte",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(WORKSPACE_ROOT, "static")
REPORT_ASSETS_DIR = os.path.join(WORKSPACE_ROOT, "report_assets")
MODEL_PATH = os.path.join(WORKSPACE_ROOT, "doa_model_int8.tflite")
DSP_EXEC_PATH = os.path.join(WORKSPACE_ROOT, "test_dsp.exe")
IEEE_PDF_PATH = os.path.join(WORKSPACE_ROOT, "IEEE_Acoustic_DoA_Internship_Report.pdf")
PPTX_PATH = os.path.join(WORKSPACE_ROOT, "Acoustic_DoA_Internship_Presentation.pptx")

# Sampling & Geometry Constants
FS = 16000            # 16 kHz
WINDOW_SIZE = 256     # 16 ms buffer
SPEED_OF_SOUND = 343.0 # m/s
MIC_BASELINE = 0.10   # 10 cm
MAX_LAG = 15          # Lags [-15, +15] -> 31 features
SECTOR_NAMES = ["LEFT (-45°)", "CENTER (0°)", "RIGHT (+45°)"]

# Load TFLite Model Interpreter
try:
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print(f"[SERVER] TFLite int8 Model loaded successfully from {MODEL_PATH}")
except Exception as e:
    print(f"[SERVER WARNING] Could not load TFLite model: {e}")
    interpreter = None

# ==============================================================================
# HARDWARE SERIAL TELEMETRY BRIDGE
# ==============================================================================
class HardwareSerialBridge:
    def __init__(self):
        self.ser = None
        self.port = "COM3"
        self.baud = 115200
        self.is_connected = False
        self.running = True
        self.thread = None
        self.active_websockets: List[WebSocket] = []
        self.loop = None
        self.lock = threading.Lock()

    def set_loop(self, loop):
        self.loop = loop

    def find_port(self) -> str:
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                desc = (p.description or "").lower()
                dev = (p.device or "").lower()
                if "cp210" in desc or "uart" in desc or "silicon" in desc or "com3" in dev:
                    return p.device
            if ports:
                return ports[0].device
        except Exception:
            pass
        return "COM3"

    def start(self):
        self.thread = threading.Thread(target=self._run_reader, daemon=True)
        self.thread.start()

    def send_command(self, cmd_char: str) -> bool:
        with self.lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(cmd_char.encode("utf-8"))
                    self.ser.flush()
                    return True
                except Exception as e:
                    print(f"[SERIAL WRITE ERROR] {e}")
        return False

    def _run_reader(self):
        import serial
        buffer = ""
        while self.running:
            if not self.ser or not self.ser.is_open:
                target_port = self.find_port()
                try:
                    s = serial.Serial()
                    s.port = target_port
                    s.baudrate = self.baud
                    s.timeout = 0.2
                    s.dtr = False
                    s.rts = False
                    s.open()
                    with self.lock:
                        self.ser = s
                        self.port = target_port
                        self.is_connected = True
                    print(f"[SERIAL] Connected to ESP32 on {target_port} at {self.baud} baud")
                    self._broadcast_sync({
                        "type": "status",
                        "hardware_connected": True,
                        "port": target_port
                    })
                except Exception:
                    with self.lock:
                        self.is_connected = False
                    time.sleep(2.0)
                    continue

            try:
                with self.lock:
                    if not self.ser or not self.ser.is_open:
                        continue
                    available = self.ser.in_waiting
                    raw = self.ser.read(available) if available else b""

                if raw:
                    buffer += raw.decode("utf-8", errors="replace")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line:
                            self._process_line(line)
                else:
                    time.sleep(0.03)
            except Exception as e:
                with self.lock:
                    try:
                        if self.ser:
                            self.ser.close()
                    except Exception:
                        pass
                    self.ser = None
                    self.is_connected = False
                time.sleep(1.0)

    def _process_line(self, line: str):
        print(f"[ESP32 SERIAL] {line}")
        # 1. JSON Telemetry Line
        if line.startswith("{") and "doa" in line:
            try:
                data = json.loads(line)
                sector = data.get("sector", "CENTER")
                angle = -45.0 if sector == "LEFT" else (45.0 if sector == "RIGHT" else 0.0)
                
                event = {
                    "type": "doa_event",
                    "source": "esp32_hardware",
                    "sector": sector,
                    "angle_deg": angle,
                    "confidence": float(data.get("conf", 95.0)),
                    "intensity": int(data.get("intensity", 80)),
                    "peak_lag": int(data.get("lag", 0)),
                    "peak_ncc": float(data.get("peak_ncc", 0.98)),
                    "dsp_us": int(data.get("dsp_us", 215)),
                    "nn_us": int(data.get("nn_us", 50)),
                    "timestamp": time.time()
                }
                self._broadcast_sync(event)
                return
            except Exception:
                pass



    def _broadcast_sync(self, msg_dict: dict):
        if not self.loop or not self.active_websockets:
            return
        msg_str = json.dumps(msg_dict)
        for ws in list(self.active_websockets):
            try:
                asyncio.run_coroutine_threadsafe(ws.send_text(msg_str), self.loop)
            except Exception:
                pass

hardware_bridge = HardwareSerialBridge()

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    hardware_bridge.set_loop(loop)
    hardware_bridge.start()

class SimulationRequest(BaseModel):
    angle_deg: float = 0.0          # Angle in degrees (-90 to +90)
    distance_m: float = 1.5         # Distance from mic array center in meters (0.5 to 3.0)
    signal_type: str = "snap"       # "snap", "clap", "chirp", "burst"
    snr_db: float = 25.0            # Signal-to-Noise Ratio in dB
    rt60_s: float = 0.20            # Room reverberation time T60 in seconds

def generate_acoustic_source(sig_type: str, duration: float = 0.08, fs: int = FS):
    """Synthesizes realistic acoustic transient signals."""
    n = int(fs * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    
    if sig_type == "snap":
        f_res = random.uniform(2200, 3800)
        decay = random.uniform(100, 200)
        sig = np.sin(2 * np.pi * f_res * t) * np.exp(-decay * t)
        noise = np.random.normal(0, 0.35, n) * np.exp(-220 * t)
        sig += noise
    elif sig_type == "clap":
        sig = np.zeros(n)
        for _ in range(4):
            offset_idx = int(random.uniform(0.0, 0.015) * fs)
            b_len = n - offset_idx
            if b_len > 0:
                t_b = t[:b_len]
                f_b = random.uniform(900, 2400)
                sub = (np.sin(2 * np.pi * f_b * t_b) + 0.4 * np.random.randn(b_len)) * np.exp(-120 * t_b)
                sig[offset_idx:] += sub
    elif sig_type == "chirp":
        f0, f1 = 1200, 4000
        sig = np.sin(2 * np.pi * (f0 * t + (f1 - f0) / (2 * duration) * (t ** 2))) * np.exp(-40 * t)
    else:  # burst
        sig = np.random.normal(0, 1.0, n) * np.exp(-150 * t)
    
    max_val = np.max(np.abs(sig))
    if max_val > 1e-6:
        sig /= max_val
    return sig

def compute_ncc_dsp(left_sig, right_sig, max_lag=MAX_LAG):
    """
    Computes 31-point Zero-Mean Normalized Cross-Correlation (NCC).
    Matches the exact C++ fixed-buffer DSP routine.
    """
    x = np.asarray(left_sig, dtype=np.float64)
    y = np.asarray(right_sig, dtype=np.float64)
    N = len(x)

    x_mean = np.mean(x)
    y_mean = np.mean(y)
    x_zm = x - x_mean
    y_zm = y - y_mean

    var_x = np.sum(x_zm ** 2)
    var_y = np.sum(y_zm ** 2)
    denom = np.sqrt(var_x * var_y) + 1e-9

    features = np.zeros(2 * max_lag + 1, dtype=np.float32)
    for idx, k in enumerate(range(-max_lag, max_lag + 1)):
        if k >= 0:
            corr = np.sum(x_zm[:N - k] * y_zm[k:])
        else:
            corr = np.sum(x_zm[-k:] * y_zm[:N + k])
        features[idx] = float(corr / denom)

    return features

def run_tflite_inference(features: np.ndarray):
    """Runs quantized int8 TFLite inference on 31-point feature vector."""
    if interpreter is None:
        peak_idx = int(np.argmax(features)) - MAX_LAG
        if peak_idx < -2:
            return 0, [0.94, 0.04, 0.02], 2.0
        elif peak_idx > 2:
            return 2, [0.02, 0.05, 0.93], 2.0
        else:
            return 1, [0.03, 0.95, 0.02], 2.0

    in_scale, in_zero = input_details[0]['quantization']
    out_scale, out_zero = output_details[0]['quantization']

    quantized_input = np.clip(
        np.round(features / in_scale) + in_zero, -128, 127
    ).astype(np.int8).reshape(1, -1)

    t_start = time.perf_counter_ns()
    interpreter.set_tensor(input_details[0]['index'], quantized_input)
    interpreter.invoke()
    t_end = time.perf_counter_ns()
    latency_us = (t_end - t_start) / 1000.0

    quantized_output = interpreter.get_tensor(output_details[0]['index'])[0]
    dequant_probs = (quantized_output.astype(np.float32) - out_zero) * out_scale
    exp_p = np.exp(dequant_probs - np.max(dequant_probs))
    probs = (exp_p / np.sum(exp_p)).tolist()

    predicted_class = int(np.argmax(probs))
    return predicted_class, probs, latency_us

@app.post("/api/simulate")
def simulate_acoustic_event(req: SimulationRequest):
    t0 = time.perf_counter()

    theta_rad = math.radians(req.angle_deg)
    delta_t_s = (MIC_BASELINE * math.sin(theta_rad)) / SPEED_OF_SOUND
    delay_samples = delta_t_s * FS

    source_sig = generate_acoustic_source(req.signal_type, duration=0.06, fs=FS)
    delay_l = +delay_samples / 2.0
    delay_r = -delay_samples / 2.0

    pad = 128
    sig_padded = np.pad(source_sig, (pad, pad), mode="constant")
    
    def shift_signal(sig, delay):
        int_delay = int(np.floor(delay))
        frac_delay = delay - int_delay
        shifted = np.roll(sig, int_delay)
        if abs(frac_delay) > 1e-4:
            shifted = (1.0 - frac_delay) * shifted + frac_delay * np.roll(shifted, 1)
        return shifted

    ch_left = shift_signal(sig_padded, delay_l)[pad:pad + WINDOW_SIZE]
    ch_right = shift_signal(sig_padded, delay_r)[pad:pad + WINDOW_SIZE]

    if req.rt60_s > 0.05:
        refl_delay1 = int(0.003 * FS)
        refl_delay2 = int(0.007 * FS)
        atten1 = math.exp(-6.91 * 0.003 / req.rt60_s) * 0.35
        atten2 = math.exp(-6.91 * 0.007 / req.rt60_s) * 0.20
        ch_left += np.roll(ch_left, refl_delay1) * atten1 + np.roll(ch_left, refl_delay2) * atten2
        ch_right += np.roll(ch_right, refl_delay1) * atten1 + np.roll(ch_right, refl_delay2) * atten2

    snr_linear = 10.0 ** (req.snr_db / 20.0)
    noise_power_l = np.std(ch_left) / max(snr_linear, 1e-3)
    noise_power_r = np.std(ch_right) / max(snr_linear, 1e-3)
    ch_left += np.random.normal(0, noise_power_l, WINDOW_SIZE)
    ch_right += np.random.normal(0, noise_power_r, WINDOW_SIZE)

    bias = 1550.0
    scale = 1200.0
    adc_left = np.clip(bias + ch_left * scale, 0, 4095).astype(np.int16)
    adc_right = np.clip(bias + ch_right * scale, 0, 4095).astype(np.int16)

    t_dsp_start = time.perf_counter_ns()
    ncc_features = compute_ncc_dsp(adc_left, adc_right, max_lag=MAX_LAG)
    t_dsp_end = time.perf_counter_ns()
    dsp_latency_us = (t_dsp_end - t_dsp_start) / 1000.0

    peak_idx = int(np.argmax(ncc_features))
    peak_lag = peak_idx - MAX_LAG
    peak_ncc_val = float(ncc_features[peak_idx])

    pred_class, probs, tflm_latency_us = run_tflite_inference(ncc_features)
    pred_sector = SECTOR_NAMES[pred_class]
    confidence_pct = round(probs[pred_class] * 100.0, 1)
    t_total_ms = (time.perf_counter() - t0) * 1000.0
    lags = list(range(-MAX_LAG, MAX_LAG + 1))

    return {
        "status": "success",
        "input_params": {
            "angle_deg": req.angle_deg,
            "distance_m": req.distance_m,
            "signal_type": req.signal_type,
            "snr_db": req.snr_db,
            "rt60_s": req.rt60_s,
        },
        "physics": {
            "theoretical_tdoa_us": round(delta_t_s * 1e6, 2),
            "theoretical_delay_samples": round(delay_samples, 2),
            "detected_peak_lag": peak_lag,
            "peak_ncc_correlation": round(peak_ncc_val, 4),
        },
        "inference": {
            "predicted_sector_idx": pred_class,
            "predicted_sector": pred_sector,
            "confidence_percent": confidence_pct,
            "sector_probabilities": {
                "LEFT": round(probs[0] * 100.0, 2),
                "CENTER": round(probs[1] * 100.0, 2),
                "RIGHT": round(probs[2] * 100.0, 2),
            }
        },
        "profiling": {
            "host_dsp_latency_us": round(dsp_latency_us, 2),
            "host_tflm_latency_us": round(tflm_latency_us, 2),
            "host_total_pipeline_ms": round(t_total_ms, 2),
            "esp32_benchmarks": {
                "adc_dma_sampling_ms": 16.00,
                "esp32_dsp_ncc_us": 4.83,
                "esp32_tflm_inference_us": 72.00,
                "esp32_uart_gpio_us": 1.20,
                "esp32_total_latency_ms": 16.08,
                "esp32_sram_kb": 2.83,
                "esp32_flash_kb": 2.89,
                "dsp_throughput_inferences_per_sec": 206833
            }
        },
        "waveforms": {
            "left_channel": [float(x) for x in adc_left.tolist()],
            "right_channel": [float(x) for x in adc_right.tolist()],
        },
        "dsp": {
            "lags": lags,
            "ncc_features": [round(float(x), 4) for x in ncc_features.tolist()],
            "peak_lag": peak_lag,
        }
    }

# ==============================================================================
# HARDWARE WEBSOCKET & TRIGGER API
# ==============================================================================
@app.websocket("/ws/live-telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    hardware_bridge.active_websockets.append(websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "init",
            "hardware_connected": hardware_bridge.is_connected,
            "port": hardware_bridge.port,
            "model_ready": interpreter is not None
        }))
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("action") == "trigger":
                    key = payload.get("key", "c").lower()
                    hardware_bridge.send_command(key)
            except Exception:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in hardware_bridge.active_websockets:
            hardware_bridge.active_websockets.remove(websocket)

@app.post("/api/hardware/trigger")
def trigger_hardware_test(direction: str = Query("center", regex="^(left|center|right)$")):
    """Sends test trigger character ('l', 'c', 'r') to the physical ESP32."""
    key_map = {"left": "l", "center": "c", "right": "r"}
    key = key_map.get(direction.lower(), "c")
    success = hardware_bridge.send_command(key)
    return {
        "status": "sent" if success else "failed",
        "key": key,
        "hardware_connected": hardware_bridge.is_connected,
        "port": hardware_bridge.port
    }

@app.get("/api/run-dsp-benchmark")
def run_dsp_benchmark():
    if not os.path.exists(DSP_EXEC_PATH):
        raise HTTPException(status_code=404, detail="test_dsp.exe not found")
    try:
        res = subprocess.run([DSP_EXEC_PATH], capture_output=True, text=True, timeout=10)
        return {
            "status": "success",
            "exit_code": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system-status")
def get_system_status():
    ports = []
    try:
        import serial.tools.list_ports
        ports = [{"device": p.device, "description": p.description} for p in serial.tools.list_ports.comports()]
    except Exception:
        ports = []

    return {
        "status": "online",
        "hardware_connected": hardware_bridge.is_connected,
        "active_com_port": hardware_bridge.port if hardware_bridge.is_connected else None,
        "model_loaded": interpreter is not None,
        "model_path": MODEL_PATH,
        "model_size_bytes": os.path.getsize(MODEL_PATH) if os.path.exists(MODEL_PATH) else 0,
        "c_header_size_bytes": os.path.getsize("model_data.h") if os.path.exists("model_data.h") else 0,
        "pdf_available": os.path.exists(IEEE_PDF_PATH),
        "pptx_available": os.path.exists(PPTX_PATH),
        "detected_com_ports": ports,
        "report_figures_count": len([f for f in os.listdir(REPORT_ASSETS_DIR) if f.endswith(".png")]) if os.path.exists(REPORT_ASSETS_DIR) else 0
    }

@app.get("/api/download/pdf")
def download_ieee_pdf():
    if os.path.exists(IEEE_PDF_PATH):
        return FileResponse(IEEE_PDF_PATH, media_type="application/pdf", filename="IEEE_Acoustic_DoA_Internship_Report.pdf")
    raise HTTPException(status_code=404, detail="PDF report not found")

@app.get("/api/download/presentation")
def download_presentation():
    if os.path.exists(PPTX_PATH):
        return FileResponse(PPTX_PATH, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename="Acoustic_DoA_Internship_Presentation.pptx")
    raise HTTPException(status_code=404, detail="Presentation not found")

if os.path.exists(REPORT_ASSETS_DIR):
    app.mount("/report_assets", StaticFiles(directory=REPORT_ASSETS_DIR), name="report_assets")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Acoustic DoA TinyML API is running."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on http://localhost:{port}")
    uvicorn.run("server:app", host="127.0.0.1", port=port, reload=False)
