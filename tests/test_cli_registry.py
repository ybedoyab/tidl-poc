from tidl_poc.cli import SIMULATIONS


def test_all_planned_simulations_registered():
    expected = {
        "parallel-chains",
        "calibration",
        "coarse-fine",
        "error-budget",
        "pvt",
        "channel-scaling",
        "frontend-jitter",
        "reference-clock",
        "reference-stability",
        "packet-logging",
        "mswu-literature",
    }
    assert expected == set(SIMULATIONS)
