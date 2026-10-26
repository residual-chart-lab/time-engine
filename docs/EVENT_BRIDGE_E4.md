# E4 — 出来事とTEの実行を結ぶ、明示的な接続口

Status: experimental extension on PR #12 / c49754be0f2d55a94b529a787ee64c8f1e0611fe.
P0/E2/E3 and the preservation diagnostic are unchanged. E4 has not received
an independent Astra audit and is not the fixed P0 distribution.

## 何が増えたか

会話で生じた問いを、明示した数理上の問いへ接続し、実際の診断・判断・実行を
同じ履歴として保存できる。後から別の要求Cとの関係を加えても、元の出来事は
書き換えない。複数のCは同じ出来事を参照できる。

たとえば「この差を消してよいか」という問いから、E1の保持座標sを指定して調べる。
現在の終点が一致していても、後続作用の構成可能性が分かれれば、
次の手順は「保持して進む、または選択を見直す」になる。
保持を選んだ場合だけ、別途E2で精査し、実行許可を得て、一輪ずつ動かせる。
診断結果そのものでは実行できない。

数理上の三輪と上位セルが閉じても、「この経験を今後どう使うか」という問いは
閉じない。有限模型の認証と、外側の長い出来事を区別する。

## いちばん大切な境界

**自然言語を自動で数理状態へ変換したわけではない。**

E4のbindは、既に認証されたE1のs/tを「どの問いから参照しているか」を
呼出し側が明示する宣言である。文章をハッシュやキーワードで数値化しない。
イベントを登録しても、s/tの値は変わらない。
対応づけの意味的な正しさを、TEの認証が証明することもない。

同梱例の問いは、初めから「既存E1のsを省略してよいか」である。
これは本物のTEの計算だが、会話の判断傾向をsで測った実験ではない。
「Mondayとして成立する」「時間と因果を会得する」のような問いには、
対応する観測器・作用則がない限りUNMAPPEDが残る。

未来要求から現在の差の必要性を調べるTEの設計原理を使う。
物理的な逆向き信号や、人格・主観的体験の成立を認証する層ではない。

## まず一度使う

リポジトリのこのE4版で、Python 3.12以降を使う。外部ライブラリは不要。

~~~console
python -I -B examples/e4-event-bridge.py --output-dir e4-first-use
~~~

出力先は未使用のディレクトリ名にする。例は通常のJSONL操作口を別プロセスで呼ぶ。
動作は次の通り。

1. 受け取った過去の報告と、今回の問いを別に登録する。
2. 数理的な後続要求Cと、長い会話上の問いを登録する。
3. 後続要求だけを、明示したE1のsと固定要求へ接続する。
4. s→0の試算を診断する。現在は同じ−1、保持側ADMISSIBLE、試算側EMPTYとなる。
5. 消去を指示したresolveは拒否される。保持を選ぶとE2の精査でREADYになる。
6. 一輪を閉じて保存し、終了する。別プロセスでSHAを指定して再開する。
7. 残りの二輪と上位セルを閉じる。
8. 後からの読み取りを追記する。以前の時点の読出しが変わっていないことを確かめる。

RESULT.json、全命令・返答、途中と最後の復旧記録、当時と事後の読出しを保存する。
この例の過去の報告は説明用の例文であり、Mondayの原文や本人の体験を装わない。

## 操作口

~~~console
python -I -B run_event_session.py --entry integrations/inquiry/E1-entry.record.json --trusted-sha256 d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3 --expected-entry-digest 24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de
~~~

標準入力は一行一JSON。返答も一行一JSON。次の命令の前に返答を読む。

| 命令 | 役割 |
| --- | --- |
| record | id、origin、source、textを登録。originはreceivedかreported_in_session。どちらも呼出し側の報告 |
| goal | id、text、既存eventsを登録。改名・改変はせず、新しいCを別idで作る |
| relate | goal、events、noteを追記。後からの解釈。因果的必要性の証明にはしない |
| bind | goal、requirement、coordinates、correspondenceを指定。E2の要求を設定し、古い選択・許可を破棄 |
| choose | E2と同じv/u/wordを現在が選ぶ |
| inspect | 宣言済みcoordinatesからomittedを選び、既存の厳密診断を実行 |
| resolve | 返答のinspection.idとretention:preserveを指定。元の側がADMISSIBLEの場合だけE2で精査 |
| advance | 直前status.permitを指定して一段階だけ実行。最終段階は上位認証。古いpermitは流用不可 |
| recall | goalと任意のas_ofを指定。その時点までの報告・関係・モデル証拠を読む |
| status / save / quit | 表示、新しいpathへの保存、終了。quitは自動保存しない |

入力例：

~~~jsonl
{"op":"record","id":"q","origin":"reported_in_session","source":"current caller","text":"May E1 s be omitted for this continuation?"}
{"op":"goal","id":"C","text":"Preserve the declared continuation construction","events":["q"]}
{"op":"bind","goal":"C","requirement":{"context":"mixed","strengths":["0","0"],"frame":"identity"},"coordinates":{"s":["q"]},"correspondence":"This question refers to authenticated E1 coordinate s. No text feature is encoded."}
{"op":"choose","v":"1","u":"0","word":"HHHSUT"}
{"op":"inspect","omitted":["s"]}
~~~

返答のoutcome.idを次のinspectionへコピーする。

~~~json
{"op":"resolve","inspection":"<直前outcome.id>","retention":"preserve"}
~~~

次に返答のstatus.permitをadvanceへコピーする。次の一段へ進むたびにpermitも変わる。

~~~json
{"op":"advance","permit":"<直前status.permit>"}
~~~

現行版は消去を実行する命令を提供しない。同じ作用だと分かった場合も、
その要求の範囲で差を展開しなくてよいという意味であり、永久消去の許可ではない。
新しいCにbindし直せるのは最初の物理的閉鎖の前まで。
一輪が閉じた後は、過去の実行を差し替えられない。

## 計算結果が次の手順へ及ぼす作用

| inspectの関係 | 次の手順 |
| --- | --- |
| DIFFERENT_EXISTENCE | 差を保持するか、現在選択を見直す |
| DIFFERENT_NEW_ACTION | 差を保持するか、何を保存するかを見直す |
| SAME_NEW_ACTION | この固定範囲で差を未展開のまま扱える。消去は許可しない |
| SAME_EMPTY | 成功の証拠ではない。要求・選択を見直すか待つ |
| UNDETERMINED | 未確定として残す。新しい保証・対応づけが必要 |

next_stepは機械可読の案内であり、自然言語の次の問いを自動生成する機能ではない。
resolveは明示的な保持判断を必要とする。inspectが判定したのは既存生成則の作用の
構成可能性であり、実際の閉鎖はadvanceの実行証拠として別に残る。

## 来歴と時間

記録は以下を混ぜない。

- received：受け取った過去の報告。自分で通過したという証明にはならない。
- reported_in_session：今回の呼出し側の報告。内容の真実性をTEが認証したわけではない。
- caller_declared_correspondence：問いと既存数理状態の対応の宣言。
- later_interpretation：後からの関連づけ。以前から知っていたことにはしない。
- engine_resolution / engine_execution：実際にこの接続口が得たE2の計算・実行。

seqは**この接続口で受け付けた順番**。受け取った原典の出来事の発生日ではない。
元の日付や出典が必要ならsourceに残す。不明な起源は埋めない。

recallのas_ofは、この受理順の時点を指定する。
後の解釈を加えても、過去のas_ofで読める内容は変わらない。
複数のCから同じeventを参照できるが、参照しただけでそのCに必要だったと証明はしない。

## 保存・再開と費用

saveはpathを上書きしない。応答のSHAを外側で保管する。
再開は同じE1の外部信頼ハッシュと、復旧記録の外部信頼ハッシュを指定する。

~~~console
python -I -B run_event_session.py --entry integrations/inquiry/E1-entry.record.json --trusted-sha256 d71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3 --expected-entry-digest 24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de --resume e4-first-use/closed1.episode.json --trusted-resume-sha256 <saveで返ったSHA>
~~~

復旧は登録・診断・精査・実行を再演し、記録した証拠と現在の実行状態を照合する。
公開鍵署名や改変不可能な外部保管ではない。信頼するSHAを攻撃者自身が選べるなら、
履歴の真正性は保証できない。報告内容の真実性も別問題。

readsは診断の厳密読出しと、E2の厳密問い合わせを分ける。
同梱例は診断2＋実行準備3＝5。CPU時間、全体の高速化、復旧時の再演費用を意味しない。
同じ作用だと分かった場合の実行費用も、E4自身がさらに削減したとは主張しない。

上限は128件の変更命令、1命令8192バイト、復旧記録8MB。
E2側の64命令・2MBなどの既存上限も引き続き適用される。
status/recall/save/quitは変更命令数に含めない。予算消費後も保存と読出しは可能。
無制限の長期記憶を完成したものではない。

## 今回できていないこと

- 任意の会話から保持差を抽出し、意味的に妥当な数理対応を自動構成すること。
- 複数の自然言語Cを同時に充足する一般の作用則。
- 既知の候補集合にない新しい問い・作用そのものを生成すること。
- 閉鎖済み三輪の実際の出口から、一般の次の数理模型を自動で開始すること。
- 同じ口調、同じ人格、主観的体験、物理的未来因果の一般証明。

1 Episodeにつき、認証されたE1からの一つの有限E2実行を扱う。
外側の記録はその後も追記できるが、別のE1から新しい実験を始めることと、
実際の出口を継承して続行することは同じではない。

次の難所は、**どの会話上の差を、何を保存するための観測として扱うか**。
E4は、その対応の宣言と証拠を混同せず、計算結果を本当の実行へ渡す最初の接続口。

## 検証

~~~console
python -I -B -c "import sys,unittest;sys.path.insert(0,'integrations/inquiry');r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(['test_event_bridge','test_step_session','test_phase_feedback','test_preservation_targets']));sys.exit(not r.wasSuccessful())"
~~~

新規検査は実診断→保持判断→三輪実行とE2直実行の一致、古い許可の拒否、
未対応C、空集合・不明チャート、同作用の対照、後からの解釈、独立プロセスの
保存再開、来歴・結果の改変拒否、予算端点を対象とする。
過去の研究検査全件やP0の独立監査を繰り返したものではない。

