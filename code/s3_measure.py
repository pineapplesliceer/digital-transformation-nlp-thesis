# -*- coding: utf-8 -*-
"""
Step 3  测度构建与信度、效度检验（Index Construction, Reliability & Validity）
--------------------------------------------------------------------------
输入：data/tokens/doc_terms.csv
输出：data/tokens/dig_index.csv（文档级数字化转型测度）
      output/tables/table3_reliability.csv（信度检验）
      output/tables/table4_validity.csv（效度检验）

测度构造（论文 3.4 节，核心公式）：
  维度密度      Den_{d,it} = Count_{d,it} / (Char_{it}/1000)                 (1)
  综合密度      Den_{it}   = Σ_{d=1}^{5} Den_{d,it}                          (2)
  主指标        DigTrans_{it} = ln(1 + Den_{it})                             (3)
  熵权法（稳健性）
      p_{d,it} = Den_{d,it} / Σ_d Den_{d,it}
      e_d = -k Σ_it p_{d,it} ln p_{d,it},  k = 1/ln(N)
      w_d = (1-e_d) / Σ_d (1-e_d)
      DigTrans_ew_{it} = ln(1 + Σ_d w_d · Den_{d,it})                        (4)
  因子得分（稳健性）：五维密度标准化后取第一主成分得分 DigTrans_pca        (5)
"""
import numpy as np
import pandas as pd
from scipy import stats

from config import TOKEN_DIR, TABLE_DIR, DIG_DICT

DIMS = list(DIG_DICT.keys())
EPS = 1e-12


# ---------- 通用统计工具 ----------
def cronbach_alpha(X: np.ndarray) -> float:
    """Cronbach's α = k/(k-1) · [1 - Σσ²_i / σ²_total]"""
    k = X.shape[1]
    item_var = X.var(axis=0, ddof=1).sum()
    total_var = X.sum(axis=1).var(ddof=1)
    return k / (k - 1) * (1 - item_var / total_var)


def spearman_brown(r: float) -> float:
    """分半信度：Spearman-Brown 校正  r_sb = 2r / (1 + r)"""
    return 2 * r / (1 + r)


def kmo(R: np.ndarray) -> float:
    """KMO 取样适切性量数"""
    Rinv = np.linalg.pinv(R)
    d = np.sqrt(np.diag(Rinv))
    A = -Rinv / np.outer(d, d)
    np.fill_diagonal(A, 0)
    R0 = R.copy()
    np.fill_diagonal(R0, 0)
    return (R0 ** 2).sum() / ((R0 ** 2).sum() + (A ** 2).sum())


def bartlett(X: np.ndarray):
    """Bartlett 球形检验，返回 (chi2, df, p)"""
    n, p = X.shape
    R = np.corrcoef(X, rowvar=False)
    sign, logdet = np.linalg.slogdet(R)
    chi2 = -(n - 1 - (2 * p + 5) / 6) * logdet
    df = p * (p - 1) / 2
    return chi2, df, stats.chi2.sf(chi2, df)


def pca_first_component(X: np.ndarray):
    """第一主成分：返回 (方差解释率, 各变量载荷)"""
    Z = (X - X.mean(0)) / X.std(0, ddof=1)
    R = np.corrcoef(Z, rowvar=False)
    val, vec = np.linalg.eigh(R)
    order = np.argsort(val)[::-1]
    val, vec = val[order], vec[:, order]
    load = vec[:, 0] * np.sqrt(val[0])
    if load.sum() < 0:      # 方向规范化，保证词频越高得分越高
        load = -load
    score = Z @ vec[:, 0]
    if np.corrcoef(score, Z.sum(1))[0, 1] < 0:
        score = -score
    return val[0] / len(val), load, score


def main():
    df = pd.read_csv(TOKEN_DIR / "doc_terms.csv")
    df["year"] = df["year"].astype(int)

    # ---------- (1)(2) 维度密度与综合密度 ----------
    per_cn = df["n_cn"] / 1000.0                       # 每千中文字
    for d in DIMS:
        df[f"den_{d}"] = df[f"cnt_{d}"] / per_cn
    den_cols = [f"den_{d}" for d in DIMS]
    df["Den"] = df[den_cols].sum(axis=1)
    df["DigTrans"] = np.log1p(df["Den"])               # 主指标 (3)
    df["DigTrans_raw"] = df[[f"cnt_{d}" for d in DIMS]].sum(axis=1)

    # ---------- (4) 熵权法（对全体样本按维度归一化，标准熵权法口径） ----------
    X = df[den_cols].to_numpy()
    X = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0) + EPS)   # 极差标准化
    P = X / X.sum(axis=0, keepdims=True)
    N = len(df)
    k = 1.0 / np.log(N)
    e = -k * (P * np.log(P + EPS)).sum(axis=0)
    w = (1 - e) / (1 - e).sum()
    df["DigTrans_ew"] = np.log1p(df[den_cols].to_numpy() @ w)
    pd.DataFrame({"dimension": DIMS, "entropy": e, "weight": w}).to_csv(
        TABLE_DIR / "table_entropy_weight.csv", index=False, encoding="utf-8-sig")

    # ---------- (5) 因子得分 ----------
    var_exp, load, score = pca_first_component(df[den_cols].to_numpy())
    df["DigTrans_pca"] = score

    # ---------- 信度检验 ----------
    X5 = df[den_cols].to_numpy()
    alpha = cronbach_alpha(X5)
    alpha_z = cronbach_alpha((X5 - X5.mean(0)) / X5.std(0, ddof=1))
    h1 = df[[f"h1_{d}" for d in DIMS]].sum(axis=1) / per_cn
    h2 = df[[f"h2_{d}" for d in DIMS]].sum(axis=1) / per_cn
    r_half = stats.spearmanr(h1, h2).statistic
    item_total = [stats.spearmanr(df[c], df["DigTrans"]).statistic for c in den_cols]
    rel = pd.DataFrame({
        "指标": ["Cronbach's α（五维密度）", "Cronbach's α（标准化后）",
                 "分半相关 r", "Spearman-Brown 分半信度",
                 "各维度与总指标相关系数区间"],
        "取值": [f"{alpha:.4f}", f"{alpha_z:.4f}", f"{r_half:.4f}",
                 f"{spearman_brown(r_half):.4f}",
                 f"{min(item_total):.4f} ~ {max(item_total):.4f}"],
        "判断标准": ["α>0.7 可接受，>0.8 良好"] * 2 + ["r>0.7", ">0.8", ">0.5"],
    })
    rel.to_csv(TABLE_DIR / "table3_reliability.csv", index=False, encoding="utf-8-sig")

    # ---------- 效度检验 ----------
    Xs = (X5 - X5.mean(0)) / X5.std(0, ddof=1)
    R = np.corrcoef(Xs, rowvar=False)
    k_kmo = kmo(R)
    chi2, bdf, bp = bartlett(Xs)
    truth = pd.read_csv(TOKEN_DIR.parent / "firm_year_truth.csv")
    m = df.merge(truth[["stock_code", "year", "theta"]], on=["stock_code", "year"], how="left")
    rho_truth = stats.spearmanr(m["DigTrans"], m["theta"]).statistic
    rho_len = stats.spearmanr(df["DigTrans"], df["n_cn"]).statistic

    val = pd.DataFrame([
        ("结构效度", "KMO 取样适切性量数", f"{k_kmo:.4f}", ">0.6 可接受，>0.8 良好"),
        ("结构效度", "Bartlett 球形检验 χ²(df)", f"{chi2:.2f}({bdf:.0f})", "p<0.001"),
        ("结构效度", "Bartlett 检验 p 值", f"{bp:.3e}", "p<0.001"),
        ("结构效度", "第一主成分方差解释率", f"{var_exp:.2%}", ">40%"),
        ("结构效度", "第一主成分载荷区间", f"{load.min():.3f} ~ {load.max():.3f}", ">0.5"),
        ("效标效度", "与人工编码得分 Spearman ρ", f"{rho_truth:.4f}", ">0.6"),
        ("区分效度", "与文档篇幅的 Spearman ρ", f"{rho_len:.4f}", "|ρ|<0.5（不单纯由篇幅驱动）"),
    ], columns=["检验类别", "统计量", "取值", "判断标准"])
    val.to_csv(TABLE_DIR / "table4_validity.csv", index=False, encoding="utf-8-sig")

    out = df[["doc_id", "stock_code", "year", "n_cn", "Den", "DigTrans",
              "DigTrans_raw", "DigTrans_ew", "DigTrans_pca"] + den_cols]
    out.to_csv(TOKEN_DIR / "dig_index.csv", index=False, encoding="utf-8-sig")

    print(f"[s3] 测度构建完成：α={alpha:.3f}，分半信度={spearman_brown(r_half):.3f}，"
          f"KMO={k_kmo:.3f}，与真值ρ={rho_truth:.3f}，"
          f"DigTrans 均值 {df.DigTrans.mean():.3f}（SD {df.DigTrans.std():.3f}）")


if __name__ == "__main__":
    main()
