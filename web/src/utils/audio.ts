/**
 * Spatial Web Audio Synthesizer for Acoustic Impulses
 */

let audioCtx: AudioContext | null = null;

export function playSpatialImpulse(angleDeg: number, intensity: number = 0.85, muted: boolean = false) {
  if (muted) return;
  if (typeof window === "undefined") return;

  try {
    const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!audioCtx) {
      audioCtx = new AudioContextClass();
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }

    const now = audioCtx.currentTime;

    // Stereo Panning (-1.0 to +1.0)
    const pan = Math.max(-1.0, Math.min(1.0, angleDeg / 45.0));
    let panner: StereoPannerNode | null = null;
    if (audioCtx.createStereoPanner) {
      panner = audioCtx.createStereoPanner();
      panner.pan.setValueAtTime(pan, now);
    }

    // 1. High frequency transient snap (clap attack)
    const snapOsc = audioCtx.createOscillator();
    const snapGain = audioCtx.createGain();

    const baseFreq = angleDeg > 15 ? 880 : (angleDeg < -15 ? 680 : 780);
    snapOsc.type = "triangle";
    snapOsc.frequency.setValueAtTime(baseFreq * 2.2, now);
    snapOsc.frequency.exponentialRampToValueAtTime(baseFreq * 0.4, now + 0.08);

    const normIntensity = Math.min(1.0, Math.max(0.2, intensity / 100.0));
    const vol = 0.12 * normIntensity;
    snapGain.gain.setValueAtTime(vol, now);
    snapGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.09);

    // 2. Warm acoustic body resonance
    const bodyOsc = audioCtx.createOscillator();
    const bodyGain = audioCtx.createGain();
    bodyOsc.type = "sine";
    bodyOsc.frequency.setValueAtTime(baseFreq * 0.7, now);
    bodyOsc.frequency.exponentialRampToValueAtTime(baseFreq * 0.3, now + 0.14);

    bodyGain.gain.setValueAtTime(vol * 0.6, now);
    bodyGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.15);

    // Routing
    const destination = panner ? panner : audioCtx.destination;
    if (panner) panner.connect(audioCtx.destination);

    snapOsc.connect(snapGain);
    snapGain.connect(destination);

    bodyOsc.connect(bodyGain);
    bodyGain.connect(destination);

    snapOsc.start(now);
    bodyOsc.start(now);

    snapOsc.stop(now + 0.1);
    bodyOsc.stop(now + 0.16);
  } catch (err) {
    // AudioContext requires initial user interaction in some browsers
  }
}
