#!/usr/bin/env python3
"""
Real-Time Serial Telemetry Monitor for ESP32 Acoustic DoA Estimation
Connects to /dev/cu.usbserial-0001 at 115200 baud and displays live inference output.
"""

import sys
import time
import serial
import serial.tools.list_ports

def find_esp32_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "usbserial" in p.device or "wchusbserial" in p.device or "SLAB_USBtoUART" in p.device:
            return p.device
    return "/dev/cu.usbserial-0001"

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else find_esp32_port()
    baud = 115200

    print("=" * 65)
    print("   ESP32 Real-Time Acoustic DoA Telemetry Monitor   ")
    print("=" * 65)
    print(f"Connecting to ESP32 on port: {port} at {baud} baud...")

    try:
        ser = serial.Serial(port, baud, timeout=1.0)
        time.sleep(0.5)
        # Flush buffers
        ser.reset_input_buffer()
        print("Connected successfully! Listening for acoustic transient events (snaps, claps)...")
        print("Press Ctrl+C to stop.\n")
        print("-" * 65)

        while True:
            line = ser.readline()
            if line:
                decoded = line.decode("utf-8", errors="replace").strip()
                if decoded:
                    if ">>> LEFT" in decoded:
                        print(f"\033[91m{decoded}\033[0m")  # Red
                    elif ">>> CENTER" in decoded:
                        print(f"\033[92m{decoded}\033[0m")  # Green
                    elif ">>> RIGHT" in decoded:
                        print(f"\033[94m{decoded}\033[0m")  # Blue
                    elif "[CONFIDENCE]" in decoded or "[PROFILING]" in decoded:
                        print(f"\033[93m{decoded}\033[0m")  # Yellow
                    else:
                        print(decoded)
    except serial.SerialException as e:
        print(f"\n[ERROR] Could not open serial port {port}: {e}")
        print("Make sure no other program (Arduino IDE Serial Monitor, etc.) has the port open.")
    except KeyboardInterrupt:
        print("\n\nMonitor terminated by user.")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
