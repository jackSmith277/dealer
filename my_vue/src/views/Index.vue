<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>经销商数据可视化平台</h1>
      <div class="header-info">
        <span class="total-dealers">全国门店总数：<strong>{{ totalDealers }}</strong> 家</span>
      </div>
    </header>

    <main class="dashboard-main">
      <div class="row row-top">
        <div class="col-left">
          <div class="card radar-card">
            <div class="card-header">
              <h3>五力雷达图</h3>
              <span class="sub-title">全国门店五力评分均值</span>
            </div>
            <div class="card-body">
              <div ref="radarChart" class="chart-container"></div>
            </div>
          </div>
        </div>

        <div class="col-center">
          <div class="card map-card">
            <div class="card-header">
              <h3>门店分布情况</h3>
              <span class="sub-title">{{ mapTitle }}</span>
            </div>
            <div class="map-filter-bar">
              <div class="filter-group">
                <label>区域：</label>
                <select v-model="mapFilters.region" @change="updateMapData">
                  <option value="all">全国</option>
                  <option value="east">华东区</option>
                  <option value="south">华南区</option>
                  <option value="north">华北区</option>
                  <option value="southwest">西南区</option>
                  <option value="northwest">西北区</option>
                  <option value="northeast">东北区</option>
                  <option value="central">华中区</option>
                </select>
              </div>
              <div class="filter-group">
                <label>门店类型：</label>
                <select v-model="mapFilters.storeType" @change="updateMapData">
                  <option value="all">全部</option>
                  <option value="direct">直营</option>
                  <option value="franchise">加盟</option>
                </select>
              </div>
              <div class="filter-group">
                <label>达标状态：</label>
                <select v-model="mapFilters.achieveStatus" @change="updateMapData">
                  <option value="all">全部</option>
                  <option value="achieved">达标</option>
                  <option value="notAchieved">未达标</option>
                </select>
              </div>
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
            <div class="card-body">
              <div ref="chinaMap" class="map-container"></div>
            </div>
          </div>
        </div>

        <div class="col-right">
          <div class="card ranking-card">
            <div class="card-header">
              <h3>门店排名</h3>
              <span class="sub-title">按五力总评分排名 TOP10</span>
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
        </div>
      </div>

      <div class="row row-bottom">
        <div class="col-left">
          <div class="card pie-card">
            <div class="card-header">
              <h3>门店评分统计</h3>
              <span class="sub-title">不同评分区间门店分布</span>
            </div>
            <div class="card-body">
              <div ref="pieChart" class="chart-container"></div>
            </div>
          </div>
        </div>

        <div class="col-center">
          <div class="card line-card">
            <div class="card-header">
              <h3>月度趋势图</h3>
              <span class="sub-title">10个月各项指标均值</span>
            </div>
            <div class="card-body">
              <div ref="lineChart" class="chart-container"></div>
            </div>
          </div>
        </div>

        <div class="col-right">
          <div class="card warning-card">
            <div class="card-header">
              <h3>门店预警</h3>
              <span class="sub-title">按评分等级分类</span>
            </div>
            <div class="card-body">
              <div class="warning-sections">
                <div class="warning-section warning-red">
                  <div class="warning-header">
                    <span class="warning-icon">!</span>
                    <span class="warning-title">高风险门店</span>
                    <span class="warning-count">{{ warningRed.length }}家</span>
                  </div>
                  <div class="warning-list">
                    <div v-for="item in warningRed.slice(0, 5)" :key="item.code" class="warning-item">
                      <span class="dealer-code">{{ item.code }}</span>
                      <span class="dealer-score">{{ item.totalScore.toFixed(2) }}分</span>
                    </div>
                    <div v-if="warningRed.length > 5" class="warning-more">
                      还有 {{ warningRed.length - 5 }} 家...
                    </div>
                  </div>
                </div>

                <div class="warning-section warning-orange">
                  <div class="warning-header">
                    <span class="warning-icon">!</span>
                    <span class="warning-title">中风险门店</span>
                    <span class="warning-count">{{ warningOrange.length }}家</span>
                  </div>
                  <div class="warning-list">
                    <div v-for="item in warningOrange.slice(0, 5)" :key="item.code" class="warning-item">
                      <span class="dealer-code">{{ item.code }}</span>
                      <span class="dealer-score">{{ item.totalScore.toFixed(2) }}分</span>
                    </div>
                    <div v-if="warningOrange.length > 5" class="warning-more">
                      还有 {{ warningOrange.length - 5 }} 家...
                    </div>
                  </div>
                </div>

                <div class="warning-section warning-green">
                  <div class="warning-header">
                    <span class="warning-icon">✓</span>
                    <span class="warning-title">健康门店</span>
                    <span class="warning-count">{{ warningGreen.length }}家</span>
                  </div>
                  <div class="warning-list">
                    <div v-for="item in warningGreen.slice(0, 5)" :key="item.code" class="warning-item">
                      <span class="dealer-code">{{ item.code }}</span>
                      <span class="dealer-score">{{ item.totalScore.toFixed(2) }}分</span>
                    </div>
                    <div v-if="warningGreen.length > 5" class="warning-more">
                      还有 {{ warningGreen.length - 5 }} 家...
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
        <div class="modal-filter-info">
          <span>筛选条件：</span>
          <span class="filter-tag" v-if="mapFilters.storeType !== 'all'">
            {{ mapFilters.storeType === 'direct' ? '直营' : '加盟' }}
          </span>
          <span class="filter-tag" v-if="mapFilters.achieveStatus !== 'all'">
            {{ mapFilters.achieveStatus === 'achieved' ? '达标' : '未达标' }}
          </span>
          <span class="filter-tag" v-if="mapFilters.region !== 'all'">
            {{ getRegionName(mapFilters.region) }}
          </span>
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
                  <option value="achieveRate">按达标率</option>
                </select>
              </div>
            </div>
            <div class="store-table-wrapper">
              <table class="store-table">
                <thead>
                  <tr>
                    <th>门店名称</th>
                    <th>类型</th>
                    <th>达标</th>
                    <th>销量</th>
                    <th>评分</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="store in sortedProvinceStores" :key="store.id">
                    <td>{{ store.name }}</td>
                    <td>{{ store.storeType === 'direct' ? '直营' : '加盟' }}</td>
                    <td :class="store.achieveStatus === 'achieved' ? 'achieved' : 'not-achieved'">
                      {{ store.achieveStatus === 'achieved' ? '是' : '否' }}
                    </td>
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
import fiveForcesData from '@/assets/fiveForcesData.json'
import dealerData from '@/assets/dealerData.json'

export default {
  name: 'Index',
  data() {
    return {
      radarChart: null,
      lineChart: null,
      pieChart: null,
      mapChart: null,
      trendChart: null,
      fiveForcesData: [],
      dealerData: [],
      totalDealers: 0,
      provinceDealerCount: {},
      mapLevel: 'country',
      currentProvince: '',
      currentCity: '',
      mapFilters: {
        storeType: 'all',
        achieveStatus: 'all',
        region: 'all'
      },
      mapStack: [],
      mockStoreData: [],
      showStoreDetailModal: false,
      selectedProvince: '',
      storeSortBy: 'sales'
    }
  },
  computed: {
    radarData() {
      if (this.fiveForcesData.length === 0) return []
      const avgPropagation = this.fiveForcesData.reduce((sum, d) => sum + (d['传播获客力'] || 0), 0) / this.fiveForcesData.length
      const avgExperience = this.fiveForcesData.reduce((sum, d) => sum + (d['体验力'] || 0), 0) / this.fiveForcesData.length
      const avgConversion = this.fiveForcesData.reduce((sum, d) => sum + (d['转化力'] || 0), 0) / this.fiveForcesData.length
      const avgService = this.fiveForcesData.reduce((sum, d) => sum + (d['服务力'] || 0), 0) / this.fiveForcesData.length
      const avgOperation = this.fiveForcesData.reduce((sum, d) => sum + (d['经营力'] || 0), 0) / this.fiveForcesData.length
      return [
        { name: '传播获客力', value: avgPropagation.toFixed(2) },
        { name: '体验力', value: avgExperience.toFixed(2) },
        { name: '转化力', value: avgConversion.toFixed(2) },
        { name: '服务力', value: avgService.toFixed(2) },
        { name: '经营力', value: avgOperation.toFixed(2) }
      ]
    },
    rankingData() {
      if (this.fiveForcesData.length === 0) return []
      const withTotal = this.fiveForcesData.map(d => ({
        code: d['经销商代码'],
        province: d['省份'],
        totalScore: (d['传播获客力'] || 0) + (d['体验力'] || 0) + (d['转化力'] || 0) + (d['服务力'] || 0) + (d['经营力'] || 0)
      }))
      return withTotal.sort((a, b) => b.totalScore - a.totalScore).slice(0, 10)
    },
    warningRed() {
      return this.getDealersByScoreRange(0, 15)
    },
    warningOrange() {
      return this.getDealersByScoreRange(15, 20)
    },
    warningGreen() {
      return this.getDealersByScoreRange(20, 25)
    },
    pieData() {
      return [
        { name: '高风险 (总分<15)', value: this.warningRed.length, color: '#ff4d4f' },
        { name: '中风险 (15≤总分<20)', value: this.warningOrange.length, color: '#fa8c16' },
        { name: '健康 (总分≥20)', value: this.warningGreen.length, color: '#52c41a' }
      ]
    },
    mapTitle() {
      if (this.mapLevel === 'country') return '全国门店地理分布'
      if (this.mapLevel === 'province') return `${this.currentProvince}门店分布`
      if (this.mapLevel === 'city') return `${this.currentCity}门店分布`
      return '门店地理分布'
    },
    currentLocation() {
      if (this.mapLevel === 'country') return '全国'
      if (this.mapLevel === 'province') return this.currentProvince
      if (this.mapLevel === 'city') return `${this.currentProvince} > ${this.currentCity}`
      return ''
    },
    sortedProvinceStores() {
      let stores = this.getFilteredStoreData().filter(s => s.province === this.selectedProvince)
      if (this.storeSortBy === 'sales') {
        stores.sort((a, b) => b.sales - a.sales)
      } else if (this.storeSortBy === 'totalScore') {
        stores.sort((a, b) => b.totalScore - a.totalScore)
      } else if (this.storeSortBy === 'achieveRate') {
        stores.sort((a, b) => {
          const aRate = a.achieveStatus === 'achieved' ? 1 : 0
          const bRate = b.achieveStatus === 'achieved' ? 1 : 0
          return bRate - aRate
        })
      }
      return stores
    },
    top10Stores() {
      return this.sortedProvinceStores.slice(0, 10)
    },
    bottom10Stores() {
      return this.sortedProvinceStores.slice(-10).reverse()
    }
  },
  mounted() {
    this.loadData()
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
    loadData() {
      this.fiveForcesData = fiveForcesData
      this.dealerData = dealerData
      this.totalDealers = this.fiveForcesData.length
      console.log('加载的数据:', {
        dealerDataLength: this.dealerData.length,
        firstDealer: this.dealerData[0]
      })
      this.calculateProvinceCount()
      this.generateMockStoreData()
      this.$nextTick(() => {
        this.initRadarChart()
        this.initLineChart()
        this.initPieChart()
        this.initMap()
      })
    },
    generateMockStoreData() {
      const provinces = Object.keys(this.provinceDealerCount)
      const cities = {
        '广东省': ['广州市', '深圳市', '东莞市', '佛山市', '珠海市'],
        '江苏省': ['南京市', '苏州市', '无锡市', '常州市', '南通市'],
        '浙江省': ['杭州市', '宁波市', '温州市', '嘉兴市', '绍兴市'],
        '山东省': ['济南市', '青岛市', '烟台市', '潍坊市', '临沂市'],
        '河南省': ['郑州市', '洛阳市', '开封市', '南阳市', '新乡市'],
        '四川省': ['成都市', '绵阳市', '德阳市', '宜宾市', '南充市'],
        '湖北省': ['武汉市', '宜昌市', '襄阳市', '荆州市', '黄石市'],
        '湖南省': ['长沙市', '株洲市', '湘潭市', '衡阳市', '岳阳市'],
        '河北省': ['石家庄市', '唐山市', '保定市', '邯郸市', '秦皇岛市'],
        '福建省': ['福州市', '厦门市', '泉州市', '漳州市', '莆田市'],
        '安徽省': ['合肥市', '芜湖市', '蚌埠市', '淮南市', '马鞍山市'],
        '辽宁省': ['沈阳市', '大连市', '鞍山市', '抚顺市', '本溪市'],
        '陕西省': ['西安市', '宝鸡市', '咸阳市', '渭南市', '延安市'],
        '江西省': ['南昌市', '九江市', '景德镇市', '萍乡市', '新余市'],
        '重庆市': ['渝中区', '江北区', '南岸区', '九龙坡区', '沙坪坝区'],
        '广西壮族自治区': ['南宁市', '柳州市', '桂林市', '梧州市', '北海市'],
        '云南省': ['昆明市', '大理市', '丽江市', '曲靖市', '玉溪市'],
        '天津市': ['和平区', '河东区', '河西区', '南开区', '河北区'],
        '上海市': ['浦东新区', '黄浦区', '静安区', '徐汇区', '长宁区'],
        '北京市': ['朝阳区', '海淀区', '丰台区', '东城区', '西城区']
      }
      
      this.mockStoreData = []
      const storeTypes = ['direct', 'franchise']
      const businessStatuses = ['open', 'closed']
      const regions = {
        '广东省': 'south', '广西壮族自治区': 'south', '海南省': 'south', '福建省': 'east',
        '江苏省': 'east', '浙江省': 'east', '上海市': 'east', '安徽省': 'east', '江西省': 'east',
        '山东省': 'east', '北京市': 'north', '天津市': 'north', '河北省': 'north', '山西省': 'north',
        '内蒙古自治区': 'north', '辽宁省': 'northeast', '吉林省': 'northeast', '黑龙江省': 'northeast',
        '河南省': 'central', '湖北省': 'central', '湖南省': 'central',
        '四川省': 'southwest', '重庆市': 'southwest', '贵州省': 'southwest', '云南省': 'southwest', '西藏自治区': 'southwest',
        '陕西省': 'northwest', '甘肃省': 'northwest', '青海省': 'northwest', '宁夏回族自治区': 'northwest', '新疆维吾尔自治区': 'northwest'
      }
      
      provinces.forEach(province => {
        const count = this.provinceDealerCount[province]
        const provinceCities = cities[province] || ['市中心']
        
        for (let i = 0; i < count; i++) {
          const city = provinceCities[Math.floor(Math.random() * provinceCities.length)]
          this.mockStoreData.push({
            id: `STORE${String(this.mockStoreData.length + 1).padStart(5, '0')}`,
            name: `${province.replace(/省|市|自治区|壮族自治区/g, '')}${city.replace(/市|区/g, '')}店${i + 1}`,
            province: province,
            city: city,
            region: regions[province] || 'east',
            storeType: storeTypes[Math.floor(Math.random() * storeTypes.length)],
            businessStatus: Math.random() > 0.1 ? 'open' : 'closed',
            achieveStatus: Math.random() > 0.3 ? 'achieved' : 'notAchieved',
            isNewStore: Math.random() > 0.9,
            sales: Math.floor(100 + Math.random() * 400),
            customerFlow: Math.floor(500 + Math.random() * 1500),
            totalScore: 15 + Math.random() * 15,
            openDate: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000)
          })
        }
      })
    },
    calculateProvinceCount() {
      const count = {}
      this.fiveForcesData.forEach(d => {
        const province = d['省份']
        if (province) {
          count[province] = (count[province] || 0) + 1
        }
      })
      this.provinceDealerCount = count
    },
    getDealersByScoreRange(min, max) {
      return this.fiveForcesData
        .map(d => ({
          code: d['经销商代码'],
          province: d['省份'],
          totalScore: (d['传播获客力'] || 0) + (d['体验力'] || 0) + (d['转化力'] || 0) + (d['服务力'] || 0) + (d['经营力'] || 0)
        }))
        .filter(d => d.totalScore >= min && d.totalScore < max)
        .sort((a, b) => a.totalScore - b.totalScore)
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
      const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月']
      const salesData = this.getMonthlyAvg('销量')
      const customerData = this.getMonthlyAvg('客流量')
      const leadData = this.getMonthlyAvg('线索量')
      const potentialData = this.getMonthlyAvg('潜客量')
      
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
    getMonthlyAvg(field) {
      const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月']
      const result = months.map(month => {
        const key = `${month}${field}`
        const values = this.dealerData.map(d => d[key]).filter(v => v !== null && v !== undefined)
        if (values.length === 0) return 0
        return Math.round(values.reduce((a, b) => a + b, 0) / values.length)
      })
      console.log(`计算 ${field} 数据:`, result)
      return result
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
    getFilteredStoreData() {
      let data = [...this.mockStoreData]
      
      if (this.mapFilters.region !== 'all') {
        data = data.filter(s => s.region === this.mapFilters.region)
      }
      if (this.mapFilters.storeType !== 'all') {
        data = data.filter(s => s.storeType === this.mapFilters.storeType)
      }
      if (this.mapFilters.achieveStatus !== 'all') {
        data = data.filter(s => s.achieveStatus === this.mapFilters.achieveStatus)
      }
      
      return data
    },
    getProvinceStoreCount() {
      const filteredData = this.getFilteredStoreData()
      const count = {}
      filteredData.forEach(store => {
        count[store.province] = (count[store.province] || 0) + 1
      })
      return count
    },
    getCityStoreCount(province) {
      const filteredData = this.getFilteredStoreData().filter(s => s.province === province)
      const count = {}
      filteredData.forEach(store => {
        count[store.city] = (count[store.city] || 0) + 1
      })
      return count
    },
    updateMapData() {
      this.renderMap()
    },
    renderMap() {
      if (this.mapLevel === 'country') {
        this.renderCountryMap()
      } else if (this.mapLevel === 'province') {
        this.renderProvinceMap()
      } else if (this.mapLevel === 'city') {
        this.renderCityMap()
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
        
        const cityStoreCount = this.getCityStoreCount(this.currentProvince)
        const data = Object.keys(cityStoreCount).map(city => ({
          name: city,
          value: cityStoreCount[city]
        }))
        
        const maxValue = Math.max(...Object.values(cityStoreCount), 5)
        
        const option = {
          backgroundColor: 'transparent',
          tooltip: {
            trigger: 'item',
            formatter: function(params) {
              if (params.value) {
                return `${params.name}<br/>门店数量：${params.value}家<br/><span style="color:#999;font-size:11px;">点击查看门店列表</span>`
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
          series: [
            {
              name: '门店分布',
              type: 'map',
              map: 'province',
              geoIndex: 0,
              data: data
            }
          ]
        }
        
        this.mapChart.setOption(option, true)
      } catch (error) {
        console.error('加载省份地图失败:', error)
      }
    },
    renderCityMap() {
      const cityStores = this.getFilteredStoreData().filter(s => 
        s.province === this.currentProvince && s.city === this.currentCity
      )
      
      const option = {
        backgroundColor: 'transparent',
        title: {
          text: `${this.currentCity}门店列表`,
          left: 'center',
          top: 10,
          textStyle: {
            color: '#333',
            fontSize: 14
          }
        },
        tooltip: {
          trigger: 'item',
          formatter: function(params) {
            const store = params.data
            return `${store.name}<br/>
              类型：${store.storeType === 'direct' ? '直营' : '加盟'}<br/>
              状态：${store.businessStatus === 'open' ? '营业中' : '已停业'}<br/>
              达标：${store.achieveStatus === 'achieved' ? '是' : '否'}<br/>
              销量：${store.sales}<br/>
              评分：${store.totalScore.toFixed(2)}`
          }
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
          data: cityStores.map(s => s.name),
          axisLabel: {
            rotate: 45,
            color: '#666',
            fontSize: 10
          }
        },
        yAxis: {
          type: 'value',
          name: '综合评分',
          axisLabel: {
            color: '#666'
          }
        },
        series: [
          {
            name: '门店评分',
            type: 'bar',
            data: cityStores.map(s => ({
              ...s,
              value: s.totalScore,
              itemStyle: {
                color: s.achieveStatus === 'achieved' ? '#52c41a' : '#ff4d4f'
              }
            })),
            barWidth: '60%'
          }
        ]
      }
      
      this.mapChart.setOption(option, true)
    },
    bindMapEvents() {
      this.mapChart.on('click', async (params) => {
        if (this.mapLevel === 'country' && params.componentType === 'series') {
          const provinceName = params.name
          if (provinceName && this.getProvinceStoreCount()[provinceName]) {
            this.mapStack.push({ level: 'country', province: '', city: '' })
            this.currentProvince = provinceName
            this.mapLevel = 'province'
            await this.renderProvinceMap()
          }
        } else if (this.mapLevel === 'province' && params.componentType === 'series') {
          const cityName = params.name
          if (cityName) {
            this.mapStack.push({ level: 'province', province: this.currentProvince, city: '' })
            this.currentCity = cityName
            this.mapLevel = 'city'
            this.renderCityMap()
          }
        }
      })
    },
    goBackLevel() {
      if (this.mapStack.length > 0) {
        const prev = this.mapStack.pop()
        this.mapLevel = prev.level
        this.currentProvince = prev.province
        this.currentCity = prev.city
        this.renderMap()
      }
    },
    goToCountry() {
      this.mapLevel = 'country'
      this.currentProvince = ''
      this.currentCity = ''
      this.mapStack = []
      this.renderMap()
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
    showProvinceDetail() {
      this.selectedProvince = this.currentProvince
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
    getRegionName(regionCode) {
      const regionMap = {
        'east': '华东区',
        'south': '华南区',
        'north': '华北区',
        'southwest': '西南区',
        'northwest': '西北区',
        'northeast': '东北区',
        'central': '华中区'
      }
      return regionMap[regionCode] || ''
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
}

.total-dealers strong {
  color: #1890ff;
  font-size: 18px;
}

.dashboard-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 120px);
}

.row {
  display: flex;
  gap: 16px;
  flex: 1;
}

.row-top {
  height: 45%;
}

.row-bottom {
  height: 55%;
}

.col-left {
  width: 25%;
  display: flex;
  flex-direction: column;
}

.col-center {
  width: 50%;
  display: flex;
  flex-direction: column;
}

.col-right {
  width: 25%;
  display: flex;
  flex-direction: column;
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

.map-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-group label {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

.filter-group select {
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  color: #333;
  background: #fff;
  cursor: pointer;
  min-width: 80px;
}

.filter-group select:focus {
  outline: none;
  border-color: #1890ff;
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
  min-height: 300px;
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
  gap: 12px;
  height: 100%;
  overflow-y: auto;
}

.warning-section {
  border-radius: 6px;
  padding: 10px;
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

.modal-filter-info {
  padding: 12px 24px;
  background: #e6f7ff;
  border-bottom: 1px solid #91d5ff;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.modal-filter-info span:first-child {
  font-size: 13px;
  color: #1890ff;
  font-weight: 500;
}

.filter-tag {
  background: #1890ff;
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
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

.store-table .achieved {
  color: #52c41a;
  font-weight: 500;
}

.store-table .not-achieved {
  color: #ff4d4f;
  font-weight: 500;
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
