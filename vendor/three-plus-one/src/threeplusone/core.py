from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, List, Sequence, Tuple


Vector = Sequence[float]
Sample = Tuple[Vector, float]


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def centered_singleton_seed(hidden: int) -> tuple[float, ...]:
    """
    Return the centered (n-1)+1 seed.

    Starting from the default singleton seed (0, ..., 0, 1), subtract its
    mean so that the seed sums to zero:

        (-1/n, ..., -1/n, 1 - 1/n)

    When hidden activations are initially identical, this preserves the
    initial output preactivation while still breaking permutation symmetry.
    """
    if hidden < 2:
        raise ValueError("centered singleton seed requires at least 2 hidden units")

    mean = 1.0 / hidden
    return tuple([-mean] * (hidden - 1) + [1.0 - mean])


@dataclass(frozen=True)
class EpochRecord:
    epoch: int
    mse: float
    hidden_spread: float


@dataclass(frozen=True)
class FitResult:
    epochs: int
    mse: float
    converged: bool
    history: Tuple[EpochRecord, ...]


class ThreePlusOneMLP:
    """
    Minimal one-hidden-layer sigmoid network with an explicit symmetry seed.

    Initial hidden incoming weights are identical:

        B_i^(0) = b_0    for every hidden unit i

    Output weights are:

        a_i^(0) = a_0 + epsilon * s_i

    where s is a user-supplied seed vector. By default,

        s = (0, 0, ..., 0, 1)

    so one hidden unit receives the perturbation and the others remain
    identical: an (n-1)+1 initialization.

    This implementation intentionally uses conventional backpropagation:
    hidden deltas are computed from a snapshot of the pre-update output
    weights. It is therefore an independent experimental system, not a
    transcription of any historical program.
    """

    def __init__(
        self,
        *,
        inputs: int = 2,
        hidden: int = 4,
        epsilon: float = 1.0,
        seed_pattern: Sequence[float] | None = None,
        base_hidden_weight: float = -1.0,
        base_output_weight: float = -1.0,
        learning_rate: float = 1.0,
        target_mse: float = 0.01,
        max_epochs: int = 5000,
    ) -> None:
        if inputs < 1 or hidden < 1:
            raise ValueError("inputs and hidden must be positive")
        if learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if target_mse <= 0:
            raise ValueError("target_mse must be positive")
        if max_epochs < 1:
            raise ValueError("max_epochs must be positive")

        self.inputs = int(inputs)
        self.hidden = int(hidden)
        self.epsilon = float(epsilon)
        self.base_hidden_weight = float(base_hidden_weight)
        self.base_output_weight = float(base_output_weight)
        self.learning_rate = float(learning_rate)
        self.target_mse = float(target_mse)
        self.max_epochs = int(max_epochs)

        if seed_pattern is None:
            seed = [0.0] * self.hidden
            seed[-1] = 1.0
        else:
            seed = [float(v) for v in seed_pattern]
            if len(seed) != self.hidden:
                raise ValueError(
                    f"seed_pattern must contain {self.hidden} values"
                )

        self.seed_pattern = tuple(seed)

        # Each hidden row is [bias, x1, ..., xd].
        self.hidden_w: List[List[float]] = [
            [self.base_hidden_weight] * (self.inputs + 1)
            for _ in range(self.hidden)
        ]

        # Output row is [bias, h1, ..., hn].
        self.output_w: List[float] = [self.base_output_weight]
        self.output_w.extend(
            self.base_output_weight + self.epsilon * s
            for s in self.seed_pattern
        )

    def clone_initial(self) -> "ThreePlusOneMLP":
        return ThreePlusOneMLP(
            inputs=self.inputs,
            hidden=self.hidden,
            epsilon=self.epsilon,
            seed_pattern=self.seed_pattern,
            base_hidden_weight=self.base_hidden_weight,
            base_output_weight=self.base_output_weight,
            learning_rate=self.learning_rate,
            target_mse=self.target_mse,
            max_epochs=self.max_epochs,
        )

    def _forward(self, x: Vector) -> tuple[list[float], float]:
        if len(x) != self.inputs:
            raise ValueError(f"expected {self.inputs} inputs, got {len(x)}")

        h = []
        for row in self.hidden_w:
            a = row[0]
            for j, value in enumerate(x, start=1):
                a += row[j] * float(value)
            h.append(_sigmoid(a))

        out_a = self.output_w[0]
        for i, hv in enumerate(h, start=1):
            out_a += self.output_w[i] * hv

        return h, _sigmoid(out_a)

    def predict(self, x: Vector) -> float:
        return self._forward(x)[1]

    def mse(self, samples: Iterable[Sample]) -> float:
        data = list(samples)
        if not data:
            raise ValueError("samples must not be empty")

        return sum(
            (float(target) - self.predict(x)) ** 2
            for x, target in data
        ) / len(data)

    def train_one(self, x: Vector, target: float) -> None:
        h, y = self._forward(x)

        output_delta = (float(target) - y) * y * (1.0 - y)

        # Standard backprop: hidden deltas use the pre-update output weights.
        old_output = self.output_w[:]

        hidden_delta = [
            h[i] * (1.0 - h[i]) * output_delta * old_output[i + 1]
            for i in range(self.hidden)
        ]

        self.output_w[0] += self.learning_rate * output_delta
        for i in range(self.hidden):
            self.output_w[i + 1] += (
                self.learning_rate * output_delta * h[i]
            )

        for i in range(self.hidden):
            self.hidden_w[i][0] += self.learning_rate * hidden_delta[i]
            for j, value in enumerate(x, start=1):
                self.hidden_w[i][j] += (
                    self.learning_rate * hidden_delta[i] * float(value)
                )

    def fit(
        self,
        samples: Iterable[Sample],
        *,
        record_every: int = 0,
    ) -> FitResult:
        data = list(samples)
        if not data:
            raise ValueError("samples must not be empty")
        if record_every < 0:
            raise ValueError("record_every must be non-negative")

        history: list[EpochRecord] = []
        error = self.mse(data)

        for epoch in range(1, self.max_epochs + 1):
            for x, target in data:
                self.train_one(x, target)

            error = self.mse(data)

            if record_every and (
                epoch == 1
                or epoch % record_every == 0
                or error <= self.target_mse
            ):
                history.append(
                    EpochRecord(
                        epoch=epoch,
                        mse=error,
                        hidden_spread=self.hidden_spread(),
                    )
                )

            if error <= self.target_mse:
                return FitResult(
                    epochs=epoch,
                    mse=error,
                    converged=True,
                    history=tuple(history),
                )

        return FitResult(
            epochs=self.max_epochs,
            mse=error,
            converged=False,
            history=tuple(history),
        )

    def hidden_spread(self) -> float:
        """
        Maximum Euclidean distance between any two hidden incoming-weight rows.
        Zero means all hidden units are still exactly symmetric.
        """
        best = 0.0
        for i in range(self.hidden):
            for j in range(i + 1, self.hidden):
                d2 = sum(
                    (a - b) ** 2
                    for a, b in zip(self.hidden_w[i], self.hidden_w[j])
                )
                best = max(best, math.sqrt(d2))
        return best

    def hidden_groups(self, digits: int = 12) -> list[list[int]]:
        """
        Group hidden units that still have identical incoming-weight vectors,
        up to decimal rounding.
        """
        groups: dict[tuple[float, ...], list[int]] = {}
        for idx, row in enumerate(self.hidden_w, start=1):
            key = tuple(round(v, digits) for v in row)
            groups.setdefault(key, []).append(idx)
        return list(groups.values())

    def output_weights(self) -> tuple[float, ...]:
        return tuple(self.output_w)

    def hidden_weights(self) -> tuple[tuple[float, ...], ...]:
        return tuple(tuple(row) for row in self.hidden_w)
