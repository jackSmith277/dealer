<template>
  <div class="sales-prediction-container">
    <div class="page-header">
      <h1 class="page-title">销量预测</h1>
      <button @click="goToHistory" class="history-btn">查看历史记录</button>
    </div>
    
    <div class="content-layout">
      <div class="left-section">
        <div class="form-card">
          <h2 class="card-title">销量预测设置</h2>
          <div class="form-content">
            <form @submit.prevent="submitForm">
              <div class="form-group">
                <label for="dealer_code">选择经销商:</label>
                <DealerSelector 
                  v-model="formData.dealer_code" 
                  :dealers="dealerList" 
                />
              </div>

              <div class="form-group">
                <label for="dimension">变化维度:</label>
                <select id="dimension" name="dimension" v-model="formData.dimension" required>
                  <option value="customer_flow">客流量 (customer_flow)</option>
                  <option value="test_drives">试驾数 (test_drives)</option>
                  <option value="leads">线索量 (leads)</option>
                  <option value="potential_customers">潜客量 (potential_customers)</option>
                  <option value="defeat_rate">战败率 (defeat_rate)</option>
                  <option value="success_rate">成交率 (success_rate)</option>
                  <option value="success_response_time">成交响应时间</option>
                  <option value="defeat_response_time">战败响应时间</option>
                  <option value="policy">国家政策补贴</option>
                  <option value="gsev">gsev</option>
                  <option value="lead_to_potential_rate">线索转化率</option>
                  <option value="potential_to_store_rate">潜客进店率</option>
                  <option value="store_to_sales_rate">进店成交率</option>
                </select>
              </div>

              <div class="form-group">
                <label for="change_percentage">变化百分比:</label>
                <select id="change_percentage" name="change_percentage" v-model="formData.change_percentage" required>
                  <option v-for="i in percentageOptions" :key="i" :value="i">{{ i }}%</option>
                </select>
              </div>

              <div class="form-group">
                <label for="base_month">基准月份 (1-10):</label>
                <select id="base_month" name="base_month" v-model="formData.base_month">
                  <option v-for="m in 10" :key="m" :value="m">{{ m }} 月</option>
                </select>
              </div>

              <div class="form-group">
                <label for="month_for_radar">雷达图月份:</label>
                <select id="month_for_radar" name="month_for_radar" v-model="formData.month_for_radar" @change="handleMonthChange">
                  <option v-for="m in 10" :key="m" :value="m">{{ m }} 月</option>
                </select>
              </div>

              <button type="submit" class="submit-btn" :disabled="loading">
                {{ loading ? '预测中...' : '提交' }}
              </button>
            </form>

            <!-- Button for Displaying Five Forces Calculation Formula -->
            <button type="button" @click="toggleFormula" class="formula-btn">显示五力计算公式</button>
          </div>
        </div>

        <!-- 五力计算公式模态框 -->
        <div v-if="showFormula" class="modal-overlay" @click="toggleFormula">
          <div class="modal-content" @click.stop>
            <div class="modal-header">
              <h2 class="modal-title">五力计算公式</h2>
              <button type="button" class="modal-close" @click="toggleFormula">×</button>
            </div>
            <div class="modal-body">
              <ul>
                <li><strong>传播获客力</strong> = (客流量 * 50% + 潜客量 * 20% + 线索量 * 30%)</li>
                <li><strong>体验力</strong> = (成交率 * 40% + 战败率 * 40% + 服务评分 * 20%)</li>
                <li><strong>转化力</strong> = (销量 * 50% + 成交率 * 10% + 成交响应时间 * 2.5% + 战败响应时间 * 2.5% + 试驾数 * 5% + 政策 * 5% + GSEV * 10% + 服务评分 * 5% + 终端检核平均分 * 10%)</li>
                <li><strong>服务力</strong> = (服务评分 * 40% + 试驾数 * 30% + 终端检核平均分 * 30%)</li>
                <li><strong>经营力</strong> = 固定为 3.5</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      <!-- left-section end -->
      
      <div class="right-section">
        <div class="chart-card">
          <h2 class="card-title">经销商原始销量</h2>
          <div class="chart-content">
            <!-- 折线统计图 -->
            <div ref="salesChart" class="sales-chart" style="height: 300px;"></div>
            
            <!-- 预测销量文字显示 -->
            <div v-if="predictionResult" class="prediction-text">
              <p><strong>预测销量:</strong> 预计{{ predictionResult.target_year }}年{{ predictionResult.target_month }}月份销量为 <span class="highlighted-value">{{ predictionResult.predicted_sales ? Math.round(predictionResult.predicted_sales) : '-' }}</span></p>
              <p><strong>销量变化:</strong> {{ Math.round(predictionResult.sales_change) }} ({{ predictionResult.sales_change_pct.toFixed(2) }}%)</p>
            </div>
            
            <!-- 错误信息显示 - 只在确实有错误信息时才显示 -->
            <div v-if="errorMessage" class="error-message">
              <p><strong>错误信息:</strong> {{ errorMessage }}</p>
            </div>

            <!-- 销量预测结果详细数据展示 -->
            <div v-if="predictionResult" class="prediction-details">
              <h3 class="details-title">销量预测结果详情</h3>
              <div class="prediction-data-grid">
                <div class="data-item">
                  <span class="data-label">经销商:</span>
                  <span class="data-value">{{ formData.dealer_code }}</span>
                </div>
                <div class="data-item">
                  <span class="data-label">变化维度:</span>
                  <span class="data-value">{{ formData.dimension }}</span>
                </div>
                <div class="data-item">
                  <span class="data-label">变化百分比:</span>
                  <span class="data-value">{{ formData.change_percentage }}%</span>
                </div>
                <div class="data-item">
                  <span class="data-label">基准月份:</span>
                  <span class="data-value">{{ formData.base_year }}年{{ formData.base_month }}月</span>
                </div>
                <div class="data-item">
                  <span class="data-label">预测月份:</span>
                  <span class="data-value">{{ predictionResult.target_year }}年{{ predictionResult.target_month }}月</span>
                </div>
                <div class="data-item">
                  <span class="data-label">预测销量:</span>
                  <span class="data-value">{{ predictionResult.predicted_sales ? Math.round(predictionResult.predicted_sales) : '-' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="bottom-cards">
          <!-- 雷达图 -->
          <div class="radar-card">
            <h2 class="card-title">五力雷达图</h2>
            <div class="radar-content">
              <div class="dealer-info">经销商代码: <strong>{{ formData.dealer_code }}</strong></div>
              <div class="radar-chart">
                <div id="radar-chart" style="width: 100%; height: 300px;"></div>
              </div>
            </div>
          </div>
          
          <!-- 五力数据 -->
          <div class="five-forces-card">
            <h2 class="card-title">五力数据</h2>
            <div class="five-forces-content">
              <table class="styled-table">
                <thead>
                  <tr>
                    <th>能力维度</th>
                    <th>权重</th>
                    <th>最终得分</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>传播获客力</td>
                    <td>20%</td>
                    <td>{{ fiveForcesData['传播获客力'] || 0 }}</td>
                  </tr>
                  <tr>
                    <td>体验力</td>
                    <td>20%</td>
                    <td>{{ fiveForcesData['体验力'] || 0 }}</td>
                  </tr>
                  <tr>
                    <td>转化力</td>
                    <td>40%</td>
                    <td>{{ fiveForcesData['转化力'] || 0 }}</td>
                  </tr>
                  <tr>
                    <td>服务力</td>
                    <td>10%</td>
                    <td>{{ fiveForcesData['服务力'] || 0 }}</td>
                  </tr>
                  <tr>
                    <td>经营力</td>
                    <td>10%</td>
                    <td>{{ fiveForcesData['经营力'] || 0 }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="2">综合得分</td>
                    <td>{{ fiveForcesData['综合得分'] || 0 }}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </div>
      <!-- right-section end -->
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { 
  getOriginalSalesData, 
  getPredictionResult,
  savePredictionHistory
} from '@/api/prediction'
import { mockData } from '@/api/mock'
import DealerSelector from '@/components/DealerSelector.vue'
import dealerData from '@/assets/dealerData.json'

export default {
  name: 'SalesPrediction',
  components: {
    DealerSelector
  },
  data() {
    return {
      formData: {
        dealer_code: '9210006',
        dimension: 'customer_flow',
        change_percentage: 10,
        base_year: 2024,
        base_month: 10,
        month_for_radar: 10
      },
      dealerCodes: [],
      dealerList: dealerData,
      percentageOptions: Array.from({length: 59}, (_, i) => (i + 1) * 5),
      showFormula: false,
      predictionResult: null,
      salesChanges: [],
      fiveForcesData: {},
      salesChart: null,
      loading: false,
      useMockData: false,
      backendAvailable: true,
      errorMessage: '',
      resizeListener: null
    }
  },
  mounted() {
    this.$nextTick(async () => {
      this.initSalesChart();
      // 获取原始销量数据，确保页面加载时能显示所有月份的原始销量
      await this.fetchOriginalSalesData();
    });
  },
  beforeDestroy() {
    // 清理事件监听器
    if (this.resizeListener) {
      window.removeEventListener('resize', this.resizeListener)
    }
  },
  methods: {
    // 跳转到历史记录页面
    goToHistory() {
      this.$router.push('/dashboard/history')
    },
    
    // 初始化数据
    async initData() {
      // 不再获取经销商列表，直接使用固定的经销商列表
      // 获取原始销量数据
      await this.fetchOriginalSalesData()
      // 五力数据将通过预测结果获取
    },

    toggleFormula() {
      this.showFormula = !this.showFormula;
    },

    // 获取原始销量数据
    async fetchOriginalSalesData() {
      try {
        this.errorMessage = ''
        const response = await getOriginalSalesData(this.formData.dealer_code, 10)
        console.log('获取原始销量数据响应:', response)
        
        if (response && response.data && Array.isArray(response.data)) {
          this.salesChanges = this.normalizeSalesChanges(response.data)
          console.log('标准化后的销量数据:', this.salesChanges)
        } else if (response && response.message) {
          this.errorMessage = response.message
          console.error('后端返回错误:', response.message)
        } else {
          console.error('后端返回数据格式错误:', response)
          this.errorMessage = '获取销量数据失败，请稍后重试'
        }
        this.updateSalesChart()
      } catch (error) {
        console.error('获取原始销量数据失败:', error)
        this.backendAvailable = false
        if (error.response && error.response.data && error.response.data.message) {
          this.errorMessage = error.response.data.message
        } else {
          this.errorMessage = '网络错误，请检查连接'
        }
      }
    },

    // 提交预测表单
    async submitForm() {
      try {
        this.errorMessage = ''
        this.loading = true
        
        this.predictionResult = null
        this.fiveForcesData = {}
        
        await this.fetchOriginalSalesData()
        
        const response = await getPredictionResult(this.formData)
        console.log('返回的对象')
        console.log(response)
        

        if (response.message) {
          const error = new Error(response.message)
          error.response = { data: { message: response.message } }
          throw error
        }

        // 处理后端返回的预测数据
        if (response.point_result) {
          const targetMonth = response.target_month
          console.log('预测目标月份:', targetMonth)
          console.log('当前销量数据:', this.salesChanges)
          const salesItem = this.salesChanges.find(s => s.month === targetMonth)
          console.log('找到的销量项:', salesItem)
          const originalSales = salesItem?.original_sales || 0
          console.log('原始销量:', originalSales)
          const predictedSales = response.point_result.scenario
          console.log('预测销量:', predictedSales)
          const salesChange = predictedSales - originalSales
          const salesChangePct = originalSales > 0 ? (salesChange / originalSales * 100) : 0
          console.log('销量变化:', salesChange, '变化率:', salesChangePct)
          
          this.predictionResult = {
            target_year: response.target_year,
            target_month: targetMonth,
            predicted_sales: predictedSales,
            baseline: response.point_result.baseline,
            delta: response.point_result.delta,
            delta_pct: response.point_result.delta_pct,
            original_sales: originalSales,
            sales_change: salesChange,
            sales_change_pct: salesChangePct
          }
        }

        // 处理销量变化数据
        if (response.sales_changes && Array.isArray(response.sales_changes)) {
          // 保留原始销量数据，只更新有变化的月份
          const updatedSalesChanges = [...this.salesChanges];
          response.sales_changes.forEach(item => {
            const month = Number(item.month);
            if (!Number.isFinite(month)) return;
            const index = updatedSalesChanges.findIndex(s => s.month === month);
            if (index !== -1) {
              // 只更新有变化的字段，保留原始销量
              updatedSalesChanges[index] = {
                ...updatedSalesChanges[index],
                ...item
              };
            }
          });
          this.salesChanges = updatedSalesChanges;
        }

        // 处理五力数据
        if (response.dealer_scores) {
          // 处理后端返回的dealer_scores数据结构
          const dealerCode = this.formData.dealer_code
          const month = this.formData.month_for_radar
          const monthStr = `${month}月`
          
          
          // 尝试不同类型的经销商代码键
          let dealerData = null
          
          // 首先尝试直接使用经销商代码
          if (response.dealer_scores[dealerCode]) {
            dealerData = response.dealer_scores[dealerCode]
          }
          
          // 尝试转换为数字类型
          if (!dealerData) {
            const dealerCodeNum = parseInt(dealerCode)
            if (response.dealer_scores[dealerCodeNum]) {
              dealerData = response.dealer_scores[dealerCodeNum]
            }
          }
          
          // 尝试遍历所有键，找到匹配的经销商代码
          if (!dealerData) {
            for (const key in response.dealer_scores) {
              if (key.toString() === dealerCode.toString()) {
                dealerData = response.dealer_scores[key]
                break
              }
            }
          }
          
          // 尝试获取第一个可用的经销商数据
          if (!dealerData) {
            const firstKey = Object.keys(response.dealer_scores)[0]
            if (firstKey) {
              dealerData = response.dealer_scores[firstKey]
            }
          }
          
          // 如果dealer_scores直接包含五力数据（不是嵌套结构）
          if (!dealerData && response.dealer_scores['传播获客力'] !== undefined) {
            dealerData = response.dealer_scores
          }
          
          
          // 从后端数据中提取当前经销商和月份的五力数据
          if (dealerData) {            
            // 转换数据结构，提取五个维度的得分
            const newFiveForcesData = {}
            
            // 尝试直接使用维度名称作为字段名
            const dimensions = ['传播获客力', '体验力', '转化力', '服务力', '经营力', '综合得分']
            
            for (const dimension of dimensions) {
              // 首先尝试直接使用维度名称
              if (dealerData[dimension] !== undefined && dealerData[dimension] !== null) {
                newFiveForcesData[dimension] = dealerData[dimension]
              } 
              // 然后尝试带月份的字段名
              else {
                const possibleFields = [
                  `${monthStr}${dimension}`,
                  `${month}月${dimension}`,
                  `${dimension}${monthStr}`,
                  `${dimension}${month}月`
                ]
                
                let foundValue = null
                for (const field of possibleFields) {
                  if (dealerData[field] !== undefined && dealerData[field] !== null) {
                    foundValue = dealerData[field]
                    break
                  }
                }
                if (foundValue !== null) {
                  newFiveForcesData[dimension] = foundValue
                }
              }
            }
            
            // 直接更新数据，确保响应式
            this.fiveForcesData = { ...newFiveForcesData }
          } else {
            this.fiveForcesData = {}
          }
          
          // 更新雷达图
          this.updateRadarChart()
        }

        
        this.updateSalesChart()
        
        // 保存预测结果到历史记录
        try {
          await this.savePredictionToHistory()
        } catch (error) {
          console.error('保存预测历史记录失败:', error)
          this.errorMessage = '预测成功，但保存历史记录失败，请稍后重试'
        }
      } catch (error) {
        this.backendAvailable = false // 标记后端不可用
        // 尝试从错误响应中提取后端错误信息
        console.log(error)
        if (error.response && error.response.data && error.response.data.message) {
          this.errorMessage = error.response.data.message
        } else {
          this.errorMessage = error.message 
        }
        
        // 保存错误信息，因为fetchOriginalSalesData会清空它
        const savedErrorMessage = this.errorMessage
        
        // 预测失败时清空所有相关数据，确保不显示之前的数据
        this.predictionResult = null
        this.fiveForcesData = {}
        
        // 重新获取原始销量数据，确保只显示原始销量，不显示预测数据
        await this.fetchOriginalSalesData()
        
        // 恢复错误信息
        this.errorMessage = savedErrorMessage
        
        // 更新雷达图，确保不显示之前的数据
        this.updateRadarChart()
        // 更新销量图表，确保不显示之前的数据
        this.updateSalesChart()

      } finally {
        this.loading = false;
      }
    },
    
    // 保存预测结果到历史记录
    async savePredictionToHistory() {
      try {
        console.log('保存历史记录前的fiveForcesData:', this.fiveForcesData)
        
        const propagationForce = this.fiveForcesData['传播获客力'] !== undefined ? this.fiveForcesData['传播获客力'] : 0
        const experienceForce = this.fiveForcesData['体验力'] !== undefined ? this.fiveForcesData['体验力'] : 0
        const conversionForce = this.fiveForcesData['转化力'] !== undefined ? this.fiveForcesData['转化力'] : 0
        const serviceForce = this.fiveForcesData['服务力'] !== undefined ? this.fiveForcesData['服务力'] : 0
        const operationForce = this.fiveForcesData['经营力'] !== undefined ? this.fiveForcesData['经营力'] : 0
        const comprehensiveScore = this.fiveForcesData['综合得分'] !== undefined ? this.fiveForcesData['综合得分'] : 0
        
        const historyData = {
          dealer_code: this.formData.dealer_code,
          dimension: this.formData.dimension,
          change_percentage: this.formData.change_percentage,
          base_year: this.formData.base_year,
          base_month: this.formData.base_month,
          target_year: this.predictionResult ? this.predictionResult.target_year : this.formData.base_year,
          target_month: this.predictionResult ? this.predictionResult.target_month : this.formData.base_month + 1,
          predicted_sales: this.predictionResult ? Math.round(this.predictionResult.predicted_sales) : null,
          month_for_radar: this.formData.month_for_radar,
          propagation_force: propagationForce,
          experience_force: experienceForce,
          conversion_force: conversionForce,
          service_force: serviceForce,
          operation_force: operationForce,
          comprehensive_score: comprehensiveScore
        }
        
        console.log('准备保存的历史记录数据:', historyData)
        const response = await savePredictionHistory(historyData)
        console.log('预测结果已保存到历史记录:', response)
        return response
      } catch (error) {
        console.error('保存历史记录失败:', error)
        throw error
      }
    },
    /**
     * 将后端返回的销量数组标准化为 1-10 月都存在的结构
     * - 若某个月后端没返回，则补一条 { month: x, original_sales: 0 }
     * - 若同时存在 original_sales / sales 字段，优先 original_sales
     */
    normalizeSalesChanges(rawList = []) {
      const monthMap = {}
      rawList.forEach(item => {
        const m = Number(item.month)
        if (!Number.isFinite(m)) return
        const value = item.original_sales != null ? item.original_sales : item.sales
        monthMap[m] = value != null ? value : 0
      })

      const fullList = []
      for (let m = 1; m <= 10; m++) {
        fullList.push({
          month: m,
          original_sales: monthMap[m] != null ? monthMap[m] : 0
        })
      }
      return fullList
    },
    updateRadarChart() {
      // 检查DOM元素是否存在
      const radarContainer = document.getElementById('radar-chart')
      if (!radarContainer) return
      
      // 准备雷达图数据
      const radarData = [
        {
          value: [
            this.fiveForcesData['传播获客力'] ? this.fiveForcesData['传播获客力'] : 0,
            this.fiveForcesData['体验力']  ? this.fiveForcesData['体验力'] : 0,
            this.fiveForcesData['转化力']  ? this.fiveForcesData['转化力'] : 0,
            this.fiveForcesData['服务力']  ? this.fiveForcesData['服务力'] : 0,
            this.fiveForcesData['经营力']  ? this.fiveForcesData['经营力'] : 0
          ],
          name: '经销商能力'
        }
      ]
      
      // 初始化echarts实例
      const myChart = echarts.init(radarContainer)
      
      // 配置雷达图选项
      const option = {
        backgroundColor: 'transparent',
        title: {
          text: '五力分析雷达图',
          textStyle: {
            fontSize: 14,
            fontWeight: 'normal',
            color: '#333'
          }
        },
        tooltip: {
          trigger: 'item'
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
            name: '能力评分',
            type: 'radar',
            data: radarData,
            areaStyle: {
              opacity: 0.3
            }
          }
        ]
      }
      
      // 应用配置
      myChart.setOption(option)
      
      // 移除旧的监听器（如果存在）
      if (this.resizeListener) {
        window.removeEventListener('resize', this.resizeListener)
      }
      
      // 保存事件监听器引用
      this.resizeListener = function() {
        myChart.resize()
      }
      
      // 添加新的监听器
      window.addEventListener('resize', this.resizeListener)
    },

    // 雷达图月份变化处理
    handleMonthChange() {
      // 当雷达图月份变化时，只同步预测月份，不自动请求后端
      this.formData.month = this.formData.month_for_radar
    },
    initSalesChart() {
      if (this.$refs.salesChart) {
        this.salesChart = echarts.init(this.$refs.salesChart);
        this.updateSalesChart();
      }
    },
    updateSalesChart() {
      if (!this.salesChart) return;
      
      const months = this.salesChanges.map(item => item.month + '月');
      const originalSales = this.salesChanges.map(item => item.original_sales);

      let predictionData = new Array(originalSales.length).fill(null);
      if (this.predictionResult && this.predictionResult.target_month) {
        const targetIndex = this.predictionResult.target_month - 1;
        if (targetIndex >= 0 && targetIndex < originalSales.length) {
          predictionData[targetIndex] = Math.round(this.predictionResult.predicted_sales);
        }
      }
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            let result = params[0].name + '<br/>';
            params.forEach(param => {
              if (param.value !== null) {
                result += param.marker + param.seriesName + ': ' + param.value + '<br/>';
              }
            });
            return result;
          }
        },
        legend: {
          data: ['原始销量', '预测销量'],
          right: 12,
          top: 10,
          orient: 'vertical',
          textStyle: { color: '#333' }
        },
        grid: { left: 50, right: 100, top: 40, bottom: 40 },
        xAxis: {
          type: 'category',
          data: months,
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          axisLabel: { color: '#666' }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#3fa9f5' } },
          splitLine: { lineStyle: { color: 'rgba(63,169,245,0.2)' } },
          axisLabel: { color: '#666' }
        },
        series: [
          {
            name: '原始销量',
            type: 'line',
            data: originalSales,
            smooth: true,
            symbol: 'circle',
            itemStyle: { color: '#5ad8ff' },
            lineStyle: { width: 2 },
            areaStyle: { color: 'rgba(90,216,255,0.15)' }
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
      };
      
      this.salesChart.setOption(option);
    }
  }
};
</script>

<style scoped>
.sales-prediction-container {
  width: 100%;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e8e8e8;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.history-btn {
  padding: 8px 16px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.history-btn:hover {
  background-color: #40a9ff;
}

.content-layout {
  display: flex;
  gap: 20px;
  width: 100%;
}

.left-section {
  width: 35%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-card {
  display: flex;
  flex-direction: column;
  min-height: 845px;
}

.form-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.form-content form {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

.form-content form .form-group:last-child {
  margin-bottom: auto;
}

.right-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-card,
.chart-card,
.radar-card,
.five-forces-card,
.formula-container {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.form-content {
  width: 100%;
}

.form-group {
  margin-bottom: 25px;
  text-align: left;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
  display: block;
}

select {
  width: 100%;
  padding: 8px;
  margin: 4px 0 10px 0;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
  font-size: 14px;
  box-sizing: border-box;
  background-color: #ffffff;
  color: #333;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg fill='%23666' height='16' viewBox='0 0 24 24' width='16' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/></svg>");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 16px 16px;
  padding-right: 30px;
}

select:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 5px rgba(24, 144, 255, 0.3);
}

.submit-btn,
.formula-btn {
  width: 100%;
  padding: 10px;
  margin: 10px 0;
  border-radius: 4px;
  border: 1px solid #1890ff;
  font-size: 14px;
  box-sizing: border-box;
  background-color: #1890ff;
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.submit-btn:hover,
.formula-btn:hover {
  background-color: #40a9ff;
  border-color: #40a9ff;
}

.submit-btn:disabled {
  background-color: #f0f0f0;
  border-color: #d9d9d9;
  color: #999;
  cursor: not-allowed;
}

.submit-btn {
  margin-top: 30px !important;
}

.formula-btn {
  margin-top: 0 !important;
}

.chart-content {
  width: 100%;
}

.sales-chart {
  width: 100%;
  height: 300px;
  margin-bottom: 20px;
}

.bottom-cards {
  display: flex;
  gap: 20px;
  margin-top: 20px;
}

.radar-card,
.five-forces-card {
  flex: 1;
}

.radar-content,
.five-forces-content {
  width: 100%;
}

.dealer-info {
  color: #666;
  margin-bottom: 10px;
  font-size: 14px;
  text-align: center;
}

.radar-chart {
  width: 100%;
  height: 300px;
}

.styled-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  font-family: Arial, sans-serif;
  margin: 15px 0;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  overflow: hidden;
}

.styled-table thead tr {
  background-color: #fafafa;
  color: #333;
  text-align: left;
}

.styled-table th,
.styled-table td {
  padding: 12px 15px;
  border: 1px solid #f0f0f0;
  color: #666;
}

.styled-table tbody tr {
  background-color: #ffffff;
}

.styled-table tbody tr:nth-of-type(even) {
  background-color: #f9f9f9;
}

.styled-table tfoot tr {
  background-color: #fafafa;
  color: #333;
  font-weight: 500;
}

.styled-table tfoot td {
  padding: 12px 15px;
  text-align: center;
}

.prediction-text {
  margin-top: 20px;
  padding: 15px;
  background-color: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 4px;
  text-align: center;
}

.prediction-text p {
  color: #389e0d;
  margin: 0;
  font-size: 16px;
}

.prediction-text .highlighted-value {
  background-color: #fff3cd;
  padding: 2px 4px;
  border-radius: 4px;
  color: #856404;
  font-weight: bold;
}

.error-message {
  margin-top: 20px;
  padding: 15px;
  background-color: #fff1f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  text-align: center;
}

.error-message p {
  color: #cf1322;
  margin: 0;
  font-size: 16px;
}

.error-message strong {
  color: #cf1322;
}

.prediction-details {
  margin-top: 20px;
  padding: 20px;
  background-color: #f0f7ff;
  border: 1px solid #adc6ff;
  border-radius: 4px;
  text-align: left;
}

.details-title {
  color: #1890ff;
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 15px 0;
  text-align: center;
}

.prediction-data-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.data-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background-color: #ffffff;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
}

.data-label {
  color: #666;
  font-size: 14px;
  font-weight: normal;
}

.data-value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.formula-container {
  margin-top: 20px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.formula-container ul {
  list-style-type: none;
  padding-left: 0;
  margin: 10px 0;
}

.formula-container li {
  font-size: 14px;
  color: #666;
  margin: 8px 0;
  line-height: 1.5;
  padding: 10px;
  background-color: #fafafa;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}

.formula-container li strong {
  color: #333;
  font-weight: 500;
}

/* 模态框样式 */
.modal-overlay {
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

.modal-content {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 80%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-title {
  font-size: 18px;
  font-weight: 500;
  color: #333;
  margin: 0;
}

.modal-close {
  font-size: 24px;
  color: #999;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.modal-close:hover {
  color: #333;
  background-color: #f0f0f0;
}

.modal-body {
  padding: 20px;
}

.modal-body ul {
  list-style-type: none;
  padding-left: 0;
  margin: 0;
}

.modal-body li {
  font-size: 14px;
  color: #666;
  margin: 10px 0;
  line-height: 1.5;
  padding: 10px;
  background-color: #fafafa;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}

.modal-body li strong {
  color: #333;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-layout {
    flex-direction: column;
  }
  
  .left-section,
  .right-section {
    width: 100%;
  }
  
  .bottom-cards {
    flex-direction: column;
  }
  
  .radar-card,
  .five-forces-card {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 18px;
  }
  
  .card-title {
    font-size: 14px;
  }
  
  .form-group label {
    font-size: 13px;
  }
  
  select {
    font-size: 13px;
  }
  
  .submit-btn,
  .formula-btn {
    font-size: 13px;
    padding: 8px;
  }
  
  .prediction-data-grid {
    grid-template-columns: 1fr;
  }
  
  .sales-chart,
  .radar-chart {
    height: 250px;
  }
  
  .modal-content {
    width: 90%;
    max-width: 90%;
  }
}
</style>