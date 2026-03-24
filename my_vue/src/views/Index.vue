<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>经销商数据可视化平台</h1>
      <div class="header-info">
        <div class="year-selector">
          <label>年份：</label>
          <select v-model="selectedYear" @change="loadAllData">
            <option v-for="year in availableYears" :key="year" :value="year">{{ year }}年</option>
          </select>
        </div>
      </div>
    </header>

    <div class="kpi-cards">
      <div class="kpi-card">
        <div class="kpi-icon kpi-icon-blue">📊</div>
        <div class="kpi-content">
          <div class="kpi-value">{{ headerKpi.totalDealers }}</div>
          <div class="kpi-label">门店总数</div>
          <div class="kpi-change" :class="headerKpi.totalDealersChange >= 0 ? 'positive' : 'negative'">
            {{ headerKpi.totalDealersChange >= 0 ? '↑' : '↓' }} {{ Math.abs(headerKpi.totalDealersChange || 0) }} 较上年
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon kpi-icon-green">⭐</div>
        <div class="kpi-content">
          <div class="kpi-value">{{ headerKpi.avgScore }}</div>
          <div class="kpi-label">平均评分</div>
          <div class="kpi-change" :class="headerKpi.scoreChange >= 0 ? 'positive' : 'negative'">
            {{ headerKpi.scoreChange >= 0 ? '↑' : '↓' }} {{ Math.abs(headerKpi.scoreChange || 0) }} ({{ headerKpi.scoreChangePct }}%)
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon kpi-icon-orange">📈</div>
        <div class="kpi-content">
          <div class="kpi-value">{{ metricsComparison.totalSales }}</div>
          <div class="kpi-label">总销量</div>
          <div class="kpi-change" :class="metricsComparison.salesChangePct >= 0 ? 'positive' : 'negative'">
            {{ metricsComparison.salesChangePct >= 0 ? '↑' : '↓' }} {{ Math.abs(metricsComparison.salesChangePct || 0) }}% 较上年
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon kpi-icon-red">⚠️</div>
        <div class="kpi-content">
          <div class="kpi-value">{{ headerKpi.warningCount }}</div>
          <div class="kpi-label">预警门店</div>
          <div class="kpi-change" :class="headerKpi.warningChange <= 0 ? 'positive' : 'negative'">
            {{ headerKpi.warningChange <= 0 ? '↓' : '↑' }} {{ Math.abs(headerKpi.warningChange || 0) }} 较上年
          </div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon kpi-icon-purple">🏆</div>
        <div class="kpi-content">
          <div class="kpi-value">{{ headerKpi.topProvince || '-' }}</div>
          <div class="kpi-label">TOP省份</div>
          <div class="kpi-sub">{{ headerKpi.topProvinceScore }}分</div>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-icon kpi-icon-cyan">✅</div>
        <div class="kpi-content">
          <div class="kpi-value">{{ headerKpi.activeDealers }}</div>
          <div class="kpi-label">活跃门店</div>
          <div class="kpi-sub">占比 {{ headerKpi.activeRatio }}%</div>
        </div>
      </div>
    </div>

    <main class="dashboard-main">
      <div class="row row-map-region">
        <div class="combined-card">
          <div class="map-section">
            <div class="card-header">
              <h3>门店分布情况</h3>
              <span class="sub-title">{{ mapTitle }}</span>
            </div>
            <div class="map-nav-bar" v-if="mapLevel !== 'country'">
              <button class="nav-btn" @click="goBackLevel">
                <span>← 返回上一级</span>
              </button>
              <button class="nav-btn" @click="goToCountry">
                <span>回到全国</span>
              </button>
              <button class="nav-btn detail-btn" @click="showProvinceDetail">
                <span>查看详情</span>
              </button>
              <span class="current-location">当前位置：{{ currentLocation }}</span>
            </div>
            <div class="card-body map-body">
              <div ref="chinaMap" class="map-container"></div>
            </div>
          </div>
          <div class="region-section">
            <div class="card-header">
              <h3>区域业绩看板</h3>
              <span class="sub-title">点击区域联动地图</span>
            </div>
            <div class="card-body region-body">
              <div class="region-list-vertical">
                <div 
                  v-for="region in regionDashboard" 
                  :key="region.region"
                  class="region-item"
                  :class="{ 'region-active': selectedRegion === region.region }"
                  @click="selectRegion(region)"
                >
                  <div class="region-header">
                    <span class="region-name">{{ region.region }}</span>
                    <span class="region-score">{{ region.avg_score }}分</span>
                  </div>
                  <div class="region-stats">
                    <div class="region-stat">
                      <span class="stat-label">门店数</span>
                      <span class="stat-value">{{ region.dealer_count }}家</span>
                    </div>
                    <div class="region-stat">
                      <span class="stat-label">环比</span>
                      <span class="stat-value" :class="region.change_pct >= 0 ? 'positive' : 'negative'">
                        {{ region.change_pct >= 0 ? '+' : '' }}{{ region.change_pct }}%
                      </span>
                    </div>
                    <div class="region-stat">
                      <span class="stat-label">预警</span>
                      <span class="stat-value warning">{{ region.warning_count }}家</span>
                    </div>
                  </div>
                  <div class="region-bar">
                    <div class="bar-fill" :style="{ width: getRegionBarWidth(region.avg_score) + '%' }"></div>
                  </div>
                  <div class="region-insight" v-if="region.insight">
                    <span class="insight-icon">💡</span>
                    <span class="insight-text">{{ region.insight }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row row-metrics">
        <div class="col-metric" v-for="metric in metricsCards" :key="metric.label">
          <div class="metric-card">
            <div class="metric-icon">{{ metric.icon }}</div>
            <div class="metric-content">
              <div class="metric-value">{{ metric.value }}</div>
              <div class="metric-label">{{ metric.label }}</div>
              <div class="metric-change" :class="metric.changeClass">
                {{ metric.changeText }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row row-charts">
        <div class="col-left-main">
          <div class="row-left-top">
            <div class="col-line-full">
              <div class="card line-card">
                <div class="card-header">
                  <h3>月度趋势图</h3>
                  <span class="sub-title">{{ chartAreaTitle }}各项指标均值</span>
                </div>
                <div class="card-body">
                  <div ref="lineChart" class="chart-container"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="row-left-bottom">
            <div class="col-radar">
              <div class="card radar-card">
                <div class="card-header">
                  <h3>五力雷达图</h3>
                  <span class="sub-title">{{ chartAreaTitle }}五力评分均值</span>
                </div>
                <div class="card-body">
                  <div ref="radarChart" class="chart-container"></div>
                </div>
              </div>
            </div>
            <div class="col-pie">
              <div class="card pie-card">
                <div class="card-header">
                  <h3>门店评分统计</h3>
                  <span class="sub-title">{{ chartAreaTitle }}门店分布</span>
                </div>
                <div class="card-body">
                  <div ref="pieChart" class="chart-container"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-right-side">
          <div class="card ranking-card">
            <div class="card-header">
              <h3>门店排名</h3>
              <span class="sub-title">{{ chartAreaTitle }}按五力总评分排名 TOP10</span>
            </div>
            <div class="card-body">
              <div class="ranking-table-wrapper">
                <table class="ranking-table">
                  <thead>
                    <tr>
                      <th>排名</th>
                      <th>门店代码</th>
                      <th>省份</th>
                      <th>总评分</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in rankingData" :key="item.code">
                      <td>
                        <span :class="['rank-badge', `rank-${index + 1}`]">{{ index + 1 }}</span>
                      </td>
                      <td>{{ item.code }}</td>
                      <td>{{ item.province }}</td>
                      <td class="score-cell">{{ item.totalScore.toFixed(2) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="card warning-card">
            <div class="card-header">
              <h3>门店预警</h3>
              <span class="sub-title">{{ chartAreaTitle }}按评分等级分类</span>
            </div>
            <div class="card-body">
              <div class="warning-sections">
                <div class="warning-section warning-red">
                  <div class="warning-header">
                    <span class="warning-icon">!</span>
                    <span class="warning-title">高风险</span>
                    <span class="warning-count">{{ warningRed.length }}家</span>
                  </div>
                  <div class="warning-list">
                    <div v-for="item in warningRed.slice(0, 3)" :key="item.code" class="warning-item">
                      <span class="dealer-code">{{ item.code }}</span>
                      <span class="dealer-score">{{ item.totalScore.toFixed(2) }}分</span>
                    </div>
                    <div v-if="warningRed.length > 3" class="warning-more">
                      还有 {{ warningRed.length - 3 }} 家...
                    </div>
                  </div>
                </div>

                <div class="warning-section warning-orange">
                  <div class="warning-header">
                    <span class="warning-icon">!</span>
                    <span class="warning-title">中风险</span>
                    <span class="warning-count">{{ warningOrange.length }}家</span>
                  </div>
                  <div class="warning-list">
                    <div v-for="item in warningOrange.slice(0, 3)" :key="item.code" class="warning-item">
                      <span class="dealer-code">{{ item.code }}</span>
                      <span class="dealer-score">{{ item.totalScore.toFixed(2) }}分</span>
                    </div>
                    <div v-if="warningOrange.length > 3" class="warning-more">
                      还有 {{ warningOrange.length - 3 }} 家...
                    </div>
                  </div>
                </div>

                <div class="warning-section warning-green">
                  <div class="warning-header">
                    <span class="warning-icon">✓</span>
                    <span class="warning-title">健康</span>
                    <span class="warning-count">{{ warningGreen.length }}家</span>
                  </div>
                  <div class="warning-list">
                    <div v-for="item in warningGreen.slice(0, 3)" :key="item.code" class="warning-item">
                      <span class="dealer-code">{{ item.code }}</span>
                      <span class="dealer-score">{{ item.totalScore.toFixed(2) }}分</span>
                    </div>
                    <div v-if="warningGreen.length > 3" class="warning-more">
                      还有 {{ warningGreen.length - 3 }} 家...
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <div class="store-detail-modal" v-if="showStoreDetailModal" @click.self="closeStoreDetailModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ selectedProvince }}门店详情</h2>
          <button class="close-btn" @click="closeStoreDetailModal">×</button>
        </div>
        <div class="modal-body">
          <div class="store-list-section">
            <div class="section-header">
              <h3>门店列表</h3>
              <div class="sort-controls">
                <label>排序：</label>
                <select v-model="storeSortBy" @change="sortStoreList">
                  <option value="sales">按业绩</option>
                  <option value="totalScore">按评分</option>
                </select>
              </div>
            </div>
            <div class="store-table-wrapper">
              <table class="store-table">
                <thead>
                  <tr>
                    <th>门店代码</th>
                    <th>城市</th>
                    <th>销量</th>
                    <th>评分</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="store in sortedProvinceStores" :key="store.id">
                    <td>{{ store.name }}</td>
                    <td>{{ store.city }}</td>
                    <td>{{ store.sales }}</td>
                    <td>{{ store.totalScore.toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="top-bottom-section">
            <div class="top-stores">
              <h4>🏆 TOP 10 门店</h4>
              <div class="mini-list">
                <div v-for="(store, index) in top10Stores" :key="store.id" class="mini-item">
                  <span class="rank">{{ index + 1 }}</span>
                  <span class="name">{{ store.name }}</span>
                  <span class="score">{{ store.totalScore.toFixed(2) }}</span>
                </div>
              </div>
            </div>
            <div class="bottom-stores">
              <h4>⚠️ 末 10 门店（重点优化）</h4>
              <div class="mini-list">
                <div v-for="(store, index) in bottom10Stores" :key="store.id" class="mini-item warning">
                  <span class="rank">{{ sortedProvinceStores.length - 9 + index }}</span>
                  <span class="name">{{ store.name }}</span>
                  <span class="score">{{ store.totalScore.toFixed(2) }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="trend-section">
            <h4>📈 核心指标趋势（近3个月）</h4>
            <div ref="trendChart" class="trend-chart"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import axios from 'axios'

const PROVINCE_REGION_MAP = {
  '辽宁省': '东北',
  '山东省': '华东',
  '湖北省': '华中',
  '广东省': '华南',
  '广西壮族自治区': '华南'
}

export default {
  name: 'Index',
  data() {
    return {
      radarChart: null,
      lineChart: null,
      pieChart: null,
      mapChart: null,
      trendChart: null,
      selectedYear: 2024,
      availableYears: [2024, 2023, 2022],
      radarAvg: {},
      monthlyAvg: {},
      rankingData: [],
      warningData: { red: 0, orange: 0, green: 0 },
      totalDealers: 0,
      provinceDealerCount: {},
      cityDealerCount: {},
      mapLevel: 'country',
      currentProvince: '',
      currentCity: '',
      mapStack: [],
      provinceStores: [],
      showStoreDetailModal: false,
      selectedProvince: '',
      storeSortBy: 'sales',
      headerKpi: {
        totalDealers: 0,
        totalDealersChange: 0,
        avgScore: 0,
        scoreChange: 0,
        scoreChangePct: 0,
        warningCount: 0,
        warningChange: 0,
        topProvince: '',
        topProvinceScore: 0,
        activeDealers: 0,
        activeRatio: 0
      },
      regionDashboard: [],
      selectedRegion: '',
      metricsComparison: {
        totalSales: 0,
        salesChangePct: 0,
        totalFlow: 0,
        flowChangePct: 0,
        totalLeads: 0,
        leadsChangePct: 0,
        avgSuccessRate: 0,
        successRateChange: 0,
        totalPotential: 0
      },
      insights: []
    }
  },
  computed: {
    radarData() {
      return [
        { name: '传播获客力', value: this.radarAvg['传播获客力'] || 0 },
        { name: '体验力', value: this.radarAvg['体验力'] || 0 },
        { name: '转化力', value: this.radarAvg['转化力'] || 0 },
        { name: '服务力', value: this.radarAvg['服务力'] || 0 },
        { name: '经营力', value: this.radarAvg['经营力'] || 0 }
      ]
    },
    pieData() {
      return [
        { name: '高风险 (总分<15)', value: this.warningRed.length, color: '#ff4d4f' },
        { name: '中风险 (15≤总分<20)', value: this.warningOrange.length, color: '#fa8c16' },
        { name: '健康 (总分≥20)', value: this.warningGreen.length, color: '#52c41a' }
      ]
    },
    warningRed() {
      return this.warningData.red || []
    },
    warningOrange() {
      return this.warningData.orange || []
    },
    warningGreen() {
      return this.warningData.green || []
    },
    mapTitle() {
      if (this.mapLevel === 'country') return '全国门店地理分布'
      if (this.mapLevel === 'province') return `${this.currentProvince}门店分布`
      return '门店地理分布'
    },
    currentLocation() {
      if (this.mapLevel === 'country') return '全国'
      if (this.mapLevel === 'province') return this.currentProvince
      return ''
    },
    chartAreaTitle() {
      if (this.mapLevel === 'country') return '全国'
      if (this.mapLevel === 'province' && this.currentCity) return this.currentCity
      if (this.mapLevel === 'province') return this.currentProvince
      return '全国'
    },
    sortedProvinceStores() {
      let stores = [...this.provinceStores]
      if (this.storeSortBy === 'sales') {
        stores.sort((a, b) => b.sales - a.sales)
      } else if (this.storeSortBy === 'totalScore') {
        stores.sort((a, b) => b.totalScore - a.totalScore)
      }
      return stores
    },
    top10Stores() {
      return this.sortedProvinceStores.slice(0, 10)
    },
    bottom10Stores() {
      return this.sortedProvinceStores.slice(-10).reverse()
    },
    metricsCards() {
      return [
        {
          icon: '👥',
          value: this.metricsComparison.totalFlow,
          label: '总客流量',
          changeText: `${this.metricsComparison.flowChangePct >= 0 ? '↑' : '↓'} ${Math.abs(this.metricsComparison.flowChangePct)}%`,
          changeClass: this.metricsComparison.flowChangePct >= 0 ? 'positive' : 'negative'
        },
        {
          icon: '📋',
          value: this.metricsComparison.totalLeads,
          label: '总线索量',
          changeText: `${this.metricsComparison.leadsChangePct >= 0 ? '↑' : '↓'} ${Math.abs(this.metricsComparison.leadsChangePct)}%`,
          changeClass: this.metricsComparison.leadsChangePct >= 0 ? 'positive' : 'negative'
        },
        {
          icon: '🎯',
          value: this.metricsComparison.avgSuccessRate + '%',
          label: '平均成交率',
          changeText: `${this.metricsComparison.successRateChange >= 0 ? '↑' : '↓'} ${Math.abs(this.metricsComparison.successRateChange)}%`,
          changeClass: this.metricsComparison.successRateChange >= 0 ? 'positive' : 'negative'
        },
        {
          icon: '👤',
          value: this.metricsComparison.totalPotential,
          label: '总潜客量',
          changeText: '本年累计',
          changeClass: 'neutral'
        }
      ]
    }
  },
  mounted() {
    this.loadAvailableYears()
    this.loadAllData()
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
    if (this.radarChart) this.radarChart.dispose()
    if (this.lineChart) this.lineChart.dispose()
    if (this.pieChart) this.pieChart.dispose()
    if (this.mapChart) this.mapChart.dispose()
  },
  methods: {
    async loadAvailableYears() {
      try {
        const response = await axios.get('/api/five-forces/years')
        if (response.data.success) {
          this.availableYears = response.data.data
          if (this.availableYears.length > 0 && !this.availableYears.includes(this.selectedYear)) {
            this.selectedYear = this.availableYears[0]
          }
        }
      } catch (error) {
        console.error('加载年份失败:', error)
      }
    },
    async loadAllData() {
      await Promise.all([
        this.loadOverviewData(),
        this.loadHeaderKpi(),
        this.loadRegionDashboard(),
        this.loadMetricsComparison(),
        this.loadInsights()
      ])
      this.$nextTick(() => {
        this.initRadarChart()
        this.initLineChart()
        this.initPieChart()
        this.initMap()
      })
    },
    async loadAreaChartData() {
      try {
        let url = `/api/index/area-data?year=${this.selectedYear}`
        if (this.currentCity) {
          url += `&province=${encodeURIComponent(this.currentProvince)}&city=${encodeURIComponent(this.currentCity)}`
        } else if (this.mapLevel === 'province' && this.currentProvince) {
          url += `&province=${encodeURIComponent(this.currentProvince)}`
        }
        
        const response = await axios.get(url)
        if (response.data.success) {
          const data = response.data.data
          this.radarAvg = data.radar_avg
          this.monthlyAvg = data.monthly_avg
          this.rankingData = data.ranking
          this.warningData = data.warning
          
          this.$nextTick(() => {
            this.initRadarChart()
            this.initLineChart()
            this.initPieChart()
          })
        }
      } catch (error) {
        console.error('加载区域图表数据失败:', error)
      }
    },
    async loadOverviewData() {
      try {
        const response = await axios.get(`/api/index/overview?year=${this.selectedYear}`)
        if (response.data.success) {
          const data = response.data.data
          this.radarAvg = data.radar_avg
          this.monthlyAvg = data.monthly_avg
          this.rankingData = data.ranking
          this.warningData = data.warning
          this.totalDealers = data.total_dealers
          this.provinceDealerCount = data.province_count
          this.cityDealerCount = data.city_count || {}
        }
      } catch (error) {
        console.error('加载概览数据失败:', error)
      }
    },
    async loadHeaderKpi() {
      try {
        const response = await axios.get(`/api/index/header-kpi?year=${this.selectedYear}`)
        if (response.data.success) {
          this.headerKpi = response.data.data
        }
      } catch (error) {
        console.error('加载头部KPI失败:', error)
      }
    },
    async loadRegionDashboard() {
      try {
        const response = await axios.get(`/api/index/region-dashboard?year=${this.selectedYear}`)
        if (response.data.success) {
          this.regionDashboard = response.data.data
        }
      } catch (error) {
        console.error('加载区域看板失败:', error)
      }
    },
    async loadMetricsComparison() {
      try {
        const response = await axios.get(`/api/index/metrics-comparison?year=${this.selectedYear}`)
        if (response.data.success) {
          this.metricsComparison = response.data.data
        }
      } catch (error) {
        console.error('加载核心指标对比失败:', error)
      }
    },
    async loadInsights() {
      try {
        const response = await axios.get(`/api/index/insights?year=${this.selectedYear}`)
        if (response.data.success) {
          this.insights = response.data.data
        }
      } catch (error) {
        console.error('加载数据洞察失败:', error)
      }
    },
    getRegionBarWidth(score) {
      const maxScore = 25
      return Math.min((score / maxScore) * 100, 100)
    },
    selectRegion(region) {
      if (this.selectedRegion === region.region) {
        this.selectedRegion = ''
        this.clearMapHighlight()
      } else {
        this.selectedRegion = region.region
        this.highlightMapRegion(region.provinces)
      }
    },
    clearMapHighlight() {
      if (!this.mapChart || this.mapLevel !== 'country') return
      this.renderCountryMap()
    },
    highlightMapRegion(provinces) {
      if (!this.mapChart || this.mapLevel !== 'country') return
      
      const storeCount = this.getProvinceStoreCount()
      const data = Object.keys(storeCount).map(province => {
        const isHighlighted = provinces.includes(province)
        return {
          name: province,
          value: storeCount[province],
          itemStyle: {
            areaColor: isHighlighted ? '#faad14' : undefined,
            borderColor: isHighlighted ? '#d48806' : undefined,
            borderWidth: isHighlighted ? 2 : 1
          },
          label: {
            show: true,
            color: isHighlighted ? '#fff' : '#666',
            fontSize: isHighlighted ? 12 : 10,
            fontWeight: isHighlighted ? 'bold' : 'normal'
          }
        }
      })
      
      const maxValue = Math.max(...Object.values(storeCount), 10)
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          formatter: function(params) {
            if (params.value) {
              return `${params.name}<br/>门店数量：${params.value}家<br/><span style="color:#999;font-size:11px;">点击查看详情</span>`
            }
            return `${params.name}<br/>暂无门店`
          }
        },
        visualMap: {
          min: 0,
          max: maxValue,
          left: 'left',
          bottom: '5%',
          text: ['高', '低'],
          calculable: true,
          inRange: {
            color: ['#e6f7ff', '#91d5ff', '#40a9ff', '#1890ff', '#096dd9']
          },
          textStyle: {
            color: '#666'
          }
        },
        geo: {
          map: 'china',
          roam: true,
          zoom: 1.2,
          center: [105, 36],
          label: {
            show: true,
            color: '#666',
            fontSize: 10
          },
          itemStyle: {
            areaColor: '#f5f5f5',
            borderColor: '#1890ff',
            borderWidth: 1
          },
          emphasis: {
            itemStyle: {
              areaColor: '#1890ff'
            },
            label: {
              color: '#fff',
              fontSize: 12
            }
          }
        },
        series: [
          {
            name: '门店分布',
            type: 'map',
            map: 'china',
            geoIndex: 0,
            data: data
          }
        ]
      }
      
      this.mapChart.setOption(option, true)
    },
    initRadarChart() {
      this.radarChart = echarts.init(this.$refs.radarChart)
      const indicatorData = this.radarData.map(d => ({ name: d.name, max: 5 }))
      const values = this.radarData.map(d => parseFloat(d.value))
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          formatter: function(params) {
            const data = params.value
            let result = '<div style="padding: 8px;">'
            indicatorData.forEach((item, index) => {
              result += `<div style="margin: 4px 0;"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#1890ff;margin-right:8px;"></span>${item.name}: <strong>${data[index]}</strong></div>`
            })
            result += '</div>'
            return result
          }
        },
        radar: {
          indicator: indicatorData,
          center: ['50%', '50%'],
          radius: '65%',
          axisName: {
            color: '#666',
            fontSize: 12,
            formatter: function(value, indicator) {
              const index = indicatorData.findIndex(d => d.name === value)
              if (index !== -1) {
                return `${value}\n${values[index]}`
              }
              return value
            }
          },
          splitArea: {
            areaStyle: {
              color: ['rgba(24, 144, 255, 0.05)', 'rgba(24, 144, 255, 0.1)', 'rgba(24, 144, 255, 0.15)', 'rgba(24, 144, 255, 0.2)', 'rgba(24, 144, 255, 0.25)']
            }
          },
          axisLine: {
            lineStyle: {
              color: '#e8e8e8'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#e8e8e8'
            }
          }
        },
        series: [{
          type: 'radar',
          data: [{
            value: values,
            name: '五力均值',
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              color: '#1890ff',
              width: 2
            },
            areaStyle: {
              color: 'rgba(24, 144, 255, 0.3)'
            },
            itemStyle: {
              color: '#1890ff'
            },
            label: {
              show: true,
              formatter: function(params) {
                return params.value
              },
              color: '#666',
              fontSize: 11
            }
          }]
        }]
      }
      this.radarChart.setOption(option)
    },
    initLineChart() {
      this.lineChart = echarts.init(this.$refs.lineChart)
      
      const monthCount = this.selectedYear === 2024 ? 10 : 12
      const months = Array.from({length: monthCount}, (_, i) => `${i + 1}月`)
      
      const salesData = months.map((_, i) => (this.monthlyAvg[i + 1] || {}).销量 || 0)
      const customerData = months.map((_, i) => (this.monthlyAvg[i + 1] || {}).客流量 || 0)
      const leadData = months.map((_, i) => (this.monthlyAvg[i + 1] || {}).线索量 || 0)
      const potentialData = months.map((_, i) => (this.monthlyAvg[i + 1] || {}).潜客量 || 0)
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        legend: {
          data: ['销量', '客流量', '线索量', '潜客量'],
          textStyle: {
            color: '#666'
          },
          top: 5
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '18%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: months,
          axisLine: {
            lineStyle: {
              color: '#e8e8e8'
            }
          },
          axisLabel: {
            color: '#666'
          }
        },
        yAxis: [
          {
            type: 'value',
            name: '销量/潜客量',
            position: 'left',
            axisLine: {
              lineStyle: {
                color: '#3b82f6'
              }
            },
            axisLabel: {
              color: '#6b7280',
              fontSize: 12
            },
            splitLine: {
              lineStyle: {
                color: '#f0f0f0'
              }
            },
            axisTick: {
              show: false
            }
          },
          {
            type: 'value',
            name: '线索量/客流量',
            position: 'right',
            axisLine: {
              lineStyle: {
                color: '#f59e0b'
              }
            },
            axisLabel: {
              color: '#6b7280',
              fontSize: 12
            },
            splitLine: {
              show: false
            },
            axisTick: {
              show: false
            }
          }
        ],
        series: [
          {
            name: '销量',
            type: 'line',
            smooth: true,
            data: salesData,
            yAxisIndex: 0,
            symbol: 'circle',
            symbolSize: 6,
            showSymbol: true,
            lineStyle: {
              width: 3,
              color: '#3b82f6'
            },
            itemStyle: {
              color: '#3b82f6',
              borderWidth: 2,
              borderColor: '#fff'
            }
          },
          {
            name: '客流量',
            type: 'line',
            smooth: true,
            data: customerData,
            yAxisIndex: 1,
            symbol: 'circle',
            symbolSize: 6,
            showSymbol: true,
            lineStyle: {
              width: 3,
              color: '#8b5cf6'
            },
            itemStyle: {
              color: '#8b5cf6',
              borderWidth: 2,
              borderColor: '#fff'
            }
          },
          {
            name: '线索量',
            type: 'line',
            smooth: true,
            data: leadData,
            yAxisIndex: 1,
            symbol: 'circle',
            symbolSize: 6,
            showSymbol: true,
            lineStyle: {
              width: 3,
              color: '#f59e0b'
            },
            itemStyle: {
              color: '#f59e0b',
              borderWidth: 2,
              borderColor: '#fff'
            }
          },
          {
            name: '潜客量',
            type: 'line',
            smooth: true,
            data: potentialData,
            yAxisIndex: 0,
            symbol: 'circle',
            symbolSize: 6,
            showSymbol: true,
            lineStyle: {
              width: 3,
              color: '#10b981'
            },
            itemStyle: {
              color: '#10b981',
              borderWidth: 2,
              borderColor: '#fff'
            }
          }
        ]
      }
      this.lineChart.setOption(option)
    },
    initPieChart() {
      this.pieChart = echarts.init(this.$refs.pieChart)
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}家 ({d}%)'
        },
        legend: {
          orient: 'horizontal',
          bottom: '5%',
          left: 'center',
          textStyle: {
            color: '#666',
            fontSize: 12
          },
          itemWidth: 12,
          itemHeight: 12
        },
        series: [
          {
            name: '门店评分分布',
            type: 'pie',
            radius: ['30%', '55%'],
            center: ['50%', '45%'],
            roseType: 'area',
            itemStyle: {
              borderRadius: 5,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: true,
              formatter: '{b}\n{c}家',
              color: '#666',
              fontSize: 11,
              lineHeight: 14
            },
            labelLine: {
              show: true,
              length: 8,
              length2: 15
            },
            data: this.pieData.map(d => ({
              name: d.name,
              value: d.value,
              itemStyle: { color: d.color }
            }))
          }
        ]
      }
      this.pieChart.setOption(option)
    },
    async initMap() {
      this.mapChart = echarts.init(this.$refs.chinaMap)
      try {
        const response = await axios.get('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
        echarts.registerMap('china', response.data)
        this.chinaGeoJson = response.data
        this.renderMap()
        this.bindMapEvents()
      } catch (error) {
        console.error('加载地图数据失败:', error)
      }
    },
    getProvinceStoreCount() {
      return this.provinceDealerCount
    },
    updateMapData() {
      this.renderMap()
    },
    renderMap() {
      if (this.mapLevel === 'country') {
        this.renderCountryMap()
      } else if (this.mapLevel === 'province') {
        this.renderProvinceMap()
      }
    },
    renderCountryMap() {
      const storeCount = this.getProvinceStoreCount()
      const data = Object.keys(storeCount).map(province => ({
        name: province,
        value: storeCount[province]
      }))
      
      const maxValue = Math.max(...Object.values(storeCount), 10)
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          formatter: function(params) {
            if (params.value) {
              return `${params.name}<br/>门店数量：${params.value}家<br/><span style="color:#999;font-size:11px;">点击查看详情</span>`
            }
            return `${params.name}<br/>暂无门店`
          }
        },
        visualMap: {
          min: 0,
          max: maxValue,
          left: 'left',
          bottom: '5%',
          text: ['高', '低'],
          calculable: true,
          inRange: {
            color: ['#e6f7ff', '#91d5ff', '#40a9ff', '#1890ff', '#096dd9']
          },
          textStyle: {
            color: '#666'
          }
        },
        geo: {
          map: 'china',
          roam: true,
          zoom: 1.2,
          center: [105, 36],
          label: {
            show: true,
            color: '#666',
            fontSize: 10
          },
          itemStyle: {
            areaColor: '#f5f5f5',
            borderColor: '#1890ff',
            borderWidth: 1
          },
          emphasis: {
            itemStyle: {
              areaColor: '#1890ff'
            },
            label: {
              color: '#fff',
              fontSize: 12
            }
          }
        },
        series: [
          {
            name: '门店分布',
            type: 'map',
            map: 'china',
            geoIndex: 0,
            data: data
          }
        ]
      }
      
      this.mapChart.setOption(option, true)
    },
    async renderProvinceMap() {
      const provinceAdcode = this.getProvinceAdcode(this.currentProvince)
      
      try {
        const response = await axios.get(`https://geo.datav.aliyun.com/areas_v3/bound/${provinceAdcode}_full.json`)
        echarts.registerMap('province', response.data)
        
        const provinceCount = this.provinceDealerCount[this.currentProvince] || 0
        
        const cityData = this.getCityDataForProvince(this.currentProvince)
        const maxValue = Math.max(...cityData.map(d => d.value), 10)
        
        const option = {
          backgroundColor: 'transparent',
          tooltip: {
            trigger: 'item',
            formatter: function(params) {
              if (params.value) {
                return `${params.name}<br/>门店数量：${params.value}家`
              }
              return `${params.name}<br/>暂无门店`
            }
          },
          visualMap: {
            min: 0,
            max: maxValue,
            left: 'left',
            bottom: '5%',
            text: ['高', '低'],
            calculable: true,
            inRange: {
              color: ['#e6f7ff', '#91d5ff', '#40a9ff', '#1890ff', '#096dd9']
            },
            textStyle: {
              color: '#666'
            }
          },
          geo: {
            map: 'province',
            roam: true,
            zoom: 1.2,
            label: {
              show: true,
              color: '#666',
              fontSize: 10
            },
            itemStyle: {
              areaColor: '#f5f5f5',
              borderColor: '#1890ff',
              borderWidth: 1
            },
            emphasis: {
              itemStyle: {
                areaColor: '#1890ff'
              },
              label: {
                color: '#fff',
                fontSize: 12
              }
            }
          },
          title: {
            text: `${this.currentProvince}\n共${provinceCount}家经销商`,
            left: 'center',
            top: 20,
            textStyle: {
              color: '#333',
              fontSize: 16,
              fontWeight: 'bold'
            }
          },
          series: [
            {
              name: '门店分布',
              type: 'map',
              map: 'province',
              geoIndex: 0,
              data: cityData
            }
          ]
        }
        
        this.mapChart.setOption(option, true)
      } catch (error) {
        console.error('加载省份地图失败:', error)
      }
    },
    getCityDataForProvince(provinceName) {
      const cityData = []
      const provinceCities = {
        '辽宁省': ['沈阳市', '大连市'],
        '山东省': ['济南市', '青岛市', '烟台市'],
        '广东省': ['广州市', '深圳市', '佛山市', '东莞市'],
        '广西壮族自治区': ['南宁市', '柳州市', '桂林市'],
        '湖北省': ['武汉市', '宜昌市', '襄阳市', '黄冈市']
      }
      
      const cities = provinceCities[provinceName] || []
      for (const city of cities) {
        const count = this.cityDealerCount[city] || 0
        if (count > 0) {
          cityData.push({
            name: city,
            value: count
          })
        }
      }
      return cityData
    },
    bindMapEvents() {
      this.mapChart.on('click', async (params) => {
        if (this.mapLevel === 'country' && params.componentType === 'series') {
          const provinceName = params.name
          if (provinceName && this.getProvinceStoreCount()[provinceName]) {
            this.mapStack.push({ level: 'country', province: '', city: '' })
            this.currentProvince = provinceName
            this.currentCity = ''
            this.mapLevel = 'province'
            
            const region = PROVINCE_REGION_MAP[provinceName]
            if (region) {
              this.selectedRegion = region
            }
            
            await this.renderProvinceMap()
            await this.loadAreaChartData()
            this.bindProvinceMapEvents()
          }
        }
      })
    },
    bindProvinceMapEvents() {
      this.mapChart.on('click', async (params) => {
        if (this.mapLevel === 'province' && params.componentType === 'series') {
          const cityName = params.name
          if (cityName) {
            let matchedCity = ''
            for (const key of Object.keys(this.cityDealerCount)) {
              if (key.includes(cityName) || cityName.includes(key)) {
                matchedCity = key
                break
              }
            }
            
            if (matchedCity || this.cityDealerCount[cityName]) {
              const targetCity = matchedCity || cityName
              if (this.currentCity === targetCity) {
                this.currentCity = ''
              } else {
                this.currentCity = targetCity
              }
              this.highlightCity(this.currentCity)
              await this.loadAreaChartData()
            }
          }
        }
      })
    },
    highlightCity(cityName) {
      if (!this.mapChart) return
      
      const option = this.mapChart.getOption()
      if (option.series && option.series[0]) {
        const data = option.series[0].data.map(item => ({
          ...item,
          itemStyle: {
            areaColor: item.name === cityName ? '#faad14' : undefined
          }
        }))
        this.mapChart.setOption({
          series: [{ data }]
        })
      }
    },
    goBackLevel() {
      if (this.mapStack.length > 0) {
        const prev = this.mapStack.pop()
        this.mapLevel = prev.level
        this.currentProvince = prev.province
        this.currentCity = ''
        this.selectedRegion = ''
        this.renderMap()
        this.loadAreaChartData()
      }
    },
    goToCountry() {
      this.mapLevel = 'country'
      this.currentProvince = ''
      this.currentCity = ''
      this.mapStack = []
      this.selectedRegion = ''
      this.renderMap()
      this.loadAreaChartData()
    },
    getProvinceAdcode(provinceName) {
      const adcodeMap = {
        '北京市': '110000',
        '天津市': '120000',
        '河北省': '130000',
        '山西省': '140000',
        '内蒙古自治区': '150000',
        '辽宁省': '210000',
        '吉林省': '220000',
        '黑龙江省': '230000',
        '上海市': '310000',
        '江苏省': '320000',
        '浙江省': '330000',
        '安徽省': '340000',
        '福建省': '350000',
        '江西省': '360000',
        '山东省': '370000',
        '河南省': '410000',
        '湖北省': '420000',
        '湖南省': '430000',
        '广东省': '440000',
        '广西壮族自治区': '450000',
        '海南省': '460000',
        '重庆市': '500000',
        '四川省': '510000',
        '贵州省': '520000',
        '云南省': '530000',
        '西藏自治区': '540000',
        '陕西省': '610000',
        '甘肃省': '620000',
        '青海省': '630000',
        '宁夏回族自治区': '640000',
        '新疆维吾尔自治区': '650000'
      }
      return adcodeMap[provinceName] || '100000'
    },
    async showProvinceDetail() {
      this.selectedProvince = this.currentProvince
      try {
        const response = await axios.get(`/api/index/province-stores?year=${this.selectedYear}&province=${encodeURIComponent(this.selectedProvince)}`)
        if (response.data.success) {
          this.provinceStores = response.data.data
        }
      } catch (error) {
        console.error('获取省份门店数据失败:', error)
        this.provinceStores = []
      }
      this.showStoreDetailModal = true
      this.$nextTick(() => {
        this.initTrendChart()
      })
    },
    closeStoreDetailModal() {
      this.showStoreDetailModal = false
      if (this.trendChart) {
        this.trendChart.dispose()
        this.trendChart = null
      }
    },
    sortStoreList() {
    },
    initTrendChart() {
      if (!this.$refs.trendChart) return
      
      this.trendChart = echarts.init(this.$refs.trendChart)
      
      const months = ['1月', '2月', '3月']
      const achieveRateData = [75, 82, 88]
      const avgSalesData = [120, 135, 142]
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        legend: {
          data: ['达标率', '单店平均业绩'],
          top: 0
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: months
        },
        yAxis: [
          {
            type: 'value',
            name: '达标率(%)',
            position: 'left',
            min: 0,
            max: 100
          },
          {
            type: 'value',
            name: '业绩(万元)',
            position: 'right'
          }
        ],
        series: [
          {
            name: '达标率',
            type: 'line',
            data: achieveRateData,
            yAxisIndex: 0,
            smooth: true,
            itemStyle: {
              color: '#1890ff'
            }
          },
          {
            name: '单店平均业绩',
            type: 'line',
            data: avgSalesData,
            yAxisIndex: 1,
            smooth: true,
            itemStyle: {
              color: '#52c41a'
            }
          }
        ]
      }
      
      this.trendChart.setOption(option)
    },
    handleResize() {
      if (this.radarChart) this.radarChart.resize()
      if (this.lineChart) this.lineChart.resize()
      if (this.pieChart) this.pieChart.resize()
      if (this.mapChart) this.mapChart.resize()
      if (this.trendChart) this.trendChart.resize()
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #f5f7fa;
  color: #333;
  padding: 16px;
  box-sizing: border-box;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.dashboard-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.header-info {
  font-size: 14px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 20px;
}

.year-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.year-selector label {
  color: #666;
}

.year-selector select {
  padding: 4px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
  background: #fff;
  cursor: pointer;
}

.year-selector select:focus {
  outline: none;
  border-color: #1890ff;
}

.kpi-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.kpi-card {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.kpi-icon-blue { background: #e6f7ff; }
.kpi-icon-green { background: #f6ffed; }
.kpi-icon-orange { background: #fff7e6; }
.kpi-icon-red { background: #fff2f0; }
.kpi-icon-purple { background: #f9f0ff; }
.kpi-icon-cyan { background: #e6fffb; }

.kpi-content {
  flex: 1;
}

.kpi-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  line-height: 1.2;
}

.kpi-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}

.kpi-change {
  font-size: 12px;
  margin-top: 4px;
}

.kpi-change.positive {
  color: #52c41a;
}

.kpi-change.negative {
  color: #ff4d4f;
}

.kpi-sub {
  font-size: 12px;
  color: #1890ff;
  margin-top: 4px;
}

.dashboard-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 20px;
}

.row {
  display: flex;
  gap: 16px;
}

.row-map-region {
  min-height: 600px;
  height: auto;
}

.combined-card {
  display: flex;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  flex: 1;
}

.map-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #f0f0f0;
}

.region-section {
  width: 380px;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

.map-body {
  flex: 1;
  padding: 12px;
}

.region-body {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
}

.region-list-vertical {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.row-map {
  min-height: 500px;
  height: auto;
}

.row-region {
  min-height: 200px;
  height: auto;
}

.row-top {
  min-height: 500px;
  height: auto;
}

.row-metrics {
  min-height: 160px;
  height: auto;
}

.row-charts {
  min-height: 800px;
  height: auto;
  display: flex;
  gap: 16px;
}

.col-left-main {
  width: 75%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.row-left-top {
  width: 100%;
  min-height: 280px;
}

.col-line-full {
  width: 100%;
}

.row-left-bottom {
  display: flex;
  gap: 16px;
  width: 100%;
  min-height: 280px;
}

.col-radar {
  width: 50%;
}

.col-pie {
  width: 50%;
}

.col-right-side {
  width: 25%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.col-right-side .card {
  flex: 1;
}

.col-map {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.col-region {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.col-full {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.col-metric {
  flex: 1;
}

.card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.card-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.sub-title {
  font-size: 12px;
  color: #999;
}

.card-body {
  flex: 1;
  padding: 12px;
  overflow: hidden;
}

.map-nav-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #e6f7ff;
  border-bottom: 1px solid #91d5ff;
}

.nav-btn {
  padding: 4px 12px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.nav-btn:hover {
  background: #096dd9;
}

.current-location {
  font-size: 12px;
  color: #1890ff;
  margin-left: auto;
}

.chart-container,
.map-container {
  width: 100%;
  height: 100%;
  min-height: 600px;
}

.region-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  overflow-y: auto;
}

.region-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  padding: 4px;
}

.region-item {
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.region-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: #1890ff;
  opacity: 0;
  transition: opacity 0.3s;
}

.region-item:hover {
  background: #f0f5ff;
  transform: translateX(-2px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.region-item:hover::before {
  opacity: 1;
}

.region-item.region-active {
  border-color: #1890ff;
  background: #e6f7ff;
  box-shadow: 0 2px 12px rgba(24, 144, 255, 0.2);
}

.region-item.region-active::before {
  opacity: 1;
}

.region-insight {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 8px;
  padding: 8px;
  background: #f0f5ff;
  border-radius: 4px;
  border-left: 3px solid #1890ff;
}

.insight-icon {
  font-size: 12px;
  flex-shrink: 0;
}

.insight-text {
  font-size: 11px;
  color: #666;
  line-height: 1.4;
}

.region-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.region-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.region-score {
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
}

.region-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}

.region-stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 11px;
  color: #999;
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.stat-value.positive {
  color: #52c41a;
}

.stat-value.negative {
  color: #ff4d4f;
}

.stat-value.warning {
  color: #fa8c16;
}

.region-bar {
  height: 4px;
  background: #e8e8e8;
  border-radius: 2px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #1890ff, #40a9ff);
  border-radius: 2px;
  transition: width 0.3s;
}

.metric-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  height: 100%;
  min-height: 120px;
}

.metric-icon {
  font-size: 36px;
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.metric-label {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.metric-change {
  font-size: 11px;
  margin-top: 2px;
}

.metric-change.positive {
  color: #52c41a;
}

.metric-change.negative {
  color: #ff4d4f;
}

.metric-change.neutral {
  color: #999;
}

.ranking-table-wrapper {
  height: 100%;
  overflow-y: auto;
}

.ranking-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.ranking-table th {
  text-align: left;
  padding: 8px 4px;
  color: #666;
  font-weight: 500;
  border-bottom: 1px solid #f0f0f0;
}

.ranking-table td {
  padding: 8px 4px;
  border-bottom: 1px solid #f5f5f5;
  color: #333;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.rank-1 {
  background: linear-gradient(135deg, #ffd700, #ffb300);
  color: #fff;
}

.rank-2 {
  background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
  color: #fff;
}

.rank-3 {
  background: linear-gradient(135deg, #cd7f32, #b87333);
  color: #fff;
}

.rank-badge:not(.rank-1):not(.rank-2):not(.rank-3) {
  background: #f0f0f0;
  color: #666;
}

.score-cell {
  color: #1890ff;
  font-weight: 600;
}

.warning-sections {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
  overflow-y: auto;
}

.warning-section {
  border-radius: 6px;
  padding: 10px;
  flex: 1;
  min-height: 80px;
}

.warning-red {
  background: #fff2f0;
  border: 1px solid #ffccc7;
}

.warning-orange {
  background: #fff7e6;
  border: 1px solid #ffd591;
}

.warning-green {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
}

.warning-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.warning-icon {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: bold;
}

.warning-red .warning-icon {
  background: #ff4d4f;
  color: #fff;
}

.warning-orange .warning-icon {
  background: #fa8c16;
  color: #fff;
}

.warning-green .warning-icon {
  background: #52c41a;
  color: #fff;
}

.warning-title {
  font-size: 13px;
  font-weight: 600;
  flex: 1;
}

.warning-red .warning-title {
  color: #cf1322;
}

.warning-orange .warning-title {
  color: #d46b08;
}

.warning-green .warning-title {
  color: #389e0d;
}

.warning-count {
  font-size: 12px;
  color: #999;
}

.warning-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.warning-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
}

.dealer-code {
  color: #666;
}

.dealer-score {
  font-weight: 500;
}

.warning-red .dealer-score {
  color: #ff4d4f;
}

.warning-orange .dealer-score {
  color: #fa8c16;
}

.warning-green .dealer-score {
  color: #52c41a;
}

.warning-more {
  font-size: 11px;
  color: #999;
  text-align: center;
  padding: 4px;
}

::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 2px;
}

::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 2px;
}

::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}

.store-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 90%;
  max-width: 1200px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 16px 24px;
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 28px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}

.store-list-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-controls label {
  font-size: 13px;
  color: #666;
}

.sort-controls select {
  padding: 4px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
}

.store-table-wrapper {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
}

.store-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.store-table th {
  background: #fafafa;
  padding: 10px 12px;
  text-align: left;
  font-weight: 500;
  color: #666;
  border-bottom: 1px solid #f0f0f0;
  position: sticky;
  top: 0;
}

.store-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f5f5f5;
  color: #333;
}

.store-table tr:hover {
  background: #f5f7fa;
}

.top-bottom-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.top-stores,
.bottom-stores {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
}

.top-stores h4,
.bottom-stores h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.mini-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mini-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 6px;
  font-size: 13px;
}

.mini-item .rank {
  width: 24px;
  height: 24px;
  background: #1890ff;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.mini-item.warning .rank {
  background: #ff4d4f;
}

.mini-item .name {
  flex: 1;
  color: #333;
}

.mini-item .score {
  color: #666;
  font-weight: 500;
}

.trend-section {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
}

.trend-section h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.trend-chart {
  width: 100%;
  height: 250px;
}

.detail-btn {
  background: #52c41a;
}

.detail-btn:hover {
  background: #389e0d;
}
</style>
