# GitHub 仓库与更新说明

本仓库已上线：<https://github.com/pineapplesliceer/digital-transformation-nlp-thesis>

## 一、在线阅读入口

| 用途 | 链接 |
|---|---|
| 仓库主页 | <https://github.com/pineapplesliceer/digital-transformation-nlp-thesis> |
| **网页版论文**（排版稿，浏览器直接读） | <https://pineapplesliceer.github.io/digital-transformation-nlp-thesis/> |
| 在线读正文（Markdown 渲染） | [paper/论文正文.md](https://github.com/pineapplesliceer/digital-transformation-nlp-thesis/blob/main/paper/%E8%AE%BA%E6%96%87%E6%AD%A3%E6%96%87.md) |
| Word 论文下载 | [paper/基于年报文本挖掘的…….docx](https://github.com/pineapplesliceer/digital-transformation-nlp-thesis/blob/main/paper/%E5%9F%BA%E4%BA%8E%E5%B9%B4%E6%8A%A5%E6%96%87%E6%9C%AC%E6%8C%96%E6%8E%98%E7%9A%84%E4%BC%81%E4%B8%9A%E6%95%B0%E5%AD%97%E5%8C%96%E8%BD%AC%E5%9E%8B%E6%B5%8B%E5%BA%A6%E5%8F%8A%E5%85%B6%E5%AF%B9%E4%BC%81%E4%B8%9A%E7%BB%A9%E6%95%88%E7%9A%84%E5%BD%B1%E5%93%8D%E7%A0%94%E7%A9%B6.docx) |
| 全部结果表 | <https://github.com/pineapplesliceer/digital-transformation-nlp-thesis/tree/main/output/tables> |

> ⚠️ GitHub **不会渲染 `.docx` 正文**：点进 Word 文件页只会看到文件大小与 **Download** 按钮。
> 想在浏览器里直接读到论文，请用**网页版论文**或 **Markdown 正文**链接。

## 二、仓库现状

- 可见性：**公开（Public）**；默认分支：`main`
- 远端文件：44 个，仓库主体约 1.4 MB
- 网页版论文由 **GitHub Pages** 托管（Settings → Pages → Source: `main` / `/docs`）
- 域名生效通常需要 1—2 分钟，首次访问若 404 稍等再刷新

被 `.gitignore` 排除的目录（`data/raw_text/`、`data/clean_text/`、`data/tokens/`）
是**可再生的批量中间语料**，执行 `cd code && python run_all.py s0 s1 s2` 即可重建，
因此不入库，以保持仓库轻量。

## 三、日后怎么更新论文

论文改动后，本地重新生成 Word 并同步到仓库：

```bash
cd "C:/Users/kakak/WorkBuddy/2026-10-05-15-33-18"
git add -A
git commit -m "更新论文"
git push origin main
```

首次推送时 Git Credential Manager 会弹出浏览器要求登录 GitHub 并授权；
之后凭据会被记住，再推送就不需要重复登录。

> 注意：本次仓库内容是通过 GitHub REST API 上传的（沙箱环境访问不到 `github.com`
> 网页域，无法直接 `git push`）。因此远端提交历史是 API 逐步提交形成的（每个文件一条，
> 共 55 条），与本地 6 条提交记录不是同一条线。**文件内容完全一致**
> （已逐个比对 blob sha，46/46 全部匹配），但若日后 `git push` 报
> `non-fast-forward`，执行一次下面这条对齐即可，之后即可正常推送：
>
> ```bash
> git fetch origin && git reset --hard origin/main
> ```

## 四、安全提醒

上传用的 Personal Access Token 曾明文出现在对话中，**请在确认传输完成后立即撤销**：

1. 打开 <https://github.com/settings/tokens>
2. 找到对应令牌（Note 大概含 `thesis`）→ 点 **Delete** 撤销

日后如需再给我一个令牌，建议：用 **Tokens (classic)**、勾 `repo`、
有效期设 **7 天**、用完即删。令牌只需通过环境变量传入，不会被写入任何文件。
