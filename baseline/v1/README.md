# Time Engine 三輪接続模型 v1 — 読み方と再現

最初に[note55-consolidated.md](note55-consolidated.md)を読む。操作上の定義は[MODEL-SPEC.md](MODEL-SPEC.md)、成果と既存検査の対応は[EVIDENCE-MAP.md](EVIDENCE-MAP.md)。この版はRR52〜54の統合版で、数理実装はRR54固定版のままである。

## ファイルの配置

再現用ZIPでは、このREADMEと統合文書を最上位に置き、元の118ファイルを`runtime/`へそのまま収録する。旧文書の現在地記述は当時の記録として残し、現在の完成範囲は最上位の統合稿を基準にする。

GitHubから取得する場合は、コミット`a67915066973a6bd5bf2c3d2fe06b0cede838b76`の[RR54ディレクトリ](https://github.com/residual-chart-lab/aki-vault/tree/a67915066973a6bd5bf2c3d2fe06b0cede838b76/10_ARTIFACTS/TimeEngine/2026-10-16__chatgpt__three-flower-upper-constraint-v001)全体がruntimeに当たる。リポジトリ内でRR55文書から照合器を実行すると、隣のRR54ディレクトリを自動で見つける。単独取得した場合は`--runtime`でそのディレクトリを指定できる。

## 保存物の照合だけ行う

Python標準ライブラリのみ。ZIP展開後、このREADMEのある場所で実行する。

```text
python verify_release.py
```

118ファイルのSHA-256、保存された8検査群と数値、二完了記録、252テストの保存実行記録、仕様に引用した検査名、統合文書のハッシュを照合する。solverの実行や全テストの再実行は行わない。結果の`full_numerical_rerun_performed`は`false`である。

## 数値と全テストを再実行する

```text
cd runtime
python validation_driver.py
```

GitHubからディレクトリを取得した場合は`runtime`の代わりに取得したRR54ディレクトリへ移動する。ドライバは主計算8検査群、既存全252テスト、二つの完全な三輪＋上位完了記録の保存・復元を実行する。厳密な有理数計算のため数分かかる。保存ログの実行時間は約529秒で、実行環境によって変わる。

別々に実行する場合：

```text
python three_flower_constraint.py
python -m unittest discover -p "test_*.py"
```

数値再実行が書き出す主結果`three_flower_constraint_result.json`は固定版とバイト一致することを既に確認している。`RR54-driver-validation.json`は実行時間などを含むため、再実行すると値が更新される。原本の保存が必要なら作業用コピーで実行する。`verify_release.py`は元の118ファイルの完全同一性を確認するため、再実行後にログだけが変わっても差分として報告する。

## 保存されている主な結果

| ファイル | 内容 |
|---|---|
| `runtime/three_flower_constraint_result.json` | 64候補、4→1、16後続の比較、未来条件の対照、上位閉鎖 |
| `runtime/macro-occurrences/first-terminal-frame.record.json` | 基準共通未来要求で実際に実行・認証した三輪＋上位一輪 |
| `runtime/macro-occurrences/alternate-terminal-frame.record.json` | 別の共通未来要求で選ばれた、別のactualな完了記録 |
| `runtime/RR54-validation.json` | RR54の別展開による数値・全テストの検証ログ |
| `frozen-runtime-manifest.json` | 固定コミット、118ファイルのサイズ・SHA-256・Git blob SHA |
| `RR55-validation.json` | 今回の仕上げで行った保存物・主張・文書の照合 |
| `RR55-PROVENANCE.json` | 統合文書と固定入力の来歴・ハッシュ |

## この版の完了条件

一輪の内部未来適合、実行・認証・差の保持、二輪・三輪への継承と参照変換、共通上位未来要求による最初の4→1の選別、確定後の探索なしの実行、二つの完全な完了記録の保存まで。

上位未来文脈は明示した可解fixture。独立した未来供給原理や全クラスの一意搬送、輪数一般の単調な拘束強化は次に残す。数え方は同じ階層の三輪＋上位の一輪である。
