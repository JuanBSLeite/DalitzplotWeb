from __future__ import annotations

import pytest

from app.services.particles import ParticleLookupError, resolve_decay, resolve_particle


def test_resolve_pion_in_gev() -> None:
    pion = resolve_particle("pi+")

    assert pion.pdgid == 211
    assert pion.mass_gev == pytest.approx(0.13957039, rel=1e-5)
    assert pion.charge == pytest.approx(1.0)


def test_resolve_three_body_decay() -> None:
    mother, daughters = resolve_decay("D0", ("pi+", "pi-", "pi0"))

    assert mother.mass_gev > sum(item.mass_gev for item in daughters)
    assert [item.pdgid for item in daughters] == [211, -211, 111]


def test_reject_unknown_particle() -> None:
    with pytest.raises(ParticleLookupError):
        resolve_particle("not-a-real-particle")
