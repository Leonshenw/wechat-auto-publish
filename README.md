# 微信公众号自动发布 - GitHub Actions 部署指南

## 📋 功能说明

- ✅ 每天 **10:00** 和 **15:00**（北京时间）自动执行
- ✅ 搜索科技热点，生成刘润风格文章（1500-2000字）
- ✅ 自动上传到公众号草稿箱
- ✅ 完全免费，24小时运行

---

## 🚀 部署步骤

### 第一步：创建 GitHub 仓库

1. 登录 https://github.com
2. 点击右上角 `+` → `New repository`
3. 仓库名：`wechat-auto-publish`
4. 选择 `Public` 或 `Private`
5. 勾选 `Add a README file`
6. 点击 `Create repository`

---

### 第二步：上传代码

**方法 A：使用 Git 命令行**

```bash
# 克隆仓库
git clone https://github.com/你的用户名/wechat-auto-publish.git
cd wechat-auto-publish

# 复制本目录所有文件到仓库
cp -r * .github/ .

# 提交并推送
git add .
git commit -m "初始化：公众号自动发布"
git push origin main
```

**方法 B：直接在 GitHub 网页上传**

1. 进入你的仓库
2. 点击 `Add file` → `Upload files`
3. 上传本目录所有文件
4. 提交

---

### 第三步：设置 GitHub Secrets

1. 进入仓库 → `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`
3. 添加以下 Secrets：

| Name | Value | 说明 |
|------|-------|------|
| `WECHAT_APPID` | `wx22254d05de1f5809` | 公众号 AppID |
| `WECHAT_APPSECRET` | `9kQK7UXFCfHP7CxLiTbrDzyNsCXCfPksJME5XrbPcCoD` | 公众号 AppSecret |
| `OPENAI_API_KEY` | `sk-...` | OpenAI API Key（可选） |

**注意：** 如果没有 OpenAI API Key，脚本会使用模板文章。

---

### 第四步：启用 GitHub Actions

1. 进入仓库 → `Actions`
2. 如果显示 "Workflows are disabled"，点击 `Enable workflows`
3. 等待几分钟，工作流会自动生效

---

## ✅ 验证部署

### 方法 1：手动触发

1. 进入仓库 → `Actions`
2. 选择 `公众号自动发文 - 上午10点`
3. 点击 `Run workflow` → `Run workflow`
4. 等待执行完成（约 2-5 分钟）
5. 查看日志，确认是否成功

### 方法 2：等待自动执行

- 北京时间 **10:00** 和 **15:00** 会自动触发
- 执行日志在 `Actions` 页面查看

---

## 📊 查看执行结果

1. 登录公众号后台：https://mp.weixin.qq.com
2. 点击左侧 `草稿箱`
3. 查看自动生成的文章

---

## 🔧 故障排查

### 问题 1：工作流没有自动执行

- 检查 `Actions` 是否已启用
- 检查仓库是否为 `Public`（Private 仓库有免费额度限制）

### 问题 2：文章生成失败

- 检查 `Secrets` 是否设置正确
- 查看 `Actions` 执行日志

### 问题 3：OpenAI API 调用失败

- 脚本会自动降级为模板文章
- 不影响整体流程

---

## 📝 注意事项

1. **免费额度**：GitHub Actions 免费提供 2000 分钟/月
   - 每次执行约 2-5 分钟
   - 每天 2 次，每月约 300 分钟
   - **完全够用！**

2. **封面图和配图**：当前版本使用模板，如需 AI 生成图片，需要配置图片生成 API

3. **文章质量**：建议配置 OpenAI API Key 以获得更好的文章质量

---

## 🆘 需要帮助？

如果遇到问题，可以：
1. 查看 `Actions` 页面的执行日志
2. 在仓库创建 `Issue`
3. 联系开发者

---

**🎉 部署完成后，你的公众号就会每天自动发布文章了！**
