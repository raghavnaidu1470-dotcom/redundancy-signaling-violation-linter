"""Minimal structural test for the ground-truth annotation schema."""

import json
import unittest
from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "ground_truth" / "schema.json"


class GroundTruthSchemaTest(unittest.TestCase):
    def test_schema_defines_required_annotation_fields(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        item = schema["items"]

        self.assertEqual(schema["type"], "array")
        self.assertEqual(item["required"], ["start_time", "end_time", "is_redundant"])
        self.assertEqual(item["properties"]["is_redundant"]["type"], "boolean")


if __name__ == "__main__":
    unittest.main()
