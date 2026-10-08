# -*- coding: utf-8 -*-
"""
Step 1 / 五步流水线之一：语料采集与语料库构建（含企业-年份基础数据）
================================================================
研究情境
  基于中国 A 股上市公司年度报告文本，构建"企业数字化转型程度"文本测度，
  并检验其对企业创新绩效的影响。

数据来源（本仓库为可复现的"预演论文"演示管线）
  · 年报文本：仿真年报语料库，随机种子固定 SEED=42，任何人运行结果一致。
  · 公司特征 / 财务 / 专利：同步仿真的企业-年份面板，模拟
    CSMAR / CNRDS 的结构（字段与真实数据库对齐）。
  · 真实研究时，只需把三个输出文件替换为：
      data/raw/raw_corpus.jsonl        ← 巨潮资讯网/CNRDS 年报正文
      data/raw/firm_profile.csv        ← CSMAR 公司基本信息
      data/raw/firm_year_financials.csv← CSMAR 财务 + CNRDS 专利
    并保持字段名不变，Step 2–5 无需任何改动。

潜在(隐)变量设计
  潜在冲击 noise 服从 AR(1)（ρ=0.85），使数字化程度具有跨期持续记忆：
  latent = 0.70*firm_effect + trend_t + 0.30*SOE + industry_effect + 0.40*noise
  · 技术词频：由 latent 经 sigmoid 映射为泊松强度生成 → 文本词频携带 latent 信息；
  · 创新绩效：由当期 latent 与控制变量驱动；因 latent 强持续，滞后测度亦含前瞻信息；
  · CDO 披露：由 latent 生成的独立外部信号，供 Step 5 做效标关联效度检验。

输出
  data/raw/raw_corpus.jsonl           企业-年份年报文本
  data/raw/firm_profile.csv           企业静态特征
  data/raw/firm_year_financials.csv   企业-年份财务/治理/专利/CDO
================================================================
"""
import json
import os
import numpy as np
import pandas as pd

from lexicon import DIGITAL_DICT, GENERIC, INDUSTRIES

SEED = 42
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def build_all(n_firms=300, years=range(2016, 2023)):
    rng = np.random.default_rng(SEED)
    years = list(years)

    # ---------------- 企业静态特征 ----------------
    firms = []
    for i in range(n_firms):
        firms.append(dict(
            firm_id=i + 1,
            stock_code=f"{600000 + i * 7:06d}",
            industry=INDUSTRIES[i % len(INDUSTRIES)],
            soe=int(rng.random() < 0.35),
            list_year=int(rng.integers(1993, 2015)),
            firm_effect=rng.normal(0, 1),
            size_lvl=rng.normal(22.0, 1.5),   # 企业固有规模(ln 总资产)
        ))
    firm_df = pd.DataFrame(firms)

    trend = {y: -0.9 + 0.16 * (y - 2016) + (0.55 if y >= 2019 else 0.0) for y in years}
    ind_effect = {ind: rng.normal(0, 0.35) for ind in INDUSTRIES}

    corpus_rows, fin_rows = [], []
    RHO = 0.90                      # 潜在冲击的持续性(AR1)，使数字化程度具有跨期记忆
    for _, f in firm_df.iterrows():
        prev_noise, prev_latent = 0.0, 0.0
        for y in years:
            noise = RHO * prev_noise + np.sqrt(1 - RHO ** 2) * rng.normal()
            prev_noise = noise
            latent = (0.55 * f["firm_effect"] + trend[y]
                      + 0.30 * f["soe"] + ind_effect[f["industry"]]
                      + 0.65 * noise)
            prev_latent = latent

            # ============ (A) 年报文本 ============
            p = _sigmoid(latent)
            weights = {"AI": 1.00, "BD": 1.15, "CC": 0.90, "BC": 0.55, "APP": 1.35}
            tokens = []
            for cat, kws in DIGITAL_DICT.items():
                k = rng.poisson(4 + 45 * p * weights[cat])
                if k > 0:
                    tokens.extend(rng.choice(kws, size=k, replace=True).tolist())
            # 通用词（年报有效词数与企业数字化强度基本独立，长度约 340~460 词，
            # 这样"词频占比"口径才不会因为分母同比例放大而丢失信息）
            n_generic = int(rng.integers(340, 461))
            tokens.extend(rng.choice(GENERIC, size=n_generic, replace=True).tolist())
            rng.shuffle(tokens)
            corpus_rows.append(dict(
                firm_id=int(f["firm_id"]), stock_code=f["stock_code"], year=y,
                industry=f["industry"], soe=int(f["soe"]), text="".join(tokens)))

            # ============ (B) 财务 / 治理 / 专利 / CDO ============
            size_z = rng.normal(0, 1)
            size = f["size_lvl"] + 0.35 * (y - 2016) + 0.9 * size_z   # 规模随时间增长
            lev = float(np.clip(rng.normal(0.44 + 0.03 * size_z, 0.18), 0.05, 0.95))
            roa = float(np.clip(rng.normal(0.045 + 0.010 * size_z, 0.055), -0.35, 0.35))
            growth = float(np.clip(rng.normal(0.12, 0.26), -0.6, 1.8))
            board = int(np.clip(round(rng.normal(9, 1.8)), 5, 15))
            dual = int(rng.random() < 0.28)
            age = y - int(f["list_year"])
            cdo = int(rng.random() < _sigmoid(1.2 * latent - 0.5))    # 是否披露首席数字官

            # 专利产出：由当期数字化水平 + 控制变量驱动。
            # 由于 latent 为强持续(AR1, ρ=0.9)，滞后一期的测度仍携带前瞻信息，
            # 可在 Step6 中作为稳健性检验。
            rate = np.exp(1.00 + 0.65 * latent + 0.25 * size_z
                          + 1.50 * roa - 0.40 * lev + 0.15 * f["soe"])
            patent = int(rng.poisson(rate))
            fin_rows.append(dict(
                firm_id=int(f["firm_id"]), year=y,
                size=round(size, 4), lev=round(lev, 4), roa=round(roa, 4),
                growth=round(growth, 4), age=age, board=board, dual=dual,
                cdo=cdo, patent=patent))

    corpus = pd.DataFrame(corpus_rows)
    fin = pd.DataFrame(fin_rows)

    # ---------------- 落盘 ----------------
    with open(os.path.join(RAW_DIR, "raw_corpus.jsonl"), "w", encoding="utf-8") as fh:
        for r in corpus_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    firm_df.drop(columns=["firm_effect", "size_lvl"]).to_csv(
        os.path.join(RAW_DIR, "firm_profile.csv"), index=False, encoding="utf-8-sig")
    fin.to_csv(os.path.join(RAW_DIR, "firm_year_financials.csv"),
               index=False, encoding="utf-8-sig")

    print(f"[Step1] 年报语料：{len(corpus)} 个企业-年份文档，"
          f"{corpus.firm_id.nunique()} 家企业 × {len(years)} 年")
    print(f"[Step1] 财务/专利面板：{len(fin)} 行，专利均值 {fin.patent.mean():.2f}，"
          f"CDO 披露比例 {fin.cdo.mean():.1%}")
    return corpus, fin


if __name__ == "__main__":
    build_all()
