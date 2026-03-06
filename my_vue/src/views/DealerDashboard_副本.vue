<template>
  <div class="dashboard-container">
    <h1 class="page-title">汽车销售提升 · 2024</h1>
    
    <!-- 经销商选择模块 -->
    <div class="dealer-selector-container">
      <div class="aleftboxtbott">
        <h2 class="tith2">经销商选择</h2>
        <div class="aleftboxtbott_cont">
          <DealerSelector 
            :dealers="dealers" 
            :selectedCode="selectedCode"
            :errorMessage="errorMessage"
            @select-dealer="(code) => selectedCode = code"
            @apply-manual="applyManualDealer"
          />
        </div>
      </div>
    </div>

    <!-- 月度快照+核心指标 -->
    <div class="snapshot-metrics-row">
      <div class="left1">
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

      <div class="core-metrics-container">
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

    <!-- 销量趋势分析+销售漏斗 -->
    <div class="trend-funnel-row">
      <div class="mrbox">
        <div class="amiddboxttop">
          <h2 class="tith2">销量趋势分析</h2>
          <div class="left2_table chart-container" ref="trendChart"></div>
        </div>
      </div>

      <div class="funnel-container">
        <div class="amiddboxtbott1">
          <h2 class="tith2">销售漏斗</h2>
          <div class="amiddboxtbott1content chart-container" ref="funnelChart"></div>
        </div>
      </div>
    </div>

    <!-- 四合一模块布局 -->
    <div class="four-in-one-row">
      <div class="four-in-one-item">
        <h2 class="tith2">成交/战败率</h2>
        <div class="chart-container" ref="rateChart"></div>
      </div>
      <div class="four-in-one-item">
        <h2 class="tith2">响应时间分析</h2>
        <div class="chart-container" ref="responseTimeChart"></div>
      </div>
      <div class="four-in-one-item">
        <h2 class="tith2">政策影响</h2>
        <div class="chart-container" ref="policyChart"></div>
      </div>
      <div class="four-in-one-item">
        <h2 class="tith2">GSEV占比</h2>
        <div class="chart-container" ref="gsevChart"></div>
      </div>
    </div>
    <!-- 四合一模块布局 end -->
    
    <!-- 评价占比框 -->
    <div class="review-box">
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
</template>

<script>
import * as echarts from 'echarts'
import dealerData from '@/assets/dealerData.json'
import DealerSelector from '@/components/DealerSelector'

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
    DealerSelector
  },
  data() {
    return {
      dealers: dealerData || [],
      selectedCode: dealerData?.[0]?.['经销商代码'] || '',
      months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月'],
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
      errorMessage: '',
      inputCode: '',
      inputProvince: ''
    }
  },
  computed: {
    currentDealer() {
      return this.dealers.find((d) => d['经销商代码'] === this.selectedCode) || {}
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
      const metrics = [
        { key: '销量', unit: '辆' },
        { key: '客流量', unit: '人次' },
        { key: '线索量', unit: '条' },
        { key: '潜客量', unit: '人' }
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
  },
  mounted() {
    this.$nextTick(() => {
      this.initCharts()
      this.renderCharts()
    })
    window.addEventListener('resize', this.handleResize)
  },
  watch: {
    selectedCode() {
      this.renderCharts()
    },
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
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
        '潜客量': 'c11e2dd',
        '成交率': 'ceeb1fd',
        '战败率': 'c24c9ff',
        '成交响应时间': 'cffff00'
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
      this.renderTrend()
      this.renderFunnel()
      this.renderRate()
      this.renderResponseTime()
      this.renderPolicy()
      this.renderGsev()
      this.renderReviewCharts()
    },
    renderTrend() {
      const sales = this.getSeries('销量')
      const traffic = this.getSeries('客流量')
      const leads = this.getSeries('线索量')
      const potential = this.getSeries('潜客量')
      this.charts.trend.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },
        legend: {
          data: ['销量', '客流量', '线索量', '潜客量'],
          right: 12,
          top: 10,
          orient: 'vertical',
          textStyle: { color: '#333' },
        },
        // 右侧为图例预留空间，避免与图形重叠
        grid: { left: 50, right: 140, top: 40, bottom: 40 },
        xAxis: {
          type: 'category',
          data: this.months,
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          axisLabel: { color: '#666' },
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          splitLine: { lineStyle: { color: 'rgba(63,169,245,0.2)' } },
          axisLabel: { color: '#666' },
        },
        series: [
          {
            name: '销量',
            type: 'bar',
            data: sales,
            barWidth: 14,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#5ad8ff' },
                { offset: 1, color: '#1767ff' },
              ]),
            },
          },
          {
            name: '客流量',
            type: 'line',
            smooth: true,
            data: traffic,
            symbol: 'circle',
            itemStyle: { color: '#b37feb' },
            areaStyle: { color: 'rgba(179, 127, 235, 0.12)' },
          },
          {
            name: '线索量',
            type: 'line',
            smooth: true,
            data: leads,
            symbol: 'circle',
            itemStyle: { color: '#ffd166' },
          },
          {
            name: '潜客量',
            type: 'line',
            smooth: true,
            data: potential,
            symbol: 'circle',
            itemStyle: { color: '#4de1c1' },
            areaStyle: { color: 'rgba(77,225,193,0.15)' },
          },
        ],
      })
    },
    renderFunnel() {
      const avgTraffic = this.average(this.getSeries('客流量'))
      const avgLeads = this.average(this.getSeries('线索量'))
      const avgPotential = this.average(this.getSeries('潜客量'))
      const avgSales = this.average(this.getSeries('销量'))
      this.charts.funnel.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'item', formatter: '{b}<br/>平均 {c}' },
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
            gap: 6,
            sort: 'descending',
            label: {
              color: '#333',
              // 使用回调返回字符串，保证换行生效
              formatter: (params) => `${params.name}\n${params.value}`,
            },
            itemStyle: {
              borderColor: '#fff',
              borderWidth: 1,
            },
            data: [
              { value: avgTraffic, name: '客流' },
              { value: avgLeads, name: '线索' },
              { value: avgPotential, name: '潜客' },
              { value: avgSales, name: '成交（销量）' },
            ],
            color: ['#b37feb', '#5ad8ff', '#52c41a', '#ff6b6b'],
          },
        ],
      })
    },
    renderRate() {
      const rate = this.getSeries('成交率').map((v) => this.toNumber(v) * 100)
      const defeat = this.getSeries('战败率').map((v) => this.toNumber(v) * 100)
      this.charts.rate.setOption({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis', valueFormatter: (v) => `${v?.toFixed(1)}%` },
        legend: {
          data: ['成交率', '战败率'],
          top: 10,
          left: 'center',
          orient: 'horizontal',
          textStyle: { color: '#333' },
        },
        // 图例在上方，调整grid以适应
        grid: { left: 30, right: 30, top: 40, bottom: 40 },
        xAxis: {
          type: 'category',
          data: this.months,
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          axisLabel: { color: '#666' },
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            formatter: '{value}%',
            color: '#666',
          },
          splitLine: { lineStyle: { color: 'rgba(63,169,245,0.2)' } },
        },
        series: [
          {
            name: '成交率',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            data: rate,
            itemStyle: { color: '#52c41a' },
            areaStyle: { color: 'rgba(82,196,26,0.15)' },
          },
          {
            name: '战败率',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            data: defeat,
            itemStyle: { color: '#ff6b6b' },
            areaStyle: { color: 'rgba(255,107,107,0.15)' },
          },
        ],
      })
    },
    average(arr = []) {
      if (!arr.length) return 0
      return arr.reduce((sum, v) => sum + this.toNumber(v), 0) / arr.length
    },
    renderResponseTime() {
      const successResponseTime = this.getSeries('成交响应时间')
      const failureResponseTime = this.getSeries('战败响应时间')
      const successAvg = this.average(successResponseTime)
      const failureAvg = this.average(failureResponseTime)
      const avgSuccessData = Array(this.months.length).fill(successAvg)
      const avgFailureData = Array(this.months.length).fill(failureAvg)
      this.charts.responseTime.setOption({
        backgroundColor: 'transparent',
        tooltip: { 
          trigger: 'axis',
          valueFormatter: (v) => `${v?.toFixed(1)}分钟`
        },
        legend: {
          data: ['成功响应时间', '失败响应时间', '成功响应时间平均值', '失败响应时间平均值'],
          top: 10,
          left: 'center',
          orient: 'horizontal',
          textStyle: { color: '#333' },
        },
        grid: { left: 30, right: 30, top: 90, bottom: 40 },
        xAxis: {
          type: 'category',
          data: this.months,
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          axisLabel: { color: '#666' },
        },
        yAxis: {
          type: 'value',
          name: '分钟',
          nameTextStyle: { color: '#666' },
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          splitLine: { lineStyle: { color: 'rgba(63,169,245,0.2)' } },
          axisLabel: { color: '#666' },
        },
        series: [
          {
            name: '成功响应时间',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            data: successResponseTime,
            itemStyle: { color: '#52c41a' },
            areaStyle: { color: 'rgba(82,196,26,0.15)' },
          },
          {
            name: '失败响应时间',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            data: failureResponseTime,
            itemStyle: { color: '#ff6b6b' },
            areaStyle: { color: 'rgba(255,107,107,0.15)' },
          },
          {
            name: '成功响应时间平均值',
            type: 'line',
            data: avgSuccessData,
            itemStyle: { color: '#1890ff' },
            lineStyle: { 
              type: 'dashed',
              width: 2
            },
            symbol: 'none',
            emphasis: {
              focus: 'series'
            }
          },
          {
            name: '失败响应时间平均值',
            type: 'line',
            data: avgFailureData,
            itemStyle: { color: '#fa8c16' },
            lineStyle: { 
              type: 'dashed',
              width: 2
            },
            symbol: 'none',
            emphasis: {
              focus: 'series'
            }
          },
        ],
      })
    },
    renderPolicy() {
      const policyData = this.getSeries('政策')
      const policyAvg = this.average(policyData)
      const avgPolicyData = Array(this.months.length).fill(policyAvg)
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
          textStyle: { color: '#333' },
        },
        grid: { left: 30, right: 30, top: 60, bottom: 40 },
        xAxis: {
          type: 'category',
          data: this.months,
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          axisLabel: { color: '#666' },
        },
        yAxis: {
          type: 'value',
          name: '政策值',
          nameTextStyle: { color: '#666' },
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          splitLine: { lineStyle: { color: 'rgba(63,169,245,0.2)' } },
          axisLabel: { color: '#666' },
        },
        series: [
          {
            name: '政策指标',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            data: policyData,
            itemStyle: { color: '#9c27b0' },
            areaStyle: { color: 'rgba(156,39,176,0.15)' },
          },
          {
            name: '政策指标平均值',
            type: 'line',
            data: avgPolicyData,
            itemStyle: { color: '#ff9800' },
            lineStyle: { 
              type: 'dashed',
              width: 2
            },
            symbol: 'none',
            emphasis: {
              focus: 'series'
            }
          },
        ],
      })
    },
    renderGsev() {
      const gsevData = this.getSeries('GSEV')
      const gsevAvg = this.average(gsevData)
      const avgGsevData = Array(this.months.length).fill(gsevAvg)
      
      // 计算Y轴范围，突出显示变化
      const minValue = Math.min(...gsevData) * 0.99
      const maxValue = Math.max(...gsevData) * 1.01
      
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
          textStyle: { color: '#333' },
        },
        grid: { left: 30, right: 30, top: 60, bottom: 40 },
        xAxis: {
          type: 'category',
          data: this.months,
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          axisLabel: { color: '#666' },
        },
        yAxis: {
          type: 'value',
          name: 'GSEV',
          nameTextStyle: { color: '#666' },
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          splitLine: { lineStyle: { color: 'rgba(63,169,245,0.2)' } },
          axisLabel: {
            color: '#666',
            formatter: (value) => value.toFixed(0)
          },
          min: minValue,
          max: maxValue,
        },
        series: [
          {
            name: 'GSEV',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            data: gsevData,
            itemStyle: { 
              color: '#4caf50',
              borderWidth: 2,
              borderColor: '#fff'
            },
            lineStyle: {
              width: 3,
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: '#4caf50' },
                { offset: 1, color: '#81c784' }
              ])
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(76,175,80,0.4)' },
                { offset: 1, color: 'rgba(76,175,80,0.05)' }
              ])
            }
          },
          {
            name: 'GSEV平均值',
            type: 'line',
            data: avgGsevData,
            itemStyle: { color: '#ff9800' },
            lineStyle: { 
              type: 'dashed',
              width: 2
            },
            symbol: 'none',
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
        if (!reviewCount) {
          chart.setOption({
            backgroundColor: 'transparent',
            title: {
              text: '暂无数据',
              left: 'center',
              top: 'center',
              textStyle: {
                color: '#999',
                fontSize: 12
              }
            },
            series: []
          })
          return
        }
        
        const goodPercent = reviewCount > 0 ? (goodCount / reviewCount * 100).toFixed(1) : 0
        const badPercent = reviewCount > 0 ? (badCount / reviewCount * 100).toFixed(1) : 0
        
        chart.setOption({
          backgroundColor: 'transparent',
          tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} ({d}%)'
          },
          series: [
            {
              name: '评价占比',
              type: 'pie',
              radius: ['40%', '70%'],
              center: ['50%', '50%'],
              avoidLabelOverlap: false,
              itemStyle: {
                borderRadius: 10,
                borderColor: '#fff',
                borderWidth: 2
              },
              label: {
                show: true,
                formatter: '{b}: {d}%',
                color: '#333',
                fontSize: 10
              },
              emphasis: {
                label: {
                  show: true,
                  fontSize: 12,
                  fontWeight: 'bold'
                },
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              },
              data: [
                { value: goodCount, name: '好评', itemStyle: { color: '#52c41a' } },
                { value: badCount, name: '差评', itemStyle: { color: '#ff4d4f' } }
              ]
            }
          ]
        })
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
  },
}
</script>

<style scoped>
.dashboard-container {
  width: 100%;
  overflow: hidden;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e8e8e8;
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

/* 月度快照样式 */
.aleftboxttop {
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

.metric-item.potential {
  color: #eb2f96;
}

.metric-item.rate {
  color: #722ed1;
}

/* 核心指标和销售漏斗布局 */
.core-funnel-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
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

.core-metrics-container {
  flex: 1;
  min-width: 0;
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

.funnel-container {
  flex: 1;
  min-width: 0;
}

.aleftboxtmidd {
  height: 100%;
  min-height: 400px;
}

/* 让销量趋势分析和销售漏斗模块高度保持一致 */
.trend-funnel-row .amiddboxttop,
.trend-funnel-row .amiddboxtbott1 {
  min-height: 420px;
  height: 420px;
}

.amiddboxtbott1 {
  height: 100%;
  padding: 20px;
}

.aleftboxttopcont {
  height: calc(100% - 40px);
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

.metric-toggle-btn {
  padding: 6px 12px;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.metric-toggle-btn:hover {
  background-color: #e0e0e0;
}

/* 核心指标小模块布局 */
.lefttoday_number {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  height: 100%;
  align-content: center;
}

.widget-inline-box {
  flex: 1;
  min-width: 140px;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 160px;
}

/* 核心指标颜色对应月度快照 */
.widget-inline-box:nth-child(1),
.metrics-row:nth-child(1) .widget-inline-box:nth-child(1) {
  background-color: #e6f7ff;
  border-left: 4px solid #1890ff;
}

.widget-inline-box:nth-child(2),
.metrics-row:nth-child(1) .widget-inline-box:nth-child(2) {
  background-color: #f6ffed;
  border-left: 4px solid #52c41a;
}

.widget-inline-box:nth-child(3),
.metrics-row:nth-child(2) .widget-inline-box:nth-child(1) {
  background-color: #fff7e6;
  border-left: 4px solid #fa8c16;
}

.widget-inline-box:nth-child(4),
.metrics-row:nth-child(2) .widget-inline-box:nth-child(2) {
  background-color: #fff0f6;
  border-left: 4px solid #eb2f96;
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

.both-mode-box {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.metrics-row {
  display: flex;
  gap: 20px;
  flex: 1;
  width: 100%;
}

.metrics-row .widget-inline-box {
  flex: 1;
  min-width: 0;
  width: calc(50% - 10px);
}

/* 销售漏斗图表容器 */
.amiddboxtbott1content {
  width: 100%;
  height: 350px;
  margin: 10px 0;
}

/* 经销商选择模块布局 */
.dealer-selector-container {
  margin-bottom: 20px;
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
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 15px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
}

.four-in-one-item h2 {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
}

.four-in-one-item .chart-container {
  flex: 1;
  min-height: 250px;
}







/* 图表容器样式 */
.chart-container {
  width: 100%;
  height: 350px;
  margin: 10px 0;
}

/* 评价占比框样式 */
.review-box {
  margin-top: 20px;
}

.review-charts-container {
  width: 100%;
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

.review-chart {
  flex: 1;
  min-height: 100px;
  width: 100%;
}

/* 经销商选择器样式 */
.dealer-selector {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
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