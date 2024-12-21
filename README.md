# Accelerated-DTMF-Transmission

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

1. Clone the repository:
   ```bash
   git clone https://github.com/rabbyt3s/Accelerated-DTMF-Transmission.git
   cd Accelerated-DTMF-Transmission

2. Install depencencies:
   ```bash
   pip install numpy scipy matplotlib soundfile sounddevice

