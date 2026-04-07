<template>
  <div class="analysis-reports-container">
    <div class="page-header">
      <h1 class="page-title">
        <i class="fas fa-file-chart-line"></i>
        历史分析报告
      </h1>
      <p class="page-subtitle">查看和管理所有生成的AI分析报告</p>
      <button class="back-btn" @click="goBack">
        ← 返回
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <i class="fas fa-exclamation-circle"></i>
      <p>{{ error }}</p>
      <button class="btn-retry" @click="loadReports">
        <i class="fas fa-redo"></i>
        重新加载
      </button>
    </div>

    <!-- 报告列表 -->
    <div v-else-if="reports.length > 0" class="reports-grid">
      <div 
        v-for="report in reports" 
        :key="report.id" 
        class="report-card"
        @click="viewReport(report)"
      >
        <div class="report-card-header">
          <div class="report-icon">
            <i class="fas fa-chart-line"></i>
          </div>
          <div class="report-meta">
            <h3 class="report-title">分析报告 #{{ report.id }}</h3>
            <p class="report-date">
              <i class="fas fa-clock"></i>
              {{ formatDate(report.report_date) }}
            </p>
          </div>
        </div>

        <div class="report-card-body">
          <div class="report-info">
            <span class="info-label">用户名:</span>
            <span class="info-value">{{ report.username }}</span>
          </div>
          <div class="report-info">
            <span class="info-label">经销商代码:</span>
            <span class="info-value">{{ report.dealer_code }}</span>
          </div>
          <div class="report-info">
            <span class="info-label">选中卡片:</span>
            <span class="info-value">{{ getCardCount(report.selected_cards) }} 个</span>
          </div>
          <div class="report-preview">
            {{ getReportPreview(report.report_content) }}
          </div>
        </div>

        <div class="report-card-footer">
          <button class="btn-view" @click.stop="viewReport(report)">
            <i class="fas fa-eye"></i>
            查看详情
          </button>
          <button class="btn-delete" @click.stop="confirmDelete(report)">
            <i class="fas fa-trash"></i>
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-container">
      <div class="empty-icon">
        <i class="fas fa-file-alt"></i>
      </div>
      <h3>暂无分析报告</h3>
      <p>还没有生成任何分析报告，前往仪表盘生成您的第一份报告吧！</p>
      <button class="btn-primary" @click="goToDashboard">
        <i class="fas fa-chart-bar"></i>
        前往仪表盘
      </button>
    </div>

    <!-- 报告详情弹窗 -->
    <div v-if="showDetailModal" class="modal-overlay" @click="closeDetailModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>
            <i class="fas fa-file-alt"></i>
            分析报告详情
          </h2>
          <button class="btn-close" @click="closeDetailModal">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <div class="detail-info-section">
            <div class="detail-info-item">
              <span class="label">报告ID:</span>
              <span class="value">{{ selectedReport.id }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">用户名:</span>
              <span class="value">{{ selectedReport.username }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">经销商代码:</span>
              <span class="value">{{ selectedReport.dealer_code }}</span>
            </div>
            <div class="detail-info-item">
              <span class="label">生成时间:</span>
              <span class="value">{{ formatDate(selectedReport.report_date) }}</span>
            </div>
          </div>

          <div class="detail-cards-section">
            <h3><i class="fas fa-th-large"></i> 选中的卡片数据</h3>
            <div class="cards-grid">
              <div v-if="parsedCards.trend" class="data-card trend-card">
                <div class="card-header">
                  <i class="fas fa-chart-line"></i>
                  <span>销量趋势分析</span>
                </div>
                <div class="card-body">
                  <div class="trend-chart-mini">
                    <div class="trend-item" v-for="(month, idx) in parsedCards.trend.months" :key="idx">
                      <span class="month-label">{{ month }}</span>
                      <div class="trend-bars">
                        <div class="bar-item">
                          <div class="bar sales" :style="{ width: getBarWidth(parsedCards.trend.sales[idx], parsedCards.trend.sales) }"></div>
                          <span class="bar-value">{{ parsedCards.trend.sales[idx] }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="parsedCards.funnel" class="data-card funnel-card">
                <div class="card-header">
                  <i class="fas fa-filter"></i>
                  <span>销售漏斗</span>
                </div>
                <div class="card-body">
                  <div class="funnel-stages">
                    <div class="funnel-stage">
                      <span class="stage-name">线索</span>
                      <span class="stage-value">{{ parsedCards.funnel.leads }}</span>
                    </div>
                    <div class="funnel-arrow"><i class="fas fa-arrow-down"></i> {{ parsedCards.funnel.leadConversionRate }}%</div>
                    <div class="funnel-stage">
                      <span class="stage-name">潜客</span>
                      <span class="stage-value">{{ parsedCards.funnel.potential }}</span>
                    </div>
                    <div class="funnel-arrow"><i class="fas fa-arrow-down"></i> {{ parsedCards.funnel.storeRate }}%</div>
                    <div class="funnel-stage">
                      <span class="stage-name">进店</span>
                      <span class="stage-value">{{ parsedCards.funnel.store }}</span>
                    </div>
                    <div class="funnel-arrow"><i class="fas fa-arrow-down"></i> {{ parsedCards.funnel.salesRate }}%</div>
                    <div class="funnel-stage highlight">
                      <span class="stage-name">成交</span>
                      <span class="stage-value">{{ parsedCards.funnel.sales }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="parsedCards.snapshot" class="data-card snapshot-card">
                <div class="card-header">
                  <i class="fas fa-camera"></i>
                  <span>月度快照</span>
                </div>
                <div class="card-body">
                  <div class="snapshot-grid">
                    <div class="snapshot-item" v-for="(snap, idx) in parsedCards.snapshot.data" :key="idx">
                      <div class="snap-month">{{ snap.month }}</div>
                      <div class="snap-metrics">
                        <div class="snap-metric">
                          <span class="metric-label">销量</span>
                          <span class="metric-value">{{ snap.sales }}</span>
                        </div>
                        <div class="snap-metric">
                          <span class="metric-label">客流</span>
                          <span class="metric-value">{{ snap.traffic }}</span>
                        </div>
                        <div class="snap-metric">
                          <span class="metric-label">成交率</span>
                          <span class="metric-value rate">{{ snap.rate }}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="parsedCards.metrics" class="data-card metrics-card">
                <div class="card-header">
                  <i class="fas fa-tachometer-alt"></i>
                  <span>核心指标</span>
                </div>
                <div class="card-body">
                  <div class="metrics-grid">
                    <div class="metric-item" v-for="(m, idx) in parsedCards.metrics.metrics" :key="idx">
                      <div class="metric-name">{{ m.label }}</div>
                      <div class="metric-display">{{ m.display }}</div>
                      <div class="metric-month">{{ m.bestMonth }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="parsedCards.rate" class="data-card rate-card">
                <div class="card-header">
                  <i class="fas fa-percentage"></i>
                  <span>成交/战败率</span>
                </div>
                <div class="card-body">
                  <div class="rate-comparison">
                    <div class="rate-item success">
                      <div class="rate-label">平均成交率</div>
                      <div class="rate-value">{{ parsedCards.rate.avgSuccessRate }}%</div>
                      <div class="rate-bar">
                        <div class="bar-fill" :style="{ width: parsedCards.rate.avgSuccessRate + '%' }"></div>
                      </div>
                    </div>
                    <div class="rate-item defeat">
                      <div class="rate-label">平均战败率</div>
                      <div class="rate-value">{{ parsedCards.rate.avgDefeatRate }}%</div>
                      <div class="rate-bar">
                        <div class="bar-fill" :style="{ width: parsedCards.rate.avgDefeatRate + '%' }"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="parsedCards.responseTime" class="data-card response-card">
                <div class="card-header">
                  <i class="fas fa-clock"></i>
                  <span>响应时间分析</span>
                </div>
                <div class="card-body">
                  <div class="response-stats">
                    <div class="response-item">
                      <span class="response-label">成交响应</span>
                      <span class="response-value">{{ parsedCards.responseTime.success }}小时</span>
                    </div>
                    <div class="response-item">
                      <span class="response-label">战败响应</span>
                      <span class="response-value">{{ parsedCards.responseTime.defeat }}小时</span>
                    </div>
                    <div class="response-item avg">
                      <span class="response-label">平均响应</span>
                      <span class="response-value">{{ parsedCards.responseTime.average }}小时</span>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="parsedCards.gsev" class="data-card gsev-card">
                <div class="card-header">
                  <i class="fas fa-car"></i>
                  <span>GSEV分析</span>
                </div>
                <div class="card-body">
                  <div class="gsev-stats">
                    <div class="gsev-main">
                      <span class="gsev-value">{{ parsedCards.gsev.avgGsev }}</span>
                      <span class="gsev-unit">辆</span>
                    </div>
                    <div class="gsev-trend" :class="parsedCards.gsev.trend">
                      <i :class="parsedCards.gsev.trend === '上升' ? 'fas fa-arrow-up' : parsedCards.gsev.trend === '下降' ? 'fas fa-arrow-down' : 'fas fa-minus'"></i>
                      {{ parsedCards.gsev.trend }}
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="parsedCards.policy" class="data-card policy-card">
                <div class="card-header">
                  <i class="fas fa-file-alt"></i>
                  <span>政策分析</span>
                </div>
                <div class="card-body">
                  <div class="policy-stats">
                    <div class="policy-item">
                      <span class="policy-label">政策总数</span>
                      <span class="policy-value">{{ parsedCards.policy.totalCount }}</span>
                    </div>
                    <div class="policy-item">
                      <span class="policy-label">月均政策</span>
                      <span class="policy-value">{{ parsedCards.policy.avgCount }}</span>
                    </div>
                    <div class="policy-item">
                      <span class="policy-label">政策影响</span>
                      <span class="policy-value impact">{{ parsedCards.policy.impact }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="parsedCards.review" class="data-card review-card">
                <div class="card-header">
                  <i class="fas fa-star"></i>
                  <span>评价分析</span>
                </div>
                <div class="card-body">
                  <div class="review-stats">
                    <div class="review-total">
                      <span class="total-value">{{ parsedCards.review.totalCount }}</span>
                      <span class="total-label">总评价</span>
                    </div>
                    <div class="review-breakdown">
                      <div class="breakdown-item good">
                        <span class="breakdown-label">好评</span>
                        <span class="breakdown-value">{{ parsedCards.review.goodRate }}%</span>
                      </div>
                      <div class="breakdown-item bad">
                        <span class="breakdown-label">差评</span>
                        <span class="breakdown-value">{{ parsedCards.review.badRate }}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="Object.keys(parsedCards).length === 0" class="no-cards">
                <i class="fas fa-inbox"></i>
                <span>暂无卡片数据</span>
              </div>
            </div>
          </div>

          <div class="detail-content-section">
            <h3>报告内容</h3>
            <div class="markdown-body" v-html="renderMarkdown(selectedReport.report_content)"></div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="downloadReport(selectedReport)">
            <i class="fas fa-download"></i>
            下载报告
          </button>
          <button class="btn-secondary" @click="copyReport(selectedReport)">
            <i class="fas fa-copy"></i>
            复制内容
          </button>
          <button class="btn-primary" @click="closeDetailModal">
            <i class="fas fa-check"></i>
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from 'marked';

export default {
  name: 'AnalysisReports',
  data() {
    return {
      loading: false,
      error: null,
      reports: [],
      showDetailModal: false,
      selectedReport: null
    };
  },
  computed: {
    parsedCards() {
      if (!this.selectedReport || !this.selectedReport.selected_cards) {
        return {};
      }
      try {
        return JSON.parse(this.selectedReport.selected_cards);
      } catch {
        return {};
      }
    }
  },
  mounted() {
    this.loadReports();
  },
  methods: {
    goBack() {
      this.$router.push('/dashboard');
    },
    getBarWidth(value, allValues) {
      if (!value || !allValues || allValues.length === 0) return '0%';
      const max = Math.max(...allValues);
      if (max === 0) return '0%';
      return Math.round((value / max) * 100) + '%';
    },
    async loadReports() {
      this.loading = true;
      this.error = null;

      try {
        // 获取当前用户信息
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const username = user.username;

        // 构建查询URL - 根据用户名筛选
        let url = '/api/analysis-reports';
        if (user.role !== 'admin') {
          // 普通用户只能看到自己的报告
          url += `?username=${username}`;
        }
        // 管理员可以看到所有报告

        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
          this.reports = result.data;
        } else {
          this.error = result.message || '加载失败';
        }
      } catch (err) {
        console.error('加载分析报告失败:', err);
        this.error = '加载失败，请检查网络连接';
      } finally {
        this.loading = false;
      }
    },

    viewReport(report) {
      this.selectedReport = report;
      this.showDetailModal = true;
    },

    closeDetailModal() {
      this.showDetailModal = false;
      this.selectedReport = null;
    },

    async confirmDelete(report) {
      if (!confirm(`确定要删除报告 #${report.id} 吗？此操作不可恢复。`)) {
        return;
      }

      try {
        const response = await fetch(`/api/analysis-reports/${report.id}`, {
          method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
          alert('删除成功');
          this.loadReports();
        } else {
          alert('删除失败: ' + result.message);
        }
      } catch (err) {
        console.error('删除报告失败:', err);
        alert('删除失败，请稍后重试');
      }
    },

    formatDate(dateStr) {
      if (!dateStr) return '';
      const utcDate = new Date(dateStr + ' UTC');
      return utcDate.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    getCardCount(selectedCardsJson) {
      try {
        const cards = JSON.parse(selectedCardsJson);
        return Object.keys(cards).length;
      } catch {
        return 0;
      }
    },

    getReportPreview(content) {
      const plainText = content.replace(/[#*`\[\]]/g, '').trim();
      return plainText.length > 100 ? plainText.substring(0, 100) + '...' : plainText;
    },

    formatSelectedCards(selectedCardsJson) {
      try {
        const cards = JSON.parse(selectedCardsJson);
        return JSON.stringify(cards, null, 2);
      } catch {
        return selectedCardsJson;
      }
    },

    renderMarkdown(content) {
      return marked(content);
    },

    downloadReport(report) {
      const blob = new Blob([report.report_content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `分析报告_${report.id}_${new Date().getTime()}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },

    copyReport(report) {
      navigator.clipboard.writeText(report.report_content).then(() => {
        alert('报告内容已复制到剪贴板');
      }).catch(err => {
        console.error('复制失败:', err);
        alert('复制失败，请手动复制');
      });
    },

    goToDashboard() {
      this.$router.push('/dashboard');
    }
  }
};
</script>

<style scoped>
.analysis-reports-container {
  padding: 30px;
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  margin-bottom: 30px;
  position: relative;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title i {
  color: #1890ff;
}

.page-subtitle {
  font-size: 14px;
  color: #666;
  margin: 10px 0 0 0;
}

.back-btn {
  position: absolute;
  right: 0;
  top: 0;
  padding: 8px 16px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.back-btn:hover {
  background: #40a9ff;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease-in-out;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-container p {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
  margin: 0;
}

/* 错误状态 */
.error-container {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background-color: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease-in-out;
}

.error-container i {
  font-size: 24px;
  color: #dc2626;
}

.error-container p {
  flex: 1;
  font-size: 14px;
  color: #b91c1c;
  margin: 0;
}

.btn-retry {
  padding: 8px 16px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.btn-retry:hover {
  background: #1d4ed8;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 报告网格 */
.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.report-card {
  background: white;
  border-radius: 8px;
  padding: 0;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.report-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.report-card-header {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.report-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 22px;
  flex-shrink: 0;
}

.report-meta {
  flex: 1;
  min-width: 0;
}

.report-title {
  margin: 0 0 6px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.report-date {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 5px;
}

.report-card-body {
  padding: 20px;
}

.report-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
}

.info-label {
  color: #6b7280;
  font-weight: 500;
}

.info-value {
  color: #1f2937;
  font-weight: 600;
}

.report-preview {
  margin-top: 15px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
  max-height: 80px;
  overflow: hidden;
  border-left: 3px solid #1890ff;
}

.report-card-footer {
  display: flex;
  gap: 10px;
  padding: 15px 20px;
  background-color: #fafafa;
  border-top: 1px solid #e5e7eb;
}

.btn-view,
.btn-delete {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.btn-view {
  background: #1890ff;
  color: white;
}

.btn-view:hover {
  background: #096dd9;
}

.btn-delete {
  background: #f5f5f5;
  color: #ff4d4f;
  border: 1px solid #e5e7eb;
}

.btn-delete:hover {
  background: #ff4d4f;
  color: white;
  border-color: #ff4d4f;
}

/* 空状态 */
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
  color: #d1d5db;
}

.empty-container h3 {
  font-size: 18px;
  margin: 0 0 10px 0;
  color: #1f2937;
  font-weight: 600;
}

.empty-container p {
  font-size: 14px;
  margin: 0 0 30px 0;
  color: #6b7280;
}

.btn-primary {
  padding: 10px 20px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: #096dd9;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(24, 144, 255, 0.2);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  background-color: #fafafa;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-header h2 i {
  color: #1890ff;
}

.btn-close {
  background: none;
  border: none;
  font-size: 20px;
  color: #6b7280;
  cursor: pointer;
  padding: 4px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.btn-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.detail-info-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
  padding: 20px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.detail-info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-info-item .label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-info-item .value {
  font-size: 15px;
  color: #1f2937;
  font-weight: 600;
}

.detail-cards-section,
.detail-content-section {
  margin-bottom: 24px;
}

.detail-cards-section h3,
.detail-content-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #1890ff;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.data-card {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: all 0.2s ease;
}

.data-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.data-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.data-card .card-header i {
  color: #1890ff;
  font-size: 14px;
}

.data-card .card-body {
  padding: 16px;
}

.no-cards {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #9ca3af;
  gap: 8px;
}

.no-cards i {
  font-size: 32px;
}

.trend-chart-mini {
  max-height: 200px;
  overflow-y: auto;
}

.trend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
}

.trend-item:last-child {
  border-bottom: none;
}

.trend-item .month-label {
  width: 40px;
  font-size: 12px;
  color: #6b7280;
  flex-shrink: 0;
}

.trend-bars {
  flex: 1;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-item .bar {
  height: 8px;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.bar-item .bar.sales {
  background: linear-gradient(90deg, #1890ff, #40a9ff);
}

.bar-item .bar-value {
  font-size: 12px;
  color: #374151;
  min-width: 40px;
  text-align: right;
}

.funnel-stages {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.funnel-stage {
  display: flex;
  justify-content: space-between;
  width: 100%;
  padding: 10px 16px;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 13px;
}

.funnel-stage.highlight {
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: white;
}

.funnel-stage .stage-name {
  color: #6b7280;
}

.funnel-stage.highlight .stage-name {
  color: rgba(255, 255, 255, 0.9);
}

.funnel-stage .stage-value {
  font-weight: 600;
  color: #1f2937;
}

.funnel-stage.highlight .stage-value {
  color: white;
}

.funnel-arrow {
  font-size: 11px;
  color: #1890ff;
  padding: 2px 0;
}

.snapshot-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.snapshot-item {
  background: #f9fafb;
  border-radius: 6px;
  padding: 10px;
}

.snap-month {
  font-size: 12px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 6px;
}

.snap-metrics {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.snap-metric {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
}

.snap-metric .metric-label {
  color: #6b7280;
}

.snap-metric .metric-value {
  font-weight: 500;
  color: #374151;
}

.snap-metric .metric-value.rate {
  color: #1890ff;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.metrics-grid .metric-item {
  text-align: center;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.metrics-grid .metric-name {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.metrics-grid .metric-display {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.metrics-grid .metric-month {
  font-size: 11px;
  color: #1890ff;
  margin-top: 4px;
}

.rate-comparison {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rate-item {
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.rate-item .rate-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}

.rate-item .rate-value {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.rate-item.success .rate-value {
  color: #10b981;
}

.rate-item.defeat .rate-value {
  color: #ef4444;
}

.rate-bar {
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}

.rate-item.success .bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #34d399);
  border-radius: 3px;
}

.rate-item.defeat .bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #ef4444, #f87171);
  border-radius: 3px;
}

.response-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.response-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.response-item.avg {
  background: linear-gradient(135deg, #1890ff, #096dd9);
}

.response-item.avg .response-label,
.response-item.avg .response-value {
  color: white;
}

.response-label {
  font-size: 13px;
  color: #6b7280;
}

.response-value {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.gsev-stats {
  text-align: center;
  padding: 16px;
}

.gsev-main {
  margin-bottom: 12px;
}

.gsev-value {
  font-size: 36px;
  font-weight: 700;
  color: #1f2937;
}

.gsev-unit {
  font-size: 14px;
  color: #6b7280;
  margin-left: 4px;
}

.gsev-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.gsev-trend.上升 {
  background: #d1fae5;
  color: #059669;
}

.gsev-trend.下降 {
  background: #fee2e2;
  color: #dc2626;
}

.gsev-trend.稳定 {
  background: #f3f4f6;
  color: #6b7280;
}

.policy-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.policy-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.policy-label {
  font-size: 13px;
  color: #6b7280;
}

.policy-value {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.policy-value.impact {
  color: #1890ff;
}

.review-stats {
  display: flex;
  align-items: center;
  gap: 20px;
}

.review-total {
  text-align: center;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.total-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

.total-label {
  font-size: 12px;
  color: #6b7280;
}

.review-breakdown {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.breakdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
}

.breakdown-item.good {
  background: #d1fae5;
}

.breakdown-item.bad {
  background: #fee2e2;
}

.breakdown-label {
  font-size: 12px;
  color: #6b7280;
}

.breakdown-value {
  font-size: 14px;
  font-weight: 600;
}

.breakdown-item.good .breakdown-value {
  color: #059669;
}

.breakdown-item.bad .breakdown-value {
  color: #dc2626;
}

/* Markdown 样式 */
.markdown-body {
  font-size: 14px;
  line-height: 1.8;
  color: #374151;
}

.markdown-body h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 24px 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #1890ff;
  color: #1f2937;
}

.markdown-body h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 20px 0 12px 0;
  color: #1f2937;
}

.markdown-body h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 16px 0 10px 0;
  color: #374151;
}

.markdown-body p {
  margin: 10px 0;
}

.markdown-body ul,
.markdown-body ol {
  margin: 10px 0;
  padding-left: 24px;
}

.markdown-body li {
  margin: 6px 0;
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  border: 1px solid #e5e7eb;
}

.markdown-body table th,
.markdown-body table td {
  border: 1px solid #e5e7eb;
  padding: 10px 12px;
  text-align: left;
}

.markdown-body table th {
  background: #f9fafb;
  font-weight: 600;
  color: #1f2937;
}

.markdown-body code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #dc2626;
}

.markdown-body strong {
  font-weight: 600;
  color: #1890ff;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  background: #fafafa;
}

.btn-secondary {
  padding: 8px 16px;
  background: white;
  color: #6b7280;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #1890ff;
  color: #1890ff;
}

.modal-footer .btn-primary {
  padding: 8px 16px;
  font-size: 14px;
}

/* 响应式 */
@media (max-width: 768px) {
  .analysis-reports-container {
    padding: 20px;
  }

  .page-title {
    font-size: 18px;
  }

  .page-subtitle {
    font-size: 13px;
  }

  .reports-grid {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 95%;
    max-height: 95vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 16px 20px;
  }

  .detail-info-section {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column;
  }

  .btn-secondary,
  .modal-footer .btn-primary {
    width: 100%;
    justify-content: center;
  }
}
</style>
