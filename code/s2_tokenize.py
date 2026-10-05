# -*- coding: utf-8 -*-
"""
Step 2  中文分词与关键词计数（Tokenization & Keyword Counting）
--------------------------------------------------------------------------
输入：data/clean_text/*.txt
输出：data/tokens/doc_terms.csv（文档级：分维度关键词词频、词数、前后半分频）
      data/tokens/top_words.csv（全体语料高频词，用于描述语料特征）

处理规则（对应论文 3.3 节）：
 T1 加载自定义词典（五维数字化转型词典全部入 jieba，避免“数字化转型”被切碎）；
 T2 停用词过滤：哈工大停用词表口径 + 本项目补充词（公司、报告、年度等）；
 T3 最长优先匹配：同一位置命中“数字化转型”时不再重复计入“数字化”，
    避免子串重复计数造成测度虚高；
 T4 否定语境处理：关键词前 2 个 token 内出现否定词（不/无/未/尚未…）则该次提及不计；
 T5 程度副词加权：关键词前 1 个 token 为程度副词（全面/深度/持续…）时按权重 1.2—1.5 计；
 T6 分半计数：以文档中点切分，分别统计两半的关键词词频，用于分半信度检验。
"""
import json
import re
import numpy as np
import pandas as pd
import jieba

from config import (CLEAN_TEXT_DIR, TOKEN_DIR, DIG_DICT, NEGATION_WORDS,
                    DEGREE_WORDS, ALL_KEYWORDS)

# 停用词（哈工大停用词表口径的常用子集 + 年报噪声词）
STOPWORDS = set("""
的 了 和 是 在 有 与 及 等 为 我 公司 报告 年度 本期 上期 我们 以及 通过 进行
实现 进一步 相关 方面 情况 由于 同时 促进 推动 提升 加强 保持 存在 具有 以 并
对 中 上 下 内 外 将 已 应 该 其 之 而 于 从 到 被 使 让 让 使 把 根据 按照 截至
""".split())

for k in ALL_KEYWORDS:                      # T1 自定义词典
    jieba.add_word(k, freq=100000)


def tokens(text: str):
    return [w for w in jieba.lcut(text) if w.strip() and w not in STOPWORDS]


def count_keywords(words):
    """T3—T5：返回 (加权词频, 加权词频_仅含程度加权, 原始计数)"""
    dim_cnt = {d: 0.0 for d in DIG_DICT}
    raw_cnt = {d: 0.0 for d in DIG_DICT}
    kw2dim = {k: d for d, ks in DIG_DICT.items() for k in ks}
    i, n = 0, len(words)
    while i < n:
        w = words[i]
        if w in kw2dim:
            # T4 否定语境
            left = words[max(0, i - 2):i]
            if any(x in NEGATION_WORDS for x in left):
                i += 1
                continue
            # T5 程度加权
            wgt = 1.0
            if i > 0 and words[i - 1] in DEGREE_WORDS:
                wgt = DEGREE_WORDS[words[i - 1]]
            d = kw2dim[w]
            dim_cnt[d] += wgt
            raw_cnt[d] += 1
        i += 1
    return dim_cnt, raw_cnt


def main():
    rows, all_words = [], []
    files = sorted(CLEAN_TEXT_DIR.glob("*.txt"))
    for idx, f in enumerate(files, 1):
        code, year = f.stem.split("_")
        text = f.read_text(encoding="utf-8")
        words = tokens(text)
        half = len(words) // 2
        w1, w2 = words[:half], words[half:]
        d_all, r_all = count_keywords(words)
        d_h1, _ = count_keywords(w1)
        d_h2, _ = count_keywords(w2)
        all_words.extend(words)
        row = {"doc_id": f"{code}_{year}", "stock_code": code, "year": int(year),
               "n_token": len(words),
               "n_cn": len(re.findall(r"[\u4e00-\u9fa5]", text))}
        for d in DIG_DICT:
            row[f"cnt_{d}"] = d_all[d]
            row[f"raw_{d}"] = r_all[d]
            row[f"h1_{d}"] = d_h1[d]
            row[f"h2_{d}"] = d_h2[d]
        rows.append(row)
        if idx % 300 == 0:
            print(f"    已处理 {idx}/{len(files)} 篇")

    df = pd.DataFrame(rows)
    df.to_csv(TOKEN_DIR / "doc_terms.csv", index=False, encoding="utf-8-sig")

    # 语料高频词（描述语料特征，不含关键词）
    from collections import Counter
    top = Counter(w for w in all_words if len(w) > 1).most_common(60)
    pd.DataFrame(top, columns=["word", "freq"]).to_csv(
        TOKEN_DIR / "top_words.csv", index=False, encoding="utf-8-sig")

    hit_rate = (df[[f"raw_{d}" for d in DIG_DICT]].sum(axis=1) > 0).mean()
    print(f"[s2] 分词完成：{len(df)} 篇文档，平均词数 {df.n_token.mean():.0f}，"
          f"含数字化关键词的文档占比 {hit_rate:.1%}")


if __name__ == "__main__":
    main()
