"""
Generates 3 dashboard-style PNGs from the real UCI diabetic readmission
dataset, replicating the business logic already defined in sql/02_data_load.sql
(diag_category bucketing, readmitted_within_30) and sql/04_views.sql
(risk_tier, medication readmission grouping) so the visuals reflect this
project's actual numbers rather than placeholder data.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIRS = [
    ROOT / "powerbi" / "screenshots",
    ROOT.parent.parent / "pavi-portfolio-site" / "assets" / "images" / "powerbi",
]
for d in OUT_DIRS:
    d.mkdir(parents=True, exist_ok=True)

PURPLE = "#7c6af7"
PURPLE_SOFT = "#a89af9"
BG = "#f4f5fa"
CARD_BG = "#ffffff"
BORDER = "#e1e3ee"
TEXT = "#1c1e2b"
TEXT_MUTED = "#6b6f8a"
PALETTE = ["#7c6af7", "#4e95d9", "#4ab07d", "#f2a553", "#e27474", "#f7cc56", "#8b90a8"]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": BORDER,
    "axes.labelcolor": TEXT_MUTED,
    "xtick.color": TEXT_MUTED,
    "ytick.color": TEXT_MUTED,
    "text.color": TEXT,
})

AGE_ORDER = ["[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)",
             "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"]

DIAG_BUCKETS = [
    (390, 459, "Circulatory"),
    (460, 519, "Respiratory"),
    (520, 579, "Digestive"),
    (250, 251, "Diabetes"),
    (800, 999, "Injury/Poisoning"),
    (140, 239, "Neoplasms"),
]


def bucket_diag(code):
    num = pd.to_numeric(code, errors="coerce")
    if pd.isna(num):
        return "Other"
    for lo, hi, label in DIAG_BUCKETS:
        if lo <= num <= hi:
            return label
    return "Other"


def load_data():
    df = pd.read_csv(ROOT / "data" / "diabetic_readmission.csv")
    df["readmitted_within_30"] = (df["readmitted"] == "<30").astype(int)
    df["diag_category"] = df["diag_1"].apply(bucket_diag)
    df["age"] = pd.Categorical(df["age"], categories=AGE_ORDER, ordered=True)
    return df


def risk_tiers(df):
    g = df.groupby(["patient_nbr", "diag_category"], observed=True).agg(
        readmit_30d_count=("readmitted_within_30", "sum"),
        inpatient_visits=("number_inpatient", "sum"),
    ).reset_index()

    def tier(row):
        if row["readmit_30d_count"] >= 2 or row["inpatient_visits"] >= 5:
            return "High"
        if row["readmit_30d_count"] == 1 or 2 <= row["inpatient_visits"] <= 4:
            return "Medium"
        return "Low"

    g["risk_tier"] = g.apply(tier, axis=1)
    return g


def kpi_card(ax, x, y, w, h, value, label):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02",
                          linewidth=1, edgecolor=BORDER, facecolor=CARD_BG,
                          transform=ax.transAxes, clip_on=False)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h * 0.62, value, transform=ax.transAxes,
            ha="center", va="center", fontsize=26, fontweight="bold", color=PURPLE)
    ax.text(x + w / 2, y + h * 0.22, label, transform=ax.transAxes,
            ha="center", va="center", fontsize=10.5, color=TEXT_MUTED)


def style_ax(ax, title):
    ax.set_facecolor(CARD_BG)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(BORDER)
    ax.set_title(title, fontsize=12, fontweight="bold", color=TEXT, loc="left", pad=10)


def page1(df, risk_df):
    overall_rate = df["readmitted_within_30"].mean() * 100
    avg_los = df["time_in_hospital"].mean()
    high_risk_count = (risk_df["risk_tier"] == "High").sum()

    age_rate = df.groupby("age", observed=True)["readmitted_within_30"].mean() * 100
    diag_counts = df["diag_category"].value_counts()

    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    fig.suptitle("Hospital Readmission Risk — Executive Summary", fontsize=18,
                 fontweight="bold", color=TEXT, x=0.04, y=0.965, ha="left")
    fig.text(0.04, 0.93, "Diabetic patient admissions · UCI Diabetes 130-US Hospitals dataset (101,766 encounters)",
              fontsize=10.5, color=TEXT_MUTED)

    kpi_ax = fig.add_axes([0.04, 0.74, 0.92, 0.13])
    kpi_ax.axis("off")
    kpi_ax.set_xlim(0, 1)
    kpi_ax.set_ylim(0, 1)
    kpi_card(kpi_ax, 0.00, 0.0, 0.31, 1.0, f"{overall_rate:.1f}%", "30-Day Readmission Rate")
    kpi_card(kpi_ax, 0.345, 0.0, 0.31, 1.0, f"{avg_los:.1f} days", "Avg. Length of Stay")
    kpi_card(kpi_ax, 0.69, 0.0, 0.31, 1.0, f"{high_risk_count:,}", "High-Risk Patient Records")

    ax1 = fig.add_axes([0.06, 0.10, 0.46, 0.55])
    ax1.plot(range(len(age_rate)), age_rate.values, color=PURPLE, linewidth=2.5, marker="o", markersize=5)
    ax1.fill_between(range(len(age_rate)), age_rate.values, color=PURPLE, alpha=0.12)
    ax1.set_xticks(range(len(age_rate)))
    ax1.set_xticklabels([a.replace(")", "") for a in age_rate.index], rotation=40, ha="right", fontsize=9)
    ax1.set_ylabel("Readmission Rate %")
    style_ax(ax1, "Readmission Rate by Age Group")

    ax2 = fig.add_axes([0.58, 0.10, 0.38, 0.55])
    diag_counts = diag_counts.sort_values()
    bars = ax2.barh(diag_counts.index, diag_counts.values, color=PALETTE[:len(diag_counts)])
    ax2.set_xlabel("Admissions")
    style_ax(ax2, "Admissions by Diagnosis Category")

    save(fig, "page-1-executive-summary.png")


def page2(df):
    pivot = df.pivot_table(index="age", columns="diag_category",
                            values="readmitted_within_30", aggfunc="mean",
                            observed=True) * 100
    pivot = pivot.reindex(AGE_ORDER)

    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    fig.suptitle("Patient Risk Heatmap", fontsize=18, fontweight="bold", color=TEXT,
                 x=0.04, y=0.965, ha="left")
    fig.text(0.04, 0.93, "30-day readmission rate (%) by age group × diagnosis category",
              fontsize=10.5, color=TEXT_MUTED)

    ax = fig.add_axes([0.14, 0.10, 0.78, 0.74])
    im = ax.imshow(pivot.values, cmap="Purples", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([a.replace(")", "") for a in pivot.index])
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                         fontsize=8.5, color="white" if val > pivot.values[~np.isnan(pivot.values)].mean() else TEXT)
    ax.set_title("Highest risk: older age groups with Circulatory / Diabetes diagnoses",
                  fontsize=11, color=TEXT_MUTED, loc="left", pad=12)
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Readmission Rate %", color=TEXT_MUTED, fontsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)

    save(fig, "page-2-patient-risk-heatmap.png")


def page3(df):
    a1c = df.copy()
    a1c["A1Cresult"] = a1c["A1Cresult"].fillna("Not Tested")
    a1c_rate = a1c.groupby("A1Cresult", observed=True)["readmitted_within_30"].mean() * 100
    a1c_rate = a1c_rate.reindex(["Not Tested", "Norm", ">7", ">8"])

    insulin_rate = df.groupby("insulin", observed=True)["readmitted_within_30"].mean() * 100
    insulin_rate = insulin_rate.reindex(["No", "Down", "Steady", "Up"])

    bins = [0, 10, 15, 20, 25, 100]
    labels = ["1-10", "11-15", "16-20", "21-25", "26+"]
    df["med_bucket"] = pd.cut(df["num_medications"], bins=bins, labels=labels)
    med_rate = df.groupby("med_bucket", observed=True)["readmitted_within_30"].mean() * 100

    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    fig.suptitle("Clinical Trends", fontsize=18, fontweight="bold", color=TEXT,
                 x=0.04, y=0.965, ha="left")
    fig.text(0.04, 0.93, "30-day readmission rate (%) by A1C result, insulin status, and medication count",
              fontsize=10.5, color=TEXT_MUTED)

    ax1 = fig.add_axes([0.05, 0.10, 0.28, 0.74])
    ax1.bar(a1c_rate.index, a1c_rate.values, color=PALETTE[0])
    style_ax(ax1, "By A1C Result")
    ax1.set_ylabel("Readmission Rate %")

    ax2 = fig.add_axes([0.38, 0.10, 0.28, 0.74])
    ax2.bar(insulin_rate.index, insulin_rate.values, color=PALETTE[1])
    style_ax(ax2, "By Insulin Status")

    ax3 = fig.add_axes([0.71, 0.10, 0.25, 0.74])
    ax3.bar(med_rate.index.astype(str), med_rate.values, color=PALETTE[2])
    style_ax(ax3, "By Medication Count")

    save(fig, "page-3-clinical-trends.png")


def save(fig, filename):
    for d in OUT_DIRS:
        fig.savefig(d / filename, dpi=150, facecolor=BG, bbox_inches=None)
    plt.close(fig)
    print(f"saved {filename}")


def main():
    df = load_data()
    risk_df = risk_tiers(df)
    page1(df, risk_df)
    page2(df)
    page3(df)


if __name__ == "__main__":
    main()
