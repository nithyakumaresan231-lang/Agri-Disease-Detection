import json
from pathlib import Path
from typing import Dict, Any, Optional

ADVISORY_FILE = Path(__file__).resolve().parent.parent / "data" / "advisories.json"


class AdvisoryService:
    def __init__(self, file_path: Path = ADVISORY_FILE):
        self.file_path = file_path
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load advisories from {self.file_path}: {e}")
                self._data = {}
        else:
            self._data = {}

    def get_all(self) -> Dict[str, Any]:
        return self._data

    def get_by_class(self, class_name: str) -> Optional[Dict[str, Any]]:
        if not self._data:
            self._load()
        return self._data.get(class_name)

    def get_fallback(self, crop: str = "Unknown Crop", disease: str = "Unspecified Condition") -> Dict[str, Any]:
        return {
            "crop": crop,
            "disease": disease,
            "is_healthy": False,
            "description": f"Foliar condition observed on {crop}. Standard disease monitoring recommended.",
            "symptoms": [
                "Discoloration or irregular marking on leaf canopy",
                "Foliage stress under environmental factors"
            ],
            "preventive_measures": [
                "Maintain adequate spacing between plants for aeration.",
                "Avoid overhead irrigation to minimize leaf wetness.",
                "Sanitize tools and remove diseased plant residues."
            ],
            "management": [
                "Consult local agronomic extension specialists for site-specific treatment.",
                "Isolate affected plants if localized spread is observed."
            ]
        }


# Singleton instance
advisory_service = AdvisoryService()
