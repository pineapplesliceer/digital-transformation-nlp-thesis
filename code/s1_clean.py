# -*- coding: utf-8 -*-
"""
Step 1  文本清洗（Corpus Cleaning）
--------------------------------------------------------------------------
输入：data/raw_text/*.txt（年报“管理层讨论与分析”语料）
输出：data/clean_text/*.txt（清洗后正文）
      data/clean_summary.csv（每篇文档字数等清洗日志）

清洗规则（对应论文 3.2 节）：
 R1 去除 HTML 标签与转义字符；R2 去除页眉页脚、章节标题、免责声明模板句；
 R3 全角字符转半角、统一标点；R4 仅保留中文/英文/数字/常用标点；
 R5 去除连续重复标点与空白；R6 句子级去重（年报模板句重复会高估词频）；
 R7 过滤中文有效字符数 < 200 的文档（防止“只有标题”的空文档污染样本）。
"""
import re
import csv
import pandas as pd
from config import RAW_TEXT_DIR, CLEAN_TEXT_DIR, DATA_DIR

TAG = re.compile(r"<[^>]+>")
ESC = re.compile(r"&[a-zA-Z]+;|&#\d+;")
BOILER = [
    r"第[一二三四五六七八九十]+节.*?讨论与分析",
    r"本公司及董事会全体成员保证.*?真实、准确、完整。",
    r"本报告涉及未来计划.*?不构成.*?承诺。",
    r"单位[:：].*?\n",
]
ONLY_KEEP = re.compile(r"[^\u4e00-\u9fa5a-zA-Z0-9，。；：、（）%\-\.]")
MULTI_PUNC = re.compile(r"([，。；：、])\1{1,}")


def full2half(s: str) -> str:
    out = []
    for ch in s:
        code = ord(ch)
        if code == 0x3000:
            out.append(" ")
        elif 0xFF01 <= code <= 0xFF5E:
            out.append(chr(code - 0xFEE0))
        else:
            out.append(ch)
    return "".join(out)


def clean(text: str) -> str:
    t = TAG.sub("", text)
    t = ESC.sub("", t)
    for pat in BOILER:
        t = re.sub(pat, "", t, flags=re.S)
    t = full2half(t)
    t = ONLY_KEEP.sub("", t)
    t = MULTI_PUNC.sub(r"\1", t)
    # 句子级去重
    sents, seen = [], set()
    for s in re.split(r"[。！？]", t):
        s = s.strip()
        if len(s) < 6:
            continue
        key = s[:40]
        if key in seen:
            continue
        seen.add(key)
        sents.append(s)
    return "。".join(sents) + "。"


def main():
    logs = []
    for f in sorted(RAW_TEXT_DIR.glob("*.txt")):
        code, year = f.stem.split("_")
        raw = f.read_text(encoding="utf-8")
        body = clean(raw)
        n_cn = len(re.findall(r"[\u4e00-\u9fa5]", body))
        if n_cn < 200:            # R7 过滤空文档
            logs.append(dict(stock_code=code, year=year, raw_len=len(raw),
                             cn_char=0, dropped=1))
            continue
        (CLEAN_TEXT_DIR / f.name).write_text(body, encoding="utf-8")
        logs.append(dict(stock_code=code, year=year, raw_len=len(raw),
                         cn_char=n_cn, dropped=0))
    df = pd.DataFrame(logs)
    df.to_csv(DATA_DIR / "clean_summary.csv", index=False, encoding="utf-8-sig")
    print(f"[s1] 清洗完成：有效文档 {(df.dropped == 0).sum()} 篇，"
          f"过滤 {(df.dropped == 1).sum()} 篇，"
          f"平均中文字数 {df[df.dropped == 0].cn_char.mean():.0f}")


if __name__ == "__main__":
    main()
