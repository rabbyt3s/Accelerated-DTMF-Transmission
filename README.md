# Accelerated DTMF Transmission

**Author**: [Yassine TAMANI](https://github.com/rabbyt3s)  
**Repository**: [Accelerated-DTMF-Transmission](https://github.com/rabbyt3s/Accelerated-DTMF-Transmission)  

---

## Overview
This repository is an experimental project demonstrating the encoding, time-compression (acceleration), and decoding of messages using **extended DTMF (Dual-Tone Multi-Frequency)** signals. The process includes:

1. **Encoding**: Convert text into a sequence of dual-tone frequencies.  
2. **Time-compression**: Accelerate the audio by a specified factor using proper decimation with internal lowpass filtering.  
3. **Restoration**: Slow down the compressed audio using interpolation with lowpass filtering to reconstruct the original duration.  
4. **Decoding**: Recover the original text by analyzing frequencies and mapping them back to characters.

The goal is to transmit audio-encoded data in extremely short bursts while preserving its decodability upon playback.

---

## Features
1. **Custom Extended DTMF**: Supports characters beyond traditional DTMF (A-Z, 0-9, etc.).  
2. **Time-compression with `resample_poly`**: Ensures proper filtering during decimation and interpolation for high-quality restoration.  
3. **Live Decoder**: Captures and decodes DTMF tones from a microphone in real-time.  
4. **Menu-driven interface**: Easily encode, decode, accelerate, and slow down audio files.

---

## Installation

1. **Clone** the repository:
   ```bash
   git clone https://github.com/rabbyt3s/Accelerated-DTMF-Transmission.git
   cd Accelerated-DTMF-Transmission
   ```

2. **Install dependencies**:
   ```bash
   pip install numpy scipy matplotlib soundfile sounddevice
   ```

---

## How It Works

### Encoding
- Input a text phrase (e.g., `"HELLO WORLD"`) and generate a WAV file using custom low and high DTMF frequencies.

### Time-Compression (Speed-Up)
- Compress the encoded file by a factor \(M\) (e.g., 10×) using proper decimation.  
- This reduces the file's duration to \(1/M\) of its original length.

### Restoration (Slow-Down)
- Restore the compressed file to its original duration via interpolation, making it decodable.

### Decoding
- Analyze the frequencies (via FFT) to extract the characters.

---

## Example Usage

### 1. Encode a Phrase
Run the main script and choose the **encode** option:
```bash
python dtmf_all_in_one.py
```
Enter your phrase (e.g., `"HELLO WORLD"`), and it will generate an encoded WAV file.

### 2. Accelerate the File
Choose the **acceleration** option and specify a factor (e.g., 10×):
```bash
python dtmf_all_in_one.py
```

### 3. Decode the Restored File
After slowing down the accelerated file, decode the tones to retrieve the original text.

---

## Technical Details

### Key Components
- **DTMF Encoding**: Each character is represented by a combination of one low and one high frequency (customized beyond standard DTMF).
- **Time Compression**:
  - Uses `scipy.signal.resample_poly` for:
    - **Decimation (speed-up)**: `up=1, down=M`
    - **Interpolation (slow-down)**: `up=M, down=1`  
  - This ensures aliasing and imaging artifacts are minimized.
- **Decoding**: Block-based FFT detects peaks near the predefined frequencies.

### Extended DTMF Frequencies
- **Low**: `[697, 770, 852, 941, 1033, 1125, 1218]`  
- **High**: `[1336, 1477, 1633, 1785, 1944]`  

Matrix for mapping characters:
```css
['A', 'B', 'C', 'D', 'E']
['F', 'G', 'H', 'I', 'J']
['K', 'L', 'M', 'N', 'O']
['P', 'Q', 'R', 'S', 'T']
['U', 'V', 'W', 'X', 'Y']
['Z', '0', '1', '2', '3']
['4', '5', '6', '7', '8']
```

---

## Live Decoder
Run the live decoder to capture tones via microphone:
```bash
python dtmf_all_in_one.py
```
Play the generated WAV file through speakers, and the system will decode the tones into text.

---

## Limitations
- Effective for compression factors up to ~10×.  
- Minor errors (e.g., duplicated characters) may occur in restored files.  
- Large compression factors (>10×) require more advanced time-stretching techniques (e.g., WSOLA, phase vocoder).

---

## Future Improvements
1. **Error Correction**: Add redundancy (e.g., checksums) to improve decoding accuracy.  
2. **Dynamic Frequencies**: Let users define frequency ranges for specific applications.  
3. **Robust Decoding**: Incorporate cross-correlation or matched filters for higher reliability.

---

## Author
**Yassine TAMANI**  
GitHub: [rabbyt3s](https://github.com/rabbyt3s)

Feel free to fork the repository, report issues, or suggest improvements!

---

## References
- **Alan V. Oppenheim, Ronald W. Schafer.** _Discrete-Time Signal Processing_, 3rd Edition, Prentice Hall, 2009.  
- **[SciPy Documentation on `resample_poly`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html)**
