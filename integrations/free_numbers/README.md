# 自由数による残差保持と、指定範囲での展開省略

[基本原則](../../docs/PRINCIPLES.md) ／ [RR58の条件と結果](../../docs/RR58_DEFERRED_RESIDUE.md)。Python 3.10以上、標準ライブラリのみ。

```text
python integrations/free_numbers/validate.py
```

主10群、新22＋関連14＝36テスト。新しい結果とログは`.work/rr58-local/`へ書く。公開済みの記録や保存されたRR58の根拠を上書きしない。

主実験だけを実行する場合：

```text
python integrations/free_numbers/experiment.py
```

入力はRR57の公開済み三記録と、その中の固定した3+1・TE状態。ハッシュに束縛した搬送とexact TE再実行で読み、元のSGD・sourceの根・128継続族を再生成しない。新しい36テストはRR57の全135テストや基準版252テストの再実行とは区別する。

`deferred.py`は、残差を保持する`RetainedPair`、観測範囲`Scope`、三判定の`assess`、後続の順序を保つ`DeferredWord`、外向き整数区間による`adaptive_preview`を実装する。

`REPLACEABLE_IN_SCOPE`は、その観測で代表を使えるという保証。差の消去や、元のsource・記録・接続読出しの差し替えを許可するものではない。`UNDETERMINED`では差を残して検査範囲または精度を増やす。実際のセル認証は既存のexact経路を使う。

自由数Coreは固定版のB₂分解だけを使う。[vendorの来歴](../../vendor/free-number-core/SOURCE.json)とMIT LICENSEを同梱する。元のCoreと3+1のコードは変更しない。
