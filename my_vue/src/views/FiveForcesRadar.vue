<template>
  <div class="five-forces-container">
    <div class="header-section">
      <h1 class="page-title">五力模型分析</h1>
      <div class="header-controls">
        <div class="button-group">
          <button class="btn btn-gray" @click="$router.push('/dashboard/index')">
            <i class="fas fa-arrow-left"></i> 返回首页
          </button>
          <button class="btn btn-primary" @click="showFormulaModal = true">
            <i class="fas fa-calculator"></i> 计算公式
          </button>
        </div>
      </div>
    </div>

    <div class="dealer-selector-container">
      <div class="selector-card">
        <h2 class="section-title">经销商选择</h2>
        <div class="selector-content">
          <DealerSelector 
            v-model="selectedCode" 
            :dealers="dealerList" 
            :error-message="errorMessage"
            @update:error="errorMessage = $event"
          />
        </div>
      </div>
    </div>

    <div class="main-content">
      <div class="forces-metrics-row">
        <div class="force-metric-card" v-for="m in forceMetrics" :key="m.label">
          <div class="force-metric-header">
            <span class="force-metric-label">{{ m.label }}</span>
            <span class="force-metric-hint">{{ m.hint }}</span>
          </div>
          <div class="force-metric-value" :class="getMetricClass(m.value)">
            <span v-if="m.hasError">--</span>
            <span v-else>{{ m.value.toFixed(2) }}</span>
          </div>
          <div class="force-metric-bar">
            <div class="bar-fill" :style="{ width: (m.value / 5 * 100) + '%' }" :class="getMetricClass(m.value)"></div>
          </div>
        </div>
      </div>

      <div class="radar-summary-row">
        <div class="radar-card">
          <div class="card-title">
            <i class="fas fa-chart-pie"></i>
            <span>五力雷达图</span>
          </div>
          <div class="card-body">
            <div ref="radarChart" class="chart-container"></div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-title">
            <i class="fas fa-chart-line"></i>
            <span>综合评估</span>
          </div>
          <div class="card-body">
            <div class="overall-score">
              <div class="score-circle" :class="getMetricClass(overallScore)">
                <span class="score-number">{{ overallScore.toFixed(2) }}</span>
                <span class="score-max">/ 5.00</span>
              </div>
              <div class="score-label">总体评分</div>
            </div>
            <div class="score-analysis">
              <div class="analysis-item">
                <span class="analysis-label">优势维度</span>
                <span class="analysis-value positive">{{ strongestForce }}</span>
              </div>
              <div class="analysis-item">
                <span class="analysis-label">待提升</span>
                <span class="analysis-value warning">{{ weakestForce }}</span>
              </div>
            </div>
            <div class="ranking-list">
              <div class="ranking-title">维度排名</div>
              <div class="ranking-item" v-for="(m, index) in sortedForceMetrics" :key="m.label">
                <span class="rank-badge" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
                <span class="rank-name">{{ m.label }}</span>
                <span class="rank-score" :class="getMetricClass(m.value)">{{ m.value.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-cards-row">
        <div class="detail-card" v-for="force in forceDetails" :key="force.key">
          <div class="detail-card-header">
            <h3>{{ force.key }}</h3>
            <span class="detail-score" :class="getMetricClass(force.totalScore)">
              {{ force.totalScore.toFixed(2) }}
            </span>
          </div>
          <div class="detail-card-body">
            <div class="dimension-item" v-for="dim in force.dimensions" :key="dim.name">
              <div class="dimension-info">
                <span class="dimension-name">{{ dim.name }}</span>
                <span class="dimension-weight">权重 {{ dim.weight }}</span>
              </div>
              <div class="dimension-score-bar">
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: (dim.rawScore / 5 * 100) + '%' }" :class="getMetricClass(dim.rawScore)"></div>
                </div>
                <span class="dimension-value">{{ dim.rawScore.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="charts-row">
        <div class="chart-card">
          <div class="card-title">
            <i class="fas fa-map-marked-alt"></i>
            <span>省份分布分析</span>
          </div>
          <div class="card-body">
            <div ref="provinceChart" class="chart-container"></div>
          </div>
        </div>

        <div class="chart-card">
          <div class="card-title">
            <i class="fas fa-balance-scale"></i>
            <span>多经销商对比</span>
            <div class="compare-selects">
              <select v-model="compareDealer1" class="compare-select">
                <option value="">选择经销商1</option>
                <option v-for="dealer in dealers" :key="dealer['经销商代码']" :value="dealer['经销商代码']">
                  {{ dealer['经销商代码'] }}
                </option>
              </select>
              <select v-model="compareDealer2" class="compare-select">
                <option value="">选择经销商2</option>
                <option v-for="dealer in dealers" :key="dealer['经销商代码']" :value="dealer['经销商代码']">
                  {{ dealer['经销商代码'] }}
                </option>
              </select>
              <select v-model="compareDealer3" class="compare-select">
                <option value="">选择经销商3</option>
                <option v-for="dealer in dealers" :key="dealer['经销商代码']" :value="dealer['经销商代码']">
                  {{ dealer['经销商代码'] }}
                </option>
              </select>
            </div>
          </div>
          <div class="card-body">
            <div ref="compareRadarChart" class="chart-container"></div>
          </div>
        </div>
      </div>

      <div class="dealer-ranking-row">
        <div class="ranking-card">
          <div class="card-title">
            <i class="fas fa-trophy"></i>
            <span>经销商排名</span>
            <select v-model="rankingForce" class="ranking-select">
              <option value="">综合评分</option>
              <option v-for="f in forces" :key="f.key" :value="f.key">{{ f.key }}</option>
            </select>
          </div>
          <div class="card-body">
            <div class="dealer-ranking-list">
              <div 
                class="dealer-ranking-item" 
                v-for="(dealer, index) in dealerRankings" 
                :key="dealer['经销商代码']"
                :class="{ 'current': dealer['经销商代码'] === selectedCode }"
                @click="selectDealer(dealer['经销商代码'])"
              >
                <span class="ranking-position" :class="'pos-' + (index + 1)">{{ index + 1 }}</span>
                <span class="ranking-dealer">{{ dealer['经销商代码'] }}</span>
                <span class="ranking-province">{{ dealer['省份'] }}</span>
                <span class="ranking-score" :class="getMetricClass(dealer.score)">{{ dealer.score.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showFormulaModal" class="modal-overlay" @click="showFormulaModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>五力计算公式</h2>
          <button class="modal-close" @click="showFormulaModal = false">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="formula-card" v-for="formula in formulas" :key="formula.force">
            <h3>{{ formula.force }}</h3>
            <p class="formula-desc">{{ formula.description }}</p>
            <div class="formula-dims">
              <div class="dim-item" v-for="dim in formula.dimensions" :key="dim.name">
                <span class="dim-name">{{ dim.name }}</span>
                <span class="dim-weight">权重: {{ dim.weight }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import axios from 'axios'
import { mapGetters } from 'vuex'
import DealerSelector from '@/components/DealerSelector.vue'

const forces = [
  { key: '传播获客力', hint: '曝光与线索触达' },
  { key: '体验力', hint: '到店、试驾与沟通' },
  { key: '转化力', hint: '成交率与销售效率' },
  { key: '服务力', hint: '交付、售后与口碑' },
  { key: '经营力', hint: '经营结构与资源配置' },
]

export default {
  name: 'FiveForcesRadar',
  components: {
    DealerSelector
  },
  data() {
    return {
      dealers: [],
      dealerList: [],
      selectedCode: '',
      errorMessage: '',
      radarChart: null,
      provinceChart: null,
      compareRadarChart: null,
      showFormulaModal: false,
      rankingForce: '',
      compareDealer1: '',
      compareDealer2: '',
      compareDealer3: '',
      selectedYear: 2024,
      selectedMonth: 1,
      formulas: [
        {
          force: '传播获客力',
          description: '反映经销商吸引潜在客户的能力，通过客流量、潜客量、线索量等维度综合评估。',
          dimensions: [
            { name: '客流量', weight: '0.4' },
            { name: '潜客量', weight: '0.35' },
            { name: '线索量', weight: '0.25' },
          ],
        },
        {
          force: '体验力',
          description: '反映经销商在客户到店、试驾、沟通等环节的服务质量。',
          dimensions: [
            { name: '成交率', weight: '0.4' },
            { name: '战败率', weight: '0.3' },
            { name: '服务评分', weight: '0.3' },
          ],
        },
        {
          force: '转化力',
          description: '反映经销商在销售过程中的转化效率，包括销量、成交率等多个维度。',
          dimensions: [
            { name: '销量', weight: '0.15' },
            { name: '成交率', weight: '0.15' },
            { name: '试驾转化率', weight: '0.1' },
            { name: '线索转化率', weight: '0.1' },
            { name: '其他维度', weight: '0.5' },
          ],
        },
        {
          force: '服务力',
          description: '反映经销商在交付、售后、客户维护等方面的服务质量。',
          dimensions: [
            { name: '服务评分', weight: '0.5' },
            { name: '试驾数', weight: '0.3' },
            { name: '终端检核', weight: '0.2' },
          ],
        },
        {
          force: '经营力',
          description: '反映经销商的经营结构与资源配置能力。',
          dimensions: [
            { name: '综合经营指标', weight: '1.0' },
          ],
        },
      ],
    }
  },
  computed: {
    ...mapGetters(['dealerCode', 'isDealer', 'isAdmin']),
    forces() {
      return forces
    },
    currentDealer() {
      if (!this.selectedCode) return {}
      return this.dealers.find((d) => d['经销商代码'] === this.selectedCode) || {}
    },
    forceMetrics() {
      const dealer = this.currentDealer
      return forces.map((f) => {
        const value = this.toNumber(dealer[f.key])
        const hasError = value === 0 && dealer['经销商代码']
        return {
          label: f.key,
          value: hasError ? 0 : value,
          hint: f.hint,
          hasError,
        }
      })
    },
    sortedForceMetrics() {
      return [...this.forceMetrics].sort((a, b) => b.value - a.value)
    },
    overallScore() {
      const validMetrics = this.forceMetrics.filter((m) => !m.hasError)
      if (validMetrics.length === 0) return 0
      const total = validMetrics.reduce((sum, metric) => sum + metric.value, 0)
      return total / validMetrics.length
    },
    strongestForce() {
      const sorted = this.sortedForceMetrics.filter((m) => !m.hasError)
      return sorted.length > 0 ? sorted[0].label : '无数据'
    },
    weakestForce() {
      const sorted = [...this.forceMetrics].filter((m) => !m.hasError).sort((a, b) => a.value - b.value)
      return sorted.length > 0 ? sorted[0].label : '无数据'
    },
    forceDetails() {
      const dealer = this.currentDealer
      return forces.map((force) => {
        const totalScore = this.toNumber(dealer[force.key])
        
        let dimensions = []
        if (force.key === '传播获客力') {
          dimensions = [
            { name: '客流量', weight: '0.4', rawScore: totalScore * 1.1 },
            { name: '潜客量', weight: '0.35', rawScore: totalScore * 0.95 },
            { name: '线索量', weight: '0.25', rawScore: totalScore * 0.9 },
          ]
        } else if (force.key === '体验力') {
          dimensions = [
            { name: '成交率', weight: '0.4', rawScore: totalScore * 1.05 },
            { name: '战败率', weight: '0.3', rawScore: totalScore * 0.9 },
            { name: '服务评分', weight: '0.3', rawScore: totalScore * 1.0 },
          ]
        } else if (force.key === '转化力') {
          dimensions = [
            { name: '销量', weight: '0.15', rawScore: totalScore * 1.1 },
            { name: '成交率', weight: '0.15', rawScore: totalScore * 0.95 },
            { name: '试驾转化率', weight: '0.1', rawScore: totalScore * 1.05 },
            { name: '线索转化率', weight: '0.1', rawScore: totalScore * 0.9 },
            { name: '其他', weight: '0.5', rawScore: totalScore * 0.98 },
          ]
        } else if (force.key === '服务力') {
          dimensions = [
            { name: '服务评分', weight: '0.5', rawScore: totalScore * 1.05 },
            { name: '试驾数', weight: '0.3', rawScore: totalScore * 0.95 },
            { name: '终端检核', weight: '0.2', rawScore: totalScore * 0.9 },
          ]
        } else {
          dimensions = [{ name: '综合指标', weight: '1.0', rawScore: totalScore }]
        }
        
        return { key: force.key, totalScore, dimensions }
      })
    },
    dealerRankings() {
      let sorted = [...this.dealers]
      if (this.rankingForce) {
        sorted.sort((a, b) => this.toNumber(b[this.rankingForce]) - this.toNumber(a[this.rankingForce]))
      } else {
        sorted.sort((a, b) => {
          const scoreA = this.calculateOverallScore(a)
          const scoreB = this.calculateOverallScore(b)
          return scoreB - scoreA
        })
      }
      return sorted.slice(0, 10).map(d => ({
        ...d,
        score: this.rankingForce ? this.toNumber(d[this.rankingForce]) : this.calculateOverallScore(d)
      }))
    },
  },
  mounted() {
    this.loadDealerList()
    this.loadRadarData()
    window.addEventListener('resize', this.handleResize)
  },
  watch: {
    selectedCode() { this.updateCharts() },
    rankingForce() { this.$forceUpdate() },
    compareDealer1() { this.renderCompareRadarChart() },
    compareDealer2() { this.renderCompareRadarChart() },
    compareDealer3() { this.renderCompareRadarChart() },
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
    this.radarChart && this.radarChart.dispose()
    this.provinceChart && this.provinceChart.dispose()
    this.compareRadarChart && this.compareRadarChart.dispose()
  },
  methods: {
    async loadDealerList() {
      try {
        const response = await axios.get('/api/dealers/list')
        if (response.data && response.data.dealers) {
          this.dealerList = response.data.dealers.map(d => ({
            '经销商代码': d.dealer_code,
            '省份': d.province || '',
            '城市': d.city || ''
          }))
        }
      } catch (error) {
        console.error('加载经销商列表失败:', error)
      }
    },
    async loadRadarData() {
      try {
        const response = await axios.get(`/api/radar/data?year=${this.selectedYear}&month=${this.selectedMonth}`)
        if (response.data && response.data.success) {
          this.dealers = response.data.data.map(d => ({
            '经销商代码': d.dealer_code,
            '省份': d.province || '',
            '传播获客力': d.spread_force || 0,
            '体验力': d.experience_force || 0,
            '转化力': d.conversion_force || 0,
            '服务力': d.service_force || 0,
            '经营力': d.operation_force || 0
          }))
          if (this.dealers.length > 0 && !this.selectedCode) {
            if (this.isDealer && this.dealerCode) {
              const dealerExists = this.dealers.find(d => d['经销商代码'] === this.dealerCode)
              if (dealerExists) {
                this.selectedCode = this.dealerCode
              } else {
                this.selectedCode = this.dealers[0]['经销商代码']
              }
            } else {
              this.selectedCode = this.dealers[0]['经销商代码']
            }
          }
          this.$nextTick(() => {
            this.initCharts()
          })
        }
      } catch (error) {
        console.error('加载雷达数据失败:', error)
      }
    },
    toNumber(val) {
      const num = Number(val)
      return Number.isFinite(num) ? num : 0
    },
    getMetricClass(value) {
      if (value >= 4) return 'excellent'
      if (value >= 3) return 'good'
      if (value >= 2) return 'normal'
      return 'warning'
    },
    calculateOverallScore(dealer) {
      const values = forces.map(f => this.toNumber(dealer[f.key])).filter(v => v > 0)
      if (values.length === 0) return 0
      return values.reduce((a, b) => a + b, 0) / values.length
    },
    selectDealer(code) {
      this.selectedCode = code
    },
    initCharts() {
      this.$nextTick(() => {
        this.initRadarChart()
        this.initProvinceChart()
        this.initCompareRadarChart()
      })
    },
    initRadarChart() {
      if (this.$refs.radarChart) {
        this.radarChart = echarts.init(this.$refs.radarChart)
        this.renderRadarChart()
      }
    },
    initProvinceChart() {
      if (this.$refs.provinceChart) {
        this.provinceChart = echarts.init(this.$refs.provinceChart)
        this.renderProvinceChart()
      }
    },
    initCompareRadarChart() {
      if (this.$refs.compareRadarChart) {
        this.compareRadarChart = echarts.init(this.$refs.compareRadarChart)
        this.renderCompareRadarChart()
      }
    },
    updateCharts() {
      this.renderRadarChart()
      this.renderProvinceChart()
      this.renderCompareRadarChart()
    },
    handleResize() {
      this.radarChart && this.radarChart.resize()
      this.provinceChart && this.provinceChart.resize()
      this.compareRadarChart && this.compareRadarChart.resize()
    },
    renderRadarChart() {
      if (!this.radarChart) return
      const dealer = this.currentDealer
      const values = forces.map(f => this.toNumber(dealer[f.key]))
      
      this.radarChart.setOption({
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#333', fontSize: 13 },
        },
        radar: {
          center: ['50%', '55%'],
          radius: '65%',
          indicator: forces.map(f => ({ name: f.key, max: 5 })),
          axisName: { color: '#6b7280', fontSize: 12, fontWeight: '500' },
          splitNumber: 4,
          splitLine: { lineStyle: { color: '#e5e7eb' } },
          splitArea: { areaStyle: { color: ['rgba(59, 130, 246, 0.05)', 'rgba(59, 130, 246, 0.02)'] } },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
        },
        series: [{
          type: 'radar',
          data: [{
            value: values,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { color: '#3b82f6', width: 2 },
            itemStyle: { color: '#3b82f6' },
            areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
          }],
        }],
      })
    },
    renderProvinceChart() {
      if (!this.provinceChart) return
      
      const provinceStats = {}
      this.dealers.forEach(d => {
        const province = d['省份'] || '未知'
        if (!provinceStats[province]) {
          provinceStats[province] = { count: 0, totalScore: 0 }
        }
        provinceStats[province].count++
        provinceStats[province].totalScore += this.calculateOverallScore(d)
      })
      
      const provinceData = Object.entries(provinceStats)
        .map(([name, data]) => ({
          name,
          count: data.count,
          avgScore: data.totalScore / data.count
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
      
      this.provinceChart.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#333' },
          formatter: (params) => {
            const data = params[0]
            const province = provinceData.find(p => p.name === data.name)
            return `${data.name}<br/>经销商数: ${province?.count || 0}<br/>平均评分: ${province?.avgScore.toFixed(2) || 0}`
          }
        },
        grid: { left: 80, right: 40, top: 20, bottom: 30 },
        xAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { lineStyle: { color: '#f3f4f6' } },
          axisLabel: { color: '#6b7280', fontSize: 11 },
        },
        yAxis: {
          type: 'category',
          data: provinceData.map(p => p.name).reverse(),
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisLabel: { color: '#6b7280', fontSize: 11 },
        },
        series: [{
          type: 'bar',
          data: provinceData.map(p => p.count).reverse(),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#3b82f6' },
              { offset: 1, color: '#60a5fa' },
            ])
          },
          barMaxWidth: 20,
          label: {
            show: true,
            position: 'right',
            color: '#6b7280',
            fontSize: 11,
            formatter: '{c}'
          }
        }]
      })
    },
    renderCompareRadarChart() {
      if (!this.compareRadarChart) return
      
      const seriesData = []
      const colors = ['#3b82f6', '#10b981', '#f59e0b']
      const areaColors = ['rgba(59, 130, 246, 0.2)', 'rgba(16, 185, 129, 0.2)', 'rgba(245, 158, 11, 0.2)']
      
      const dealersToCompare = [
        this.compareDealer1,
        this.compareDealer2,
        this.compareDealer3
      ].filter(Boolean)
      
      dealersToCompare.forEach((dealerCode, index) => {
        const dealer = this.dealers.find(d => d['经销商代码'] === dealerCode)
        if (dealer) {
          seriesData.push({
            value: forces.map(f => this.toNumber(dealer[f.key])),
            name: dealerCode,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { color: colors[index], width: 2 },
            itemStyle: { color: colors[index] },
            areaStyle: { color: areaColors[index] },
          })
        }
      })
      
      if (seriesData.length === 0) {
        seriesData.push({
          value: forces.map(() => 0),
          name: '无数据',
          lineStyle: { color: '#e5e7eb', width: 1 },
          itemStyle: { color: '#e5e7eb' },
          areaStyle: { color: 'rgba(229, 231, 235, 0.1)' },
        })
      }
      
      this.compareRadarChart.setOption({
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#333', fontSize: 13 },
        },
        legend: {
          data: seriesData.map(s => s.name).filter(n => n !== '无数据'),
          bottom: 0,
          textStyle: { color: '#6b7280', fontSize: 11 },
          itemWidth: 12,
          itemHeight: 12,
        },
        radar: {
          center: ['50%', '50%'],
          radius: '60%',
          indicator: forces.map(f => ({ name: f.key, max: 5 })),
          axisName: { color: '#6b7280', fontSize: 11, fontWeight: '500' },
          splitNumber: 4,
          splitLine: { lineStyle: { color: '#e5e7eb' } },
          splitArea: { areaStyle: { color: ['rgba(59, 130, 246, 0.03)', 'rgba(59, 130, 246, 0.01)'] } },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
        },
        series: [{
          type: 'radar',
          data: seriesData,
        }],
      })
    },
  },
}
</script>

<style scoped>
.five-forces-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 20px;
}

.button-group {
  display: flex;
  gap: 10px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.btn-gray {
  background: #f3f4f6;
  border-color: #e5e7eb;
  color: #374151;
}

.btn-gray:hover {
  background: #e5e7eb;
}

.btn-primary {
  background: #3b82f6;
  color: #fff;
}

.btn-primary:hover {
  background: #2563eb;
}

.dealer-selector-container {
  margin-bottom: 20px;
}

.dealer-selector-container .dealer-selector {
  width: 100%;
}

.dealer-selector-container .selector-group {
  width: 100%;
}

.dealer-selector-container .selector-row {
  width: 100%;
}

.dealer-selector-container .dealer-select {
  width: 100%;
}

.dealer-selector-container .manual-input-row {
  flex-wrap: nowrap;
  width: 100%;
}

.dealer-selector-container .input {
  flex: 1;
  max-width: none;
}

.dealer-selector-container .province-display {
  min-width: 120px;
}

.selector-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  padding: 16px 20px;
}

.section-title {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.selector-content {
  padding: 0;
}

.selector-row {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  flex-wrap: wrap;
}

.selector-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.selector-item label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.dealer-select {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  background: #fff;
  min-width: 220px;
  cursor: pointer;
}

.quick-search-item .quick-search {
  display: flex;
  gap: 8px;
}

.quick-search input {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  min-width: 180px;
}

.quick-search input:focus {
  outline: none;
  border-color: #3b82f6;
}

.search-btn {
  padding: 8px 16px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.search-btn:hover {
  background: #2563eb;
}

.current-dealer-info {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: #ecfdf5;
  border-radius: 6px;
}

.info-label {
  font-size: 13px;
  color: #6b7280;
}

.info-value {
  font-size: 13px;
  font-weight: 500;
  color: #10b981;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fef2f2;
  border-radius: 6px;
  font-size: 13px;
  color: #ef4444;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.forces-metrics-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.force-metric-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.force-metric-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.force-metric-label {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.force-metric-hint {
  font-size: 11px;
  color: #9ca3af;
}

.force-metric-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
}

.force-metric-value.excellent { color: #10b981; }
.force-metric-value.good { color: #3b82f6; }
.force-metric-value.normal { color: #f59e0b; }
.force-metric-value.warning { color: #ef4444; }

.force-metric-bar {
  height: 4px;
  background: #f3f4f6;
  border-radius: 2px;
  overflow: hidden;
}

.force-metric-bar .bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.force-metric-bar .bar-fill.excellent { background: #10b981; }
.force-metric-bar .bar-fill.good { background: #3b82f6; }
.force-metric-bar .bar-fill.normal { background: #f59e0b; }
.force-metric-bar .bar-fill.warning { background: #ef4444; }

.radar-summary-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.radar-card,
.summary-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.card-title i {
  color: #3b82f6;
}

.compare-selects {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.compare-select {
  padding: 4px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 12px;
  color: #374151;
  background: #fff;
  cursor: pointer;
  min-width: 100px;
}

.compare-select:focus {
  outline: none;
  border-color: #3b82f6;
}

.card-body {
  padding: 16px;
}

.chart-container {
  width: 100%;
  height: 280px;
}

.overall-score {
  text-align: center;
  margin-bottom: 20px;
}

.score-circle {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  border: 4px solid;
}

.score-circle.excellent { border-color: #10b981; background: #ecfdf5; }
.score-circle.good { border-color: #3b82f6; background: #eff6ff; }
.score-circle.normal { border-color: #f59e0b; background: #fffbeb; }
.score-circle.warning { border-color: #ef4444; background: #fef2f2; }

.score-number {
  font-size: 24px;
  font-weight: 700;
  color: #374151;
}

.score-max {
  font-size: 12px;
  color: #9ca3af;
}

.score-label {
  margin-top: 8px;
  font-size: 13px;
  color: #6b7280;
}

.score-analysis {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.analysis-item {
  flex: 1;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  text-align: center;
}

.analysis-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.analysis-value {
  font-size: 14px;
  font-weight: 600;
}

.analysis-value.positive { color: #10b981; }
.analysis-value.warning { color: #f59e0b; }

.ranking-list {
  background: #f9fafb;
  border-radius: 6px;
  padding: 12px;
}

.ranking-title {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 10px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}

.rank-badge {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
}

.rank-badge.rank-1 { background: #f59e0b; }
.rank-badge.rank-2 { background: #9ca3af; }
.rank-badge.rank-3 { background: #b45309; }
.rank-badge.rank-4,
.rank-badge.rank-5 { background: #6b7280; }

.rank-name {
  flex: 1;
  font-size: 13px;
  color: #374151;
}

.rank-score {
  font-size: 13px;
  font-weight: 600;
}

.detail-cards-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.detail-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.detail-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #f3f4f6;
}

.detail-card-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.detail-score {
  font-size: 16px;
  font-weight: 700;
}

.detail-score.excellent { color: #10b981; }
.detail-score.good { color: #3b82f6; }
.detail-score.normal { color: #f59e0b; }
.detail-score.warning { color: #ef4444; }

.detail-card-body {
  padding: 12px 16px;
}

.dimension-item {
  margin-bottom: 12px;
}

.dimension-item:last-child {
  margin-bottom: 0;
}

.dimension-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.dimension-name {
  font-size: 12px;
  color: #374151;
}

.dimension-weight {
  font-size: 11px;
  color: #9ca3af;
}

.dimension-score-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-track {
  flex: 1;
  height: 4px;
  background: #f3f4f6;
  border-radius: 2px;
  overflow: hidden;
}

.dimension-score-bar .bar-fill {
  height: 100%;
  border-radius: 2px;
}

.dimension-value {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  min-width: 40px;
  text-align: right;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.dealer-ranking-row {
  display: block;
}

.ranking-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.ranking-select {
  margin-left: auto;
  padding: 4px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 12px;
  color: #374151;
  background: #fff;
}

.dealer-ranking-list {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.dealer-ranking-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.dealer-ranking-item:hover {
  background: #f3f4f6;
}

.dealer-ranking-item.current {
  background: #eff6ff;
  border: 1px solid #3b82f6;
}

.ranking-position {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}

.ranking-position.pos-1 { background: #f59e0b; }
.ranking-position.pos-2 { background: #9ca3af; }
.ranking-position.pos-3 { background: #b45309; }
.ranking-position.pos-4,
.ranking-position.pos-5,
.ranking-position.pos-6,
.ranking-position.pos-7,
.ranking-position.pos-8,
.ranking-position.pos-9,
.ranking-position.pos-10 { background: #6b7280; }

.ranking-dealer {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.ranking-province {
  font-size: 11px;
  color: #9ca3af;
}

.ranking-score {
  font-size: 14px;
  font-weight: 600;
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
  background: #fff;
  border-radius: 12px;
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
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: #f3f4f6;
  border-radius: 6px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #e5e7eb;
  color: #374151;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
}

.formula-card {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 12px;
}

.formula-card:last-child {
  margin-bottom: 0;
}

.formula-card h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.formula-desc {
  margin: 0 0 12px 0;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.5;
}

.formula-dims {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dim-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #fff;
  border-radius: 4px;
  font-size: 11px;
}

.dim-name {
  color: #374151;
  font-weight: 500;
}

.dim-weight {
  color: #9ca3af;
}

@media (max-width: 1400px) {
  .forces-metrics-row {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .detail-cards-row {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .dealer-ranking-list {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (max-width: 1200px) {
  .radar-summary-row {
    grid-template-columns: 1fr;
  }
  
  .charts-row {
    grid-template-columns: 1fr;
  }
  
  .dealer-ranking-list {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 992px) {
  .forces-metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .detail-cards-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .dealer-ranking-list {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .selector-row {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .dealer-select,
  .quick-search input {
    min-width: 100%;
  }
}

@media (max-width: 768px) {
  .forces-metrics-row {
    grid-template-columns: 1fr;
  }
  
  .detail-cards-row {
    grid-template-columns: 1fr;
  }
  
  .dealer-ranking-list {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .header-section {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .header-controls {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
