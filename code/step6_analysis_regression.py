# -*- coding: utf-8 -*-
"""
Step 6（附加）/ 实证分析：描述统计、相关性、回归与稳健性、异质性
================================================================
模型设定（被解释变量：创新绩效 Patent = ln(1+专利授权量)）：

  (1) 混合 OLS ：Patent = α + β·Dig + γ·Controls + ε
  (2) 双向固定效应：Patent = α + β·Dig + γ·Controls + μ_i + λ_t + ε
      μ_i 企业固定效应，λ_t 年份固定效应，标准误在企业层面聚类。
  (3) 稳健性 a：以 Dig_share 替换 Dig
  (4) 稳健性 b：以熵权法 Dig_ent 替换 Dig
  (5) 稳健性 c：核心解释变量滞后一期 Dig_{t-1}
  (6) 异质性：按产权性质（国企/非国企）与行业技术属性分组

输出：
  data/output/descriptive_stats.csv
  data/output/regression_results.csv
  figures/fig1_dig_trend.png / fig2_distribution.png / fig3_top_keywords.png
================================================================
"""
import os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE_DIR, "data", "output")
FIG = os.path.join(BASE_DIR, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

CONTROLS_POOL = "size + lev + roa + growth + age + board + dual + soe"
# 双向固定效应下，企业固定效应会吸收 SOE，且 age=year-上市年份 与"企业FE+年份FE"完全共线，
# 故 FE 模型剔除 soe 与 age，避免设计矩阵奇异。
CONTROLS_FE = "size + lev + roa + growth + board + dual"
FE = "C(firm_id_c) + C(year_c)"

HIGH_TECH = ["信息技术", "高端制造", "医药生物"]


def fit(formula, data, cluster=True):
    m = smf.ols(formula, data=data).fit(
        cov_type="cluster", cov_kwds={"groups": data["firm_id"]}) if cluster \
        else smf.ols(formula, data=data).fit()
    return m


def star(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def main():
    df = pd.read_csv(os.path.join(OUT, "panel_data.csv"))

    # ---------- 描述性统计 ----------
    vars_ = ["Dig", "Dig_share", "Dig_ent", "Patent", "size", "lev", "roa",
             "growth", "age", "board", "dual", "soe"]
    desc = df[vars_].describe().T[["count", "mean", "std", "min", "50%", "max"]]
    desc.columns = ["样本量", "均值", "标准差", "最小值", "中位数", "最大值"]
    desc = desc.round(4)
    # 补 p25 / p75
    desc["P25"] = df[vars_].quantile(0.25).round(4)
    desc["P75"] = df[vars_].quantile(0.75).round(4)
    desc = desc[["样本量", "均值", "标准差", "最小值", "P25", "中位数", "P75", "最大值"]]
    desc.to_csv(os.path.join(OUT, "descriptive_stats.csv"), encoding="utf-8-sig")

    # ---------- 回归 ----------
    df["Dig_lag"] = df.groupby("firm_id")["Dig"].shift(1)
    df["firm_id_c"] = df["firm_id"].astype("category")
    df["year_c"] = df["year"].astype("category")

    models = {}
    models["(1) 混合OLS"] = fit(f"Patent ~ Dig + {CONTROLS_POOL}", df)
    models["(2) 双向固定效应"] = fit(f"Patent ~ Dig + {CONTROLS_FE} + {FE}", df)
    models["(3) 占比口径"] = fit(f"Patent ~ Dig_share + {CONTROLS_FE} + {FE}", df)
    models["(4) 熵权指数"] = fit(f"Patent ~ Dig_ent + {CONTROLS_FE} + {FE}", df)
    sub = df.dropna(subset=["Dig_lag"])
    models["(5) 滞后一期"] = fit(f"Patent ~ Dig_lag + {CONTROLS_FE} + {FE}", sub)

    # ---------- 异质性 ----------
    het = {}
    het["国企"] = fit(f"Patent ~ Dig + {CONTROLS_FE} + {FE}", df[df.soe == 1])
    het["非国企"] = fit(f"Patent ~ Dig + {CONTROLS_FE} + {FE}", df[df.soe == 0])
    het["高新技术行业"] = fit(f"Patent ~ Dig + {CONTROLS_FE} + {FE}",
                        df[df.industry.isin(HIGH_TECH)])
    het["其他行业"] = fit(f"Patent ~ Dig + {CONTROLS_FE} + {FE}",
                       df[~df.industry.isin(HIGH_TECH)])

    # ---------- 汇总表 ----------
    rows = []
    for name, m in {**models, **het}.items():
        core = [v for v in ("Dig", "Dig_share", "Dig_ent", "Dig_lag") if v in m.params]
        v = core[0]
        rows.append(dict(模型=name, 核心变量=v,
                         coefficient=round(m.params[v], 4),
                         std_err=round(m.bse[v], 4),
                         t_value=round(m.tvalues[v], 3),
                         p_value=round(m.pvalues[v], 4),
                         significance=star(m.pvalues[v]),
                         N=int(m.nobs),
                         R2=round(m.rsquared, 4)))
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(OUT, "regression_results.csv"),
               index=False, encoding="utf-8-sig")

    # 全模型文本摘要
    with open(os.path.join(OUT, "regression_summary.txt"), "w", encoding="utf-8") as fh:
        for name, m in {**models, **het}.items():
            fh.write(f"\n{'='*60}\n{name}\n{'='*60}\n")
            fh.write(str(m.summary()) + "\n")

    # ---------- 图 1：数字化转型年度趋势 ----------
    trend = df.groupby("year")["Dig"].agg(["mean", "std", "count"])
    plt.figure(figsize=(7, 4.2))
    plt.plot(trend.index, trend["mean"], marker="o", color="#c0392b", label="Dig 均值")
    plt.fill_between(trend.index, trend["mean"] - trend["std"] / np.sqrt(trend["count"]),
                     trend["mean"] + trend["std"] / np.sqrt(trend["count"]),
                     alpha=0.18, color="#c0392b")
    plt.title("图1  企业数字化转型程度(Dig)的年度趋势")
    plt.xlabel("年份"); plt.ylabel("Dig = ln(1+关键词总词频)")
    plt.grid(alpha=0.3, ls="--"); plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "fig1_dig_trend.png"), dpi=150)
    plt.close()

    # ---------- 图 2：分布 ----------
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].hist(df["Dig"], bins=35, color="#2980b9", alpha=0.85)
    axes[0].set_title("(a) Dig 分布"); axes[0].set_xlabel("Dig")
    axes[1].hist(df["Patent"], bins=35, color="#27ae60", alpha=0.85)
    axes[1].set_title("(b) 创新绩效 Patent 分布"); axes[1].set_xlabel("ln(1+专利数)")
    plt.suptitle("图2  核心变量分布")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig2_distribution.png"), dpi=150)
    plt.close()

    # ---------- 图 3：Top 关键词 ----------
    top = pd.read_csv(os.path.join(OUT, "top_keywords.csv")).head(15).iloc[::-1]
    plt.figure(figsize=(7, 5.2))
    plt.barh(top["keyword"], top["freq"], color="#8e44ad", alpha=0.85)
    plt.title("图3  高频数字化关键词 Top15")
    plt.xlabel("出现频次"); plt.tight_layout()
    plt.savefig(os.path.join(FIG, "fig3_top_keywords.png"), dpi=150)
    plt.close()

    print(res.to_string(index=False))
    print(f"\n[Step6] 回归结果 -> {os.path.join(OUT, 'regression_results.csv')}")
    return df, models, het, res


if __name__ == "__main__":
    main()
