"""Unit test for result-layer consolidation."""

import json
import tempfile
import unittest
from pathlib import Path

from src.results.build_result import build_video_result


class FixedEmbeddingModel:
    def encode(self, texts, normalize_embeddings=True):
        # Return high similarity for the fixture
        return [[1.0, 0.0], [0.8, 0.6]]


class BuildResultTest(unittest.TestCase):
    def test_build_video_result_schema_and_sorting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            aligned_dir = Path(temp_dir) / "aligned"
            results_dir = Path(temp_dir) / "results"
            aligned_dir.mkdir()

            video_stem = "sample_lecture"
            sample_aligned = [
                {
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "spoken_text": "Later spoken explanation",
                    "onscreen_text": "Later slide bullet",
                },
                {
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "spoken_text": "Earlier spoken introduction",
                    "onscreen_text": "Earlier slide title",
                },
            ]
            (aligned_dir / f"{video_stem}.json").write_text(
                json.dumps(sample_aligned), encoding="utf-8"
            )

            result = build_video_result(
                video_stem,
                aligned_dir=aligned_dir,
                output_dir=results_dir,
                min_overlap=0.5,
                scoring_method="embedding",
                embedding_model=FixedEmbeddingModel(),
            )

            # Check dict schema
            self.assertEqual(result["video"], video_stem)
            self.assertIn("violations", result)
            self.assertEqual(len(result["violations"]), 2)

            # Check sorted ascending by start_time
            self.assertEqual(result["violations"][0]["start_time"], 0.0)
            self.assertEqual(result["violations"][1]["start_time"], 10.0)

            # Check violation record schema
            first_v = result["violations"][0]
            self.assertEqual(
                set(first_v.keys()),
                {"start_time", "end_time", "score", "spoken_text", "onscreen_text"},
            )
            self.assertAlmostEqual(first_v["score"], 0.8)

            # Check file persistence
            saved_file = results_dir / f"{video_stem}.json"
            self.assertTrue(saved_file.is_file())
            saved_data = json.loads(saved_file.read_text(encoding="utf-8"))
            self.assertEqual(saved_data, result)


if __name__ == "__main__":
    unittest.main()
