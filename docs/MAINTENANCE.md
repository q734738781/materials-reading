# 站点维护

## 目录

- `dist/`：可直接发布的静态网页、文章和图片。
- `scripts/export.py`：从本地 Markdown 文献卡生成站点。
- `scripts/check.py`：检查站内链接和发布内容。
- `.github/workflows/pages.yml`：GitHub Pages 发布流程。

## 更新文献

```sh
python -m pip install -r requirements.txt
python scripts/export.py --source /path/to/reading-cards --queue /path/to/digest-state.json
python scripts/check.py
python -m http.server 8765 --directory dist
```

导出只读原始卡片，复制正文引用的图片，保留摘要译文与论文链接；PDF 不进入发布目录。检查后提交 `dist/` 的变化并推送到 `main`，GitHub Actions 会更新网站。

首次发布时，在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。

数学公式使用固定版本 MathJax，中文字体有系统字体后备。
