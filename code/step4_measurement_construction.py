# -*- coding: utf-8 -*-
"""
Step 4 / 五步流水线之四：测度合成与指数构建
================================================================
把 Step 3 得到的关键词词频，合成"企业数字化转型程度"测度：

  · Dig      = ln(1 + 数字化转型关键词总词频)         ← 主测度（对数化，缓解右偏）
  · Dig_share= 关键词总词频 / 年报有效词数 × 100       ← 占比口径（稳健性）
  · Dig_ent  = 熵权法合成的五维综合指数               ← 多维度合成（稳健性）

熵权法公式：
  归一化  p_ij = x_ij / Σ_i x_ij
  信息熵  e_j  = -k Σ_i p_ij ln(p_ij),  k = 1/ln(n)
  权重    w_j  = (1 - e_j) / Σ_j (1 - e_j)
  综合指数 Dig_ent,i = Σ_j w_j · x*_ij  (x* 为极差标准化)

输出：
  data/output/panel_data.csv   企业-年份面板（含测度、控制变量、被解释变量）
  data/output/dig_weights.csv  熵权法各维度权重
================================================================
"""
import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE_DIR, "data", "raw")
OUT = os.path.join(BASE_DIR, "data", "output")
os.makedirs(OUT, exist_ok=True)

CATS = ["AI", "BD", "CC", "BC", "APP"]


def entropy_weights(X: np.ndarray):
    """输入 n×m 非负矩阵，返回 m 个权重与 n 维综合得分。"""
    n, m = X.shape
    P = X / X.sum(axis=0, keepdims=True)
    P = np.where(P <= 0, 1e-12, P)
    k = 1.0 / np.log(n)
    e = -k * (P * np.log(P)).sum(axis=0)
    d = 1.0 - e
    w = d / d.sum()
    Xs = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0) + 1e-12)
    score = Xs @ w
    return w, score


def main():
    freq = pd.read_csv(os.path.join(OUT, "keyword_frequency.csv"))
    fin = pd.read_csv(os.path.join(RAW, "firm_year_financials.csv"))
    prof = pd.read_csv(os.path.join(RAW, "firm_profile.csv"))

    df = freq.merge(fin, on=["firm_id", "year"], how="inner") \
             .merge(prof, on=["firm_id"], how="left")

    # 主测度：对数化总词频
    df["Dig"] = np.log1p(df["freq_total"])
    # 稳健性①：词频占比
    df["Dig_share"] = df["freq_total"] / df["n_tokens"] * 100
    # 稳健性②：熵权法五维综合指数
    W, score = entropy_weights(df[[f"freq_{c}" for c in CATS]].to_numpy(float))
    df["Dig_ent"] = score
    pd.DataFrame({"dimension": CATS, "entropy_weight": np.round(W, 4)}).to_csv(
        os.path.join(OUT, "dig_weights.csv"), index=False, encoding="utf-8-sig")

    # 被解释变量：创新绩效（专利授权量取对数）
    df["Patent"] = np.log1p(df["patent"])
    # 公司规模已为 ln 总资产
    keep = ["firm_id", "year", "industry", "soe",
            "freq_AI", "freq_BD", "freq_CC", "freq_BC", "freq_APP", "freq_total", "n_tokens",
            "Dig", "Dig_share", "Dig_ent",
            "size", "lev", "roa", "growth", "age", "board", "dual", "cdo",
            "patent", "Patent"]
    panel = df[keep].sort_values(["firm_id", "year"]).reset_index(drop=True)
    panel.to_csv(os.path.join(OUT, "panel_data.csv"), index=False, encoding="utf-8-sig")

    print(f"[Step4] 面板规模：{len(panel)} 行 × {panel.shape[1]} 列")
    print(f"[Step4] Dig      均值 {panel.Dig.mean():.3f}  标准差 {panel.Dig.std():.3f}")
    print(f"[Step4] Dig_ent  均值 {panel.Dig_ent.mean():.3f}  标准差 {panel.Dig_ent.std():.3f}")
    print("[Step4] 熵权法权重：", dict(zip(CATS, np.round(W, 4))))
    print(f"[Step4] 面板 -> {os.path.join(OUT, 'panel_data.csv')}")
    return panel


if __name__ == "__main__":
    main()
