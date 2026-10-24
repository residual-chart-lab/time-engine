# P0 — Pythonと作業場所を決めて始める

2026-10-24。監査済みP0の外側に付ける起動案内。P0 ZIPの中身は変更しない。

自由数の理論を先に学ぶ必要はない。**表示値が同じでも、状態まで同じとは限らない。続きを渡すときは`save`で作った記録ごと渡す。** 要求を変えたら精査し直す。詳しくは[状態と表示の扱い](STATE_AND_VALUE.md)。

最初に使うのは、導入済みのPython 3.12以降の実行ファイルと、ZIPを展開した `time-engine-p0` フォルダー。P0はWindows Python 3.12/3.14、Linux Python 3.12で動作記録がある。

## Windows / PowerShell

次の二つだけ、自分の環境の実在するパスに置き換える。`P0_ROOT` は `MANIFEST.json` と `engine` がある配布物ルートを指す。

```powershell
$P0_PYTHON = 'C:/path/to/python.exe'
$P0_ROOT = (Resolve-Path -LiteralPath 'C:/path/to/time-engine-p0').Path
& $P0_PYTHON --version
& $P0_PYTHON -I (Join-Path $P0_ROOT 'verify_package.py')
```

`python` がWindowsAppsのエイリアスを指し、ファイルアクセスエラーで起動できない事例があった。ここでは、導入済みPythonの実行ファイルを明示して使える。起動確認でPythonの版が表示されたら、その同じ実行ファイルで以後も進める。

一度だけ、実行引数を用意する。

```powershell
$P0_RUN_ARGS = @(
  '-I', (Join-Path $P0_ROOT 'engine/run_time_engine.py'),
  '--entry', (Join-Path $P0_ROOT 'engine/integrations/inquiry/E1-entry.record.json'),
  '--trusted-sha256', 'd71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3',
  '--expected-entry-digest', '24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de'
)
& $P0_PYTHON @P0_RUN_ARGS
```

起動時は `UNBOUND`、在庫6。標準入力へJSONを一行ずつ送る。現在のPowerShell作業フォルダーを配布物ルートへ変更する必要はない。

## Linux / Bash

同じ二つのパスを、実在するPython実行ファイルと展開先に置き換える。

```bash
P0_PYTHON='/absolute/path/to/python3.12'
P0_ROOT='/absolute/path/to/time-engine-p0'
"$P0_PYTHON" --version
"$P0_PYTHON" -I "$P0_ROOT/verify_package.py"
P0_RUN_ARGS=(
  -I "$P0_ROOT/engine/run_time_engine.py"
  --entry "$P0_ROOT/engine/integrations/inquiry/E1-entry.record.json"
  --trusted-sha256 d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3
  --expected-entry-digest 24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de
)
"$P0_PYTHON" "${P0_RUN_ARGS[@]}"
```

このBash記法の案内自体は、今回のWindowsでの案内確認では実行していない。P0本体のLinux動作は、独立監査の結果を参照する。

## 一輪で止めて保存する

起動後、次を一行ずつ入力する。

```jsonl
{"op":"bind","requirement":{"context":"mixed","strengths":["1/1024","1/1024"],"frame":"split"}}
{"op":"choose","v":"1","u":"0","word":"HHHSUT"}
{"op":"resolve"}
{"op":"advance"}
```

`CLOSED1` が第一輪の正常完了。その後は次の入力まで待つ。保存先には、既にある親フォルダーの中の、新しいファイル名を指定する。例のパスは自分の保存先へ置き換える。

```jsonl
{"op":"save","path":"C:/my-work/first-flower.json"}
{"op":"quit"}
```

Linuxなら、例えば `/home/me/my-work/first-flower.json` のような絶対パスを使う。返された `sha256` を保存記録と別に保持する。

相対的な保存パスは、プロセスを起動した作業フォルダーを基準にする。ここでは保存・再開とも絶対パスで揃える。

## 続きを再開する

PowerShellでは、先ほどの引数をそのまま使う。二つの文字列を実際の保存先と保存応答のSHAに置き換える。

```powershell
& $P0_PYTHON @P0_RUN_ARGS --resume 'C:/my-work/first-flower.json' --trusted-resume-sha256 '<保存応答のSHA-256>'
```

Bashでは次の形になる。

```bash
"$P0_PYTHON" "${P0_RUN_ARGS[@]}" --resume '/home/me/my-work/first-flower.json' --trusted-resume-sha256 '<保存応答のSHA-256>'
```

`resumed` / `CLOSED1` を確認してから、次を一行ずつ送る。

```jsonl
{"op":"advance"}
{"op":"advance"}
{"op":"advance"}
{"op":"quit"}
```

第二輪、第三輪、上位認証の順に進み、最後は `STOPPED`、認証成功、在庫9になる。

## 文書のパスの基準

| 文書・操作 | パスの基準 |
|---|---|
| P0最上位README | `time-engine-p0/` |
| `engine/docs/STEP_SESSION_E2.md` の「リポジトリのルート」 | `time-engine-p0/engine/` |
| この案内のモデル参照 | `P0_ROOT` に指定した絶対パス |
| JSONの `save.path` と `--resume` | 指定した絶対パス。相対なら起動した作業フォルダー |

## 固定版と観測

P0 ZIPは3,498,756 bytes、SHA-256は次の値。受渡し時は実ファイルを照合する。

`91d9218bd368d7987e13ac2a14440ad38ed84d0d227b1102f225fdb0ef89fc4d`

監査で一度、再構築の成功ログと後刻のZIP実体が一致しなかった。原因は未特定のまま記録され、別出力先での再構築は全バイト一致した。ログだけを最終ファイルの照合に代用しない。

[独立監査の固定報告](https://github.com/residual-chart-lab/time-engine/blob/1583d9a84800ed0259340db4eb1f07fcc4c5e8a0/research/astra-e2-p0-audit-2026-10-24/REVIEW.md)。ZIP内の未監査フラグは作成時点の記録であり、その後に監査PASSとなった。今回変更したのはこの外側の案内で、模型や認証条件は変更していない。
