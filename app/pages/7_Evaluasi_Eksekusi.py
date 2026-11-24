"""Halaman 7 -- Evaluasi & Riwayat Eksekusi (WP-36). Hanya membaca log JSON di `logs/` (D-010, D-137); tidak menjalankan
tahap atau menghitung ulang estimasi. D-140: status hitung dipisah dari penilaian terhadap acuan, eksekusi dipisah dari
evaluasi-saja, lineage output (artefak sinkron/tidak), metrik arah dengan interval bootstrap blok origin & per segmen."""

import json

import pandas as pd
import streamlit as st

from common import CFG, STRETCH, commodity_labels, page_header, picker
from kagami.tracking import assessment, registry, store
from kagami.viz import plots
from kagami.viz.style import fmt_num

page_header("Evaluasi & Riwayat Eksekusi",
            "Tahap mana yang benar-benar dieksekusi, dari input mana, apakah artefaknya sinkron, dan apakah hasil "
            "evaluasinya lebih baik dari acuan?")

LABELS = {k: v.label for k, v in registry.TASKS.items()}
SHORT = {k: v.split(" · ")[0] for k, v in LABELS.items()}
SECTIONS = ["Ringkasan", "Evaluasi per tahap", "Perbandingan run", "Alur pipeline", "Riwayat"]
STATUS_LABEL = {"ok": "berhasil dihitung", "not_applicable": "tidak berlaku", "failed": "gagal dihitung"}
RUN_STATUS = {"success": "berhasil", "failed": "gagal"}
RUN_TYPE = {"execution": "eksekusi", "evaluation": "evaluasi-saja"}
ASSESS = assessment.LABELS
ASSESS_ORDER = ["worse", "review", "inconclusive", "better", "expected", "info", "not_computed"]
TABLE_METRICS = ("_by_segment", "carry_forward_by_commodity", "_selective", "_seed_replication", "_block_sensitivity")   # nilai berupa tabel → ditampilkan terpisah


def fmt_value(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    if isinstance(v, bool):
        return "ya" if v else "tidak"
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    if isinstance(v, float):
        if v.is_integer() and abs(v) < 1e15:
            return f"{int(v):,}".replace(",", ".")
        return f"{v:,.0f}".replace(",", ".") if abs(v) >= 1000 else f"{v:.4g}".replace(".", ",")
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def fmt_time(iso) -> str:
    if not iso or (isinstance(iso, float) and pd.isna(iso)):
        return "–"
    return pd.to_datetime(iso, format="ISO8601", utc=True).strftime("%Y-%m-%d %H:%M UTC")


def fmt_dur(v) -> str:
    return "–" if v is None or pd.isna(v) else fmt_num(float(v), 1) + " dtk"


def fmt_ci(lo, hi) -> str:
    return "–" if lo is None or hi is None or pd.isna(lo) or pd.isna(hi) else f"{fmt_num(lo, 3)} s.d. {fmt_num(hi, 3)}"


def metric_view(m: pd.DataFrame) -> pd.DataFrame:
    ref = [("–" if pd.isna(v) else fmt_value(v)) + (f" ({lab})" if isinstance(lab, str) and lab else "")
           for v, lab in zip(m["reference"], m["reference_label"])]
    return pd.DataFrame({"kelompok": m["group"], "metrik": m["name"], "nilai": m["value"].map(fmt_value),
                         "acuan": ref, "interval 95%": [fmt_ci(a, b) for a, b in zip(m["ci_low"], m["ci_high"])],
                         "q (BH)": m["q_value"].map(lambda v: "–" if pd.isna(v) else fmt_num(v, 3)),
                         "penilaian": m["assessment"].map(ASSESS), "interpretasi": m["interpretation"].fillna(""),
                         "status hitung": m["status"].map(STATUS_LABEL), "konteks data": m["context"]})


def ref_view(refs, sync: pd.DataFrame | None = None) -> pd.DataFrame:
    st_map = dict(zip(sync["artifact"], sync["state"])) if sync is not None and len(sync) else {}
    cur = dict(zip(sync["artifact"], sync["current_sha"])) if sync is not None and len(sync) else {}
    return pd.DataFrame([{"artefak": a.name, "path": a.path, "lokasi": a.location, "sha256": a.sha256[:12],
                          "= file sekarang": ("ya" if cur.get(a.name) == a.sha256[:12] else "tidak")
                          if a.name in cur else "–",
                          "status artefak": st_map.get(a.name, "–"), "baris": a.rows, "kolom": a.columns,
                          "sel kosong": a.missing_cells, "memori (MB)": a.memory_mb,
                          "run produsen": a.producer_run_id or "–"} for a in refs])


def assess_counts(m: pd.DataFrame) -> str:
    c = m["assessment"].value_counts()
    parts = [f"{int(c[k])} {ASSESS[k]}" for k in ("worse", "review", "inconclusive", "better", "expected") if k in c]
    return " · ".join(parts) or "–"


MODEL_ORDER = ["M0", "M1", "M2", "M3", "C1", "C2", "PTST", "TSMX", "TSMX_fx", "TFM", "TFM_fx"]
MODEL_NAMES = {"M0": "M0 tanpa perubahan", "M1": "M1 ridge dasar", "M2": "M2 ridge + kurs", "M3": "M3 gradient boosting",
               "C1": "C1 klasifier tanpa kurs", "C2": "C2 klasifier + kurs", "PTST": "PatchTST", "TSMX": "TSMixer",
               "TSMX_fx": "TSMixer + kurs", "TFM": "TimesFM 3.0", "TFM_fx": "TimesFM 3.0 + kurs"}


def benchmark_table(m: pd.DataFrame, h: str) -> pd.DataFrame:
    """Satu baris per model untuk horizon h: rasio MAE vs M1 (q BH), akurasi arah vs baseline, metrik klasifikasi lengkap."""
    v = m[m["status"] == "ok"].set_index("name")
    rows = []
    for mo in MODEL_ORDER:
        def g(k, d=3, mo=mo):
            n = f"{h}_{mo}_dir_{k}"
            return fmt_num(float(v.loc[n, "value"]), d) if n in v.index else "–"
        ratio = v.loc[f"mae_ratio_vs_m1_{h}_{mo}"] if f"mae_ratio_vs_m1_{h}_{mo}" in v.index else None
        acc = v.loc[f"{h}_{mo}_dir_accuracy"] if f"{h}_{mo}_dir_accuracy" in v.index else None
        if ratio is None and acc is None:
            continue
        actx = json.loads(acc["context"]) if acc is not None else {}
        rows.append({
            "model": MODEL_NAMES.get(mo, mo),
            "MAE / M1": fmt_num(float(ratio["value"]), 3) if ratio is not None else "–",
            "penilaian MAE": ASSESS.get(ratio["assessment"], "–") if ratio is not None else "–",
            "akurasi arah": g("accuracy"), "selisih vs baseline": fmt_ci(actx.get("gap_ci_low"), actx.get("gap_ci_high")),
            "penilaian arah": ASSESS.get(acc["assessment"], "–") if acc is not None else "–",
            "F1 makro": g("f1_macro"), "F1 berbobot": g("f1_weighted"), "F1 naik": g("f1_naik"), "F1 turun": g("f1_turun"),
            "precision naik": g("precision_naik"), "precision turun": g("precision_turun"),
            "recall naik": g("recall_naik"), "recall turun": g("recall_turun"), "balanced acc.": g("balanced_accuracy"),
            "MCC": g("mcc"), "ROC-AUC": g("roc_auc"), "PR-AUC": g("pr_auc"),
            "akurasi termasuk perubahan nol": g("accuracy_incl_no_change"), "cakupan": g("coverage")})
    return pd.DataFrame(rows)


runs = store.runs_table(CFG)
if runs.empty:
    st.info("Belum ada log eksekusi di `logs/`. Jalankan sebuah tahap (`python -m kagami task3`) atau evaluasi artefak "
            "yang sudah ada dengan `python -m kagami evaluate all`.")
    st.stop()
records = {r.run_id: r for r in store.load_runs(CFG)}
metrics = assessment.assess_table(store.metrics_table(CFG))
tasks = [t for t in registry.ORDER if t in set(runs["task_id"])]
sync = store.artifact_sync(CFG)
states = store.stage_states(CFG, sync)
# run terakhir yang punya log evaluasi, per tahap (sumber penilaian terkini)
latest_eval = {t: d["run_id"].iloc[-1] for t, d in runs[runs["metrics_ok"] + runs["metrics_na"] > 0].groupby("task_id")}

# Pemilih bagian (bukan st.tabs): hanya bagian aktif yang dirender, jadi grafik plotly tidak digambar di tab tersembunyi
# (lebar nol sampai jendela di-resize) dan pilihan tersimpan di URL (?bagian=...).
section = picker("Bagian", SECTIONS, key="bagian", radio=True)

# --------------------------------------------------------------------------- A. ringkasan
if section == "Ringkasan":
    exe = runs[runs["run_type"] == "execution"]
    ev = runs[runs["run_type"] == "evaluation"]
    never = [t for t in tasks if states.get(t) in ("hanya dievaluasi", "belum ada run")]
    unsynced = sync[sync["state"] == "tidak sinkron"]
    cur = metrics[metrics["run_id"].isin(latest_eval.values())]
    flagged = cur[cur["assessment"].isin(["worse", "review"])]
    c = st.columns(3)
    c[0].metric("Eksekusi berhasil", f"{int((exe['status'] == 'success').sum())}/{len(exe)}",
                help="run yang benar-benar menjalankan pipeline tahap")
    c[1].metric("Evaluasi-saja", len(ev), help="membaca artefak yang sudah ada tanpa menjalankan ulang tahap")
    c[2].metric("Run gagal", int((runs["status"] == "failed").sum()))
    c = st.columns(3)
    c[0].metric("Tahap belum dieksekusi", len(never),
                help=", ".join(LABELS[t] for t in never) if never else "semua tahap punya run eksekusi")
    c[1].metric("Artefak tidak sinkron", len(unsynced),
                help="file artefak sekarang berbeda dari output run eksekusi terakhir yang menulisnya")
    c[2].metric("Metrik perlu perhatian", len(flagged),
                help="penilaian 'lebih buruk dari acuan' atau 'perlu ditinjau' pada evaluasi terbaru tiap tahap")

    st.subheader("Status per tahap")
    rows = []
    for t in tasks:
        tr = runs[runs["task_id"] == t]
        lx, le = tr[tr["run_type"] == "execution"], tr[tr["run_type"] == "evaluation"]
        rid = latest_eval.get(t)
        rows.append({"tahap": LABELS[t], "status tahap": states.get(t, "–"),
                     "eksekusi terakhir": fmt_time(lx["started_at"].iloc[-1]) if len(lx) else "belum ada",
                     "waktu eksekusi": fmt_dur(lx["duration_s"].iloc[-1]) if len(lx) else "–",
                     "evaluasi terakhir": fmt_time(le["started_at"].iloc[-1]) if len(le) else "–",
                     "penilaian metrik (evaluasi terbaru)": assess_counts(metrics[metrics["run_id"] == rid])
                     if rid else "–"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, **STRETCH)
    st.caption("Status tahap: **dieksekusi** = run eksekusi terakhir sukses dan semua artefaknya sama dengan file sekarang; "
               "**output tidak sinkron** = file sekarang bukan hasil run eksekusi terakhir; **hanya dievaluasi** = belum "
               "ada run eksekusi tercatat, hanya evaluasi artefak lama.")

    st.subheader("Temuan evaluasi yang perlu diperhatikan")
    if flagged.empty:
        st.success("Tidak ada metrik yang lebih buruk dari acuan atau perlu ditinjau.")
    else:
        st.dataframe(pd.DataFrame({"tahap": flagged["task_id"].map(LABELS), "metrik": flagged["name"],
                                   "nilai": flagged["value"].map(fmt_value),
                                   "penilaian": flagged["assessment"].map(ASSESS),
                                   "interpretasi": flagged["interpretation"]}), hide_index=True, **STRETCH)
    if len(unsynced):
        st.warning("Artefak tidak sinkron dengan run eksekusi terakhir: " + ", ".join(
            f"`{a}` (sekarang {fmt_value(r1)} baris, run eksekusi {fmt_value(r2)} baris)"
            for a, r1, r2 in zip(unsynced["artifact"], unsynced["current_rows"], unsynced["last_execution_rows"]))
            + ". Lihat bagian Alur pipeline.")
    if exe["duration_s"].notna().any():
        st.plotly_chart(plots.run_durations(runs, {k: v.replace(" · ", " – ") for k, v in LABELS.items()}), **STRETCH)
    with st.expander("Keluarga metrik yang tidak berlaku untuk proyek ini"):
        st.dataframe(pd.DataFrame({"keluarga metrik": list(registry.NOT_APPLICABLE_FAMILIES),
                                   "alasan": list(registry.NOT_APPLICABLE_FAMILIES.values())}),
                     hide_index=True, **STRETCH)

# --------------------------------------------------------------------------- B. evaluasi per tahap
if section == "Evaluasi per tahap":
    want = st.query_params.get("run")
    want_task = records[want].task_id if want in records else None
    c1, c2 = st.columns(2)
    default_task = want_task or ("task4" if "task4" in tasks else tasks[-1])
    task = c1.selectbox("Tahap", tasks, index=tasks.index(default_task), format_func=LABELS.get, key="eval_task")
    trun = runs[runs["task_id"] == task]
    ids = list(trun["run_id"])[::-1]
    rid = c2.selectbox("Run", ids, index=ids.index(want) if want in ids else 0, key=f"eval_run_{task}",
                       format_func=lambda r: f"{r} ({RUN_TYPE.get(records[r].run_type, records[r].run_type)})")
    rec = records[rid]
    dirty = {True: "ada perubahan belum di-commit", False: "bersih", None: "tidak diketahui"}[rec.git_dirty]
    st.caption(f"Jenis run: {RUN_TYPE.get(rec.run_type, rec.run_type)} · {rec.kind} · algoritma: "
               f"{'; '.join(rec.algorithms)} · dataset {rec.dataset_id} · commit {(rec.git_commit or '–')[:8]} "
               f"(working tree {dirty}) · code hash {(rec.code_sha256 or '–')[:12]} · platform {rec.platform}"
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
        cnt, ac = m["status"].value_counts(), m["assessment"].value_counts()
        cc = st.columns(3)
        cc[0].metric("Berhasil dihitung", int(cnt.get("ok", 0)))
        cc[1].metric("Tidak berlaku", int(cnt.get("not_applicable", 0)))
        cc[2].metric("Gagal dihitung", int(cnt.get("failed", 0)))
        cc = st.columns(4)
        cc[0].metric("Lebih baik dari acuan", int(ac.get("better", 0)))
        cc[1].metric("Belum terbukti berbeda", int(ac.get("inconclusive", 0)))
        cc[2].metric("Lebih buruk dari acuan", int(ac.get("worse", 0)))
        cc[3].metric("Perlu ditinjau", int(ac.get("review", 0)))
        st.caption("Dua lapis: **status hitung** hanya menyatakan metrik berhasil dihitung; **penilaian** membandingkan "
                   "nilai dengan acuan eksplisit (peluang, baseline kelas mayoritas, α, rasio 1 terhadap M1, p95 plasebo). "
                   "'Lebih baik/buruk' hanya bila interval atau uji mendukung; selain itu 'belum terbukti berbeda'. "
                   "Perbandingan eksploratif (beda berpasangan, metrik arah vs acuan, rasio MAE model eksploratif) dikoreksi "
                   "Benjamini–Hochberg per keluarga (q < 0,05, D-143); uji resmi praregistrasi tidak dikoreksi di sini.")
        hs = sorted({n.split("_")[0] for n in m["name"] if n.startswith("h") and n.split("_")[0][1:].isdigit()})
        if task == "task4" and hs:
            st.subheader("Perbandingan model (Task 4)")
            hb = st.radio("Horizon", hs, index=len(hs) - 1, horizontal=True, key="bench_h",
                          format_func=lambda x: x.replace("h", "h = ") + " minggu")
            st.dataframe(benchmark_table(m, hb), hide_index=True, **STRETCH)
            st.caption("MAE / M1 < 1 = lebih akurat dari ridge dasar (DM HAC; model eksploratif dikoreksi BH). Metrik "
                       "klasifikasi = arah naik/turun pada baris dengan perubahan harga ≠ 0 (cakupan = porsi baris yang "
                       "dievaluasi); 'akurasi termasuk perubahan nol' menghitung minggu tanpa perubahan sebagai salah. "
                       "M2 vs M1 adalah uji resmi; C, PTST, TSMX, TFM eksploratif (D-141, D-142). Evaluasi bersyarat "
                       "pseudo-real-time, bukan ramalan.")
        adv = st.toggle("Tampilkan diagnostik lanjutan", value=task != "task4", key=f"adv_{task}")
        scal = m[~m["name"].str.endswith(TABLE_METRICS)]
        groups = list(dict.fromkeys(scal["group"]))
        f1, f2 = st.columns(2)
        pick = f1.multiselect("Kelompok metrik", groups, default=groups, key="eval_groups")
        present = [a for a in ASSESS_ORDER if a in set(scal["assessment"])]
        judged = [a for a in present if a not in ("info", "not_computed")]
        pick_a = f2.multiselect("Penilaian", present, default=judged or present, format_func=ASSESS.get,
                                key=f"eval_assess_{task}")
        st.dataframe(metric_view(scal[scal["group"].isin(pick) & scal["assessment"].isin(pick_a)]),
                     hide_index=True, **STRETCH)
        st.caption(f"{int(scal['group'].isin(pick).sum())} metrik pada kelompok terpilih; default hanya metrik yang punya "
                   "penilaian terhadap acuan (tambahkan 'informasi' untuk melihat semuanya).")

        dm = m[m["name"].str.contains("_dir_") & ~m["name"].str.endswith(TABLE_METRICS)].copy()
        if adv and len(dm[dm["status"] == "ok"]):
            st.subheader("Arah perubahan harga (diagnostik klasifikasi)")
            st.caption("Ramalan regresi Task 4 diubah menjadi arah (naik/turun) dan dibandingkan dengan arah aktual. "
                       "Diagnostik tambahan, bukan uji praregistrasi (D-139). Interval 95% dari bootstrap blok origin "
                       "(unit = origin, karena seri dalam satu origin berbagi guncangan nasional dan origin bertumpuk; "
                       "D-140). Acuan akurasi = selalu menebak arah terbanyak.")
            dm["key"] = dm["name"].str.extract(r"^(h\d+_.+?)_dir_")[0]
            dm["metric"] = dm["name"].str.extract(r"_dir_(.+)$")[0]
            ok_ = dm[dm["status"] == "ok"]
            rows = []
            for key, d in ok_.groupby("key", sort=True):
                g = d.set_index("metric")

                def cell(k: str, g=g) -> str:
                    if k not in g.index:
                        return "–"
                    r = g.loc[k]
                    ci = fmt_ci(r["ci_low"], r["ci_high"])
                    return fmt_num(float(r["value"]), 3) + ("" if ci == "–" else f" ({ci})")

                acc = g.loc["accuracy"] if "accuracy" in g.index else None
                ctx = json.loads(acc["context"]) if acc is not None else {}
                rows.append({"horizon · model": key, "akurasi": cell("accuracy"),
                             "baseline mayoritas": fmt_num(float(g.loc["majority_baseline_accuracy", "value"]), 3)
                             if "majority_baseline_accuracy" in g.index else "–",
                             "selisih vs baseline (interval)": fmt_ci(ctx.get("gap_ci_low"), ctx.get("gap_ci_high")),
                             "penilaian akurasi": ASSESS.get(acc["assessment"], "–") if acc is not None else "–",
                             "balanced acc.": cell("balanced_accuracy"), "F1 makro": cell("f1_macro"),
                             "recall turun": cell("recall_turun"), "MCC": cell("mcc"), "ROC-AUC": cell("roc_auc")})
            st.dataframe(pd.DataFrame(rows), hide_index=True, **STRETCH)
            na_keys = sorted(set(dm.loc[dm["status"] == "not_applicable", "key"].dropna()) - set(ok_["key"]))
            if na_keys:
                st.caption("Tidak berlaku: " + ", ".join(
                    f"{k} ({dm.loc[dm['key'] == k, 'reason'].iloc[0]})" for k in na_keys))
            conf = m[m["name"].str.endswith("_dir_confusion") & (m["status"] == "ok")]
            keys = list(conf["name"].str.replace("_dir_confusion", "", regex=False))
            ck = st.selectbox("Confusion matrix", keys, index=len(keys) - 1, key=f"eval_conf_{task}")
            row = conf[conf["name"] == f"{ck}_dir_confusion"].iloc[0]
            ctx = json.loads(row["context"])
            st.plotly_chart(plots.confusion_matrix(
                row["value"], ctx.get("labels", ["naik", "turun"]), f"Arah perubahan · {ck}",
                f"n = {fmt_num(ctx.get('n'), 0)} · {fmt_num(ctx.get('n_no_change_excluded'), 0)} perubahan nol dikeluarkan · "
                f"porsi naik {fmt_num(100 * ctx.get('share_naik', float('nan')), 1)}% · evaluasi bersyarat "
                "pseudo-real-time"), **STRETCH)

        dpm = m[m["group"].str.startswith("model deep") & (m["status"] == "ok")]
        if adv and len(dpm):
            st.subheader("Model deep learning & foundation (eksploratif, D-142)")
            st.caption("Bukan uji praregistrasi. PTST = PatchTST, TSMX = TSMixer (harga saja), TSMX_fx = TSMixer + kurs & "
                       "harga dunia; ketiganya dilatih ulang tiap 16 minggu dari data s.d. origin. TFM = TimesFM 3.0 zero-shot "
                       "(google/timesfm-3.0-pytorch, lisensi non-komersial), TFM_fx = + kovariat masa lalu kurs & harga dunia. "
                       "Origin & baris uji sama dengan M0–M3; uji resmi H5 tetap M2 vs M1.")
            rows = []
            for name in sorted(dpm.loc[dpm["name"].str.startswith("mae_ratio_vs_m1_h"), "name"]):
                h, mo = name.replace("mae_ratio_vs_m1_", "").split("_", 1)
                r = dpm[dpm["name"] == name].iloc[0]
                acc = dpm[dpm["name"] == f"{h}_{mo}_dir_accuracy"]
                ax = json.loads(acc["context"].iloc[0]) if len(acc) else {}
                mae = dpm[dpm["name"] == f"{h}_{mo}_mae"]
                rows.append({"model": mo, "horizon": h, "MAE": fmt_num(mae["value"].iloc[0], 4) if len(mae) else "–",
                             "MAE / M1": fmt_num(r["value"], 3), "DM p": fmt_num(json.loads(r["context"]).get("dm_p"), 3),
                             "penilaian MAE": ASSESS.get(r["assessment"], "–"),
                             "akurasi arah": fmt_num(acc["value"].iloc[0], 3) if len(acc) else "–",
                             "selisih vs baseline (interval)": fmt_ci(ax.get("gap_ci_low"), ax.get("gap_ci_high")),
                             "penilaian arah": ASSESS.get(acc["assessment"].iloc[0], "–") if len(acc) else "–"})
            if rows:
                st.dataframe(pd.DataFrame(rows), hide_index=True, **STRETCH)
        cls = m[m["name"].str.endswith("_accuracy_diff") & (m["status"] == "ok")]
        sel = m[m["name"].str.endswith("_selective") & (m["status"] == "ok")]
        if adv and (len(cls) or len(sel)):
            st.subheader("Perbandingan berpasangan & klasifier arah (eksploratif)")
            st.caption("Bukan uji praregistrasi. C1 = HistGradientBoostingClassifier dengan fitur dasar + identitas seri "
                       "(tanpa kurs); C2 = C1 + fitur kurs & harga dunia (= fitur M3), dilatih langsung untuk arah naik/turun "
                       "(D-141). Setiap baris = selisih akurasi arah A − B pada baris uji yang sama, interval bootstrap blok "
                       "origin berpasangan. Uji resmi H5 tetap MAE & DM.")
        if adv and len(cls):
            st.dataframe(pd.DataFrame({
                "perbandingan": cls["name"].str.replace("_accuracy_diff", "", regex=False),
                "arti": [json.loads(c).get("comparison", "") for c in cls["context"]],
                "akurasi A": [fmt_num(json.loads(c).get("acc_a"), 3) for c in cls["context"]],
                "akurasi B": [fmt_num(json.loads(c).get("acc_b"), 3) for c in cls["context"]],
                "selisih A − B": cls["value"].map(lambda v: fmt_num(v, 3, sign=True)),
                "interval 95%": [fmt_ci(a, b) for a, b in zip(cls["ci_low"], cls["ci_high"])],
                "q (BH)": cls["q_value"].map(lambda v: "–" if pd.isna(v) else fmt_num(v, 3)),
                "penilaian": cls["assessment"].map(ASSESS)}), hide_index=True, **STRETCH)
        if adv and len(sel):
            names = list(sel["name"])
            sname = st.selectbox("Prediksi selektif", names, index=len(names) - 1, key=f"sel_{task}",
                                 format_func=lambda n: n.replace("_selective", ""))
            stab = pd.DataFrame(sel.loc[sel["name"] == sname, "value"].iloc[0])
            if len(stab):
                st.dataframe(pd.DataFrame({
                    "cakupan target": stab["target_coverage"].map(lambda v: f"{fmt_num(100 * v, 0)}%"),
                    "cakupan nyata": stab["coverage"].map(lambda v: f"{fmt_num(100 * v, 1)}%"),
                    "n": stab["n"].map(lambda v: fmt_value(int(v))), "akurasi": stab["accuracy"].map(lambda v: fmt_num(v, 3)),
                    "baseline mayoritas (baris terpilih)": stab["majority_baseline_accuracy"].map(lambda v: fmt_num(v, 3)),
                    "selisih": stab["accuracy_gap"].map(lambda v: fmt_num(v, 3, sign=True)),
                    "F1 makro": stab["f1_macro"].map(lambda v: fmt_num(v, 3))}), hide_index=True, **STRETCH)
                st.caption("Per origin hanya baris dengan keyakinan |p − 0,5| terbesar yang diramalkan. Akurasi pada cakupan "
                           "kecil tidak berlaku untuk semua kasus: baca bersama cakupan dan baseline pada baris terpilih.")

        seg = m[m["name"].str.endswith("_dir_by_segment") & (m["status"] == "ok")]
        seg = seg[seg["value"].map(lambda v: isinstance(v, list) and len(v) > 0)]   # < 3 origin → tabel kosong
        if adv and len(seg):
            st.subheader("Arah & galat per segmen")
            st.caption("Agregat semua komoditas bisa menutupi kegagalan per komoditas. Baseline = arah terbanyak di "
                       "segmen itu; interval selisih dari bootstrap blok origin. Segmen 'kaku' = porsi sel carry_forward "
                       "≥ 50% (kekakuan harga, U22). MAE / M1 > 1 = lebih buruk dari ridge dasar.")
            hs = list(seg["name"])
            s1, s2, s3 = st.columns(3)
            hname = s1.selectbox("Horizon", hs, index=len(hs) - 1, key=f"seg_h_{task}",
                                 format_func=lambda n: n.split("_")[0].replace("h", "h = "))
            tab = pd.DataFrame(seg.loc[seg["name"] == hname, "value"].iloc[0])
            types = list(dict.fromkeys(tab["segment_type"]))
            stype = s2.selectbox("Jenis segmen", types, index=types.index("komoditas") if "komoditas" in types else 0,
                                 key=f"seg_type_{task}")
            models = list(dict.fromkeys(tab["model"]))
            smodel = s3.selectbox("Model", models, index=models.index("M2") if "M2" in models else 0,
                                  key=f"seg_model_{task}")
            t = tab[(tab["segment_type"] == stype) & (tab["model"] == smodel)].copy()
            lab = commodity_labels()
            t["segmen"] = t["segment"].map(lambda s: lab.get(s, s))
            st.dataframe(pd.DataFrame({
                "segmen": t["segmen"], "n": t["n"].map(lambda v: fmt_value(int(v)) if pd.notna(v) else "–"),
                "akurasi": t["accuracy"].map(lambda v: fmt_num(v, 3)),
                "baseline": t["majority_baseline_accuracy"].map(lambda v: fmt_num(v, 3)),
                "selisih (interval)": [f"{fmt_num(g, 3, sign=True)} ({fmt_ci(a, b)})" for g, a, b in
                                       zip(t["accuracy_gap"], t["gap_ci_low"], t["gap_ci_high"])],
                "q (BH)": t["gap_q"].map(lambda v: fmt_num(v, 3)) if "gap_q" in t else "–",
                "penilaian": t["assessment"].map(ASSESS), "balanced acc.": t["balanced_accuracy"].map(lambda v: fmt_num(v, 3)),
                "recall turun": t["recall_turun"].map(lambda v: fmt_num(v, 3)), "MCC": t["mcc"].map(lambda v: fmt_num(v, 3)),
                "MAE": t["mae"].map(lambda v: fmt_num(v, 4)),
                "MAE / M1": t["mae_ratio_vs_m1"].map(lambda v: fmt_num(v, 3))}), hide_index=True, **STRETCH)
            fd = t.dropna(subset=["gap_ci_low", "gap_ci_high"]).rename(columns={"accuracy_gap": "estimate",
                                                                               "gap_ci_low": "ci_low",
                                                                               "gap_ci_high": "ci_high"})
            if len(fd):
                st.plotly_chart(plots.forest(fd, ["segmen"], f"Akurasi arah − baseline mayoritas · {smodel} · {stype}",
                                             "selisih akurasi", "Titik penuh = interval 95% (bootstrap blok origin) tidak "
                                             "memuat nol; kiri nol = lebih buruk dari selalu menebak arah terbanyak"),
                                **STRETCH)

        srep = m[m["name"].str.endswith("_seed_replication") & (m["status"] == "ok")]
        if adv and len(srep):
            st.subheader("Replikasi seed model deep (D-144)")
            st.caption("PatchTST & TSMixer dilatih ulang dengan seed berbeda pada origin, jendela, dan jadwal refit yang sama. "
                       "Rentang antar seed = ketidakpastian pelatihan; selisih antarmodel yang lebih kecil dari rentang ini "
                       "tidak bermakna.")
            for name, val in zip(srep["name"], srep["value"]):
                sd = pd.DataFrame(val)
                st.markdown(f"**{name.split('_')[0].replace('h', 'h = ')}**")
                st.dataframe(pd.DataFrame({
                    "model": sd["model"].map(lambda x: MODEL_NAMES.get(x, x)), "seed": sd["n_seeds"],
                    **{lab: [f"{fmt_num(a, 3)} ± {fmt_num(b, 3)} ({fmt_num(c, 3)}..{fmt_num(d, 3)})"
                             for a, b, c, d in zip(sd[f"{k}_mean"], sd[f"{k}_sd"], sd[f"{k}_min"], sd[f"{k}_max"])]
                       for k, lab in (("mae_ratio_vs_m1", "MAE / M1"), ("accuracy", "akurasi arah"),
                                      ("f1_macro", "F1 makro"), ("f1_weighted", "F1 berbobot"), ("mcc", "MCC"))}}),
                    hide_index=True, **STRETCH)
            st.caption("Format: rerata ± simpangan baku (min..maks) antar seed.")

        bsen = m[m["name"].str.endswith("_block_sensitivity") & (m["status"] == "ok")]
        if adv and len(bsen):
            st.subheader("Kepekaan panjang blok bootstrap & lag DM (D-144)")
            bn = st.selectbox("Horizon", list(bsen["name"]), index=len(bsen) - 1, key=f"blk_{task}",
                              format_func=lambda n: n.split("_")[0].replace("h", "h = "))
            bt = pd.DataFrame(bsen.loc[bsen["name"] == bn, "value"].iloc[0])
            ci = bt[bt["ci_low"].notna()].copy()
            if len(ci):
                ci["sel"] = [f"{fmt_ci(a, b)} · p {fmt_num(p, 3)}" for a, b, p in zip(ci["ci_low"], ci["ci_high"], ci["p"])]
                st.dataframe(ci.pivot_table(index="comparison", columns="block", values="sel", aggfunc="first")
                             .rename_axis(columns="blok (origin)").reset_index(), hide_index=True, **STRETCH)
            dmt = bt[bt["ci_low"].isna()].copy()
            if len(dmt):
                dmt["sel"] = [f"{fmt_num(r, 3)} · p {fmt_num(p, 3)}" for r, p in zip(dmt["ratio"], dmt["p"])]
                st.dataframe(dmt.pivot_table(index="comparison", columns="block", values="sel", aggfunc="first")
                             .reset_index(), hide_index=True, **STRETCH)
            stab = m[m["name"] == bn.replace("_block_sensitivity", "_block_decisions_stable_share")]
            if len(stab):
                st.caption(f"Keputusan (interval di atas / memuat / di bawah nol) sama di semua panjang blok untuk "
                           f"{fmt_num(100 * float(stab['value'].iloc[0]), 0)}% perbandingan.")

        cf = m[m["name"] == "carry_forward_by_commodity"]
        if len(cf) and cf["status"].iloc[0] == "ok":
            st.subheader("Kekakuan harga per komoditas")
            cft = pd.DataFrame(cf["value"].iloc[0])
            cft["commodity"] = cft["commodity"].map(lambda s: commodity_labels().get(s, s))
            st.dataframe(cft.rename(columns={"commodity": "komoditas", "carry_forward_share": "porsi carry_forward",
                                             "observed_share": "porsi teramati",
                                             "max_carry_forward_streak_weeks": "rangkaian carry_forward terpanjang (minggu)",
                                             "median_series_max_streak_weeks": "median rangkaian terpanjang per seri"}),
                         hide_index=True, **STRETCH)

        # tren hanya untuk metrik yang nilainya benar-benar berbeda antar run (run yang membaca artefak sama → datar)
        tm = metrics[(metrics["task_id"] == task) & (metrics["status"] == "ok")]
        tm = tm[tm["value"].map(lambda v: isinstance(v, (int, float)) and not isinstance(v, bool))]
        varying = sorted(n for n, d in tm.groupby("name") if d["value"].astype(float).round(12).nunique() > 1)
        if len(trun) > 1:
            if varying:
                name = st.selectbox("Tren metrik antar run (hanya metrik yang berubah)", varying, key="eval_trend")
                st.plotly_chart(plots.metric_trend(metrics, runs, task, name), **STRETCH)
            else:
                st.caption("Tren antar run tidak ditampilkan: semua metrik bernilai sama di setiap run tahap ini "
                           "(run membaca artefak yang sama).")
    with st.expander(f"Input ({len(rec.inputs)}) & output ({len(rec.outputs)}) run ini"):
        if rec.inputs:
            st.markdown("**Input** (sha256 saat dibaca; run produsen = run yang menulis file dengan hash sama)")
            st.dataframe(ref_view(rec.inputs), hide_index=True, **STRETCH)
        if rec.outputs:
            st.markdown("**Output** (= file sekarang: apakah file di lokasi baca masih hasil run ini)")
            st.dataframe(ref_view(rec.outputs, sync), hide_index=True, **STRETCH)

# --------------------------------------------------------------------------- C. perbandingan
if section == "Perbandingan run":
    multi = [t for t in tasks if (runs["task_id"] == t).sum() >= 2]
    if not multi:
        st.info("Belum ada tahap dengan dua run atau lebih.")
        st.stop()
    task_c = st.selectbox("Tahap (hanya tahap dengan ≥ 2 run)", multi, format_func=LABELS.get, key="cmp_task")
    ids = list(runs.loc[runs["task_id"] == task_c, "run_id"])
    chosen = st.multiselect("Run yang dibandingkan (pertama = acuan)", ids[::-1], default=ids[::-1][:2],
                            key=f"cmp_runs_{task_c}",       # kunci per tahap: pilihan run tidak terbawa antar tahap
                            format_func=lambda r: f"{r} ({RUN_TYPE.get(records[r].run_type, '')})")
    if len(chosen) < 2:
        st.info("Pilih minimal dua run dari tahap yang sama.")
    else:
        cmp = store.compare_runs(CFG, chosen)
        sel = [records[r] for r in chosen]
        base = sel[0]

        def same(f) -> str:
            vals = [f(r) for r in sel]
            return "sama" if len({json.dumps(v, sort_keys=True, default=str) for v in vals}) == 1 else "berbeda"

        def io_same(io: str) -> str:
            sig = [sorted((a.name, a.sha256) for a in getattr(r, io)) for r in sel]
            return "sama" if all(s == sig[0] for s in sig) else "berbeda"

        st.markdown("**Sidik jari run**")
        st.dataframe(pd.DataFrame([
            {"komponen": "jenis run", **{r.run_id: RUN_TYPE.get(r.run_type, r.run_type) for r in sel},
             "hasil": same(lambda r: r.run_type)},
            {"komponen": "commit", **{r.run_id: (r.git_commit or "–")[:8] for r in sel}, "hasil": same(lambda r: r.git_commit)},
            {"komponen": "working tree", **{r.run_id: {True: "kotor", False: "bersih", None: "–"}[r.git_dirty] for r in sel},
             "hasil": same(lambda r: r.git_dirty)},
            {"komponen": "code hash", **{r.run_id: (r.code_sha256 or "– (log lama)")[:12] for r in sel},
             "hasil": same(lambda r: r.code_sha256)},
            {"komponen": "config hash", **{r.run_id: ", ".join(v[:8] for v in r.config_sha256.values()) for r in sel},
             "hasil": same(lambda r: r.config_sha256)},
            {"komponen": "dataset", **{r.run_id: r.dataset_id for r in sel}, "hasil": same(lambda r: r.dataset_id)},
            {"komponen": "platform", **{r.run_id: r.platform for r in sel}, "hasil": same(lambda r: r.platform)},
            {"komponen": "artefak input", **{r.run_id: f"{len(r.inputs)} file" for r in sel}, "hasil": io_same("inputs")},
            {"komponen": "artefak output", **{r.run_id: f"{len(r.outputs)} file" for r in sel}, "hasil": io_same("outputs")},
        ]), hide_index=True, **STRETCH)

        mt = cmp["metrics"]
        chg_cols = [c for c in mt.columns if c.startswith("perubahan ")]
        if chg_cols:
            allchg = pd.concat([mt[c] for c in chg_cols])
            cc = st.columns(4)
            for i, k in enumerate(("sama", "berubah", "baru", "hilang")):
                cc[i].metric(f"Metrik {k}", int((allchg == k).sum()))
        hide = st.toggle("Sembunyikan metrik yang sama", value=True, key="cmp_only")
        if hide and chg_cols:
            mt = mt[(mt[chg_cols] != "sama").any(axis=1)]
        show = mt.copy()
        for c in chosen:
            if c in show:
                show[c] = show[c].map(fmt_value)
        st.dataframe(show, hide_index=True, **STRETCH)
        st.caption("perubahan: sama | berubah (nilai berbeda) | baru (tidak ada di run acuan) | hilang (tidak ada di run "
                   "pembanding). delta = nilai run − nilai run acuan (hanya metrik numerik).")
        st.markdown("**Perbedaan parameter & lingkungan**")
        st.dataframe(cmp["params"].astype(str) if len(cmp["params"]) else pd.DataFrame({"catatan": ["tidak ada beda"]}),
                     hide_index=True, **STRETCH)
        st.markdown("**Artefak input/output (sha256)** — input berubah = perubahan di tahap hulu")
        st.dataframe(cmp["artifacts"], hide_index=True, **STRETCH)

# --------------------------------------------------------------------------- D. pipeline
if section == "Alur pipeline":
    edges = pd.DataFrame(registry.dependency_edges())
    stale_df = store.staleness(CFG)
    stale = set(stale_df.loc[stale_df["stale"], "task_id"])
    st.plotly_chart(plots.pipeline_graph(edges, states, stale, SHORT), **STRETCH)
    st.caption("Warna = status tahap: dieksekusi (biru), output tidak sinkron (kuning tua), hanya dievaluasi (biru muda: "
               "belum ada run eksekusi tercatat), gagal (oranye). Dependensi dibaca dari REQUIRES/OPTIONAL setiap pipeline "
               "(dites: setiap artefak yang dibaca harus dideklarasikan). 'Basi' = artefak input berubah setelah run "
               "terakhir tahap itu.")
    if stale:
        st.warning("Input berubah setelah run terakhir: " + ", ".join(LABELS.get(t, t) for t in sorted(stale)))
        st.dataframe(stale_df[stale_df["stale"]], hide_index=True, **STRETCH)

    st.subheader("Sinkron artefak (lineage output)")
    st.caption("Apakah file artefak yang dibaca app & tahap berikutnya benar-benar ditulis oleh run eksekusi tercatat. "
               "Run paling baru tidak dianggap produsen resmi hanya karena paling baru. `checksums` tidak sinkron bila "
               "ditulis ulang di folder lain: isi snapshot sama, hanya kolom waktu `recorded_at` yang berbeda.")
    states_present = [s for s in store.SYNC_STATES if s in set(sync["state"])]
    pick_s = st.multiselect("Status artefak", states_present, default=states_present, key="sync_state")
    sv = sync[sync["state"].isin(pick_s)]
    st.dataframe(sv.rename(columns={"artifact": "artefak", "stage": "tahap", "current_sha": "sha sekarang",
                                    "state": "status", "producer_run": "run eksekusi produsen",
                                    "last_execution_run": "run eksekusi terakhir", "last_execution_sha": "sha run itu",
                                    "last_execution_rows": "baris (run)", "current_rows": "baris (sekarang)",
                                    "evaluated_by": "dievaluasi oleh"}), hide_index=True, **STRETCH)

    e = edges.assign(produsen=edges["producer"].map(LABELS), konsumen=edges["consumer"].map(LABELS),
                     jenis=edges["required"].map({True: "wajib", False: "opsional"}))
    with st.expander(f"Daftar dependensi ({len(e)} sisi)"):
        st.dataframe(e[["produsen", "artifact", "konsumen", "jenis"]].rename(columns={"artifact": "artefak"}),
                     hide_index=True, **STRETCH)
    pipes = store.load_pipelines(CFG)
    if pipes:
        st.markdown("**Eksekusi pipeline (`kagami all`)**")
        st.dataframe(pd.DataFrame([{"pipeline": k, "mulai": fmt_time(v.get("started_at")),
                                    "status": RUN_STATUS.get(v.get("status"), v.get("status")),
                                    "run": " → ".join(f"{r['task_id']}:{RUN_STATUS.get(r['status'], r['status'])}"
                                                      for r in v.get("runs", []))}
                                   for k, v in pipes.items()]), hide_index=True, **STRETCH)

# --------------------------------------------------------------------------- E. riwayat
if section == "Riwayat":
    t_all = pd.to_datetime(runs["started_at"], format="ISO8601", utc=True)
    c1, c2, c3 = st.columns(3)
    f_task = c1.multiselect("Tahap", tasks, default=tasks, format_func=LABELS.get, key="hist_task")
    f_status = c2.multiselect("Status", sorted(runs["status"].unique()), default=sorted(runs["status"].unique()),
                              format_func=lambda s: RUN_STATUS.get(s, s), key="hist_status")
    f_type = c3.multiselect("Jenis run", sorted(runs["run_type"].unique()), default=sorted(runs["run_type"].unique()),
                            format_func=lambda s: RUN_TYPE.get(s, s), key="hist_type")
    c4, c5 = st.columns(2)
    plats = sorted(runs["platform"].fillna("–").unique())
    f_plat = c4.multiselect("Platform", plats, default=plats, key="hist_platform")
    d0, d1 = t_all.min().date(), t_all.max().date()
    rng = c5.date_input("Rentang tanggal mulai (UTC)", value=(d0, d1), min_value=d0, max_value=d1, key="hist_dates")
    lo, hi = (rng[0], rng[-1]) if isinstance(rng, (tuple, list)) and len(rng) else (d0, d1)
    keep = (runs["task_id"].isin(f_task) & runs["status"].isin(f_status) & runs["run_type"].isin(f_type)
            & runs["platform"].fillna("–").isin(f_plat) & (t_all.dt.date >= lo) & (t_all.dt.date <= hi))
    mode = st.radio("Tampilan", ["Semua run", "Terbaru per tahap + semua eksekusi", "Hanya eksekusi"], horizontal=True,
                    key="hist_mode")
    if mode != "Semua run":
        latest_ids = set(runs.groupby("task_id")["run_id"].last())
        keep &= runs["run_type"].eq("execution") | (runs["run_id"].isin(latest_ids) & (mode != "Hanya eksekusi"))
    h = runs[keep].assign(_t=t_all[keep]).sort_values("_t", ascending=False)
    view = pd.DataFrame({
        "run": h["run_id"], "detail": "?bagian=Evaluasi+per+tahap&run=" + h["run_id"],
        "tahap": h["task_id"].map(LABELS), "jenis": h["run_type"].map(RUN_TYPE),
        "status": h["status"].map(RUN_STATUS), "mulai": h["started_at"].map(fmt_time),
        "waktu eksekusi": h["duration_s"].map(fmt_dur), "ringkasan evaluasi": h["summary"],
        "dataset": h["dataset_id"], "commit": h["git_commit"].fillna("–"),
        "working tree": h["git_dirty"].map({True: "kotor", False: "bersih"}).fillna("–"),
        "code hash": h["code_sha256"].fillna("– (log lama)"), "versi evaluator": h["evaluator_version"].fillna("–"),
        "platform": h["platform"],
        "galat": h["error_type"].fillna("–"), "algoritma": h["algorithm"]})
    st.dataframe(view, hide_index=True, **STRETCH, column_config={
        "detail": st.column_config.LinkColumn("detail", display_text="buka evaluasi"),
        "algoritma": st.column_config.TextColumn("algoritma", width="large")})
    st.caption(f"{len(view)} dari {len(runs)} run · 'buka evaluasi' membuka bagian Evaluasi per tahap untuk run itu · "
               "working tree kotor = kode/config berubah tanpa commit saat run (commit saja tidak mewakili kodenya; "
               "pakai code hash).")

st.caption("Sumber: log pelacakan `logs/runs`, `logs/evaluations`, `logs/errors`, `logs/pipelines` (WP-36) · waktu dalam "
           "UTC · metrik dihitung dari artefak hasil saat evaluasi; penilaian terhadap acuan dihitung saat halaman dibaca "
           "(D-140).")
