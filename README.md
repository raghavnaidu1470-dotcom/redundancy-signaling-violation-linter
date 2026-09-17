# Redundancy & Signaling Violation Linter

An automated multimedia cognitive linter for educational and instructional lecture videos, grounded in **Cognitive Load Theory** and **Richard Mayer’s Principles of Multimedia Learning**.

The linter analyzes synchronized audio and video channels to detect pedagogical violations that impede student learning:
- **The Redundancy Principle**: Learners acquire information less effectively when on-screen text and spoken narration duplicate identical verbal content simultaneously without added visual benefit.
- **The Signaling Principle**: Learners benefit when attention is guided by visual cues, highlights, or slide transitions when spoken topics shift.

---

## Architecture Overview

```
                          ┌───────────────────────────┐
                          │   Lecture Video Source    │
                          │ (Local File / Web / URL)  │
                          └─────────────┬─────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
         ┌─────────────────────┐                 ┌─────────────────────┐
         │  Audio Processing   │                 │  Visual Processing  │
         │  (FFmpeg 16kHz PCM) │                 │  (PySceneDetect +   │
         │          │          │                 │ Fixed Cadence Fall) │
         │          ▼          │                 │          │          │
         │   Faster-Whisper    │                 │          ▼          │
         │  (Word Timestamps)  │                 │  Tesseract OCR +    │
         └──────────┬──────────┘                 │ OpenCV Binarization │
                    │                            └──────────┬──────────┘
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │   Temporal Alignment        │
                         │ (5s Synchronized Windows)   │
                         └──────────────┬──────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
       ┌─────────────────────────┐             ┌─────────────────────────┐
       │   Redundancy Detector   │             │   Signaling Detector    │
       │ (Sentence Transformers  │             │ (Un-signaled Thematic   │
       │  paraphrase-MiniLM-L3)  │             │  Shift During Stasis)   │
       └────────────┬────────────┘             └────────────┬────────────┘
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │ Result Consolidation Layer  │
                         │    (data/results/*.json)    │
                         └──────────────┬──────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │   Demonstration Web UI      │
                         │  (HTML5 Click-to-Seek +     │
                         │   HTTP 206 Video Streaming) │
                         └─────────────────────────────┘
```

---

## Installation & Setup

### 1. System Dependencies
This project requires `ffmpeg` (for mono 16 kHz audio extraction) and `tesseract` (for optical character recognition):

- **macOS (Homebrew)**:
  ```bash
  brew install ffmpeg tesseract
  ```
- **Ubuntu / Debian**:
  ```bash
  sudo apt-get update && sudo apt-get install -y ffmpeg tesseract-ocr
  ```

### 2. Python Environment
Install Python dependencies into the local virtual environment:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

---

## Usage

### 1. Interactive Demonstration Web UI
Launch the built-in demo server:

```bash
./.venv/bin/python app/server.py 8080
```
Open **`http://localhost:8080`** in your browser to:
- **Test Pre-analyzed Lectures**: Instant zero-latency inspection of benchmark lectures (`MIT 18.06 Gilbert Strang`, `MIT 18.200 Discrete Math`).
- **Drag & Drop Local Videos**: Drop in any `.mp4`, `.mov`, or `.webm` file from your desktop.
- **Analyze Web URLs**: Paste any YouTube or online video link to download and evaluate on the fly.
- **True Click-to-Seek Playback**: Click any *"Potential Redundancy"* card to immediately seek the video player to that timestamp.

### 2. Batch Processing Pipeline
To batch-process all lecture videos residing in `data/videos/`:

```bash
./.venv/bin/python -m src.batch_pipeline --videos-dir data/videos --model small
```

### 3. Running Results Consolidation CLI
To run redundancy violation detection on a single aligned video:

```bash
./.venv/bin/python -m src.results.build_result "01 [01]"
```

### 4. Running the Test Suite
Run the unit test suite across all modules:

```bash
./.venv/bin/python -m unittest discover tests
```
*(All 32 tests pass in < 0.1s without external network dependencies).*

---

## Empirical Evaluation Results

All metrics are micro-aggregated precision, recall, and $F_1$ evaluated against ground-truth human annotations following the interval criteria in `data/ground_truth/LABELING_GUIDE.md`.

### Development Set Threshold Sweep (4 Lecture Samples, 19 Redundant Intervals)

| Embedding Threshold | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: |
| 0.10 | 0.1169 | 0.4737 | 0.1875 |
| 0.15 | 0.2162 | 0.4211 | 0.2857 |
| **0.20 (Selected)** | **0.5000** | **0.4211** | **0.4571** |
| 0.25 | 0.8000 | 0.2105 | 0.3333 |
| 0.30 | 1.0000 | 0.1579 | 0.2727 |
| 0.35 | 1.0000 | 0.0526 | 0.1000 |
| 0.40 | 0.0000 | 0.0000 | 0.0000 |

*Token-Overlap Baseline*: Peaked at Jaccard threshold 0.05 with $F_1 = 0.3871$ ($P=0.5000, R=0.3158$), confirming dense sentence embeddings (`paraphrase-MiniLM-L3-v2`) outperform lexical word overlap.

### Held-Out Evaluation (MIT 6.006 Lectures 5, 6, and 7 at Threshold 0.20)

| Lecture | Predictions | Ground Truth Positives | TP | FP | FN | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Lecture 5** | 3 | 0 | 0 | 3 | 0 | 0.0000 | 0.0000 | 0.0000 |
| **Lecture 6** | 0 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| **Lecture 7** | 21 | 0 | 0 | 21 | 0 | 0.0000 | 0.0000 | 0.0000 |
| **Combined (5–7)** | **24** | **0** | **0** | **24** | **0** | **0.0000** | **0.0000** | **0.0000** |

---

## Known Limitations

1. **Chalkboard & Blackboard OCR Degradation**:
   - Tesseract is optimized for clean typography on digital presentation slides. On chalkboard lectures (such as MIT 6.006), chalk handwriting, chalk dust, and variable classroom lighting produce corrupted text strings (e.g. `et benagy tree Se Mined k)...`).
   - Although fixed-cadence sampling resolves continuous camera segmentation failures, handwriting recognition noise remains the primary driver of false positives in blackboard videos.
2. **Zero Held-Out Redundant Ground Truth**:
   - The first 10 minutes of MIT 6.006 Lectures 5, 6, and 7 contain zero genuine redundancy intervals (professors write brief formula sketches while explaining higher-level intuitions). Held-out evaluations currently test false-positive rejection rather than recall on unseen positive examples.
3. **Development-Selected Threshold Caveat**:
   - The selected embedding threshold of `0.20` was tuned on the 4 development lecture clips and should not be assumed optimal across different teaching domains or speech speeds without larger multi-domain cross-validation.
4. **Inter-Annotator Agreement Sample**:
   - Double-annotated labels (`data/ground_truth_second/01 [01].json`) exist for only one lecture clip, indicating moderate boundary ambiguity in subjective redundancy perception (11 positives vs. 8 in primary set).

---

## Future Work

- **Vision-Language Model OCR**: Integrating multimodal models (e.g. Gemini Vision or Florence-2) for robust handwriting transcription on blackboard surfaces.
- **Physical Signaling & Gesture Tracking**: Computer vision tracking for instructor pointing gestures, laser pointers, and cursor movement to evaluate fine-grained visual signaling.
- **Automated Summaries & Slide Linter Export**: Generating PDF cognitive health reports and slide revision recommendations for lecture authors.
