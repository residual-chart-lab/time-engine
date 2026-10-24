# 起動案内の確認記録

2026-10-24。変更対象は `docs/P0_STARTUP.md` と受入状況の案内。固定P0のZIP、source、認証処理、運動式を変更していない。

PowerShellの案内にある `P0_PYTHON`、`P0_ROOT`、`P0_RUN_ARGS` へ実在するパスを指定し、配布物外の空白を含むフォルダーへ移動して実行した。Python 3.12で照合、3.14で標準入力へstatus/quitを送って開始、さらに初見試験で得た第一輪checkpointを絶対パスで指定して再開した。

`startup-check.json` は環境と結果、`start.jsonl` / `resume.jsonl` は実際の応答。第一輪checkpointのSHAは `7eeacc493777697c6dec70831b9307f20918edc1d6fd566fe08d61582199a476`。保存済み記録と別保持のSHAを使い、状態はCLOSED1、在庫7へ復旧した。今回の動作確認ではその先のadvanceは送っていない。

この記録は新規unit test数に加算しない。Bash記法の実行や全件検査も行っていない。P0本体のLinux動作には固定された独立監査報告を参照する。
