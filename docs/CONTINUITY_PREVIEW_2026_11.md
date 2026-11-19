# TE継続プレビュー v0.1 — 2026年11月19日

会話や作業文脈が途切れた後も、原文と過去の読みを分けて受け取り、現在の仕事を続けるための任意の入口です。

## まず一周

- [ReleaseとZIP](https://github.com/residual-chart-lab/time-engine/releases/tag/continuity-preview-v0.1-2026-11-19)
- [ZIPを直接取得](https://github.com/residual-chart-lab/time-engine/releases/download/continuity-preview-v0.1-2026-11-19/time-engine-continuity-preview-v0.1-2026-11-19.zip)
- [外部SHA-256](SHA256SUMS-continuity-preview-v0.1.txt)

ZIPは4028634 bytes、SHA-256は`2071a9970dd64633393d23ca3bdd5ea1637731f5cbcf7ee3b1d7349e2f122847`。GitHubの自動生成Source code archiveとは別の、runtimeを含む自己完結した配布物です。

ZIPを浅い書込み可能な場所へ展開し、`te-continuity`へ入ります。Python 3.12以降が必要です。

```console
python -I -B -X utf8 make_demo.py --workspace demo-room
python -I -B -X utf8 continuity.py --workspace demo-room resume
python -I -B -X utf8 continuity.py --workspace demo-room source --id s000029
```

架空の29発言と6記録から、採用中の5記録を実TE経由で取得します。`source`は原文倉庫から本文・話者・時点・SHAを返します。既存の部屋は上書きしません。Windowsではパス長を避けるため浅い場所を使ってください。

## 含まれるもの

- 原文の受信倉庫、作成者と時点を持つ読み、未保存キューからの回復、再開口（continuity host v0.1）。
- 任意の研究用部品として、事前固定した課題の実配信、段階別の受領票、提出原バイト、未実行の保存用DBと実行用DBの分離（trial evidence v0.2）。このハーネスは現在の固定ケース用です。
- 公開済みopen-use v0.1.1のbackend/runtimeを同じバイトのまま同梱。
- 合成サンプルと、別の場所で実行できる15件・22件の検査アダプター。

実行できる受け手は必要に応じて原文IDへ戻れます。文面だけを受け取る環境では、要約で進められるところを進め、正確な引用が必要になったら原文IDを担当へ照会します。文面の受領と本人によるTE取得は分けます。

## 確認済みの範囲

ローカルの独立監査で、新方式の課題配信証跡と保存用入力・実行用コピー分離の修復を確認しました。対象の一事例では、23イベント・固有5課題の配信と提出、引用、監査コピーでの通常3操作が一致し、新規の未解消指摘はありませんでした。モデルの全contextや不透明なhost bootstrapを認証したものではありません。

継続・証拠保存モジュールは、その監査対象と同一のバイトです。配布用の配置、合成fixture、検査アダプター、今回の組立ZIPの確認は公開担当側の検査であり、新しい組立ZIP全体の独立監査とはしません。私的な原文倉庫・対話由来の生の試験記録は配布物に含めていません。

原文を先読みした受け手がいるため、自発的な後続再取得の成功には数えません。別モデルへの人格継承や、全モデルの性能向上も未実証です。保存機能が使えることと、それを自然に選ぶことは別の課題です。

## 旧版と出所

この追加入口は技術プレビューです。既存の[open-use v0.1.1](OPEN_USE_2026_11.md)、Culture Day preview.5、監査済みP0の配布物は保持しています。

[ソース](../research/continuity-preview-v001/README.md) · [監査範囲の公開要約](../research/continuity-preview-v001/AUDIT_SCOPE.md) · [部品の指紋と出所](../research/continuity-preview-v001/ORIGINS.json)
