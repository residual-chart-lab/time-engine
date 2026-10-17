from __future__ import annotations

from typing import List, Sequence, Tuple

Vector = Sequence[float]
Sample = Tuple[Vector, float]


def xnor() -> List[Sample]:
    return [
        ([0.0, 0.0], 1.0),
        ([0.0, 1.0], 0.0),
        ([1.0, 0.0], 0.0),
        ([1.0, 1.0], 1.0),
    ]
