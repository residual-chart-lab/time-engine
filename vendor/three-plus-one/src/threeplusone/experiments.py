from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .core import ThreePlusOneMLP, Sample


@dataclass(frozen=True)
class SweepRow:
    epsilon: float
    epochs: int
    mse: float
    converged: bool
    hidden_spread: float
    hidden_groups: tuple[tuple[int, ...], ...]


def epsilon_sweep(
    samples: Iterable[Sample],
    epsilons: Sequence[float],
    **network_kwargs,
) -> list[SweepRow]:
    data = list(samples)
    rows: list[SweepRow] = []

    for epsilon in epsilons:
        net = ThreePlusOneMLP(
            epsilon=float(epsilon),
            **network_kwargs,
        )
        result = net.fit(data)
        rows.append(
            SweepRow(
                epsilon=float(epsilon),
                epochs=result.epochs,
                mse=result.mse,
                converged=result.converged,
                hidden_spread=net.hidden_spread(),
                hidden_groups=tuple(
                    tuple(group) for group in net.hidden_groups()
                ),
            )
        )

    return rows
