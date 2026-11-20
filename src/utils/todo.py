"""Penanda pekerjaan yang belum diimplementasikan.

Setiap stub memanggil ``todo("WP-xx")``. ID harus ada di docs/WORKPLAN.md
(dicek oleh tests/test_wiring.py), sehingga agent selalu tahu spesifikasi mana yang berlaku.
"""

from __future__ import annotations


class NotImplementedYet(NotImplementedError):
    """Dilempar oleh stub; pesan menunjuk ke paket kerja di WORKPLAN."""


def todo(wp_id: str) -> None:
    raise NotImplementedYet(
        f"{wp_id} belum diimplementasikan. Spesifikasi: docs/WORKPLAN.md ({wp_id}) "
        f"dan docs/METHODS.md."
    )
