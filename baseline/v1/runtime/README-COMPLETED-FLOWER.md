# 一輪の最小模型 v1 — 実行と再現

Python 3標準ライブラリだけで動く。まずZIPを展開し、その中のディレクトリで次を実行する。

```text
python run_one_flower.py --branch first --choice 0 --output my-flower.json
```

一輪の結果を表示し、完全な認証付き完了記録をJSONへ保存する。保存先に既存ファイルがある場合は上書きしない。

同じsourceと文脈から別の花びらを選ぶ例：

```text
python run_one_flower.py --branch first --choice 1 --output my-other-flower.json
```

choice 0は短い二作用、choice 1は遠回りの四作用となり、どちらも一輪として閉じる。第二枝は`--branch second`。この二候補の違いは基準模型のものであり、全ての摂動模型で二候補があるという意味ではない。

`examples/`には二枝×二選択の完全な完了記録を同梱する。これらは結果の要約だけではなく、sourceとconsumerの全ての入れ子の認証、実行済み語と出来事の記録を持つ。

完了記録を復元して検証する例：

```python
import json
from pathlib import Path
from completed_single_flower import Configuration, import_record

payload = json.loads(Path('examples/first-choice-1.record.json').read_text(encoding='utf-8'))
record = import_record(payload, Configuration(source_branch='first', petal_choice=1))
```

復元時は、入口に与えた設定との一致を検証する。ファイルの作者を認証する機能ではない。

全検証：

```text
python completed_single_flower.py
python -m unittest discover -p "test_*.py"
```

模型条件、自由な選択値、探索上限、保存範囲はnote52-original.mdに記載する。実際の検証結果はRR52-validation.json。
