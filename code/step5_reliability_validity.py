# -*- coding: utf-8 -*-
"""
Step 5 / 五步流水线之五：信度与效度检验
================================================================
测度好不好，必须检验。本步骤对 5 维度词频标度做心理测量学检验：

  信度(reliability)
    · Cronbach's α        —— 内部一致性
    · 分半信度(Split-half) —— 奇偶维度相关 + Spearman-Brown 校正
    · 校正后项-总相关(CITC)

  效度(validity)
    · 内容效度：Top 关键词是否落在数字化语义域（由 Step 3 词表体现）
    · 结构效度：KMO 取样适切性 + Bartlett 球形检验
    · 效标关联效度：Dig 与独立外部信号 CDO 披露的相关系数

输出：
  data/output/reliability_validity.csv  各项检验指标
  data/output/correlation_matrix.csv    维度与测度相关系数矩阵
================================================================
"""
import os
import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE_DIR, "data", "output")

CATS = ["AI", "BD", "CC", "BC", "APP"]


def cronbach_alpha(X: np.ndarray) -> float:
    """X: n×k，列为题项。返回标准化后 α。"""
    X = (X - X.mean(0)) / (X.std(0, ddof=1) + 1e-12)   # 标准化，消除量纲差异
    n, k = X.shape
    item_var = X.var(0, ddof=1).sum()
    total_var = X.sum(1).var(ddof=1)
    return k / (k - 1) * (1 - item_var / total_var)


def split_half(X: np.ndarray):
    """奇偶分半：奇数维度 vs 偶数维度，返回相关系数与 Spearman-Brown 校正值。"""
    odd, even = X[:, 0::2].sum(1), X[:, 1::2].sum(1)
    r = np.corrcoef(odd, even)[0, 1]
    sb = 2 * r / (1 + r)
    return r, sb


def kmo_bartlett(X: np.ndarray):
    """返回 (KMO, Bartlett chi2, p 值)。"""
    R = np.corrcoef(X, rowvar=False)
    invR = np.linalg.pinv(R)
    D = np.diag(1 / np.sqrt(np.diag(invR)))
    P = -D @ invR @ D                          # 偏相关矩阵
    R_off = R.copy(); np.fill_diagonal(R_off, 0.0)
    P_off = P.copy(); np.fill_diagonal(P_off, 0.0)
    kmo = (R_off ** 2).sum() / ((R_off ** 2).sum() + (P_off ** 2).sum())
    n, m = X.shape
    chi2 = -(n - 1 - (2 * m + 5) / 6) * np.log(np.linalg.det(R))
    df = m * (m - 1) / 2
    p = 1 - stats.chi2.cdf(chi2, df)
    return kmo, chi2, p


def main():
    panel = pd.read_csv(os.path.join(OUT, "panel_data.csv"))
    X = panel[[f"freq_{c}" for c in CATS]].to_numpy(float)

    # ---------- 信度 ----------
    alpha = cronbach_alpha(X)
    r_sh, sb = split_half(X)

    citc = {}
    Xz = (X - X.mean(0)) / (X.std(0, ddof=1) + 1e-12)
    for j, c in enumerate(CATS):
        rest = np.delete(Xz, j, axis=1).sum(1)
        citc[c] = float(np.corrcoef(Xz[:, j], rest)[0, 1])

    # ---------- 效度 ----------
    kmo, chi2, kp = kmo_bartlett(X)
    # 效标关联效度：Dig 与 CDO（point-biserial = Pearson）
    r_cdo, p_cdo = stats.pearsonr(panel["Dig"], panel["cdo"])
    # 与替代测度的一致性（聚合效度）
    r_ent, _ = stats.pearsonr(panel["Dig"], panel["Dig_ent"])
    r_share, _ = stats.pearsonr(panel["Dig"], panel["Dig_share"])

    rows = [
        ("信度", "Cronbach's α（5 维度）", f"{alpha:.4f}", "α>0.7 视为内部一致性良好"),
        ("信度", "分半相关系数", f"{r_sh:.4f}", "奇偶维度相关"),
        ("信度", "Spearman-Brown 校正分半信度", f"{sb:.4f}", "校正后信度"),
        ("效度", "KMO 取样适切性", f"{kmo:.4f}", ">0.7 适合做因子/合成"),
        ("效度", "Bartlett 球形检验 χ²", f"{chi2:.2f}", f"p={kp:.3e}"),
        ("效度", "效标关联效度 r(Dig, CDO)", f"{r_cdo:.4f}", f"p={p_cdo:.3e}"),
        ("效度", "聚合效度 r(Dig, Dig_ent)", f"{r_ent:.4f}", "与熵权法指数一致性"),
        ("效度", "聚合效度 r(Dig, Dig_share)", f"{r_share:.4f}", "与占比口径一致性"),
    ]
    for c in CATS:
        rows.append(("信度", f"CITC-{c}", f"{citc[c]:.4f}", "校正后项-总相关>0.4"))

    out = pd.DataFrame(rows, columns=["类别", "指标", "取值", "说明"])
    out.to_csv(os.path.join(OUT, "reliability_validity.csv"),
               index=False, encoding="utf-8-sig")

    # 相关系数矩阵
    corr = panel[["Dig", "Dig_share", "Dig_ent", "size", "lev", "roa",
                  "growth", "Patent"]].corr().round(3)
    corr.to_csv(os.path.join(OUT, "correlation_matrix.csv"), encoding="utf-8-sig")

    print(out.to_string(index=False))
    print(f"[Step5] 信效度结果 -> {os.path.join(OUT, 'reliability_validity.csv')}")


if __name__ == "__main__":
    main()
