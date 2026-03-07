# 调试步骤 - 解决"暂无报告内容"问题

## 当前状态
已添加详细的调试日志，现在需要重启开发服务器并测试。

## 操作步骤

### 1. 重启开发服务器（重要！）

**必须重启才能加载 .env 文件中的环境变量**

```bash
# 在终端中按 Ctrl+C 停止当前服务器
# 然后重新启动
npm run serve
```

### 2. 打开浏览器控制台

1. 打开浏览器（Chrome/Edge）
2. 按 F12 打开开发者工具
3. 切换到 "Console"（控制台）标签
4. 清空之前的日志（点击 🚫 图标）

### 3. 测试报告生成

1. 进入销量驱动页面
2. 点击"分析报告"按钮
3. 选择一个或多个卡片（会看到卡片边框变蓝）
4. 点击"生成报告"

### 4. 查看控制台输出

你应该会看到以下日志输出：

```
=== generateReportFromSelection 被调用 ===
选中的卡片: ['trend', 'funnel', ...]
开始提取卡片数据...
=== extractCardData 被调用 ===
selectedCards: ['trend', 'funnel', ...]
处理卡片: trend
处理卡片: funnel
...
=== extractCardData 完成 ===
最终的 cardData: {trend: {...}, funnel: {...}}
cardData 的键: ['trend', 'funnel', ...]
提取的卡片数据: {trend: {...}, funnel: {...}}
准备显示报告模态框...
showReportModal 已设置为: true
=== generateReportFromSelection 执行完成 ===
ReportModal visible 变化: true
当前 reportContent: 
当前 cardData: {trend: {...}, funnel: {...}}
开始生成新报告...
开始生成报告，cardData: {trend: {...}, funnel: {...}}
cardData 键: ['trend', 'funnel', ...]
开始调用 DeepSeek API...
generateSalesReportStream 被调用
API Key 前缀: sk-829e1b
生成的 prompt 长度: xxxx
开始调用 DeepSeek API...
API URL: https://api.deepseek.com/v1/chat/completions
API 响应状态: 200 OK
开始读取流数据...
收到数据块: xxx
收到数据块: xxx
...
流数据读取完成，共收到 xx 个数据块
报告生成完成，内容长度: xxxx
```

## 可能的问题和解决方案

### 问题 1: 控制台没有任何输出

**原因：** 
- 没有重启开发服务器
- 代码没有保存
- 浏览器缓存问题

**解决方法：**
1. 确保所有文件已保存
2. 重启开发服务器
3. 硬刷新浏览器（Ctrl+Shift+R）

### 问题 2: 显示 "API Key 未配置"

**原因：** 环境变量未加载

**解决方法：**
1. 确认 `.env` 文件在项目根目录（与 package.json 同级）
2. 确认 API Key 不是示例值
3. 重启开发服务器
4. 在控制台执行：
   ```javascript
   console.log(import.meta.env.VITE_DEEPSEEK_API_KEY)
   ```
   应该显示你的 API Key

### 问题 3: cardData 为空对象 {}

**原因：** 数据提取失败

**解决方法：**
1. 检查是否选择了卡片
2. 查看控制台中 "处理卡片: xxx" 的日志
3. 检查 vm.currentDealer 是否有数据

### 问题 4: API 调用失败

**原因：** 
- 网络问题
- API Key 无效
- API 地址错误

**解决方法：**
1. 检查网络连接
2. 验证 API Key 是否有效
3. 查看控制台的错误信息

### 问题 5: 收到 [DONE] 但没有内容

**原因：** API 返回了空响应

**解决方法：**
1. 检查 prompt 是否正确生成
2. 查看 API 配额是否用完
3. 尝试使用更简单的 prompt 测试

## 快速测试环境变量

在浏览器控制台执行以下代码：

```javascript
// 测试环境变量
console.log('API Key:', import.meta.env.VITE_DEEPSEEK_API_KEY);
console.log('API URL:', import.meta.env.VITE_DEEPSEEK_API_URL);

// 测试 API Key 格式
const key = import.meta.env.VITE_DEEPSEEK_API_KEY;
if (!key) {
  console.error('❌ API Key 未配置');
} else if (key === 'your_api_key_here' || key === 'sk-your-api-key-here') {
  console.error('❌ API Key 是示例值，请替换为真实密钥');
} else if (key.startsWith('sk-')) {
  console.log('✅ API Key 格式正确');
} else {
  console.warn('⚠️ API Key 格式可能不正确');
}
```

## 下一步

完成上述步骤后，请将控制台的完整输出截图或复制给我，我会帮你进一步分析问题。

特别关注：
1. 是否有红色的错误信息
2. cardData 的内容是否为空
3. API 调用是否成功
4. 是否收到了数据块
