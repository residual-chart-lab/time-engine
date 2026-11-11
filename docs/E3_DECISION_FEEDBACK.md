# E3 — 判定の理由と次操作を応答する

2026-10-24。次候補用の小さな強化。監査済みP0 ZIPはそのまま保持する。

E2の薄い操作口は、内部で区別している判定を外側では `REJECTED` としてまとめていた。E3は、既に得られた判定と、現在の段階で送れる操作の種類をstatusへ追加する。新しい判定法や運動式は足していない。

## 追加する四つの項目

| 項目 | 意味 |
|---|---|
| `plan_status` | 現在の要求・選択に対する観測構成の状態。未選択ならnull |
| `assessment_status` | 現在のActionが持つ既存の判定。精査前ならnull |
| `phase_operations` | 現在の段階と命令予算から送れる操作の種類 |
| `commands_remaining` | 成功命令64件の上限までの残数 |

従来の項目は維持する。新しい項目は既存の判定を読み出す表示であり、成立許可の発行器ではない。クライアントは必要な項目を読めばよく、追加項目をcheckpointへ書き戻す必要はない。

`plan_status=AVAILABLE` は十分な観測を構成できたという状態であり、実際の成立判定とは別である。

## REJECTEDの中で分けること

| `assessment_status` | 既存実行器が返した意味 |
|---|---|
| `ADMISSIBLE` | 指定した要求・現在選択に対して、作用を準備できた |
| `EMPTY` | 今回の指定候補・補正族・範囲で成立しない |
| `UNKNOWN_CHART` | 関係する文脈が認証する範囲の外。成立可能性の結論にしない |
| `UNDETERMINED_FIRST_BOUNDARY` | 最初の非空境界を認証できない |
| `UNDETERMINED_SINGULAR` | 特異な除算などにより判定を確定できない |
| その他の構成器の状態 | 内部の状態名をそのまま返す。新しい不成立定理として扱わない |

現在のCだけでなく、構成された後続文脈で範囲外になる場合もある。`EMPTY`も、他の全ての選択や模型一般の不成立を述べるものではない。

## 次操作は段階の案内

通常は、UNBOUNDではbind、CHOSENではresolve、READYではadvance、CLOSED1〜3ではadvanceへ進める。第一輪を実行する前は、bindやchooseによる変更の自由も残る。STOPPEDはstatus/save/quitとなる。

命令予算が尽きた場合もstatus/save/quitを表示する。保存先の存在やサイズ上限など、各操作の引数・実行時の検証は別に行う。返されたリストに含まれることは、任意の引数で必ず成功する保証ではない。

`ADMISSIBLE`は実行後も最後の判定として残り得る。現在動けるかはphaseと実行側の検査で決まり、この表示だけで動かしてよいとはしない。返されたリストを書き換えても、実行側の検査は変わらない。

## 保持と互換性

要求をbindし直すと旧Plan/Actionが外れるため、新しい判定表示もnullになる。精査は新要求で行い、正規の観測は再利用できる。表示の取得で数値読出しや履歴の変更を行わない。

checkpointの形式・要求・保持値・実履歴は変更していない。初見受入で実際に作られた旧P0のCLOSED1記録をfixtureとして固定した。

SHA-256: `7eeacc493777697c6dec70831b9307f20918edc1d6fd566fe08d61582199a476`

E3で読んで表示を取得しても、同じcheckpointのバイト列を保持した。そこから第二輪・第三輪・上位認証まで成立した。

## 検証

```text
python -I integrations/inquiry/validate_phase_feedback.py
```

新3件＋既存E2の8件、計11テストがWindows Python 3.12.14で通過。

- 実CLIでmixed → outside_chart → zero_head → mixedへ要求を変更。判定はADMISSIBLE → UNKNOWN_CHART → EMPTY → ADMISSIBLE。
- bind/choose時に古い判定表示が残らず、statusだけを読んでも状態が変わらない。
- 元要求への復帰は追加数値読出し0。
- 旧P0の保存記録がバイト一致で再開でき、表示取得の数値読出しを禁止しても動く。
- 三輪完了後に表示リストを書き換えても、余分なadvanceは拒否される。
- 命令予算が尽きても保存と状態確認の案内が残る。

結果は `integrations/inquiry/E3-validation.json` と `.log`。この記録の作成時点では、独立監査・Linux/別Python実行を済ませたとは数えていなかった。後述のAstra監査でLinuxの14テストが通過した。E1や過去の全件検査は繰り返していない。

## P0との版の区別

P0 ZIPの固定元sourceや同梱ファイルをE3に差し替えない。P0を再構築する場合は、監査済みP0の展開先にある `build_candidate.py`、または固定版 `f60fad90fcadaccf438c29a2f1a21bbf532dfea3` を使う。

E3作業木はP0固定元の422ファイルとは異なるので、P0専用builderはそのままではsource変更として拒否する。E3を配布する際には、別候補としてsourceを固定し、名前とSHAを付ける。今回は判定応答を強化した実行版までとする。

## 追補：表示と状態の境界

自由数を知らない受け手も状態を落とさず使えるよう、statusに`schema: time-engine-session-view-v1`を付け、要求と費用の入れ子を内部から切り離した。従来はPythonの返答中の要求を書き換えると、内部の要求記録とjournalにも影響した。今回、その再現を確認して修正した。作用の認証を突破したという結果ではない。

[状態と表示の扱い](STATE_AND_VALUE.md)に、通常利用の三つの約束と、実装を変える際の境界を記載した。表示は再開記録ではなく、値の一致だけから元の保持状態を再構成する入口は設けない。checkpoint形式は変えていない。

```text
python -I integrations/inquiry/validate_state_view.py
```

追補の新3件と、上記E3の3件・既存E2の8件を合わせて14テスト。現在のsourceと結果は`integrations/inquiry/STATE-VIEW-validation.json`、`.log`、`STATE-VIEW-PROVENANCE.json`に固定する。先の`E3-validation.*`と`E3-PROVENANCE.json`は追補前の版の記録として保持する。

- status/applyの返答の入れ子を編集しても、内部の要求・journal・費用・保存バイト列が変わらず、再開できる。表示取得の数値読出しは0。
- 外部SHAを付けた表示や数値要約でも、入口・再開記録の代わりにはならない。完全記録のcurrentだけ表示へ置き換えたものも拒否する。
- 数値と物理履歴を保ったまま保持数の由来だけを差し替えた再開記録は、SHAを計算し直しても拒否する。原記録は再開できる。この試験は搬送境界の確認であり、合法な二状態で新しい後続差を発見した実験とは数えない。

独立監査・全過去検査は追加していない。

## Astra独立監査の受入

2026-10-24。[固定監査報告](https://github.com/residual-chart-lab/time-engine/blob/0dd5e8b71cc094a69c50a8d8c6899581789d505e/research/astra-e3-audit-2026-10-24/REVIEW.md)で、`ccc0b93840e207ce9c3b2630acdf359a66bc2b54`のE3実装と読書案内がPASS。Linux CPython 3.12.14で14テストが通過し、旧P0のCLOSED1記録も同じバイト列で復旧した。

P0の構築元を明示する手順指摘を受け、P0受入状況と旧候補紹介を補修した。作用・認証・保持・checkpoint形式は変更していない。保存済みのE3検証JSON等の`independent_audit: false`は当時の出力として保持し、その後の監査は上記報告を根拠にする。E3はP0に含まれない別の固定成果であり、E3入りの新しい配布候補の梱包・受入はまだ行っていない。
