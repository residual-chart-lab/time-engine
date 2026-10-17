# RR52 v002 再現方法

Python標準ライブラリのみ。ZIP全体を展開し、このファイルのあるディレクトリで実行する。

```text
python retrospective_residue_readout.py
python -m unittest discover -p "test_*.py"
```

新しい再参照は10検査群、全テストは211件（旧195＋新16）。入力の四つの `examples/*.record.json` はv001の保存完了記録そのもので、初めのコマンドがこれらを復元・検証してから後の作用に使う。新しい結果は `retrospective_residue_readout_result.json` に保存される。

一輪自体も初めから計算し直す場合：

```text
python completed_single_flower.py
python run_one_flower.py --branch first --choice 1 --output new-record.json
```

元の10検査群・34近傍模型の再計算ができる。v001の再現方法は `README-COMPLETED-FLOWER.md`、今回の再点検の本文は `note52-recheck.md`。旧 `note52-original.md` と旧検証文書はv001の記録として保持している。最新の検証・来歴は `RR52-v002-validation.json` / `RR52-v002-PROVENANCE.json` を参照する。

利用例：

```python
from retrospective_residue_readout import load_published, ReferenceInput, read_retained
from robust_flower_geometry import diagonal
from certified_cell_bridge import UpperState

record = load_published('first', 1)  # expected entry config is checked here
present = ReferenceInput(UpperState(diagonal((1.5, 0.25, -0.75)), (1, 2, -1, 3)))
response = read_retained(record, record.commitment, present)
print(response.after.accumulated)
```

計算は有理数で行う。任意の分数は `fractions.Fraction` を渡す。上の有限二進小数はexactに変換できる値を用いている。参照は正則チャートと保存作用のlevel 3に限り、保存記録と信頼した確定記録の対応を検証する。読み取りのための参照状態だけを更新し、次フラワーを生成しない。
