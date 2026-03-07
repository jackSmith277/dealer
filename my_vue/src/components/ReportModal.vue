<template>
  <div class="report-modal-overlay" @click="closeModal">
    <div class="report-modal" @click.stop>
      <div class="report-header">
        <h2 class="report-title">
          <i class="fas fa-chart-line"></i>
          AI 智能分析报告
        </h2>
        <button class="close-btn" @click="closeModal">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="report-body">
        <!-- 生成中状态 -->
        <div v-if="generating" class="generating-container">
          <div class="generating-animation">
            <div class="spinner"></div>
            <div class="ai-icon">
              <i class="fas fa-brain"></i>
            </div>
          </div>
          <p class="generating-text">AI 正在分析数据，生成报告中...</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <p class="progress-text">{{ progressText }}</p>
        </div>

        <!-- 错误状态 -->
        <div v-else-if="error" class="error-container">
          <div class="error-icon">
            <i class="fas fa-exclamation-triangle"></i>
          </div>
          <p class="error-message">{{ error }}</p>
          <button class="btn btn-primary" @click="retryGenerate">
            <i class="fas fa-redo"></i>
            重新生成
          </button>
        </div>

        <!-- 报告内容 -->
        <div v-else-if="reportContent" class="report-content">
          <!-- 流式显示的内容 -->
          <div v-if="streaming" class="streaming-content">
            <div class="markdown-body" v-html="renderedContent"></div>
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
          
          <!-- 完整内容 -->
          <div v-else class="markdown-body" v-html="renderedContent"></div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-container">
          <div class="empty-icon">
            <i class="fas fa-file-alt"></i>
          </div>
          <p class="empty-text">暂无报告内容</p>
        </div>
      </div>

      <div class="report-footer">
        <div class="footer-info">
          <span class="info-item">
            <i class="fas fa-clock"></i>
            生成时间: {{ generatedTime }}
          </span>
          <span class="info-item">
            <i class="fas fa-cube"></i>
            模型: DeepSeek-Chat
          </span>
        </div>
        <div class="footer-actions">
          <button class="btn btn-secondary" @click="copyReport" :disabled="!reportContent">
            <i class="fas fa-copy"></i>
            复制报告
          </button>
          <button class="btn btn-secondary" @click="downloadReport" :disabled="!reportContent">
            <i class="fas fa-download"></i>
            下载报告
          </button>
          <button class="btn btn-primary" @click="closeModal">
            <i class="fas fa-check"></i>
            完成
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from 'marked';

export default {
  name: 'ReportModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    cardData: {
      type: Object,
      default: () => ({})
    },
    dealerCode: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      generating: false,
      streaming: false,
      error: null,
      reportContent: '',
      progress: 0,
      progressText: '准备中...',
      generatedTime: ''
    };
  },
  computed: {
    renderedContent() {
      if (!this.reportContent) return '';
      return marked(this.reportContent);
    }
  },
  watch: {
    visible(newVal, oldVal) {

      
      // 只在从 false 变为 true 时生成报告
      if (newVal && !oldVal) {
        this.generateReport();
      }
    }
  },
  mounted() {

    
    // 如果挂载时 visible 已经是 true，立即生成报告
    if (this.visible && this.cardData && Object.keys(this.cardData).length > 0) {
      this.$nextTick(() => {
        this.generateReport();
      });
    }
  },
  methods: {
    closeModal() {
      this.$emit('close');
    },

    async generateReport() {
      this.generating = true;
      this.streaming = true;
      this.error = null;
      this.reportContent = '';
      this.progress = 0;
      this.progressText = '正在连接 AI 服务...';

      try {

        
        // 检查 cardData 是否为空
        if (!this.cardData || Object.keys(this.cardData).length === 0) {
          throw new Error('没有可分析的数据，请先选择卡片后再生成报告');
        }

        // 动态导入 DeepSeek 模块
        const { generateSalesReportStream } = await import('@/DS/deepseek.js');

        this.progress = 20;
        this.progressText = '正在分析数据...';


        let hasReceivedData = false;

        // 使用流式生成
        await generateSalesReportStream(
          this.cardData,
          (chunk) => {
            hasReceivedData = true;
            this.reportContent += chunk;
            this.progress = Math.min(90, this.progress + 1);
            this.progressText = '正在生成报告...';
          }
        );



        // 检查是否真的收到了数据
        if (!hasReceivedData || !this.reportContent) {
          throw new Error('API 调用成功但未返回内容，请检查 API 配置或稍后重试');
        }

        this.progress = 100;
        this.progressText = '生成完成！';
        this.generating = false;
        this.streaming = false;
        this.generatedTime = new Date().toLocaleString('zh-CN');

        // 保存报告到数据库
        await this.saveReportToDatabase();

      } catch (err) {

        
        // 提供更友好的错误信息
        let errorMessage = err.message || '生成报告失败，请稍后重试';
        
        // 针对常见错误提供具体的解决方案
        if (errorMessage.includes('API Key')) {
          errorMessage += '\n\n解决方案：\n1. 在项目根目录创建 .env 文件\n2. 添加配置：VITE_DEEPSEEK_API_KEY=你的密钥\n3. 重启开发服务器';
        } else if (errorMessage.includes('fetch')) {
          errorMessage = '网络请求失败，请检查网络连接或 API 地址配置';
        }
        
        this.error = errorMessage;
        this.generating = false;
        this.streaming = false;
      }
    },

    retryGenerate() {
      this.error = null;
      this.reportContent = '';
      this.generateReport();
    },

    copyReport() {
      if (!this.reportContent) return;

      navigator.clipboard.writeText(this.reportContent).then(() => {
        alert('报告已复制到剪贴板');
      }).catch(err => {
        console.error('复制失败:', err);
        alert('复制失败，请手动复制');
      });
    },

    downloadReport() {
      if (!this.reportContent) return;

      const blob = new Blob([this.reportContent], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `销售分析报告_${new Date().getTime()}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },

    async saveReportToDatabase() {
      try {
        // 获取当前登录用户信息
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const username = user.username || 'unknown';
        
        // 使用传入的经销商代码（当前选择的经销商）
        const dealerCode = this.dealerCode || 'unknown';

        // 准备保存的数据
        const reportData = {
          username: username,  // 当前登录用户
          dealer_code: dealerCode,  // 当前选择的经销商
          selected_cards: JSON.stringify(this.cardData),
          report_content: this.reportContent
        };

        console.log('保存分析报告到数据库:', reportData);

        // 发送保存请求
        const response = await fetch('http://localhost:5000/api/analysis-reports', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(reportData)
        });

        const result = await response.json();
        
        if (result.success) {
          console.log('分析报告保存成功:', result.data.id);
        } else {
          console.error('保存分析报告失败:', result.message);
        }
      } catch (error) {
        console.error('保存分析报告到数据库时出错:', error);
      }
    }
  }
};
</script>

<style scoped>
.report-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.report-modal {
  background: #fff;
  border-radius: 12px;
  width: 90%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  border-bottom: 1px solid #e8e8e8;
}

.report-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 10px;
}

.report-title i {
  color: #1890ff;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  padding: 5px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.report-body {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
  min-height: 400px;
}

/* 生成中状态 */
.generating-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.generating-animation {
  position: relative;
  width: 100px;
  height: 100px;
  margin-bottom: 30px;
}

.spinner {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid #f0f0f0;
  border-top: 4px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.ai-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 40px;
  color: #1890ff;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    opacity: 0.7;
    transform: translate(-50%, -50%) scale(1.1);
  }
}

.generating-text {
  font-size: 16px;
  color: #666;
  margin-bottom: 20px;
}

.progress-bar {
  width: 100%;
  max-width: 400px;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #1890ff, #40a9ff);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: #999;
}

/* 错误状态 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.error-icon {
  font-size: 60px;
  color: #ff4d4f;
  margin-bottom: 20px;
}

.error-message {
  font-size: 16px;
  color: #666;
  margin-bottom: 30px;
  text-align: center;
  white-space: pre-wrap;
  max-width: 600px;
  line-height: 1.6;
}

/* 报告内容 */
.report-content {
  animation: fadeIn 0.5s ease;
}

.streaming-content {
  position: relative;
}

.typing-indicator {
  display: inline-flex;
  gap: 4px;
  margin-left: 5px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #1890ff;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-10px);
  }
}

/* Markdown 样式 */
.markdown-body {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
}

.markdown-body h1 {
  font-size: 28px;
  font-weight: 600;
  margin: 30px 0 20px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid #e8e8e8;
  color: #1890ff;
}

.markdown-body h2 {
  font-size: 24px;
  font-weight: 600;
  margin: 25px 0 15px 0;
  color: #333;
}

.markdown-body h3 {
  font-size: 20px;
  font-weight: 600;
  margin: 20px 0 12px 0;
  color: #555;
}

.markdown-body p {
  margin: 12px 0;
}

.markdown-body ul,
.markdown-body ol {
  margin: 12px 0;
  padding-left: 30px;
}

.markdown-body li {
  margin: 8px 0;
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

.markdown-body table th,
.markdown-body table td {
  border: 1px solid #e8e8e8;
  padding: 10px 15px;
  text-align: left;
}

.markdown-body table th {
  background: #fafafa;
  font-weight: 600;
}

.markdown-body code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.markdown-body pre {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 15px 0;
}

.markdown-body blockquote {
  border-left: 4px solid #1890ff;
  padding-left: 15px;
  margin: 15px 0;
  color: #666;
  font-style: italic;
}

.markdown-body strong {
  font-weight: 600;
  color: #1890ff;
}

/* 空状态 */
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 60px;
  color: #d9d9d9;
  margin-bottom: 20px;
}

.empty-text {
  font-size: 16px;
  color: #999;
}

/* 底部 */
.report-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  border-top: 1px solid #e8e8e8;
  background: #fafafa;
}

.footer-info {
  display: flex;
  gap: 20px;
}

.info-item {
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 5px;
}

.info-item i {
  color: #999;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #40a9ff;
}

.btn-secondary {
  background: white;
  color: #666;
  border: 1px solid #d9d9d9;
}

.btn-secondary:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #1890ff;
  color: #1890ff;
}

/* 响应式 */
@media (max-width: 768px) {
  .report-modal {
    width: 95%;
    max-height: 95vh;
  }

  .report-header,
  .report-body,
  .report-footer {
    padding: 15px 20px;
  }

  .report-title {
    font-size: 18px;
  }

  .footer-info {
    flex-direction: column;
    gap: 8px;
  }

  .footer-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
