"""Uji pemulihan struktur tertanam (WP-21) -- batas deteksi struktur regional. docs/METHODS.md §M2.5."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kagami.utils.todo import todo
from kagami.utils.config import Config



def recovery_curve(cfg: Config, placebo_X: list[np.ndarray]) -> pd.DataFrame:
    """WP-21. Untuk delta ∈ params.clustering.planted_deltas dan k_true ∈ {2,3}: jalankan pipeline penuh
    (select_k + ward) pada noise plasebo realistis + struktur tertanam, planted_reps kali.
    recovery_rate = P(k terpilih == k_true dan ARI >= 0.8); ari_mean. -> artefak 'planted_recovery'.
    """
    todo("WP-21")
