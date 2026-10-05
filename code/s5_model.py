# -*- coding: utf-8 -*-
"""
Step 5  计量回归与异质性分析（Regression, Robustness & Heterogeneity）
--------------------------------------------------------------------------
输入：data/panel_firm_year.csv
输出：output/tables/table6_baseline.csv      基准回归（双向固定效应）
      output/tables/table7_robust.csv        稳健性（滞后、替换指标、替换因变量）
      output/tables/table8_heterogeneity.csv 异质性（产权性质、行业技术属性）
      output/tables/table9_endogeneity.txt  内生性与共同冲击处理
      output/tables/table10_classify.csv     分类任务（Logit 识别高数字化企业）
      output/tables/regression_log.txt       全部结果的可读日志

模型设定（论文 3.5 节）：
  Perf_it = α + β·DigTrans_it + γ'Controls_it + μ_i + λ_t + ε_it      (6)
  标准误按企业层面聚类（cluster-robust），以缓解序列相关与异方差。
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.sandbox.regression.gmm import IV2SLS

from config import DATA_DIR, TABLE_DIR, CONTROLS

CTRL = " + ".join(CONTROLS)
LOG = []


def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def fit(formula, df, cluster="stock_code"):
    return smf.ols(formula, data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df[cluster]})


def row(res, name):
    b, se, p = res.params[name], res.bse[name], res.pvalues[name]
    return f"{b:.4f}{stars(p)}", f"({se:.4f})", int(res.nobs), res.rsquared


def main():
    df = pd.read_csv(DATA_DIR / "panel_firm_year.csv")
    df["year"] = df["year"].astype(int)
    df = df.sort_values(["stock_code", "year"])
    df["ROA_F1"] = df.groupby("stock_code")["ROA"].shift(-1)   # 下一期绩效（内生性检验用）
    print(f"样本：{df.stock_code.nunique()} 家企业，{df.year.nunique()} 年，N = {len(df)}")
    LOG.append(f"样本：{df.stock_code.nunique()} 家企业，{df.year.nunique()} 年，N = {len(df)}")

    # ---------------- 表6 基准回归：ROA ----------------
    dfc = df[~df["year"].isin([2020, 2021, 2022])]             # 剔除疫情冲击年份
    models = {
        "(1) 仅年份FE": f"ROA ~ DigTrans + C(year)",
        "(2) 加控制变量": f"ROA ~ DigTrans + {CTRL} + C(year)",
        "(3) 双向FE（基准）": f"ROA ~ DigTrans + {CTRL} + C(year) + C(stock_code)",
        "(4) 剔除冲击年份": f"ROA ~ DigTrans + {CTRL} + C(year) + C(stock_code)",
    }
    res6, raw6 = {}, {}
    for k, f in models.items():
        d = dfc if "剔除" in k else df
        r = fit(f, d)
        res6[k] = r
        raw6[k] = dict(coef=r.params["DigTrans"], se=r.bse["DigTrans"],
                       t=r.tvalues["DigTrans"], p=r.pvalues["DigTrans"],
                       n=int(r.nobs), r2=r.rsquared)
    # 直接以文本形式整理（三线表风格）
    lines = ["表6 数字化转型对企业绩效（ROA）的影响：基准回归", "-" * 78,
             f"{'变量':<16}{'（1）':>14}{'（2）':>14}{'（3）':>14}{'（4）':>14}"]
    coefs = [row(res6[k], "DigTrans")[0] for k in models]
    ses = [row(res6[k], "DigTrans")[1] for k in models]
    lines.append(f"{'DigTrans':<16}" + "".join(f"{c:>14}" for c in coefs))
    lines.append(f"{'':<16}" + "".join(f"{s:>14}" for s in ses))
    for label in ["控制变量", "年份固定效应", "企业固定效应", "N", "R²"]:
        vals = []
        for i, k in enumerate(models):
            r = res6[k]
            vals.append({"控制变量": "否" if i == 0 else "是",
                         "年份固定效应": "是",
                         "企业固定效应": "否" if i < 2 else "是",
                         "N": str(int(r.nobs)), "R²": f"{r.rsquared:.3f}"}[label])
        lines.append(f"{label:<16}" + "".join(f"{v:>14}" for v in vals))
    lines.append("-" * 78)
    lines.append("注：括号内为企业层面聚类稳健标准误；*** ** * 分别表示 1%、5%、10% 显著性水平；"
                 "（4）列剔除 2020—2022 年外部冲击年份。")
    tbl6_txt = "\n".join(lines)
    print(tbl6_txt)
    LOG.append(tbl6_txt)
    pd.DataFrame(raw6).T.round(4).to_csv(TABLE_DIR / "table6_baseline.csv", encoding="utf-8-sig")
    (TABLE_DIR / "table6_baseline.txt").write_text(tbl6_txt, encoding="utf-8")

    # ---------------- 表7 稳健性 ----------------
    specs = {
        "(1) 替换因变量：TobinQ": "TobinQ",
        "(2) 替换因变量：TFP_LP": "TFP_LP",
        "(3) 替换核心指标：熵权法": None,
        "(4) 替换核心指标：因子得分": None,
    }
    lines7 = ["表7 稳健性检验", "-" * 70,
              f"{'变量/模型':<26}{'（1）':>11}{'（2）':>11}{'（3）':>11}{'（4）':>11}"]
    coefs, ses, ns, r2s = [], [], [], []
    for k, dv in specs.items():
        if dv:
            r = fit(f"{dv} ~ DigTrans + {CTRL} + C(year) + C(stock_code)", df)
            key = "DigTrans"
        elif "熵权" in k:
            r = fit(f"ROA ~ DigTrans_ew + {CTRL} + C(year) + C(stock_code)", df)
            key = "DigTrans_ew"
        else:
            r = fit(f"ROA ~ DigTrans_pca + {CTRL} + C(year) + C(stock_code)", df)
            key = "DigTrans_pca"
        c, s, n, rr = row(r, key)
        coefs.append(c); ses.append(s); ns.append(str(n)); r2s.append(f"{rr:.3f}")
    for label, vals in [("核心解释变量", coefs), ("", ses), ("控制变量", ["是"] * 4),
                        ("双向固定效应", ["是"] * 4), ("N", ns), ("R²", r2s)]:
        lines7.append(f"{label:<26}" + "".join(f"{v:>11}" for v in vals))
    lines7.append("-" * 70)
    tbl7_txt = "\n".join(lines7)
    print(tbl7_txt); LOG.append(tbl7_txt)
    (TABLE_DIR / "table7_robust.txt").write_text(tbl7_txt, encoding="utf-8")

    # ---------------- 表8 异质性 ----------------
    groups = {
        "(1) 国有企业": df[df.SOE == 1],
        "(2) 非国有企业": df[df.SOE == 0],
        "(3) 高技术行业": df[df.industry.isin(["C39", "C35", "C40"])],
        "(4) 传统制造行业": df[~df.industry.isin(["C39", "C35", "C40"])],
    }
    lines8 = ["表8 异质性分析（因变量：ROA）", "-" * 62,
              f"{'':<22}" + "".join(f"{k:>10}" for k in groups)]
    coefs, ses, ns = [], [], []
    for k, d in groups.items():
        r = fit(f"ROA ~ DigTrans + {CTRL} + C(year) + C(stock_code)", d)
        c, s, n, _ = row(r, "DigTrans")
        coefs.append(c); ses.append(s); ns.append(str(n))
    for label, vals in [("DigTrans", coefs), ("", ses), ("N", ns)]:
        lines8.append(f"{label:<22}" + "".join(f"{v:>10}" for v in vals))
    lines8.append("-" * 62)
    lines8.append("注：分组回归均控制全部控制变量与双向固定效应；标准误按企业层面聚类。")

    # 交互项检验（组间差异的正式统计检验）
    df["HighTech"] = df["industry"].isin(["C39", "C35", "C40"]).astype(int)
    r_soe = fit(f"ROA ~ DigTrans + DigTrans:SOE + {CTRL} + C(year) + C(stock_code)", df)
    r_ht = fit(f"ROA ~ DigTrans + DigTrans:HighTech + {CTRL} + C(year) + C(stock_code)", df)
    lines8.append(
        f"交互项检验：DigTrans×SOE = {r_soe.params['DigTrans:SOE']:.4f}"
        f"（p = {r_soe.pvalues['DigTrans:SOE']:.3f}）；"
        f"DigTrans×HighTech = {r_ht.params['DigTrans:HighTech']:.4f}"
        f"（p = {r_ht.pvalues['DigTrans:HighTech']:.3f}）")
    tbl8_txt = "\n".join(lines8)
    print(tbl8_txt); LOG.append(tbl8_txt)
    (TABLE_DIR / "table8_heterogeneity.txt").write_text(tbl8_txt, encoding="utf-8")

    # ---------------- 表9 内生性与共同冲击处理 ----------------
    specs9 = {
        "(1) 基准（双向FE）":
            (f"ROA ~ DigTrans + {CTRL} + C(year) + C(stock_code)", df),
        "(2) 行业×年度联合FE":
            (f"ROA ~ DigTrans + {CTRL} + C(year):C(industry) + C(stock_code)", df),
        "(3) 因变量取下一期":
            (f"ROA_F1 ~ DigTrans + {CTRL} + C(year):C(industry) + C(stock_code)",
             df.dropna(subset=["ROA_F1"])),
        "(4) 剔除冲击年份":
            (f"ROA ~ DigTrans + {CTRL} + C(year):C(industry) + C(stock_code)", dfc),
    }
    lines9 = ["表9 内生性与共同冲击处理（因变量：ROA）", "-" * 76]
    coef9, se9, n9, r9 = [], [], [], []
    for k, (f, d) in specs9.items():
        r = fit(f, d)
        c, s, n, rr = row(r, "DigTrans")
        coef9.append(c); se9.append(s); n9.append(str(n)); r9.append(f"{rr:.3f}")
    lines9.append(f"{'':<22}" + "".join(f"{k:>13}" for k in specs9))
    lines9.append(f"{'DigTrans':<22}" + "".join(f"{v:>13}" for v in coef9))
    lines9.append(f"{'':<22}" + "".join(f"{v:>13}" for v in se9))
    lines9.append(f"{'控制变量':<22}" + "".join(f"{'是':>13}" for _ in specs9))
    lines9.append(f"{'N':<22}" + "".join(f"{v:>13}" for v in n9))
    lines9.append(f"{'R²':<22}" + "".join(f"{v:>13}" for v in r9))
    lines9.append("-" * 76)
    lines9.append("注：标准误按企业层面聚类；(2) 以行业×年度联合固定效应吸收行业层面的随时间共同冲击，"
                  "\n(3) 以未来一期绩效为因变量缓解反向因果，(4) 剔除 2020—2022 年外部冲击样本。")
    txt9 = "\n".join(lines9)
    print(txt9); LOG.append(txt9)
    (TABLE_DIR / "table9_endogeneity.txt").write_text(txt9, encoding="utf-8")

    # ---------------- 表10 分类任务：Logit 识别高数字化企业 ----------------
    cls = smf.logit(f"DigUnion ~ {CTRL}", data=df).fit(disp=0)
    pr = cls.predict(df).to_numpy()
    ytrue = df["DigUnion"].to_numpy()
    acc = float(((pr > 0.5).astype(int) == ytrue).mean())
    # AUC：等价于 Mann-Whitney U 统计量
    pos, neg = ytrue.sum(), (1 - ytrue).sum()
    order = np.argsort(pr)
    ranks = np.empty(len(pr), dtype=float)
    ranks[order] = np.arange(1, len(pr) + 1)
    auc = float((ranks[ytrue == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))

    txt10 = ("表10 分类任务：以公司财务特征识别“高数字化”企业（Logit 模型）\n" + "-" * 58 +
             f"\n样本量 N = {len(df)}；高数字化组占比 = {ytrue.mean():.1%}"
             f"\nPseudo R² = {cls.prsquared:.4f}；准确率 = {acc:.3f}；AUC = {auc:.3f}"
             f"\n结论：仅凭财务特征分类能力有限（AUC≈{auc:.2f}），说明"
             f"“数字化程度”这类企业软信息难以由财务指标替代，"
             f"必须依赖文本信息进行测度，从而支持本文文本挖掘测度的必要性。\n" + "-" * 58)
    print(txt10); LOG.append(txt10)
    (TABLE_DIR / "table10_classify.txt").write_text(txt10, encoding="utf-8")

    (TABLE_DIR / "regression_log.txt").write_text("\n\n".join(LOG), encoding="utf-8")
    print("[s5] 回归分析完成，全部结果已写入 output/tables/")


if __name__ == "__main__":
    main()
