# P0 — 受入済みの版と現在の使い方

2026-10-24。有限三輪模型の技術配布候補P0は、E2/P0の独立監査と、初見AI一つによる手順書からの受入試験を通過した。現在の起動案内は [P0_STARTUP.md](P0_STARTUP.md)。

## 固定しているもの

- 監査対象：`f60fad90fcadaccf438c29a2f1a21bbf532dfea3`。
- main統合：`50682f53d461c675d0adf54e6d62f68d7507fd57`。内容は監査対象と同じ。
- ZIP：3,498,756 bytes、SHA-256 `91d9218bd368d7987e13ac2a14440ad38ed84d0d227b1102f225fdb0ef89fc4d`。
- 固定した内側のsource：`1c185365bfcb2ea9f6c52c73ba263cf48c356d32`、422ファイル。

同梱文書の未監査フラグは作成時点の記録として維持する。起動案内とこの受入状況は外側の補足であり、監査済みZIPの内容は変更しない。

## 同じP0を再構築する

構築元は、**監査済みP0の展開物**、または[固定版f60fad9](https://github.com/residual-chart-lab/time-engine/tree/f60fad90fcadaccf438c29a2f1a21bbf532dfea3)の別チェックアウトに限る。現在のE3作業木は固定sourceと異なるため、そのままP0を作ろうとするとbuilderが正しく拒否する。作業中のcheckoutを固定版へ強制的に戻す必要はない。

展開済みの`time-engine-p0/`には、`build_candidate.py`、`P0-SOURCE.json`、`engine/`がある。そのフォルダーで、新しい出力先を指定する。

```text
python -I build_candidate.py --output-dir .work/p0-rebuild
```

ソースから取得する場合は、固定版を新しいフォルダーへ受け取る。

```text
git clone --no-checkout https://github.com/residual-chart-lab/time-engine.git time-engine-p0-source
git -C time-engine-p0-source checkout --detach f60fad90fcadaccf438c29a2f1a21bbf532dfea3
cd time-engine-p0-source
python -I build_candidate.py --output-dir .work/p0-build
```

出力されたZIP実体のサイズとSHA-256を、上記の固定値へ照合する。Python/zlibの異なる圧縮実装間でのバイト一致を一般保証した手順ではない。起動できるPython実行ファイルの選び方は[P0_STARTUP.md](P0_STARTUP.md)を参照する。

## 独立監査

[Astraの固定報告](https://github.com/residual-chart-lab/time-engine/blob/1583d9a84800ed0259340db4eb1f07fcc4c5e8a0/research/astra-e2-p0-audit-2026-10-24/REVIEW.md)はPASS。Linuxで新8テスト、要求変更、復旧改変5例の拒否、展開物からの受入と再構築を確認した。Windows候補とLinux再構築のZIPは全バイト一致した。

初回再構築の成功ログと後刻のZIP実体が食い違った一件は原因未特定。別出力先での再構築と実ファイルの全バイト一致を確認した事実と区別し、報告に残している。

## 初見AIの受入

履歴を渡さない別AIを一つ起動し、P0 ZIPと短い課題文から試験した。Windows/Python 3.12.14で、次が成立した。

- 不成立の要求への変更と実行拒否、元要求への復帰。
- 初回読出し4、復帰後の追加数値読出し0。
- 第一輪完了で保存し、別プロセスで同じ状態へ復旧。
- 三輪と上位セルの認証完了、STOPPED、在庫9。

実装コードの閲覧や、運動に関する補足説明は要さなかった。使えるPython実行ファイルの選択と文書の作業フォルダーの基準は、今回の起動案内へ補足した。これは一回の初見受入であり、あらゆる環境・AIへの一般保証ではない。

## 起動案内の確認範囲

[確認記録](../research/p0-startup-guide-v001/startup-check.json)。PowerShellで、配布物外の空白を含む作業フォルダーから、Python 3.12.14での照合、3.14.3でのUNBOUND起動と既存CLOSED1記録からの再開を確認した。

Bash記法の案内は今回実行していない。P0本体のLinux保証には前述の独立監査を使う。今回は起動手順の補足に絞り、模型の変更、三輪の重複実行、全件検査、追加AIや独立監査の起動は行っていない。

## E3の現在の監査範囲

[AstraのE3固定監査](https://github.com/residual-chart-lab/time-engine/blob/0dd5e8b71cc094a69c50a8d8c6899581789d505e/research/astra-e3-audit-2026-10-24/REVIEW.md)は、`ccc0b93840e207ce9c3b2630acdf359a66bc2b54`の表示層・保存互換・読書案内をPASSとした。Linuxの14テストを通過し、P0の全監査は再実行していない。今回の構築元の明記は、その監査の手順指摘への補修。E3の実装をP0 ZIPへ入れたという意味ではない。

配布ファイルと公開先の役割は[P0の配布準備と受渡し](P0_RELEASE_HANDOFF.md)にまとめた。
