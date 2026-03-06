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
              <th>综合得分</th>
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
              <td>{{ history.month }}月</td>
              <td>{{ history.prediction_result }}</td>
              <td>{{ history.comprehensive_score || 0 }}</td>
              <td>{{ history.created_at }}</td>
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
                <span class="value">{{ selectedHistory.month }}月</span>
              </div>
              <div class="info-item">
                <span class="label">雷达图月份:</span>
                <span class="value">{{ selectedHistory.month_for_radar }}月</span>
              </div>
              <div class="info-item">
                <span class="label">预测结果:</span>
                <span class="value">{{ selectedHistory.prediction_result }}</span>
              </div>
              <div class="info-item">
                <span class="label">综合得分:</span>
                <span class="value">{{ selectedHistory.comprehensive_score || 0 }}</span>
              </div>
              <div class="info-item">
                <span class="label">创建时间:</span>
                <span class="value">{{ selectedHistory.created_at }}</span>
              </div>
            </div>
          </div>
          
          <!-- 图表区域 -->
          <div class="charts-section">
            <div class="chart-container">
              <h4>销量对比</h4>
              <div ref="salesChart" class="chart" style="width: 100%; height: 400px;"></div>
            </div>
            <div class="chart-container">
              <h4>五力分析</h4>
              <div ref="radarChart" class="chart" style="width: 100%; height: 400px;"></div>
            </div>
          </div>
          
          <!-- 五力数据表格 -->
          <div class="five-forces-table">
            <h4>五力数据</h4>
            <table class="forces-table">
              <thead>
                <tr>
                  <th>能力维度</th>
                  <th>得分</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>传播获客力</td>
                  <td>{{ selectedHistory.propagation_force || 0 }}</td>
                </tr>
                <tr>
                  <td>体验力</td>
                  <td>{{ selectedHistory.experience_force || 0 }}</td>
                </tr>
                <tr>
                  <td>转化力</td>
                  <td>{{ selectedHistory.conversion_force || 0 }}</td>
                </tr>
                <tr>
                  <td>服务力</td>
                  <td>{{ selectedHistory.service_force || 0 }}</td>
                </tr>
                <tr>
                  <td>经营力</td>
                  <td>{{ selectedHistory.operation_force || 0 }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { getPredictionHistory, getPredictionHistoryDetail } from '@/api/prediction'

export default {
  name: 'HistoryRecords',
  data() {
    return {
      historyList: [],
      selectedHistory: {},
      showDetailDialog: false,
      salesChart: null,
      radarChart: null,
      loading: false
    }
  },
  mounted() {
    this.fetchHistoryList()
  },
  methods: {
    // 返回销量预测页面
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
    viewHistoryDetail(history) {
      this.selectedHistory = history
      this.showDetailDialog = true
      this.$nextTick(() => {
        this.renderSalesChart()
        this.renderRadarChart()
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
      if (this.radarChart) {
        this.radarChart.dispose()
        this.radarChart = null
      }
    },
    
    // 渲染销量折线图
    renderSalesChart() {
      if (!this.$refs.salesChart) return
      
      this.salesChart = echarts.init(this.$refs.salesChart)
      
      // 模拟原始销量数据（实际应从后端获取）
      const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月']
      const originalSales = [100, 110, 105, 115, 120, 118, 125, 130, 128, 135]
      
      // 预测销量数据
      const predictionData = [...originalSales]
      // 在预测月份位置设置预测值
      if (this.selectedHistory.month) {
        const monthIndex = this.selectedHistory.month - 1
        if (monthIndex >= 0 && monthIndex < predictionData.length) {
          predictionData[monthIndex] = this.selectedHistory.prediction_result
        }
      }
      
      const option = {
        tooltip: {
          trigger: 'axis'
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
            type: 'line',
            data: predictionData,
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            itemStyle: {
              color: '#ff6b6b'
            },
            lineStyle: {
              width: 2,
              type: 'dashed'
            }
          }
        ]
      }
      
      this.salesChart.setOption(option)
      
      // 监听窗口 resize 事件
      window.addEventListener('resize', this.handleResize)
    },
    
    // 渲染五力雷达图
    renderRadarChart() {
      if (!this.$refs.radarChart) return
      
      this.radarChart = echarts.init(this.$refs.radarChart)
      
      const option = {
        tooltip: {},
        legend: {
          data: ['五力得分'],
          right: 10,
          top: 10
        },
        radar: {
          indicator: [
            { name: '传播获客力', max: 20 },
            { name: '体验力', max: 20 },
            { name: '转化力', max: 40 },
            { name: '服务力', max: 10 },
            { name: '经营力', max: 10 }
          ]
        },
        series: [
          {
            name: '五力得分',
            type: 'radar',
            data: [
              {
                value: [
                  this.selectedHistory.propagation_force || 0,
                  this.selectedHistory.experience_force || 0,
                  this.selectedHistory.conversion_force || 0,
                  this.selectedHistory.service_force || 0,
                  this.selectedHistory.operation_force || 0
                ],
                name: '五力得分',
                areaStyle: {
                  opacity: 0.3
                }
              }
            ]
          }
        ]
      }
      
      this.radarChart.setOption(option)
    },
    
    // 处理窗口 resize 事件
    handleResize() {
      if (this.salesChart) {
        this.salesChart.resize()
      }
      if (this.radarChart) {
        this.radarChart.resize()
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
    if (this.radarChart) {
      this.radarChart.dispose()
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
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-bottom: 30px;
}

.chart-container {
  background-color: #fafafa;
  padding: 20px;
  border-radius: 8px;
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