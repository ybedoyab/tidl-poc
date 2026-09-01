from tidl_poc.common.rng import rng
from tidl_poc.models.packet_logging import crc32_concept, make_records, reconcile, udp_impair


def test_crc_stable():
    assert crc32_concept(b"abc") == crc32_concept(b"abc")
    assert crc32_concept(b"abc") != crc32_concept(b"abd")


def test_internal_log_prevents_measurement_loss():
    records = make_records(64)
    impaired = udp_impair(records, rng(0), drop_p=0.2, dup_p=0.1, reorder_frac=0.1)
    stats = reconcile(records, impaired)
    assert stats["udp_loss_unique"] > 0
    assert stats["measurement_loss_if_log_intact"] == 0
    assert stats["reconciled_unique"] == stats["n_truth"]
    assert stats["external_loss_implies_measurement_loss"] is False


def test_record_schema_fields():
    rec = make_records(1).iloc[0]
    for key in (
        "utc_epoch",
        "coarse_count",
        "channel",
        "fine_timestamp_ps",
        "sequence",
        "quality_bits",
        "calibration_version",
        "crc32",
    ):
        assert key in rec.index
