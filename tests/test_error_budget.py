import numpy as np
import pytest

from tidl_poc.models.error_budget import BudgetTerm, combine_terms, monte_carlo, rss, scenarios


def test_rss_identity():
    assert rss(np.array([3.0, 4.0])) == pytest.approx(5.0)


def test_independent_gaussians_match_rss():
    terms = [
        BudgetTerm("a", 6.0, "assumption", "test"),
        BudgetTerm("b", 8.0, "assumption", "test"),
    ]
    samples = monte_carlo(terms, 80_000, seed=0)
    assert np.std(samples, ddof=1) == pytest.approx(10.0, rel=0.03)


def test_correlated_term_inflates_versus_zero_common():
    independent = [
        BudgetTerm("a", 6.0, "assumption", "test"),
        BudgetTerm("b", 8.0, "assumption", "test"),
    ]
    with_common = independent + [BudgetTerm("c", 5.0, "assumption", "test", True)]
    rss_ind = combine_terms(independent)["rss_including_common_ps"]
    rss_all = combine_terms(with_common)["rss_including_common_ps"]
    assert rss_all > rss_ind


def test_stress_fails_20ps_illustrative_may_pass():
    sc = scenarios()
    illus = combine_terms(sc["literature_informed_illustrative"])["rss_including_common_ps"]
    cons = combine_terms(sc["conservative"])["rss_including_common_ps"]
    stress = combine_terms(sc["stress"])["rss_including_common_ps"]
    assert stress > 20.0
    assert cons > 20.0
    # Illustrative is allowed to be under or near 20 ps; it must be below stress.
    assert illus < cons < stress


def test_every_term_has_provenance():
    for terms in scenarios().values():
        for term in terms:
            assert term.provenance in {"literature", "assumption"}
            assert term.source
