#!/usr/bin/env python3
"""
Builds an executive-grade 16:9 widescreen PowerPoint presentation (.pptx)
for the Acoustic Direction of Arrival (DoA) Estimation Research Internship Project.
Contains 12 comprehensive slides with diagrams, flowcharts, tables, and metric cards.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

PPTX_FILENAME = "Acoustic_DoA_Internship_Presentation.pptx"

# Color Palette
COLOR_NAVY_DARK  = RGBColor(13, 35, 58)      # #0D233A - Executive Title BG
COLOR_NAVY_LIGHT = RGBColor(21, 101, 192)    # #1565C0 - Primary Blue Accent
COLOR_CYAN       = RGBColor(0, 180, 216)     # #00B4D8 - Accent Cyan
COLOR_BG_LIGHT   = RGBColor(248, 249, 250)   # #F8F9FA - Light Slide BG
COLOR_CARD_BG    = RGBColor(255, 255, 255)   # #FFFFFF - White Card BG
COLOR_CARD_BORDER= RGBColor(207, 216, 220)   # #CFD8DC - Subtle Border
COLOR_TEXT_DARK  = RGBColor(33, 37, 41)      # #212529 - Charcoal Text
COLOR_TEXT_MUTED = RGBColor(108, 117, 125)   # #6C757D - Muted Subtitle
COLOR_GREEN      = RGBColor(46, 125, 50)     # #2E7D32 - Success Green
COLOR_ORANGE     = RGBColor(230, 81, 0)      # #E65100 - Accent Orange

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def add_header(slide, title_text, category_text="RESEARCH INTERNSHIP PROJECT DEFENSE"):
        # Top banner category
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_c = cat_box.text_frame
        tf_c.word_wrap = True
        p_c = tf_c.paragraphs[0]
        p_c.text = category_text.upper()
        p_c.font.size = Pt(10)
        p_c.font.bold = True
        p_c.font.color.rgb = COLOR_NAVY_LIGHT

        # Main Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.6))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(22)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_NAVY_DARK

        # Accent dividing line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.35), Inches(11.733), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = COLOR_CYAN
        line.line.color.rgb = COLOR_CYAN

    def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    # ==========================================================================
    # SLIDE 1: TITLE SLIDE (EXECUTIVE NAVY THEME)
    # ==========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_NAVY_DARK
    bg1.line.fill.background()

    # Title Box
    t_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.333), Inches(2.2))
    tf1 = t_box.text_frame
    tf1.word_wrap = True
    
    p0 = tf1.paragraphs[0]
    p0.text = "RESEARCH INTERNSHIP FINAL PROJECT DEFENSE"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_CYAN
    p0.space_after = Pt(14)

    p1 = tf1.add_paragraph()
    p1.text = "Acoustic Direction of Arrival (DoA) Estimation\non ESP32 Using Dual Sensors & Quantized TinyML"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    p1.space_after = Pt(14)

    p2 = tf1.add_paragraph()
    p2.text = "Ultra-Low-Power Embedded Edge AI • 10 cm Baseline • 31-Point Normalized Cross-Correlation"
    p2.font.size = Pt(14)
    p2.font.color.rgb = RGBColor(200, 225, 245)

    # 4 Key Stat Badges on Title Slide
    badges = [
        ("97.33%", "Test Accuracy"),
        ("0.56 ms", "Pipeline Latency"),
        ("2.44 KB", "Model Footprint"),
        ("4.0 KB", "Tensor Arena RAM")
    ]
    for i, (val, lbl) in enumerate(badges):
        b_x = Inches(1.0 + i * 2.9)
        b_y = Inches(4.3)
        b_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, b_x, b_y, Inches(2.6), Inches(1.2))
        b_card.fill.solid()
        b_card.fill.fore_color.rgb = RGBColor(21, 48, 78)
        b_card.line.color.rgb = COLOR_CYAN
        b_card.line.width = Pt(1.2)
        
        tf_b = b_card.text_frame
        tf_b.word_wrap = True
        pb1 = tf_b.paragraphs[0]
        pb1.text = val
        pb1.font.size = Pt(20)
        pb1.font.bold = True
        pb1.font.color.rgb = COLOR_CYAN
        pb1.alignment = PP_ALIGN.CENTER
        
        pb2 = tf_b.add_paragraph()
        pb2.text = lbl
        pb2.font.size = Pt(10)
        pb2.font.color.rgb = RGBColor(240, 240, 240)
        pb2.alignment = PP_ALIGN.CENTER

    # Footer Metadata
    f_box = s1.shapes.add_textbox(Inches(1.0), Inches(6.0), Inches(11.333), Inches(0.8))
    tff = f_box.text_frame
    pf = tff.paragraphs[0]
    pf.text = "Author: Embedded AI & TinyML Research Group  |  Platform: ESP32 (Xtensa Dual-Core @ 240 MHz)  |  Target: MAX9814 Electret Array"
    pf.font.size = Pt(11)
    pf.font.color.rgb = RGBColor(160, 185, 210)

    # ==========================================================================
    # SLIDE 2: MOTIVATION & PROBLEM FORMULATION
    # ==========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Executive Summary & Research Problem Formulation")

    # Left Column: Challenge & Industry Need
    add_card(s2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    box2_l = s2.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tf2_l = box2_l.text_frame
    tf2_l.word_wrap = True

    p = tf2_l.paragraphs[0]
    p.text = "The Edge Acoustic Challenge"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY_LIGHT
    p.space_after = Pt(10)

    points_l = [
        "Acoustic spatial awareness is vital for robotic orientation, voice-command focus, and acoustic event localization.",
        "Classical beamforming algorithms (MUSIC, ESPRIT, GCC-PHAT) require multichannel synchronous ADCs and matrix inversions prohibitive on edge MCUs.",
        "Multipath reverberation (room reflections) causes destructive interference and false peaks in classical TDOA peak-picking.",
        "Low-cost microcontrollers (ESP32) feature multiplexed SAR ADCs with inter-channel conversion skews and phase jitter.",
        "Core Goal: Deliver real-time 3-sector classification on a $4 ESP32 within strict memory (< 8 KB RAM) and timing (< 10 ms) boundaries."
    ]
    for pt in points_l:
        p = tf2_l.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_after = Pt(8)

    # Right Column: Engineered Solution & Core Directives
    add_card(s2, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    box2_r = s2.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tf2_r = box2_r.text_frame
    tf2_r.word_wrap = True

    p = tf2_r.paragraphs[0]
    p.text = "Engineered Research Directives"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_GREEN
    p.space_after = Pt(10)

    points_r = [
        "Hardware Setup: 2x MAX9814 analog electret mics separated by a compact d = 10 cm baseline, sampled via ADC1 GPIO34/35 @ 16 kHz.",
        "Feature Engineering: In-place 31-point Zero-Mean Normalized Cross-Correlation (NCC) across lags [-15, +15]. Zero heap allocation (malloc=0).",
        "Acoustic Simulation: 1,500 samples generated via PyRoomAcoustics in 5x5x3m room with realistic reverberation (T60 ≈ 0.20s).",
        "TinyML MLP Model: 31 -> Dense(16, ReLU) -> Dense(3, Softmax) quantized to full 8-bit integer precision (int8).",
        "Outcome: 97.33% accuracy, 2.44 KB Flash, 4.0 KB RAM arena, and 0.56 ms total compute latency (94.4% timing margin)."
    ]
    for pt in points_r:
        p = tf2_r.add_paragraph()
        p.text = "✔ " + pt
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_after = Pt(8)

    # ==========================================================================
    # SLIDE 3: TDOA ACOUSTIC WAVEFRONT GEOMETRY & PHYSICS
    # ==========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Mathematical Formulation of Time Difference of Arrival (TDOA)")

    # Left Card: Geometry Diagram
    add_card(s3, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    if os.path.exists("report_assets/fig2_tdoa_geometry.png"):
        s3.shapes.add_picture("report_assets/fig2_tdoa_geometry.png", Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.8))

    # Right Card: Theoretical Math Breakdown
    add_card(s3, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    box3 = s3.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tf3 = box3.text_frame
    tf3.word_wrap = True

    p = tf3.paragraphs[0]
    p.text = "Mathematical Proof & Spatial Bounds"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY_LIGHT
    p.space_after = Pt(8)

    math_points = [
        ("Far-field (Fraunhofer) Boundary:", "dF = 2·d² / λ = 2·(0.10)² / 0.086 ≈ 23.3 cm. Since R ≥ 1.0 m, planar wavefront assumption is exact."),
        ("Path Difference Equation:", "Δr = d · sin(θ), where θ is azimuth from broadside (+Y)."),
        ("Continuous Delay Equation:", "τ(θ) = Δr / c = (d / c) · sin(θ), with c = 343 m/s."),
        ("Discrete Lag Formulation:", "k_τ(θ) = τ(θ) · Fs = (d·Fs / c) · sin(θ) ≈ 4.6647 · sin(θ) samples."),
        ("LEFT (-45° nominal):", "τ = -206.15 μs ⇒ k_τ ≈ -3.30 samples (Left channel leads)."),
        ("CENTER (0° nominal):", "τ = 0.00 μs ⇒ k_τ = 0.00 samples (Simultaneous arrival)."),
        ("RIGHT (+45° nominal):", "τ = +206.15 μs ⇒ k_τ ≈ +3.30 samples (Right channel leads)."),
        ("Why 31 Lags [-15, +15]?", "Window = ±937.5 μs (3.2x physical transit time of 291.5 μs). Captures sinc interpolation curve and early multipath echoes.")
    ]
    for title, desc in math_points:
        p = tf3.add_paragraph()
        p.text = "• " + title + " " + desc
        p.font.size = Pt(9.5)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_after = Pt(4)

    # ==========================================================================
    # SLIDE 4: SYSTEM HARDWARE & SOFTWARE ARCHITECTURE
    # ==========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "End-to-End System Hardware & Software Architecture")

    # Architecture Image
    add_card(s4, Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.3))
    if os.path.exists("report_assets/fig1_system_architecture.png"):
        s4.shapes.add_picture("report_assets/fig1_system_architecture.png", Inches(1.0), Inches(1.8), Inches(7.1), Inches(4.8))

    # Architecture Key Highlights
    add_card(s4, Inches(8.6), Inches(1.6), Inches(3.9), Inches(5.3))
    box4 = s4.shapes.add_textbox(Inches(8.8), Inches(1.8), Inches(3.5), Inches(4.9))
    tf4 = box4.text_frame
    tf4.word_wrap = True

    p = tf4.paragraphs[0]
    p.text = "Architectural Pillars"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY_LIGHT
    p.space_after = Pt(8)

    arch_highlights = [
        "Transducers: Dual MAX9814 electret amplifiers with internal 2V mic bias and AGC.",
        "ADC Configuration: GPIO34 (Left) and GPIO35 (Right) on SAR ADC1 (avoids Wi-Fi lock on ADC2).",
        "Deterministic DSP: 256-sample windowing @ 16 kHz. Static stack arrays with zero malloc.",
        "Pre-Trigger Ring Buffer: 32 samples (2 ms) retained to prevent impulse attack clipping.",
        "TinyML Engine: TFLM running on Xtensa LX6 @ 240 MHz. Static 4 KB Tensor Arena.",
        "Lockout Debounce: 300 ms refractory window eliminates reverberant echo re-triggers."
    ]
    for h in arch_highlights:
        p = tf4.add_paragraph()
        p.text = "✔ " + h
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_after = Pt(6)

    # ==========================================================================
    # SLIDE 5: DIGITAL SIGNAL PROCESSING & FEATURE ENGINEERING
    # ==========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Feature Engineering: Zero-Mean Normalized Cross-Correlation")

    # Left: NCC Curves Diagram
    add_card(s5, Inches(0.8), Inches(1.6), Inches(6.0), Inches(5.3))
    if os.path.exists("report_assets/fig6_ncc_spatial_curves.png"):
        s5.shapes.add_picture("report_assets/fig6_ncc_spatial_curves.png", Inches(1.0), Inches(1.8), Inches(5.6), Inches(4.8))

    # Right: DSP Routine & Optimization
    add_card(s5, Inches(7.1), Inches(1.6), Inches(5.4), Inches(5.3))
    box5 = s5.shapes.add_textbox(Inches(7.3), Inches(1.8), Inches(5.0), Inches(4.9))
    tf5 = box5.text_frame
    tf5.word_wrap = True

    p = tf5.paragraphs[0]
    p.text = "Mathematical Routine & Optimization"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_ORANGE
    p.space_after = Pt(8)

    dsp_points = [
        "Step 1: DC Bias Removal: Computes means μx, μy across 256 samples; subtracts DC in-place.",
        "Step 2: Energy Normalization: Calculates Ex = ∑x̃[n]² and Ey = ∑ỹ[n]². Denominator = √(Ex·Ey) + 1e-7.",
        "Step 3: Normalized Correlation across [-15, +15]: NCC[k] = Rxy[k] / Denominator ∈ [-1.0, 1.0].",
        "Gain Invariance: Scalar gain factors cancel completely: NCC[a·x, b·y] ≡ NCC[x, y]. Fully immune to MAX9814 AGC gain variations!",
        "Xtensa FPU Acceleration: 4-way loop unrolling with pointer arithmetic executes in 0.48 ms on ESP32 (5.1 μs on host PC).",
        "Zero-Malloc Guarantee: Fixed-size static arrays (s_x_zm[256], s_y_zm[256]) guarantee deterministic execution without heap fragmentation."
    ]
    for pt in dsp_points:
        p = tf5.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_after = Pt(5)

    # ==========================================================================
    # SLIDE 6: ACOUSTIC SIMULATION & SYNTHETIC DATASET
    # ==========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Acoustic Simulation & Synthetic Dataset Generation")

    # 3 Cards on Slide 6
    # Card 1: Room Acoustics
    add_card(s6, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.3))
    box6_1 = s6.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.3), Inches(4.9))
    tf6_1 = box6_1.text_frame
    tf6_1.word_wrap = True
    p = tf6_1.paragraphs[0]
    p.text = "1. Room Acoustics"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY_LIGHT
    p.space_after = Pt(8)
    r_pts = [
        "PyRoomAcoustics 3D shoe-box room: 5.0m x 5.0m x 3.0m.",
        "Reverberation time target: T60 = 0.20s (representative of indoor conference / office space).",
        "Sabine wall absorption: α = 0.5492.",
        "Image Source Model (ISM) reflection order capped at 4th order for early multipath modeling."
    ]
    for pt in r_pts:
        p = tf6_1.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(10)
        p.space_after = Pt(5)

    # Card 2: Acoustic Transients
    add_card(s6, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.3))
    box6_2 = s6.shapes.add_textbox(Inches(5.0), Inches(1.8), Inches(3.3), Inches(4.9))
    tf6_2 = box6_2.text_frame
    tf6_2.word_wrap = True
    p = tf6_2.paragraphs[0]
    p.text = "2. Transient Signals"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_ORANGE
    p.space_after = Pt(8)
    t_pts = [
        "Synthesizes 4 realistic transient event classes mimicking snap/clap impulses.",
        "Finger snaps: high-frequency resonant decay (1.8 - 4.2 kHz) with noise burst.",
        "Hand claps: multi-burst decaying envelope with random sub-burst offsets.",
        "Speech plosives / clicks: frequency modulated linear chirps & bandpassed noise pulses."
    ]
    for pt in t_pts:
        p = tf6_2.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(10)
        p.space_after = Pt(5)

    # Card 3: Dataset Balance
    add_card(s6, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.3))
    box6_3 = s6.shapes.add_textbox(Inches(9.0), Inches(1.8), Inches(3.3), Inches(4.9))
    tf6_3 = box6_3.text_frame
    tf6_3.word_wrap = True
    p = tf6_3.paragraphs[0]
    p.text = "3. Spatial Perturbations"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_GREEN
    p.space_after = Pt(8)
    d_pts = [
        "1,500 total balanced samples (500 per class).",
        "LEFT: -45° nominal (range: [-55°, -35°]).",
        "CENTER: 0° nominal (range: [-10°, +10°]).",
        "RIGHT: +45° nominal (range: [+35°, +55°]).",
        "Distance perturbations: 1.0m - 2.4m.",
        "Elevation variation: ±0.25m.",
        "Additive sensor noise: SNR ~ 22-28 dB."
    ]
    for pt in d_pts:
        p = tf6_3.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(10)
        p.space_after = Pt(5)

    # ==========================================================================
    # SLIDE 7: TINYML MODEL ARCHITECTURE & INT8 QUANTIZATION
    # ==========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "TinyML Architecture & 8-Bit Integer (Int8) Quantization")

    # Left: Network Topology
    add_card(s7, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    box7_l = s7.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tf7_l = box7_l.text_frame
    tf7_l.word_wrap = True
    p = tf7_l.paragraphs[0]
    p.text = "Ultra-Compact MLP Topology"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY_LIGHT
    p.space_after = Pt(8)
    mlp_pts = [
        "Input Layer: 31 nodes (31-point normalized cross-correlation vector).",
        "Hidden Layer: Dense(16, activation='relu') ⇒ 31 x 16 + 16 = 512 parameters.",
        "Output Layer: Dense(3, activation='softmax') ⇒ 16 x 3 + 3 = 51 parameters.",
        "Total Trainable Parameters: Exactly 563 weights & biases.",
        "Arithmetic Complexity: 649 Multiply-Accumulate (MAC) operations per inference.",
        "Inference Execution Time: ~0.08 ms on Xtensa LX6 @ 240 MHz."
    ]
    for pt in mlp_pts:
        p = tf7_l.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(10.5)
        p.space_after = Pt(6)

    # Right: Quantization Math & Footprint
    add_card(s7, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    box7_r = s7.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tf7_r = box7_r.text_frame
    tf7_r.word_wrap = True
    p = tf7_r.paragraphs[0]
    p.text = "Full Int8 Quantization & Memory"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_GREEN
    p.space_after = Pt(8)
    q_pts = [
        "Quantization Strategy: Post-Training Integer Quantization (PTQ) using representative dataset calibration.",
        "Input Mapping: q_in = round(x / 0.00763765) - 4  (signed int8 [-128, 127]).",
        "Output Mapping: prob = (q_out - (-128)) * 0.00390625.",
        "Model Footprint: 2,440 bytes (2.38 KB) in Flash (< 10 KB budget, 76.2% margin!).",
        "Runtime Tensor Arena: 4,096 bytes (4 KB) static SRAM (< 8 KB budget, 48.8% margin!).",
        "Embedded C Array: Exported as 16-byte aligned array `g_model_data` in `model_data.h`."
    ]
    for pt in q_pts:
        p = tf7_r.add_paragraph()
        p.text = "✔ " + pt
        p.font.size = Pt(10.5)
        p.space_after = Pt(6)

    # ==========================================================================
    # SLIDE 8: REAL-TIME FIRMWARE & FINITE STATE MACHINE
    # ==========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "ESP32 Real-Time Firmware & Finite State Machine")

    # Flowchart Image
    add_card(s8, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    if os.path.exists("report_assets/fig3_dsp_flowchart.png"):
        s8.shapes.add_picture("report_assets/fig3_dsp_flowchart.png", Inches(1.2), Inches(1.7), Inches(4.8), Inches(5.1))

    # Right: Firmware Design Highlights
    add_card(s8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    box8 = s8.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tf8 = box8.text_frame
    tf8.word_wrap = True
    p = tf8.paragraphs[0]
    p.text = "Firmware Engineering Rigor"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY_LIGHT
    p.space_after = Pt(8)
    fw_pts = [
        "Boot & Calibration: Samples 2,048 readings to establish ambient DC bias (nominally ~1.25V / 1550 ADC units).",
        "High-Precision 16 kHz Polling: Uses `esp_timer_get_time()` with busy-wait delay to enforce exact 62.5 μs sample periods.",
        "Circular Pre-Trigger Buffer: 32 samples (2 ms) stored continuously; prevents missing sharp snap/clap onset attack edges.",
        "Dual-Condition Energy Trigger: Triggers when absolute deviation from DC bias > 380 units. Slow IIR updates bias during silence.",
        "Zero-Copy DSP Execution: Fills 256-sample frame buffer and calls unrolled NCC routine without any heap allocation.",
        "Echo Debounce Refractory Lockout: 300 ms lockout post-inference suppresses room reverberation and multipath retriggers."
    ]
    for pt in fw_pts:
        p = tf8.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(10)
        p.space_after = Pt(6)

    # ==========================================================================
    # SLIDE 9: EXPERIMENTAL RESULTS & CONFUSION MATRIX
    # ==========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Experimental Validation & Confusion Matrix Analysis")

    # Confusion Matrix Image
    add_card(s9, Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.3))
    if os.path.exists("report_assets/fig4_confusion_matrix_and_metrics.png"):
        s9.shapes.add_picture("report_assets/fig4_confusion_matrix_and_metrics.png", Inches(1.0), Inches(1.8), Inches(7.1), Inches(4.8))

    # Right: Results Summary Card
    add_card(s9, Inches(8.6), Inches(1.6), Inches(3.9), Inches(5.3))
    box9 = s9.shapes.add_textbox(Inches(8.8), Inches(1.8), Inches(3.5), Inches(4.9))
    tf9 = box9.text_frame
    tf9.word_wrap = True
    p = tf9.paragraphs[0]
    p.text = "Performance Metrics"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_GREEN
    p.space_after = Pt(8)
    res_pts = [
        "Overall Test Accuracy: 97.33% across 225 independent test samples.",
        "LEFT (-45°): Precision = 93.75%, Recall = 100.0% (75/75), F1 = 96.77%.",
        "CENTER (0°): Precision = 100.0%, Recall = 98.67% (74/75), F1 = 99.33%.",
        "RIGHT (+45°): Precision = 98.59%, Recall = 93.33% (70/75), F1 = 95.89%.",
        "High Robustness: Operates seamlessly under reverberant room conditions (T60 ≈ 0.20s) and SNR down to 22 dB.",
        "Low Confusion: Only 6 out of 225 samples misclassified, occurring solely at extreme boundary angles."
    ]
    for pt in res_pts:
        p = tf9.add_paragraph()
        p.text = "✔ " + pt
        p.font.size = Pt(9.5)
        p.space_after = Pt(5)

    # ==========================================================================
    # SLIDE 10: RESOURCE UTILIZATION & BENCHMARKING
    # ==========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Embedded Resource Profiling & Constraint Verification")

    # Left: Benchmark Charts
    add_card(s10, Inches(0.8), Inches(1.6), Inches(7.5), Inches(5.3))
    if os.path.exists("report_assets/fig5_hardware_profiling_benchmark.png"):
        s10.shapes.add_picture("report_assets/fig5_hardware_profiling_benchmark.png", Inches(1.0), Inches(1.8), Inches(7.1), Inches(4.8))

    # Right: Constraint Check Table Card
    add_card(s10, Inches(8.6), Inches(1.6), Inches(3.9), Inches(5.3))
    box10 = s10.shapes.add_textbox(Inches(8.8), Inches(1.8), Inches(3.5), Inches(4.9))
    tf10 = box10.text_frame
    tf10.word_wrap = True
    p = tf10.paragraphs[0]
    p.text = "Constraint Compliance"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY_LIGHT
    p.space_after = Pt(8)
    comp_pts = [
        ("Flash Memory Footprint:", "Budget: < 10.0 KB\nAchieved: 2.44 KB (76.2% margin) [PASS]"),
        ("Tensor Arena RAM:", "Budget: < 8.0 KB\nAchieved: 4.00 KB (48.8% margin) [PASS]"),
        ("DSP Feature Extraction:", "31-Lag NCC: 0.48 ms @ 240 MHz [PASS]"),
        ("Quantized Model Inference:", "649 MACs: 0.08 ms @ 240 MHz [PASS]"),
        ("Total Pipeline Latency:", "Budget: < 10.0 ms\nAchieved: 0.56 ms (94.4% margin!) [PASS]"),
        ("Dynamic Heap Allocation:", "Requirement: malloc = 0\nAchieved: 0 bytes dynamic [PASS]")
    ]
    for lbl, val in comp_pts:
        p = tf10.add_paragraph()
        p.text = "• " + lbl + " " + val
        p.font.size = Pt(9.5)
        p.space_after = Pt(4)

    # ==========================================================================
    # SLIDE 11: THEORETICAL HARDWARE LIMITATIONS & DEFENSE
    # ==========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Research Defense: Hardware Limitations & Mitigations")

    # 3 Column Cards
    # Card 1: Conical Ambiguity
    add_card(s11, Inches(0.8), Inches(1.6), Inches(3.7), Inches(5.3))
    box11_1 = s11.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(3.3), Inches(4.9))
    tf11_1 = box11_1.text_frame
    tf11_1.word_wrap = True
    p = tf11_1.paragraphs[0]
    p.text = "1. Front-Back Ambiguity"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_ORANGE
    p.space_after = Pt(8)
    a_pts = [
        "Physical Cause: A 1D 2-mic linear array measures delay along baseline axis: Δr = d·cos(α).",
        "Rotational symmetry creates a cone of revolution ('cone of confusion'). Front azimuth θ produces identical delay to rear 180°-θ.",
        "Mitigation: Wall-mounted baffling restricts acoustic arrivals to the front half-plane.",
        "Future Upgrade: 2D planar array (3 mics in triangle) resolves 360° front/back ambiguity."
    ]
    for pt in a_pts:
        p = tf11_1.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(9.5)
        p.space_after = Pt(4)

    # Card 2: SAR ADC Jitter
    add_card(s11, Inches(4.8), Inches(1.6), Inches(3.7), Inches(5.3))
    box11_2 = s11.shapes.add_textbox(Inches(5.0), Inches(1.8), Inches(3.3), Inches(4.9))
    tf11_2 = box11_2.text_frame
    tf11_2.word_wrap = True
    p = tf11_2.paragraphs[0]
    p.text = "2. SAR ADC Phase Jitter"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY_LIGHT
    p.space_after = Pt(8)
    j_pts = [
        "Physical Cause: ESP32 ADC1 shares a single sample-and-hold (S/H) capacitor multiplexed across pins.",
        "Sequential read of GPIO34 and GPIO35 creates a ~9.5 μs inter-channel hardware delay.",
        "Fictitious Path Offset: Δr_skew = c · 9.5 μs ≈ 3.26 mm (0.15 samples).",
        "Mitigation: Because skew is constant, the MLP input weights automatically learn and calibrate this hardware bias.",
        "Alternative: ESP32 I2S parallel ADC DMA ping-pong mode."
    ]
    for pt in j_pts:
        p = tf11_2.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(9.5)
        p.space_after = Pt(4)

    # Card 3: AGC Dynamics
    add_card(s11, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.3))
    box11_3 = s11.shapes.add_textbox(Inches(9.0), Inches(1.8), Inches(3.3), Inches(4.9))
    tf11_3 = box11_3.text_frame
    tf11_3.word_wrap = True
    p = tf11_3.paragraphs[0]
    p.text = "3. MAX9814 AGC Dynamics"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_GREEN
    p.space_after = Pt(8)
    g_pts = [
        "Physical Cause: Independent active AGC circuits adjust gains dynamically based on individual SPL.",
        "Mathematical Invariance: Zero-Mean NCC divides by standard deviations: NCC[a·x, b·y] ≡ NCC[x, y].",
        "Strict Scalar Gain Invariance: Scalar gain differences from AGC have ZERO effect on normalized correlation shape.",
        "Onset Timing: Processing within first 16 ms operates inside pre-compression linear attack window."
    ]
    for pt in g_pts:
        p = tf11_3.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(9.5)
        p.space_after = Pt(4)

    # ==========================================================================
    # SLIDE 12: CONCLUSION & FUTURE WORK
    # ==========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Conclusions, Deliverables & Future Research Directions")

    # Left Card: Key Achievements
    add_card(s12, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.3))
    box12_l = s12.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.2), Inches(4.9))
    tf12_l = box12_l.text_frame
    tf12_l.word_wrap = True
    p = tf12_l.paragraphs[0]
    p.text = "Key Project Achievements"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_GREEN
    p.space_after = Pt(8)
    ach_pts = [
        "Autonomous End-to-End System: Integrated analog front-end, high-speed acquisition, DSP feature engine, and TinyML inference.",
        "State-of-the-Art Efficiency: Total execution time of 0.56 ms satisfies the < 10 ms requirement with a 94.4% timing margin.",
        "Extreme Memory Economy: Model footprint is only 2.44 KB Flash (76% margin) and Tensor Arena is 4.0 KB RAM (49% margin).",
        "Robust Indoor Accuracy: 97.33% classification accuracy in reverberant 0.20s T60 room environments.",
        "Production-Grade Firmware: Clean, zero-malloc C++ implementation with debouncing and circular pre-triggering."
    ]
    for pt in ach_pts:
        p = tf12_l.add_paragraph()
        p.text = "✔ " + pt
        p.font.size = Pt(10.5)
        p.space_after = Pt(6)

    # Right Card: Deliverables & Next Steps
    add_card(s12, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.3))
    box12_r = s12.shapes.add_textbox(Inches(7.0), Inches(1.8), Inches(5.3), Inches(4.9))
    tf12_r = box12_r.text_frame
    tf12_r.word_wrap = True
    p = tf12_r.paragraphs[0]
    p.text = "Deliverables & Future Roadmap"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_NAVY_LIGHT
    p.space_after = Pt(8)
    del_pts = [
        "1. Complete Simulation & Training Script: `train_doa.py`",
        "2. Quantized Int8 TFLite Binary: `doa_model_int8.tflite` (2,440 bytes)",
        "3. Embedded Model Header: `model_data.h` (C-array)",
        "4. Production Arduino C++ Firmware: `esp32_doa_firmware.ino`",
        "5. C++ Validation & Latency Harness: `test_dsp.cpp` (5.1 μs)",
        "6. Formal IEEE Project Report PDF: `IEEE_Acoustic_DoA_Internship_Report.pdf`",
        "7. Next Steps: Planar 3-mic triangular array for 360° azimuth/elevation localization and adaptive beam steering."
    ]
    for pt in del_pts:
        p = tf12_r.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(10)
        p.space_after = Pt(4)

    prs.save(PPTX_FILENAME)
    print(f"PowerPoint Presentation successfully created: {PPTX_FILENAME} ({os.path.getsize(PPTX_FILENAME)} bytes)")

if __name__ == "__main__":
    create_presentation()
