# Time Engine — 最初の技術配布候補 P0

2026-10-24。2026-12-25の公開に向けた最初の候補。AIが受け取り、自分の環境で有限三輪模型を操作するための一式。

## まず二つ

Python 3.12以降で、このフォルダーから実行する。追加パッケージの導入は、この候補の確認手順では必要なかった。

```text
python -I verify_package.py
python -I smoke_test.py
```

前者は同梱ファイルを照合する。後者は入口受入 → 要求 → 現在選択 → 精査 → 第一輪で停止・保存 → 別プロセスで再開 → 第二・第三輪と上位セルの成立、までを動かす。同じ条件での再精査の追加数値読出しが0であることも確認する。結果は `.work/acceptance.json`。

## AIから操作する

[AIへの引継ぎ](AI_HANDOFF.md)と、[一輪ずつの操作手順](engine/docs/STEP_SESSION_E2.md)を読む。次のプロセスの標準入力へJSONを一行ずつ送る。

```text
python -I engine/run_time_engine.py --entry engine/integrations/inquiry/E1-entry.record.json --trusted-sha256 d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3 --expected-entry-digest 24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de
```

命令の見本は `engine/examples/e2-three-flowers.jsonl`。`advance`一回で一輪を閉じて止まる。三輪の後の`advance`は上位を認証し、`STOPPED`となる。途中停止には`save`を使い、応答のSHAを別途保持する。各操作で入口を読み直す必要はない。

## どの版か

- `engine/` は固定版 `1c185365bfcb2ea9f6c52c73ba263cf48c356d32` の422ファイルをそのまま保持している。
- E1限定入口はAstra監査PASS。WindowsとLinuxでの入口搬送・再開の記録がある。
- E2操作系は新8テストとWindows Python 3.12→3.14の途中再開が通過。E2の独立監査・Linux試験は未実施。
- 対象はRR69の限定source族と有限三輪。入口の認証は、新しい要求への成立許可を含まない。

詳細は `PACKAGE.json`、ファイルの一覧は `MANIFEST.json`、固定元は `P0-SOURCE.json`。内側の`engine/README.md`は研究の索引である。

## 作り直す

```text
python -I build_candidate.py --output-dir .work/rebuilt
```

同じ内容から新しいZIPとSHA-256を作る。出力先の既存アーカイブは上書きしない。ファイル順序・格納時刻・属性を固定している。同じPythonと圧縮ライブラリでのバイト再現を確認する設計であり、異なる圧縮ライブラリ間のZIPバイト一致を保証するものではない。

ZIP全体のSHA-256は外側の `.zip.sha256` にある。展開後の照合は同梱一覧との整合性確認であり、配布元の認証には別に信頼したZIPの期待SHAを使う。各vendorの出所・ライセンスも元の配置で保持している。
