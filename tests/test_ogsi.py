"""Tests for nych.ogsi: a concrete Gamma/Psi over domain.expand_domain's
expansion-path trajectories.

Uses stdlib unittest (consistent with TCTA's own test suite -- no pytest
install available in this session; nych's other tests are pytest-based
but are not run here)."""

import unittest

from nych.domain import expand_domain, get_domain_ontology
from nych.ogsi import (
    GammaSignature,
    build_expansion_trajectory,
    gamma_domain_signature,
    known_domain_families,
    psi_resolve_family,
)
from tcta_engine.ogsi import collision_rate, prefix_stability_holds


class _Ctx:
    def __init__(self, domain, intent="process", competency=None):
        self.domain = domain
        self.intent = intent
        self.competency = competency


class _Packet:
    pass


class _State:
    pass


def _expansion(domain: str, intent: str = "process"):
    return expand_domain(_Packet(), _Ctx(domain, intent=intent), _State())


class TestBuildExpansionTrajectory(unittest.TestCase):
    def test_trajectory_has_one_transform_per_waypoint(self):
        expansion = _expansion("programming", intent="design")
        trajectory = build_expansion_trajectory(expansion)
        self.assertEqual(len(trajectory), 3)

    def test_each_transform_result_carries_the_same_domain(self):
        expansion = _expansion("medical", intent="diagnose")
        trajectory = build_expansion_trajectory(expansion)
        for t in trajectory:
            self.assertEqual(t.apply(None)["domain"], "medical")


class TestGammaDomainSignature(unittest.TestCase):
    def test_signature_is_the_domain_label(self):
        expansion = _expansion("construction", intent="measure")
        trajectory = build_expansion_trajectory(expansion)
        sig = gamma_domain_signature(trajectory)
        self.assertEqual(sig, GammaSignature(domain="construction"))

    def test_raises_on_empty_trajectory(self):
        with self.assertRaises(ValueError):
            gamma_domain_signature([])

    def test_prefix_and_full_trajectory_share_signature(self):
        # This is H1 (prefix stability) holding by construction for this
        # Gamma, as the module docstring discloses -- not deep evidence.
        expansion = _expansion("finance", intent="forecast")
        trajectory = build_expansion_trajectory(expansion)
        full_sig = gamma_domain_signature(trajectory)
        prefix_sig = gamma_domain_signature(trajectory[:1])
        self.assertEqual(full_sig, prefix_sig)

    def test_prefix_stability_holds_via_tcta_engine_h1_test(self):
        expansion = _expansion("legal", intent="draft")
        trajectory = build_expansion_trajectory(expansion)
        self.assertTrue(prefix_stability_holds(gamma_domain_signature, trajectory, k=1))
        self.assertTrue(prefix_stability_holds(gamma_domain_signature, trajectory, k=2))


class TestPsiResolveFamily(unittest.TestCase):
    def test_resolves_to_matching_candidate(self):
        sig = GammaSignature(domain="programming")
        resolved = psi_resolve_family(sig, known_domain_families())
        self.assertEqual(resolved, "programming")

    def test_unresolved_when_no_candidate_matches(self):
        sig = GammaSignature(domain="astrology")
        resolved = psi_resolve_family(sig, known_domain_families())
        self.assertIsNone(resolved)

    def test_known_domain_families_excludes_the_unknown_fallback(self):
        families = known_domain_families()
        self.assertNotIn("unknown", families)
        self.assertIn("testing", families)
        self.assertEqual(set(families), set(get_domain_ontology()) - {"unknown"})


class TestCollisionRateAcrossDomains(unittest.TestCase):
    def test_different_domains_never_collide_under_this_gamma(self):
        # H2 (family separability): two different real domains' expansion
        # trajectories, under this Gamma, never collide -- disclosed as a
        # property of this Gamma's construction (it reads only the domain
        # field), not as deep separability evidence.
        programming_family = [
            build_expansion_trajectory(_expansion("programming", intent="design")),
            build_expansion_trajectory(_expansion("programming", intent="test")),
        ]
        medical_family = [
            build_expansion_trajectory(_expansion("medical", intent="diagnose")),
            build_expansion_trajectory(_expansion("medical", intent="monitor")),
        ]
        rate = collision_rate(gamma_domain_signature, programming_family, medical_family)
        self.assertEqual(rate, 0.0)

    def test_same_domain_different_intents_always_collide(self):
        same_domain_a = [build_expansion_trajectory(_expansion("testing", intent="plan"))]
        same_domain_b = [build_expansion_trajectory(_expansion("testing", intent="report"))]
        rate = collision_rate(gamma_domain_signature, same_domain_a, same_domain_b)
        self.assertEqual(rate, 1.0)


if __name__ == "__main__":
    unittest.main()
