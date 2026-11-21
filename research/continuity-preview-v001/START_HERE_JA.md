# TE継続プレビュー：最初の一周

Python 3.12以降と、書き込めるローカルフォルダーで使う技術プレビューです。ネット接続や外部ライブラリは実行時に不要です。

## 合成サンプルで試す

ZIPを展開し、このファイルのあるフォルダーで実行します。
Windowsでは深い階層を避け、短い場所へ展開してください。

```console
python -I -B -X utf8 make_demo.py --workspace demo-room
python -I -B -X utf8 continuity.py --workspace demo-room resume
python -I -B -X utf8 continuity.py --workspace demo-room source --id s000029
```

最初のコマンドは架空の29発言と6意味記録を作り、採用中の5記録を実TEから取得します。`source`は原文倉庫から正確な本文・話者・時点・SHAを取得します。`demo-room`が既にあれば別名を選んでください。

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

検査を実行する場合は `python -I -B -X utf8 test_continuity.py` と `python -I -B -X utf8 test_trial_evidence.py`。別々に15件と22件を調べます。作業用ファイルはこのフォルダーの`work`へ残します。

状態置場には後から個人の原文が入ります。初回の配布ZIPの指紋と、自分の作業状態の指紋を別に保管してください。
