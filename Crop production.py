import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

SELECTED_YEAR   = "2022-23" #modify according to the year of your desire after analysing the data in the website
SELECTED_SEASON = "Kharif"  #modify according to the year of your desire after analysing the data in the website

df = pd.read_csv("upag_apy.csv")
print("All columns:", df.columns.tolist())
print("All seasons:", df["Season"].unique())
print("Sample years:", df["Crop Year"].dropna().unique()[:10])

mask = (
    (df["Crop Year"].astype(str).str.strip() == SELECTED_YEAR) &
    (df["Season"].astype(str).str.strip()    == SELECTED_SEASON)
)
filtered = df[mask].copy()
print(f"\nRows after filter: {len(filtered)}")
print(filtered.head())

if filtered.empty:
    print("\n No data for that year/season. Available combinations:")
    print(df.groupby(["Crop Year", "Season"]).size().reset_index(name="rows").to_string())
    raise SystemExit("Change SELECTED_YEAR / SELECTED_SEASON above and re-run.")

CROP_COL  = "Crop"         
STATE_COL = "State"
METRIC_COL = "Metric"
VALUE_COL  = "Value"
CYCLE_COL  = "Estimation Cycle"

filtered[VALUE_COL] = pd.to_numeric(filtered[VALUE_COL], errors="coerce")

latest_cycle = (filtered[CYCLE_COL]
                .value_counts().index[0])   # most frequent = most complete
print(f"\nUsing estimation cycle: {latest_cycle}")
filtered = filtered[filtered[CYCLE_COL] == latest_cycle]

pivot = (filtered[filtered[STATE_COL] == "All India"]
         .pivot_table(index=CROP_COL, columns=METRIC_COL,
                      values=VALUE_COL, aggfunc="sum")
         .reset_index())
pivot.columns.name = None
print(f"\nPivoted shape: {pivot.shape}")
print(pivot.head())

state_df = (filtered[filtered[METRIC_COL] == "Production"]
            .groupby(STATE_COL)[VALUE_COL].sum()
            .sort_values(ascending=False)
            .drop("All India", errors="ignore"))

if "Production" in pivot.columns:
    top_crops = (pivot[[CROP_COL, "Production"]]
                 .dropna()
                 .sort_values("Production", ascending=False)
                 .head(10))

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(top_crops[CROP_COL][::-1],
                   top_crops["Production"][::-1],
                   color=sns.color_palette("YlGn_r", 10))
    ax.set_xlabel("Production (Lakh Tonnes)", fontsize=12)
    ax.set_title(f"Top 10 Crops by Production\n{SELECTED_SEASON} {SELECTED_YEAR} | {latest_cycle}",
                 fontsize=14, fontweight="bold")
    ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    sns.despine()
    plt.tight_layout()
    plt.savefig("plot1_top_crops.png", dpi=150)
    plt.show()

if not state_df.empty:
    top_states = state_df.head(10)

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(top_states.index[::-1], top_states.values[::-1],
                   color=sns.color_palette("Blues_r", 10))
    ax.set_xlabel("Production (Lakh Tonnes)", fontsize=12)
    ax.set_title(f"Top 10 States by Production\n{SELECTED_SEASON} {SELECTED_YEAR}",
                 fontsize=14, fontweight="bold")
    ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    sns.despine()
    plt.tight_layout()
    plt.savefig("plot2_top_states.png", dpi=150)
    plt.show()

trend = (df[
    (df[STATE_COL] == "All India") &
    (df[METRIC_COL] == "Production") &
    (df[CYCLE_COL] == "Final Estimate") &   # only final, not advance
    (df["Season"].astype(str).str.strip() == SELECTED_SEASON)
].copy())

trend[VALUE_COL]  = pd.to_numeric(trend[VALUE_COL], errors="coerce")
trend["Crop Year"] = trend["Crop Year"].astype(str).str.strip()
yearly = (trend.groupby("Crop Year")[VALUE_COL]
               .sum().reset_index()
               .sort_values("Crop Year"))

if not yearly.empty:
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(yearly["Crop Year"], yearly[VALUE_COL],
            marker="o", linewidth=2, color="#218144")
    ax.fill_between(yearly["Crop Year"], yearly[VALUE_COL],
                    alpha=0.15, color="#218144")
    ax.set_xlabel("Crop Year", fontsize=12)
    ax.set_ylabel("Production (Lakh Tonnes)", fontsize=12)
    ax.set_title(f"All India {SELECTED_SEASON} Production — Trend Over Years",
                 fontsize=14, fontweight="bold")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    ax.grid(alpha=0.3)
    sns.despine()
    plt.tight_layout()
    plt.savefig("plot3_trend.png", dpi=150)
    plt.show()

if "Area" in pivot.columns and "Yield" in pivot.columns and "Production" in pivot.columns:
    scatter_df = pivot[["Crop", "Area", "Yield", "Production"]].dropna()
    top20 = scatter_df.nlargest(20, "Production")

    fig, ax = plt.subplots(figsize=(11, 7))
    scatter = ax.scatter(
        top20["Area"], top20["Yield"],
        s=top20["Production"] / top20["Production"].max() * 1000,
        c=top20["Production"], cmap="YlOrRd",
        alpha=0.75, edgecolors="gray", linewidth=0.5
    )
    for _, row in top20.iterrows():
        ax.annotate(row["Crop"], (row["Area"], row["Yield"]),
                    fontsize=7, ha="center", va="bottom")
    plt.colorbar(scatter, label="Production (Lakh Tonnes)")
    ax.set_xlabel("Area (Lakh Ha)", fontsize=12)
    ax.set_ylabel("Yield (Kg/Ha)", fontsize=12)
    ax.set_title(f"Area vs Yield (bubble = Production)\n{SELECTED_SEASON} {SELECTED_YEAR}",
                 fontsize=14, fontweight="bold")
    ax.grid(alpha=0.3)
    sns.despine()
    plt.tight_layout()
    plt.savefig("plot4_scatter.png", dpi=150)
    plt.show()
    