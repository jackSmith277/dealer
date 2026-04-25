<template>
  <div class="task-history-page">
    <div class="page-header">
      <h1 class="page-title">历史执行记录</h1>
      <div class="header-controls">
        <button class="btn btn-gray" @click="$router.push('/dashboard/decision-support')">
          <i class="fas fa-arrow-left"></i> 返回决策支持
        </button>
      </div>
    </div>
    
    <div class="filter-bar">
      <div class="filter-row">
        <div class="filter-item">
          <label class="filter-label">区域</label>
          <select v-model="filters.region" @change="onRegionChange" class="filter-select">
            <option value="">全部区域</option>
            <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
          </select>
        </div>
        
        <div class="filter-item">
          <label class="filter-label">省份</label>
          <select v-model="filters.province" @change="loadTaskHistory" class="filter-select">
            <option value="">全部省份</option>
            <option v-for="province in filteredProvinces" :key="province" :value="province">{{ province }}</option>
          </select>
        </div>
        
        <div class="filter-item">
          <label class="filter-label">经销商</label>
          <select v-model="filters.dealerCode" @change="loadTaskHistory" class="filter-select">
            <option value="">全部经销商</option>
            <option v-for="dealer in filteredDealers" :key="dealer['经销商代码']" :value="dealer['经销商代码']">
              {{ dealer['经销商代码'] }} - {{ dealer['省份'] }}
            </option>
          </select>
        </div>
        
        <div class="filter-item">
          <label class="filter-label">任务状态</label>
          <select v-model="filters.status" @change="loadTaskHistory" class="filter-select">
            <option value="">全部状态</option>
            <option value="pending">待执行</option>
            <option value="in_progress">执行中</option>
            <option value="completed">已完成</option>
          </select>
        </div>
        
        <div class="filter-item">
          <label class="filter-label">时间范围</label>
          <div class="date-range-picker">
            <input type="date" v-model="filters.startDate" @change="loadTaskHistory" class="date-input">
            <span class="date-separator">至</span>
            <input type="date" v-model="filters.endDate" @change="loadTaskHistory" class="date-input">
          </div>
        </div>
        
        <div class="filter-item">
          <button class="btn-refresh" @click="loadTaskHistory">
            <i class="fas fa-sync-alt"></i> 刷新
          </button>
        </div>
      </div>
    </div>
    
    <div class="task-history-stats">
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-content">
          <div class="stat-value">{{ taskHistoryStats.total }}</div>
          <div class="stat-label">总任务</div>
        </div>
      </div>
      <div class="stat-card pending">
        <div class="stat-icon">⏳</div>
        <div class="stat-content">
          <div class="stat-value">{{ taskHistoryStats.pending }}</div>
          <div class="stat-label">待执行</div>
        </div>
      </div>
      <div class="stat-card in-progress">
        <div class="stat-icon">🔄</div>
        <div class="stat-content">
          <div class="stat-value">{{ taskHistoryStats.in_progress }}</div>
          <div class="stat-label">执行中</div>
        </div>
      </div>
      <div class="stat-card completed">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ taskHistoryStats.completed }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>
    </div>
    
    <div class="task-history-container">
      <div class="task-history-body">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <div class="loading-text">加载中...</div>
        </div>
        
        <div v-else-if="taskHistory.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-text">暂无执行记录</div>
        </div>
        
        <div v-else class="task-history-list">
          <div v-for="task in taskHistory" :key="task.id" class="task-history-card" :class="task.status">
            <div class="task-card-header">
              <div class="task-card-title">
                <span class="task-icon">{{ task.icon }}</span>
                <span class="task-title-text">{{ task.title }}</span>
              </div>
              <span :class="['task-status-badge', task.status]">{{ getTaskStatusText(task.status) }}</span>
            </div>
            
            <div class="task-card-body">
              <div class="task-card-desc">{{ task.description }}</div>
              
              <div class="task-card-meta">
                <div class="meta-row">
                  <span class="meta-label">经销商：</span>
                  <span class="meta-value">{{ task.dealerCode }}</span>
                  <span class="meta-province" v-if="task.dealerProvince">({{ task.dealerProvince }})</span>
                </div>
                <div class="meta-row">
                  <span class="meta-label">下发时间：</span>
                  <span class="meta-value">{{ task.createdAt }}</span>
                </div>
              </div>
              
              <div class="task-progress-section" v-if="task.status !== 'pending'">
                <div class="progress-header">
                  <span>执行进度</span>
                  <span class="progress-value">{{ task.progress }}%</span>
                </div>
                <div class="progress-bar-container">
                  <div class="progress-bar-fill" :style="{ width: task.progress + '%' }"></div>
                </div>
              </div>
              
              <div class="task-feedback-section" v-if="task.feedback">
                <div class="feedback-header">经销商反馈：</div>
                <div class="feedback-content">{{ task.feedback }}</div>
              </div>
            </div>
            
            <div class="task-card-footer">
              <button class="btn-task-detail" @click="viewTaskDetail(task)">查看详情</button>
            </div>
          </div>
        </div>
        
        <div class="pagination" v-if="totalPages > 1">
          <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--; loadTaskHistory()">
            <i class="fas fa-chevron-left"></i>
          </button>
          <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage++; loadTaskHistory()">
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="showTaskDetail" class="dialog-overlay" @click="showTaskDetail = false">
      <div class="dialog-content task-detail-dialog" @click.stop>
        <div class="dialog-header">
          <h3>任务详情</h3>
          <button class="dialog-close" @click="showTaskDetail = false">✕</button>
        </div>
        <div class="dialog-body" v-if="currentTaskDetail">
          <div class="detail-section">
            <div class="detail-label">任务标题</div>
            <div class="detail-value">{{ currentTaskDetail.title }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">任务描述</div>
            <div class="detail-value">{{ currentTaskDetail.description }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">经销商</div>
            <div class="detail-value">{{ currentTaskDetail.dealerCode }} ({{ currentTaskDetail.dealerProvince || '未知省份' }})</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">下发时间</div>
            <div class="detail-value">{{ currentTaskDetail.createdAt }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">执行状态</div>
            <div class="detail-value">
              <span :class="['task-status-badge', currentTaskDetail.status]">{{ getTaskStatusText(currentTaskDetail.status) }}</span>
            </div>
          </div>
          <div class="detail-section" v-if="currentTaskDetail.status !== 'pending'">
            <div class="detail-label">执行进度</div>
            <div class="detail-value">
              <div class="progress-bar-container">
                <div class="progress-bar-fill" :style="{ width: currentTaskDetail.progress + '%' }"></div>
              </div>
              <span>{{ currentTaskDetail.progress }}%</span>
            </div>
          </div>
          <div class="detail-section" v-if="currentTaskDetail.feedback">
            <div class="detail-label">经销商反馈</div>
            <div class="detail-value feedback-box">{{ currentTaskDetail.feedback }}</div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-confirm" @click="showTaskDetail = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'TaskHistory',
  data() {
    return {
      loading: false,
      regions: ['华东', '华南', '华北', '华中', '西南', '西北', '东北'],
      allProvinces: [],
      dealerList: [],
      filters: {
        region: '',
        province: '',
        dealerCode: '',
        status: '',
        startDate: '',
        endDate: ''
      },
      taskHistory: [],
      taskHistoryStats: {
        total: 0,
        pending: 0,
        in_progress: 0,
        completed: 0
      },
      currentPage: 1,
      totalRecords: 0,
      pageSize: 10,
      showTaskDetail: false,
      currentTaskDetail: null
    }
  },
  
  computed: {
    filteredProvinces() {
      if (!this.filters.region) {
        return this.allProvinces
      }
      
      const regionProvinceMap = {
        '华东': ['上海', '江苏', '浙江', '安徽', '福建', '江西', '山东'],
        '华南': ['广东', '广西', '海南'],
        '华北': ['北京', '天津', '河北', '山西', '内蒙古'],
        '华中': ['河南', '湖北', '湖南'],
        '西南': ['重庆', '四川', '贵州', '云南', '西藏'],
        '西北': ['陕西', '甘肃', '青海', '宁夏', '新疆'],
        '东北': ['辽宁', '吉林', '黑龙江']
      }
      
      return regionProvinceMap[this.filters.region] || []
    },
    
    filteredDealers() {
      if (!this.filters.province && !this.filters.region) {
        return this.dealerList
      }
      
      return this.dealerList.filter(dealer => {
        const dealerProvince = dealer['省份'] || ''
        
        if (this.filters.province) {
          const filterProvince = this.filters.province.replace(/省|市|自治区/g, '')
          const cleanDealerProvince = dealerProvince.replace(/省|市|自治区/g, '')
          if (!cleanDealerProvince.includes(filterProvince) && !filterProvince.includes(cleanDealerProvince)) {
            return false
          }
        }
        
        if (this.filters.region) {
          const matchedProvinces = this.filteredProvinces.map(p => p.replace(/省|市|自治区/g, ''))
          const cleanDealerProvince = dealerProvince.replace(/省|市|自治区/g, '')
          const isMatch = matchedProvinces.some(p => 
            cleanDealerProvince.includes(p) || p.includes(cleanDealerProvince)
          )
          if (!isMatch) return false
        }
        
        return true
      })
    },
    
    totalPages() {
      return Math.ceil(this.totalRecords / this.pageSize)
    }
  },
  
  mounted() {
    this.loadDealerList()
    this.loadTaskHistory()
  },
  
  methods: {
    async loadDealerList() {
      try {
        const response = await axios.get('/api/dealers/list')
        if (response.data && response.data.dealers) {
          this.dealerList = response.data.dealers.map(d => ({
            '经销商代码': d.dealer_code,
            '省份': d.province || '',
            '城市': d.city || ''
          }))
          
          const provinces = new Set()
          this.dealerList.forEach(dealer => {
            if (dealer['省份']) {
              provinces.add(dealer['省份'])
            }
          })
          this.allProvinces = Array.from(provinces).sort()
        }
      } catch (error) {
        console.error('加载经销商列表失败:', error)
      }
    },
    
    onRegionChange() {
      this.filters.province = ''
      this.filters.dealerCode = ''
      this.loadTaskHistory()
    },
    
    async loadTaskHistory() {
      this.loading = true
      try {
        const params = {
          region: this.filters.region,
          province: this.filters.province,
          dealerCode: this.filters.dealerCode,
          status: this.filters.status,
          startDate: this.filters.startDate,
          endDate: this.filters.endDate,
          page: this.currentPage,
          pageSize: this.pageSize
        }
        
        const response = await axios.get('/api/decision/task-history', { params })
        
        if (response.data.success) {
          this.taskHistory = response.data.tasks || []
          this.totalRecords = response.data.total || 0
          this.taskHistoryStats = response.data.stats || {
            total: 0,
            pending: 0,
            in_progress: 0,
            completed: 0
          }
        }
      } catch (error) {
        console.error('加载任务历史失败:', error)
        this.taskHistory = []
      } finally {
        this.loading = false
      }
    },
    
    getTaskStatusText(status) {
      const statusMap = {
        'pending': '待执行',
        'in_progress': '执行中',
        'completed': '已完成'
      }
      return statusMap[status] || status
    },
    
    viewTaskDetail(task) {
      this.currentTaskDetail = task
      this.showTaskDetail = true
    }
  }
}
</script>

<style scoped>
.task-history-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.header-controls {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-gray {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #d9d9d9;
}

.btn-gray:hover {
  background: #e8e8e8;
}

.filter-bar {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  min-width: 150px;
  background-color: white;
}

.date-range-picker {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  width: 140px;
}

.date-separator {
  color: #999;
  font-size: 14px;
}

.btn-refresh {
  padding: 8px 16px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s;
}

.btn-refresh:hover {
  background: #40a9ff;
}

.task-history-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-card .stat-icon {
  font-size: 32px;
}

.stat-card .stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.stat-card .stat-label {
  font-size: 14px;
  color: #666;
}

.stat-card.pending .stat-value {
  color: #faad14;
}

.stat-card.in-progress .stat-value {
  color: #1890ff;
}

.stat-card.completed .stat-value {
  color: #52c41a;
}

.task-history-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.task-history-body {
  padding: 16px;
  min-height: 400px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 12px;
  color: #666;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  color: #999;
}

.task-history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-history-card {
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  padding: 16px;
  transition: all 0.3s;
}

.task-history-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.task-history-card.pending {
  border-left: 3px solid #faad14;
}

.task-history-card.in_progress {
  border-left: 3px solid #1890ff;
}

.task-history-card.completed {
  border-left: 3px solid #52c41a;
}

.task-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-icon {
  font-size: 18px;
}

.task-title-text {
  font-weight: 600;
  color: #333;
}

.task-status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.task-status-badge.pending {
  background: #fffbe6;
  color: #faad14;
}

.task-status-badge.in_progress {
  background: #e6f7ff;
  color: #1890ff;
}

.task-status-badge.completed {
  background: #f6ffed;
  color: #52c41a;
}

.task-card-body {
  margin-bottom: 12px;
}

.task-card-desc {
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
  line-height: 1.5;
}

.task-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

.meta-row {
  display: flex;
  align-items: center;
}

.meta-label {
  color: #999;
}

.meta-value {
  color: #333;
}

.meta-province {
  color: #1890ff;
  margin-left: 4px;
}

.task-progress-section {
  margin-top: 12px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 12px;
  color: #666;
}

.progress-value {
  color: #1890ff;
  font-weight: 500;
}

.progress-bar-container {
  height: 6px;
  background: #e8e8e8;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #1890ff, #52c41a);
  border-radius: 3px;
  transition: width 0.3s;
}

.task-feedback-section {
  margin-top: 12px;
  padding: 10px;
  background: #f0f5ff;
  border-radius: 4px;
}

.feedback-header {
  font-size: 12px;
  color: #1890ff;
  margin-bottom: 6px;
}

.feedback-content {
  font-size: 13px;
  color: #333;
  line-height: 1.5;
}

.task-card-footer {
  display: flex;
  justify-content: flex-end;
}

.btn-task-detail {
  padding: 6px 16px;
  background: white;
  color: #1890ff;
  border: 1px solid #1890ff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.btn-task-detail:hover {
  background: #e6f7ff;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.page-btn {
  padding: 8px 12px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.dialog-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #999;
}

.dialog-body {
  padding: 20px;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 6px;
}

.detail-value {
  font-size: 14px;
  color: #333;
}

.feedback-box {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  line-height: 1.6;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
}

.btn-confirm {
  padding: 8px 24px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-confirm:hover {
  background: #40a9ff;
}
</style>
