# -*- coding: utf-8 -*-
"""
Step 3 / 五步流水线之三：词典构建与关键词词频统计
================================================================
做法：
  ① 载入数字化技术词典（5 维度，见 step1_dictionary 或本文件内嵌副本）
  ② 对每篇文档逐维度统计关键词出现频次
  ③ 同时输出全样本关键词总频表（用于绘制词云/Top 词图，检验内容效度）
输出：
  data/output/keyword_frequency.csv   每行 (firm_id, year, 各维度词频, 总频)
  data/output/top_keywords.csv        全样本 Top-50 关键词及频次
================================================================
"""
import json
import os
import collections
import pandas as pd

from lexicon import DIGITAL_DICT, CATS, WORD2CAT

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERIM = os.path.join(BASE_DIR, "data", "interim")
OUT = os.path.join(BASE_DIR, "data", "output")
os.makedirs(OUT, exist_ok=True)


def main():
    rows, counter = [], collections.Counter()
    with open(os.path.join(INTERIM, "tokens.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            freq = collections.Counter({c: 0 for c in CATS})
            for w in d["tokens"]:
                if w in WORD2CAT:
                    freq[WORD2CAT[w]] += 1
                    counter[w] += 1
            rec = {"firm_id": d["firm_id"], "year": d["year"]}
            rec.update({f"freq_{c}": freq[c] for c in CATS})
            rec["freq_total"] = sum(freq[c] for c in CATS)
            rec["n_tokens"] = d["n_tokens"]
            rows.append(rec)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "keyword_frequency.csv"), index=False, encoding="utf-8-sig")

    top = pd.DataFrame(counter.most_common(50), columns=["keyword", "freq"])
    top.to_csv(os.path.join(OUT, "top_keywords.csv"), index=False, encoding="utf-8-sig")

    print(f"[Step3] 词典维度数：{len(CATS)}，词典词条数：{len(WORD2CAT)}")
    print(f"[Step3] 识别到不同的数字化关键词：{len(counter)} 个")
    print(f"[Step3] 词频矩阵 -> {os.path.join(OUT, 'keyword_frequency.csv')}")
    print(top.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
