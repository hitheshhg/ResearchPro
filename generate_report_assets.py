#!/usr/bin/env python3
"""
Generates publication-quality figures and flowcharts for IEEE Project Report and PPT presentation.
All figures are saved in 300 DPI high-resolution PNG format.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIR = "report_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.titlesize": 14,
})

# ==============================================================================
# FIG 1: SYSTEM HARDWARE & SOFTWARE ARCHITECTURE
# ==============================================================================
def generate_system_architecture():
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)

    # Styles
    box_blue = dict(boxstyle="round,pad=0.5", facecolor="#E3F2FD", edgecolor="#1565C0", linewidth=1.5)
    box_green = dict(boxstyle="round,pad=0.5", facecolor="#E8F5E9", edgecolor="#2E7D32", linewidth=1.5)
    box_orange = dict(boxstyle="round,pad=0.5", facecolor="#FFF3E0", edgecolor="#E65100", linewidth=1.5)
    box_purple = dict(boxstyle="round,pad=0.5", facecolor="#F3E5F5", edgecolor="#6A1B9A", linewidth=1.5)
    box_gray = dict(boxstyle="round,pad=0.5", facecolor="#ECEFF1", edgecolor="#37474F", linewidth=1.5)

    # Title
    ax.text(50, 56, "End-to-End Edge AI Acoustic DoA Estimation System Architecture", 
            ha="center", va="center", fontsize=13, weight="bold", color="#1A237E")

    # Layer 1: Sensors
    ax.text(12, 45, "MAX9814 Mic L\n(Left Channel)\nAnalog Out", ha="center", va="center", bbox=box_blue, fontsize=9)
    ax.text(12, 31, "MAX9814 Mic R\n(Right Channel)\nAnalog Out", ha="center", va="center", bbox=box_blue, fontsize=9)
    ax.text(12, 19, "Acoustic Baseline\nd = 10 cm (0.10 m)", ha="center", va="center", bbox=box_gray, fontsize=8, style="italic")

    # Double-headed arrow between mics
    ax.annotate("", xy=(12, 36), xytext=(12, 40), arrowprops=dict(arrowstyle="<->", color="#1565C0", lw=1.5))

    # Layer 2: ESP32 ADC & Ring Buffer
    ax.text(35, 45, "ESP32 SAR ADC1_CH6\n(GPIO34, 12-bit)\n16 kHz Sampling", ha="center", va="center", bbox=box_green, fontsize=9)
    ax.text(35, 31, "ESP32 SAR ADC1_CH7\n(GPIO35, 12-bit)\n16 kHz Sampling", ha="center", va="center", bbox=box_green, fontsize=9)
    ax.text(35, 17, "Pre-Trigger Ring Buffer\n(32 samples / 2 ms lead)\n& Dynamic Bias Tracker", ha="center", va="center", bbox=box_green, fontsize=8.5)

    # Layer 3: Energy Detector & DSP Feature Engine
    ax.text(58, 45, "Transient Energy Trigger\nE > 380 ADC units\n(Snaps, Claps, Speech)", ha="center", va="center", bbox=box_orange, fontsize=9)
    ax.text(58, 31, "31-Point Normalized\nCross-Correlation (NCC)\nLags [-15, +15] | 256 smp", ha="center", va="center", bbox=box_orange, fontsize=9)
    ax.text(58, 17, "Feature Scaling & Int8\nQuantization Quantizer\nq = round(x/s) + z", ha="center", va="center", bbox=box_orange, fontsize=8.5)

    # Layer 4: TinyML Engine
    ax.text(82, 45, "TFLM Engine (Xtensa)\nQuantized Int8 MLP\n31 -> 16(ReLU) -> 3", ha="center", va="center", bbox=box_purple, fontsize=9)
    ax.text(82, 31, "Softmax Dequantization\n& Sector Argmax\nConfidence %", ha="center", va="center", bbox=box_purple, fontsize=9)
    ax.text(82, 17, "Refractory Debounce\n300 ms Echo Lockout\nUART 115200 Baud", ha="center", va="center", bbox=box_purple, fontsize=8.5)

    # Connecting arrows
    arr = dict(arrowstyle="->", color="#37474F", lw=1.5)
    ax.annotate("", xy=(23, 45), xytext=(20, 45), arrowprops=arr)
    ax.annotate("", xy=(23, 31), xytext=(20, 31), arrowprops=arr)
    ax.annotate("", xy=(46, 45), xytext=(44, 45), arrowprops=arr)
    ax.annotate("", xy=(46, 31), xytext=(44, 31), arrowprops=arr)
    ax.annotate("", xy=(70, 45), xytext=(67, 45), arrowprops=arr)
    ax.annotate("", xy=(70, 31), xytext=(67, 31), arrowprops=arr)
    ax.annotate("", xy=(58, 37), xytext=(58, 40), arrowprops=arr)
    ax.annotate("", xy=(82, 37), xytext=(82, 40), arrowprops=arr)
    ax.annotate("", xy=(82, 23), xytext=(82, 26), arrowprops=arr)

    # Output banner
    ax.text(50, 6, "Output: LEFT (-45°) | CENTER (0°) | RIGHT (+45°)  [Total Pipeline Latency: 0.56 ms | SRAM: 4 KB | Flash: 2.44 KB]",
            ha="center", va="center", fontsize=9.5, weight="bold", color="#1B5E20",
            bbox=dict(boxstyle="square,pad=0.4", facecolor="#C8E6C9", edgecolor="#2E7D32"))

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig1_system_architecture.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

# ==============================================================================
# FIG 2: TDOA ACOUSTIC WAVEFRONT GEOMETRY
# ==============================================================================
def generate_tdoa_geometry():
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    
    # Coordinate system
    ax.axhline(0, color="black", lw=1.2, ls="--", alpha=0.6)
    ax.axvline(0, color="black", lw=1.2, ls="--", alpha=0.6)

    # Microphones
    d = 0.10 # 10 cm
    mic1 = (-d/2, 0)
    mic2 = (+d/2, 0)

    ax.scatter([mic1[0], mic2[0]], [mic1[1], mic2[1]], color=["#D32F2F", "#1976D2"], s=180, zorder=5)
    ax.text(mic1[0], -0.015, "Mic 1 (Left)\n(-d/2, 0)", ha="center", va="top", fontsize=9, weight="bold", color="#D32F2F")
    ax.text(mic2[0], -0.015, "Mic 2 (Right)\n(+d/2, 0)", ha="center", va="top", fontsize=9, weight="bold", color="#1976D2")

    # Baseline dimension line
    ax.annotate("", xy=(mic2[0], -0.035), xytext=(mic1[0], -0.035),
                arrowprops=dict(arrowstyle="<->", color="#333333", lw=1.5))
    ax.text(0, -0.042, "Baseline d = 10 cm", ha="center", va="top", fontsize=9.5, weight="bold")

    # Sound source arriving at theta = 45 degrees
    theta_deg = 45
    theta_rad = np.radians(theta_deg)
    r = 0.15

    # Rays from mics to source
    src_dir = np.array([np.sin(theta_rad), np.cos(theta_rad)])
    
    # Wavefront lines (perpendicular to direction)
    for dist in np.linspace(0.04, 0.14, 4):
        p_c = dist * src_dir
        normal = np.array([-np.cos(theta_rad), np.sin(theta_rad)]) * 0.06
        p1 = p_c - normal
        p2 = p_c + normal
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#7B1FA2", lw=1.5, ls="-", alpha=0.7)
    
    ax.text(0.12, 0.13, "Planar Wavefront\n(Far-field R > 23 cm)", color="#7B1FA2", fontsize=9, weight="bold")

    # Propagation ray from center
    ax.annotate("", xy=(src_dir[0]*0.16, src_dir[1]*0.16), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color="#E65100", lw=2))
    ax.text(src_dir[0]*0.17, src_dir[1]*0.17, "Acoustic Propagation Ray\nθ = +45° (RIGHT Sector)", 
            color="#E65100", fontsize=9, weight="bold")

    # Path difference triangle
    # Drop perpendicular from Mic 1 to ray of Mic 2
    proj_pt = np.array([mic2[0] - d * np.sin(theta_rad) * np.sin(theta_rad), 
                        mic2[1] + d * np.sin(theta_rad) * np.cos(theta_rad)])
    
    ax.plot([mic1[0], proj_pt[0]], [mic1[1], proj_pt[1]], color="#C2185B", lw=1.8, ls=":")
    ax.plot([mic2[0], proj_pt[0]], [mic2[1], proj_pt[1]], color="#C2185B", lw=2.5)
    ax.text((mic2[0] + proj_pt[0])/2 + 0.008, (mic2[1] + proj_pt[1])/2, 
            "Δr = d·sin(θ)\n= 7.07 cm\nτ = +206.15 μs\n(+3.30 samples)", 
            color="#C2185B", fontsize=8.5, weight="bold")

    # Angle arc
    arc_angles = np.linspace(np.pi/2 - theta_rad, np.pi/2, 30)
    arc_r = 0.04
    ax.plot(arc_r * np.cos(arc_angles), arc_r * np.sin(arc_angles), color="#E65100", lw=1.5)
    ax.text(0.015, 0.045, "θ", color="#E65100", fontsize=11, weight="bold")

    # Broadside label
    ax.text(0, 0.155, "Broadside (0°)\n[CENTER Sector]", ha="center", va="bottom", fontsize=9, color="#1B5E20", weight="bold")

    ax.set_xlim(-0.10, 0.18)
    ax.set_ylim(-0.06, 0.18)
    ax.set_aspect("equal")
    ax.set_title("Geometric & Theoretical Time Difference of Arrival (TDOA) Model", pad=15, weight="bold", color="#1A237E")
    ax.set_xlabel("X-Axis (Array Baseline) [m]")
    ax.set_ylabel("Y-Axis (Broadside Direction) [m]")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig2_tdoa_geometry.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

# ==============================================================================
# FIG 3: FIRMWARE LOGIC FLOWCHART
# ==============================================================================
def generate_firmware_flowchart():
    fig, ax = plt.subplots(figsize=(7, 10), dpi=300)
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 140)

    def draw_box(y, text, color, shape="rect", h=10, w=60):
        if shape == "rect":
            box = patches.FancyBboxPatch((50 - w/2, y - h/2), w, h, boxstyle="round,pad=1.0",
                                         facecolor=color[0], edgecolor=color[1], lw=1.5)
            ax.add_patch(box)
            ax.text(50, y, text, ha="center", va="center", fontsize=8.5, weight="bold", color="#212121")
        elif shape == "diamond":
            diamond = patches.Polygon([[50, y + h/2], [50 + w/2, y], [50, y - h/2], [50 - w/2, y]],
                                      facecolor=color[0], edgecolor=color[1], lw=1.5)
            ax.add_patch(diamond)
            ax.text(50, y, text, ha="center", va="center", fontsize=8, weight="bold", color="#212121")
        return y

    c_blue   = ("#E3F2FD", "#1565C0")
    c_green  = ("#E8F5E9", "#2E7D32")
    c_yellow = ("#FFF9C4", "#F57F17")
    c_orange = ("#FFE0B2", "#E65100")
    c_purple = ("#F3E5F5", "#7B1FA2")
    c_red    = ("#FFEBEE", "#C62828")

    ax.text(50, 136, "ESP32 Real-Time Firmware Execution Flowchart", ha="center", va="center",
            fontsize=12, weight="bold", color="#1A237E")

    draw_box(128, "Power-On Boot & System Init\nConfigure ADC1 GPIO34/35 (12-bit, 11dB)", c_blue, h=8, w=68)
    draw_box(116, "Calibrate MAX9814 Quiescent Biases\n(2048 readings -> ~1.25V / 1550 code)", c_blue, h=8, w=68)
    draw_box(104, "Load Quantized FlatBuffer Model\nAllocate Static 4 KB Tensor Arena", c_purple, h=8, w=68)
    
    draw_box(91, "High-Precision 16 kHz Polling Loop\nesp_timer_get_time() [62.5 μs interval]", c_green, h=8, w=68)
    draw_box(79, "Acquire Left/Right ADC & Update\nCircular Pre-Trigger Buffer (32 samples)", c_green, h=8, w=68)
    
    draw_box(65, "Instantaneous Energy\nE > 380 ADC units?", c_yellow, shape="diamond", h=11, w=44)

    draw_box(49, "Populate 256-sample Frame Buffer\n(32 pre-trigger + 224 synchronous samples)", c_orange, h=8, w=68)
    draw_box(37, "Zero-Mean & 31-Point NCC Feature DSP\nLags [-15, +15] (Runtime: ~0.48 ms)", c_orange, h=8, w=68)
    draw_box(25, "Int8 Feature Quantization & TFLM Invoke\nArgmax Sector Output & Confidence %", c_purple, h=8, w=68)
    draw_box(13, "Serial Telemetry Output (115200 Baud)\nRefractory Debounce Lockout (300 ms)", c_red, h=8, w=68)

    # Arrows
    arr = dict(arrowstyle="->", color="#37474F", lw=1.5)
    for y1, y2 in [(124, 120), (112, 108), (100, 95), (87, 83), (75, 71), (59.5, 53), (45, 41), (33, 29), (21, 17)]:
        ax.annotate("", xy=(50, y2), xytext=(50, y1), arrowprops=arr)

    # Decision No Branch
    ax.annotate("", xy=(80, 91), xytext=(72, 65), arrowprops=dict(arrowstyle="->", color="#C62828", lw=1.3, connectionstyle="angle,angleA=0,angleB=90,rad=5"))
    ax.text(75, 67, "No", fontsize=8.5, weight="bold", color="#C62828")

    # Decision Yes Branch
    ax.text(52, 56, "Yes", fontsize=8.5, weight="bold", color="#2E7D32")

    # Loop back from bottom to polling loop
    ax.plot([50 - 34, 10, 10, 50 - 34], [13, 13, 91, 91], color="#1565C0", lw=1.3)
    ax.annotate("", xy=(50 - 34, 91), xytext=(15, 91),
                arrowprops=dict(arrowstyle="->", color="#1565C0", lw=1.3))

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig3_dsp_flowchart.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

# ==============================================================================
# FIG 4: CONFUSION MATRIX & CLASSIFICATION METRICS
# ==============================================================================
def generate_confusion_matrix_and_metrics():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=300)

    # Confusion matrix data from test run
    cm = np.array([
        [75,  0,  0],
        [ 0, 74,  1],
        [ 5,  0, 70]
    ])
    classes = ["LEFT\n(-45°)", "CENTER\n(0°)", "RIGHT\n(+45°)"]

    # Heatmap
    im = ax1.imshow(cm, interpolation="nearest", cmap="Blues")
    cbar = ax1.figure.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("Sample Count", rotation=-90, va="bottom", fontsize=9)

    ax1.set(xticks=np.arange(cm.shape[1]),
            yticks=np.arange(cm.shape[0]),
            xticklabels=classes, yticklabels=classes,
            title="Confusion Matrix (Overall Acc: 97.33%)",
            ylabel="True Target Sector",
            xlabel="Predicted Sector")

    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax1.text(j, i, format(cm[i, j], "d"),
                     ha="center", va="center",
                     fontsize=12, weight="bold",
                     color="white" if cm[i, j] > thresh else "#1A237E")

    # Metrics Bar Chart
    precisions = [93.75, 100.0, 98.59]
    recalls    = [100.0, 98.67, 93.33]
    f1_scores  = [96.77, 99.33, 95.89]

    x = np.arange(len(classes))
    width = 0.25

    rects1 = ax2.bar(x - width, precisions, width, label="Precision (%)", color="#1E88E5")
    rects2 = ax2.bar(x, recalls, width, label="Recall (%)", color="#43A047")
    rects3 = ax2.bar(x + width, f1_scores, width, label="F1-Score (%)", color="#FB8C00")

    ax2.set_ylabel("Score Percentage (%)")
    ax2.set_title("Sector Classification Metrics")
    ax2.set_xticks(x)
    ax2.set_xticklabels(classes)
    ax2.set_ylim(80, 105)
    ax2.grid(axis="y", ls="--", alpha=0.5)
    ax2.legend(loc="lower right", fontsize=8.5)

    # Bar value labels
    for rects in [rects1, rects2, rects3]:
        for r in rects:
            h = r.get_height()
            ax2.annotate(f"{h:.1f}", xy=(r.get_x() + r.get_width()/2, h),
                         xytext=(0, 2), textcoords="offset points",
                         ha="center", va="bottom", fontsize=7, weight="bold")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig4_confusion_matrix_and_metrics.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

# ==============================================================================
# FIG 5: RESOURCE BUDGET VS UTILIZATION
# ==============================================================================
def generate_resource_benchmark():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=300)

    # Memory: Budget vs Actual
    categories = ["Flash Memory\n(Model Footprint)", "SRAM Tensor Arena\n(Runtime Memory)"]
    budgets = [10.0, 8.0]
    actuals = [2.44, 4.00]
    used_internal = [2.44, 2.17] # actually used inside arena

    x = np.arange(len(categories))
    w = 0.35

    ax1.bar(x - w/2, budgets, w, label="Specified Budget Limit", color="#E53935", alpha=0.85)
    ax1.bar(x + w/2, actuals, w, label="System Allocated", color="#1E88E5", alpha=0.85)
    ax1.bar(x + w/2, used_internal, w, label="Net Active Peak", color="#43A047", alpha=0.85)

    ax1.set_ylabel("Memory (Kilobytes - KB)")
    ax1.set_title("Memory Footprint vs Strict Constraints")
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.set_ylim(0, 12)
    ax1.grid(axis="y", ls="--", alpha=0.5)
    ax1.legend(loc="upper right", fontsize=8.5)

    for i in range(len(categories)):
        ax1.text(x[i] - w/2, budgets[i] + 0.2, f"{budgets[i]:.1f} KB", ha="center", fontsize=8.5, weight="bold")
        ax1.text(x[i] + w/2, actuals[i] + 0.2, f"{actuals[i]:.2f} KB", ha="center", fontsize=8.5, weight="bold", color="#1565C0")

    # Latency Breakdown
    stages = ["DSP Feature Extraction\n(31-Lag NCC @ 240 MHz)", "TinyML Int8 Inference\n(TFLM Xtensa Invoke)", "Total Pipeline Latency\n(Constraint: < 10 ms)"]
    latencies = [0.48, 0.08, 0.56]
    colors = ["#FB8C00", "#8E24AA", "#2E7D32"]

    bars = ax2.bar(stages, latencies, color=colors, width=0.5, alpha=0.85)
    ax2.axhline(10.0, color="#E53935", lw=1.8, ls="--", label="Max Latency Constraint (10.0 ms)")
    ax2.set_ylabel("Latency (Milliseconds - ms)")
    ax2.set_title("Real-Time Execution Latency (94.4% Margin)")
    ax2.set_ylim(0, 11)
    ax2.grid(axis="y", ls="--", alpha=0.5)
    ax2.legend(loc="upper right", fontsize=8.5)

    for b in bars:
        h = b.get_height()
        ax2.annotate(f"{h:.2f} ms", xy=(b.get_x() + b.get_width()/2, h),
                     xytext=(0, 3), textcoords="offset points",
                     ha="center", va="bottom", fontsize=9, weight="bold")

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig5_hardware_profiling_benchmark.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

# ==============================================================================
# FIG 6: NCC SPATIAL CORRELATION CURVES
# ==============================================================================
def generate_ncc_curves():
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)

    lags = np.arange(-15, 16)
    
    # Theoretical sinc-spread NCC curves for Left (-45), Center (0), Right (+45)
    def make_ncc(center_lag, noise_lvl=0.03):
        curve = np.sinc((lags - center_lag) * 0.4)
        curve += np.random.normal(0, noise_lvl, len(lags))
        return curve / np.max(np.abs(curve))

    ncc_left = make_ncc(-3.3)
    ncc_center = make_ncc(0.0)
    ncc_right = make_ncc(+3.3)

    ax.plot(lags, ncc_left, "o-", color="#D32F2F", lw=2, label="LEFT (-45°) [Peak Lag ≈ -3.3 smp]")
    ax.plot(lags, ncc_center, "s-", color="#2E7D32", lw=2, label="CENTER (0°) [Peak Lag = 0.0 smp]")
    ax.plot(lags, ncc_right, "^-", color="#1976D2", lw=2, label="RIGHT (+45°) [Peak Lag ≈ +3.3 smp]")

    ax.axvline(0, color="gray", ls="--", alpha=0.7)
    ax.axvline(-3.3, color="#D32F2F", ls=":", alpha=0.6)
    ax.axvline(+3.3, color="#1976D2", ls=":", alpha=0.6)

    ax.set_title("31-Point Normalized Cross-Correlation (NCC) Spatial Signature", pad=12, weight="bold", color="#1A237E")
    ax.set_xlabel("Discrete Spatial Lag k (k ∈ [-15, +15]) [62.5 μs / sample]")
    ax.set_ylabel("Normalized Cross-Correlation NCC[k] ∈ [-1.0, 1.0]")
    ax.set_xticks(np.arange(-15, 16, 3))
    ax.set_ylim(-0.6, 1.15)
    ax.grid(True, ls="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=8.5)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig6_ncc_spatial_curves.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    generate_system_architecture()
    generate_tdoa_geometry()
    generate_firmware_flowchart()
    generate_confusion_matrix_and_metrics()
    generate_resource_benchmark()
    generate_ncc_curves()
    print("All 6 publication-grade figures generated successfully!")
