"""D-027: lokasi kode / mentah / output terpisah; artefak dicari lintas lokasi (lokal, Kaggle, Colab)."""

import pandas as pd
import pytest

from kagami.utils.config import Config
from kagami.utils.env import init_runtime, kaggle_artifact_dirs, kaggle_raw_dir
from kagami.utils.io import ArtifactMissing, artifact_path, exists, read_artifact, require, write_artifact


def _ep():
    return pd.DataFrame({"episode_id": [1], "start_week": ["2020-03-02"], "end_week": ["2020-04-27"],
                         "cum_dlog_e": [0.12]})


def test_local_defaults(cfg):
    assert cfg.raw_dir == cfg.root / "data" / "raw" and cfg.out_dir == cfg.root
    assert cfg.read_dirs == (cfg.root,)


def test_write_to_out_read_from_previous_stage(cfg, tmp_path):
    prev, out = tmp_path / "nb00_output", tmp_path / "working"
    c_prev = Config(root=cfg.root, out_root=prev)
    write_artifact(c_prev, "episodes", _ep())
    c = Config(root=cfg.root, out_root=out, artifact_dirs=(prev,))
    assert exists(c, "episodes") and read_artifact(c, "episodes")["episode_id"].tolist() == [1]
    assert artifact_path(c, "episodes").is_relative_to(out)            # tulis tetap ke out_dir
    with pytest.raises(ArtifactMissing, match="profiles"):
        require(c, "episodes", "profiles")


def test_raw_dir_override(cfg, tmp_path):
    c = Config(root=cfg.root, raw_root=tmp_path)
    assert c.source_path("jisdor") == tmp_path / "bi_jisdor" / "jisdor_daily.xlsx"


def test_kaggle_discovery(tmp_path):
    (tmp_path / "kagami-raw" / "raw" / "bi_pihps").mkdir(parents=True)
    (tmp_path / "kagami-nb00" / "results").mkdir(parents=True)
    (tmp_path / "kagami-code" / "configs").mkdir(parents=True)
    assert kaggle_raw_dir(tmp_path) == tmp_path / "kagami-raw" / "raw"
    assert kaggle_artifact_dirs(tmp_path) == (tmp_path / "kagami-nb00",)


def test_colab_layout(cfg, tmp_path, monkeypatch):
    for v in ("KAGAMI_RAW_DIR", "KAGAMI_OUT_DIR"):
        monkeypatch.delenv(v, raising=False)
    c = init_runtime("colab", drive_dir=str(tmp_path), verbose=False)
    assert c.raw_dir == tmp_path / "data" / "raw" and c.out_dir == tmp_path
