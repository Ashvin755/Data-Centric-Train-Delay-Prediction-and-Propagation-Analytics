"""
Regenerate the two raster figures used in the JRTPM manuscript at
submission-grade resolution.

The plotting logic is a faithful transcription of the corresponding cells in
`notebooks/first.ipynb`:

  * train_18238_station_delay_30d.png  <- 30-day halt-only Plotly line chart
  * alpha_profile_plot.png             <- matplotlib alpha profile

Elsevier artwork guidance (Guide for authors, "Formats"):
  * bitmapped line drawings : TIFF/JPG/PNG at 1000 dpi
    (min. width 3543 px single column, 7480 px full page)
  * charts                 : XLS/XLSX preferred, otherwise high-res raster

Both figures are rendered here as vector PDFs (the preferred format for line
art) AND as high-DPI PNG fallbacks.

Run from the repository root:
    python docs/sati_conference/elsevier/regen_figures.py
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = REPO_ROOT / "dataset" / "supabase" / "rail_data_rows_27march.csv"
STATICS_DIR = REPO_ROOT / "docs" / "statics"
OUT_DIR = Path(__file__).resolve().parent

TRAIN_NO = 18238
ALPHA_THRESHOLD_MIN = 1.0

TRAIN_NAME = "Chhattisgarh Express (PT) (18238)"

# Elsevier artwork guidance (Guide for authors, "Formats"):
#   * vector drawings        : EPS or PDF, with fonts embedded
#   * bitmapped line drawings : TIFF/JPG/PNG at 1000 dpi
#     (min. width 3543 px single column, 7480 px full page)
#   * charts                 : XLS/XLSX preferred, otherwise high-res raster
#
# Both figures are therefore produced as vector PDFs, which is the preferred
# format for line art and sidesteps resolution limits entirely. Raster PNG
# copies are also emitted for convenience, but they are NOT what the
# manuscript includes.
#
# Both figures are drawn with matplotlib rather than Plotly. Plotly could not
# produce a usable static artefact on this machine: Kaleido's direct PDF export
# silently rasterises to a full-page bitmap, and its SVG output takes ~108 s to
# convert and renders the page background black. See make_30d_plot().
FIGSIZE_30D = (18.0, 7.0)
FIGSIZE_ALPHA = (18.0, 7.0)

# Raster-fallback sizing only. The vector PDF is the real deliverable, so the
# PNGs are kept modest rather than spending minutes on a ~7500 px export that
# nothing consumes. 18 in * 200 -> ~3600 px, which clears Elsevier's
# single-column minimum of 3543 px.
PNG_DPI = 200


# --------------------------------------------------------------------------
# Data loading (mirrors notebook cell 1 + 2)
#
# Parsing the CSV and converting the four Unix-timestamp columns to IST is the
# expensive part of a rebuild, and it does not change when only the plotting
# changes. The prepared frame is therefore cached on disk and reused; the
# cache is invalidated automatically when the source CSV or any static-route
# JSON is newer.
#
# Pickle is used rather than Parquet because the prepared frame contains
# timezone-aware datetime columns, and pickle round-trips those exactly
# without requiring an extra engine (pyarrow/fastparquet) to be installed.
# The cache is a derived artefact and is git-ignored; deleting it is safe.
# --------------------------------------------------------------------------
CACHE_PATH = OUT_DIR / ".cache" / "rail_frame_18238.pkl"


def load_frame(use_cache: bool = True) -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    # Fast path: reuse the prepared frame if the cache is current.
    if use_cache and CACHE_PATH.exists():
        newest_src = max(
            DATA_PATH.stat().st_mtime,
            *(p.stat().st_mtime for p in STATICS_DIR.glob("*.json")),
        )
        if CACHE_PATH.stat().st_mtime >= newest_src:
            with open(CACHE_PATH, "rb") as fh:
                df = pickle.load(fh)
            print(f"Loaded {len(df):,} rows from cache ({CACHE_PATH.name})")
            return df

    df = pd.read_csv(DATA_PATH)
    df = df.drop(
        columns=["distance_from_origin_km", "created_at", "updated_at"],
        errors="ignore",
    )

    unix_time_cols = [
        "scheduled_arrival",
        "scheduled_departure",
        "actual_arrival",
        "actual_departure",
    ]
    unix_time_cols = [c for c in unix_time_cols if c in df.columns]

    for c in unix_time_cols:
        parsed_utc = pd.to_datetime(df[c], unit="s", errors="coerce", utc=True)
        df[f"{c}_ist"] = parsed_utc.dt.tz_convert("Asia/Kolkata")

    # Event-time axis: prefer actual_departure, then actual_arrival, etc.
    for candidate in [
        "actual_departure",
        "actual_arrival",
        "scheduled_departure",
        "scheduled_arrival",
    ]:
        if candidate in unix_time_cols and df[f"{candidate}_ist"].notna().any():
            time_col = f"{candidate}_ist"
            break
    else:
        raise ValueError("No usable timestamp column found.")

    df["_event_time"] = df[time_col]
    df = df.dropna(subset=["_event_time"]).sort_values("_event_time").reset_index(drop=True)

    if "journey_date" in df.columns:
        df["journey_date"] = pd.to_datetime(df["journey_date"], errors="coerce").dt.date

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "wb") as fh:
        pickle.dump(df, fh, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"Loaded {len(df):,} rows; event-time axis = {time_col}; cache written")
    return df


def halt_order(train_no: int) -> list[str]:
    """Halt-only station sequence from the static route JSON."""
    path = STATICS_DIR / f"{train_no}_static.json"
    if not path.exists():
        raise FileNotFoundError(f"Static route file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        static_json = json.load(f)

    route_rows = static_json.get("data", {}).get("route", [])
    halt_route = [r for r in route_rows if int(r.get("isHalt", 0)) == 1]
    order = [
        r.get("stationCode")
        for r in sorted(halt_route, key=lambda x: x.get("sequence", 10**9))
        if r.get("stationCode")
    ]
    if not order:
        raise ValueError(f"No halt stations found for train {train_no}.")
    return order


def build_30d_frame(df: pd.DataFrame, train_no: int, order: list[str]) -> pd.DataFrame:
    """Halt-only rows in the latest 30-day window, deduped and full-grid expanded."""
    m = df[df["train_no"] == train_no].copy()
    m = m.dropna(
        subset=["delay_departure_minutes", "station_code", "_event_time", "journey_date"]
    )
    if m.empty:
        raise ValueError(f"No rows for train {train_no} after filtering.")

    m["journey_date"] = pd.to_datetime(m["journey_date"], errors="coerce").dt.date
    m = m.dropna(subset=["journey_date"])

    latest = m["journey_date"].max()
    start = latest - pd.Timedelta(days=29)
    m = m[(m["journey_date"] >= start) & (m["journey_date"] <= latest)].copy()
    if m.empty:
        raise ValueError(f"No records for {train_no} in the selected 30-day window.")

    m = m[m["station_code"].isin(order)].copy()
    if m.empty:
        raise ValueError(f"No halt-station records for {train_no} in the window.")

    m = m.sort_values(["journey_date", "station_code", "id"])
    m = m.drop_duplicates(subset=["journey_date", "station_code"], keep="last")

    journey_dates = sorted(m["journey_date"].unique())
    full_index = pd.MultiIndex.from_product(
        [journey_dates, order], names=["journey_date", "station_code"]
    )
    out = (
        m.set_index(["journey_date", "station_code"])[["delay_departure_minutes", "id"]]
        .reindex(full_index)
        .reset_index()
    )
    out["station_code"] = pd.Categorical(
        out["station_code"], categories=order, ordered=True
    )
    out = out.sort_values(["journey_date", "station_code"])
    out["journey_date"] = out["journey_date"].astype(str)
    return out


# --------------------------------------------------------------------------
# Figure 1: 30-day halt-station vs departure delay
# --------------------------------------------------------------------------
def make_30d_plot(df: pd.DataFrame, write_png: bool = True) -> Path:
    """
    Render the 30-day halt-station delay chart as a true vector PDF.

    The notebook renders this figure with Plotly for interactivity, but Plotly
    cannot produce a usable static artefact here:

    * Kaleido's direct PDF export silently rasterises into a single full-page
      bitmap, so the figure is neither vector nor resolution independent.
    * Kaleido's SVG export is vector, but converting it with svglib takes
      ~108 s for this figure and renders the page background solid black,
      because svglib resolves SVG's unset fill to PDF's black default on the
      clip-path rects that Plotly emits. The resulting PDF still *looks*
      structurally valid, which is what made the defect easy to ship.

    Matplotlib is already the tool used for the alpha figure, writes a genuine
    vector PDF directly, renders a white background, and completes in well
    under a second. The visual result is equivalent: one line per journey
    date, shared categorical station axis, static route order.
    """
    order = halt_order(TRAIN_NO)
    month_df = build_30d_frame(df, TRAIN_NO, order)

    present = set(month_df["station_code"].dropna().unique())
    missing = [s for s in order if s not in present]

    journey_dates = sorted(month_df["journey_date"].unique())
    xpos = {s: i for i, s in enumerate(order)}

    cmap = plt.get_cmap("turbo")
    fig, ax = plt.subplots(figsize=FIGSIZE_30D, dpi=100)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    for i, jd in enumerate(journey_dates):
        sub = month_df[month_df["journey_date"] == jd]
        xs = [xpos.get(s, np.nan) for s in sub["station_code"]]
        ys = sub["delay_departure_minutes"].to_numpy(dtype=float)
        ax.plot(
            xs, ys,
            color=cmap(i / max(len(journey_dates) - 1, 1)),
            linewidth=0.9,
            alpha=0.85,
            marker="o",
            markersize=2.0,
            label=jd,
        )

    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order, rotation=70, ha="right", fontsize=7)
    ax.set_xlim(-0.5, len(order) - 0.5)
    ax.set_xlabel("Station (halt-only, static route order)", fontsize=10)
    ax.set_ylabel("Delay Departure (minutes)", fontsize=10)
    ax.set_title(
        f"{TRAIN_NAME} - Halt Station vs Departure Delay (30 Days)\n"
        f"Journey dates: {journey_dates[0]} to {journey_dates[-1]}",
        fontsize=12,
    )
    ax.grid(alpha=0.25)
    ax.legend(
        title="Journey Date",
        ncol=2,
        fontsize=6.5,
        title_fontsize=7.5,
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        frameon=False,
    )
    fig.tight_layout()

    # Vector PDF: the submission artefact, resolution independent.
    pdf_path = OUT_DIR / "train_18238_station_delay_30d.pdf"
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight", facecolor="white")
    print(f"  wrote {pdf_path.name} (vector)")

    png_path = OUT_DIR / "train_18238_station_delay_30d.png"
    if write_png:
        fig.savefig(
            png_path, format="png", dpi=PNG_DPI, bbox_inches="tight",
            facecolor="white",
        )
        print(f"  wrote {png_path.name} (dpi={PNG_DPI}, raster fallback)")

    plt.close(fig)

    print(f"  journeys plotted: {len(journey_dates)}")
    print(f"  halt stations: {len(order)}; missing from window: {len(missing)}")
    if missing:
        print(f"  missing: {missing}")
    return png_path


# --------------------------------------------------------------------------
# Figure 2: alpha profile
# --------------------------------------------------------------------------
def compute_alpha(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    order = halt_order(TRAIN_NO)
    seq_map = {s: i + 1 for i, s in enumerate(order)}

    m = df[df["train_no"] == TRAIN_NO].copy()
    m = m.dropna(
        subset=["delay_departure_minutes", "station_code", "_event_time", "journey_date"]
    )
    m["journey_date"] = pd.to_datetime(m["journey_date"], errors="coerce").dt.date
    m = m.dropna(subset=["journey_date"])

    latest = m["journey_date"].max()
    start = latest - pd.Timedelta(days=29)
    m = m[(m["journey_date"] >= start) & (m["journey_date"] <= latest)].copy()
    m = m[m["station_code"].isin(order)].copy()
    m = m.sort_values(["journey_date", "station_code", "id"])
    m = m.drop_duplicates(subset=["journey_date", "station_code"], keep="last")
    m["seq"] = m["station_code"].map(seq_map)
    m = m.dropna(subset=["seq"]).copy()
    m["seq"] = m["seq"].astype(int)

    pair_rows = []
    for journey_date_value, g in m.groupby("journey_date"):
        gg = g.sort_values("seq")[["station_code", "seq", "delay_departure_minutes"]].copy()
        gg["station_to"] = gg["station_code"].shift(-1)
        gg["seq_to"] = gg["seq"].shift(-1)
        gg["delay_to"] = gg["delay_departure_minutes"].shift(-1)
        gg = gg.dropna(subset=["station_to", "delay_departure_minutes", "delay_to"])
        gg = gg[(gg["seq_to"] - gg["seq"]) == 1].copy()
        if gg.empty:
            continue

        gg["delta_delay_min"] = gg["delay_to"] - gg["delay_departure_minutes"]
        for _, row in gg.iterrows():
            pair_rows.append(
                {
                    "journey_date": journey_date_value,
                    "station_from": row["station_code"],
                    "station_to": row["station_to"],
                    "seq_from": int(row["seq"]),
                    "seq_to": int(row["seq_to"]),
                    "delta_delay_min": float(row["delta_delay_min"]),
                }
            )

    pairs = pd.DataFrame(pair_rows)
    if pairs.empty:
        raise ValueError("No valid adjacent station-pair deltas found.")

    def _mad(values: pd.Series) -> float:
        med = float(values.median())
        return float((values - med).abs().median())

    stats = (
        pairs.groupby(["station_from", "station_to", "seq_from", "seq_to"], as_index=False)
        .agg(
            n_journeys=("delta_delay_min", "size"),
            alpha_median_min=("delta_delay_min", "median"),
            alpha_mean_min=("delta_delay_min", "mean"),
            alpha_std_min=("delta_delay_min", "std"),
            alpha_q25_min=("delta_delay_min", lambda s: s.quantile(0.25)),
            alpha_q75_min=("delta_delay_min", lambda s: s.quantile(0.75)),
            alpha_mad_min=("delta_delay_min", _mad),
        )
    )
    stats["alpha_iqr_min"] = stats["alpha_q75_min"] - stats["alpha_q25_min"]
    stats["pair_label"] = stats["station_from"] + " -> " + stats["station_to"]

    template = pd.DataFrame(
        {
            "station_from": order[:-1],
            "station_to": order[1:],
            "seq_from": np.arange(1, len(order)),
            "seq_to": np.arange(2, len(order) + 1),
        }
    )
    template["pair_label"] = template["station_from"] + " -> " + template["station_to"]

    full = template.merge(
        stats,
        on=["station_from", "station_to", "seq_from", "seq_to", "pair_label"],
        how="left",
    )
    journey_count = m["journey_date"].nunique()
    full["coverage_ratio"] = full["n_journeys"] / journey_count

    print(
        f"  window: {start} to {latest} ({journey_count} journey dates); "
        f"halt stations: {len(order)}; expected pairs: {len(order) - 1}"
    )
    return full, full.dropna(subset=["alpha_median_min", "alpha_mean_min"]).copy()


def make_alpha_plot(rankable: pd.DataFrame, write_png: bool = True) -> Path:
    rankable = rankable.sort_values("seq_from").reset_index(drop=True)

    x = rankable["seq_from"].values
    median_vals = rankable["alpha_median_min"].values
    mean_vals = rankable["alpha_mean_min"].values
    q25 = rankable["alpha_q25_min"].values
    q75 = rankable["alpha_q75_min"].values

    fig, ax = plt.subplots(figsize=FIGSIZE_ALPHA, dpi=100)
    ax.plot(x, median_vals, marker="o", linewidth=2, label="Median alpha", color="#1f77b4")
    ax.plot(x, mean_vals, marker="x", linewidth=1.5, label="Mean alpha",
            color="#ff7f0e", alpha=0.9)
    ax.fill_between(x, q25, q75, color="#1f77b4", alpha=0.18, label="Median IQR band")

    ax.axhline(0, color="black", linewidth=1, linestyle="--", alpha=0.7)
    ax.axhline(1, color="green", linewidth=1, linestyle=":", alpha=0.9,
               label="+1 min threshold")
    ax.axhline(-1, color="red", linewidth=1, linestyle=":", alpha=0.9,
               label="-1 min threshold")

    ax.set_title("Train 18238 - Adjacent Halt Pair Alpha Profile (30-day window)")
    ax.set_xlabel("Adjacent Pair Position in Static Halt Order")
    ax.set_ylabel("Alpha (delay_to - delay_from), minutes")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.25)
    fig.tight_layout()

    pdf_path = OUT_DIR / "alpha_profile_plot.pdf"
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
    print(f"  wrote {pdf_path.name}")

    png_path = OUT_DIR / "alpha_profile_plot.png"
    if write_png:
        fig.savefig(png_path, format="png", dpi=PNG_DPI, bbox_inches="tight")
        print(f"  wrote {png_path.name} (dpi={PNG_DPI}, raster fallback)")
    plt.close(fig)
    return png_path


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
def validate_pdf(path: Path) -> None:
    """
    Fail loudly if an exported figure PDF is not a clean, white-background,
    non-empty, genuinely vector render.

    Two distinct defects have been caught by this function:

    * a black page background, where every structural check still passed;
    * a fully rasterised PDF, where Kaleido silently produced a single
      3000x1300 bitmap covering the whole page instead of vector operators.

    Both are invisible to "is the file a valid PDF" style checks, so the
    background corners are sampled and the vector/raster ratio is asserted.
    """
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"{path.name}: missing or empty")

    header = path.read_bytes()[:5]
    if header != b"%PDF-":
        raise RuntimeError(f"{path.name}: bad header {header!r}")

    try:
        import pymupdf
    except ImportError:
        print(f"  [warn] {path.name}: PyMuPDF not installed, skipped render check")
        return

    with pymupdf.open(path) as doc:
        if doc.page_count == 0:
            raise RuntimeError(f"{path.name}: no pages")
        page = doc[0]
        text = page.get_text().strip()
        if not text:
            raise RuntimeError(f"{path.name}: page contains no text (blank render)")

        # Vector check: a real vector figure has far more path operators than
        # embedded images, and must not be one full-page bitmap.
        vectors = len(page.get_drawings())
        images = page.get_images(full=True)
        page_area = page.rect.get_area()
        for im in images:
            for r in page.get_image_rects(im[0]):
                if r.get_area() > 0.9 * page_area:
                    raise RuntimeError(
                        f"{path.name}: page is a single full-page bitmap "
                        f"({im[2]}x{im[3]} px) - this is raster, not vector"
                    )
        if vectors < 20 and not images:
            raise RuntimeError(
                f"{path.name}: only {vectors} vector paths and no images - "
                "the figure appears empty"
            )

        pix = page.get_pixmap(dpi=40)
        corners = [
            pix.pixel(2, 2),
            pix.pixel(pix.width - 3, 2),
            pix.pixel(2, pix.height - 3),
            pix.pixel(pix.width - 3, pix.height - 3),
        ]
        if all(sum(px[:3]) < 60 for px in corners):
            raise RuntimeError(
                f"{path.name}: page background renders BLACK in all corners "
                f"(corners={corners[:2]}...) - refusing to ship this file"
            )
        if not all(px[0] > 200 and px[1] > 200 and px[2] > 200 for px in corners):
            raise RuntimeError(
                f"{path.name}: page background is not white (corners={corners})"
            )

    print(
        f"  [ok] {path.name}: valid PDF, white background, "
        f"{vectors} vector paths, {len(images)} images, {len(text)} chars"
    )


# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore the prepared-frame Parquet cache and re-read the CSV.",
    )
    ap.add_argument(
        "--only",
        choices=["30d", "alpha"],
        help="Rebuild only one figure.",
    )
    ap.add_argument(
        "--no-png",
        action="store_true",
        help="Skip the convenience raster copies (PDF only).",
    )
    args = ap.parse_args()

    print("Regenerating manuscript figures at submission resolution.\n")
    df = load_frame(use_cache=not args.no_cache)

    if args.only in (None, "30d"):
        print("[1/2] 30-day halt-station delay plot")
        make_30d_plot(df, write_png=not args.no_png)

    if args.only in (None, "alpha"):
        print("\n[2/2] alpha profile plot")
        _, rankable = compute_alpha(df)
        make_alpha_plot(rankable, write_png=not args.no_png)

    print("\nValidating exported PDFs...")
    for stem in ("train_18238_station_delay_30d", "alpha_profile_plot"):
        validate_pdf(OUT_DIR / f"{stem}.pdf")

    print("\nDone.")


if __name__ == "__main__":
    main()
