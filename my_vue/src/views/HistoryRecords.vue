<template>
  <div class="history-records-container">
    <div class="page-header">
      <h1 class="page-title">历史预测记录</h1>
      <button @click="goBack" class="back-btn">返回销量预测</button>
    </div>
    
    <div class="history-table-container">
      <h2 class="section-title">预测历史记录</h2>
      <div class="table-wrapper">
        <table class="history-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>经销商代码</th>
              <th>变化维度</th>
              <th>变化百分比</th>
              <th>预测月份</th>
              <th>预测结果</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="history in historyList" :key="history.id">
              <td>{{ history.id }}</td>
              <td>{{ history.dealer_code }}</td>
              <td>{{ history.dimension }}</td>
              <td>{{ history.change_percentage }}%</td>
              <td>{{ history.target_month }}月</td>
              <td>{{ history.predicted_sales }}</td>
              <td>{{ formatLocalTime(history.created_at) }}</td>
              <td>
                <button @click="viewHistoryDetail(history)" class="view-btn">查看详情</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div v-if="historyList.length === 0" class="empty-state">
        <p>暂无历史预测记录</p>
      </div>
    </div>
    
    <!-- 历史记录详情弹窗 -->
    <div v-if="showDetailDialog" class="detail-dialog-overlay">
      <div class="detail-dialog">
        <div class="dialog-header">
          <h3>预测详情</h3>
          <button @click="closeDetailDialog" class="close-btn">&times;</button>
        </div>
        <div class="dialog-content">
          <!-- 基本信息 -->
          <div class="basic-info">
            <h4>基本信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">经销商代码:</span>
                <span class="value">{{ selectedHistory.dealer_code }}</span>
              </div>
              <div class="info-item">
                <span class="label">变化维度:</span>
                <span class="value">{{ selectedHistory.dimension }}</span>
              </div>
              <div class="info-item">
                <span class="label">变化百分比:</span>
                <span class="value">{{ selectedHistory.change_percentage }}%</span>
              </div>
              <div class="info-item">
                <span class="label">预测月份:</span>
                <span class="value">{{ selectedHistory.target_year }}年{{ selectedHistory.target_month }}月</span>
              </div>
              <div class="info-item">
                <span class="label">雷达图月份:</span>
                <span class="value">{{ selectedHistory.month_for_radar }}月</span>
              </div>
              <div class="info-item">
                <span class="label">预测结果:</span>
                <span class="value">{{ selectedHistory.predicted_sales }}</span>
              </div>
              <div class="info-item">
                <span class="label">创建时间:</span>
                <span class="value">{{ formatLocalTime(selectedHistory.created_at) }}</span>
              </div>
            </div>
          </div>
          
          <!-- 图表区域 -->
          <div class="charts-section">
            <div class="chart-container">
              <h4>销量对比</h4>
              <div ref="salesChart" class="chart" style="width: 100%; height: 400px;"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { getPredictionHistory, getPredictionHistoryDetail, getOriginalSalesData } from '@/api/prediction'

export default {
  name: 'HistoryRecords',
  data() {
    return {
      historyList: [],
      selectedHistory: {},
      showDetailDialog: false,
      salesChart: null,
      loading: false,
      originalSalesData: []
    }
  },
  mounted() {
    this.fetchHistoryList()
  },
  methods: {
    formatLocalTime(utcTimeStr) {
      if (!utcTimeStr) return '-'
      const date = new Date(utcTimeStr + ' UTC')
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    },
    
    goBack() {
      this.$router.push('/dashboard/prediction')
    },
    
    // 获取历史记录列表
    async fetchHistoryList() {
      try {
        this.loading = true
        const response = await getPredictionHistory()
        if (response.success) {
          this.historyList = response.data
        }
      } catch (error) {
        console.error('获取历史记录失败:', error)
      } finally {
        this.loading = false
      }
    },
    
    // 查看历史记录详情
    async viewHistoryDetail(history) {
      this.selectedHistory = history
      this.showDetailDialog = true
      
      try {
        const response = await getOriginalSalesData(history.dealer_code, 10)
        if (response && response.data && Array.isArray(response.data)) {
          this.originalSalesData = response.data
        }
      } catch (error) {
        console.error('获取原始销量数据失败:', error)
        this.originalSalesData = []
      }
      
      this.$nextTick(() => {
        this.renderSalesChart()
      })
    },
    
    // 关闭详情弹窗
    closeDetailDialog() {
      this.showDetailDialog = false
      this.selectedHistory = {}
      // 销毁图表实例
      if (this.salesChart) {
        this.salesChart.dispose()
        this.salesChart = null
      }
    },
    
    renderSalesChart() {
      if (!this.$refs.salesChart) return
      
      this.salesChart = echarts.init(this.$refs.salesChart)
      
      const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月']
      
      const originalSales = months.map((_, index) => {
        const month = index + 1
        const item = this.originalSalesData.find(d => d.month === month)
        return item && item.sales != null ? item.sales : 0
      })
      
      const predictionData = new Array(10).fill(null)
      if (this.selectedHistory.target_month && this.selectedHistory.predicted_sales) {
        const monthIndex = this.selectedHistory.target_month - 1
        if (monthIndex >= 0 && monthIndex < predictionData.length) {
          predictionData[monthIndex] = this.selectedHistory.predicted_sales
        }
      }
      
      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            let result = params[0].name + '<br/>'
            params.forEach(param => {
              if (param.value !== null) {
                result += param.marker + param.seriesName + ': ' + param.value + '<br/>'
              }
            })
            return result
          }
        },
        legend: {
          data: ['原始销量', '预测销量'],
          right: 10,
          top: 10
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: months
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '原始销量',
            type: 'line',
            data: originalSales,
            smooth: true,
            itemStyle: {
              color: '#5ad8ff'
            },
            lineStyle: {
              width: 2
            },
            areaStyle: {
              color: 'rgba(90,216,255,0.15)'
            }
          },
          {
            name: '预测销量',
            type: 'scatter',
            data: predictionData,
            symbol: 'circle',
            symbolSize: 12,
            itemStyle: {
              color: '#ff4d4f',
              borderColor: '#fff',
              borderWidth: 2
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(255,77,79,0.5)'
              }
            }
          }
        ]
      }
      
      this.salesChart.setOption(option)
      
      window.addEventListener('resize', this.handleResize)
    },
    
    // 处理窗口 resize 事件
    handleResize() {
      if (this.salesChart) {
        this.salesChart.resize()
      }
    }
  },
  beforeDestroy() {
    // 移除事件监听器
    window.removeEventListener('resize', this.handleResize)
    // 销毁图表实例
    if (this.salesChart) {
      this.salesChart.dispose()
    }
  }
}
</script>

<style scoped>
.history-records-container {
  width: 100%;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.back-btn {
  padding: 8px 16px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.back-btn:hover {
  background-color: #40a9ff;
}

.section-title {
  font-size: 18px;
  font-weight: 500;
  color: #333;
  margin-bottom: 20px;
}

.table-wrapper {
  overflow-x: auto;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  overflow: hidden;
}

.history-table th,
.history-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.history-table th {
  background-color: #fafafa;
  font-weight: 500;
  color: #333;
}

.history-table tbody tr:hover {
  background-color: #f9f9f9;
}

.view-btn {
  padding: 6px 12px;
  background-color: #52c41a;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.view-btn:hover {
  background-color: #73d13d;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-top: 20px;
}

.empty-state p {
  color: #999;
  font-size: 16px;
  margin: 0;
}

/* 详情弹窗样式 */
.detail-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.detail-dialog {
  background-color: white;
  border-radius: 8px;
  width: 90%;
  max-width: 1000px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.close-btn:hover {
  background-color: #f0f0f0;
  color: #333;
}

.dialog-content {
  padding: 20px;
}

.basic-info {
  margin-bottom: 30px;
}

.basic-info h4,
.chart-container h4,
.five-forces-table h4 {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item .label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.info-item .value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.charts-section {
  margin-bottom: 30px;
}

.chart-container {
  background-color: #fafafa;
  padding: 20px;
  border-radius: 8px;
  width: 100%;
}

.forces-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #fafafa;
  border-radius: 8px;
  overflow: hidden;
}

.forces-table th,
.forces-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.forces-table th {
  background-color: #f0f0f0;
  font-weight: 500;
  color: #333;
}

.forces-table tbody tr:hover {
  background-color: #f0f0f0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .detail-dialog {
    width: 95%;
    margin: 20px;
  }
}
</style>