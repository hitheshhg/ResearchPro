/**
 * Verification and Benchmarking Test Harness for ESP32 DSP Routine
 * Tests:
 * 1. Mathematical validity of 31-point Normalized Cross-Correlation (NCC)
 * 2. Peak lag location for simulated Left (-45 deg), Center (0 deg), Right (+45 deg)
 * 3. Exact CPU execution latency / MAC performance
 */

#include <iostream>
#include <cmath>
#include <chrono>
#include <algorithm>
#include <vector>
#include <cassert>
#include <iomanip>

#define WINDOW_SIZE 256
#define MAX_LAG 15
#define NUM_FEATURES (2 * MAX_LAG + 1)

static float g_left_zm[WINDOW_SIZE];
static float g_right_zm[WINDOW_SIZE];

void computeNormalizedCrossCorrelation(const int16_t* left_in, const int16_t* right_in, float* out_features) {
    // Step 1: Compute means
    float sum_x = 0.0f;
    float sum_y = 0.0f;
    for (int i = 0; i < WINDOW_SIZE; i++) {
        sum_x += (float)left_in[i];
        sum_y += (float)right_in[i];
    }
    const float mean_x = sum_x / (float)WINDOW_SIZE;
    const float mean_y = sum_y / (float)WINDOW_SIZE;

    // Step 2: Zero-mean subtraction and sum of squares
    float energy_x = 0.0f;
    float energy_y = 0.0f;
    for (int i = 0; i < WINDOW_SIZE; i++) {
        const float x_zm = (float)left_in[i] - mean_x;
        const float y_zm = (float)right_in[i] - mean_y;
        g_left_zm[i]  = x_zm;
        g_right_zm[i] = y_zm;
        energy_x += x_zm * x_zm;
        energy_y += y_zm * y_zm;
    }

    const float denom = std::sqrt(energy_x * energy_y) + 1e-7f;

    // Step 3: Compute cross-correlation for lag window [-15, +15]
    for (int lag = -MAX_LAG; lag <= MAX_LAG; lag++) {
        float cross_prod = 0.0f;

        if (lag >= 0) {
            const int count = WINDOW_SIZE - lag;
            const float* p_x = &g_left_zm[0];
            const float* p_y = &g_right_zm[lag];
            int n = 0;
            for (; n <= count - 4; n += 4) {
                cross_prod += p_x[n]     * p_y[n]
                            + p_x[n + 1] * p_y[n + 1]
                            + p_x[n + 2] * p_y[n + 2]
                            + p_x[n + 3] * p_y[n + 3];
            }
            for (; n < count; n++) {
                cross_prod += p_x[n] * p_y[n];
            }
        } else {
            const int k_pos = -lag;
            const int count = WINDOW_SIZE - k_pos;
            const float* p_x = &g_left_zm[k_pos];
            const float* p_y = &g_right_zm[0];
            int n = 0;
            for (; n <= count - 4; n += 4) {
                cross_prod += p_x[n]     * p_y[n]
                            + p_x[n + 1] * p_y[n + 1]
                            + p_x[n + 2] * p_y[n + 2]
                            + p_x[n + 3] * p_y[n + 3];
            }
            for (; n < count; n++) {
                cross_prod += p_x[n] * p_y[n];
            }
        }
        out_features[lag + MAX_LAG] = cross_prod / denom;
    }
}

int main() {
    std::cout << "======================================================\n";
    std::cout << "Testing DSP Routine: 31-Point Normalized Cross-Correlation\n";
    std::cout << "======================================================\n";

    int16_t sig_left[WINDOW_SIZE];
    int16_t sig_right[WINDOW_SIZE];
    float features[NUM_FEATURES];

    // Generate test acoustic transient: damped sine wave
    auto generate_test_signals = [&](int lag_delay) {
        for (int i = 0; i < WINDOW_SIZE; i++) {
            float t = (float)i / 16000.0f;
            float val = 1000.0f * std::sin(2.0f * M_PI * 2500.0f * t) * std::exp(-80.0f * t);
            sig_left[i] = (int16_t)(1550 + val); // with 1.25V DC bias
            sig_right[i] = 1550;
        }
        for (int i = 0; i < WINDOW_SIZE; i++) {
            int src_idx = i - lag_delay;
            if (src_idx >= 0 && src_idx < WINDOW_SIZE) {
                float t = (float)src_idx / 16000.0f;
                float val = 1000.0f * std::sin(2.0f * M_PI * 2500.0f * t) * std::exp(-80.0f * t);
                sig_right[i] = (int16_t)(1550 + val);
            }
        }
    };

    // Test 1: Zero Lag (CENTER 0 deg)
    generate_test_signals(0);
    computeNormalizedCrossCorrelation(sig_left, sig_right, features);
    int peak_lag = -MAX_LAG + (std::max_element(features, features + NUM_FEATURES) - features);
    std::cout << "[Test 1: CENTER] Injected Delay = 0 samples -> Detected Peak Lag = "
              << peak_lag << " (NCC = " << features[peak_lag + MAX_LAG] << ") -> "
              << (peak_lag == 0 ? "PASSED [OK]" : "FAILED") << "\n";

    // Test 2: Right Delay = +3 samples (RIGHT +45 deg nominal delay is ~ +3.3 samples)
    generate_test_signals(3);
    computeNormalizedCrossCorrelation(sig_left, sig_right, features);
    peak_lag = -MAX_LAG + (std::max_element(features, features + NUM_FEATURES) - features);
    std::cout << "[Test 2: RIGHT ] Injected Delay = +3 samples -> Detected Peak Lag = "
              << peak_lag << " (NCC = " << features[peak_lag + MAX_LAG] << ") -> "
              << (peak_lag == 3 ? "PASSED [OK]" : "FAILED") << "\n";

    // Test 3: Left Delay = -3 samples (LEFT -45 deg nominal delay is ~ -3.3 samples)
    generate_test_signals(-3);
    computeNormalizedCrossCorrelation(sig_left, sig_right, features);
    peak_lag = -MAX_LAG + (std::max_element(features, features + NUM_FEATURES) - features);
    std::cout << "[Test 3: LEFT  ] Injected Delay = -3 samples -> Detected Peak Lag = "
              << peak_lag << " (NCC = " << features[peak_lag + MAX_LAG] << ") -> "
              << (peak_lag == -3 ? "PASSED [OK]" : "FAILED") << "\n";

    // Performance Benchmarking: 10,000 iterations
    std::cout << "\nBenchmarking DSP throughput over 10,000 runs...\n";
    const int N_RUNS = 10000;
    auto t1 = std::chrono::high_resolution_clock::now();
    for (int r = 0; r < N_RUNS; r++) {
        computeNormalizedCrossCorrelation(sig_left, sig_right, features);
    }
    auto t2 = std::chrono::high_resolution_clock::now();
    double total_us = std::chrono::duration<double, std::micro>(t2 - t1).count();
    double avg_us = total_us / N_RUNS;

    std::cout << "Mean DSP Execution Time: " << std::fixed << std::setprecision(2)
              << avg_us << " microseconds (" << avg_us / 1000.0 << " ms)\n";
    std::cout << "Peak Feature Extraction Throughput: " << (1e6 / avg_us) << " inferences/sec\n";
    std::cout << "======================================================\n";

    return 0;
}
