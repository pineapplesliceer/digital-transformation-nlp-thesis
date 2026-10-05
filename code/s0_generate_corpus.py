# -*- coding: utf-8 -*-
"""
Step 0  预演语料与仿真数据生成器（仅用于毕业论文“预演”阶段）
--------------------------------------------------------------------------
【重要说明｜学术诚信】
本研究处于“预演（选题与设计验证）”阶段，尚未获得商用数据库的完整授权。
为验证“文本挖掘→测度构建→面板回归”全流程是否可行，本脚本按照真实年报语料的
统计特征（行业分布、篇幅、关键词长尾分布、企业间与年份间的方差结构）生成
**仿真语料（synthetic corpus）**，并公开全部数据生成过程（DGP），
使得他人可以完整复现；正式研究与送审版论文将把本步骤替换为
“巨潮资讯网年报 PDF 抓取 + 文本抽取”，其余 s1—s5 代码无需修改。

DGP（数据生成过程）：
  真实数字化强度 θ_it = φ_i(企业固定效应) + δ·(t-2015)(时间趋势) + ω·行业效应 + ε
  语料关键词提及次数  m_it ~ Poisson( exp(θ_it) )，关键词按维度权重多项式抽样
  企业绩效          ROA_it = β·θ_it + γ'Controls + μ_i + λ_t + ν_it
  由于 θ 只进入文本生成过程、回归时使用**从文本反推的测度 DigTrans**，
  因此“测量误差 → 衰减偏误”这一真实研究中的核心问题在预演中被保留。
"""
import json
import numpy as np
import pandas as pd

from config import (RAW_TEXT_DIR, DATA_DIR, YEAR_START, YEAR_END, N_FIRM,
                    RANDOM_SEED, INDUSTRIES, DIG_DICT)

rng = np.random.default_rng(RANDOM_SEED)

DIMS = list(DIG_DICT.keys())
# 各维度在语料中出现的基准强度（模拟真实语料中“应用类”词多于“区块链”类词）
DIM_BASE = {"人工智能技术": 0.52, "大数据技术": 0.62, "云计算技术": 0.48,
            "区块链技术": 0.26, "数字技术应用": 0.95}

# 句式生成池：以“主语 × 动词 × 环节”组合生成高度多样的句子，
# 保证清洗环节的句子级去重不会把语料压缩（真实年报的句子重复度也远低于模板）。
SUBJ = ["公司", "报告期内公司", "本集团", "公司管理层", "公司上下", "各生产基地"]
DIG_VERB = ["持续加大", "重点布局", "全面深化", "加快推动", "稳步推进",
            "积极部署", "深入拓展", "系统推进"]
DIG_ACT = ["在生产制造环节的落地应用", "与业务流程的深度融合", "在供应链管理中的协同应用",
           "在研发设计环节的推广", "在市场营销环节的应用", "在质量管理环节的实践",
           "在客户服务环节的延伸", "在仓储物流环节的贯通"]
NEG_TPL = ["受资金与人才储备制约，{subj}{kw}相关业务尚未大规模落地。",
           "{subj}暂未布局{kw}，相关工作仍处于可行性论证阶段。",
           "由于订单结构以传统产品为主，{subj}对{kw}的投入较为有限。"]
NEUT_SUBJ = ["公司", "报告期内", "本集团", "公司管理层", "各子公司", "本期"]
NEUT_VERB = ["持续加强", "稳步推进", "进一步优化", "不断完善", "着力提升",
             "有效控制", "稳步提升", "有序开展"]
NEUT_OBJ = ["质量管理体系建设", "产品一次交验合格率", "供应链协同效率", "客户结构调整",
            "产能布局优化", "安全环保设施运行", "人才梯队建设", "海外渠道拓展",
            "成本费用管控", "库存周转效率", "售后服务体系", "研发人员引进力度",
            "应收账款回收管理", "生产设备维护保养", "品牌影响力建设", "原材料采购管理"]
NEUT_SUF = ["，以提升整体运营效率。", "，为后续经营发展奠定基础。", "，经营质量总体保持稳定。",
            "，相关指标较上年有所改善。", "，未发生重大安全生产事故。"]


def build_firms():
    """生成企业基本信息与真实（潜在）数字化强度 θ_it"""
    codes, names = [], []
    pool = [f"{pre}{n}" for pre in ["000", "002", "300", "600", "601", "603"]
            for n in range(100, 999)]
    chosen = rng.choice(pool, size=N_FIRM, replace=False)   # 保证股票代码唯一
    for i in range(N_FIRM):
        codes.append(str(chosen[i]))
        names.append(f"{rng.choice(list('华联信通新中科智远创'))}联"
                     f"{rng.choice(list('电子机械科技材料智能装备'))}份")
    firms = pd.DataFrame({
        "stock_code": codes,
        "firm_name": names,
        "industry": rng.choice(INDUSTRIES, size=N_FIRM),
        "soe": rng.binomial(1, 0.32, size=N_FIRM),
        "list_year": rng.integers(1995, 2016, size=N_FIRM),
    })
    # 企业固定效应：部分企业天然更数字化
    firms["theta_fe"] = 0.55 + 1.30 * rng.beta(2, 4, size=N_FIRM) + 0.30 * firms["soe"]
    return firms


def build_truth(firms):
    """生成企业-年份的真实数字化强度与财务基本面（模拟 CSMAR 财务数据）"""
    ind_eff = {ind: v for ind, v in zip(INDUSTRIES, rng.normal(0, 0.15, len(INDUSTRIES)))}
    rows = []
    for _, f in firms.iterrows():
        size0 = rng.normal(22.2, 1.1)      # ln(总资产)
        roa_i = rng.normal(0.045, 0.022)   # 企业绩效固定效应
        e_prev = 0.0                       # 数字化强度的持续性成分（AR(1)）
        high_tech = f["industry"] in ("C39", "C35", "C40")
        # 异质性设定：高技术行业数字化的边际效应更强，国有企业略弱
        b_theta = 0.014 + 0.006 * float(high_tech) - 0.0025 * float(f["soe"])
        for y in range(YEAR_START, YEAR_END + 1):
            trend = 0.055 * (y - YEAR_START)                       # 数字化转型的时代趋势
            # 企业数字化具有强持续性：AR(1) 成分 + 暂时性冲击
            e_persist = 0.82 * e_prev + rng.normal(0, 0.18)
            e_prev = e_persist
            theta = (f["theta_fe"] + trend + ind_eff[f["industry"]]
                     + e_persist + rng.normal(0, 0.10))
            theta = max(theta, 0.05)
            size = size0 + 0.06 * (y - YEAR_START) + rng.normal(0, 0.09)
            lev = np.clip(rng.normal(0.42, 0.16) - 0.0015 * (y - YEAR_START), 0.05, 0.92)
            growth = rng.normal(0.10, 0.22) - 0.004 * (y - YEAR_START)
            first = np.clip(rng.normal(0.33, 0.13), 0.05, 0.78)
            indep = np.clip(rng.normal(0.375, 0.05), 0.25, 0.60)
            capital = np.clip(rng.normal(1.9, 0.7), 0.5, 6.0)
            age = np.log(y - f["list_year"] + 1)
            # ==== 绩效方程（真实数据生成过程；ROA 以小数计，输出时×100 转为百分比）====
            roa = (0.030 + b_theta * theta - 0.075 * lev + 0.028 * growth
                   - 0.004 * (size - 22.2) + 0.012 * (first - 0.33)
                   + 0.06 * (indep - 0.375) - 0.0035 * (capital - 1.9)
                   + roa_i + rng.normal(0, 0.018))
            # 数字化强度对市场估值的作用更强（预期先行）
            tobinq = (2.1 + 0.90 * theta - 0.35 * (size - 22.2) + 0.9 * growth
                      - 0.5 * lev + rng.normal(0, 1.0))
            # 全要素生产率：数字化通过技术改造提升效率（LP 法的简化模拟）
            tfp = (6.5 + 0.12 * theta + 0.02 * (size - 22.2) - 0.01 * capital
                   + rng.normal(0, 0.15))
            rows.append(dict(stock_code=f["stock_code"], firm_name=f["firm_name"],
                             industry=f["industry"], year=y, theta=theta,
                             Size=size, Lev=lev, Growth=growth, Age=age, First=first,
                             Indep=indep, Capital=capital, SOE=int(f["soe"]),
                             ROA=roa * 100, TobinQ=max(tobinq, 0.4), TFP_LP=tfp,
                             list_year=int(f["list_year"])))
    return pd.DataFrame(rows)


def gen_text(theta, year, industry_dims):
    """
    依据真实强度 θ 生成一段年报“管理层讨论与分析”语料。
    设计要点（与真实年报的统计特征一致）：
      (1) 篇幅近似固定（约 1900—2600 字），不随 θ 增长 —— 因此“词频密度”不会因
          文档变长而被稀释，测度与真实强度保持单调关系；
      (2) 五个维度各自独立服从 Poisson( μ_d )，μ_d = A·exp(λθ)·w_d，
          即在“企业数字化强度 θ”这一共同因子上载荷不同、并带有独立测量噪声，
          这正是后续 Cronbach's α 与因子分析能够进行的前提。
    """
    dims, weights = [], []
    for d in DIMS:
        w = DIM_BASE[d] * industry_dims.get(d, 1.0)
        dims.append(d)
        weights.append(w)
    weights = np.array(weights) / np.sum(weights)

    # 目标篇幅先独立给定，确保“词频密度”不会因文档变长而被稀释
    target_len = int(rng.integers(4200, 6200))         # MD&A 摘录约 4200—6200 字
    cap = int(target_len * 0.70 / 32)                  # 数字化相关句子的数量上限

    # (2) 五维独立 Poisson 计数过程：共同因子 θ + 维度载荷 w_d + 独立测量噪声
    A, lam = 30.0, 0.70
    cnt = {d: int(rng.poisson(A * np.exp(lam * theta) * weights[i]))
           for i, d in enumerate(dims)}
    tot = sum(cnt.values())
    if tot > cap:                                      # 超出篇幅容量则按比例压缩
        cnt = {d: int(round(cnt[d] * cap / tot)) for d in dims}

    paras = []
    for i, d in enumerate(dims):
        for _ in range(cnt[d]):
            kw = str(rng.choice(DIG_DICT[d]))
            if rng.random() < 0.08:                    # 约 8% 为否定语境句（供 T4 规则识别）
                paras.append(str(rng.choice(NEG_TPL)).format(
                    subj=str(rng.choice(SUBJ)), kw=kw))
            else:
                paras.append(f"{rng.choice(SUBJ)}{rng.choice(DIG_VERB)}{kw}"
                             f"{rng.choice(DIG_ACT)}。")

    # (1) 用与数字化无关的经营性表述填充至目标篇幅，制造“噪声文本”
    used = sum(len(p) for p in paras) + 30
    n_fill = max(6, int(round((target_len - used) / 30)))
    for _ in range(n_fill):
        paras.append(f"{rng.choice(NEUT_SUBJ)}{rng.choice(NEUT_VERB)}"
                     f"{rng.choice(NEUT_OBJ)}{rng.choice(NEUT_SUF)}")

    rng.shuffle(paras)
    title = f"第四节 管理层讨论与分析（{year}年度）"
    return title + "\n" + "".join(paras)


def main():
    firms = build_firms()
    truth = build_truth(firms)
    truth.to_csv(DATA_DIR / "firm_year_truth.csv", index=False, encoding="utf-8-sig")

    # 行业对数字化的结构差异（如 C39 计算机通信设备更数字化）
    ind_dims = {ind: {} for ind in INDUSTRIES}
    for ind in INDUSTRIES:
        for d in DIMS:
            ind_dims[ind][d] = float(np.clip(rng.normal(1.0, 0.15), 0.6, 1.5))

    n = 0
    for _, r in truth.iterrows():
        txt = gen_text(r["theta"], int(r["year"]), ind_dims[r["industry"]])
        (RAW_TEXT_DIR / f"{r['stock_code']}_{r['year']}.txt").write_text(txt, encoding="utf-8")
        n += 1
    meta = {"n_firm": N_FIRM, "years": [YEAR_START, YEAR_END], "n_doc": n,
            "seed": RANDOM_SEED, "corpus": "synthetic MD&A corpus (预演用)",
            "gen_time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}
    (DATA_DIR / "corpus_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
    print(f"[s0] 生成语料 {n} 篇，企业 {N_FIRM} 家，区间 {YEAR_START}-{YEAR_END}，"
          f"文件写入 {RAW_TEXT_DIR}")


if __name__ == "__main__":
    main()
