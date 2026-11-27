# TE継続プレビュー：最初の一周

Python 3.12以降と、書き込めるローカルフォルダーで使う技術プレビューです。ネット接続や外部ライブラリは実行時に不要です。

v0.1の作業場も、そのまま新版の `continuity.py --workspace <既存の場所> resume` で開けます。作業場は初期化時のバックエンドを絶対パスとSHAで参照するため、以前の `open_use/` は元の場所に置いてください。

## 合成サンプルで試す

ZIPを展開し、このファイルのあるフォルダーで実行します。
Windowsでは深い階層を避け、短い場所へ展開してください。

```console
python -I -B -X utf8 make_demo.py --workspace demo-room
python -I -B -X utf8 continuity.py --workspace demo-room resume
python -I -B -X utf8 continuity.py --workspace demo-room source --id s000029
```

最初のコマンドは架空の29発言と6意味記録を作り、採用中の5記録を実TEから取得します。`source`は原文倉庫から正確な本文・話者・時点・SHAを取得します。`demo-room`が既にあれば別名を選んでください。

## 案と決定を一緒に読み返す

入口札に二つの案が出ました。「札の文面が決まった」と引き継ぐとき、昨日の案を採っても同じ要約になるでしょうか。なるなら、採用した案の原文と、それに決めた発言を一枚のしおりで結べます。上のデモで確かめるには次を実行してください。

```console
python -I -B -X utf8 continuity.py --workspace demo-room read --id demo-outcome --bookmark
```

`sources.proposal.text` に受付係の提案、`sources.decision.text` に進行係の「受付係の文に決めます」が戻ります。それぞれのIDとSHA-256も返ります。`resume` では採用中の記録に参照が載り、原文は必要になったときに開けます。

自分で記録する場合は、次の例を `sign.json` として保存し、`note --file sign.json` へ渡します。IDはその作業場の `capture` が返したものを使います。この例は上のデモでも試せます。

```json
{
  "id": "sign-choice", "kind": "reading", "actor": "recorder", "actor_role": "main",
  "reading_time": "current", "slot": "sign", "adoption": "adopt",
  "payload": {"reading": "入口札の文面が決まった"},
  "sources": ["s000025", "s000026"],
  "decision_bookmark": {"state": "adopted", "proposal": "s000025", "decision": "s000026"}
}
```

| 読めた範囲 | state | 結ぶ原文 |
|---|---|---|
| どの案を採ったか明示されている | `adopted` | `proposal` に採った案、`decision` にその決定 |
| 決めるのを見送った発言がある | `deferred` | `decision` に保留の発言。案を指せるときは `proposal` も指定可 |
| 手元で確認できたのは提案まで | `proposal_only` | `proposal` のみ。その後どう決まったかは開いたまま |

しおりの各IDを同じ記録の `sources` に含めます。一つの発言で提案してその場で決めた場合、両方の役に同じIDを使えます。TEは原文の実在と保存時の指紋を照合します。その発言が何を決めたかは記録者の読みとして残ります。`adoption` は再開時のスロットにこの記録を置く指定です。後で決定が届いたら、新しいIDの記録を同じスロットに置けば、以前の記録は元のIDから読み直せます。

## 自分の仕事に使う

```console
python -I -B -X utf8 continuity.py --workspace my-room init --backend open_use/te_use.py --work "my ongoing work"
python -I -B -X utf8 continuity.py --workspace my-room capture --session my-session.jsonl --start-marker "my capture boundary"
python -I -B -X utf8 continuity.py --workspace my-room resume
```

指定した一つの対応形式session.jsonlから、ユーザーのテキストと最終回答を受信します。対応形式はサンプルと`continuity.py`を参照してください。ほかの製品の会話や全チャットを自動取得する機能ではありません。`note --file <JSON>`で作成者を明記した読みを別に残し、後から採用を選び直せます。

`BOOTSTRAP.json`と`RESUME.json`を次の担当への入口にします。文面だけを受け取った場合と、本人が実TEから取得した場合は分けます。要約で足りれば原文取得は不要です。正確な引用が必要なら原文IDへ戻り、取得できない環境ではIDを指定して担当へ照会してください。

## 試験を監査可能にする

`trial_evidence.py`は任意の研究用部品です。課題本文を受け手の起動前に固定し、実際の返却バイト・受領票・提出原バイトを保存します。未実行の保存用DBと実行用DBを分け、指紋を照合します。

これは現在の固定ケース用のハーネスで、`prepare()`はsource ID `s000029`と「僕は黙って」で始まる行、A/Bの全5段階を前提にします。合成サンプルはその前提を満たします。一般的な課題生成や意味の自動検出まで実装したものではありません。

検査を実行する場合は `python -I -B -X utf8 test_continuity.py` と `python -I -B -X utf8 test_trial_evidence.py`。それぞれ20件と22件を調べます。作業用ファイルはこのフォルダーの`work`へ残します。

状態置場には後から個人の原文が入ります。初回の配布ZIPの指紋と、自分の作業状態の指紋を別に保管してください。
