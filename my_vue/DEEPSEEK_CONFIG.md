# DeepSeek API 配置指南

## 问题：点击"生成报告"后显示"暂无报告内容"

这个问题通常是由于 DeepSeek API 未正确配置导致的。

## 解决方案

### 1. 获取 DeepSeek API 密钥

1. 访问 [DeepSeek 官网](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API Key 并复制

### 2. 配置环境变量

在项目根目录（`my_vue` 文件夹）下已经创建了 `.env` 文件，请按以下步骤配置：

1. 打开 `.env` 文件
2. 将 `VITE_DEEPSEEK_API_KEY` 的值替换为你的真实 API 密钥：

```env
# DeepSeek API 配置

# DeepSeek API 密钥（请替换为您的真实密钥）
VITE_DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# DeepSeek API 地址
VITE_DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
```

### 3. 重启开发服务器

配置完成后，必须重启开发服务器才能生效：

```bash
# 停止当前运行的服务器（Ctrl+C）
# 然后重新启动
npm run serve
```

### 4. 测试报告生成

1. 在销量驱动页面选择要分析的卡片
2. 点击"分析报告" -> "生成报告"
3. 等待 AI 分析完成

## 常见问题

### Q1: 配置后仍然显示"暂无报告内容"

**可能原因：**
- 未重启开发服务器
- API 密钥无效或已过期
- 网络连接问题

**解决方法：**
1. 确保已重启开发服务器
2. 检查浏览器控制台（F12）查看详细错误信息
3. 验证 API 密钥是否正确
4. 检查网络连接

### Q2: 显示 "API Key 未配置" 错误

**解决方法：**
1. 确认 `.env` 文件在项目根目录（与 `package.json` 同级）
2. 确认环境变量名称正确：`VITE_DEEPSEEK_API_KEY`（注意 `VITE_` 前缀）
3. 确认 API 密钥不是示例值（`your_api_key_here` 或 `sk-your-api-key-here`）
4. 重启开发服务器

### Q3: 显示网络请求失败

**可能原因：**
- 无法访问 DeepSeek API（可能需要代理）
- API URL 配置错误
- 防火墙拦截

**解决方法：**
1. 检查网络连接
2. 如果在国内，可能需要配置代理
3. 验证 `VITE_DEEPSEEK_API_URL` 配置是否正确

## 技术说明

### 环境变量加载机制

Vue 3 + Vite 项目使用 `import.meta.env` 来访问环境变量：
- 环境变量必须以 `VITE_` 开头才能在客户端代码中访问
- `.env` 文件在开发服务器启动时加载
- 修改 `.env` 后必须重启服务器

### 报告生成流程

1. 用户选择卡片并点击"生成报告"
2. 系统提取选中卡片的数据（`dataExtractor.js`）
3. 构建分析提示词（`deepseek.js`）
4. 调用 DeepSeek API 进行流式生成
5. 实时显示生成的报告内容

### 调试方法

打开浏览器控制台（F12），查看以下信息：

```javascript
// 检查环境变量是否加载
console.log(import.meta.env.VITE_DEEPSEEK_API_KEY)
console.log(import.meta.env.VITE_DEEPSEEK_API_URL)

// 查看报告生成过程的日志
// 会显示：
// - 开始生成报告
// - cardData 内容
// - API 调用状态
// - 收到的数据块
// - 错误信息（如果有）
```

## 安全提示

⚠️ **重要：不要将 `.env` 文件提交到 Git 仓库！**

`.env` 文件已添加到 `.gitignore`，但请确保：
1. 不要在代码中硬编码 API 密钥
2. 不要在公开的地方分享 API 密钥
3. 定期更换 API 密钥
4. 使用 `.env.example` 作为配置模板

## 联系支持

如果以上方法都无法解决问题，请：
1. 检查浏览器控制台的完整错误信息
2. 查看 DeepSeek API 文档
3. 联系技术支持
