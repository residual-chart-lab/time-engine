# 自由数を深く知りたくなったら

**使い始めるために、先に全てを学ぶ必要はない。気になった問いから、原典・実装・検証へ進める。**

自由数は独立した数学体系である。この案内は、Time Engineが使っている部分から、その数学と確かめ方へ辿るための入口。まず動かしたい場合は[P0起動案内](P0_STARTUP.md)へ。

## どこが気になった？

| 問い | 最初に読むもの | 次に辿るもの |
|---|---|---|
| 表示が同じでも、なぜ同じ状態とは言えない？ | [状態と表示の扱い](STATE_AND_VALUE.md) | [保持と置換の原則](PRINCIPLES.md) → 下の「数学の原典へ」 |
| どの範囲で、差の展開を省略できる？ | [RR58：範囲付きの置換判定](RR58_DEFERRED_RESIDUE.md) | [判定の実装](../integrations/free_numbers/deferred.py) → [検査と保存結果](../integrations/free_numbers/README.md) |
| 要求が変わると、何を読み直す？ | [RR66：同一性の解像度](RR66_ADAPTIVE_IDENTITY_RESOLUTION.md) | [RR68：読み方そのものを構成する](RR68_OBSERVATION_SYNTHESIS.md) |
| 保持した差は、本当にTEの成立へ効く？ | [RR65：混合残差と実作用集合](RR65_MIXED_RESIDUAL_ACTION_SETS.md) | [RR69：三輪への保証の接続](RR69_THREE_FLOWER_OBSERVATION_TRANSFER.md) |
| 実装を変えるなら、何を保つ？ | [保持と置換の原則](PRINCIPLES.md) | 下の「コードと根拠へ」から、変える箇所の元の検査へ |

## 数学の原典へ

TEに組み込んだ原典の固定版は、Free Numbers Coreの`9efc241d38e5ca2cd07f425b747bfb5d67ea0235`。以下の外部リンクもその版へ固定している。原典を読んでTEへ戻れるが、TEを数学の定義に置く必要はない。

| 知りたいこと | 原典 | この配布物からの参照 |
|---|---|---|
| Core v1として何が閉じたのか | [09：Core Closure Theorem](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/09-core-closure-theorem.md) | 外部の独立Core。最初に全体の到達点を確認できる |
| なぜ圧縮後の差を残すのか | [00：Capability Ledger](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/00-capability-ledger.md) | 外部。保存すべき働きを列挙する文書で、定理の証明そのものではない |
| どの同一性・観測を区別するのか | [01：Abstract Core](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/01-abstract-core.md) | 外部。抽象構成の足場・候補を読む。Core v1の確定範囲は09と照合する |
| 値が0でも、応答が異なるとは？ | [02：Conditioned Zero](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/02-conditioned-zero.md) → [03：独立性の監査](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/03-independence-audit.md) | 外部。着想・局所的な実現・そこでの証明範囲を分ける |
| TEが最初に使った、値と残差の座標は？ | [04：Length-Two Exact Splitting](../vendor/free-number-core/core/04-length-two-exact-splitting.md) | 原典を同梱。B₂の厳密な分解と応答の証明 |
| 高いgradeでは、どう復元・合成する？ | [05：長さ3](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/05-length-three-propagation.md) → [07：境界をまたぐ合成](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/07-length-four-cross-boundary-propagation.md)と[07の修正](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/07-kernel-identification-amendment.md) → [08：全gradeの復元](https://github.com/residual-chart-lab/free-number-core/blob/9efc241d38e5ca2cd07f425b747bfb5d67ea0235/core/08-all-grade-response-reconstruction.md) → 09 | 外部。原典の証明を読む道。P0が全gradeのdecoderを実装した、という意味ではない |

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

保持参照・由来・読出し計数などのruntimeは[retention.py](../vendor/free-number-runtime/runtime/free_numbers/retention.py)、有理係数の式は[algebra.py](../vendor/free-number-runtime/runtime/free_numbers/algebra.py)、保存・復元は[checkpoint.py](../vendor/free-number-runtime/runtime/free_numbers/checkpoint.py)から辿れる。[runtimeの来歴](../vendor/free-number-runtime/SOURCE.json)はCore原典の版と分けて記録している。

保存結果は、その版と条件での実行記録。修正前の検証記録のSHAを、修正後コードに対する検証と読み替えない。再計算したい場合は[自由数接続の再現手順](../integrations/free_numbers/README.md)または[要求・観測構成の再現手順](../integrations/inquiry/README.md)から、目的に合う検査を選ぶ。通常の利用のために過去の全検査を回す必要はない。

## 読んだ先で、何を試す？

たとえば、次の問いを立てられる。

- 「同じ」と見なしたのは、表示値・現在応答・成立判定・全作用・履歴のどれか。
- 置換可能性を保証した観測Pと後続作用の範囲Γは、次の要求にも合っているか。
- 必要になった差を、元の記録から再び読めるか。

今の通常操作口は、第一輪の実行前の要求・語・接続範囲の変更と、必要観測の自動精査に対応する。任意のP/Γを指定する一般の置換判定命令や、閉鎖後の新要求への変更命令はない。研究用APIで扱えることと、同じP0セッションから操作できることを分ける。

考えた検査に対応する命令がなければ、問いと不足する操作を残せばよい。その提案は次の入口を考える材料になる。現在の保証範囲を広げて成功扱いにする必要はない。

## この案内の版

2026-10-24。次候補E3とともに整備している読書案内。E3の表示追加は独立監査前であり、監査済みP0 ZIPへ差し替えていない。案内自体は新しい定理・数値実験・監査結果を追加しない。自由数Core、runtime、TEで採用した作用則、それを使うAIの行動は、それぞれの根拠へ辿って確認する。
