# 独立リポジトリへの移行記録

2026-10-17。三輪接続模型v1の再現用配置を独立リポジトリへ収録した。数理・運動則・検査条件は変更していない。Git履歴全体を移したものではなく、固定スナップショットを原典への参照付きで保存した。

## 固定した原典

| 対象 | 元コミット | 元ディレクトリ |
|---|---|---|
| RR55統合文書13件 | `90f88f1392b42f2bc0ceabf9fc05643707d2569b` | [RR55](https://github.com/residual-chart-lab/aki-vault/tree/90f88f1392b42f2bc0ceabf9fc05643707d2569b/10_ARTIFACTS/TimeEngine/2026-10-16__chatgpt__three-flower-consolidation-v001) |
| RR54実装・検証118件 | `a67915066973a6bd5bf2c3d2fe06b0cede838b76` | [RR54](https://github.com/residual-chart-lab/aki-vault/tree/a67915066973a6bd5bf2c3d2fe06b0cede838b76/10_ARTIFACTS/TimeEngine/2026-10-16__chatgpt__three-flower-upper-constraint-v001) |

統合文書を `baseline/v1/`、runtimeを `baseline/v1/runtime/` に置いた。118件のGit blob SHA・SHA-256・サイズはRR55固定マニフェストと一致する。統合文書も元のGit blob SHAと一致し、改行を含めて原本を保存した。

[全131ファイルの移行対応表](../migration/source-manifest.json)に原典パス、移行先、Git blob SHA、SHA-256、サイズを残す。新規README・この記録・接続課題は移行時の案内であり、RR55原文に含まれていたものではない。

## 今回行った検証

- 全131ファイルの元Git blob SHAとの一致。
- 既存 `verify_release.py` の成功：runtime118件、ソース45件、保存結果8群、保存テスト252件、完了記録2件、文書11件のハッシュ、根拠の検査名23参照。
- 数値solver・252テスト・完了記録の再実行はしていない。

[照合器の今回の出力](../migration/release-verification.json)にある日付2026-10-16は固定版の値。移行検証日は2026-10-17である。保存済みの過去の検証記録と、移行時に再実行した照合器を区別する。

## 継承するもの

aki-vaultの原典・研究ブランチ・失敗や監査の履歴は残す。Vault mainには開発先と節目を戻す。旧文書中の当時の「次の課題」やパスも原文として保存し、現在の入口はこのリポジトリのREADMEとする。

3+1の独立研究は[完結宣言](https://github.com/residual-chart-lab/three-plus-one/blob/8e1031827f0f1106ea3a75b02b2be0e9721bba3a/docs/RESEARCH_CLOSURE.md)を保持し、以降の接続研究はTime Engine側で行う。今回3+1本体を取り込んだり、自由数を再定義したりしていない。

公開範囲は非公開のまま。新しいライセンスは付与していない。
