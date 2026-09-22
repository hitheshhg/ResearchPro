"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Sector, DoAEvent, TelemetryState } from "@/types/telemetry";
import { playSpatialImpulse } from "@/utils/audio";

interface UseTelemetryOptions {
  onAcousticTrigger?: (sector: Sector, angle: number, intensity: number) => void;
}

export function useHardwareTelemetry({ onAcousticTrigger }: UseTelemetryOptions = {}) {
  const [telemetry, setTelemetry] = useState<TelemetryState>({
    connected: false,
    port: "COM3",
    sector: "CENTER",
    angle: 0,
    confidence: 98.5,
    intensity: 0,
    peakLag: 0,
    peakNcc: 0.992,
    dspLatencyUs: 4.8,
    nnLatencyUs: 72.0,
    audioMuted: false,
  });

  const socketRef = useRef<WebSocket | null>(null);
  const onTriggerRef = useRef(onAcousticTrigger);
  onTriggerRef.current = onAcousticTrigger;

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    function connect() {
      const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const wsUrl = `ws://${host}:8000/ws/live-telemetry`;

      try {
        ws = new WebSocket(wsUrl);
        socketRef.current = ws;

        ws.onopen = () => {
          setTelemetry((prev) => ({ ...prev, connected: true }));
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "init" || data.type === "status") {
              setTelemetry((prev) => ({
                ...prev,
                connected: Boolean(data.hardware_connected),
                port: data.port || prev.port,
              }));
            } else if (data.type === "doa_event") {
              const ev = data as DoAEvent;
              const sector = ev.sector || "CENTER";
              const angle = Math.round(ev.angle_deg || 0);
              const intensity = ev.intensity || 85;

              setTelemetry((prev) => ({
                ...prev,
                sector,
                angle,
                confidence: ev.confidence || 98.0,
                intensity,
                peakLag: ev.peak_lag !== undefined ? ev.peak_lag : 0,
                peakNcc: ev.peak_ncc || 0.992,
                dspLatencyUs: ev.dsp_us ? parseFloat((ev.dsp_us / 1000).toFixed(1)) : 4.8,
                nnLatencyUs: ev.nn_us ? parseFloat((ev.nn_us / 1000).toFixed(1)) : 72.0,
              }));

              playSpatialImpulse(angle, intensity, telemetry.audioMuted);

              if (onTriggerRef.current) {
                onTriggerRef.current(sector, angle, intensity);
              }
            }
          } catch (e) {
            console.error("[WS PARSE ERROR]", e);
          }
        };

        ws.onclose = () => {
          setTelemetry((prev) => ({ ...prev, connected: false }));
          reconnectTimeout = setTimeout(connect, 2500);
        };

        ws.onerror = () => {
          try {
            ws?.close();
          } catch {}
        };
      } catch (err) {
        reconnectTimeout = setTimeout(connect, 3000);
      }
    }

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  }, [telemetry.audioMuted]);

  const sendHardwareTrigger = useCallback(
    (sector: Sector, intensity: number = 90) => {
      const keyMap: Record<Sector, string> = {
        LEFT: "l",
        CENTER: "c",
        RIGHT: "r",
      };
      const key = keyMap[sector];
      const angle = sector === "LEFT" ? -45 : sector === "RIGHT" ? 45 : 0;
      const lag = sector === "LEFT" ? 3 : sector === "RIGHT" ? -3 : 0;

      // Optimistic UI state update
      setTelemetry((prev) => ({
        ...prev,
        sector,
        angle,
        confidence: 99.2,
        intensity,
        peakLag: lag,
      }));

      playSpatialImpulse(angle, intensity, telemetry.audioMuted);

      if (onTriggerRef.current) {
        onTriggerRef.current(sector, angle, intensity);
      }

      // Send to backend via WebSocket or HTTP fallback
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ action: "trigger", key }));
      } else {
        const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
        fetch(`http://${host}:8000/api/hardware/trigger?direction=${sector.toLowerCase()}`, {
          method: "POST",
        }).catch(() => {});
      }
    },
    [telemetry.audioMuted]
  );

  const toggleMute = useCallback(() => {
    setTelemetry((prev) => ({ ...prev, audioMuted: !prev.audioMuted }));
  }, []);

  return {
    telemetry,
    sendHardwareTrigger,
    toggleMute,
  };
}
