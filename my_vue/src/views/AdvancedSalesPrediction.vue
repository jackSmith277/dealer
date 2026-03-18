<template>
  <div class="advanced-prediction-container">
    <div class="content-layout">
      <div class="left-section">
        <div class="form-card">
          <h2 class="card-title">基准设置 (Baseline)</h2>
          <div class="form-content">
            <div class="form-group show-manual-input">
              <label for="dealer_code">经销商选择:</label>
              <DealerSelector 
                v-model="baseline.dealer_code" 
                :dealers="dealerList" 
                :showManualInput="true"
              />
            </div>

            <div class="form-group">
              <label for="base_month">基准月份:</label>
              <select id="base_month" name="base_month" v-model="baseline.base_month" required>
                <option v-for="month in 12" :key="month" :value="month">{{ month }}月</option>
              </select>
            </div>

            <div class="form-group">
              <label for="horizons">预测长度 (月):</label>
              <select id="horizons" name="horizons" v-model="baseline.horizons" required>
                <option value="3">短期 (1-3月)</option>
                <option value="6">中期 (3-6月)</option>
                <option value="12">远期 (6-12月)</option>
              </select>
            </div>

            <div class="form-group">
              <label for="interval_strategy">区间策略:</label>
              <select id="interval_strategy" name="interval_strategy" v-model="baseline.interval_strategy" required>
                <option value="80">80% (q10-q90)</option>
                <option value="90">90% (q05-q95)</option>
              </select>
            </div>
          </div>
        </div>

        <div class="form-card">
          <h2 class="card-title">情景设置 (Scenario)</h2>
          <div class="form-content">
            <div class="form-group">
              <label for="dimension">特征维度:</label>
              <select id="dimension" name="dimension" v-model="newScenario.dimension" required>
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
              <select id="change_percentage" name="change_percentage" v-model.number="newScenario.change_percentage" required>
                <option value="-50">-50%</option>
                <option value="-30">-30%</option>
                <option value="-20">-20%</option>
                <option value="-15">-15%</option>
                <option value="-10">-10%</option>
                <option value="-5">-5%</option>
                <option value="0">0%</option>
                <option value="5">+5%</option>
                <option value="10">+10%</option>
                <option value="15">+15%</option>
                <option value="20">+20%</option>
                <option value="30">+30%</option>
                <option value="50">+50%</option>
                <option value="100">+100%</option>
              </select>
            </div>

            <button type="button" class="add-scenario-btn" @click="addScenario">添加情景</button>

            <div class="scenario-list" v-if="scenarios.length > 0">
              <h3 class="scenario-list-title">已添加情景</h3>
              <div class="scenario-item" v-for="(scenario, index) in scenarios" :key="index">
                <div class="scenario-info">
                  <span class="scenario-name">{{ scenario.dimension }} {{ scenario.change_percentage > 0 ? '+' : '' }}{{ scenario.change_percentage }}%</span>
                </div>
                <div class="scenario-actions">
                  <button type="button" class="edit-btn" @click="editScenario(index)">编辑</button>
                  <button type="button" class="delete-btn" @click="deleteScenario(index)">删除</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="form-card">
          <div class="form-content">
            <div class="action-buttons">
              <button type="button" class="submit-btn" @click="runPrediction" :disabled="loading">
                {{ loading ? '预测中...' : '运行预测' }}
              </button>
              <button type="button" class="reset-btn" @click="resetForm" :disabled="loading">
                重置
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="right-section">
        <div class="chart-card">
          <h2 class="card-title">关键指标</h2>
          <div class="key-indicators">
            <div class="indicator-card">
              <div class="indicator-title">预测期间总销量</div>
              <div class="indicator-value">{{ totalPredictedSales }}</div>
            </div>
            <div class="indicator-card">
              <div class="indicator-title">与历史平均增长率</div>
              <div class="indicator-value">{{ growthRate }}%</div>
            </div>
            <div class="indicator-card">
              <div class="indicator-title">最大情景差异</div>
              <div class="indicator-value">{{ maxScenarioDifference }}%</div>
            </div>
            <div class="indicator-card">
              <div class="indicator-title">置信区间宽度</div>
              <div class="indicator-value">{{ confidenceIntervalWidth }}</div>
            </div>
          </div>
        </div>

        <div class="chart-card">
          <h2 class="card-title">销量预测趋势</h2>
          <div ref="mainChart" class="chart-container"></div>
        </div>

        <div class="chart-card">
          <h2 class="card-title">多情景对比</h2>
          <div ref="comparisonChart" class="chart-container"></div>
        </div>

        <div class="chart-card">
          <h2 class="card-title">预测数据</h2>
          <div class="data-table">
            <table>
              <thead>
                <tr>
                  <th>月份</th>
                  <th>基准情景 (q50)</th>
                  <th v-for="(scenario, index) in scenarios" :key="index">{{ scenario.dimension }} {{ scenario.change_percentage > 0 ? '+' : '' }}{{ scenario.change_percentage }}%</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(data, key) in predictionTableData" :key="key">
                  <td>{{ key }}</td>
                  <td>{{ data.baseline.q50 }}</td>
                  <td v-for="(scenario, index) in data.scenarios" :key="index">{{ scenario.q50 }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="chart-card" v-if="scenarioAnalysis.length > 0">
          <h2 class="card-title">情景分析</h2>
          <div class="scenario-analysis">
            <div class="analysis-item" v-for="(analysis, index) in scenarioAnalysis" :key="index">
              <div class="analysis-header">
                <span class="analysis-name">{{ scenarios[index].dimension }} {{ scenarios[index].change_percentage > 0 ? '+' : '' }}{{ scenarios[index].change_percentage }}%</span>
              </div>
              <div class="analysis-details">
                <div class="analysis-row">
                  <span class="analysis-label">与基准差异:</span>
                  <span class="analysis-value">{{ analysis.difference }}%</span>
                </div>
                <div class="analysis-row">
                  <span class="analysis-label">最大差异月份:</span>
                  <span class="analysis-value">{{ analysis.maxDifferenceMonth }}月</span>
                </div>
                <div class="analysis-row">
                  <span class="analysis-label">敏感性:</span>
                  <span class="analysis-value">{{ analysis.sensitivity }}</span>
                </div>
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
import DealerSelector from '@/components/DealerSelector.vue'
import dealerData from '@/assets/dealerData.json'
import { getQuantileForecast } from '@/api/prediction'

export default {
  name: 'AdvancedSalesPrediction',
  components: {
    DealerSelector
  },
  data() {
    return {
      baseline: {
        dealer_code: 'B440045',
        base_month: 1,
        horizons: 3,
        interval_strategy: 80
      },
      newScenario: {
        dimension: 'leads',
        change_percentage: 10
      },
      scenarios: [],
      dealerList: dealerData,
      predictionResults: [],
      predictionTableData: {},
      scenarioAnalysis: [],
      totalPredictedSales: 0,
      growthRate: 0,
      maxScenarioDifference: 0,
      confidenceIntervalWidth: 0,
      loading: false,
      errorMessage: '',
      mainChart: null,
      comparisonChart: null,
      resizeListener: null
    }
  },
  mounted() {
    this.loadMockData();
    this.resizeListener = window.addEventListener('resize', () => {
      if (this.mainChart) {
        this.mainChart.resize();
      }
      if (this.comparisonChart) {
        this.comparisonChart.resize();
      }
    });
  },
  beforeDestroy() {
    if (this.resizeListener) {
      window.removeEventListener('resize', this.resizeListener)
    }
    if (this.mainChart) {
      this.mainChart.dispose();
    }
    if (this.comparisonChart) {
      this.comparisonChart.dispose();
    }
  },
  methods: {
    loadMockData() {
      const horizons = parseInt(this.baseline.horizons);
      const baseSales = 150;
      
      const generateBaselineData = (months) => {
        const data = [];
        for (let i = 1; i <= months; i++) {
          const baseQ50 = Math.round(baseSales + (Math.random() * 20 - 10));
          
          let q05, q10, q25, q75, q90, q95;
          
          if (months <= 3) {
            const interval = baseQ50 * 0.1;
            q05 = Math.round(baseQ50 - interval * 1.5);
            q10 = Math.round(baseQ50 - interval);
            q25 = Math.round(baseQ50 - interval * 0.5);
            q75 = Math.round(baseQ50 + interval * 0.5);
            q90 = Math.round(baseQ50 + interval);
            q95 = Math.round(baseQ50 + interval * 1.5);
          } else if (months <= 6) {
            const interval = baseQ50 * 0.15;
            q05 = Math.round(baseQ50 - interval * 1.5);
            q10 = Math.round(baseQ50 - interval);
            q25 = Math.round(baseQ50 - interval * 0.5);
            q75 = Math.round(baseQ50 + interval * 0.5);
            q90 = Math.round(baseQ50 + interval);
            q95 = Math.round(baseQ50 + interval * 1.5);
          } else {
            const interval = baseQ50 * 0.25;
            q05 = Math.round(baseQ50 - interval * 1.5);
            q10 = Math.round(baseQ50 - interval);
            q25 = Math.round(baseQ50 - interval * 0.5);
            q75 = Math.round(baseQ50 + interval * 0.5);
            q90 = Math.round(baseQ50 + interval);
            q95 = Math.round(baseQ50 + interval * 1.5);
          }
          
          data.push({
            month: i,
            q50: baseQ50,
            q10: q10,
            q90: q90,
            q05: q05,
            q95: q95,
            q25: q25,
            q75: q75
          });
        }
        return data;
      };
      
      this.predictionResults = [
        {
          scenario: 'baseline',
          monthly: generateBaselineData(horizons)
        }
      ];
      this.processPredictionResults();
      this.updateMainChart();
      this.updateComparisonChart();
    },
    addScenario() {
      if (!this.newScenario.dimension || this.newScenario.change_percentage === undefined) {
        return;
      }
      this.scenarios.push({ ...this.newScenario });
      this.newScenario = {
        dimension: 'leads',
        change_percentage: 10
      };
    },
    editScenario(index) {
      this.newScenario = { ...this.scenarios[index] };
      this.scenarios.splice(index, 1);
    },
    deleteScenario(index) {
      this.scenarios.splice(index, 1);
    },
    async runPrediction() {
      try {
        this.errorMessage = '';
        this.loading = true;

        const horizons = parseInt(this.baseline.horizons);
        const horizonsArray = [];
        for (let i = 1; i <= horizons; i++) {
          horizonsArray.push(i);
        }

        const scenarios = [];
        scenarios.push({ name: 'baseline' });
        this.scenarios.forEach(s => {
          scenarios.push({
            name: `${s.dimension}${s.change_percentage > 0 ? '+' : ''}${s.change_percentage}%`,
            dimension: s.dimension,
            change_percentage: s.change_percentage
          });
        });

        const params = {
          dealer_code: this.baseline.dealer_code,
          base_year: 2024,
          base_month: this.baseline.base_month,
          horizons: horizonsArray,
          quantiles: [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95],
          calib_alpha: this.baseline.interval_strategy === 80 ? 0.2 : 0.1,
          scenarios: scenarios
        };

        console.log('分位数预测请求数据:', params);

        const response = await getQuantileForecast(params);
        console.log('分位数预测响应:', response);

        if (response && response.scenarios) {
          this.predictionResults = this.transformApiResponse(response);
          this.processPredictionResults();
          this.updateMainChart();
          this.updateComparisonChart();
        } else {
          this.errorMessage = '预测结果格式错误';
        }

      } catch (error) {
        console.error('预测失败:', error);
        if (error.response && error.response.data && error.response.data.message) {
          this.errorMessage = error.response.data.message;
        } else {
          this.errorMessage = error.message || '预测失败，请稍后重试';
        }
      } finally {
        this.loading = false;
      }
    },
    transformApiResponse(response) {
      const results = [];
      
      if (!response.scenarios) return results;
      
      for (const [scenarioName, scenarioData] of Object.entries(response.scenarios)) {
        const monthly = [];
        const horizons = scenarioData.horizons_requested || [];
        const months = scenarioData.months || [];
        const years = scenarioData.years || [];
        const point = scenarioData.point || [];
        const quantiles = scenarioData.quantiles || {};
        const meta = scenarioData.meta || {};
        
        const intervalName = meta.interval_name || 'calibrated_interval_80';
        const intervalData = scenarioData[intervalName];
        
        for (let i = 0; i < horizons.length; i++) {
          const monthData = {
            month: months[i] || (i + 1),
            year: years[i] || 2024,
            horizon: horizons[i],
            q50: point[i] || 0
          };
          
          if (quantiles['0.05']) monthData.q05 = quantiles['0.05'][i];
          if (quantiles['0.1']) monthData.q10 = quantiles['0.1'][i];
          if (quantiles['0.25']) monthData.q25 = quantiles['0.25'][i];
          if (quantiles['0.75']) monthData.q75 = quantiles['0.75'][i];
          if (quantiles['0.9']) monthData.q90 = quantiles['0.9'][i];
          if (quantiles['0.95']) monthData.q95 = quantiles['0.95'][i];
          
          if (intervalData) {
            monthData.interval80_lower = intervalData.lower[i];
            monthData.interval80_upper = intervalData.upper[i];
          }
          
          if (scenarioData.calibrated_interval_80) {
            monthData.interval80_lower = scenarioData.calibrated_interval_80.lower[i];
            monthData.interval80_upper = scenarioData.calibrated_interval_80.upper[i];
          }
          
          if (scenarioData.calibrated_interval_90) {
            monthData.interval90_lower = scenarioData.calibrated_interval_90.lower[i];
            monthData.interval90_upper = scenarioData.calibrated_interval_90.upper[i];
          }
          
          monthly.push(monthData);
        }
        
        results.push({
          scenario: scenarioName,
          monthly: monthly,
          hasInterval80: !!scenarioData.calibrated_interval_80 || intervalName === 'calibrated_interval_80',
          hasInterval90: !!scenarioData.calibrated_interval_90 || intervalName === 'calibrated_interval_90',
          intervalName: intervalName
        });
      }
      
      return results;
    },
    processPredictionResults() {
      this.predictionTableData = {};
      this.scenarioAnalysis = [];
      this.totalPredictedSales = 0;
      this.growthRate = 0;
      this.maxScenarioDifference = 0;
      this.confidenceIntervalWidth = 0;

      if (!this.predictionResults || this.predictionResults.length === 0) {
        return;
      }

      const baselineResult = this.predictionResults[0];
      if (baselineResult) {
        let totalSales = 0;
        baselineResult.monthly.forEach(item => {
          totalSales += item.q50;
          const key = `${item.year}-${item.month}`;
          if (!this.predictionTableData[key]) {
            this.predictionTableData[key] = {
              baseline: item,
              scenarios: []
            };
          }
        });
        this.totalPredictedSales = totalSales.toFixed(2);

        const firstMonth = baselineResult.monthly[0];
        if (firstMonth) {
          if (this.baseline.interval_strategy === 80 || firstMonth.interval80_lower) {
            const lower = firstMonth.interval80_lower || firstMonth.q10;
            const upper = firstMonth.interval80_upper || firstMonth.q90;
            this.confidenceIntervalWidth = (upper - lower).toFixed(2);
          } else {
            const lower = firstMonth.interval90_lower || firstMonth.q05;
            const upper = firstMonth.interval90_upper || firstMonth.q95;
            this.confidenceIntervalWidth = (upper - lower).toFixed(2);
          }
        }
      }

      for (let i = 1; i < this.predictionResults.length; i++) {
        const scenarioResult = this.predictionResults[i];
        if (scenarioResult) {
          let maxDifference = 0;
          let maxDifferenceMonth = 1;
          let totalDifference = 0;

          scenarioResult.monthly.forEach(item => {
            const key = `${item.year}-${item.month}`;
            if (this.predictionTableData[key]) {
              this.predictionTableData[key].scenarios.push(item);
              
              const baselineValue = this.predictionTableData[key].baseline.q50;
              const difference = ((item.q50 - baselineValue) / baselineValue * 100).toFixed(2);
              totalDifference += parseFloat(difference);
              
              if (Math.abs(parseFloat(difference)) > Math.abs(maxDifference)) {
                maxDifference = difference;
                maxDifferenceMonth = item.month;
              }
            }
          });

          const scenario = this.scenarios[i - 1];
          const sensitivity = scenario ? (Math.abs(totalDifference / scenario.change_percentage)).toFixed(2) : 0;

          this.scenarioAnalysis.push({
            difference: totalDifference.toFixed(2),
            maxDifferenceMonth: maxDifferenceMonth,
            sensitivity: sensitivity
          });

          if (Math.abs(parseFloat(maxDifference)) > Math.abs(this.maxScenarioDifference)) {
            this.maxScenarioDifference = maxDifference;
          }
        }
      }

      if (baselineResult && baselineResult.monthly.length > 1) {
        const firstValue = baselineResult.monthly[0].q50;
        const lastValue = baselineResult.monthly[baselineResult.monthly.length - 1].q50;
        if (firstValue > 0) {
          this.growthRate = ((lastValue - firstValue) / firstValue * 100).toFixed(2);
        } else {
          this.growthRate = 0;
        }
      }
    },
    updateMainChart() {
      if (!this.$refs.mainChart) return;

      this.mainChart = echarts.init(this.$refs.mainChart);

      const months = [];
      const baselineQ50 = [];
      const baselineInterval80Lower = [];
      const baselineInterval80Upper = [];
      const baselineInterval90Lower = [];
      const baselineInterval90Upper = [];
      const baselineQ25 = [];
      const baselineQ75 = [];
      const scenarioLines = [];

      if (this.predictionResults.length > 0) {
        const baselineResult = this.predictionResults[0];
        baselineResult.monthly.forEach(item => {
          months.push(`${item.year}/${item.month}`);
          baselineQ50.push(item.q50);
          baselineInterval80Lower.push(item.interval80_lower || item.q10);
          baselineInterval80Upper.push(item.interval80_upper || item.q90);
          baselineInterval90Lower.push(item.interval90_lower || item.q05);
          baselineInterval90Upper.push(item.interval90_upper || item.q95);
          baselineQ25.push(item.q25);
          baselineQ75.push(item.q75);
        });

        for (let i = 1; i < this.predictionResults.length; i++) {
          const scenarioResult = this.predictionResults[i];
          const scenarioData = [];
          scenarioResult.monthly.forEach(item => {
            scenarioData.push(item.q50);
          });
          scenarioLines.push({
            name: `${this.scenarios[i - 1].dimension} ${this.scenarios[i - 1].change_percentage > 0 ? '+' : ''}${this.scenarios[i - 1].change_percentage}%`,
            type: 'line',
            data: scenarioData,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 2
            }
          });
        }
      }

      const horizons = this.predictionResults.length > 0 ? this.predictionResults[0].monthly.length : parseInt(this.baseline.horizons);
      const intervalStrategy = parseInt(this.baseline.interval_strategy);
      const series = [
        {
          name: '基准情景',
          type: 'line',
          data: baselineQ50,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 2,
            color: '#1890ff'
          },
          itemStyle: {
            color: '#1890ff'
          }
        }
      ];

      if (horizons <= 3) {
        series.push(
          {
            name: '90%置信区间',
            type: 'custom',
            renderItem: function(params, api) {
              const points = [];
              for (let i = 0; i < params.dataIndex; i++) {
                points.push(api.coord([api.value(0, i), api.value(1, i)]));
              }
              for (let i = params.dataIndex; i >= 0; i--) {
                points.push(api.coord([api.value(0, i), api.value(2, i)]));
              }
              return {
                type: 'polygon',
                shape: {
                  points: points
                },
                style: {
                  fill: 'rgba(82, 196, 26, 0.15)'
                }
              };
            },
            data: months.map((month, index) => [index, baselineInterval90Upper[index], baselineInterval90Lower[index]])
          },
          {
            name: '80%置信区间',
            type: 'custom',
            renderItem: function(params, api) {
              const points = [];
              for (let i = 0; i < params.dataIndex; i++) {
                points.push(api.coord([api.value(0, i), api.value(1, i)]));
              }
              for (let i = params.dataIndex; i >= 0; i--) {
                points.push(api.coord([api.value(0, i), api.value(2, i)]));
              }
              return {
                type: 'polygon',
                shape: {
                  points: points
                },
                style: {
                  fill: 'rgba(24, 144, 255, 0.25)'
                }
              };
            },
            data: months.map((month, index) => [index, baselineInterval80Upper[index], baselineInterval80Lower[index]])
          },
          {
            name: '50%置信区间',
            type: 'custom',
            renderItem: function(params, api) {
              const points = [];
              for (let i = 0; i < params.dataIndex; i++) {
                points.push(api.coord([api.value(0, i), api.value(1, i)]));
              }
              for (let i = params.dataIndex; i >= 0; i--) {
                points.push(api.coord([api.value(0, i), api.value(2, i)]));
              }
              return {
                type: 'polygon',
                shape: {
                  points: points
                },
                style: {
                  fill: 'rgba(250, 173, 20, 0.35)'
                }
              };
            },
            data: months.map((month, index) => [index, baselineQ75[index], baselineQ25[index]])
          }
        );
      } else if (horizons <= 6) {
        series.push(
          {
            name: '80%置信区间',
            type: 'custom',
            renderItem: function(params, api) {
              const points = [];
              for (let i = 0; i < params.dataIndex; i++) {
                points.push(api.coord([api.value(0, i), api.value(1, i)]));
              }
              for (let i = params.dataIndex; i >= 0; i--) {
                points.push(api.coord([api.value(0, i), api.value(2, i)]));
              }
              return {
                type: 'polygon',
                shape: {
                  points: points
                },
                style: {
                  fill: 'rgba(24, 144, 255, 0.2)'
                }
              };
            },
            data: months.map((month, index) => [index, baselineInterval80Upper[index], baselineInterval80Lower[index]])
          }
        );
      } else {
        series.push(
          {
            name: '80%置信区间',
            type: 'custom',
            renderItem: function(params, api) {
              const points = [];
              for (let i = 0; i < params.dataIndex; i++) {
                points.push(api.coord([api.value(0, i), api.value(1, i)]));
              }
              for (let i = params.dataIndex; i >= 0; i--) {
                points.push(api.coord([api.value(0, i), api.value(2, i)]));
              }
              return {
                type: 'polygon',
                shape: {
                  points: points
                },
                style: {
                  fill: 'rgba(24, 144, 255, 0.2)'
                }
              };
            },
            data: months.map((month, index) => [index, baselineInterval80Upper[index], baselineInterval80Lower[index]])
          }
        );
      }

      // 添加情景线
      series.push(...scenarioLines);

      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['基准情景', ...(horizons <= 3 ? ['90%置信区间', '80%置信区间', '50%置信区间'] : ['80%置信区间']), ...this.scenarios.map(s => `${s.dimension} ${s.change_percentage > 0 ? '+' : ''}${s.change_percentage}%`)],
          top: 10
        },
        grid: {
          left: 50,
          right: 50,
          top: 50,
          bottom: 50
        },
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
        series: series
      };

      this.mainChart.setOption(option);
    },
    updateComparisonChart() {
      if (!this.$refs.comparisonChart) return;

      this.comparisonChart = echarts.init(this.$refs.comparisonChart);

      const months = [];
      const series = [];

      if (this.predictionResults.length > 0) {
        const baselineResult = this.predictionResults[0];
        baselineResult.monthly.forEach(item => {
          months.push(item.month + '月');
        });

        // 添加基准情景
        const baselineData = [];
        baselineResult.monthly.forEach(item => {
          baselineData.push(item.q50);
        });
        series.push({
          name: '基准情景',
          type: 'line',
          data: baselineData,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 2,
            color: '#1890ff'
          },
          itemStyle: {
            color: '#1890ff'
          }
        });

        // 添加其他情景
        for (let i = 1; i < this.predictionResults.length; i++) {
          const scenarioResult = this.predictionResults[i];
          const scenarioData = [];
          scenarioResult.monthly.forEach(item => {
            scenarioData.push(item.q50);
          });
          series.push({
            name: `${this.scenarios[i - 1].dimension} ${this.scenarios[i - 1].change_percentage > 0 ? '+' : ''}${this.scenarios[i - 1].change_percentage}%`,
            type: 'line',
            data: scenarioData,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 2
            }
          });
        }
      }

      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['基准情景', ...this.scenarios.map(s => `${s.dimension} ${s.change_percentage > 0 ? '+' : ''}${s.change_percentage}%`)],
          top: 10
        },
        grid: {
          left: 50,
          right: 50,
          top: 50,
          bottom: 50
        },
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
        series: series
      };

      this.comparisonChart.setOption(option);
    },
    resetForm() {
      this.baseline = {
        dealer_code: 'B440045',
        base_month: 1,
        horizons: 3,
        interval_strategy: 80
      };

      this.newScenario = {
        dimension: 'leads',
        change_percentage: 10
      };

      this.scenarios = [];

      this.predictionResults = [];
      this.predictionTableData = {};
      this.scenarioAnalysis = [];
      this.totalPredictedSales = 0;
      this.growthRate = 0;
      this.maxScenarioDifference = 0;
      this.confidenceIntervalWidth = 0;
      this.errorMessage = '';

      if (this.mainChart) {
        this.mainChart.dispose();
        this.mainChart = null;
      }
      if (this.comparisonChart) {
        this.comparisonChart.dispose();
        this.comparisonChart = null;
      }
    },
    goToHistory() {
      this.$router.push('/dashboard/history')
    },
    exportData() {
      console.log('导出数据');
    }
  }
};
</script>

<style scoped>
.advanced-prediction-container {
  width: 100%;
  overflow: hidden;
}

.content-layout {
  display: flex;
  gap: 20px;
  padding: 20px;
  height: calc(100vh - 80px);
  overflow: hidden;
}

.left-section {
  flex: 0 0 400px;
  overflow-y: auto;
  padding-right: 10px;
}

.right-section {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
  padding: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.form-group input,
.form-group select {
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.3s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.help-text {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.add-scenario-btn {
  padding: 10px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.add-scenario-btn:hover {
  background-color: #40a9ff;
}

.scenario-list {
  margin-top: 16px;
}

.scenario-list-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #333;
}

.scenario-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 8px;
}

.scenario-name {
  font-size: 14px;
  color: #333;
}

.scenario-actions {
  display: flex;
  gap: 8px;
}

.edit-btn,
.delete-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.edit-btn {
  background-color: #52c41a;
  color: white;
}

.edit-btn:hover {
  background-color: #73d13d;
}

.delete-btn {
  background-color: #ff4d4f;
  color: white;
}

.delete-btn:hover {
  background-color: #ff7875;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.submit-btn,
.reset-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.submit-btn {
  flex: 1;
  background-color: #1890ff;
  color: white;
}

.submit-btn:hover {
  background-color: #40a9ff;
}

.submit-btn:disabled {
  background-color: #d9d9d9;
  cursor: not-allowed;
}

.reset-btn {
  flex: 1;
  background-color: #f0f0f0;
  color: #333;
}

.reset-btn:hover {
  background-color: #e0e0e0;
}

.reset-btn:disabled {
  background-color: #f0f0f0;
  cursor: not-allowed;
}

.chart-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 20px;
}

.chart-container {
  width: 100%;
  height: 400px;
  margin-top: 16px;
}

.key-indicators {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.indicator-card {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.indicator-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.indicator-value {
  font-size: 20px;
  font-weight: 600;
  color: #1890ff;
}

.data-table {
  margin-top: 16px;
  overflow-x: auto;
}

.data-table table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
}

.data-table th {
  background-color: #f9f9f9;
  font-weight: 600;
  color: #333;
}

.scenario-analysis {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.analysis-item {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
}

.analysis-header {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.analysis-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.analysis-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.analysis-label {
  font-size: 14px;
  color: #666;
}

.analysis-value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.error-message {
  color: #ff4d4f;
  font-size: 14px;
  margin-top: 12px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-layout {
    flex-direction: column;
    height: auto;
  }
  
  .left-section {
    flex: 1;
    max-width: 100%;
  }
  
  .right-section {
    flex: 1;
  }
}
</style>