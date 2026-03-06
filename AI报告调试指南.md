# AI 报告生成调试指南

## 问题：报告内容为空

### 调试步骤

#### 1. 打开浏览器控制台

按 `F12` 打开开发者工具，切换到 `Console` 标签。

#### 2. 生成报告并查看日志

点击"生成报告"后，控制台会输出详细的调试信息：

```
开始生成报告，cardData: {...}
generateSalesReportStream 被调用
cardData: {...}
API Key 前缀: sk-829e1b...
生成的 prompt 长度: 1234
prompt 预览: 请基于以下汽车经销商的销售数据...
开始调用 DeepSeek API...
API URL: https://api.deepseek.com/v1/chat/completions
API 响应状态: 200 OK
开始读取流数据...
收到数据块: ...
流数据读取完成，共收到 X 个数据块
报告生成完成，内容长度: 1234
```

#### 3. 检查可能的问题

##### 问题 A：cardData 为空
**日志显示**：
```
cardData: {}
```

**原因**：没有选择卡片或数据提取失败

**解决方案**：
1. 确保至少选择了一个卡片
2. 检查卡片是否正确高亮显示
3. 查看 `提取的卡片数据:` 日志

##### 问题 B：API 调用失败
**日志显示**：
```
API 响应状态: 401 Unauthorized
或
API 响应状态: 403 Forbidden
```

**原因**：API Key 无效或过期

**解决方案**：
1. 检查 `.env` 文件中的 API Key
2. 访问 https://platform.deepseek.com/ 验证 API Key
3. 检查 API Key 是否有余额

##### 问题 C：网络错误
**日志显示**：
```
DeepSeek 流式调用失败: TypeError: Failed to fetch
```

**原因**：网络连接问题或 CORS 错误

**解决方案**：
1. 检查网络连接
2. 检查是否能访问 api.deepseek.com
3. 检查防火墙设置

##### 问题 D：收到数据但不显示
**日志显示**：
```
收到数据块: ...
流数据读取完成，共收到 100 个数据块
报告生成完成，内容长度: 0
```

**原因**：数据接收但未正确拼接

**解决方案**：这是代码 bug，需要检查 onChunk 回调

##### 问题 E：API 返回错误
**日志显示**：
```
API 错误响应: {"error": {"message": "..."}}
```

**原因**：API 参数错误或服务异常

**解决方案**：查看错误信息，根据提示修复

### 快速测试

#### 测试 1：验证 API Key

在浏览器控制台运行：

```javascript
// 测试 API Key
fetch('https://api.deepseek.com/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer sk-829e1bc28fe145beae4780d96fd5d2df'
  },
  body: JSON.stringify({
    model: 'deepseek-chat',
    messages: [{role: 'user', content: '你好'}],
    stream: false
  })
})
.then(r => r.json())
.then(d => console.log('API 测试成功:', d))
.catch(e => console.error('API 测试失败:', e));
```

**预期结果**：
- 成功：返回 AI 的回复
- 失败：返回错误信息

#### 测试 2：验证数据提取

在浏览器控制台运行：

```javascript
// 查看当前页面的 Vue 实例
const vm = document.querySelector('.dashboard-container').__vue__;
console.log('当前经销商:', vm.currentDealer);
console.log('选中的卡片:', vm.selectedCards);
console.log('报告数据:', vm.reportCardData);
```

#### 测试 3：手动触发报告生成

```javascript
// 手动生成报告
const vm = document.querySelector('.dashboard-container').__vue__;
vm.selectedCards = ['trend', 'funnel'];
vm.generateReportFromSelection();
```

### 常见错误及解决方案

#### 错误 1：401 Unauthorized

```
API 响应状态: 401 Unauthorized
API 错误响应: {"error": {"message": "Invalid API key"}}
```

**解决方案**：
1. 检查 API Key 是否正确
2. 重启开发服务器（让 .env 生效）
3. 清除浏览器缓存

#### 错误 2：429 Too Many Requests

```
API 响应状态: 429 Too Many Requests
```

**解决方案**：
1. 等待几分钟后重试
2. 检查 API 使用配额
3. 升级 API 套餐

#### 错误 3：Network Error

```
DeepSeek 流式调用失败: TypeError: Failed to fetch
```

**解决方案**：
1. 检查网络连接
2. 尝试使用 VPN
3. 检查防火墙设置

#### 错误 4：CORS Error

```
Access to fetch at 'https://api.deepseek.com/...' from origin 'http://localhost:8080' has been blocked by CORS policy
```

**解决方案**：
这通常不应该发生，因为 DeepSeek API 支持 CORS。如果出现：
1. 检查 API URL 是否正确
2. 联系 DeepSeek 技术支持

### 临时解决方案：使用非流式 API

如果流式 API 有问题，可以临时使用非流式 API：

修改 `ReportModal.vue` 的 `generateReport` 方法：

```javascript
async generateReport() {
  this.generating = true;
  this.error = null;
  this.reportContent = '';
  this.progress = 0;

  try {
    const { generateSalesReport } = await import('@/DS/deepseek.js');
    
    this.progress = 50;
    this.progressText = '正在生成报告...';
    
    // 使用非流式 API
    const report = await generateSalesReport(this.cardData);
    
    this.reportContent = report;
    this.progress = 100;
    this.generating = false;
    this.generatedTime = new Date().toLocaleString('zh-CN');
    
  } catch (err) {
    console.error('生成报告失败:', err);
    this.error = err.message;
    this.generating = false;
  }
}
```

### 获取帮助

如果以上方法都无法解决问题：

1. **复制完整的控制台日志**
2. **截图错误信息**
3. **记录操作步骤**
4. **联系技术支持**

### 检查清单

在报告问题前，请确认：

- [ ] 已选择至少一个卡片
- [ ] API Key 已正确配置
- [ ] 开发服务器已重启
- [ ] 浏览器控制台已打开
- [ ] 已查看完整的错误日志
- [ ] 网络连接正常
- [ ] API Key 有余额

---

**更新时间**：2026-03-05
**版本**：v1.1 - 添加详细日志
