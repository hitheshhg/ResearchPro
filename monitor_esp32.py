#!/usr/bin/env python3
"""
Real-Time Serial Telemetry Monitor for ESP32 Acoustic DoA Estimation
Connects to ESP32 on COM port at 115200 baud and displays live direction & intensity.
"""

import sys
import time
import serial
import serial.tools.list_ports

def find_esp32_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return "COM3"
    # Look for CP210x or ESP32
    for p in ports:
        desc = (p.description or "").lower()
        dev = (p.device or "").lower()
        if "cp210" in desc or "uart" in desc or "ch340" in desc or "silicon" in desc or "com" in dev:
            return p.device
    return ports[0].device

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else find_esp32_port()
    baud = 115200

    print("=" * 68)
    print("      ESP32 REAL-TIME ACOUSTIC DoA & SOUND INTENSITY MONITOR        ")
    print("=" * 68)
    print(f"Connecting to ESP32 on port: {port} at {baud} baud...")

    try:
        ser = serial.Serial()
        ser.port = port
        ser.baudrate = baud
        ser.timeout = 1.0
        ser.dtr = False
        ser.rts = False
        ser.open()
        time.sleep(1.0)
        ser.reset_input_buffer()

        print("\n[STATUS] Connected successfully to ESP32!")
        print("[VISUAL] Blue LED on ESP32 (GPIO 2) displays real-time sound intensity.")
        print("[ACTION] Snap fingers, clap, click, or speak from Left, Center, or Right.")
        print("Press Ctrl+C to stop.\n")
        print("-" * 68)

        while True:
            line = ser.readline()
            if line:
                decoded = line.decode("utf-8", errors="replace").strip()
                if not decoded:
                    continue
                
                # Highlight directions
                if "LEFT" in decoded and ">>>" in decoded:
                    print(f"\033[96m\033[1m{decoded}\033[0m")       # Bright Cyan / Bold
                elif "CENTER" in decoded and ">>>" in decoded:
                    print(f"\033[92m\033[1m{decoded}\033[0m")     # Bright Green / Bold
                elif "RIGHT" in decoded and ">>>" in decoded:
                    print(f"\033[95m\033[1m{decoded}\033[0m")      # Bright Magenta / Bold
                elif "Sound Intensity:" in decoded:
                    print(f"\033[94m{decoded}\033[0m")             # Blue
                elif "Confidence:" in decoded:
                    print(f"\033[93m{decoded}\033[0m")             # Yellow
                elif "Acoustic Physics:" in decoded:
                    print(f"\033[97m{decoded}\033[0m")             # White
                elif decoded.startswith("{"):
                    pass # Hide raw JSON line for clean terminal UX
                else:
                    print(decoded)

    except serial.SerialException as e:
        print(f"\n[ERROR] Could not open serial port {port}: {e}")
        print("Check if another application (such as Arduino IDE Serial Monitor) has the port open.")
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
