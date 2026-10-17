# v18 rev.5 — RR47に用いた原文抜粋

原本：10_ARTIFACTS/TimeEngine/2026-09-13__source__v18-front-snapshot-v001/v18-closed-time-engine-rev5.md
固定取得元：1450f74d628b214d6cb19a95d8f9a184b6e35aec
ローカル原本SHA-256：788cd5e7ce984bd450ec443a2e86ebdc2926bf139e38bc7f4929cc4bc5f05e1f

範囲は一始まり行番号。原文の内容を変更しない。

## CG1: two-boundary causal cell
原本行 131–208

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


## CG5/CG6: terminal witness and full residual transport
原本行 337–494

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


## R1/R2/R3 and N1/N2/N3
原本行 2426–2604

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
