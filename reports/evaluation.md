# Evaluation Summary

## Dataset split

- Development: four labeled 5-minute lecture samples (19 redundant intervals).
- Held-out: MIT 6.006 Lectures 5–7, processed for their first 10 minutes. Lectures 5 and 6 have labels; Lecture 7 is not yet labeled.

## Development results

Metrics are micro-aggregated precision, recall, and F1.

| Embedding threshold | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: |
| 0.10 | 0.1169 | 0.4737 | 0.1875 |
| 0.15 | 0.2162 | 0.4211 | 0.2857 |
| 0.20 | 0.5000 | 0.4211 | 0.4571 |
| 0.25 | 0.8000 | 0.2105 | 0.3333 |
| 0.30 | 1.0000 | 0.1579 | 0.2727 |
| 0.35 | 1.0000 | 0.0526 | 0.1000 |
| 0.40 | 0.0000 | 0.0000 | 0.0000 |

Selected development threshold: **embedding similarity 0.20**, which produced the highest F1 (0.4571).

Token-overlap baseline:

| Threshold | Precision | Recall | F1 |
| ---: | ---: | ---: | ---: |
| 0.05 | 0.5000 | 0.3158 | 0.3871 |
| 0.10 | 1.0000 | 0.1579 | 0.2727 |
| 0.15–0.30 | 0.0000 | 0.0000 | 0.0000 |

## Held-out results at embedding threshold 0.20

| Lecture | TP | FP | FN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 0 | 3 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 6 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 5–6 combined | 0 | 3 | 0 | 0.0000 | 0.0000 | 0.0000 |

Lecture 7 produced 21 embedding candidates at 0.20, but has no ground-truth labels, so held-out metrics are not available for it.

## Limitation

OCR quality is the limiting factor in held-out Lectures 5–7. Lecture 5 repeatedly produced corrupted slide text, Lecture 6 produced blank on-screen text, and Lecture 7 produced one repeated, heavily corrupted OCR string. These outputs cause false positives or prevent meaningful redundancy scoring; held-out metrics therefore measure the current end-to-end OCR-plus-detector pipeline, not semantic similarity alone.

## Held-Out Evaluation (Updated)

Following the ground-truth labeling of Lecture 7 (121 intervals following the labeling guide, all labeled non-redundant due to corrupted blackboard OCR), held-out evaluation was recomputed across the complete held-out set (Lectures 5, 6, and 7) at embedding threshold 0.20:

| Lecture | Predictions | GT Positives | TP | FP | FN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 3 | 0 | 0 | 3 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 6 | 0 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 7 | 21 | 0 | 0 | 21 | 0 | 0.0000 | 0.0000 | 0.0000 |
| **Combined (5–7)** | **24** | **0** | **0** | **24** | **0** | **0.0000** | **0.0000** | **0.0000** |

All 21 candidate predictions generated for Lecture 7 are false positives resulting from the detector matching spoken narration against the single corrupted OCR string repeatedly present across all blackboard windows. Because there are no true redundant instances in Lectures 5–7, recall and F1 remain 0.0000.
