# Time Engine — まず動かす

2026-10-24。配布前のE2操作系。対象は、監査済みE1の限定入口と、既存RR69の三輪模型。

1. [入口の固定状況](docs/ENTRY_TRANSPORT_E1_STATUS.md)で対応範囲を確認する。
2. [操作手順](docs/STEP_SESSION_E2.md)に従い `run_time_engine.py` を起動する。
3. `examples/e2-three-flowers.jsonl` の命令を標準入力に一行ずつ渡す。

入口は最初に一度認証し、同じプロセスで保持する。要求・選択・精査の後、`advance` 一回につき一輪を閉じる。第三輪の次の `advance` は上位セルを認証し、`STOPPED` になる。

第一輪以降の閉じた過去は巻き戻さない。停止や復旧には `save` と起動時の `--resume` を使う。既存の `README.md` は研究模型の索引として残している。

## 使ってから、深く知りたくなったら

[自由数への読書案内](docs/FREE_NUMBERS_READING_PATH.md)から、問いに合う原典・実装・検証記録へ進める。操作前に全てを学ぶ必要はない。
