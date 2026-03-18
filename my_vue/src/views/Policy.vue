<template>
  <div class="policy-container">
    <div class="header-section">
      <h1 class="page-title">地方促消费政策展示</h1>

    </div>

      <!-- 数据统计仪表盘 -->
    <div class="dashboard-section">
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-icon total">
            <i class="fas fa-file-alt"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ totalPolicies }}</span>
            <span class="stat-label">全国政策总数</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon new">
            <i class="fas fa-check-circle"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ activePolicies }}</span>
            <span class="stat-label">有效政策数量</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon expiring">
            <i class="fas fa-globe"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ coveredProvinces }}</span>
            <span class="stat-label">覆盖省份数量</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon cities">
            <i class="fas fa-map-marker-alt"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ coveredCities }}</span>
            <span class="stat-label">覆盖城市数量</span>
          </div>
        </div>
      </div>
    </div>

    <div class="content-section">
      <div class="map-section">
        <div class="map-header">
          <div class="map-header-top">
            <div class="map-header-left">
              <h2 class="section-title">全国政策分布图</h2>
              <p class="section-subtitle">点击省份或输入省份名称查看详细政策信息</p>
            </div>
            <div class="header-controls">
              <button class="btn btn-gray" @click="resetMap">
                <i class="fas fa-redo mr-1"></i>重置地图
              </button>
              <button class="btn btn-gray" @click="exportPolicies">
                <i class="fas fa-download mr-1"></i>导出政策
              </button>
            </div>
          </div>
          
          <div class="province-search">
            <input
              type="text"
              v-model="searchQuery"
              @input="handleSearchInput"
              @focus="showSuggestions = true"
              @blur="hideSuggestions"
              placeholder="输入省份名称..."
              class="search-input"
            />
            <div v-if="showSuggestions && filteredProvinces.length > 0" class="suggestions-list">
              <div
                v-for="province in filteredProvinces"
                :key="province"
                class="suggestion-item"
                @mousedown="selectProvince(province)"
              >
                {{ province }}
              </div>
            </div>
          </div>
        </div>
        <div ref="chinaMap" class="china-map"></div>
        <div class="map-legend">
          <div class="legend-item">
            <span class="legend-color color-1"></span>
            <span class="legend-text">0-5项政策</span>
          </div>
          <div class="legend-item">
            <span class="legend-color color-2"></span>
            <span class="legend-text">6-10项政策</span>
          </div>
          <div class="legend-item">
            <span class="legend-color color-3"></span>
            <span class="legend-text">11-20项政策</span>
          </div>
          <div class="legend-item">
            <span class="legend-color color-4"></span>
            <span class="legend-text">20项以上政策</span>
          </div>
        </div>
      </div>

      <div class="policy-section" v-if="selectedProvince">
        <div class="policy-header">
          <h2 class="section-title">{{ policySectionTitle }}政策详情</h2>
          <p class="section-subtitle">共找到 {{ filteredPolicies.length }} 项政策</p>
          <div class="filter-row">
            <div class="city-search">
              <input
                type="text"
                v-model="citySearchQuery"
                @input="handleCitySearchInput"
                @focus="showCitySuggestions = true"
                @blur="hideCitySuggestions"
                placeholder="输入地级市/自治州名称"
                class="search-input"
              />
              <div v-if="showCitySuggestions && filteredCities.length > 0" class="suggestions-list">
                <div
                  v-for="city in filteredCities"
                  :key="city"
                  class="suggestion-item"
                  @mousedown="selectCity(city)"
                >
                  {{ city }}
                </div>
              </div>
            </div>
            <div class="category-filter">
              <select v-model="selectedCategory" @change="filterPoliciesByCategory" class="category-select">
                <option value="">全部分类</option>
                <option v-for="category in availableCategories" :key="category" :value="category">
                  {{ category }}
                </option>
              </select>
            </div>
          </div>
        </div>
        <div class="policy-list">
          <div v-if="loading" class="loading-container">
            <div class="loading-spinner"></div>
            <p class="loading-text">政策加载中...</p>
          </div>
          <div v-else-if="filteredPolicies.length === 0" class="empty-container">
            <i class="fas fa-file-alt empty-icon"></i>
            <p class="empty-text">暂无政策数据</p>
          </div>
          <div v-else class="policy-cards">
            <div v-for="(policy, index) in filteredPolicies" :key="index" class="policy-card">
              <div class="policy-card-header">
                <h3 class="policy-title">{{ policy['政策名称'] || '政策标题' }}</h3>
                <span class="policy-date">{{ policy['执行时间'] || '发布日期' }}</span>
              </div>
              <div class="policy-card-body">
                <div class="policy-info">
                  <div class="info-item">
                    <i class="fas fa-building info-icon"></i>
                    <span class="info-label">地区：</span>
                    <span class="info-value">{{ policy['省/直辖市/自治区'] || '未知' }}</span>
                  </div>
                  <div class="info-item">
                    <i class="fas fa-tag info-icon"></i>
                    <span class="info-label">政策分类：</span>
                    <span class="info-value">{{ policy['政策分类'] || '未知' }}</span>
                  </div>
                  <div class="info-item">
                    <i class="fas fa-calendar info-icon"></i>
                    <span class="info-label">执行时间：</span>
                    <span class="info-value">{{ policy['执行时间'] || '未说明' }}</span>
                  </div>
                  <div class="info-item">
                    <i class="fas fa-clock info-icon"></i>
                    <span class="info-label">结束时间：</span>
                    <span class="info-value">{{ policy['结束时间'] || '未说明' }}</span>
                  </div>
                </div>
                <div class="policy-content">
                  <h4 class="content-title">政策内容：</h4>
                  <p class="content-text">{{ policy['政策主要内容'] || '暂无详细内容' }}</p>
                </div>
                <div class="policy-actions">
                  <button class="btn btn-sm btn-primary" @click="viewPolicyDetail(policy)">
                    <i class="fas fa-eye mr-1"></i>查看详情
                  </button>
                  <a v-if="policy['原文链接']" :href="policy['原文链接']" target="_blank" class="btn btn-sm btn-secondary">
                    <i class="fas fa-external-link-alt mr-1"></i>查看原文
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="policy-section placeholder-section" v-else>
        <div class="placeholder-content">
          <i class="fas fa-map-marked-alt placeholder-icon"></i>
          <h3 class="placeholder-title">请选择省份</h3>
          <p class="placeholder-text">点击地图上的省份查看该地区的促消费政策</p>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">政策详情</h3>
          <button class="modal-close" @click="closeModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <h4 class="detail-title">政策名称</h4>
            <p class="detail-text">{{ currentPolicy['政策名称'] }}</p>
          </div>
          <div class="detail-section">
            <h4 class="detail-title">地区</h4>
            <p class="detail-text">{{ currentPolicy['省/直辖市/自治区'] }}</p>
          </div>
          <div class="detail-section">
            <h4 class="detail-title">地级市/自治州</h4>
            <p class="detail-text">{{ currentPolicy['地级市/自治州'] || '未说明' }}</p>
          </div>
          <div class="detail-section">
            <h4 class="detail-title">政策分类</h4>
            <p class="detail-text">{{ currentPolicy['政策分类'] }}</p>
          </div>
          <div class="detail-section">
            <h4 class="detail-title">执行时间</h4>
            <p class="detail-text">{{ currentPolicy['执行时间'] }}</p>
          </div>
          <div class="detail-section">
            <h4 class="detail-title">结束时间</h4>
            <p class="detail-text">{{ currentPolicy['结束时间'] }}</p>
          </div>
          <div class="detail-section">
            <h4 class="detail-title">政策主要内容</h4>
            <p class="detail-text">{{ currentPolicy['政策主要内容'] }}</p>
          </div>
          <div class="detail-section" v-if="currentPolicy['原文链接']">
            <h4 class="detail-title">原文链接</h4>
            <a :href="currentPolicy['原文链接']" target="_blank" class="detail-link">{{ currentPolicy['原文链接'] }}</a>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">关闭</button>
        </div>
      </div>
    </div>   

    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="chart-card trend-card">
        <div class="chart-header">
          <h3 class="chart-title">政策发布趋势</h3>
          <p class="chart-subtitle">各月份政策发布数量分布</p>
        </div>
        <div ref="trendChart" class="chart-container"></div>
      </div>
      <div class="chart-card pie-card">
        <div class="chart-header">
          <h3 class="chart-title">政策类型分布</h3>
          <p class="chart-subtitle">各类型政策占比情况</p>
        </div>
        <div ref="pieChart" class="chart-container"></div>
      </div>
      <div class="chart-card ranking-card">
        <div class="chart-header">
          <h3 class="chart-title">政策热度排行榜</h3>
          <p class="chart-subtitle">TOP 15 政策活跃省份</p>
        </div>
        <div class="ranking-list">
          <div 
            v-for="(item, index) in top10Provinces" 
            :key="item.name" 
            class="ranking-item"
            :class="{ 'top-three': index < 3 }"
          >
            <span class="ranking-number" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
            <span class="ranking-name">{{ item.name }}</span>
            <div class="ranking-bar-container">
              <div class="ranking-bar" :style="{ width: (item.value / top10Provinces[0].value * 100) + '%' }"></div>
            </div>
            <span class="ranking-value">{{ item.value }}项</span>
          </div>
        </div>
      </div>
      <div class="category-stats-card">
        <div class="chart-header">
          <h3 class="chart-title">政策分类统计</h3>
          <p class="chart-subtitle">各类型政策数量分布</p>
        </div>
        <div class="category-cards-grid">
          <div 
            v-for="(stat, category) in categoryStats" 
            :key="category" 
            class="category-card"
          >
            <div class="category-icon">
              <i :class="getCategoryIcon(category)"></i>
            </div>
            <div class="category-info">
              <span class="category-name">{{ category }}</span>
              <span class="category-count">{{ stat.count }}项政策</span>
            </div>
            <div class="category-percentage">{{ stat.percentage }}%</div>
          </div>
        </div>
      </div>
    </div>

    
  </div>
</template>

<script>
import * as echarts from 'echarts'
import axios from 'axios'
import * as XLSX from 'xlsx'

export default {
  name: 'Policy',
  data() {
    return {
      chart: null,
      trendChart: null,
      pieChart: null,
      selectedProvince: null,
      policyData: [],
      filteredPolicies: [],
      loading: false,
      showModal: false,
      currentPolicy: {},
      searchQuery: '',
      showSuggestions: false,
      filteredProvinces: [],
      citySearchQuery: '',
      showCitySuggestions: false,
      filteredCities: [],
      selectedCity: null,
      selectedCategory: '',
      availableCategories: [],
      provinceMapping: {
        '北京': '北京市',
        '天津': '天津市',
        '河北': '河北省',
        '山西': '山西省',
        '内蒙古': '内蒙古自治区',
        '辽宁': '辽宁省',
        '吉林': '吉林省',
        '黑龙江': '黑龙江省',
        '上海': '上海市',
        '江苏': '江苏省',
        '浙江': '浙江省',
        '安徽': '安徽省',
        '福建': '福建省',
        '江西': '江西省',
        '山东': '山东省',
        '河南': '河南省',
        '湖北': '湖北省',
        '湖南': '湖南省',
        '广东': '广东省',
        '广西': '广西壮族自治区',
        '海南': '海南省', 
        '重庆': '重庆市',
        '四川': '四川省',
        '贵州': '贵州省',
        '云南': '云南省',
        '西藏': '西藏自治区',
        '陕西': '陕西省',
        '甘肃': '甘肃省',
        '青海': '青海省',
        '宁夏': '宁夏回族自治区',
        '新疆': '新疆维吾尔自治区',
        '台湾': '台湾省',
        '香港': '香港特别行政区',
        '澳门': '澳门特别行政区',
        '南海诸岛':'南海诸岛',
      }
    }
  },
  async mounted() {
    await this.loadPolicyData()
    this.initChart()
    this.$nextTick(() => {
      this.initTrendChart()
      this.initPieChart()
    })
  },
  beforeDestroy() {
    if (this.chart) {
      this.chart.dispose()
    }
    if (this.trendChart) {
      this.trendChart.dispose()
    }
    if (this.pieChart) {
      this.pieChart.dispose()
    }
  },
  computed: {
    policySectionTitle() {
      if (this.selectedCity) {
        return `${this.selectedProvince}${this.selectedCity}`
      }
      return this.selectedProvince
    },
    totalPolicies() {
      return this.policyData.length
    },
    activePolicies() {
      const now = new Date()
      return this.policyData.filter(policy => {
        const endTime = policy['结束时间']
        if (!endTime) return true
        const endDate = new Date(endTime)
        return endDate >= now
      }).length
    },
    coveredProvinces() {
      const provinces = new Set()
      this.policyData.forEach(policy => {
        const province = policy['省/直辖市/自治区']
        if (province) {
          provinces.add(province)
        }
      })
      return provinces.size
    },
    coveredCities() {
      const cities = new Set()
      this.policyData.forEach(policy => {
        const city = policy['地级市/自治州']
        const province = policy['省/直辖市/自治区']
        if (city) {
          cities.add(`${province}-${city}`)
        } else if (province) {
          cities.add(province)
        }
      })
      return cities.size
    },
    top10Provinces() {
      const counts = this.getProvinceCounts()
      return Object.entries(counts)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 15)
    },
    categoryStats() {
      const stats = {}
      const total = this.policyData.length || 1
      this.policyData.forEach(policy => {
        const category = policy['政策分类'] || '其他'
        if (!stats[category]) {
          stats[category] = { count: 0, percentage: 0 }
        }
        stats[category].count++
      })
      Object.keys(stats).forEach(category => {
        stats[category].percentage = ((stats[category].count / total) * 100).toFixed(1)
      })
      return stats
    },
    monthlyTrendData() {
      const monthlyData = {}
      this.policyData.forEach(policy => {
        const execTime = policy['执行时间']
        if (execTime) {
          const date = new Date(execTime)
          const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
          monthlyData[monthKey] = (monthlyData[monthKey] || 0) + 1
        }
      })
      const sortedMonths = Object.keys(monthlyData).sort()
      return {
        months: sortedMonths,
        values: sortedMonths.map(m => monthlyData[m])
      }
    },
    categoryPieData() {
      const data = []
      Object.entries(this.categoryStats).forEach(([name, stat]) => {
        data.push({ name, value: stat.count })
      })
      return data
    }
  },
  methods: {
    initChart() {
      this.chart = echarts.init(this.$refs.chinaMap)
      this.loadMapData()
      
      window.addEventListener('resize', this.handleResize)
    },
    
    initTrendChart() {
      if (!this.$refs.trendChart) return
      this.trendChart = echarts.init(this.$refs.trendChart)
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: this.monthlyTrendData.months,
          axisLabel: {
            rotate: 45,
            fontSize: 10
          }
        },
        yAxis: {
          type: 'value',
          minInterval: 1
        },
        series: [{
          name: '政策数量',
          type: 'line',
          smooth: true,
          data: this.monthlyTrendData.values,
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(54, 162, 235, 0.5)' },
                { offset: 1, color: 'rgba(54, 162, 235, 0.1)' }
              ]
            }
          },
          lineStyle: {
            color: '#36a2eb',
            width: 2
          },
          itemStyle: {
            color: '#36a2eb'
          }
        }]
      }
      this.trendChart.setOption(option)
    },
    
    initPieChart() {
      if (!this.$refs.pieChart) return
      this.pieChart = echarts.init(this.$refs.pieChart)
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}项 ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: '1%',
          top: 'center',
          textStyle: {
            fontSize: 11
          }
        },
        series: [{
          name: '政策类型',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['30%', '50%'],
          avoidLabelOverlap: false,
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: this.categoryPieData,
          color: ['#36a2eb', '#ff6384', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40', '#c9cbcf']
        }]
      }
      this.pieChart.setOption(option)
    },
    
    getCategoryIcon(category) {
      const iconMap = {
        '消费券': 'fas fa-ticket-alt',
        '补贴': 'fas fa-hand-holding-usd',
        '以旧换新': 'fas fa-exchange-alt',
        '下乡补贴': 'fas fa-tractor',
        '充电设施': 'fas fa-charging-station',
        '购置税减免': 'fas fa-receipt',
        '其他': 'fas fa-file-alt'
      }
      return iconMap[category] || 'fas fa-file-alt'
    },
    
    async loadMapData() {
      try {
        const response = await axios.get('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
        echarts.registerMap('china', response.data)
        this.renderMap()
      } catch (error) {
        console.error('加载地图数据失败:', error)
      }
    },
    
    async loadPolicyData() {
      this.loading = true
      try {
        const response = await axios.get('/api/policies')
        this.policyData = response.data
      } catch (error) {
        console.error('加载政策数据失败:', error)
        this.policyData = this.getMockPolicyData()
      } finally {
        this.loading = false
      }
    },
    
    getMockPolicyData() {
      return [
        {
          '省/直辖市/自治区': '北京市',
          '政策名称': '北京市汽车消费券发放政策',
          '政策分类': '消费券',
          '执行时间': '2024-03-01',
          '结束时间': '2024-12-31',
          '政策主要内容': '对购买新能源乘用车的消费者，给予最高10000元的消费券补贴。'
        },
        {
          '省/直辖市/自治区': '上海市',
          '政策名称': '上海市新能源汽车推广应用补贴',
          '政策分类': '补贴',
          '执行时间': '2024-02-15',
          '结束时间': '2024-12-31',
          '政策主要内容': '对购买符合条件的新能源汽车，给予最高15000元的财政补贴。'
        },
        {
          '省/直辖市/自治区': '广东省',
          '政策名称': '广东省汽车以旧换新补贴政策',
          '政策分类': '以旧换新',
          '执行时间': '2024-01-20',
          '结束时间': '2024-12-31',
          '政策主要内容': '对报废旧车并购买新车的消费者，给予最高8000元的补贴。'
        },
        {
          '省/直辖市/自治区': '江苏省',
          '政策名称': '江苏省汽车下乡补贴政策',
          '政策分类': '下乡补贴',
          '执行时间': '2024-03-10',
          '结束时间': '2024-12-31',
          '政策主要内容': '对农村居民购买指定车型，给予最高6000元的下乡补贴。'
        },
        {
          '省/直辖市/自治区': '浙江省',
          '政策名称': '浙江省新能源汽车充电设施建设补贴',
          '政策分类': '充电设施',
          '执行时间': '2024-02-28',
          '结束时间': '2024-12-31',
          '政策主要内容': '对建设新能源汽车充电设施的单位和个人，给予最高5000元的补贴。'
        }
      ]
    },
    
    renderMap() {
      const provinceCounts = this.getProvinceCounts()
      const data = Object.keys(provinceCounts).map(province => ({
        name: this.provinceMapping[province],
        value: provinceCounts[province]
      }))
      const maxValue = Math.max(...Object.values(provinceCounts), 20)
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: (params)=> {
            return `${params.name}<br/>政策数量：${params.value}项`
          }
        },
        visualMap: {
          min: 0,
          max: maxValue,
          left: 'left',
          bottom: 'bottom',
          text: ['高', '低'],
          calculable: true,
          inRange: {
            color: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4']
          },
          pieces: [  // 使用 pieces 来定义分段
            { min: 0, max: 5, color: '#e0f3f8', label: '0-5项政策' },
            { min: 6, max: 10, color: '#abd9e9', label: '6-10项政策' },
            { min: 11, max: 20, color: '#74add1', label: '11-20项政策' },
            { min: 21, color: '#4575b4', label: '20项以上政策' }
          ]
        },
        series: [
          {
            name: '政策数量',
            type: 'map',
            map: 'china',
            roam: true,
            emphasis: {
              label: {
                show: true
              },
              itemStyle: {
                areaColor: '#f4d03f'
              }
            },
            select: {
              itemStyle: {
                areaColor: '#f39c12'
              }
            },
            data: data
          }
        ]
      }
      
      this.chart.setOption(option)
      
      this.chart.on('click', (params) => {
        if (params.name) {
          this.handleProvinceClick(params.name)
        }
      })
    },
    
    getProvinceCounts() {
      const counts = {}
      
      this.policyData.forEach(policy => {
        const province = policy["省/直辖市/自治区"] || ''
        if (province) {
          counts[province] = (counts[province] || 0) + 1
        }
      }) 
      /* 确保所有省份都有计数 */
      const allProvinces = Object.keys(this.provinceMapping)
      allProvinces.forEach(province => {
        if (!counts[province]) {
          counts[province] = 0
        }
      })
      return counts
    },
    
    handleProvinceClick(provinceName) {
      this.selectedProvince = provinceName
      this.citySearchQuery = ''
      this.selectedCity = null
      this.selectedCategory = ''
      this.updateAvailableCategories()
      this.filterPolicies(provinceName)
    },
    
    filterPolicies(provinceName) {
      this.loading = true
      setTimeout(() => {
        const filtered = this.policyData.filter(
          policy => policy['省/直辖市/自治区'] === provinceName
        )

        // 尝试模糊匹配
        if (filtered.length === 0) {
          const fuzzyFiltered = this.policyData.filter(
            policy => {
              const province = policy['省/直辖市/自治区'] || ''
              return province.includes(provinceName) || provinceName.includes(province)
            }
          )
          this.filteredPolicies = fuzzyFiltered
        } else {
          this.filteredPolicies = filtered
        }
        this.loading = false
      }, 300)
    },
    
    resetMap() {
      this.selectedProvince = null
      this.filteredPolicies = []
      this.searchQuery = ''
      this.filteredProvinces = []
      this.citySearchQuery = ''
      this.filteredCities = []
      this.selectedCity = null
      this.selectedCategory = ''
      this.availableCategories = []
      this.chart.dispatchAction({
        type: 'downplay'
      })
      this.chart.dispatchAction({
        type: 'unSelect'
      })
    },
    
    viewPolicyDetail(policy) {
      this.currentPolicy = policy
      this.showModal = true
    },
    
    closeModal() {
      this.showModal = false
      this.currentPolicy = {}
    },
    
    exportPolicies() {
      if (!this.selectedProvince) {
        alert('请先选择省份')
        return
      }
      
      if (this.filteredPolicies.length === 0) {
        alert('该省份暂无政策数据可导出')
        return
      }

      const exportData = this.filteredPolicies.map(policy => ({
        '政策名称': policy['政策名称'] || '',
        '地区': policy['省/直辖市/自治区'] || '',
        '地级市/自治州': policy['地级市/自治州'] || '',
        '政策分类': policy['政策分类'] || '',
        '执行时间': policy['执行时间'] || '',
        '结束时间': policy['结束时间'] || '',
        '政策主要内容': policy['政策主要内容'] || '',
        '原文链接': policy['原文链接'] || ''
      }))

      const ws = XLSX.utils.json_to_sheet(exportData)
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, '政策数据')
      
      const fileName = `${this.selectedProvince}政策数据_${new Date().getTime()}.xlsx`
      XLSX.writeFile(wb, fileName)
      
      alert(`成功导出${this.filteredPolicies.length}项政策数据`)
    },
    
    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
      if (this.trendChart) {
        this.trendChart.resize()
      }
      if (this.pieChart) {
        this.pieChart.resize()
      }
    },
    
    handleSearchInput() {
      if (!this.searchQuery.trim()) {
        this.filteredProvinces = []
        return
      }
      const query = this.searchQuery.trim().toLowerCase()
      const allProvinces = Object.values(this.provinceMapping)
      this.filteredProvinces = allProvinces.filter(province => 
        province.toLowerCase().includes(query)
      ).slice(0, 8)
    },
    
    hideSuggestions() {
      setTimeout(() => {
        this.showSuggestions = false
      }, 200)
    },
    
    selectProvince(provinceName) {
      this.searchQuery = provinceName
      this.showSuggestions = false
      this.selectedProvince = provinceName
      this.citySearchQuery = ''
      this.selectedCity = null
      this.filteredCities = []
      this.selectedCategory = ''
      this.updateAvailableCategories()
      this.filterPolicies(provinceName)
      this.highlightProvinceOnMap(provinceName)
    },
    
    highlightProvinceOnMap(provinceName) {
      if (!this.chart) return
      this.chart.dispatchAction({
        type: 'downplay'
      })
      this.chart.dispatchAction({
        type: 'unSelect'
      })
      this.chart.dispatchAction({
        type: 'select',
        name: provinceName
      })
    },
    
    getAvailableCities(provinceName) {
      const cities = new Set()
      this.policyData.forEach(policy => {
        const province = policy['省/直辖市/自治区'] || ''
        if (province === provinceName || province.includes(provinceName) || provinceName.includes(province)) {
          const city = policy['地级市/自治州']
          if (city && city.trim()) {
            cities.add(city.trim())
          }
        }
      })
      return Array.from(cities).sort()
    },
    
    handleCitySearchInput() {
      const query = this.citySearchQuery.trim().toUpperCase()
      if (query === 'ALL' || query === '') {
        this.filteredCities = ['ALL（显示全部）']
        return
      }
      const availableCities = this.getAvailableCities(this.selectedProvince)
      const searchQuery = this.citySearchQuery.trim().toLowerCase()
      this.filteredCities = availableCities.filter(city => 
        city.toLowerCase().includes(searchQuery)
      ).slice(0, 8)
      if (this.filteredCities.length === 0) {
        this.filteredCities = ['ALL（显示全部）']
      }
    },
    
    hideCitySuggestions() {
      setTimeout(() => {
        this.showCitySuggestions = false
      }, 200)
    },
    
    selectCity(city) {
      if (city === 'ALL（显示全部）') {
        this.citySearchQuery = ''
        this.selectedCity = null
      } else {
        this.citySearchQuery = city
        this.selectedCity = city
      }
      this.showCitySuggestions = false
      this.filterPoliciesByCity()
    },
    
    filterPoliciesByCity() {
      this.applyFilters()
    },
    
    filterPoliciesByCategory() {
      this.applyFilters()
    },
    
    applyFilters() {
      if (!this.selectedProvince) return
      
      this.loading = true
      setTimeout(() => {
        let filtered = this.policyData.filter(policy => {
          const province = policy['省/直辖市/自治区'] || ''
          return province === this.selectedProvince || 
                 province.includes(this.selectedProvince) || 
                 this.selectedProvince.includes(province)
        })
        
        if (this.selectedCity) {
          filtered = filtered.filter(policy => {
            const city = (policy['地级市/自治州'] || '').trim().toUpperCase()
            const selectedCityUpper = this.selectedCity.trim().toUpperCase()
            return city === selectedCityUpper || city === 'ALL' || city === ''
          })
        }
        
        if (this.selectedCategory) {
          filtered = filtered.filter(policy => {
            const category = policy['政策分类'] || ''
            return category === this.selectedCategory
          })
        }
        
        this.filteredPolicies = filtered
        this.loading = false
      }, 300)
    },
    
    updateAvailableCategories() {
      const categories = new Set()
      this.policyData.forEach(policy => {
        const province = policy['省/直辖市/自治区'] || ''
        if (province === this.selectedProvince || 
            province.includes(this.selectedProvince) || 
            this.selectedProvince.includes(province)) {
          const category = policy['政策分类']
          if (category && category.trim()) {
            categories.add(category.trim())
          }
        }
      })
      this.availableCategories = Array.from(categories).sort()
    }
  }
}
</script>

<style scoped>
.policy-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

/* 数据统计仪表盘样式 */
.dashboard-section {
  margin-bottom: 20px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.total {
  background: #e8f4fd;
  color: #1890ff;
}

.stat-icon.new {
  background: #f6ffed;
  color: #52c41a;
}

.stat-icon.expiring {
  background: #fff7e6;
  color: #fa8c16;
}

.stat-icon.cities {
  background: #e6fffb;
  color: #13c2c2;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

/* 图表区域样式 */
.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.trend-card {
  grid-column: 1;
  grid-row: 1;
}

.pie-card {
  grid-column: 2;
  grid-row: 1;
}

.ranking-card {
  grid-column: 3;
  grid-row: 1 / 3;
  display: flex;
  flex-direction: column;
}

.category-stats-card {
  grid-column: 1 / 3;
  grid-row: 2;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.chart-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.chart-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.chart-subtitle {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #999;
}

.chart-container {
  height: 250px;

}

/* 排行榜样式 */
.ranking-list {
  flex: 1;
  padding: 12px 20px;
  overflow-y: auto;
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}

.ranking-item:last-child {
  border-bottom: none;
}

.ranking-item.top-three {
  background: linear-gradient(90deg, #fff9e6 0%, transparent 100%);
  margin: 0 -20px;
  padding: 10px 20px;
}

.ranking-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #999;
  background: #f0f0f0;
  margin-right: 12px;
  flex-shrink: 0;
}

.ranking-number.rank-1 {
  background: linear-gradient(135deg, #ffd700 0%, #ffb347 100%);
  color: white;
}

.ranking-number.rank-2 {
  background: linear-gradient(135deg, #c0c0c0 0%, #a8a8a8 100%);
  color: white;
}

.ranking-number.rank-3 {
  background: linear-gradient(135deg, #cd7f32 0%, #b87333 100%);
  color: white;
}

.ranking-name {
  flex: 0 0 80px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.ranking-bar-container {
  flex: 1;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  margin: 0 12px;
  overflow: hidden;
}

.ranking-bar {
  height: 100%;
  background: #1890ff;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.ranking-value {
  flex: 0 0 50px;
  font-size: 14px;
  color: #666;
  text-align: right;
}

.category-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  padding: 16px 20px;
}

.category-card {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  background: #f8f9fa;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.category-card:hover {
  background: #f0f4ff;
  transform: translateX(4px);
}

.category-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #f0f5ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2f54eb;
  font-size: 18px;
  margin-right: 12px;
}

.category-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.category-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.category-count {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.category-percentage {
  font-size: 16px;
  font-weight: 600;
  color: #667eea;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.header-controls {
  display: flex;
  gap: 10px;
}

.content-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.map-section {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  min-width: 600px;
}

.map-header {
  margin-bottom: 20px;
}

.map-header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.map-header-left {
  flex: 1;
}

.province-search {
  position: relative;
  margin-top: 15px;
}

.search-input {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.search-input:focus {
  border-color: #3498db;
}

.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-top: none;
  border-radius: 0 0 4px 4px;
  max-height: 250px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.suggestion-item {
  padding: 10px 15px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.suggestion-item:hover {
  background-color: #f5f5f5;
}

.filter-row {
  display: flex;
  gap: 15px;
  margin-top: 15px;
}

.city-search {
  position: relative;
  flex: 1;
  max-width: 290px;
}

.category-filter {
  flex: 1;
  max-width: 150px;
}

.category-select {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
  background: white;
  cursor: pointer;
  box-sizing: border-box;
}

.category-select:focus {
  border-color: #3498db;
}

.section-title {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.section-subtitle {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.china-map {
  width: 100%;
  height: 500px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.map-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 15px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
}

.legend-color.color-1 {
  background: #e0f3f8;
}

.legend-color.color-2 {
  background: #abd9e9;
}

.legend-color.color-3 {
  background: #74add1;
}

.legend-color.color-4 {
  background: #4575b4;
}

.legend-text {
  font-size: 12px;
  color: #666;
}

.policy-section {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  min-width: 400px;
  max-width: 500px;
}

.policy-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.policy-list {
  max-height: 600px;
  overflow-y: auto;
}

.loading-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text,
.empty-text {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.empty-icon {
  font-size: 48px;
  color: #ddd;
  margin-bottom: 15px;
}

.policy-cards {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.policy-card {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
  background: #fafafa;
  transition: all 0.3s;
}

.policy-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.policy-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.policy-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  flex: 1;
}

.policy-date {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
  margin-left: 10px;
}

.policy-card-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.policy-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item {
  display: flex;
  align-items: center;
  font-size: 12px;
}

.info-icon {
  width: 16px;
  color: #3498db;
  margin-right: 8px;
}

.info-label {
  color: #666;
  margin-right: 5px;
}

.info-value {
  color: #333;
  font-weight: 500;
}

.policy-content {
  margin-top: 5px;
}

.content-title {
  margin: 0 0 5px 0;
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.content-text {
  margin: 0;
  font-size: 12px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.policy-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-gray {
  background: #f0f0f0;
  color: #333;
}

.btn-gray:hover {
  background: #e0e0e0;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover {
  background: #2980b9;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.mr-1 {
  margin-right: 4px;
}

.placeholder-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 500px;
}

.placeholder-content {
  text-align: center;
  padding: 40px;
}

.placeholder-icon {
  font-size: 64px;
  color: #ddd;
  margin-bottom: 20px;
}

.placeholder-title {
  margin: 0 0 10px 0;
  font-size: 18px;
  color: #666;
}

.placeholder-text {
  margin: 0;
  font-size: 14px;
  color: #999;
}

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
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.detail-text {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.detail-link {
  color: #3498db;
  text-decoration: none;
  word-break: break-all;
}

.detail-link:hover {
  text-decoration: underline;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
}

/* 响应式样式 */
@media (max-width: 1400px) {
  .charts-section {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto auto;
  }
  
  .trend-card {
    grid-column: 1;
    grid-row: 1;
  }
  
  .pie-card {
    grid-column: 2;
    grid-row: 1;
  }
  
  .category-stats-card {
    grid-column: 1 / 3;
    grid-row: 2;
  }
  
  .ranking-card {
    grid-column: 1 / 3;
    grid-row: 3;
  }
}

@media (max-width: 1200px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-section {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }
  
  .trend-card,
  .pie-card,
  .category-stats-card,
  .ranking-card {
    grid-column: 1;
    grid-row: auto;
  }
  
  .content-section {
    flex-direction: column;
  }
  
  .map-section {
    min-width: auto;
  }
}

@media (max-width: 768px) {
  .stat-cards {
    grid-template-columns: 1fr;
  }
  
  .header-section {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .header-controls {
    width: 100%;
    justify-content: flex-end;
  }
  
  .map-header-top {
    flex-direction: column;
    gap: 15px;
  }
  
  .map-header-top .header-controls {
    width: auto;
  }
  
  .category-cards-grid {
    grid-template-columns: 1fr;
  }
}
</style>
