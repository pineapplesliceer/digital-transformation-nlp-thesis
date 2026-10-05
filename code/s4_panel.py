# -*- coding: utf-8 -*-
"""
Step 4  面板数据构建与描述性统计（Panel Construction & Descriptive Statistics）
--------------------------------------------------------------------------
输入：data/tokens/dig_index.csv + data/firm_year_truth.csv（财务与公司治理变量）
输出：data/panel_firm_year.csv / .xlsx（企业—年份面板，核心交付物）
      output/tables/table1_var_def.csv（变量定义表）
      output/tables/table2_descriptive.csv（描述性统计）
      output/tables/table5_correlation.csv（相关系数矩阵）

处理规则：
 P1 平衡面板筛选：样本企业在 2015—2023 年均需有观测，剔除缺失值；
 P2 连续变量上下 1% 缩尾处理（winsorize）；
 P3 生成分类变量 DigUnion（高于当年行业中位数为 1）；
 P4 生成滞后项 DigTrans_L1 与同行业同年度均值 IV_IndYear（工具变量）。
"""
import numpy as np
import pandas as pd

from config import (TOKEN_DIR, DATA_DIR, TABLE_DIR, VAR_DEF, CONTROLS)


def winsorize(s: pd.Series, low=0.01, high=0.99) -> pd.Series:
    lo, hi = s.quantile(low), s.quantile(high)
    return s.clip(lo, hi)


def main():
    idx = pd.read_csv(TOKEN_DIR / "dig_index.csv")
    fin = pd.read_csv(DATA_DIR / "firm_year_truth.csv")
    df = idx.merge(fin, on=["stock_code", "year"], how="inner")

    # P1 平衡面板
    years = sorted(df["year"].unique())
    cnt = df.groupby("stock_code")["year"].nunique()
    keep = cnt[cnt == len(years)].index
    df = df[df["stock_code"].isin(keep)].copy()
    df = df.dropna(subset=["DigTrans", "ROA", "TobinQ"] + CONTROLS)

    # P2 缩尾
    for c in ["DigTrans", "ROA", "TobinQ", "Lev", "Growth", "First", "Capital"]:
        df[c] = winsorize(df[c])

    # P3 分类变量：高于“当年—行业”中位数记为高数字化组
    med = df.groupby(["year", "industry"])["DigTrans"].transform("median")
    df["DigUnion"] = (df["DigTrans"] > med).astype(int)

    # P4 滞后项与工具变量（同行业—同年度“其他企业”均值，留一法构造）
    df = df.sort_values(["stock_code", "year"])
    df["DigTrans_L1"] = df.groupby("stock_code")["DigTrans"].shift(1)
    g = df.groupby(["industry", "year"])["DigTrans"]
    df["IV_peer"] = (g.transform("sum") - df["DigTrans"]) / (g.transform("count") - 1)

    cols = ["stock_code", "firm_name", "industry", "year", "DigTrans", "DigTrans_raw",
            "DigTrans_ew", "DigTrans_pca", "DigUnion", "DigTrans_L1", "IV_peer",
            "ROA", "TobinQ", "TFP_LP", "Size", "Lev", "Growth", "Age", "First",
            "Indep", "Capital", "SOE"]
    panel = df[cols].round(6)
    panel.to_csv(DATA_DIR / "panel_firm_year.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(DATA_DIR / "panel_firm_year.xlsx", engine="openpyxl") as xw:
        panel.to_excel(xw, sheet_name="panel", index=False)
        pd.DataFrame(VAR_DEF, columns=["变量符号", "变量名称", "度量方式", "数据来源"]
                     ).to_excel(xw, sheet_name="变量定义", index=False)
        panel.groupby("year")[["DigTrans", "ROA", "TobinQ"]].mean().round(4).to_excel(
            xw, sheet_name="年度均值", index=True)

    # 表1 变量定义
    pd.DataFrame(VAR_DEF, columns=["变量符号", "变量名称", "度量方式", "数据来源"]).to_csv(
        TABLE_DIR / "table1_var_def.csv", index=False, encoding="utf-8-sig")

    # 表2 描述性统计
    show = ["DigTrans", "DigTrans_raw", "DigUnion", "ROA", "TobinQ", "TFP_LP"] + CONTROLS
    desc = panel[show].describe().T
    desc["median"] = panel[show].median()
    desc["skew"] = panel[show].skew()
    desc = desc.rename(columns={"count": "N", "mean": "均值", "std": "标准差",
                                "min": "最小值", "25%": "P25", "50%": "中位数",
                                "75%": "P75", "max": "最大值", "median": "中位数2",
                                "skew": "偏度"})
    desc = desc[["N", "均值", "标准差", "最小值", "P25", "中位数", "P75", "最大值", "偏度"]]
    desc.round(4).to_csv(TABLE_DIR / "table2_descriptive.csv", encoding="utf-8-sig")

    # 表5 相关系数矩阵
    corr_vars = ["DigTrans", "ROA", "TobinQ", "Size", "Lev", "Growth", "Age",
                 "First", "Indep", "Capital"]
    panel[corr_vars].corr(method="pearson").round(3).to_csv(
        TABLE_DIR / "table5_correlation.csv", encoding="utf-8-sig")

    # 年度均值趋势（用于论文图1 + 数据说明）
    trend = panel.groupby("year").agg(
        DigTrans_mean=("DigTrans", "mean"), DigTrans_sd=("DigTrans", "std"),
        ROA_mean=("ROA", "mean"), n=("DigTrans", "size")).round(4)
    trend.to_csv(TABLE_DIR / "table_trend.csv", encoding="utf-8-sig")

    print(f"[s4] 面板构建完成：{panel.stock_code.nunique()} 家企业 × {len(years)} 年 "
          f"= {len(panel)} 个观测；DigTrans 均值 {panel.DigTrans.mean():.3f}；"
          f"高数字化组占比 {panel.DigUnion.mean():.1%}")


if __name__ == "__main__":
    main()
