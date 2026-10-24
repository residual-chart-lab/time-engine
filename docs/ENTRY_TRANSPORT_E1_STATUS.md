# E1 限定入口 — 固定状況

2026-10-24。PR #8の監査対象版 `0f708c1d35eda52415a24347839d122046cf595b` はAstra監査PASS。修正必須項目なし。mainへの統合は `35e402979fcaab419d2756dddc6ee7e4b4241a28`。

支持する範囲はRR69の対角source族、接触1/2、petal 0、gain 1、keep/erase/restore。新しい要求への成立許可は入口に含めない。この対応範囲を広げる変更はしていない。

[固定された監査報告](https://github.com/residual-chart-lab/time-engine/blob/f88e5b1fa1d056ad6d28f0eeb04d498cbd3ec255/research/astra-e1-audit-2026-10-23/REVIEW.md)では、42関連テスト、11改変例の拒否と発行権限不残留、要求分離、Linuxでの入口受入・三輪/上位閉鎖・保存再開を確認している。提出済みWindows 3.12/3.14の完了記録と、Linuxで再生成した完了記録のハッシュも一致した。

元のE1実装と記録は固定版のまま保持する。`ENTRY_TRANSPORT_E1.md` と `ENTRY_TRANSPORT_E1_PORTABILITY.md` の「別環境未確認」は、それぞれの初回試験時点の記述である。現時点ではWindowsのPython 3.12/3.14と、AstraによるLinux Python 3.12の結果が揃っている。E2操作系のLinux試験を済ませたという意味には使わない。

過去のexternal検査器が出力する `operating_system_changed: false` は比較を行わない固定値なので、OS搬送の根拠として使わない。実際の `runtime.platform` と、上記監査・提出記録を照合する。E2の検証報告は実際の `runtime.system` を記録する。

入口サイズ上限は2,000,000 bytes・4,096 graph nodes。署名配布サービス、任意履歴の一般受入、任意の長期CPU/メモリ上限を保証する仕様ではない。上流の学習再現と、保存されたTE履歴の厳密な検証再演は分ける。
