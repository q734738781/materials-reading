# AI for Materials 文献精读

材料设计、原子模拟与科研智能体的中文文献阅读站。支持八话题筛选、关键词检索、日期排序、独立文章链接和数学公式。

## 发布到 GitHub Pages

将本目录推送到独立的公开仓库（建议 `materials-reading`），在 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。首次部署完成后可访问 `https://<username>.github.io/materials-reading/`。

`dist/` 已包含可直接发布的静态网页。仓库不包含论文 PDF、邮箱数据、队列文件、密钥或本机路径。CI 也会拒绝发布 PDF。

## 更新文献

本机保存新的 Markdown 精读卡后重新导出，再提交 `dist/` 的变化即可。导出只读原始卡片；只复制正文引用的图片。

```sh
python -m pip install -r requirements.txt
python scripts/export.py --source /path/to/reading-cards --queue /path/to/digest-state.json
python -m http.server 8765 --directory dist
```

图片与摘要译文保留论文来源。论文原图、原始摘要及其译文不适用网站代码的开放许可，不声称取得统一转载授权。数学公式使用固定版本 MathJax，中文衬线字体有系统字体后备。
