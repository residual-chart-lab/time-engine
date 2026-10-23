# E1 — Pythonの版をまたぐ搬送試験

2026-10-23。[最初のE1実装](ENTRY_TRANSPORT_E1.md)に続き、固定入口を別のPython環境へ渡した結果。元の記録・実装の修正は不要だった。

| 項目 | 送出側の対照 | 別の受信環境 |
|---|---|---|
| 実行環境 | CPython 3.12.14 | CPython 3.14.3 |
| OS | Windows 11、x64 | 同じPCのWindows 11、x64 |
| 起動 | 独立プロセス、`-I` | 別のPython導入先、独立プロセス、`-I` |
| 凍結入力 | E1公開時の403ファイルをハッシュ照合 | 同じ403ファイルだけを別フォルダーへコピーし照合 |
| 過去生成器 | 七つを禁止 | 七つを禁止 |
| 結果 | 三輪・上位認証、在庫9、STOPPED | 同じ |
| 確認項目 | 13項目 | 14項目。3.12の完了記録の受入も含む |

受信側では新たなsource登録や学習を行わない。固定記録を認証した後の厳密な履歴再演は、前の実装どおり行う。両環境で、第一輪を閉じた時点の保存再開、三輪・上位セルの閉鎖、完了時点の保存再開を確認した。

両環境の結果は、既存RR69公開記録と、全物理履歴・認証・数・要求・操作の点で厳密に一致した。さらに今回作った完了記録は、両環境でバイト列も一致した。

- 元の入口SHA-256: `d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3`
- 今回の完了記録SHA-256: `5149e8d86856b514c13ea2e9a9c3f8995410d2adef7c917d8439a9ba21479415`
- 今回の完了記録: 162,897 bytes。

3.12で作った完了記録を3.14で直接読み込み、再認証できた。旧RR69公開checkpointとのバイト一致や、あらゆる環境でのバイト一致を一般保証する結果ではない。

## 拒否と発行の境界

両環境で、誤った期待ハッシュ、誤った入口識別子、二つのsource履歴の入れ替えを拒否した。失敗した読込から入口の発行権限が残らないことも確認した。入口の受入時点では新要求を束縛せず、その後に同じ固定実演用要求と現在選択を与える。

## 再現

リポジトリのルートで実行する。追加パッケージのインストールはこの試験には不要だった。`-I` はユーザー環境のPython探索経路を除外するために使う。

```text
<python-3.12> -I integrations/inquiry/validate_entry_transport_external.py --output .work/e1-portability/python312
```

403ファイルの基準は `integrations/inquiry/E1-PORTABILITY-INPUT.json`。その後に追加した本試験の文書・結果・実行器は、この凍結入力403件の数に含めない。

同じ凍結入力を別フォルダーへコピーし、別のPythonで実行する。checkpointのパスは最初の環境で作ったファイルを指す。

```text
<python-3.14> -I integrations/inquiry/validate_entry_transport_external.py --output .work/e1-portability/python314 --checkpoint <python312-output>/completed.record.json --trusted-checkpoint-sha256 5149e8d86856b514c13ea2e9a9c3f8995410d2adef7c917d8439a9ba21479415
```

別機器に渡す場合は、記録と別に保持した期待ハッシュを使う。新しく作ったcheckpointのSHAは各実行の `result.json` に出る。上の値は今回固定した実験の値である。

結果は `integrations/inquiry/E1-python312.json`、`E1-python314.json`、出所とファイルハッシュは `E1-PORTABILITY-PROVENANCE.json` に保存した。13/14という数は、この受入試験内の確認項目数であり、前回の42 unit testsに足して新しいunit test数と数えない。元の42件と全247件の再実行は、今回は行っていない。

## 残る範囲

今回変えたのはPythonの導入先・バージョン・プロセス・展開フォルダー。OS・CPU・機器・浮動小数環境を変えた試験は未実施。上流の学習再現も試験対象に含めない。固定RR69対角source族・接触1/2・petal 0・gain 1というE1の対応範囲を広げる変更はしていない。
