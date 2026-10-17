# v18 rev.5 — RR51の全履歴選択と残差評価の原文抜粋

原本SHA-256: 788cd5e7ce984bd450ec443a2e86ebdc2926bf139e38bc7f4929cc4bc5f05e1f
固定取得元: 1450f74d628b214d6cb19a95d8f9a184b6e35aec。一始まり行番号。

## §7 Result-Selected History：原本行 882–938

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



## S2 Greedy First-Boundary Rule：原本行 1719–1745

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



## §29–30 Path Selection and Residue Isolation / Projection Residue and Exact Residue：原本行 3134–3240

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



