from __future__ import annotations

import argparse

from .core import ThreePlusOneMLP, centered_singleton_seed
from .datasets import xnor
from .experiments import epsilon_sweep


DEFAULT_SWEEP = [0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]


def _demo(epsilon: float, hidden: int, centered: bool) -> None:
    seed_pattern = centered_singleton_seed(hidden) if centered else None
    net = ThreePlusOneMLP(
        hidden=hidden,
        epsilon=epsilon,
        seed_pattern=seed_pattern,
    )
    result = net.fit(xnor(), record_every=100)

    print(f"epsilon={epsilon:g}")
    print(f"converged={result.converged}")
    print(f"epochs={result.epochs}")
    print(f"mse={result.mse:.12f}")
    print(f"hidden_spread={net.hidden_spread():.12f}")
    print(f"hidden_groups={net.hidden_groups()}")

    for x, target in xnor():
        print(
            f"{int(x[0])}{int(x[1])} "
            f"target={int(target)} "
            f"prediction={net.predict(x):.9f}"
        )


def _sweep(values: list[float], hidden: int, centered: bool) -> None:
    seed_pattern = centered_singleton_seed(hidden) if centered else None
    rows = epsilon_sweep(
        xnor(),
        values,
        hidden=hidden,
        seed_pattern=seed_pattern,
    )
    print("epsilon,converged,epochs,mse,hidden_spread,hidden_groups")
    for row in rows:
        print(
            f"{row.epsilon:g},"
            f"{row.converged},"
            f"{row.epochs},"
            f"{row.mse:.12f},"
            f"{row.hidden_spread:.12f},"
            f"{row.hidden_groups}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="three-plus-one",
        description=(
            "Run small deterministic experiments on symmetry breaking "
            "in one-hidden-layer neural networks."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Run the XNOR three-plus-one demo")
    demo.add_argument("--epsilon", type=float, default=1.0)
    demo.add_argument("--hidden", type=int, default=4)
    demo.add_argument(
        "--centered",
        action="store_true",
        help="Use a zero-sum centered (n-1)+1 seed",
    )

    sweep = sub.add_parser("sweep", help="Sweep epsilon on XNOR")
    sweep.add_argument("--hidden", type=int, default=4)
    sweep.add_argument(
        "--centered",
        action="store_true",
        help="Use a zero-sum centered (n-1)+1 seed",
    )
    sweep.add_argument(
        "epsilons",
        nargs="*",
        type=float,
        default=DEFAULT_SWEEP,
    )

    args = parser.parse_args()

    if args.command == "demo":
        _demo(args.epsilon, args.hidden, args.centered)
    elif args.command == "sweep":
        values = args.epsilons or DEFAULT_SWEEP
        _sweep(values, args.hidden, args.centered)


if __name__ == "__main__":
    main()
