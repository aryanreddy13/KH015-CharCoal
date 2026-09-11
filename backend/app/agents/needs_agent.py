"""
Needs Assessment Agent (Phase 1 Placeholder)

Responsibilities (Phase 2):
- Consume multi-source reports (citizen forms, emergency calls, satellite metadata).
- Synthesize quantitative requirement estimates (e.g. boats, doctors, ration packs).
- Score severity per resource category on a scale of 0.0 to 10.0.
- Update Zone requirement manifests automatically.
"""

from typing import Dict, Any, List

class NeedsAssessmentAgent:
    def __init__(self):
        self.model_name = "gemini-1.5-flash-stub"

    async def assess_needs(self, disaster_type: str, casualties: int, description: str) -> List[Dict[str, Any]]:
        """
        TODO (Phase 2):
        Execute structured LLM prompt to estimate rescue, medical, food, water, and shelter deficits.
        """
        # Baseline deterministic calculation for Phase 1 stub
        return [
            {"resource_type": "Rescue", "quantity_required": max(1, casualties // 10), "severity": 8.5},
            {"resource_type": "Medical", "quantity_required": max(2, casualties // 5), "severity": 9.0},
        ]

needs_agent = NeedsAssessmentAgent()
