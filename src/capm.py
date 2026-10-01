# capm.py
import seaborn as sns
import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use('Agg')


stock_list = ["AAPL", "MSFT", "MU", "TSLA",
              "NFLX", "JPM", "COST", "LMT", "ABBV", "NEE"]
industry_map = {"AAPL": "Consumer Tech",
                "MSFT": "Software",
                "MU": "Semiconductor",
                "TSLA": "EV Auto",
                "NFLX": "Media",
                "JPM": "Banking",
                "COST": "Retail",
                "LMT": "Aerospace",
                "ABBV": "Healthcare",
                "NEE": "Utility"}

start_date = "2021-07-01"
end_date = "2026-07-01"
market_rate = "^GSPC"
ticker = stock_list + [market_rate]

# download data
raw_data = yf.download(ticker, start=start_date, end=end_date)
price_data = raw_data["Close"]
log_returns = np.log(price_data / price_data.shift(1))
log_returns = log_returns.replace([np.inf, -np.inf], np.nan).dropna()
log_returns = log_returns.dropna()
file_path = "/Users/athenazhao/Desktop/Athena Zhao Projects/CAPM_Project/outputs/all_data.xlsx"


# risk free rate
rf_daily = 0.04/252

# Calculation of all
results_table = []
plot_storage = []
rolling_beta_df = pd.DataFrame(index=log_returns.index)

for stock in stock_list:
    stock_excess = log_returns[stock]-rf_daily
    market_excess = log_returns[market_rate]-rf_daily
    stock_excess, market_excess = stock_excess.align(
        market_excess, join="inner")

    data = pd.DataFrame(
        {"stock": stock_excess, "market": market_excess}).dropna()
    data = data.dropna()

    x = data["market"]
    x_const = sm.add_constant(x)
    y = data["stock"]
    model = sm.OLS(y, x_const).fit()

    alpha = model.params["const"]
    beta = model.params["market"]
    r2 = model.rsquared
    p_alpha = model.pvalues["const"]
    p_beta = model.pvalues["market"]
    residuals = model.resid

    results_table.append({
        "Stock": stock,
        "Alpha": alpha,
        "Beta": beta,
        "R2": r2,
        "P_alpha": p_alpha,
        "P_beta": p_beta
    })

    plot_storage.append({
        "ticker": stock,
        "industry": industry_map[stock],
        "x": data["market"],
        "y": data["stock"],
        "alpha": alpha,
        "beta": beta,
        "residuals": residuals
    })

    # rolling beta time series
    roll_data = pd.DataFrame(
        {"market": market_excess, "stock": stock_excess}).dropna()
    window_length = 50
    beta_list = []
    for i in range(len(roll_data)):
        if i < window_length-1:
            beta_list.append(np.nan)
        else:
            window_slice = roll_data.iloc[i-window_length+1:i+1]
            window_slice = window_slice.dropna()
            if len(window_slice) == 0 or len(window_slice) < 5:
                beta_list.append(np.nan)
            else:
                x_win = window_slice["market"]
                x_const_win = sm.add_constant(x_win)
                y_win = window_slice["stock"]
                window_model = sm.OLS(y_win, x_const_win).fit()
                beta_list.append(window_model.params["market"])
    rolling_series = pd.Series(beta_list, index=roll_data.index)
    rolling_beta_df[stock] = rolling_series

    # summary
    print(f'\n=========={stock}In-sample regression summary=========')
    print(model.summary())

result_df = pd.DataFrame(results_table)

with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
    price_data.to_excel(writer, sheet_name="Price", index=True)
    log_returns.to_excel(writer, sheet_name="LogReturn", index=True)
    result_df.to_excel(writer, sheet_name="CAPM_Result", index=False)
    rolling_beta_df.to_excel(writer, sheet_name="RollingBeta", index=True)

print("ok,file_path")

# scatter plot of stock excess returns and market excess returns
plt.figure(figsize=(12, 7))
for info in plot_storage:
    plt.scatter(info["x"], info["y"], alpha=0.4, s=12, label=info["ticker"])
plt.title("All stocks scatter")
plt.xlabel("market excess return")
plt.ylabel("stock excess return")
plt.legend()
plt.tight_layout()
plt.savefig(
    "/Users/athenazhao/Desktop/Athena Zhao Projects/CAPM_Project/outputs/all_stock_scatter.png", dpi=300)
plt.close()


# regression line and scatter plot for each stock
fig_combo, axes_combo = plt.subplots(nrows=5, ncols=2, figsize=(14, 16))
axes_combo = axes_combo.flatten()

for idx, info in enumerate(plot_storage):
    ax = axes_combo[idx]
    ax.scatter(info["x"], info["y"], alpha=0.4, s=10)
    x_line = np.linspace(info["x"].min(), info["x"].max(), 100)
    y_line = info["alpha"]+info["beta"] * x_line
    ax.plot(x_line, y_line, c="red", lw=2, label=info["beta"])
    ax.set_title(f"{info['ticker']}CAPM Regression line & scatter plots")
    ax.set_xlabel("Market Excess Return")
    ax.set_ylabel("Stock Excess Return ")
    ax.legend()
    ax.grid(True, alpha=0.3)
plt.suptitle("Regression lines and residual plots for each stock", fontsize=16)
plt.tight_layout()
plt.savefig(
    "/Users/athenazhao/Desktop/Athena Zhao Projects/CAPM_Project/outputs/each_stock_scatter.png", dpi=300)
plt.close()

# residual plots
fig_resid, axes_resid = plt.subplots(5, 2, figsize=(14, 16))
axes_resid = axes_resid.flatten()
for idx, info in enumerate(plot_storage):
    ax = axes_resid[idx]
    ax.scatter(info["x"], info["residuals"], alpha=0.4, c="orange", s=8)
    ax.axhline(y=0, c="red", ls="--")
    ax.set_title(f"{info['ticker']} Residual Plot")
    ax.set_xlabel("Market Excess Return")
    ax.set_ylabel("Regression Residual")
    ax.grid(alpha=0.3)
plt.suptitle("CAPM Residual Plots", fontsize=16)
plt.tight_layout()
plt.savefig(
    "/Users/athenazhao/Desktop/Athena Zhao Projects/CAPM_Project/outputs/residual_plots.png", dpi=300)
plt.close()


# rolling beta chart
plt.figure(figsize=(13, 6))
for col in rolling_beta_df.columns:
    plt.plot(rolling_beta_df.index, rolling_beta_df[col], lw=1.2, label=col)
plt.axhline(y=1, color="black", linestyle="--", label="Market beta=1")
plt.title("50-day rolling market time series")
plt.xlabel("date")
plt.ylabel("rolling beta coefficients")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(
    "/Users/athenazhao/Desktop/Athena Zhao Projects/CAPM_Project/outputs/rolling_beta_charts.png", dpi=300)
plt.close()

# Beta Comparison Bar Chart
plt.figure(figsize=(12, 5))
plt.bar(result_df["Stock"], result_df["Beta"], label="stock_beta")
plt.axhline(y=1, color="blue", linestyle="--", label="Market Beta = 1")
plt.title("Cross-Industry Stock Market Exposure Beta")
plt.xlabel("Ticker")
plt.ylabel("Full sample beta")
plt.legend()
plt.tight_layout()
plt.savefig(
    "/Users/athenazhao/Desktop/Athena Zhao Projects/CAPM_Project/outputs/beta_comparison.png", dpi=300)
plt.close()


print("test end")
