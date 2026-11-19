"""
AIT mandatory assignment - Norway vs China after the 2010 Nobel Peace Prize
Ex-post structural gravity (PPML) on CEPII TradeProd TPe (V202606), Food sector.

Install once:  pip install pyfixest pandas matplotlib
Run:           python norway_china_nobel.py path/to/TPe_V202606.dta
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyfixest as pf

DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("TPe_V202606.dta")
OUT = Path("output")
OUT.mkdir(exist_ok=True)

YEARS = (2000, 2022)
FREEZE = (2011, 2016)        # sanctions period
AFTER_FROM = 2017            # after normalisation (Dec 2016)
REF_YEAR = 2009              # reference year in the event study
DIVERSION = ["VNM", "HKG"]   # possible re-routing destinations


# ---------------------------------------------------------------------------
# 1. Load TradeProd and keep the Food industry
# ---------------------------------------------------------------------------
def load(path: Path) -> pd.DataFrame:
    cols = ["year", "iso3_tp_o", "iso3_tp_d", "trade_comb", "industry"]
    if path.suffix == ".csv":
        df = pd.read_csv(path, usecols=cols)
    else:  # the .dta is ~850 MB: read only the needed columns, in chunks
        df = pd.concat(ch[ch["year"].between(*YEARS)] for ch in
                       pd.read_stata(path, columns=cols, chunksize=2_000_000))
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={"iso3_tp_o": "iso3_o", "iso3_tp_d": "iso3_d"})
    print("Columns:", list(df.columns))
    print("Industries:", df["industry"].unique()[:20])
    return df


def keep_food(df: pd.DataFrame) -> pd.DataFrame:
    ind = df["industry"].astype(str)
    food = ind.str.contains("food", case=False)
    if not food.any():
        raise SystemExit("No industry label contains 'Food' - check the printed "
                         "industry values and set the filter by hand.")
    print("Using industry:", ind[food].unique())
    return df[food]


# ---------------------------------------------------------------------------
# 2. Build the estimation sample and treatment variables
# ---------------------------------------------------------------------------
def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["year"].between(*YEARS)].copy()
    df = df.rename(columns={"trade_comb": "X"})
    df = df[["year", "iso3_o", "iso3_d", "X"]].dropna(subset=["X"])
    df["year"] = df["year"].astype(int)

    df["intl"] = (df["iso3_o"] != df["iso3_d"]).astype(int)
    nor_chn = (df["iso3_o"] == "NOR") & (df["iso3_d"] == "CHN")
    df["NOR_CHN"] = nor_chn.astype(int)
    df["freeze"] = (nor_chn & df["year"].between(*FREEZE)).astype(int)
    df["after"] = (nor_chn & (df["year"] >= AFTER_FROM)).astype(int)
    for c in DIVERSION:
        df[f"NOR_{c}_freeze"] = ((df["iso3_o"] == "NOR") & (df["iso3_d"] == c)
                                 & df["year"].between(*FREEZE)).astype(int)

    # International border x year: controls for globalisation (Yotov et al. ch. 1)
    for y in range(YEARS[0] + 1, YEARS[1] + 1):
        df[f"brdr_{y}"] = ((df["intl"] == 1) & (df["year"] == y)).astype(int)

    # Event-study dummies (NOR->CHN x year, excluding the reference year)
    for y in range(YEARS[0], YEARS[1] + 1):
        if y != REF_YEAR:
            df[f"ev_{y}"] = (nor_chn & (df["year"] == y)).astype(int)

    df["exp_year"] = df["iso3_o"] + "_" + df["year"].astype(str)
    df["imp_year"] = df["iso3_d"] + "_" + df["year"].astype(str)
    df["pair"] = df["iso3_o"] + "_" + df["iso3_d"]
    return df


# ---------------------------------------------------------------------------
# 3. Descriptive figure
# ---------------------------------------------------------------------------
def figure(df: pd.DataFrame) -> None:
    nor = df[(df["iso3_o"] == "NOR") & (df["intl"] == 1)].copy()
    nor["dest"] = np.where(nor["iso3_d"] == "CHN", "China", "Rest of world")
    s = nor.groupby(["dest", "year"])["X"].sum().unstack(0)
    idx = 100 * s / s.loc[REF_YEAR]
    ax = idx.plot(figsize=(8, 4.5))
    for x in (2010.8, 2016.95):
        ax.axvline(x, ls="--", c="grey")
    ax.set_ylabel(f"Norwegian food exports ({REF_YEAR} = 100)")
    ax.set_xlabel("")
    ax.set_title("Norway's food exports: China vs. rest of world")
    plt.tight_layout()
    plt.savefig(OUT / "fig1_nor_food_exports.png", dpi=200)
    plt.close()


# ---------------------------------------------------------------------------
# 4. Regressions
# ---------------------------------------------------------------------------
FE = "exp_year + imp_year + pair"
VCOV = {"CRV1": "pair"}


def pct(b: float) -> float:
    return 100 * (np.exp(b) - 1)


def main_regression(df: pd.DataFrame):
    brdr = " + ".join(c for c in df.columns if c.startswith("brdr_"))
    div = " + ".join(f"NOR_{c}_freeze" for c in DIVERSION)
    fit = pf.fepois(f"X ~ freeze + after + {div} + {brdr} | {FE}",
                    data=df, vcov=VCOV)
    tab = fit.tidy().loc[["freeze", "after"] + [f"NOR_{c}_freeze" for c in DIVERSION]]
    tab["effect_%"] = tab["Estimate"].apply(pct)
    print("\nMain PPML regression\n", tab.round(3))
    tab.round(3).to_csv(OUT / "table1_main.csv")
    return fit


def event_study(df: pd.DataFrame):
    brdr = " + ".join(c for c in df.columns if c.startswith("brdr_"))
    ev = [c for c in df.columns if c.startswith("ev_")]
    fit = pf.fepois(f"X ~ {' + '.join(ev)} + {brdr} | {FE}", data=df, vcov=VCOV)
    t = fit.tidy().loc[ev]
    t["year"] = [int(c[3:]) for c in t.index]
    t = pd.concat([t, pd.DataFrame({"Estimate": [0.0], "2.5%": [0.0],
                                    "97.5%": [0.0], "year": [REF_YEAR]})])
    t = t.sort_values("year")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.errorbar(t["year"], t["Estimate"],
                yerr=[t["Estimate"] - t["2.5%"], t["97.5%"] - t["Estimate"]],
                fmt="o", capsize=3)
    ax.axhline(0, c="black", lw=0.8)
    for x in (2010.5, 2016.5):
        ax.axvline(x, ls="--", c="grey")
    ax.set_ylabel("PPML coefficient, NOR→CHN (log points)")
    ax.set_title(f"Event study (reference year {REF_YEAR})")
    plt.tight_layout()
    plt.savefig(OUT / "fig2_event_study.png", dpi=200)
    plt.close()
    t.round(3).to_csv(OUT / "table2_event_study.csv")
    return fit


if __name__ == "__main__":
    raw = load(DATA)
    df = prepare(keep_food(raw))
    print(f"Sample: {len(df):,} flows, {df['pair'].nunique():,} pairs")
    figure(df)
    main_regression(df)
    event_study(df)
    print(f"\nFigures and tables saved in {OUT.resolve()}")
    # Placebo: change keep_food() to another industry (e.g. 'Machines') and rerun.
