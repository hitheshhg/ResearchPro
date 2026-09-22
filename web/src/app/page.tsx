"use client";

import { useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { LuxuryHud } from "@/components/LuxuryHud";
import { useHardwareTelemetry } from "@/hooks/useHardwareTelemetry";
import { Sector } from "@/types/telemetry";
import type { AcousticCanvas3DRef } from "@/components/AcousticCanvas3D";

// Dynamically import Three.js Canvas to avoid SSR window issues
const AcousticCanvas3D = dynamic(
  () => import("@/components/AcousticCanvas3D").then((mod) => mod.AcousticCanvas3D),
  { ssr: false }
);

export default function Home() {
  const canvasRef = useRef<AcousticCanvas3DRef>(null);

  // Handle incoming live hardware DoA triggers from WebSocket
  const handleAcousticTrigger = useCallback((sector: Sector, angle: number, intensity: number) => {
    if (canvasRef.current) {
      canvasRef.current.triggerAcousticImpulse(sector, angle, intensity);
    }
  }, []);

  const { telemetry, sendHardwareTrigger, toggleMute } = useHardwareTelemetry({
    onAcousticTrigger: handleAcousticTrigger,
  });

  const handleUserTrigger = useCallback(
    (sector: Sector, intensity?: number) => {
      sendHardwareTrigger(sector, intensity);
    },
    [sendHardwareTrigger]
  );

  return (
    <main className="relative w-screen h-screen overflow-hidden bg-[#040507]">
      {/* Ambient Vignette & Radial Light Stage */}
      <div className="cinematic-backdrop">
        <div className="vignette-layer" />
        <div className="radial-bloom-glow" />
        <div className="subtle-grid-floor" />
      </div>

      {/* 3D Three.js WebGL Stage */}
      <AcousticCanvas3D ref={canvasRef} />

      {/* Floating Luxury HUD */}
      <LuxuryHud
        telemetry={telemetry}
        onTrigger={handleUserTrigger}
        onToggleMute={toggleMute}
      />
    </main>
  );
}
