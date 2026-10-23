# E1 — 記録から受け取る入口

2026-10-23。基準版main `fbf0bb413436f26b29825addccd435aace288fa3` に対する、最初の入口搬送実装。

確定した過去の記録を受け取り、その記録を検証してから、新しい要求・現在の選択へ進む。受信側で実験用の過去生成器を使わず、既存の三輪と上位セルを閉じられることを確認した。

## 受け取れる入口

この版が支持するのはRR69の対角source族、接触1/2、petal 0、gain 1、keep/erase/restoreである。任意の外部履歴を受け取る仕様ではない。上流入力には、リポジトリ内の固定RR56記録を、既存の信頼ハッシュ付きtransport経路で使う。

搬送対象は、二つの元のFlight、bootstrap後の実Engine、実際に公開されたU、数の完全な保存状態である。実状態・在庫・継承値・順序付き履歴・源の対応を含む。保持値や元の差を消去しない。

入口記録は未来要求、現在の選択、計画、実行許可を持たない。数値観測を取得する前の入口を書き出す。既に動的観測を取得した入口の書出しは拒否し、その段階の保存には既存のsession形式を使う。

## 検証と発行

`integrations/inquiry/entry_transport.py` の `dumps(entry)` と `loads(raw, trusted_sha256, expected_entry_digest)` が書出しと受入を行う。

受信時には、呼出側が別途保持した期待ハッシュと入口digestを必須にする。記録内部の自己申告だけでは受け入れない。既知の型・参照・形式、RR56入力、実際の閉鎖と公開、継承、source係数、数の元値・範囲・由来、基底とtraceを検証した後で、受信側の正規な入口を発行する。

保存済みの厳密なTE履歴は検証のために再演する。上流学習や実験用の過去生成・経路探索は行わない。したがって受入の計算費用がゼロになる仕組みではなく、受入時には保持した正確な値の照合も行う。

保存と読込には共通の上限、2,000,000 bytes・4,096 graph nodesを使う。型付きgraphの構造にも照合をかけ、余分な未参照nodeを拒否する。入口発行前に全検証を行い、不成立の記録から発行権限を残さない。

元の393ファイルは変更していない。追加した受入器が認証後の発行を担当する。

## 最短の実行

リポジトリのルートで、Pythonから実行する。公開された見本記録の期待値は次の通り。

- SHA-256: `d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3`
- entry digest: `24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de`
- 79,158 bytes、527 graph nodes。

```text
python run_entry_transport.py receive --entry integrations/inquiry/E1-entry.record.json --trusted-sha256 d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3 --expected-entry-digest 24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de
```

これは在庫6の入口を受け取る。新しい要求はまだ束縛しない。

```text
python run_entry_transport.py run --entry integrations/inquiry/E1-entry.record.json --trusted-sha256 d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3 --expected-entry-digest 24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de
```

`run` は固定の実演用要求を別途束縛する。mixed、strengths 1/1024・1/1024、split、v1/u0、HHHSUTを使い、三輪と上位セルを認証して `STOPPED`、在庫9になる。一般の要求を解釈するAI用対話入口は、このCLIにはまだ含めない。

送出側で新しい入口記録を作る場合は、未使用のファイル名を指定する。

```text
python run_entry_transport.py export --entry .work/new-entry.record.json
```

`export` の送出側は既存の登録・過去生成器を使う。出力されたSHAとdigestを記録と別に保持して受信側に渡す。

## 確認したこと

```text
python integrations/inquiry/validate_entry_transport.py
```

新しい入口検査11件と、変更していない三輪側の回帰検査31件、計42件が通過。元393ファイルのSHA-256も一致した。結果は `integrations/inquiry/E1-validation.json` と同 `.log`、出所と各追加ファイルのハッシュは `E1-PROVENANCE.json` に収録した。再実行時の出力先は `.work/e1-validation/`。

受信側は別のPythonプロセスで起動し、七つの登録・過去生成器を例外に差し替えてから入口を読む。その状態で三輪・上位セルを閉じ、RR69公開記録との完全な実データ一致、受信後に作ったcheckpointの保存・再開を確認した。追加したCLIからの実行も `STOPPED`、認証成功、在庫9を確認した。

改変した期待ハッシュ・入口識別子・数の記録・模型・源履歴・余分なgraph nodeの拒否、保存/読込の上限、入口段階以外の書出し拒否も検査した。

## 保証の範囲

RR69との一致は、復号後の実状態・在庫・全物理履歴・認証と、graph以外の保存項目についての厳密な一致である。保存時の共有参照配置が変わるため、旧checkpointとのバイト一致は主張しない。各ファイルは、それぞれの期待ハッシュで確認する。

確認したのは同一環境の別プロセスへの搬送であり、別OS・別Python環境での受入は未確認。既存全247テストの再実行は今回行っておらず、変更箇所に直結する42件に絞った。既存の厳密履歴再演・数の読込を使う範囲であり、任意長の式や任意サイズの整数を扱える新仕様ではない。

次は別環境でこの入口を受け取り、同じ検査を行う。対応する入口・要求の拡張と、共通の段階実行操作は、その後に切り出す。
