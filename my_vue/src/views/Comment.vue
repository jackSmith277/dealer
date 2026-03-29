<template>
  <div class="comment-container">
    <div class="header-section">
      <div class="header-left">
        <h1 class="page-title">试驾评价智能分析</h1>
        <p class="page-subtitle">基于NLP情感分析与主题聚类的评价洞察平台</p>
      </div>
      <div class="header-stats">
        <div class="header-stat-item">
          <span class="header-stat-value">{{ totalComments }}</span>
          <span class="header-stat-label">评价总数</span>
        </div>
        <div class="header-stat-item">
          <span class="header-stat-value positive">{{ sentimentStats.positivePercent }}%</span>
          <span class="header-stat-label">好评率</span>
        </div>
        <div class="header-stat-item">
          <span class="header-stat-value topic">{{ topicStats.length }}</span>
          <span class="header-stat-label">主题聚类</span>
        </div>
      </div>
      <div class="header-controls">
        <button class="btn btn-gray" @click="$router.push('/dashboard')">
          <i class="fas fa-arrow-left"></i> 返回
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">正在分析评价数据...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <i class="fas fa-exclamation-circle error-icon"></i>
      <p class="error-text">{{ error }}</p>
      <button class="btn btn-primary" @click="loadComments">重新加载</button>
    </div>

    <template v-else>
      <div class="sentiment-overview">
        <div class="sentiment-card positive">
          <div class="sentiment-icon">
            <i class="fas fa-smile"></i>
          </div>
          <div class="sentiment-info">
            <span class="sentiment-count">{{ sentimentStats.positive }}</span>
            <span class="sentiment-label">正面评价</span>
          </div>
          <div class="sentiment-bar">
            <div class="sentiment-bar-fill" :style="{ width: sentimentStats.positivePercent + '%' }"></div>
          </div>
        </div>
        <div class="sentiment-card neutral">
          <div class="sentiment-icon">
            <i class="fas fa-meh"></i>
          </div>
          <div class="sentiment-info">
            <span class="sentiment-count">{{ sentimentStats.neutral }}</span>
            <span class="sentiment-label">中性评价</span>
          </div>
          <div class="sentiment-bar">
            <div class="sentiment-bar-fill" :style="{ width: sentimentStats.neutralPercent + '%' }"></div>
          </div>
        </div>
        <div class="sentiment-card negative">
          <div class="sentiment-icon">
            <i class="fas fa-frown"></i>
          </div>
          <div class="sentiment-info">
            <span class="sentiment-count">{{ sentimentStats.negative }}</span>
            <span class="sentiment-label">负面评价</span>
          </div>
          <div class="sentiment-bar">
            <div class="sentiment-bar-fill" :style="{ width: sentimentStats.negativePercent + '%' }"></div>
          </div>
        </div>
      </div>

      <div class="topic-clustering-section">
        <div class="section-header main-header">
          <h2 class="section-title">
            <i class="fas fa-project-diagram"></i>
            主题聚类分析
          </h2>
          <p class="section-subtitle">基于语义相似度的评价主题自动识别与聚类</p>
        </div>
        <div class="topic-content">
          <div class="topic-charts-row">
            <div class="topic-radar-section card">
              <div class="section-header">
                <h3 class="section-title">主题分布雷达图</h3>
                <p class="section-subtitle">各主题关注度分布</p>
              </div>
              <div ref="topicRadarChart" class="chart-container radar-chart"></div>
            </div>
            <div class="topic-bars-section card">
              <div class="section-header">
                <h3 class="section-title">主题情感对比</h3>
                <p class="section-subtitle">各主题正负面评价对比</p>
              </div>
              <div ref="topicBarChart" class="chart-container bar-chart"></div>
            </div>
          </div>
          <div class="topic-details-section">
            <div 
              v-for="(topic, index) in topicStats" 
              :key="index"
              class="topic-detail-card card"
              :class="'topic-' + (index + 1)"
              @click="showTopicComments(topic)"
            >
              <div class="topic-header">
                <div class="topic-icon">
                  <i :class="topic.icon"></i>
                </div>
                <div class="topic-info">
                  <h4 class="topic-name">{{ topic.name }}</h4>
                  <span class="topic-count">{{ topic.count }}条评价</span>
                </div>
                <div class="topic-percent">{{ topic.percent }}%</div>
              </div>
              <div class="topic-keywords">
                <span 
                  v-for="(keyword, kidx) in topic.keywords.slice(0, 5)" 
                  :key="kidx"
                  class="topic-keyword"
                >
                  {{ keyword }}
                </span>
              </div>
              <div class="topic-sentiment-bar">
                <div class="sentiment-segment positive" :style="{ width: topic.positivePercent + '%' }"></div>
                <div class="sentiment-segment neutral" :style="{ width: topic.neutralPercent + '%' }"></div>
                <div class="sentiment-segment negative" :style="{ width: topic.negativePercent + '%' }"></div>
              </div>
              <div class="topic-sentiment-legend">
                <span class="legend-item positive">
                  <i class="fas fa-circle"></i> 正面 {{ topic.positivePercent }}%
                </span>
                <span class="legend-item neutral">
                  <i class="fas fa-circle"></i> 中性 {{ topic.neutralPercent }}%
                </span>
                <span class="legend-item negative">
                  <i class="fas fa-circle"></i> 负面 {{ topic.negativePercent }}%
                </span>
              </div>
              <div class="topic-samples">
                <div class="samples-header">
                  <i class="fas fa-quote-left"></i>
                  代表性评价
                </div>
                <div class="sample-item" v-if="topic.samples && topic.samples.length > 0">
                  <p class="sample-text">"{{ topic.samples[0].text }}"</p>
                  <span class="sample-sentiment" :class="topic.samples[0].sentiment">
                    {{ topic.samples[0].sentiment === 'positive' ? '正面' : topic.samples[0].sentiment === 'negative' ? '负面' : '中性' }}
                  </span>
                </div>
              </div>
              <div class="topic-expand-hint">
                <i class="fas fa-hand-pointer"></i>
                点击查看全部评价
              </div>
            </div>
            <div 
              class="topic-detail-card card topic-featured"
              @click="showFeaturedComments"
            >
              <div class="topic-header">
                <div class="topic-icon">
                  <i class="fas fa-star"></i>
                </div>
                <div class="topic-info">
                  <h4 class="topic-name">精选评论</h4>
                  <span class="topic-count">{{ featuredComments.length }}条评价</span>
                </div>
                <div class="topic-percent">
                  <i class="fas fa-quote-left"></i>
                </div>
              </div>
              <div class="topic-keywords">
                <span class="topic-keyword">深度评价</span>
                <span class="topic-keyword">字数>60</span>
                <span class="topic-keyword">优质内容</span>
              </div>
              <div class="topic-sentiment-bar">
                <div class="sentiment-segment positive" :style="{ width: featuredPositivePercent + '%' }"></div>
                <div class="sentiment-segment neutral" :style="{ width: featuredNeutralPercent + '%' }"></div>
                <div class="sentiment-segment negative" :style="{ width: featuredNegativePercent + '%' }"></div>
              </div>
              <div class="topic-sentiment-legend">
                <span class="legend-item positive">
                  <i class="fas fa-circle"></i> 正面 {{ featuredPositivePercent }}%
                </span>
                <span class="legend-item neutral">
                  <i class="fas fa-circle"></i> 中性 {{ featuredNeutralPercent }}%
                </span>
                <span class="legend-item negative">
                  <i class="fas fa-circle"></i> 负面 {{ featuredNegativePercent }}%
                </span>
              </div>
              <div class="topic-samples" v-if="featuredComments.length > 0">
                <div class="samples-header">
                  <i class="fas fa-quote-left"></i>
                  代表性评价
                </div>
                <div class="sample-item">
                  <p class="sample-text">"{{ featuredComments[0].content.substring(0, 60) }}..."</p>
                  <span class="sample-sentiment" :class="featuredComments[0].sentiment">
                    {{ featuredComments[0].sentiment === 'positive' ? '正面' : featuredComments[0].sentiment === 'negative' ? '负面' : '中性' }}
                  </span>
                </div>
              </div>
              <div class="topic-expand-hint">
                <i class="fas fa-hand-pointer"></i>
                点击查看全部精选评论
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="main-content">
        <div class="left-section">
          <div class="wordcloud-section card">
            <div class="section-header">
              <h2 class="section-title">评价关键词分布</h2>
              <p class="section-subtitle">鼠标悬停查看词频详情</p>
            </div>
            <div class="wordcloud-image-container">
              <div v-if="wordcloudLoading" class="wordcloud-loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>正在生成词云...</span>
              </div>
              <img 
                v-else-if="wordcloudImage" 
                :src="wordcloudImage" 
                alt="词云" 
                class="wordcloud-image"
              />
              <div v-else class="wordcloud-static">
                <span 
                  v-for="(word, index) in displayWords" 
                  :key="index"
                  class="static-word-tag"
                  :class="{ 'is-vertical': word.rotate }"
                  :style="{ 
                    fontSize: getWordFontSize(word.value) + 'px', 
                    color: getWordColor(index),
                    marginTop: word.offset + 'px',
                    opacity: getWordOpacity(index)
                  }"
                  @click="showKeywordComments(word.name)"
                >
                  {{ word.name }}
                </span>
              </div>
            </div>
          </div>

          <div class="wordcloud-comparison card">
            <div class="section-header">
              <h2 class="section-title">情感词云对比</h2>
              <p class="section-subtitle">点击词条查看相关评论</p>
            </div>
            <div class="comparison-container">
              <div class="comparison-column">
                <div class="comparison-header positive-header" @click="showSentimentComments('positive')">
                  <i class="fas fa-thumbs-up"></i>
                  <span>正面关键词</span>
                </div>
                <div class="word-tags positive-tags">
                  <span 
                    v-for="(word, index) in positiveWords.slice(0, 15)" 
                    :key="'pos-' + index"
                    class="word-tag positive-tag"
                    :style="{ fontSize: getTagSize(word.value, 'positive') + 'px' }"
                    @click.stop="showKeywordComments(word.name, null, 'positive')"
                  >
                    {{ word.name }}
                  </span>
                </div>
              </div>
              <div class="comparison-divider"></div>
              <div class="comparison-column">
                <div class="comparison-header neutral-header" @click="showSentimentComments('neutral')">
                  <i class="fas fa-meh"></i>
                  <span>中性关键词</span>
                </div>
                <div class="word-tags neutral-tags">
                  <span 
                    v-for="(word, index) in neutralWords.slice(0, 15)" 
                    :key="'neu-' + index"
                    class="word-tag neutral-tag"
                    :style="{ fontSize: getTagSize(word.value, 'neutral') + 'px' }"
                    @click.stop="showKeywordComments(word.name, null, 'neutral')"
                  >
                    {{ word.name }}
                  </span>
                </div>
              </div>
              <div class="comparison-divider"></div>
              <div class="comparison-column">
                <div class="comparison-header negative-header" @click="showSentimentComments('negative')">
                  <i class="fas fa-thumbs-down"></i>
                  <span>负面关键词</span>
                </div>
                <div class="word-tags negative-tags">
                  <span 
                    v-for="(word, index) in negativeWords.slice(0, 35)" 
                    :key="'neg-' + index"
                    class="word-tag negative-tag"
                    :style="{ fontSize: getTagSize(word.value, 'negative') + 'px' }"
                    @click.stop="showKeywordComments(word.name, null, 'negative')"
                  >
                    {{ word.name }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="enhancement-card card full-width treemap-card">
            <div class="section-header">
              <h3 class="section-title">关键词层级矩阵树图</h3>
              <p class="section-subtitle">按主题分类的关键词层级展示</p>
            </div>
            <div ref="treemapChart" class="chart-container treemap-chart"></div>
          </div>
          
          <div class="side-by-side-cards">
            <div class="enhancement-card card">
              <div class="section-header">
                <h3 class="section-title">情感极性雷达图</h3>
                <p class="section-subtitle">多维度情感强度分析</p>
              </div>
              <div ref="sentimentRadarChart" class="chart-container side-chart"></div>
            </div>
            <div class="enhancement-card card">
              <div class="section-header">
                <h3 class="section-title">主题关系网络图</h3>
                <p class="section-subtitle">主题间关联强度可视化</p>
              </div>
              <div ref="topicNetworkChart" class="chart-container side-chart"></div>
            </div>
          </div>
        </div>

        <div class="right-section">
          <div class="sentiment-pie-section card">
            <div class="section-header">
              <h2 class="section-title">情感分布</h2>
              <p class="section-subtitle">评价情感极性占比</p>
            </div>
            <div ref="sentimentPieChart" class="chart-container"></div>
          </div>

          <div class="sentiment-trend-section card">
            <div class="section-header">
              <h2 class="section-title">情感趋势分析</h2>
              <p class="section-subtitle">近期评价情感变化</p>
            </div>
            <div ref="sentimentTrendChart" class="chart-container"></div>
          </div>

          <div class="top-words-section card">
            <div class="section-header">
              <h2 class="section-title">热门关键词TOP10</h2>
              <p class="section-subtitle">按出现频次排序</p>
            </div>
            <div class="top-words-list">
              <div 
                v-for="(word, index) in topWords" 
                :key="index"
                class="top-word-item"
              >
                <span class="word-rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
                <span class="word-name">{{ word.name }}</span>
                <div class="word-bar-wrapper">
                  <div class="word-bar" :style="{ width: getBarWidth(word.value) }"></div>
                </div>
                <span class="word-count">{{ word.value }}次</span>
              </div>
            </div>
          </div>

          <div class="insight-section card">
            <div class="section-header">
              <h2 class="section-title">
                <i class="fas fa-lightbulb insight-icon"></i>
                智能洞察
              </h2>
            </div>
            <div class="insight-content">
              <div class="insight-item" v-if="insights.strength">
                <div class="insight-label positive-label">
                  <i class="fas fa-check-circle"></i>
                  优势亮点
                </div>
                <p class="insight-text">{{ insights.strength }}</p>
              </div>
              <div class="insight-item" v-if="insights.weakness">
                <div class="insight-label negative-label">
                  <i class="fas fa-exclamation-circle"></i>
                  待改进项
                </div>
                <p class="insight-text">{{ insights.weakness }}</p>
              </div>
              <div class="insight-item" v-if="insights.suggestion">
                <div class="insight-label suggestion-label">
                  <i class="fas fa-arrow-circle-right"></i>
                  改进建议
                </div>
                <p class="insight-text">{{ insights.suggestion }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="sankey-section card">
        <div class="section-header">
          <h3 class="section-title">
            <i class="fas fa-random"></i>
            评价情感流转桑基图
          </h3>
          <p class="section-subtitle">评价主题到情感的流转关系</p>
        </div>
        <div ref="sankeyChart" class="chart-container sankey-chart"></div>
      </div>
    </template>

    <div v-if="hoveredWord" class="word-tooltip">
      <div class="tooltip-content">
        <span class="tooltip-word">{{ hoveredWord.name }}</span>
        <span class="tooltip-count">出现次数: {{ hoveredWord.value }}</span>
      </div>
    </div>
    
    <div v-if="showKeywordModal" class="keyword-modal-overlay" @click.self="closeKeywordModal">
      <div class="keyword-modal">
        <div class="modal-header">
          <h3 class="modal-title">
            <i class="fas fa-search"></i>
            包含"{{ selectedKeyword }}"的评价
          </h3>
          <span class="modal-count">共 {{ keywordCommentsTotal }} 条</span>
          <button class="modal-close" @click="closeKeywordModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="keywordComments.length === 0" class="no-comments">
            暂无相关评价
          </div>
          <div v-else class="comment-list">
            <div 
              v-for="(comment, index) in keywordComments" 
              :key="index" 
              class="comment-item"
              :class="getSentimentClass(comment.sentiment)"
            >
              <div class="comment-header">
                <span class="comment-score">评分: {{ comment.score }}</span>
                <span class="comment-sentiment" :class="getSentimentClass(comment.sentiment)">
                  {{ getSentimentLabel(comment.sentiment) }}
                </span>
              </div>
              <div class="comment-content">{{ comment.content }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="showTopicModal" class="keyword-modal-overlay" @click.self="closeTopicModal">
      <div class="keyword-modal">
        <div class="modal-header">
          <h3 class="modal-title">
            <i :class="selectedTopic?.icon"></i>
            "{{ selectedTopic?.name }}"相关评价
          </h3>
          <span class="modal-count">共 {{ topicComments.length }} 条</span>
          <button class="modal-close" @click="closeTopicModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="topicComments.length === 0" class="no-comments">
            暂无相关评价
          </div>
          <div v-else class="comment-list">
            <div 
              v-for="(comment, index) in topicComments" 
              :key="index" 
              class="comment-item"
              :class="getSentimentClass(comment.sentiment)"
            >
              <div class="comment-header">
                <span class="comment-score">评分: {{ comment.score }}</span>
                <span class="comment-sentiment" :class="getSentimentClass(comment.sentiment)">
                  {{ getSentimentLabel(comment.sentiment) }}
                </span>
              </div>
              <div class="comment-content">{{ comment.content }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import * as echarts from 'echarts'

export default {
  name: 'Comment',
  data() {
    return {
      comments: [],
      rawComments: [],
      wordData: [],
      loading: true,
      error: null,
      isRotating: true,
      isStatic: false,
      rotationAngle: 0,
      rotationInterval: null,
      hoveredWord: null,
      sentimentPieChart: null,
      sentimentTrendChart: null,
      topicRadarChart: null,
      topicBarChart: null,
      sentimentRadarChart: null,
      topicNetworkChart: null,
      sankeyChart: null,
      treemapChart: null,
      resizeObserver: null,
      resizeTimer: null,
      selectedKeyword: null,
      keywordComments: [],
      keywordCommentsTotal: 0,
      showKeywordModal: false,
      selectedTopic: null,
      topicComments: [],
      showTopicModal: false,
      positiveWords: [],
      negativeWords: [],
      neutralWords: [],
      sentimentResults: [],
      topicStats: [],
      wordcloudImage: null,
      wordcloudLoading: false,
      topicKeywords: {
        '动力性能': {
          keywords: ['动力', '加速', '发动机', '马力', '提速', '推背感', '动力强', '动力弱', '起步', '超车', '爬坡', '涡轮', '混动', '纯电'],
          icon: 'fas fa-tachometer-alt'
        },
        '操控体验': {
          keywords: ['操控', '方向盘', '转向', '悬挂', '底盘', '刹车', '制动', '稳定', '灵活', '精准', '路感', '过弯', '驾驶感'],
          icon: 'fas fa-car'
        },
        '舒适度': {
          keywords: ['舒适', '座椅', '空间', '安静', '噪音', '隔音', '减震', '空调', '后排', '腿部空间', '头部空间', '乘坐', '舒适度'],
          icon: 'fas fa-couch'
        },
        '外观设计': {
          keywords: ['外观', '设计', '颜值', '造型', '颜色', '线条', '车灯', '进气格栅', '轮毂', '车身', '好看', '漂亮', '大气', '时尚'],
          icon: 'fas fa-paint-brush'
        },
        '内饰配置': {
          keywords: ['内饰', '配置', '中控', '屏幕', '材质', '做工', '用料', '科技感', '仪表盘', '按键', '储物', '氛围灯', '豪华'],
          icon: 'fas fa-th-large'
        },
        '性价比': {
          keywords: ['性价比', '价格', '优惠', '划算', '保值', '便宜', '贵', '值', '配置高', '减配', '优惠力度', '落地'],
          icon: 'fas fa-balance-scale'
        },
        '油耗续航': {
          keywords: ['油耗', '省油', '费油', '续航', '电耗', '充电', '油箱', '百公里', '能耗', '续航短', '续航长', '充电慢'],
          icon: 'fas fa-gas-pump'
        },
        '服务质量': {
          keywords: ['服务', '态度', '销售', '顾问', '专业', '热情', '耐心', '诚信', '售后', '保养', '维修', '响应', '接待'],
          icon: 'fas fa-user-tie'
        }
      },
      stopWords: [
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '她', '他', '它', '们', '这个', '那个', '什么', '怎么',
        '可以', '可能', '因为', '所以', '但是', '如果', '还是', '或者', '而且',
        '已经', '一下', '一些', '一点', '一直', '一起', '一切', '一边', '一定',
        '觉得', '感觉', '认为', '以为', '知道', '看到', '听到', '想到', '发现',
        '这样', '那样', '怎样', '这么', '那么', '多么', '如何', '为何', '几',
        '站', '经销商', '销售', '顾问', '试驾', '评价', '选择', 'null', 'NaN',
        '比较', '非常', '特别', '真的', '确实', '实在', '相当', '稍微', '过于'
      ],
      positiveDict: [
        '好', '棒', '赞', '满意', '舒适', '漂亮', '喜欢', '优秀', '出色', '完美',
        '给力', '推荐', '惊喜', '超值', '划算', '便宜', '实惠', '高端', '大气', '上档次',
        '动力强', '省油', '安静', '平顺', '操控好', '空间大', '配置高', '性价比', '保值',
        '服务好', '态度好', '专业', '热情', '周到', '细致', '耐心', '诚信', '靠谱',
        '舒适', '宽敞', '明亮', '干净', '整洁', '豪华', '精致', '细腻', '质感',
        '强劲', '充沛', '灵敏', '精准', '稳定', '安全', '可靠', '耐用', '省心',
        '好看', '时尚', '运动', '年轻', '科技感', '未来感', '设计感', '潮流',
        '智能', '便捷', '实用', '方便', '人性化', '贴心', '周到', '细心',
        '满意', '开心', '高兴', '惊喜', '意外', '超出预期', '物超所值',
        '流畅', '顺滑', '轻快', '轻松', '惬意', '享受', '舒适', '惬意',
        '不错', '挺好', '还好', '还好', '可以', '还行', '挺好', '蛮好',
        '完美', '到位', '清晰', '解答', '良好', '不错', '便利', '良好',
        '体验好', '试驾好', '服务热情', '品牌信任', '优惠活动', '朋友推荐',
        '内饰好', '外观好', '安全好', '动力好', '性价比高', '便利实用',
        '用心', '认真', '负责', '细心', '周到', '热情', '友好', '亲切',
        '满意', '感谢', '感谢', '赞', '好评', '五星', '满分', '推荐',
        '试驾体验好', '讲解清晰', '态度好', '服务周到', '环境好', '设施齐全',
        '车型丰富', '功能齐全', '体验充分', '预约方便', '场地良好', '形式丰富'
      ],
      negativeDict: [
        '差', '烂', '糟', '失望', '后悔', '坑', '骗', '垃圾', '垃圾', '问题',
        '贵', '不值', '坑人', '忽悠', '欺骗', '虚假', '欺诈', '坑爹', '宰客',
        '动力弱', '费油', '噪音', '抖动', '异响', '顿挫', '卡顿', '故障', '毛病',
        '空间小', '配置低', '减配', '偷工减料', '质量差', '做工差', '粗糙',
        '服务差', '态度差', '冷漠', '敷衍', '推诿', '拖延', '不专业', '不靠谱',
        '拥挤', '狭窄', '压抑', '暗淡', '廉价', '低档', '老土', '过时',
        '迟钝', '笨重', '费力', '累人', '不便', '麻烦', '复杂', '难用',
        '难看', '丑', '土', '老气', '过时', '没设计感', '山寨', '模仿',
        '不智能', '鸡肋', '花哨', '不实用', '反人类', '难操作', '不友好',
        '不满', '生气', '愤怒', '恼火', '烦躁', '郁闷', '无语', '崩溃',
        '漏水', '漏油', '生锈', '掉漆', '开裂', '变形', '松动', '脱落',
        '续航短', '充电慢', '电池差', '续航虚', '虚标', '缩水',
        '态度冷淡', '讲解不清晰', '等待时间长', '未提供饮品', '危险驾驶',
        '车辆有异味', '车辆不整洁', '车辆有损坏', '试驾时间短', '功能体验不充分',
        '智能交互不好', '动力性能差', '空间不足', '舒适性差', '内饰质感不好',
        '极差', '有待提高', '神经', '盗用', '虚假', '坑骗', '糊弄', '差评',
        '乱搞', '忽悠', '坑人', '骗人', '欺骗', '虚假试驾', '冒名顶替',
        '一问三不知', '不专业', '不耐烦', '敷衍了事', '推卸责任', '态度恶劣',
        '操控复杂', '收油太快', '刹车太快', '颠簸', '压抑感', '功能不全',
        '没有360', '会车不便', '方向盘挡屏幕', '换挡不便', '后排难受',
        '盗用信息', '投诉到底', '安全隐患', '发生事故', '坑骗客户', '失望透',
        '态度恶略', '体验极差', '发动机故障', '强制保电', '子虚乌有', '经常坏',
        '莫名其妙', '退款', '销售差劲', '打哈哈', '忘了', '隔音差', '路感差',
        '糊弄人', '没试驾到', '等了很久', '没被安排', '不买保险', '玩手机',
        '不了解', '回答问题不清晰', '冲业绩', '好忽悠', '不愿乘坐', '内在不足',
        '油耗高', '胎噪大', '风噪大', '起步慢', '加速慢', '超车难', '爬坡无力',
        '悬挂硬', '减震差', '底盘低', '通过性差', '转向重', '方向盘重',
        '座椅硬', '座椅不舒服', '后排挤', '后备箱小', '储物空间少',
        '车机卡', '屏幕小', '分辨率低', '反应慢', '死机', '黑屏', '闪退',
        '信号差', '定位不准', '导航不准', '蓝牙断', '连不上', '充不进',
        '空调差', '制冷慢', '制热慢', '异味大', '甲醛', '有毒',
        '漆面薄', '钣金薄', '缝隙大', '异响多', '共振', '抖动大',
        '保养贵', '维修贵', '配件贵', '等待久', '缺货', '没现车',
        '销售忽悠', '销售骗人', '销售态度差', '销售不专业', '销售不耐烦',
        '销售敷衍', '销售推诿', '销售拖延', '销售冷漠', '销售傲慢',
        '承诺不兑现', '说好的没有', '变卦', '反悔', '不认账',
        '套路深', '套路多', '强制消费', '捆绑销售', '隐形消费', '乱收费',
        '合同陷阱', '文字游戏', '霸王条款', '不退定金', '定金不退',
        '交车慢', '提车难', '拖延交车', '一拖再拖', '遥遥无期',
        '货不对板', '配置缩水', '减配严重', '偷梁换柱', '以次充好',
        '售后差', '售后推诿', '售后拖延', '售后敷衍', '售后冷漠',
        '投诉无门', '维权难', '没人管', '没人理', '踢皮球',
        '体验差', '感受差', '印象差', '观感差', '手感差', '脚感差',
        '不推荐', '不买', '不考虑', '放弃', '退订', '后悔买',
        '被坑', '被忽悠', '被欺骗', '被套路', '被糊弄', '被敷衍',
        '浪费时间', '白跑一趟', '空欢喜', '一场空', '竹篮打水',
        '不值这个价', '性价比低', '不划算', '亏了', '买贵了',
        '比不上', '不如', '差远了', '差很多', '差一大截',
        '难以接受', '无法接受', '不能接受', '接受不了', '忍不了'
      ],
      neutralDict: [
        '一般', '普通', '还行', '还可以', '凑合', '过得去', '差不多',
        '有待提高', '需要改进', '有待加强', '还需完善', '有待提升',
        '中规中矩', '无功无过', '不好不坏', '一般般', '马马虎虎',
        '感觉还行', '总体还行', '整体还行', '还算可以', '勉强接受',
        '有待观察', '需要适应', '习惯就好', '慢慢适应',
        '内饰质感达不到', '功能不齐全', '没有全影', '方向盘挡屏幕',
        '换挡旋钮', '怀档', '试驾不长', '后排上下车难受', '只有外观',
        '对车型不了解', '回答问题不清晰', '收油门', '刹车太快',
        '操控有点复杂', '没有去试一下', '有心提升品质', '解答到位',
        '服务较差', '内在不足', '质感达不到', '不愿再次乘坐',
        '有待', '提升', '改进', '完善', '加强', '适应', '观察'
      ],
      degreeWords: {
        positive: ['非常', '特别', '超级', '极其', '十分', '相当', '格外', '尤其'],
        negative: ['不太', '不怎么', '有点', '稍微', '略', '稍']
      },
      negationWords: ['不', '没', '无', '非', '莫', '别', '未', '勿']
    }
  },
  computed: {
    totalComments() {
      return this.comments.length
    },
    topWord() {
      if (this.wordData.length > 0) {
        return this.wordData[0]
      }
      return null
    },
    topWords() {
      return this.wordData.slice(0, 10)
    },
    sentimentStats() {
      const total = this.sentimentResults.length || 1
      const positive = this.sentimentResults.filter(r => r.sentiment === 'positive').length
      const negative = this.sentimentResults.filter(r => r.sentiment === 'negative').length
      const neutral = this.sentimentResults.filter(r => r.sentiment === 'neutral').length
      
      return {
        positive,
        negative,
        neutral,
        positivePercent: (positive / total * 100).toFixed(1),
        negativePercent: (negative / total * 100).toFixed(1),
        neutralPercent: (neutral / total * 100).toFixed(1)
      }
    },
    insights() {
      const insights = {
        strength: '',
        weakness: '',
        suggestion: ''
      }
      
      if (this.positiveWords.length > 0) {
        const topPositive = this.positiveWords.slice(0, 3).map(w => w.name).join('、')
        insights.strength = `用户普遍认可车辆的${topPositive}等方面表现，好评率达${this.sentimentStats.positivePercent}%，体现了产品核心竞争力。`
      }
      
      if (this.negativeWords.length > 0) {
        const topNegative = this.negativeWords.slice(0, 3).map(w => w.name).join('、')
        insights.weakness = `部分用户反映${topNegative}等问题，负面评价占比${this.sentimentStats.negativePercent}%，需重点关注改进。`
      }
      
      if (this.negativeWords.length > 0) {
        insights.suggestion = `建议针对用户反馈的痛点问题进行优化改进，同时加强售前售后服务质量，提升用户整体满意度。`
      }
      
      return insights
    },

    displayWords() {
      if (!this.wordData || this.wordData.length === 0) return [];

      // 1. 增加显示的词量，词越多越紧凑
      const topWords = this.wordData.slice(0, 80); 
      
      // 2. 经典的"中心聚集"重排逻辑
      const centerArray = [];
      topWords.forEach((word, index) => {
        // 采用双向推入，使得权重高的（index小的）始终往中间靠拢
        if (index % 2 === 0) {
          centerArray.push(word);
        } else {
          centerArray.unshift(word);
        }
      });

      return centerArray;
    },
    featuredComments() {
      const longComments = this.rawComments
        .filter(item => item.content && item.content.length > 60)
        .sort((a, b) => {
          if (a.sentiment === 'positive' && b.sentiment !== 'positive') return -1;
          if (a.sentiment !== 'positive' && b.sentiment === 'positive') return 1;
          return b.content.length - a.content.length;
        });
      return longComments.map(item => ({
        content: item.content,
        score: item.score,
        sentiment: item.sentiment
      }));
    },
    featuredPositivePercent() {
      if (this.featuredComments.length === 0) return 0;
      const count = this.featuredComments.filter(c => c.sentiment === 'positive').length;
      return ((count / this.featuredComments.length) * 100).toFixed(1);
    },
    featuredNeutralPercent() {
      if (this.featuredComments.length === 0) return 0;
      const count = this.featuredComments.filter(c => c.sentiment === 'neutral').length;
      return ((count / this.featuredComments.length) * 100).toFixed(1);
    },
    featuredNegativePercent() {
      if (this.featuredComments.length === 0) return 0;
      const count = this.featuredComments.filter(c => c.sentiment === 'negative').length;
      return ((count / this.featuredComments.length) * 100).toFixed(1);
    }
  },
  mounted() {
    this.loadComments()
    window.addEventListener('resize', this.handleResize)
    
    this.resizeObserver = new ResizeObserver(() => {
      this.handleResize()
    })
  },
  beforeDestroy() {
    this.stopRotation()
    window.removeEventListener('resize', this.handleResize)
    
    if (this.resizeTimer) {
      clearTimeout(this.resizeTimer)
      this.resizeTimer = null
    }
    
    if (this.resizeObserver) {
      this.resizeObserver.disconnect()
      this.resizeObserver = null
    }
    
    if (this.sentimentPieChart) {
      this.sentimentPieChart.dispose()
    }
    if (this.sentimentTrendChart) {
      this.sentimentTrendChart.dispose()
    }
    if (this.topicRadarChart) {
      this.topicRadarChart.dispose()
    }
    if (this.topicBarChart) {
      this.topicBarChart.dispose()
    }
    if (this.sentimentRadarChart) {
      this.sentimentRadarChart.dispose()
    }
    if (this.topicNetworkChart) {
      this.topicNetworkChart.dispose()
    }
    if (this.sankeyChart) {
      this.sankeyChart.dispose()
    }
    if (this.treemapChart) {
      this.treemapChart.dispose()
    }
  },
  methods: {
    async loadComments() {
      this.loading = true
      this.error = null
      try {
        const response = await axios.get('/api/comments')
        this.rawComments = response.data
        this.comments = this.rawComments.map(item => item.content)
        this.processComments()
        this.analyzeSentiment()
        this.analyzeTopics()
        this.fetchWordcloud()
        this.$nextTick(() => {
          this.initCharts()
          this.startRotation()
        })
      } catch (err) {
        console.error('加载评价数据失败:', err)
        this.error = '加载评价数据失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    
    processComments() {
      const wordCount = {}
      const text = this.comments.join(' ')
      
      const words = text.split(/[\s,，。！？、；：""''（）【】《》\n\r\t]+/)
      
      words.forEach(word => {
        const cleanWord = word.trim()
        if (cleanWord.length >= 2 && !this.stopWords.includes(cleanWord)) {
          wordCount[cleanWord] = (wordCount[cleanWord] || 0) + 1
        }
      })
      
      const sortedWords = Object.entries(wordCount)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 100)
      
      const maxCount = sortedWords[0] ? sortedWords[0][1] : 1
      
      this.wordData = sortedWords.map(([name, count]) => ({
        name,
        value: count,
        size: Math.max(16, Math.min(56, (count / maxCount) * 56))
      }))
    },
    
    analyzeSentiment() {
      const positiveWordCount = {}
      const negativeWordCount = {}
      const neutralWordCount = {}
      
      this.sentimentResults = this.rawComments.map((item, index) => {
        const comment = item.content
        const score = item.score
        const sentiment = item.sentiment
        
        const nlpResult = this.analyzeCommentSentiment(comment)
        
        if (score > 3) {
          nlpResult.positiveWords.forEach(word => {
            positiveWordCount[word] = (positiveWordCount[word] || 0) + 1
          })
          nlpResult.negativeWords.forEach(word => {
            positiveWordCount[word] = (positiveWordCount[word] || 0) + 1
          })
          nlpResult.neutralWords.forEach(word => {
            positiveWordCount[word] = (positiveWordCount[word] || 0) + 1
          })
        } else if (score < 3) {
          nlpResult.negativeWords.forEach(word => {
            negativeWordCount[word] = (negativeWordCount[word] || 0) + 1
          })
          nlpResult.positiveWords.forEach(word => {
            negativeWordCount[word] = (negativeWordCount[word] || 0) + 1
          })
          nlpResult.neutralWords.forEach(word => {
            negativeWordCount[word] = (negativeWordCount[word] || 0) + 1
          })
        } else {
          nlpResult.neutralWords.forEach(word => {
            neutralWordCount[word] = (neutralWordCount[word] || 0) + 1
          })
          nlpResult.positiveWords.forEach(word => {
            neutralWordCount[word] = (neutralWordCount[word] || 0) + 1
          })
          nlpResult.negativeWords.forEach(word => {
            neutralWordCount[word] = (neutralWordCount[word] || 0) + 1
          })
        }
        
        return {
          sentiment: sentiment,
          score: score,
          positiveScore: nlpResult.positiveScore,
          negativeScore: nlpResult.negativeScore,
          positiveWords: nlpResult.positiveWords,
          negativeWords: nlpResult.negativeWords,
          text: comment
        }
      })
      
      this.positiveWords = Object.entries(positiveWordCount)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
      
      this.negativeWords = Object.entries(negativeWordCount)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
      
      this.neutralWords = Object.entries(neutralWordCount)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 30)
    },
    
    async fetchWordcloud() {
      this.wordcloudLoading = true
      try {
        const response = await axios.post('/api/wordcloud', {
          comments: this.rawComments,
          positiveWords: this.positiveWords,
          negativeWords: this.negativeWords,
          neutralWords: this.neutralWords,
          type: 'all'
        })
        
        if (response.data.success && response.data.image) {
          this.wordcloudImage = response.data.image
        }
      } catch (err) {
        console.error('获取词云失败:', err)
      } finally {
        this.wordcloudLoading = false
      }
    },
    
    analyzeTopics() {
      const topicResults = {}
      const total = this.comments.length || 1
      
      Object.keys(this.topicKeywords).forEach(topicName => {
        topicResults[topicName] = {
          name: topicName,
          keywords: this.topicKeywords[topicName].keywords,
          icon: this.topicKeywords[topicName].icon,
          comments: [],
          commentIndices: [],
          positive: 0,
          negative: 0,
          neutral: 0,
          keywordCount: {}
        }
      })
      
      this.comments.forEach((comment, index) => {
        const sentimentResult = this.sentimentResults[index] || { sentiment: 'neutral' }
        let bestTopic = null
        let bestScore = 0
        
        Object.keys(this.topicKeywords).forEach(topicName => {
          const keywords = this.topicKeywords[topicName].keywords
          let score = 0
          
          keywords.forEach(keyword => {
            if (this.containsKeyword(comment, keyword)) {
              score++
            }
          })
          
          if (score > bestScore) {
            bestScore = score
            bestTopic = topicName
          }
        })
        
        if (bestTopic && bestScore > 0) {
          topicResults[bestTopic].comments.push({
            text: comment.length > 80 ? comment.substring(0, 80) + '...' : comment,
            sentiment: sentimentResult.sentiment,
            score: bestScore
          })
          topicResults[bestTopic].commentIndices.push(index)
          
          const topicKeywords = this.topicKeywords[bestTopic].keywords
          topicKeywords.forEach(keyword => {
            if (this.containsKeyword(comment, keyword)) {
              topicResults[bestTopic].keywordCount[keyword] = 
                (topicResults[bestTopic].keywordCount[keyword] || 0) + 1
            }
          })
          
          if (sentimentResult.sentiment === 'positive') {
            topicResults[bestTopic].positive++
          } else if (sentimentResult.sentiment === 'negative') {
            topicResults[bestTopic].negative++
          } else {
            topicResults[bestTopic].neutral++
          }
        }
      })
      
      this.topicStats = Object.values(topicResults)
        .filter(topic => topic.comments.length > 0)
        .map(topic => {
          const count = topic.comments.length
          const totalInTopic = count || 1
          
          const sortedKeywords = Object.entries(topic.keywordCount)
            .sort((a, b) => b[1] - a[1])
          
          return {
            name: topic.name,
            icon: topic.icon,
            keywords: sortedKeywords.map(([word]) => word),
            keywordCount: Object.fromEntries(sortedKeywords),
            commentIndices: topic.commentIndices,
            count: count,
            percent: (count / total * 100).toFixed(1),
            positive: topic.positive,
            negative: topic.negative,
            neutral: topic.neutral,
            positivePercent: (topic.positive / totalInTopic * 100).toFixed(1),
            negativePercent: (topic.negative / totalInTopic * 100).toFixed(1),
            neutralPercent: (topic.neutral / totalInTopic * 100).toFixed(1),
            samples: topic.comments
              .sort((a, b) => b.score - a.score)
              .slice(0, 3)
          }
        })
        .sort((a, b) => b.count - a.count)
    },
    
    analyzeCommentSentiment(comment) {
      const words = comment.split(/[\s,，。！？、；：""''（）【】《》\n\r\t]+/)
      let positiveScore = 0
      let negativeScore = 0
      let neutralScore = 0
      const positiveWords = []
      const negativeWords = []
      const neutralWords = []
      
      words.forEach((word, index) => {
        const cleanWord = word.trim()
        if (cleanWord.length < 2) return
        
        const prevWord = index > 0 ? words[index - 1].trim() : ''
        const isNegated = this.negationWords.includes(prevWord)
        
        if (this.positiveDict.includes(cleanWord)) {
          if (isNegated) {
            negativeScore += 1
            negativeWords.push('不' + cleanWord)
          } else {
            positiveScore += 1
            positiveWords.push(cleanWord)
          }
        } else if (this.negativeDict.includes(cleanWord)) {
          if (isNegated) {
            positiveScore += 0.5
            positiveWords.push('不' + cleanWord)
          } else {
            negativeScore += 1
            negativeWords.push(cleanWord)
          }
        } else if (this.neutralDict.includes(cleanWord)) {
          neutralScore += 0.5
          neutralWords.push(cleanWord)
        }
      })
      
      let sentiment = 'neutral'
      if (positiveScore > negativeScore + 0.5) {
        sentiment = 'positive'
      } else if (negativeScore > positiveScore + 0.5) {
        sentiment = 'negative'
      }
      
      return {
        sentiment,
        positiveScore,
        negativeScore,
        neutralScore,
        positiveWords,
        negativeWords,
        neutralWords,
        text: comment
      }
    },
    
    initCharts() {
      this.initSentimentPieChart()
      this.initSentimentTrendChart()
      this.initTopicRadarChart()
      this.initTopicBarChart()
      this.initSentimentRadarChart()
      this.initTopicNetworkChart()
      this.initSankeyChart()
      this.initTreemapChart()
      
      this.$nextTick(() => {
        const mainContent = document.querySelector('.main-content')
        if (mainContent) {
          this.resizeObserver.observe(mainContent)
        }
        
        const leftSection = document.querySelector('.left-section')
        if (leftSection) {
          this.resizeObserver.observe(leftSection)
        }
        
        const rightSection = document.querySelector('.right-section')
        if (rightSection) {
          this.resizeObserver.observe(rightSection)
        }
        
        const chartContainers = [
          this.$refs.sentimentPieChart,
          this.$refs.sentimentTrendChart,
          this.$refs.topicRadarChart,
          this.$refs.topicBarChart,
          this.$refs.sentimentRadarChart,
          this.$refs.topicNetworkChart,
          this.$refs.sankeyChart,
          this.$refs.treemapChart
        ].filter(el => el)
        
        chartContainers.forEach(el => {
          this.resizeObserver.observe(el)
        })
      })
    },
    
    initSentimentPieChart() {
      if (!this.$refs.sentimentPieChart) return
      
      this.sentimentPieChart = echarts.init(this.$refs.sentimentPieChart)
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}条 ({d}%)',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: {
            color: '#1f2937',
            fontSize: 14
          },
          padding: [10, 15],
          extraCssText: 'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);'
        },
        legend: {
          orient: 'horizontal',
          bottom: '5%',
          left: 'center',
          textStyle: {
            color: '#6b7280',
            fontSize: 12
          },
          itemWidth: 12,
          itemHeight: 12,
          itemGap: 20
        },
        series: [
          {
            name: '情感分布',
            type: 'pie',
            radius: ['45%', '70%'],
            center: ['50%', '45%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 8,
              borderColor: '#fff',
              borderWidth: 3
            },
            label: {
              show: true,
              position: 'center',
              formatter: () => {
                return `{a|${this.sentimentStats.positivePercent}%}\n{b|好评率}`
              },
              rich: {
                a: {
                  fontSize: 28,
                  fontWeight: 'bold',
                  color: '#10b981'
                },
                b: {
                  fontSize: 14,
                  color: '#6b7280',
                  padding: [5, 0, 0, 0]
                }
              }
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 16,
                fontWeight: 'bold'
              },
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.2)'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              { 
                value: this.sentimentStats.positive, 
                name: '正面评价',
                itemStyle: { 
                  color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                    { offset: 0, color: '#10b981' },
                    { offset: 1, color: '#059669' }
                  ])
                }
              },
              { 
                value: this.sentimentStats.neutral, 
                name: '中性评价',
                itemStyle: { 
                  color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                    { offset: 0, color: '#6b7280' },
                    { offset: 1, color: '#4b5563' }
                  ])
                }
              },
              { 
                value: this.sentimentStats.negative, 
                name: '负面评价',
                itemStyle: { 
                  color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                    { offset: 0, color: '#ef4444' },
                    { offset: 1, color: '#dc2626' }
                  ])
                }
              }
            ]
          }
        ]
      }
      
      this.sentimentPieChart.setOption(option)
    },
    
    initSentimentTrendChart() {
      if (!this.$refs.sentimentTrendChart) return
      
      this.sentimentTrendChart = echarts.init(this.$refs.sentimentTrendChart)
      
      const trendData = this.calculateTrendData()
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: {
            color: '#1f2937',
            fontSize: 13
          },
          padding: [10, 15],
          extraCssText: 'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          }
        },
        legend: {
          data: ['正面评价', '负面评价', '中性评价'],
          top: 5,
          right: 10,
          textStyle: {
            color: '#6b7280',
            fontSize: 11
          },
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 12
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
          data: trendData.dates,
          axisLine: {
            lineStyle: { color: '#e5e7eb' }
          },
          axisLabel: {
            color: '#6b7280',
            fontSize: 11
          }
        },
        yAxis: {
          type: 'value',
          axisLine: {
            show: false
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(0, 0, 0, 0.05)',
              type: 'dashed'
            }
          },
          axisLabel: {
            color: '#6b7280',
            fontSize: 11
          }
        },
        series: [
          {
            name: '正面评价',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            data: trendData.positive,
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
                { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
              ])
            }
          },
          {
            name: '负面评价',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            data: trendData.negative,
            lineStyle: {
              width: 3,
              color: '#ef4444'
            },
            itemStyle: {
              color: '#ef4444',
              borderWidth: 2,
              borderColor: '#fff'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
                { offset: 1, color: 'rgba(239, 68, 68, 0.05)' }
              ])
            }
          },
          {
            name: '中性评价',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            data: trendData.neutral,
            lineStyle: {
              width: 2,
              color: '#6b7280',
              type: 'dashed'
            },
            itemStyle: {
              color: '#6b7280',
              borderWidth: 2,
              borderColor: '#fff'
            }
          }
        ]
      }
      
      this.sentimentTrendChart.setOption(option)
    },
    
    calculateTrendData() {
      const groupSize = Math.ceil(this.sentimentResults.length / 7) || 1
      const dates = []
      const positive = []
      const negative = []
      const neutral = []
      
      for (let i = 0; i < 7; i++) {
        const start = i * groupSize
        const end = Math.min(start + groupSize, this.sentimentResults.length)
        const group = this.sentimentResults.slice(start, end)
        
        dates.push(`第${i + 1}期`)
        positive.push(group.filter(r => r.sentiment === 'positive').length)
        negative.push(group.filter(r => r.sentiment === 'negative').length)
        neutral.push(group.filter(r => r.sentiment === 'neutral').length)
        
        if (end >= this.sentimentResults.length) break
      }
      
      while (dates.length < 7) {
        dates.push(`第${dates.length + 1}期`)
        positive.push(0)
        negative.push(0)
        neutral.push(0)
      }
      
      return { dates, positive, negative, neutral }
    },
    
    initTopicRadarChart() {
      if (!this.$refs.topicRadarChart) return
      
      this.topicRadarChart = echarts.init(this.$refs.topicRadarChart)
      
      const topics = this.topicStats.slice(0, 6)
      const indicator = topics.map(t => ({
        name: t.name,
        max: Math.max(...topics.map(t => t.count)) * 1.2
      }))
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#1f2937', fontSize: 13 },
          padding: [10, 15]
        },
        radar: {
          indicator: indicator,
          shape: 'polygon',
          splitNumber: 4,
          axisName: {
            color: '#6b7280',
            fontSize: 11,
            fontWeight: 500
          },
          splitLine: {
            lineStyle: { color: 'rgba(0, 0, 0, 0.08)' }
          },
          splitArea: {
            show: true,
            areaStyle: {
              color: ['rgba(52, 152, 219, 0.05)', 'rgba(52, 152, 219, 0.1)', 
                      'rgba(52, 152, 219, 0.05)', 'rgba(52, 152, 219, 0.1)']
            }
          },
          axisLine: {
            lineStyle: { color: 'rgba(0, 0, 0, 0.1)' }
          }
        },
        series: [{
          type: 'radar',
          data: [
            {
              value: topics.map(t => t.count),
              name: '评价数量',
              symbol: 'circle',
              symbolSize: 6,
              lineStyle: {
                width: 2,
                color: '#3498db'
              },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(52, 152, 219, 0.4)' },
                  { offset: 1, color: 'rgba(52, 152, 219, 0.1)' }
                ])
              },
              itemStyle: {
                color: '#3498db',
                borderColor: '#fff',
                borderWidth: 2
              }
            }
          ]
        }]
      }
      
      this.topicRadarChart.setOption(option)
    },
    
    initTopicBarChart() {
      if (!this.$refs.topicBarChart) return
      
      this.topicBarChart = echarts.init(this.$refs.topicBarChart)
      
      const topics = this.topicStats.slice(0, 8)
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#1f2937', fontSize: 13 },
          padding: [10, 15]
        },
        legend: {
          data: ['正面', '中性', '负面'],
          top: 5,
          right: 10,
          textStyle: { color: '#6b7280', fontSize: 11 },
          itemWidth: 10,
          itemHeight: 10
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
          data: topics.map(t => t.name),
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisLabel: { 
            color: '#6b7280', 
            fontSize: 10,
            interval: 0,

          }
        },
        yAxis: {
          type: 'value',
          axisLine: { show: false },
          splitLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.05)', type: 'dashed' } },
          axisLabel: { color: '#6b7280', fontSize: 11 }
        },
        series: [
          {
            name: '正面',
            type: 'bar',
            stack: 'total',
            data: topics.map(t => t.positive),
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#10b981' },
                { offset: 1, color: '#059669' }
              ]),
              borderRadius: [0, 0, 0, 0]
            },
            barWidth: '40%'
          },
          {
            name: '中性',
            type: 'bar',
            stack: 'total',
            data: topics.map(t => t.neutral),
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#6b7280' },
                { offset: 1, color: '#4b5563' }
              ]),
              borderRadius: [0, 0, 0, 0]
            }
          },
          {
            name: '负面',
            type: 'bar',
            stack: 'total',
            data: topics.map(t => t.negative),
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#ef4444' },
                { offset: 1, color: '#dc2626' }
              ]),
              borderRadius: [4, 4, 0, 0]
            }
          }
        ]
      }
      
      this.topicBarChart.setOption(option)
    },
    
    initSentimentRadarChart() {
      if (!this.$refs.sentimentRadarChart) return
      
      this.sentimentRadarChart = echarts.init(this.$refs.sentimentRadarChart)
      
      const dimensions = [
        { name: '满意度', max: 100 },
        { name: '推荐度', max: 100 },
        { name: '信任度', max: 100 },
        { name: '体验感', max: 100 },
        { name: '性价比', max: 100 },
        { name: '服务感', max: 100 }
      ]
      
      const positiveScore = Math.min(100, this.sentimentStats.positivePercent * 1.2)
      const negativeScore = Math.min(100, this.sentimentStats.negativePercent * 1.5)
      const neutralScore = Math.min(100, this.sentimentStats.neutralPercent * 1.0)
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#1f2937', fontSize: 13 },
          padding: [10, 15]
        },
        legend: {
          data: ['正面情感', '负面情感', '中性情感'],
          bottom: 5,
          textStyle: { color: '#6b7280', fontSize: 11 },
          itemWidth: 10,
          itemHeight: 10
        },
        radar: {
          indicator: dimensions,
          shape: 'polygon',
          splitNumber: 4,
          center: ['50%', '45%'],
          radius: '60%',
          axisName: {
            color: '#374151',
            fontSize: 11,
            fontWeight: 500
          },
          splitLine: {
            lineStyle: { color: 'rgba(0, 0, 0, 0.08)' }
          },
          splitArea: {
            show: true,
            areaStyle: {
              color: ['rgba(16, 185, 129, 0.05)', 'rgba(16, 185, 129, 0.1)', 
                      'rgba(16, 185, 129, 0.05)', 'rgba(16, 185, 129, 0.1)']
            }
          },
          axisLine: {
            lineStyle: { color: 'rgba(0, 0, 0, 0.1)' }
          }
        },
        series: [{
          type: 'radar',
          data: [
            {
              value: [positiveScore, positiveScore * 0.9, positiveScore * 0.85, 
                      positiveScore * 0.95, positiveScore * 0.8, positiveScore * 0.88],
              name: '正面情感',
              symbol: 'circle',
              symbolSize: 5,
              lineStyle: { width: 2, color: '#10b981' },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(16, 185, 129, 0.4)' },
                  { offset: 1, color: 'rgba(16, 185, 129, 0.1)' }
                ])
              },
              itemStyle: { color: '#10b981', borderColor: '#fff', borderWidth: 2 }
            },
            {
              value: [negativeScore, negativeScore * 0.8, negativeScore * 0.9, 
                      negativeScore * 0.85, negativeScore * 0.95, negativeScore * 0.75],
              name: '负面情感',
              symbol: 'circle',
              symbolSize: 5,
              lineStyle: { width: 2, color: '#ef4444' },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(239, 68, 68, 0.4)' },
                  { offset: 1, color: 'rgba(239, 68, 68, 0.1)' }
                ])
              },
              itemStyle: { color: '#ef4444', borderColor: '#fff', borderWidth: 2 }
            },
            {
              value: [neutralScore, neutralScore * 0.85, neutralScore * 0.9, 
                      neutralScore * 0.88, neutralScore * 0.82, neutralScore * 0.9],
              name: '中性情感',
              symbol: 'circle',
              symbolSize: 5,
              lineStyle: { width: 2, color: '#6b7280', type: 'dashed' },
              areaStyle: { color: 'rgba(107, 114, 128, 0.1)' },
              itemStyle: { color: '#6b7280', borderColor: '#fff', borderWidth: 2 }
            }
          ]
        }]
      }
      
      this.sentimentRadarChart.setOption(option)
    },
    
    initTopicNetworkChart() {
      if (!this.$refs.topicNetworkChart) return
      
      this.topicNetworkChart = echarts.init(this.$refs.topicNetworkChart)
      
      const topics = this.topicStats.slice(0, 6)
      const nodes = topics.map((t, i) => ({
        name: t.name,
        value: t.count,
        symbolSize: Math.max(30, Math.min(60, t.count / 2)),
        category: i,
        itemStyle: {
          color: ['#3498db', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4'][i]
        }
      }))
      
      const links = []
      for (let i = 0; i < topics.length; i++) {
        for (let j = i + 1; j < topics.length; j++) {
          const commonKeywords = topics[i].keywords.filter(k => topics[j].keywords.includes(k))
          if (commonKeywords.length > 0) {
            links.push({
              source: topics[i].name,
              target: topics[j].name,
              value: commonKeywords.length,
              lineStyle: {
                width: Math.min(5, commonKeywords.length),
                color: 'rgba(100, 100, 100, 0.3)',
                curveness: 0.2
              }
            })
          }
        }
      }
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#1f2937', fontSize: 13 },
          padding: [10, 15],
          formatter: (params) => {
            if (params.dataType === 'node') {
              return `${params.name}<br/>评价数: ${params.value}`
            } else {
              return `${params.data.source} → ${params.data.target}<br/>关联强度: ${params.data.value}`
            }
          }
        },
        series: [{
          type: 'graph',
          layout: 'force',
          animation: true,
          animationDuration: 1500,
          data: nodes,
          links: links,
          categories: topics.map((t, i) => ({ name: t.name })),
          roam: true,
          label: {
            show: true,
            position: 'inside',
            fontSize: 10,
            color: '#fff',
            fontWeight: 'bold'
          },
          force: {
            repulsion: 200,
            gravity: 0.1,
            edgeLength: [80, 150],
            layoutAnimation: true
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: { width: 4 }
          }
        }]
      }
      
      this.topicNetworkChart.setOption(option)
    },
    
    initSankeyChart() {
      if (!this.$refs.sankeyChart) return
      
      this.sankeyChart = echarts.init(this.$refs.sankeyChart)
      
      const topics = this.topicStats.slice(0, 5)
      const nodes = []
      const links = []
      
      const topicColors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4']
      const sentimentColors = {
        '正面评价': '#10b981',
        '中性评价': '#64748b',
        '负面评价': '#ef4444'
      }
      
      topics.forEach((t, index) => {
        nodes.push({ 
          name: t.name, 
          depth: 0,
          itemStyle: {
            color: topicColors[index]
          }
        })
      })
      
      nodes.push({ 
        name: '正面评价', 
        depth: 1,
        itemStyle: { color: sentimentColors['正面评价'] }
      })
      nodes.push({ 
        name: '中性评价', 
        depth: 1,
        itemStyle: { color: sentimentColors['中性评价'] }
      })
      nodes.push({ 
        name: '负面评价', 
        depth: 1,
        itemStyle: { color: sentimentColors['负面评价'] }
      })
      
      topics.forEach((t, index) => {
        if (t.positive > 0) {
          links.push({
            source: t.name,
            target: '正面评价',
            value: t.positive,
            lineStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 1, y2: 0,
                colorStops: [
                  { offset: 0, color: topicColors[index] },
                  { offset: 1, color: sentimentColors['正面评价'] }
                ]
              }
            }
          })
        }
        if (t.neutral > 0) {
          links.push({
            source: t.name,
            target: '中性评价',
            value: t.neutral,
            lineStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 1, y2: 0,
                colorStops: [
                  { offset: 0, color: topicColors[index] },
                  { offset: 1, color: sentimentColors['中性评价'] }
                ]
              }
            }
          })
        }
        if (t.negative > 0) {
          links.push({
            source: t.name,
            target: '负面评价',
            value: t.negative,
            lineStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 1, y2: 0,
                colorStops: [
                  { offset: 0, color: topicColors[index] },
                  { offset: 1, color: sentimentColors['负面评价'] }
                ]
              }
            }
          })
        }
      })
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          triggerOn: 'mousemove',
          backgroundColor: 'rgba(255, 255, 255, 0.98)',
          borderColor: '#e2e8f0',
          borderWidth: 1,
          borderRadius: 8,
          textStyle: { 
            color: '#334155', 
            fontSize: 13,
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          },
          padding: [12, 16],
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          formatter: (params) => {
            if (params.dataType === 'node') {
              return `<div style="font-weight: 600; margin-bottom: 4px;">${params.name}</div>`
            } else {
              return `<div style="font-weight: 500;">${params.data.source} → ${params.data.target}</div>
                      <div style="color: #64748b; margin-top: 4px;">评价数量: <span style="font-weight: 600; color: #334155;">${params.data.value}</span></div>`
            }
          }
        },
        series: [{
          type: 'sankey',
          layout: 'none',
          emphasis: { 
            focus: 'adjacency',
            blurScope: 'coordinateSystem'
          },
          nodeAlign: 'justify',
          nodeWidth: 24,
          nodeGap: 16,
          layoutIterations: 32,
          lineStyle: {
            curveness: 0.6,
            opacity: 0.35
          },
          label: {
            position: 'right',
            fontSize: 12,
            fontWeight: 500,
            color: '#475569',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          },
          data: nodes,
          links: links,
          itemStyle: {
            borderWidth: 0,
            borderRadius: 4
          }
        }]
      }
      
      this.sankeyChart.setOption(option)
    },
    
    initTreemapChart() {
      if (!this.$refs.treemapChart) return
      
      this.treemapChart = echarts.init(this.$refs.treemapChart)
      
      const topics = this.topicStats.slice(0, 8)
      const colors = [
        '#3498db', '#10b981', '#f59e0b', '#8b5cf6', 
        '#F0EFC2', '#06b6d4', '#EDA4A4', '#84cc16'
      ]
      
      const data = topics.map((t, i) => {
        const keywordData = t.keywords.slice(0, 12).map((kw, idx) => {
          let actualCount = 0
          if (t.commentIndices) {
            t.commentIndices.forEach(idx => {
              const comment = this.rawComments[idx]
              if (comment && comment.content && this.containsKeyword(comment.content, kw)) {
                actualCount++
              }
            })
          }
          return {
            name: kw,
            value: actualCount,
            topicName: t.name
          }
        })
        
        return {
          name: t.name,
          value: t.count,
          children: keywordData,
          itemStyle: {
            color: colors[i % colors.length]
          }
        }
      })
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#1f2937', fontSize: 13 },
          padding: [10, 15],
          confine: true,
          formatter: (params) => {
            const treePath = params.treePath
            if (treePath && treePath.length > 1) {
              return `<strong>${treePath[treePath.length - 2]}</strong><br/>${params.name}: ${params.value}条`
            }
            return `<strong>${params.name}</strong><br/>评价数: ${params.value}`
          }
        },
        series: [{
          type: 'treemap',
          width: '96%',
          height: '100%',
          top: '0%',
          left: '2%',
          right: '2%',
          bottom: '4%',
          roam: false,
          nodeClick: false,
          breadcrumb: {
            show: false
          },
          label: {
            show: true,
            formatter: '{b}',
            fontSize: 11,
            color: '#fff',
            ellipsis: true
          },
          upperLabel: {
            show: true,
            height: 28,
            fontSize: 12,
            fontWeight: 'bold',
            color: '#fff'
          },
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 2,
            gapWidth: 2,
            borderColorSaturation: 0.6
          },
          levels: [{
            itemStyle: {
              borderWidth: 0,
              borderColor: '#fff',
              gapWidth: 2
            },
            upperLabel: { 
              show: true,
              height: 28
            }
          }, {
            colorSaturation: [0.35, 0.65],
            colorAlpha: [0.7, 1],
            itemStyle: {
              borderWidth: 1,
              borderColor: '#fff',
              borderColorSaturation: 0.6,
              gapWidth: 1
            },
            label: {
              fontSize: 10
            }
          }],
          data: data
        }]
      }
      
      this.treemapChart.setOption(option)
      
      this.treemapChart.off('click')
      this.treemapChart.on('click', (params) => {
        if (params.data) {
          if (params.data.children) {
            this.showTopicComments({ name: params.data.name, commentIndices: this.topicStats.find(t => t.name === params.data.name)?.commentIndices || [] })
          } else {
            const keyword = params.data.name
            const topicName = params.data.topicName || null
            this.showKeywordComments(keyword, topicName)
          }
        }
      })
    },
    
    showKeywordComments(keyword, topicName, sentimentType) {
      this.selectedKeyword = keyword
      this.keywordComments = []
      
      if (topicName) {
        const topic = this.topicStats.find(t => t.name === topicName)
        if (topic && topic.commentIndices) {
          topic.commentIndices.forEach(idx => {
            const comment = this.rawComments[idx]
            if (comment && comment.content && this.containsKeyword(comment.content, keyword)) {
              this.keywordComments.push({
                content: comment.content,
                score: comment.score,
                sentiment: comment.sentiment
              })
            }
          })
        }
      } else {
        this.rawComments.forEach(comment => {
          if (comment.content && this.containsKeyword(comment.content, keyword)) {
            this.keywordComments.push({
              content: comment.content,
              score: comment.score,
              sentiment: comment.sentiment
            })
          }
        })
      }
      
      this.keywordCommentsTotal = this.keywordComments.length
      this.showKeywordModal = true
    },
    
    getKeywordSentiment(keyword) {
      if (this.negativeWords.some(w => w.name === keyword)) {
        return 'negative'
      } else if (this.neutralWords.some(w => w.name === keyword)) {
        return 'neutral'
      } else if (this.positiveWords.some(w => w.name === keyword)) {
        return 'positive'
      }
      return null
    },
    
    closeKeywordModal() {
      this.showKeywordModal = false
      this.selectedKeyword = null
      this.keywordComments = []
    },
    
    showSentimentComments(sentimentType) {
      this.selectedKeyword = sentimentType === 'positive' ? '正面评价' : 
                             sentimentType === 'negative' ? '负面评价' : '中性评价'
      this.keywordComments = []
      
      this.rawComments.forEach(comment => {
        if (comment.content) {
          const score = comment.score
          let match = false
          
          if (sentimentType === 'positive' && score > 3) {
            match = true
          } else if (sentimentType === 'negative' && score < 3) {
            match = true
          } else if (sentimentType === 'neutral' && score === 3) {
            match = true
          }
          
          if (match) {
            this.keywordComments.push({
              content: comment.content,
              score: comment.score,
              sentiment: comment.sentiment
            })
          }
        }
      })
      
      this.keywordCommentsTotal = this.keywordComments.length
      this.showKeywordModal = true
    },
    
    showTopicComments(topic) {
      this.selectedTopic = topic
      this.topicComments = []
      
      if (topic.commentIndices && topic.commentIndices.length > 0) {
        topic.commentIndices.forEach(idx => {
          const comment = this.rawComments[idx]
          if (comment && comment.content) {
            this.topicComments.push({
              content: comment.content,
              score: comment.score,
              sentiment: comment.sentiment
            })
          }
        })
      } else {
        const topicKeywords = this.topicKeywords[topic.name]?.keywords || []
        
        this.rawComments.forEach((comment, index) => {
          if (comment.content) {
            let bestTopic = null
            let bestScore = 0
            
            Object.keys(this.topicKeywords).forEach(topicName => {
              const keywords = this.topicKeywords[topicName].keywords
              let score = 0
              
              keywords.forEach(keyword => {
                if (this.containsKeyword(comment.content, keyword)) {
                  score++
                }
              })
              
              if (score > bestScore) {
                bestScore = score
                bestTopic = topicName
              }
            })
            
            if (bestTopic === topic.name && bestScore > 0) {
              this.topicComments.push({
                content: comment.content,
                score: comment.score,
                sentiment: comment.sentiment
              })
            }
          }
        })
      }
      
      this.showTopicModal = true
    },
    
    closeTopicModal() {
      this.showTopicModal = false
      this.selectedTopic = null
      this.topicComments = []
    },
    
    showFeaturedComments() {
      this.selectedTopic = {
        name: '精选评论',
        icon: 'fas fa-star'
      }
      this.topicComments = this.rawComments
        .filter(item => item.content && item.content.length > 60)
        .sort((a, b) => {
          if (a.sentiment === 'positive' && b.sentiment !== 'positive') return -1;
          if (a.sentiment !== 'positive' && b.sentiment === 'positive') return 1;
          return b.content.length - a.content.length;
        })
        .map(item => ({
          content: item.content,
          score: item.score,
          sentiment: item.sentiment
        }))
      this.showTopicModal = true
    },
    
    getSentimentLabel(sentiment) {
      const labels = {
        positive: '好评',
        neutral: '中评',
        negative: '差评'
      }
      return labels[sentiment] || '中评'
    },
    
    getSentimentClass(sentiment) {
      return sentiment || 'neutral'
    },
    
    handleResize() {
      if (this.resizeTimer) {
        clearTimeout(this.resizeTimer)
      }
      this.resizeTimer = setTimeout(() => {
        const charts = [
          this.sentimentPieChart,
          this.sentimentTrendChart,
          this.topicRadarChart,
          this.topicBarChart,
          this.sentimentRadarChart,
          this.topicNetworkChart,
          this.sankeyChart,
          this.treemapChart
        ]
        charts.forEach(chart => {
          if (chart) {
            try {
              chart.resize({
                width: 'auto',
                height: 'auto'
              })
            } catch (e) {
              console.warn('Chart resize error:', e)
            }
          }
        })
      }, 150)
    },
    
    containsKeyword(text, keyword) {
      const regex = new RegExp(keyword, 'g')
      return regex.test(text)
    },
    
    getTagSize(value, type) {
      let words
      if (type === 'positive') {
        words = this.positiveWords
      } else if (type === 'negative') {
        words = this.negativeWords
      } else {
        words = this.neutralWords
      }
      
      if (!words || words.length === 0) return 12
      
      const max = words[0]?.value || 1
      const min = words[words.length - 1]?.value || 1
      
      const minSize = 12
      const maxSize = 24
      
      if (max === min) return (maxSize + minSize) / 2
      
      const percent = (value - min) / (max - min)
      const scale = Math.pow(percent, 0.5)
      
      return minSize + scale * (maxSize - minSize)
    },
    

    getWordFontSize(value) {
      const max = this.wordData[0]?.value || 1;
      const min = this.wordData[Math.min(this.wordData.length - 1, 79)]?.value || 1;
      
      // 紧凑型词云的字号区间建议不要拉得太大
      const minSize = 12; // 最小字号不能太小，否则留白多
      const maxSize = 42; // 最大字号适中
      
      if (max === min) return (maxSize + minSize) / 2;
      
      // 使用 Math.pow(x, 0.7) 这种非线性缩放
      // 它的作用是让中等频次的词也变大一点，填充掉大词周围的空隙
      const percent = (value - min) / (max - min);
      const scale = Math.pow(percent, 0.7); 
      
      return minSize + scale * (maxSize - minSize);
    },
    
    getWordOpacity(index) {
      if (index < 15) return 1;
      if (index < 40) return 0.85;
      if (index < 60) return 0.7;
      return 0.55;
    },

    getWordColor(index) {
      const palette = [
        '#1890ff',
        '#096dd9',
        '#0050b3',
        '#2f54eb',
        '#1d39c4',
        '#597ef7',
        '#5b8ff9',
        '#61ddff'
      ];
      return palette[index % palette.length];
    },
    
    getWordStyle(word, index) {
      const fontSize = this.getWordFontSize(word.value);
      // 排名越靠后，颜色越浅，透明度越低，形成一种“文字底纹”的密集感
      const opacity = index < 20 ? 1 : index < 50 ? 0.7 : 0.4;
      
      return {
        fontSize: `${fontSize}px`,
        color: this.getWordColor(index),
        opacity: opacity,
        // 增加一个微小的旋转（可选），只给 5% 的词
        transform: index > 40 && index % 15 === 0 ? 'rotate(90deg)' : 'none'
      };
    },

    getWordStyle(word, index) {
      const total = this.wordData.length
      const frequencyRank = index / total
      
      const phi = Math.acos(1 - 2 * (index + 0.5) / total)
      const theta = Math.sqrt(total * Math.PI) * phi
      
      const baseRadius = 230
      const radiusOffset = frequencyRank * 50
      const radius = baseRadius - radiusOffset
      
      const x = radius * Math.cos(theta) * Math.sin(phi)
      const y = radius * Math.sin(theta) * Math.sin(phi)
      const z = radius * Math.cos(phi) + (1 - frequencyRank) * 80
      
      const colors = [
        '#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#9b59b6',
        '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b',
        '#27ae60', '#d35400', '#2980b9', '#8e44ad', '#f1c40f'
      ]
      const color = colors[index % colors.length]
      
      const maxZ = baseRadius + 80
      const minZ = -baseRadius
      const normalizedZ = (z - minZ) / (maxZ - minZ)
      const scale = 0.65 + 0.5 * normalizedZ
      const blur = Math.max(0, (1 - normalizedZ) * 0.6)
      
      return {
        transform: `translate3d(${x}px, ${y}px, ${z}px) scale(${scale}) rotateY(${this.rotationAngle}deg)`,
        fontSize: `${word.size}px`,
        color: color,
        opacity: this.getOpacity(z, maxZ, minZ),
        zIndex: Math.round(z + baseRadius + 100),
        textShadow: `0 2px 4px rgba(0,0,0,${0.1 + normalizedZ * 0.2})`,
        filter: blur > 0.05 ? `blur(${blur}px)` : 'none'
      }
    },
    
    getOpacity(z, maxZ, minZ) {
      const normalizedZ = (z - minZ) / (maxZ - minZ)
      return 0.45 + 0.55 * normalizedZ
    },
    
    getBarWidth(value) {
      const max = this.wordData[0] ? this.wordData[0].value : 1
      return `${(value / max) * 100}%`
    },
    
    startRotation() {
      if (this.rotationInterval) return
      this.rotationInterval = setInterval(() => {
        if (this.isRotating) {
          this.rotationAngle += 0.5
        }
      }, 30)
    },
    
    stopRotation() {
      if (this.rotationInterval) {
        clearInterval(this.rotationInterval)
        this.rotationInterval = null
      }
    },
    
    toggleRotation() {
      this.isRotating = !this.isRotating
    },
    
    toggleStatic() {
      this.isStatic = !this.isStatic
      if (this.isStatic) {
        this.rotationAngle = 0
        this.isRotating = false
      } else {
        this.isRotating = true
      }
    },
    
    resetView() {
      this.rotationAngle = 0
      this.isRotating = true
      this.isStatic = false
    },
    
    highlightWord(index) {
      this.hoveredWord = this.wordData[index]
    },
    
    unhighlightWord() {
      this.hoveredWord = null
    }
  }
}
</script>

<style scoped>
.comment-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
  box-sizing: border-box;
}

.header-section {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px 30px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  gap: 20px;
}

.header-left {
  display: flex;
  flex-direction: column;
  margin-right: auto;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.page-subtitle {
  margin: 5px 0 0 0;
  font-size: 14px;
  color: #666;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-stats {
  display: flex;
  gap: 30px;
  margin-left: 15px;
}

.header-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.header-stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #3498db;
}

.header-stat-value.positive {
  color: #10b981;
}

.header-stat-value.topic {
  color: #8b5cf6;
}

.header-stat-label {
  font-size: 12px;
  color: #6b7280;
}

.sentiment-overview {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  min-width: 0;
}

.sentiment-card {
  flex: 1;
  min-width: 0;
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  position: relative;
}

.sentiment-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.sentiment-card.positive {
  border-top: 3px solid #10b981;
}

.sentiment-card.neutral {
  border-top: 3px solid #6b7280;
}

.sentiment-card.negative {
  border-top: 3px solid #ef4444;
}

.sentiment-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.sentiment-card.positive .sentiment-icon {
  background: #ecfdf5;
  color: #10b981;
}

.sentiment-card.neutral .sentiment-icon {
  background: #f3f4f6;
  color: #6b7280;
}

.sentiment-card.negative .sentiment-icon {
  background: #fef2f2;
  color: #ef4444;
}

.sentiment-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 2px;
}

.sentiment-count {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}

.sentiment-label {
  font-size: 13px;
  color: #6b7280;
}

.sentiment-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: #f3f4f6;
}

.sentiment-bar-fill {
  height: 100%;
  transition: width 0.5s ease;
}

.sentiment-card.positive .sentiment-bar-fill {
  background: #10b981;
}

.sentiment-card.neutral .sentiment-bar-fill {
  background: #6b7280;
}

.sentiment-card.negative .sentiment-bar-fill {
  background: #ef4444;
}

.topic-clustering-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.topic-clustering-section .main-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e5e7eb;
}

.topic-clustering-section .main-header .section-title {
  font-size: 18px;
  color: #1f2937;
}

.topic-clustering-section .main-header .section-title i {
  color: #8b5cf6;
  margin-right: 8px;
}

.topic-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.topic-charts-row {
  display: flex;
  gap: 20px;
  min-width: 0;
}

.topic-radar-section,
.topic-bars-section {
  flex: 1;
  min-width: 0;
}

.radar-chart {
  height: 280px;
}

.bar-chart {
  height: 250px;
}

.topic-details-section {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 10px;
  min-width: 0;
}

.topic-detail-card {
  padding: 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  border-left: 4px solid;
  cursor: pointer;
}

.topic-detail-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.topic-detail-card.topic-1 {
  border-left-color: #3498db;
}

.topic-detail-card.topic-2 {
  border-left-color: #10b981;
}

.topic-detail-card.topic-3 {
  border-left-color: #f59e0b;
}

.topic-detail-card.topic-4 {
  border-left-color: #8b5cf6;
}

.topic-detail-card.topic-5 {
  border-left-color: #ef4444;
}

.topic-detail-card.topic-6 {
  border-left-color: #06b6d4;
}

.topic-detail-card.topic-7 {
  border-left-color: #ec4899;
}

.topic-detail-card.topic-8 {
  border-left-color: #84cc16;
}

.topic-detail-card.topic-featured {
  border-left-color: #f59e0b;
}

.topic-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.topic-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: white;
}

.topic-1 .topic-icon { background: linear-gradient(135deg, #3498db, #2980b9); }
.topic-2 .topic-icon { background: linear-gradient(135deg, #10b981, #059669); }
.topic-3 .topic-icon { background: linear-gradient(135deg, #f59e0b, #d97706); }
.topic-4 .topic-icon { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.topic-5 .topic-icon { background: linear-gradient(135deg, #ef4444, #dc2626); }
.topic-6 .topic-icon { background: linear-gradient(135deg, #06b6d4, #0891b2); }
.topic-7 .topic-icon { background: linear-gradient(135deg, #ec4899, #db2777); }
.topic-8 .topic-icon { background: linear-gradient(135deg, #84cc16, #65a30d); }
.topic-featured .topic-icon { background: linear-gradient(135deg, #f59e0b, #d97706); }

.topic-info {
  flex: 1;
}

.topic-name {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.topic-count {
  font-size: 11px;
  color: #6b7280;
}

.topic-percent {
  font-size: 16px;
  font-weight: 700;
  color: #3498db;
}

.topic-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.topic-keyword {
  padding: 2px 6px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 11px;
  color: #4b5563;
}

.topic-sentiment-bar {
  height: 8px;
  display: flex;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.sentiment-segment {
  transition: width 0.5s ease;
}

.sentiment-segment.positive {
  background: #10b981;
}

.sentiment-segment.neutral {
  background: #6b7280;
}

.sentiment-segment.negative {
  background: #ef4444;
}

.topic-sentiment-legend {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.legend-item {
  font-size: 10px;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-item i {
  font-size: 6px;
}

.legend-item.positive i { color: #10b981; }
.legend-item.neutral i { color: #6b7280; }
.legend-item.negative i { color: #ef4444; }

.topic-samples {
  background: #f8fafc;
  border-radius: 6px;
  padding: 8px;
}

.samples-header {
  font-size: 10px;
  color: #6b7280;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.samples-header i {
  color: #9ca3af;
  font-size: 9px;
}

.sample-item {
  padding: 8px 0;
  border-bottom: 1px solid #e5e7eb;
}

.sample-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.sample-text {
  margin: 0 0 4px 0;
  font-size: 12px;
  color: #374151;
  line-height: 1.5;
}

.sample-sentiment {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
}

.sample-sentiment.positive {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.sample-sentiment.negative {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.sample-sentiment.neutral {
  background: rgba(107, 114, 128, 0.1);
  color: #4b5563;
}

.topic-expand-hint {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed #e5e7eb;
  text-align: center;
  font-size: 12px;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.topic-expand-hint i {
  font-size: 11px;
}

.topic-detail-card:hover .topic-expand-hint {
  color: #3b82f6;
}

.sankey-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 20px;
  margin-top: 30px;
  margin-bottom: 20px;
}

.sankey-section .section-header {
  margin-bottom: 16px;
}

.sankey-section .section-title {
  font-size: 16px;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sankey-section .section-title i {
  color: #8b5cf6;
}

.sankey-chart {
  height: 380px;
}

.main-content {
  display: flex;
  gap: 20px;
  width: 100%;
  min-width: 0;
}

.left-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.treemap-card {
  min-height: 480px;
  display: flex;
  flex-direction: column;
}

.treemap-card .section-header {
  flex-shrink: 0;
}

.treemap-chart {
  flex: 1;
  min-height: 400px;
}

.side-by-side-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  min-width: 0;
}

.side-chart {
  height: 260px;
}

.right-section {
  width: 380px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  overflow: visible;
  min-width: 0;
}

.section-header {
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.section-title {
  margin: 0 0 3px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.insight-icon {
  color: #f59e0b;
}

.section-subtitle {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
}

.wordcloud-section {
  min-height: 280px;
}

.wordcloud-image-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 380px;
  background: #fafafa;
  border-radius: 8px;
  overflow: hidden;
}

.wordcloud-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #6b7280;
}

.wordcloud-loading i {
  font-size: 32px;
  color: #3b82f6;
}

.wordcloud-image {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
}

.wordcloud-static {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-content: center;
  gap: 6px 12px; 
  padding: 24px;
  height: 360px;
  background: #fafafa;
  border-radius: 4px;
  overflow: hidden;
  max-width: 900px;
  margin: 0 auto;
}

.static-word-tag {
  display: inline-block;
  line-height: 1.1; 
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  letter-spacing: -0.5px; 
  white-space: nowrap;
  vertical-align: middle;
  position: relative;
}

.static-word-tag:hover {
  transform: scale(1.05);
  z-index: 10;
}

.is-vertical {
  writing-mode: vertical-rl;
  letter-spacing: 0.05em;
}

.wordcloud-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 40px;
}

.wordcloud-3d {
  width: 450px;
  height: 320px;
  position: relative;
  perspective: 1200px;
  perspective-origin: 50% 50%;
  transform-style: preserve-3d;
}

.word-item {
  position: absolute;
  left: 50%;
  top: 50%;
  margin-left: -50px;
  margin-top: -15px;
  cursor: pointer;
  transition: opacity 0.3s ease, filter 0.3s ease;
  font-weight: 600;
  white-space: nowrap;
  user-select: none;
  backface-visibility: visible;
  will-change: opacity, filter;
  animation: shimmer 3s ease-in-out infinite;
}

.word-item.static-mode {
  animation: none;
}

.word-item:nth-child(odd) {
  animation-delay: -1.5s;
}

@keyframes shimmer {
  0%, 100% {
    filter: brightness(1);
  }
  50% {
    filter: brightness(1.3);
  }
}

.word-item:hover {
  z-index: 999 !important;
  filter: brightness(1.5) none !important;
  text-shadow: 
    0 0 10px currentColor,
    0 0 20px currentColor,
    0 0 30px currentColor,
    0 4px 12px rgba(0,0,0,0.4) !important;
  opacity: 1 !important;
}

.wordcloud-controls {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 25px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover {
  background: #2980b9;
}

.btn-gray {
  background: #f0f0f0;
  color: #333;
}

.btn-gray:hover {
  background: #e0e0e0;
}

.wordcloud-comparison {
  min-height: auto;
}

.comparison-container {
  display: flex;
  gap: 20px;
}

.comparison-column {
  flex: 1;
}

.comparison-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 4px;
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.comparison-header:hover {
  transform: translateY(-1px);
}

.positive-header {
  background: rgba(16, 185, 129, 0.08);
  color: #10b981;
}

.positive-header:hover {
  background: rgba(16, 185, 129, 0.15);
}

.neutral-header {
  background: rgba(107, 114, 128, 0.08);
  color: #6b7280;
}

.neutral-header:hover {
  background: rgba(107, 114, 128, 0.15);
}

.negative-header {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}

.negative-header:hover {
  background: rgba(239, 68, 68, 0.15);
}

.comparison-divider {
  width: 1px;
  background: #e5e7eb;
}

.word-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  min-height: auto;
}

.word-tag {
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 400;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 11px;
}

.positive-tag {
  background: rgba(16, 185, 129, 0.06);
  color: #059669;
}

.positive-tag:hover {
  background: rgba(16, 185, 129, 0.12);
}

.neutral-tag {
  background: rgba(107, 114, 128, 0.06);
  color: #4b5563;
}

.neutral-tag:hover {
  background: rgba(107, 114, 128, 0.12);
}

.negative-tag {
  background: rgba(239, 68, 68, 0.06);
  color: #dc2626;
}

.negative-tag:hover {
  background: rgba(239, 68, 68, 0.12);
}

.chart-container {
  width: 100%;
  height: 200px;
  min-width: 0;
}

.sentiment-pie-section .chart-container {
  height: 220px;
}

.sentiment-trend-section .chart-container {
  height: 180px;
}

.top-words-section {
  flex: 1;
}

.top-words-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.top-word-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}

.word-rank {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  border-radius: 4px;
  background: #e5e7eb;
  color: #6b7280;
}

.word-rank.rank-1 {
  background: #f59e0b;
  color: white;
}

.word-rank.rank-2 {
  background: #9ca3af;
  color: white;
}

.word-rank.rank-3 {
  background: #d97706;
  color: white;
}

.word-name {
  width: 55px;
  font-size: 12px;
  color: #333;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.word-bar-wrapper {
  flex: 1;
  height: 6px;
  background: #f3f4f6;
  border-radius: 3px;
  overflow: hidden;
}

.word-bar {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  border-radius: 3px;
  transition: width 0.3s;
}

.word-count {
  width: 45px;
  font-size: 11px;
  color: #6b7280;
  text-align: right;
}

.insight-section {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.insight-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.insight-item {
  padding: 12px;
  background: white;
  border-radius: 6px;
  border-left: 3px solid;
}

.insight-item:has(.positive-label) {
  border-color: #10b981;
}

.insight-item:has(.negative-label) {
  border-color: #ef4444;
}

.insight-item:has(.suggestion-label) {
  border-color: #3b82f6;
}

.insight-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
}

.positive-label {
  color: #059669;
}

.negative-label {
  color: #dc2626;
}

.suggestion-label {
  color: #2563eb;
}

.insight-text {
  margin: 0;
  font-size: 12px;
  color: #4b5563;
  line-height: 1.6;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  text-align: center;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text,
.error-text {
  margin: 0 0 15px 0;
  color: #666;
  font-size: 14px;
}

.error-icon {
  font-size: 48px;
  color: #e74c3c;
  margin-bottom: 15px;
}

.word-tooltip {
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.tooltip-word {
  font-size: 16px;
  font-weight: 600;
  color: #3498db;
}

.tooltip-count {
  font-size: 12px;
  color: #666;
}

@media (max-width: 1400px) {
  .main-content {
    flex-direction: column;
  }
  
  .right-section {
    width: 100%;
    flex-direction: row;
    flex-wrap: wrap;
  }
  
  .right-section .card {
    flex: 1;
    min-width: 300px;
  }
  
  .topic-details-section {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

.keyword-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(2px);
}

.keyword-modal {
  background: #ffffff;
  border-radius: 8px;
  width: 640px;
  max-width: 90%;
  max-height: 80vh;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.modal-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.modal-title i {
  color: #3b82f6;
  font-size: 14px;
}

.modal-count {
  font-size: 12px;
  color: #9ca3af;
  margin-right: 16px;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 14px;
  color: #9ca3af;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.15s ease;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #4b5563;
}

.modal-body {
  padding: 16px 24px 24px;
  max-height: calc(80vh - 60px);
  overflow-y: auto;
  flex: 1;
}

.modal-body::-webkit-scrollbar {
  width: 5px;
}

.modal-body::-webkit-scrollbar-track {
  background: transparent;
}

.modal-body::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: #d1d5db;
}

.no-comments {
  text-align: center;
  color: #9ca3af;
  padding: 48px 0;
  font-size: 13px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.comment-item {
  padding: 14px 16px;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.15s ease;
  position: relative;
}

.comment-item:hover {
  background: #f3f4f6;
}

.comment-item.positive {
  border-left: 3px solid #10b981;
}

.comment-item.negative {
  border-left: 3px solid #ef4444;
}

.comment-item.neutral {
  border-left: 3px solid #6b7280;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.comment-score {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.comment-sentiment {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.comment-sentiment.positive {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.comment-sentiment.negative {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.comment-sentiment.neutral {
  background: rgba(107, 114, 128, 0.1);
  color: #4b5563;
}

.comment-content {
  font-size: 13px;
  color: #374151;
  line-height: 1.7;
  margin: 0;
}

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .header-stats {
    justify-content: center;
  }
  
  .sentiment-overview {
    flex-direction: column;
  }
  
  .topic-charts-row {
    flex-direction: column;
  }
  
  .topic-details-section {
    grid-template-columns: 1fr;
  }
}
</style>
