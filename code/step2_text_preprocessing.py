# -*- coding: utf-8 -*-
"""
Step 2 / 五步流水线之二：文本预处理（清洗 + 分词 + 去停用词）
================================================================
流程：
  ① 清洗：去标点/数字/空白、全角转半角、去除页眉页脚等噪声（本仿真语料已较干净）
  ② 分词：jieba 精确模式，并加载 lexicon.USER_WORDS 自定义词典以提高专业词召回
  ③ 去停用词：删除中文停用词、单字、纯符号 token
输出：
  data/interim/tokens.jsonl  每行 {"firm_id","year","tokens":[...],"n_tokens":int}
  data/interim/stopwords.txt 本次使用的停用词表（可复现）
================================================================
"""
import json
import os
import re
import jieba

from lexicon import USER_WORDS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE_DIR, "data", "raw", "raw_corpus.jsonl")
INTERIM = os.path.join(BASE_DIR, "data", "interim")
os.makedirs(INTERIM, exist_ok=True)

# 加载自定义词典：把数字化关键词与年报高频词加入 jieba，
# 显著提升专业词召回率（文献中提高测度准确度的标准做法）。
for _w in USER_WORDS:
    jieba.add_word(_w, freq=10_000_000)

# 精简版中文停用词表（研究用，可按需扩充）
STOPWORDS = set("""
的 了 和 是 与 及 或 在 对 为 以 于 而 其 等 中 上 下 之 者 有 也 就 都 并 被
将 从 到 由 这 那 你 我 他 她 它 我们 你们 他们 公司 报告期内 本报告期 年度 报告
一 二 三 四 五 六 七 八 九 十 个 年 月 日 元 万 亿 百分点 同比 以上 以下
以 内 外 前 后 左 右 不 无 未 非 该 各 每 全 更 最 很 较 十分 非常 进一步 不断
实现 推进 加强 持续 情况 方面 作用 水平 能力 方式 过程 问题 影响 关系 依据
""".split())


def full2half(text: str) -> str:
    """全角转半角"""
    out = []
    for ch in text:
        code = ord(ch)
        if code == 0x3000:
            out.append(" ")
        elif 0xFF01 <= code <= 0xFF5E:
            out.append(chr(code - 0xFEE0))
        else:
            out.append(ch)
    return "".join(out)


def clean(text: str) -> str:
    text = full2half(text)
    text = re.sub(r"[\s\r\n\t]+", "", text)          # 去空白
    text = re.sub(r"[^\u4e00-\u9fa5A-Za-z]", "", text)  # 仅保留中文与字母
    return text


def tokenize(text: str):
    text = clean(text)
    toks = []
    for w in jieba.cut(text, cut_all=False):
        w = w.strip()
        if not w or len(w) < 2:          # 去掉单字与空串
            continue
        if w in STOPWORDS:
            continue
        toks.append(w)
    return toks


def main():
    with open(os.path.join(INTERIM, "stopwords.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(STOPWORDS)))

    n_doc, total = 0, 0
    with open(RAW, encoding="utf-8") as fin, \
         open(os.path.join(INTERIM, "tokens.jsonl"), "w", encoding="utf-8") as fout:
        for line in fin:
            d = json.loads(line)
            toks = tokenize(d["text"])
            total += len(toks)
            n_doc += 1
            fout.write(json.dumps({"firm_id": d["firm_id"], "year": d["year"],
                                   "tokens": toks, "n_tokens": len(toks)},
                                  ensure_ascii=False) + "\n")
    print(f"[Step2] 分词完成：{n_doc} 篇文档，共 {total} 个有效词，"
          f"篇均 {total / n_doc:.1f} 词")
    print(f"[Step2] 分词结果 -> {os.path.join(INTERIM, 'tokens.jsonl')}")


if __name__ == "__main__":
    main()
