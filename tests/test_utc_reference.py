from tidl_poc.models.utc_reference import RefState, default_scenario, run_script, step


def test_loss_enters_holdover():
    state, q, bits = step(RefState.LOCKED, mhz_ok=True, pps_ok=False, qualify_count=3)
    assert state == RefState.HOLDOVER
    assert bits & (1 << 5)
    assert not (bits & (1 << 4))


def test_reacquire_returns_to_locked():
    df = run_script(default_scenario())
    states = df["state"].tolist()
    assert "LOCKED" in states
    assert "HOLDOVER" in states
    assert "REACQUIRE" in states
    # After the final restore block the last state should be LOCKED.
    assert df.iloc[-1]["state"] == "LOCKED"
    assert bool(df.iloc[-1]["utc_valid"])


def test_utc_valid_only_when_locked():
    df = run_script(default_scenario())
    assert (df.loc[df["utc_valid"], "state"] == "LOCKED").all()
