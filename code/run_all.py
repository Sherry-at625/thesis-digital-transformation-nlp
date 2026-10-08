# -*- coding: utf-8 -*-
"""
run_all.py —— 一键复现整条流水线
================================================================
用法：
    python code/run_all.py
依赖安装：
    pip install -r requirements.txt
执行顺序（五步流水线 + 实证分析）：
    Step1 语料采集 → Step2 文本预处理 → Step3 词典与词频
    → Step4 测度合成 → Step5 信效度检验 → Step6 回归与可视化
================================================================
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    import step1_corpus_collection as s1
    import step2_text_preprocessing as s2
    import step3_dictionary_frequency as s3
    import step4_measurement_construction as s4
    import step5_reliability_validity as s5
    import step6_analysis_regression as s6
    import export_tables as s7

    t0 = time.time()
    print("=" * 64)
    print(" 企业数字化转型文本测度 · 五步流水线一键复现")
    print("=" * 64)

    print("\n>>> Step 1  语料采集与语料库构建")
    s1.build_all()
    print("\n>>> Step 2  文本预处理（清洗/分词/去停用词）")
    s2.main()
    print("\n>>> Step 3  词典构建与关键词词频统计")
    s3.main()
    print("\n>>> Step 4  测度合成与指数构建")
    s4.main()
    print("\n>>> Step 5  信度与效度检验")
    s5.main()
    print("\n>>> Step 6  描述统计 / 回归 / 稳健性 / 异质性 / 绘图")
    s6.main()
    print("\n>>> Export  汇总测度结果表（Excel 多工作表）")
    s7.main()

    print("\n" + "=" * 64)
    print(f" 全部完成，用时 {time.time() - t0:.1f} 秒。"
          f"结果见 data/output/ 与 figures/")
    print("=" * 64)


if __name__ == "__main__":
    main()
