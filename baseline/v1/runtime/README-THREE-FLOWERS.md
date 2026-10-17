# RR54 再現方法

Python標準ライブラリのみ。ZIP全体を展開し、このファイルのあるディレクトリで実行する。

```text
python three_flower_constraint.py
python -m unittest discover -p "test_*.py"
```

主計算は8検査群、テストは252件（既存232＋新20）。64の三輪候補は元の入口から計算する。未来の経路一覧を入力する方式ではない。

一式の検証を一つのプロセスで行い、候補試算を再利用する場合：

```text
python validation_driver.py
```

この方式も主計算と全テストを実行し、二つの完全な完了記録を `macro-occurrences/` へ保存して検証する。厳密な有理数計算のため、再現には数分かかる。

利用例：

```python
import json
from three_flower_constraint import (
    construct_test_requirement, select_macro, execute_macro,
    export_macro, import_macro,
)

fixture = construct_test_requirement(0)  # explicit solvable test requirement
requirement = fixture.requirement
receipt = select_macro(requirement)     # receives a frame/result, not a path list
actual = execute_macro(receipt)
saved = json.loads(json.dumps(export_macro(actual)))
assert import_macro(saved, requirement) == actual
```

`construct_test_requirement` は可解な検査課題を作るための明示したfixture。独立に未知な未来の生成則と同一視しない。別のフレームの対照はindex 63で作る。選択器へ渡すのはその文脈・固定要求・誤差基準であり、基準の経路ラベルは渡さない。

結果は `three_flower_constraint_result.json`。本文 `note54-original.md`、原本対応 `RR54-source-map.md`、検証 `RR54-validation.json`、来歴 `RR54-PROVENANCE.json`。過去のRR53以前の文書・検証結果は旧名のまま保持する。
