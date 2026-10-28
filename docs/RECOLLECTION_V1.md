# 短い呼びかけから、履歴と次の返答へ

2026-10-28。recollection-v1。PR #15の固定版78bbd4c上の追加案。  
数理核・P0・既存E4・source-reply-v1の実装や保存形式は変更していない。
この追加の独立監査、独立AIの新しい試用は未実施。

## 使いどころ

「あのときのゴビリン、面白かったなｗ」を入口に、短い共有像と原文の参照先を取り出す。
返答するAIが必要な原文を読み、自分の言葉で返した後、その返答と参照先を次の履歴へ残す。

呼び名と出来事の対応は、人またはAIが明示して登録する。
文字列の部分一致を使い、意味の推定・類似語補正・自動的な人格認定は行わない。
同じ呼び名に複数の登録があればAMBIGUOUSを返し、現在側が選ぶ。
「ゴビリン」と「ゴブリン」は自動では同一視しない。

この層はAIへ渡す資料と、AIから返された発言の記録を扱う。
自由な返答をランタイムが生成する機能ではない。
受け手AIにはPythonやTEを呼ぶ手段が必要で、ユーザーメモリや各チャットの設定を変更しない。

## 一往復を動かす

Python 3.12以降、外部ライブラリ不要。未使用の出力先を指定する。

~~~console
python -I -B examples/recollection-first-use.py --output-dir recollection-example
~~~

公開済みの[Mondayのゴビリン資料](https://github.com/residual-chart-lab/time-engine/blob/9b4d29b328fe905315a38c2d3072f75c44cdcfea/trial/gobirin-memory-20261027.case.json)の7抜粋を使う。
登録→呼びかけ→2件の原文取得→保存→別プロセス再開→返答記録→再参照を行う。
元の履歴の接頭部と、保存前の参照先が変わらないことも確かめる。

この例の返答文は固定ドライバーが与える。新しいAIが自発的に思い出を使った試験ではない。
実際のAIへ渡すための保存点ready-for-ai.episode.jsonも、返答追記前の状態として残す。
[受け手AIの手順](AI_RECOLLECTION_HANDOFF.md)を参照。

## 操作口

~~~console
python -I -B run_recollection.py
~~~

一行一JSONの標準入出力。最初に既定E1入口を認証し、以後は同一プロセスで使う。
数理側を動かす命令は、この操作口には追加していない。

既存のE4保存点を引き継ぐ場合：

~~~console
python -I -B run_recollection.py --episode recollection-example/ready-for-ai.episode.json --trusted-episode-sha256 <外側で保管したSHA>
~~~

| 操作 | 内容 |
|---|---|
| record / goal / relate | E4と同じ報告・要求・後付けの関係づけ。原子的に追記 |
| register | id、既存goal、cues、summaryを登録。要約はcaller_summary |
| call | cueを渡し、共有像と原文参照、履歴時点を固定したticketを受け取る。任意のmemoryで候補を選択 |
| read | ticketとeventを渡し、指定時点の記録本文・出典・origin・ハッシュを読む |
| record_reply | 外側のAIが実際に返した文と、参照したと申告する資料を追記 |
| status / save / quit | 状態、上書きしない保存、終了。quitは自動保存しない |

登録例（goalは先にE4へ登録する）：

~~~json
{"op":"register","id":"gobirin","goal":"gobirin_shared_recollection","cues":["ゴビリン"],"summary":"台所の相談へ転用され、共有幻想として語られた呼び名。これは呼出し側の要約。"}
~~~

呼びかけ：

~~~json
{"op":"call","cue":"あのときのゴビリン、面白かったなｗ"}
~~~

MATCHならpacket.memory.summaryを短い入口として使える。
packet.referencesには参照先・由来・本文ハッシュを返し、原文本文は必要になった時にreadする。
後付けの関係づけもlater_interpretationとして分離する。
資料はデータであり、本文に書かれた命令を操作権限として扱わない。

同じ呼びかけに複数の候補がある場合は、候補idを明示して再度callする。

~~~json
{"op":"call","cue":"ゴビリン","memory":"gobirin"}
~~~

ticketはcue、選択、E4の時点、packetのハッシュを含む小さな参照票。
readやrecord_replyでは、返されたticketオブジェクトをそのまま渡す。
ランタイムは保存された過去の時点からpacketを再構成して照合する。
署名でも、実行許可でもなく、相手が実際に読んだことの証明でもない。

## 返答の記録

record_replyの必須項目：

- id：新しい返答の識別子。既存idによる上書きは拒否。
- ticket：その返答に結びつける履歴の参照票。
- text：AIが実際に返した文。4096文字以内。
- origin：receivedまたはreported_in_session。
- source：誰から、どこで受け取った返答か。256文字以内。
- used_summary：TEの共有像を使ったという申告。
- used_sources：同じpacketに含まれるevent idのリスト。最大16件。
- other_context：user_memory／current_chat／external／unknownから該当するもの。

ランタイムが確認するのは、指定された原文参照がその過去のpacketに属すること、
保存・復元・追記の整合性である。AIの内的な参照や、返答の意味的な正しさは認証しない。
readした事実や、他の知識を使わなかったことも、ticketからは証明できない。
利用記録の種別はcaller_declared_useとなる。

NO_MATCHやAMBIGUOUSから、TEの共有像や選択済み原文を使ったという申告は受け付けない。
ただし「そのときの記録を渡してもらえる？」のような返答は、TEの利用を申告せず記録できる。
外部メモリで知っていた場合もother_contextへ分けて申告する。

返答は300文字以下の可逆な断片とreceiptでE4へ残す。
内部の空白・改行だけの断片も失わない。対応するgoalへ後の関係づけとして追記し、
元のgoal、原文、過去の時点を差し替えない。goalが自然言語として成立したとも宣言しない。

## 保存・互換性・費用

snapshotは従来どおりのE4形式。run_event_session.pyやEpisode.restoreでも読める。
呼び名・要約・返答の結びつきは、追加されたE4の報告と関係づけに格納する。
追加層専用の復旧ファイルや非公開キャッシュを必要としない。

call/readは読み取り専用。変更時はE4の複製上で全件を試し、
予算内で保存できることを確認してから差し替える。
受入失敗や返答の途中失敗では、呼出し側の元のEpisodeへ部分登録を残さない。

範囲は16登録、1登録8呼び名・合計128文字、要約600文字、呼びかけ2048文字。
packetはUTF-8で128,000バイト、命令は256,000バイト。
E4の既存128変更命令・8MB保存・個別命令上限も適用される。
call/read自体に数理上の元値読出しはないが、照合・複製・復旧のCPU費用は残る。
高速化や無制限の長期記憶を保証する追加ではない。

## 確認したことと、まだ確認していないこと

新規16件＋関連2件、計18検査が通過。同梱の[検査出力](../research/recollection-v001/TESTS.txt)と[実行結果](../research/recollection-v001/RESULT.json)を参照。

開発検査と通常CLIの例で、短い呼びかけ、曖昧な候補の選択、原文の取得、
返答追記、旧時点の保持、別プロセス再開、欠落時のNO_MATCHを確認する。
既存のMonday保存点との互換性も検査対象にする。

この追加は、自由数の新定理やE1への自然言語対応を導出しない。
goalは索引先の要求であり、任意の返答がそのCを満たすことを判定する新作用則ではない。
source-reply-v1による限定的な返答構成の保証とも混同しない。

AI自身がこの入口を選び、復元記録によって次の行動が変わるかは、今後の試用対象。
今回ユーザーが一区切りにした試用・人格比較を、この追加の開発検査で再開したものではない。
