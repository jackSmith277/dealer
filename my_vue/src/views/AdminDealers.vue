<template>
  <div class="admin-dealers-container">
    <div class="admin-dealers-header">
      <h1>经销商管理</h1>
      <div class="header-actions">
        <button class="back-btn" @click="$router.push('/dashboard/index')">
          ← 返回首页
        </button>
        <button class="add-btn" @click="$router.push('/admin/dealers/add')">
          + 添加经销商
        </button>
      </div>
    </div>
    
    <div class="admin-dealers-content">
      <!-- 搜索和筛选 -->
      <div class="search-filter">
        <div class="search-bar">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索经销商名称或联系人..."
          >
          <button class="search-btn">🔍</button>
        </div>
        
        <div class="filter-options">
          <RegionCascader 
            v-model="filters.region"
          />
          
          <CustomSelect 
            v-model="filters.level" 
            :options="levelOptions"
            placeholder="所有等级"
          />
        </div>
      </div>
      
      <!-- 统计信息 -->
      <div class="stats-container">
        <div class="stat-card">
          <h3>总经销商数</h3>
          <p>{{ totalDealers }}</p>
        </div>
        <div class="stat-card">
          <h3>启用状态</h3>
          <p>{{ activeDealers }}</p>
        </div>
        <div class="stat-card">
          <h3>禁用状态</h3>
          <p>{{ inactiveDealers }}</p>
        </div>
      </div>
      
      <!-- 经销商列表 -->
      <div class="dealers-table-container">
        <div v-if="loading" class="loading">
          加载中...
        </div>
        
        <div v-else-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div v-else>
          <table class="dealers-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>经销商名称</th>
                <th>等级</th>
                <th>地区</th>
                <th>联系人</th>
                <th>电话</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="dealer in filteredDealers" :key="dealer.id">
                <td>{{ dealer.id }}</td>
                <td>{{ dealer.dealer_name }}</td>
                <td>{{ dealer.level }}</td>
                <td>{{ dealer.region }}</td>
                <td>{{ dealer.contact_name }}</td>
                <td>{{ dealer.contact_phone }}</td>
                <td>
                  <span class="status-badge" :class="dealer.status === 1 ? 'active' : 'inactive'">
                    {{ dealer.status === 1 ? '启用' : '禁用' }}
                  </span>
                </td>
                <td class="actions">
                  <button class="view-btn" @click="viewDealer(dealer)">
                    查看
                  </button>
                  <button class="edit-btn" @click="editDealer(dealer)">
                    编辑
                  </button>
                  <button 
                    :class="dealer.status === 1 ? 'disable-btn' : 'enable-btn'"
                    @click="toggleDealerStatus(dealer)"
                  >
                    {{ dealer.status === 1 ? '禁用' : '启用' }}
                  </button>
                  <button class="delete-btn" @click="deleteDealer(dealer)">
                    删除
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          
          <!-- 空状态 -->
          <div v-if="filteredDealers.length === 0" class="empty-state">
            没有找到经销商
          </div>
        </div>
      </div>
      
      <!-- 分页 -->
      <div class="pagination" v-if="!loading && !error && allFilteredDealers.length > 0">
        <button class="page-btn" @click.stop.prevent="prevPage" :disabled="currentPage === 1">
          上一页
        </button>
        <span class="page-info">
          第 {{ currentPage }} / {{ totalPages }} 页 (共 {{ allFilteredDealers.length }} 条)
        </span>
        <button class="page-btn" @click.stop.prevent="nextPage" :disabled="currentPage >= totalPages">
          下一页
        </button>
      </div>
    </div>
    
    <!-- 查看经销商弹窗 -->
    <div class="modal" v-if="showViewModal" @click.self="showViewModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <div class="header-title">
            <div class="title-icon">🏢</div>
            <div>
              <h3>经销商详情</h3>
              <p class="header-subtitle">{{ viewDealerData.dealer_name }}</p>
            </div>
          </div>
          <button class="close-btn" @click="showViewModal = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <h4 class="section-title">基本信息</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <label>经销商名称</label>
                <span class="detail-value">{{ viewDealerData.dealer_name }}</span>
              </div>
              <div class="detail-item">
                <label>经销商等级</label>
                <span class="detail-value detail-badge" :class="'level-' + viewDealerData.level">
                  {{ viewDealerData.level }}
                </span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h4 class="section-title">地区与地址</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <label>所属地区</label>
                <span class="detail-value">{{ viewDealerData.region }}</span>
              </div>
              <div class="detail-item full-width">
                <label>详细地址</label>
                <span class="detail-value">{{ viewDealerData.address }}</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h4 class="section-title">联系信息</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <label>联系人</label>
                <span class="detail-value">{{ viewDealerData.contact_name }}</span>
              </div>
              <div class="detail-item">
                <label>联系电话</label>
                <span class="detail-value contact-phone">
                  <a :href="'tel:' + viewDealerData.contact_phone">{{ viewDealerData.contact_phone }}</a>
                </span>
              </div>
            </div>
          </div>

          <div class="detail-section status-section">
            <h4 class="section-title">状态</h4>
            <div class="status-display">
              <span class="status-badge" :class="viewDealerData.status === 1 ? 'active' : 'inactive'">
                {{ viewDealerData.status === 1 ? '✓ 启用' : '✕ 禁用' }}
              </span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-close" @click="showViewModal = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import RegionCascader from '@/components/RegionCascader.vue'
import CustomSelect from '@/components/CustomSelect.vue'

export default {
  name: 'AdminDealers',
  components: {
    RegionCascader,
    CustomSelect
  },
  data() {
    return {
      dealers: [],
      searchQuery: '',
      filters: {
        region: { province: '', city: '' },
        level: ''
      },
      loading: true,
      error: '',
      currentPage: 1,
      pageSize: 10,
      showViewModal: false,
      viewDealerData: {},
      levelOptions: [
        { value: '', label: '所有等级' },
        { value: 'A+', label: 'A+' },
        { value: 'A', label: 'A' },
        { value: 'B+', label: 'B+' },
        { value: 'B', label: 'B' },
        { value: 'C+', label: 'C+' },
        { value: 'C', label: 'C' }
      ]
    }
  },
  computed: {
    // 先过滤，再分页
    allFilteredDealers() {
      let result = [...this.dealers]
      
      // 搜索过滤
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        result = result.filter(dealer => 
          (dealer.dealer_name && dealer.dealer_name.toLowerCase().includes(query)) ||
          (dealer.contact_name && dealer.contact_name.toLowerCase().includes(query))
        )
      }
      
      // 地区过滤 - 将省份和城市合并与region字段匹配
      if (this.filters.region.province && this.filters.region.province !== '全部地区') {
        if (this.filters.region.city && this.filters.region.city !== '全部城市') {
          // 选择了省份和城市，精确匹配 "省份城市"
          const regionStr = this.filters.region.province + this.filters.region.city
          result = result.filter(dealer => dealer.region === regionStr)
        } else {
          // 只选择了省份或选择了全部城市，匹配以省份开头的region
          result = result.filter(dealer => dealer.region && dealer.region.startsWith(this.filters.region.province))
        }
      }
      
      // 等级过滤
      if (this.filters.level) {
        result = result.filter(dealer => dealer.level === this.filters.level)
      }
      
      return result
    },
    filteredDealers() {
      // 分页
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.allFilteredDealers.slice(start, end)
    },
    totalDealers() {
      return this.dealers.length
    },
    activeDealers() {
      return this.dealers.filter(dealer => dealer.status === 1).length
    },
    inactiveDealers() {
      return this.dealers.filter(dealer => dealer.status === 0).length
    },
    totalPages() {
      const pages = Math.ceil(this.allFilteredDealers.length / this.pageSize)
      console.log('totalPages computed:', pages, 'allFilteredDealers.length:', this.allFilteredDealers.length, 'pageSize:', this.pageSize)
      return pages
    }
  },
  watch: {
    currentPage(newVal) {
      console.log('currentPage changed to:', newVal)
    }
  },
  mounted() {
    this.loadDealers()
  },
  methods: {
    async loadDealers() {
      this.loading = true
      this.error = ''
      
      try {
        const response = await axios.get('http://localhost:5000/api/dealers/list')
        
        if (response.data && response.data.dealers) {
          this.dealers = response.data.dealers.map(dealer => ({
            id: dealer.id,
            user_id: dealer.user_id,
            dealer_name: dealer.dealer_name || dealer.dealer_code,
            level: dealer.level || dealer.fed_level || '未设置',
            region: dealer.region || '未设置',
            province: dealer.province || '',
            city: dealer.city || '',
            contact_name: dealer.contact_name || '',
            contact_phone: dealer.contact_phone || '',
            status: dealer.status || 1
          }))
        }
        
        console.log('加载的经销商数据:', this.dealers)
      } catch (err) {
        this.error = err.response?.data?.message || '加载经销商列表失败'
      } finally {
        this.loading = false
      }
    },
    
    handleSearch() {
      console.log('handleSearch called, resetting currentPage to 1')
      this.currentPage = 1
    },
    
    handleFilter() {
      console.log('handleFilter called, resetting currentPage to 1')
      this.currentPage = 1
    },
    
    viewDealer(dealer) {
      this.viewDealerData = { ...dealer }
      this.showViewModal = true
    },
    
    editDealer(dealer) {
      this.$router.push(`/admin/dealers/edit/${dealer.user_id}`)
    },
    
    async toggleDealerStatus(dealer) {
      const newStatus = dealer.status === 1 ? 0 : 1
      const statusText = newStatus === 1 ? '启用' : '禁用'
      
      if (!confirm(`确定要${statusText}这个经销商吗？`)) {
        return
      }
      
      try {
        const token = this.$store.state.token
        await axios.put(`http://localhost:5000/api/users/${dealer.user_id}`, {
          status: newStatus
        }, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        })
        
        dealer.status = newStatus
        alert(`经销商${statusText}成功`)
      } catch (err) {
        alert(`${statusText}失败：` + (err.response?.data?.error || '未知错误'))
      }
    },
    
    async deleteDealer(dealer) {
      if (!confirm('确定要删除这个经销商吗？删除后无法恢复。')) {
        return
      }
      
      try {
        const token = this.$store.state.token
        await axios.delete(`http://localhost:5000/api/users/${dealer.user_id}`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        })
        
        // 重新加载列表
        this.loadDealers()
        alert('经销商删除成功')
      } catch (err) {
        alert('删除失败：' + (err.response?.data?.error || '未知错误'))
      }
    },
    
    prevPage() {
      console.log('prevPage called, currentPage:', this.currentPage, 'totalPages:', this.totalPages)
      if (this.currentPage > 1) {
        this.currentPage--
        console.log('currentPage changed to:', this.currentPage)
      }
    },
    
    nextPage() {
      console.log('nextPage called, currentPage:', this.currentPage, 'totalPages:', this.totalPages)
      if (this.currentPage < this.totalPages) {
        this.currentPage++
        console.log('currentPage changed to:', this.currentPage)
      }
    }
  }
}
</script>

<style scoped>
.admin-dealers-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  color: #333;
  background-color: #ffffff;
  min-height: 100vh;
}

.admin-dealers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.admin-dealers-header h1 {
  font-size: 24px;
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.back-btn {
  padding: 8px 16px;
  background-color: #ffffff;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background-color: #f5f5f5;
  border-color: #1890ff;
  color: #1890ff;
}

.add-btn {
  padding: 8px 16px;
  background-color: #1890ff;
  color: #ffffff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.add-btn:hover {
  background-color: #40a9ff;
}

.admin-dealers-content {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.search-filter {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 15px;
}

.search-bar {
  display: flex;
  flex: 1;
  min-width: 300px;
}

.search-bar input {
  flex: 1;
  padding: 10px 12px;
  background-color: #ffffff;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 4px 0 0 4px;
  font-size: 14px;
  box-sizing: border-box;
  height: 40px;
  display: flex;
  align-items: center;
}

.search-btn {
  padding: 10px 15px;
  background-color: #f0f0f0;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  transition: background-color 0.3s;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.search-btn:hover {
  background-color: #e0e0e0;
}

.filter-options {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: flex-end;
}

.filter-options > div {
  flex: 0 0 auto;
  width: 140px;
}

.filter-options > :deep(.custom-select-wrapper) {
  flex: 0 0 auto;
  width: 140px;
}

.stats-container {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1;
  min-width: 200px;
  background-color: #fafafa;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stat-card h3 {
  font-size: 14px;
  color: #666;
  margin: 0 0 10px 0;
}

.stat-card p {
  font-size: 24px;
  font-weight: bold;
  margin: 0;
  color: #333;
}

.dealers-table-container {
  margin-bottom: 30px;
  overflow-x: auto;
}

.loading {
  text-align: center;
  padding: 50px;
  font-size: 18px;
  color: #888;
}

.error-message {
  background-color: rgba(255, 0, 0, 0.1);
  border: 1px solid #ff4444;
  color: #ff4444;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.dealers-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #ffffff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.dealers-table th,
.dealers-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #e8e8e8;
  color: #333;
  vertical-align: middle;
}

.dealers-table th {
  background-color: #fafafa;
  font-weight: bold;
  font-size: 14px;
  color: #333;
}

.dealers-table tr:hover {
  background-color: #f5f5f5;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.status-badge.active {
  background-color: rgba(76, 175, 80, 0.2);
  color: #4CAF50;
}

.status-badge.inactive {
  background-color: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.actions {
  white-space: nowrap;
}

.view-btn,
.edit-btn,
.delete-btn,
.disable-btn,
.enable-btn {
  display: inline-block;
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.3s;
  margin: 2px;
}

.view-btn {
  background-color: #2196F3;
  color: white;
}

.view-btn:hover {
  background-color: #1976D2;
}

.edit-btn {
  background-color: #FFC107;
  color: #333;
}

.edit-btn:hover {
  background-color: #FFB300;
}

.delete-btn {
  background-color: #F44336;
  color: white;
}

.delete-btn:hover {
  background-color: #D32F2F;
}

.disable-btn {
  background-color: #FF9800;
  color: white;
}

.disable-btn:hover {
  background-color: #F57C00;
}

.enable-btn {
  background-color: #4CAF50;
  color: white;
}

.enable-btn:hover {
  background-color: #388E3C;
}

.empty-state {
  text-align: center;
  padding: 50px;
  font-size: 18px;
  color: #888;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 30px;
}

.page-btn {
  padding: 8px 16px;
  background-color: #ffffff;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  background-color: #f5f5f5;
  border-color: #1890ff;
  color: #1890ff;
}

.page-btn:disabled {
  background-color: #f5f5f5;
  color: #999;
  cursor: not-allowed;
  border-color: #d9d9d9;
}

.page-info {
  font-size: 14px;
  color: #666;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background-color: #ffffff;
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  animation: slideUp 0.3s ease-out;
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
  padding: 28px 28px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.title-icon {
  font-size: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #1890ff 0%, #0050b3 100%);
  border-radius: 10px;
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.header-subtitle {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: #6b7280;
}

.close-btn {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 8px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.close-btn:hover {
  background-color: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 28px;
  overflow-y: auto;
  flex: 1;
}

.detail-section {
  margin-bottom: 28px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f0f0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-item label {
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.detail-value {
  font-size: 15px;
  color: #1f2937;
  font-weight: 500;
  word-break: break-word;
}

.detail-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  width: fit-content;
}

.type-4S店 {
  background-color: #dbeafe;
  color: #1e40af;
}

.type-二级网点 {
  background-color: #ddd6fe;
  color: #5b21b6;
}

.type-授权经销商 {
  background-color: #dcfce7;
  color: #166534;
}

.level-A级 {
  background-color: #fef3c7;
  color: #92400e;
}

.level-B级 {
  background-color: #fed7aa;
  color: #92400e;
}

.level-C级 {
  background-color: #fecaca;
  color: #991b1b;
}

.contact-phone a {
  color: #1890ff;
  text-decoration: none;
  transition: color 0.2s;
}

.contact-phone a:hover {
  color: #0050b3;
  text-decoration: underline;
}

.status-section {
  background-color: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 0;
}

.status-display {
  display: flex;
  align-items: center;
}

.status-badge {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.status-badge.active {
  background-color: #d1fae5;
  color: #065f46;
}

.status-badge.inactive {
  background-color: #fee2e2;
  color: #991b1b;
}

.modal-footer {
  padding: 20px 28px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  background-color: #f9fafb;
  flex-shrink: 0;
  position: sticky;
  bottom: 0;
  z-index: 10;
}

.btn-close {
  padding: 10px 24px;
  background-color: #ffffff;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-close:hover {
  background-color: #f3f4f6;
  border-color: #9ca3af;
  color: #1f2937;
}

@media (max-width: 768px) {
  .search-filter {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-bar {
    min-width: unset;
  }
  
  .filter-options {
    justify-content: space-between;
    align-items: stretch;
  }

  .filter-options > div {
    flex: 1;
    min-width: unset;
  }

  .filter-options > :deep(.custom-select-wrapper) {
    flex: 1;
    min-width: unset;
  }
  
  .stats-container {
    flex-direction: column;
  }
  
  .stat-card {
    min-width: unset;
  }
  
  .dealers-table {
    font-size: 12px;
  }
  
  .dealers-table th,
  .dealers-table td {
    padding: 8px 10px;
  }
  
  .actions {
    flex-direction: column;
    gap: 4px;
  }

  .modal-content {
    width: 95%;
    max-width: 100%;
    max-height: 90vh;
    border-radius: 16px 16px 0 0;
  }

  .modal-header {
    padding: 20px 20px 16px;
  }

  .header-title {
    gap: 12px;
  }

  .title-icon {
    width: 40px;
    height: 40px;
    font-size: 24px;
  }

  .modal-header h3 {
    font-size: 18px;
  }

  .modal-body {
    padding: 20px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .detail-item.full-width {
    grid-column: 1;
  }

  .modal-footer {
    padding: 16px 20px;
  }

  .btn-close {
    width: 100%;
  }
}
</style>