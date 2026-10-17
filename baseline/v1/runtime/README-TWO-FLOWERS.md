# RR53 二輪の接続の再現

Python標準ライブラリのみ。このファイルのあるディレクトリで実行する。

```text
python two_flower_connection.py
python -m unittest discover -p "test_*.py"
```

新10検査群、二輪接続の新21テスト、関連232テスト。一輪目の入力はRR52 v001の二枝×二選択の四つのexact完了記録 `examples/*.record.json`。二輪目のsourceは、実際に継承した入口と接続文脈から計算し、実行・認証・公開してから使う。

```python
from two_flower_connection import (
    load_published, ConnectionSpec, connect_two, verify_connection, brief,
    export_connected, import_connected,
)
import json

first = load_published('first', 0)
spec = ConnectionSpec(source_branch=0, petal_choice=1)
two = connect_two(first, spec)
assert verify_connection(two, first, spec)
print(brief(two))
saved = json.loads(json.dumps(export_connected(two)))
assert import_connected(saved, first, spec) == two
```

`ConnectionSpec` は実行前に固定する接続条件。既定値は同じ階層の二輪を、headの読出しを基準に保持差を強さ1/1024で加える `anchored` 接続。二輪目のsource枝0/1、花びら選択、有限語探索の上限も明示する。直接渡す `direct` は今回の比較対象であり、不成立時に自動で規則を切り替える処理はない。

完了した二輪目は次の要求を発行せずに停止する。上位のlevel 3出力二つは保持し、下位のlevel 2在庫には入れない。これらを一つのさらに上位の花に閉じることは別段階。

`two_flower_connection_result.json` が新結果。全入力・依存ファイルのハッシュと実行ログは `RR53-validation.json` / `RR53-PROVENANCE.json`。旧RR52の再現方法と結果は旧名のまま保持する。
