<template>
  <div class="decision-support-container">
    <div class="page-header">
      <h1 class="page-title">决策支持</h1>
      <div class="header-controls" v-if="isAdmin">
        <button class="btn btn-gray" @click="$router.push('/dashboard/index')">
          <i class="fas fa-arrow-left"></i> 返回
        </button>
        <button class="history-btn" @click="$router.push('/task-history')">
          <i class="fas fa-history"></i> 历史执行记录
        </button>
      </div>
    </div>
    
    <div class="filter-bar">
      <div class="filter-row">
        <div class="filter-item">
          <label class="filter-label">时间范围</label>
          <div class="date-range-picker">
            <input type="month" v-model="filters.startDate" class="date-input">
            <span class="date-separator">至</span>
            <input type="month" v-model="filters.endDate" class="date-input">
          </div>
        </div>
        
        <div class="filter-item" v-if="isAdmin">
          <label class="filter-label">区域</label>
          <select v-model="filters.region" class="filter-select" @change="handleRegionChange">
            <option value="">全部区域</option>
            <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
          </select>
        </div>
        
        <div class="filter-item" v-if="isAdmin">
          <label class="filter-label">省份</label>
          <select v-model="filters.province" class="filter-select" @change="handleProvinceChange">
            <option value="">全部省份</option>
            <option v-for="province in filteredProvinces" :key="province" :value="province">{{ province }}</option>
          </select>
        </div>
        
        <div class="filter-item">
          <label class="filter-label">经销商</label>
          <div class="dealer-input-group">
            <select v-model="filters.dealerCode" class="filter-select dealer-select">
              <option value="">全部经销商</option>
              <option v-for="dealer in filteredDealers" :key="dealer['经销商代码']" :value="dealer['经销商代码']">
                {{ dealer['经销商代码'] }} - {{ dealer['省份'] }}
              </option>
            </select>
            <input
              v-model="inputDealerCode"
              placeholder="手动输入代码"
              class="input-dealer-code"
              @input="handleDealerCodeInput"
              @keyup.enter="applyManualDealer"
            >
            <div class="province-display" :class="{ 'has-province': matchedProvince }">
              <span class="province-label">省份：</span>
              <span class="province-value">{{ matchedProvince || '自动匹配' }}</span>
            </div>
          </div>
        </div>
        
        <div class="filter-item filter-buttons">
          <button class="btn-apply" @click="applyFilters">应用筛选</button>
          <button class="btn-reset" @click="resetFilters">重置</button>
        </div>
      </div>
      
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    </div>
    
    <div class="content-area">
      <div class="metrics-row">
        <div class="metric-card">
          <div class="metric-icon sales-icon">�</div>
          <div class="metric-content">
            <div class="metric-value">{{ formatNumber(metrics.totalSales) }}</div>
            <div class="metric-label">总销量</div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon orders-icon">�</div>
          <div class="metric-content">
            <div class="metric-value">{{ formatNumber(metrics.totalTraffic) }}</div>
            <div class="metric-label">总客流量</div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon profit-icon">🎯</div>
          <div class="metric-content">
            <div class="metric-value">{{ formatNumber(metrics.totalPotential) }}</div>
            <div class="metric-label">总潜客量</div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon leads-icon">📋</div>
          <div class="metric-content">
            <div class="metric-value">{{ formatNumber(metrics.totalLeads) }}</div>
            <div class="metric-label">总线索量</div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon rate-icon">📈</div>
          <div class="metric-content">
            <div class="metric-value">{{ metrics.avgSuccessRate }}%</div>
            <div class="metric-label">总成交率</div>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon policy-icon">📜</div>
          <div class="metric-content">
            <div class="metric-value">{{ metrics.totalPolicies }}</div>
            <div class="metric-label">总政策数量</div>
          </div>
        </div>
      </div>
      <div class="charts-row">
        <div class="chart-container trend-chart">
          <div class="chart-header">
            <h3>经营数据趋势</h3>
          </div>
          <div class="chart-body" ref="trendChart"></div>
        </div>
        
        <div class="chart-container policy-chart">
          <div class="chart-header">
            <h3>政策关联网络图</h3>
            <button class="btn-refresh" @click="resetNetworkGraph">
              <i class="fas fa-redo"></i> 重置
            </button>
          </div>
          <div class="network-stats-bar">
            <div class="network-stat-item">
              <span class="stat-label">节点数：</span>
              <span class="stat-value">{{ networkStats.nodes }}</span>
            </div>
            <div class="network-stat-item">
              <span class="stat-label">关联数：</span>
              <span class="stat-value">{{ networkStats.links }}</span>
            </div>
          </div>
          <div class="chart-body network-body" ref="networkGraph"></div>
          <div class="network-legend">
            <div class="legend-item">
              <span class="legend-node province"></span>
              <span class="legend-text">省份节点</span>
            </div>
            <div class="legend-item">
              <span class="legend-node category"></span>
              <span class="legend-text">政策分类</span>
            </div>
          </div>
        </div>
      </div>

      <div class="roi-row">
        <div class="chart-container roi-chart">
          <div class="chart-header">
            <h3>政策投入 - 销量产出四象限门店分类图</h3>
          </div>
          <div class="chart-body" ref="roiChart"></div>
        </div>
      </div>
      
      <!-- 漏斗断点智能诊断 -->
      <div class="diagnosis-row" v-if="isAdmin && diagnosisAlerts.length > 0">
        <div class="diagnosis-container">
          <div class="diagnosis-header">
            <h3>漏斗断点智能诊断</h3>
            <div class="diagnosis-badge">实时监测</div>
          </div>
          <div class="diagnosis-content">
            <div class="diagnosis-card" v-for="(alert, index) in diagnosisAlerts" :key="index" :class="alert.level">
              <div class="alert-icon">{{ alert.icon }}</div>
              <div class="alert-body">
                <div class="alert-title">{{ alert.title }}</div>
                <div class="alert-desc">{{ alert.description }}</div>
                <div class="alert-stats">
                  <span class="stat-tag">当前: {{ alert.value }}</span>
                  <span class="stat-tag avg">均值: {{ alert.avg }}</span>
                </div>
              </div>
              <div class="diagnosis-actions">
                <button class="btn-diagnosis-action" :class="{ 'dispatched': alert.isDispatched }" @click="implementAdvice(alert, [alert.dealerCode])" :disabled="alert.isDispatched">
                  {{ alert.isDispatched ? '已下发' : (alert.actionTitle ? '下发专项整改' : '一键下发任务') }}
                </button>
                <button v-if="alert.level === 'error' || alert.stage === '试驾成交率'" class="btn-benchmark-action" @click="showPeerBenchmark(alert.dealerCode)">
                  <i class="fas fa-bullseye"></i> 查找对标店
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="advice-row">
        <div class="advice-container strategy-advice" v-if="isAdmin">
          <div class="advice-header">
            <h3>策略级决策建议</h3>
            <button class="btn-refresh" @click="generateStrategyAdvices">
              <i class="fas fa-sync-alt"></i> 刷新
            </button>
          </div>
          <div class="advice-content">
            <div class="advice-card" v-for="(advice, index) in strategyAdvices" :key="index">
              <div class="advice-icon">{{ advice.icon }}</div>
              <div class="advice-body">
                <div class="advice-title">{{ advice.title }}</div>
                <div class="advice-description">{{ advice.description }}</div>
                <div class="advice-actions">
                  <button class="btn-action" @click="viewAdviceDetail(advice)">查看详情</button>
                  <button class="btn-action secondary" :class="{ 'dispatched': advice.isDispatched }" @click="implementAdvice(advice)" :disabled="advice.isDispatched">{{ advice.isDispatched ? '已下发' : '立即执行' }}</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="advice-container execution-advice">
          <div class="advice-header">
            <h3>{{ isAdmin ? '执行级决策建议' : '决策建议' }}</h3>
            <button class="btn-refresh" @click="generateExecutionAdvices">
              <i class="fas fa-sync-alt"></i> 刷新
            </button>
          </div>
          <div class="advice-content">
            <div class="advice-card" v-for="(advice, index) in executionAdvices" :key="index">
              <div class="advice-icon">{{ advice.icon }}</div>
              <div class="advice-body">
                <div class="advice-title">{{ advice.title }}</div>
                <div class="advice-description">{{ advice.description }}</div>
                <div class="advice-actions">
                  <button class="btn-action" @click="viewAdviceDetail(advice)">查看详情</button>
                  <button class="btn-action secondary" :class="{ 'dispatched': advice.isDispatched }" @click="implementAdvice(advice)" :disabled="advice.isDispatched">{{ advice.isDispatched ? '已下发' : '立即执行' }}</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="table-row">
        <div class="table-container">
          <div class="table-header">
            <h3>{{ isAdmin ? '区域经销商汇总数据' : '门店经营数据' }}</h3>
            <div class="table-actions">
              <span class="data-info" v-if="dealerData.length > 0">
                共 {{ dealerData.length }} 条经销商数据
                <span v-if="filters.region || filters.province || filters.dealerCode">
                  | 筛选后: {{ getFilteredDealerData().length }} 条
                </span>
              </span>
              <button class="btn-export" @click="exportTableData">
                <i class="fas fa-download"></i> 导出Excel
              </button>
            </div>
          </div>
          <div class="table-body">
            <div v-if="tableData.length === 0 && !loading" class="empty-state">
              <div class="empty-icon">📭</div>
              <div class="empty-text">暂无数据</div>
              <div class="empty-hint" v-if="dealerData.length === 0">经销商数据未加载，请检查后端API</div>
              <div class="empty-hint" v-else-if="getFilteredDealerData().length === 0">当前筛选条件下没有数据，请调整筛选条件</div>
            </div>
            <table v-else class="data-table">
              <thead>
                <tr>
                  <th v-for="column in tableColumns" :key="column.key" @click="sortBy(column.key)">
                    {{ column.label }}
                    <i v-if="sortKey === column.key" :class="['fas', sortOrder === 'asc' ? 'fa-sort-up' : 'fa-sort-down']"></i>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in tableData" :key="index">
                  <td v-for="column in tableColumns" :key="column.key">
                    {{ formatTableCell(row[column.key], column.key) }}
                  </td>
                </tr>
              </tbody>
            </table>
            
            <div class="pagination" v-if="totalPages > 1">
              <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">
                <i class="fas fa-chevron-left"></i>
              </button>
              <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
              <button class="page-btn" :disabled="currentPage === totalPages" @click="currentPage++">
                <i class="fas fa-chevron-right"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">数据加载中...</div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import * as echarts from 'echarts'

const metricKeys = {
  '销量': (m) => `${m}销量`,
  '客流量': (m) => `${m}客流量`,
  '线索量': (m) => `${m}线索量`,
  '潜客量': (m) => `${m}潜客量`
}

export default {
  name: 'DecisionSupport',
  data() {
    return {
      isAdmin: false,
      loading: false,
      errorMessage: '',
      roiChart: null,
      diagnosisAlerts: [],
      filters: {
        startDate: this.getDefaultStartDate(),
        endDate: this.getCurrentMonth(),
        region: '',
        province: '',
        dealerCode: ''
      },
      
      inputDealerCode: '',
      matchedProvince: '',
      
      regions: ['华东', '华南', '华北', '华中', '西南', '西北', '东北'],
      allProvinces: [],
      dealerList: [],
      dealerData: [],
      
      metrics: {
        totalSales: 0,
        totalTraffic: 0,
        totalPotential: 0,
        totalLeads: 0,
        avgSuccessRate: 0,
        totalPolicies: 0
      },
      
      standards: {
        monthlySales: 0,
        monthlyTraffic: 0,
        monthlyLeads: 0,
        monthlyPotential: 0,
        successRate: 15,
        policyCount: 5
      },
      
      trendChart: null,
      networkChart: null,
      networkStats: {
        nodes: 0,
        links: 0
      },
      
      policyData: [],
      
      strategyAdvices: [],
      executionAdvices: [],
      
      tableColumns: [],
      tableData: [],
      currentPage: 1,
      pageSize: 20,
      totalRecords: 0,
      sortKey: '',
      sortOrder: 'asc'
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
    
    filteredMonths() {
      const start = this.filters.startDate
      const end = this.filters.endDate
      
      if (!start || !end) {
        return ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
      }
      
      const [startYear, startMonth] = start.split('-').map(Number)
      const [endYear, endMonth] = end.split('-').map(Number)
      
      const months = []
      let currentYear = startYear
      let currentMonth = startMonth
      
      while (currentYear < endYear || (currentYear === endYear && currentMonth <= endMonth)) {
        months.push(`${currentMonth}月`)
        currentMonth++
        if (currentMonth > 12) {
          currentMonth = 1
          currentYear++
        }
      }
      
      return months
    },
    
    totalPages() {
      return Math.ceil(this.totalRecords / this.pageSize)
    }
  },
  
  mounted() {
    this.checkUserRole()
    this.initializeData()
  },
  
  methods: {
    checkUserRole() {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      this.isAdmin = user.role === 'admin'
      
      if (this.isAdmin) {
        this.tableColumns = [
          { key: 'dealerCode', label: '经销商代码' },
          { key: 'province', label: '省份' },
          { key: 'totalSales', label: '总销量' },
          { key: 'totalTraffic', label: '总客流量' },
          { key: 'totalPotential', label: '总潜客量' },
          { key: 'totalLeads', label: '总线索量' }
        ]
      } else {
        this.tableColumns = [
          { key: 'dealerCode', label: '经销商代码' },
          { key: 'province', label: '省份' },
          { key: 'totalSales', label: '总销量' },
          { key: 'totalTraffic', label: '总客流量' },
          { key: 'totalPotential', label: '总潜客量' },
          { key: 'totalLeads', label: '总线索量' }
        ]
      }
    },
    
    getDefaultStartDate() {
      return '2024-01'
    },
    
    getCurrentMonth() {
      return '2024-10'
    },
    
    async initializeData() {
      this.loading = true
      
      try {
        await Promise.all([
          this.loadDealerList(),
          this.loadDealerData(),
          this.loadPolicyData(),
          this.loadFunnelDiagnosis(),
          this.loadROIAnalysis()
        ])
        
        this.initTrendChart()
        this.initNetworkGraph()
        this.generateStrategyAdvices()
        this.generateExecutionAdvices()
        this.loadTableData()
      } catch (error) {
        console.error('初始化数据失败:', error)
        this.errorMessage = '数据加载失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    
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
    
    async loadDealerData() {
      try {
        const response = await axios.get('/api/dashboard/metrics', {
          params: { year: 2024 }
        })
        if (response.data.success) {
          this.dealerData = response.data.data || []
          this.calculateMetrics()
        }
      } catch (error) {
        console.error('加载经销商数据失败:', error)
      }
    },
    
    calculateMetrics() {
      const dealers = this.getFilteredDealerData()
      const allDealers = this.dealerData
      
      let totalSales = 0
      let totalTraffic = 0
      let totalLeads = 0
      let totalPotential = 0
      
      dealers.forEach(dealer => {
        this.filteredMonths.forEach(m => {
          totalSales += this.toNumber(dealer[`${m}销量`])
          totalTraffic += this.toNumber(dealer[`${m}客流量`])
          totalLeads += this.toNumber(dealer[`${m}线索量`])
          totalPotential += this.toNumber(dealer[`${m}潜客量`])
        })
      })
      
      this.metrics.totalSales = totalSales
      this.metrics.totalTraffic = totalTraffic
      this.metrics.totalPotential = totalPotential
      this.metrics.totalLeads = totalLeads
      this.metrics.avgSuccessRate = totalLeads > 0 ? ((totalSales / totalLeads) * 100).toFixed(1) : 0
      this.metrics.totalPolicies = this.getFilteredPolicies().length
      
      let allTotalSales = 0
      let allTotalTraffic = 0
      let allTotalLeads = 0
      let allTotalPotential = 0
      
      allDealers.forEach(dealer => {
        this.filteredMonths.forEach(m => {
          allTotalSales += this.toNumber(dealer[`${m}销量`])
          allTotalTraffic += this.toNumber(dealer[`${m}客流量`])
          allTotalLeads += this.toNumber(dealer[`${m}线索量`])
          allTotalPotential += this.toNumber(dealer[`${m}潜客量`])
        })
      })
      
      const monthCount = this.filteredMonths.length || 1
      const dealerCount = allDealers.length || 1
      
      this.standards = {
        monthlySales: Math.round(allTotalSales / dealerCount / monthCount),
        monthlyTraffic: Math.round(allTotalTraffic / dealerCount / monthCount),
        monthlyLeads: Math.round(allTotalLeads / dealerCount / monthCount),
        monthlyPotential: Math.round(allTotalPotential / dealerCount / monthCount),
        successRate: allTotalLeads > 0 ? ((allTotalSales / allTotalLeads) * 100).toFixed(1) : 15,
        policyCount: Math.round(this.policyData.length / (this.allProvinces.length || 1))
      }
    },
    
    async loadPolicyData() {
      try {
        const response = await axios.get('/api/policies')
        this.policyData = response.data || []
      } catch (error) {
        console.error('加载政策数据失败:', error)
        this.policyData = []
      }
    },
    
    getFilteredDealerData() {
      let dealers = []
      
      if (!this.dealerData || this.dealerData.length === 0) {
        console.warn('经销商数据未加载或为空')
        return []
      }
      
      if (this.filters.dealerCode) {
        dealers = this.dealerData.filter(d => d['经销商代码'] === this.filters.dealerCode)
        console.log(`按经销商代码筛选: ${this.filters.dealerCode}, 找到 ${dealers.length} 条记录`)
      } else if (this.filters.province) {
        dealers = this.dealerData.filter(d => {
          const dealerProvince = d['省份'] || ''
          return dealerProvince === this.filters.province || dealerProvince.includes(this.filters.province)
        })
        console.log(`按省份筛选: ${this.filters.province}, 找到 ${dealers.length} 条记录`)
      } else if (this.filters.region) {
        const provinces = this.filteredProvinces
        dealers = this.dealerData.filter(d => {
          const dealerProvince = d['省份'] || ''
          return provinces.some(p => dealerProvince === p || dealerProvince.includes(p))
        })
        console.log(`按区域筛选: ${this.filters.region}, 包含省份: ${provinces.join(', ')}, 找到 ${dealers.length} 条记录`)
      } else {
        dealers = this.dealerData
        console.log(`未筛选, 共 ${dealers.length} 条记录`)
      }
      
      return dealers
    },
    
    getCurrentDealerData() {
      const dealers = this.getFilteredDealerData()
      return dealers.length > 0 ? dealers[0] : {}
    },
    
    getSeriesByTimeRange(key) {
      const dealers = this.getFilteredDealerData()
      if (dealers.length === 0) {
        return this.filteredMonths.map(() => 0)
      }
      
      return this.filteredMonths.map((m) => {
        let total = 0
        let validCount = 0
        dealers.forEach(dealer => {
          const value = dealer[metricKeys[key](m)]
          if (value !== null && value !== undefined && value !== '') {
            const num = parseFloat(value)
            if (!isNaN(num)) {
              total += num
              validCount++
            }
          }
        })
        return validCount > 0 ? Math.round(total / validCount) : 0
      })
    },
    
    toNumber(value) {
      if (value === null || value === undefined || value === '') return 0
      const num = parseFloat(value)
      return isNaN(num) ? 0 : num
    },
    
    initTrendChart() {
      if (!this.$refs.trendChart) return
      
      if (this.trendChart) {
        this.trendChart.dispose()
      }
      
      this.trendChart = echarts.init(this.$refs.trendChart)
      this.updateTrendChart()
      
      window.addEventListener('resize', () => {
        this.trendChart && this.trendChart.resize()
      })
    },
    
    updateTrendChart() {
      if (!this.trendChart) return
      
      const sales = this.getSeriesByTimeRange('销量')
      const traffic = this.getSeriesByTimeRange('客流量')
      const leads = this.getSeriesByTimeRange('线索量')
      const potential = this.getSeriesByTimeRange('潜客量')
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: {
            color: '#1f2937',
            fontSize: 14
          },
          padding: [10, 15],
          formatter: function(params) {
            let result = params[0].name + '<br/>'
            const seriesColors = {
              '销量': '#3b82f6',
              '客流量': '#8b5cf6',
              '线索量': '#f59e0b',
              '潜客量': '#10b981'
            }
            const order = ['线索量', '潜客量', '客流量', '销量']
            order.forEach(function(seriesName) {
              const item = params.find(p => p.seriesName === seriesName)
              if (item) {
                const color = seriesColors[item.seriesName] || item.color
                result += '<span style="display:inline-block;margin-right:8px;border-radius:2px;width:12px;height:12px;background-color:' + color + '"></span>'
                result += item.seriesName + ': ' + item.value + '<br/>'
              }
            })
            return result
          }
        },
        legend: {
          data: ['线索量', '潜客量', '客流量', '销量'],
          right: 12,
          top: 10,
          orient: 'vertical',
          textStyle: { 
            color: '#6b7280',
            fontSize: 14
          },
          itemWidth: 12,
          itemHeight: 12
        },
        grid: { left: 50, right: 140, top: 40, bottom: 40 },
        xAxis: {
          type: 'category',
          data: this.filteredMonths,
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisLabel: { 
            color: '#6b7280',
            fontSize: 12
          }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { 
            lineStyle: { 
              color: 'rgba(0, 0, 0, 0.05)',
              type: 'dashed'
            } 
          },
          axisLabel: { 
            color: '#6b7280',
            fontSize: 12
          }
        },
        series: [
          {
            name: '销量',
            type: 'bar',
            data: sales,
            barWidth: 14,
            color: '#3b82f6',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#3b82f6' },
                { offset: 1, color: '#2563eb' }
              ])
            }
          },
          {
            name: '客流量',
            type: 'line',
            smooth: true,
            data: traffic,
            color: '#8b5cf6'
          },
          {
            name: '线索量',
            type: 'line',
            smooth: true,
            data: leads,
            color: '#f59e0b'
          },
          {
            name: '潜客量',
            type: 'line',
            smooth: true,
            data: potential,
            color: '#10b981'
          }
        ]
      }
      
      this.trendChart.setOption(option)
    },
    
    initNetworkGraph() {
      if (!this.$refs.networkGraph) {
        console.warn('networkGraph ref not found')
        return
      }
      
      if (this.networkChart) {
        this.networkChart.dispose()
      }
      
      this.networkChart = echarts.init(this.$refs.networkGraph)
      
      window.addEventListener('resize', () => {
        this.networkChart && this.networkChart.resize()
      })
      
      this.$nextTick(() => {
        this.updateNetworkGraph()
      })
    },
    
    buildNetworkData() {
      const nodes = []
      const links = []
      const nodeMap = new Map()
      
      const categoryColors = {
        province: '#3498db',
        category: '#e74c3c',
        keyword: '#2ecc71'
      }
      
      const normalizeProvince = (name) => {
        if (!name) return ''
        return name.replace(/省|市|自治区|特别行政区/g, '').trim()
      }
      
      const allPolicies = this.policyData || []
      let selectedProvince = this.filters.province
      
      if (this.filters.dealerCode && !selectedProvince) {
        const dealer = this.dealerList.find(d => d['经销商代码'] === this.filters.dealerCode)
        if (dealer && dealer['省份']) {
          selectedProvince = dealer['省份']
        }
      }
      
      const normalizedSelected = selectedProvince ? normalizeProvince(selectedProvince) : null
      
      const provinceCounts = {}
      const categoryStats = {}
      
      allPolicies.forEach(policy => {
        const province = policy['省/直辖市/自治区']
        const category = policy['政策分类']
        
        if (province) {
          provinceCounts[province] = (provinceCounts[province] || 0) + 1
        }
        if (category) {
          categoryStats[category] = (categoryStats[category] || 0) + 1
        }
      })
      
      const relatedCategories = new Set()
      if (normalizedSelected) {
        allPolicies.forEach(policy => {
          const policyProvince = policy['省/直辖市/自治区']
          const normalizedPolicyProvince = normalizeProvince(policyProvince)
          if (normalizedPolicyProvince === normalizedSelected && policy['政策分类']) {
            relatedCategories.add(policy['政策分类'])
          }
        })
      }
      
      Object.entries(provinceCounts).forEach(([name, count]) => {
        if (count > 0) {
          const nodeId = `province_${name}`
          nodeMap.set(nodeId, nodes.length)
          const normalized = normalizeProvince(name)
          const isSelected = normalizedSelected && normalized === normalizedSelected
          const isRelated = !normalizedSelected || isSelected
          nodes.push({
            id: nodeId,
            name: name,
            nodeType: 'province',
            policyCount: count,
            category: 0,
            value: count,
            itemStyle: {
              color: categoryColors.province,
              opacity: isRelated ? 1 : 0.2
            },
            label: {
              show: true,
              opacity: isRelated ? 1 : 0.3
            }
          })
        }
      })
      
      Object.entries(categoryStats).forEach(([name, count]) => {
        const nodeId = `category_${name}`
        nodeMap.set(nodeId, nodes.length)
        const isRelated = !normalizedSelected || relatedCategories.has(name)
        nodes.push({
          id: nodeId,
          name: name,
          nodeType: 'category',
          policyCount: count,
          category: 1,
          value: count,
          itemStyle: {
            color: categoryColors.category,
            opacity: isRelated ? 1 : 0.2
          },
          label: {
            show: true,
            opacity: isRelated ? 1 : 0.3
          }
        })
      })
      
      allPolicies.forEach(policy => {
        const province = policy['省/直辖市/自治区']
        const category = policy['政策分类']
        
        if (province && category) {
          const provinceId = `province_${province}`
          const categoryId = `category_${category}`
          
          if (nodeMap.has(provinceId) && nodeMap.has(categoryId)) {
            const linkId = `${provinceId}-${categoryId}`
            if (!links.find(l => l.id === linkId)) {
              const normalizedProvince = normalizeProvince(province)
              const isRelated = !normalizedSelected || normalizedProvince === normalizedSelected
              links.push({
                id: linkId,
                source: provinceId,
                target: categoryId,
                value: 1,
                lineStyle: {
                  opacity: isRelated ? 0.6 : 0.1
                }
              })
            }
          }
        }
      })
      
      let relatedNodeCount = 0
      let relatedLinkCount = 0
      
      if (normalizedSelected) {
        nodes.forEach(node => {
          if (node.itemStyle.opacity === 1) {
            relatedNodeCount++
          }
        })
        links.forEach(link => {
          if (link.lineStyle.opacity > 0.1) {
            relatedLinkCount++
          }
        })
        this.networkStats = {
          nodes: relatedNodeCount,
          links: relatedLinkCount
        }
      } else {
        this.networkStats = {
          nodes: nodes.length,
          links: links.length
        }
      }
      
      return { nodes, links }
    },
    
    extractKeywords(text) {
      const keywords = []
      const patterns = [
        /以旧换新/g,
        /购车补贴/g,
        /置换补贴/g,
        /消费券/g,
        /报废补贴/g,
        /下乡补贴/g,
        /新能源/g,
        /电动汽车/g,
        /燃油车/g,
        /二手车/g,
        /补贴金额/g,
        /最高补贴/g,
        /优惠政策/g,
        /促销活动/g,
        /节能/g,
        /环保/g
      ]
      
      patterns.forEach(pattern => {
        const matches = text.match(pattern)
        if (matches) {
          matches.forEach(match => {
            if (!keywords.includes(match)) {
              keywords.push(match)
            }
          })
        }
      })
      
      return keywords
    },
    
    getFilteredPolicies() {
      let policies = this.policyData || []
      
      let filterProvince = this.filters.province
      
      if (this.filters.dealerCode && !filterProvince) {
        const dealer = this.dealerList.find(d => d['经销商代码'] === this.filters.dealerCode)
        if (dealer && dealer['省份']) {
          filterProvince = dealer['省份']
        }
      }
      
      if (filterProvince) {
        const cleanProvince = filterProvince.replace(/省|市|自治区/g, '')
        policies = policies.filter(policy => {
          const policyProvince = (policy['省/直辖市/自治区'] || '').replace(/省|市|自治区/g, '')
          return policyProvince === cleanProvince || policyProvince.includes(cleanProvince) || cleanProvince.includes(policyProvince)
        })
      } else if (this.filters.region) {
        policies = policies.filter(policy => {
          const province = policy['省/直辖市/自治区']
          return this.filteredProvinces.includes(province)
        })
      }
      
      return policies
    },
    
    updateNetworkGraph() {
      if (!this.networkChart) return
      
      const graphData = this.buildNetworkData()
      
      if (!graphData.nodes || graphData.nodes.length === 0) {
        this.networkChart.setOption({
          title: {
            text: '暂无政策数据',
            left: 'center',
            top: 'center',
            textStyle: {
              color: '#999',
              fontSize: 14
            }
          }
        })
        return
      }
      
      const categories = [
        { name: 'province', itemStyle: { color: '#3498db' } },
        { name: 'category', itemStyle: { color: '#e74c3c' } }
      ]
      
      const option = {
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e8e8e8',
          borderWidth: 1,
          padding: [8, 12],
          textStyle: {
            color: '#333',
            fontSize: 12
          },
          formatter: (params) => {
            if (params.dataType === 'node') {
              const typeNames = {
                province: '省份',
                category: '政策分类'
              }
              const typeName = typeNames[params.data.nodeType] || params.data.nodeType
              return `<div style="font-weight: 600; margin-bottom: 4px;">${params.name}</div>
                      <div style="color: #666; font-size: 11px;">类型: ${typeName}</div>
                      <div style="color: #666; font-size: 11px;">关联政策: ${params.data.policyCount || 0}项</div>`
            }
            return null
          }
        },
        series: [{
          type: 'graph',
          layout: 'circular',
          symbolSize: 30,
          roam: true,
          draggable: true,
          label: {
            show: true,
            position: 'right',
            fontSize: 11,
            color: '#333',
            formatter: '{b}',
            distance: 5
          },
          edgeSymbol: ['none', 'arrow'],
          edgeSymbolSize: [2, 6],
          data: graphData.nodes,
          links: graphData.links,
          lineStyle: {
            color: '#d9d9d9',
            curveness: 0.1,
            width: 1
          },
          emphasis: {
            focus: 'adjacency',
            itemStyle: {
              shadowBlur: 8,
              shadowColor: 'rgba(0, 0, 0, 0.2)'
            },
            lineStyle: {
              width: 2,
              color: '#3498db'
            }
          },
          categories: categories,
          circular: {
            rotateLabel: true
          }
        }]
      }
      
      this.networkChart.setOption(option)
    },
    
    resetNetworkGraph() {
      this.updateNetworkGraph()
    },
    
    generateStrategyAdvices() {
      const advices = []
      const policies = this.getFilteredPolicies()
      const policyCount = policies.length
      
      const dealers = this.getFilteredDealerData()
      const dealerCount = dealers.length
      
      const avgSales = dealerCount > 0 ? this.metrics.totalSales / dealerCount : 0
      const avgTraffic = dealerCount > 0 ? this.metrics.totalTraffic / dealerCount : 0
      const avgLeads = dealerCount > 0 ? this.metrics.totalLeads / dealerCount : 0
      const avgPotential = dealerCount > 0 ? this.metrics.totalPotential / dealerCount : 0
      const successRate = parseFloat(this.metrics.avgSuccessRate) || 0
      
      const monthCount = this.filteredMonths.length || 1
      const monthlyAvgSales = avgSales / monthCount
      const monthlyAvgTraffic = avgTraffic / monthCount
      const monthlyAvgLeads = avgLeads / monthCount
      const monthlyAvgPotential = avgPotential / monthCount
      
      const standards = this.standards
      
      const categoryStats = {}
      policies.forEach(policy => {
        const category = policy['政策分类']
        if (category) {
          categoryStats[category] = (categoryStats[category] || 0) + 1
        }
      })
      
      if (monthlyAvgSales < standards.monthlySales) {
        const gap = standards.monthlySales - monthlyAvgSales
        advices.push({
          icon: '📉',
          title: '销量提升策略',
          description: `当前月均销量${monthlyAvgSales.toFixed(0)}辆，低于标准值${standards.monthlySales}辆，差距${gap.toFixed(0)}辆。建议：1. 分析销量下滑原因，针对性制定改进方案；2. 加强销售团队培训，提升成交技巧；3. 优化库存结构，确保热销车型充足；${policyCount > 0 ? `4. 结合当前${policyCount}项政策，制定促销方案吸引客户。` : '4. 增加促销活动频次，提升客户购买意愿。'}`
        })
      } else if (monthlyAvgSales > standards.monthlySales * 1.2) {
        advices.push({
          icon: '📈',
          title: '销量保持策略',
          description: `当前月均销量${monthlyAvgSales.toFixed(0)}辆，表现优秀。建议：1. 总结成功经验，形成可复制模式；2. 关注客户满意度，确保服务质量；3. 持续关注市场动态，及时调整策略。`
        })
      }
      
      if (monthlyAvgTraffic < standards.monthlyTraffic) {
        const gap = standards.monthlyTraffic - monthlyAvgTraffic
        advices.push({
          icon: '👥',
          title: '客流增长策略',
          description: `当前月均客流量${monthlyAvgTraffic.toFixed(0)}人，低于标准值${standards.monthlyTraffic}人，差距${gap.toFixed(0)}人。建议：1. 加大线上营销投放，扩大品牌曝光；2. 优化展厅环境，提升客户体验；3. 举办试驾活动，吸引潜在客户；${policyCount > 0 ? `4. 利用政策宣传作为引流手段，在社交媒体推广优惠政策。` : '4. 与本地媒体合作，提升品牌知名度。'}`
        })
      } else if (monthlyAvgTraffic > standards.monthlyTraffic * 1.2) {
        advices.push({
          icon: '🎯',
          title: '客流转化策略',
          description: `当前月均客流量${monthlyAvgTraffic.toFixed(0)}人，表现优秀。建议重点提升转化率：1. 优化接待流程，提升客户体验；2. 加强销售培训，提高成交能力；3. 建立客户跟进机制，防止客户流失。`
        })
      }
      
      if (monthlyAvgLeads < standards.monthlyLeads) {
        const gap = standards.monthlyLeads - monthlyAvgLeads
        advices.push({
          icon: '📋',
          title: '线索获取策略',
          description: `当前月均线索量${monthlyAvgLeads.toFixed(0)}条，低于标准值${standards.monthlyLeads}条，差距${gap.toFixed(0)}条。建议：1. 拓展线索获取渠道，如汽车网站、社交媒体等；2. 优化官网用户体验，降低咨询门槛；3. 提升客服响应速度，及时跟进线索；${policyCount > 0 ? `4. 制作政策解读内容，吸引客户主动咨询。` : '4. 加强线上广告投放，提升品牌曝光。'}`
        })
      }
      
      if (monthlyAvgPotential < standards.monthlyPotential) {
        const gap = standards.monthlyPotential - monthlyAvgPotential
        advices.push({
          icon: '🎯',
          title: '潜客转化策略',
          description: `当前月均潜客量${monthlyAvgPotential.toFixed(0)}人，低于标准值${standards.monthlyPotential}人，差距${gap.toFixed(0)}人。建议：1. 加强客户跟进频次，保持联系热度；2. 优化销售话术，增强说服力；3. 提供个性化购车方案，满足客户需求；${policyCount > 0 ? `4. 向潜客推送政策优惠信息，刺激购买决策。` : '4. 建立客户关怀体系，提升客户粘性。'}`
        })
      }
      
      if (successRate < standards.successRate) {
        advices.push({
          icon: '📊',
          title: '成交率提升策略',
          description: `当前成交率${successRate}%，低于标准值${standards.successRate}%。建议：1. 分析流失客户原因，针对性改进；2. 加强销售团队培训，提升成交技巧；3. 优化报价策略，提高竞争力；4. 建立客户异议处理机制。`
        })
      }
      
      if (policyCount > 0) {
        const topCategories = Object.entries(categoryStats)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3)
          .map(([name]) => name)
          .join('、')
        
        if (policyCount < standards.policyCount) {
          advices.push({
            icon: '📜',
            title: '政策资源拓展',
            description: `当前区域仅有${policyCount}项政策，低于标准值${standards.policyCount}项。建议：1. 关注政府部门政策发布渠道，及时获取信息；2. 主动与相关部门沟通，了解政策动向；3. 参与行业协会活动，拓展政策信息来源。`
          })
        } else {
          advices.push({
            icon: '📜',
            title: '政策利用策略',
            description: `当前区域共有${policyCount}项政策，主要涉及${topCategories}等领域。建议：1. 深入研究政策内容，提取关键优惠信息；2. 制定针对性营销方案，突出政策优势；3. 培训销售团队熟练掌握政策要点；4. 与政府部门保持沟通，及时获取最新政策动态。`
          })
        }
        
        const hasSubsidy = policies.some(p => 
          (p['政策主要内容'] || '').includes('补贴') || 
          (p['政策主要内容'] || '').includes('优惠')
        )
        if (hasSubsidy) {
          advices.push({
            icon: '💰',
            title: '补贴政策应用',
            description: `当前区域存在补贴类政策。建议：1. 制作补贴计算器工具，帮助客户直观了解优惠金额；2. 在展厅显著位置展示补贴政策海报；3. 培训销售人员熟练讲解补贴申请流程；4. 协助客户准备申请材料，提升服务体验。`
          })
        }
      } else {
        advices.push({
          icon: '⚠️',
          title: '政策资源缺失',
          description: `当前区域暂无政策数据。建议：1. 关注政府部门政策发布渠道；2. 主动与相关部门沟通了解政策动向；3. 参考周边区域政策，制定本地化营销策略。`
        })
      }
      
      if (advices.length === 0) {
        advices.push({
          icon: '✅',
          title: '经营状况良好',
          description: '当前各项经营指标表现良好，建议继续保持现有经营策略，同时关注市场变化，及时调整策略。'
        })
      }
      
      this.strategyAdvices = advices
      this.checkAdvicesDispatchStatus()
    },
    
    generateExecutionAdvices() {
      const advices = []
      const policies = this.getFilteredPolicies()
      const policyCount = policies.length
      
      const dealers = this.getFilteredDealerData()
      const dealerCount = dealers.length
      
      const sales = this.getSeriesByTimeRange('销量')
      const traffic = this.getSeriesByTimeRange('客流量')
      const leads = this.getSeriesByTimeRange('线索量')
      const potential = this.getSeriesByTimeRange('潜客量')
      
      const latestSales = sales[sales.length - 1] || 0
      const latestTraffic = traffic[traffic.length - 1] || 0
      const latestLeads = leads[leads.length - 1] || 0
      const latestPotential = potential[potential.length - 1] || 0
      
      const prevSales = sales.length > 1 ? sales[sales.length - 2] : latestSales
      const salesTrend = prevSales > 0 ? ((latestSales - prevSales) / prevSales * 100).toFixed(1) : 0
      
      const standards = this.standards
      
      if (latestSales < standards.monthlySales) {
        const gap = standards.monthlySales - latestSales
        advices.push({
          icon: '🚗',
          title: '门店销售提升',
          description: `本月销量${latestSales}辆，低于标准值${standards.monthlySales}辆，差距${gap}辆。建议：1. 加强销售团队培训，提升成交技巧；2. 优化展厅车辆陈列，突出热门车型；3. 增加试驾活动频次，提升客户体验；${policyCount > 0 ? `4. 利用现有${policyCount}项政策，向客户强调购车优惠。` : '4. 制定个性化促销方案。'}`
        })
      } else if (latestSales > standards.monthlySales * 1.2) {
        advices.push({
          icon: '🏆',
          title: '销售业绩优秀',
          description: `本月销量${latestSales}辆，表现优秀。建议：1. 总结成功经验，分享给团队；2. 关注客户满意度，确保服务质量；3. 维护老客户关系，促进转介绍。`
        })
      }
      
      if (latestTraffic < standards.monthlyTraffic) {
        const gap = standards.monthlyTraffic - latestTraffic
        advices.push({
          icon: '🏪',
          title: '门店客流提升',
          description: `本月客流量${latestTraffic}人，低于标准值${standards.monthlyTraffic}人，差距${gap}人。建议：1. 优化门店位置标识，提升可见度；2. 改善展厅环境，营造舒适氛围；3. 增加休息区舒适度，提供免费饮品；${policyCount > 0 ? `4. 在店门口设置政策宣传展板，吸引路人关注。` : '4. 举办主题活动吸引客户。'}`
        })
      }
      
      if (latestLeads < standards.monthlyLeads) {
        const gap = standards.monthlyLeads - latestLeads
        advices.push({
          icon: '📱',
          title: '线索跟进优化',
          description: `本月线索量${latestLeads}条，低于标准值${standards.monthlyLeads}条，差距${gap}条。建议：1. 加强线上渠道投放，扩大曝光；2. 优化官网表单设计，降低填写门槛；3. 提升客服响应速度，及时跟进；${policyCount > 0 ? `4. 在广告素材中突出政策优惠，提升点击率和咨询量。` : '4. 建立线索分级跟进机制。'}`
        })
      }
      
      if (latestPotential < standards.monthlyPotential) {
        const gap = standards.monthlyPotential - latestPotential
        advices.push({
          icon: '💬',
          title: '客户沟通加强',
          description: `本月潜客量${latestPotential}人，低于标准值${standards.monthlyPotential}人，差距${gap}人。建议：1. 增加客户回访频次，保持联系；2. 优化客户沟通话术，增强亲和力；3. 提供个性化购车方案，满足需求；${policyCount > 0 ? `4. 向潜客发送政策优惠信息，刺激购买决策。` : '4. 建立客户关怀体系。'}`
        })
      }
      
      if (parseFloat(salesTrend) < -10) {
        advices.push({
          icon: '⚠️',
          title: '销量下滑预警',
          description: `本月销量环比下降${Math.abs(salesTrend)}%，需要重点关注。建议：1. 分析销量下滑原因，针对性改进；2. 加强销售团队激励，提升积极性；3. 推出限时优惠活动，刺激购买；${policyCount > 0 ? `4. 加大政策宣传力度，吸引潜在客户。` : '4. 优化客户跟进流程，防止客户流失。'}`
        })
      } else if (parseFloat(salesTrend) > 10) {
        advices.push({
          icon: '📈',
          title: '销量增长势头',
          description: `本月销量环比增长${salesTrend}%，势头良好。建议：1. 保持现有营销策略，巩固成果；2. 分析增长原因，复制成功经验；3. 关注库存情况，确保供应充足。`
        })
      }
      
      if (policyCount > 0) {
        const policyTitles = policies.slice(0, 2).map(p => p['政策名称'] || '政策').join('、')
        
        advices.push({
          icon: '📢',
          title: '政策宣传执行',
          description: `当前有${policyCount}项政策可利用，如"${policyTitles}"等。建议：1. 组织销售团队学习政策内容，确保准确传达；2. 制作政策宣传海报和折页，放置展厅显眼位置；3. 在客户洽谈时主动介绍适用政策；4. 协助客户准备申请材料，提升服务质量。`
        })
        
        const keywords = this.extractPolicyKeywords(policies)
        if (keywords.length > 0) {
          advices.push({
            icon: '🔑',
            title: '政策关键词营销',
            description: `当前政策涉及关键词：${keywords.slice(0, 5).join('、')}。建议：1. 在营销文案中融入这些关键词，提升搜索曝光；2. 针对不同关键词制定差异化话术；3. 制作关键词对应的FAQ，快速解答客户疑问；4. 在社交媒体发布相关内容，扩大传播。`
          })
        }
      } else {
        advices.push({
          icon: '📋',
          title: '政策信息收集',
          description: `当前区域暂无政策数据。建议：1. 主动收集本地政策信息；2. 关注政府部门官方网站和公众号；3. 与同行交流，了解政策动态。`
        })
      }
      
      if (advices.length === 0) {
        advices.push({
          icon: '✅',
          title: '执行情况良好',
          description: '当前各项执行指标表现良好，建议继续保持现有执行力度，同时关注细节优化，提升客户体验。'
        })
      }
      
      this.executionAdvices = advices
      this.checkAdvicesDispatchStatus('execution')
    },
    
    extractPolicyKeywords(policies) {
      const keywordSet = new Set()
      policies.forEach(policy => {
        const content = policy['政策主要内容'] || ''
        const keywords = this.extractKeywords(content)
        keywords.forEach(k => keywordSet.add(k))
      })
      return Array.from(keywordSet)
    },
    
    async loadTableData() {
      try {
        const response = await axios.get('/api/decision/table-data', {
          params: {
            ...this.filters,
            page: this.currentPage,
            pageSize: this.pageSize,
            sortKey: this.sortKey,
            sortOrder: this.sortOrder
          }
        })
        
        if (response.data && response.data.success) {
          const data = response.data.data || {}
          this.tableData = data.rows || []
          this.totalRecords = data.total || 0
          console.log('从后端加载表格数据成功:', this.tableData.length, '条记录')
        } else {
          throw new Error('后端返回数据格式错误')
        }
      } catch (error) {
        console.warn('从后端加载表格数据失败，使用本地数据:', error.message)
        
        const dealers = this.getFilteredDealerData()
        
        const tableRows = dealers.map(dealer => {
          let totalSales = 0
          let totalTraffic = 0
          let totalLeads = 0
          let totalPotential = 0
          
          this.filteredMonths.forEach(m => {
            totalSales += this.toNumber(dealer[`${m}销量`])
            totalTraffic += this.toNumber(dealer[`${m}客流量`])
            totalLeads += this.toNumber(dealer[`${m}线索量`])
            totalPotential += this.toNumber(dealer[`${m}潜客量`])
          })
          
          return {
            dealerCode: dealer['经销商代码'] || '',
            province: dealer['省份'] || '',
            totalSales: totalSales,
            totalTraffic: totalTraffic,
            totalPotential: totalPotential,
            totalLeads: totalLeads
          }
        }).filter(row => row.dealerCode && row.dealerCode.trim() !== '')
        
        if (this.sortKey) {
          tableRows.sort((a, b) => {
            const aVal = a[this.sortKey] || 0
            const bVal = b[this.sortKey] || 0
            if (this.sortOrder === 'asc') {
              return aVal > bVal ? 1 : -1
            } else {
              return aVal < bVal ? 1 : -1
            }
          })
        }
        
        this.totalRecords = tableRows.length
        const startIndex = (this.currentPage - 1) * this.pageSize
        const endIndex = startIndex + this.pageSize
        this.tableData = tableRows.slice(startIndex, endIndex)
        
        console.log('使用本地数据:', this.tableData.length, '/', this.totalRecords, '条记录')
      }
    },
    
    handleRegionChange() {
      this.filters.province = ''
      this.filters.dealerCode = ''
      this.inputDealerCode = ''
      this.matchedProvince = ''
      console.log('区域改变:', this.filters.region, '可用省份:', this.filteredProvinces)
      this.calculateMetrics()
      this.updateTrendChart()
      this.updateNetworkGraph()
      this.loadTableData()
      this.generateStrategyAdvices()
      this.generateExecutionAdvices()
    },
    
    handleProvinceChange() {
      this.filters.dealerCode = ''
      this.inputDealerCode = ''
      this.matchedProvince = ''
      console.log('省份改变:', this.filters.province)
      this.calculateMetrics()
      this.updateTrendChart()
      this.updateNetworkGraph()
      this.loadTableData()
      this.generateStrategyAdvices()
      this.generateExecutionAdvices()
    },
    
    handleDealerCodeInput() {
      const code = (this.inputDealerCode || '').trim()
      this.updateMatchedProvince(code)
    },
    
    updateMatchedProvince(code) {
      if (!code) {
        this.matchedProvince = ''
        return
      }
      const dealer = this.dealerList.find((d) => String(d['经销商代码']) === code)
      if (dealer) {
        this.matchedProvince = dealer['省份'] || ''
      } else {
        this.matchedProvince = ''
      }
    },
    
    applyManualDealer() {
      const code = (this.inputDealerCode || '').trim()
      
      if (!code) {
        this.errorMessage = '请输入经销商代码'
        return
      }
      
      const target = this.dealerList.find((d) => String(d['经销商代码']) === code)
      
      if (!target) {
        this.errorMessage = '未找到对应经销商，请检查代码后重试'
        return
      }
      
      this.filters.dealerCode = target['经销商代码']
      this.matchedProvince = target['省份'] || ''
      this.errorMessage = ''
    },
    
    applyFilters() {
      if (this.inputDealerCode) {
        this.applyManualDealer()
      }
      
      this.currentPage = 1
      this.initializeData()
    },
    
    resetFilters() {
      this.filters = {
        startDate: this.getDefaultStartDate(),
        endDate: this.getCurrentMonth(),
        region: '',
        province: '',
        dealerCode: ''
      }
      
      this.inputDealerCode = ''
      this.matchedProvince = ''
      this.errorMessage = ''
      
      this.applyFilters()
    },
    
    viewAdviceDetail(advice) {
      alert(`建议详情：\n\n${advice.title}\n\n${advice.description}`)
    },
    
    async checkAdvicesDispatchStatus(type = 'strategy') {
      const advices = type === 'strategy' ? this.strategyAdvices : this.executionAdvices
      if (!advices || advices.length === 0) return
      
      const dealers = this.getFilteredDealerData()
      const dealerCodes = dealers.map(d => d['经销商代码']).filter(code => code)
      if (dealerCodes.length === 0) return
      
      for (let advice of advices) {
        try {
          const response = await axios.post('/api/decision/check-task-exists', {
            title: advice.title,
            dealerCodes: dealerCodes,
            filters: this.filters
          })
          
          if (response.data.success && response.data.exists) {
            this.$set(advice, 'isDispatched', true)
          } else {
            this.$set(advice, 'isDispatched', false)
          }
        } catch (error) {
          this.$set(advice, 'isDispatched', false)
        }
      }
      
      if (type === 'strategy') {
        this.strategyAdvices = [...advices]
      } else {
        this.executionAdvices = [...advices]
      }
    },
    
    async checkDiagnosisDispatchStatus() {
      if (!this.diagnosisAlerts || this.diagnosisAlerts.length === 0) return
      
      for (let alert of this.diagnosisAlerts) {
        try {
          const response = await axios.post('/api/decision/check-task-exists', {
            title: alert.actionTitle || alert.title,
            dealerCodes: [alert.dealerCode],
            filters: this.filters
          })
          
          if (response.data.success && response.data.exists) {
            this.$set(alert, 'isDispatched', true)
          } else {
            this.$set(alert, 'isDispatched', false)
          }
        } catch (error) {
          this.$set(alert, 'isDispatched', false)
        }
      }
      
      this.diagnosisAlerts = [...this.diagnosisAlerts]
    },
    
    async implementAdvice(advice, specificDealerCodes = null) {
      if (!this.isAdmin) {
        alert('只有管理员可以执行决策建议')
        return
      }
      if (!advice) return
      
      // 处理告警对象和建议对象的标题/描述差异
      const normalizedAdvice = {
        title: advice.actionTitle || advice.title,
        description: advice.actionDesc || advice.description,
        icon: advice.icon
      }
      
      let dealerCodes = []
      if (specificDealerCodes) {
        dealerCodes = Array.isArray(specificDealerCodes) ? specificDealerCodes : [specificDealerCodes]
      } else {
        const dealers = this.getFilteredDealerData()
        if (dealers.length === 0) {
          alert('当前筛选条件下没有经销商数据，请调整筛选条件')
          return
        }
        dealerCodes = dealers.map(d => d['经销商代码']).filter(code => code)
      }
      
      try {
        const checkResponse = await axios.post('/api/decision/check-task-exists', {
          title: normalizedAdvice.title,
          dealerCodes: dealerCodes,
          filters: this.filters
        })
        
        if (checkResponse.data.success && checkResponse.data.exists) {
          alert(`该任务已下发过！\n\n${checkResponse.data.message}\n\n请勿重复下发相同任务。`)
          // 同步本地状态
          this.$set(advice, 'isDispatched', true)
          return
        }
      } catch (error) {
        console.error('检查任务失败:', error)
      }
      
      const confirmed = confirm(`确认要执行此建议吗？\n\n${normalizedAdvice.title}\n\n执行后，${dealerCodes.length}个相关经销商将收到任务通知。`)
      if (!confirmed) return
      
      try {
        const response = await axios.post('/api/decision/implement-advice', {
          advice: normalizedAdvice,
          dealerCodes: dealerCodes,
          filters: this.filters
        })
        
        if (response.data.success) {
          alert(`决策建议已成功执行，${dealerCodes.length}个经销商将收到任务通知`)
          // 关键修复：立即更新本地状态，避免刷新页面
          this.$set(advice, 'isDispatched', true)
        } else {
          throw new Error(response.data.message || '执行失败')
        }
      } catch (error) {
        console.error('执行决策建议失败:', error)
        
        if (error.response && error.response.status === 404) {
          const mockSuccess = confirm('后端API暂未实现，是否模拟执行成功？\n\n点击"确定"模拟成功，点击"取消"放弃操作')
          if (mockSuccess) {
            this.$set(advice, 'isDispatched', true)
            alert(`模拟执行成功！\n\n已向${dealerCodes.length}个经销商发送任务通知：\n${dealerCodes.slice(0, 5).join(', ')}${dealerCodes.length > 5 ? '...' : ''}`)
          }
        } else {
          alert('执行失败：' + (error.message || '请稍后重试'))
        }
      }
    },
    
    sortBy(key) {
      if (this.sortKey === key) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortKey = key
        this.sortOrder = 'asc'
      }
      
      this.loadTableData()
    },
    
    exportTableData() {
      try {
        const dealers = this.getFilteredDealerData()
        
        const tableRows = dealers.map(dealer => {
          let totalSales = 0
          let totalTraffic = 0
          let totalLeads = 0
          let totalPotential = 0
          
          this.filteredMonths.forEach(m => {
            totalSales += this.toNumber(dealer[`${m}销量`])
            totalTraffic += this.toNumber(dealer[`${m}客流量`])
            totalLeads += this.toNumber(dealer[`${m}线索量`])
            totalPotential += this.toNumber(dealer[`${m}潜客量`])
          })
          
          return {
            '经销商代码': dealer['经销商代码'] || '',
            '省份': dealer['省份'] || '',
            '总销量': totalSales,
            '总客流量': totalTraffic,
            '总潜客量': totalPotential,
            '总线索量': totalLeads
          }
        }).filter(row => row['经销商代码'] && row['经销商代码'].trim() !== '')
        
        if (tableRows.length === 0) {
          alert('没有可导出的数据')
          return
        }
        
        const headers = ['经销商代码', '省份', '总销量', '总客流量', '总潜客量', '总线索量']
        let csvContent = headers.join(',') + '\n'
        
        tableRows.forEach(row => {
          const values = headers.map(header => {
            const value = row[header]
            if (typeof value === 'string' && value.includes(',')) {
              return `"${value}"`
            }
            return value
          })
          csvContent += values.join(',') + '\n'
        })
        
        const BOM = '\uFEFF'
        const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        
        link.setAttribute('href', url)
        link.setAttribute('download', `经销商数据_${new Date().toISOString().slice(0, 10)}.csv`)
        link.style.visibility = 'hidden'
        
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        alert('数据导出成功')
      } catch (error) {
        console.error('导出数据失败:', error)
        alert('导出失败，请稍后重试')
      }
    },
    
    formatNumber(value) {
      if (!value) return '0'
      return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
    },
    
    formatTableCell(value, key) {
      if (value === null || value === undefined) return '-'
      
      if (['totalSales', 'totalTraffic', 'totalPotential', 'totalLeads'].includes(key)) {
        return this.formatNumber(value)
      }
      
      return value
    },

    async loadFunnelDiagnosis() {
      console.log('[前端] loadFunnelDiagnosis 被调用, isAdmin:', this.isAdmin)
      if (!this.isAdmin) return
      console.log('[前端] 调用漏斗诊断接口, filters:', JSON.stringify(this.filters))
      try {
        const response = await axios.get('/api/decision/funnel-diagnosis', {
          params: this.filters
        })
        console.log('[前端] 漏斗诊断响应:', response.data)
        if (response.data.success) {
          this.diagnosisAlerts = response.data.alerts || []
          this.checkDiagnosisDispatchStatus()
          console.log('[前端] 诊断告警数量:', this.diagnosisAlerts.length)
        }
      } catch (error) {
        console.error('加载漏斗诊断失败:', error)
      }
    },

    async loadROIAnalysis() {
      try {
        const response = await axios.get('/api/decision/roi-analysis', {
          params: this.filters
        })
        if (response.data.success) {
          this.initROIChart(response.data)
        }
      } catch (error) {
        console.error('加载ROI分析失败:', error)
      }
    },

    initROIChart(data) {
      this.$nextTick(() => {
        if (!this.$refs.roiChart) return
        
        if (this.roiChart) {
          this.roiChart.dispose()
        }
        
        this.roiChart = echarts.init(this.$refs.roiChart)
        
        const option = {
          title: {
            text: '政策投入 - 销量产出四象限门店分类图',
            left: 'center',
            top: 10,
            textStyle: { fontSize: 16, color: '#333', fontWeight: 'bold' }
          },
          tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e8e8e8',
            borderWidth: 1,
            padding: [10, 14],
            textStyle: { color: '#333', fontSize: 12 },
            formatter: (params) => {
              return `<div style="font-weight: bold; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 5px;">${params.data.name}</div>
                      <div style="display: flex; justify-content: space-between; gap: 20px;">
                        <span style="color: #666;">政策投入:</span>
                        <span style="font-weight: bold;">${params.data.value[0]}</span>
                      </div>
                      <div style="display: flex; justify-content: space-between; gap: 20px;">
                        <span style="color: #666;">实际销量:</span>
                        <span style="font-weight: bold;">${params.data.value[1]}</span>
                      </div>
                      <div style="margin-top: 5px; font-size: 11px; color: #999;">省份: ${params.data.province}</div>`
            }
          },
          grid: { top: 70, right: 50, bottom: 50, left: 60 },
          xAxis: {
            name: '政策投入',
            nameLocation: 'middle',
            nameGap: 30,
            splitLine: { lineStyle: { type: 'dashed', color: '#eee' } },
            axisLine: { lineStyle: { color: '#999' } }
          },
          yAxis: {
            name: '实际销量',
            nameLocation: 'middle',
            nameGap: 40,
            splitLine: { lineStyle: { type: 'dashed', color: '#eee' } },
            axisLine: { lineStyle: { color: '#999' } }
          },
          series: [{
            type: 'scatter',
            data: data.points,
            symbolSize: (val) => Math.sqrt(val[1]) * 0.4 + 3,
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.1)',
              color: (params) => {
                const x = params.value[0]
                const y = params.value[1]
                if (x >= data.avgPolicy && y >= data.avgSales) return '#ff4d4f'
                if (x >= data.avgPolicy && y < data.avgSales) return '#faad14'
                if (x < data.avgPolicy && y >= data.avgSales) return '#52c41a'
                return '#1890ff'
              }
            },
            markLine: {
              silent: true,
              lineStyle: { type: 'solid', color: '#ff7875', width: 1.5, opacity: 0.6 },
              label: { position: 'end', fontSize: 11, color: '#ff7875' },
              data: [
                { xAxis: data.avgPolicy, label: { formatter: '投入均值' } },
                { yAxis: data.avgSales, label: { formatter: '销量均值', position: 'end' } }
              ]
            },
            markArea: {
              silent: true,
              data: [
                [{ name: '重点扶持型 (高投入高产出)', xAxis: data.avgPolicy, yAxis: data.avgSales, itemStyle: { color: 'rgba(255, 77, 79, 0.03)' }, label: { position: 'insideTopRight', color: '#ff4d4f', opacity: 0.5 } }, { xAxis: 'max', yAxis: 'max' }],
                [{ name: '优先复制型 (低投入高产出)', xAxis: 0, yAxis: data.avgSales, itemStyle: { color: 'rgba(82, 196, 26, 0.03)' }, label: { position: 'insideTopLeft', color: '#52c41a', opacity: 0.5 } }, { xAxis: data.avgPolicy, yAxis: 'max' }],
                [{ name: '关注引导型 (低投入低产出)', xAxis: 0, yAxis: 0, itemStyle: { color: 'rgba(24, 144, 255, 0.03)' }, label: { position: 'insideBottomLeft', color: '#1890ff', opacity: 0.5 } }, { xAxis: data.avgPolicy, yAxis: data.avgSales }],
                [{ name: '整改优化型 (高投入低产出)', xAxis: data.avgPolicy, yAxis: 0, itemStyle: { color: 'rgba(250, 173, 20, 0.03)' }, label: { position: 'insideBottomRight', color: '#faad14', opacity: 0.5 } }, { xAxis: 'max', yAxis: data.avgSales }]
              ]
            }
          }]
        }
        
        this.roiChart.setOption(option)
      })
    },

    async showPeerBenchmark(dealerCode) {
      this.loading = true
      try {
        const response = await axios.get('/api/decision/peer-benchmark', {
          params: { dealer_code: dealerCode }
        })
        if (response.data.success) {
          const benchmark = response.data
          const confirmed = confirm(`系统已为您找到最佳对标门店：${benchmark.benchmarkDealer}\n\n该对标店雷达评分近期提升了 ${benchmark.growth.toFixed(1)} 分。\n\n其优秀执行经验如下：\n"${benchmark.feedbackTemplate}"\n\n是否将此经验作为附件，一键抄送给经销商 ${dealerCode} 并下发对标学习任务？`)
          
          if (confirmed) {
            await this.implementAdvice({
              title: `【对标学习】向优秀门店 ${benchmark.benchmarkDealer} 学习经验`,
              description: `系统通过五力雷达数据分析，识别出 ${benchmark.benchmarkDealer} 为您当前级别的对标标杆。请参考其优秀执行经验：\n\n${benchmark.feedbackTemplate}\n\n请结合本店实际情况，提交一份学习整改报告。`,
              icon: '🏆'
            }, [dealerCode])
          }
        }
      } catch (error) {
        console.error('获取对标数据失败:', error)
        alert('暂未找到合适的同级对标门店数据')
      } finally {
        this.loading = false
      }
    }
  },
  
  watch: {
    currentPage() {
      this.loadTableData()
    },
    'filters.dealerCode'() {
      this.calculateMetrics()
      this.updateTrendChart()
      this.updateNetworkGraph()
      this.loadFunnelDiagnosis()
      this.loadROIAnalysis()
      this.loadTableData()
    },
    'filters.province'() {
      this.calculateMetrics()
      this.updateTrendChart()
      this.updateNetworkGraph()
      this.loadFunnelDiagnosis()
      this.loadROIAnalysis()
      this.loadTableData()
    },
    'filters.region'() {
      this.calculateMetrics()
      this.updateTrendChart()
      this.updateNetworkGraph()
      this.loadFunnelDiagnosis()
      this.loadROIAnalysis()
      this.loadTableData()
    },
    'filters.startDate'() {
      this.calculateMetrics()
      this.updateTrendChart()
      this.loadFunnelDiagnosis()
      this.loadROIAnalysis()
      this.loadTableData()
    },
    'filters.endDate'() {
      this.calculateMetrics()
      this.updateTrendChart()
      this.loadFunnelDiagnosis()
      this.loadROIAnalysis()
      this.loadTableData()
    }
  },
  
  beforeDestroy() {
    if (this.trendChart) {
      this.trendChart.dispose()
    }
    if (this.networkChart) {
      this.networkChart.dispose()
    }
    if (this.roiChart) {
      this.roiChart.dispose()
    }
    window.removeEventListener('resize', this.handleResize)
  }
}
</script>

<style scoped>
.decision-support-container {
  position: relative;
  min-height: calc(100vh - 100px);
  background-color: #f5f7fa;
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

.filter-select {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  min-width: 150px;
  background-color: white;
}

.dealer-input-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dealer-select {
  min-width: 200px;
}

.input-dealer-code {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  width: 140px;
}

.input-dealer-code:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.province-display {
  display: flex;
  align-items: center;
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 8px 12px;
  min-width: 110px;
}

.province-display.has-province {
  background: #e6f7ff;
  border-color: #91d5ff;
}

.province-label {
  color: #666;
  font-size: 14px;
  margin-right: 4px;
}

.province-value {
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

.province-display.has-province .province-value {
  color: #1890ff;
}

.filter-buttons {
  display: flex;
  flex-direction: row;
  gap: 10px;
  align-items: flex-end;
}

.filter-buttons .btn-apply,
.filter-buttons .btn-reset {
  margin-top: 24px;
}

.btn-apply {
  padding: 8px 20px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-apply:hover {
  background: #40a9ff;
}

.btn-reset {
  padding: 8px 20px;
  background: white;
  color: #666;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-reset:hover {
  color: #1890ff;
  border-color: #1890ff;
}

.error-message {
  margin-top: 10px;
  padding: 8px 12px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  color: #ff4d4f;
  font-size: 13px;
}

.content-area {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
}

.metric-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
}

.metric-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.sales-icon {
  background: #e6f7ff;
}

.orders-icon {
  background: #f6ffed;
}

.profit-icon {
  background: #fff7e6;
}

.leads-icon {
  background: #f9f0ff;
}

.rate-icon {
  background: #e6fffb;
}

.policy-icon {
  background: #fff1f0;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.metric-change {
  font-size: 12px;
  font-weight: 500;
}

.metric-change.positive {
  color: #52c41a;
}

.metric-change.negative {
  color: #ff4d4f;
}

.charts-row {
  display: grid;
  grid-template-columns: 60% 40%;
  gap: 20px;
}

.chart-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.chart-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.network-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.network-select {
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  background: white;
}

.btn-refresh {
  padding: 4px 12px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #666;
}

.btn-refresh:hover {
  color: #1890ff;
  border-color: #1890ff;
}

.network-stats-bar {
  display: flex;
  gap: 20px;
  margin-bottom: 10px;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.network-stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.network-stat-item .stat-label {
  font-size: 12px;
  color: #666;
}

.network-stat-item .stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #1890ff;
}

.chart-body {
  height: 300px;
}

.network-body {
  height: 250px;
}

.network-legend {
  display: flex;
  gap: 20px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.network-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-node {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-node.province {
  background: #3498db;
}

.legend-node.category {
  background: #e74c3c;
}

.legend-node.keyword {
  background: #2ecc71;
}

.legend-text {
  font-size: 12px;
  color: #666;
}

.advice-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.advice-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.advice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.advice-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.advice-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.advice-card {
  display: flex;
  gap: 15px;
  padding: 15px;
  background: #fafafa;
  border-radius: 6px;
  border-left: 3px solid #1890ff;
}

.advice-icon {
  width: 40px;
  height: 40px;
  background: #e6f7ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.advice-body {
  flex: 1;
}

.advice-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.advice-description {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 10px;
}

.advice-actions {
  display: flex;
  gap: 10px;
}

.btn-action {
  padding: 4px 12px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-action.secondary {
  background: white;
  color: #1890ff;
  border: 1px solid #1890ff;
}

.btn-action:hover {
  opacity: 0.8;
}

.table-row {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.table-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.data-info {
  font-size: 13px;
  color: #666;
  padding: 4px 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-text {
  font-size: 16px;
  color: #999;
  margin-bottom: 10px;
}

.empty-hint {
  font-size: 14px;
  color: #ff4d4f;
}

.btn-export {
  padding: 6px 16px;
  background: #52c41a;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-export:hover {
  background: #73d13d;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead th {
  padding: 12px;
  background: #fafafa;
  border-bottom: 2px solid #e8e8e8;
  text-align: left;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  cursor: pointer;
}

.data-table thead th:hover {
  background: #f0f0f0;
}

.data-table tbody td {
  padding: 12px;
  border-bottom: 1px solid #e8e8e8;
  font-size: 14px;
  color: #666;
}

.data-table tbody tr:hover {
  background: #fafafa;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
}

.page-btn {
  width: 32px;
  height: 32px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-btn:hover:not(:disabled) {
  color: #1890ff;
  border-color: #1890ff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
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

@media (max-width: 1400px) {
  .metrics-row {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .charts-row {
    grid-template-columns: 1fr;
  }
  
  .advice-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-item {
    width: 100%;
  }
  
  .filter-buttons {
    justify-content: center;
  }
  
  .filter-buttons .btn-apply,
  .filter-buttons .btn-reset {
    margin-top: 0;
  }
  
  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

.diagnosis-row {
  margin-bottom: 24px;
}

.diagnosis-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  padding: 20px;
}

.diagnosis-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.diagnosis-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.diagnosis-badge {
  margin-left: 12px;
  padding: 2px 8px;
  background: #f0f5ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
}

.diagnosis-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

.diagnosis-content::-webkit-scrollbar {
  width: 6px;
}

.diagnosis-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.diagnosis-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.diagnosis-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.diagnosis-card {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  background: #fafafa;
  border-left: 4px solid #d9d9d9;
  transition: all 0.3s;
}

.diagnosis-card:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.diagnosis-card.error {
  background: #fff1f0;
  border-left-color: #ff4d4f;
}

.diagnosis-card.warning {
  background: #fffbe6;
  border-left-color: #faad14;
}

.alert-icon {
  font-size: 24px;
  margin-right: 16px;
}

.alert-body {
  flex: 1;
}

.alert-title {
  font-weight: bold;
  font-size: 15px;
  color: #262626;
  margin-bottom: 4px;
}

.alert-desc {
  font-size: 13px;
  color: #595959;
  margin-bottom: 8px;
}

.alert-stats {
  display: flex;
  gap: 12px;
}

.stat-tag {
  font-size: 12px;
  padding: 1px 6px;
  background: rgba(0,0,0,0.05);
  border-radius: 4px;
  color: #8c8c8c;
}

.stat-tag.avg {
  color: #1890ff;
  background: #e6f7ff;
}

.btn-diagnosis-action {
  padding: 6px 16px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.btn-diagnosis-action:hover {
  background: #40a9ff;
}

.btn-diagnosis-action.dispatched {
  background: #d9d9d9;
  color: #8c8c8c;
  cursor: not-allowed;
}

.btn-diagnosis-action.dispatched:hover {
  background: #d9d9d9;
}

.btn-action.secondary.dispatched {
  background: #d9d9d9;
  color: #8c8c8c;
  cursor: not-allowed;
}

.btn-action.secondary.dispatched:hover {
  background: #d9d9d9;
}

.roi-row {
  margin-bottom: 24px;
}

.roi-chart .chart-body {
  height: 450px;
}

.diagnosis-actions {
  display: flex;
  gap: 8px;
}

.btn-benchmark-action {
  padding: 6px 12px;
  background: white;
  color: #52c41a;
  border: 1px solid #52c41a;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.btn-benchmark-action:hover {
  background: #f6ffed;
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

.history-btn {
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

.history-btn:hover {
  background: #40a9ff;
}
</style>
