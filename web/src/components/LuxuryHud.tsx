"use client";

import { FC } from "react";
import { Sector, TelemetryState } from "@/types/telemetry";

interface LuxuryHudProps {
  telemetry: TelemetryState;
  onTrigger: (sector: Sector, intensity?: number) => void;
  onToggleMute: () => void;
}

export const LuxuryHud: FC<LuxuryHudProps> = ({ telemetry, onTrigger, onToggleMute }) => {
  const getDirectionText = () => {
    switch (telemetry.sector) {
      case "RIGHT":
        return "Right (+45°)";
      case "LEFT":
        return "Left (-45°)";
      case "CENTER":
        return "Boresight Center (0°)";
      default:
        return "Awaiting Acoustic Impulse";
    }
  };

  const getHeroClass = () => {
    switch (telemetry.sector) {
      case "RIGHT":
        return "hero-direction state-right";
      case "LEFT":
        return "hero-direction state-left";
      case "CENTER":
        return "hero-direction state-center";
      default:
        return "hero-direction";
    }
  };

  return (
    <div className="luxury-hud-overlay">
      {/* Top Bar: Lab-Grade Hardware Telemetry */}
      <header className="hud-header">
        <div className="telemetry-capsule brand-capsule">
          <div className={`laser-indicator ${telemetry.connected ? "" : "searching"}`} />
          <div className="brand-meta">
            <span className="brand-title">
              SOUND DIRECTION <strong>ESTIMATION</strong>
            </span>
            <span className="sub-meta">
              ML & TINYML // {telemetry.connected ? `ESP32 (${telemetry.port})` : "CONNECTING ESP32..."}
            </span>
          </div>
        </div>

        <div className="hud-center-badge" title="Summer Research Internship Programme (SRIP 2025-26)">
          <span className="chip-dot" />
          <div className="center-badge-content">
            <span className="center-badge-title">
              HITHESH H G <span>• NNM23CS084</span>
            </span>
            <span className="center-badge-sub">
              Guide: Dr. Keerthana B Chigateri • Dept. of CSE, NMAMIT Nitte
            </span>
          </div>
        </div>

        <div className="telemetry-capsule stats-capsule">
          <div className="stat-unit">
            <span className="stat-k">DSP NCC</span>
            <span className="stat-v">{telemetry.dspLatencyUs} μs</span>
          </div>
          <div className="stat-sep">/</div>
          <div className="stat-unit">
            <span className="stat-k">TFLITE</span>
            <span className="stat-v">{telemetry.nnLatencyUs} μs</span>
          </div>
          <div className="stat-sep">/</div>
          <div className="stat-unit">
            <span className="stat-k">RATE</span>
            <span className="stat-v">16 kHz</span>
          </div>
        </div>
      </header>

      {/* Center Stage: Holographic Acoustic Radar Callout */}
      <div className="acoustic-hero-zone">
        <div className="sector-monolith">{telemetry.sector}</div>

        <div className="hero-direction-wrap">
          <h1 className={getHeroClass()}>{getDirectionText()}</h1>
        </div>

        {/* Precision Telemetry Pill */}
        <div className="precision-telemetry-pill">
          <div className="tele-item">
            <span className="tele-label">ANGLE</span>
            <span className="tele-val">
              {telemetry.angle > 0 ? `+${telemetry.angle.toFixed(1)}°` : `${telemetry.angle.toFixed(1)}°`}
            </span>
          </div>
          <span className="tele-bullet">▪</span>
          <div className="tele-item">
            <span className="tele-label">CONFIDENCE</span>
            <span className="tele-val highlight-cyan">{telemetry.confidence.toFixed(1)}%</span>
          </div>
          <span className="tele-bullet">▪</span>
          <div className="tele-item">
            <span className="tele-label">LAG τ</span>
            <span className="tele-val">{telemetry.peakLag}</span>
          </div>
          <span className="tele-bullet">▪</span>
          <div className="tele-item">
            <span className="tele-label">PEAK NCC</span>
            <span className="tele-val">{telemetry.peakNcc.toFixed(3)}</span>
          </div>
        </div>

        {/* Swiss Nagra Sound Intensity Station (Mirrors ESP32 Blue LED) */}
        <div className="intensity-station" title="Acoustic Pressure Level (Mirrors ESP32 Blue LED Brightness)">
          <div className="intensity-label-row">
            <span className="int-k">ONBOARD BLUE LED // PRESSURE</span>
            <span className="int-v">{telemetry.intensity}%</span>
          </div>
          <div className="intensity-track">
            <div className="intensity-fill" style={{ width: `${Math.min(100, telemetry.intensity)}%` }} />
            <div
              className="intensity-peak"
              style={{
                left: `${Math.min(99, telemetry.intensity)}%`,
                opacity: telemetry.intensity > 10 ? 1 : 0,
              }}
            />
          </div>
          <div className="intensity-ticks">
            <span>0</span>
            <span>25</span>
            <span>50</span>
            <span>75</span>
            <span>100%</span>
          </div>
        </div>
      </div>

      {/* Bottom Action Cockpit */}
      <footer className="hud-footer">
        <div className="action-cockpit">
          {/* Left Trigger Button */}
          <button
            className={`cockpit-btn ${telemetry.sector === "LEFT" ? "active" : ""}`}
            onClick={() => onTrigger("LEFT")}
            title="Simulate / Trigger Left Sound Wave (-45°)"
          >
            <svg className="wifi-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M4 8a12 12 0 0 0 0 8" strokeWidth="2" strokeLinecap="round" />
              <path d="M7 10a8 8 0 0 0 0 4" strokeWidth="2" strokeLinecap="round" />
              <path d="M10 12a4 4 0 0 0 0 0" strokeWidth="2.5" strokeLinecap="round" />
            </svg>
            <span>
              LEFT <small>-45°</small>
            </span>
          </button>

          {/* Center Trigger Button */}
          <button
            className={`cockpit-btn ${telemetry.sector === "CENTER" ? "active" : ""}`}
            onClick={() => onTrigger("CENTER")}
            title="Simulate / Trigger Center Boresight Sound (0°)"
          >
            <svg className="wifi-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M5 12a10 10 0 0 1 14 0" strokeWidth="2" strokeLinecap="round" />
              <path d="M8 14a6 6 0 0 1 8 0" strokeWidth="2" strokeLinecap="round" />
              <circle cx="12" cy="16" r="1.5" fill="currentColor" />
            </svg>
            <span>
              CENTER <small>0°</small>
            </span>
          </button>

          {/* Right Trigger Button */}
          <button
            className={`cockpit-btn ${telemetry.sector === "RIGHT" ? "active" : ""}`}
            onClick={() => onTrigger("RIGHT")}
            title="Simulate / Trigger Right Sound Wave (+45°)"
          >
            <span>
              RIGHT <small>+45°</small>
            </span>
            <svg className="wifi-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M20 8a12 12 0 0 1 0 8" strokeWidth="2" strokeLinecap="round" />
              <path d="M17 10a8 8 0 0 1 0 4" strokeWidth="2" strokeLinecap="round" />
              <path d="M14 12a4 4 0 0 1 0 0" strokeWidth="2.5" strokeLinecap="round" />
            </svg>
          </button>

          <div className="cockpit-divider" />

          {/* Clap Impulse Button */}
          <button
            className="cockpit-btn btn-impulse"
            onClick={() => onTrigger(telemetry.sector, 100)}
            title="Fire High-Energy Clap / Whistle Impulse"
          >
            <svg className="impulse-svg-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
            <span>CLAP IMPULSE</span>
          </button>

          <div className="cockpit-divider" />

          {/* Spatial Audio Mute Toggle */}
          <button
            className={`cockpit-btn btn-icon-only ${telemetry.audioMuted ? "active" : ""}`}
            onClick={onToggleMute}
            title={telemetry.audioMuted ? "Unmute Spatial Audio" : "Mute Spatial Audio"}
          >
            <svg className="sound-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" strokeWidth="2" strokeLinejoin="round" />
              {!telemetry.audioMuted ? (
                <>
                  <path d="M15.54 8.46a5 5 0 0 1 0 7.07" strokeWidth="2" strokeLinecap="round" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14" strokeWidth="2" strokeLinecap="round" />
                </>
              ) : (
                <line x1="23" y1="9" x2="17" y2="15" strokeWidth="2" strokeLinecap="round" />
              )}
            </svg>
          </button>
        </div>

        <div className="hud-footnote">
          <span>SRIP 2025–26 • HITHESH H G (NNM23CS084) • GUIDE: DR. KEERTHANA B CHIGATERI • NMAMIT NITTE</span>
        </div>
      </footer>
    </div>
  );
};
