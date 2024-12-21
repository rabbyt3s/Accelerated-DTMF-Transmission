import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
import sounddevice as sd
from scipy.signal import find_peaks, butter, filtfilt, get_window, resample_poly
import queue
import threading
from datetime import datetime

# Frequencies used for DTMF encoding/decoding
FREQS_LOW = [697, 770, 852, 941, 1033, 1125, 1218]
FREQS_HIGH = [1336, 1477, 1633, 1785, 1944]

# Character matrix mapping frequencies to symbols
EXTENDED_MATRIX = [
    ['A', 'B', 'C', 'D', 'E'],
    ['F', 'G', 'H', 'I', 'J'],
    ['K', 'L', 'M', 'N', 'O'],
    ['P', 'Q', 'R', 'S', 'T'],
    ['U', 'V', 'W', 'X', 'Y'],
    ['Z', '0', '1', '2', '3'],
    ['4', '5', '6', '7', '8']
]

def find_frequencies(char):
    for i, row in enumerate(EXTENDED_MATRIX):
        if char in row:
            return FREQS_LOW[i], FREQS_HIGH[row.index(char)]
    return None

def generate_tone(char, duration=0.2, sample_rate=44100):
    # Generates a DTMF tone by combining two sine waves at specific frequencies
    freqs = find_frequencies(char)
    if not freqs:
        return np.zeros(int(sample_rate * duration))

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    sig_low = np.sin(2 * np.pi * freqs[0] * t)
    sig_high = np.sin(2 * np.pi * freqs[1] * t)
    signal = 0.5 * sig_low + 0.5 * sig_high

    # Apply fade in/out to avoid clicks
    fade_len = int(sample_rate * 0.01)
    if fade_len > 0 and len(signal) > 2*fade_len:
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = fade_in[::-1]
        signal[:fade_len] *= fade_in
        signal[-fade_len:] *= fade_out

    # Normalize amplitude
    max_amp = np.max(np.abs(signal)) + 1e-9
    signal /= max_amp
    return signal

def encode_phrase(phrase, output_wav="encoded_phrase.wav",
                  char_duration=0.15, gap_duration=0.3):
    # Converts text to DTMF audio by generating tones for each character
    sr = 44100
    signals = []
    gap = np.zeros(int(sr * gap_duration))

    for char in phrase.upper():
        if char.isspace():
            signals.append(gap)
        else:
            tone = generate_tone(char, duration=char_duration, sample_rate=sr)
            signals.append(tone)
            signals.append(gap)

    final_signal = np.concatenate(signals)
    final_signal /= (np.max(np.abs(final_signal)) + 1e-9)

    sf.write(output_wav, final_signal, sr)
    print(f"[ENCODE] Phrase encoded into '{output_wav}'")

# Matrix used for decoding matches encoding matrix
DTMF_MATRIX = EXTENDED_MATRIX

def butter_bandpass(lowcut, highcut, fs, order=5):
    # Creates a Butterworth bandpass filter
    from scipy.signal import butter
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

class LiveDecoder:
    # Real-time DTMF decoder using microphone input
    def __init__(self):
        self.sample_rate = 44100
        self.chunk_duration = 0.1
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        self.audio_queue = queue.Queue()
        self.running = False

        self.last_detection_time = datetime.now()
        self.min_gap = 0.25
        self.decoded_chars = []

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.audio_queue.put(indata.copy())

    def process_audio(self):
        while self.running:
            try:
                chunk = self.audio_queue.get().flatten()
                if np.max(np.abs(chunk)) < 0.01:
                    continue

                # Filter and process audio chunk
                b, a = butter_bandpass(600, 2000, self.sample_rate)
                filtered_chunk = filtfilt(b, a, chunk)

                window = np.hanning(len(filtered_chunk))
                windowed = filtered_chunk * window
                fft_result = np.abs(np.fft.fft(windowed))
                freqs = np.fft.fftfreq(len(windowed), 1/self.sample_rate)

                pos_mask = freqs > 0
                freqs = freqs[pos_mask]
                fft_result = fft_result[pos_mask]

                # Detect frequency peaks
                peaks, props = find_peaks(fft_result,
                                          height=np.max(fft_result)*0.2,
                                          distance=30,
                                          prominence=0.1)

                detected_freqs = freqs[peaks]
                peak_heights = props['peak_heights']

                # Match detected frequencies to DTMF tones
                low_candidates = []
                high_candidates = []
                tol = 40

                for freq_val, amp_val in zip(detected_freqs, peak_heights):
                    for i, f_l in enumerate(FREQS_LOW):
                        if abs(freq_val - f_l) < tol:
                            low_candidates.append((i, amp_val))
                    for j, f_h in enumerate(FREQS_HIGH):
                        if abs(freq_val - f_h) < tol:
                            high_candidates.append((j, amp_val))

                # Validate and decode detected frequencies
                if len(low_candidates) == 1 and len(high_candidates) == 1:
                    low_idx, low_amp = low_candidates[0]
                    high_idx, high_amp = high_candidates[0]

                    ratio_amp = min(low_amp, high_amp) / max(low_amp, high_amp)
                    if ratio_amp > 0.2:
                        current_time = datetime.now()
                        dt = (current_time - self.last_detection_time).total_seconds()
                        if dt >= self.min_gap:
                            detected_char = DTMF_MATRIX[low_idx][high_idx]
                            self.decoded_chars.append(detected_char)
                            self.last_detection_time = current_time
                            print(f"Detected char: {detected_char}")
                            print("Text so far:", "".join(self.decoded_chars))
            except queue.Empty:
                continue

    def start_listening(self):
        self.running = True
        self.decoded_chars = []

        processing_thread = threading.Thread(target=self.process_audio)
        processing_thread.start()

        print("Live DTMF decoding started. Press Ctrl+C to stop.")
        try:
            with sd.InputStream(callback=self.audio_callback,
                                channels=1,
                                samplerate=self.sample_rate,
                                blocksize=self.chunk_size):
                while self.running:
                    sd.sleep(100)
        except KeyboardInterrupt:
            print("\nStopping live decoding...")

        self.running = False
        processing_thread.join()
        print("Final decoded text (live):", "".join(self.decoded_chars))

def speedup_signal(signal, factor):
    # Accelerates audio by downsampling with anti-aliasing filter
    fast_signal = resample_poly(signal, up=1, down=factor)
    return fast_signal

def slowdown_signal(signal, factor):
    # Decelerates audio by upsampling with anti-imaging filter
    slow_signal = resample_poly(signal, up=factor, down=1)
    return slow_signal

def test_speed_transform(input_file, speed_factor=10):
    # Tests speed transformation by accelerating then decelerating
    audio, sr = sf.read(input_file)
    if audio.ndim > 1:
        audio = audio[:, 0]

    print(f"[SPEED TEST] Reading '{input_file}' @ {sr} Hz")

    print(f"Accelerating x{speed_factor}...")
    fast = speedup_signal(audio, speed_factor)
    fast_file = f"fast_{input_file}"
    sf.write(fast_file, fast, sr)
    print(f"Fast version saved to {fast_file}")

    print(f"Slowing down x{speed_factor} (to original duration approx.)...")
    restored = slowdown_signal(fast, speed_factor)
    restored_file = f"restored_{input_file}"
    sf.write(restored_file, restored, sr)
    print(f"Restored version saved to {restored_file}")

    # Visualize results
    plt.figure(figsize=(10, 6))
    plt.subplot(311)
    plt.title("Original (first 1000 samples)")
    plt.plot(audio[:1000])

    plt.subplot(312)
    plt.title(f"Accelerated x{speed_factor} (first 1000 samples)")
    plt.plot(fast[:1000])

    plt.subplot(313)
    plt.title("Restored (first 1000 samples)")
    plt.plot(restored[:1000])
    plt.tight_layout()
    plt.show()

    print(f"Original length : {len(audio)} samples")
    print(f"Fast length     : {len(fast)} samples")
    print(f"Restored length : {len(restored)} samples")

    if len(restored) == len(audio):
        diff = np.max(np.abs(audio - restored))
        print(f"Max difference: {diff:.4f}")
    else:
        print("Note: The length differs from the original. Some mismatch is normal.")

def main():
    print("=== DTMF All-In-One ===")
    while True:
        print("\nOptions:")
        print("1) Encode phrase to DTMF (WAV)")
        print("2) Start live DTMF decoder (micro)")
        print("3) Test speed transform (accelerate/decelerate) a WAV file")
        print("4) Slow down an accelerated file")
        print("5) Quit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            phrase = input("Enter the phrase to encode: ")
            out_file = input("Output file (e.g. 'my_encoded.wav') [default=encoded_phrase.wav]: ") or "encoded_phrase.wav"
            encode_phrase(phrase, out_file)
        elif choice == "2":
            print("Starting live DTMF decoder...")
            decoder = LiveDecoder()
            decoder.start_listening()
        elif choice == "3":
            in_file = input("Which WAV file to transform?: ").strip()
            if not in_file:
                print("Invalid file!")
                continue
            fac_str = input("Acceleration factor (integer) [default=10]: ").strip()
            if not fac_str.isdigit():
                fac_str = "10"
            speed_fac = int(fac_str)
            test_speed_transform(in_file, speed_fac)
        elif choice == "4":
            in_file = input("Which WAV file to slow down?: ").strip()
            if not in_file:
                print("Invalid file!")
                continue
            fac_str = input("Slowdown factor (integer) [default=10]: ").strip()
            if not fac_str.isdigit():
                fac_str = "10"
            speed_fac = int(fac_str)
            
            audio, sr = sf.read(in_file)
            if audio.ndim > 1:
                audio = audio[:, 0]
            
            print(f"Slowing down x{speed_fac}...")
            slowed = slowdown_signal(audio, speed_fac)
            slow_file = f"slowed_{in_file}"
            sf.write(slow_file, slowed, sr)
            print(f"Slowed version saved to {slow_file}")
        elif choice == "5":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()
