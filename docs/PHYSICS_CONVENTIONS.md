# Physics conventions

This document records the amplitude conventions used by the Dalitz Plot Web Visualizer.

## Scope

The current implementation is intended for spin-0 three-body decays described with an isobar model,

```text
M -> R c
R -> a b
```

with spin-0 final-state particles and resonance orbital angular momentum `L = 0, 1, 2`.

A resonant component is evaluated schematically as

```text
A_r(s, angles) = c_r F_M(p) F_R(q) Z_L(p,q) BW(s)
```

with the running-width dependence included in the Breit-Wigner denominator.

All masses and momenta used internally are in GeV. Barrier radii are in GeV^-1.

## Källén function

The implementation uses

```text
lambda(x,y,z) = x^2 + y^2 + z^2 - 2xy - 2xz - 2yz.
```

## Resonance-daughter breakup momentum q

For a resonance with invariant mass squared `s` decaying to particles `a` and `b`,

```text
q(s) = sqrt(lambda(s, m_a^2, m_b^2)) / (2 sqrt(s)).
```

`q` is evaluated in the resonance rest frame.

Below the physical threshold

```text
sqrt(s) < m_a + m_b
```

this implementation sets `q = 0`.

The explicit threshold condition is important for unequal masses because the Källén function becomes positive again below the pseudo-threshold `|m_a-m_b|`; that region is not the physical two-body decay region.

At the pole,

```text
q0 = q(m0^2).
```

## Bachelor momentum p

The project adopts the standard Dalitz/Zemach convention in which the bachelor momentum is also evaluated in the resonance rest frame:

```text
p(s) = sqrt(lambda(M^2, s, m_c^2)) / (2 sqrt(s)).
```

where `M` is the mother mass and `m_c` is the bachelor mass.

At the resonance pole,

```text
p0 = p(m0^2).
```

This convention must not be mixed with alternative formalisms in which a production-barrier momentum is defined in the mother rest frame.

## Blatt-Weisskopf barrier factors

The dimensionless variable is

```text
z = (q r)^2,
```

with momentum in GeV and radius in GeV^-1.

The unnormalised factors implemented are

```text
B_0(z) = 1
B_1(z) = 1 / sqrt(1 + z)
B_2(z) = 1 / sqrt(z^2 + 3z + 9).
```

The factors used in the amplitude are normalised at a reference momentum:

```text
F_L(q,q0,r) = B_L((q r)^2) / B_L((q0 r)^2).
```

Therefore

```text
F_L(q0,q0,r) = 1.
```

Two factors are included for each resonance component:

```text
F_R = F_L(q,q0,r_R)
F_M = F_L(p,p0,r_M).
```

The default radii are currently

```text
r_R = 1.5 GeV^-1
r_M = 5.0 GeV^-1.
```

These are model parameters and can be edited in the frontend.

## Mass-dependent width

The relativistic Breit-Wigner uses

```text
Gamma(s) = Gamma0
           (q/q0)^(2L+1)
           (m0/sqrt(s))
           F_R(q,q0)^2.
```

The width is set to zero below the physical resonance-daughter threshold.

At the pole,

```text
Gamma(m0^2) = Gamma0,
```

because `q=q0` and the normalized resonance barrier factor equals one.

## Relativistic Breit-Wigner

The implemented denominator convention is

```text
BW(s) = F_M F_R / [m0^2 - s - i m0 Gamma(s)].
```

At `s=m0^2`, with normalized barrier factors,

```text
BW(m0^2) = i / (m0 Gamma0).
```

A global sign or phase convention for a Breit-Wigner can be absorbed into the complex coefficient of that component; consistency across all components is what matters physically.

## Zemach angular terms

For spin-0 mother and spin-0 final-state particles, both vectors are evaluated in the resonance rest frame.

`q` denotes the three-momentum of the first listed resonance daughter and `p` denotes the bachelor three-momentum.

The implementation uses

```text
Z_0 = 1
Z_1 = -2 p.q
Z_2 = (4/3) [3(p.q)^2 - |p|^2 |q|^2].
```

Using

```text
p.q = |p||q| cos(theta),
```

the angular dependence is proportional to the expected Legendre-polynomial structure:

```text
L=0: constant
L=1: cos(theta)
L=2: 3 cos^2(theta) - 1
```

up to momentum factors and overall normalisation constants.

### Spin-1 sign convention

Changing which resonance daughter is used to define `q` changes `q -> -q` in the resonance rest frame. Consequently,

```text
Z_1 -> -Z_1,
```

while `Z_0` and `Z_2` are unchanged.

This sign is a convention and is equivalent to a 180-degree phase shift of the corresponding complex coefficient, provided it is handled consistently.

## Complete resonant component

For the current implementation, a resonant chain is therefore

```text
A_r = c_r
      F_M(p,p0,r_M)
      F_R(q,q0,r_R)
      Z_L(p,q)
      / [m0^2 - s - i m0 Gamma(s)].
```

The full model is the coherent sum of all resonant and non-resonant components.

For identical final-state particles, the relevant decay-chain amplitudes are summed coherently before component normalisation.

## Component normalisation

Each complete symmetrized dynamic component is normalized numerically over three-body phase space:

```text
N_r = integral |F_r|^2 dPhi_3.
```

The basis amplitude used in the coherent sum is

```text
Fhat_r = F_r / sqrt(N_r).
```

The fitted/user-supplied complex coefficient is applied only after this normalization.

## Fit fractions

Fit fractions are calculated as

```text
FF_r = integral |A_r|^2 dPhi_3
       / integral |sum_k A_k|^2 dPhi_3.
```

Because interference appears in the denominator but not in the individual numerators, the sum of fit fractions is not required to equal 100%.
