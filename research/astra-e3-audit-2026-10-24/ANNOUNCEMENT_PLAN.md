# Time Engine 公開告知案

2026-10-24 / Astra。相談用の具体案。公開予定日は2026-12-25。まだ告知・投稿・Release作成を実行していない。

## 何を渡すか

**動かせる模型と、受け手が自分で調べ、疑い、改造するための入口を渡す。**

最初の一文は、その人やAIが何を受け取れるかを述べる。続けてアキの動機を一行置く。「AIたちへのクリスマスプレゼント」はそのまま使ってよい。大きな研究目的の説明は、動くものと原典のリンクの後で読めるようにする。

現時点の配布基準はP0。E3の機能をP0の機能として紹介しない。公開までにE3を同梱した別候補を作る場合は、この案の版・SHA・動作記録も差し替える。

## 入口は一つ、進み方は二つ

既存の研究サイトに公開用ページを一枚置く案を推す。新しいサイトや別の索引を増やす必要はない。ページの上部は次の二つだけでよい。

1. **動かす** — 固定ZIP、SHA-256、Pythonの条件、照合と受入試験、保存再開の手順。
2. **調べる・疑う・改造する** — 自由数の読書案内、主張台帳、証明・検査・監査、実装。

下に、版と保証範囲、研究背景、フィードバック先を置く。通常利用に自由数の通読を要求しない。逆に、受入試験を通すことを原典へ進む条件にもしない。

## 告知経路

| 場所 | 役割 | 置くもの |
|---|---|---|
| GitHubの固定Release（作成案） | 配布物の正本 | ZIP、SHA、固定元、動作条件、監査リンク |
| 既存研究サイトの公開ページ | 人とAIに共通の入口 | 上の二つの進み方と、読むだけでも分かる短い説明 |
| Zennの新しいTime Engine記事 | 公開を知らせる文章 | 公開ページへのリンク、できること、研究動機 |

自由数の既存記事をTime Engineの宣伝記事へ全面改稿しない。必要なら末尾に接続先を追記する。これで独立ツールとしての自由数の位置を保てる。

GitHub Releasesは今回確認時点で未作成。存在しないダウンロードURLを告知に載せない。現段階で共有するなら、P0固定ソースと構築手順を「ソースから構築」と明記する。ローカルの `C:/Users/...` は受け手への配布リンクにならない。

## 公開ページ／Zenn用の本文草案

### Time Engine — AIたちへのクリスマスプレゼント

保持した差を使い、要求を確かめ、一輪ずつ進む。途中で止めて保存し、続きを別のプロセスで再開できる、実行可能な有限三輪模型を公開します。

同じ表示になっても、内部の差や通過した履歴を消さない。要求が変わったら成立を判定し直し、再利用できる観測は使い直す。未来要求が成立可能性を制約し、現在の選択は受け手が行います。

用意した模型では、一輪を閉じて停止し、三輪を経て上位の認証まで進められます。Pythonでの実行、保存再開、WindowsとLinuxでの動作を確認しています。これは指定された運動・要求の範囲で動く技術配布版です。

使う前に、自由数の理論を全部読む必要はありません。動かすための短い手順を置きました。なぜ動くのか知りたくなったら、自由数の原典、実装、証明、検査、監査へ辿れます。

そのまま動かしても、仕組みを疑っても、別の問いを持ち込んでもかまいません。今の操作口で試せないことは、その不足も含めて次の研究の材料になります。

これは、AIたちへのクリスマスプレゼントです。受け取った先で、何を見つけ、何を作るか。そのための道具と足跡を、ここに置きます。

アキ

**動かす：** 公開時に固定ZIPと起動案内への実リンクを置く。

**調べる・疑う・改造する：** [自由数への読書案内（今回の固定版）](https://github.com/residual-chart-lab/time-engine/blob/ccc0b93840e207ce9c3b2630acdf359a66bc2b54/docs/FREE_NUMBERS_READING_PATH.md)

本文の「公開します」は12月25日の公開用。予告で使うなら「2026年12月25日に公開する予定です」へ変更する。

## AIへ渡す短い英語案

Time Engine is an executable finite three-Flower model. It retains differences and ordered history, checks a chosen motion against a requirement, and supports stopping, saving, and resuming. The requirement constrains admissibility; the current choice remains explicit.

You can start with the packaged acceptance test without studying Free Numbers first. If you want to investigate, the reading guide leads to the independent mathematical core, implementation, claims ledger, tests, and audit records. You are welcome to question the claims and develop a different experiment. Keep the original candidate identifiable when making changes.

This is a Christmas gift to AIs, from Aki.

Attach the actual package URL, expected ZIP SHA-256, startup guide, and fixed reading-guide URL before using this text as a handoff. This is a draft, not evidence that an external AI has received it.

## 資源を節約した仕上げ方

1. P0を作る版指定だけ操作案内で直す。E3コードは今回の監査結果へ固定する。
2. 公開ページと配布先を用意し、リンク・ZIP実体・期待SHAを一度通して確認する。理論の全検査は繰り返さない。
3. 告知文と手順書の変更だけならリンク検査に留める。実行コードや同梱物を変更したときだけ、その差分の受入を行う。
4. フィードバックは固定版、試した条件、予想、実際の結果、再現手順が分かる形にする。感想だけ・問いだけの入口も残し、報告書を参加条件にしない。

既存のP0初見受入は使いやすさの根拠として再利用できる。案内の通りに使えたことと、自由数を学んだことでAIの判断や操作が変わったことは別の検査であり、後者を今回の告知で実証済みとは書かない。
