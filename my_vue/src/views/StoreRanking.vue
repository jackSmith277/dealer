<template>
  <div class="store-ranking-container">
    <header class="ranking-header">
      <h1>门店排行对比分析</h1>
    </header>

    <div class="ranking-settings">
      <div class="setting-item">
        <label>排行维度：</label>
        <select v-model="rankingDimension" @change="updateRanking">
          <option value="total">五力综合评分</option>
          <option value="propagation">传播获客力</option>
          <option value="experience">体验力</option>
          <option value="conversion">转化力</option>
          <option value="service">服务力</option>
          <option value="operation">经营力</option>
        </select>
      </div>
      <div class="setting-item">
        <label>排行范围：</label>
        <select v-model="rankingScope" @change="updateRanking">
          <option value="all">全平台</option>
          <option value="region">同区域</option>
        </select>
      </div>
      <div class="setting-item" v-if="rankingScope === 'region'">
        <label>选择区域：</label>
        <select v-model="selectedRegion" @change="updateRanking">
          <option v-for="region in regions" :key="region" :value="region">{{ region }}</option>
        </select>
      </div>
      <div class="setting-item">
        <label>时间范围：</label>
        <select v-model="timeRange" @change="updateRanking">
          <option value="month">当月</option>
          <option value="quarter">近3月</option>
          <option value="halfYear">近6月</option>
        </select>
      </div>
    </div>

    <div class="ranking-content">
      <div class="ranking-left">
        <div class="card">
          <div class="card-header">
            <h3>门店排行榜</h3>
            <span class="sub-title">TOP 20</span>
          </div>
          <div class="card-body">
            <div class="ranking-list">
              <div 
                v-for="(store, index) in rankingList" 
                :key="store.code"
                class="ranking-item"
                :class="{ 
                  'selected': selectedStores.includes(store.code),
                  'top-three': index < 3
                }"
                @click="toggleStoreSelection(store.code)"
              >
                <div class="rank-badge" :class="'rank-' + (index + 1)">
                  {{ index + 1 }}
                </div>
                <div class="store-info">
                  <div class="store-name">{{ store.name }}</div>
                  <div class="store-dealer">{{ store.dealer }} | {{ store.region }}</div>
                </div>
                <div class="store-score">
                  <div class="score-value">{{ store.score.toFixed(2) }}</div>
                  <div class="score-gap" v-if="index > 0">
                    <span class="gap-label">差距</span>
                    <span class="gap-value">-{{ (rankingList[index - 1].score - store.score).toFixed(2) }}</span>
                  </div>
                </div>
                <div class="select-indicator" v-if="selectedStores.includes(store.code)">
                  <span class="check-icon">✓</span>
                </div>
              </div>
            </div>
            <div class="selection-tip">
              已选择 {{ selectedStores.length }}/3 家门店进行对比
            </div>
          </div>
        </div>
      </div>

      <div class="ranking-right">
        <div class="comparison-section" v-if="selectedStores.length > 0">
          <div class="card">
            <div class="card-header">
              <h3>五力雷达对比</h3>
              <span class="sub-title">多维度能力对比</span>
            </div>
            <div class="card-body">
              <div ref="radarChart" class="chart-container"></div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h3>核心指标对比</h3>
              <span class="sub-title">关键业务指标对比</span>
            </div>
            <div class="card-body">
              <div ref="barChart" class="chart-container"></div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h3>趋势对比</h3>
              <span class="sub-title">近6个月趋势变化</span>
            </div>
            <div class="card-body">
              <div ref="lineChart" class="chart-container"></div>
            </div>
          </div>

          <div class="card analysis-card">
            <div class="card-header">
              <h3>对比小结</h3>
              <span class="sub-title">智能分析报告</span>
            </div>
            <div class="card-body">
              <div class="analysis-report" v-html="analysisReport"></div>
            </div>
          </div>
        </div>

        <div class="empty-state" v-else>
          <div class="empty-icon">📊</div>
          <div class="empty-text">请从左侧排行榜中选择 1-3 家门店进行对比分析</div>
          <div class="empty-tip">点击门店即可选中/取消</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'StoreRanking',
  data() {
    return {
      rankingDimension: 'total',
      rankingScope: 'all',
      selectedRegion: '华东区',
      timeRange: 'month',
      selectedStores: [],
      radarChart: null,
      barChart: null,
      lineChart: null,
      regions: ['华东区', '华南区', '华北区', '西南区', '西北区', '东北区', '华中区'],
      allStores: []
    }
  },
  computed: {
    rankingList() {
      let stores = [...this.allStores]
      
      if (this.rankingScope === 'region') {
        stores = stores.filter(s => s.region === this.selectedRegion)
      }
      
      const dimensionKey = {
        total: 'totalScore',
        propagation: 'propagationScore',
        experience: 'experienceScore',
        conversion: 'conversionScore',
        service: 'serviceScore',
        operation: 'operationScore'
      }
      
      stores.sort((a, b) => b[dimensionKey[this.rankingDimension]] - a[dimensionKey[this.rankingDimension]])
      
      return stores.slice(0, 20).map(s => ({
        ...s,
        score: s[dimensionKey[this.rankingDimension]]
      }))
    },
    selectedStoresData() {
      return this.rankingList.filter(s => this.selectedStores.includes(s.code))
    },
    analysisReport() {
      if (this.selectedStoresData.length === 0) return ''
      
      const stores = this.selectedStoresData
      let report = ''
      
      if (stores.length === 1) {
        const store = stores[0]
        report = `
          <div class="report-section">
            <h4>📊 ${store.name} 单店分析</h4>
            <p>综合评分：<strong>${store.totalScore.toFixed(2)}</strong> 分，排名第 <strong>${this.rankingList.findIndex(s => s.code === store.code) + 1}</strong> 位</p>
            <div class="strength-weakness">
              <div class="strength">
                <span class="label">优势维度：</span>
                <span class="value">${this.getStrengthDimensions(store).join('、')}</span>
              </div>
              <div class="weakness">
                <span class="label">待提升维度：</span>
                <span class="value">${this.getWeaknessDimensions(store).join('、')}</span>
              </div>
            </div>
            <div class="suggestion">
              <span class="label">优化建议：</span>
              <span class="value">建议重点关注${this.getWeaknessDimensions(store)[0]}的提升，可参考标杆门店的做法进行改进。</span>
            </div>
          </div>
        `
      } else {
        const sorted = [...stores].sort((a, b) => b.totalScore - a.totalScore)
        const best = sorted[0]
        
        report = `
          <div class="report-section">
            <h4>🏆 标杆门店分析</h4>
            <p><strong>${best.name}</strong> 综合评分最高（${best.totalScore.toFixed(2)}分），其优势在于${this.getStrengthDimensions(best).join('、')}等方面表现突出。</p>
            <p class="highlight">优秀做法：${this.getBestPractices(best)}</p>
          </div>
          <div class="report-section">
            <h4>📈 对比分析</h4>
            <div class="comparison-table">
              ${this.generateComparisonTable(stores)}
            </div>
          </div>
          <div class="report-section">
            <h4>💡 优化建议</h4>
            ${this.generateOptimizationSuggestions(sorted)}
          </div>
        `
      }
      
      return report
    }
  },
  mounted() {
    this.generateMockData()
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
    if (this.radarChart) this.radarChart.dispose()
    if (this.barChart) this.barChart.dispose()
    if (this.lineChart) this.lineChart.dispose()
  },
  methods: {
    generateMockData() {
      const provinces = ['广东省', '江苏省', '浙江省', '山东省', '河南省', '四川省', '湖北省', '湖南省', '河北省', '福建省', '安徽省', '辽宁省', '陕西省', '江西省', '重庆市', '广西壮族自治区', '云南省', '天津市', '上海市', '北京市']
      const regions = ['华东区', '华南区', '华北区', '西南区', '西北区', '东北区', '华中区']
      const dealerNames = ['华晨汽车', '众诚汽车', '恒通汽车', '鑫源汽车', '盛达汽车', '宏图汽车', '嘉诚汽车', '永达汽车', '中升汽车', '广汇汽车']
      
      this.allStores = []
      
      for (let i = 0; i < 50; i++) {
        const province = provinces[Math.floor(Math.random() * provinces.length)]
        const region = regions[Math.floor(Math.random() * regions.length)]
        
        this.allStores.push({
          code: `STORE${String(10001 + i).padStart(5, '0')}`,
          name: `${province.replace(/省|市|自治区|壮族自治区/g, '')}${Math.floor(Math.random() * 10) + 1}号店`,
          dealer: dealerNames[Math.floor(Math.random() * dealerNames.length)],
          province: province,
          region: region,
          totalScore: 70 + Math.random() * 30,
          propagationScore: 60 + Math.random() * 40,
          experienceScore: 65 + Math.random() * 35,
          conversionScore: 55 + Math.random() * 45,
          serviceScore: 70 + Math.random() * 30,
          operationScore: 60 + Math.random() * 40,
          sales: Math.floor(100 + Math.random() * 400),
          customerFlow: Math.floor(500 + Math.random() * 1500),
          leadCount: Math.floor(2000 + Math.random() * 8000),
          potentialCount: Math.floor(300 + Math.random() * 700),
          trendData: Array.from({ length: 6 }, () => 60 + Math.random() * 30)
        })
      }
    },
    updateRanking() {
      this.selectedStores = []
      this.updateCharts()
    },
    toggleStoreSelection(code) {
      const index = this.selectedStores.indexOf(code)
      if (index > -1) {
        this.selectedStores.splice(index, 1)
      } else if (this.selectedStores.length < 3) {
        this.selectedStores.push(code)
      }
      this.$nextTick(() => {
        this.updateCharts()
      })
    },
    updateCharts() {
      if (this.selectedStores.length === 0) {
        if (this.radarChart) {
          this.radarChart.clear()
        }
        if (this.barChart) {
          this.barChart.clear()
        }
        if (this.lineChart) {
          this.lineChart.clear()
        }
        return
      }
      
      this.initRadarChart()
      this.initBarChart()
      this.initLineChart()
    },
    initRadarChart() {
      if (!this.radarChart) {
        this.radarChart = echarts.init(this.$refs.radarChart)
      }
      
      const colors = ['#3b82f6', '#10b981', '#f59e0b']
      const indicator = [
        { name: '传播获客力', max: 100 },
        { name: '体验力', max: 100 },
        { name: '转化力', max: 100 },
        { name: '服务力', max: 100 },
        { name: '经营力', max: 100 }
      ]
      
      const series = this.selectedStoresData.map((store, index) => ({
        name: store.name,
        value: [
          store.propagationScore,
          store.experienceScore,
          store.conversionScore,
          store.serviceScore,
          store.operationScore
        ],
        lineStyle: {
          color: colors[index],
          width: 2
        },
        areaStyle: {
          color: colors[index],
          opacity: 0.1
        },
        itemStyle: {
          color: colors[index]
        }
      }))
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item'
        },
        legend: {
          data: this.selectedStoresData.map(s => s.name),
          bottom: 10,
          textStyle: {
            color: '#666'
          }
        },
        radar: {
          indicator: indicator,
          center: ['50%', '50%'],
          radius: '65%',
          axisName: {
            color: '#666',
            fontSize: 12
          },
          splitLine: {
            lineStyle: {
              color: '#e8e8e8'
            }
          },
          splitArea: {
            areaStyle: {
              color: ['rgba(59, 130, 246, 0.02)', 'rgba(59, 130, 246, 0.05)']
            }
          }
        },
        series: [{
          type: 'radar',
          data: series
        }]
      }
      
      this.radarChart.setOption(option)
    },
    initBarChart() {
      if (!this.barChart) {
        this.barChart = echarts.init(this.$refs.barChart)
      }
      
      const colors = ['#3b82f6', '#10b981', '#f59e0b']
      const metrics = ['销量', '客流量', '潜客量']
      
      const series = metrics.map((metric, index) => {
        const dataKey = {
          '销量': 'sales',
          '客流量': 'customerFlow',
          '潜客量': 'potentialCount'
        }
        
        return {
          name: metric,
          type: 'bar',
          data: this.selectedStoresData.map(store => store[dataKey[metric]]),
          itemStyle: {
            color: colors[index]
          },
          barGap: '10%',
          barWidth: '20%'
        }
      })
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        legend: {
          data: metrics,
          bottom: 10,
          textStyle: {
            color: '#666'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          top: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: this.selectedStoresData.map(s => s.name),
          axisLabel: {
            color: '#666',
            fontSize: 11,
            rotate: this.selectedStoresData.length > 2 ? 15 : 0
          },
          axisLine: {
            lineStyle: {
              color: '#e8e8e8'
            }
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            color: '#666'
          },
          axisLine: {
            lineStyle: {
              color: '#e8e8e8'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0'
            }
          }
        },
        series: series
      }
      
      this.barChart.setOption(option)
    },
    initLineChart() {
      if (!this.lineChart) {
        this.lineChart = echarts.init(this.$refs.lineChart)
      }
      
      const colors = ['#3b82f6', '#10b981', '#f59e0b']
      const months = ['1月', '2月', '3月', '4月', '5月', '6月']
      
      const series = this.selectedStoresData.map((store, index) => ({
        name: store.name,
        type: 'line',
        data: store.trendData,
        smooth: true,
        lineStyle: {
          color: colors[index],
          width: 3
        },
        itemStyle: {
          color: colors[index]
        },
        symbol: 'circle',
        symbolSize: 6
      }))
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: this.selectedStoresData.map(s => s.name),
          bottom: 10,
          textStyle: {
            color: '#666'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          top: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: months,
          axisLabel: {
            color: '#666'
          },
          axisLine: {
            lineStyle: {
              color: '#e8e8e8'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: '综合评分',
          axisLabel: {
            color: '#666'
          },
          axisLine: {
            lineStyle: {
              color: '#e8e8e8'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0'
            }
          }
        },
        series: series
      }
      
      this.lineChart.setOption(option)
    },
    handleResize() {
      if (this.radarChart) this.radarChart.resize()
      if (this.barChart) this.barChart.resize()
      if (this.lineChart) this.lineChart.resize()
    },
    getStrengthDimensions(store) {
      const dimensions = [
        { name: '传播获客力', score: store.propagationScore },
        { name: '体验力', score: store.experienceScore },
        { name: '转化力', score: store.conversionScore },
        { name: '服务力', score: store.serviceScore },
        { name: '经营力', score: store.operationScore }
      ]
      dimensions.sort((a, b) => b.score - a.score)
      return dimensions.slice(0, 2).map(d => d.name)
    },
    getWeaknessDimensions(store) {
      const dimensions = [
        { name: '传播获客力', score: store.propagationScore },
        { name: '体验力', score: store.experienceScore },
        { name: '转化力', score: store.conversionScore },
        { name: '服务力', score: store.serviceScore },
        { name: '经营力', score: store.operationScore }
      ]
      dimensions.sort((a, b) => a.score - b.score)
      return dimensions.slice(0, 2).map(d => d.name)
    },
    getBestPractices(store) {
      const practices = [
        '建立了完善的客户跟进体系，线索转化率持续提升',
        '注重客户体验管理，服务满意度保持高位',
        '数字化营销投入力度大，获客渠道多元化',
        '团队培训机制完善，销售能力持续增强',
        '精细化运营管理，成本控制效果显著'
      ]
      return practices[Math.floor(Math.random() * practices.length)]
    },
    generateComparisonTable(stores) {
      let html = '<table class="compare-table"><thead><tr><th>门店</th><th>综合评分</th><th>优势维度</th><th>劣势维度</th></tr></thead><tbody>'
      stores.forEach(store => {
        html += `
          <tr>
            <td>${store.name}</td>
            <td>${store.totalScore.toFixed(2)}</td>
            <td class="strength">${this.getStrengthDimensions(store)[0]}</td>
            <td class="weakness">${this.getWeaknessDimensions(store)[0]}</td>
          </tr>
        `
      })
      html += '</tbody></table>'
      return html
    },
    generateOptimizationSuggestions(sorted) {
      let html = ''
      sorted.slice(1).forEach(store => {
        const weakness = this.getWeaknessDimensions(store)[0]
        html += `<p><strong>${store.name}</strong>：建议重点提升${weakness}，可参考${sorted[0].name}的优秀做法，制定针对性改进计划。</p>`
      })
      return html
    }
  }
}
</script>

<style scoped>
.store-ranking-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.ranking-header {
  margin-bottom: 20px;
}

.ranking-header h1 {
  font-size: 24px;
  color: #1f2937;
  margin: 0;
}

.ranking-settings {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 20px;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.setting-item label {
  color: #6b7280;
  font-size: 14px;
  white-space: nowrap;
}

.setting-item select {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  background: #fff;
  cursor: pointer;
  min-width: 120px;
}

.setting-item select:focus {
  outline: none;
  border-color: #3b82f6;
}

.ranking-content {
  display: flex;
  gap: 20px;
  min-height: calc(100vh - 200px);
}

.ranking-left {
  width: 400px;
  flex-shrink: 0;
}

.ranking-right {
  flex: 1;
  min-width: 0;
}

.card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1f2937;
}

.sub-title {
  font-size: 12px;
  color: #9ca3af;
}

.card-body {
  padding: 16px 20px;
}

.ranking-list {
  max-height: 600px;
  overflow-y: auto;
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.ranking-item:hover {
  background: #f9fafb;
}

.ranking-item.selected {
  background: #eff6ff;
  border-color: #3b82f6;
}

.ranking-item.top-three {
  background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%);
}

.ranking-item.top-three.selected {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #3b82f6;
}

.rank-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  margin-right: 12px;
  background: #e5e7eb;
  color: #6b7280;
}

.rank-badge.rank-1 {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: #fff;
}

.rank-badge.rank-2 {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  color: #fff;
}

.rank-badge.rank-3 {
  background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
  color: #fff;
}

.store-info {
  flex: 1;
  min-width: 0;
}

.store-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 2px;
}

.store-dealer {
  font-size: 12px;
  color: #9ca3af;
}

.store-score {
  text-align: right;
  margin-left: 12px;
}

.score-value {
  font-size: 16px;
  font-weight: bold;
  color: #3b82f6;
}

.score-gap {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

.gap-label {
  margin-right: 4px;
}

.gap-value {
  color: #ef4444;
}

.select-indicator {
  margin-left: 8px;
}

.check-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: #3b82f6;
  color: #fff;
  border-radius: 50%;
  font-size: 12px;
}

.selection-tip {
  text-align: center;
  padding: 12px;
  color: #6b7280;
  font-size: 13px;
  border-top: 1px solid #f0f0f0;
  margin-top: 12px;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  color: #6b7280;
  margin-bottom: 8px;
}

.empty-tip {
  font-size: 13px;
  color: #9ca3af;
}

.analysis-card .card-body {
  padding: 20px;
}

.analysis-report {
  font-size: 14px;
  line-height: 1.8;
  color: #374151;
}

.report-section {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.report-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.report-section h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #1f2937;
}

.report-section p {
  margin: 8px 0;
}

.report-section .highlight {
  background: #fef3c7;
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 3px solid #f59e0b;
}

.strength-weakness {
  margin: 12px 0;
}

.strength-weakness > div {
  margin: 6px 0;
}

.strength-weakness .label {
  color: #6b7280;
}

.strength-weakness .value {
  font-weight: 500;
}

.strength .value {
  color: #10b981;
}

.weakness .value {
  color: #ef4444;
}

.suggestion {
  margin-top: 12px;
  padding: 10px;
  background: #eff6ff;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}

.suggestion .label {
  color: #6b7280;
}

.suggestion .value {
  color: #374151;
}

.compare-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}

.compare-table th,
.compare-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.compare-table th {
  background: #f9fafb;
  font-weight: 500;
  color: #6b7280;
  font-size: 13px;
}

.compare-table td {
  font-size: 13px;
}

.compare-table .strength {
  color: #10b981;
}

.compare-table .weakness {
  color: #ef4444;
}
</style>
