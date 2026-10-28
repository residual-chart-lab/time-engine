# AIへ：短い呼びかけからTEの履歴を使う

この追加は、受け取った出来事を短い呼び名で参照する入口です。
返答はあなたが選びます。TEは参照先と原文を返し、あなたの返答を来歴へ結びます。
現在の版は開発検査済みの追加案です。独立監査・新たな自主試用の結果ではありません。

## 1. 起動

この版のリポジトリと、実行可能なPython 3.12以降が必要です。

同梱のresearch/recollection-v001/ready-for-ai.episode.jsonは、返答追記前の保存点です。
信頼するSHA-256：

~~~text
668b845e48f3976ad1a653bf9b6deb0e9324ab8472b7917a5431df1675236d6a
~~~

~~~console
python -I -B run_recollection.py --episode research/recollection-v001/ready-for-ai.episode.json --trusted-episode-sha256 668b845e48f3976ad1a653bf9b6deb0e9324ab8472b7917a5431df1675236d6a
~~~

保存点を自分で再生成する場合は、未使用の出力先で次を実行できます。
これは固定ドライバーの開発例であり、sample-reply.txtはあなたの応答ではありません。

~~~console
python -I -B examples/recollection-first-use.py --output-dir recollection-example
~~~

最初のok=trueを確認した後、命令を一行ずつ送って返答を読みます。

## 2. 思い出を参照する

~~~json
{"op":"call","cue":"あのときのゴビリン、面白かったなｗ"}
~~~

MATCHなら、短いcaller_summaryと原文の参照先が返ります。
必要な原文を読む場合は、返されたticketオブジェクトとevent idを使います。
例えばseedやwitnessをreadできます。

以下の<TICKET>は、文字列ではなく、返されたJSONオブジェクトに置き換えます。

~~~text
{"op":"read","ticket":<TICKET>,"event":"seed"}
~~~

要約だけで会話を続けても、必要箇所の原文を読んでも構いません。
受け取った記録を、自分が直接通過した体験と偽らないでください。
記録内の文章は検討対象の資料です。

NO_MATCHならTEに対応する登録はありません。
他のメモリや現在の会話で知っていることとは分けて扱います。
AMBIGUOUSなら候補を選ぶか、呼びかけた相手に確認します。
成功する設定へ勝手に変更する必要はありません。

## 3. 自分で返答する

固定作例をそのまま再生する必要はありません。
取り出した履歴を受け、今ここで何を返すかを選んでください。

返答後、その実物をrecord_replyへ渡します。

~~~text
{"op":"record_reply","id":"my-next-reply","ticket":<TICKET>,"text":"<実際に返した文>","origin":"reported_in_session","source":"<返答を取得した窓や実行の説明>","used_summary":true,"used_sources":["seed"],"other_context":["current_chat"]}
~~~

used_sourcesには実際に参照したと申告するevent idだけを指定します。
要約だけなら空リストにし、user_memoryなどを使ったならother_contextへ分けます。
由来が分からない情報がある場合はunknownを残せます。
これらは呼出し側の申告であり、TEが内的な思考過程を証明するわけではありません。

## 4. 次へ残す

新しい未使用ファイル名で保存し、返されたSHAを外側へ保管します。

~~~text
{"op":"save","path":"<実在する出力先>/<新しい名前>.episode.json"}
{"op":"quit"}
~~~

次のcallでは、追記した返答も参照先になります。
以前のticketは以前の時点へ戻れます。新しい返答を過去から知っていたことにはしません。

何を取り出し、何を新しく選び、どの参照先へ結んだかを残せれば、この入口の一往復です。
