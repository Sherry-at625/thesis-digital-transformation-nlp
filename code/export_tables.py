# -*- coding: utf-8 -*-
"""
export_tables.py —— 汇总"测度结果表"（Excel 多工作表）
================================================================
把 data/output/ 下的分散结果合并为一个便于提交的 Excel 文件：
  测度结果表.xlsx
    工作表 1  panel_data         企业—年份面板（含测度）
    工作表 2  descriptive_stats  描述性统计
    工作表 3  reliability        信度与效度检验
    工作表 4  correlation        相关系数矩阵
    工作表 5  regression         回归 / 稳健性 / 异质性结果
    工作表 6  entropy_weights    熵权法各维度权重
    工作表 7  top_keywords       高频数字化关键词 Top50
运行： python code/export_tables.py
================================================================
"""
import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "output")
XLSX = os.path.join(OUT, "测度结果表.xlsx")


def main():
    panel = pd.read_csv(os.path.join(OUT, "panel_data.csv"))
    desc = pd.read_csv(os.path.join(OUT, "descriptive_stats.csv"), index_col=0)
    rel = pd.read_csv(os.path.join(OUT, "reliability_validity.csv"))
    corr = pd.read_csv(os.path.join(OUT, "correlation_matrix.csv"), index_col=0)
    reg = pd.read_csv(os.path.join(OUT, "regression_results.csv"))
    wts = pd.read_csv(os.path.join(OUT, "dig_weights.csv"))
    top = pd.read_csv(os.path.join(OUT, "top_keywords.csv"))

    with pd.ExcelWriter(XLSX, engine="openpyxl") as w:
        panel.to_excel(w, sheet_name="panel_data", index=False)
        desc.to_excel(w, sheet_name="descriptive_stats")
        rel.to_excel(w, sheet_name="reliability", index=False)
        corr.to_excel(w, sheet_name="correlation")
        reg.to_excel(w, sheet_name="regression", index=False)
        wts.to_excel(w, sheet_name="entropy_weights", index=False)
        top.to_excel(w, sheet_name="top_keywords", index=False)

    print(f"[Export] 测度结果表 -> {XLSX}")
    print(f"[Export] 共 7 个工作表，面板数据 {panel.shape[0]} 行 × {panel.shape[1]} 列")


if __name__ == "__main__":
    main()
