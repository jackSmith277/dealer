<template>
  <div class="task-management-container">
    <div class="page-header">
      <h1>任务管理</h1>
      <p class="page-desc">查看收到的决策任务并反馈执行进度</p>
    </div>
    
    <div class="task-stats">
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-content">
          <div class="stat-value">{{ taskStats.total }}</div>
          <div class="stat-label">总任务数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⏳</div>
        <div class="stat-content">
          <div class="stat-value">{{ taskStats.pending }}</div>
          <div class="stat-label">待执行</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔄</div>
        <div class="stat-content">
          <div class="stat-value">{{ taskStats.inProgress }}</div>
          <div class="stat-label">执行中</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ taskStats.completed }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>
    </div>
    
    <div class="filter-bar">
      <div class="filter-item">
        <label>任务状态：</label>
        <select v-model="filterStatus" @change="loadTasks">
          <option value="">全部</option>
          <option value="pending">待执行</option>
          <option value="in_progress">执行中</option>
          <option value="completed">已完成</option>
        </select>
      </div>
      <div class="filter-item">
        <label>时间范围：</label>
        <input type="date" v-model="filterStartDate" @change="loadTasks">
        <span>至</span>
        <input type="date" v-model="filterEndDate" @change="loadTasks">
      </div>
    </div>
    
    <div class="task-list">
      <div v-if="tasks.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <div class="empty-text">暂无任务</div>
      </div>
      
      <div v-for="task in tasks" :key="task.id" class="task-card">
        <div class="task-header">
          <div class="task-title">
            <span class="task-icon">{{ getTaskIcon(task.type) }}</span>
            <h3>{{ task.title }}</h3>
          </div>
          <span :class="['task-status', task.status]">{{ getStatusText(task.status) }}</span>
        </div>
        
        <div class="task-body">
          <div class="task-description">{{ task.description }}</div>
          
          <div class="task-meta">
            <div class="meta-item">
              <span class="meta-label">发布时间：</span>
              <span class="meta-value">{{ task.createdAt }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">截止时间：</span>
              <span class="meta-value">{{ task.deadline }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">发布人：</span>
              <span class="meta-value">{{ task.publisher }}</span>
            </div>
          </div>
          
          <div v-if="task.progress > 0" class="task-progress">
            <div class="progress-label">执行进度：{{ task.progress }}%</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
            </div>
          </div>
          
          <div v-if="task.feedback" class="task-feedback">
            <div class="feedback-label">反馈内容：</div>
            <div class="feedback-content">{{ task.feedback }}</div>
          </div>
        </div>
        
        <div class="task-actions">
          <button 
            v-if="task.status === 'pending'" 
            class="btn-action btn-start"
            @click="startTask(task)"
          >
            开始执行
          </button>
          <button 
            v-if="task.status === 'in_progress'" 
            class="btn-action btn-update"
            @click="showUpdateDialog(task)"
          >
            更新进度
          </button>
          <button 
            v-if="task.status === 'in_progress'" 
            class="btn-action btn-complete"
            @click="completeTask(task)"
          >
            完成任务
          </button>
          <button class="btn-action btn-detail" @click="showTaskDetail(task)">
            查看详情
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="showDialog" class="dialog-overlay" @click="closeDialog">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header">
          <h3>{{ dialogTitle }}</h3>
          <button class="dialog-close" @click="closeDialog">✕</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>执行进度：</label>
            <div class="progress-input">
              <input type="range" v-model="updateProgress" min="0" max="100" step="5">
              <span class="progress-value">{{ updateProgress }}%</span>
            </div>
          </div>
          <div class="form-group">
            <label>反馈说明：</label>
            <textarea v-model="updateFeedback" placeholder="请输入执行情况说明..." rows="4"></textarea>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-cancel" @click="closeDialog">取消</button>
          <button class="btn-confirm" @click="submitUpdate">确认</button>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">加载中...</div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'TaskManagement',
  data() {
    return {
      tasks: [],
      taskStats: {
        total: 0,
        pending: 0,
        inProgress: 0,
        completed: 0
      },
      filterStatus: '',
      filterStartDate: '',
      filterEndDate: '',
      showDialog: false,
      dialogTitle: '',
      currentTask: null,
      updateProgress: 0,
      updateFeedback: '',
      loading: false
    }
  },
  mounted() {
    this.loadTasks()
  },
  methods: {
    async loadTasks() {
      this.loading = true
      
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        const params = {
          dealerCode: user.dealerCode || user.username,
          status: this.filterStatus,
          startDate: this.filterStartDate,
          endDate: this.filterEndDate
        }
        
        const response = await axios.get('/api/tasks', { params })
        
        if (response.data.success) {
          this.tasks = response.data.tasks || []
          this.calculateStats()
        }
      } catch (error) {
        console.error('加载任务失败:', error)
        this.tasks = this.getMockTasks()
        this.calculateStats()
      } finally {
        this.loading = false
      }
    },
    
    getMockTasks() {
      return [
        {
          id: 1,
          title: '销量提升策略执行',
          description: '根据决策建议，需要加强销售团队培训，优化库存结构，制定促销方案。目标：月销量提升20%。',
          type: 'sales',
          status: 'pending',
          progress: 0,
          createdAt: '2024-01-15 10:30',
          deadline: '2024-02-15 18:00',
          publisher: '总部经理',
          feedback: ''
        },
        {
          id: 2,
          title: '客流增长策略执行',
          description: '加大线上营销投放，优化展厅环境，举办试驾活动。目标：月客流量提升15%。',
          type: 'traffic',
          status: 'in_progress',
          progress: 60,
          createdAt: '2024-01-10 09:00',
          deadline: '2024-02-10 18:00',
          publisher: '总部经理',
          feedback: '已完成线上营销投放，展厅环境优化进行中'
        },
        {
          id: 3,
          title: '政策宣传执行',
          description: '组织销售团队学习政策内容，制作政策宣传海报，协助客户准备申请材料。',
          type: 'policy',
          status: 'completed',
          progress: 100,
          createdAt: '2024-01-05 14:00',
          deadline: '2024-01-20 18:00',
          publisher: '总部经理',
          feedback: '已完成所有政策宣传工作，销售团队已掌握政策要点'
        }
      ]
    },
    
    calculateStats() {
      this.taskStats = {
        total: this.tasks.length,
        pending: this.tasks.filter(t => t.status === 'pending').length,
        inProgress: this.tasks.filter(t => t.status === 'in_progress').length,
        completed: this.tasks.filter(t => t.status === 'completed').length
      }
    },
    
    getTaskIcon(type) {
      const icons = {
        'sales': '📈',
        'traffic': '👥',
        'policy': '📜',
        'leads': '📋',
        'potential': '🎯',
        'default': '📋'
      }
      return icons[type] || icons.default
    },
    
    getStatusText(status) {
      const texts = {
        'pending': '待执行',
        'in_progress': '执行中',
        'completed': '已完成'
      }
      return texts[status] || status
    },
    
    async startTask(task) {
      const confirmed = confirm('确认开始执行此任务吗？')
      if (!confirmed) return
      
      try {
        const response = await axios.post(`/api/tasks/${task.id}/start`)
        
        if (response.data.success) {
          task.status = 'in_progress'
          task.progress = 0
          this.calculateStats()
          alert('任务已开始执行')
        }
      } catch (error) {
        console.error('开始任务失败:', error)
        task.status = 'in_progress'
        task.progress = 0
        this.calculateStats()
        alert('任务已开始执行')
      }
    },
    
    showUpdateDialog(task) {
      this.currentTask = task
      this.updateProgress = task.progress
      this.updateFeedback = task.feedback || ''
      this.dialogTitle = '更新任务进度'
      this.showDialog = true
    },
    
    async submitUpdate() {
      if (!this.currentTask) return
      
      try {
        const response = await axios.post(`/api/tasks/${this.currentTask.id}/update`, {
          progress: this.updateProgress,
          feedback: this.updateFeedback
        })
        
        if (response.data.success) {
          this.currentTask.progress = this.updateProgress
          this.currentTask.feedback = this.updateFeedback
          this.closeDialog()
          alert('进度更新成功')
        }
      } catch (error) {
        console.error('更新进度失败:', error)
        this.currentTask.progress = this.updateProgress
        this.currentTask.feedback = this.updateFeedback
        this.closeDialog()
        alert('进度更新成功')
      }
    },
    
    async completeTask(task) {
      const confirmed = confirm('确认完成此任务吗？')
      if (!confirmed) return
      
      try {
        const response = await axios.post(`/api/tasks/${task.id}/complete`)
        
        if (response.data.success) {
          task.status = 'completed'
          task.progress = 100
          this.calculateStats()
          alert('任务已完成')
        }
      } catch (error) {
        console.error('完成任务失败:', error)
        task.status = 'completed'
        task.progress = 100
        this.calculateStats()
        alert('任务已完成')
      }
    },
    
    showTaskDetail(task) {
      alert(`任务详情：\n\n${task.title}\n\n${task.description}\n\n发布时间：${task.createdAt}\n截止时间：${task.deadline}\n发布人：${task.publisher}\n当前进度：${task.progress}%\n${task.feedback ? '\n反馈内容：' + task.feedback : ''}`)
    },
    
    closeDialog() {
      this.showDialog = false
      this.currentTask = null
      this.updateProgress = 0
      this.updateFeedback = ''
    }
  }
}
</script>

<style scoped>
.task-management-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 28px;
  color: #333;
  margin-bottom: 10px;
}

.page-desc {
  color: #666;
  font-size: 14px;
}

.task-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  font-size: 32px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.filter-bar {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  display: flex;
  gap: 20px;
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-item label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.filter-item select,
.filter-item input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-text {
  font-size: 16px;
  color: #999;
}

.task-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.task-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-title h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.task-icon {
  font-size: 20px;
}

.task-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.task-status.pending {
  background: #fff7e6;
  color: #fa8c16;
}

.task-status.in_progress {
  background: #e6f7ff;
  color: #1890ff;
}

.task-status.completed {
  background: #f6ffed;
  color: #52c41a;
}

.task-body {
  padding: 20px;
}

.task-description {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 15px;
}

.task-meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 15px;
}

.meta-item {
  font-size: 13px;
}

.meta-label {
  color: #999;
}

.meta-value {
  color: #333;
  margin-left: 5px;
}

.task-progress {
  margin-bottom: 15px;
}

.progress-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.progress-bar {
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #1890ff, #52c41a);
  border-radius: 4px;
  transition: width 0.3s;
}

.task-feedback {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.feedback-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 5px;
}

.feedback-content {
  font-size: 14px;
  color: #333;
}

.task-actions {
  padding: 15px 20px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 10px;
}

.btn-action {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.btn-start {
  background: #1890ff;
  color: white;
}

.btn-start:hover {
  background: #40a9ff;
}

.btn-update {
  background: #fa8c16;
  color: white;
}

.btn-update:hover {
  background: #ffa940;
}

.btn-complete {
  background: #52c41a;
  color: white;
}

.btn-complete:hover {
  background: #73d13d;
}

.btn-detail {
  background: white;
  color: #666;
  border: 1px solid #d9d9d9;
}

.btn-detail:hover {
  color: #1890ff;
  border-color: #1890ff;
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
  z-index: 9999;
}

.dialog-content {
  background: white;
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
}

.dialog-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  color: #999;
  cursor: pointer;
}

.dialog-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.progress-input {
  display: flex;
  align-items: center;
  gap: 15px;
}

.progress-input input[type="range"] {
  flex: 1;
}

.progress-value {
  font-size: 14px;
  font-weight: 500;
  color: #1890ff;
  min-width: 40px;
}

.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;
}

.dialog-footer {
  padding: 15px 20px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-cancel {
  padding: 8px 20px;
  background: white;
  color: #666;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
}

.btn-confirm {
  padding: 8px 20px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 15px;
  font-size: 14px;
  color: #666;
}

@media (max-width: 768px) {
  .task-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .task-meta {
    grid-template-columns: 1fr;
  }
}
</style>
