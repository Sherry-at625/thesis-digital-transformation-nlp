# 基于年报文本分析的企业数字化转型测度及其对创新绩效的影响研究

> 本科毕业论文（预演稿）配套仓库 —— 大连财经学院 · 大数据管理与应用
>
> 一条**完整、可复现**的 NLP 文本测度"五步流水线"：从年报语料到可回归的企业—年份面板，
> 并附论文全文与全部中间结果。

---

## 一、研究一句话概述

以 2016—2022 年中国 A 股 300 家上市公司共 **2100 个企业—年份观测**为样本，
用 jieba 分词 + 自定义五维数字化词典构造企业数字化转型测度 **Dig**，
经信度与效度检验后，用双向固定效应模型检验其对企业创新绩效的影响：
**Dig 每提高 1 个单位，创新绩效（ln(1+专利授权数)）显著提高 0.429 个单位**（t = 5.54，p < 0.01），
替换测度与滞后一期检验均稳健。

---

## 二、交付物清单

| 交付材料 | 对应文件 |
| --- | --- |
| 预演论文全文（含封面、目录、正文、参考文献） | `论文/毕业论文模拟稿.docx` |
| 可复现代码（五步流水线 Python 脚本） | `code/step1_*.py` ~ `code/step6_*.py` + `code/run_all.py` |
| 测度结果表（企业—年份面板） | `data/output/panel_data.csv` |
| 数据来源说明 | `docs/数据来源说明.md` |
| 信效度检验表 | `data/output/reliability_validity.csv` |
| 回归结果表 | `data/output/regression_results.csv` |
| 图 1—图 3 | `figures/fig1_dig_trend.png`、`fig2_distribution.png`、`fig3_top_keywords.png` |

---

## 三、五步流水线（Five-Step Pipeline）

```
Step1 语料采集与语料库构建   → data/raw/raw_corpus.jsonl
Step2 文本预处理（清洗/分词/去停用词） → data/interim/tokens.jsonl
Step3 词典构建与关键词词频统计 → data/output/keyword_frequency.csv
Step4 测度合成与指数构建      → data/output/panel_data.csv
Step5 信度与效度检验          → data/output/reliability_validity.csv
(Step6 实证分析：回归/稳健性/异质性/绘图 → regression_results.csv + figures/)
```

| 步骤 | 脚本 | 关键处理 |
| --- | --- | --- |
| 1 | `code/step1_corpus_collection.py` | 按（企业代码，年份）建文档索引，形成语料库 |
| 2 | `code/step2_text_preprocessing.py` | 全角转半角→去噪→jieba 精确模式（加载自定义词典）→去停用词与单字 |
| 3 | `code/step3_dictionary_frequency.py` | 5 维度 58 词条词典 + 倒排索引，统计各维度词频 |
| 4 | `code/step4_measurement_construction.py` | Dig = ln(1+总词频)；占比口径；熵权法综合指数 |
| 5 | `code/step5_reliability_validity.py` | Cronbach's α、分半信度、CITC、KMO、Bartlett、效标关联效度 |
| 6 | `code/step6_analysis_regression.py` | 描述统计、聚类稳健标准误回归、稳健性、异质性、绘图 |

---

## 四、核心结果

### 4.1 信度与效度检验

| 指标 | 取值 | 判断 |
| --- | --- | --- |
| Cronbach's α（5 维度） | 0.933 | > 0.7，内部一致性优良 |
| Spearman-Brown 校正分半信度 | 0.932 | 高 |
| KMO 取样适切性 | 0.908 | > 0.7，极佳 |
| Bartlett 球形检验 | p < 0.01 | 维度存在公共因子 |
| 效标关联效度 r(Dig, CDO) | 0.451 | p < 0.01，显著为正 |
| 聚合效度 r(Dig, Dig_ent) | 0.974 | 与熵权法指数高度一致 |
| CITC（各维度） | 0.754 ~ 0.859 | 均 > 0.4 |

### 4.2 回归结果（被解释变量：Patent）

| 模型 | 核心变量系数 | t 值 | N | R² |
| --- | --- | --- | --- | --- |
| (1) 混合 OLS | 1.0231*** | 25.60 | 2100 | 0.407 |
| (2) 双向固定效应 | 0.4286*** | 5.54 | 2100 | 0.582 |
| (3) 稳健性：占比口径 | 0.0198*** | 5.81 | 2100 | 0.582 |
| (4) 稳健性：熵权指数 | 1.5378*** | 8.23 | 2100 | 0.591 |
| (5) 稳健性：滞后一期 | 0.2238** | 2.46 | 1800 | 0.598 |
| 异质性：国有企业 | 0.3740** | 2.51 | 784 | 0.633 |
| 异质性：非国有企业 | 0.4459*** | 4.25 | 1316 | 0.548 |
| 异质性：高新技术行业 | 0.5183*** | 3.70 | 798 | 0.562 |
| 异质性：其他行业 | 0.3720*** | 3.48 | 1302 | 0.596 |

> 注：标准误在企业层面聚类；*** / ** / * 表示 1% / 5% / 10% 水平显著。

---

## 五、如何复现

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 一键跑完整条流水线（Step1 → Step6）
python code/run_all.py

# 3. 依据结果重新生成论文 Word
python code/build_thesis_docx.py
```

随机种子固定为 `SEED = 42`，任何人运行都会得到与本文**完全一致**的结果。

---

## 六、目录结构

```
thesis-digital-transformation-nlp/
├── code/                      # 五步流水线 + 论文生成脚本
│   ├── lexicon.py             # 共享词表（五维数字化词典 / 通用词 / 停用词）
│   ├── step1_corpus_collection.py
│   ├── step2_text_preprocessing.py
│   ├── step3_dictionary_frequency.py
│   ├── step4_measurement_construction.py
│   ├── step5_reliability_validity.py
│   ├── step6_analysis_regression.py
│   ├── run_all.py
│   └── build_thesis_docx.py
├── data/
│   ├── raw/                   # 语料、公司特征、财务/专利面板
│   ├── interim/               # 停用词表、分词结果
│   └── output/                # 词频矩阵、面板数据、信效度表、回归结果
├── figures/                   # 图 1—图 3
├── docs/数据来源说明.md
├── 论文/毕业论文模拟稿.docx
├── requirements.txt
└── README.md
```

---

## 七、关于数据的重要说明

本仓库为"预演论文"，**实证数据为仿真数据**：由 `step1` 以固定随机种子生成，
字段结构与 CSMAR / CNRDS / 巨潮资讯网的真实数据完全对齐，并在数据生成过程中
内置了"数字化转型 → 创新绩效"的真实正向效应（AR(1) 持续冲击，ρ = 0.9）。

做真实研究时，只需把 `data/raw/` 下的三个文件替换为真实数据导出文件，
**保持字段名不变**，`Step 2`—`Step 6` 的代码无需任何修改即可运行。
详见 `docs/数据来源说明.md`。
