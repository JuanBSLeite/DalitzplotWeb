# Physics conventions

This document records the amplitude conventions used by the Dalitz Plot Web Visualizer.

## Scope

The current amplitude engine is intentionally restricted to

```text
spin-0 mother -> spin-0 daughter 1 + spin-0 daughter 2 + spin-0 daughter 3
```

with an isobar decomposition

```text
M -> R c
R -> a b
```

and orbital angular momentum `L = 0, 1, 2`.

Channels containing a nonzero-spin mother or final-state particle are rejected by the amplitude layer. Such channels require a helicity/canonical-spin formalism and are outside the current implementation.

Only the relativistic Breit-Wigner (`RBW`) lineshape is supported at present.

All masses and momenta are in GeV internally. Barrier radii are in GeV^-1.

## Amplitude

A resonant contribution is

```text
A_r(s) = c_r F_M(p,p0) F_R(q,q0) Z_L(p,q)
         / [m0^2 - s - i m0 Gamma(s)].
```

The full amplitude is the coherent sum

```text
A = sum_r A_r + A_NR.
```

The complex coefficient is

```text
c_r = magnitude * exp(i phase).
```

## Källén function

```text
lambda(x,y,z) = x^2 + y^2 + z^2 - 2xy - 2xz - 2yz.
```

## Resonance-daughter momentum q

For `R(s) -> a b`, the physical breakup momentum in the resonance rest frame is

```text
q(s) = sqrt(lambda(s,m_a^2,m_b^2)) / (2 sqrt(s)).
```

The code explicitly requires

```text
sqrt(s) >= m_a + m_b.
```

Below this threshold, the event-by-event physical momentum is set to zero. This explicit condition avoids incorrectly using the positive Källén branch below the pseudo-threshold for unequal masses.

## Bachelor momentum p

The bachelor momentum is evaluated in the same resonance rest frame,

```text
p(s) = sqrt(lambda(M^2,s,m_c^2)) / (2 sqrt(s)).
```

This is the momentum convention used by the Zemach tensors and by the mother-vertex barrier factor in this project.

## Physical and virtual resonance poles

For a pole inside the kinematically accessible daughter-pair interval

```text
m_min = m_a + m_b
m_max = M - m_c,
```

the reference mass is simply

```text
m_ref = m0.
```

The reference momenta are

```text
q0 = q(m_ref^2)
p0 = p(m_ref^2).
```

A resonance pole may also lie outside the accessible interval. Such a contribution is treated as a virtual resonance: the true pole mass `m0` remains in the Breit-Wigner denominator, while only the reference momenta are evaluated at an effective mass mapped into the physical interval,

```text
m_ref = m_min + (m_max-m_min)/2 *
        [1 + tanh((m0 - (m_min+m_max)/2)/(m_max-m_min))].
```

Thus

```text
q0 = q(m_ref^2)
p0 = p(m_ref^2),
```

while the denominator remains

```text
m0^2 - s - i m0 Gamma(s).
```

This replaces the earlier `sqrt(|lambda|)` subthreshold prescription and avoids the former constant-width threshold fallback.

## Blatt-Weisskopf factors

The dimensionless variable is

```text
z = (q r)^2.
```

The unnormalised factors are

```text
B_0(z) = 1
B_1(z) = 1 / sqrt(1 + z)
B_2(z) = 1 / sqrt(z^2 + 3z + 9).
```

The normalized factor is

```text
F_L(q,q0,r) = B_L((q r)^2) / B_L((q0 r)^2).
```

Therefore

```text
F_L(q0,q0,r) = 1.
```

Each resonant contribution contains

```text
F_R = F_L(q,q0,r_R)
F_M = F_L(p,p0,r_M).
```

Current default radii are

```text
r_R = 1.5 GeV^-1
r_M = 5.0 GeV^-1.
```

## Mass-dependent width

The RBW running width is

```text
Gamma(s) = Gamma0
           (q/q0)^(2L+1)
           (m0/sqrt(s))
           F_R(q,q0)^2.
```

The width is zero where the physical daughter channel is closed.

For an ordinary pole inside the physical interval,

```text
Gamma(m0^2) = Gamma0.
```

For a virtual pole, `q0` is defined at `m_ref`, while `m0` remains the nominal pole parameter in the RBW denominator and in the `m0/sqrt(s)` factor.

## Relativistic Breit-Wigner

The only currently supported lineshape is

```text
RBW(s) = F_M F_R / [m0^2 - s - i m0 Gamma(s)].
```

For a physical pole at `s=m0^2`, where both normalized barrier factors equal one,

```text
RBW(m0^2) = i / (m0 Gamma0).
```

A global sign convention can be absorbed in the complex coefficient, but the convention must remain consistent across all amplitudes.

## Zemach angular terms

Both vectors are evaluated in the resonance rest frame. `q` is the momentum of the first listed resonance daughter and `p` is the bachelor momentum.

```text
Z_0 = 1
Z_1 = -2 p.q
Z_2 = (4/3) [3(p.q)^2 - |p|^2 |q|^2].
```

With

```text
p.q = |p||q| cos(theta),
```

the angular dependence is proportional to

```text
L=0: 1
L=1: cos(theta)
L=2: 3 cos^2(theta) - 1,
```

apart from momentum factors and overall constants.

Changing which resonance daughter defines `q` flips the sign of `Z_1` and is equivalent to a 180-degree phase convention change for that amplitude.

## Bose symmetry

For identical final-state particles, all distinct physical bachelor assignments are summed coherently before component normalization.

If the two particles forming a resonance are identical spin-0 bosons, odd orbital angular momentum is forbidden. The implementation explicitly rejects such a component:

```text
identical spin-0 pair -> L must be even.
```

## Deterministic component normalization

Each complete symmetrized dynamic basis function is normalized using a fixed integration grid that is independent of the visualization grid and of toy-MC generation.

The current deterministic integration grid has resolution

```text
260 x 260
```

before removal of points outside the physical Dalitz boundary.

For a regular grid in `(s12,s13)`, three-body phase space is uniform in `ds12 ds13` up to a common channel-wide factor, so the component integral is evaluated as

```text
N_r ~= sum_i |F_r(s12_i,s13_i)|^2 Delta s12 Delta s13.
```

The normalized basis is

```text
Fhat_r = F_r / sqrt(N_r).
```

The user's magnitude and phase are applied only after this normalization.

The normalization cache key contains the quantities that change the dynamic basis (channel, pair, spin, mass, width, barrier radii, symmetrization) and deliberately excludes magnitude and phase. Therefore a change only in a complex coefficient does not recompute the basis normalization.

Most importantly, `N_r` no longer depends on:

- theoretical-plot display resolution;
- toy event count;
- toy random seed;
- phase-space weights of a particular generated toy sample.

The same cached normalization is reused by theoretical plots and toy generation.

## Theoretical projections

Because the Dalitz phase-space density is constant in `ds12 ds13` up to an overall factor, the theoretical projections numerically integrate the intensity over the complementary invariant. The grid spacings are explicitly included in these sums.

## Fit fractions

Fit fractions are evaluated on the same fixed deterministic integration grid,

```text
FF_r = integral |A_r|^2 dPhi3
       / integral |sum_k A_k|^2 dPhi3.
```

They therefore do not depend on the display resolution or on a toy sample.

Interference is present only in the total denominator, so

```text
sum_r FF_r
```

is not required to equal one.

## Toy Monte Carlo

`phasespace` is used to generate three-body phase-space points. The displayed toy is a weighted sample with

```text
w_total = w_phase_space |A|^2.
```

It is not an unweighted accept-reject sample. The toy weights are used to populate distributions, but they are no longer used to define the amplitude-component normalization.
