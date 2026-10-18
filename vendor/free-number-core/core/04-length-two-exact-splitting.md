# Length-Two Exact Splitting

**Status:** proved concrete-model theorem and reconstruction coordinate chart  
**Branch:** `core-reconstruction`  
**Depends on:** `core/00-capability-ledger.md`, `core/01-abstract-core.md`, `core/02-conditioned-zero.md`, `core/03-independence-audit.md`  
**Model:** quaternionic boundary words at structural length two

## 0. Purpose

This note closes the first nontrivial grade of the quaternionic boundary-word model exactly.

At length two, the representative space is

\[
B_2=V\otimes V,
\qquad
V=\operatorname{Im}\mathbb H.
\]

Compression sends a boundary word to its quaternionic value,

\[
m_2(u|v)=vu.
\]

The central result is that every length-two representative splits uniquely into:

1. a quaternionic value component;
2. a symmetric trace-free residual component.

More precisely,

\[
\boxed{
B_2\cong \mathbb H\oplus S^2_0V
}
\]

as real vector spaces and as the corresponding rotation modules.

This is not yet a multiplication law on the right-hand side. It is the first exact value-residual coordinate chart for Free Numbers.

The note also proves that the residual coordinate is completely recovered by the canonical length-two internal response

\[
A_2(S)=-2C_S.
\]

Thus length two admits a finite complete signature.

---

## 1. Conventions

Let

\[
V=\operatorname{Im}\mathbb H
=\operatorname{span}_{\mathbb R}\{i,j,k\}
\]

with the Euclidean inner product and orientation determined by quaternion multiplication.

For \(u,v\in V\),

\[
uv=-\langle u,v\rangle+u\times v.
\]

Therefore

\[
vu=-\langle u,v\rangle+v\times u
=-\langle u,v\rangle-u\times v.
\]

The length-two compression map is

\[
m_2:V\otimes V\longrightarrow\mathbb H,
\qquad
m_2(u|v)=vu.
\]

Choose an oriented orthonormal basis \(e_1,e_2,e_3\) of \(V\), and define the metric tensor

\[
g:=\sum_{a=1}^{3}e_a|e_a.
\]

For this note, use the unnormalised wedge convention

\[
u\wedge v:=u|v-v|u.
\]

Let

\[
*: \Lambda^2V\longrightarrow V
\]

be the orientation isomorphism determined by

\[
*(u\wedge v)=u\times v.
\]

---

## 2. Orthogonal tensor decomposition

The standard decomposition of rank-two tensors is

\[
V\otimes V
=
\mathbb Rg
\oplus
\Lambda^2V
\oplus
S^2_0V.
\]

Here:

- \(\mathbb Rg\) is the scalar trace sector;
- \(\Lambda^2V\) is the antisymmetric sector;
- \(S^2_0V\) is the symmetric trace-free sector.

The dimensions are

\[
9=1+3+5.
\]

The first two sectors have total dimension four, matching

\[
\dim_{\mathbb R}\mathbb H=4.
\]

Define the proposed value sector

\[
W_2:=\mathbb Rg\oplus\Lambda^2V.
\]

---

## 3. Action of compression on the three sectors

### 3.1 Metric sector

Since \(e_a^2=-1\),

\[
m_2(g)
=
\sum_{a=1}^{3}e_ae_a
=-3.
\]

Thus the metric line maps isomorphically onto the scalar part of \(\mathbb H\).

### 3.2 Antisymmetric sector

For \(u,v\in V\),

\[
\begin{aligned}
m_2(u\wedge v)
&=m_2(u|v-v|u)\\
&=vu-uv\\
&=-2(u\times v).
\end{aligned}
\]

Equivalently,

\[
m_2|_{\Lambda^2V}=-2*.
\]

Since \(*:\Lambda^2V\to V\) is an isomorphism, the antisymmetric sector maps isomorphically onto the imaginary quaternionic part.

### 3.3 Symmetric trace-free sector

Let

\[
S=\sum_{a,b}S_{ab}\,e_a|e_b
\in S^2_0V.
\]

Then

\[
m_2(S)
=
\sum_{a,b}S_{ab}e_be_a.
\]

The scalar contribution is the negative trace,

\[
-\sum_aS_{aa}=0,
\]

and the imaginary contribution is the contraction of a symmetric coefficient tensor with an antisymmetric multiplication tensor, hence also zero.

Therefore

\[
\boxed{
m_2(S)=0
\qquad(S\in S^2_0V).
}
\]

---

## 4. Length-Two Residual Decomposition Theorem

### Theorem 4.1

The compression map satisfies

\[
\ker m_2=S^2_0V.
\]

Its restriction

\[
m_2|_{W_2}:W_2\longrightarrow\mathbb H
\]

is an isomorphism.

Hence there is a split exact sequence

\[
0
\longrightarrow
S^2_0V
\longrightarrow
B_2
\xrightarrow{\ m_2\ }
\mathbb H
\longrightarrow
0.
\]

### Proof

The decomposition

\[
B_2=W_2\oplus S^2_0V
\]

is direct.

Section 3 shows that:

- \(m_2\) maps \(\mathbb Rg\) isomorphically onto \(\mathbb R\subset\mathbb H\);
- \(m_2\) maps \(\Lambda^2V\) isomorphically onto \(V\subset\mathbb H\);
- \(m_2\) kills \(S^2_0V\).

Therefore \(m_2|_{W_2}\) is an isomorphism onto \(\mathbb H=\mathbb R\oplus V\), and the full kernel is exactly \(S^2_0V\). ∎

---

## 5. Explicit splitting map

Write a quaternion as

\[
q=a+w,
\qquad
a\in\mathbb R,
\quad
w\in V.
\]

Define

\[
\sigma_2:\mathbb H\longrightarrow B_2
\]

by

\[
\boxed{
\sigma_2(a+w)
=
-\frac{a}{3}g
-\frac12*^{-1}(w).
}
\]

Then

\[
\begin{aligned}
m_2(\sigma_2(a+w))
&=
-\frac{a}{3}m_2(g)
-\frac12m_2(*^{-1}(w))\\
&=
-\frac{a}{3}(-3)
-\frac12(-2w)\\
&=a+w.
\end{aligned}
\]

Thus

\[
\boxed{
m_2\circ\sigma_2=\operatorname{id}_{\mathbb H}.
}
\]

The section \(\sigma_2\) is the inverse of \(m_2|_{W_2}\).

It is canonical relative to the metric, orientation, and quaternionic multiplication fixed on \(V\). It is not asserted to be a canonical splitting for every abstract Free Numbers model.

---

## 6. Residual projection

Define

\[
\rho_2:B_2\longrightarrow B_2
\]

by

\[
\boxed{
\rho_2
:=
\operatorname{id}_{B_2}-\sigma_2\circ m_2.
}
\]

For every \(x\in B_2\),

\[
m_2(\rho_2(x))
=
m_2(x)-m_2(\sigma_2(m_2(x)))
=0.
\]

Hence

\[
\rho_2(x)\in\ker m_2=S^2_0V.
\]

The map \(\rho_2\) is the projection onto \(S^2_0V\) along \(W_2\). In particular,

\[
\rho_2^2=\rho_2,
\qquad
\operatorname{im}\rho_2=S^2_0V,
\qquad
\ker\rho_2=W_2.
\]

Every \(x\in B_2\) therefore has the unique decomposition

\[
\boxed{
x
=
\sigma_2(m_2(x))
+
\rho_2(x).
}
\]

The first term is the canonical value lift. The second is the residual tensor.

---

## 7. Exact value-residual coordinates

Define

\[
\Phi_2:B_2\longrightarrow\mathbb H\oplus S^2_0V
\]

by

\[
\boxed{
\Phi_2(x)
=
\bigl(m_2(x),\rho_2(x)\bigr).
}
\]

Define the inverse candidate

\[
\Psi_2:\mathbb H\oplus S^2_0V\longrightarrow B_2
\]

by

\[
\boxed{
\Psi_2(q,S)
=
\sigma_2(q)+S.
}
\]

Then

\[
\Psi_2(\Phi_2(x))
=
\sigma_2(m_2(x))+\rho_2(x)
=x,
\]

and, because \(m_2(S)=0\) and \(\rho_2(S)=S\),

\[
\Phi_2(\Psi_2(q,S))
=(q,S).
\]

Therefore:

### Theorem 7.1 — Exact length-two coordinate theorem

\[
\boxed{
\Phi_2:
B_2
\xrightarrow{\ \cong\ }
\mathbb H\oplus S^2_0V
}
\]

is a linear isomorphism with inverse \(\Psi_2\).

The length-two representative is completely determined by the pair

\[
(q,S)
=
\bigl(m_2(x),\rho_2(x)\bigr).
\]

This is the first exact Free Number coordinate chart in the quaternionic boundary-word model.

It is an exact coordinate statement, not yet an assertion that \(\mathbb H\oplus S^2_0V\) carries the final Free Numbers multiplication.

---

## 8. Explicit formula for a pure boundary word

Let

\[
x=u|v,
\qquad
u,v\in V.
\]

Its compressed value is

\[
q=m_2(u|v)=vu
=-\langle u,v\rangle+v\times u.
\]

The canonical value lift is

\[
\boxed{
\sigma_2(vu)
=
\frac{\langle u,v\rangle}{3}g
+
\frac12(u|v-v|u).
}
\]

The residual projection is

\[
\begin{aligned}
\rho_2(u|v)
&=
u|v-\sigma_2(vu)\\
&=
\frac12(u|v+v|u)
-
\frac{\langle u,v\rangle}{3}g.
\end{aligned}
\]

Thus

\[
\boxed{
\rho_2(u|v)
=
\operatorname{Sym}_0(u|v),
}
\]

the symmetric trace-free part of the rank-one tensor \(u|v\).

The exact length-two coordinate of a pure product is therefore

\[
\boxed{
\Phi_2(u|v)
=
\left(
vu,
\frac12(u|v+v|u)
-
\frac{\langle u,v\rangle}{3}g
\right).
}
\]

This completes the first multiplication table

\[
B_1\times B_1\longrightarrow
\mathbb H\oplus S^2_0V
\]

at the level of exact coordinates.

---

## 9. Canonical internal response

For

\[
S=\sum_{a,b}S_{ab}\,e_a|e_b
\in S^2_0V,
\]

define the canonical length-two internal response

\[
A_2(S):V\longrightarrow\mathbb H
\]

by

\[
A_2(S)(c)
:=
\sum_{a,b}S_{ab}\,e_bc e_a.
\]

The response takes values in \(V\subset\mathbb H\) on \(S^2_0V\).

Let

\[
C_S:V\longrightarrow V
\]

be metric contraction by \(S\). Under the standard identification

\[
S^2_0V
\cong
\operatorname{Sym}_0(V),
\]

\(C_S\) is the symmetric trace-free endomorphism represented by \(S\).

The established length-two insertion-response lemma gives

\[
\boxed{
A_2(S)=-2C_S.
}
\]

Since

\[
S\longmapsto C_S
\]

is injective, so is

\[
A_2|_{S^2_0V}.
\]

Therefore no nonzero length-two residual is invisible to the canonical internal response.

Equivalently,

\[
\boxed{
K_2^{\mathrm{null}}=0.
}
\]

---

## 10. Reconstruction from value and response

Define the residualised exact response signature

\[
\mathcal J_2^{\mathrm{exact}}:B_2
\longrightarrow
\mathbb H\oplus\operatorname{Sym}_0(V)
\]

by

\[
\boxed{
\mathcal J_2^{\mathrm{exact}}(x)
=
\bigl(
 m_2(x),
 A_2(\rho_2(x))
\bigr).
}
\]

Let

\[
q=m_2(x),
\qquad
R=A_2(\rho_2(x)).
\]

Since

\[
R=-2C_{\rho_2(x)},
\]

we recover the residual tensor by

\[
\boxed{
\rho_2(x)
=
C^{-1}\left(-\frac12R\right),
}
\]

where

\[
C:S^2_0V\xrightarrow{\cong}\operatorname{Sym}_0(V)
\]

is the contraction identification.

Then

\[
\boxed{
x
=
\sigma_2(q)
+
C^{-1}\left(-\frac12R\right).
}
\]

### Theorem 10.1 — Finite response completeness at length two

The signature

\[
\mathcal J_2^{\mathrm{exact}}
\]

is injective.

Thus a length-two representative is completely reconstructed from:

1. its quaternionic compressed value;
2. the canonical internal response of its residual projection.

The phrase “one response” here means one response operator \(V\to V\), not one scalar sample. Evaluating the operator on a basis of \(V\) produces a finite matrix certificate with five independent residual coordinates.

Dimensionally,

\[
\underbrace{9}_{B_2}
=
\underbrace{4}_{\mathbb H}
+
\underbrace{5}_{S^2_0V}.
\]

No information remains unaccounted for.

---

## 11. Equality criterion at length two

For \(x,y\in B_2\), the following are equivalent:

\[
x=y,
\]

\[
m_2(x)=m_2(y)
\quad\text{and}\quad
\rho_2(x)=\rho_2(y),
\]

and

\[
m_2(x)=m_2(y)
\quad\text{and}\quad
A_2(\rho_2(x))=A_2(\rho_2(y)).
\]

Therefore:

### Corollary 11.1

At length two, the exact observational relation generated by compressed value and canonical residual response coincides with representative equality.

There is no nontrivial quotient left after both sectors are retained.

This is a length-two theorem only. It does not imply that a similarly small signature is complete at every grade.

---

## 12. The zero fiber as a five-dimensional residual space

The zero fiber is

\[
Z_2
:=
m_2^{-1}(0)
=
S^2_0V.
\]

Hence

\[
\dim Z_2=5.
\]

The additive zero is one element of this fiber,

\[
0_{B_2}\in Z_2,
\]

but it is not the only element.

Every nonzero

\[
S\in S^2_0V
\]

satisfies

\[
m_2(S)=0
\]

while

\[
A_2(S)=-2C_S\neq0.
\]

Thus length two contains a complete concrete family of states that are:

- null under value compression;
- non-null as representatives;
- non-null under admissible internal response;
- finitely distinguishable from one another.

This is the exact concrete realization of the abstract conditioned-zero phenomenon, before assigning any external interpretation to a particular residual.

A separate construction is still required to define a meaningful parameter map

\[
\lambda\longmapsto S_\lambda\in S^2_0V.
\]

The residual vessel exists. The semantics of how a condition selects a point in that vessel are not assumed here.

---

## 13. Two explicit zero-valued examples

### 13.1 Diagonal anisotropy

Let

\[
S_1=i|i-j|j.
\]

Then

\[
m_2(S_1)=ii-jj=-1-(-1)=0.
\]

As an endomorphism,

\[
C_{S_1}
=
\operatorname{diag}(1,-1,0).
\]

Therefore

\[
A_2(S_1)
=-2C_{S_1}
=
\operatorname{diag}(-2,2,0).
\]

The compressed value is zero, but the response is not.

### 13.2 Off-diagonal anisotropy

Let

\[
S_2=i|j+j|i.
\]

Then

\[
m_2(S_2)=ji+ij=-k+k=0.
\]

The associated contraction map exchanges the \(i\)- and \(j\)-directions:

\[
C_{S_2}(i)=j,
\qquad
C_{S_2}(j)=i,
\qquad
C_{S_2}(k)=0.
\]

Hence

\[
A_2(S_2)=-2C_{S_2}\neq0.
\]

Moreover,

\[
A_2(S_1)\neq A_2(S_2),
\]

so the two zero-valued states are distinguished by the canonical response.

---

## 14. What has been completed

At length two, the following are now exact:

1. **Kernel classification**
   \[
   \ker m_2=S^2_0V.
   \]

2. **Value-sector identification**
   \[
   W_2=\mathbb Rg\oplus\Lambda^2V
   \cong\mathbb H.
   \]

3. **Split exact sequence**
   \[
   0\to S^2_0V\to B_2\to\mathbb H\to0.
   \]

4. **Explicit section**
   \[
   \sigma_2(a+w)
   =-\frac a3g-\frac12*^{-1}(w).
   \]

5. **Explicit residual projection**
   \[
   \rho_2=\operatorname{id}-\sigma_2m_2.
   \]

6. **Exact coordinates**
   \[
   B_2\cong\mathbb H\oplus S^2_0V.
   \]

7. **Injective residual response**
   \[
   A_2(S)=-2C_S.
   \]

8. **Finite complete signature**
   \[
   \mathcal J_2^{\mathrm{exact}}(x)
   =
   \bigl(m_2(x),A_2(\rho_2(x))\bigr).
   \]

9. **Exact equality test**
   value equality plus residual-response equality is representative equality.

Length two is therefore not merely an example of residual survival. It is a completely solved value-residual coordinate system.

---

## 15. Deliberate non-claims

This note does not claim:

1. that \(\mathbb H\oplus S^2_0V\) already carries the final Free Numbers multiplication;
2. that the exact splitting has the same form at every grade;
3. that the quaternionic boundary-word model is the universal Free Numbers model;
4. that every abstract condition is a point of \(S^2_0V\);
5. that the residual is a hidden quaternionic scalar;
6. that a single scalar probe recovers the residual;
7. that topological phase, physical volume, or physical time has been represented;
8. that full observational equality at higher length is finitely decidable;
9. that canonical vertical response exhausts every possible response sector at higher grades.

The proved statement is narrower and stronger:

> At structural length two, quaternionic value and symmetric trace-free residual form exact complementary coordinates, and the residual is completely detected by the canonical internal response.

---

## 16. Formalization targets

A Lean formalization of this note should separate the following components.

### F1. Tensor decomposition

Formalize

\[
V\otimes V
\cong
\mathbb Rg\oplus\Lambda^2V\oplus S^2_0V.
\]

### F2. Compression formulas

Prove

\[
m_2(g)=-3,
\qquad
m_2|_{\Lambda^2V}=-2*,
\qquad
m_2|_{S^2_0V}=0.
\]

### F3. Kernel theorem

Prove

\[
\ker m_2=S^2_0V.
\]

### F4. Explicit section and projection

Define \(\sigma_2\) and \(\rho_2\), then prove

\[
m_2\sigma_2=\operatorname{id},
\qquad
\rho_2^2=\rho_2.
\]

### F5. Coordinate equivalence

Construct the linear equivalence

\[
B_2\simeq\mathbb H\oplus S^2_0V.
\]

### F6. Response theorem

Import or reprove

\[
A_2(S)=-2C_S.
\]

### F7. Complete signature

Prove injectivity of

\[
x\longmapsto
\bigl(m_2(x),A_2(\rho_2(x))\bigr).
\]

---

## 17. Next cut: length-three propagation

The next note should not repeat the length-two classification. It should ask how the solved coordinate pair

\[
(q,S)\in\mathbb H\oplus S^2_0V
\]

propagates when a new boundary element is attached.

For \(x\in B_2\) and \(u\in V\), compare

\[
x|u\in B_3
\]

and

\[
u|x\in B_3.
\]

The first questions are:

1. Which part of \(m_3(x|u)\) is determined by \(q=m_2(x)\)?
2. How does \(S=\rho_2(x)\) contribute to the new compressed value?
3. Which new length-three residual components are generated?
4. Are left and right propagation determined by the same data?
5. What cross-boundary term is required for compositional closure?

This is the first genuine propagation test for the exact length-two Free Number coordinates.

---

## 18. Decision

The length-two sector passes the reconstruction gate.

It provides:

- a non-collapsing compression;
- a nontrivial zero fiber;
- a complete residual coordinate;
- an injective contextual response;
- a finite exact equality certificate;
- and an explicit value-residual splitting independent of temporal or cognitive interpretation.

The resulting theorem may be stated compactly as

\[
\boxed{
B_2
\xrightarrow{\ \cong\ }
\mathbb H\oplus S^2_0V,
\qquad
x\longmapsto
\bigl(m_2(x),\rho_2(x)\bigr),
}
\]

with residual recovery

\[
\boxed{
A_2(\rho_2(x))=-2C_{\rho_2(x)}.
}
\]

At length two, compression is not disappearance. It is an exact projection onto the value sector, with a five-dimensional residual complement that remains fully observable under canonical internal response.
