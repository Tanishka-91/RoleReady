"""Basic tests: python -m pytest  (or  python test_readiness.py)."""
import matching as M
import readiness as R


def test_evidence_weights_take_the_strongest_source():
    w = R.evidence_weights({"python", "sql"}, {"sql"}, {"python": 80})
    assert w["python"][0] == 1.0 and w["sql"][0] == 0.75


def test_failed_test_does_not_count():
    w = R.evidence_weights({"python"}, set(), {"python": 40})
    assert w["python"][0] == 0.5


def test_labels():
    assert R.label_for(0, 0) == "Ready"
    assert R.label_for(10, 10) == "Reachable"
    assert R.label_for(14, 10) == "Stretch"
    assert R.label_for(40, 10) == "Not feasible"


def test_more_evidence_means_fewer_hours():
    hours = {"sql": 20}
    a = R.evaluate(["sql"], {"sql": (0.5, "x")}, hours, 10, 14)
    b = R.evaluate(["sql"], {"sql": (1.0, "x")}, hours, 10, 14)
    assert a["hours_needed"] == 10 and b["hours_needed"] == 0 and b["label"] == "Ready"


def test_deadline_changes_label():
    far = R.evaluate(["java"], {}, {"java": 30}, 10, 28)
    near = R.evaluate(["java"], {}, {"java": 30}, 10, 3)
    assert far["label"] in ("Reachable", "Ready") and near["label"] == "Not feasible"


def test_alias_normalisation():
    assert M.norm_skill("DSA") == "data structures"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
    print("all tests passed")
