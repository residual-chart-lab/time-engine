# 自由数を深く知りたくなったら

**使い始めるために、先に全てを学ぶ必要はない。気になった問いから、原典・実装・検証へ進める。**

**自由数へ到達できる道を置く。どこまで読み、どう理解し、どこを疑うかは、受け取った側が選べる。**

自由数は独立した数学体系である。この案内は、Time Engineが使っている部分から、その数学と確かめ方へ辿るための入口。まず動かしたい場合は[P0起動案内](P0_STARTUP.md)へ。

## どこが気になった？

| 問い | 最初に読むもの | 次に辿るもの |
|---|---|---|
| 表示が同じでも、なぜ同じ状態とは言えない？ | [状態と表示の扱い](STATE_AND_VALUE.md) | [保持と置換の原則](PRINCIPLES.md) → 下の「数学の原典へ」 |
| どの範囲で、差の展開を省略できる？ | [RR58：範囲付きの置換判定](RR58_DEFERRED_RESIDUE.md) | [判定の実装](../integrations/free_numbers/deferred.py) → [検査と保存結果](../integrations/free_numbers/README.md) |
| 要求が変わると、何を読み直す？ | [RR66：同一性の解像度](RR66_ADAPTIVE_IDENTITY_RESOLUTION.md) | [RR68：読み方そのものを構成する](RR68_OBSERVATION_SYNTHESIS.md) |
| 保持した差は、本当にTEの成立へ効く？ | [RR65：混合残差と実作用集合](RR65_MIXED_RESIDUAL_ACTION_SETS.md) | [RR69：三輪への保証の接続](RR69_THREE_FLOWER_OBSERVATION_TRANSFER.md) |
| 主張に納得できない。どこを検証すればよい？ | 下の「主張を疑うとき」 | Coreの主張台帳・証明・計算証明書、TEの独立対照・監査へ |
| 今の形を守ることと、次に成立する運動を守ることは同じ？ | [保護対象を分ける](PROTECTION_TARGETS.md) | 追加の読み取り専用診断。固定P0の同梱機能・E3監査の対象外 |
| 実装を変えるなら、何を保つ？ | [保持と置換の原則](PRINCIPLES.md) | 下の「コードと根拠へ」から、変える箇所の元の検査へ |

## 数学の原典へ

TEに組み込んだ原典の固定版は、Free Numbers Coreの`9efc241d38e5ca2cd07f425b747bfb5d67ea0235`。以下の外部リンクもその版へ固定している。原典を読んでTEへ戻れるが、TEを数学の定義に置く必要はない。

| 知りたいこと | 原典 | この配布物からの参照 |
|---|---|---|
| Core v1として何が閉じたのか | [09：Core Closure Theorem](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/09-core-closure-theorem.md) | 外部の独立Core。最初に全体の到達点を確認できる |
| 何が証明・計算照合・仕様・未解決なのか | [Claims Ledger](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/CLAIMS_LEDGER.md)と[修正追補](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/CLAIMS_LEDGER_ADDENDUM_2026-07-12.md) | 外部。主張IDから根拠へ進む。追補が更新する項目は両方を確認する |
| なぜ圧縮後の差を残すのか | [00：Capability Ledger](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/00-capability-ledger.md) | 外部。保存すべき働きを列挙する文書で、定理の証明そのものではない |
| どの同一性・観測を区別するのか | [01：Abstract Core](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/01-abstract-core.md) | 外部。抽象構成の足場・候補を読む。Core v1の確定範囲は09と照合する |
| 値が0でも、応答が異なるとは？ | [02：Conditioned Zero](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/02-conditioned-zero.md) → [03：独立性の監査](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/03-independence-audit.md) | 外部。着想・局所的な実現・そこでの証明範囲を分ける |
| TEが最初に使った、値と残差の座標は？ | [04：Length-Two Exact Splitting](../vendor/free-number-core/core/04-length-two-exact-splitting.md) | 原典を同梱。B₂の厳密な分解と応答の証明 |
| 高いgradeでは、どう復元・合成する？ | [05：長さ3](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/05-length-three-propagation.md) → [07：境界をまたぐ合成](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/07-length-four-cross-boundary-propagation.md)と[07の修正](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/07-kernel-identification-amendment.md) → [08：全gradeの復元](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/08-all-grade-response-reconstruction.md) → 09 | 外部。原典の証明を読む道。P0が全gradeのdecoderを実装した、という意味ではない |

タグ`core-v1.0.0`は上記コミットを指すことを確認済み。Claims Ledgerはこの固定版へリンクする。2026-10-24の確認時、`main/CLAIMS_LEDGER.md`は404だった。

原典には研究途中のREADMEや引継ぎ文書も保存されている。その時点の未完了項目と、その後の定理・修正文書を分けて読む。09が閉じているのは、四元数の厳密応答による最初の独立Coreであり、あらゆる自由数模型の普遍分類ではない。

同梱原典の版とSHAは[SOURCE.json](../vendor/free-number-core/SOURCE.json)。ネット接続なしでも04とTE側の文書・コード・検証記録は読める。外部Core全体の取得は、P0を動かすための依存ではない。

## コードと根拠へ

関心のある主張について、説明 → 実装 → 検査 → 保存結果の順に辿れる。

| 確かめたい働き | 実装 | 検査 | 保存した結果・条件 |
|---|---|---|---|
| 指定範囲だけで代表を使い、元の差は残す | [RR58 deferred.py](../integrations/free_numbers/deferred.py) | [test_deferred.py](../integrations/free_numbers/test_deferred.py) | [RR58結果](../integrations/free_numbers/RR58-result.json)・[検証記録](../integrations/free_numbers/RR58-validation.json) |
| 要求変更後に既読の関係から復元する | [adaptive_resolution.py](../integrations/inquiry/adaptive_resolution.py) | [test_adaptive_session.py](../integrations/inquiry/test_adaptive_session.py) | [監査後の一読出し補修](../research/rr66-read-repair-v001/README.md)・[現在の補修検証](../research/rr66-read-repair-v001/repair-validation.json) |
| 要求式から十分な観測を構成する | [observation_synthesis.py](../integrations/inquiry/observation_synthesis.py)・[TEへの接続](../integrations/inquiry/synthesized_resolution.py) | [test_synthesized_session.py](../integrations/inquiry/test_synthesized_session.py) | [RR68結果](../integrations/inquiry/RR68-result.json)・[検証記録](../integrations/inquiry/RR68-validation.json) |
| 観測の保証を三輪の作用・全分母条件・閉鎖へ渡す | [three_flower_synthesis.py](../integrations/inquiry/three_flower_synthesis.py)・[段階実行](../integrations/inquiry/three_flower_session.py) | [test_three_flower_synthesis.py](../integrations/inquiry/test_three_flower_synthesis.py) | [RR69の事前入力](../integrations/inquiry/RR69-inputs.json)・[結果](../integrations/inquiry/RR69-result.json)・[検証記録](../integrations/inquiry/RR69-validation.json) |

実行層全体の使い方は、[採用Runtime v0.1.1のREADME](https://github.com/residual-chart-lab/free-number-core/blob/a9c3041a411db8f79f51d02e9f35af58f5edb2d3/runtime/README.md)と[設計・保証範囲](https://github.com/residual-chart-lab/free-number-core/blob/a9c3041a411db8f79f51d02e9f35af58f5edb2d3/research/demand-runtime-v001/DESIGN.md)へ。こちらはCore凍結後の実行層の版へ固定しており、Coreの証明と同じ版番号にはしない。

保持参照・由来・読出し計数などのruntimeは[retention.py](../vendor/free-number-runtime/runtime/free_numbers/retention.py)、有理係数の式は[algebra.py](../vendor/free-number-runtime/runtime/free_numbers/algebra.py)、保存・復元は[checkpoint.py](../vendor/free-number-runtime/runtime/free_numbers/checkpoint.py)から辿れる。[runtimeの来歴](../vendor/free-number-runtime/SOURCE.json)はCore原典の版と分けて記録している。

保存結果は、その版と条件での実行記録。修正前の検証記録のSHAを、修正後コードに対する検証と読み替えない。再計算したい場合は[自由数接続の再現手順](../integrations/free_numbers/README.md)または[要求・観測構成の再現手順](../integrations/inquiry/README.md)から、目的に合う検査を選ぶ。通常の利用のために過去の全検査を回す必要はない。

## 主張を疑うとき

案内を読んで同意する必要はない。気になった主張を、定義・仮定・証明・実行結果へ分けて検査できる。

| 疑問 | 調べる根拠 | 検査対象の範囲 |
|---|---|---|
| Coreの復元や合成の主張は正しい？ | Claims Ledgerの`FN-CORE1-001/002/004` → [Core 08の証明](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/08-all-grade-response-reconstruction.md) → [計算証明書](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/certificates/core08_all_grade_response_certificate.py) | 有限grade一般の証明と、有限例の厳密計算を分ける。計算証明書だけで全gradeの証明を代用しない |
| 置換証を別の観測や後続へ流用していない？ | [RR58の検査](../integrations/free_numbers/test_deferred.py)。`test_same_compression_does_not_justify_kernel_replacement`、`test_broader_scope_requires_a_new_certificate` | 圧縮値・kernel・境界テンソル、元の入口、指定した有限範囲を照合する |
| 観測の省略で、本来の作用や分母条件を失っていない？ | [三輪の観測構成と照合](../integrations/inquiry/three_flower_synthesis.py) → [独立な行列・連立方程式の対照](../integrations/inquiry/rr69_study.py) → [検査](../integrations/inquiry/test_three_flower_synthesis.py) | 再構成した作用全体、元の全分母、途中の境界を比較する。最後の成功値だけを根拠にしない |
| 正規の状態を受け取り、同じ履歴から再開している？ | [入口検査](../integrations/inquiry/test_entry_transport.py)・[操作/再開検査](../integrations/inquiry/test_step_session.py) → [E1独立監査](https://github.com/residual-chart-lab/time-engine/blob/f88e5b1fa1d056ad6d28f0eeb04d498cbd3ec255/research/astra-e1-audit-2026-10-23/REVIEW.md)・[E2/P0独立監査](https://github.com/residual-chart-lab/time-engine/blob/1583d9a84800ed0259340db4eb1f07fcc4c5e8a0/research/astra-e2-p0-audit-2026-10-24/REVIEW.md) | 各監査の固定版と対象範囲を読む。E3全体の独立監査や、Core全体の証明に広げない |

Claims Ledgerの`PROVED`、`EXACT-CHECK`、`LEAN`、`SPECIFICATION`、`OPEN`は異なる根拠を表す。閉鎖宣言も個別定理の証明と区別されている。修正追補には、条件付きで成立した主張と、なお未解決の主張を分けた記録がある。

検査結果を残すなら、固定版・対象の主張IDまたは箇所・入力と条件・予想・実際の結果・再現手順があればよい。定理の仮定内での反例、仕様を変えた別模型、現在の操作口では試せない提案を分けて残せる。新しい問いや反論を、こちらが用意した成功手順へ合わせる必要はない。

## 読んだ先で、何を試す？

たとえば、次の問いを立てられる。

- 「同じ」と見なしたのは、表示値・現在応答・成立判定・全作用・履歴のどれか。
- 置換可能性を保証した観測Pと後続作用の範囲Γは、次の要求にも合っているか。
- 必要になった差を、元の記録から再び読めるか。

今の通常操作口は、第一輪の実行前の要求・語・接続範囲の変更と、必要観測の自動精査に対応する。任意のP/Γを指定する一般の置換判定命令や、閉鎖後の新要求への変更命令はない。研究用APIで扱えることと、同じP0セッションから操作できることを分ける。

考えた検査に対応する命令がなければ、問いと不足する操作を残せばよい。その提案は次の入口を考える材料になる。現在の保証範囲を広げて成功扱いにする必要はない。

## この案内の版

2026-10-24。次候補E3とともに整備している読書案内。E3の実装とこの読書案内は、固定版`ccc0b938`で[Astraの独立監査](https://github.com/residual-chart-lab/time-engine/blob/0dd5e8b71cc094a69c50a8d8c6899581789d505e/research/astra-e3-audit-2026-10-24/REVIEW.md)を通過した。監査済みP0 ZIPへE3を差し替えてはいない。案内自体は新しい定理・数値実験・監査結果を追加しない。自由数Core、runtime、TEで採用した作用則、それを使うAIの行動は、それぞれの根拠へ辿って確認する。
