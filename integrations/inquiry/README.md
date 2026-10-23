# 精査を始める起点と、その後の成立判定

## 二輪の要求を、最初の実行前へ引き戻す：RR64

[RR64の作用則と再現手順](../../docs/RR64_TWO_FLOWER_BUNDLE_DEMAND.md)。指定した二輪継続の共通Cから、現在候補の許容性と後続sourceの補正を計算する。修復済み自由数runtimeの有限多項式と包含区間を利用し、完成未来経路を判定前に生成しない。

```text
python run_bundle.py choices --x=-1 --later-max=12
python integrations/inquiry/validate_bundle.py
```

600照会、二輪・上位認証の実行7組、判定と作用の問いの分離、誤った消去補正の対照、履歴・自由数グラフの保存と厳密再実行を検査する。新22テストと関連検査の記録は`RR64-validation.json`、新しい出力先は`.work/rr64-local/`。主入力は計算前にコミット済みで、後から追加した補正予算の診断とは区別する。

## Cと問いPから精査し、実際の現在作用を作る：RR62

[RR62の条件・証明・結果](../../docs/RR62_DEMAND_DIRECTED_RESIDUE.md)。元の保持source Sを実際の語へ再使用し、Cと保持差によって新しいTを生成する。成立可否と作用集合の問いを分け、必要なスコープだけで保持スカラーを読む。現在の二つの語の自由と、元の差を保つ。

```text
python integrations/inquiry/validate_demand.py
```

主11群、168読出し、34実行、33成功認証。新20テスト、RR61・自由数・搬送の関連検査を使う。出力は`.work/rr62-local/`。判定の省略件数を処理全体の高速化率にはしない。

## 独立Cから現在補正を求める：RR61

[RR61の条件・証明・対照](../../docs/RR61_INDEPENDENT_C_PULLBACK.md)。未来境界を先に固定し、保持差から現在補正を求める。全first-return語族を解析的に扱い、特定の成功経路を要求へ埋め込まない。同情報の前向き対照と等価であることも示す。

```text
python integrations/inquiry/validate_pullback.py
```

主12群、42判定、38実行、36成功認証。新20テストと、RR60の18・搬送11・既存接続21を使う。登録した範囲外gainの一履歴は入力拒否として残す。出力は`.work/rr61-local/`。元のstock・履歴・終点、旧モデル・旧結果は保持する。

## 内部の接続要求から精査を起こす：RR60

[RR60の条件と結果](../../docs/RR60_INTERNAL_INQUIRY.md)。一輪を実行・認証して閉じた後、現在が次への接続を要求すると、RR53の順序付き読出しが保持差に依存するかを調べる。通知を保存してから次の文脈を構成する。特定の後文脈や後の成功結果を通知へ渡さない。

```text
python integrations/inquiry/validate_internal.py
```

主11群、新18＋RR59の12＋RR58の22＋RR53の接続21＝73テスト。主実験だけなら`python integrations/inquiry/rr60_study.py`。新しい記録は`.work/rr60-local/`へ保存し、旧版を上書きしない。

24個の独立な一輪と48接続を比較する。到来kernelで差が相殺しても文脈は変わる二つのprimitive対照、通知後に実際の二輪目が閉じる一例を含む。接続を要求する現在の選択と、接続則・強度は模型条件として残す。通知は認証や差の消去許可ではない。

## 保存した文脈で起点と成立を分ける：RR59

[RR59の条件・結果](../../docs/RR59_INQUIRY_INITIATION.md)。Python 3.10以上、標準ライブラリのみ。

```text
python integrations/inquiry/validate.py
```

主8群、新12＋RR58の22＝34テスト。新しい結果は`.work/rr59-local/`へ保存し、配布した記録を更新しない。

主実験だけなら：

```text
python integrations/inquiry/rr59_study.py
```

`inquiry_probe.py`は、到来済みの一つのkernel観測だけから、既知の残差方向が露出するかを調べ、`InspectionSignal`を返す。固定結果Fや語の合否は受け取らない。発火記録は置換判定証でも、Decoderの認証でもない。

元のsource、保持された差、過去の閉鎖・在庫・履歴は保つ。後段では非発火側も読み、元の後文脈と、その対角成分を±1/1024ずらす対照で、発火と固定結果への効果を比較する。

保存済みの文脈を模擬到来として使う。実際のLLM内部状態、未知未来の予測性能、生物の予測符号化は測定しない。手がかりの規則をTime Engineの運動から導出したとも数えない。
