<template>
  <div class="admin-dealers-container">
    <div class="admin-dealers-header">
      <h1>经销商管理</h1>
      <div class="header-actions">
        <button class="back-btn" @click="$router.push('/dashboard')">
          ← 返回仪表盘
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
            @input="handleSearch"
          >
          <button class="search-btn">🔍</button>
        </div>
        
        <div class="filter-options">
          <select v-model="filters.region" @change="handleFilter">
            <option value="">所有地区</option>
            <option value="北京">北京</option>
            <option value="上海">上海</option>
            <option value="广州">广州</option>
            <option value="深圳">深圳</option>
          </select>
          
          <select v-model="filters.level" @change="handleFilter">
            <option value="">所有等级</option>
            <option value="A级">A级</option>
            <option value="B级">B级</option>
            <option value="C级">C级</option>
          </select>
          
          <select v-model="filters.type" @change="handleFilter">
            <option value="">所有类型</option>
            <option value="4S店">4S店</option>
            <option value="二级网点">二级网点</option>
            <option value="授权经销商">授权经销商</option>
          </select>
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
                <th>类型</th>
                <th>品牌</th>
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
                <td>{{ dealer.dealer_type }}</td>
                <td>{{ dealer.brand }}</td>
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
      <div class="pagination" v-if="!loading && !error && dealers.length > 0">
        <button class="page-btn" @click="prevPage" :disabled="currentPage === 1">
          上一页
        </button>
        <span class="page-info">
          第 {{ currentPage }} / {{ totalPages }} 页
        </span>
        <button class="page-btn" @click="nextPage" :disabled="currentPage === totalPages">
          下一页
        </button>
      </div>
    </div>
    
    <!-- 查看经销商弹窗 -->
    <div class="modal" v-if="showViewModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>经销商详情</h3>
          <button class="close-btn" @click="showViewModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-item">
            <label>经销商名称：</label>
            <span>{{ viewDealerData.dealer_name }}</span>
          </div>
          <div class="detail-item">
            <label>经销商类型：</label>
            <span>{{ viewDealerData.dealer_type }}</span>
          </div>
          <div class="detail-item">
            <label>主营品牌：</label>
            <span>{{ viewDealerData.brand }}</span>
          </div>
          <div class="detail-item">
            <label>经销商等级：</label>
            <span>{{ viewDealerData.level }}</span>
          </div>
          <div class="detail-item">
            <label>所属地区：</label>
            <span>{{ viewDealerData.region }}</span>
          </div>
          <div class="detail-item">
            <label>联系人：</label>
            <span>{{ viewDealerData.contact_name }}</span>
          </div>
          <div class="detail-item">
            <label>联系电话：</label>
            <span>{{ viewDealerData.contact_phone }}</span>
          </div>
          <div class="detail-item">
            <label>详细地址：</label>
            <span>{{ viewDealerData.address }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="close-btn" @click="showViewModal = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AdminDealers',
  data() {
    return {
      dealers: [],
      searchQuery: '',
      filters: {
        region: '',
        level: '',
        type: ''
      },
      loading: true,
      error: '',
      currentPage: 1,
      pageSize: 10,
      showViewModal: false,
      viewDealerData: {}
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
      
      // 地区过滤
      if (this.filters.region) {
        result = result.filter(dealer => dealer.region === this.filters.region)
      }
      
      // 等级过滤
      if (this.filters.level) {
        result = result.filter(dealer => dealer.level === this.filters.level)
      }
      
      // 类型过滤
      if (this.filters.type) {
        result = result.filter(dealer => dealer.dealer_type === this.filters.type)
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
      return Math.ceil(this.allFilteredDealers.length / this.pageSize)
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
        const token = this.$store.state.token
        const response = await axios.get('http://localhost:5000/api/users', {
          headers: {
            Authorization: `Bearer ${token}`
          }
        })
        
        // 过滤出经销商用户
        this.dealers = response.data
          .filter(user => user.role === 'dealer' && user.dealer)
          .map(user => ({
            id: user.id, // 用户ID
            dealer_id: user.dealer.id, // 经销商ID
            status: user.status,
            dealer_name: user.dealer.dealer_name || '未设置',
            dealer_type: user.dealer.dealer_type || '未设置',
            brand: user.dealer.brand || '未设置',
            level: user.dealer.level || '未设置',
            region: user.dealer.region || '未设置',
            contact_name: user.dealer.contact_name || '未设置',
            contact_phone: user.dealer.contact_phone || '未设置',
            address: user.dealer.address || '未设置'
          }))
        
        console.log('加载的经销商数据:', this.dealers)
      } catch (err) {
        this.error = err.response?.data?.error || '加载经销商列表失败'
      } finally {
        this.loading = false
      }
    },
    
    handleSearch() {
      this.currentPage = 1
    },
    
    handleFilter() {
      this.currentPage = 1
    },
    
    viewDealer(dealer) {
      this.viewDealerData = { ...dealer }
      this.showViewModal = true
    },
    
    editDealer(dealer) {
      this.$router.push(`/admin/dealers/edit/${dealer.id}`)
    },
    
    async deleteDealer(dealer) {
      if (!confirm('确定要删除这个经销商吗？删除后无法恢复。')) {
        return
      }
      
      try {
        const token = this.$store.state.token
        await axios.delete(`http://localhost:5000/api/users/${dealer.id}`, {
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
      if (this.currentPage > 1) {
        this.currentPage--
      }
    },
    
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
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
  padding: 10px;
  background-color: #ffffff;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 4px 0 0 4px;
  font-size: 14px;
}

.search-btn {
  padding: 10px 15px;
  background-color: #f0f0f0;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  transition: background-color 0.3s;
}

.search-btn:hover {
  background-color: #e0e0e0;
}

.filter-options {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-options select {
  padding: 10px;
  background-color: #ffffff;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  min-width: 120px;
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
  display: flex;
  gap: 8px;
}

.view-btn,
.edit-btn,
.delete-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.3s;
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
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: #ffffff;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  color: #333;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.close-btn:hover {
  background-color: #f5f5f5;
}

.modal-body {
  padding: 20px;
}

.detail-item {
  display: flex;
  margin-bottom: 15px;
  align-items: flex-start;
}

.detail-item label {
  width: 120px;
  font-weight: bold;
  color: #333;
  flex-shrink: 0;
}

.detail-item span {
  flex: 1;
  color: #666;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: flex-end;
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
}
</style>