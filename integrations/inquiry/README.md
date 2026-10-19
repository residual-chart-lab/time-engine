# 精査を始める起点と、その後の成立判定

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
