# -*- coding: utf-8 -*-
"""
doc-formatter / Stage 2 内部工具：把 Stage 1 的 Markdown 终稿渲染为
academic-paper 模板版式的 HTML（供 Stage 3 html-to-docx 转换）。
样式全部走 design-token 的 CSS 变量，禁止裸值；结构化内容一律用 <table>。
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE1 = ROOT / "output" / "thesis-docx" / "stage1" / "final_draft.md"
STAGE2 = ROOT / "output" / "thesis-docx" / "stage2"
TOKENS = Path("C:/Users/kakak/.workbuddy/plugins/cache/workbuddy-builtin/tencent-docx/"
              "5.6.2-wb.39306529.g21b643f7.he233403f909a/skills/design-token/"
              "tokens/compiled/academic-paper.json")
STAGE2.mkdir(parents=True, exist_ok=True)


def inline(t: str) -> str:
    """行内 Markdown → HTML（先转义，再处理行内标记）"""
    t = html.escape(t, quote=False)
    t = re.sub(r"\\\*", "\x00", t)          # 保护转义星号
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t.replace("\x00", "*")


def split_long(text: str, limit: int = 450):
    """超过 limit 字符的纯文本段落按句号断段（含行内标签的段落不拆，避免破坏标签）"""
    if "<" in text or len(text) <= limit:
        return f"<p>{text}</p>"
    parts, cur = [], ""
    for seg in text.split("。"):
        seg = seg + "。"
        if len(cur) + len(seg) > limit and cur:
            parts.append(cur)
            cur = seg
        else:
            cur += seg
    if cur:
        parts.append(cur)
    return "\n".join(f"<p>{x}</p>" for x in parts)


def parse_table(rows):
    """GFM 表格 → 三线表"""
    head = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    body = []
    for r in rows[2:]:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        if len(cells) < len(head):
            cells += [""] * (len(head) - len(cells))
        body.append(cells[:len(head)])
    out = ['<table class="three-line-table"><thead><tr>']
    out += [f"<th>{inline(c)}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def main():
    md = STAGE1.read_text(encoding="utf-8")
    lines = md.split("\n")

    title, subtitle, info_rows = "", "", []
    abstract, keywords, refs = "", "", []
    refs_heading = ""
    toc, sections = [], []
    LEADS = {
        "一、绪论": "本部分交代选题的现实与政策背景、研究的理论与现实意义，梳理已有文献的三条脉络并识别研究缺口，最后给出研究思路与全文结构安排。",
        "二、研究方法与数据": "本部分说明样本选择口径、文本预处理与关键词计数规则、数字化转型测度的构造公式、变量定义以及计量模型设定与检验策略，是全文可复现性的核心依据。",
        "三、实证分析": "本部分依次报告描述性统计、信度与效度检验、相关性分析、基准回归、稳健性检验、异质性分析、内生性处理与补充的分类任务，并讨论各项结果的经济含义。",
        "四、结论、局限与展望": "本部分归纳三项主要发现，给出理论与实践启示，坦诚说明数据代表性、测度构造、识别策略与边界条件四方面的局限，并指出后续研究的方向。",
        "附录 A　数据来源说明": "本附录汇总论文全部数据的来源渠道、获取方式与本稿所处状态。",
        "附录 B　可复现代码与复现说明": "本附录给出全部脚本的功能与产物对应关系，以及一键复现步骤。",
    }
    buf, mode = [], None            # mode: 'abstract' | 'refs' | 'body'
    i = 0

    def flush_paras():
        """把缓冲区里的普通段落冲进当前容器"""
        nonlocal buf
        text = " ".join(x.strip() for x in buf).strip()
        buf = []
        if not text:
            return ""
        if mode == "refs":
            return f"<p class='ref-item'>{inline(text)}</p>"
        return split_long(inline(text))

    body_parts, abs_parts, ref_parts = [], [], []

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        # 表格块
        if s.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].strip()) <= set("|-: "):
            block = [s]
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                block.append(lines[j].strip())
                j += 1
            tbl = parse_table(block)
            (ref_parts if mode == "refs" else abs_parts if mode == "abstract" else body_parts).append(tbl)
            i = j
            continue

        if s.startswith("# ") and not title:
            title = s[2:].strip()
            i += 1
            continue
        if s.startswith("## ——"):
            subtitle = s[3:].strip()
            i += 1
            continue
        if s.startswith("**作者**"):
            info_rows.append(("学生姓名", "王晓珂"))
            info_rows.append(("学　　号", "202364029"))
            info_rows.append(("专　　业", "大数据管理与应用"))
            info_rows.append(("年　　级", "2023 级"))
            info_rows.append(("院　　系", "管理学院"))
            i += 1
            continue
        if s == "## 摘要":
            body_parts.append(flush_paras())
            mode = "abstract"
            i += 1
            continue
        if s.startswith("**关键词**"):
            keywords = s.replace("**关键词**：", "").replace("**关键词**:", "").strip()
            mode = "body"
            i += 1
            continue
        if s == "## 参考文献":
            body_parts.append(flush_paras())
            refs_heading = f'<h2 id="s{len(toc)}">参考文献</h2>'
            toc.append("参考文献")
            mode = "refs"
            i += 1
            continue
        if s.startswith("## "):
            body_parts.append(flush_paras())
            _t = s[3:].strip()
            body_parts.append(f'<h2 id="s{len(toc)}">{inline(_t)}</h2>')
            if LEADS.get(_t):
                body_parts.append(f"<p>{LEADS[_t]}</p>")
            toc.append(_t)
            mode = "body"
            i += 1
            continue
        if s.startswith("### "):
            body_parts.append(flush_paras())
            body_parts.append(f"<h3>{inline(s[4:].strip())}</h3>")
            i += 1
            continue
        if s.startswith("> "):
            body_parts.append(flush_paras())
            body_parts.append(f'<p class="formula">{inline(s[2:].strip())}</p>')
            i += 1
            continue
        if re.match(r"^\*\*表\s*\d+", s) or re.match(r"^表\s*\d+　", s):
            body_parts.append(flush_paras())
            body_parts.append(f'<p class="table-caption">{inline(s.strip("*"))}</p>')
            i += 1
            continue
        if s.startswith("注："):
            body_parts.append(flush_paras())
            body_parts.append(f'<p class="table-note">{inline(s)}</p>')
            i += 1
            continue

        if not s:
            par = flush_paras()
            if par:
                (ref_parts if mode == "refs" else abs_parts if mode == "abstract" else body_parts).append(par)
            i += 1
            continue

        # 参考文献条目
        if mode == "refs" and re.match(r"^\[\d+\]", s):
            par = flush_paras()
            if par:
                ref_parts.append(par)
            ref_parts.append(f"<p class='ref-item'>{inline(s)}</p>")
            i += 1
            continue

        buf.append(s)
        i += 1

    par = flush_paras()
    if par:
        (ref_parts if mode == "refs" else abs_parts if mode == "abstract" else body_parts).append(par)

    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    css_vars = "\n".join(f"    {k}: {v};" for k, v in tokens["css_variables"].items())
    (STAGE2 / "design_tokens.json").write_text(
        json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")

    toc_html = "\n".join(f'<li><a href="#s{k}">{html.escape(t)}</a></li>'
                         for k, t in enumerate(toc))
    info_html = "\n".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in info_rows)
    cover_title = html.escape(title)

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="docx-page-size" content="A4">
<title>{cover_title}</title>
<style>
@page {{ @bottom-center {{ content: counter(page); }} }}
@page cover {{ @bottom-center {{ content: none; }} }}
section[role="cover"] {{ page: cover; }}

:root {{
{css_vars}
    --fs-h1: var(--typography-fontSize-h1);
    --fs-h2: var(--typography-fontSize-h2);
    --fs-h3: var(--typography-fontSize-h3);
    --fs-body: var(--typography-fontSize-body);
    --fs-small: var(--typography-fontSize-caption);
    --fs-title: var(--typography-fontSize-title);
    --ff-heading: var(--typography-fontFamily-heading);
    --ff-body: var(--typography-fontFamily-body);
    --ff-latin: var(--typography-fontFamily-bodyLatin);
    --lh-body: var(--typography-lineHeight-body);
    --indent: var(--spacing-indent);
    --page-content-width: 16.0cm;
    --fs-note: 9pt;
    --fs-ref: 10.5pt;
    --sp-1: var(--sp-1); --sp-2: var(--sp-2); --sp-3: var(--sp-3); --sp-4: var(--sp-4);
    --sp-5: var(--sp-5); --sp-6: var(--sp-6); --sp-8: var(--sp-8);
    --sp-cover-top: 4.5cm; --sp-cover-bottom: 3.2cm;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: var(--ff-body);
  font-size: var(--fs-body);
  line-height: var(--lh-body);
  color: var(--color-text);
  background: var(--color-background);
  max-width: var(--page-content-width);
  margin-left: auto; margin-right: auto;
  padding: var(--layout-marginTop) 0 var(--layout-marginBottom) 0;
}}
h1, h2, h3 {{ font-family: var(--ff-heading); font-weight: var(--typography-fontWeight-heading); color: var(--color-heading); }}
h1 {{ font-size: var(--fs-h1); margin-bottom: var(--spacing-paragraph); }}
h2 {{ font-size: var(--fs-h2); margin-top: var(--spacing-sectionGap); margin-bottom: var(--spacing-paragraph); }}
h3 {{ font-size: var(--fs-h3); margin-top: var(--spacing-paragraph); margin-bottom: var(--spacing-paragraph); }}
p {{ margin-bottom: var(--spacing-paragraphAfter); text-indent: var(--indent); text-align: justify; }}
code {{ font-family: var(--typography-fontFamily-code); font-size: var(--fs-ref); }}

section[role="cover"] {{ text-align: center; }}
.cover-title {{ text-align: center; font-size: var(--fs-title); font-weight: var(--typography-fontWeight-heading); margin-top: var(--sp-cover-top); margin-bottom: 0.6cm; }}
.cover-subtitle {{ text-align: center; font-size: var(--fs-h3); margin-bottom: var(--sp-cover-bottom); text-indent: 0; }}
.cover-info-list {{ border-collapse: collapse; margin: 0 auto; }}
.cover-info-list td {{ padding: var(--sp-4) var(--sp-8); font-size: var(--fs-body); border: none; text-indent: 0; }}
.cover-info-list td:first-child {{ text-align: right; }}
.cover-info-list td:last-child {{ text-align: left; }}

.doc-toc {{ margin-bottom: var(--spacing-sectionGap); }}
.toc-title {{ text-align: center; font-family: var(--ff-heading); font-size: var(--fs-h2); font-weight: var(--typography-fontWeight-heading); text-indent: 0; margin-bottom: var(--sp-6); }}
.toc-list {{ list-style: none; padding-left: 0; }}
.toc-list li {{ margin-bottom: var(--sp-2); text-indent: 0; }}
.toc-list a {{ color: var(--color-text); text-decoration: none; }}

.abstract-text {{ text-indent: 0; font-size: var(--typography-fontSize-abstract); line-height: var(--typography-lineHeight-abstract); }}
.keywords {{ text-indent: 0; font-size: var(--typography-fontSize-abstract); margin-top: var(--sp-5); }}

.three-line-table {{ border-collapse: collapse; width: 100%; margin-bottom: var(--spacing-paragraphAfter); }}
.three-line-table th, .three-line-table td {{ padding: var(--sp-3) var(--sp-5); text-align: center; font-size: var(--fs-small); border: none; text-indent: 0; }}
.three-line-table thead tr {{ border-top: 1.5pt solid var(--color-tableBorder); border-bottom: 0.75pt solid var(--color-tableBorder); }}
.three-line-table tbody tr:last-child {{ border-bottom: 1.5pt solid var(--color-tableBorder); }}
.three-line-table td:first-child, .three-line-table th:first-child {{ text-align: left; }}

.table-caption {{ text-align: center; text-indent: 0; font-family: var(--ff-heading); font-size: var(--fs-small); font-weight: var(--typography-fontWeight-heading); margin-top: var(--sp-6); margin-bottom: var(--sp-1); }}
.table-note {{ text-indent: 0; font-size: var(--fs-note); color: var(--color-text); margin-bottom: var(--sp-8); }}
.formula {{ text-indent: 0; text-align: center; font-family: var(--ff-latin); margin: var(--sp-5) 0; }}
.ref-item {{ text-indent: 0; font-size: var(--fs-ref); margin-bottom: var(--sp-4); }}
</style>
</head>
<body>
<section role="cover">
  <h1 class="cover-title">{cover_title}</h1>
  <p class="cover-subtitle">{html.escape(subtitle)}</p>
  <table class="cover-info-list">
    <tbody>
{info_html}
    </tbody>
  </table>
</section>

<section role="body" data-page-restart="1">
  <div class="doc-toc">
    <p class="toc-title">目　录</p>
    <ol class="toc-list">
{toc_html}
    </ol>
  </div>
  <div class="abstract">
    <p class="toc-title" style="text-align:center">摘　要</p>
    {"".join(abs_parts)}
    <p class="keywords"><strong>关键词：</strong>{html.escape(keywords)}</p>
  </div>
  <main class="paper-body">
{"".join(body_parts)}
  </main>
  <div class="references">
    {refs_heading}
    <div class="ref-list">
{"".join(ref_parts)}
    </div>
  </div>
</section>
</body>
</html>
"""
    out = STAGE2 / "formatted-企业数字化转型测度.html"
    out.write_text(doc, encoding="utf-8")
    print(f"[stage2] HTML 已生成：{out}（{len(doc)} 字符，{len(toc)} 个章节，"
          f"{doc.count('three-line-table')//2} 张表）")


if __name__ == "__main__":
    main()
