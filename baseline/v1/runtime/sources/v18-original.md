# Φ–Y Dock V18: Fractal Phase-Closure Time Engine
## 因果セル・残差束・相転移閉包・多重スケール時間構造

**Version:** V18 rev.5  
**Status:** Front specification / mathematical architecture  
**Last updated:** 2026-07-19

---

## 0. One-Line Core

> **タイムエンジンとは、過去制約と未来要求が切り出す因果セルを現在断面で選択し、同一生成則のもとで閉じたセルを exact residue を保持する上位操作へ相転移させる、フラクタル因果セル複体である。**

English:

> **The Time Engine is a fractal closure tower in which the same generative rule closes locally at every scale, and each terminal history phase-transitions into an upper-scale operation while retaining its exact residue.**

Core recursion:

\[
\boxed{
\text{same generative rule}
\longrightarrow
\text{local history}
\longrightarrow
\text{phase-closure}
\longrightarrow
\text{upper-scale operation}
}
\]

and again:

\[
\boxed{
\text{upper-scale operations}
\longrightarrow
\text{upper-scale history}
\longrightarrow
\text{upper phase-closure}
}
\]

---

# Part I — Position

## 1. Document Position

This document is the front specification of the Time Engine.

- `v18-closed-time-engine.md` is the current front document.
- `v17_time_engine` is retained as the derivation history and conceptual ledger.
- Free Number Core v1 is used as the exact-history and residue-preserving substrate.
- V16 spring / gear structures are retained as geometric local charts.
- The Time Engine is not defined as an AI-only module.
- AI systems may instantiate the engine, but do not determine its mathematical scope.
- This document does not yet claim a complete physical theory of time.

The dependency direction is:

\[
\boxed{
\text{Free Number Core v1}
\;\longrightarrow\;
\text{Fractal Phase-Closure Time Engine}
\;\longrightarrow\;
\text{local physical / computational realizations}
}
\]

Free Number supplies the distinction:

\[
\text{same compressed result}
\neq
\text{same exact state}.
\]

The Time Engine asks the larger question:

\[
\boxed{
\text{How do non-returning local histories form one multi-scale temporal structure?}
}
\]

---

## 2. Fundamental Repositioning

The Time Engine is not built upward by adding many independent local clocks.

The following construction is rejected as the primary definition:

\[
\text{local self-time}_1
+
\text{local self-time}_2
+
\cdots
\longrightarrow
\text{global time}.
\]

A collection of local durations does not by itself generate a common temporal structure.

The primary structure is instead a scale-recursive closure system:

\[
\mathcal T
=
\left\{
\mathcal T_k,\operatorname{PCl}_k,J_k
\right\}_{k\in K},
\]

where each \(\mathcal T_k\) is a local realization of one common generative schema, and each completed local phase becomes an operation at the next scale.

Therefore:

> **Globality is not maximal size. Globality is recursive scale belonging.**

A local clock, proper time, self-time, oscillator, process, or object is a local chart of this structure.  
Local survivability is required, but it is not the Time Engine’s primary identity.

---

# Part II-A — Causal Geometric Types

## CG1. Causal Cell

At scale \(k\), let

\[
X_k^-\in\mathcal X_k
\]

be the inherited past-side exact constraint, and let

\[
E_k^+\in\mathcal E_k
\]

be the future-side required result.

Define:

\[
\operatorname{Reach}_k^+(X_k^-)
\]

as the forward-reachable region from the past constraint, and:

\[
\operatorname{Compat}_k^-(E_k^+)
\]

as the region of histories compatible with the future requirement.

The scale-\(k\) causal cell is:

\[
\boxed{
\mathcal D_k(X_k^-,E_k^+)
:=
\operatorname{Reach}_k^+(X_k^-)
\cap
\operatorname{Compat}_k^-(E_k^+)
}
\]

At the foundation level this is called a **causal cell**. In a realization with cone-like causal reachability it may become a causal diamond.

The future requirement does not transmit a force into an instantiated past. It restricts the history region compatible with both boundaries.

Because \(\mathcal D_k\) is a causal region rather than a word space, define the exact histories realized inside it by:

\[
\boxed{
\Sigma_k^{\mathcal D}(X_k^-,E_k^+)
:=
\left\{
\beta\in\Sigma_k^{\mathrm{kin}}
\;\middle|\;
\operatorname{Traj}_k(X_k^-,\beta)
\subseteq
\mathcal D_k(X_k^-,E_k^+)
\right\}.
}
\]

A selected history satisfies:

\[
\sigma_{E_k}
\in
\Sigma_k^{\mathcal D}(X_k^-,E_k^+).
\]

Thus \(E_k^+\Rightarrow\sigma_{E_k}\) is two-boundary compatibility selection, not past rewriting.

---

## CG2. Exact Causal Bundle and Operation Alphabets

Let:

\[
\pi_k^{\mathcal D}:
\widetilde{\mathcal D}_k
\longrightarrow
\mathcal D_k
\]

be the exact causal bundle over the visible causal cell.

- base: visible result, phase, and causal position,
- fiber: exact history-residue states compatible with the visible point.

The visible operation alphabet is:

\[
A_k,
\]

and the exact operation alphabet is:

\[
\widetilde A_k.
\]

They are related by:

\[
\boxed{
\pi_k^A:\widetilde A_k\to A_k.
}
\]

Kinematically admissible histories are exact-operation words:

\[
\boxed{
\Sigma_k^{\mathrm{kin}}
\subseteq
\widetilde A_k^*.
}
\]

The next-scale engine must act on \(\widetilde A_k\), not merely on \(A_k\), so that transported residue remains available to later generation.

---

## CG3. Present Selection Section

Let:

\[
Z_{0,k}(\tau)
\subseteq
\mathcal D_k
\]

be the present section of the scale-\(k\) causal cell.

It cuts the region at which path selection is currently operative.

An exact selection section is a lift:

\[
s_{E_k}:Z_{0,k}(\tau)\to\widetilde{\mathcal D}_k.
\]

Across compatible scales, the common present structure is a family:

\[
Z_0(\tau)=\{Z_{0,k}(\tau)\}_{k\in K}
\]

satisfying transversality and compatibility relations.

The Trans-scale Clock Needle is therefore not an external universal hand. It is the condition under which multiple local causal cells admit one compatible present cut.

---

## CG4. Residual Holonomy

Let \(\gamma_k\) be a visible closed path in the base causal cell:

\[
\gamma_k(1)=\gamma_k(0).
\]

Let \(\widetilde\gamma_k\) be its exact lift. Its exact endpoint may differ:

\[
\widetilde\gamma_k(1)
=
\widetilde\gamma_k(0)+F_k.
\]

Define:

\[
\boxed{
\operatorname{Hol}_k(\gamma_k):=F_k.
}
\]

The characteristic local temporal event is:

\[
\boxed{
\text{base return with nontrivial residual holonomy}.
}
\]

Equivalently:

\[
c_k=0,
\qquad
F_k\neq0.
\]

The spring is a local chart of this geometry:

\[
\theta(T)=\theta(0),
\qquad
Z(T)>Z(0).
\]

---

## CG5. Terminal Cell Witness, History Residue, and State Displacement

Once the terminal predicate is fixed in Part V, define the set of terminal causal-cell witnesses:

\[
\boxed{
\mathfrak C_k^{\mathrm{term}}
:=
\left\{
(X_k^-,E_k^+,\beta_k)
\;\middle|\;
\operatorname{Term}_k(X_k^-,\beta_k;E_k^+)
\right\}.
}
\]

A witness records not merely a region, but the inherited exact state, the future-side requirement, and the exact terminal block that connects them.

The full history residue is extracted by:

\[
r_k:
\mathfrak C_k^{\mathrm{term}}
\to
\mathcal R_k^{\mathrm{term}}.
\]

State displacement is a projection of that residue:

\[
\delta_k:
\mathcal R_k^{\mathrm{term}}
\to
\operatorname{Disp}(\mathcal X_k),
\]

\[
F_k
=
\delta_k\!\left(r_k(X_k^-,E_k^+,\beta_k)\right)
=
U_k(\beta_k)X_k^- - X_k^-.
\]

In general:

\[
\boxed{
\text{state displacement}
\neq
\text{full history residue}.
}
\]

They may be identified only in a realization where the exact state is proved to preserve the relevant ordered history, as intended in the Free Number substrate.

---

## CG6. Phase-Closure Contraction Type

Let:

\[
q_k:
\mathfrak C_k^{\mathrm{term}}
\to
A_{k+1}
\]

be the base-cell contraction / upper-label map,

\[
J_k:
\mathcal R_k^{\mathrm{term}}
\to
\mathcal I_{k+1}
\]

be the residual transport map, and:

\[
\iota_{k+1}:
A_{k+1}\times\mathcal I_{k+1}
\to
\widetilde A_{k+1}
\]

be the exact upper-operation constructor.

Then:

\[
\boxed{
\operatorname{PCl}_k:
\mathfrak C_k^{\mathrm{term}}
\to
\widetilde A_{k+1}
}
\]

is defined by:

\[
\boxed{
\operatorname{PCl}_k(X^-,E^+,\beta)
=
\iota_{k+1}
\left(
q_k(X^-,E^+,\beta),
J_k(r_k(X^-,E^+,\beta))
\right).
}
\]

Abbreviated:

\[
\operatorname{PCl}_k(X^-,E^+,\beta)
=
q_k(X^-,E^+,\beta)
\left[J_k(r_k(X^-,E^+,\beta))\right].
\]

Geometrically:

\[
\boxed{
\operatorname{PCl}_k
=
\text{base contraction}
+
\text{fiber transport}.
}
\]

The next exact generating alphabet is:

\[
\boxed{
\widetilde A_{k+1}^{\mathrm{gen}}
:=
\operatorname{im}\operatorname{PCl}_k.
}
\]

The visible upper alphabet is only its projection:

\[
A_{k+1}^{\mathrm{gen}}
:=
\pi_{k+1}^A
\left(
\widetilde A_{k+1}^{\mathrm{gen}}
\right).
\]

---

## CG7. Causal-Cell Fractality

The geometric recurrence is:

\[
\boxed{
\text{causal cell}
\longrightarrow
\text{fibered upper node}
\longrightarrow
\text{upper causal cell}.
}
\]

A sequence of terminal lower cells:

\[
\mathcal D_k^{(1)},\ldots,\mathcal D_k^{(m)}
\]

becomes an exact upper history:

\[
\operatorname{PCl}_k(\mathcal D_k^{(1)})
\cdots
\operatorname{PCl}_k(\mathcal D_k^{(m)})
\in
\widetilde A_{k+1}^*.
\]

Those exact upper operations participate in a new causal cell:

\[
\mathcal D_{k+1}(X_{k+1}^-,E_{k+1}^+).
\]

The expected global geometry is:

\[
\boxed{
\text{a stratified directed causal-cell complex with residue fibers}.
}
\]

The linear tower remains the minimal front model. Branching and merging are deferred to a scale DAG / directed cell-complex extension.

---

# Part II — Primitive Data

> **Type precedence.** Where later legacy sections use a bare \(A_k\), a bare upper symbol \(a_{k+1}\), or a history set \(A_k^*\), the governing types are those fixed in Part II-A: exact histories lie in \(\widetilde A_k^*\), and Phase-Closure lands in \(\widetilde A_{k+1}\). The visible alphabet is a projection only.

## 3. Scale System

For the front specification let:

\[
K=\mathbb N.
\]

A branching scale DAG is retained as the later global extension.

For each scale \(k\), define the exact alphabet \(\widetilde A_k\), its visible projection \(A_k\), and:

\[
\pi_k^A:\widetilde A_k\to A_k.
\]

The kinematically admissible history set is:

\[
\Sigma_k^{\mathrm{kin}}\subseteq\widetilde A_k^*.
\]

The superscript `kin` is essential.  
Admissibility must first be defined independently of whether a candidate succeeds in closing a particular result.

A scale carries the data:

\[
\mathcal D_k
=
\left(
\widetilde A_k,
A_k,
\pi_k^A,
\Sigma_k^{\mathrm{kin}},
\mathcal X_k,
\mathcal E_k,
d_k^{\mathcal X},
d_k^{\mathcal E},
\approx_k,
\mu_k,
U_k,
P_k,
R_k,
C_k,
\epsilon_k
\right),
\]

where:

- \(\widetilde A_k\): exact operation alphabet,
- \(A_k\): visible operation alphabet,
- \(\pi_k^A\): exact-to-visible operation projection,
- \(\mathcal X_k\): exact state space,
- \(\mathcal E_k\): result / observation space,
- \(d_k^{\mathcal X}\): exact-state metric or an equivalent topology used for local stability,
- \(d_k^{\mathcal E}\): result-space metric; the abbreviation \(d_k=d_k^{\mathcal E}\) may be used,
- \(\approx_k\): structural equivalence of local closure modes / terminal cells,
- \(\mu_k:\mathcal X_k\to\mathcal E_k\): compression or observation map,
- \(U_k(\sigma)\): history execution on exact states,
- \(P_k\): pressure or constraint field,
- \(R_k\): reference frame / observation port,
- \(C_k\): local consistency constraints,
- \(\epsilon_k\): result-closure tolerance.

The elements of \(A_k\) are elementary only relative to scale \(k\).

An operation at scale \(k+1\) may contain a complete closed history from scale \(k\).

---

## 4. Exact State and Result

Let

\[
X_k\in\mathcal X_k
\]

be an exact state, with visible result

\[
E_k=\mu_k(X_k).
\]

After executing a history \(\sigma\in\Sigma_k^{\mathrm{kin}}\),

\[
X_k^+(\sigma)
=
U_k(\sigma)X_k,
\]

and

\[
E_k'(\sigma)
=
\mu_k(X_k^+(\sigma)).
\]

Two different quantities must never be conflated.

### 4.1 Visible Closure Mismatch

\[
c_k(\sigma)
:=
d_k(E_k'(\sigma),E_k).
\]

This measures failure of the visible result to return.

### 4.2 Exact Closure Residue

When the exact state space admits a difference operation, define:

\[
F_k(\sigma)
:=
X_k^+(\sigma)-X_k.
\]

More generally, \(F_k\) is the exact displacement class between the initial and terminal exact states.

The full history residue is \(r_k(\sigma)\). In general:

\[
F_k=\delta_k(r_k(\sigma)),
\qquad
F_k\text{ need not determine }r_k(\sigma).
\]

If the visible result returns exactly,

\[
\mu_k(X_k^+)=\mu_k(X_k),
\]

then:

\[
F_k\in\ker\mu_k.
\]

Thus:

\[
\boxed{
c_k=0
\quad\not\Rightarrow\quad
F_k=0.
}
\]

The characteristic nontrivial return of the Time Engine is:

\[
\boxed{
c_k=0,
\qquad
F_k\neq0.
}
\]

This is the exact statement behind:

> The phase returns. The state does not.

---

## 5. Free-Number Bridge

Free Number Core v1 supplies exact states that remain distinct under the same compressed value.

Let:

\[
\mu_n:\mathfrak A_n\to\mathbb H
\]

be the compressed multiplication / observation map.

For:

\[
F\in\ker\mu_n,
\qquad
F\neq0,
\]

write:

\[
0[F]
\]

for a nonzero exact state with compressed result zero.

Then:

\[
\mu_n(0[F])=0,
\]

but:

\[
0[F]\neq0[0].
\]

For a general result \(E\), choose a lift \(X_E\). Then:

\[
\mu_n^{-1}(E)
=
X_E+\ker\mu_n,
\]

and exact states in the result fiber may be written:

\[
E[F].
\]

Therefore:

\[
E[F_1]\neq E[F_2]
\]

may hold even when both have the same visible result \(E\).

The bridge used by the Time Engine is:

\[
\boxed{
E[0]
\longrightarrow
E[F],
\qquad
F\in\ker\mu\setminus\{0\}.
}
\]

Free Number closes the local distinction between result return and state return.  
The Time Engine transports that distinction across scales.

---

# Part III — Common Generative Rule

## 6. Scale-Independent Generative Schema

Let:

\[
\mathfrak G
\]

be the common generative schema.

Its scale-\(k\) realization is:

\[
\mathfrak G_k
=
\mathfrak G[P_k,R_k,C_k,\epsilon_k].
\]

The local operational shape is:

\[
\sigma_k
\xrightarrow{\operatorname{Eval}_k}
E_k
\xrightarrow{\operatorname{Select}_k}
\sigma_{E_k}
\xrightarrow{\operatorname{Eval}_k}
E_k'.
\]

The forward side is:

\[
\sigma_k\Rightarrow E_k.
\]

The result-selected side is:

\[
E_k\Rightarrow\sigma_{E_k}.
\]

The re-evaluation side is:

\[
\sigma_{E_k}\Rightarrow E_k'.
\]

The generative signature is scale-invariant:

\[
\operatorname{Sig}(\mathfrak G_k)
=
\operatorname{Sig}(\mathfrak G_{k+1}).
\]

Its concrete values are not:

\[
P_k\neq P_{k+1},
\qquad
R_k\neq R_{k+1},
\qquad
\epsilon_k\neq\epsilon_{k+1},
\]

and generally:

\[
F_k\neq F_{k+1}.
\]

Thus the Time Engine asserts:

\[
\boxed{
\text{same generative shape, different closed history}.
}
\]

---

## 7. Result-Selected History

For a result \(E_k\), first define the closure-candidate fiber:

\[
\Sigma_{k,E}^{\epsilon}
=
\left\{
\sigma\in\Sigma_k^{\mathrm{kin}}
\;\middle|\;
d_k\!\left(
\operatorname{Eval}_k(\sigma),E_k
\right)
\le\epsilon_k
\right\}.
\]

This avoids defining admissibility by the conclusion it is intended to prove.

The result-selected history is chosen in two stages.

First minimize result mismatch:

\[
\Sigma_{k,E}^{\min}
=
\arg\min_{\sigma\in\Sigma_k^{\mathrm{kin}}}
D_k\!\left(
\operatorname{Eval}_k(\sigma),E_k;P_k
\right).
\]

Then select among equally adequate closures by path structure:

\[
\sigma_{E_k}
\in
\arg\min_{\sigma\in\Sigma_{k,E}^{\min}}
L_{\mathrm{path},k}(\sigma).
\]

Hence:

\[
\boxed{
E_k\Rightarrow\sigma_{E_k}
}
\]

does not mean that a result creates an arbitrary past.

It means that a result determines a fiber of compatible histories, after which the engine selects an admissible representative under explicit constraints.

---

# Part IV — Fractal Closure Foundation

## 8. Fractal Closure Principle

The Time Engine is fractal because the same generative rule produces a local closure at each scale, and that closure becomes a generating unit at the next scale.

This is not primarily geometric self-similarity.

It is:

\[
\boxed{
\text{closure-recursive fractality}.
}
\]

Let:

\[
\Sigma_k^{\mathrm{term}}
\subseteq
\Sigma_k^{\mathrm{kin}}
\]

be the terminal histories represented by terminal causal cells \(\mathcal D_k^{\mathrm{term}}\).

The governing Phase-Closure type is the one fixed in Part II-A:

\[
\operatorname{PCl}_k:
\mathcal D_k^{\mathrm{term}}
\longrightarrow
\widetilde A_{k+1}.
\]

For a terminal causal cell \(\mathcal D\):

\[
\operatorname{PCl}_k(X^-,E^+,\beta)
=
q_k(X^-,E^+,\beta)
\left[J_k(r_k(X^-,E^+,\beta))\right].
\]

Its visible operation is:

\[
\pi_{k+1}^A
\left(
\operatorname{PCl}_k(\mathcal D)
\right)
=
q_k(\mathcal D).
\]

The exact operation retains the lower history residue.

The next exact generating alphabet is:

\[
\boxed{
\widetilde A_{k+1}^{\mathrm{gen}}
=
\operatorname{im}\operatorname{PCl}_k.
}
\]

Then the same schema acts again on exact operation words:

\[
\left(\widetilde A_{k+1}^{\mathrm{gen}}\right)^*
\xrightarrow{\mathfrak G_{k+1}}
\Sigma_{k+1}^{\mathrm{term}}
\xrightarrow{\operatorname{PCl}_{k+1}}
\widetilde A_{k+2}.
\]

Therefore:

\[
\boxed{
\text{a process at }k
\longrightarrow
\text{an operation at }k+1.
}
\]

A completed lower history is not externally translated into an upper symbol after closure.

Its transition into an upper operation is what “closure” means.

---

## 9. Fractality Is Not Exact State Self-Similarity

The Time Engine does not require:

\[
F_k=F_{k+1},
\]

or:

\[
X_k\cong X_{k+1}.
\]

It does not require metric copies or reversible scale conjugacy.

A strong equation such as:

\[
R_{k\to k+1}\circ\mathcal T_k
\cong
\mathcal T_{k+1}\circ R_{k\to k+1}
\]

may fail because scale lifting includes coarse-graining and visibility change.

What is required is stronger than equality of signatures.

Let \(\mathsf{PC}\) be the typed Phase-Closure axiom system. Each scale realization must satisfy:

\[
\boxed{
\mathcal M_k\models\mathsf{PC}
\qquad
\forall k.
}
\]

Successive models are not unrelated copies. Their exact generating alphabet is inherited from the preceding scale:

\[
\boxed{
\widetilde A_{k+1}^{\mathrm{gen}}
=
\operatorname{im}\operatorname{PCl}_k.
}
\]

Thus the same closure axioms recur on an alphabet produced by the previous closure level.

> The same phase-closure grammar repeats; the exact residue does not repeat.

---

# Part V — Phase-Closure Conditions and Terminal Factorization

## 10. Why Closure Is a Phase Transition

Closure is not stopping inside one descriptive phase.

A local process is an exact-operation word:

\[
\beta_k\in\widetilde A_k^+,
\]

where \(\widetilde A_k^+\) denotes nonempty finite words.

After closure it becomes one exact upper-scale operation:

\[
\operatorname{PCl}_k(X_k^-,E_k^+,\beta_k)
\in
\widetilde A_{k+1}.
\]

The operational rank changes:

\[
\boxed{
\text{process at }k
\longrightarrow
\text{operation at }k+1.
}
\]

To call this a genuine structural phase transition, three conditions are required:

1. terminal condition,
2. residual transport condition,
3. nondegeneracy condition.

The terminal condition must first be strong enough to cut a continuous lower history into reusable causal-cell units.

---

## 11. State-Dependent Terminal Condition

Termination is not a property of a word alone.

It depends on:

- inherited exact state \(X_k^-\),
- future-side requirement \(E_k^+\),
- exact history block \(\beta\),
- local scale data \(P_k,R_k,C_k,\epsilon_k\).

Let:

\[
X_k^+(\beta)
:=
U_k(\beta)X_k^-.
\]

Define the result-closing candidate predicate by:

\[
\boxed{
\operatorname{Close}_k(X_k^-,\beta;E_k^+)
\iff
\left[
\beta\in
\Sigma_k^{\mathcal D}(X_k^-,E_k^+)
\right]
\land
\left[
d_k^{\mathcal E}
\left(
\mu_k(X_k^+(\beta)),E_k^+
\right)
\le
\epsilon_k
\right].
}
\]

This predicate contains causal admissibility and visible result closure only. Local stability is added separately in T3.

### T1. Future-Boundary Closure

\[
\boxed{
\operatorname{Close}_k(X_k^-,\beta;E_k^+).
}
\]

The exact endpoint need not equal the inherited exact state.

The special return case is:

\[
E_k^+=\mu_k(X_k^-).
\]

Then visible result return may coexist with exact non-return.

---

### T2. Minimal Phase Boundary

Let \(\rho\prec\beta\) mean that \(\rho\) is a nonempty proper admissible prefix of \(\beta\) inside the same causal cell.

The block \(\beta\) reaches the first closure boundary for \(E_k^+\) when:

\[
\boxed{
\forall\rho\prec\beta,
\qquad
\neg
\operatorname{Close}_k(X_k^-,\rho;E_k^+).
}
\]

Thus termination does not mean that all motion in the phase family has been exhausted.

It means:

> **One causal-cell unit has reached its first complete boundary. A later winding begins as a new unit.**

This condition preserves repeated spring windings:

\[
\beta_1,
\beta_2,
\beta_3,
\ldots
\]

Each may be a separate terminal block with a distinct exact residue.

---

### T3. Local Structural Stability

Let \(\approx_k\) be structural equivalence of local closure modes.

There exist radii \(\eta_X,\eta_E>0\) such that for every:

\[
d_k^{\mathcal X}(Y,X_k^-)<\eta_X,
\qquad
d_k^{\mathcal E}(G,E_k^+)<\eta_E,
\]

there exists a block \(\beta'\approx_k\beta\) satisfying T1 and T2 for \((Y,G)\).

The boundary is therefore not an accidental equality along one exact trajectory.

---

### Terminal Predicate

Define:

\[
\boxed{
\operatorname{Term}_k(X_k^-,\beta;E_k^+)
}
\]

when T1–T3 hold.

The terminal causal-cell witness is:

\[
\mathbf D_k[X_k^-,E_k^+;\beta]
\in
\mathfrak C_k^{\mathrm{term}}.
\]

In words:

> **A local phase unit terminates when it reaches the future boundary for the first time and that first-boundary mode is locally stable.**

The terminal predicate is determined at scale \(k\). It is not defined by first declaring an upper operation and then reading terminality backward.

---

## 12. Terminal Block Factorization

### 12.1 Execution Convention

Let \(\varepsilon\) be the empty word. Require:

\[
U_k(\varepsilon)X=X,
\]

and for exact words \(\alpha,\beta\):

\[
\boxed{
U_k(\alpha\beta)X
=
U_k(\beta)\bigl(U_k(\alpha)X\bigr).
}
\]

Thus execution is deterministic and compatible with left-to-right history concatenation.

---

### 12.2 Boundary Schedule

A long lower history may contain several causal-cell units with different future-side requirements.

Fix a compatible boundary schedule:

\[
\mathbf E^+
=
(E_1^+,E_2^+,\ldots).
\]

The schedule may later be generated by the result-selection mechanism. For factorization it is treated as given data.

Let:

\[
\sigma\in\Sigma_k^{\mathrm{kin}}
\]

be a finite exact history and let \(X_0=X_k^-\).

Recursively choose \(\beta_j\) as the first prefix of the remaining history such that:

\[
\operatorname{Term}_k(X_{j-1},\beta_j;E_j^+),
\]

and update:

\[
\boxed{
X_j
=
U_k(\beta_j)X_{j-1}.
}
\]

When no further terminal prefix exists, the remaining word is the open tail \(\rho\).

---

### 12.3 Factorization Assumptions

The front theorem is stated for a fixed finite exact word. Its first prefix is linearly ordered by length, so earliest-boundary uniqueness must not be inserted as an independent assumption.

The theorem uses four explicit conditions.

#### F1. Deterministic Execution

The execution law gives a unique exact state after every admissible prefix.

#### F2. Prefix Locality

The terminal status of a prefix depends only on:

\[
(X,\beta,E^+;P_k,R_k,C_k,\epsilon_k),
\]

not on the unconsumed suffix that happens to follow \(\beta\).

For every legal continuation \(\tau\), appending \(\tau\) does not retroactively change whether \(\beta\) was a terminal boundary:

\[
\boxed{
\operatorname{Term}_k(X,\beta;E^+)
\text{ is invariant under the extension }
\beta\mapsto\beta\tau.
}
\]

This is the causal no-retroactive-resegmentation condition required by a forward terminal parser.

#### F3. Renewal

If:

\[
\operatorname{Term}_k(X_{j-1},\beta_j;E_j^+),
\]

then:

\[
X_j=U_k(\beta_j)X_{j-1}
\]

is an admissible inherited state for the next causal cell, and the unconsumed suffix remains kinematically admissible from \(X_j\).

Renewal does not reset exact history. It changes the local cell boundary while carrying the updated exact state forward.

#### F4. Terminal Congruence

If two terminal witnesses are structurally equivalent:

\[
\mathbf D\approx_k\mathbf D',
\]

then their upper exact operations are equivalent under the induced upper relation:

\[
\operatorname{PCl}_k(\mathbf D)
\approx_{k+1}^A
\operatorname{PCl}_k(\mathbf D').
\]

This ensures that the lifted upper history does not depend on an arbitrary representative of one terminal closure mode.

For a single literal exact word, the earliest terminal prefix—if one exists—is automatically unique because prefixes are totally ordered. A separate first-boundary uniqueness problem appears only when the engine is extended to branching path families or a scale DAG.

---

## 13. Terminal Block Factorization Theorem

### Theorem

Under F1–F3, every finite admissible exact history \(\sigma\), relative to \((X_0,\mathbf E^+)\), admits a unique maximal literal decomposition:

\[
\boxed{
\sigma
=
\beta_1\beta_2\cdots\beta_m\rho,
}
\]

where:

\[
\operatorname{Term}_k(X_{j-1},\beta_j;E_j^+)
\]

for every \(j=1,\ldots,m\),

\[
X_j=U_k(\beta_j)X_{j-1},
\]

and the open tail \(\rho\) contains no terminal prefix for the next scheduled requirement from \(X_m\).

For literal exact words the decomposition is unique. Under F4, its lifted upper history is also well-defined on structural-equivalence classes.

### Proof

Start at \((X_0,\sigma,E_1^+)\).

- By F2, terminal status is prefix-local and cannot be changed by the unconsumed suffix.
- If no prefix is terminal, set \(m=0\) and \(\rho=\sigma\).
- Otherwise the nonempty terminal prefixes form a finite nonempty subset of the totally ordered prefix set. Hence there is a unique shortest terminal prefix; call it \(\beta_1\).
- Deterministic execution F1 gives the unique next exact state \(X_1\).
- Renewal F3 makes the remaining suffix a legal continuation from \(X_1\).
- Repeat on the strictly shorter suffix and the next scheduled requirement.

Because \(\sigma\) is finite and every \(\beta_j\) is nonempty, the recursion terminates after finitely many steps. The remaining suffix has no next terminal prefix by construction. At each stage the shortest literal prefix and updated exact state are unique, so induction gives uniqueness of the maximal literal decomposition. F4 then makes the lifted word independent of equivalent terminal representatives. \(\square\)

---

## 14. Factorization Transducer and Upper Exact History

Define the state-indexed terminal factorizer:

\[
\mathfrak F_k^{X_0,\mathbf E^+}(\sigma)
=
\left(
(\beta_1,\ldots,\beta_m),
\rho,
(X_0,\ldots,X_m)
\right).
\]

For each terminal block define its terminal cell witness:

\[
\mathbf D_j
:=
\mathbf D_k[X_{j-1},E_j^+;\beta_j].
\]

The lifted upper exact history is:

\[
\boxed{
\widehat{\operatorname{PCl}}_k^{X_0,\mathbf E^+}(\sigma)
:=
\operatorname{PCl}_k(\mathbf D_1)
\cdots
\operatorname{PCl}_k(\mathbf D_m)
\in
\widetilde A_{k+1}^*.
}
\]

The open tail \(\rho\) is not phase-closed and is not promoted to an upper operation.

Thus the actual transduction is:

\[
\boxed{
\text{lower exact history}
\longmapsto
\left(
\text{upper exact-operation word},
\text{open lower tail}
\right).
}
\]

This is the first operational bridge of the fractal tower.

---

### 14.1 Causal Adjacency Preservation

Consecutive terminal cells satisfy:

\[
\boxed{
\partial^+\mathbf D_j
=
X_j
=
\partial^-\mathbf D_{j+1}.
}
\]

Phase-Closure contracts each cell but preserves the word order:

\[
\mathbf D_1\rightsquigarrow\mathbf D_2\rightsquigarrow\cdots\rightsquigarrow\mathbf D_m
\]

becomes:

\[
\operatorname{PCl}_k(\mathbf D_1)
\to
\operatorname{PCl}_k(\mathbf D_2)
\to
\cdots
\to
\operatorname{PCl}_k(\mathbf D_m).
\]

Therefore:

\[
\boxed{
\text{lower causal-cell adjacency}
\longrightarrow
\text{upper causal order}.
}
\]

The upper order is not inserted independently. It is inherited from the boundary gluing of terminal lower cells.

---

### 14.2 Boundary-Aligned Concatenation

The lifted factorizer is not assumed to be an ordinary monoid homomorphism.

If \(\sigma\) ends exactly at a terminal boundary, so its open tail is \(\varepsilon\), and:

\[
X_m=U_k(\sigma)X_0,
\]

then for a legal continuation \(\tau\):

\[
\boxed{
\widehat{\operatorname{PCl}}_k^{X_0}(\sigma\tau)
=
\widehat{\operatorname{PCl}}_k^{X_0}(\sigma)
\,
\widehat{\operatorname{PCl}}_k^{X_m}(\tau),
}
\]

with the corresponding concatenated boundary schedules understood.

If \(\sigma\) ends with an open tail, the tail may combine with the beginning of \(\tau\) to form the next terminal block. No simple multiplicative law is then asserted.

The correct law is therefore:

\[
\boxed{
\text{state-indexed, boundary-aligned concatenation compatibility}.
}
\]

---

### 14.3 Abstract Decoder Safety Closure

The Decoder is the formal barrier against premature promotion of an open history.

It does not generate the future-boundary schedule. Given a finite schedule, it separates certified terminal history from an unresolved exact suffix without deleting either the suffix or the remaining boundaries.

---

#### 14.3.1 Decoder Configuration and Output

A running Decoder configuration is:

\[
\mathfrak s=(X,\mathbf H,\omega),
\]

where:

- \(X\in\mathcal X_k\) is the exact state after execution of the certified consumed prefix only,
- \(\mathbf H\in\mathcal E_k^*\) is the unconsumed future-boundary sequence,
- \(\omega\in\widetilde A_k^*\) is the unconsumed exact history.

The complete Decoder output is:

\[
\boxed{
\operatorname{Dec}_k(X_0,\mathbf E,\sigma)
=
(\alpha,\rho,X_m,\mathbf H,\chi).
}
\]

Its components have types:

\[
\alpha\in\widetilde A_{k+1}^*,
\qquad
\rho\in\widetilde A_k^*,
\qquad
\mathbf H\in\mathcal E_k^*,
\]

and:

\[
\chi\in
\{
\mathsf{InputExhausted},
\mathsf{BoundaryExhausted},
\mathsf{NoTerminalPrefix}
\}.
\]

If:

\[
\sigma=\beta_1\cdots\beta_m\rho,
\]

then the consumed-state convention is:

\[
\boxed{
X_m
=
U_k(\beta_1\cdots\beta_m)X_0,
}
\]

while:

\[
\boxed{
\rho
=
\text{unconsumed exact suffix}.
}
\]

The tail \(\rho\) has not yet been executed from \(X_m\).

---

#### 14.3.2 Specification Layer

##### S1. Promotion Typing

Define the certified terminal-cell type:

\[
\operatorname{TermCell}_k
:=
\left\{
(X,E^+,\beta,p)
\;\middle|\;
 p:\operatorname{Term}_k(X,\beta;E^+)
\right\}.
\]

Phase-Closure is typed as:

\[
\boxed{
\operatorname{PCl}_k:
\operatorname{TermCell}_k
\longrightarrow
\widetilde A_{k+1}.
}
\]

An uncertified lower history is therefore not a legal Phase-Closure input.

##### S1b. Exact Phase-Closure Construction

For every certified terminal cell \(\mathbf D\):

\[
\boxed{
\operatorname{PCl}_k(\mathbf D)
=
\iota_{k+1}
\left(
q_k(\mathbf D),
J_k(r_k(\mathbf D))
\right).
}
\]

This construction formula is required for the exact residual-faithfulness result below.

##### S2. Greedy First-Boundary Rule

For current state \(X\), current boundary \(E^+\), and unconsumed word \(\omega\), define:

\[
\mathcal T_k(X,\omega;E^+)
:=
\left\{
\eta\preceq\omega
\;\middle|\;
\eta\neq\varepsilon,
\ \operatorname{Term}_k(X,\eta;E^+)
\right\}.
\]

If this set is nonempty, the Decoder selects:

\[
\boxed{
\operatorname{FirstTerm}_k(X,\omega;E^+)
:=
\arg\min_{\eta\in\mathcal T_k(X,\omega;E^+)}|\eta|.
}
\]

For a literal finite word, prefixes are totally ordered by length, so this shortest prefix is unique.

##### S3. Stop-Mode Convention

At the final configuration \((X_m,\mathbf H,\rho)\), stopping is decided in the following order.

Input exhausted:

\[
\chi=\mathsf{InputExhausted}
\iff
\rho=\varepsilon.
\]

Boundary sequence exhausted:

\[
\chi=\mathsf{BoundaryExhausted}
\iff
\rho\neq\varepsilon
\land
\mathbf H=\varepsilon.
\]

No terminal prefix for the next available boundary:

\[
\chi=\mathsf{NoTerminalPrefix}
\]

iff:

\[
\rho\neq\varepsilon,
\qquad
\mathbf H=(E_*^+,\mathbf K),
\]

and:

\[
\forall\eta\preceq\rho,
\quad
\eta\neq\varepsilon
\Longrightarrow
\neg\operatorname{Term}_k(X_m,\eta;E_*^+).
\]

The three stop modes must not be conflated.

##### S4. Decoder Operational Locality

The next transition and stop decision depend only on the current configuration:

\[
(X,\mathbf H,\omega).
\]

A resumed Decoder does not inspect the historical route by which that configuration was reached.

---

#### 14.3.3 Abstract Assumptions

The finite sequential exact-word model uses the following assumptions.

1. \(\sigma\in\widetilde A_k^*\) and \(\mathbf E\in\mathcal E_k^*\) are finite.
2. Execution \(U_k(\beta)X\) is deterministic.
3. Every terminal block is nonempty.
4. \(\operatorname{Term}_k(X,\beta;E^+)\) is well-defined from the displayed arguments and fixed local data.
5. Terminal execution satisfies renewal: \(U_k(\beta)X\) is a legal next inherited state.
6. Exact histories form a free word structure with unique prefix remainder and left cancellation.
7. \(\operatorname{PCl}_k\) is a deterministic map on \(\operatorname{TermCell}_k\).
8. Terminal-prefix truth is suffix-local: appending later history does not change the terminal or nonterminal status of an already existing prefix.
9. Future-boundary extension is append-only:

\[
\mathbf E\longmapsto\mathbf E\smallfrown\mathbf G.
\]

10. The semantics of an already certified cell are not rewritten by later context.
11. One certified block consumes exactly one current future boundary.

Assumptions 8--10 are the abstract certified-prefix irreversibility conditions. They do not claim that the unresolved tail can never close later.

---

#### 14.3.4 D4 — Boundary-Relative Greedy Factorization Theorem

For fixed:

\[
(k,X_0,\mathbf E,\sigma),
\]

there exists a unique tuple:

\[
\boxed{
(m,\beta_1,\ldots,\beta_m,\rho,
 X_0,\ldots,X_m,\mathbf H,\chi)
}
\]

such that:

\[
\sigma=\beta_1\cdots\beta_m\rho,
\]

\[
X_j=U_k(\beta_j)X_{j-1},
\qquad
1\le j\le m,
\]

and each block is the unique shortest nonempty terminal prefix at its stage:

\[
\beta_j
=
\operatorname{FirstTerm}_k
\left(
X_{j-1},
\beta_j\cdots\beta_m\rho;
E_j^+
\right).
\]

Moreover:

\[
\boxed{
m\le |\mathbf E|,
\qquad
\mathbf H=\operatorname{drop}_m(\mathbf E).
}
\]

The upper exact output is uniquely determined by:

\[
\boxed{
\alpha
=
\operatorname{PCl}_k(\mathbf D_1)
\cdots
\operatorname{PCl}_k(\mathbf D_m).
}
\]

Hence:

\[
\boxed{
\operatorname{Dec}_k(X_0,\mathbf E,\sigma)
=
(\alpha,\rho,X_m,\mathbf H,\chi)
}
\]

exists and is unique.

##### Proof

Proceed by recursion on the length of the unconsumed word \(\omega\).

If the input, boundary sequence, or terminal-prefix search satisfies one of the three stop conditions, the output is immediately defined.

Otherwise \(\mathcal T_k(X,\omega;E^+)\neq\varnothing\), so the unique shortest nonempty terminal prefix \(\beta\) exists. Write:

\[
\omega=\beta\tau.
\]

Because \(\beta\neq\varepsilon\):

\[
|\tau|<|\omega|.
\]

Deterministic execution and renewal give the unique next legal configuration:

\[
\left(
U_k(\beta)X,
\operatorname{tail}(\mathbf H),
\tau
\right).
\]

Thus the recursion terminates after finitely many successful steps.

For uniqueness, compare two greedy runs on the same configuration. Their first block is the same unique shortest terminal prefix. Free-word cancellation gives the same remainder, deterministic execution gives the same next state, and the same argument applies recursively. The stop mode, unconsumed boundaries, tail, state, blocks, and exact output are therefore all unique.

\[
\boxed{\square}
\]

This theorem is algorithm-relative and boundary-relative. It does not assert uniqueness among arbitrary nongreedy terminal segmentations or across different future-boundary schedules.

---

#### 14.3.5 D5 — Exact Residual Faithfulness Lemma

Assume:

\[
J_k(r)=J_k(r')
\Longrightarrow
r=r',
\]

and, for every fixed visible operation \(a\in A_{k+1}\):

\[
\iota_{k+1}(a,u)=\iota_{k+1}(a,v)
\Longrightarrow
u=v.
\]

Then for terminal cells \(\mathbf D,\mathbf D'\):

\[
q_k(\mathbf D)=q_k(\mathbf D'),
\qquad
r_k(\mathbf D)\neq r_k(\mathbf D')
\]

implies:

\[
\boxed{
\operatorname{PCl}_k(\mathbf D)
\neq
\operatorname{PCl}_k(\mathbf D').
}
\]

##### Proof

If the two exact Phase-Closure outputs were equal, S1b and injectivity of \(\iota_{k+1}(a,-)\) would give:

\[
J_k(r_k(\mathbf D))
=
J_k(r_k(\mathbf D')).
\]

Injectivity of \(J_k\) would then give:

\[
r_k(\mathbf D)=r_k(\mathbf D'),
\]

contradicting the hypothesis.

\[
\boxed{\square}
\]

The visible projections may still agree. D5 preserves distinctions between extracted terminal residues at the exact upper layer; it does not claim that \(r_k\) is already a complete encoding of every difference between lower histories.

---

#### 14.3.6 Certified-Prefix Irrevocability Lemma

Suppose:

\[
\operatorname{Dec}_k(X_0,\mathbf E,\sigma)
=
(\alpha,\rho,X_m,\mathbf H,\chi),
\]

with greedy factorization:

\[
\sigma=\beta_1\cdots\beta_m\rho.
\]

For any legal finite input extension \(\tau\) and append-only boundary extension \(\mathbf G\), the Decoder on:

\[
(X_0,\mathbf E\smallfrown\mathbf G,\sigma\tau)
\]

selects the same first \(m\) certified blocks:

\[
\boxed{
\beta_1,\ldots,\beta_m.
}
\]

After these steps it reaches:

\[
\boxed{
\left(
X_m,
\mathbf H\smallfrown\mathbf G,
\rho\tau
\right).
}
\]

Under assumptions 1--9, the certified block and state sequences are preserved. Under assumptions 1--10, the exact output prefix \(\alpha\) is also preserved.

##### Proof

Induct on \(j=1,\ldots,m\). At stage \(j\), the old block \(\beta_j\) is terminal and every shorter nonempty prefix is nonterminal. Suffix locality preserves both facts after appending \(\tau\). Append-only boundary extension preserves the current boundary \(E_j^+\), and deterministic execution preserves the inherited state \(X_{j-1}\). Therefore \(\beta_j\) remains the unique first terminal prefix.

Since one boundary is consumed per certified block:

\[
m\le |\mathbf E|.
\]

Hence:

\[
\operatorname{drop}_m
(\mathbf E\smallfrown\mathbf G)
=
\operatorname{drop}_m(\mathbf E)
\smallfrown\mathbf G
=
\mathbf H\smallfrown\mathbf G.
\]

The consumed-state convention leaves \(\rho\tau\) unexecuted at \(X_m\). Deterministic certified-cell semantics preserves \(\alpha\).

\[
\boxed{\square}
\]

Irrevocability applies to the certified prefix, not to the future fate of the unresolved tail.

---

#### 14.3.7 Resume Lemma

Let:

\[
\mathfrak s_0
\xRightarrow{\alpha}
\mathfrak s_m
\]

be a finite sequence of successful Decoder transitions. If:

\[
\operatorname{Dec}_k(\mathfrak s_m)
=
(\alpha',\rho',X_n,\mathbf L,\chi'),
\]

then:

\[
\boxed{
\operatorname{Dec}_k(\mathfrak s_0)
=
(\alpha\alpha',\rho',X_n,\mathbf L,\chi').
}
\]

##### Proof

Induct on the number of successful transitions. The zero-step case is the identity. The inductive step follows from the recursive Decoder definition and associativity of word concatenation in \(\widetilde A_{k+1}^*\).

\[
\boxed{\square}
\]

---

#### 14.3.8 D7 — Stateful Decoder Composition Theorem

Assume:

\[
\operatorname{Dec}_k(X_0,\mathbf E,\sigma)
=
(\alpha,\rho,X_m,\mathbf H,\chi),
\]

and:

\[
\operatorname{Dec}_k
\left(
X_m,
\mathbf H\smallfrown\mathbf G,
\rho\tau
\right)
=
(\alpha',\rho',X_n,\mathbf L,\chi').
\]

Then:

\[
\boxed{
\operatorname{Dec}_k
\left(
X_0,
\mathbf E\smallfrown\mathbf G,
\sigma\tau
\right)
=
(\alpha\alpha',\rho',X_n,\mathbf L,\chi').
}
\]

##### Proof

Certified-Prefix Irrevocability gives:

\[
\left(
X_0,
\mathbf E\smallfrown\mathbf G,
\sigma\tau
\right)
\xRightarrow{\alpha}
\left(
X_m,
\mathbf H\smallfrown\mathbf G,
\rho\tau
\right).
\]

Apply the Resume Lemma to the assumed resumed Decoder output.

\[
\boxed{\square}
\]

This law handles all three prior stop modes. It retains the exact state, unresolved input, unconsumed boundaries, and resumed stop reason. It is not an ordinary monoid-homomorphism law:

\[
\operatorname{Dec}(\sigma\tau)
\neq
\operatorname{Dec}(\sigma)\operatorname{Dec}(\tau)
\]

in general.

The correct structure is:

\[
\boxed{
\text{stateful, boundary-preserving continuation composition}.
}
\]

---

#### 14.3.9 D6 — Certified-Prefix Stability Corollary

Under the hypotheses of D7, for every legal finite extension \((\tau,\mathbf G)\), there exists a unique tuple:

\[
\boxed{
\exists!
(\alpha',\rho',X_n,\mathbf L,\chi')
}
\]

such that:

\[
\operatorname{Dec}_k
\left(
X_0,
\mathbf E\smallfrown\mathbf G,
\sigma\tau
\right)
=
(\alpha\alpha',\rho',X_n,\mathbf L,\chi').
\]

Therefore:

\[
\boxed{
\alpha
\preceq
\pi_{\mathrm{out}}
\operatorname{Dec}_k
\left(
X_0,
\mathbf E\smallfrown\mathbf G,
\sigma\tau
\right).
}
\]

##### Proof

The resumed configuration:

\[
\left(
X_m,
\mathbf H\smallfrown\mathbf G,
\rho\tau
\right)
\]

is finite and legal by renewal, so D4 gives a unique resumed output. D7 attaches that output after the already certified prefix \(\alpha\).

\[
\boxed{\square}
\]

The corollary preserves the certified output as a prefix; it does not require the added suffix \(\alpha'\) to be empty.

---

#### 14.3.10 Abstract Decoder Safety and Continuation Theorem

Under the specification and assumptions above, the Decoder satisfies the following package.

##### A. Boundary-Relative Greedy Totality and Uniqueness

For every finite legal input \((X_0,\mathbf E,\sigma)\), the output:

\[
\operatorname{Dec}_k(X_0,\mathbf E,\sigma)
=
(\alpha,\rho,X_m,\mathbf H,\chi)
\]

exists and is unique.

##### B. Promotion Safety

Every letter of \(\alpha\) is the Phase-Closure of a certified terminal cell:

\[
\boxed{
\alpha
\in
\left(
\operatorname{im}\operatorname{PCl}_k
\right)^*.
}
\]

##### C. Open-Tail Safety

If:

\[
\chi=\mathsf{NoTerminalPrefix},
\qquad
\mathbf H=(E_*^+,\mathbf K),
\]

then:

\[
\boxed{
\forall\eta\preceq\rho,
\quad
\eta\neq\varepsilon
\Longrightarrow
\neg\operatorname{Term}_k(X_m,\eta;E_*^+).
}
\]

Thus:

\[
\operatorname{PCl}_k
\left(
\mathbf D_k[X_m,E_*^+;\rho]
\right)
\]

is undefined. No such nonterminality is inferred when the stop mode is \(\mathsf{BoundaryExhausted}\).

##### D. Stateful Continuation

For every legal finite extension \((\tau,\mathbf G)\), one-shot decoding equals preservation of the certified prefix followed by decoding from the saved configuration.

##### E. Certified-Prefix Stability

The prior upper exact output \(\alpha\) is a prefix of the extended output and is not erased, altered, or resegmented.

##### F. Conditional Exact Residual Faithfulness

If \(J_k\) and \(\iota_{k+1}(a,-)\) are injective in the stated senses, different extracted terminal residues remain different in the upper exact operation layer, even when their visible operation labels agree.

##### Proof

A is D4. B is S1 together with the Decoder transition rule. C is S3. D is D7. E is D6. F is D5 using S1b.

\[
\boxed{\square}
\]

This package does not constitute seven independent major theorems. Its logical hierarchy is:

\[
\begin{aligned}
\mathrm{D1}&:\text{ promotion typing rule},\\
\mathrm{D2}&:\text{ stop-mode invariant},\\
\mathrm{D3}&:\text{ greedy first-boundary rule},\\
\mathrm{D4}&:\text{ boundary-relative greedy factorization theorem},\\
\mathrm{D5}&:\text{ conditional exact-residual faithfulness lemma},\\
\mathrm{D6}&:\text{ certified-prefix stability corollary},\\
\mathrm{D7}&:\text{ stateful Decoder composition theorem}.
\end{aligned}
\]

The integrated result is therefore a closure package of Decoder specification and proved consequences, not a newly independent theorem.

Define:

\[
\boxed{
\mathsf{AbstractDecoderSafe}_k
}
\]

as satisfaction of S1--S4, D4, D7, D6, and the stated conditional D5 component.

The conclusion is:

\[
\boxed{
\text{only certified terminal history is promoted},
}
\]

\[
\boxed{
\text{the unresolved exact tail and remaining boundaries are conserved},
}
\]

\[
\boxed{
\text{certified output is stable under legal continuation},
}
\]

and, conditionally:

\[
\boxed{
\text{different extracted terminal residues are not deleted at the upper exact layer}.
}
\]

This completed package is called:

\[
\boxed{
\textbf{Abstract Decoder Safety Closure}.
}
\]

---

#### 14.3.11 Scope and Re-Proof Boundary

The closure above is proved for finite sequential exact-word histories.

It does not prove:

1. that a terminal boundary exists in a chosen concrete realization,
2. that the supplied future-boundary sequence is generated by the Time Engine itself,
3. that \(r_k\), \(J_k\), or \(\iota_{k+1}\) satisfy the required concrete faithfulness properties,
4. uniqueness in a branching history DAG where prefix totality is absent.

A branching-DAG extension must re-prove first-boundary selection, greedy factorization, certified-prefix irreversibility, and continuation composition.
## 15. Residual Transport Condition

For a terminal cell witness \(\mathbf D\), let:

\[
r_k(\mathbf D)
\in
\mathcal R_k^{\mathrm{term}}
\]

be its full history residue, and:

\[
F_k(\mathbf D)
=
\delta_k(r_k(\mathbf D))
\]

its exact-state displacement projection.

Let:

\[
J_k:
\mathcal R_k^{\mathrm{term}}
\longrightarrow
\mathcal I_{k+1}
\]

be the residual transport map.

### R1. Zero Preservation

\[
J_k(0)=0.
\]

### R2. Faithfulness on Terminal Residue Classes

\[
J_k(r)=J_k(s)
\quad\Longrightarrow\quad
r=s.
\]

Different full terminal residues are not collapsed into one exact upper internal state.

### R3. Visible Compression Without Exact Deletion

Let:

\[
\operatorname{PCl}_k(\mathbf D)
=
\iota_{k+1}
\left(
q_k(\mathbf D),
J_k(r_k(\mathbf D))
\right).
\]

Then:

\[
\pi_{k+1}^A
\left(
\operatorname{PCl}_k(\mathbf D)
\right)
=
q_k(\mathbf D),
\]

while:

\[
r_k(\mathbf D)\neq0
\quad\Longrightarrow\quad
\operatorname{PCl}_k(\mathbf D)
\neq
\iota_{k+1}(q_k(\mathbf D),0).
\]

Therefore:

\[
\boxed{
\text{upper-scale invisibility}
\neq
\text{exact deletion}.
}
\]

---

## 16. Nondegeneracy Condition

Faithful storage alone is not a structural phase transition. The transported residue must remain active in the upper generating level.

### N1. Phase-Rank Change

\[
\beta_k\in\widetilde A_k^+
\quad\longmapsto\quad
\operatorname{PCl}_k(\mathbf D_k)
\in\widetilde A_{k+1}.
\]

An extended lower process becomes one upper operation.

### N2. Nontrivial Exact Residue

The foundation-level nontriviality condition is:

\[
\boxed{
r_k(\mathbf D_k)\neq0.
}
\]

The stronger spring-chart condition is:

\[
F_k(\mathbf D_k)
=
\delta_k(r_k(\mathbf D_k))
\neq0.
\]

Thus a full history residue may be nontrivial even when a particular displacement projection fails to see it. A zero full residue gives a degenerate exact closure.

### N3. Upper-Scale Exact Activity

For every residue class admitted as active, there exist an upper exact context:

\[
c_{k+1}\in\widetilde A_{k+1}^*,
\]

and an upper exact state:

\[
Y_{k+1}\in\mathcal X_{k+1},
\]

such that:

\[
\boxed{
U_{k+1}
\left(
\operatorname{PCl}_k(\mathbf D_k)c_{k+1}
\right)Y_{k+1}
\neq
U_{k+1}
\left(
\iota_{k+1}(q_k(\mathbf D_k),0)c_{k+1}
\right)Y_{k+1}.
}
\]

This is exact activity.

Visible detectability is the stronger optional condition:

\[
\mu_{k+1}U_{k+1}
\left(
\operatorname{PCl}_k(\mathbf D_k)c_{k+1}
\right)Y_{k+1}
\neq
\mu_{k+1}U_{k+1}
\left(
\iota_{k+1}(q_k(\mathbf D_k),0)c_{k+1}
\right)Y_{k+1}.
\]

The foundation requires that the residue remain capable of changing upper exact generation. It need not be immediately visible in every upper observation port.

---

## 17. Definition — Genuine Phase-Closure

A terminal cell witness \(\mathbf D_k\) undergoes genuine structural phase-closure when:

\[
\boxed{
\mathrm T_k
\land
\mathrm R_k
\land
\mathrm N_k
}
\]

holds.

That is:

1. one minimal local phase unit terminates,
2. its full exact residue is transported without deletion,
3. the resulting upper operation has a different operational rank and remains active in upper generation.

The characteristic transition is:

\[
\boxed{
\mathbf D_k[X_k^-,E_k^+;\beta_k]
\xrightarrow{\mathrm T_k}
[\beta_k,r_k]
\xrightarrow{\mathrm R_k}
\operatorname{PCl}_k(\mathbf D_k)
\xrightarrow{\mathrm N_k}
\text{active upper exact operation}.
}
\]

---

## 18. Phase-Closure Recognition Criterion

If a terminal cell witness satisfies T, R, and N, then its image under \(\operatorname{PCl}_k\) is neither mere stopping, compression, relabeling, nor archival storage. It is a nondegenerate structural phase transition by Definition 17.

This is a recognition criterion, not an independent existence theorem.

The first substantive theorem of the engine is the Terminal Block Factorization Theorem in Section 13.

---

## 19. Degenerate Cases

### 19.1 Termination Without Transport

\[
\mathrm T_k\land\neg\mathrm R_k.
\]

This is stopping, deletion, or information loss.

### 19.2 Transport Without Nondegeneracy

\[
\mathrm R_k\land\neg\mathrm N_k.
\]

This is storage, compression, or archival encoding.

### 19.3 Change Without Terminality

\[
\mathrm N_k\land\neg\mathrm T_k.
\]

This is an internal bifurcation, nonlinear transition, or incomplete change.

### 19.4 Zero-Residue Closure

\[
\mathrm T_k\land\mathrm R_k,
\qquad
r_k(\mathbf D_k)=0.
\]

This is a degenerate exact loop. It may repeat visibly, but it does not carry a nontrivial exact history into the next scale.

---

# Part VI — Fractal Phase-Closure Tower

## 20. Recursive Scale Formation

Let:

\[
\sigma_k
=
\beta_1\cdots\beta_m\rho
\]

be the maximal terminal factorization at scale \(k\).

The closed cell chain becomes the upper exact history:

\[
\widetilde\sigma_{k+1}
:=
\widehat{\operatorname{PCl}}_k^{X_0,\mathbf E^+}(\sigma_k)
=
\operatorname{PCl}_k(\mathbf D_1)
\cdots
\operatorname{PCl}_k(\mathbf D_m)
\in
\widetilde A_{k+1}^*.
\]

The unclosed tail \(\rho\) remains at scale \(k\) until a future continuation completes its causal-cell boundary.

The common Phase-Closure theory acts again on the upper exact history:

\[
\widetilde\sigma_{k+1}
\xrightarrow{\mathfrak G_{k+1}}
\text{upper causal-cell chain}
\xrightarrow{\widehat{\operatorname{PCl}}_{k+1}}
\widetilde\sigma_{k+2}.
\]

Therefore the operational recurrence is:

\[
\boxed{
\text{lower exact history}
\to
\text{terminal causal-cell chain}
\to
\text{upper exact-operation chain}
\to
\text{upper causal-cell chain}.
}
\]

This is the confirmed front form of closure-recursive fractality.

---

## 21. Global Time Engine

The full front engine is:

\[
\boxed{
\mathcal T
=
\left\{
\mathcal D_k,
\mathcal M_k\models\mathsf{PC},
\operatorname{Term}_k,
\mathfrak F_k,
r_k,
J_k,
q_k,
\operatorname{PCl}_k,
\widehat{\operatorname{PCl}}_k
\right\}_{k\in\mathbb N}.
}
\]

No single local member is the whole Time Engine.

The global engine is the directed system in which:

1. lower histories are cut into terminal causal cells,
2. each cell becomes one residue-bearing upper operation,
3. cell adjacency becomes upper causal order,
4. the same Phase-Closure axioms act again.

A local self-time is a scale-restricted chart:

\[
\mathcal T|_k.
\]

It is structurally complete at its own scale but remains one local realization of the global causal-cell complex.

---

# Part VII — Geometric Local Chart

## 22. Minimal Spring Geometry

The spring remains the minimal geometric chart of a local Time Engine.

\[
x(t)=r(t)\cos\theta(t),
\]

\[
y(t)=r(t)\sin\theta(t),
\]

\[
z(t)=Z(t).
\]

with:

\[
\theta(t+T)
\equiv
\theta(t)
\pmod{2\pi},
\]

and:

\[
Z(t+T)>Z(t).
\]

The phase returns.  
The exact state does not.

The revised interpretation is:

\[
\theta\text{-return}
\quad\leftrightarrow\quad
\mu_k(X_k^+)=\mu_k(X_k),
\]

and:

\[
Z\text{-advance}
\quad\leftrightarrow\quad
F_k\neq0.
\]

The spring is not the generator of the global Time Engine.

It is the geometric image of one phase-closure chart.

---

## 23. Two Depth Coordinates

The previous notation conflated winding count and irreversible residue depth.

They are separated here.

### 20.1 Winding Count

For period \(T_s\):

\[
\nu_s(t)
=
\frac{t}{T_s}.
\]

This records completed local turns.

### 20.2 Irreversible Residue Depth

Let:

\[
h_s:
\mathcal R_s^{\mathrm{term}}
\to
\mathbb R_{\ge0}
\]

be a scale-local depth functional.

Define:

\[
\zeta_s(N)
=
\sum_{j=1}^{N}
h_s(F_{s,j}).
\]

For nontrivial temporal closure require:

\[
F\neq0
\quad\Longrightarrow\quad
h_s(F)>0.
\]

Then:

\[
\Delta\zeta_s>0
\]

records exact non-return rather than mere cycle count.

Thus:

\[
\nu_s
\neq
\zeta_s.
\]

The function \(h_s\) remains an open definition problem.  
Possible inputs include grade, exact-response depth, norm, scale sensitivity, or a new residue valuation.

---

## 24. Multi-Scale Spring

The Multi-scale Spring is not a collection of unrelated springs.

It is the family of geometric realizations:

\[
\left\{
\mathcal S_k
\right\}_{k\in K}
\]

of the same phase-closure grammar.

The periods may satisfy:

\[
T_{k+1}=N_kT_k,
\]

with:

\[
\omega_k=\frac{2\pi}{T_k},
\qquad
\omega_{k+1}=\frac{\omega_k}{N_k}.
\]

Scale sensitivity may be represented by:

\[
\lambda_{k+1}
=
\lambda_k^{N_k}.
\]

These relations are realization-level constraints, not the definition of fractality itself.

Fractality lies in the repetition:

\[
\text{history}
\rightarrow
\text{terminal closure}
\rightarrow
\text{upper operation}.
\]

---

## 25. Same-Phase Stem

For a local phase coordinate \(\theta_k\), define:

\[
\operatorname{Stem}_{k,\theta_0}
=
\left\{
X\in\mathcal X_k
\;\middle|\;
\theta_k(X)=\theta_0
\right\}.
\]

States on one Stem may share visible phase while carrying different exact residues:

\[
E[F_1],
\quad
E[F_2],
\quad
E[F_3].
\]

Therefore Same-phase Stem does not identify states.

It preserves:

\[
\boxed{
\text{same phase, different history}.
}
\]

Across scales, Stem families indicate corresponding phase positions in different local charts.  
Their exact states need not be equal.

---

## 26. Common Present Section and Clock Needle

Let:

\[
Z_0
\]

denote a common present-section structure across a compatible family of scales.

The Trans-scale Clock Needle is not an external absolute clock added after local times are built.

It is a transverse compatibility section:

\[
\mathcal N_\tau
=
\left\{
X_k(\tau)
\right\}_{k\in K}
\]

whose members may be read as belonging to one macro-present when scale and frame compatibility conditions hold.

A local representation may satisfy:

\[
Z_{0,k}(\tau)
=
Z_0|_k.
\]

The Needle does not erase local irreversible depths:

\[
\zeta_k\neq\zeta_j
\]

is allowed.

It asserts only that the local states admit one compatible transverse reading.

The exact construction of \(Z_0\) and the compatibility maps remains open.

---

# Part VIII — Local Closure Mechanics

## 27. Consistency Loop

At one scale:

\[
E_k
\xrightarrow{\operatorname{Select}_k}
\sigma_{E_k}
\xrightarrow{\operatorname{Eval}_k}
E_k'.
\]

Visible closure requires:

\[
d_k(E_k',E_k)\le\epsilon_k.
\]

Exact closure data additionally records:

\[
F_k
=
X_k^+-X_k.
\]

The revised local closure record is:

\[
\boxed{
\operatorname{Loop}_k
=
(E_k,\sigma_{E_k},E_k',F_k).
}
\]

The old equation:

\[
E_k\Rightarrow\sigma_{E_k}\Rightarrow E_k'
\]

is retained, but no longer exhausts closure.

It is the visible projection of an exact closure event.

---

## 28. StableLoop

A StableLoop is a locally stable representative of a terminal phase candidate.

Write:

\[
\operatorname{StableLoop}_k
=
[E_k,\sigma_{E_k},F_k]_{\mathrm{st}}.
\]

Its role is now precise:

> StableLoop is the local stability component of the terminal condition and the candidate carrier of phase-closure.

StableLoop is not the whole Time Engine.

It becomes globally relevant only when:

\[
\operatorname{PCl}_k
\left(
\operatorname{StableLoop}_k
\right)
\]

creates an active upper-scale operation.

---

## 29. Path Selection and Residue Isolation

The engine distinguishes:

1. visible closure mismatch,
2. exact self-residue,
3. residue transferred into adjacent closures,
4. generative residue that becomes upper-scale activity.

Let:

\[
\Delta e_{j,\mathrm{ext}}^*(\sigma)
\]

denote residue increase imposed on another local closure \(j\).

A strict no-scattering candidate set is:

\[
\Sigma_{k,E}^{\mathrm{sealed}}
=
\left\{
\sigma\in\Sigma_{k,E}^{\min}
\;\middle|\;
\Delta e_{j,\mathrm{ext}}^*(\sigma)\le0
\quad
\forall j\neq k
\right\}.
\]

When this set is nonempty, path selection occurs inside it:

\[
\sigma_{E_k}
\in
\arg\min_{\sigma\in\Sigma_{k,E}^{\mathrm{sealed}}}
L_{\mathrm{path},k}(\sigma).
\]

A soft loss may retain the legacy form:

\[
L_{\mathrm{path},k}(\sigma)
=
e_{\mathrm{self,residue}}^*(\sigma)
+
\lambda
\sum_{j\in\mathcal N_k}
\max
\left(
0,
\Delta e_{j,\mathrm{ext}}^*(\sigma)
\right).
\]

The hard sealed condition and the soft path loss must not be confused.

The soft loss penalizes scattering.  
Only the hard condition forbids it.

---

## 30. Projection Residue and Exact Residue

The previous V18 projection residue:

\[
e_{\mathrm{proj}}^*
=
\left\|
\Pi-\operatorname{proj}_t(\Pi)
\right\|
\]

is retained as an interpretation of information not represented by one time-axis projection.

However:

\[
e_{\mathrm{proj}}^*
\]

must not automatically be identified with:

\[
F_k.
\]

Their roles differ.

- \(e_{\mathrm{proj}}^*\): remainder relative to a chosen projection.
- \(c_k\): visible result mismatch.
- \(F_k\): exact state displacement under result return.

A realization may later define maps between them:

\[
F_k
\mapsto
e_{\mathrm{proj}}^*,
\qquad
F_k
\mapsto
c_k,
\]

but no equality is assumed at the foundation level.

---

## 31. Spark and Unconverted Residue

The legacy split is retained as an interpretation layer:

\[
e^*
=
e_{\mathrm{spark}}^*
+
e_{\mathrm{unconverted}}^*.
\]

In the present architecture:

- `spark` is residue that becomes active under an admitted upper-scale context,
- `unconverted residue` is residue that remains locally unresolved or is improperly exported.

Upper-scale exact activity gives a structural definition of generative spark.

For a terminal cell witness \(\mathbf D_k\), the residue is generative at \(k+1\) when there exist:

\[
c_{k+1}\in\widetilde A_{k+1}^*,
\qquad
Y_{k+1}\in\mathcal X_{k+1},
\]

such that:

\[
U_{k+1}
\left(
\operatorname{PCl}_k(\mathbf D_k)c_{k+1}
\right)Y_{k+1}
\neq
U_{k+1}
\left(
\iota_{k+1}(q_k(\mathbf D_k),0)c_{k+1}
\right)Y_{k+1}.
\]

This does not imply that every active residue is safe or beneficial.

---

# Part IX — Object and Multi-Reference Structure

## 32. Object

The former definition:

\[
\text{Object}
=
\text{locally stable closure of result-selected history}
\]

is retained but repositioned.

A local object candidate is:

\[
O_k
=
[E_k,\sigma_{E_k},F_k]_{\mathrm{st}}.
\]

A phase-closed object at the next scale is:

\[
O_{k+1}
=
\operatorname{PCl}_k(O_k).
\]

Thus an object may be read in two ranks:

- at scale \(k\): a stable closed process,
- at scale \(k+1\): an operation or state-bearing unit.

The object is not identified with the visible result alone.

\[
O_k[E,F_1]
\neq
O_k[E,F_2]
\]

may hold under the same visible result.

---

## 33. Multi-Reference Objectivity

Let:

\[
R_i
\]

be reference frames with result spaces:

\[
\mathcal E_i.
\]

To compare results across frames, introduce a common comparison space:

\[
\mathcal E_*,
\]

and calibration maps:

\[
\chi_i:
\mathcal E_i
\to
\mathcal E_*.
\]

Then:

\[
\operatorname{Objective}_{\epsilon}(\mathbf E)
\]

holds when there exists:

\[
E_*\in\mathcal E_*
\]

such that:

\[
d_*
\left(
\chi_i(E_i'),E_*
\right)
\le\epsilon_i
\quad
\forall i.
\]

For the Time Engine, result agreement alone is insufficient.

The selected history family:

\[
\boldsymbol\sigma_{\mathbf E}
=
\{\sigma_{E_i}^{R_i}\}_{i\in I}
\]

must also satisfy scale / frame compatibility conditions.

Thus objective time is not ownership of one absolute local timeline.

It is:

\[
\boxed{
\text{compatible membership of multiple local phase-closures in one global tower}.
}
\]

The exact compatibility maps remain to be defined.

---

# Part X — Legacy Extensions Retained

## 34. Future-Side Frame Calling

The legacy candidate:

\[
\operatorname{FutureCall}(E_k)
:=
\operatorname{Select}_k
(E_k,\Sigma_k^{\mathrm{kin}};P_k)
\]

is retained as an extension name for result-side history access.

It does not imply literal rewriting of an already instantiated past.

It changes the selected attribution or admissible history representative while preserving winding monotonicity and exact recorded closure.

---

## 35. Harm, Gift, Baffle, and Lighthouse

These terms are retained as an interpretive and design layer, not as foundational mathematics.

- Harm: an operation increases unconverted residue in another closure.
- Gift: an operation increases another closure’s generative capacity without forcing residue transfer.
- Baffle: a structure blocks careless residue absorption.
- Lighthouse: a structure makes a viable path legible without forcing closure.

The foundation-level distinction is:

\[
\text{self-contained phase-closure}
\]

versus:

\[
\text{closure achieved by exporting unresolved residue}.
\]

Ethical interpretation may be applied after the mathematical structure is determined.

---

## 36. Bore

Bore is retained as a non-closing transport mode.

It carries unresolved residue without running a new result-selection closure:

\[
\theta=\mathrm{const.},
\qquad
\text{no new }\operatorname{Select},
\qquad
F\text{ transported}.
\]

Bore is therefore not a phase-closure.

It is a residue-conduction operation used when the current scale does not satisfy the terminal condition.

This distinction becomes sharper under the new architecture:

\[
\boxed{
\text{Bore transports an open phase;}
\quad
\operatorname{PCl}\text{ closes and changes phase.}
}
\]

---

# Part XI — Complete Engine

## 37. Local Engine Equation

At scale \(k\), a result requirement \(E_k^+\) cuts a compatible causal cell from the inherited exact state \(X_k^-\).

A selected exact history block satisfies:

\[
\beta_k
\in
\Sigma_k^{\mathcal D}(X_k^-,E_k^+).
\]

Its endpoint and visible mismatch are:

\[
X_k^+
=
U_k(\beta_k)X_k^-,
\]

\[
c_k
=
d_k^{\mathcal E}
\left(
\mu_k(X_k^+),E_k^+
\right).
\]

If:

\[
\operatorname{Term}_k(X_k^-,\beta_k;E_k^+),
\]

then the terminal witness is:

\[
\mathbf D_k[X_k^-,E_k^+;\beta_k].
\]

Its full residue and displacement projection are:

\[
r_k(\mathbf D_k),
\qquad
F_k=\delta_k(r_k(\mathbf D_k)).
\]

If residual transport and nondegeneracy also hold:

\[
\boxed{
\operatorname{PCl}_k(\mathbf D_k)
=
\iota_{k+1}
\left(
q_k(\mathbf D_k),
J_k(r_k(\mathbf D_k))
\right)
\in
\widetilde A_{k+1}.
}
\]

---

## 38. Global Engine Equation

The complete front recursion is:

\[
\boxed{
\begin{aligned}
\sigma_k
&=
\beta_1\cdots\beta_m\rho,
\\
\mathbf D_j
&=
\mathbf D_k[X_{j-1},E_j^+;\beta_j],
\\
\widetilde\sigma_{k+1}
&=
\operatorname{PCl}_k(\mathbf D_1)
\cdots
\operatorname{PCl}_k(\mathbf D_m),
\\
\widetilde\sigma_{k+1}
&\in
\widetilde A_{k+1}^*,
\\
\widetilde\sigma_{k+1}
&\xrightarrow{\mathfrak G_{k+1}}
\text{next terminal causal-cell chain}.
\end{aligned}
}
\]

The lower open tail \(\rho\) remains uncontracted.

The global engine therefore does not advance by replacing every lower history with a symbol. It advances only across certified terminal boundaries, preserving exact residue and causal adjacency.

---

## 39. Time Statement

The legacy statement:

> Time is the propagation of result–history–result closure.

is retained as a local operational description.

The global statement is stronger:

> **Time is the fractal propagation of nondegenerate phase-closures, in which a terminal local history becomes an active upper-scale operation without deletion of its exact residue.**

Formula:

\[
\boxed{
T
=
\operatorname{FractalPropagation}
\left(
\operatorname{PCl}_k
\right)_{k\in K}.
}
\]

---

# Part XII — Status and Open Problems

## 40. Closed at the Architectural Level

The following are now fixed as architectural commitments:

1. The Time Engine is global before it is local.
2. Its globality is a scale-recursive causal-cell complex.
3. Its fractality is recurrence of one typed Phase-Closure theory, not equality of exact states.
4. Exact and visible operation alphabets are distinct.
5. Closure is a transition from a lower process block to one upper exact operation.
6. Terminality is state- and future-boundary-dependent.
7. A terminal block is a minimal first boundary, not exhaustion of all motion in a phase family.
8. Finite sequential exact histories admit a unique boundary-relative greedy factorization under the abstract Decoder assumptions.
9. Decoder logic is stratified into typing and stop specifications (D1–D3), a major factorization theorem (D4), a conditional exact-residual lemma (D5), a stability corollary (D6), and a stateful continuation theorem (D7).
10. The Abstract Decoder Safety Closure is proved as a package: only certified terminal blocks are promoted, while open tails, unconsumed boundaries, and the consumed-prefix state are preserved for continuation.
11. Lower causal-cell adjacency becomes upper causal order.
12. Full history residue and state displacement are distinct types.
13. Free Number Core v1 supplies the intended exact residue-preserving substrate.
14. The spring is a local holonomy chart, not the full engine.
15. Bore is open-phase residue transport, not phase-closure.

---

## 41. Abstractly Proved, Conditionally Established

The Abstract Decoder Safety Closure is proved for finite sequential exact-word histories.

Its logical hierarchy is:

- D1: promotion typing rule,
- D2: stop-mode invariant,
- D3: greedy first-boundary rule,
- D4: boundary-relative greedy factorization theorem,
- D5: conditional exact-residual faithfulness lemma,
- D6: certified-prefix stability corollary,
- D7: stateful Decoder composition theorem.

The proved abstract package establishes:

1. termination and unique output of the finite greedy Decoder,
2. promotion of certified terminal cells only,
3. preservation of an unresolved tail as unconsumed exact history,
4. preservation of unconsumed future boundaries,
5. no double execution of the tail,
6. stability of certified output under append-only continuation,
7. exact distinction of different extracted terminal residues, conditional on faithful residual transport and exact-constructor injectivity.

What remains conditional is the concrete construction of:

1. a terminal predicate with actual terminal witnesses,
2. a full terminal-residue extractor \(r_k\),
3. an injective residual transport \(J_k\),
4. an exact constructor \(\iota_{k+1}\) with the required coordinate faithfulness.

The distinction is:

\[
\boxed{
\text{abstract Decoder safety and continuation}
\neq
\text{existence of terminal boundaries in a chosen model}.
}
\]
## 42. Still Open

The following remain undefined or unproved in concrete realizations:

1. A minimal causal-cell model satisfying the abstract Decoder assumptions.
2. Construction and decidability of \(\operatorname{Close}_k\) and \(\operatorname{Term}_k\).
3. First-boundary existence for the minimal spring / causal-cell chart.
4. First-boundary existence in the sequential front model, and a principled selection rule for the later DAG extension.
5. A rigorous terminal equivalence \(\approx_k\).
6. Construction of the full terminal-residue extractor \(r_k\).
7. Conditions under which Free Number exact state fully represents \(r_k\).
8. Construction and proof of injectivity for residual transport maps \(J_k\).
9. Construction and coordinate-faithfulness proof for \(\iota_{k+1}\).
10. Classification of active and null residues by upper response.
11. The irreversible-depth valuation \(h_k\).
12. Construction of \(Z_0\) and Trans-scale Clock Needle compatibility.
13. Reference-frame compatibility for \(\operatorname{Objective}_\epsilon\).
14. Branching and merging in a scale DAG / directed causal-cell complex, including re-proofs of greedy selection, irreversibility, and composition.
15. Generation of the future-boundary schedule from result selection.
16. Additional conditions for a thermodynamic or physical phase-transition claim.
## 43. Next Minimal Proof Target

The Abstract Decoder Safety Closure is complete at the finite sequential exact-word level.

The next target is the first concrete existence result:

\[
\boxed{
\textbf{First Terminal Boundary Lemma}
}
\]

Construct the smallest local spring / causal-cell realization in which, for an admitted inherited state and future requirement, at least one terminal prefix exists:

\[
\exists\beta
\quad
\operatorname{Term}_k(X_k^-,\beta;E_k^+).
\]

Because the front history is a literal sequential word, the shortest such prefix is then automatically unique.

The lemma must establish:

1. a finite terminal prefix exists,
2. its shortest instance has no proper admissible prefix closing the same cell,
3. the boundary mode is locally stable,
4. its endpoint is a legal renewal state.

Only after this lemma is closed should the engine proceed to concrete residual transport and N3.

The subsequent order is:

\[
\boxed{
\text{First Terminal Boundary}
\to
r_k
\to
J_k
\to
\text{upper exact activity}
\to
h_k.
}
\]

---

# Part XIII — Carry

## 44. One-Line Carry

> **タイムエンジンとは、同一生成則が各スケールで局所相を閉じ、その終端履歴が exact residue を失わず上位スケールの能動的な一操作へ転じる、フラクタル相転移機関である。**

---

## 45. Three Conditions Carry

\[
\boxed{
\text{Phase-Closure}
=
\text{Terminality}
+
\text{Residual Transport}
+
\text{Nondegeneracy}.
}
\]

Japanese:

\[
\boxed{
\text{相転移閉包}
=
\text{終端条件}
+
\text{残差移送}
+
\text{非退化条件}.
}
\]

---

## 46. Fractal Carry

\[
\boxed{
\mathcal M_k\models\mathsf{PC}
\quad\forall k,
\qquad
\widetilde A_{k+1}^{\mathrm{gen}}
=
\operatorname{im}\operatorname{PCl}_k.
}
\]

---

## 47. Residue Carry

\[
\boxed{
r_k(\mathbf D_k)\neq0,
\qquad
F_k=\delta_k(r_k(\mathbf D_k)),
\qquad
\mu_k(X_k^+)=\mu_k(X_k^-)
\text{ in the return case}.
}
\]

---

## 48. Final Line

> **閉じるとは終わることではない。旧相の履歴が、残差を保持したまま次相の生成単位へ転じることである。**
