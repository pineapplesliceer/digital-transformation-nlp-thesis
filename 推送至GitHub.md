# 把本仓库推送到 GitHub —— 两种方式（任选其一）

本地仓库**已经准备好**：42 个文件已提交到 `main` 分支，两次提交记录齐全，
`.gitignore` 已排除 27 MB 可再生语料与内部工作记忆，仓库主体约 1.4 MB。
剩下的只差"用你的账号建立一个远端仓库并推送"这一步。

- 本地路径：`C:\Users\kakak\WorkBuddy\2026-10-05-15-33-18`
- 提交记录：`git log --oneline` 应显示 2 条提交
- 工作区状态：`git status` 应为 clean

---

## 方式 A（推荐，最省事）：浏览器建仓 + 两条命令

### 第 1 步 × 在浏览器建空仓库
打开 <https://github.com/new>，填写：

| 字段 | 填什么 |
|---|---|
| Repository name | `digital-transformation-nlp-thesis` |
| Description | 毕业论文预演稿：基于年报文本挖掘的企业数字化转型测度及其对企业绩效的影响研究 |
| 可见性 | 勾 **Public**（想开网页版必须公开；也可勾 Private，只有你能打开链接） |
| Initialize this repository with | **什么都不要勾**（不要 README、不要 .gitignore、不要 License，否则会和本地提交冲突） |

点 **Create repository**。

### 第 2 步 × 在终端粘贴命令行
Windows 上打开 **Git Bash**（或把下面命令里的反斜杠路径在 CMD 中执行），
把 `<你的用户名>` 换成你的 GitHub 用户名（按你提供的信息是 `pineapplesliceer`）：

```bash
cd "C:/Users/kakak/WorkBuddy/2026-10-05-15-33-18"
git remote add origin https://github.com/<你的用户名>/digital-transformation-nlp-thesis.git
git branch -M main
git push -u origin main
```

推送时 **Git Credential Manager 会弹出浏览器窗口**要你登录 GitHub 并授权——
这一步在你自己电脑上能正常完成（我所在的沙箱访问不了 github.com 网页域，所以只能由你完成）。

### 第 3 步 × 开启网页版论文（可选，30 秒）
仓库页 → **Settings** → 左侧 **Pages** → Source 选 **Deploy from a branch** →
Branch 选 **main**、目录选 **/docs** → **Save**。
等 1—2 分钟后，论文就会在浏览器里以排版稿形式打开。

---

## 方式 B：给我一个有效令牌，我一次性完成建仓+上传+开 Pages

我这边 `api.github.com` 可直连，拿到有效令牌后可以全自动完成：
建仓 → 上传 42 个文件 → 设置默认分支 → 开启 GitHub Pages → 关联本地远端。

令牌要求（**权限越小越好**）：

1. 打开 <https://github.com/settings/tokens>
2. 推荐用 **Tokens (classic)** → **Generate new token (classic)**
   - Note：`thesis-upload-temp`
   - Expiration：**7 天**（用完就过期）
   - 勾选 **`repo`**（建仓与写文件必须；`workflow` 不需要）
3. 点 Generate，**完整复制** `ghp_` 开头的那串（40 个字符，务必整段复制，不要带空格）

> 上次失败的原因：令牌被 GitHub 判为 `Bad credentials`（无效）。
> 对照实验显示匿名请求正常返回 200、`api.github.com` 可直连、绕过代理同样 401，
> 因此与本机网络、代理、权限范围都无关，是令牌串本身的问题（漏字符 / 已过期 / 未最终生成）。
> 常见坑：页面关闭后令牌只显示一次，未点 **Generate token** 时复制到的是占位示例串。

**安全提醒**：令牌等同于密码。请在你确认推送成功后**立即到
<https://github.com/settings/tokens> 撤销（Delete）该令牌**，它的有效期请设为 7 天以内。

---

## 推送成功后会得到这些链接

把 `<用户名>` 换成你的用户名（预计为 `pineapplesliceer`）：

| 用途 | 链接 |
|---|---|
| 仓库主页（含 README 摘要） | `https://github.com/<用户名>/digital-transformation-nlp-thesis` |
| 网页版论文（排版稿，开启 Pages 后生效） | `https://<用户名>.github.io/digital-transformation-nlp-thesis/` |
| 在线读论文正文（Markdown 渲染） | `https://github.com/<用户名>/digital-transformation-nlp-thesis/blob/main/paper/%E8%AE%BA%E6%96%87%E6%AD%A3%E6%96%87.md` |
| **Word 论文下载页** | `https://github.com/<用户名>/digital-transformation-nlp-thesis/blob/main/paper/%E5%9F%BA%E4%BA%8E%E5%B9%B4%E6%8A%A5%E6%96%87%E6%9C%AC%E6%8C%96%E6%8E%98%E7%9A%84%E4%BC%81%E4%B8%9A%E6%95%B0%E5%AD%97%E5%8C%96%E8%BD%AC%E5%9E%8B%E6%B5%8B%E5%BA%A6%E5%8F%8A%E5%85%B6%E5%AF%B9%E4%BC%81%E4%B8%9A%E7%BB%A9%E6%95%88%E7%9A%84%E5%BD%B1%E5%93%8D%E7%A0%94%E7%A9%B6.docx` |
| 全部结果表 | `https://github.com/<用户名>/digital-transformation-nlp-thesis/tree/main/output/tables` |

> 说明：GitHub **不会渲染 `.docx` 正文**，点进 Word 文件页只会看到文件大小与 **Download** 按钮。
> 想在浏览器里直接"读到"论文，用上表中的**网页版论文**或 **Markdown 正文**链接。

## 仓库里都有什么

```
README.md        仓库首页说明（选题、声明、结果摘要、复现方法）
paper/           Word 论文稿 + Markdown 正文
code/            五步可复现流水线（run_all.py 一键复现约 80 秒）
data/            企业—年份面板 1620×22、真值表、清洗摘要
output/tables/   论文全部结果表（表 1—表 10）
docs/index.html  论文网页版（GitHub Pages 入口，右下角带 Word 下载按钮）
```

被 `.gitignore` 排除的目录（`data/raw_text/`、`data/clean_text/`、`data/tokens/`）
是**可再生的批量中间语料**，执行 `cd code && python run_all.py s0 s1 s2` 即可重建，
因此不入库，以保持仓库轻量。
