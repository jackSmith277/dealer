<template>
  <div class="review-container">
    <div class="page-header">
      <h1>数据提交审核</h1>
      <p class="page-desc">审核经销商提交的销售数据和政策数据</p>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>状态筛选：</label>
        <select v-model="filterStatus" @change="loadSubmissions">
          <option value="">全部</option>
          <option value="pending">待审核</option>
          <option value="approved">已通过</option>
          <option value="rejected">已拒绝</option>
        </select>
      </div>
      <div class="filter-item">
        <label>经销商代码：</label>
        <input type="text" v-model="filterDealerCode" placeholder="输入经销商代码搜索" @input="loadSubmissions">
      </div>
      <div class="stats">
        <span class="stat-item">待审核：<strong class="count-pending">{{ stats.pending }}</strong></span>
        <span class="stat-item">已通过：<strong class="count-approved">{{ stats.approved }}</strong></span>
        <span class="stat-item">已拒绝：<strong class="count-rejected">{{ stats.rejected }}</strong></span>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>提交时间</th>
            <th>经销商代码</th>
            <th>经销商名称</th>
            <th>数据类型</th>
            <th>文件名</th>
            <th>数据月份</th>
            <th>状态</th>
            <th>备注</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in submissions" :key="index">
            <td>{{ item.submitTime }}</td>
            <td>{{ item.dealerCode }}</td>
            <td>{{ item.dealerName }}</td>
            <td>{{ item.dataType }}</td>
            <td class="file-cell" :title="item.fileName">{{ item.fileName }}</td>
            <td>{{ item.month }}</td>
            <td>
              <span :class="['status-badge', item.status]">{{ getStatusText(item.status) }}</span>
            </td>
            <td class="note-cell">
              <span v-if="item.note" :title="item.note">{{ item.note }}</span>
              <span v-else class="no-note">-</span>
            </td>
            <td class="action-cell">
              <button class="btn-download" @click="downloadFile(item)" title="下载文件">下载</button>
              <template v-if="item.status === 'pending'">
                <button class="btn-approve" @click="review(item, 'approve')">通过</button>
                <button class="btn-reject" @click="showRejectDialog(item)">拒绝</button>
              </template>
              <span v-else class="done-text">已处理</span>
            </td>
          </tr>
          <tr v-if="submissions.length === 0">
            <td colspan="9" class="empty-text">暂无提交记录</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 拒绝原因对话框 -->
    <div v-if="rejectDialog.visible" class="dialog-overlay" @click.self="closeRejectDialog">
      <div class="dialog">
        <h3>拒绝原因</h3>
        <textarea v-model="rejectDialog.note" rows="4" placeholder="请输入拒绝原因..."></textarea>
        <div class="dialog-actions">
          <button class="btn-cancel" @click="closeRejectDialog">取消</button>
          <button class="btn-confirm-reject" @click="confirmReject">确认拒绝</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AdminSubmissionReview',
  data() {
    return {
      submissions: [],
      filterStatus: 'pending',
      filterDealerCode: '',
      stats: { pending: 0, approved: 0, rejected: 0 },
      rejectDialog: {
        visible: false,
        item: null,
        note: ''
      }
    }
  },
  mounted() {
    this.loadSubmissions()
  },
  methods: {
    async loadSubmissions() {
      try {
        const params = {}
        if (this.filterStatus) params.status = this.filterStatus
        if (this.filterDealerCode) params.dealerCode = this.filterDealerCode

        const response = await axios.get('/api/data-submit/admin/list', { params })
        if (response.data.success) {
          this.submissions = response.data.data
          this.calcStats()
        }
      } catch (error) {
        console.error('加载提交记录失败:', error)
      }
    },
    calcStats() {
      const counts = { pending: 0, approved: 0, rejected: 0 }
      this.submissions.forEach(item => {
        if (counts[item.status] !== undefined) counts[item.status]++
      })
      this.stats = counts
    },
    getStatusText(status) {
      const map = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
      return map[status] || status
    },
    async review(item, action) {
      try {
        const response = await axios.put(`/api/data-submit/${item.id}/review`, { action })
        if (response.data.success) {
          this.loadSubmissions()
        }
      } catch (error) {
        console.error('审核操作失败:', error)
        alert('审核操作失败：' + (error.response?.data?.message || '未知错误'))
      }
    },
    showRejectDialog(item) {
      this.rejectDialog = { visible: true, item, note: '' }
    },
    closeRejectDialog() {
      this.rejectDialog = { visible: false, item: null, note: '' }
    },
    async confirmReject() {
      const { item, note } = this.rejectDialog
      try {
        const response = await axios.put(`/api/data-submit/${item.id}/review`, {
          action: 'reject',
          note: note
        })
        if (response.data.success) {
          this.closeRejectDialog()
          this.loadSubmissions()
        }
      } catch (error) {
        console.error('拒绝操作失败:', error)
        alert('拒绝操作失败：' + (error.response?.data?.message || '未知错误'))
      }
    },
    async downloadFile(item) {
      try {
        const response = await axios.get(`/api/data-submit/${item.id}/download`, {
          responseType: 'blob'
        })
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', item.fileName)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('下载文件失败:', error)
        alert('下载失败：' + (error.response?.data?.message || '未知错误'))
      }
    }
  }
}
</script>

<style scoped>
.review-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
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

/* 筛选栏 */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-size: 14px;
  color: #333;
  white-space: nowrap;
}

.filter-item select,
.filter-item input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.filter-item input {
  width: 180px;
}

.filter-item select:focus,
.filter-item input:focus {
  border-color: #1890ff;
}

.stats {
  margin-left: auto;
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: 13px;
  color: #666;
}

.count-pending { color: #fa8c16; }
.count-approved { color: #52c41a; }
.count-rejected { color: #ff4d4f; }

/* 表格 */
.table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e8e8e8;
  font-size: 14px;
}

th {
  background: #fafafa;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
}

td {
  color: #666;
}

.file-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note-cell {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-note {
  color: #ccc;
}

.status-badge {
  display: inline-block;
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

.action-cell {
  white-space: nowrap;
}

.btn-approve,
.btn-reject,
.btn-download {
  padding: 6px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
  margin-right: 8px;
}

.btn-approve {
  background: #52c41a;
  color: white;
}

.btn-approve:hover {
  background: #73d13d;
}

.btn-reject {
  background: #ff4d4f;
  color: white;
}

.btn-reject:hover {
  background: #ff7875;
}

.btn-download {
  background: #1890ff;
  color: white;
}

.btn-download:hover {
  background: #40a9ff;
}

.done-text {
  color: #999;
  font-size: 13px;
}

.empty-text {
  text-align: center;
  color: #999;
  padding: 40px 0;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 8px;
  padding: 24px;
  width: 420px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dialog h3 {
  margin-bottom: 16px;
  color: #333;
  font-size: 16px;
}

.dialog textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
}

.dialog textarea:focus {
  border-color: #1890ff;
  outline: none;
}

.dialog-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel {
  padding: 8px 20px;
  background: white;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-cancel:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.btn-confirm-reject {
  padding: 8px 20px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-confirm-reject:hover {
  background: #ff7875;
}
</style>
