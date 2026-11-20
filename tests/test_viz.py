"""Setiap fungsi viz menghasilkan figure dari artefak sintetis berkolom sesuai kontrak."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from kagami.viz import plots


def test_all_plots_build():
    h = np.arange(13)
    prof = pd.DataFrame({"commodity": "gula_pasir", "level": "national", "unit": "ALL", "driver": "e",
                         "horizon": h, "estimate": h * 0.01, "ci_low": h * 0.01 - 0.02, "ci_high": h * 0.01 + 0.02})
    weeks = pd.date_range("2020-01-06", periods=10, freq="W-MON")
    drv = pd.DataFrame({"week": weeks, "log_e": np.log(15000) + np.arange(10) * 0.001})
    eps = pd.DataFrame({"start_week": [weeks[2]], "end_week": [weeks[5]]})
    panel = pd.DataFrame({"commodity": ["a", "a", "b"], "status": ["observed", "missing", "carry_forward"]})
    co = pd.DataFrame({"province_i": [1, 1, 2, 2], "province_j": [1, 2, 1, 2], "share": [1, .3, .3, 1]})
    pr = pd.DataFrame({"delta": [.1, .2, .1, .2], "k_true": [2, 2, 3, 3], "recovery_rate": [.2, .9, .1, .7]})
    fe = pd.DataFrame({"subset": "all", "model": ["M1", "M2", "M3"], "commodity": "gula_pasir", "horizon": 8,
                       "mae_ratio_vs_m1": [1, .95, 1.02]})
    rob = pd.DataFrame({"check_id": ["a", "b"], "commodity": "x", "horizon": 8, "estimate": [.1, .2],
                        "ci_low": [0, .1], "ci_high": [.2, .3]})
    figs = [plots.response_curve(prof, "gula_pasir", "national", "ALL", "e"), plots.fx_drivers(drv, eps),
            plots.status_share(panel), plots.coassign_heatmap(co), plots.recovery_curve(pr),
            plots.forecast_ratios(fe), plots.forest(rob, ["check_id", "horizon"], "uji")]
    assert all(isinstance(f, go.Figure) for f in figs)
