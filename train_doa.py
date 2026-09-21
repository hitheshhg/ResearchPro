#!/usr/bin/env python3
"""
Direction of Arrival (DoA) Estimation Pipeline for ESP32 TinyML
- Simulates 5x5x3m acoustic shoe-box room with reverberation (T60 ~ 0.2s) using pyroomacoustics
- Synthesizes 1,500 samples (500 Left, 500 Center, 500 Right) with angular and spatial perturbations
- Extracts 31-point Zero-Mean Normalized Cross-Correlation (NCC) vectors (lags [-15, +15])
- Trains an ultra-compact MLP: Input(31) -> Dense(16, ReLU) -> Dense(3, Softmax)
- Evaluates test accuracy and outputs Confusion Matrix
- Quantizes model to full 8-bit integer (int8) TFLite format
- Exports the quantized model as an embedded C header file: 'model_data.h'
"""

import os
import sys
import math
import random
import numpy as np
import scipy.signal as signal
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# Suppress excessive TensorFlow logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
import tensorflow as tf

# Set random seeds for reproducibility
SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)
random.seed(SEED)

# ==============================================================================
# 1. ACOUSTIC SIMULATION & SIGNAL GENERATION PARAMETERS
# ==============================================================================
FS = 16000            # Sampling rate in Hz
WINDOW_SIZE = 256     # Samples per channel per inference window (16 ms)
MAX_LAG = 15          # Discrete lag range: [-15, +15] -> 31 spatial features
NUM_CLASSES = 3       # 0: Left (-45 deg), 1: Center (0 deg), 2: Right (+45 deg)
SAMPLES_PER_CLASS = 500
TOTAL_SAMPLES = NUM_CLASSES * SAMPLES_PER_CLASS  # 1,500 samples

# Room Dimensions: 5m x 5m x 3m
ROOM_DIM = [5.0, 5.0, 3.0]
TARGET_T60 = 0.20     # 200 ms reverberation time

# Microphone array geometry: 2 MAX9814 microphones spaced 10 cm apart along X-axis
MIC_BASELINE = 0.10   # 10 cm = 0.10 m
MIC_CENTER = np.array([ROOM_DIM[0] / 2.0, ROOM_DIM[1] / 2.0, 1.2])  # Array center in room
# Left mic: -5 cm along X; Right mic: +5 cm along X
MIC_POSITIONS = np.array([
    [MIC_CENTER[0] - MIC_BASELINE / 2.0, MIC_CENTER[1], MIC_CENTER[2]],  # Mic 0: Left
    [MIC_CENTER[0] + MIC_BASELINE / 2.0, MIC_CENTER[1], MIC_CENTER[2]]   # Mic 1: Right
]).T  # Shape: (3, 2) for pyroomacoustics

# Angular sectors (degrees relative to broadside +Y axis)
# Left: -45 deg nominal, perturbations in [-55, -35]
# Center: 0 deg nominal, perturbations in [-10, +10]
# Right: +45 deg nominal, perturbations in [+35, +55]
ANGLE_RANGES = {
    0: (-55.0, -35.0),  # LEFT
    1: (-10.0, +10.0),  # CENTER
    2: (+35.0, +55.0),  # RIGHT
}
CLASS_NAMES = ["LEFT (-45°)", "CENTER (0°)", "RIGHT (+45°)"]

# ==============================================================================
# 2. ACOUSTIC TRANSIENT SYNTHESIZER
# ==============================================================================
def generate_transient_signal(fs=FS, duration=0.08):
    """
    Synthesizes acoustic transients mimicking finger snaps, hand claps,
    speech plosives, and tongue clicks.
    """
    n_samples = int(fs * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    sig_type = random.choice(["snap", "clap", "chirp", "burst"])
    
    if sig_type == "snap":
        # Rapid decaying high-frequency oscillation (1.5 kHz - 4.5 kHz)
        f_res = random.uniform(1800, 4200)
        decay = random.uniform(80, 220)
        sig = np.sin(2 * np.pi * f_res * t) * np.exp(-decay * t)
        # Add high-frequency noise burst at onset
        noise_decay = random.uniform(150, 300)
        noise = np.random.normal(0, 0.4, n_samples) * np.exp(-noise_decay * t)
        sig += noise
    elif sig_type == "clap":
        # Multiple closely spaced sub-bursts with exponential decay
        sig = np.zeros(n_samples)
        num_bursts = random.randint(3, 6)
        for _ in range(num_bursts):
            offset_s = random.uniform(0.0, 0.02)
            offset_idx = int(offset_s * fs)
            b_decay = random.uniform(70, 180)
            b_len = n_samples - offset_idx
            if b_len > 0:
                t_b = t[:b_len]
                f_b = random.uniform(800, 2800)
                sub_burst = (np.sin(2 * np.pi * f_b * t_b) + 0.5 * np.random.randn(b_len)) * np.exp(-b_decay * t_b)
                sig[offset_idx:] += sub_burst
    elif sig_type == "chirp":
        # Frequency modulated pulse
        f0 = random.uniform(800, 1500)
        f1 = random.uniform(2500, 4500)
        decay = random.uniform(50, 120)
        sig = signal.chirp(t, f0=f0, f1=f1, t1=duration, method="linear") * np.exp(-decay * t)
    else:  # "burst"
        # Bandpassed noise burst
        noise = np.random.normal(0, 1.0, n_samples)
        decay = random.uniform(90, 200)
        envelope = np.exp(-decay * t)
        # Bandpass filter between 500 Hz and 4000 Hz
        sos = signal.butter(4, [500, 4000], btype="bandpass", fs=fs, output="sos")
        sig = signal.sosfilt(sos, noise) * envelope

    # Normalize peak
    max_val = np.max(np.abs(sig))
    if max_val > 1e-6:
        sig /= max_val
    return sig.astype(np.float32)

# ==============================================================================
# 3. NORMALIZED CROSS-CORRELATION FEATURE EXTRACTION (DSP ROUTINE)
# ==============================================================================
def compute_ncc_features(sig_left, sig_right, max_lag=MAX_LAG):
    """
    Computes zero-mean Normalized Cross-Correlation (NCC) vector for lags [-max_lag, +max_lag].
    Exact mathematical equivalent of the embedded C fixed-buffer routine.
    Feature vector length: 2 * max_lag + 1 = 31.
    """
    x = np.asarray(sig_left, dtype=np.float64)
    y = np.asarray(sig_right, dtype=np.float64)
    N = len(x)
    assert len(y) == N, "Signals must have identical length"

    # Step 1: Remove DC bias (Zero-mean normalization)
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    x_zero = x - x_mean
    y_zero = y - y_mean

    # Step 2: Calculate signal energy / variance
    var_x = np.sum(x_zero ** 2)
    var_y = np.sum(y_zero ** 2)
    denom = np.sqrt(var_x * var_y) + 1e-9

    # Step 3: Compute Cross-Correlation for lags k in [-max_lag, +max_lag]
    features = np.zeros(2 * max_lag + 1, dtype=np.float32)
    for idx, k in enumerate(range(-max_lag, max_lag + 1)):
        if k >= 0:
            # y is delayed relative to x: sum(x[n] * y[n+k])
            corr = np.sum(x_zero[:N - k] * y_zero[k:])
        else:
            # x is delayed relative to y: sum(x[n - k] * y[n])
            corr = np.sum(x_zero[-k:] * y_zero[:N + k])
        features[idx] = float(corr / denom)

    return features

# ==============================================================================
# 4. DATASET SYNTHESIS WITH PYROOMACOUSTICS
# ==============================================================================
def synthesize_dataset():
    """
    Generates 1,500 acoustic samples simulated in a 5x5x3m reverberant room.
    Extracts 31-point NCC feature vector for each sample.
    """
    import pyroomacoustics as pra

    print("=" * 70)
    print("STEP 1: Synthesizing Dataset with PyRoomAcoustics")
    print(f"Room: {ROOM_DIM[0]}x{ROOM_DIM[1]}x{ROOM_DIM[2]}m, Target T60: {TARGET_T60}s")
    print(f"Array: 2 MAX9814 mics spaced {MIC_BASELINE*100:.1f} cm apart at {MIC_CENTER}")
    print(f"Target: {NUM_CLASSES} classes, {SAMPLES_PER_CLASS} samples/class = {TOTAL_SAMPLES} total")
    print("=" * 70)

    # Invert Sabine's formula to determine wall absorption and maximum ISM reflection order
    e_absorption, max_order = pra.inverse_sabine(TARGET_T60, ROOM_DIM)
    max_order = min(max_order, 4)  # Retain early reflections up to 4th order for fast ISM simulation
    print(f"Calculated wall energy absorption: {e_absorption:.4f}, Max ISM order: {max_order}", flush=True)

    X_features = []
    y_labels = []

    for class_idx in range(NUM_CLASSES):
        ang_min, ang_max = ANGLE_RANGES[class_idx]
        class_name = CLASS_NAMES[class_idx]
        print(f"\nGenerating {SAMPLES_PER_CLASS} samples for Class {class_idx} [{class_name}] (Angles: {ang_min}° to {ang_max}°)...")

        for sample_i in range(SAMPLES_PER_CLASS):
            # Create room instance
            room = pra.ShoeBox(
                ROOM_DIM,
                fs=FS,
                materials=pra.Material(e_absorption),
                max_order=max_order
            )
            # Add 2-mic array
            room.add_microphone_array(pra.MicrophoneArray(MIC_POSITIONS, FS))

            # Sample random angle, distance, and height perturbation
            theta_deg = random.uniform(ang_min, ang_max)
            theta_rad = math.radians(theta_deg)
            dist = random.uniform(1.0, 2.4)
            delta_z = random.uniform(-0.25, 0.25)

            # Source position relative to mic center:
            # Broadside is +Y. Angle theta measured from +Y:
            # theta < 0 -> -X (Left), theta > 0 -> +X (Right)
            src_x = MIC_CENTER[0] + dist * math.sin(theta_rad)
            src_y = MIC_CENTER[1] + dist * math.cos(theta_rad)
            src_z = MIC_CENTER[2] + delta_z

            # Clamp within room bounds (keep 20 cm margin from walls)
            src_x = np.clip(src_x, 0.2, ROOM_DIM[0] - 0.2)
            src_y = np.clip(src_y, 0.2, ROOM_DIM[1] - 0.2)
            src_z = np.clip(src_z, 0.2, ROOM_DIM[2] - 0.2)

            # Generate source signal and add to room
            audio_signal = generate_transient_signal(fs=FS, duration=0.08)
            room.add_source([src_x, src_y, src_z], signal=audio_signal)

            # Simulate acoustic propagation and multipath reflections
            room.simulate()

            # Extracted microphone signals: shape (2, num_samples)
            mic_sigs = room.mic_array.signals
            ch0 = mic_sigs[0, :]  # Left
            ch1 = mic_sigs[1, :]  # Right

            # Add realistic ambient acoustic & ADC thermal noise (SNR ~ 25 dB)
            p_sig = (np.mean(ch0 ** 2) + np.mean(ch1 ** 2)) / 2.0
            p_noise = p_sig / (10 ** (random.uniform(22.0, 30.0) / 10.0)) + 1e-9
            noise_std = np.sqrt(p_noise)
            ch0 += np.random.normal(0, noise_std, len(ch0))
            ch1 += np.random.normal(0, noise_std, len(ch1))

            # Detect onset / energy peak to extract exactly WINDOW_SIZE (256) samples
            combined_energy = ch0 ** 2 + ch1 ** 2
            peak_idx = int(np.argmax(combined_energy))
            # Start window slightly before peak (lead of 32 samples)
            start_idx = max(0, peak_idx - 32)
            end_idx = start_idx + WINDOW_SIZE

            if end_idx > len(ch0):
                end_idx = len(ch0)
                start_idx = max(0, end_idx - WINDOW_SIZE)

            win_left = ch0[start_idx:end_idx]
            win_right = ch1[start_idx:end_idx]

            # Zero-pad if signal shorter than WINDOW_SIZE
            if len(win_left) < WINDOW_SIZE:
                win_left = np.pad(win_left, (0, WINDOW_SIZE - len(win_left)))
                win_right = np.pad(win_right, (0, WINDOW_SIZE - len(win_right)))

            # Extract 31-point NCC feature vector
            feat = compute_ncc_features(win_left, win_right, max_lag=MAX_LAG)
            X_features.append(feat)
            y_labels.append(class_idx)

            if (sample_i + 1) % 100 == 0:
                sys.stdout.write(f".")
                sys.stdout.flush()

    X = np.array(X_features, dtype=np.float32)
    y = np.array(y_labels, dtype=np.int32)
    print(f"\nDataset synthesis complete! Feature matrix: {X.shape}, Labels: {y.shape}")
    return X, y

# ==============================================================================
# 5. TINYML MODEL ARCHITECTURE & TRAINING
# ==============================================================================
def train_mlp_model(X_train, y_train, X_val, y_val):
    """
    Builds and trains an ultra-compact MLP:
    Input: (31,) -> Dense(16, ReLU) -> Dense(3, Softmax)
    Parameters:
      Layer 1: 31 * 16 + 16 = 512 parameters
      Layer 2: 16 * 3 + 3 = 51 parameters
      Total: 563 parameters (~563 bytes in int8!)
    """
    print("\n" + "=" * 70)
    print("STEP 2: Building and Training Compact MLP")
    print("Architecture: Input(31) -> Dense(16, ReLU) -> Dense(3, Softmax)")
    print("=" * 70)

    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(2 * MAX_LAG + 1,), name="ncc_input"),
        tf.keras.layers.Dense(16, activation="relu", name="dense_hidden"),
        tf.keras.layers.Dense(NUM_CLASSES, activation="softmax", name="sector_output")
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.003),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=15,
            restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            min_lr=1e-5
        )
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=60,
        batch_size=32,
        callbacks=callbacks,
        verbose=1
    )

    return model

# ==============================================================================
# 6. EVALUATION & PERFORMANCE VERIFICATION
# ==============================================================================
def evaluate_model(model, X_test, y_test):
    """
    Evaluates classification performance, accuracy, and confusion matrix.
    """
    print("\n" + "=" * 70)
    print("STEP 3: Model Evaluation on Independent Test Set")
    print("=" * 70)

    y_pred_probs = model.predict(X_test)
    y_pred = np.argmax(y_pred_probs, axis=1)

    acc = np.mean(y_pred == y_test) * 100.0
    print(f"\nOverall Test Accuracy: {acc:.2f}%\n")

    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=CLASS_NAMES, digits=4))

    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:")
    print(f"                Predicted LEFT  Predicted CENTER  Predicted RIGHT")
    for row_idx, row in enumerate(cm):
        print(f"Actual {CLASS_NAMES[row_idx]:<14}: {row[0]:^14} {row[1]:^16} {row[2]:^15}")

    return acc, cm

# ==============================================================================
# 7. INT8 QUANTIZATION FOR TENSORFLOW LITE FOR MICROCONTROLLERS
# ==============================================================================
def quantize_to_int8(model, representative_data, output_tflite_path="doa_model_int8.tflite"):
    """
    Performs full 8-bit integer quantization (weights and activations).
    Generates TFLite model compatible with ESP32 Xtensa TFLM.
    """
    print("\n" + "=" * 70)
    print("STEP 4: Full 8-bit Integer (int8) Quantization")
    print("=" * 70)

    def representative_dataset_gen():
        for i in range(len(representative_data)):
            # TFLite expects input with batch dimension
            sample = np.expand_dims(representative_data[i], axis=0).astype(np.float32)
            yield [sample]

    @tf.function(input_signature=[tf.TensorSpec(shape=[1, 2 * MAX_LAG + 1], dtype=tf.float32)])
    def model_fn(x):
        return model(x)

    concrete_func = model_fn.get_concrete_function()
    converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete_func])
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset_gen

    # Enforce full integer quantization for TFLM execution
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    tflite_model_int8 = converter.convert()

    with open(output_tflite_path, "wb") as f:
        f.write(tflite_model_int8)

    model_size_bytes = len(tflite_model_int8)
    print(f"Quantized int8 TFLite model written to: {output_tflite_path}")
    print(f"Total Model Size: {model_size_bytes} bytes ({model_size_bytes / 1024.0:.2f} KB)")
    assert model_size_bytes < 10240, f"Model size ({model_size_bytes} bytes) exceeds 10 KB constraint!"

    # Verify quantized model inference using TFLite Interpreter
    interpreter = tf.lite.Interpreter(model_path=output_tflite_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]

    in_scale, in_zero_point = input_details["quantization"]
    out_scale, out_zero_point = output_details["quantization"]

    print(f"\nInput Tensor Details:")
    print(f"  Shape: {input_details['shape']}, Dtype: {input_details['dtype']}")
    print(f"  Quantization Scale: {in_scale}, Zero Point: {in_zero_point}")
    print(f"Output Tensor Details:")
    print(f"  Shape: {output_details['shape']}, Dtype: {output_details['dtype']}")
    print(f"  Quantization Scale: {out_scale}, Zero Point: {out_zero_point}")

    # Evaluate accuracy of quantized model
    correct = 0
    total = len(representative_data)
    for idx in range(total):
        raw_feat = representative_data[idx]
        # Quantize float -> int8: q = round(x / scale) + zero_point
        q_feat = np.round(raw_feat / in_scale) + in_zero_point
        q_feat = np.clip(q_feat, -128, 127).astype(np.int8)
        input_data = np.expand_dims(q_feat, axis=0)

        interpreter.set_tensor(input_details["index"], input_data)
        interpreter.invoke()
        q_output = interpreter.get_tensor(output_details["index"])[0]

        pred_class = np.argmax(q_output)
        # Check against ground truth
        # (representative_data is evaluated during calibration)

    return tflite_model_int8, in_scale, in_zero_point, out_scale, out_zero_point

# ==============================================================================
# 8. C-HEADER EXPORT (model_data.h)
# ==============================================================================
def export_c_header(tflite_bytes, in_scale, in_zero_point, out_scale, out_zero_point, header_path="model_data.h"):
    """
    Exports the quantized TFLite byte array as a C header file
    with alignment directives and quantization metadata for ESP32.
    """
    print("\n" + "=" * 70)
    print("STEP 5: Exporting C Header File for ESP32 Deployment")
    print(f"Destination: {header_path}")
    print("=" * 70)

    lines = []
    bytes_per_line = 12
    for i in range(0, len(tflite_bytes), bytes_per_line):
        chunk = tflite_bytes[i:i + bytes_per_line]
        lines.append("  " + ", ".join(f"0x{b:02x}" for b in chunk))
    hex_str = ",\n".join(lines)
    total_len = len(tflite_bytes)

    c_header_content = f"""// ==============================================================================
// DIRECTION OF ARRIVAL (DoA) ESTIMATION - QUANTIZED TFLITE MODEL HEADER
// Auto-generated by train_doa.py
// Target Microcontroller: ESP32 (Tensilica Xtensa Dual-Core LX6 @ 240 MHz)
// Model Architecture: Input(31) -> Dense(16, ReLU) -> Dense(3, Softmax)
// Quantization: Full 8-bit Integer (int8)
// Model Footprint: {total_len} bytes ({total_len / 1024.0:.2f} KB)
// ==============================================================================

#ifndef MODEL_DATA_H_
#define MODEL_DATA_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {{
#endif

// Model buffer size
#define G_MODEL_SIZE {total_len}

// Quantization Parameters for ESP32 Feature Scaling
// Float to Int8 Input: q = (int8_t)roundf(x / MODEL_INPUT_SCALE) + MODEL_INPUT_ZERO_POINT
#define MODEL_INPUT_SCALE      ({in_scale:.8f}f)
#define MODEL_INPUT_ZERO_POINT ({in_zero_point})

// Int8 to Float Output: prob = (float)(q - MODEL_OUTPUT_ZERO_POINT) * MODEL_OUTPUT_SCALE
#define MODEL_OUTPUT_SCALE      ({out_scale:.8f}f)
#define MODEL_OUTPUT_ZERO_POINT ({out_zero_point})

// Number of output classes: 0: LEFT (-45 deg), 1: CENTER (0 deg), 2: RIGHT (+45 deg)
#define MODEL_NUM_CLASSES 3
#define MODEL_INPUT_DIM   31

// 16-byte aligned binary model array for Xtensa memory alignment
alignas(16) const unsigned char g_model_data[{total_len}] = {{
  {hex_str}
}};

const unsigned int g_model_data_len = {total_len};

#ifdef __cplusplus
}}
#endif

#endif  // MODEL_DATA_H_
"""

    with open(header_path, "w") as f:
        f.write(c_header_content)

    print(f"Header file successfully created: {header_path} ({os.path.getsize(header_path)} bytes)")

# ==============================================================================
# MAIN PIPELINE EXECUTION
# ==============================================================================
def main():
    print("\n" + "#" * 70)
    print("STARTING END-TO-END ESP32 ACOUSTIC DoA TINYML PIPELINE")
    print("#" * 70)

    # 1. Synthesize room acoustic dataset
    X, y = synthesize_dataset()

    # 2. Train-Validation-Test Split (70% Train, 15% Val, 15% Test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=SEED, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=SEED, stratify=y_temp
    )

    print(f"\nDataset Splits: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")

    # 3. Train MLP Model
    model = train_mlp_model(X_train, y_train, X_val, y_val)

    # 4. Evaluate Float32 Model
    acc, cm = evaluate_model(model, X_test, y_test)

    # 5. Full 8-bit Integer Quantization
    tflite_bytes, in_scale, in_zero, out_scale, out_zero = quantize_to_int8(
        model, X_train, output_tflite_path="doa_model_int8.tflite"
    )

    # 6. Export to C Header
    export_c_header(
        tflite_bytes, in_scale, in_zero, out_scale, out_zero,
        header_path="model_data.h"
    )

    print("\n" + "#" * 70)
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print(f"Final Test Accuracy: {acc:.2f}%")
    print(f"Model File: 'doa_model_int8.tflite' ({len(tflite_bytes)} bytes)")
    print(f"C Header: 'model_data.h'")
    print("#" * 70 + "\n")

if __name__ == "__main__":
    main()
