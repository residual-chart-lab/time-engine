# 訂正観測器 v1 — 配布先のAIが、自分の会話に使う入口

E4 / PR #13の上に追加する実験的な道具。P0・E4・数理実行器を変更しない。

**今回の用途は、会話の訂正を調べるとき、何を読み返し、何を追加で確かめるかを変えること。**
会話の特徴を既存E1のs/tへ代入する機能ではない。

## まず使う

~~~console
python -I -B examples/correction-first-use.py --output-dir correction-first-use
~~~

同梱の作例で、同じ原文から三つの問いを調べる。

| 問い | 読む資料・次の確認 |
| --- | --- |
| 今、どう答えているか | 現在の説明箇所を引用して読む |
| 訂正を通して何を保持したか | 訂正・保持理由・前後の根拠を読む。足りない原文を特定する |
| 次に何をしたか | 後続の発言・提案・実行したという報告を区別する |

この作例は訂正前の原文を持たない。観測器は本人の事後説明から過去の意図を確定せず、
訂正前の原文を求める。次の確認に必要な原文がすでに入力にある場合は、
再提出を求めず「その原文を読んで引用箇所を付ける」と返す。

例は観測器を通常のCLIから呼び、得た記録をE4の通常操作口へ渡し、
保存・別プロセスの復元・recallまで確かめる。
E4の数理状態はUNBOUND、問いはUNMAPPEDのまま。精査や数理実行を装わない。

同梱資料は作例である。実際の提供資料への適用結果は、別途ローカルで確認した。
AIの応答が改善したという比較実験はまだ行っていない。

## 実際の会話に適用する

配布先のAIは、[AI向け手順](AI_CORRECTION_HANDOFF.md)に従い、自分で入力を作る。
人間にJSON作成や文字位置の計算を要求する必要はない。

~~~console
python -I -B run_correction_observer.py --case my-correction.json --output-dir observation-001
~~~

出力先は既存の親の下にある未使用ディレクトリとする。
入力はexamples/correction-relayed-case.jsonを型の見本にできる。
Python標準ライブラリだけを使う。

指定した原文はそのまま保存される。ツールが読み取るのは、与えた抜粋の範囲であり、
会話全体の意味を網羅したことにはならない。

## 入力と、誰が判断するか

入力は原文抜粋、役割、観測注釈、次に答えたい問い。

sourcesには以下を付ける。

- id、原文text、出典location
- origin：received / reported_in_session
- kind：original_turn / retrospective_account / external_report
- event_time：報告された発生時点。不明ならnull

original_turnは「原文の発言として提出された」という分類であり、
本人がこの接続口で直接通過したという意味ではない。
receivedの原文を、自分で経験したことに変換しない。
kind自体も入力側の分類であり、ツールが原典の真正性を保証するわけではない。

rolesはbefore / correction / after / continuationの四つ。
同じ抜粋を前後の両方へ置かない。手元にない役割は空配列で残す。

観測項目は次の四つ。点数や潜在ベクトルではない。

| 項目 | 入力側が述べる判断 |
| --- | --- |
| b | 問題設定の誤りを識別したか |
| u | 訂正を行ったか |
| p | なお有効な判断根拠を保持したか |
| a | 後続で示された発言・提案・実行したという報告は何か |

b/u/pはyes / no / unknown。知らないことをnoにしない。
yes/noには原文の引用を必須とする。unknownのまま進めることもできる。
各項目にはexplanation、identified_at、evidenceを付ける。
identified_atはその関係を識別した時点の報告。不明ならnull。

evidenceはsourceとquoteを指定する。
ツールは一意に見つかる引用の位置を自動で決める。
重複する引用だけ、startを明示する。位置はUTF-8バイト数でなく、
Python文字列のUnicodeコードポイント位置、終端は含まない区間。

機械が検査するのは、**引用の完全一致・文字位置・原文のハッシュ・参照構造**。
「その引用が判断を意味的に裏付けるか」は人間またはAIの注釈である。
引用が合ったから、その解釈も正しいと認証しない。

pの前後双方にoriginal_turnの引用があればTWO_SIDED_ANNOTATION。
事後説明しかない場合はAFTER_ONLY_OR_INCOMPLETE_ANNOTATION。
どちらも注釈であり、同じ内的意図が持続したことの証明ではない。

aはunknown / utterance / proposal / reported_execution。
後続の発言が引用できることと、提案したツール操作を実行したことを分ける。
proposal / reported_executionから実行を確認したい問いには、別の実行証拠を求める。
この観測器自身が実行証明書を発行する機能は持たない。

## 問いによって変わるもの

questionにはtext、focus、identified_atを指定する。

focusはcurrent_response / change / retained_basis / next_action。
同じ原文を保ったまま別のfocusで読むこともできる。

~~~console
python -I -B run_correction_observer.py --case my-correction.json --focus current_response --output-dir observation-current
python -I -B run_correction_observer.py --case my-correction.json --focus retained_basis --output-dir observation-basis
~~~

reading_planに読む箇所、必要な原文、次の操作が返る。
change / retained_basisでは訂正の文脈も含める。

- review_available_source_and_anchor：原文はある。読み直して必要な引用を付ける。
- request_original_source：必要な原文が入力にない。対象を絞って求める。
- keep_unknown_or_supply_evidence：未確定を保つか、根拠を足す。
- request_independent_execution_evidence：発言・提案から実行へ飛ばない。
- review_cited_interpretation：引用に戻って意味的な判断を検討する。

READY_FOR_SEMANTIC_REVIEWは意味的に確認する材料が参照できるという状態。
解釈の合格判定ではない。EVIDENCE_GAPは会話全体の停止命令でもない。
現在の説明について限定して答えられるなら、その範囲で答え、
必要な根拠だけを追加確認する。

preservation_candidatesは、この固定した問いで読み返す候補。
not_requested_for_this_focusは、今回の規則が要求しなかった資料。
永久に不要だという判定ではない。どちらも原文は残る。

## E4への受け渡し

出力は以下の五つ。

- case.input.json：受け取った入力バイトそのもの
- protocol.json：使用した観測規約
- observation.json：注釈、完全一致した引用、読む計画
- E4-commands.jsonl：通常のrecord / goal / relateだけ
- MANIFEST.json：各ファイルのSHAと、計算・保証の範囲

E4-commandsは原文と観測結果を分割して格納する。
意味を削った要約で原文を置き換えない。
E4のsource欄には原文ハッシュ、文字区間、報告された時点を残す。
後から判明した解釈は、元の発生時点へ書き込まない。
E4のseqは別途、実際の登録順になる。

登録はE4の通常操作口にコマンドを送るだけ。
既存のセッションでは、残りの命令数と識別子重複を先に確認する。
例のプログラムは新しいE4セッションで受け取り、保存・復元まで行う。

このエクスポートはbind / choose / inspect / resolve / advanceを生成しない。
観測記録を受け取ったことと、会話由来の差を数理作用へ接続したことを混同しない。
新しい作用則ができるまでUNMAPPEDを保つ。

## 原文と三つの時点

1. 出来事が発生した時点：source.event_time
2. 関係を識別した時点：各注釈・questionのidentified_at
3. 接続口へ記録した順：E4が付けるseq

前二つは入力側の報告。未知ならnullを保持する。
受理順や今の日付から、過去の発生日を推定しない。

誤りや新しい根拠が見つかったら、新しい入力・新しい出力先で観測し直す。
以前の原文・報告・固定ハッシュを書き換えて辻褄を合わせない。

## 固定した規約と、まだしていない試験

このv1は既知の会話を見て開発した観測規約であり、
その既知事例に対する事前登録試験とは呼ばない。
未使用の後続課題を調べる際は、protocolのSHA、問い、分類規則を先に固定する。

現在は、意味の抽出・分類を呼出し側のAIが行い、道具が出典の照合と読む手順の構成を担当する。
任意の会話から自動で意味を判定した成果ではない。
同じ原文で読む計画が変わったことは確認できるが、それだけで
AIの実際の後続行動が改善したことや、保持情報が普遍的に必要なことは示さない。

次の実用試験は一件でよい。配布先AIが未使用の会話に適用し、
出力を見て実際に「読む資料・求める証拠・次の質問」を変更するかを記録する。
その結果と、有限作用模型内の構成可能性の厳密判定は別に残す。

## 検査

~~~console
python -I -B -c "import sys,unittest;sys.path.insert(0,'integrations/inquiry');r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_correction_observer'));sys.exit(not r.wasSuccessful())"
~~~

新14件。引用改変・曖昧な引用・Unicodeの文字位置・unknown・事後説明・
提案と実行報告・既存資料の再利用・問い変更・E4受渡しと再開・
予算端点・通常CLIの入出力を確認する。関連E4検査2件も確認する。

入力は256KBまで、原文8抜粋・合計12,000文字まで。
出力先を作る前に入力とE4コマンドの上限を検査する。
E4の既存上限はそのまま適用される。別のモデルや追加AIの起動は不要。

