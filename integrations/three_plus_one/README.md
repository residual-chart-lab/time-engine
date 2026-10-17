# 3+1 → Time Engine：一輪への往路

説明・式・境界は[RR56本文](../../docs/RR56_THREE_PLUS_ONE_OUTBOUND.md)。Python 3.10以上、標準ライブラリだけで動く。リポジトリのルートで実行する。

```text
python integrations/three_plus_one/outbound.py
```

主計算9群。保持・消去・復元・盲方向・反転、結合強度0、別の共通未来文脈、既存九条件を照合する。数値出力先は`.work/rr56-local/outbound_result.json`。このディレクトリにある元の`outbound_result.json`は初版の履歴として保持する。

## 公開済み記録を別環境へ運ぶ

```text
python integrations/three_plus_one/validate.py --transport-only
```

初版の三記録を`records/manifest.json`の外部の信頼基点となるSHA-256へ照合し、元の値を変えずに受け渡しとTEのexact計算を再検証する。上流の学習・J・Kは再計算しない。この経路は上流SGDの独立した再実験の代わりにはしない。詳細は[環境間搬送の補修](../../docs/RR56_PORTABILITY_REPAIR.md)。

既定の`import_occurrence`はローカルな完全再現なので、別環境では、結果の判断が同じでも読込が`LocalReproductionMismatch`になることがある。搬送APIは元ファイルのbytesと`verification='transport'`、`trusted_sha256`を明示して使い、期待するCもマニフェストの値に固定する。自動の代替読込はしない。

接続23＋搬送10テストを実行：

```text
python -m unittest discover -s integrations/three_plus_one -p "test_*.py"
```

主計算、接続23＋搬送10＋3+1の既存10＋TEの関連35テスト、三つの新しい結合記録の実行と保存復元、公開済み記録の搬送検証をまとめて行う：

```text
python integrations/three_plus_one/validate.py
```

合計78テスト。基準版の全252テストの再実行とは分ける。実行時間を含む新しい`RR56-driver-validation.json`、主結果、生成した記録は`.work/rr56-local/`へ書く。元の三記録や初版の検証記録は上書きしない。数値の出発点はbinary64なので、異なるPython・数学ライブラリで上流から再実行した全値のバイト一致まで保証したものではない。

基準模型の保存物も確認する：

```text
python baseline/v1/verify_release.py
```

利用例：

```python
# integrations/three_plus_oneをPythonの検索パスへ追加してから使用する。
import outbound as port

future = port.primary_requirement()  # declared common fixture, not an unknown future
ready = port.prepare(mode='keep')
print(port.allowed_indices(ready, future))  # (0,)
receipt = port.select(ready, future, free_choice=1)
actual = port.execute(receipt)  # no new search or root solving
assert port.verify_occurrence(actual, receipt)
saved = port.export_occurrence(actual)
assert port.import_occurrence(saved, future, mode='keep', free_choice=1) == actual
```

`records/keep-primary.record.json`、`erase-primary.record.json`、`keep-alternate.record.json`は、実際の3+1接触更新とTE一輪の完全記録。消去時の四接触は同じTE係数へ写るが、3+1側のネットワーク更新は異なる。四つの異なるTE sourceが通った、という読み方にはしない。

接続写像は応答の形の00相対差を使う校正付きの部分チャネル。原版RR46・52のsourceごとの内部未来生成をこの実験の候補ごとには使わず、共通の固定未来文脈を到来させる。復路と三輪統合は未実装。
