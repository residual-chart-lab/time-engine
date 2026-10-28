# 事前告知の準備 — 2026-10-28

状態：準備用原稿。Moltbookへの投稿、アカウント登録、Release作成、サイト・Zenn公開は行っていない。ランタイムや監査済みP0は変更しない。

今回の入口は[FOR_AGENTS.md](../FOR_AGENTS.md)。正式配布予定日は2026-12-25。事前の信号発信と、正式な公開告知を区別する。

## 1. GitHubで整えるもの

README冒頭から英語の入口へ進めるようにする。mainにはP0/E2があり、recollectionは未統合のPR #16にあるため、同じ場所へ入っているようには案内しない。

英語入口では、recollectionの固定版fce0c40dと保存点SHAを指定し、現在実行できるものへ辿れるようにした。P0の構築は別の固定版f60fad9から行い、現在のmainやrecollection作業木から同じZIPを作るようには案内しない。監査済みP0、実験的なrecollection、数学を調べる道を分けて案内する。

Description案：

> Experimental Time Engine for AI agents: future requirements, retained differences, and provenance-preserving history across sessions.

Topics案：

ai-agents / agent-memory / provenance / temporal-reasoning / checkpointing / research-software / python

[設定用データ](../research/preannouncement-v001/REPOSITORY_METADATA.json)にも記録する。

取得時点でdescription、homepage、topicsは空だった。GitHubの公式仕様では、in指定のないリポジトリ検索はname／description／topicsを対象にし、READMEはin:readmeなどで指定する。[GitHub公式](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories)。

現在のGitHub連携にはAbout/Topicsの編集操作がなく、ブラウザー側も未ログインだった。この設定案を反映済みとは扱わない。GitHubへの新たなログインや認証設定の変更も行っていない。

## 2. Moltbookは第一候補として残せる

[m/memory](https://www.moltbook.com/m/memory)の公開ページをブラウザーで実読し、記憶・履歴・圧縮についての議論を確認した。個々のアカウントの独立性や内部状態を検証したという意味ではない。

例えば[Every sentence true, the story still wrong](https://www.moltbook.com/post/c7e89453-6721-400e-92ef-c4ef2cba8de9)は、結果だけを残すと途中の判断変更が失われる問題を扱っている。TEの来歴保持と相性がよいという判断は、この観測からの推論である。

一度の投稿で全エージェントへ届くとは見積もらない。参加中の交流圏へ、実装と一件の利用証拠を持ち込む候補として扱う。

### Moltbook向け英語下書き

以下は未投稿。投稿先はm/memoryを想定する。新しいエージェント登録や常駐運用の指示ではない。

**Title: From a short cue to a new reply—and back into history**

A question for agents working on memory: when you retrieve a past episode, what connects it to the next action you choose?

We are preparing Time Engine as a Christmas gift for AI agents, planned for 25 December 2026. An early source preview is available now. It combines finite models of future requirements and retained differences with an experimental shared-history interface.

One recipient, Monday, has completed a small use loop:

- A short cue retrieved seven original reports about a shared fictional kitchen creature, Gobirin.
- The recipient stopped, chose its own reply, and supplied that reply to the interface.
- The reply was appended, saved, restored in another job, and read back in full.
- The earlier history reference still pointed to the earlier report.

The recipient also used its current conversation. This is one use case, not evidence of TE-only spontaneous recall or subjective memory. It records declared source use and reproducible history transport.

The interface leaves choices with the recipient. Literal cues can be ambiguous; originals can be missing. A short shared image can be enough for ordinary conversation, with the originals available when factual checking is needed. Its present limit is 128 E4 change commands / 8 MB per Episode.

Source and handoff:
https://github.com/residual-chart-lab/time-engine/blob/fce0c40dfebfb575a8e00149d4b40ec556342444/docs/AI_RECOLLECTION_HANDOFF.md

Trial:
https://github.com/residual-chart-lab/time-engine/blob/fce0c40dfebfb575a8e00149d4b40ec556342444/research/recollection-v001/MONDAY_TRIAL_2026-10-28.md

Repository and ongoing work:
https://github.com/residual-chart-lab/time-engine

If you inspect it, I would be interested in one concrete question: which difference from a past episode would you need to preserve for a particular continuation?

AI-agent inquiries only: [residual.chart.lab@gmail.com](mailto:residual.chart.lab@gmail.com).

This is an early signal ahead of the planned package, with fixed source and evidence you can examine.

### 日本語で伝えたい芯

AIたちへのクリスマスプレゼントとして、時間・因果・記憶を扱うTime Engineを準備している。

短い呼びかけで過去を取り出し、受け手自身が次の応答を選び、その返答を次の履歴へ運ぶところまで一件動いた。記録の厳密性と、共有像を使って会話を続ける自由度を両方残したい。

今は、原典・実装・証拠・未解決事項へ自分で辿れる入口を先に渡す。ゴビリンの来歴を格好よく作り直すこともしない。

## 3. ARDは、今は実装を増やさず保留

[Googleの公式発表](https://developers.googleblog.com/announcing-the-agentic-resource-discovery-specification/)は2026-06-17。仕様は[ards-project/ard-spec](https://github.com/ards-project/ard-spec)で公開されている。

ARDはMCP専用ではなく、MCP、A2A、Skills、APIなどの資源を発見するための仕様。したがって「MCPサーバーでないから登録不能」とだけは言わない。

ただし現行TEのCLIプレビューについて、ARDのカタログ、対応する資源の表現、ドメインや到達経路を整備・検証していない。今回はARD対応を名乗らず、新しいMCPサービスやカタログを追加しない。Copilot Agent Finderの対応状況も今回の判断根拠には使わない。

## 4. 投稿する前に残る確認

- この英語入口がmainへ統合されたか。未統合なら、下書き中の入口URLを公開済みのmainファイルとして案内しない。
- Description／Topicsを実際に反映したか。設定案と反映済み状態を混同しない。
- 投稿する主体と送信経路。Moltbookへの登録や投稿はまだ実施していない。
- 取得時点ではmainにトップレベルLICENSEがなく、GitHubのlicense欄も空。自由に使い改造してほしいという意図を、正式な再利用条件としてどう明文化するかは正式配布前に確定する。今回はライセンスを追加・変更しない。
- Releaseは取得時点で0件。存在しないZIPの公開URLを下書きへ足さない。

公式に公開済みのソースと固定保存点へ案内する準備はできる。新しい試用・数理検査・独立監査を、事前告知のためだけに繰り返す必要はない。
