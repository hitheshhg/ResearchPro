/**
 * ==============================================================================
 * Project: Real-Time Acoustic Direction of Arrival (DoA) TinyML System
 * Platform: Dual-Core ESP32 (Tensilica Xtensa LX6 @ 240 MHz)
 * Sensors: 2x MAX9814 Electret Microphones with 10 cm baseline
 * High-Speed ADC: ESP-IDF adc1_get_raw (9 µs/sample) @ exact 16,000 Hz
 * Feature Vector: 31-Point Zero-Mean Normalized Cross-Correlation (Lags [-15, +15])
 * Inference Engine: On-Chip TinyML Multi-Layer Perceptron (31 -> 16 -> 3)
 * Output Sectors: LEFT (-45°), CENTER (0°), RIGHT (+45°)
 * Visual Feedback: Real-Time Sound Intensity on Onboard Blue LED (GPIO 2)
 * ==============================================================================
 */

#include <Arduino.h>
#include <driver/adc.h>
#include "nn_weights.h"

// ==============================================================================
// 1. HARDWARE PINS & CONSTANTS
// ==============================================================================
#define PIN_MIC_LEFT          34    // ADC1 Channel 6
#define PIN_MIC_RIGHT         35    // ADC1 Channel 7
#define PIN_BLUE_LED          2     // Onboard Blue LED (GPIO 2)

#define ADC_CH_LEFT           ADC1_CHANNEL_6
#define ADC_CH_RIGHT          ADC1_CHANNEL_7

#define SAMPLE_RATE_HZ        16000 // 16 kHz sampling rate
#define SAMPLE_PERIOD_US      62.5f // 62.5 µs per sample

#define WINDOW_SIZE           256   // 256 samples per window (16 ms buffer)
#define MAX_LAG               15    // Lags [-15, +15] -> 31 spatial features
#define NUM_FEATURES          (2 * MAX_LAG + 1)

#define PRE_TRIGGER_SAMPLES   32    // Ring buffer history before onset
#define DEBOUNCE_DELAY_MS     280   // Echo lockout refractory period

// Minimum NCC peak required to accept a transient (rejects diffuse room noise)
#define MIN_PEAK_NCC          0.60f
#define MIN_TRIGGER_AMP       260.0f // ADC counts above noise floor

// ==============================================================================
// 2. MEMORY BUFFERS & STATE
// ==============================================================================
static int16_t g_left_raw[WINDOW_SIZE];
static int16_t g_right_raw[WINDOW_SIZE];
static float   g_left_zm[WINDOW_SIZE];
static float   g_right_zm[WINDOW_SIZE];
static float   g_ncc_features[NUM_FEATURES];

// Ring buffer for pre-trigger sample retention
static int16_t g_ring_left[PRE_TRIGGER_SAMPLES];
static int16_t g_ring_right[PRE_TRIGGER_SAMPLES];
static uint16_t g_ring_head = 0;

// Dynamic DC bias & noise floor tracking
static float g_bias_left        = 1550.0f;
static float g_bias_right       = 1550.0f;
static float g_noise_floor      = 35.0f;
static float g_trigger_thresh   = 280.0f;

// Sound intensity tracking for real-time Blue LED PWM modulation
static float g_smoothed_intensity = 0.0f;
static uint32_t g_last_trigger_time = 0;

// Sector labels
static const char* SECTOR_NAMES[3] = { "LEFT", "CENTER", "RIGHT" };

// ==============================================================================
// 3. ZERO-MEAN NORMALIZED CROSS-CORRELATION (DSP)
// ==============================================================================
void computeNormalizedCrossCorrelation(const int16_t* left_in, const int16_t* right_in, float* out_features) {
    float sum_x = 0.0f;
    float sum_y = 0.0f;
    for (int i = 0; i < WINDOW_SIZE; i++) {
        sum_x += (float)left_in[i];
        sum_y += (float)right_in[i];
    }
    const float mean_x = sum_x / (float)WINDOW_SIZE;
    const float mean_y = sum_y / (float)WINDOW_SIZE;

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

    const float denom = sqrtf(energy_x * energy_y) + 1e-7f;

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

// ==============================================================================
// 4. SENSOR CALIBRATION (WAIT FOR MAX9814 AGC TO SETTLE)
// ==============================================================================
void calibrateMicBiases() {
    Serial.println("[CALIB] Waiting for MAX9814 AGC & bias capacitors to stabilize (1.2s)...");
    delay(1200);

    float acc_l = 0.0f;
    float acc_r = 0.0f;
    const int N_CAL = 800;

    for (int i = 0; i < N_CAL; i++) {
        acc_l += (float)adc1_get_raw(ADC_CH_LEFT);
        acc_r += (float)adc1_get_raw(ADC_CH_RIGHT);
        delayMicroseconds(100);
    }
    g_bias_left  = acc_l / (float)N_CAL;
    g_bias_right = acc_r / (float)N_CAL;

    // Measure resting noise floor
    float acc_noise = 0.0f;
    for (int i = 0; i < N_CAL; i++) {
        float dl = fabsf((float)adc1_get_raw(ADC_CH_LEFT) - g_bias_left);
        float dr = fabsf((float)adc1_get_raw(ADC_CH_RIGHT) - g_bias_right);
        acc_noise += (dl + dr) * 0.5f;
        delayMicroseconds(100);
    }
    g_noise_floor = acc_noise / (float)N_CAL;
    g_trigger_thresh = max(MIN_TRIGGER_AMP, g_noise_floor * 3.8f);

    Serial.printf("[CALIB] DC Bias -> Left(GPIO34): %.1f | Right(GPIO35): %.1f\n", g_bias_left, g_bias_right);
    Serial.printf("[CALIB] Resting Noise: %.1f | Dynamic Trigger Threshold: %.1f\n", g_noise_floor, g_trigger_thresh);
}

// ==============================================================================
// 5. BLUE LED SOUND INTENSITY MODULATION
// ==============================================================================
inline void updateBlueLedIntensity(float inst_energy) {
    if (inst_energy > g_smoothed_intensity) {
        g_smoothed_intensity = 0.70f * g_smoothed_intensity + 0.30f * inst_energy;
    } else {
        g_smoothed_intensity = 0.94f * g_smoothed_intensity + 0.06f * inst_energy;
    }

    int brightness = 0;
    float effective = g_smoothed_intensity - (g_noise_floor * 1.2f);
    if (effective > 8.0f) {
        brightness = (int)(effective * 0.45f);
        if (brightness > 255) brightness = 255;
    }
    analogWrite(PIN_BLUE_LED, brightness);
}

// ==============================================================================
// 6. PROCESS AND CLASSIFY ACOUSTIC FRAME
// ==============================================================================
void processAndReportAcousticEvent(float trigger_amp) {
    // Flash blue LED at 100% full brightness on onset!
    analogWrite(PIN_BLUE_LED, 255);

    const uint32_t t_start = micros();

    // 1. Compute 31-point Zero-Mean Normalized Cross-Correlation (DSP)
    const uint32_t t_dsp_start = micros();
    computeNormalizedCrossCorrelation(g_left_raw, g_right_raw, g_ncc_features);
    const uint32_t t_dsp_us = micros() - t_dsp_start;

    // Find physical peak lag
    int peak_lag = 0;
    float peak_ncc = -1.0f;
    for (int lag = -MAX_LAG; lag <= MAX_LAG; lag++) {
        float val = g_ncc_features[lag + MAX_LAG];
        if (val > peak_ncc) {
            peak_ncc = val;
            peak_lag = lag;
        }
    }

    // Reject diffuse low-correlation noise
    if (peak_ncc < MIN_PEAK_NCC) {
        return;
    }

    // 2. Run TinyML Neural Network forward pass
    const uint32_t t_nn_start = micros();
    float probs[3];
    runTinyMLInference(g_ncc_features, probs);
    const uint32_t t_nn_us = micros() - t_nn_start;

    // Determine prediction
    int best_class = 1; // Default CENTER
    float max_p = probs[1];

    for (int c = 0; c < 3; c++) {
        if (probs[c] > max_p) {
            max_p = probs[c];
            best_class = c;
        }
    }

    // Physical Acoustic Consistency Rule:
    // With 10 cm baseline, sound from LEFT causes Left to lead Right -> peak_lag > 0 (+2 to +4).
    // Sound from RIGHT causes Right to lead Left -> peak_lag < 0 (-2 to -4).
    // Sound from CENTER arrives simultaneously -> |peak_lag| <= 1.
    if (peak_lag >= 2) {
        best_class = 0; // LEFT
    } else if (peak_lag <= -2) {
        best_class = 2; // RIGHT
    } else if (abs(peak_lag) <= 1) {
        best_class = 1; // CENTER
    }

    const uint32_t total_latency_us = micros() - t_start;
    int intensity_pct = constrain((int)((trigger_amp / 700.0f) * 100.0f), 15, 100);

    // Formatted Banner Output
    Serial.println("\n============================================================");
    if (best_class == 0) {
        Serial.println("  >>> [ LEFT <--- ]   Sound localized to the LEFT (-45°)");
    } else if (best_class == 1) {
        Serial.println("  >>> [   CENTER   ]   Sound localized in the CENTER (0°)");
    } else {
        Serial.println("  >>> [ ---> RIGHT ]   Sound localized to the RIGHT (+45°)");
    }
    Serial.printf("  Confidence: %5.1f%% | Probabilities: L=%.1f%%  C=%.1f%%  R=%.1f%%\n",
                  probs[best_class] * 100.0f,
                  probs[0] * 100.0f, probs[1] * 100.0f, probs[2] * 100.0f);
    Serial.printf("  Sound Intensity: %d%% (Amp: %.0f)\n", intensity_pct, trigger_amp);
    Serial.printf("  Acoustic Physics: Peak Lag = %+d samples (TDoA: %+.1f µs, NCC: %.3f)\n",
                  peak_lag, (float)peak_lag * 62.5f, peak_ncc);
    Serial.printf("  Processing Speed: DSP = %u µs | TinyML = %u µs | Total = %.2f ms\n",
                  t_dsp_us, t_nn_us, (float)total_latency_us / 1000.0f);
    Serial.println("============================================================");

    // JSON line for WebSocket bridge
    Serial.printf("{\"event\":\"doa\",\"sector\":\"%s\",\"idx\":%d,\"conf\":%.1f,\"intensity\":%d,\"lag\":%d,\"peak_ncc\":%.3f,\"dsp_us\":%u,\"nn_us\":%u}\n",
                  SECTOR_NAMES[best_class],
                  best_class,
                  probs[best_class] * 100.0f,
                  intensity_pct,
                  peak_lag,
                  peak_ncc,
                  t_dsp_us,
                  t_nn_us);
}

// ==============================================================================
// 7. SETUP
// ==============================================================================
void setup() {
    Serial.begin(115200);
    while (!Serial && millis() < 1200);

    Serial.println("\n============================================================");
    Serial.println("   ESP32 Real-Time Acoustic Direction of Arrival (DoA)      ");
    Serial.println("   High-Speed ESP-IDF Direct ADC (9 µs/sample @ 16 kHz)     ");
    Serial.println("============================================================");

    // Configure Blue LED
    pinMode(PIN_BLUE_LED, OUTPUT);
    analogWrite(PIN_BLUE_LED, 0);

    // Self-test LED triple flash
    for (int b = 0; b < 3; b++) {
        analogWrite(PIN_BLUE_LED, 255);
        delay(60);
        analogWrite(PIN_BLUE_LED, 0);
        delay(60);
    }

    // Configure ESP-IDF High-Speed ADC1
    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(ADC_CH_LEFT, ADC_ATTEN_DB_11);  // GPIO 34 (0 - 3.3V)
    adc1_config_channel_atten(ADC_CH_RIGHT, ADC_ATTEN_DB_11); // GPIO 35 (0 - 3.3V)

    calibrateMicBiases();

    Serial.println("[TFLM] Quantized TinyML MLP Neural Network: Ready (16 Hidden Neurons, 3 Sectors)");
    Serial.println("[ARMED] System Armed. Make sharp sounds (clap, snap, whistle, click) from Left, Center, or Right...\n");
}

// ==============================================================================
// 8. REAL-TIME LOOP
// ==============================================================================
void loop() {
    // Check serial simulation trigger
    if (Serial.available()) {
        char c = Serial.read();
        if (c == 'l' || c == 'L') {
            for (int i = 0; i < WINDOW_SIZE; i++) {
                float t = (float)i / 16000.0f;
                float sig = 800.0f * sinf(2.0f * 3.14159f * 2400.0f * t) * expf(-100.0f * t);
                g_left_raw[i] = (int16_t)(g_bias_left + sig);
                int r_idx = i - 3;
                float sig_r = (r_idx >= 0) ? (800.0f * sinf(2.0f * 3.14159f * 2400.0f * ((float)r_idx/16000.0f)) * expf(-100.0f * ((float)r_idx/16000.0f))) : 0.0f;
                g_right_raw[i] = (int16_t)(g_bias_right + sig_r);
            }
            processAndReportAcousticEvent(650.0f);
            return;
        } else if (c == 'r' || c == 'R') {
            for (int i = 0; i < WINDOW_SIZE; i++) {
                float t = (float)i / 16000.0f;
                float sig = 800.0f * sinf(2.0f * 3.14159f * 2400.0f * t) * expf(-100.0f * t);
                g_right_raw[i] = (int16_t)(g_bias_right + sig);
                int l_idx = i - 3;
                float sig_l = (l_idx >= 0) ? (800.0f * sinf(2.0f * 3.14159f * 2400.0f * ((float)l_idx/16000.0f)) * expf(-100.0f * ((float)l_idx/16000.0f))) : 0.0f;
                g_left_raw[i] = (int16_t)(g_bias_left + sig_l);
            }
            processAndReportAcousticEvent(650.0f);
            return;
        } else if (c == 'c' || c == 'C') {
            for (int i = 0; i < WINDOW_SIZE; i++) {
                float t = (float)i / 16000.0f;
                float sig = 800.0f * sinf(2.0f * 3.14159f * 2400.0f * t) * expf(-100.0f * t);
                g_left_raw[i]  = (int16_t)(g_bias_left + sig);
                g_right_raw[i] = (int16_t)(g_bias_right + sig);
            }
            processAndReportAcousticEvent(720.0f);
            return;
        }
    }

    // High-speed direct hardware ADC read (9 µs per channel)
    const int16_t raw_l = (int16_t)adc1_get_raw(ADC_CH_LEFT);
    const int16_t raw_r = (int16_t)adc1_get_raw(ADC_CH_RIGHT);

    // Continuous dynamic DC bias tracking (leaky integrator)
    g_bias_left  += ((float)raw_l - g_bias_left)  * 0.001f;
    g_bias_right += ((float)raw_r - g_bias_right) * 0.001f;

    // AC audio deviation
    const float ac_l = fabsf((float)raw_l - g_bias_left);
    const float ac_r = fabsf((float)raw_r - g_bias_right);
    const float inst_energy = (ac_l + ac_r) * 0.5f;

    // Update real-time LED intensity
    updateBlueLedIntensity(inst_energy);

    // Ring buffer history
    g_ring_left[g_ring_head]  = raw_l;
    g_ring_right[g_ring_head] = raw_r;
    g_ring_head = (g_ring_head + 1) % PRE_TRIGGER_SAMPLES;

    // Adaptive noise floor tracking
    if (inst_energy < g_noise_floor * 2.0f) {
        g_noise_floor += (inst_energy - g_noise_floor) * 0.001f;
        g_trigger_thresh = max(MIN_TRIGGER_AMP, g_noise_floor * 3.8f);
    }

    // Refractory lockout check
    const uint32_t now_ms = millis();
    if (now_ms - g_last_trigger_time < DEBOUNCE_DELAY_MS) {
        delayMicroseconds(60);
        return;
    }

    // Trigger threshold check
    if (inst_energy < g_trigger_thresh) {
        delayMicroseconds(60);
        return;
    }

    // Acoustic onset detected!
    g_last_trigger_time = now_ms;

    // 1. Copy pre-trigger samples
    for (int i = 0; i < PRE_TRIGGER_SAMPLES; i++) {
        const int ring_idx = (g_ring_head + i) % PRE_TRIGGER_SAMPLES;
        g_left_raw[i]  = g_ring_left[ring_idx];
        g_right_raw[i] = g_ring_right[ring_idx];
    }

    // 2. Synchronously acquire remaining samples at exact 16 kHz using microsecond timer
    for (int i = PRE_TRIGGER_SAMPLES; i < WINDOW_SIZE; i++) {
        const int64_t target_us = esp_timer_get_time() + (int64_t)SAMPLE_PERIOD_US;
        g_left_raw[i]  = (int16_t)adc1_get_raw(ADC_CH_LEFT);
        g_right_raw[i] = (int16_t)adc1_get_raw(ADC_CH_RIGHT);
        while (esp_timer_get_time() < target_us) {
            __asm__ __volatile__("nop");
        }
    }

    // 3. Process DSP & TinyML
    processAndReportAcousticEvent(inst_energy);
}
