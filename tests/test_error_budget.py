import numpy as np
import pytest

from tidl_poc.models.error_budget import (
    KIND_BIAS,
    KIND_COMMON,
    KIND_RANDOM,
    PROVENANCE_ALLOCATION,
    PROVENANCE_LITERATURE,
    BudgetTerm,
    classify_budget,
    combine_terms,
    literature_tdc_ssp_ps,
    monte_carlo,
    rss,
    scenarios,
)


def test_rss_identity():
    assert rss(np.array([3.0, 4.0])) == pytest.approx(5.0)


def test_independent_gaussians_match_rss():
    terms = [
        BudgetTerm("a", 6.0, PROVENANCE_ALLOCATION, "test", KIND_RANDOM),
        BudgetTerm("b", 8.0, PROVENANCE_ALLOCATION, "test", KIND_RANDOM),
    ]
    samples = monte_carlo(terms, 80_000, seed=0)
    assert np.std(samples, ddof=1) == pytest.approx(10.0, rel=0.03)


def test_correlated_term_inflates_versus_zero_common():
    independent = [
        BudgetTerm("a", 6.0, PROVENANCE_ALLOCATION, "test", KIND_RANDOM),
        BudgetTerm("b", 8.0, PROVENANCE_ALLOCATION, "test", KIND_RANDOM),
    ]
    with_common = independent + [
        BudgetTerm("c", 5.0, PROVENANCE_ALLOCATION, "test", KIND_COMMON),
    ]
    rss_ind = combine_terms(independent)["rss_including_common_ps"]
    rss_all = combine_terms(with_common)["rss_including_common_ps"]
    assert rss_all > rss_ind


def test_bias_excluded_from_precision_rss_included_in_accuracy():
    terms = [
        BudgetTerm("rand", 6.0, PROVENANCE_ALLOCATION, "test", KIND_RANDOM),
        BudgetTerm("bias", 8.0, PROVENANCE_ALLOCATION, "test", KIND_BIAS),
        BudgetTerm("common", 4.0, PROVENANCE_ALLOCATION, "test", KIND_COMMON),
    ]
    c = classify_budget(terms)
    assert c["precision_rss_ps"] == pytest.approx(6.0)
    assert c["precision_rss_with_common_ps"] == pytest.approx(rss(np.array([6.0, 4.0])))
    assert c["accuracy_bias_sum_ps"] == pytest.approx(8.0)
    assert c["accuracy_worst_case_ps"] == pytest.approx(8.0 + c["precision_rss_with_common_ps"])


def test_monte_carlo_does_not_randomise_bias():
    terms = [
        BudgetTerm("rand", 3.0, PROVENANCE_ALLOCATION, "test", KIND_RANDOM),
        BudgetTerm("bias", 100.0, PROVENANCE_ALLOCATION, "test", KIND_BIAS),
    ]
    samples = monte_carlo(terms, 20_000, seed=1)
    assert np.std(samples, ddof=1) == pytest.approx(3.0, rel=0.05)


def test_stress_fails_20ps_illustrative_may_pass():
    sc = scenarios()
    illus = classify_budget(sc["literature_informed_illustrative"])["precision_rss_with_common_ps"]
    cons = classify_budget(sc["conservative"])["precision_rss_with_common_ps"]
    stress = classify_budget(sc["stress"])["precision_rss_with_common_ps"]
    assert stress > 20.0
    assert cons > 20.0
    assert illus < cons < stress


def test_target_allocation_uses_eight_chain_literature_tdc():
    sc = scenarios()
    assert "target_allocation" in sc
    tdc = next(t for t in sc["target_allocation"] if t.name == "fpga_fine_tdc_ssp_ps")
    assert tdc.provenance == PROVENANCE_LITERATURE
    assert tdc.sigma_ps == pytest.approx(literature_tdc_ssp_ps(8), rel=0, abs=1e-12)
    frontend = next(t for t in sc["target_allocation"] if t.name == "frontend_threshold_jitter_ps")
    assert frontend.sigma_ps == 5.0
    assert frontend.provenance == PROVENANCE_ALLOCATION


def test_every_term_has_kind_and_provenance():
    allowed_kind = {KIND_RANDOM, KIND_BIAS, KIND_COMMON}
    allowed_prov = {PROVENANCE_LITERATURE, PROVENANCE_ALLOCATION}
    for terms in scenarios().values():
        for term in terms:
            assert term.kind in allowed_kind
            assert term.provenance in allowed_prov
            assert term.source
            if term.provenance == PROVENANCE_LITERATURE:
                assert "Mao" in term.source
            else:
                assert term.provenance == PROVENANCE_ALLOCATION
