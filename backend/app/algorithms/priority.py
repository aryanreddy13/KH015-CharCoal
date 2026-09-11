"""
Priority Calculation Algorithm (Phase 1 Placeholder & Baseline)

Formula Preview (Phase 2):
Priority = (Severity * 0.45) + (Casualty_Impact * 0.35) + (Vulnerability_Index * 0.20)
"""

def calculate_priority_score(severity: float, affected_count: int, urgency_factor: float = 1.0) -> float:
    """
    Computes priority score normalized between 0.0 and 10.0.
    """
    casualty_scale = min(10.0, (affected_count / 50.0))
    raw_score = (severity * 0.5) + (casualty_scale * 0.3) + (urgency_factor * 2.0)
    return round(min(10.0, max(0.0, raw_score)), 2)
