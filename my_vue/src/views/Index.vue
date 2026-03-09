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
              <span class="sub-title">全国门店地理分布</span>
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
      fiveForcesData: [],
      dealerData: [],
      totalDealers: 0,
      provinceDealerCount: {}
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
      this.$nextTick(() => {
        this.initRadarChart()
        this.initLineChart()
        this.initPieChart()
        this.initMap()
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
      console.log('折线图数据:', { salesData, customerData, leadData, potentialData })
      
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
          top: '15%',
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
            name: '销量/客流量/潜客量',
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
            name: '线索量',
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
        animation: true,
        animationDuration: 1000,
        animationEasing: 'cubicOut',
        animationDelay: function(idx) {
          return idx * 50;
        },
        series: [
          {
            name: '销量',
            type: 'line',
            smooth: true,
            data: salesData,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 3,
              color: '#3b82f6'
            },
            itemStyle: {
              color: '#3b82f6',
              borderWidth: 2,
              borderColor: '#fff'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0.05)'
                }
              ])
            }
          },
          {
            name: '客流量',
            type: 'line',
            smooth: true,
            data: customerData,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 3,
              color: '#8b5cf6'
            },
            itemStyle: {
              color: '#8b5cf6',
              borderWidth: 2,
              borderColor: '#fff'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(139, 92, 246, 0.3)' },
                { offset: 1, color: 'rgba(139, 92, 246, 0.05)'
                }
              ])
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
            lineStyle: {
              width: 3,
              color: '#f59e0b'
            },
            itemStyle: {
              color: '#f59e0b',
              borderWidth: 2,
              borderColor: '#fff'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(245, 158, 11, 0.3)' },
                { offset: 1, color: 'rgba(245, 158, 11, 0.05)'
                }
              ])
            }
          },
          {
            name: '潜客量',
            type: 'line',
            smooth: true,
            data: potentialData,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 3,
              color: '#10b981'
            },
            itemStyle: {
              color: '#10b981',
              borderWidth: 2,
              borderColor: '#fff'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
                { offset: 1, color: 'rgba(16, 185, 129, 0.05)'
                }
              ])
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
        this.renderMap()
      } catch (error) {
        console.error('加载地图数据失败:', error)
      }
    },
    renderMap() {
      const provinceMapping = {
        '辽宁省': '辽宁省',
        '吉林省': '吉林省',
        '黑龙江省': '黑龙江省',
        '北京市': '北京市',
        '天津市': '天津市',
        '河北省': '河北省',
        '山西省': '山西省',
        '内蒙古自治区': '内蒙古自治区',
        '上海市': '上海市',
        '江苏省': '江苏省',
        '浙江省': '浙江省',
        '安徽省': '安徽省',
        '福建省': '福建省',
        '江西省': '江西省',
        '山东省': '山东省',
        '河南省': '河南省',
        '湖北省': '湖北省',
        '湖南省': '湖南省',
        '广东省': '广东省',
        '广西壮族自治区': '广西壮族自治区',
        '海南省': '海南省',
        '重庆市': '重庆市',
        '四川省': '四川省',
        '贵州省': '贵州省',
        '云南省': '云南省',
        '西藏自治区': '西藏自治区',
        '陕西省': '陕西省',
        '甘肃省': '甘肃省',
        '青海省': '青海省',
        '宁夏回族自治区': '宁夏回族自治区',
        '新疆维吾尔自治区': '新疆维吾尔自治区',
        '台湾省': '台湾省',
        '香港特别行政区': '香港特别行政区',
        '澳门特别行政区': '澳门特别行政区'
      }
      const data = Object.keys(this.provinceDealerCount).map(province => ({
        name: province,
        value: this.provinceDealerCount[province]
      }))
      const maxValue = Math.max(...Object.values(this.provinceDealerCount), 50)
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
          bottom: '10%',
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
          },
          {
            name: '门店标注',
            type: 'scatter',
            coordinateSystem: 'geo',
            symbol: 'pin',
            symbolSize: 30,
            label: {
              show: true,
              formatter: '{@[2]}',
              color: '#fff',
              fontSize: 10
            },
            itemStyle: {
              color: '#ff4d4f'
            },
            data: this.getScatterData()
          }
        ]
      }
      this.mapChart.setOption(option)
    },
    getScatterData() {
      const provinceCoords = {
        '辽宁省': [123.4, 41.8],
        '吉林省': [125.3, 43.9],
        '黑龙江省': [126.6, 45.8],
        '北京市': [116.4, 39.9],
        '天津市': [117.2, 39.1],
        '河北省': [114.5, 38.0],
        '山西省': [112.5, 37.9],
        '内蒙古自治区': [111.7, 41.8],
        '上海市': [121.5, 31.2],
        '江苏省': [118.8, 32.1],
        '浙江省': [120.2, 30.3],
        '安徽省': [117.3, 31.9],
        '福建省': [119.3, 26.1],
        '江西省': [115.9, 28.7],
        '山东省': [117.0, 36.7],
        '河南省': [113.7, 34.8],
        '湖北省': [114.3, 30.6],
        '湖南省': [113.0, 28.2],
        '广东省': [113.3, 23.1],
        '广西壮族自治区': [108.3, 22.8],
        '海南省': [110.4, 19.0],
        '重庆市': [106.5, 29.6],
        '四川省': [104.1, 30.7],
        '贵州省': [106.7, 26.6],
        '云南省': [102.7, 25.0],
        '西藏自治区': [91.1, 29.6],
        '陕西省': [109.0, 34.3],
        '甘肃省': [103.8, 36.1],
        '青海省': [101.8, 36.6],
        '宁夏回族自治区': [106.3, 38.5],
        '新疆维吾尔自治区': [87.6, 43.8]
      }
      return Object.keys(this.provinceDealerCount).map(province => {
        const coords = provinceCoords[province] || [105, 35]
        return {
          name: province,
          value: [...coords, this.provinceDealerCount[province]]
        }
      })
    },
    handleResize() {
      if (this.radarChart) this.radarChart.resize()
      if (this.lineChart) this.lineChart.resize()
      if (this.pieChart) this.pieChart.resize()
      if (this.mapChart) this.mapChart.resize()
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
</style>
