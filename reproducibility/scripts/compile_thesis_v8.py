#!/usr/bin/env python3
r"""
THESIS COMPILATION SCRIPT FOR GOOGLE COLAB  v8
===============================================
TurkQuish — Springer Nature manuscript
"""
import os, shutil, glob, subprocess, time, sys, re

# ── YOUR PATHS ───────────────────────────────────────────────
LATEX_DIR   = "Latex"
DATA_DIR    = "/"
COMPILE_DIR = "/content/compile_thesis"   # MUST be local — Drive I/O is 10× slower
# ─────────────────────────────────────────────────────────────

os.makedirs(COMPILE_DIR, exist_ok=True)

# ── Active manuscript detection ───────────────────────────────
def _version_score(filename):
    """Return the last integer in a filename, used to prefer v6 over v5, etc."""
    nums = re.findall(r"(\d+)", filename)
    return int(nums[-1]) if nums else -1


def detect_main_tex():
    """Find the manuscript .tex file without hardcoding v5/v6.

    Priority:
      1. Highest-version main_integrated*.tex in LATEX_DIR
      2. Common fallback names, so the error message remains clear if missing
    """
    existing = []
    if os.path.isdir(LATEX_DIR):
        existing = [os.path.basename(p) for p in glob.glob(os.path.join(LATEX_DIR, "main_integrated*.tex"))]
    if existing:
        existing.sort(
            key=lambda x: (_version_score(x), os.path.getmtime(os.path.join(LATEX_DIR, x))),
            reverse=True,
        )
        return existing[0]
    for fallback in ("main_integrated_v6.tex", "main_integrated_v7.tex", "main_integrated.tex"):
        if os.path.exists(os.path.join(LATEX_DIR, fallback)):
            return fallback
    return "main_integrated_v6.tex"  # fallback name used only for a clear fatal message


MAIN_TEX  = detect_main_tex()
MAIN_STEM = os.path.splitext(MAIN_TEX)[0]

print("="*66)
print("THESIS COMPILATION  v8  (TurkQuish / Springer Nature)")
print("="*66)
print(f"Source:      {LATEX_DIR}")
print(f"Compile dir: {COMPILE_DIR}  ← local (fast)")
print(f"Manuscript:  {MAIN_TEX}")

# ═══════════════════════════════════════════════════════════════
# STEP 0 — Install LaTeX packages
# ═══════════════════════════════════════════════════════════════
print("\n[0] Checking / installing required LaTeX packages…")

PKGS = [
    "texlive-science",        # algorithm, algorithmicx, algpseudocode
    "texlive-latex-extra",    # multirow, booktabs, appendix, listings, tabularx
    "texlive-fonts-extra",    # lmodern, mathrsfs, extra fonts
    "texlive-bibtex-extra",   # natbib, sn-mathphys-num.bst compatible BSTs
    "texlive-font-utils",
    "texlive-lang-european",  # T1 font encoding for Turkish characters
]

r = subprocess.run("kpsewhich algorithm.sty", shell=True, capture_output=True)
if r.returncode == 0:
    print("    ✓ LaTeX packages already installed — skipping")
else:
    print(f"    Installing: {' '.join(PKGS)}")
    r = subprocess.run(
        f"apt-get install -y {' '.join(PKGS)} > /tmp/apt.log 2>&1", shell=True)
    if r.returncode == 0:
        print("    ✓ Packages installed")
    else:
        print("    ✗ apt-get failed — check /tmp/apt.log")
        subprocess.run("tlmgr install algorithms algorithmicx 2>/dev/null", shell=True)


# ═══════════════════════════════════════════════════════════════
# STEP 0b — Install Pandoc / citeproc for DOCX export
# ═══════════════════════════════════════════════════════════════
print("\n[0b] Checking / installing Pandoc for DOCX export…")


def _pandoc_version_tuple():
    if not shutil.which("pandoc"):
        return ()
    try:
        line = subprocess.run(["pandoc", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
        m = re.search(r"pandoc\s+(\d+)\.(\d+)(?:\.(\d+))?", line)
        if not m:
            return ()
        return tuple(int(x) for x in m.groups(default="0"))
    except Exception:
        return ()


def _pandoc_version_line():
    try:
        return subprocess.run(["pandoc", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    except Exception:
        return "pandoc detected"


if not shutil.which("pandoc"):
    print("    Installing: pandoc")
    r = subprocess.run(
        "apt-get update -qq && apt-get install -y pandoc > /tmp/pandoc_apt.log 2>&1",
        shell=True,
    )
    if r.returncode == 0 and shutil.which("pandoc"):
        print("    ✓ Pandoc installed")
    else:
        print("    ⚠ Pandoc install failed — DOCX export will be skipped")
        print("      Check /tmp/pandoc_apt.log if you need to debug it.")

if shutil.which("pandoc"):
    print(f"    ✓ {_pandoc_version_line()}")
    # Pandoc >= 2.11 supports --citeproc. Older Colab builds such as 2.9.2.1
    # need the separate pandoc-citeproc filter for citation processing.
    _pv = _pandoc_version_tuple()
    _needs_external_citeproc = bool(_pv) and _pv < (2, 11, 0)
    if _needs_external_citeproc and not shutil.which("pandoc-citeproc"):
        print("    Installing: pandoc-citeproc  (needed for old Pandoc citation export)")
        r = subprocess.run(
            "apt-get install -y pandoc-citeproc > /tmp/pandoc_citeproc_apt.log 2>&1",
            shell=True,
        )
        if r.returncode == 0 and shutil.which("pandoc-citeproc"):
            print("    ✓ pandoc-citeproc installed")
        else:
            print("    ⚠ pandoc-citeproc not available — DOCX will still export, but citation processing may be skipped")
            print("      Check /tmp/pandoc_citeproc_apt.log if you need to debug it.")

# ═══════════════════════════════════════════════════════════════
# STEP 1 — Pre-flight: sn-jnl.cls
# ═══════════════════════════════════════════════════════════════
print("\n[1] Pre-flight check…")
cls_candidates = [
    os.path.join(LATEX_DIR, "sn-jnl.cls"),
    "/content/drive/MyDrive/sn-jnl.cls",
    os.path.join(DATA_DIR, "sn-jnl.cls"),
    "/content/sn-jnl.cls",
]
cls_src = next((p for p in cls_candidates if os.path.exists(p)), None)
if cls_src:
    shutil.copy2(cls_src, os.path.join(COMPILE_DIR, "sn-jnl.cls"))
    print(f"    ✓ sn-jnl.cls  ← {cls_src}")
else:
    print("    ✗ FATAL: sn-jnl.cls not found.")
    print("      Download from springernature.com → LaTeX template")
    print("      Upload to: " + LATEX_DIR)
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# STEP 2 — Copy support files
# ═══════════════════════════════════════════════════════════════
print("\n[2] Copying support files…")

# Format: { filename : (fatal_if_missing, [alternative_names]) }
# fatal=True  → abort if file not found
# fatal=False → create a benign empty placeholder so pdflatex doesn't choke
SUPPORT_FILES = {
    MAIN_TEX:                         (True,  []),
    "sn-mathphys-num.bst":           (False, []),
    # FIX: check both bib filename variants (with and without _1 suffix)
    "sn-bibliography.bib":           (False, ["sn-bibliography_1.bib"]),
    "step7c_comparison_table.tex":   (False, []),
    "shap_top_features_5class.tex":  (False, []),
    "shap_top_features_binary.tex":  (False, []),
    "convergence_table_5class.tex":  (False, []),
    "convergence_table_binary.tex":  (False, []),   # ← ADDED in v5
    "feature_selection_summary.tex": (False, []),
    "step5_ablation_table.tex":      (False, []),   # ← ADDED in v5
}

for fn, (fatal, alternatives) in SUPPORT_FILES.items():
    dst = os.path.join(COMPILE_DIR, fn)

    # Try primary name, then alternatives
    src = None
    for candidate in [fn] + alternatives:
        p = os.path.join(LATEX_DIR, candidate)
        if os.path.exists(p):
            src = p
            break

    if src:
        shutil.copy2(src, dst)
        marker = "" if os.path.basename(src) == fn else f"  (copied from {os.path.basename(src)})"
        print(f"    ✓ {fn}{marker}")
    elif fatal:
        print(f"    ✗ FATAL: {fn} not found")
        sys.exit(1)
    else:
        # Write a non-empty comment placeholder so \input{} doesn't error
        with open(dst, 'w') as f:
            f.write(f"% PLACEHOLDER: {fn} was not found in LATEX_DIR\n"
                    f"% Copy the real file to: {LATEX_DIR}\n")
        print(f"    ~ {fn}  (placeholder — file not found in LATEX_DIR)")

# ═══════════════════════════════════════════════════════════════
# STEP 3 — Collect PNG figures from all eval directories
# ═══════════════════════════════════════════════════════════════
print("\n[3] Collecting PNG figures…")

FIG_ROOTS = [
    LATEX_DIR,
    os.path.join(DATA_DIR, "journal_eval_5class"),
    os.path.join(DATA_DIR, "journal_eval_binary"),
    os.path.join(DATA_DIR, "journal_eval_xai"),
    os.path.join(DATA_DIR, "journal_eval_combined"),
    os.path.join(DATA_DIR, "journal_eval_combined_folds"),
    os.path.join(DATA_DIR, "journal_eval_feature_selection"),
    os.path.join(DATA_DIR, "journal_eval_ablation"),   # ← ADDED v6: fig_ablation_*.png
    os.path.join(DATA_DIR, "ablation"),                # ← ADDED v6: fallback ablation dir
    DATA_DIR,
]

copied = 0
for root_dir in FIG_ROOTS:
    if not os.path.isdir(root_dir):
        continue
    for dirpath, _, files in os.walk(root_dir):
        for fn in files:
            if not fn.endswith(".png"):
                continue
            src = os.path.join(dirpath, fn)
            dst = os.path.join(COMPILE_DIR, fn)
            if not os.path.exists(dst):
                try:
                    shutil.copy2(src, dst)
                    copied += 1
                except Exception:
                    pass

total_pngs = len(glob.glob(os.path.join(COMPILE_DIR, "*.png")))
print(f"    Copied {copied} PNG file(s)  |  Total in compile dir: {total_pngs}")

# ═══════════════════════════════════════════════════════════════
# STEP 3b — Missing-figure audit  [FIXED in v5]
#
# v4 PROBLEM: Created 1×1 white PNG placeholders for every missing figure.
#   → pdflatex compiled without errors
#   → PDF showed blank boxes (looked fine at a glance, was invalid)
#   → Author had no visibility into which figures were missing
#
# v5 FIX: Report missing figures, write MISSING_FIGURES.txt, and let
#   pdflatex error naturally so the author knows what to generate.
# ═══════════════════════════════════════════════════════════════
print("\n[3b] Auditing missing figures…")

# All figures referenced by \includegraphics in main_integrated_v7.tex.
# Kept in sync with the .tex on 2026-06-13. If you add/remove a figure in the
# manuscript, update this list so the audit stays meaningful.
KEY_FIGURES = [
    # Architecture / overview
    "architecture_diagram",
    # Operational prototype (composite of the 4 Flutter screens — YOU generate this)
    "turkquish_mobile_prototype",
    # Model comparison
    "comparison_7model_5fold", "cv_all_metrics", "all_confusion_matrices",
    "per_class_heatmap",
    # Discrimination curves / calibration / threshold (combined-fold)
    "roc_curves", "pr_curves", "det_curves", "calibration_curves",
    "threshold_cost_analysis",
    "radar_chart", "fold_stability",
    # Cross-validation all-folds curves (Section 4.7)
    "cv_roc_5class",        "cv_roc_binary",
    "cv_pr_5class",         "cv_pr_binary",
    "cv_det_binary",
    "cv_calibration_5class","cv_calibration_binary",
    "cv_confusion_histgb_5class",
    "cv_confusion_histgb_5class_perfold",   # per-fold panel — DIFFERENT from above; YOU generate this
    "cv_confusion_histgb_binary",
    "cv_metrics_all_folds_5class","cv_metrics_all_folds_binary",
    "cv_roc_per_class_5class","cv_pr_per_class_5class",
    "cv_error_patterns_5class","cv_error_patterns_binary",
    # Deep-learning baseline attention
    "step7b_attention_summary",
    # XAI / SHAP
    "shap_bar_5class",     "shap_bar_binary",
    "shap_beeswarm_5class","shap_beeswarm_binary",
    "shap_dependence_5class",
    "shap_waterfall_5class","shap_waterfall_binary",
    "shap_perclass_heatmap_5class",
    # LIME / permutation / convergence
    "lime_local_5class",   "lime_local_binary",
    "permutation_importance_5class","permutation_importance_binary",
    "convergence_5class",  "convergence_binary",
    # Feature selection (Section 3.8)
    "feature_correlation_heatmap", "top_features_label_corr",
    "mutual_information_scores", "near_zero_variance",
    "multi_method_consensus", "feature_stability_cv",
    "feature_selection_curve", "feature_group_summary",
    "feature_redundancy", "class_conditional_distributions",
    "turkish_feature_analysis_5class",
    # Efficiency / error analysis
    "efficiency", "error_analysis", "error_url_length",
    # Deployment
    "deployment_workflow",
    # Feature-group ablation (Section 4, A1–A8)
    "fig_ablation_contribution_summary",
    "fig_ablation_delta_macro_f1",
    "fig_ablation_macro_f1",
    "fig_ablation_efficiency_tradeoff",
    "fig_ablation_feature_group_matrix",
]

# Figures you must generate yourself (not produced by the eval notebooks).
# These are flagged separately so a missing one is an explicit, expected TODO
# rather than a surprise.
AUTHOR_GENERATED_FIGURES = [
    "turkquish_mobile_prototype",          # 4-panel composite of the app screens
    "cv_confusion_histgb_5class_perfold",  # per-fold confusion panel
]

_all_missing = [
    n for n in KEY_FIGURES
    if not os.path.exists(os.path.join(COMPILE_DIR, f"{n}.png"))
]
# Split into (a) author-generated TODO figures and (b) eval-pipeline figures
# that should have been produced and copied.
todo_missing    = [n for n in _all_missing if n in AUTHOR_GENERATED_FIGURES]
missing_figs    = [n for n in _all_missing if n not in AUTHOR_GENERATED_FIGURES]

if todo_missing:
    print(f"\n    ⚠  {len(todo_missing)} author-generated figure(s) not yet in the compile dir:")
    for n in todo_missing:
        print(f"        ⧗  {n}.png   (you generate this — see notes)")
    print("        These are expected TODOs, not pipeline failures.")

if missing_figs:
    print(f"\n    ⚠  WARNING — {len(missing_figs)} of {len(KEY_FIGURES)} figures are missing:\n")
    for n in missing_figs:
        print(f"        ✗  {n}.png")
    report_path = os.path.join(COMPILE_DIR, "MISSING_FIGURES.txt")
    with open(report_path, "w") as f:
        f.write(f"MISSING FIGURES REPORT — TurkQuish\n")
        f.write(f"Generated : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total expected         : {len(KEY_FIGURES)}\n")
        f.write(f"Pipeline figures missing: {len(missing_figs)}\n")
        f.write(f"Author-TODO missing     : {len(todo_missing)}  ({', '.join(todo_missing) if todo_missing else 'none'})\n\n")
        f.write("Missing files:\n")
        for n in missing_figs:
            f.write(f"  MISSING: {n}.png\n")
        f.write("\nAction required:\n")
        f.write("  Run your evaluation notebooks/scripts to generate these figures,\n")
        f.write("  then re-run this compilation script.\n")
    print(f"\n    Report written → {report_path}")
    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │  NOTE (v5 change)                                               │
    │  v4 silently created 1×1 white PNG placeholders for all these  │
    │  files. pdflatex compiled without errors but the manuscript     │
    │  contained blank figure boxes — an invalid submission.         │
    │  v5 lets pdflatex error on missing figures so you know exactly  │
    │  what to generate before submitting.                            │
    └─────────────────────────────────────────────────────────────────┘
""")
elif not todo_missing:
    print(f"    ✓ All {len(KEY_FIGURES)} key figures found")
else:
    print(f"    ✓ All pipeline figures found "
          f"({len(KEY_FIGURES)-len(todo_missing)}/{len(KEY_FIGURES)}); "
          f"{len(todo_missing)} author-generated figure(s) still to add.")

# ═══════════════════════════════════════════════════════════════
# STEP 4 — Compile: pdflatex → bibtex → pdflatex → pdflatex
#
# FIX v5: Added BibTeX pass.  v4 ran 3× pdflatex with no bibtex,
# so all \cite{} appeared as [?] and the bibliography was empty.
# ═══════════════════════════════════════════════════════════════
os.chdir(COMPILE_DIR)

# Clean stale build artifacts so BibTeX mode is detected from the current source,
# not from an old .aux/.bbl left in /content/compile_thesis.
for ext in ("aux", "bbl", "blg", "log", "out", "toc", "lof", "lot"):
    stale = os.path.join(COMPILE_DIR, f"{MAIN_STEM}.{ext}")
    if os.path.exists(stale):
        try:
            os.remove(stale)
        except Exception:
            pass

print(f"\n[4] Compiling  (auto bibliography mode)…")
print(f"    Working dir: {os.getcwd()}")

def run_latex(label, extra_flags=""):
    t0 = time.time()
    cmd = (f"pdflatex -interaction=nonstopmode {extra_flags} "
           f"{MAIN_TEX}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    elapsed = time.time() - t0
    errors = [l for l in r.stdout.split("\n")
              if l.startswith("!") or "Emergency stop" in l or "Fatal error" in l]
    ok = r.returncode == 0 and not errors
    status = "✓" if ok else "✗"
    print(f"  {status}  {label}  ({elapsed:.0f}s)")
    if not ok:
        for e in errors[:5]:
            print(f"       {e}")
    return ok

def run_bibtex(label="bibtex"):
    t0 = time.time()
    r = subprocess.run(f"bibtex {MAIN_STEM}", shell=True,
                       capture_output=True, text=True)
    elapsed = time.time() - t0
    ok = r.returncode == 0
    print(f"  {'✓' if ok else '✗'}  {label}  ({elapsed:.0f}s)")
    if not ok:
        for l in r.stdout.split("\n")[:5]:
            if l.strip():
                print(f"       {l}")
    return ok

ok1 = run_latex("pdflatex pass 1 / 3")

# Detect bibliography mode from the current files after pass 1.
# - External BibTeX mode: .aux contains \bibdata{...}; run bibtex.
# - Embedded bibliography mode: main_integrated.tex contains \begin{thebibliography};
#   do NOT run bibtex, because BibTeX will fail with "I found no \bibdata command".
aux_path = os.path.join(COMPILE_DIR, f"{MAIN_STEM}.aux")
tex_path = os.path.join(COMPILE_DIR, MAIN_TEX)

aux_text = open(aux_path, encoding="utf-8", errors="replace").read() if os.path.exists(aux_path) else ""
tex_text = open(tex_path, encoding="utf-8", errors="replace").read() if os.path.exists(tex_path) else ""

has_bibdata = r"\bibdata" in aux_text
has_embedded_bibliography = r"\begin{thebibliography}" in tex_text

if has_bibdata:
    print("    Bibliography mode: external BibTeX database detected from .aux")
    bib_ok = run_bibtex("bibtex")
elif has_embedded_bibliography:
    print("    Bibliography mode: embedded thebibliography detected — skipping bibtex")
    bib_ok = True
else:
    print("    ⚠ Bibliography mode: no \\bibdata and no embedded thebibliography found")
    print("      Add either \\bibliography{sn-bibliography} or an embedded thebibliography block.")
    bib_ok = False

ok2 = run_latex("pdflatex pass 2 / 3")
ok3 = run_latex("pdflatex pass 3 / 3")

# ── v6: sanity-check that the six Cluster Computing refs are in the .bib ──
# If they are absent, the Related-Work positioning citations render as [?].
_bib_path = None
for _cand in ("sn-bibliography.bib", "sn-bibliography_1.bib"):
    _p = os.path.join(COMPILE_DIR, _cand)
    if os.path.exists(_p):
        _bib_path = _p
        break
if _bib_path:
    _bib_txt = open(_bib_path, encoding="utf-8", errors="replace").read()
    _cc_keys = ["ref_cc_phishtackle", "ref_cc_jain2025", "ref_cc_bourigue2025",
                "ref_cc_youssef2026", "ref_cc_jamali2023", "ref_cc_liu2025"]
    _cc_missing = [k for k in _cc_keys if k not in _bib_txt]
    if _cc_missing:
        print(f"    ⚠ {len(_cc_missing)} Cluster Computing ref(s) absent from "
              f"{os.path.basename(_bib_path)}: {', '.join(_cc_missing)}")
        print("      Those \\cite{} calls will render as [?]. Use the augmented .bib.")

# ═══════════════════════════════════════════════════════════════
# STEP 5 — Warning / quality summary
# ═══════════════════════════════════════════════════════════════
print("\n[5] Compilation quality summary:")

log_path = os.path.join(COMPILE_DIR, f"{MAIN_STEM}.log")
if os.path.exists(log_path):
    log = open(log_path, encoding="utf-8", errors="replace").read()

    ov   = log.count("Overfull \\hbox")
    un   = log.count("Underfull \\hbox")
    vb   = log.count("Underfull \\vbox")
    refs = len(re.findall(r"LaTeX Warning: Reference `[^']+' on page .* undefined", log))
    cits = len(re.findall(r"LaTeX Warning: Citation `[^']+' on page .* undefined", log))
    pg   = re.search(r"Output written.*?(\d+) page", log)

    sym  = lambda n, good=0: "✓" if n == good else "✗" if n > 0 else "⚠"
    print(f"  Overfull  \\hbox    : {ov:4d}  {sym(ov)}")
    print(f"  Underfull \\hbox    : {un:4d}  {'✓' if un==0 else '⚠'}")
    print(f"  Underfull \\vbox    : {vb:4d}  {'✓' if vb<=10 else '⚠  (>10 is unusual)'}")
    print(f"  Undefined refs     : {refs:4d}  {sym(refs)}"
          + ("  ← run bibtex + 2× pdflatex again" if refs > 0 else ""))
    print(f"  Undefined citations: {cits:4d}  {sym(cits)}"
          + ("  ← check .bib file keys match \\cite{} keys" if cits > 0 else ""))
    if missing_figs:
        print(f"  Missing figures    : {len(missing_figs):4d}  ✗  (see MISSING_FIGURES.txt)")
    if todo_missing:
        print(f"  Author-TODO figs   : {len(todo_missing):4d}  ⧗  ({', '.join(todo_missing)})")

    if ov > 0:
        print("\n  Overfull \\hbox details:")
        for m in re.findall(r"Overfull \\hbox.*?pt too wide[^\n]*", log):
            print(f"    ! {m}")

    if pg:
        print(f"\n  {'✓' if ok3 else '⚠'}  {pg.group(0)}")
    else:
        print("\n  ✗  No PDF produced — fix the errors listed above and re-run.")
else:
    print("  ✗  Log file not found")

# ═══════════════════════════════════════════════════════════════
# STEP 6 — Copy PDF back to Drive
# ═══════════════════════════════════════════════════════════════
print("\n[6] Saving PDF to Drive…")
src_pdf = os.path.join(COMPILE_DIR, f"{MAIN_STEM}.pdf")
dst_pdf = os.path.join(LATEX_DIR, f"{MAIN_STEM}.pdf")

if os.path.exists(src_pdf):
    shutil.copy2(src_pdf, dst_pdf)
    sz_mb = os.path.getsize(dst_pdf) / 1e6
    print(f"  ✓  Saved → {dst_pdf}  ({sz_mb:.1f} MB)")
    if sz_mb < 0.5:
        print("  ⚠  PDF is suspiciously small (<0.5 MB) — likely compiled with errors.")
    if missing_figs:
        print(f"  ✗  PDF has {len(missing_figs)} missing pipeline figure(s). DO NOT SUBMIT.")
    elif todo_missing:
        print(f"  ⧗  {len(todo_missing)} author-generated figure(s) still to add "
              f"({', '.join(todo_missing)}). Add before submitting.")
    elif not ok3 or not bib_ok:
        print("  ⚠  Compilation had errors or bibliography mode is unresolved — review the log before submitting.")
    else:
        print("  ✓  Compilation looks clean.")
else:
    print("  ✗  PDF not produced — fix errors above and re-run.")


# ═══════════════════════════════════════════════════════════════
# STEP 7 — Export DOCX beside the PDF
# ═══════════════════════════════════════════════════════════════
print("\n[7] Exporting DOCX to Drive…")

src_docx = os.path.join(COMPILE_DIR, f"{MAIN_STEM}.docx")
dst_docx = os.path.join(LATEX_DIR, f"{MAIN_STEM}.docx")


def _patch_known_pandoc_math_blocks(tex_text):
    """Patch DOCX-only LaTeX content that Pandoc struggles with.

    This does NOT modify MAIN_TEX. It only modifies the temporary
    *_pandoc_docx.tex file used for Word export.
    """
    patches = []

    # Pandoc can fail when it sees several $$...$$ chunks nested inside a wider
    # math parse. The mask-update equation is clearer as one aligned equation.
    marker = r"\mathbf{B}_{\text{trusted}}"
    if marker in tex_text:
        idx = tex_text.find(marker)
        possible_starts = [
            tex_text.rfind(r"\begin{equation}", 0, idx),
            tex_text.rfind(r"\begin{equation*}", 0, idx),
            tex_text.rfind(r"\[", 0, idx),
            tex_text.rfind("$$", 0, idx),
        ]
        start = max(possible_starts)
        phish_idx = tex_text.find(r"\mathbf{B}_{\text{phish\_hit}}", idx)
        if phish_idx == -1:
            phish_idx = tex_text.find(r"phish\_hit", idx)

        if start != -1 and phish_idx != -1:
            end_candidates = []
            for token in (r"\end{equation}", r"\end{equation*}", r"\]", "$$"):
                pos = tex_text.find(token, phish_idx)
                if pos != -1:
                    end_candidates.append((pos + len(token), token))
            if end_candidates:
                end, _ = min(end_candidates, key=lambda x: x[0])
                old_block = tex_text[start:end]
                label_match = re.search(r"\\label\{[^}]+\}", old_block)
                label_line = "\n" + label_match.group(0) if label_match else ""
                clean_block = r"""
\begin{equation}
\begin{aligned}
\mathbf{B}_{\mathrm{trusted}} &= [w(s_i) \geq 0.85],\\
\mathbf{B}_{\mathrm{low\_conf}} &= [w(s_i) < 0.85 \text{ and } \Lambda_i \neq \mathrm{None}],\\
\mathbf{B}_{\mathrm{nohit}} &= \left[\sum_j \kappa_j = 0\right],\\
\mathbf{y}[\mathbf{B}_{\mathrm{trusted}}] &\leftarrow M(\Lambda),\\
\mathbf{y}[\mathbf{B}_{\mathrm{low\_conf}} \wedge \mathbf{B}_{\mathrm{nohit}}] &\leftarrow M(\Lambda),\\
\mathbf{y}[\neg\mathbf{B}_{\mathrm{trusted}} \wedge \neg\mathbf{B}_{\mathrm{nohit}} \wedge \mathbf{B}_{\mathrm{phish\_hit}}] &\leftarrow 1.
\end{aligned}%s
\end{equation}
""" % label_line
                tex_text = tex_text[:start] + clean_block + tex_text[end:]
                patches.append("normalized mask-update equation block for Pandoc DOCX export")

    return tex_text, patches


def prepare_pandoc_tex(src_tex, dst_tex):
    """Create a Pandoc-friendly LaTeX copy for DOCX export only."""
    text = open(src_tex, encoding="utf-8", errors="replace").read()
    patches = []

    # Word does not need sideways/landscape environments; normal table wrappers
    # are more reliable for Pandoc conversion.
    replacements = {
        r"\begin{sidewaystable}": r"\begin{table}",
        r"\end{sidewaystable}": r"\end{table}",
        r"\begin{landscape}": r"% PANDOC-DOCX: removed landscape wrapper",
        r"\end{landscape}": r"% PANDOC-DOCX: removed landscape wrapper",
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
            patches.append(f"replaced {old} for DOCX compatibility")

    text, math_patches = _patch_known_pandoc_math_blocks(text)
    patches.extend(math_patches)

    with open(dst_tex, "w", encoding="utf-8") as f:
        f.write(text)
    return dst_tex, patches


def pandoc_citeproc_args(bib_path):
    """Return citation-processing args compatible with installed Pandoc."""
    if not bib_path:
        return []
    pv = _pandoc_version_tuple()
    if pv and pv >= (2, 11, 0):
        return ["--citeproc", "--bibliography", bib_path]
    if shutil.which("pandoc-citeproc"):
        return ["--filter", "pandoc-citeproc", "--bibliography", bib_path]
    return []


def build_pandoc_cmd(input_tex, output_docx, bib_path=None, use_citations=True):
    resource_paths = [
        COMPILE_DIR,
        LATEX_DIR,
        DATA_DIR,
        os.path.join(DATA_DIR, "journal_eval_5class"),
        os.path.join(DATA_DIR, "journal_eval_binary"),
        os.path.join(DATA_DIR, "journal_eval_xai"),
        os.path.join(DATA_DIR, "journal_eval_combined"),
        os.path.join(DATA_DIR, "journal_eval_combined_folds"),
        os.path.join(DATA_DIR, "journal_eval_feature_selection"),
        os.path.join(DATA_DIR, "journal_eval_ablation"),
        os.path.join(DATA_DIR, "ablation"),
    ]
    resource_path_arg = ":".join(p for p in resource_paths if os.path.isdir(p))

    cmd = [
        pandoc_bin,
        input_tex,
        "--from=latex",
        "--to=docx",
        "--standalone",
        "--number-sections",
        "--wrap=none",
        "--resource-path", resource_path_arg,
        "--metadata", "link-citations=true",
        "--output", output_docx,
    ]
    if use_citations:
        cmd.extend(pandoc_citeproc_args(bib_path))
    return cmd


pandoc_bin = shutil.which("pandoc")
if not pandoc_bin:
    print("  ⚠  Pandoc not available — DOCX export skipped.")
    print("     To enable it manually in Colab, run: !apt-get install -y pandoc")
else:
    tex_file = os.path.join(COMPILE_DIR, MAIN_TEX)
    pandoc_tex_file = os.path.join(COMPILE_DIR, f"{MAIN_STEM}_pandoc_docx.tex")
    pandoc_tex_file, docx_patches = prepare_pandoc_tex(tex_file, pandoc_tex_file)

    if docx_patches:
        print("  ✓  Prepared Pandoc-safe LaTeX copy for DOCX export:")
        for p in docx_patches[:6]:
            print(f"     - {p}")
        if len(docx_patches) > 6:
            print(f"     ... {len(docx_patches)-6} more patch(es)")
    else:
        print("  ✓  Prepared Pandoc-safe LaTeX copy; no special patches needed")

    bib_for_pandoc = None
    for _cand in ("sn-bibliography.bib", "sn-bibliography_1.bib"):
        _p = os.path.join(COMPILE_DIR, _cand)
        if os.path.exists(_p):
            bib_for_pandoc = _p
            break

    cite_args = pandoc_citeproc_args(bib_for_pandoc)
    attempts = []
    if bib_for_pandoc and cite_args:
        attempts.append(("Pandoc-safe source with citation processing", build_pandoc_cmd(pandoc_tex_file, src_docx, bib_for_pandoc, True)))
    elif bib_for_pandoc:
        print("  ⚠  Bibliography found, but compatible citeproc support was not found; exporting DOCX without processed citations.")

    attempts.append(("Pandoc-safe source without citation processing", build_pandoc_cmd(pandoc_tex_file, src_docx, bib_for_pandoc, False)))
    attempts.append(("raw source without citation processing", build_pandoc_cmd(tex_file, src_docx, bib_for_pandoc, False)))

    final_result = None
    final_label = None
    for label, cmd in attempts:
        t0 = time.time()
        r = subprocess.run(cmd, cwd=COMPILE_DIR, capture_output=True, text=True)
        elapsed = time.time() - t0
        if r.returncode == 0 and os.path.exists(src_docx):
            final_result = (r, elapsed)
            final_label = label
            break
        else:
            print(f"  ⚠  {label} failed ({elapsed:.0f}s). Trying next DOCX fallback…")

    if final_result:
        r, elapsed = final_result
        shutil.copy2(src_docx, dst_docx)
        sz_mb = os.path.getsize(dst_docx) / 1e6
        print(f"  ✓  Saved → {dst_docx}  ({sz_mb:.1f} MB)")
        print(f"  ✓  DOCX method: {final_label}")
        print("  ℹ  DOCX is an editable conversion; verify equations, algorithms, wide tables, and references manually.")

        if r.stderr.strip():
            warn_lines = [l for l in r.stderr.splitlines() if l.strip()]
            warn_path = os.path.join(COMPILE_DIR, f"{MAIN_STEM}_pandoc_warnings.txt")
            dst_warn_path = os.path.join(LATEX_DIR, f"{MAIN_STEM}_pandoc_warnings.txt")
            with open(warn_path, "w", encoding="utf-8") as f:
                f.write("PANDOC WARNINGS REPORT — TurkQuish DOCX export\n")
                f.write(f"Generated : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Method    : {final_label}\n")
                f.write("=" * 70 + "\n\n")
                f.write(r.stderr)
            shutil.copy2(warn_path, dst_warn_path)

            print("  Pandoc notes/warnings:")
            for l in warn_lines[:8]:
                print(f"     - {l}")
            if len(warn_lines) > 8:
                print(f"     ... {len(warn_lines)-8} more warning line(s)")
            print(f"  ℹ  Full Pandoc warning report saved → {dst_warn_path}")

            if "Could not convert TeX math" in r.stderr:
                print("  ⚠  Some equation(s) may remain as raw TeX in the DOCX. Search the warning report for the exact location.")
    else:
        print("  ✗  DOCX not produced by Pandoc after all fallbacks.")
        print("  PDF saving is unaffected; fix the Pandoc issue only if you need DOCX.")

print("\n" + "="*66 + "\nDONE\n")
