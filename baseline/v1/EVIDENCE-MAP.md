# 成果と根拠の対応 — RR55

数値・実装は全て[RR54固定版](https://github.com/residual-chart-lab/aki-vault/tree/a67915066973a6bd5bf2c3d2fe06b0cede838b76/10_ARTIFACTS/TimeEngine/2026-10-16__chatgpt__three-flower-upper-constraint-v001)を根拠にする。同梱の`runtime/`はこの118ファイルとバイト単位で同じもの。以下のファイル名はそのruntime内を指す。

## 成果から検査へ

| 確定する内容 | 実装・保存結果 | 直接対応する既存検査 |
|---|---|---|
| 一輪の選択・実行・認証・停止 | `completed_single_flower.py`、`completed_single_flower_result.json` | `test_completed_single_flower.py::test_end_to_end_closes_one_cell_and_retains_the_actual_endpoint`、`test_only_the_actual_source_is_published_and_no_next_flower_is_requested` |
| 複数の成立履歴と、確定後の探索なしの実行 | 同上 | `test_different_free_choices_preserve_two_distinct_completed_histories`、`test_execution_and_value_resume_never_call_a_solver_search_or_local_ranker` |
| 固定要求と入口継承への束縛 | 同上 | `test_target_substitution_cannot_turn_the_approximate_endpoint_into_zero_error`、`test_consumer_inheritance_and_committed_prefix_cannot_be_replaced_on_resume` |
| 保存した差が新しい参照状態へ作用する | `retrospective_residue_readout.py`、`retrospective_residue_readout_result.json` | `test_retrospective_residue_readout.py::test_two_saved_histories_act_differently_in_the_changed_reference`、`test_actual_endpoint_gain_is_removed_by_a_declared_reading_convention` |
| 二輪の継承と文脈の変換 | `two_flower_connection.py`、`two_flower_connection_result.json`、`inheritance-transformation-audit.json` | `test_two_flower_connection.py::test_second_inherits_both_actual_tapes_accumulators_and_stock_without_reset`、`test_changed_first_history_changes_the_next_port_and_the_actual_second_source` |
| 直接接続の不成立を、指定source族の範囲で区別 | `two_flower_connection.py`のSturm列とroot count | `test_direct_port_obstruction_is_global_for_the_declared_source_line` |
| 64の局所成立と、一輪目4→1 | `three_flower_constraint_result.json`のcheck 1・2 | `test_three_flower_constraint.py::test_all_declared_three_flower_continuations_are_locally_closed`、`test_common_future_reduces_four_first_choices_to_one` |
| 後の二輪の16通りでも除外候補を救済できない | 同check 2・3 | `test_later_source_and_petal_reselection_cannot_rescue_excluded_first_choices` |
| 上位の一輪で、三作用後に初めて閉じる | 同check 4 | `test_shared_boundary_actually_closes_after_three_upper_operations`、`test_actual_upper_endpoint_is_retained_separately_from_fixed_requirement` |
| 未来文脈を変えると最初の選択も変わる | 同check 5 | `test_changing_future_frame_changes_which_first_history_is_selected` |
| 各経路に自分用の未来文脈を許すと四候補が戻る | 同check 6 | `test_unbound_future_frame_restores_all_first_choices` |
| 選別は履歴ラベルによらず、確定後は再探索しない | `three_flower_constraint.py`の`admissible`、`execute_macro` | `test_predicate_uses_actual_actions_rather_than_history_labels`、`test_committed_execution_never_searches_or_resolves_future_roots` |
| 三輪の実行と上位認証、差し替え拒否、exact保存 | `macro-occurrences/*.record.json`二件 | `test_every_connection_inherits_actual_states_and_keeps_prefixes`、`test_replaced_first_occurrence_is_rejected_against_frozen_macro_receipt`、`test_exact_json_round_trip_keeps_the_actual_macro_history` |

この対応表に挙げたテストはRR54の全252テストに含まれる。RR55で新たな数理検査を加えたという意味ではない。今回の照合器は対応するファイル・検査名の存在も確認する。

## 原本の流れ

| 段階 | 固定原本 | この版へ残すこと |
|---|---|---|
| 基本構想 | 同梱`sources/v18-original.md`、[v18固定原本](https://github.com/residual-chart-lab/aki-vault/blob/1450f74d628b214d6cb19a95d8f9a184b6e35aec/10_ARTIFACTS/TimeEngine/2026-09-13__source__v18-front-snapshot-v001/v18-closed-time-engine-rev5.md) | 過去の束縛と未来適合、出来事の認証、残差の忠実な輸送。抽象仕様の全てを実装済みとはしない |
| RR46〜48 | [RR46](https://github.com/residual-chart-lab/aki-vault/blob/7f74c095eac7fda6c9b4de385f97f2b63e833cb5/10_ARTIFACTS/TimeEngine/2026-10-14__chatgpt__intraflower-future-constraint-v001/note46-original.md)、[RR47認証修正](https://github.com/residual-chart-lab/aki-vault/blob/529e119da4525a9235138c29862e2ea2c2d1f2ed/10_ARTIFACTS/TimeEngine/2026-10-14__chatgpt__closure-causal-pullback-v002/note47-certificate-repair.md)、[RR48端点補足](https://github.com/residual-chart-lab/aki-vault/blob/0575c9a8b1323b1bcd2faa8c276344b947eb20d4/10_ARTIFACTS/TimeEngine/2026-10-15__chatgpt__local-flower-structural-stability-v002/note48-revised.md) | 一輪内部の未来適合、actualな境界で必要な差、宣言近傍での構造保存 |
| RR49〜51 | 同梱`RR49-source-map.md`〜`RR51-source-map.md`と旧結果 | 接続距離と選択則を分ける。局所argminの反例を残し、成立履歴の自由を守る |
| RR52 | [一輪再点検](https://github.com/residual-chart-lab/aki-vault/blob/0b3b27b35ce53a70bf20c29129464bbe8b679e0e/10_ARTIFACTS/TimeEngine/2026-10-16__chatgpt__completed-single-flower-v002/note52-recheck.md) | 一輪の確定・実行・保持・停止、保存した差の操作的再参照 |
| RR53 | [二輪接続](https://github.com/residual-chart-lab/aki-vault/blob/c5f46fc682411ca67d5d05cbfc864f1f50619a6c/10_ARTIFACTS/TimeEngine/2026-10-16__chatgpt__two-flower-connection-v001/note53-original.md)、[継承と変換](https://github.com/residual-chart-lab/aki-vault/blob/5d8f222a595996919842caf47807225f4669533a/10_ARTIFACTS/TimeEngine/2026-10-16__chatgpt__two-flower-connection-v002/note53-inheritance-transformation.md) | 実状態と履歴の継承、現在文脈の変換、新sourceの実行・公開 |
| RR54 | [三輪と上位要求](https://github.com/residual-chart-lab/aki-vault/blob/a67915066973a6bd5bf2c3d2fe06b0cede838b76/10_ARTIFACTS/TimeEngine/2026-10-16__chatgpt__three-flower-upper-constraint-v001/note54-original.md) | 有限模型内の4→1、全16後続の比較、二つの共通未来条件、実行と保存 |

## 要求の強まりについて混ぜない三つの結果

| 比較 | 得られた内容 | 今回の主張の範囲 |
|---|---|---|
| 同じ境界を固定し、sourceの不可視方向をずらす | RR48のw=ε/|g|が、出発点を除く指定区間で縮小 | 出発点では許容集合は空。全ての時間進行に沿う単調性ではない |
| 実際の一輪を時間順に実行する | 遠回りでも閉じる。D=2→1→2→1→0の例がある | 時刻・距離の単調減少を一輪の完成条件にしない |
| 三輪へ共通の上位未来条件を加える | RR54で一輪目4→1、除外候補の全16後続も不成立 | この共通条件・有限比較クラスの結果。輪数一般の単調強化定理ではない |

RR48の連続近傍保証は、その宣言パラメータ域の一輪に対するもの。RR54の三輪全体で同じ近傍保証を実施したとは記録しない。

## 検証の出所

RR54の`RR54-validation.json`と`RR54-driver-validation.json`には、別展開での主計算8群・全252テスト・二完了記録の再認証・結果JSONのバイト一致がある。RR55ではこれを既存の数値検証として引き継ぐ。

今回の新規確認は、118保存ファイル・公開Git blob・再現ZIPとの同一性、保存結果の正確な有理数比較、対応する検査名、仕様と再現文書の整合である。数値solverや全252テストの再実行には数えない。Astra監査の通過はアキからの報告として別ファイルへ保存し、監査原文を取得したという扱いにはしない。
