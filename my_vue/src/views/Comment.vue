<template>
  <div class="comment-container">
    <div class="header-section">
      <h1 class="page-title">试驾评价词云</h1>
      <p class="page-subtitle">基于试驾用户评价内容生成的3D词云展示</p>
    </div>

    <div class="content-section">
      <div class="wordcloud-section">
        <div class="section-header">
          <h2 class="section-title">评价关键词分布</h2>
          <p class="section-subtitle">鼠标悬停查看词频详情</p>
        </div>
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p class="loading-text">正在加载评价数据...</p>
        </div>
        <div v-else-if="error" class="error-container">
          <i class="fas fa-exclamation-circle error-icon"></i>
          <p class="error-text">{{ error }}</p>
          <button class="btn btn-primary" @click="loadComments">重新加载</button>
        </div>
        <div v-else class="wordcloud-wrapper">
          <div class="wordcloud-3d" ref="wordcloudContainer">
            <div 
              v-for="(word, index) in wordData" 
              :key="index"
              class="word-item"
              :class="{ 'static-mode': isStatic }"
              :style="getWordStyle(word, index)"
              @mouseenter="highlightWord(index)"
              @mouseleave="unhighlightWord"
            >
              {{ word.name }}
            </div>
          </div>
          <div class="wordcloud-controls">
            <button class="btn btn-gray" @click="toggleRotation" :disabled="isStatic">
              <i :class="isRotating ? 'fas fa-pause' : 'fas fa-play'"></i>
              {{ isRotating ? '暂停' : '播放' }}
            </button>
            <button class="btn" :class="isStatic ? 'btn-primary' : 'btn-gray'" @click="toggleStatic">
              <i :class="isStatic ? 'fas fa-sync' : 'fas fa-stop'"></i>
              {{ isStatic ? '动态' : '静态' }}
            </button>
            <button class="btn btn-gray" @click="resetView">
              <i class="fas fa-redo"></i>
              重置
            </button>
          </div>
        </div>
      </div>

      <div class="stats-section">
        <div class="section-header">
          <h2 class="section-title">数据统计</h2>
          <p class="section-subtitle">评价数据概览</p>
        </div>
        <div class="stats-cards">
          <div class="stat-card">
            <div class="stat-icon-wrapper">
              <i class="fas fa-comments stat-icon"></i>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ totalComments }}</span>
              <span class="stat-label">评价总数</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon-wrapper">
              <i class="fas fa-font stat-icon"></i>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ wordData.length }}</span>
              <span class="stat-label">关键词数量</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon-wrapper">
              <i class="fas fa-fire stat-icon"></i>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ topWord ? topWord.name : '-' }}</span>
              <span class="stat-label">最热关键词</span>
            </div>
          </div>
        </div>

        <div class="top-words-section">
          <h3 class="subsection-title">热门关键词TOP10</h3>
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
      </div>
    </div>

    <div v-if="hoveredWord" class="word-tooltip">
      <div class="tooltip-content">
        <span class="tooltip-word">{{ hoveredWord.name }}</span>
        <span class="tooltip-count">出现次数: {{ hoveredWord.value }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Comment',
  data() {
    return {
      comments: [],
      wordData: [],
      loading: true,
      error: null,
      isRotating: true,
      isStatic: false,
      rotationAngle: 0,
      rotationInterval: null,
      hoveredWord: null,
      stopWords: [
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
        '自己', '这', '那', '她', '他', '它', '们', '这个', '那个', '什么', '怎么',
        '可以', '可能', '因为', '所以', '但是', '如果', '还是', '或者', '而且',
        '已经', '一下', '一些', '一点', '一直', '一起', '一切', '一边', '一定',
        '比较', '非常', '特别', '真的', '确实', '实在', '相当', '稍微', '过于',
        '觉得', '感觉', '认为', '以为', '知道', '看到', '听到', '想到', '发现',
        '这样', '那样', '怎样', '这么', '那么', '多么', '如何', '为何', '几',
        '站', '经销商', '销售', '顾问', '试驾', '评价', '选择', 'null', 'NaN'
      ]
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
    }
  },
  mounted() {
    this.loadComments()
  },
  beforeDestroy() {
    this.stopRotation()
  },
  methods: {
    async loadComments() {
      this.loading = true
      this.error = null
      try {
        const response = await axios.get('/api/comments')
        this.comments = response.data
        this.processComments()
        this.startRotation()
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
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.page-subtitle {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.content-section {
  display: flex;
  gap: 20px;
}

.wordcloud-section {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  min-width: 500px;
}

.section-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.section-title {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.section-subtitle {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
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

.wordcloud-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 90px;
}

.wordcloud-3d {
  width: 500px;
  height: 500px;
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

.word-item:nth-child(3n) {
  animation-duration: 4s;
}

.word-item:nth-child(4n) {
  animation-delay: -2.5s;
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
  animation: glow-pulse 0.6s ease-in-out infinite alternate;
}

@keyframes glow-pulse {
  0% {
    text-shadow: 
      0 0 10px currentColor,
      0 0 20px currentColor,
      0 0 30px currentColor,
      0 4px 12px rgba(0,0,0,0.4);
  }
  100% {
    text-shadow: 
      0 0 15px currentColor,
      0 0 30px currentColor,
      0 0 45px currentColor,
      0 0 60px currentColor,
      0 4px 12px rgba(0,0,0,0.4);
  }
}

.wordcloud-controls {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 80px;
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

.stats-section {
  width: 350px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.stats-cards {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 25px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 6px;
  transition: all 0.3s;
}

.stat-card:hover {
  background: #f0f0f0;
}

.stat-icon-wrapper {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3498db, #2980b9);
  border-radius: 8px;
}

.stat-icon {
  font-size: 24px;
  color: white;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.top-words-section {
  margin-top: 20px;
}

.subsection-title {
  margin: 0 0 15px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.top-words-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.top-word-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
}

.word-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  border-radius: 4px;
  background: #e0e0e0;
  color: #666;
}

.word-rank.rank-1 {
  background: #f39c12;
  color: white;
}

.word-rank.rank-2 {
  background: #bdc3c7;
  color: white;
}

.word-rank.rank-3 {
  background: #e67e22;
  color: white;
}

.word-name {
  width: 60px;
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

.word-bar-wrapper {
  flex: 1;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.word-bar {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  border-radius: 4px;
  transition: width 0.3s;
}

.word-count {
  width: 50px;
  font-size: 12px;
  color: #666;
  text-align: right;
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
</style>
