"""Halaman 7 -- Evaluasi & Riwayat Eksekusi (WP-36). Hanya membaca log JSON di `logs/` (D-010, D-137); tidak menjalankan
tahap atau menghitung ulang apa pun."""

import json

import pandas as pd
import streamlit as st

from common import CFG, STRETCH, page_header, picker
from kagami.tracking import registry, store
from kagami.viz import plots

page_header("Evaluasi & Riwayat Eksekusi",
            "Tahap mana yang sudah dijalankan, berhasil atau gagal, dari input mana, dan bagaimana ukuran mutunya?")

LABELS = {k: v.label for k, v in registry.TASKS.items()}
SHORT = {k: v.split(" · ")[0] for k, v in LABELS.items()}
SECTIONS = ["Ringkasan", "Evaluasi per tahap", "Perbandingan run", "Alur pipeline", "Riwayat"]
STATUS_LABEL = {"ok": "ok", "not_applicable": "tidak berlaku", "failed": "gagal"}


def fmt_value(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    if isinstance(v, bool):
        return "ya" if v else "tidak"
    if isinstance(v, float):
        return f"{v:.4g}"
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def metric_view(m: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"kelompok": m["group"], "metrik": m["name"], "nilai": m["value"].map(fmt_value),
                         "status": m["status"].map(STATUS_LABEL), "alasan": m["reason"].fillna(""),
                         "konteks data": m["context"]})


def ref_view(refs) -> pd.DataFrame:
    return pd.DataFrame([{"artefak": a.name, "path": a.path, "lokasi": a.location, "sha256": a.sha256[:12],
                          "baris": a.rows, "kolom": a.columns, "sel kosong": a.missing_cells, "memori (MB)": a.memory_mb,
                          "run produsen": a.producer_run_id or "–"} for a in refs])


runs = store.runs_table(CFG)
if runs.empty:
    st.info("Belum ada log eksekusi di `logs/`. Jalankan sebuah tahap (`python -m kagami task3`) atau evaluasi artefak "
            "yang sudah ada dengan `python -m kagami evaluate all`.")
    st.stop()
records = {r.run_id: r for r in store.load_runs(CFG)}
metrics = store.metrics_table(CFG)
tasks = [t for t in registry.ORDER if t in set(runs["task_id"])]

# Pemilih bagian (bukan st.tabs): hanya bagian aktif yang dirender, jadi grafik plotly tidak digambar di tab tersembunyi
# (lebar nol sampai jendela di-resize) dan pilihan tersimpan di URL (?bagian=...).
section = picker("Bagian", SECTIONS, key="bagian", radio=True)

# --------------------------------------------------------------------------- A. ringkasan
if section == "Ringkasan":
    exe = runs[runs["run_type"] == "execution"]
    last = runs.iloc[-1]
    c = st.columns(3)
    c[0].metric("Total run", len(runs), help="eksekusi + evaluasi-saja")
    c[1].metric("Berhasil", int((runs["status"] == "success").sum()))
    c[2].metric("Gagal", int((runs["status"] == "failed").sum()))
    c = st.columns(3)
    c[0].metric("Rerata waktu eksekusi", f"{exe['duration_s'].mean():.1f} dtk" if exe["duration_s"].notna().any()
                else "–", help="hanya run eksekusi; run evaluasi-saja tidak punya waktu eksekusi teramati")
    c[1].metric("Run eksekusi", len(exe), help="run evaluasi-saja tidak dihitung")
    c[2].metric("Run terakhir", "berhasil" if last["status"] == "success" else "gagal",
                help=f"{last['run_id']} · {last['started_at']}")
    latest = runs.groupby("task_id").tail(1).set_index("task_id").reindex(tasks).reset_index()
    st.subheader("Status terakhir per tahap")
    st.dataframe(pd.DataFrame({
        "tahap": latest["task_id"].map(LABELS), "run": latest["run_id"], "jenis": latest["run_type"],
        "status": latest["status"], "mulai (UTC)": latest["started_at"],
        "waktu eksekusi (dtk)": latest["duration_s"], "ringkasan evaluasi": latest["summary"]}),
        hide_index=True, **STRETCH)
    if runs["duration_s"].notna().any():
        st.plotly_chart(plots.run_durations(runs), **STRETCH)
    with st.expander("Keluarga metrik yang tidak berlaku untuk proyek ini"):
        st.dataframe(pd.DataFrame({"keluarga metrik": list(registry.NOT_APPLICABLE_FAMILIES),
                                   "alasan": list(registry.NOT_APPLICABLE_FAMILIES.values())}),
                     hide_index=True, **STRETCH)

# --------------------------------------------------------------------------- B. evaluasi per tahap
if section == "Evaluasi per tahap":
    c1, c2 = st.columns(2)
    task = c1.selectbox("Tahap", tasks, index=len(tasks) - 1 if "task4" not in tasks else tasks.index("task4"),
                        format_func=LABELS.get, key="eval_task")
    trun = runs[runs["task_id"] == task]
    rid = c2.selectbox("Run", list(trun["run_id"])[::-1], key=f"eval_run_{task}")
    rec = records[rid]
    st.caption(f"Jenis: {rec.kind} · algoritma: {'; '.join(rec.algorithms)} · dataset {rec.dataset_id} · "
               f"commit {(rec.git_commit or '–')[:8]} · platform {rec.platform}"
               + (f" · {rec.note}" if rec.note else ""))
    if rec.status == "failed":
        err = store.load_errors(CFG).get(rid, {})
        st.error(f"Run gagal: {err.get('error_type', rec.error_type)}: {err.get('message', '')}")
        with st.expander("Traceback"):
            st.code(err.get("traceback", "(tidak ada)"))
    m = metrics[metrics["run_id"] == rid]
    if m.empty:
        st.info("Run ini tidak punya log evaluasi (run gagal: evaluasi dilewati).")
    else:
        cnt = m["status"].value_counts()
        cc = st.columns(3)
        cc[0].metric("Metrik ok", int(cnt.get("ok", 0)))
        cc[1].metric("Tidak berlaku", int(cnt.get("not_applicable", 0)))
        cc[2].metric("Gagal dihitung", int(cnt.get("failed", 0)))
        groups = list(dict.fromkeys(m["group"]))
        pick = st.multiselect("Kelompok metrik", groups, default=groups, key="eval_groups")
        st.dataframe(metric_view(m[m["group"].isin(pick)]), hide_index=True, **STRETCH)
        st.caption("Metrik 'tidak berlaku' sengaja tidak dihitung (syaratnya tidak terpenuhi); alasannya di kolom alasan. "
                   "Konteks data = artefak sumber, subset, dan n.")
        numeric = sorted({n for n, v in zip(metrics.loc[metrics["task_id"] == task, "name"],
                                             metrics.loc[metrics["task_id"] == task, "value"])
                          if isinstance(v, (int, float)) and not isinstance(v, bool)})
        if numeric and len(trun) > 1:
            name = st.selectbox("Tren metrik antar run", numeric, key="eval_trend")
            st.plotly_chart(plots.metric_trend(metrics, runs, task, name), **STRETCH)
    with st.expander(f"Input ({len(rec.inputs)}) & output ({len(rec.outputs)}) run ini"):
        if rec.inputs:
            st.markdown("**Input** (sha256 saat dibaca; run produsen = run yang menulis file dengan hash sama)")
            st.dataframe(ref_view(rec.inputs), hide_index=True, **STRETCH)
        if rec.outputs:
            st.markdown("**Output**")
            st.dataframe(ref_view(rec.outputs), hide_index=True, **STRETCH)

# --------------------------------------------------------------------------- C. perbandingan
if section == "Perbandingan run":
    task_c = st.selectbox("Tahap", tasks, format_func=LABELS.get, key="cmp_task")
    ids = list(runs.loc[runs["task_id"] == task_c, "run_id"])
    chosen = st.multiselect("Run yang dibandingkan (pertama = acuan)", ids[::-1], default=ids[::-1][:2],
                            key=f"cmp_runs_{task_c}")      # kunci per tahap: pilihan run tidak terbawa antar tahap
    if len(chosen) < 2:
        st.info("Pilih minimal dua run dari tahap yang sama.")
    else:
        cmp = store.compare_runs(CFG, chosen)
        mt = cmp["metrics"]
        only = st.toggle("Hanya metrik yang berubah", value=True, key="cmp_only")
        if only and len(mt):
            vals = mt[chosen].map(fmt_value)
            mt = mt[vals.nunique(axis=1) > 1]
        show = mt.copy()
        for c in chosen:
            if c in show:
                show[c] = show[c].map(fmt_value)
        st.dataframe(show, hide_index=True, **STRETCH)
        st.caption("delta = nilai run − nilai run acuan (hanya metrik numerik).")
        st.markdown("**Perbedaan konfigurasi & lingkungan**")
        st.dataframe(cmp["params"].astype(str) if len(cmp["params"]) else pd.DataFrame({"catatan": ["tidak ada beda"]}),
                     hide_index=True, **STRETCH)
        st.markdown("**Artefak input/output (sha256)** — input berubah = perubahan di tahap hulu")
        st.dataframe(cmp["artifacts"], hide_index=True, **STRETCH)

# --------------------------------------------------------------------------- D. pipeline
if section == "Alur pipeline":
    edges = pd.DataFrame(registry.dependency_edges())
    latest_status = {t: r.status for t, r in store.latest_runs(CFG).items()}
    stale_df = store.staleness(CFG)
    stale = set(stale_df.loc[stale_df["stale"], "task_id"])
    st.plotly_chart(plots.pipeline_graph(edges, latest_status, stale, SHORT), **STRETCH)
    st.caption("Dependensi dibaca dari REQUIRES/OPTIONAL setiap pipeline (bukan diasumsikan linear). 'Basi' = artefak "
               "input berubah setelah run terakhir tahap itu.")
    e = edges.assign(produsen=edges["producer"].map(LABELS), konsumen=edges["consumer"].map(LABELS),
                     jenis=edges["required"].map({True: "wajib", False: "opsional"}))
    st.dataframe(e[["produsen", "artifact", "konsumen", "jenis"]].rename(columns={"artifact": "artefak"}),
                 hide_index=True, **STRETCH)
    if stale:
        st.warning("Input berubah setelah run terakhir: " + ", ".join(LABELS.get(t, t) for t in sorted(stale)))
        st.dataframe(stale_df[stale_df["stale"]], hide_index=True, **STRETCH)
    pipes = store.load_pipelines(CFG)
    if pipes:
        st.markdown("**Eksekusi pipeline penuh (`kagami all`)**")
        st.dataframe(pd.DataFrame([{"pipeline": k, "mulai": v.get("started_at"), "status": v.get("status"),
                                    "run": " → ".join(f"{r['task_id']}:{r['status']}" for r in v.get("runs", []))}
                                   for k, v in pipes.items()]), hide_index=True, **STRETCH)

# --------------------------------------------------------------------------- E. riwayat
if section == "Riwayat":
    c1, c2, c3 = st.columns(3)
    f_task = c1.multiselect("Tahap", tasks, default=tasks, format_func=LABELS.get, key="hist_task")
    f_status = c2.multiselect("Status", sorted(runs["status"].unique()), default=sorted(runs["status"].unique()),
                              key="hist_status")
    f_type = c3.multiselect("Jenis run", sorted(runs["run_type"].unique()), default=sorted(runs["run_type"].unique()),
                            key="hist_type")
    h = runs[runs["task_id"].isin(f_task) & runs["status"].isin(f_status) & runs["run_type"].isin(f_type)]
    st.dataframe(h.iloc[::-1][["run_id", "task_id", "started_at", "dataset_id", "algorithm", "status", "run_type",
                               "duration_s", "summary", "git_commit", "platform", "error_type"]].rename(columns={
        "task_id": "tahap", "started_at": "mulai (UTC)", "dataset_id": "dataset", "algorithm": "algoritma",
        "run_type": "jenis", "duration_s": "waktu eksekusi (dtk)", "summary": "ringkasan evaluasi"}),
        hide_index=True, **STRETCH)

st.caption("Sumber: log pelacakan `logs/runs`, `logs/evaluations`, `logs/errors`, `logs/pipelines` (WP-36) · waktu dalam "
           "UTC · metrik dihitung dari artefak hasil, bukan saat halaman dibuka.")
