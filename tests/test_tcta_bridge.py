"""Tests for nych.tcta_bridge: wiring tcta_engine's Omega(C)/SPREAD/
ALGORITHM_SELECT onto NYCH's real domain -> constraint -> selection stage
(domain.expand_domain -> constraint.apply_constraints ->
selection.select_candidate).

Builds real CandidateTransform/ConstraintMask/SelectionResult objects via
the actual pipeline functions (not mocks), consistent with the rest of
this session's testing approach. Uses stdlib unittest (no pytest install
available in this session)."""

import unittest

from nych.constraint import apply_constraints
from nych.domain import expand_domain
from nych.selection import select_candidate
from nych.types import CandidateTransform, NychContext, NychState
from nych.tcta_bridge import (
    compute_narrowing,
    constraint_check_from_mask,
    verify_omega_c_matches_constraint_mask,
)


def _generate_candidates(expansion):
    candidates = []
    for tote in expansion.tote_candidates:
        candidates.append(
            CandidateTransform(
                transform_id=tote["tote_id"],
                input_state={"domain": expansion.domain},
                output_state={"domain": expansion.domain, "technique": expansion.technique},
                technique=expansion.technique,
                tote=tote,
                admissibility_evidence=["domain_match", "competency_match"],
                score=tote.get("admissibility_score", 1.0),
            )
        )
    return candidates


def _context(domain, intent="process", competency="novice"):
    return NychContext(domain=domain, subject="user", intent=intent, competency=competency)


class TestConstraintCheckFromMask(unittest.TestCase):
    def setUp(self):
        self.context = _context("programming", intent="design")

    def test_all_generated_candidates_are_admissible(self):
        # domain.py's _generate_tote_candidates (plus an optional extra
        # record from the TOTE loop database, if one is locally present --
        # see expand_domain's db lookup) always produces candidates whose
        # output_state's domain matches expansion.domain and whose
        # admissibility_evidence is non-empty, so apply_constraints (real
        # function, not mocked) should admit every one of them.
        expansion = expand_domain(None, self.context, NychState(current={}))
        candidates = _generate_candidates(expansion)
        mask = apply_constraints(candidates, self.context, None, NychState(current={}))
        self.assertEqual(mask.admissible_count, len(expansion.tote_candidates))
        self.assertEqual(mask.rejected_count, 0)

    def test_constraint_check_matches_mask_admissibility(self):
        expansion = expand_domain(None, self.context, NychState(current={}))
        candidates = _generate_candidates(expansion)
        mask = apply_constraints(candidates, self.context, None, NychState(current={}))
        check = constraint_check_from_mask(mask)
        for c in candidates:
            stamped = {**c.output_state, "_transform_id": c.transform_id}
            expected = c in mask.admissible_candidates
            self.assertEqual(check(stamped, None), expected)


class TestVerifyOmegaCMatchesConstraintMask(unittest.TestCase):
    def test_recomputed_omega_c_matches_for_admitted_candidates(self):
        context = _context("medical", intent="diagnose")
        expansion = expand_domain(None, context, NychState(current={}))
        candidates = _generate_candidates(expansion)
        mask = apply_constraints(candidates, context, None, NychState(current={}))
        self.assertTrue(verify_omega_c_matches_constraint_mask(candidates, mask))

    def test_recomputed_omega_c_matches_when_some_are_rejected(self):
        context = _context("construction", intent="measure", competency="expert")
        expansion = expand_domain(None, context, NychState(current={}))
        candidates = _generate_candidates(expansion)
        # Force a mismatch on one candidate's declared competency so
        # apply_constraints' real competency check rejects it.
        bad = candidates[0]
        tampered = CandidateTransform(
            transform_id=bad.transform_id,
            input_state=bad.input_state,
            output_state={**bad.output_state, "competency": "mismatched-competency"},
            technique=bad.technique,
            tote=bad.tote,
            admissibility_evidence=bad.admissibility_evidence,
            score=bad.score,
        )
        candidates = [tampered] + candidates[1:]
        mask = apply_constraints(candidates, context, None, NychState(current={}))
        self.assertEqual(mask.rejected_count, 1)
        self.assertTrue(verify_omega_c_matches_constraint_mask(candidates, mask))


class TestComputeNarrowing(unittest.TestCase):
    def _mask_and_selection(self, domain="programming", intent="design"):
        context = _context(domain, intent=intent)
        expansion = expand_domain(None, context, NychState(current={}))
        candidates = _generate_candidates(expansion)
        mask = apply_constraints(candidates, context, None, NychState(current={}))
        selection = select_candidate(mask.admissible_candidates, context, None, NychState(current={}))
        return mask, selection

    def test_one_selected_out_of_all_admissible_gives_expected_spread(self):
        mask, selection = self._mask_and_selection()
        result = compute_narrowing(mask, selection)
        self.assertEqual(result.omega_c_count, mask.admissible_count)
        self.assertEqual(result.t_g_count, 1)
        self.assertAlmostEqual(result.spread, 1.0 / mask.admissible_count)

    def test_low_spread_selects_hdrp_localized_with_default_thresholds(self):
        mask, selection = self._mask_and_selection()
        result = compute_narrowing(mask, selection, spread_low=0.5, spread_high=0.9)
        self.assertEqual(result.algorithm_select_result, "HDRP_LOCALIZED")

    def test_no_admissible_candidates_discloses_undefined_spread(self):
        context = _context("legal", intent="draft")
        mask, selection = self._mask_and_selection("legal", "draft")
        # Build an empty mask by hand: no admissible candidates at all.
        from nych.constraint import ConstraintMask

        empty_mask = ConstraintMask(
            admissible_candidates=[],
            rejected_candidates=mask.admissible_candidates + mask.rejected_candidates,
            rejection_reasons={},
            admissible_count=0,
            rejected_count=mask.admissible_count + mask.rejected_count,
        )
        empty_selection = select_candidate([], context, None, NychState(current={}))
        result = compute_narrowing(empty_mask, empty_selection)
        self.assertIsNone(result.spread)
        self.assertIsNone(result.algorithm_select_result)
        self.assertIsNotNone(result.note)


if __name__ == "__main__":
    unittest.main()
