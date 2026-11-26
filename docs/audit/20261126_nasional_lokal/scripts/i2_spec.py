"""D-158 iterasi 2: varian HGB (PROTOKOL_I2 §2) untuk run_nl.py STAGE=i2 (tabel `fresh`)."""
KB_IW = ["kb_iw_up", "kb_iw_med", "kp_iw_up", "kp_iw_med"]


def variants(h, b):
    return {"base": {"cols": b}, "FR_REF": {"cols": b + ["iw_gap", "iw_gap_nat"]},
            "FR_CITY": {"cols": b + ["iw_gap", "iw_gap_nat"] + KB_IW}, "BR1": {"cols": b + ["kb_up_1"]}}
