<template>
  <div class="dashboard-container" :class="{ 'show-export-dropdown': showExportDropdown || showReportDropdown }">
    <!-- 页面标题和操作按钮 -->
    <div class="header-section">
      <h1 class="page-title">汽车销售提升 · 2024</h1>
      <div class="header-controls">
        <!-- 时间范围选择器 -->
        <div class="time-range-selector">
          <label class="time-range-label">时间范围：</label>
          <select v-model="timeRange" class="time-range-select" @change="handleTimeRangeChange">
            <option value="all">全部时间</option>
            <option value="quarter">按季度</option>
            <option value="month">按月度</option>
          </select>
          
          <!-- 季度选择器 -->
          <select v-if="timeRange === 'quarter'" v-model="selectedQuarter" class="time-range-select" @change="renderCharts">
            <option value="1">第一季度</option>
            <option value="2">第二季度</option>
            <option value="3">第三季度</option>
            <option value="4">第四季度</option>
          </select>
          
          <!-- 月度选择器 -->
          <select v-if="timeRange === 'month'" v-model="selectedMonth" class="time-range-select" @change="renderCharts">
            <option v-for="i in 12" :key="i" :value="i">{{ i }}月</option>
          </select>
        </div>
        
        <!-- 操作按钮组 -->
        <div class="button-group">
          <!-- 分析报告下拉菜单 -->
          <div class="dropdown">
            <button class="btn btn-gray dropdown-toggle" @click="toggleReportDropdown">
              <i class="fas fa-file-alt mr-1"></i>分析报告
              <i :class="['fas', showReportDropdown ? 'fa-chevron-up' : 'fa-chevron-down', 'ml-1']"></i>
            </button>
            <div v-if="showReportDropdown" class="dropdown-menu">
              <button class="dropdown-item" @click.stop="selectAllCards">
                <i :class="['fas', isAllSelected ? 'fa-times-square' : 'fa-check-square', 'mr-1']"></i>{{ isAllSelected ? '取消全选' : '选择全部卡片' }}
              </button>
              <button class="dropdown-item" @click="generateReportFromSelection">
                <i class="fas fa-file-export mr-1"></i>生成报告
              </button>
            </div>
          </div>
          <div class="dropdown">
            <button class="btn btn-gray dropdown-toggle" @click="toggleExportDropdown">
              <i class="fas fa-download mr-1"></i>数据导出
              <i :class="['fas', showExportDropdown ? 'fa-chevron-up' : 'fa-chevron-down', 'ml-1']"></i>
            </button>
            <div v-if="showExportDropdown" class="dropdown-menu">
              <div class="dropdown-submenu">
                <button class="dropdown-item dropdown-toggle" @click.stop="toggleAllExportSubmenu">
                  <i class="fas fa-file-alt mr-1"></i>全部导出
                  <i :class="['fas', showAllExportSubmenu ? 'fa-chevron-down' : 'fa-chevron-right', 'ml-1']"></i>
                </button>
                <div v-if="showAllExportSubmenu" class="dropdown-submenu-menu">
                  <button class="dropdown-item" @click="exportData('excel', 'all')">
                    <i class="fas fa-file-excel mr-1"></i>Excel格式
                  </button>
                  <button class="dropdown-item" @click="exportData('csv', 'all')">
                    <i class="fas fa-file-csv mr-1"></i>CSV格式
                  </button>
                  <button class="dropdown-item" @click="exportData('pdf', 'all')">
                    <i class="fas fa-file-pdf mr-1"></i>PDF格式
                  </button>
                </div>
              </div>
              <div class="dropdown-submenu">
                <button class="dropdown-item dropdown-toggle" @click.stop="toggleSelectedExportSubmenu">
                  <i class="fas fa-file-excel mr-1"></i>部分导出
                  <i :class="['fas', showSelectedExportSubmenu ? 'fa-chevron-down' : 'fa-chevron-right', 'ml-1']"></i>
                </button>
                <div v-if="showSelectedExportSubmenu" class="dropdown-submenu-menu">
                  <button class="dropdown-item" @click="exportData('excel', 'selected')">
                    <i class="fas fa-file-excel mr-1"></i>Excel格式
                  </button>
                  <button class="dropdown-item" @click="exportData('csv', 'selected')">
                    <i class="fas fa-file-csv mr-1"></i>CSV格式
                  </button>
                  <button class="dropdown-item" @click="exportData('pdf', 'selected')">
                    <i class="fas fa-file-pdf mr-1"></i>PDF格式
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">数据加载中...</p>
    </div>
    
    <!-- 错误信息 -->
    <div v-if="error" class="error-container">
      <div class="error-icon">
        <i class="fas fa-exclamation-circle"></i>
      </div>
      <div class="error-content">
        <p class="error-message">{{ error }}</p>
        <button class="btn btn-blue" @click="renderCharts">重新加载</button>
      </div>
    </div>
    
    <!-- 经销商选择模块 -->
    <div class="dealer-selector-container">
      <div class="aleftboxtbott">
        <h2 class="tith2">经销商选择</h2>
        <div class="aleftboxtbott_cont">
          <DealerSelector 
            :dealers="dealers" 
            v-model="selectedCode"
            :errorMessage="errorMessage"
            @apply-manual="applyManualDealer"
          />
        </div>
      </div>
    </div>

    <!-- 月度快照+核心指标 -->
    <div class="snapshot-metrics-row">
      <div class="left1">
        <div class="card-wrapper" :class="{ 'card-selected': selectedCards.includes('snapshot') }">
          <div class="card-checkbox">
            <input 
              type="checkbox" 
              :checked="selectedCards.includes('snapshot')"
              @change="toggleCardSelection('snapshot')"
            />
          </div>
          <div class="aleftboxttop">
            <h2 class="tith2">月度快照</h2>
            <div id="aleftboxttop" class="aleftboxttopcont">   
              <ul class="month-list">
                <li v-for="snap in monthSnapshots" :key="snap.month">
                  <span class="month-label">{{ snap.month }}</span>
                  <span class="metric-item sales">销量 {{ snap.sales }}</span>
                  <span class="metric-item traffic">客流 {{ snap.traffic }}</span>
                  <span class="metric-item leads">线索 {{ snap.leads }}</span>
                  <span class="metric-item potential">潜客 {{ snap.potential }}</span>
                  <span class="metric-item rate">成交率 {{ snap.rate }}%</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div class="core-metrics-container">
        <div class="card-wrapper" :class="{ 'card-selected': selectedCards.includes('metrics') }">
          <div class="card-checkbox">
            <input 
              type="checkbox" 
              :checked="selectedCards.includes('metrics')"
              @change="toggleCardSelection('metrics')"
            />
          </div>
          <div class="aleftboxtmidd">
            <div class="metrics-header">
              <h2 class="tith2">核心指标</h2>
              <button class="metric-toggle-btn" @click="toggleMetricDisplayMode">
                {{ getMetricDisplayModeText() }}
              </button>
            </div>
            <div class="core-metrics-grid">
              <div 
                v-for="(item, index) in headlineMetrics" 
                :key="index"
                class="core-metric-item"
              >
                <h4 class="metric-name">{{ item.label }}</h4>
                <h3 :class="getMetricColorClass(item.label)">{{ item.display }}</h3>
                <p class="text-muted month-text">{{ item.bestMonth }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 销量趋势分析+销售漏斗 -->
    <div class="trend-funnel-row">
      <div class="mrbox">
        <div class="card-wrapper" :class="{ 'card-selected': selectedCards.includes('trend') }">
          <div class="card-checkbox">
            <input 
              type="checkbox" 
              :checked="selectedCards.includes('trend')"
              @change="toggleCardSelection('trend')"
            />
          </div>
          <div class="amiddboxttop">
            <h2 class="tith2">销量趋势分析</h2>
            <div class="left2_table chart-container" ref="trendChart"></div>
          </div>
        </div>
      </div>

      <div class="funnel-container">
        <div class="card-wrapper" :class="{ 'card-selected': selectedCards.includes('funnel') }">
          <div class="card-checkbox">
            <input 
              type="checkbox" 
              :checked="selectedCards.includes('funnel')"
              @change="toggleCardSelection('funnel')"
            />
          </div>
          <div class="amiddboxtbott1">
            <h2 class="tith2">销售漏斗</h2>
            <div class="amiddboxtbott1content chart-container" ref="funnelChart"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 四合一模块布局 -->
    <div class="four-in-one-row">
      <div class="four-in-one-item">
        <div class="card-wrapper" :class="{ 'card-selected': selectedCards.includes('rate') }">
          <div class="card-checkbox">
            <input 
              type="checkbox" 
              :checked="selectedCards.includes('rate')"
              @change="toggleCardSelection('rate')"
            />
          </div>
          <h2 class="tith2">成交/战败率</h2>
          <div class="chart-container" ref="rateChart"></div>
        </div>
      </div>
      <div class="four-in-one-item">
        <div class="card-wrapper" :class="{ 'card-selected': selectedCards.includes('responseTime') }">
          <div class="card-checkbox">
            <input 
              type="checkbox" 
              :checked="selectedCards.includes('responseTime')"
              @change="toggleCardSelection('responseTime')"
            />
          </div>
          <h2 class="tith2">响应时间分析</h2>
          <div class="chart-container" ref="responseTimeChart"></div>
        </div>
      </div>
      <div class="four-in-one-item">
        <div class="card-wrapper" :class="{ 'card-selected': selectedCards.includes('policy') }">
          <div class="card-checkbox">
            <input 
              type="checkbox" 
              :checked="selectedCards.includes('policy')"
              @change="toggleCardSelection('policy')"
            />
          </div>
          <h2 class="tith2">政策影响</h2>
          <div class="chart-container" ref="policyChart"></div>
        </div>
      </div>
      <div class="four-in-one-item">
        <div class="card-wrapper" :class="{ 'card-selected': selectedCards.includes('gsev') }">
          <div class="card-checkbox">
            <input 
              type="checkbox" 
              :checked="selectedCards.includes('gsev')"
              @change="toggleCardSelection('gsev')"
            />
          </div>
          <h2 class="tith2">GSEV占比</h2>
          <div class="chart-container" ref="gsevChart"></div>
        </div>
      </div>
    </div>
    <!-- 四合一模块布局 end -->
    
    <!-- 评价占比框 -->
    <div class="review-box">
      <div class="card-wrapper" :class="{ 'card-selected': selectedCards.includes('review') }">
        <div class="card-checkbox">
          <input 
            type="checkbox" 
            :checked="selectedCards.includes('review')"
            @change="toggleCardSelection('review')"
          />
        </div>
        <h2 class="tith2">好坏评占比</h2>
        <div class="review-charts-container">
          <div class="review-charts-row">
            <div v-for="(month, index) in months" :key="month" class="review-chart-item">
              <div class="review-chart-title">{{ month }}</div>
              <div ref="reviewCharts" class="review-chart"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 报告模态框 -->
    <ReportModal 
      v-if="showReportModal"
      :visible="showReportModal"
      :cardData="reportCardData"
      :dealerCode="selectedCode"
      @close="closeReportModal"
    />
  </div>
</template>

<script>
import * as echarts from 'echarts'
import dealerData from '@/assets/dealerData.json'
import DealerSelector from '@/components/DealerSelector'
import ReportModal from '@/components/ReportModal.vue'
import { extractCardData } from '@/DS/dataExtractor.js'

const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月']

const metricKeys = {
  销量: (m) => `${m}销量`,
  客流量: (m) => `${m}客流量`,
  潜客量: (m) => `${m}潜客量`,
  线索量: (m) => `${m}线索量`,
  成交率: (m) => `${m}成交率`,
  战败率: (m) => `${m}战败率`,
  成交响应时间: (m) => `${m}成交响应时间`,
  战败响应时间: (m) => `${m}战败响应时间`,
  政策: (m) => `${m}政策`,
  GSEV: (m) => `${m}GSEV`,
  评价数: (m) => `${m}评价数`,
  好评数: (m) => `${m}好评数`,
  差评数: (m) => `${m}差评数`,
}

export default {
  name: 'DealerDashboard',
  components: {
    DealerSelector,
    ReportModal
  },
  data() {
    return {
      dealers: dealerData || [],
      selectedCode: dealerData?.[0]?.['经销商代码'] || '',
      months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月'],
      timeRange: 'all', // all, quarter, month
      selectedQuarter: 1,
      selectedMonth: 1,
      // 加载状态
      loading: false,
      error: null,
      // 导出下拉菜单状态
      showExportDropdown: false,
      // 导出子菜单状态
      showAllExportSubmenu: false,
      showSelectedExportSubmenu: false,
      // 图表实例
      charts: {
        trend: null,
        funnel: null,
        rate: null,
        responseTime: null,
        policy: null,
        gsev: null,
        reviewCharts: []
      },
      metricDisplayMode: 'peak', // peak, valley, both
      // 卡片抖动和选择状态
      isReportMode: false,
      selectedCards: [],
      // 报告下拉菜单状态
      showReportDropdown: false,
      // 报告模态框状态
      showReportModal: false,
      reportCardData: {},
      // ResizeObserver实例
      resizeObserver: null
    }
  },
  computed: {
    currentDealer() {
      return this.dealers.find((d) => d['经销商代码'] === this.selectedCode) || {}
    },
    // 根据选择的时间范围返回相应的月份
    filteredMonths() {
      if (this.timeRange === 'all') {
        // 全部时间，返回所有月份
        return this.months
      } else if (this.timeRange === 'quarter') {
        // 按季度，返回对应季度的月份
        const quarterMonths = {
          1: ['1月', '2月', '3月'],
          2: ['4月', '5月', '6月'],
          3: ['7月', '8月', '9月'],
          4: ['10月', '11月', '12月']
        }
        return quarterMonths[this.selectedQuarter] || []
      } else if (this.timeRange === 'month') {
        // 按月度，返回对应月份
        return [`${this.selectedMonth}月`]
      }
      return this.months
    },
    monthSnapshots() {
      return this.months.map((m) => {
        const sales = this.toNumber(this.currentDealer[metricKeys.销量(m)])
        const traffic = this.toNumber(this.currentDealer[metricKeys.客流量(m)])
        const leads = this.toNumber(this.currentDealer[metricKeys.线索量(m)])
        const potential = this.toNumber(this.currentDealer[metricKeys.潜客量(m)])
        const rate = this.toNumber(this.currentDealer[metricKeys.成交率(m)] * 100)
        return {
          month: m,
          sales: this.formatNumber(sales),
          traffic: this.formatNumber(traffic),
          leads: this.formatNumber(leads),
          potential: this.formatNumber(potential),
          rate: (rate || 0).toFixed(1),
        }
      })
    },
    headlineMetrics() {
      const recentMonth = this.months[this.months.length - 1]
      const metrics = [
        { key: '销量', unit: '辆' },
        { key: '客流量', unit: '人' },
        { key: '线索量', unit: '条' },
        { key: '潜客量', unit: '人' },
      ]
      return metrics.map((m) => {
        const series = this.months.map((mo) => this.toNumber(this.currentDealer[metricKeys[m.key](mo)]))
        const peakIdx = this.findMaxIndex(series)
        const valleyIdx = this.findMinIndex(series)
        
        let display = ''
        let bestMonth = ''
        let worstMonth = ''
        
        if (this.metricDisplayMode === 'peak') {
          const peakValue = series[peakIdx]
          display = m.key.includes('率')
            ? `${(peakValue * 100 || 0).toFixed(1)}${m.unit}`
            : `${this.formatNumber(peakValue)}${m.unit}`
          bestMonth = this.months[peakIdx] || '-'
        } else if (this.metricDisplayMode === 'valley') {
          const valleyValue = series[valleyIdx]
          display = m.key.includes('率')
            ? `${(valleyValue * 100 || 0).toFixed(1)}${m.unit}`
            : `${this.formatNumber(valleyValue)}${m.unit}`
          bestMonth = this.months[valleyIdx] || '-'
        } else if (this.metricDisplayMode === 'both') {
          const peakValue = series[peakIdx]
          const valleyValue = series[valleyIdx]
          const peakDisplay = m.key.includes('率')
            ? `${(peakValue * 100 || 0).toFixed(1)}${m.unit}`
            : `${this.formatNumber(peakValue)}${m.unit}`
          const valleyDisplay = m.key.includes('率')
            ? `${(valleyValue * 100 || 0).toFixed(1)}${m.unit}`
            : `${this.formatNumber(valleyValue)}${m.unit}`
          display = `${peakDisplay} / ${valleyDisplay}`
          bestMonth = this.months[peakIdx] || '-'
          worstMonth = this.months[valleyIdx] || '-'
        }
        
        return { 
          label: m.key, 
          display, 
          bestMonth,
          worstMonth
        }
      })
    },
    isAllSelected() {
      const allCardIds = ['trend', 'funnel', 'snapshot', 'metrics', 'policy', 'rate', 'responseTime', 'gsev', 'review']
      return allCardIds.every(id => this.selectedCards.includes(id))
    },
  },
  mounted() {
    this.$nextTick(() => {
      this.initCharts()
      this.renderCharts()
    })
    
    this.resizeObserver = new ResizeObserver(() => {
      this.handleResize()
    })
    
    const chartContainers = [
      this.$refs.trendChart,
      this.$refs.funnelChart,
      this.$refs.rateChart,
      this.$refs.responseTimeChart,
      this.$refs.policyChart,
      this.$refs.gsevChart
    ].filter(el => el)
    
    chartContainers.forEach(el => {
      this.resizeObserver.observe(el)
    })
    
    if (Array.isArray(this.$refs.reviewCharts)) {
      this.$refs.reviewCharts.forEach(el => {
        if (el) {
          this.resizeObserver.observe(el)
        }
      })
    }
    
    window.addEventListener('resize', this.handleResize)
  },
  watch: {
    selectedCode(newCode, oldCode) {
      console.log('经销商代码变化:', oldCode, '->', newCode)
      console.log('当前经销商数据:', this.currentDealer)
      this.renderCharts()
    },
  },
  beforeDestroy() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect()
      this.resizeObserver = null
    }
    
    window.removeEventListener('resize', this.handleResize)
    document.removeEventListener('click', this.closeExportDropdown)
    document.removeEventListener('click', this.closeReportDropdown)
    Object.keys(this.charts).forEach((key) => {
      if (key === 'reviewCharts') {
        // 处理reviewCharts数组
        if (Array.isArray(this.charts.reviewCharts)) {
          this.charts.reviewCharts.forEach((chart) => chart && chart.dispose())
        }
      } else {
        // 处理单个图表对象
        if (this.charts[key]) {
          this.charts[key].dispose()
        }
      }
    })
  },
  methods: {
    getMetricColorClass(label) {
      const colorMap = {
        '销量': 'ceeb1fd',
        '客流量': 'c24c9ff',
        '线索量': 'cffff00',
        '潜客量': 'c11e2dd'
      }
      return colorMap[label] || 'c24c9ff'
    },
    applyManualDealer() {
      const code = (this.inputCode || '').trim()
      const province = (this.inputProvince || '').trim()

      if (!code && !province) {
        this.errorMessage = '请至少输入经销商代码或省份再查询'
        return
      }

      let target = null
      // 优先按代码精确匹配
      if (code) {
        target = this.dealers.find((d) => String(d['经销商代码']) === code)
      }
      // 若无结果且填了省份，则按省份模糊匹配第一条
      if (!target && province) {
        const lower = province.toLowerCase()
        target = this.dealers.find((d) => String(d['省份'] || '').toLowerCase().includes(lower))
      }

      if (!target) {
        this.errorMessage = '未找到对应经销商，请检查代码或省份后重试'
        return
      }

      this.selectedCode = target['经销商代码']
      this.errorMessage = ''
    },
    toNumber(val) {
      const num = Number(val)
      return Number.isFinite(num) ? num : 0
    },
    formatNumber(val) {
      const num = this.toNumber(val)
      if (num >= 10000) return `${(num / 10000).toFixed(1)}万`
      return num.toLocaleString()
    },
    findMaxIndex(arr = []) {
      let idx = 0
      let maxValue = this.toNumber(arr[0])
      arr.forEach((v, i) => {
        const currentValue = this.toNumber(v)
        if (currentValue > maxValue) {
          maxValue = currentValue
          idx = i
        } else if (currentValue === maxValue) {
          // 选择最后一个出现的最大值
          idx = i
        }
      })
      return idx
    },
    findMinIndex(arr = []) {
      let idx = 0
      let minValue = this.toNumber(arr[0])
      arr.forEach((v, i) => {
        const currentValue = this.toNumber(v)
        if (currentValue < minValue) {
          minValue = currentValue
          idx = i
        } else if (currentValue === minValue) {
          // 选择最后一个出现的最小值
          idx = i
        }
      })
      return idx
    },
    toggleMetricDisplayMode() {
      const modes = ['peak', 'valley', 'both']
      const currentIndex = modes.indexOf(this.metricDisplayMode)
      this.metricDisplayMode = modes[(currentIndex + 1) % modes.length]
    },
    getMetricDisplayModeText() {
      const modeMap = {
        peak: '峰值',
        valley: '谷值',
        both: '全部'
      }
      return modeMap[this.metricDisplayMode]
    },
    getSeries(key) {
      return this.months.map((m) => this.toNumber(this.currentDealer[metricKeys[key](m)]))
    },
    // 根据选择的时间范围获取数据
    getSeriesByTimeRange(key) {
      return this.filteredMonths.map((m) => this.toNumber(this.currentDealer[metricKeys[key](m)]))
    },
    initCharts() {
      this.charts.trend = echarts.init(this.$refs.trendChart)
      this.charts.funnel = echarts.init(this.$refs.funnelChart)
      this.charts.rate = echarts.init(this.$refs.rateChart)
      this.charts.responseTime = echarts.init(this.$refs.responseTimeChart)
      this.charts.policy = echarts.init(this.$refs.policyChart)
      this.charts.gsev = echarts.init(this.$refs.gsevChart)
      this.initReviewCharts()
    },
    renderCharts() {

      
      // 设置加载状态
      this.loading = true
      this.error = null
      
      try {
        // 模拟数据加载延迟，实际项目中可以根据真实数据加载时间调整
        setTimeout(() => {
          this.renderTrend()
          this.renderFunnel()
          this.renderRate()
          this.renderResponseTime()
          this.renderPolicy()
          this.renderGsev()
          this.renderReviewCharts()
          

          
          // 数据加载完成，设置加载状态为false
          this.loading = false
        }, 300)
      } catch (err) {
        // 处理错误
        this.error = '数据加载失败，请重试'
        this.loading = false
        console.error('Chart rendering error:', err)
      }
    },
    handleTimeRangeChange() {
      // 当时间范围变化时，重新渲染图表
      this.renderCharts()
    },
    renderTrend() {
      // 根据选择的时间范围获取数据
      const sales = this.getSeriesByTimeRange('销量')
      const traffic = this.getSeriesByTimeRange('客流量')
      const leads = this.getSeriesByTimeRange('线索量')
      const potential = this.getSeriesByTimeRange('潜客量')
      
      // 判断是否为月度时间范围
      const isMonthRange = this.timeRange === 'month'
      
      this.charts.trend.setOption({
        backgroundColor: 'transparent',
        // 专业的tooltip配置
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: {
            color: '#1f2937',
            fontSize: 14
          },
          padding: [10, 15],
          extraCssText: 'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);',
          formatter: function(params) {
            let result = params[0].name + '<br/>';
            // 为每个系列指定明确的颜色
            const seriesColors = {
              '销量': '#3b82f6',
              '客流量': '#8b5cf6',
              '线索量': '#f59e0b',
              '潜客量': '#10b981'
            };
            // 按照指定顺序显示：线索量、潜客量、客流量、销量
            const order = ['线索量', '潜客量', '客流量', '销量'];
            order.forEach(function(seriesName) {
              const item = params.find(p => p.seriesName === seriesName);
              if (item) {
                const color = seriesColors[item.seriesName] || item.color;
                result += '<span style="display:inline-block;margin-right:8px;border-radius:2px;width:12px;height:12px;background-color:' + color + '"></span>';
                result += item.seriesName + ': ' + item.value + '<br/>';
              }
            });
            return result;
          }
        },
        // 图例配置
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
          itemHeight: 12,
          selectedMode: 'multiple' // 允许用户选择显示/隐藏系列
        },
        // 右侧为图例预留空间，避免与图形重叠
        grid: { left: 50, right: 140, top: 40, bottom: 40 },
        // x轴配置
        xAxis: {
          type: 'category',
          data: this.filteredMonths,
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisLabel: { 
            color: '#6b7280',
            fontSize: 12,
            rotate: 0
          },
          axisTick: {
            alignWithLabel: true
          }
        },
        // y轴配置
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
          },
          axisTick: {
            show: false
          }
        },
        // 动画配置
        animation: true,
        animationDuration: 1000,
        animationEasing: 'cubicOut',
        animationDelay: function(idx) {
          return idx * 50;
        },
        // 系列配置
        series: [
          {
            name: '销量',
            type: 'bar',
            data: sales,
            barWidth: isMonthRange ? 35 : 14,
            color: '#3b82f6',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#3b82f6' },
                { offset: 1, color: '#2563eb' },
              ])
            },
            emphasis: {
              itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: '#60a5fa' },
                  { offset: 1, color: '#3b82f6' },
                ])
              }
            },
            // 数据标签
            label: {
              show: false,
              position: 'top',
              color: '#6b7280',
              fontSize: 10
            }
          },
          {
            name: '客流量',
            type: isMonthRange ? 'bar' : 'line',
            smooth: true,
            data: traffic,
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            barWidth: isMonthRange ? 35 : undefined,
            itemStyle: { 
              color: '#8b5cf6',
              borderWidth: isMonthRange ? 0 : 2,
              borderColor: '#fff'
            },
            lineStyle: {
              width: 3
            },
            areaStyle: isMonthRange ? undefined : {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(139, 92, 246, 0.3)' },
                { offset: 1, color: 'rgba(139, 92, 246, 0.05)' }
              ])
            },
            emphasis: {
              symbolSize: 8
            }
          },
          {
            name: '线索量',
            type: isMonthRange ? 'bar' : 'line',
            smooth: true,
            data: leads,
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            barWidth: isMonthRange ? 35 : undefined,
            itemStyle: { 
              color: '#f59e0b',
              borderWidth: isMonthRange ? 0 : 2,
              borderColor: '#fff'
            },
            lineStyle: {
              width: 3
            },
            emphasis: {
              symbolSize: 8
            }
          },
          {
            name: '潜客量',
            type: isMonthRange ? 'bar' : 'line',
            smooth: true,
            data: potential,
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            barWidth: isMonthRange ? 35 : undefined,
            itemStyle: { 
              color: '#10b981',
              borderWidth: isMonthRange ? 0 : 2,
              borderColor: '#fff'
            },
            lineStyle: {
              width: 3
            },
            areaStyle: isMonthRange ? undefined : {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
                { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
              ])
            },
            emphasis: {
              symbolSize: 8
            }
          },
        ],
      })
    },
    renderFunnel() {
      const avgTraffic = this.average(this.getSeriesByTimeRange('客流量'))
      const avgLeads = this.average(this.getSeriesByTimeRange('线索量'))
      const avgPotential = this.average(this.getSeriesByTimeRange('潜客量'))
      const avgSales = this.average(this.getSeriesByTimeRange('销量'))
      
      // 计算转化率
      const leadConversionRate = (avgLeads / avgTraffic * 100).toFixed(1)
      const potentialConversionRate = (avgPotential / avgLeads * 100).toFixed(1)
      const salesConversionRate = (avgSales / avgPotential * 100).toFixed(1)
      
      this.charts.funnel.setOption({
        backgroundColor: 'transparent',
        // 专业的tooltip配置
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: {
            color: '#1f2937',
            fontSize: 14
          },
          padding: [10, 15],
          extraCssText: 'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);',
          formatter: function(params) {
            let result = params.name + '<br/>';
            result += '平均数量: ' + params.value + '<br/>';
            
            // 添加转化率信息
            if (params.name === '线索') {
              result += '转化率: ' + leadConversionRate + '%<br/>';
            } else if (params.name === '潜客') {
              result += '转化率: ' + potentialConversionRate + '%<br/>';
            } else if (params.name === '成交（销量）') {
              result += '转化率: ' + salesConversionRate + '%<br/>';
            }
            
            return result;
          }
        },
        series: [
          {
            name: '漏斗',
            type: 'funnel',
            left: '10%',
            top: 20,
            bottom: 10,
            width: '80%',
            minSize: '0%',
            maxSize: '100%',
            gap: 8,
            sort: 'descending',
            // 标签配置
            label: {
              color: '#374151',
              fontSize: 14,
              fontWeight: '500',
              // 使用回调返回字符串，保证换行生效
              formatter: (params) => {
                let label = `${params.name}\n${params.value}`;
                // 添加转化率信息
                if (params.name === '线索') {
                  label += `\n${leadConversionRate}%`;
                } else if (params.name === '潜客') {
                  label += `\n${potentialConversionRate}%`;
                } else if (params.name === '成交（销量）') {
                  label += `\n${salesConversionRate}%`;
                }
                return label;
              },
            },
            // 标签线配置
            labelLine: {
              length: 10,
              lineStyle: {
                color: '#6b7280',
                width: 1,
                type: 'solid'
              }
            },
            // 项目样式
            itemStyle: {
              borderColor: '#fff',
              borderWidth: 2,
              borderRadius: [4, 4, 0, 0],
              shadowBlur: 5,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.1)'
            },
            // 强调样式
            emphasis: {
              label: {
                fontSize: 16,
                fontWeight: 'bold'
              },
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.2)'
              }
            },
            // 数据
            data: [
              { value: avgTraffic, name: '客流' },
              { value: avgLeads, name: '线索' },
              { value: avgPotential, name: '潜客' },
              { value: avgSales, name: '成交（销量）' },
            ],
            // 专业的配色方案 - 与销量趋势分析保持一致
            color: [
              new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: '#8b5cf6' },
                { offset: 1, color: '#6d28d9' },
              ]),
              new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: '#f59e0b' },
                { offset: 1, color: '#d97706' },
              ]),
              new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: '#10b981' },
                { offset: 1, color: '#059669' },
              ]),
              new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: '#3b82f6' },
                { offset: 1, color: '#2563eb' },
              ]),
            ],
          },
        ],
        // 动画配置
        animation: true,
        animationDuration: 1200,
        animationEasing: 'cubicOut',
        animationDelay: function(idx) {
          return idx * 200;
        }
      })
    },
    renderRate() {
      const rate = this.getSeriesByTimeRange('成交率').map((v) => this.toNumber(v) * 100)
      const defeat = this.getSeriesByTimeRange('战败率').map((v) => this.toNumber(v) * 100)
      
      // 判断是否为月度时间范围
      const isMonthRange = this.timeRange === 'month'
      
      this.charts.rate.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis', valueFormatter: (v) => `${v?.toFixed(1)}%` },
        legend: {
          data: ['成交率', '战败率'],
          top: 10,
          left: 'center',
          orient: 'horizontal',
          textStyle: { color: '#6b7280' },
        },
        // 图例在上方，调整grid以适应
        grid: { left: 30, right: 30, top: 40, bottom: 40 },
        xAxis: {
          type: 'category',
          data: this.filteredMonths,
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisLabel: { color: '#6b7280' },
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            formatter: '{value}%',
            color: '#6b7280',
          },
          splitLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.05)' } },
        },
        series: [
          {
            name: '成交率',
            type: isMonthRange ? 'bar' : 'line',
            smooth: true,
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            barWidth: isMonthRange ? 35 : undefined,
            data: rate,
            itemStyle: { color: '#10b981' },
            areaStyle: isMonthRange ? undefined : { color: 'rgba(16, 185, 129, 0.1)' },
          },
          {
            name: '战败率',
            type: isMonthRange ? 'bar' : 'line',
            smooth: true,
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            barWidth: isMonthRange ? 35 : undefined,
            data: defeat,
            itemStyle: { color: '#ef4444' },
            areaStyle: isMonthRange ? undefined : { color: 'rgba(239, 68, 68, 0.1)' },
          },
        ],
      })
    },
    average(arr = []) {
      if (!arr.length) return 0
      return arr.reduce((sum, v) => sum + this.toNumber(v), 0) / arr.length
    },
    renderResponseTime() {
      const successResponseTime = this.getSeriesByTimeRange('成交响应时间')
      const failureResponseTime = this.getSeriesByTimeRange('战败响应时间')
      const successAvg = this.average(successResponseTime)
      const failureAvg = this.average(failureResponseTime)
      const avgSuccessData = Array(this.filteredMonths.length).fill(successAvg)
      const avgFailureData = Array(this.filteredMonths.length).fill(failureAvg)
      
      // 判断是否为月度时间范围
      const isMonthRange = this.timeRange === 'month'
      
      this.charts.responseTime.setOption({
        backgroundColor: 'transparent',
        tooltip: { 
          trigger: 'axis',
          valueFormatter: (v) => `${v?.toFixed(1)}分钟`
        },
        legend: {
          data: ['成功响应时间', '失败响应时间', '成功响应平均数', '失败响应平均数'],
          top: 10,
          left: 'center',
          orient: 'horizontal',
          textStyle: { color: '#6b7280', fontSize: 12 },
          itemWidth: 25,
          itemGap: 15,
        },
        grid: { left: 30, right: 30, top: 90, bottom: 40 },
        xAxis: {
          type: 'category',
          data: this.filteredMonths,
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisLabel: { color: '#6b7280' },
        },
        yAxis: {
          type: 'value',
          name: '分钟',
          nameTextStyle: { color: '#6b7280' },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.05)' } },
          axisLabel: { color: '#6b7280' },
        },
        series: [
          {
            name: '成功响应时间',
            type: isMonthRange ? 'bar' : 'line',
            smooth: true,
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            barWidth: isMonthRange ? 35 : undefined,
            data: successResponseTime,
            itemStyle: { color: '#10b981' },
            areaStyle: isMonthRange ? undefined : { color: 'rgba(16, 185, 129, 0.1)' },
          },
          {
            name: '失败响应时间',
            type: isMonthRange ? 'bar' : 'line',
            smooth: true,
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            barWidth: isMonthRange ? 35 : undefined,
            data: failureResponseTime,
            itemStyle: { color: '#ef4444' },
            areaStyle: isMonthRange ? undefined : { color: 'rgba(239, 68, 68, 0.1)' },
          },
          {
            name: '成功响应平均数',
            type: isMonthRange ? 'bar' : 'line',
            barWidth: isMonthRange ? 35 : undefined,
            data: avgSuccessData,
            itemStyle: { 
              color: '#3b82f6',
              borderType: 'dashed'
            },
            lineStyle: { 
              type: 'dashed',
              width: 2
            },
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            emphasis: {
              focus: 'series'
            }
          },
          {
            name: '失败响应平均数',
            type: isMonthRange ? 'bar' : 'line',
            barWidth: isMonthRange ? 35 : undefined,
            data: avgFailureData,
            itemStyle: { 
              color: '#f59e0b',
              borderType: 'dashed'
            },
            lineStyle: { 
              type: 'dashed',
              width: 2
            },
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            emphasis: {
              focus: 'series'
            }
          },
        ],
      })
    },
    renderPolicy() {
      const policyData = this.getSeriesByTimeRange('政策')
      const policyAvg = this.average(policyData)
      const avgPolicyData = Array(this.filteredMonths.length).fill(policyAvg)
      
      // 判断是否为月度时间范围
      const isMonthRange = this.timeRange === 'month'
      
      this.charts.policy.setOption({
        backgroundColor: 'transparent',
        tooltip: { 
          trigger: 'axis',
          valueFormatter: (v) => `${v?.toFixed(1)}`
        },
        legend: {
          data: ['政策指标', '政策指标平均值'],
          top: 10,
          left: 'center',
          orient: 'horizontal',
          textStyle: { color: '#6b7280' },
        },
        grid: { left: 30, right: 30, top: 60, bottom: 40 },
        xAxis: {
          type: 'category',
          data: this.filteredMonths,
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisLabel: { color: '#6b7280' },
        },
        yAxis: {
          type: 'value',
          name: '政策值',
          nameTextStyle: { color: '#6b7280' },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.05)' } },
          axisLabel: { color: '#6b7280' },
        },
        series: [
          {
            name: '政策指标',
            type: isMonthRange ? 'bar' : 'line',
            smooth: true,
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            barWidth: isMonthRange ? 35 : undefined,
            data: policyData,
            itemStyle: { color: '#8b5cf6' },
            areaStyle: isMonthRange ? undefined : { color: 'rgba(139, 92, 246, 0.1)' },
          },
          {
            name: '政策指标平均值',
            type: isMonthRange ? 'bar' : 'line',
            barWidth: isMonthRange ? 35 : undefined,
            data: avgPolicyData,
            itemStyle: { 
              color: '#f59e0b',
              borderType: 'dashed'
            },
            lineStyle: { 
              type: 'dashed',
              width: 2
            },
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            emphasis: {
              focus: 'series'
            }
          },
        ],
      })
    },
    renderGsev() {
      const gsevData = this.getSeriesByTimeRange('GSEV')
      const gsevAvg = this.average(gsevData)
      const avgGsevData = Array(this.filteredMonths.length).fill(gsevAvg)
      
      // 计算Y轴范围，突出显示变化
      const minValue = Math.min(...gsevData) * 0.99
      const maxValue = Math.max(...gsevData) * 1.01
      
      // 判断是否为月度时间范围
      const isMonthRange = this.timeRange === 'month'
      
      this.charts.gsev.setOption({
        backgroundColor: 'transparent',
        tooltip: { 
          trigger: 'axis',
          valueFormatter: (v) => `${v?.toFixed(1)}`
        },
        legend: {
          data: ['GSEV', 'GSEV平均值'],
          top: 10,
          left: 'center',
          orient: 'horizontal',
          textStyle: { color: '#6b7280' },
        },
        grid: { left: 30, right: 30, top: 60, bottom: 40 },
        xAxis: {
          type: 'category',
          data: this.filteredMonths,
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisLabel: { color: '#6b7280' },
        },
        yAxis: {
          type: 'value',
          name: 'GSEV',
          nameTextStyle: { color: '#6b7280' },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.05)' } },
          axisLabel: { color: '#6b7280' },
          min: minValue,
          max: maxValue,
          axisLabel: {
            color: '#6b7280',
            formatter: (value) => value.toFixed(0)
          }
        },
        series: [
          {
            name: 'GSEV',
            type: isMonthRange ? 'bar' : 'line',
            smooth: true,
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 8,
            barWidth: isMonthRange ? 35 : undefined,
            data: gsevData,
            itemStyle: { 
              color: '#10b981',
              borderWidth: isMonthRange ? 0 : 2,
              borderColor: '#fff'
            },
            lineStyle: {
              width: 3,
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: '#10b981' },
                { offset: 1, color: '#059669' }
              ])
            },
            areaStyle: isMonthRange ? undefined : {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(16, 185, 129, 0.2)' },
                { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
              ])
            }
          },
          {
            name: 'GSEV平均值',
            type: isMonthRange ? 'bar' : 'line',
            barWidth: isMonthRange ? 35 : undefined,
            data: avgGsevData,
            itemStyle: { 
              color: '#f59e0b',
              borderType: 'dashed'
            },
            lineStyle: { 
              type: 'dashed',
              width: 2
            },
            symbol: isMonthRange ? 'none' : 'circle',
            symbolSize: 6,
            emphasis: {
              focus: 'series'
            }
          },
        ],
      })
    },
    initReviewCharts() {
      this.charts.reviewCharts = []
      if (this.$refs.reviewCharts) {
        const chartElements = Array.isArray(this.$refs.reviewCharts) ? this.$refs.reviewCharts : [this.$refs.reviewCharts]
        chartElements.forEach(element => {
          if (element) {
            const chart = echarts.init(element)
            this.charts.reviewCharts.push(chart)
          }
        })
      }
    },
    renderReviewCharts() {
      this.months.forEach((month, index) => {
        const chart = this.charts.reviewCharts[index]
        if (!chart) return
        
        const reviewCount = this.toNumber(this.currentDealer[metricKeys.评价数(month)])
        const goodCount = this.toNumber(this.currentDealer[metricKeys.好评数(month)])
        const badCount = this.toNumber(this.currentDealer[metricKeys.差评数(month)])
        
        // 如果没有评价数据，显示空状态
        if (!reviewCount && !goodCount && !badCount) {
          chart.setOption({
            backgroundColor: 'transparent',
            title: {
              text: '暂无数据',
              left: 'center',
              top: 'center',
              textStyle: {
                color: '#9ca3af',
                fontSize: 12
              }
            },
            series: []
          })
          return
        }
        
        // 使用实际的评价总数计算百分比
        const actualReviewCount = reviewCount || (goodCount + badCount)
        const goodPercent = actualReviewCount > 0 ? (goodCount / actualReviewCount * 100).toFixed(1) : 0
        const badPercent = actualReviewCount > 0 ? (badCount / actualReviewCount * 100).toFixed(1) : 0
        
        chart.setOption({
          backgroundColor: 'transparent',
          title: {
            text: ''
          },
          tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e5e7eb',
            borderWidth: 1,
            textStyle: {
              color: '#1f2937',
              fontSize: 12
            },
            padding: [8, 12],
            extraCssText: 'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);',
            position: function (point, params, dom, rect, size) {
              const x = point[0]
              const y = point[1]
              const boxWidth = size.contentSize[0]
              const boxHeight = size.contentSize[1]
              const posX = x + boxWidth > size.viewSize[0] ? x - boxWidth - 10 : x + 10
              const posY = y + boxHeight > size.viewSize[1] ? y - boxHeight - 10 : y + 10
              return [posX, posY]
            },
            confine: true
          },
          series: [
            {
              name: '评价占比',
              type: 'pie',
              radius: ['30%', '50%'],
              center: ['50%', '45%'],
              avoidLabelOverlap: true,
              itemStyle: {
                borderRadius: 10,
                borderColor: '#fff',
                borderWidth: 2
              },
              label: {
                show: true,
                formatter: '{b}\n{d}%',
                color: '#6b7280',
                fontSize: 11,
                position: 'outside',
                distance: 5,
                align: 'center',
                verticalAlign: 'middle'
              },
              labelLine: {
                show: true,
                length: 5,
                length2: 10,
                smooth: true
              },
              emphasis: {
                label: {
                  show: true,
                  fontSize: 14,
                  fontWeight: 'bold'
                },
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.1)'
                }
              },
              data: [
                { value: goodCount, name: '好评', itemStyle: { color: '#10b981' } },
                { value: badCount, name: '差评', itemStyle: { color: '#ef4444' } }
              ]
            }
          ]
        }, true)
      })
    },
    handleResize() {
      // 处理单个图表
      Object.keys(this.charts).forEach((key) => {
        if (key !== 'reviewCharts' && this.charts[key]) {
          this.charts[key].resize()
        }
      })
      // 处理reviewCharts数组
      if (Array.isArray(this.charts.reviewCharts)) {
        this.charts.reviewCharts.forEach((c) => c && c.resize())
      }
    },
    // 切换导出下拉菜单
    toggleExportDropdown() {
      this.showExportDropdown = !this.showExportDropdown
      // 点击其他地方关闭下拉菜单
      setTimeout(() => {
        document.addEventListener('click', this.closeExportDropdown)
      }, 100)
      // 关闭菜单时清空卡片选中状态
      if (!this.showExportDropdown) {
        this.selectedCards = []
      }
    },
    // 关闭导出下拉菜单
    closeExportDropdown(event) {
      // 如果点击的是卡片复选框或卡片包装器，不关闭菜单
      if (event.target.closest('.card-checkbox') || event.target.closest('.card-wrapper')) {
        return
      }
      
      if (!event.target.closest('.dropdown')) {
        this.showExportDropdown = false
        this.showAllExportSubmenu = false
        this.showSelectedExportSubmenu = false
        document.removeEventListener('click', this.closeExportDropdown)
        // 关闭菜单时清空卡片选中状态
        this.selectedCards = []
      }
    },
    // 切换全部导出子菜单
    toggleAllExportSubmenu() {
      this.showAllExportSubmenu = !this.showAllExportSubmenu
      this.showSelectedExportSubmenu = false
    },
    // 切换部分导出子菜单
    toggleSelectedExportSubmenu() {
      this.showSelectedExportSubmenu = !this.showSelectedExportSubmenu
      this.showAllExportSubmenu = false
    },
    // 导出数据
    exportData(format, scope = 'all') {
      this.showExportDropdown = false
      this.showAllExportSubmenu = false
      this.showSelectedExportSubmenu = false
      
      // 如果是导出选中卡片，但没有选中任何卡片，提示用户
      if (scope === 'selected' && this.selectedCards.length === 0) {
        alert('请先选择要导出的卡片！')
        return
      }
      
      // 数据导出过程
      this.loading = true
      
      try {
        console.log(`Exporting data as ${format}, scope: ${scope}...`)
        
        // 准备导出数据
        const exportData = this.prepareExportData(scope)
        console.log('Export data prepared:', exportData)
        
        if (format === 'csv') {
          // 导出为CSV格式
          this.exportToCSV(exportData, scope)
          alert(`CSV格式数据已成功导出！`)
        } else if (format === 'excel') {
          // 导出为Excel格式
          this.exportToExcel(exportData, scope)
          alert(`Excel格式数据已成功导出！`)
        } else if (format === 'pdf') {
          // 导出为PDF格式
          this.exportToPDF(exportData, scope)
          alert(`PDF格式数据已成功导出！`)
        }
        
        // 导出成功后清空卡片选中状态
        this.selectedCards = []
      } catch (error) {
        console.error('Export error:', error)
        this.error = '数据导出失败，请重试'
        alert(`数据导出失败：${error.message}`)
      } finally {
        this.loading = false
      }
    },
    // 导出为Excel格式
    exportToExcel(dataObj, scope = 'all') {
      try {
        console.log('Exporting to Excel...')
        
        // 创建Excel XML内容
        let excelContent = `<?xml version="1.0" encoding="UTF-8"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
  xmlns:o="urn:schemas-microsoft-com:office:office"
  xmlns:x="urn:schemas-microsoft-com:office:excel"
  xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
  xmlns:html="http://www.w3.org/TR/REC-html40">`
        
        // 添加主数据工作表
        if (dataObj.mainData && dataObj.mainData.length > 0) {
          excelContent += `
  <Worksheet ss:Name="销售数据">
    <Table>`
          dataObj.mainData.forEach((row) => {
            excelContent += `<Row>`
            row.forEach((cell) => {
              excelContent += `<Cell>`
              excelContent += `<Data ss:Type="String">${cell}</Data>`
              excelContent += `</Cell>`
            })
            excelContent += `</Row>`
          })
          excelContent += `    </Table>
  </Worksheet>`
        }
        
        // 添加核心指标工作表
        if (dataObj.metricsData && dataObj.metricsData.length > 0) {
          excelContent += `
  <Worksheet ss:Name="核心指标">
    <Table>`
          dataObj.metricsData.forEach((row) => {
            excelContent += `<Row>`
            row.forEach((cell) => {
              excelContent += `<Cell>`
              excelContent += `<Data ss:Type="String">${cell}</Data>`
              excelContent += `</Cell>`
            })
            excelContent += `</Row>`
          })
          excelContent += `    </Table>
  </Worksheet>`
        }
        
        // 添加销售漏斗工作表
        if (dataObj.funnelData && dataObj.funnelData.length > 0) {
          excelContent += `
  <Worksheet ss:Name="销售漏斗">
    <Table>`
          dataObj.funnelData.forEach((row) => {
            excelContent += `<Row>`
            row.forEach((cell) => {
              excelContent += `<Cell>`
              excelContent += `<Data ss:Type="String">${cell}</Data>`
              excelContent += `</Cell>`
            })
            excelContent += `</Row>`
          })
          excelContent += `    </Table>
  </Worksheet>`
        }
        
        // 闭合标签
        excelContent += `
</Workbook>`
        
        console.log('Excel content generated:', excelContent.substring(0, 100) + '...')
        
        // 创建Blob对象
        const blob = new Blob([excelContent], { type: 'application/vnd.ms-excel' })
        console.log('Blob created:', blob)
        
        // 创建下载链接
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        console.log('URL created:', url)
        
        // 设置下载属性
        const dealerName = this.currentDealer['经销商名称'] || '全部'
        const scopeText = scope === 'selected' ? this.getSelectedCardsNames() : '全部数据'
        const fileName = `销售数据_${scopeText}_${dealerName}_${new Date().toISOString().slice(0, 10)}.xls`
        link.setAttribute('href', url)
        link.setAttribute('download', fileName)
        link.style.visibility = 'hidden'
        console.log('Download link prepared:', fileName)
        
        // 添加到DOM并触发下载
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        console.log('Excel export completed successfully')
      } catch (error) {
        console.error('Error exporting to Excel:', error)
        throw error
      }
    },
    // 导出为PDF格式
    exportToPDF(dataObj, scope = 'all') {
      try {
        console.log('Exporting to PDF...')
        
        // 创建HTML内容
        let htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>销售数据报告</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 20px;
    }
    h1 {
      text-align: center;
      color: #333;
    }
    h2 {
      color: #555;
      margin-top: 30px;
      border-bottom: 2px solid #1890ff;
      padding-bottom: 5px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      margin-bottom: 30px;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 8px;
      text-align: left;
    }
    th {
      background-color: #f2f2f2;
      font-weight: bold;
    }
    tr:nth-child(even) {
      background-color: #f9f9f9;
    }
    .footer {
      margin-top: 20px;
      text-align: right;
      font-size: 12px;
      color: #666;
    }
    .section {
      page-break-inside: avoid;
    }
  </style>
</head>
<body>
  <h1>销售数据报告</h1>
  <p>经销商：${this.currentDealer['经销商名称'] || '全部'}</p>
  <p>导出日期：${new Date().toLocaleString()}</p>
`
        
        // 添加主数据表
        if (dataObj.mainData && dataObj.mainData.length > 0) {
          htmlContent += `
  <div class="section">
    <h2>销售数据</h2>
    <table>
      <tr>`
          dataObj.mainData[0].forEach(header => {
            htmlContent += `<th>${header}</th>`
          })
          htmlContent += `</tr>
`
          for (let i = 1; i < dataObj.mainData.length; i++) {
            htmlContent += `      <tr>`
            dataObj.mainData[i].forEach(cell => {
              htmlContent += `<td>${cell}</td>`
            })
            htmlContent += `</tr>
`
          }
          htmlContent += `    </table>
  </div>
`
        }
        
        // 添加核心指标表
        if (dataObj.metricsData && dataObj.metricsData.length > 0) {
          htmlContent += `
  <div class="section">
    <h2>核心指标</h2>
    <table>
      <tr>`
          dataObj.metricsData[0].forEach(header => {
            htmlContent += `<th>${header}</th>`
          })
          htmlContent += `</tr>
`
          for (let i = 1; i < dataObj.metricsData.length; i++) {
            htmlContent += `      <tr>`
            dataObj.metricsData[i].forEach(cell => {
              htmlContent += `<td>${cell}</td>`
            })
            htmlContent += `</tr>
`
          }
          htmlContent += `    </table>
  </div>
`
        }
        
        // 添加销售漏斗表
        if (dataObj.funnelData && dataObj.funnelData.length > 0) {
          htmlContent += `
  <div class="section">
    <h2>销售漏斗</h2>
    <table>
      <tr>`
          dataObj.funnelData[0].forEach(header => {
            htmlContent += `<th>${header}</th>`
          })
          htmlContent += `</tr>
`
          for (let i = 1; i < dataObj.funnelData.length; i++) {
            htmlContent += `      <tr>`
            dataObj.funnelData[i].forEach(cell => {
              htmlContent += `<td>${cell}</td>`
            })
            htmlContent += `</tr>
`
          }
          htmlContent += `    </table>
  </div>
`
        }
        
        // 闭合标签
        htmlContent += `  <div class="footer">
    报告生成时间：${new Date().toLocaleString()}
  </div>
</body>
</html>
`
        
        console.log('HTML content generated for PDF:', htmlContent.substring(0, 100) + '...')
        
        // 创建Blob对象
        const blob = new Blob([htmlContent], { type: 'text/html' })
        console.log('Blob created:', blob)
        
        // 创建下载链接
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        console.log('URL created:', url)
        
        // 设置下载属性
        const dealerName = this.currentDealer['经销商名称'] || '全部'
        const scopeText = scope === 'selected' ? this.getSelectedCardsNames() : '全部数据'
        const fileName = `销售数据报告_${scopeText}_${dealerName}_${new Date().toISOString().slice(0, 10)}.html`
        link.setAttribute('href', url)
        link.setAttribute('download', fileName)
        link.style.visibility = 'hidden'
        console.log('Download link prepared:', fileName)
        
        // 添加到DOM并触发下载
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        // 提示用户在浏览器中打开HTML文件并打印为PDF
        setTimeout(() => {
          alert('HTML格式报告已导出，请在浏览器中打开该文件并使用打印功能保存为PDF格式。')
        }, 500)
        
        console.log('PDF export completed successfully')
      } catch (error) {
        console.error('Error exporting to PDF:', error)
        throw error
      }
    },
    // 准备导出数据（支持多表格）
    prepareExportData(scope = 'all') {
      try {
        // 返回一个对象，包含多个数据表
        const result = {
          mainData: [],      // 主数据表（按月份）
          metricsData: [],   // 核心指标数据
          funnelData: []     // 销售漏斗数据
        }
        
        if (scope === 'all') {
          // 导出全部数据 - 按月份导出主数据
          const columns = ['月份', '销量', '客流量', '线索量', '潜客量', '成交率', '战败率', '成交响应时间', '战败响应时间', '政策指标', 'GSEV', '评价数', '好评数', '差评数']
          result.mainData.push(columns)
          
          this.filteredMonths.forEach((month, index) => {
            const row = [
              month,
              this.getSeriesByTimeRange('销量')[index] || 0,
              this.getSeriesByTimeRange('客流量')[index] || 0,
              this.getSeriesByTimeRange('线索量')[index] || 0,
              this.getSeriesByTimeRange('潜客量')[index] || 0,
              this.getSeriesByTimeRange('成交率')[index] || 0,
              this.getSeriesByTimeRange('战败率')[index] || 0,
              this.getSeriesByTimeRange('成交响应时间')[index] || 0,
              this.getSeriesByTimeRange('战败响应时间')[index] || 0,
              this.getSeriesByTimeRange('政策')[index] || 0,
              this.getSeriesByTimeRange('GSEV')[index] || 0,
              this.getSeriesByTimeRange('评价数')[index] || 0,
              this.getSeriesByTimeRange('好评数')[index] || 0,
              this.getSeriesByTimeRange('差评数')[index] || 0
            ]
            result.mainData.push(row)
          })
          
          // 全部导出时，也单独处理核心指标
          result.metricsData.push(['指标', '显示值', '最佳月份', '最差月份'])
          
          const metrics = [
            { key: '销量', unit: '辆' },
            { key: '客流量', unit: '人次' },
            { key: '线索量', unit: '条' },
            { key: '潜客量', unit: '人' },
          ]
          
          metrics.forEach((m) => {
            const series = this.months.map((mo) => this.toNumber(this.currentDealer[metricKeys[m.key](mo)]))
            const peakIdx = this.findMaxIndex(series)
            const valleyIdx = this.findMinIndex(series)
            
            let display = ''
            let bestMonth = ''
            let worstMonth = ''
            
            if (this.metricDisplayMode === 'peak') {
              const peakValue = series[peakIdx]
              display = m.key.includes('率')
                ? `${(peakValue * 100 || 0).toFixed(1)}${m.unit}`
                : `${this.formatNumber(peakValue)}${m.unit}`
              bestMonth = this.months[peakIdx] || '-'
              worstMonth = '-'
            } else if (this.metricDisplayMode === 'valley') {
              const valleyValue = series[valleyIdx]
              display = m.key.includes('率')
                ? `${(valleyValue * 100 || 0).toFixed(1)}${m.unit}`
                : `${this.formatNumber(valleyValue)}${m.unit}`
              bestMonth = '-'
              worstMonth = this.months[valleyIdx] || '-'
            } else if (this.metricDisplayMode === 'both') {
              const peakValue = series[peakIdx]
              const valleyValue = series[valleyIdx]
              const peakDisplay = m.key.includes('率')
                ? `${(peakValue * 100 || 0).toFixed(1)}${m.unit}`
                : `${this.formatNumber(peakValue)}${m.unit}`
              const valleyDisplay = m.key.includes('率')
                ? `${(valleyValue * 100 || 0).toFixed(1)}${m.unit}`
                : `${this.formatNumber(valleyValue)}${m.unit}`
              display = `${peakDisplay} / ${valleyDisplay}`
              bestMonth = this.months[peakIdx] || '-'
              worstMonth = this.months[valleyIdx] || '-'
            }
            
            result.metricsData.push([m.key, display, bestMonth, worstMonth])
          })
          
          // 全部导出时，也单独处理销售漏斗
          result.funnelData.push(['类型', '销量', '客流量', '线索量', '潜客量', '线索转化率', '潜客转化率', '成交转化率'])
          
          const salesData = this.getSeriesByTimeRange('销量')
          const trafficData = this.getSeriesByTimeRange('客流量')
          const leadsData = this.getSeriesByTimeRange('线索量')
          const potentialData = this.getSeriesByTimeRange('潜客量')
          
          const avgSales = this.average(salesData)
          const avgTraffic = this.average(trafficData)
          const avgLeads = this.average(leadsData)
          const avgPotential = this.average(potentialData)
          
          const leadConversionRate = avgTraffic > 0 ? ((avgLeads / avgTraffic) * 100).toFixed(1) : 0
          const potentialConversionRate = avgLeads > 0 ? ((avgPotential / avgLeads) * 100).toFixed(1) : 0
          const salesConversionRate = avgPotential > 0 ? ((avgSales / avgPotential) * 100).toFixed(1) : 0
          
          result.funnelData.push(['均值', avgSales.toFixed(1), avgTraffic.toFixed(1), avgLeads.toFixed(1), avgPotential.toFixed(1), leadConversionRate + '%', potentialConversionRate + '%', salesConversionRate + '%'])
        } else {
          // 选中卡片导出
          const hasMetrics = this.selectedCards.includes('metrics')
          const hasFunnel = this.selectedCards.includes('funnel')
          const otherCards = this.selectedCards.filter(id => id !== 'metrics' && id !== 'funnel')
          
          // 处理核心指标 - 直接使用页面显示的数据
          if (hasMetrics) {
            result.metricsData.push(['指标', '显示值', '最佳月份', '最差月份'])
            
            // 使用 headlineMetrics 计算属性，确保与页面显示一致
            this.headlineMetrics.forEach((metric) => {
              const bestMonth = metric.bestMonth || '-'
              const worstMonth = metric.worstMonth || '-'
              result.metricsData.push([metric.label, metric.display, bestMonth, worstMonth])
            })
          }
          
          // 处理销售漏斗
          if (hasFunnel) {
            result.funnelData.push(['类型', '销量', '客流量', '线索量', '潜客量', '线索转化率', '潜客转化率', '成交转化率'])
            
            const salesData = this.getSeriesByTimeRange('销量')
            const trafficData = this.getSeriesByTimeRange('客流量')
            const leadsData = this.getSeriesByTimeRange('线索量')
            const potentialData = this.getSeriesByTimeRange('潜客量')
            
            const avgSales = this.average(salesData)
            const avgTraffic = this.average(trafficData)
            const avgLeads = this.average(leadsData)
            const avgPotential = this.average(potentialData)
            
            const leadConversionRate = avgTraffic > 0 ? ((avgLeads / avgTraffic) * 100).toFixed(1) : 0
            const potentialConversionRate = avgLeads > 0 ? ((avgPotential / avgLeads) * 100).toFixed(1) : 0
            const salesConversionRate = avgPotential > 0 ? ((avgSales / avgPotential) * 100).toFixed(1) : 0
            
            result.funnelData.push(['均值', avgSales.toFixed(1), avgTraffic.toFixed(1), avgLeads.toFixed(1), avgPotential.toFixed(1), leadConversionRate + '%', potentialConversionRate + '%', salesConversionRate + '%'])
          }
          
          // 处理其他卡片（按月份）
          if (otherCards.length > 0) {
            const columns = ['月份']
            
            if (otherCards.includes('trend') || otherCards.includes('snapshot')) {
              columns.push('销量', '客流量', '线索量', '潜客量', '成交率')
            }
            if (otherCards.includes('rate')) {
              columns.push('成交率', '战败率')
            }
            if (otherCards.includes('responseTime')) {
              columns.push('成交响应时间', '战败响应时间')
            }
            if (otherCards.includes('policy')) {
              columns.push('政策指标')
            }
            if (otherCards.includes('gsev')) {
              columns.push('GSEV')
            }
            if (otherCards.includes('review')) {
              columns.push('评价数', '好评数', '差评数')
            }
            
            result.mainData.push(columns)
            
            this.filteredMonths.forEach((month, index) => {
              const row = [month]
              
              columns.slice(1).forEach(column => {
                switch (column) {
                  case '销量':
                    row.push(this.getSeriesByTimeRange('销量')[index] || 0)
                    break
                  case '客流量':
                    row.push(this.getSeriesByTimeRange('客流量')[index] || 0)
                    break
                  case '线索量':
                    row.push(this.getSeriesByTimeRange('线索量')[index] || 0)
                    break
                  case '潜客量':
                    row.push(this.getSeriesByTimeRange('潜客量')[index] || 0)
                    break
                  case '成交率':
                    row.push(this.getSeriesByTimeRange('成交率')[index] || 0)
                    break
                  case '战败率':
                    row.push(this.getSeriesByTimeRange('战败率')[index] || 0)
                    break
                  case '成交响应时间':
                    row.push(this.getSeriesByTimeRange('成交响应时间')[index] || 0)
                    break
                  case '战败响应时间':
                    row.push(this.getSeriesByTimeRange('战败响应时间')[index] || 0)
                    break
                  case '政策指标':
                    row.push(this.getSeriesByTimeRange('政策')[index] || 0)
                    break
                  case 'GSEV':
                    row.push(this.getSeriesByTimeRange('GSEV')[index] || 0)
                    break
                  case '评价数':
                    row.push(this.getSeriesByTimeRange('评价数')[index] || 0)
                    break
                  case '好评数':
                    row.push(this.getSeriesByTimeRange('好评数')[index] || 0)
                    break
                  case '差评数':
                    row.push(this.getSeriesByTimeRange('差评数')[index] || 0)
                    break
                }
              })
              
              result.mainData.push(row)
            })
          }
        }
        
        console.log('Prepared export data:', result)
        return result
      } catch (error) {
        console.error('Error preparing export data:', error)
        throw error
      }
    },
    // 准备导出数据（旧版本，保持兼容）
    prepareExportDataOld(scope = 'all') {
      try {
        // 从当前经销商数据中提取需要导出的数据
        const data = []
        
        // 根据导出范围确定要导出的列
        let columns = []
        
        if (scope === 'all') {
          // 导出全部数据
          columns = ['月份', '销量', '客流量', '线索量', '潜客量', '成交率', '战败率', '成交响应时间', '战败响应时间', '政策指标', 'GSEV', '评价数', '好评数', '差评数']
        } else {
          // 检查是否只选择了关键数值卡片
          if (this.selectedCards.length === 1 && this.selectedCards.includes('metrics')) {
            // 关键数值：根据显示模式导出峰值、谷值或两者
            columns = ['指标', '显示值', '最佳月份', '最差月份']
          } else if (this.selectedCards.length === 1 && this.selectedCards.includes('funnel')) {
            // 销售漏斗：导出均值数据
            columns = ['类型', '销量', '客流量', '线索量', '潜客量', '线索转化率', '潜客转化率', '成交转化率']
          } else {
            // 其他情况：确保所有导出的数据都包含月份标识
            columns.push('月份')
            
            // 根据选中的卡片确定要导出的列
            if (this.selectedCards.includes('trend') || this.selectedCards.includes('snapshot')) {
              columns.push('销量', '客流量', '线索量', '潜客量', '成交率')
            }
            if (this.selectedCards.includes('funnel')) {
              columns.push('销量', '客流量', '线索量', '潜客量', '线索转化率', '潜客转化率', '成交转化率')
            }
            if (this.selectedCards.includes('rate')) {
              columns.push('成交率', '战败率')
            }
            if (this.selectedCards.includes('responseTime')) {
              columns.push('成交响应时间', '战败响应时间')
            }
            if (this.selectedCards.includes('policy')) {
              columns.push('政策指标')
            }
            if (this.selectedCards.includes('gsev')) {
              columns.push('GSEV')
            }
            if (this.selectedCards.includes('review')) {
              columns.push('评价数', '好评数', '差评数')
            }
            // 如果没有选中任何卡片，默认导出全部
            if (columns.length === 1) {
              columns = ['月份', '销量', '客流量', '线索量', '潜客量', '成交率', '战败率', '成交响应时间', '战败响应时间', '政策指标', 'GSEV', '评价数', '好评数', '差评数']
            }
          }
        }
        
        // 添加表头
        data.push(columns)
        
        // 添加数据行
        if (this.selectedCards.length === 1 && this.selectedCards.includes('metrics')) {
          // 关键数值：导出指标的峰值、谷值或两者
          const metrics = [
            { key: '销量', unit: '辆' },
            { key: '客流量', unit: '人次' },
            { key: '线索量', unit: '条' },
            { key: '潜客量', unit: '人' },
          ]
          
          metrics.forEach((m) => {
            const series = this.months.map((mo) => this.toNumber(this.currentDealer[metricKeys[m.key](mo)]))
            const peakIdx = this.findMaxIndex(series)
            const valleyIdx = this.findMinIndex(series)
            
            let display = ''
            let bestMonth = ''
            let worstMonth = ''
            
            if (this.metricDisplayMode === 'peak') {
              const peakValue = series[peakIdx]
              display = m.key.includes('率')
                ? `${(peakValue * 100 || 0).toFixed(1)}${m.unit}`
                : `${this.formatNumber(peakValue)}${m.unit}`
              bestMonth = this.months[peakIdx] || '-'
              worstMonth = '-'
            } else if (this.metricDisplayMode === 'valley') {
              const valleyValue = series[valleyIdx]
              display = m.key.includes('率')
                ? `${(valleyValue * 100 || 0).toFixed(1)}${m.unit}`
                : `${this.formatNumber(valleyValue)}${m.unit}`
              bestMonth = '-'
              worstMonth = this.months[valleyIdx] || '-'
            } else if (this.metricDisplayMode === 'both') {
              const peakValue = series[peakIdx]
              const valleyValue = series[valleyIdx]
              const peakDisplay = m.key.includes('率')
                ? `${(peakValue * 100 || 0).toFixed(1)}${m.unit}`
                : `${this.formatNumber(peakValue)}${m.unit}`
              const valleyDisplay = m.key.includes('率')
                ? `${(valleyValue * 100 || 0).toFixed(1)}${m.unit}`
                : `${this.formatNumber(valleyValue)}${m.unit}`
              display = `${peakDisplay} / ${valleyDisplay}`
              bestMonth = this.months[peakIdx] || '-'
              worstMonth = this.months[valleyIdx] || '-'
            }
            
            data.push([m.key, display, bestMonth, worstMonth])
          })
        } else if (this.selectedCards.length === 1 && this.selectedCards.includes('funnel')) {
          // 销售漏斗：导出四个量的均值
          const salesData = this.getSeriesByTimeRange('销量')
          const trafficData = this.getSeriesByTimeRange('客流量')
          const leadsData = this.getSeriesByTimeRange('线索量')
          const potentialData = this.getSeriesByTimeRange('潜客量')
          
          const avgSales = this.average(salesData)
          const avgTraffic = this.average(trafficData)
          const avgLeads = this.average(leadsData)
          const avgPotential = this.average(potentialData)
          
          // 计算转化率
          const leadConversionRate = avgTraffic > 0 ? ((avgLeads / avgTraffic) * 100).toFixed(1) : 0
          const potentialConversionRate = avgLeads > 0 ? ((avgPotential / avgLeads) * 100).toFixed(1) : 0
          const salesConversionRate = avgPotential > 0 ? ((avgSales / avgPotential) * 100).toFixed(1) : 0
          
          // 添加数据行
          data.push(['均值', avgSales.toFixed(1), avgTraffic.toFixed(1), avgLeads.toFixed(1), avgPotential.toFixed(1), leadConversionRate + '%', potentialConversionRate + '%', salesConversionRate + '%'])
        } else {
          // 其他卡片：按月份导出数据
          this.filteredMonths.forEach((month, index) => {
            const row = []
            
            columns.forEach(column => {
              switch (column) {
                case '月份':
                  row.push(month)
                  break
                case '销量':
                  row.push(this.getSeriesByTimeRange('销量')[index] || 0)
                  break
                case '客流量':
                  row.push(this.getSeriesByTimeRange('客流量')[index] || 0)
                  break
                case '线索量':
                  row.push(this.getSeriesByTimeRange('线索量')[index] || 0)
                  break
                case '潜客量':
                  row.push(this.getSeriesByTimeRange('潜客量')[index] || 0)
                  break
                case '线索转化率':
                  const traffic = this.getSeriesByTimeRange('客流量')[index] || 0
                  const leads = this.getSeriesByTimeRange('线索量')[index] || 0
                  row.push(traffic > 0 ? ((leads / traffic) * 100).toFixed(1) + '%' : '0%')
                  break
                case '潜客转化率':
                  const leadsData = this.getSeriesByTimeRange('线索量')[index] || 0
                  const potential = this.getSeriesByTimeRange('潜客量')[index] || 0
                  row.push(leadsData > 0 ? ((potential / leadsData) * 100).toFixed(1) + '%' : '0%')
                  break
                case '成交转化率':
                  const potentialData = this.getSeriesByTimeRange('潜客量')[index] || 0
                  const sales = this.getSeriesByTimeRange('销量')[index] || 0
                  row.push(potentialData > 0 ? ((sales / potentialData) * 100).toFixed(1) + '%' : '0%')
                  break
                case '成交率':
                  row.push(this.getSeriesByTimeRange('成交率')[index] || 0)
                  break
                case '战败率':
                  row.push(this.getSeriesByTimeRange('战败率')[index] || 0)
                  break
                case '成交响应时间':
                  row.push(this.getSeriesByTimeRange('成交响应时间')[index] || 0)
                  break
                case '战败响应时间':
                  row.push(this.getSeriesByTimeRange('战败响应时间')[index] || 0)
                  break
                case '政策指标':
                  row.push(this.getSeriesByTimeRange('政策')[index] || 0)
                  break
                case 'GSEV':
                  row.push(this.getSeriesByTimeRange('GSEV')[index] || 0)
                  break
                case '评价数':
                  row.push(this.getSeriesByTimeRange('评价数')[index] || 0)
                  break
                case '好评数':
                  row.push(this.getSeriesByTimeRange('好评数')[index] || 0)
                  break
                case '差评数':
                  row.push(this.getSeriesByTimeRange('差评数')[index] || 0)
                  break
                default:
                  row.push(0)
              }
            })
            
            data.push(row)
          })
        }
        
        console.log('Prepared export data:', data)
        return data
      } catch (error) {
        console.error('Error preparing export data:', error)
        throw error
      }
    },
    // 获取选中卡片的名称
    getSelectedCardsNames() {
      const cardNameMap = {
        'snapshot': '月度快照',
        'metrics': '核心指标',
        'trend': '销量趋势分析',
        'funnel': '销售漏斗',
        'rate': '成交战败率',
        'responseTime': '响应时间分析',
        'policy': '政策影响',
        'gsev': 'GSEV占比',
        'review': '好坏评占比'
      }
      
      return this.selectedCards.map(id => cardNameMap[id] || id).join('_')
    },
    // 导出为CSV格式
    exportToCSV(dataObj, scope = 'all') {
      try {
        console.log('Exporting to CSV...')
        
        let csvContent = ''
        
        // 处理主数据表
        if (dataObj.mainData && dataObj.mainData.length > 0) {
          csvContent += dataObj.mainData.map(row => row.join(',')).join('\n')
        }
        
        // 处理核心指标数据（单独一页）
        if (dataObj.metricsData && dataObj.metricsData.length > 0) {
          if (csvContent) csvContent += '\n\n=== 核心指标 ===\n'
          csvContent += dataObj.metricsData.map(row => row.join(',')).join('\n')
        }
        
        // 处理销售漏斗数据（单独一页）
        if (dataObj.funnelData && dataObj.funnelData.length > 0) {
          if (csvContent) csvContent += '\n\n=== 销售漏斗 ===\n'
          csvContent += dataObj.funnelData.map(row => row.join(',')).join('\n')
        }
        
        console.log('CSV content generated:', csvContent.substring(0, 100) + '...')
        
        // 创建Blob对象
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
        console.log('Blob created:', blob)
        
        // 创建下载链接
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        console.log('URL created:', url)
        
        // 设置下载属性
        const dealerName = this.currentDealer['经销商名称'] || '全部'
        const scopeText = scope === 'selected' ? this.getSelectedCardsNames() : '全部数据'
        const fileName = `销售数据_${scopeText}_${dealerName}_${new Date().toISOString().slice(0, 10)}.csv`
        link.setAttribute('href', url)
        link.setAttribute('download', fileName)
        link.style.visibility = 'hidden'
        console.log('Download link prepared:', fileName)
        
        // 添加到DOM并触发下载
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        console.log('CSV export completed successfully')
      } catch (error) {
        console.error('Error exporting to CSV:', error)
        throw error
      }
    },
    // 切换报告下拉菜单
    toggleReportDropdown() {
      this.showReportDropdown = !this.showReportDropdown
      // 关闭其他下拉菜单
      if (this.showReportDropdown) {
        this.showExportDropdown = false
        // 添加点击其他地方关闭下拉菜单的监听
        setTimeout(() => {
          document.addEventListener('click', this.closeReportDropdown)
        }, 100)
      } else {
        // 关闭菜单时清空卡片选中状态
        this.selectedCards = []
        document.removeEventListener('click', this.closeReportDropdown)
      }
    },
    // 关闭报告下拉菜单
    closeReportDropdown(event) {
      // 如果点击的是卡片复选框或卡片包装器，不关闭菜单
      if (event.target.closest('.card-checkbox') || event.target.closest('.card-wrapper')) {
        return
      }
      
      if (!event.target.closest('.dropdown')) {
        this.showReportDropdown = false
        document.removeEventListener('click', this.closeReportDropdown)
        // 关闭菜单时清空卡片选中状态
        this.selectedCards = []
      }
    },
    // 选择全部卡片
    selectAllCards() {
      const allCardIds = ['trend', 'funnel', 'snapshot', 'metrics', 'policy', 'rate', 'responseTime', 'gsev', 'review']
      
      if (this.isAllSelected) {
        this.selectedCards = []
      } else {
        this.selectedCards = [...allCardIds]
      }
    },
    // 根据选中的卡片生成报告
    generateReportFromSelection() {
      console.log('=== generateReportFromSelection 被调用 ===');
      console.log('选中的卡片:', this.selectedCards);
      
      if (this.selectedCards.length === 0) {
        alert('请至少选择一个卡片！')
        return
      }
      
      // 如果还没进入报告模式，自动进入
      if (!this.isReportMode) {
        this.isReportMode = true
      }
      
      console.log('开始提取卡片数据...');
      console.log('当前组件实例 this:', this);
      
      // 提取选中卡片的数据
      this.reportCardData = extractCardData(this, this.selectedCards)

      console.log('提取的卡片数据:', this.reportCardData);
      console.log('卡片数据的键:', Object.keys(this.reportCardData));
      console.log('卡片数据是否为空:', Object.keys(this.reportCardData).length === 0);
      
      // 显示报告模态框
      console.log('准备显示报告模态框...');
      this.showReportModal = true
      console.log('showReportModal 已设置为:', this.showReportModal);
      
      // 关闭下拉菜单并清空选中状态
      this.showReportDropdown = false
      this.selectedCards = []
      console.log('=== generateReportFromSelection 执行完成 ===');
    },
    
    // 关闭报告模态框
    closeReportModal() {
      this.showReportModal = false
      // 清空卡片选中状态
      this.selectedCards = []
    },
    // 切换卡片选择状态
    toggleCardSelection(cardId) {
      // 只在选择卡片状态下才响应点击事件
      if (!this.showExportDropdown && !this.showReportDropdown) {
        return
      }
      
  
      const index = this.selectedCards.indexOf(cardId)
      if (index > -1) {
        this.selectedCards.splice(index, 1)
  
      } else {
        this.selectedCards.push(cardId)
   
      }
    },
  },
}
</script>

<style scoped>
/* 自定义样式 */
.dashboard-container {
  width: 100%;
  overflow: hidden;
}

/* 卡片包装器和复选框样式 */
.card-wrapper {
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
}

/* 选中状态 */
.card-wrapper.card-selected {
  box-shadow: 0 0 0 3px #1890ff;
  border-radius: 8px;
}

/* 复选框容器 */
.card-checkbox {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
  background: white;
  border-radius: 4px;
  padding: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  display: none;
}

.card-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

/* 选择模式时显示复选框 */
.show-export-dropdown .card-checkbox,
.dashboard-container.show-export-dropdown .card-checkbox,
.dashboard-container.show-report-dropdown .card-checkbox {
  display: block;
}

/* 页面标题和操作按钮 */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 24px;
}

/* 加载状态样式 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease-in-out;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-text {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

/* 错误信息样式 */
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

.error-icon {
  font-size: 24px;
  color: #dc2626;
}

.error-content {
  flex: 1;
}

.error-message {
  font-size: 14px;
  color: #b91c1c;
  margin: 0 0 12px 0;
}

/* 动画效果 */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes cardSelect {
  0% { 
    transform: scale(1);
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2), 0 4px 6px -1px rgba(59, 130, 246, 0.1);
  }
  50% { 
    transform: scale(1.02);
    box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.3), 0 8px 12px -2px rgba(59, 130, 246, 0.15);
  }
  100% { 
    transform: scale(1);
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2), 0 4px 6px -1px rgba(59, 130, 246, 0.1);
  }
}

@keyframes checkboxPulse {
  0%, 100% { 
    transform: scale(1);
  }
  50% { 
    transform: scale(1.1);
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .header-controls {
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
  }
  
  .time-range-selector {
    flex-wrap: wrap;
  }
  
  .card-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .card-wide {
    grid-column: 1 / -1;
  }
  
  .reviews-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 12px;
  }
  
  .header-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-controls {
    width: 100%;
    align-items: stretch;
  }
  
  .button-group {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .btn {
    flex: 1;
    min-width: 120px;
  }
  
  .card-row {
    grid-template-columns: 1fr;
  }
  
  .card-row-2 {
    grid-template-columns: 1fr;
  }
  
  .card-row-4 {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .snapshot-item {
    grid-template-columns: repeat(3, 1fr);
    gap: 4px;
    font-size: 12px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .reviews-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .card-title {
    font-size: 14px;
  }
  
  .chart-container {
    height: 200px;
  }
  
  .chart-large {
    height: 250px;
  }
  
  .review-chart {
    height: 100px;
  }
}

@media (max-width: 480px) {
  .time-range-selector {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .time-range-select {
    width: 100%;
  }
  
  .card-row-4 {
    grid-template-columns: 1fr;
  }
  
  .reviews-grid {
    grid-template-columns: 1fr;
  }
  
  .snapshot-item {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .loading-container {
    padding: 20px;
  }
  
  .error-container {
    flex-direction: column;
    text-align: center;
  }
  
  .chart-container {
    height: 180px;
  }
  
  .chart-large {
    height: 220px;
  }
}

/* 下拉菜单样式 */
.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-toggle {
  position: relative;
  z-index: 2;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  z-index: 10;
  min-width: 160px;
  overflow: visible;
  animation: fadeIn 0.2s ease-in-out;
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  width: 100%;
  text-align: left;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
  transition: all 0.2s ease;
  position: relative;
}

.dropdown-item:hover {
  background-color: #f3f4f6;
  color: #1f2937;
}

.dropdown-item i {
  margin-right: 8px;
  font-size: 14px;
}

.dropdown-divider {
  height: 1px;
  background-color: #e5e7eb;
  margin: 4px 0;
}

/* 嵌套下拉菜单 */
.dropdown-submenu {
  position: relative;
  z-index: 9999;
}

.dropdown-submenu-menu {
  position: absolute;
  top: 0;
  right: 100%;
  margin-right: 4px;
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  z-index: 9999;
  min-width: 140px;
  overflow: visible;
  animation: fadeIn 0.2s ease-in-out;
  display: block;
  padding: 4px 0;
}

.dropdown-submenu-menu .dropdown-item {
  padding: 8px 16px;
  white-space: nowrap;
}

.dropdown-toggle {
  justify-content: space-between;
}

/* 响应式下拉菜单 */
@media (max-width: 768px) {
  .dropdown-menu {
    right: auto;
    left: 0;
    width: 100%;
  }
  
  .dropdown-item {
    justify-content: center;
    text-align: center;
  }
  
  .dropdown-submenu-menu {
    position: relative;
    top: 0;
    right: 0;
    left: 0;
    margin-top: 4px;
    margin-right: 0;
    border: none;
    border-radius: 0;
    box-shadow: none;
  }
}

.time-range-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time-range-label {
  font-size: 14px;
  color: #000000;
  font-weight: 500;
}

.time-range-select {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  border: 1px solid #e5e7eb;
  background-color: white;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s ease;
}

.time-range-select:hover {
  border-color: #d1d5db;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.time-range-select:focus {
  outline: none;
  ring: 2px solid #2563eb;
  ring-offset: 2px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e8e8e8;
}

.button-group {
  display: flex;
  gap: 8px;
}

/* 按钮样式 */
.btn {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  display: inline-flex;
  align-items: center;
}

.btn-gray {
  background-color: #f3f4f6;
  color: #374151;
}

.btn-gray:hover {
  background-color: #e5e7eb;
}

.btn-blue {
  background-color: #2563eb;
  color: white;
}

.btn-blue:hover {
  background-color: #1d4ed8;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 14px;
  background-color: #f3f4f6;
  color: #374151;
}

.btn-sm:hover {
  background-color: #e5e7eb;
}

/* 卡片样式 */
.card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 0;
  position: relative;
  border: 2px solid transparent;
  box-sizing: border-box;
}

/* 卡片选中框 */
.card-checkbox {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 100;
  pointer-events: auto;
  display: none;
}

.show-export-dropdown .card-checkbox {
  display: block;
}

.card-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  pointer-events: auto;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  background-color: white;
  transition: all 0.2s ease;
}

.card-checkbox input[type="checkbox"]:checked {
  background-color: #3b82f6;
  border-color: #3b82f6;
}

.card-checkbox input[type="checkbox"]:hover {
  border-color: #3b82f6;
}

.card-checkbox input[type="checkbox"]:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
}

/* 卡片抖动动画 */
@keyframes swing {
  0%, 100% { transform: translateZ(0); }
  50% { transform: translateZ(20px); }
}

.card-shake {
  animation: swing 0.8s ease-in-out infinite;
  cursor: pointer;
  transform-style: preserve-3d;
  perspective: 1000px;
}

.card-selected {
  border: 2px solid #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2), 0 4px 6px -1px rgba(59, 130, 246, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  animation: cardSelect 0.4s ease-out;
}

.card-selected::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05));
  pointer-events: none;
  z-index: -1;
}

.card-selected .card-header {
  background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
  border-bottom-color: #3b82f6;
}

.card-selected .card-title {
  color: #1e40af;
}

.card-selected .card-checkbox input[type="checkbox"]:checked {
  animation: checkboxPulse 0.3s ease-out;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.card-body {
  padding: 16px;
}

/* 经销商选择器样式 */
.dealer-selector {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

/* 卡片行布局 */
.card-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.card-row-2 {
  grid-template-columns: repeat(2, 1fr);
}

.card-row-4 {
  grid-template-columns: repeat(4, 1fr);
}

.card-wide {
  grid-column: span 2;
}

.card-full {
  grid-column: 1 / -1;
}

/* 企业级卡片样式增强 */
.card {
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
}

.card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

/* 卡片头部增强 */
.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background-color: #f9fafb;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

/* 卡片内容区域 */
.card-body {
  padding: 20px;
}

/* 月度快照 */
.snapshot-list {
  max-height: 300px;
  overflow-y: auto;
}

.snapshot-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.snapshot-item {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  padding: 12px;
  background-color: #f9fafb;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 14px;
}

.snapshot-month {
  font-weight: 500;
}

.snapshot-rate {
  color: #10b981;
  font-weight: 500;
}

/* 关键数值 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.metrics-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metric-item {
  background-color: #f9fafb;
  padding: 16px;
  border-radius: 6px;
  text-align: center;
}

.metric-label {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 4px 0;
}

.metric-value {
  font-size: 20px;
  font-weight: bold;
  color: #2563eb;
  margin: 4px 0 8px 0;
}

.metric-detail {
  font-size: 12px;
  color: #6b7280;
  margin: 8px 0 0 0;
}

/* 图表容器样式 */
.chart-container {
  width: 100%;
  height: 350px;
  margin: 10px 0;
}

.four-in-one-item .chart-container {
  flex: 1;
  min-height: 250px;
}

/* 好坏评占比 */
.reviews-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.review-item {
  background-color: #f9fafb;
  padding: 12px;
  border-radius: 6px;
  text-align: center;
}

.review-month {
  font-size: 14px;
  font-weight: 500;
  margin: 0 0 8px 0;
}

.review-chart {
  flex: 1;
  min-height: 100px;
  width: 100%;
}

/* 滚动条样式 */

/* ==================== 新增布局样式（来自DealerDashboard_副本.vue） ==================== */

/* 经销商选择模块 */
.dealer-selector-container {
  margin-bottom: 20px;
}

.aleftboxtbott {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
  margin-bottom: 20px;
}

.aleftboxtbott_cont {
  margin-top: 10px;
}

/* 月度快照+核心指标布局 */
.snapshot-metrics-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.left1 {
  flex: 1;
  min-width: 0;
}

.left1 .card-wrapper {
  height: 100%;
}

.core-metrics-container {
  flex: 1;
  min-width: 0;
}

.core-metrics-container .card-wrapper {
  height: 100%;
}

.aleftboxttop {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
  height: 100%;
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.aleftboxttopcont {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px;
  max-height: 400px;
  height: 400px;
}

/* 自定义滚动条样式 */
.aleftboxttopcont::-webkit-scrollbar {
  width: 6px;
}

.aleftboxttopcont::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.aleftboxttopcont::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.aleftboxttopcont::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.month-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.month-list li {
  display: flex;
  align-items: center;
  padding: 20px 10px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.3s;
  min-height: 60px;
}

.month-list li:hover {
  background-color: #f5f5f5;
}

.month-list li:last-child {
  border-bottom: none;
}

.month-label {
  font-weight: 600;
  color: #333;
  min-width: 50px;
  margin-right: 15px;
}

.metric-item {
  flex: 1;
  font-size: 13px;
  color: #666;
  padding: 0 10px;
}

.metric-item.sales {
  color: #1890ff;
}

.metric-item.traffic {
  color: #52c41a;
}

.metric-item.leads {
  color: #fa8c16;
}

/* 卡片包装器和复选框样式 */
.card-wrapper {
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 选中状态 - 更柔和的高亮效果 */
.card-wrapper.card-selected {
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.4), 
              0 4px 12px rgba(24, 144, 255, 0.15) !important;
  border-radius: 8px;
  transform: translateY(-2px);
}

/* 复选框容器 - 更自然的设计 */
.card-checkbox {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
  display: none;
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 自定义复选框样式 */
.card-checkbox input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  width: 22px;
  height: 22px;
  border: 2px solid #d9d9d9;
  border-radius: 4px;
  background-color: #fff;
  cursor: pointer;
  position: relative;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

/* 复选框悬停效果 */
.card-checkbox input[type="checkbox"]:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}

/* 复选框选中状态 */
.card-checkbox input[type="checkbox"]:checked {
  background-color: #1890ff;
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

/* 复选框选中后的对勾 */
.card-checkbox input[type="checkbox"]:checked::after {
  content: '';
  position: absolute;
  left: 6px;
  top: 2px;
  width: 6px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

/* 复选框焦点状态 */
.card-checkbox input[type="checkbox"]:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.1);
}

/* 选择模式时显示复选框 */
.dashboard-container.show-export-dropdown .card-checkbox,
.dashboard-container.show-report-dropdown .card-checkbox {
  display: block;
}

/* 卡片悬停效果 - 仅在选择模式下 */
.dashboard-container.show-export-dropdown .card-wrapper:hover,
.dashboard-container.show-report-dropdown .card-wrapper:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

/* 已选中卡片的悬停效果 */
.dashboard-container.show-export-dropdown .card-wrapper.card-selected:hover,
.dashboard-container.show-report-dropdown .card-wrapper.card-selected:hover {
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.5), 
              0 6px 16px rgba(24, 144, 255, 0.2) !important;
}


.metric-item.potential {
  color: #eb2f96;
}

.metric-item.rate {
  color: #722ed1;
}

/* 核心指标样式 */
.aleftboxtmidd {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
  height: 100%;
  min-height: 400px;
}







/* 销量趋势分析+销售漏斗布局 */
.trend-funnel-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  align-items: stretch;
}

.mrbox {
  flex: 2;
  min-width: 0;
}

.mrbox .card-wrapper {
  height: 100%;
}

.funnel-container {
  flex: 1;
  min-width: 0;
}

.funnel-container .card-wrapper {
  height: 100%;
}

.amiddboxttop {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
  min-height: 420px;
  height: 420px;
}

.amiddboxtbott1 {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
  min-height: 420px;
  height: 420px;
}

.left2_table {
  height: calc(100% - 40px);
}

.amiddboxtbott1content {
  height: calc(100% - 40px);
}

/* 四合一模块布局 */
.four-in-one-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.four-in-one-item {
  flex: 1;
  min-width: 200px;
  min-height: 300px;
}

.four-in-one-item .card-wrapper {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 15px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 评价占比框样式 */
.review-box {
  margin-top: 20px;
}

.review-box .card-wrapper {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.review-charts-container {
  margin-top: 20px;
}

.review-charts-row {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  justify-content: space-between;
}

.review-chart-item {
  width: calc(10% - 13.5px);
  min-width: 80px;
  background: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  padding: 15px;
  text-align: center;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
}

.review-chart-item:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.review-chart-title {
  margin-bottom: 15px;
  color: #333;
  font-size: 14px;
  font-weight: bold;
}

/* ==================== 新增布局样式结束 ==================== */
.snapshot-list::-webkit-scrollbar {
  width: 6px;
}

.snapshot-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.snapshot-list::-webkit-scrollbar-thumb {
  background: #c5c5c5;
  border-radius: 3px;
}

.snapshot-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 模块通用样式 */
.aleftboxttop,
.aleftboxtmidd,
.aleftboxtbott,
.amiddboxttop,
.amiddboxtbott1,
.amiddboxtbott2,
.arightboxtop,
.arightboxbott,
.review-box {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
  margin-bottom: 20px;
}

/* 核心指标容器样式 */
.core-metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 20px;
  padding: 20px;
  height: calc(100% - 80px);
}

.core-metric-item {
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

/* 核心指标颜色对应月度快照 */
.core-metric-item:nth-child(1) {
  background-color: #e6f7ff;
  border-left: 4px solid #1890ff;
}

.core-metric-item:nth-child(2) {
  background-color: #f6ffed;
  border-left: 4px solid #52c41a;
}

.core-metric-item:nth-child(3) {
  background-color: #fff7e6;
  border-left: 4px solid #fa8c16;
}

.core-metric-item:nth-child(4) {
  background-color: #fff0f6;
  border-left: 4px solid #eb2f96;
}

/* 核心指标标题和按钮布局 */
.metrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.metrics-header h2 {
  margin: 0;
}

/* 指标切换按钮样式 */
.metric-toggle-btn {
  display: block;
  width: 80px;
  height: 32px;
  background: #f0f0f0;
  border: 1px solid #e8e8e8;
  color: #333;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.3s ease;
  margin-left: auto;
  margin-top: 10px;
  cursor: pointer;
}

.metric-toggle-btn:hover {
  background: #e8e8e8;
  border-color: #d9d9d9;
}

/* 核心指标小模块内容样式 */
.metric-name {
  margin: 0 0 15px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.core-metric-item h3 {
  margin: 0 0 15px 0;
  font-size: 24px;
  font-weight: bold;
}

.month-text {
  margin: 0;
  font-size: 12px;
  color: #666;
}



/* 响应式设计 */
@media (max-width: 1200px) {
  .month-list li {
    width: 23%;
  }
  
  .review-chart-item {
    width: 23%;
  }
  
  .chart-container {
    height: 300px;
  }
}

@media (max-width: 768px) {
  .month-list li {
    width: 45%;
  }
  
  .review-chart-item {
    width: 45%;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .chart-container {
    height: 250px;
  }
  
  .aleftboxttop,
  .aleftboxtmidd,
  .aleftboxtbott,
  .amiddboxttop,
  .amiddboxtbott1,
  .amiddboxtbott2,
  .arightboxtop,
  .arightboxbott,
  .review-box {
    padding: 15px;
  }
}
</style>