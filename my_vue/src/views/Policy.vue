<template>
  <div class="policy-container">
    <div class="header-section">
      <h1 class="page-title">地方促消费政策展示</h1>
      <div class="header-controls">
        <button class="btn btn-gray" @click="resetMap">
          <i class="fas fa-redo mr-1"></i>重置地图
        </button>
        <button class="btn btn-gray" @click="exportPolicies">
          <i class="fas fa-download mr-1"></i>导出政策
        </button>
      </div>
    </div>

    <div class="content-section">
      <div class="map-section">
        <div class="map-header">
          <h2 class="section-title">全国政策分布图</h2>
          <p class="section-subtitle">点击省份或输入省份名称查看详细政策信息</p>
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
  },
  beforeDestroy() {
    if (this.chart) {
      this.chart.dispose()
    }
  },
  computed: {
    policySectionTitle() {
      if (this.selectedCity) {
        return `${this.selectedProvince}${this.selectedCity}`
      }
      return this.selectedProvince
    }
  },
  methods: {
    initChart() {
      this.chart = echarts.init(this.$refs.chinaMap)
      this.loadMapData()
      
      window.addEventListener('resize', this.handleResize)
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
</style>
