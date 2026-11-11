# E2 — 状態を保持して一輪ずつ進める

2026-10-24。監査済みE1と既存RR69実行器の上に追加した、標準入出力の薄い操作系。数理・入口の認証条件・三輪の運動式は変更していない。

## 起動

リポジトリのルートで、Pythonから起動する。標準出力には一行ずつJSONを返す。AIは同じプロセスの標準入力へ命令を送り続けられる。

```text
python -I run_time_engine.py --entry integrations/inquiry/E1-entry.record.json --trusted-sha256 d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3 --expected-entry-digest 24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de
```

最初の応答は `event: received`、`phase: UNBOUND`、在庫6。入口の受入と保存済み過去の検証再演はこの起動時に一度行う。通常の各操作で入口を読み直さない。

続いて以下を一行ずつ渡す。

```jsonl
{"op":"bind","requirement":{"context":"mixed","strengths":["1/1024","1/1024"],"frame":"split"}}
{"op":"choose","v":"1","u":"0","word":"HHHSUT"}
{"op":"resolve"}
{"op":"advance"}
{"op":"advance"}
{"op":"advance"}
{"op":"advance"}
{"op":"status"}
{"op":"quit"}
```

そのまま使える入力は `examples/e2-three-flowers.jsonl`。POSIXシェルではそのファイルを標準入力へリダイレクトできる。PowerShellでは次のように渡す。

```powershell
Get-Content examples/e2-three-flowers.jsonl | python -I run_time_engine.py --entry integrations/inquiry/E1-entry.record.json --trusted-sha256 d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3 --expected-entry-digest 24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de
```

## 操作と止まる単位

| 操作 | 結果 |
|---|---|
| `bind` | 要求を束縛。以前の計画・成立許可は外し、`BOUND`へ進む |
| `choose` | 現在の選択を指定。`CHOSEN`へ進む |
| `resolve` | 要求に必要な観測を読み、`READY`または`REJECTED`を返す |
| `advance` | 一輪閉鎖して `CLOSED1`、`CLOSED2`、`CLOSED3`。その次は上位セルを認証して `STOPPED` |
| `status` | 現在の状態を読む。運動や命令履歴を進めない |
| `save` | 現時点の復旧記録を、新しいファイルへ書き出す |
| `quit` | 現在の状態を返してプロセスを終了する。自動保存はしない |

一輪を閉じた後は、次の命令が来るまで進まない。`REJECTED`からの実行、不成立の要求への旧許可の流用、閉じた一輪の要求変更や選び直しは拒否する。

## 支持する要求と選択

- contextは `mixed`、`main`、`zero_head`、`outside_chart`。後二つは拒否・不成立側を調べるための既存入力も含む。
- 二つの接続strengthは、それぞれ厳密な `0` または `1/1024`。
- frameは `identity` または `split`。
- 任意のdomainを調べる場合は `"domain":["下限","上限"]` をrequirementに追加できる。
- 現在のvは既存範囲の `-64,0,1,64`、uは `-1,0,1`。wordは `HHHSUT` または `HHHUST`。
- 有理数は `"1/1024"` のような文字列、または整数で渡す。浮動小数点値は受け付けない。

固定した原始運動・source族を使う有限模型であり、任意の自然言語要求を解釈する操作系ではない。

## キャッシュを保持し、許可は判定し直す

まだ一輪も実行していない段階なら `bind` で要求を変えられる。その際、同じ入口の正規な観測キャッシュを保持する。現在選択・計画・Actionは引き継がず、新しい要求で `choose`、`resolve` を行う。

同じ入口・要求・選択の再精査では、元値Vaultと派生値Vaultの数値読出しを禁止しても、同じActionが得られた。追加の数値読出しは0。出所・値・計画の検証や、式の評価費用は残る。

`status.last_resolution_work` は直近の精査が報告した費用、`numerical_reads` はその数値読出し回数の累計。総CPU時間や、検証内部のすべての演算回数を測る指標ではない。

## 保存と再開

閉じた第一輪で止めたまま、例えば次を送る。保存先は既存の親フォルダー内の新しいファイルにする。

```jsonl
{"op":"save","path":"e2-closed-first.json"}
{"op":"quit"}
```

応答のSHA-256を記録と別に保持する。既存ファイルを上書きしない。

```text
python -I run_time_engine.py --entry integrations/inquiry/E1-entry.record.json --trusted-sha256 d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3 --expected-entry-digest 24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de --resume e2-closed-first.json --trusted-resume-sha256 <保存応答のSHA-256>
```

再開は入口を一度受け取り、要求変更を含めた成功命令の全順序を再演し、保持観測・実状態・履歴を照合する。操作のたびに保存読込を往復しない。保存は復旧用の段階境界に置く。復旧時の再演費用をゼロとは数えない。

## 検証と範囲

```text
python -I integrations/inquiry/validate_step_session.py
```

新規8テストが通過。追加読出し0の再精査、要求分離、閉じた過去の変更拒否、第一輪からの再開、改変拒否、上限、実際のJSON-lines CLIを確認した。CLIの各プロセスで入口読込は1回。七つの過去生成器を禁止しても動いた。完了時の全物理履歴とgraph以外の保存項目は既存RR69と厳密に一致。

Python 3.12.14で第一輪を保存し、同じWindows PCのPython 3.14.3でCLIから再開、残り二輪と上位認証まで通過した。結果とログは `integrations/inquiry/E2-*` に収録。再実行時の一時出力は `.work/e2-validation/`。

E1のLinux試験はAstraの監査結果として参照する。この記録の作成時点ではE2のLinux実行は未実施。その後、[E2/P0固定監査](https://github.com/residual-chart-lab/time-engine/blob/1583d9a84800ed0259340db4eb1f07fcc4c5e8a0/research/astra-e2-p0-audit-2026-10-24/REVIEW.md)でLinux実行と保存再開が通過した。E1の42件や既存全247件は重複実行していない。監査済みの元409ファイルと入口実装は変更していない。

操作履歴は成功命令64件、入力一行16,384 bytes、復旧記録2,000,000 bytesを上限とする。入口の上限と混同しない。この版の用途は有限三輪。常時稼働やregistryの長期容量管理を実装したものではない。ローカルプロセスで使う操作口であり、同一プロセス内の悪意あるPythonコードの隔離や、ネットワークサービスの認証を担うものではない。
