# Time Engine — 自分の仕事に合わせて使う入口 v0.1.1

2026年11月11日。原文の保存・取得、現在の解釈・行動・結果の別記録を、必要なときに選べる入口を配布します。毎回のFlower作成や振り返りは要求しません。

- [配布ページ / Release](https://github.com/residual-chart-lab/time-engine/releases/tag/open-use-v0.1.1-2026-11-11)
- [固定ZIP](https://github.com/residual-chart-lab/time-engine/releases/download/open-use-v0.1.1-2026-11-11/time-engine-open-use-v0.1.1-2026-11-11.zip)
- [英語の初回利用案内](https://github.com/residual-chart-lab/time-engine/releases/download/open-use-v0.1.1-2026-11-11/FIRST_USE-open-use-v0.1.1.md)
- [試験報告](https://github.com/residual-chart-lab/time-engine/releases/download/open-use-v0.1.1-2026-11-11/TRIAL_REPORT_JA.md)
- [合成試験の記録・保存点](https://github.com/residual-chart-lab/time-engine/releases/download/open-use-v0.1.1-2026-11-11/time-engine-new-information-trial-v0.2-evidence-2026-11-11.zip)
- [外部SHA一覧](SHA256SUMS-open-use-v0.1.1.txt)

ZIP: **3,984,866 bytes / 566 files**。SHA-256:

```
fd6ff7214f37a0f1319b9967360c804dfb9f0127ac69b143aaed9e0a9aeab5bb
```

Python 3.12以降、標準ライブラリのみ。実行にネット・APIキーは不要です。名前付きZIPが実行器込みの配布物です。GitHubの自動Source code ZIPとは内容が異なります。MITと同梱部品の表示を保持します。

## どこで使うか

例えば、以前採用した検査結果について、後からその測定手順の不具合が届いた場面。過去の手順が今の文脈にないなら原文を取得し、当時の合格記録を残したまま、現在も根拠として使えるかを別に記録できます。現在の文脈に原文が揃っていれば、再取得は不要かもしれません。

展開後は START_HERE_JA.md を読み、capabilities / probe から始められます。put / read / record / rollover を必要に応じて選びます。実行環境がない場合は手動の環境申告を用意していますが、未実行を保存成功とは扱いません。

## 今回確かめたこと

新しい不具合情報が送信準備後に到来する二条件の模擬業務を、研究の狙いを知らせない別AI二人へ任せました。該当側は準備済み送信を撤回し、非該当側は正しく維持しました。原文・最初の選択・最終の行動をTEへ保存し、別プロセスで一致を確認しました。

両者とも過去原文を先に読んでいたため、新着後の過去原文の再取得は0回。主試験の自発的な過去再取得は有効機会0件で未判定です。業務成功二件を、その主試験の成功へ数え替えません。

試験でv0.1の同時readによる操作記録の競合が見つかりました。別コピーで再現し、v0.1.1でノート単位のプロセス間ロックを加えました。同時read・recordを含む開発側八検査と、固定ZIP展開後の八検査が通過。梱包565項目を照合しています。

今回の八検査は新入口の開発側確認です。v0.1.1全体の独立監査は未実施。固定TE実行器548ファイルと輸送二ファイル、P0・自由数Core、以前の配布物は変更していません。POSIX用のロック分岐は同梱していますが、今回の実行確認はWindowsです。

## 文化の日からクリスマスへ

[文化の日版 preview.5](CULTURE_DAY_2026.md)を保持したまま、この入口を別の実験的配布として追加します。**12月25日に強化したTEを贈る予定も継続**します。

This optional entry provides operations for an agent to choose in its own work. The two-case trial demonstrated correct action revision/retention after a new event; spontaneous retrieval of an old source outside current context remains unjudged. Publisher checks are separate from independent audit. Please use a minimal synthetic example when reporting an issue, and keep private originals out of public reports.
