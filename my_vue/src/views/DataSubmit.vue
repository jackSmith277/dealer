<template>
  <div class="data-submit-container">
    <div class="page-header">
      <h1>数据提交</h1>
      <p class="page-desc">提交月度销售数据和政策数据</p>
    </div>
    
    <div class="submit-sections">
      <div class="submit-section">
        <div class="section-header">
          <h2>📊 销售数据提交</h2>
          <span class="section-desc">上传月度销售数据Excel文件</span>
        </div>
        
        <div class="upload-area">
          <div class="upload-box" @click="triggerSalesUpload" @dragover.prevent @drop.prevent="handleSalesDrop">
            <input type="file" ref="salesFileInput" @change="handleSalesFileChange" accept=".xlsx,.xls,.csv" style="display: none">
            <div class="upload-icon">📁</div>
            <div class="upload-text">
              <p class="upload-title">点击或拖拽文件到此处上传</p>
              <p class="upload-hint">支持 .xlsx, .xls, .csv 格式</p>
            </div>
          </div>
          
          <div v-if="salesFile" class="file-info">
            <div class="file-name">
              <span class="file-icon">📄</span>
              <span>{{ salesFile.name }}</span>
            </div>
            <div class="file-size">{{ formatFileSize(salesFile.size) }}</div>
          </div>
        </div>
        
        <div class="form-group">
          <label>数据月份：</label>
          <input type="month" v-model="salesMonth" class="month-input">
        </div>
        
        <div class="form-actions">
          <button class="btn-submit" @click="submitSalesData" :disabled="!salesFile || !salesMonth || submitting">
            {{ submitting ? '提交中...' : '提交销售数据' }}
          </button>
        </div>
      </div>
      
      <div class="submit-section">
        <div class="section-header">
          <h2>📜 政策数据提交</h2>
          <span class="section-desc">上传当地政策数据Excel文件</span>
        </div>
        
        <div class="upload-area">
          <div class="upload-box" @click="triggerPolicyUpload" @dragover.prevent @drop.prevent="handlePolicyDrop">
            <input type="file" ref="policyFileInput" @change="handlePolicyFileChange" accept=".xlsx,.xls,.csv" style="display: none">
            <div class="upload-icon">📁</div>
            <div class="upload-text">
              <p class="upload-title">点击或拖拽文件到此处上传</p>
              <p class="upload-hint">支持 .xlsx, .xls, .csv 格式</p>
            </div>
          </div>
          
          <div v-if="policyFile" class="file-info">
            <div class="file-name">
              <span class="file-icon">📄</span>
              <span>{{ policyFile.name }}</span>
            </div>
            <div class="file-size">{{ formatFileSize(policyFile.size) }}</div>
          </div>
        </div>
        
        <div class="form-group">
          <label>政策生效月份：</label>
          <input type="month" v-model="policyMonth" class="month-input">
        </div>
        
        <div class="form-actions">
          <button class="btn-submit" @click="submitPolicyData" :disabled="!policyFile || !policyMonth || submitting">
            {{ submitting ? '提交中...' : '提交政策数据' }}
          </button>
        </div>
      </div>
    </div>
    
    <div class="submit-history">
      <h2>提交历史</h2>
      <div class="history-table">
        <table>
          <thead>
            <tr>
              <th>提交时间</th>
              <th>数据类型</th>
              <th>文件名</th>
              <th>状态</th>
              <th>备注</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(record, index) in submitHistory" :key="index">
              <td>{{ record.submitTime }}</td>
              <td>{{ record.dataType }}</td>
              <td>{{ record.fileName }}</td>
              <td>
                <span :class="['status-badge', record.status]">{{ getStatusText(record.status) }}</span>
              </td>
              <td>{{ record.note || '-' }}</td>
            </tr>
            <tr v-if="submitHistory.length === 0">
              <td colspan="5" class="empty-text">暂无提交记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">数据提交中...</div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'DataSubmit',
  data() {
    return {
      salesFile: null,
      salesMonth: this.getCurrentMonth(),
      policyFile: null,
      policyMonth: this.getCurrentMonth(),
      submitting: false,
      loading: false,
      submitHistory: []
    }
  },
  mounted() {
    this.loadSubmitHistory()
  },
  methods: {
    getCurrentMonth() {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      return `${year}-${month}`
    },
    
    triggerSalesUpload() {
      this.$refs.salesFileInput.click()
    },
    
    triggerPolicyUpload() {
      this.$refs.policyFileInput.click()
    },
    
    handleSalesFileChange(event) {
      const file = event.target.files[0]
      if (file) {
        this.salesFile = file
      }
    },
    
    handlePolicyFileChange(event) {
      const file = event.target.files[0]
      if (file) {
        this.policyFile = file
      }
    },
    
    handleSalesDrop(event) {
      const file = event.dataTransfer.files[0]
      if (file && this.isValidFile(file)) {
        this.salesFile = file
      }
    },
    
    handlePolicyDrop(event) {
      const file = event.dataTransfer.files[0]
      if (file && this.isValidFile(file)) {
        this.policyFile = file
      }
    },
    
    isValidFile(file) {
      const validTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'text/csv'
      ]
      const validExtensions = ['.xlsx', '.xls', '.csv']
      const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
      
      return validTypes.includes(file.type) || validExtensions.includes(fileExtension)
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    },
    
    async submitSalesData() {
      if (!this.salesFile || !this.salesMonth) {
        alert('请选择文件和数据月份')
        return
      }
      
      this.submitting = true
      this.loading = true
      
      try {
        const formData = new FormData()
        formData.append('file', this.salesFile)
        formData.append('month', this.salesMonth)
        formData.append('dealerCode', this.getDealerCode())
        
        const response = await axios.post('/api/data-submit/sales', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        if (response.data.success) {
          alert('销售数据提交成功')
          this.salesFile = null
          this.$refs.salesFileInput.value = ''
          this.loadSubmitHistory()
        } else {
          alert('提交失败：' + (response.data.message || '未知错误'))
        }
      } catch (error) {
        console.error('提交销售数据失败:', error)
        alert('提交失败，请稍后重试')
      } finally {
        this.submitting = false
        this.loading = false
      }
    },
    
    async submitPolicyData() {
      if (!this.policyFile || !this.policyMonth) {
        alert('请选择文件和政策生效月份')
        return
      }
      
      this.submitting = true
      this.loading = true
      
      try {
        const formData = new FormData()
        formData.append('file', this.policyFile)
        formData.append('month', this.policyMonth)
        formData.append('dealerCode', this.getDealerCode())
        
        const response = await axios.post('/api/data-submit/policy', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        if (response.data.success) {
          alert('政策数据提交成功')
          this.policyFile = null
          this.$refs.policyFileInput.value = ''
          this.loadSubmitHistory()
        } else {
          alert('提交失败：' + (response.data.message || '未知错误'))
        }
      } catch (error) {
        console.error('提交政策数据失败:', error)
        alert('提交失败，请稍后重试')
      } finally {
        this.submitting = false
        this.loading = false
      }
    },
    
    getDealerCode() {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      return user.dealerCode || user.username || ''
    },
    
    async loadSubmitHistory() {
      try {
        const response = await axios.get('/api/data-submit/history', {
          params: {
            dealerCode: this.getDealerCode()
          }
        })
        
        if (response.data.success) {
          this.submitHistory = response.data.history || []
        }
      } catch (error) {
        console.error('加载提交历史失败:', error)
      }
    },
    
    getStatusText(status) {
      const statusMap = {
        'pending': '待审核',
        'approved': '已通过',
        'rejected': '已拒绝'
      }
      return statusMap[status] || status
    }
  }
}
</script>

<style scoped>
.data-submit-container {
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

.submit-sections {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.submit-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-header {
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 18px;
  color: #333;
  margin-bottom: 5px;
}

.section-desc {
  color: #666;
  font-size: 13px;
}

.upload-area {
  margin-bottom: 20px;
}

.upload-box {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-box:hover {
  border-color: #1890ff;
  background-color: #f0f9ff;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.upload-title {
  font-size: 16px;
  color: #333;
  margin-bottom: 5px;
}

.upload-hint {
  font-size: 13px;
  color: #999;
}

.file-info {
  margin-top: 15px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #333;
  font-size: 14px;
}

.file-icon {
  font-size: 18px;
}

.file-size {
  color: #999;
  font-size: 13px;
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

.month-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.form-actions {
  text-align: right;
}

.btn-submit {
  padding: 10px 30px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-submit:hover:not(:disabled) {
  background: #40a9ff;
}

.btn-submit:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

.submit-history {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.submit-history h2 {
  font-size: 18px;
  color: #333;
  margin-bottom: 20px;
}

.history-table table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th,
.history-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e8e8e8;
}

.history-table th {
  background: #fafafa;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.history-table td {
  color: #666;
  font-size: 14px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.pending {
  background: #fff7e6;
  color: #fa8c16;
}

.status-badge.approved {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.rejected {
  background: #fff2f0;
  color: #ff4d4f;
}

.empty-text {
  text-align: center;
  color: #999;
  padding: 40px 0;
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
  .submit-sections {
    grid-template-columns: 1fr;
  }
}
</style>
