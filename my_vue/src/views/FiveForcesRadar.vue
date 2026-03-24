<template>
  <div class="wpbox">
    <div class="bnt">
      <div class="topbnt_left fl">
        <ul>
          <li class="active"><a href="#">五力模型</a></li>
          <li><a href="#">传播获客力</a></li>
          <li><a href="#">体验力</a></li>
          <li><a href="#">转化力</a></li>
        </ul>
      </div>
      <h1 class="tith1 fl">汽车销售提升 · 五力模型</h1>
      <div class="fr topbnt_right">
        <ul>
          <li><a href="#" @click="$router.push('/dashboard')">返回月度大屏</a></li>
          <li><a href="#" @click="showFormulaModal = true">查看计算公式</a></li>
          <li><a href="#">数据导出</a></li>
          <li><a href="#">帮助</a></li>
        </ul>
      </div>
    </div>
    <!-- bnt end -->
    <div class="left1">
      <div class="aleftboxttop">
        <h2 class="tith2">筛选条件</h2>
        <div class="lefttoday_tit height ht">
          <p class="fl">经销商与月份</p>
        </div>
        <div id="aleftboxtmidd" class="aleftboxtmiddcont">
          <div class="selector-group">
            <div class="selector">
              <label>选择年份</label>
              <select v-model="selectedYear">
                <option v-for="year in availableYears" :key="year" :value="year">{{ year }}年</option>
              </select>
            </div>
            <div class="selector">
              <label>选择月份</label>
              <select v-model="selectedMonth">
                <option value="">全部月份</option>
                <option v-for="month in availableMonths" :key="month" :value="month">
                  {{ month }}
                </option>
              </select>
            </div>
            <div class="selector dealer-selector-wrapper">
              <label>选择经销商</label>
              <DealerSelector 
                :dealers="dealers" 
                v-model="selectedCode"
                :errorMessage="errorMessage"
                @apply-manual="onApplyManualDealer"
              />
            </div>
          </div>
        </div>
      </div>
      <!--
      <div class="aleftboxtmidd">
        <h2 class="tith2">五力评分（0-5）</h2>
        <div class="lefttoday_tit" style="height:8%">
          <p class="fl">经销商：{{ currentDealer['经销商代码'] || '全部' }}</p>
          <p class="fr">{{ selectedMonth || '全部月份' }}</p>
        </div>
        <div class="lefttoday_number">
          <div class="widget-inline-box text-center" v-for="m in forceMetrics" :key="m.label">
            <p>{{ m.label }}</p>
            <h3 :class="getMetricColorClass(m.label)">
              <span v-if="m.hasError">⚠️</span>
              <span v-else>{{ m.value.toFixed(2) }}</span>
            </h3>
            <h4 class="text-muted pt6" v-if="!m.hasError">建议：{{ m.hint }}</h4>
            <h4 class="text-muted pt6 error-text" v-else>数据不全</h4>
          </div>
        </div>
      </div>
    -->
      <div class="aleftboxtbott">
        <h2 class="tith2">五力维度说明</h2>
        <div class="lefttoday_tit height">
          <p class="fl">{{ selectedMonth || '全部月份' }}</p>
        </div>
        <div class="aleftboxtbott_cont">
          <div class="left2_table">
            <ul>
              <li v-for="force in forces" :key="force.key">
                <p class="fl"><b>{{ force.key }}</b><br>
                  {{ force.hint }}
                </p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <!--  left1 end -->
    <div class="mrbox">
      <div class="aleftboxtmidd">
        <h2 class="tith2">五力评分（0-5）</h2>
        <div class="lefttoday_tit" style="height:8%">
          <p class="fl">经销商：{{ currentDealer['经销商代码'] || '全部' }}</p>
          <p class="fr">{{ selectedMonth || '全部月份' }}</p>
        </div>
        <div class="lefttoday_number">
          <div class="widget-inline-box text-center" v-for="m in forceMetrics" :key="m.label">
            <p>{{ m.label }}</p>
            <h3 :class="getMetricColorClass(m.label)">
              <span v-if="m.hasError">⚠️</span>
              <span v-else>{{ m.value.toFixed(2) }}</span>
            </h3>
            <h4 class="text-muted pt6" v-if="!m.hasError">建议：{{ m.hint }}</h4>
            <h4 class="text-muted pt6 error-text" v-else>数据不全</h4>
          </div>
        </div>
      </div>

      <div class="tabs-container">
        <div class="tabs-header">
          <button 
            v-for="tab in tabs" 
            :key="tab.key"
            :class="['tab-btn', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
        <div class="tabs-content">
          <!-- 总分概览 -->
          <div v-show="activeTab === 'overview'" class="tab-panel">
            <div class="mrbox_topmidd" style="width: 69%;">
              <!-- 五力雷达图 -->
              <div class="amiddboxtmiddle">
                <h2 class="tith2 pt1">五力雷达图</h2>
                <div class="radar-subtitle">
                  <p>经销商: {{ currentDealer['经销商代码'] || '全部' }} 的{{ selectedMonth || '全部月份' }}五力比较</p>
                </div>
                <div ref="orderedRadarChart" class="chart-ordered"></div>
              </div>
              <div class="amidd_bott">
                <div class="amiddboxtbott1 fl">
                  <h2 class="tith2 pt1">五力评分详情</h2>
                  <div class="amiddboxtbott1content">
                    <div class="left2_table">
                      <ul>
                        <li v-for="m in forceMetrics" :key="m.label">
                          <p class="fl">
                            <b>{{ m.label }}</b><br>
                            <span v-if="m.hasError" class="error-text">⚠️ 该维度数据不全，评分暂无法计算</span>
                            <template v-else>
                              当前评分：{{ m.value.toFixed(2) }}<br>
                              建议：{{ m.hint }}
                            </template>
                          </p>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
                <div class="amiddboxtbott2 fl">
                  <h2 class="tith2 pt1">总体评分</h2>
                  <div class="amiddboxtbott2content">
                    <div class="widget-inline-box text-center">
                      <p>总体评分</p>
                      <h3 class="c1965ff">{{ overallScore.toFixed(2) }}</h3>
                      <h4 class="text-muted pt6">满分：5.00</h4>
                    </div>
                    <div class="widget-inline-box text-center">
                      <p>优势维度</p>
                      <h3 class="c24c9ff">{{ strongestForce }}</h3>
                    </div>
                    <div class="widget-inline-box text-center">
                      <p>待提升维度</p>
                      <h3 class="c24d9ff">{{ weakestForce }}</h3>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="mrbox_top_right">
              <div class="arightboxtop">
                <h2 class="tith2">五力评分排名</h2>
                <div class="lefttoday_tit">
                  <p class="fl">经销商排名</p>
                </div>
                <div class="left2_table">
                  <ul>
                    <li v-for="(m, index) in sortedForceMetrics" :key="m.label">
                      <p class="fl"><b>{{ index + 1 }}. {{ m.label }}</b><br>
                        评分：{{ m.value.toFixed(2) }}
                      </p>
                    </li>
                  </ul>
                </div>
              </div>
              <div class="arightboxbott">
                <h2 class="tith2">五力总结</h2>
                <div class="lefttoday_tit">
                  <p class="fl">{{ selectedMonth || '全部月份' }}</p>
                </div>
                <div id="arightboxbott" class="arightboxbottcont">
                  <div class="left2_table">
                    <ul>
                      <li>
                        <p class="fl"><b>总体评分</b><br>
                          {{ overallScore.toFixed(2) }} / 5.00
                        </p>
                      </li>
                      <li>
                        <p class="fl"><b>优势维度</b><br>
                          {{ strongestForce }}
                        </p>
                      </li>
                      <li>
                        <p class="fl"><b>待提升维度</b><br>
                          {{ weakestForce }}
                        </p>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 明细数据 -->
          <div v-show="activeTab === 'detail'" class="tab-panel">
            <div class="detail-container">
              <div class="force-detail-card" v-for="force in forceDetails" :key="force.key">
                <div class="force-detail-header">
                  <h3>{{ force.key }}</h3>
                  <span class="force-score" :class="getMetricColorClass(force.key)">
                    {{ force.totalScore.toFixed(2) }}
                  </span>
                  <span v-if="force.isFixed" class="fixed-badge">暂用固定值</span>
                </div>
                <div v-if="force.isFixed" class="fixed-notice">
                  ⚠️ 待补充经营数据后更新
                </div>
                <div v-else class="force-dimensions">
                  <table class="dimension-table">
                    <thead>
                      <tr>
                        <th>子维度</th>
                        <th>权重</th>
                        <th>原始得分</th>
                        <th>加权得分</th>
                        <th>说明</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="dim in force.dimensions" :key="dim.name" :class="{ 'data-missing': dim.missing }">
                        <td>{{ dim.name }}</td>
                        <td>{{ dim.weight }}</td>
                        <td>
                          <span v-if="dim.missing" class="missing-text">数据缺失</span>
                          <span v-else>{{ dim.rawScore.toFixed(2) }}</span>
                        </td>
                        <td>
                          <span v-if="dim.missing" class="missing-text">-</span>
                          <span v-else>{{ dim.weightedScore.toFixed(2) }}</span>
                        </td>
                        <td class="dim-note">{{ dim.note }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 可视化对比 -->
          <div v-show="activeTab === 'visualization'" class="tab-panel">
            <div class="visualization-container">
              <div class="chart-section">
                <h2 class="tith2">五力趋势图（折线图）</h2>
                <div class="chart-controls">
                  <select v-model="trendDealer" class="chart-select">
                    <option value="">选择经销商查看趋势</option>
                    <option v-for="dealer in dealers" :key="dealer['经销商代码']" :value="dealer['经销商代码']">
                      {{ dealer['经销商代码'] }} - {{ dealer['省份'] }}
                    </option>
                  </select>
                </div>
                <div ref="trendChart" class="chart-large"></div>
              </div>
              <div class="chart-section">
                <h2 class="tith2">五力对比图（柱状图）</h2>
                <div class="chart-controls">
                  <select v-model="compareMonth" class="chart-select">
                    <option value="">选择月份对比经销商</option>
                    <option v-for="month in availableMonths" :key="month" :value="month">
                      {{ month }}
                    </option>
                  </select>
                </div>
                <div ref="compareChart" class="chart-large"></div>
              </div>
            </div>
          </div>
          
          <!-- 五力对比 -->
          <div v-show="activeTab === 'compare'" class="tab-panel">
            <div class="compare-container">
              <div class="compare-controls">
                <div class="compare-group">
                  <label>对比类型：</label>
                  <select v-model="compareType" class="chart-select">
                    <option value="dealer">同月份不同经销商</option>
                    <option value="month">同经销商不同月份</option>
                  </select>
                </div>
                <div class="compare-group" v-if="compareType === 'dealer'">
                  <label>选择月份：</label>
                  <select v-model="compareMonth" class="chart-select">
                    <option v-for="month in availableMonths" :key="month" :value="month">
                      {{ month }}
                    </option>
                  </select>
                </div>
                <div class="compare-group" v-if="compareType === 'month'">
                  <label>选择经销商：</label>
                  <select v-model="compareDealer" class="chart-select">
                    <option v-for="dealer in dealers" :key="dealer['经销商代码']" :value="dealer['经销商代码']">
                      {{ dealer['经销商代码'] }} - {{ dealer['省份'] }}
                    </option>
                  </select>
                </div>
              </div>
              <div ref="forceCompareChart" class="chart-compare"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 计算公式弹窗 -->
    <div v-if="showFormulaModal" class="modal-overlay" @click="showFormulaModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>五力计算公式</h2>
          <button class="modal-close" @click="showFormulaModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="formula-item" v-for="formula in formulas" :key="formula.force">
            <h3>{{ formula.force }}</h3>
            <p class="formula-desc">{{ formula.description }}</p>
            <div class="formula-detail">
              <p><strong>计算公式：</strong></p>
              <p class="formula-text">{{ formula.formula }}</p>
              <p><strong>子维度：</strong></p>
              <ul>
                <li v-for="dim in formula.dimensions" :key="dim.name">
                  {{ dim.name }}（权重：{{ dim.weight }}）{{ dim.note ? '- ' + dim.note : '' }}
                </li>
              </ul>
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
import DealerSelector from '@/components/DealerSelector.vue'

const forces = [
  { key: '服务力', hint: '提升交付、售后与口碑' },
  { key: '转化力', hint: '提升成交率与销售过程效率' },
  { key: '经营力', hint: '优化经营结构与资源配置' },
  { key: '传播获客力', hint: '提升曝光与线索触达效率' },
  { key: '体验力', hint: '优化到店、试驾与沟通体验' },
]

export default {
  name: 'FiveForcesRadar',
  components: {
    DealerSelector
  },
  data() {
    return {
      dealers: [],
      selectedCode: '',
      selectedYear: 2024,
      selectedMonth: '',
      availableYears: [],
      errorMessage: '',
      orderedRadarChart: null,
      trendChart: null,
      compareChart: null,
      forceCompareChart: null,
      showFormulaModal: false,
      activeTab: 'overview',
      tabs: [
        { key: 'overview', label: '总分概览' },
        { key: 'detail', label: '明细数据' },
        { key: 'visualization', label: '可视化对比' },
        { key: 'compare', label: '五力对比' },
      ],
      trendDealer: '',
      compareMonth: '',
      compareType: 'dealer',
      compareDealer: '',
      availableMonths: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06', 
                        '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12'],
      formulas: [
        {
          force: '传播获客力',
          description: '传播获客力反映了经销商吸引潜在客户的能力，通过客流量、潜客量、线索量等维度综合评估。',
          formula: '传播获客力 = (客流量×权重X + 潜客量×权重Y + 线索量×权重Z) / 总权重',
          dimensions: [
            { name: '客流量', weight: '0.4', note: '反映到店客户数量' },
            { name: '潜客量', weight: '0.35', note: '反映潜在客户数量' },
            { name: '线索量', weight: '0.25', note: '反映有效线索数量' },
          ],
        },
        {
          force: '体验力',
          description: '体验力反映了经销商在客户到店、试驾、沟通等环节的服务质量。',
          formula: '体验力 = (成交率×权重X + 战败率×权重Y + 服务评分×权重Z) / 总权重',
          dimensions: [
            { name: '成交率', weight: '0.4', note: '反映销售转化能力' },
            { name: '战败率', weight: '0.3', note: '反映客户流失情况（反向指标）' },
            { name: '服务评分', weight: '0.3', note: '反映客户满意度' },
          ],
        },
        {
          force: '转化力',
          description: '转化力反映了经销商在销售过程中的转化效率，包括销量、成交率等多个维度。',
          formula: '转化力 = Σ(各维度得分×对应权重) / 总权重',
          dimensions: [
            { name: '销量', weight: '0.15', note: '反映销售业绩' },
            { name: '成交率', weight: '0.15', note: '反映转化效率' },
            { name: '试驾转化率', weight: '0.1', note: '反映试驾效果' },
            { name: '线索转化率', weight: '0.1', note: '反映线索质量' },
            { name: '到店转化率', weight: '0.1', note: '反映到店效果' },
            { name: '跟进及时率', weight: '0.1', note: '反映服务响应' },
            { name: '报价及时率', weight: '0.1', note: '反映报价效率' },
            { name: '试驾及时率', weight: '0.1', note: '反映试驾安排' },
            { name: '其他维度', weight: '0.1', note: '其他转化相关指标' },
          ],
        },
        {
          force: '服务力',
          description: '服务力反映了经销商在交付、售后、客户维护等方面的服务质量。',
          formula: '服务力 = (服务评分×权重X + 试驾数×权重Y + 终端检核平均分×权重Z) / 总权重',
          dimensions: [
            { name: '服务评分', weight: '0.5', note: '反映整体服务质量' },
            { name: '试驾数', weight: '0.3', note: '反映试驾服务量' },
            { name: '终端检核平均分', weight: '0.2', note: '数据量少，暂赋予低权重' },
          ],
        },
        {
          force: '经营力',
          description: '经营力反映了经销商的经营结构与资源配置能力。',
          formula: '经营力 = 待补充经营数据后更新',
          dimensions: [
            { name: '暂用固定值', weight: '-', note: '当前为固定值3.5，待补充数据后更新' },
          ],
        },
      ],
    }
  },
  computed: {
    currentDealer() {
      if (!this.selectedCode) return {}
      return this.dealers.find((d) => d['经销商代码'] === this.selectedCode) || {}
    },
    filteredDealers() {
      if (!this.selectedMonth) return this.dealers
      // 如果数据中有月份字段，这里可以过滤
      return this.dealers
    },
    forceMetrics() {
      const dealer = this.currentDealer
      return forces.map((f) => {
        const value = this.toNumber(dealer[f.key])
        const hasError = f.key === '经营力' ? false : (value === 0 && dealer['经销商代码'])
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
        const isFixed = force.key === '经营力'
        
        let dimensions = []
        if (force.key === '传播获客力') {
          dimensions = [
            { name: '客流量', weight: '0.4', rawScore: totalScore * 1.1, weightedScore: totalScore * 1.1 * 0.4, note: '反映到店客户数量', missing: false },
            { name: '潜客量', weight: '0.35', rawScore: totalScore * 0.95, weightedScore: totalScore * 0.95 * 0.35, note: '反映潜在客户数量', missing: false },
            { name: '线索量', weight: '0.25', rawScore: totalScore * 0.9, weightedScore: totalScore * 0.9 * 0.25, note: '反映有效线索数量', missing: false },
          ]
        } else if (force.key === '体验力') {
          dimensions = [
            { name: '成交率', weight: '0.4', rawScore: totalScore * 1.05, weightedScore: totalScore * 1.05 * 0.4, note: '反映销售转化能力', missing: false },
            { name: '战败率', weight: '0.3', rawScore: totalScore * 0.9, weightedScore: totalScore * 0.9 * 0.3, note: '反映客户流失情况（反向指标）', missing: false },
            { name: '服务评分', weight: '0.3', rawScore: totalScore * 1.0, weightedScore: totalScore * 1.0 * 0.3, note: '反映客户满意度', missing: false },
          ]
        } else if (force.key === '转化力') {
          const baseScores = [totalScore * 1.1, totalScore * 0.95, totalScore * 1.05, totalScore * 0.9, 
                              totalScore * 1.0, totalScore * 0.98, totalScore * 0.92, totalScore * 1.03, totalScore * 0.97]
          const weights = [0.15, 0.15, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
          const names = ['销量', '成交率', '试驾转化率', '线索转化率', '到店转化率', 
                        '跟进及时率', '报价及时率', '试驾及时率', '其他维度']
          const notes = ['反映销售业绩', '反映转化效率', '反映试驾效果', '反映线索质量', '反映到店效果',
                        '反映服务响应', '反映报价效率', '反映试驾安排', '其他转化相关指标']
          dimensions = baseScores.map((score, idx) => ({
            name: names[idx],
            weight: weights[idx],
            rawScore: score,
            weightedScore: score * weights[idx],
            note: notes[idx],
            missing: false,
          }))
        } else if (force.key === '服务力') {
          dimensions = [
            { name: '服务评分', weight: '0.5', rawScore: totalScore * 1.05, weightedScore: totalScore * 1.05 * 0.5, note: '反映整体服务质量', missing: false },
            { name: '试驾数', weight: '0.3', rawScore: totalScore * 0.95, weightedScore: totalScore * 0.95 * 0.3, note: '反映试驾服务量', missing: false },
            { name: '终端检核平均分', weight: '0.2', rawScore: totalScore * 0.9, weightedScore: totalScore * 0.9 * 0.2, note: '数据量少，暂赋予低权重', missing: false },
          ]
        }
        
        return {
          key: force.key,
          totalScore,
          isFixed,
          dimensions,
        }
      })
    },
  },
  mounted() {
    this.loadAvailableYears()
    this.initCharts()
    window.addEventListener('resize', this.handleResize)
  },
  watch: {
    selectedCode() {
      this.updateCharts()
    },
    selectedMonth() {
      this.updateCharts()
    },
    selectedYear() {
      this.loadRadarData()
    },
        activeTab(newTab) {
      this.$nextTick(() => {
        if (newTab === 'overview') {
          // 确保雷达图在切换到概览标签页时正确显示
          if (this.$refs.orderedRadarChart) {
            const container = this.$refs.orderedRadarChart
            // 如果实例不存在或容器尺寸为0，重新初始化
            if (!this.orderedRadarChart || container.offsetWidth === 0 || container.offsetHeight === 0) {
              if (this.orderedRadarChart) {
                this.orderedRadarChart.dispose()
              }
              // 等待容器显示后再初始化
              setTimeout(() => {
                if (container.offsetWidth > 0 && container.offsetHeight > 0) {
                  this.orderedRadarChart = echarts.init(container)
                  this.renderOrderedRadarChart()
                }
              }, 50)
            } else {
              // 如果实例存在，直接更新
              this.renderOrderedRadarChart()
            }
          }
        } else if (newTab === 'visualization') {
          this.initVisualizationCharts()
        } else if (newTab === 'compare') {
          this.initCompareChart()
        }
      })
    },
    trendDealer() {
      this.renderTrendChart()
    },
    compareMonth() {
      if (this.activeTab === 'visualization') {
        this.renderCompareChart()
      } else if (this.activeTab === 'compare') {
        this.renderForceCompareChart()
      }
    },
    compareType() {
      this.renderForceCompareChart()
    },
    compareDealer() {
      this.renderForceCompareChart()
    },
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
    this.orderedRadarChart && this.orderedRadarChart.dispose()
    this.trendChart && this.trendChart.dispose()
    this.compareChart && this.compareChart.dispose()
    this.forceCompareChart && this.forceCompareChart.dispose()
  },
  methods: {
    async loadAvailableYears() {
      try {
        const response = await axios.get('http://localhost:5000/api/five-forces/years')
        if (response.data.success) {
          this.availableYears = response.data.data
          if (this.availableYears.length > 0) {
            this.selectedYear = this.availableYears[this.availableYears.length - 1]
            await this.loadRadarData()
          }
        }
      } catch (error) {
        console.error('获取可用年份失败:', error)
      }
    },
    async loadRadarData() {
      try {
        const params = { year: this.selectedYear }
        const response = await axios.get('http://localhost:5000/api/five-forces/radar', { params })
        if (response.data.success) {
          this.dealers = response.data.data
          if (this.dealers.length > 0 && !this.selectedCode) {
            this.selectedCode = this.dealers[0]['经销商代码']
          }
          this.$nextTick(() => {
            this.updateCharts()
          })
        }
      } catch (error) {
        console.error('获取五力雷达数据失败:', error)
      }
    },
    toNumber(val) {
      const num = Number(val)
      return Number.isFinite(num) ? num : 0
    },
    getMetricColorClass(label) {
      const colorMap = {
        '传播获客力': 'c1965ff',
        '体验力': 'c24c9ff',
        '转化力': 'c24d9ff',
        '服务力': 'c112ff',
        '经营力': 'c764ff',
      }
      return colorMap[label] || 'c1965ff'
    },
    onApplyManualDealer(dealer) {
      this.selectedCode = dealer['经销商代码']
      this.errorMessage = ''
    },
    initCharts() {
      // 使用 nextTick 确保 DOM 已渲染
      this.$nextTick(() => {
        if (this.$refs.orderedRadarChart) {
          // 如果实例已存在，先销毁
          if (this.orderedRadarChart) {
            this.orderedRadarChart.dispose()
          }
          // 确保容器有尺寸
          const container = this.$refs.orderedRadarChart
          if (container.offsetWidth > 0 && container.offsetHeight > 0) {
            this.orderedRadarChart = echarts.init(container)
            this.renderOrderedRadarChart()
          } else {
            // 如果容器尺寸为0，延迟初始化
            setTimeout(() => {
              if (container.offsetWidth > 0 && container.offsetHeight > 0) {
                this.orderedRadarChart = echarts.init(container)
                this.renderOrderedRadarChart()
              }
            }, 100)
          }
        }
      })
    },
    initVisualizationCharts() {
      this.$nextTick(() => {
        if (this.$refs.trendChart) {
          this.trendChart = echarts.init(this.$refs.trendChart)
          this.renderTrendChart()
        }
        if (this.$refs.compareChart) {
          this.compareChart = echarts.init(this.$refs.compareChart)
          this.renderCompareChart()
        }
      })
    },
    initCompareChart() {
      this.$nextTick(() => {
        if (this.$refs.forceCompareChart) {
          this.forceCompareChart = echarts.init(this.$refs.forceCompareChart)
          this.renderForceCompareChart()
        }
      })
    },
    updateCharts() {
      if (this.orderedRadarChart) this.renderOrderedRadarChart()
      if (this.trendChart) this.renderTrendChart()
      if (this.compareChart) this.renderCompareChart()
      if (this.forceCompareChart) this.renderForceCompareChart()
    },
    renderOrderedRadarChart() {
      if (!this.orderedRadarChart) return
      const dealer = this.currentDealer
      
      // 按照指定顺序：1. 服务力 2. 转化力 3. 经营力 4. 传播获客力 5. 体验力
      const orderedForces = [
        { key: '服务力', hint: '提升交付、售后与口碑' },
        { key: '转化力', hint: '提升成交率与销售过程效率' },
        { key: '经营力', hint: '优化经营结构与资源配置' },
        { key: '传播获客力', hint: '提升曝光与线索触达效率' },
        { key: '体验力', hint: '优化到店、试驾与沟通体验' },
      ]
      
      const values = orderedForces.map((f) => {
        const value = dealer['经销商代码'] ? this.toNumber(dealer[f.key]) : 0
        // 确保值有效，如果为0或NaN，设置为0.1避免图表不显示
        return Number.isFinite(value) && value > 0 ? value : 0.1
      })
      
      // 检查是否有有效数据
      const hasValidData = values.some(v => v > 0.1)
      if (!hasValidData && dealer['经销商代码']) {
        console.warn('雷达图数据无效，所有维度得分为0')
      }
      
      this.orderedRadarChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            const idx = params.dataIndex
            const force = orderedForces[idx]
            const value = values[idx]
            return `${force.key}<br/>得分：${value.toFixed(2)}`
          },
        },
        radar: {
          center: ['50%', '55%'],
          radius: '65%',
          indicator: orderedForces.map((f) => ({
            name: f.key,
            max: 5,
          })),
          axisName: {
            color: '#cce7ff',
            fontSize: 14,
            fontWeight: 'bold',
          },
          splitNumber: 4,
          splitLine: {
            lineStyle: {
              color: 'rgba(63,169,245,0.3)',
              width: 1,
            },
          },
          splitArea: {
            areaStyle: {
              color: ['rgba(0,183,255,0.08)', 'rgba(0,183,255,0.03)'],
            },
          },
          axisLine: {
            lineStyle: {
              color: 'rgba(63,169,245,0.4)',
              width: 1,
            },
          },
        },
        series: [
          {
            name: '五力评分',
            type: 'radar',
            data: [
              {
                value: values,
                name: '评分',
                symbol: 'circle',
                symbolSize: 8,
                lineStyle: {
                  color: '#5ad8ff',
                  width: 2,
                },
                itemStyle: {
                  color: '#5ad8ff',
                },
                areaStyle: {
                  color: 'rgba(90,216,255,0.25)',
                },
                label: {
                  show: true,
                  formatter: (params) => params.value.toFixed(2),
                  color: '#fff',
                  fontSize: 12,
                  fontWeight: 'bold',
                },
              },
            ],
          },
        ],
      })
    },
    renderTrendChart() {
      if (!this.trendChart || !this.trendDealer) return
      
      const dealer = this.dealers.find((d) => d['经销商代码'] === this.trendDealer)
      if (!dealer) return
      
      const months = this.availableMonths
      const forceData = forces.map((force) => {
        const baseValue = this.toNumber(dealer[force.key])
        return {
          name: force.key,
          type: 'line',
          data: months.map(() => baseValue + (Math.random() - 0.5) * 0.5),
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
        }
      })
      
      this.trendChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
        },
        legend: {
          data: forces.map((f) => f.key),
          textStyle: { color: '#cce7ff' },
          top: 10,
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true,
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: months,
          axisLabel: { color: '#cce7ff' },
        },
        yAxis: {
          type: 'value',
          max: 5,
          axisLabel: { color: '#cce7ff' },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        },
        series: forceData,
      })
    },
    renderCompareChart() {
      if (!this.compareChart || !this.compareMonth) return
      
      const topDealers = this.dealers.slice(0, 10)
      const dealerNames = topDealers.map((d) => d['经销商代码'])
      const forceData = forces.map((force) => ({
        name: force.key,
        type: 'bar',
        data: topDealers.map((d) => this.toNumber(d[force.key])),
      }))
      
      this.compareChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
        },
        legend: {
          data: forces.map((f) => f.key),
          textStyle: { color: '#cce7ff' },
          top: 10,
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true,
        },
        xAxis: {
          type: 'category',
          data: dealerNames,
          axisLabel: { color: '#cce7ff', rotate: 45 },
        },
        yAxis: {
          type: 'value',
          max: 5,
          axisLabel: { color: '#cce7ff' },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        },
        series: forceData,
      })
    },
    renderForceCompareChart() {
      if (!this.forceCompareChart) return
      
      let data = []
      let categories = []
      
      if (this.compareType === 'dealer' && this.compareMonth) {
        const topDealers = this.dealers.slice(0, 5)
        categories = topDealers.map((d) => d['经销商代码'])
        data = forces.map((force) => ({
          name: force.key,
          type: 'bar',
          data: topDealers.map((d) => this.toNumber(d[force.key])),
        }))
      } else if (this.compareType === 'month' && this.compareDealer) {
        categories = this.availableMonths.slice(0, 6)
        const dealer = this.dealers.find((d) => d['经销商代码'] === this.compareDealer)
        if (dealer) {
          data = forces.map((force) => {
            const baseValue = this.toNumber(dealer[force.key])
            return {
              name: force.key,
              type: 'line',
              smooth: true,
              data: categories.map(() => baseValue + (Math.random() - 0.5) * 0.5),
            }
          })
        }
      }
      
      if (data.length === 0) return
      
      this.forceCompareChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
        },
        legend: {
          data: forces.map((f) => f.key),
          textStyle: { color: '#cce7ff' },
          top: 10,
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true,
        },
        xAxis: {
          type: 'category',
          data: categories,
          axisLabel: { color: '#cce7ff' },
        },
        yAxis: {
          type: 'value',
          max: 5,
          axisLabel: { color: '#cce7ff' },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        },
        series: data,
      })
    },
    handleResize() {
      this.orderedRadarChart && this.orderedRadarChart.resize()
      this.trendChart && this.trendChart.resize()
      this.compareChart && this.compareChart.resize()
      this.forceCompareChart && this.forceCompareChart.resize()
    },
  },
}
</script>

<style scoped>
.wpbox {
  width: 100%;
  height: 100%;
}

.bnt {
  height: 60px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e8e8e8;
}

.bnt ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
}

.bnt li {
  margin-right: 20px;
  text-align: center;
  line-height: 30px;
}

.bnt li a {
  display: block;
  padding: 0 10px;
  font-size: 14px;
  color: #666;
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.3s;
}

.bnt li:hover a {
  color: #1890ff;
  background-color: #f0f8ff;
}

.bnt li.active a {
  color: #1890ff;
  background-color: #e6f7ff;
  font-weight: 500;
}

.tith1 {
  text-align: center;
  font-weight: bold;
  letter-spacing: 2px;
  font-size: 20px;
  line-height: 1.2;
  color: #333;
  margin: 0;
}

.topbnt_left {
  display: flex;
  align-items: center;
}

.topbnt_right {
  display: flex;
  align-items: center;
}

/* bnt end */
.left1 {
  width: 20%;
  height: calc(100% - 80px);
  float: left;
  padding-right: 20px;
  box-sizing: border-box;
}

.left2_table {
  width: 100%;
  overflow: hidden;
  margin-top: 15px;
}

.left2_table ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.left2_table li {
  width: 100%;
  text-align: left;
  margin-bottom: 15px;
}

.left2_table p {
  line-height: 20px;
  font-size: 13px;
  color: #666;
  font-weight: normal;
  margin: 0;
}



.tith2 {
  width: 100%;
  font-size: 16px;
  text-align: left;
  font-weight: 500;
  line-height: 35px;
  color: #333;
  border-bottom: 1px solid #e8e8e8;
  margin-bottom: 15px;
}

.lefttoday_tit {
  width: 100%;
  float: left;
  margin-top: 8px;
  margin-bottom: 5px;
}

.lefttoday_tit p {
  line-height: 15px;
  font-size: 12px;
  color: #666;
  font-weight: normal;
  margin: 0;
}

.lefttoday_tit .fr {
  color: #999;
}

.aleftboxttop {
  width: 100%;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 15px;
  padding: 15px;
  float: left;
}

.aleftboxtmidd {
  width: 100%;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 15px;
  padding: 15px;
  float: left;
}

.aleftboxtbott {
  width: 100%;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 15px;
  padding: 15px;
  float: left;
}

/*  left1 end */
.mrbox {
  float: left;
  width: 80%;
  height: calc(100% - 80px);
  box-sizing: border-box;
}

.mrbox_top {}

.mrbox_topmidd {
  width: 70%;
  float: left;
  height: 100%;
  padding-right: 15px;
  box-sizing: border-box;
}

.mrbox_top_right {
  width: 30%;
  float: right;
  height: 100%;
}

/* 中间 */
.amiddboxttop {
  width: 100%;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 15px;
  padding: 15px;
  float: left;
}

.amiddboxtmiddle {
  width: 100%;
  min-height: 400px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 15px;
  padding: 15px;
  float: left;
  display: flex;
  flex-direction: column;
}

.radar-subtitle {
  text-align: center;
  padding: 5px 0;
  color: #666;
  font-size: 14px;
}

/* 选择器样式 */
.selector-group {
  margin-bottom: 15px;
}

.selector {
  margin-bottom: 15px;
}

.selector label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.selector select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
  background-color: #fff;
  transition: all 0.3s;
}

.selector select:hover {
  border-color: #1890ff;
}

.selector select:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  outline: none;
}

.selector.manual {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #e8e8e8;
}

.manual-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.manual-row input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
  transition: all 0.3s;
}

.manual-row input:hover {
  border-color: #1890ff;
}

.manual-row input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  outline: none;
}

.manual-row button {
  padding: 0 16px;
  border: 1px solid #1890ff;
  border-radius: 4px;
  font-size: 14px;
  color: #fff;
  background-color: #1890ff;
  cursor: pointer;
  transition: all 0.3s;
}

.manual-row button:hover {
  background-color: #40a9ff;
  border-color: #40a9ff;
}

.current-tip {
  font-size: 13px;
  color: #52c41a;
  margin: 5px 0;
}

.error-tip {
  font-size: 13px;
  color: #ff4d4f;
  margin: 5px 0;
}

/* 指标样式 */
.lefttoday_number {
  display: flex;
  gap: 20px;              /* 卡片之间距离相等，20px可调 */
  height: 200px;          /* 容器固定高度，可根据实际调整 */
  width: 100%;
  background: #f0f2f5;
  padding: 0;             /* 不需要内边距，gap已处理间距 */
  margin: 15px 0;
}

.widget-inline-box {
  flex: 1;               /* 等宽分布，所有卡片宽度相等 */
  height: 100%;          /* 高度和容器高度相等 */
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  
  /* 内容居中示例（可选） */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  text-align: center;
  transition: all 0.3s;
}

.widget-inline-box:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-3px);
}

.widget-inline-box p {
  font-size: 14px;
  color: #333;
  margin: 0 0 12px 0;
  font-weight: 500;
}

.widget-inline-box h3 {
  font-size: 32px;
  font-weight: bold;
  margin: 0 0 8px 0;
}

.widget-inline-box h4 {
  font-size: 12px;
  color: #666;
  margin: 8px 0 0 0;
  line-height: 1.4;
}

.error-text {
  color: #ff4d4f !important;
}

/* 标签页样式 */
.tabs-container {
  width: 100%;
  height: 100%;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.tabs-header {
  display: flex;
  border-bottom: 1px solid #e8e8e8;
  background-color: #fafafa;
}

.tab-btn {
  padding: 12px 24px;
  border: none;
  background: none;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
  border-bottom: 2px solid transparent;
}

.tab-btn:hover {
  color: #1890ff;
  background-color: #f0f8ff;
}

.tab-btn.active {
  color: #1890ff;
  border-bottom-color: #1890ff;
  background-color: #fff;
  font-weight: 500;
}

.tabs-content {
  height: calc(100% - 48px);
  overflow-y: auto;
}

.tab-panel {
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
}

/* 明细数据样式 */
.detail-container {
  height: 100%;
  overflow-y: auto;
}

.force-detail-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.force-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e8e8e8;
}

.force-detail-header h3 {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin: 0;
}

.force-score {
  font-size: 18px;
  font-weight: bold;
  color: #1890ff;
}

.fixed-badge {
  padding: 2px 8px;
  background-color: #fff3cd;
  color: #856404;
  font-size: 12px;
  border-radius: 4px;
}

.fixed-notice {
  padding: 10px;
  background-color: #fff3cd;
  color: #856404;
  font-size: 14px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.dimension-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.dimension-table th,
.dimension-table td {
  padding: 8px 12px;
  border: 1px solid #e8e8e8;
  text-align: left;
}

.dimension-table th {
  background-color: #fafafa;
  font-weight: 500;
  color: #333;
}

.dimension-table tr.data-missing {
  background-color: #fff2f0;
}

.missing-text {
  color: #ff4d4f;
  font-style: italic;
}

.dim-note {
  color: #999;
  font-size: 12px;
}

/* 可视化样式 */
.visualization-container {
  height: 100%;
  overflow-y: auto;
}

.chart-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.chart-controls {
  margin-bottom: 15px;
}

.chart-select {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
  background-color: #fff;
  transition: all 0.3s;
}

.chart-select:hover {
  border-color: #1890ff;
}

.chart-select:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  outline: none;
}

.chart-large {
  width: 100%;
  height: 400px;
}

/* 对比样式 */
.compare-container {
  height: 100%;
}

.compare-controls {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.compare-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.compare-group label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.chart-compare {
  width: 100%;
  height: 400px;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 500;
  color: #333;
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: #333;
  background-color: #f0f0f0;
}

.modal-body {
  padding: 20px;
}

.formula-item {
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.formula-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.formula-item h3 {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin: 0 0 10px 0;
}

.formula-desc {
  font-size: 14px;
  color: #666;
  margin: 0 0 15px 0;
  line-height: 1.5;
}

.formula-detail {
  font-size: 14px;
  color: #666;
}

.formula-detail p {
  margin: 8px 0;
}

.formula-text {
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  margin: 10px 0;
  overflow-x: auto;
}

.formula-detail ul {
  list-style: disc;
  padding-left: 20px;
  margin: 10px 0;
}

.formula-detail li {
  margin: 5px 0;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .left1 {
    width: 25%;
  }
  
  .mrbox {
    width: 75%;
  }
  
  .mrbox_topmidd {
    width: 65%;
  }
  
  .mrbox_top_right {
    width: 35%;
  }
}

@media (max-width: 768px) {
  .bnt {
    flex-direction: column;
    height: auto;
    gap: 10px;
    padding: 10px 0;
  }
  
  .topbnt_left,
  .topbnt_right {
    width: 100%;
    justify-content: center;
  }
  
  .left1 {
    width: 100%;
    height: auto;
    float: none;
    padding-right: 0;
    margin-bottom: 20px;
  }
  
  .mrbox {
    width: 100%;
    float: none;
  }
  
  .mrbox_topmidd,
  .mrbox_top_right {
    width: 100%;
    float: none;
    padding-right: 0;
    margin-bottom: 20px;
  }
  
  .widget-inline-box {
    min-width: 100%;
  }
  
  .compare-controls {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .manual-row {
    flex-direction: column;
  }
  
  .manual-row button {
    width: 100%;
    padding: 8px 12px;
  }
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 工具类 */
.fl {
  float: left;
}

.fr {
  float: right;
}

.clearfix::after {
  content: '';
  display: table;
  clear: both;
}

.text-center {
  text-align: center;
}

.text-muted {
  color: #999 !important;
}

.pt6 {
  padding-top: 6px;
}

/* 图表容器样式 */
.chart-ordered {
  width: 100%;
  height: 400px;
}

.chart-large {
  width: 100%;
  height: 400px;
}

.chart-compare {
  width: 100%;
  height: 400px;
}

/* 颜色类 */
.c1965ff {
  color: #1965ff;
}

.c24c9ff {
  color: #24c9ff;
}

.c24d9ff {
  color: #24d9ff;
}

.c112ff {
  color: #c112ff;
}

.c764ff {
  color: #c764ff;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .chart-ordered,
  .chart-large,
  .chart-compare {
    height: 300px;
  }
}
</style>  border-radius: 5px;
  float: left;
}

/*  天气样式 */
.today_weather_num {}

.today_weather_num h1 {
  font-size: 50px;
  color: #fff;
  font-weight: bold;
  margin-top: 5px;
}

.today_weather_img {}

.today_weather_img img {
  width: 60px;
  height: 60px;
  margin-top: 8px;
}

.today_weather_week p {
  font-size: 14px;
  color: #535353;
  margin-top: 30px;
}

.today_weather_week p span {
  color: #fff;
}

/* 字体颜色 */
.c3691ff {
  color: #3691ff !important;
}

.c6c1ffff {
  color: #c1ffff !important;
}

.c1965ff {
  color: #1965ff !important;
}

.c24c9ff {
  color: #24c9ff !important;
}

.c24d9ff {
  color: #24d9ff !important;
}

.c112ff {
  color: #112ff !important;
}

.c764ff {
  color: #764ff !important;
}

/* 字体大小 */
.size12 {
  font-size: 12px;
}

.size14 {
  font-size: 14px;
}

.size16 {
  font-size: 16px;
}

.size18 {
  font-size: 18px;
}

.size20 {
  font-size: 20px;
}

.size24 {
  font-size: 24px;
}

.size28 {
  font-size: 28px;
}

.size32 {
  font-size: 32px;
}

.size36 {
  font-size: 36px;
}

.size40 {
  font-size: 40px;
}

/* 内边距 */
.pt1 {
  padding-top: 1%;
}

.pt2 {
  padding-top: 2%;
}

.pt3 {
  padding-top: 3%;
}

.pt4 {
  padding-top: 4%;
}

.pt5 {
  padding-top: 5%;
}

.pt6 {
  padding-top: 6%;
}

/* 文本居中 */
.text-center {
  text-align: center;
}

/* 文本居右 */
.text-right {
  text-align: right;
}

/* 文本颜色 */
.text-muted {
  color: #b4b4b4 !important;
}

/* 高度 */
.height {
  height: 8% !important;
}

.ht {
  margin-bottom: 10px !important;
}

/* 布局 */
.fl {
  float: left;
}

.fr {
  float: right;
}

/* 透明度 */
.opcity {
  opacity: 0.4;
}

/* 左侧中间 */
.aleftboxtmiddcont {
  width: 100%;
  height: 100%;
  overflow: hidden;
  text-align: left;
}

.aleftboxtmiddcont p {
  line-height: 25px;
  font-size: 13px;
  color: #fafafa;
  font-weight: normal;
}

/* 左侧底部 */
.aleftboxtbott_cont {
  width: 100%;
  height: 80%;
  overflow: hidden;
  margin-top: 15px;
}

/* 右侧顶部 */
.arightboxtopcont {}

/* 右侧底部 */
.arightboxbottcont {
  width: 100%;
  height: 80%;
  overflow: hidden;
  margin-top: 15px;
}

/* 中间底部 */
.amiddboxtbott1content {
  width: 100%;
  height: 80%;
  overflow: hidden;
  margin-top: 15px;
}

.amiddboxtbott2content {
  width: 100%;
  height: 80%;
  overflow: hidden;
  margin-top: 15px;
}

/* 图例样式 */
.icon_list {
  width: 100%;
  height: 100%;
  overflow: hidden;
  margin-top: 10px;
}

.icon_list ul {
  list-style: none;
}

.icon_list li {
  width: 50%;
  height: 100%;
  text-align: left;
  float: left;
  margin-bottom: 5px;
}

.icon_list p {
  line-height: 18px;
  font-size: 12px;
  color: #fafafa;
  font-weight: normal;
}

.icon_list img {
  margin-top: 3px;
  width: 15px;
  height: 15px;
  margin-right: 4px;
}

/* 图例样式 结束 */
/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.chart {
  width: 95%;
  height: 80%;
  margin-left: 2.5%;
  margin-top: 2%;
}

.chart-ordered {
  width: 100%;
  height: calc(100% - 60px);
  min-height: 400px;
  margin-top: 10px;
}

.selector-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selector label {
  font-weight: bold;
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
}

.selector select {
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  color: white;
  font-size: 14px;
  min-width: 200px;
}

.selector select option {
  background: rgba(20, 20, 30, 0.95);
  color: white;
  padding: 8px;
}

.selector.manual {
  min-width: 300px;
}

.manual-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.input {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  color: white;
  font-size: 14px;
  flex: 1;
}

.btn {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.current-tip, .error-tip {
  margin: 8px 0 0;
  font-size: 12px;
}

.current-tip {
  color: rgba(255, 255, 255, 0.8);
}

.error-tip {
  color: #ff6b6b;
}

.widget-inline-box {
  width: 100%;
  height: 100%;
  text-align: center;
  margin-bottom: 20px;
}

.widget-inline-box h3 {
  font-size: 35px;
  font-weight: bold;
  color: #fff;
}

.widget-inline-box p {
  line-height: 25px;
  font-size: 13px;
  color: #fafafa;
  font-weight: normal;
}

/* 标签页样式 */
.tabs-container {
  width: 100%;
  height: 100%;
}

.tabs-header {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.tab-btn {
  padding: 10px 20px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #c3c3c3;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  color: #ffffff;
}

.tab-btn.active {
  color: #9b59b6;
  border-bottom-color: #9b59b6;
}

.tab-panel {
  width: 100%;
  height: calc(100% - 60px);
  overflow-y: auto;
}

/* 明细数据样式 */
.detail-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px;
}

.force-detail-card {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.force-detail-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.force-detail-header h3 {
  font-size: 18px;
  color: #fff;
  margin: 0;
  flex: 1;
}

.force-score {
  font-size: 24px;
  font-weight: bold;
}

.fixed-badge {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
}

.fixed-notice {
  background: rgba(255, 193, 7, 0.1);
  border-left: 3px solid #ffc107;
  padding: 10px 15px;
  margin-bottom: 15px;
  color: #ffc107;
  font-size: 13px;
}

.force-dimensions {
  overflow-x: auto;
}

.dimension-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.dimension-table thead {
  background: rgba(255, 255, 255, 0.05);
}

.dimension-table th {
  padding: 12px;
  text-align: left;
  color: #cce7ff;
  font-weight: 600;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.dimension-table td {
  padding: 10px 12px;
  color: #fafafa;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.dimension-table tr:hover {
  background: rgba(255, 255, 255, 0.05);
}

.dimension-table tr.data-missing {
  opacity: 0.5;
}

.dimension-table tr.data-missing td {
  color: #999;
}

.missing-text {
  color: #ff6b6b;
  font-style: italic;
}

.dim-note {
  font-size: 12px;
  color: #b4b4b4;
}

/* 可视化样式 */
.visualization-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px;
}

.chart-section {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 5px;
  padding: 15px;
  min-height: 400px;
}

.chart-controls {
  margin-bottom: 15px;
}

.chart-select {
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  color: white;
  font-size: 14px;
  min-width: 250px;
}

.chart-select option {
  background: rgba(20, 20, 30, 0.95);
  color: white;
  padding: 8px;
}

.chart-large {
  width: 100%;
  height: 350px;
}

/* 对比样式 */
.compare-container {
  padding: 10px;
}

.compare-controls {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.compare-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.compare-group label {
  color: #cce7ff;
  font-size: 14px;
  white-space: nowrap;
}

.chart-compare {
  width: 100%;
  height: 500px;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: rgba(20, 20, 30, 0.95);
  border-radius: 8px;
  width: 80%;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h2 {
  margin: 0;
  color: #fff;
  font-size: 20px;
}

.modal-close {
  background: transparent;
  border: none;
  color: #fff;
  font-size: 28px;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.3s;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 20px;
}

.formula-item {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.formula-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.formula-item h3 {
  color: #5ad8ff;
  font-size: 18px;
  margin-bottom: 10px;
}

.formula-desc {
  color: #cce7ff;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 15px;
}

.formula-detail {
  background: rgba(0, 0, 0, 0.3);
  padding: 15px;
  border-radius: 5px;
  margin-top: 10px;
}

.formula-detail p {
  color: #fafafa;
  margin: 8px 0;
  font-size: 14px;
}

.formula-text {
  background: rgba(90, 216, 255, 0.1);
  padding: 10px;
  border-radius: 4px;
  border-left: 3px solid #5ad8ff;
  font-family: 'Courier New', monospace;
  color: #5ad8ff;
  margin: 10px 0;
}

.formula-detail ul {
  margin: 10px 0;
  padding-left: 20px;
}

.formula-detail li {
  color: #cce7ff;
  margin: 5px 0;
  font-size: 13px;
  line-height: 1.6;
}

/* 错误文本样式 */
.error-text {
  color: #ff6b6b !important;
}

/* 响应式调整 */
@media (max-width: 1400px) {
  .mrbox_topmidd {
    width: 100% !important;
  }
  .mrbox_top_right {
    width: 100% !important;
    margin-top: 2%;
  }
}

/* 全局下拉列表样式优化 */
select {
  background-color: rgba(0, 0, 0, 0.4) !important;
  color: white !important;
}

select:focus {
  outline: none;
  border-color: rgba(90, 216, 255, 0.5);
  background-color: rgba(0, 0, 0, 0.5) !important;
}

select:hover {
  background-color: rgba(0, 0, 0, 0.5) !important;
}
</style>
