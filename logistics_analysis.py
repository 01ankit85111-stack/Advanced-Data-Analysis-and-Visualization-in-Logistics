"""
Week 3 Task: Advanced Data Analysis and Visualization in Logistics
This version DISPLAYS every graph and also saves it in the charts/ folder.
Install once:  pip install pandas numpy matplotlib seaborn
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt      # no "Agg" backend, so graphs can open
import seaborn as sns

# If you use Jupyter Notebook / Google Colab, uncomment the next line:
# %matplotlib inline

np.random.seed(42)
sns.set_theme(style="whitegrid", palette="deep")
OUT = "charts/"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------
# 1. DATA SIMULATION
# ---------------------------------------------------------------
N = 1500
modes = np.random.choice(["Road", "Rail", "Air", "Sea"], N, p=[0.55, 0.15, 0.12, 0.18])
regions = np.random.choice(["North", "South", "East", "West", "Central"], N)
carriers = np.random.choice(["FastTrack", "SwiftMove", "CargoPlus", "BlueLine"], N)

dist_base = {"Road": 450, "Rail": 900, "Air": 1800, "Sea": 2500}
distance = np.array([max(50, np.random.normal(dist_base[m], dist_base[m] * 0.35)) for m in modes])
volume = np.random.gamma(shape=3.0, scale=180, size=N)            # kg
speed = {"Road": 55, "Rail": 45, "Air": 600, "Sea": 30}           # km/h effective
handling = {"Road": 4, "Rail": 10, "Air": 8, "Sea": 36}           # hrs
rate = {"Road": 0.9, "Rail": 0.55, "Air": 3.4, "Sea": 0.35}       # cost per km

delivery_time = np.array([distance[i] / speed[modes[i]] + handling[modes[i]] +
                          np.random.exponential(3) for i in range(N)])
cost = np.array([distance[i] * rate[modes[i]] + volume[i] * 0.45 +
                 np.random.normal(0, 60) for i in range(N)])
cost = np.clip(cost, 40, None)
carrier_delay = {"FastTrack": 0.10, "SwiftMove": 0.18, "CargoPlus": 0.25, "BlueLine": 0.14}
delay_prob = np.array([carrier_delay[c] for c in carriers]) + (distance > 1500) * 0.08
delayed = np.random.rand(N) < delay_prob
delivery_time = delivery_time + delayed * np.random.uniform(4, 20, N)
dates = pd.to_datetime("2025-01-01") + pd.to_timedelta(np.random.randint(0, 365, N), unit="D")

df = pd.DataFrame({
    "shipment_id": [f"SH{1000+i}" for i in range(N)],
    "date": dates, "region": regions, "carrier": carriers, "mode": modes,
    "distance_km": distance.round(1), "volume_kg": volume.round(1),
    "delivery_time_hrs": delivery_time.round(1),
    "transport_cost": cost.round(2), "delayed": delayed.astype(int),
})
df["cost_per_kg"] = (df.transport_cost / df.volume_kg).round(3)
df["month"] = df.date.dt.to_period("M").astype(str)

# add missing values, then clean them
df.loc[df.sample(20, random_state=1).index, "volume_kg"] = np.nan
df["volume_kg"] = df["volume_kg"].fillna(df.groupby("mode")["volume_kg"].transform("median"))
df.to_csv("logistics_dataset.csv", index=False)

# ---------------------------------------------------------------
# 2. EXPLORATORY DATA ANALYSIS
# ---------------------------------------------------------------
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
print(df.head()); print(df.info())
num = ["distance_km", "volume_kg", "delivery_time_hrs", "transport_cost", "cost_per_kg"]
desc = df[num].describe().T
desc["median"] = df[num].median()
desc["skew"] = df[num].skew()
print("\n--- Summary statistics ---\n", desc.round(2))
corr = df[num + ["delayed"]].corr()
print("\n--- Correlation matrix ---\n", corr.round(2))
print("\n--- Mean by mode ---\n", df.groupby("mode")[["delivery_time_hrs", "transport_cost"]].mean().round(2))
print("\n--- Delay rate by carrier ---\n", df.groupby("carrier").delayed.mean().round(3))
print("\n--- Delay rate by region ---\n", df.groupby("region").delayed.mean().round(3))

# ---------------------------------------------------------------
# 3. VISUALIZATIONS (each one is shown AND saved)
# ---------------------------------------------------------------
def show_and_save(filename):
    plt.tight_layout()
    plt.savefig(OUT + filename, dpi=150)   # save image for your DOC file
    plt.show()                             # display on screen

# Fig 1 Histogram + KDE: delivery time distribution
plt.figure(figsize=(8, 5))
sns.histplot(df.delivery_time_hrs, bins=40, kde=True, color="#2a6fdb")
plt.axvline(df.delivery_time_hrs.mean(), color="red", ls="--", label=f"Mean {df.delivery_time_hrs.mean():.1f}h")
plt.axvline(df.delivery_time_hrs.median(), color="green", ls="--", label=f"Median {df.delivery_time_hrs.median():.1f}h")
plt.title("Distribution of Delivery Time"); plt.xlabel("Delivery time (hours)"); plt.legend()
show_and_save("fig1_delivery_hist.png")

# Fig 2 Boxplot: cost by transport mode
plt.figure(figsize=(8, 5))
sns.boxplot(data=df, x="mode", y="transport_cost", order=["Road", "Rail", "Sea", "Air"])
plt.title("Transportation Cost by Mode"); plt.xlabel("Mode"); plt.ylabel("Cost")
show_and_save("fig2_cost_box.png")

# Fig 3 Scatter + regression: distance vs cost
plt.figure(figsize=(8, 5))
sns.scatterplot(data=df, x="distance_km", y="transport_cost", hue="mode", alpha=0.6)
sns.regplot(data=df, x="distance_km", y="transport_cost", scatter=False, color="black", line_kws={"lw": 1.5})
plt.title("Distance vs Transportation Cost"); plt.xlabel("Distance (km)"); plt.ylabel("Cost")
show_and_save("fig3_distance_cost.png")

# Fig 4 Correlation heatmap
plt.figure(figsize=(7, 5.5))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
plt.title("Correlation Heatmap")
show_and_save("fig4_heatmap.png")

# Fig 5 Line chart: monthly shipments and average cost
m = df.groupby("month").agg(shipments=("shipment_id", "count"), avg_cost=("transport_cost", "mean")).reset_index()
fig, ax1 = plt.subplots(figsize=(9, 5))
ax1.plot(m.month, m.shipments, marker="o", color="#2a6fdb"); ax1.set_ylabel("Shipments", color="#2a6fdb")
ax2 = ax1.twinx(); ax2.plot(m.month, m.avg_cost, marker="s", color="#e67e22"); ax2.set_ylabel("Avg cost", color="#e67e22")
ax1.set_title("Monthly Shipments and Average Cost (2025)"); plt.setp(ax1.get_xticklabels(), rotation=45)
show_and_save("fig5_monthly_trend.png")

# Fig 6 Bar chart: delay rate by carrier
plt.figure(figsize=(8, 5))
cd = df.groupby("carrier").delayed.mean().sort_values() * 100
sns.barplot(x=cd.index, y=cd.values, color="#c0392b")
for i, v in enumerate(cd.values):
    plt.text(i, v + 0.3, f"{v:.1f}%", ha="center")
plt.title("Delay Rate by Carrier"); plt.ylabel("Delayed shipments (%)"); plt.xlabel("Carrier")
show_and_save("fig6_delay_carrier.png")

# Fig 7 Heatmap: avg delivery time by region and mode
pv = df.pivot_table(index="region", columns="mode", values="delivery_time_hrs", aggfunc="mean")
plt.figure(figsize=(7.5, 5))
sns.heatmap(pv, annot=True, fmt=".1f", cmap="YlOrRd")
plt.title("Avg Delivery Time (hrs): Region x Mode")
show_and_save("fig7_region_mode.png")

# ---------------------------------------------------------------
# 4. KEY INSIGHT METRICS
# ---------------------------------------------------------------
print("\nOverall delay rate:", round(df.delayed.mean() * 100, 1), "%")
print("Avg cost/kg by mode:\n", df.groupby("mode").cost_per_kg.mean().round(2))
print("Avg delivery time (delayed vs on-time):\n", df.groupby("delayed").delivery_time_hrs.mean().round(1))
q1, q3 = df.transport_cost.quantile(.25), df.transport_cost.quantile(.75)
print("Cost outliers (IQR rule):", int((df.transport_cost > q3 + 1.5 * (q3 - q1)).sum()))