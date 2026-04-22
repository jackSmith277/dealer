<template>
  <div class="policy-container">
    <div class="header-section">
      <h1 class="page-title">地方促消费政策展示</h1>
      <div class="header-controls">
        <button class="btn btn-gray" @click="$router.push('/dashboard')">
          <i class="fas fa-arrow-left"></i> 返回
        </button>
      </div>
    </div>

      <!-- 数据统计仪表盘 -->
    <div class="dashboard-section">
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-icon total">
            <i class="fas fa-file-alt"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ totalPolicies }}</span>
            <span class="stat-label">全国政策总数</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon new">
            <i class="fas fa-check-circle"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ activePolicies }}</span>
            <span class="stat-label">有效政策数量</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon expiring">
            <i class="fas fa-globe"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ coveredProvinces }}</span>
            <span class="stat-label">覆盖省份数量</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon cities">
            <i class="fas fa-map-marker-alt"></i>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ coveredCities }}</span>
            <span class="stat-label">覆盖城市数量</span>
          </div>
        </div>
      </div>
    </div>

    <div class="content-section">
      <div class="map-section">
        <div class="map-header">
          <div class="map-header-top">
            <div class="map-header-left">
              <h2 class="section-title">全国政策分布图</h2>
              <p class="section-subtitle">点击省份或输入省份名称查看详细政策信息</p>
            </div>
            <div class="header-controls">
              <button class="btn btn-gray" @click="resetMap">
                <i class="fas fa-redo mr-1"></i>重置地图
              </button>
              <button class="btn btn-gray" @click="exportPolicies">
                <i class="fas fa-download mr-1"></i>导出政策
              </button>
            </div>
          </div>
          
          <div class="province-search">
            <input
              type="text"
              v-model="searchQuery"
              @input="handleSearchInput"
              @focus="showSuggestions = true"
              @blur="hideSuggestions"
              placeholder="输入省份名称..."
              class="search-input"
            />
            <div v-if="showSuggestions && filteredProvinces.length > 0" class="suggestions-list">
              <div
                v-for="province in filteredProvinces"
                :key="province"
                class="suggestion-item"
                @mousedown="selectProvince(province)"
              >
                {{ province }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- 时空动态可视化控制面板 -->
        <div class="time-control-panel" v-if="showTimeControl" :class="{ 'is-time-playing': isTimePlaying }">
          <div class="panel-header">
            <div class="panel-title">
              <i class="fas fa-history"></i>
              <span>政策时空演变</span>
            </div>
            <div class="panel-actions">
              <button class="btn-close" @click="toggleTimeControl" title="关闭">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
          
          <div class="panel-content">
            <!-- 时间轴控制 -->
            <div class="time-axis-section">
              <div class="time-axis-header">
                <div class="time-range">
                  <span class="time-label">时间轴</span>
                  <span class="time-range-value">{{ timeRange.start }} - {{ timeRange.end }}</span>
                </div>
                <div class="time-controls">
                  <button class="btn-control" @click="prevTimePoint" :disabled="currentTimeIndex <= 0" title="上一时间点">
                    <i class="fas fa-chevron-left"></i>
                  </button>
                  <button class="btn-control btn-primary" @click="toggleTimeAnimation" :title="isTimePlaying ? '暂停动画' : '播放动画'">
                    <i class="fas" :class="isTimePlaying ? 'fa-pause' : 'fa-play'"></i>
                  </button>
                  <button class="btn-control" @click="nextTimePoint" :disabled="currentTimeIndex >= timePoints.length - 1" title="下一时间点">
                    <i class="fas fa-chevron-right"></i>
                  </button>
                  <button class="btn-control btn-secondary" @click="resetTimeControl" title="重置">
                    <i class="fas fa-redo"></i>
                  </button>
                </div>
              </div>
              
              <div class="time-slider-container">
                <input
                  type="range"
                  v-model="currentTimeIndex"
                  :min="0"
                  :max="timePoints.length - 1"
                  class="time-slider"
                  @input="updateTimeMap"
                />
                <div class="time-slider-track">
                  <div class="time-slider-progress" :style="{ width: (timePoints.length > 1 ? (currentTimeIndex / (timePoints.length - 1) * 100) : 0) + '%' }"></div>
                </div>
                <div class="time-marks">
                  <div 
                    v-for="(point, index) in filteredTimePoints" 
                    :key="index"
                    class="time-mark"
                    :class="{ active: currentTimeIndex >= getTimeIndex(point) }"
                    :style="{ left: (timePoints.length > 1 ? (getTimeIndex(point) / (timePoints.length - 1) * 100) : 0) + '%' }"
                    :title="point"
                  >
                    <span class="mark-label">{{ point }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 状态信息 -->
            <div class="status-section">
              <div class="status-grid">
                <div class="status-item">
                  <div class="status-label">当前时间</div>
                  <div class="status-value">{{ currentTimePoint || '--' }}</div>
                </div>
                <div class="status-item">
                  <div class="status-label">累计政策</div>
                  <div class="status-value">{{ currentPolicyCount }}</div>
                </div>
                <div class="status-item">
                  <div class="status-label">动画速度</div>
                  <div class="status-select">
                    <select v-model="animationSpeed" class="speed-select">
                      <option value="1000">慢速</option>
                      <option value="500">中速</option>
                      <option value="200">快速</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 时间点指示器 -->
            <div class="time-indicator" v-if="currentTimePoint">
              <div class="indicator-content">
                <i class="fas fa-calendar-alt indicator-icon"></i>
                <div class="indicator-text">
                  <div class="indicator-title">当前展示：{{ currentTimePoint }}</div>
                  <div class="indicator-subtitle">累计 {{ currentPolicyCount }} 项政策</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="map-container">
          <div ref="chinaMap" class="china-map"></div>
          <div class="time-toggle-button">
            <button class="btn-time-toggle" @click="toggleTimeControl" :title="showTimeControl ? '隐藏时间轴' : '显示时间轴'">
              <i class="fas" :class="showTimeControl ? 'fa-clock' : 'fa-history'"></i>
              <span>{{ showTimeControl ? '时间轴' : '时空分析' }}</span>
            </button>
          </div>
          <div class="map-credits">
            <span>审图号：GS（2024）0650号</span>
            <span>数据来源：国家地理信息公共服务平台</span>
          </div>
        </div>
        
        <div class="map-legend">
          <div class="legend-item">
            <span class="legend-color color-1"></span>
            <span class="legend-text">0-5项政策</span>
          </div>
          <div class="legend-item">
            <span class="legend-color color-2"></span>
            <span class="legend-text">6-10项政策</span>
          </div>
          <div class="legend-item">
            <span class="legend-color color-3"></span>
            <span class="legend-text">11-20项政策</span>
          </div>
          <div class="legend-item">
            <span class="legend-color color-4"></span>
            <span class="legend-text">20项以上政策</span>
          </div>
        </div>
      </div>

      <div class="policy-section" v-if="selectedProvince">
        <div class="policy-header">
          <h2 class="section-title">{{ policySectionTitle }}政策详情</h2>
          <p class="section-subtitle">共找到 {{ filteredPolicies.length }} 项政策</p>
          <div class="filter-row">
            <div class="city-search">
              <input
                type="text"
                v-model="citySearchQuery"
                @input="handleCitySearchInput"
                @focus="showCitySuggestions = true"
                @blur="hideCitySuggestions"
                placeholder="输入地级市/自治州名称"
                class="search-input"
              />
              <div v-if="showCitySuggestions && filteredCities.length > 0" class="suggestions-list">
                <div
                  v-for="city in filteredCities"
                  :key="city"
                  class="suggestion-item"
                  @mousedown="selectCity(city)"
                >
                  {{ city }}
                </div>
              </div>
            </div>
            <div class="category-filter">
              <select v-model="selectedCategory" @change="filterPoliciesByCategory" class="category-select">
                <option value="">全部分类</option>
                <option v-for="category in availableCategories" :key="category" :value="category">
                  {{ category }}
                </option>
              </select>
            </div>
          </div>
        </div>
        <div class="policy-list" :class="{ 'expanded': showTimeControl }">
          <div v-if="loading" class="loading-container">
            <div class="loading-spinner"></div>
            <p class="loading-text">政策加载中...</p>
          </div>
          <div v-else-if="filteredPolicies.length === 0" class="empty-container">
            <i class="fas fa-file-alt empty-icon"></i>
            <p class="empty-text">暂无政策数据</p>
          </div>
          <div v-else class="policy-cards">
            <div v-for="(policy, index) in filteredPolicies" :key="index" class="policy-card">
              <div class="policy-card-header">
                <h3 class="policy-title">{{ policy['政策名称'] || '政策标题' }}</h3>
                <span class="policy-date">{{ policy['执行时间'] || '发布日期' }}</span>
              </div>
              <div class="policy-card-body">
                <div class="policy-info">
                  <div class="info-item">
                    <i class="fas fa-building info-icon"></i>
                    <span class="info-label">地区：</span>
                    <span class="info-value">{{ policy['省/直辖市/自治区'] || '未知' }}</span>
                  </div>
                  <div class="info-item">
                    <i class="fas fa-tag info-icon"></i>
                    <span class="info-label">政策分类：</span>
                    <span class="info-value">{{ policy['政策分类'] || '未知' }}</span>
                  </div>
                  <div class="info-item">
                    <i class="fas fa-calendar info-icon"></i>
                    <span class="info-label">执行时间：</span>
                    <span class="info-value">{{ policy['执行时间'] || '未说明' }}</span>
                  </div>
                  <div class="info-item">
                    <i class="fas fa-clock info-icon"></i>
                    <span class="info-label">结束时间：</span>
                    <span class="info-value">{{ policy['结束时间'] || '未说明' }}</span>
                  </div>
                </div>
                <div class="policy-content">
                  <h4 class="content-title">政策内容：</h4>
                  <p class="content-text">{{ policy['政策主要内容'] || '暂无详细内容' }}</p>
                </div>
                <div class="policy-actions">
                  <button class="btn btn-sm btn-primary" @click="viewPolicyDetail(policy)">
                    <i class="fas fa-eye mr-1"></i>查看详情
                  </button>
                  <a v-if="policy['原文链接']" :href="policy['原文链接']" target="_blank" class="btn btn-sm btn-secondary">
                    <i class="fas fa-external-link-alt mr-1"></i>查看原文
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="policy-section placeholder-section" v-else>
        <div class="placeholder-content">
          <i class="fas fa-map-marked-alt placeholder-icon"></i>
          <h3 class="placeholder-title">请选择省份</h3>
          <p class="placeholder-text">点击地图上的省份查看该地区的促消费政策</p>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <div class="modal-header-left">
            <i class="fas fa-file-alt modal-icon"></i>
            <h3 class="modal-title">政策详情</h3>
          </div>
          <button class="modal-close" @click="closeModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="detail-section policy-name-section">
            <h4 class="detail-title">
              <i class="fas fa-bookmark"></i>
              政策名称
            </h4>
            <p class="detail-text policy-name">{{ currentPolicy['政策名称'] }}</p>
          </div>
          
          <div class="detail-grid">
            <div class="detail-section">
              <h4 class="detail-title">
                <i class="fas fa-map-marker-alt"></i>
                地区
              </h4>
              <p class="detail-text">{{ currentPolicy['省/直辖市/自治区'] }}</p>
            </div>
            <div class="detail-section">
              <h4 class="detail-title">
                <i class="fas fa-city"></i>
                地级市/自治州
              </h4>
              <p class="detail-text">{{ currentPolicy['地级市/自治州'] || '未说明' }}</p>
            </div>
          </div>
          
          <div class="detail-grid">
            <div class="detail-section">
              <h4 class="detail-title">
                <i class="fas fa-tag"></i>
                政策分类
              </h4>
              <p class="detail-text">{{ currentPolicy['政策分类'] }}</p>
            </div>
            <div class="detail-section">
              <h4 class="detail-title">
                <i class="fas fa-calendar-check"></i>
                执行时间
              </h4>
              <p class="detail-text">{{ currentPolicy['执行时间'] || '未说明' }}</p>
            </div>
          </div>
          
          <div class="detail-grid">
            <div class="detail-section">
              <h4 class="detail-title">
                <i class="fas fa-calendar-times"></i>
                结束时间
              </h4>
              <p class="detail-text">{{ currentPolicy['结束时间'] || '未说明' }}</p>
            </div>
            <div class="detail-section" v-if="currentPolicy['原文链接']">
              <h4 class="detail-title">
                <i class="fas fa-link"></i>
                原文链接
              </h4>
              <a :href="currentPolicy['原文链接']" target="_blank" class="detail-link">
                <i class="fas fa-external-link-alt"></i>
                查看原文
              </a>
            </div>
          </div>
          
          <div class="detail-section content-section">
            <h4 class="detail-title">
              <i class="fas fa-file-alt"></i>
              政策主要内容
            </h4>
            <p class="detail-text content-text">{{ currentPolicy['政策主要内容'] }}</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">
            <i class="fas fa-times"></i>
            关闭
          </button>
        </div>
      </div>
    </div>   


    <!-- 政策关联网络图与智能搜索 -->
    <div class="network-search-row">
      <!-- 政策关联网络图 -->
      <div class="network-graph-card">
        <div class="network-header">
          <div class="network-title">
            <i class="fas fa-project-diagram"></i>
            <span>政策关联网络图</span>
          </div>
          <div class="network-controls">
            <select v-model="networkLayout" class="network-select" @change="updateNetworkGraph">
              <option value="force">力导向布局</option>
              <option value="circular">环形布局</option>
              <option value="radial">径向布局</option>
            </select>
            <button class="btn btn-sm" @click="resetNetworkGraph">
              <i class="fas fa-redo"></i>
              重置
            </button>
          </div>
        </div>
        
        <div class="network-content">
          <div class="network-top-bar">
            <div class="network-legend">
              <div class="legend-title">节点类型</div>
              <div class="legend-items">
                <div class="legend-item">
                  <span class="legend-node province"></span>
                  <span class="legend-label">省份节点</span>
                </div>
                <div class="legend-item">
                  <span class="legend-node category"></span>
                  <span class="legend-label">政策分类</span>
                </div>
                <div class="legend-item">
                  <span class="legend-node keyword"></span>
                  <span class="legend-label">关键词</span>
                </div>
              </div>
            </div>
            
            <div class="network-stats">
              <div class="stat-card">
                <div class="stat-icon nodes">
                  <i class="fas fa-circle"></i>
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ networkStats.nodes }}</span>
                  <span class="stat-label">节点数</span>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon links">
                  <i class="fas fa-link"></i>
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ networkStats.links }}</span>
                  <span class="stat-label">关联数</span>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon density">
                  <i class="fas fa-project-diagram"></i>
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ networkStats.density }}</span>
                  <span class="stat-label">网络密度</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="network-container" ref="networkGraph"></div>
        </div>
        
        <div class="network-tooltip" v-if="selectedNode">
          <div class="tooltip-header">
            <i :class="getNodeIcon(selectedNode.type)"></i>
            <span>{{ selectedNode.name }}</span>
          </div>
          <div class="tooltip-content">
            <div class="tooltip-item">
              <span class="tooltip-label">关联政策：</span>
              <span class="tooltip-value">{{ selectedNode.policyCount }}项</span>
            </div>
            <div class="tooltip-item">
              <span class="tooltip-label">关联节点：</span>
              <span class="tooltip-value">{{ selectedNode.connections }}个</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 智能搜索政策卡片 -->
      <div class="smart-search-card">
      <div class="search-card-header">
        <div class="search-card-title">
          <i class="fas fa-search"></i>
          <span>智能政策搜索</span>
        </div>
        <p class="search-card-subtitle">输入关键词快速查找相关政策</p>
      </div>
      
      <div class="search-card-body">
        <div class="search-input-wrapper">
          <i class="fas fa-search search-icon"></i>
          <input
            type="text"
            v-model="smartSearchQuery"
            @input="handleSmartSearch"
            placeholder="输入关键词搜索政策（如：补贴、新能源汽车、消费券...）"
            class="smart-search-input"
          />
          <button 
            v-if="smartSearchQuery" 
            class="clear-search-btn"
            @click="clearSmartSearch"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="search-suggestions" v-if="smartSearchQuery && searchSuggestions.length > 0">
          <span class="suggestion-label">热门搜索：</span>
          <div class="suggestion-tags">
            <span 
              v-for="(suggestion, index) in searchSuggestions" 
              :key="index"
              class="suggestion-tag"
              @click="applySuggestion(suggestion)"
            >
              {{ suggestion }}
            </span>
          </div>
        </div>
        
        <div class="search-results" v-if="smartSearchQuery">
          <div class="results-header">
            <span class="results-count">
              找到 <strong>{{ smartSearchResults.length }}</strong> 条相关政策
            </span>
            <div class="results-sort">
              <select v-model="searchSortBy" class="sort-select">
                <option value="relevance">按相关度</option>
                <option value="date">按时间</option>
              </select>
            </div>
          </div>
          
          <div class="results-list" v-if="smartSearchResults.length > 0">
            <div 
              v-for="(policy, index) in paginatedSearchResults" 
              :key="index"
              class="result-item"
              @click="viewPolicyDetail(policy)"
            >
              <div class="result-header">
                <h4 class="result-title" v-html="highlightKeyword(policy['政策名称'], smartSearchQuery)"></h4>
                <span class="result-category">{{ policy['政策分类'] }}</span>
              </div>
              <div class="result-meta">
                <div class="meta-item">
                  <i class="fas fa-map-marker-alt"></i>
                  <span class="info-label">地区：</span>
                  <span class="info-value">{{ policy['省/直辖市/自治区'] }}</span>
                </div>
                <div class="meta-item" v-if="policy['地级市/自治州']">
                  <i class="fas fa-city"></i>
                  <span class="info-label">城市：</span>
                  <span class="info-value">{{ policy['地级市/自治州'] }}</span>
                </div>
                <div class="meta-item">
                  <i class="fas fa-calendar"></i>
                  <span class="info-label">执行时间：</span>
                  <span class="info-value">{{ policy['执行时间'] || '未说明' }}</span>
                </div>
              </div>
              <div class="result-content-wrapper">
                <h4 class="content-title">政策内容：</h4>
                <p class="result-content" v-html="highlightKeyword(truncateText(policy['政策主要内容'], 120), smartSearchQuery)"></p>
              </div>
              <div class="result-tags">
                <span class="tag" v-if="policy['政策主要内容']?.includes('补贴')">补贴</span>
                <span class="tag" v-if="policy['政策主要内容']?.includes('消费券')">消费券</span>
                <span class="tag" v-if="policy['政策主要内容']?.includes('新能源')">新能源</span>
              </div>
            </div>
          </div>
          
          <div class="no-results" v-else>
            <i class="fas fa-search-minus"></i>
            <p>未找到相关政策</p>
            <span class="no-results-hint">尝试使用其他关键词搜索</span>
          </div>
          
          <div class="results-pagination" v-if="smartSearchResults.length > searchPageSize">
            <button 
              class="pagination-btn"
              :disabled="searchCurrentPage === 1"
              @click="searchCurrentPage--"
            >
              <i class="fas fa-chevron-left"></i>
            </button>
            <span class="pagination-info">
              {{ searchCurrentPage }} / {{ totalSearchPages }}
            </span>
            <button 
              class="pagination-btn"
              :disabled="searchCurrentPage >= totalSearchPages"
              @click="searchCurrentPage++"
            >
              <i class="fas fa-chevron-right"></i>
            </button>
          </div>
        </div>
        
        <div class="search-placeholder" v-else>
          <div class="placeholder-icon">
            <i class="fas fa-search"></i>
          </div>
          <p class="placeholder-text">输入关键词开始搜索</p>
          <div class="quick-search-tags">
            <span class="quick-tag" @click="applySuggestion('补贴')">补贴</span>
            <span class="quick-tag" @click="applySuggestion('新能源汽车')">新能源汽车</span>
            <span class="quick-tag" @click="applySuggestion('消费券')">消费券</span>
            <span class="quick-tag" @click="applySuggestion('以旧换新')">以旧换新</span>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <div class="chart-card trend-card">
        <div class="chart-header">
          <div class="chart-title">
            <i class="fas fa-chart-line"></i>
            <span >政策发布趋势</span>
          </div>
          <p class="chart-subtitle">各月份政策发布数量分布</p>
        </div>
        <div ref="trendChart" class="chart-container"></div>
      </div>
      <div class="chart-card pie-card">
        <div class="chart-header">
          <div class="chart-title">
            <i class="fas fa-chart-pie"></i>
            <span>政策类型分布</span>
          </div>
          <p class="chart-subtitle">各类型政策占比情况</p>
        </div>
        <div ref="pieChart" class="chart-container"></div>
      </div>
      <div class="chart-card ranking-card">
        <div class="chart-header">
          <div class="chart-title">
            <i class="fas fa-fire"></i>
            <span>政策热度排行榜</span>
          </div>
          <p class="chart-subtitle">TOP 15 政策活跃省份</p>
        </div>
        <div class="ranking-list">
          <div 
            v-for="(item, index) in top10Provinces" 
            :key="item.name" 
            class="ranking-item"
            :class="{ 'top-three': index < 3 }"
          >
            <span class="ranking-number" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
            <span class="ranking-name">{{ item.name }}</span>
            <div class="ranking-bar-container">
              <div class="ranking-bar" :style="{ width: (item.value / top10Provinces[0].value * 100) + '%' }"></div>
            </div>
            <span class="ranking-value">{{ item.value }}项</span>
          </div>
        </div>
      </div>
      <div class="category-stats-card">
        <div class="chart-header">
          <div class="chart-title">
            <i class="fas fa-layer-group"></i>
            <span>政策分类统计</span>
          </div>
          <p class="chart-subtitle">各类型政策数量分布</p>
        </div>
        <div class="category-cards-grid">
          <div 
            v-for="(stat, category) in categoryStats" 
            :key="category" 
            class="category-card"
          >
            <div class="category-icon">
              <i :class="getCategoryIcon(category)"></i>
            </div>
            <div class="category-info">
              <span class="category-name">{{ category }}</span>
              <span class="category-count">{{ stat.count }}项政策</span>
            </div>
            <div class="category-percentage">{{ stat.percentage }}%</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 多维度对比卡片 -->
    <div class="comparison-card">
      <div class="comparison-header">
        <div class="comparison-title">
          <i class="fas fa-chart-bar"></i>
          <span>多维度对比分析</span>
        </div>
      </div>
      
      <div class="comparison-content">
        <!-- 对比维度选择 -->
        <div class="dimension-selector">
          <div class="selector-header">
            <h3 class="selector-title">选择对比维度</h3>
          </div>
          <div class="selector-options">
            <div 
              v-for="dim in availableDimensions" 
              :key="dim.value"
              class="dimension-option"
              :class="{ active: selectedDimension === dim.value }"
              @click="selectComparisonDimension(dim.value)"
            >
              <i :class="dim.icon"></i>
              <span>{{ dim.label }}</span>
            </div>
          </div>
        </div>

        <!-- 对比项目选择 -->
        <div class="comparison-items-section">
          <div class="items-header">
            <h3 class="items-title">选择对比项目</h3>
            <span class="items-hint">（最多选择5个）</span>
          </div>
          <div class="items-selector">
            <div class="items-search">
              <input 
                type="text" 
                v-model="comparisonSearchQuery" 
                :placeholder="'搜索' + getDimensionLabel(selectedDimension) + '...'"
                class="search-input"
              />
            </div>
            <div class="items-list">
              <div 
                v-for="item in filteredComparisonItems" 
                :key="item"
                class="item-checkbox"
                :class="{ disabled: selectedComparisonItems.length >= 5 && !selectedComparisonItems.includes(item) }"
              >
                <label>
                  <input 
                    type="checkbox" 
                    :value="item" 
                    v-model="selectedComparisonItems"
                    :disabled="selectedComparisonItems.length >= 5 && !selectedComparisonItems.includes(item)"
                  />
                  <span class="checkbox-label">{{ item }}</span>
                  <span class="checkbox-count">({{ getComparisonItemCount(item) }}项政策)</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- 对比结果展示 -->
        <div class="comparison-results" v-if="selectedComparisonItems.length > 0">
          <div class="results-header">
            <h3 class="results-title">对比结果</h3>
            <div class="results-actions">
              <button class="btn btn-sm" @click="exportComparisonData">
                <i class="fas fa-download"></i>
                导出数据
              </button>
            </div>
          </div>
          
          <!-- 对比图表 -->
          <div class="comparison-charts">
            <div class="chart-card">
              <div class="chart-header">
                <h4 class="chart-title">政策数量对比</h4>
              </div>
              <div class="chart-container" ref="comparisonBarChart"></div>
            </div>
            
            <div class="chart-card">
              <div class="chart-header">
                <h4 class="chart-title">占比分布</h4>
              </div>
              <div class="chart-container" ref="comparisonPieChart"></div>
            </div>
          </div>

          <!-- 详细数据表格 -->
          <div class="comparison-table-section">
            <div class="table-header">
              <h4 class="table-title">详细数据对比</h4>
            </div>
            <div class="comparison-table-container">
              <table class="comparison-table">
                <thead>
                  <tr>
                    <th>对比项</th>
                    <th>政策数量</th>
                    <th>占比</th>
                    <th>有效政策</th>
                    <th>已过期</th>
                    <th>平均有效期</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in selectedComparisonItems" :key="item">
                    <td class="item-name">{{ item }}</td>
                    <td class="item-value">{{ getComparisonItemCount(item) }}</td>
                    <td class="item-percentage">{{ getComparisonItemPercentage(item) }}%</td>
                    <td class="item-active">{{ getActivePolicyCount(item) }}</td>
                    <td class="item-expired">{{ getExpiredPolicyCount(item) }}</td>
                    <td class="item-duration">{{ getAverageDuration(item) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 政策文本智能分析卡片 -->
    <div class="text-analysis-card">
      <div class="analysis-header">
        <div class="analysis-title">
          <i class="fas fa-brain"></i>
          <span>政策文本智能分析</span>
        </div>
        <div class="analysis-controls">
          <select v-model="selectedAnalysisType" class="analysis-select" @change="updateTextAnalysis">
            <option value="keywords">关键词分析</option>
            <option value="topics">主题分析</option>
            <option value="summary">文本摘要</option>
          </select>
          <button class="btn btn-sm" @click="refreshAnalysis">
            <i class="fas fa-sync-alt"></i>
            刷新分析
          </button>
        </div>
      </div>
      
      <div class="analysis-content">
        <!-- 关键词分析 -->
        <div v-if="selectedAnalysisType === 'keywords'" class="keywords-analysis">
          <div class="analysis-section full-width">
            <h3 class="section-title">高频关键词分布</h3>
            <div class="keywords-chart" ref="wordCloudChart"></div>
          </div>
        </div>

        <!-- 主题分析 -->
        <div v-if="selectedAnalysisType === 'topics'" class="topics-analysis">
          <div class="topics-grid">
            <div 
              v-for="(topic, index) in policyTopics" 
              :key="index"
              class="topic-card"
            >
              <div class="topic-header">
                <div class="topic-icon">
                  <i :class="topic.icon"></i>
                </div>
                <h4 class="topic-title">{{ topic.name }}</h4>
              </div>
              <div class="topic-content">
                <div class="topic-stats">
                  <div class="stat-item">
                    <span class="stat-label">相关政策</span>
                    <span class="stat-number">{{ topic.count }}项</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">占比</span>
                    <span class="stat-number">{{ topic.percentage }}%</span>
                  </div>
                </div>
                <div class="topic-keywords">
                  <span 
                    v-for="(kw, kwIndex) in topic.keywords" 
                    :key="kwIndex"
                    class="topic-keyword"
                  >
                    {{ kw }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 文本摘要 -->
        <div v-if="selectedAnalysisType === 'summary'" class="summary-analysis">
          <div class="summary-section">
            <h3 class="section-title">政策概览</h3>
            <div class="summary-stats">
              <div class="summary-stat-card">
                <div class="stat-icon">
                  <i class="fas fa-file-alt"></i>
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ totalPolicies }}</span>
                  <span class="stat-label">政策总数</span>
                </div>
              </div>
              <div class="summary-stat-card">
                <div class="stat-icon">
                  <i class="fas fa-align-left"></i>
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ averageTextLength }}</span>
                  <span class="stat-label">平均文本长度</span>
                </div>
              </div>
              <div class="summary-stat-card">
                <div class="stat-icon">
                  <i class="fas fa-tags"></i>
                </div>
                <div class="stat-info">
                  <span class="stat-value">{{ uniqueKeywords }}</span>
                  <span class="stat-label">独特关键词</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="summary-section">
            <h3 class="section-title">政策要点摘要</h3>
            <div class="policy-highlights">
              <div 
                v-for="(highlight, index) in policyHighlights" 
                :key="index"
                class="highlight-item"
              >
                <div class="highlight-icon">
                  <i class="fas fa-lightbulb"></i>
                </div>
                <div class="highlight-content">
                  <h4 class="highlight-title">{{ highlight.title }}</h4>
                  <p class="highlight-text">{{ highlight.content }}</p>
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
import 'echarts-gl'
import axios from 'axios'
import * as XLSX from 'xlsx'

const chinaJson = {
  "type": "FeatureCollection",
  "features": [
    {"type": "Feature", "properties": {"name": "北京"}, "geometry": {"type": "Polygon", "coordinates": [[[116.4, 39.9], [116.5, 39.9], [116.5, 40.0], [116.4, 40.0], [116.4, 39.9]]]}},
    {"type": "Feature", "properties": {"name": "天津"}, "geometry": {"type": "Polygon", "coordinates": [[[117.2, 39.1], [117.3, 39.1], [117.3, 39.2], [117.2, 39.2], [117.2, 39.1]]]}},
    {"type": "Feature", "properties": {"name": "河北"}, "geometry": {"type": "Polygon", "coordinates": [[[114.5, 38.0], [115.0, 38.0], [115.0, 38.5], [114.5, 38.5], [114.5, 38.0]]]}},
    {"type": "Feature", "properties": {"name": "山西"}, "geometry": {"type": "Polygon", "coordinates": [[[112.5, 37.8], [113.0, 37.8], [113.0, 38.3], [112.5, 38.3], [112.5, 37.8]]]}},
    {"type": "Feature", "properties": {"name": "内蒙古"}, "geometry": {"type": "Polygon", "coordinates": [[[111.6, 40.8], [112.5, 40.8], [112.5, 41.5], [111.6, 41.5], [111.6, 40.8]]]}},
    {"type": "Feature", "properties": {"name": "辽宁"}, "geometry": {"type": "Polygon", "coordinates": [[[123.4, 41.8], [124.0, 41.8], [124.0, 42.3], [123.4, 42.3], [123.4, 41.8]]]}},
    {"type": "Feature", "properties": {"name": "吉林"}, "geometry": {"type": "Polygon", "coordinates": [[[126.6, 43.9], [127.2, 43.9], [127.2, 44.4], [126.6, 44.4], [126.6, 43.9]]]}},
    {"type": "Feature", "properties": {"name": "黑龙江"}, "geometry": {"type": "Polygon", "coordinates": [[[126.6, 45.7], [127.5, 45.7], [127.5, 46.3], [126.6, 46.3], [126.6, 45.7]]]}},
    {"type": "Feature", "properties": {"name": "上海"}, "geometry": {"type": "Polygon", "coordinates": [[[121.5, 31.2], [121.6, 31.2], [121.6, 31.3], [121.5, 31.3], [121.5, 31.2]]]}},
    {"type": "Feature", "properties": {"name": "江苏"}, "geometry": {"type": "Polygon", "coordinates": [[[118.8, 32.0], [119.5, 32.0], [119.5, 32.6], [118.8, 32.6], [118.8, 32.0]]]}},
    {"type": "Feature", "properties": {"name": "浙江"}, "geometry": {"type": "Polygon", "coordinates": [[[120.2, 30.3], [120.8, 30.3], [120.8, 30.8], [120.2, 30.8], [120.2, 30.3]]]}},
    {"type": "Feature", "properties": {"name": "安徽"}, "geometry": {"type": "Polygon", "coordinates": [[[117.3, 31.9], [117.8, 31.9], [117.8, 32.4], [117.3, 32.4], [117.3, 31.9]]]}},
    {"type": "Feature", "properties": {"name": "福建"}, "geometry": {"type": "Polygon", "coordinates": [[[119.3, 26.1], [119.8, 26.1], [119.8, 26.6], [119.3, 26.6], [119.3, 26.1]]]}},
    {"type": "Feature", "properties": {"name": "江西"}, "geometry": {"type": "Polygon", "coordinates": [[[115.9, 28.7], [116.4, 28.7], [116.4, 29.2], [115.9, 29.2], [115.9, 28.7]]]}},
    {"type": "Feature", "properties": {"name": "山东"}, "geometry": {"type": "Polygon", "coordinates": [[[117.0, 36.6], [117.8, 36.6], [117.8, 37.2], [117.0, 37.2], [117.0, 36.6]]]}},
    {"type": "Feature", "properties": {"name": "河南"}, "geometry": {"type": "Polygon", "coordinates": [[[113.6, 34.8], [114.2, 34.8], [114.2, 35.3], [113.6, 35.3], [113.6, 34.8]]]}},
    {"type": "Feature", "properties": {"name": "湖北"}, "geometry": {"type": "Polygon", "coordinates": [[[114.3, 30.5], [114.9, 30.5], [114.9, 31.0], [114.3, 31.0], [114.3, 30.5]]]}},
    {"type": "Feature", "properties": {"name": "湖南"}, "geometry": {"type": "Polygon", "coordinates": [[[113.0, 28.2], [113.6, 28.2], [113.6, 28.7], [113.0, 28.7], [113.0, 28.2]]]}},
    {"type": "Feature", "properties": {"name": "广东"}, "geometry": {"type": "Polygon", "coordinates": [[[113.2, 23.2], [113.8, 23.2], [113.8, 23.7], [113.2, 23.7], [113.2, 23.2]]]}},
    {"type": "Feature", "properties": {"name": "广西"}, "geometry": {"type": "Polygon", "coordinates": [[[108.3, 22.8], [109.0, 22.8], [109.0, 23.4], [108.3, 23.4], [108.3, 22.8]]]}},
    {"type": "Feature", "properties": {"name": "海南"}, "geometry": {"type": "Polygon", "coordinates": [[[110.3, 20.0], [110.8, 20.0], [110.8, 20.5], [110.3, 20.5], [110.3, 20.0]]]}},
    {"type": "Feature", "properties": {"name": "重庆"}, "geometry": {"type": "Polygon", "coordinates": [[[106.5, 29.6], [107.0, 29.6], [107.0, 30.1], [106.5, 30.1], [106.5, 29.6]]]}},
    {"type": "Feature", "properties": {"name": "四川"}, "geometry": {"type": "Polygon", "coordinates": [[[104.1, 30.7], [104.8, 30.7], [104.8, 31.3], [104.1, 31.3], [104.1, 30.7]]]}},
    {"type": "Feature", "properties": {"name": "贵州"}, "geometry": {"type": "Polygon", "coordinates": [[[106.7, 26.6], [107.3, 26.6], [107.3, 27.1], [106.7, 27.1], [106.7, 26.6]]]}},
    {"type": "Feature", "properties": {"name": "云南"}, "geometry": {"type": "Polygon", "coordinates": [[[102.7, 25.0], [103.4, 25.0], [103.4, 25.6], [102.7, 25.6], [102.7, 25.0]]]}},
    {"type": "Feature", "properties": {"name": "西藏"}, "geometry": {"type": "Polygon", "coordinates": [[[91.1, 30.0], [92.0, 30.0], [92.0, 30.7], [91.1, 30.7], [91.1, 30.0]]]}},
    {"type": "Feature", "properties": {"name": "陕西"}, "geometry": {"type": "Polygon", "coordinates": [[[109.0, 34.3], [109.6, 34.3], [109.6, 34.8], [109.0, 34.8], [109.0, 34.3]]]}},
    {"type": "Feature", "properties": {"name": "甘肃"}, "geometry": {"type": "Polygon", "coordinates": [[[103.7, 36.0], [104.4, 36.0], [104.4, 36.6], [103.7, 36.6], [103.7, 36.0]]]}},
    {"type": "Feature", "properties": {"name": "青海"}, "geometry": {"type": "Polygon", "coordinates": [[[101.7, 36.6], [102.4, 36.6], [102.4, 37.2], [101.7, 37.2], [101.7, 36.6]]]}},
    {"type": "Feature", "properties": {"name": "宁夏"}, "geometry": {"type": "Polygon", "coordinates": [[[106.3, 38.5], [106.8, 38.5], [106.8, 39.0], [106.3, 39.0], [106.3, 38.5]]]}},
    {"type": "Feature", "properties": {"name": "新疆"}, "geometry": {"type": "Polygon", "coordinates": [[[87.7, 43.8], [88.5, 43.8], [88.5, 44.4], [87.7, 44.4], [87.7, 43.8]]]}},
    {"type": "Feature", "properties": {"name": "台湾"}, "geometry": {"type": "Polygon", "coordinates": [[[121.5, 25.0], [122.0, 25.0], [122.0, 25.5], [121.5, 25.5], [121.5, 25.0]]]}},
    {"type": "Feature", "properties": {"name": "香港"}, "geometry": {"type": "Polygon", "coordinates": [[[114.2, 22.3], [114.3, 22.3], [114.3, 22.4], [114.2, 22.4], [114.2, 22.3]]]}},
    {"type": "Feature", "properties": {"name": "澳门"}, "geometry": {"type": "Polygon", "coordinates": [[[113.5, 22.2], [113.6, 22.2], [113.6, 22.3], [113.5, 22.3], [113.5, 22.2]]]}}
  ]
}

echarts.registerMap('china', chinaJson)

export default {
  name: 'Policy',
  data() {
    return {
      chart: null,
      trendChart: null,
      pieChart: null,
      selectedProvince: null,
      policyData: [],
      filteredPolicies: [],
      loading: false,
      showModal: false,
      currentPolicy: {},
      searchQuery: '',
      showSuggestions: false,
      filteredProvinces: [],
      citySearchQuery: '',
      showCitySuggestions: false,
      filteredCities: [],
      selectedCity: null,
      selectedCategory: '',
      availableCategories: [],
      // 时空动态可视化相关数据
      showTimeControl: false,
      timePoints: [], // 所有时间点（年月）
      currentTimeIndex: 0,
      currentTimePoint: '',
      isTimePlaying: false,
      animationTimer: null,
      animationSpeed: 500, // 毫秒
      timeRange: {
        start: '',
        end: ''
      },
      timeSeriesData: {}, // 按时间点组织的政策数据
      currentPolicyCount: 0,
      provinceMapping: {
        '北京': '北京市',
        '天津': '天津市',
        '河北': '河北省',
        '山西': '山西省',
        '内蒙古': '内蒙古自治区',
        '辽宁': '辽宁省',
        '吉林': '吉林省',
        '黑龙江': '黑龙江省',
        '上海': '上海市',
        '江苏': '江苏省',
        '浙江': '浙江省',
        '安徽': '安徽省',
        '福建': '福建省',
        '江西': '江西省',
        '山东': '山东省',
        '河南': '河南省',
        '湖北': '湖北省',
        '湖南': '湖南省',
        '广东': '广东省',
        '广西': '广西壮族自治区',
        '海南': '海南省', 
        '重庆': '重庆市',
        '四川': '四川省',
        '贵州': '贵州省',
        '云南': '云南省',
        '西藏': '西藏自治区',
        '陕西': '陕西省',
        '甘肃': '甘肃省',
        '青海': '青海省',
        '宁夏': '宁夏回族自治区',
        '新疆': '新疆维吾尔自治区',
        '台湾': '台湾省',
        '香港': '香港特别行政区',
        '澳门': '澳门特别行政区',
        '南海诸岛':'南海诸岛',
      },
      // 多维度对比相关数据
      selectedDimension: 'province',
      selectedComparisonItems: [],
      comparisonSearchQuery: '',
      comparisonBarChart: null,
      comparisonPieChart: null,
      availableDimensions: [
        { value: 'province', label: '省份对比', icon: 'fas fa-map-marked-alt' },
        { value: 'category', label: '政策分类对比', icon: 'fas fa-tags' },
        { value: 'time', label: '时间对比', icon: 'fas fa-calendar-alt' },
        { value: 'city', label: '城市对比', icon: 'fas fa-city' }
      ],
      // 政策文本智能分析相关数据
      selectedAnalysisType: 'keywords',
      wordCloudChart: null,
      topKeywords: [],
      policyTopics: [],
      policyHighlights: [],
      resizeObserver: null,
      keywordStats: {},
      // 智能搜索相关数据
      smartSearchQuery: '',
      smartSearchResults: [],
      searchSuggestions: ['补贴', '新能源汽车', '消费券', '以旧换新', '购车', '家电'],
      searchSortBy: 'relevance',
      searchCurrentPage: 1,
      searchPageSize: 5,
      // 政策关联网络图相关数据
      networkChart: null,
      networkLayout: 'force',
      networkStats: {
        nodes: 0,
        links: 0,
        density: '0.00'
      },
      selectedNode: null,
      networkData: {
        nodes: [],
        links: []
      }
    }
  },
  async mounted() {
    await this.loadPolicyData()
    this.initChart()
    this.$nextTick(() => {
      this.initTrendChart()
      this.initPieChart()
      this.updateTextAnalysis()
      this.initNetworkGraph()
    })
    
    this.resizeObserver = new ResizeObserver(() => {
      this.handleResize()
    })
    
    const chartContainers = [
      this.$refs.chart,
      this.$refs.trendChart,
      this.$refs.pieChart,
      this.$refs.wordCloudChart,
      this.$refs.networkGraph,
      this.$refs.comparisonBarChart,
      this.$refs.comparisonPieChart
    ].filter(el => el)
    
    chartContainers.forEach(el => {
      this.resizeObserver.observe(el)
    })
    
    window.addEventListener('resize', this.handleResize)
  },
  watch: {
    selectedComparisonItems(newVal) {
      if (newVal.length > 0) {
        this.$nextTick(() => {
          this.initComparisonCharts()
        })
      }
    }
  },
  beforeDestroy() {
    if (this.chart) {
      this.chart.dispose()
    }
    if (this.trendChart) {
      this.trendChart.dispose()
    }
    if (this.pieChart) {
      this.pieChart.dispose()
    }
    if (this.comparisonBarChart) {
      this.comparisonBarChart.dispose()
    }
    if (this.comparisonPieChart) {
      this.comparisonPieChart.dispose()
    }
    if (this.wordCloudChart) {
      this.wordCloudChart.dispose()
    }
    if (this.networkChart) {
      this.networkChart.dispose()
    }
    
    if (this.resizeObserver) {
      this.resizeObserver.disconnect()
      this.resizeObserver = null
    }
    
    window.removeEventListener('resize', this.handleResize)
    
    if (this.animationTimer) {
      clearInterval(this.animationTimer)
      this.animationTimer = null
    }
  },
  computed: {
    policySectionTitle() {
      if (this.selectedCity) {
        return `${this.selectedProvince}${this.selectedCity}`
      }
      return this.selectedProvince
    },
    totalPolicies() {
      return this.policyData.length
    },
    activePolicies() {
      const now = new Date()
      return this.policyData.filter(policy => {
        const endTime = policy['结束时间']
        if (!endTime) return true
        const endDate = new Date(endTime)
        return endDate >= now
      }).length
    },
    coveredProvinces() {
      const provinces = new Set()
      this.policyData.forEach(policy => {
        const province = policy['省/直辖市/自治区']
        if (province) {
          provinces.add(province)
        }
      })
      return provinces.size
    },
    coveredCities() {
      const cities = new Set()
      this.policyData.forEach(policy => {
        const city = policy['地级市/自治州']
        const province = policy['省/直辖市/自治区']
        if (city) {
          cities.add(`${province}-${city}`)
        } else if (province) {
          cities.add(province)
        }
      })
      return cities.size
    },
    top10Provinces() {
      const counts = this.getProvinceCounts()
      return Object.entries(counts)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 15)
    },
    categoryStats() {
      const stats = {}
      const total = this.policyData.length || 1
      this.policyData.forEach(policy => {
        const category = policy['政策分类'] || '其他'
        if (!stats[category]) {
          stats[category] = { count: 0, percentage: 0 }
        }
        stats[category].count++
      })
      Object.keys(stats).forEach(category => {
        stats[category].percentage = ((stats[category].count / total) * 100).toFixed(1)
      })
      return stats
    },
    monthlyTrendData() {
      const monthlyData = {}
      this.policyData.forEach(policy => {
        const execTime = policy['执行时间']
        if (execTime) {
          const date = new Date(execTime)
          const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
          monthlyData[monthKey] = (monthlyData[monthKey] || 0) + 1
        }
      })
      const sortedMonths = Object.keys(monthlyData).sort()
      return {
        months: sortedMonths,
        values: sortedMonths.map(m => monthlyData[m])
      }
    },
    categoryPieData() {
      const data = []
      Object.entries(this.categoryStats).forEach(([name, stat]) => {
        data.push({ name, value: stat.count })
      })
      return data
    },
    // 时空动态可视化计算属性
    filteredTimePoints() {
      // 只显示部分时间点标签，避免重叠
      const step = Math.max(1, Math.floor(this.timePoints.length / 6))
      return this.timePoints.filter((_, index) => index % step === 0 || index === this.timePoints.length - 1)
    },
    currentTimeData() {
      if (!this.timePoints.length || this.currentTimeIndex < 0 || this.currentTimeIndex >= this.timePoints.length) {
        return {}
      }
      return this.timeSeriesData[this.timePoints[this.currentTimeIndex]] || {}
    },
    // 多维度对比计算属性
    filteredComparisonItems() {
      let items = []
      
      switch(this.selectedDimension) {
        case 'province':
          items = Object.keys(this.getProvinceCounts())
          break
        case 'category':
          items = Object.keys(this.categoryStats)
          break
        case 'time':
          items = this.getYearsList()
          break
        case 'city':
          items = this.getCitiesList()
          break
      }
      
      if (this.comparisonSearchQuery) {
        items = items.filter(item => 
          item.toLowerCase().includes(this.comparisonSearchQuery.toLowerCase())
        )
      }
      
      return items.sort()
    },
    // 政策文本智能分析计算属性
    averageTextLength() {
      if (this.policyData.length === 0) return 0
      const totalLength = this.policyData.reduce((sum, policy) => {
        const content = policy['政策主要内容'] || ''
        return sum + content.length
      }, 0)
      return Math.round(totalLength / this.policyData.length)
    },
    uniqueKeywords() {
      return this.topKeywords.length
    },
    // 智能搜索计算属性
    totalSearchPages() {
      return Math.ceil(this.smartSearchResults.length / this.searchPageSize)
    },
    paginatedSearchResults() {
      const start = (this.searchCurrentPage - 1) * this.searchPageSize
      const end = start + this.searchPageSize
      return this.smartSearchResults.slice(start, end)
    }
  },
  methods: {
    // 初始化时间序列数据
    initTimeSeriesData() {
      const timeData = {}
      const allTimePoints = new Set()
      
      // 遍历所有政策，按执行时间组织数据
      this.policyData.forEach(policy => {
        const execTime = policy['执行时间']
        if (execTime) {
          try {
            const date = new Date(execTime)
            const year = date.getFullYear()
            const month = date.getMonth() + 1
            const timeKey = `${year}-${String(month).padStart(2, '0')}`
            
            if (!timeData[timeKey]) {
              timeData[timeKey] = {
                policies: [],
                provinceCounts: {}
              }
            }
            
            // 添加政策到对应时间点
            timeData[timeKey].policies.push(policy)
            
            // 更新省份计数
            const province = policy['省/直辖市/自治区'] || ''
            if (province) {
              const provinceName = this.provinceMapping[province] || province
              timeData[timeKey].provinceCounts[provinceName] = 
                (timeData[timeKey].provinceCounts[provinceName] || 0) + 1
            }
            
            allTimePoints.add(timeKey)
          } catch (error) {
            console.warn('解析时间失败:', execTime, error)
          }
        }
      })
      
      // 按时间排序
      const sortedTimePoints = Array.from(allTimePoints).sort()
      
      // 计算累计数据
      const cumulativeData = {}
      let cumulativePolicies = []
      const cumulativeProvinceCounts = {}
      
      sortedTimePoints.forEach((timePoint, index) => {
        const currentData = timeData[timePoint]
        
        // 累计政策
        cumulativePolicies = [...cumulativePolicies, ...currentData.policies]
        
        // 累计省份计数
        Object.entries(currentData.provinceCounts).forEach(([province, count]) => {
          cumulativeProvinceCounts[province] = (cumulativeProvinceCounts[province] || 0) + count
        })
        
        // 保存累计数据
        cumulativeData[timePoint] = {
          policies: [...cumulativePolicies],
          provinceCounts: { ...cumulativeProvinceCounts },
          cumulativeCount: cumulativePolicies.length
        }
      })
      
      this.timeSeriesData = cumulativeData
      this.timePoints = sortedTimePoints
      
      // 设置时间范围
      if (sortedTimePoints.length > 0) {
        this.timeRange.start = sortedTimePoints[0]
        this.timeRange.end = sortedTimePoints[sortedTimePoints.length - 1]
        this.currentTimePoint = sortedTimePoints[0]
        this.currentPolicyCount = cumulativeData[sortedTimePoints[0]]?.cumulativeCount || 0
      }
    },
    
    initChart() {
      this.chart = echarts.init(this.$refs.chinaMap)
      this.loadMapData()
      
      window.addEventListener('resize', this.handleResize)
    },
    
    initTrendChart() {
      if (!this.$refs.trendChart) return
      this.trendChart = echarts.init(this.$refs.trendChart)
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: this.monthlyTrendData.months,
          axisLabel: {
            rotate: 45,
            fontSize: 10
          }
        },
        yAxis: {
          type: 'value',
          minInterval: 1
        },
        series: [{
          name: '政策数量',
          type: 'line',
          smooth: true,
          data: this.monthlyTrendData.values,
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(54, 162, 235, 0.5)' },
                { offset: 1, color: 'rgba(54, 162, 235, 0.1)' }
              ]
            }
          },
          lineStyle: {
            color: '#36a2eb',
            width: 2
          },
          itemStyle: {
            color: '#36a2eb'
          }
        }]
      }
      this.trendChart.setOption(option)
    },
    
    initPieChart() {
      if (!this.$refs.pieChart) return
      this.pieChart = echarts.init(this.$refs.pieChart)
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}项 ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: '-10%',
          top: 'center',
          textStyle: {
            fontSize: 11
          }
        },
        series: [{
          name: '政策类型',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['30%', '50%'],
          avoidLabelOverlap: false,
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: this.categoryPieData,
          color: ['#36a2eb', '#ff6384', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40', '#c9cbcf']
        }]
      }
      this.pieChart.setOption(option)
    },
    
    getCategoryIcon(category) {
      const iconMap = {
        '消费券': 'fas fa-ticket-alt',
        '补贴': 'fas fa-hand-holding-usd',
        '以旧换新': 'fas fa-exchange-alt',
        '下乡补贴': 'fas fa-tractor',
        '充电设施': 'fas fa-charging-station',
        '购置税减免': 'fas fa-receipt',
        '其他': 'fas fa-file-alt'
      }
      return iconMap[category] || 'fas fa-file-alt'
    },
    
    async loadMapData() {
      try {
        const response = await axios.get('/map/100000_full.json')
        echarts.registerMap('china', response.data)
        this.renderMap()
      } catch (error) {
        console.error('加载地图数据失败:', error)
      }
    },
    
    async loadPolicyData() {
      this.loading = true
      try {
        const response = await axios.get('/api/policies')
        this.policyData = response.data
        // 初始化时间序列数据
        this.initTimeSeriesData()
      } catch (error) {
        console.error('加载政策数据失败:', error)
        this.policyData = this.getMockPolicyData()
        // 使用模拟数据初始化时间序列
        this.initTimeSeriesData()
      } finally {
        this.loading = false
      }
    },
    
    getMockPolicyData() {
      return [
        {
          '省/直辖市/自治区': '北京市',
          '政策名称': '北京市汽车消费券发放政策',
          '政策分类': '消费券',
          '执行时间': '2024-03-01',
          '结束时间': '2024-12-31',
          '政策主要内容': '对购买新能源乘用车的消费者，给予最高10000元的消费券补贴。'
        },
        {
          '省/直辖市/自治区': '上海市',
          '政策名称': '上海市新能源汽车推广应用补贴',
          '政策分类': '补贴',
          '执行时间': '2024-02-15',
          '结束时间': '2024-12-31',
          '政策主要内容': '对购买符合条件的新能源汽车，给予最高15000元的财政补贴。'
        },
        {
          '省/直辖市/自治区': '广东省',
          '政策名称': '广东省汽车以旧换新补贴政策',
          '政策分类': '以旧换新',
          '执行时间': '2024-01-20',
          '结束时间': '2024-12-31',
          '政策主要内容': '对报废旧车并购买新车的消费者，给予最高8000元的补贴。'
        },
        {
          '省/直辖市/自治区': '江苏省',
          '政策名称': '江苏省汽车下乡补贴政策',
          '政策分类': '下乡补贴',
          '执行时间': '2024-03-10',
          '结束时间': '2024-12-31',
          '政策主要内容': '对农村居民购买指定车型，给予最高6000元的下乡补贴。'
        },
        {
          '省/直辖市/自治区': '浙江省',
          '政策名称': '浙江省新能源汽车充电设施建设补贴',
          '政策分类': '充电设施',
          '执行时间': '2024-02-28',
          '结束时间': '2024-12-31',
          '政策主要内容': '对建设新能源汽车充电设施的单位和个人，给予最高5000元的补贴。'
        }
      ]
    },
    
    renderMap(reset = false) {
      const provinceCounts = this.getProvinceCounts()
      const data = Object.keys(provinceCounts).map(province => ({
        name: this.provinceMapping[province],
        value: provinceCounts[province]
      }))
      const maxValue = Math.max(...Object.values(provinceCounts), 20)
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: (params)=> {
            if (params.value !== undefined && params.value !== null && !isNaN(params.value)) {
              return `${params.name}<br/>政策数量：${params.value}项`
            }
            return params.name
          }
        },
        visualMap: {
          min: 0,
          max: maxValue,
          left: 'left',
          bottom: 'bottom',
          text: ['高', '低'],
          calculable: true,
          inRange: {
            color: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4']
          },
          pieces: [  // 使用 pieces 来定义分段
            { min: 0, max: 5, color: '#e0f3f8', label: '0-5项政策' },
            { min: 6, max: 10, color: '#abd9e9', label: '6-10项政策' },
            { min: 11, max: 20, color: '#74add1', label: '11-20项政策' },
            { min: 21, color: '#4575b4', label: '20项以上政策' }
          ]
        },
        series: [
          {
            name: '政策数量',
            type: 'map',
            map: 'china',
            roam: true,
            emphasis: {
              label: {
                show: true
              },
              itemStyle: {
                areaColor: '#f4d03f'
              }
            },
            select: {
              itemStyle: {
                areaColor: '#FFD700'
              }
            },
            data: data
          }
        ]
      }
      
      if (reset) {
        this.chart.clear()
      }
      this.chart.setOption(option, { notMerge: reset })
      
      this.chart.on('click', (params) => {
        if (params.name) {
          this.handleProvinceClick(params.name)
        }
      })
    },
    
    getProvinceCounts() {
      const counts = {}
      
      this.policyData.forEach(policy => {
        const province = policy["省/直辖市/自治区"] || ''
        if (province) {
          counts[province] = (counts[province] || 0) + 1
        }
      }) 
      /* 确保所有省份都有计数 */
      const allProvinces = Object.keys(this.provinceMapping)
      allProvinces.forEach(province => {
        if (!counts[province]) {
          counts[province] = 0
        }
      })
      return counts
    },
    
    handleProvinceClick(provinceName) {
      this.selectedProvince = provinceName
      this.citySearchQuery = ''
      this.selectedCity = null
      this.selectedCategory = ''
      this.updateAvailableCategories()
      this.filterPolicies(provinceName)
    },
    
    filterPolicies(provinceName) {
      this.loading = true
      setTimeout(() => {
        const filtered = this.policyData.filter(
          policy => policy['省/直辖市/自治区'] === provinceName
        )

        // 尝试模糊匹配
        if (filtered.length === 0) {
          const fuzzyFiltered = this.policyData.filter(
            policy => {
              const province = policy['省/直辖市/自治区'] || ''
              return province.includes(provinceName) || provinceName.includes(province)
            }
          )
          this.filteredPolicies = fuzzyFiltered
        } else {
          this.filteredPolicies = filtered
        }
        this.loading = false
      }, 300)
    },
    
    // 时空动态可视化方法
    toggleTimeControl() {
      this.showTimeControl = !this.showTimeControl
      if (this.showTimeControl && this.timePoints.length === 0) {
        this.initTimeSeriesData()
      }
    },
    
    getTimeIndex(timePoint) {
      return this.timePoints.indexOf(timePoint)
    },
    
    updateTimeMap() {
      if (this.currentTimeIndex >= 0 && this.currentTimeIndex < this.timePoints.length) {
        const timePoint = this.timePoints[this.currentTimeIndex]
        this.currentTimePoint = timePoint
        
        const timeData = this.timeSeriesData[timePoint]
        if (timeData && this.chart) {
          this.currentPolicyCount = timeData.cumulativeCount
          
          // 准备地图数据
          const data = Object.keys(timeData.provinceCounts).map(province => ({
            name: province,
            value: timeData.provinceCounts[province]
          }))
          
          // 更新地图
          this.chart.setOption({
            series: [{
              data: data
            }]
          })
        }
      }
    },
    
    prevTimePoint() {
      if (this.currentTimeIndex > 0) {
        this.currentTimeIndex--
        this.updateTimeMap()
      }
    },
    
    nextTimePoint() {
      if (this.currentTimeIndex < this.timePoints.length - 1) {
        this.currentTimeIndex++
        this.updateTimeMap()
      }
    },
    
    toggleTimeAnimation() {
      if (this.isTimePlaying) {
        this.stopTimeAnimation()
      } else {
        this.startTimeAnimation()
      }
    },
    
    startTimeAnimation() {
      if (this.timePoints.length === 0) return
      
      this.isTimePlaying = true
      this.animationTimer = setInterval(() => {
        if (this.currentTimeIndex < this.timePoints.length - 1) {
          this.currentTimeIndex++
          this.updateTimeMap()
        } else {
          this.stopTimeAnimation()
        }
      }, this.animationSpeed)
    },
    
    stopTimeAnimation() {
      this.isTimePlaying = false
      if (this.animationTimer) {
        clearInterval(this.animationTimer)
        this.animationTimer = null
      }
    },
    
    resetTimeControl() {
      this.stopTimeAnimation()
      this.currentTimeIndex = 0
      this.updateTimeMap()
    },
    
    resetMap() {
      this.selectedProvince = null
      this.filteredPolicies = []
      this.searchQuery = ''
      this.filteredProvinces = []
      this.citySearchQuery = ''
      this.filteredCities = []
      this.selectedCity = null
      this.selectedCategory = ''
      this.availableCategories = []
      
      if (this.chart) {
        this.renderMap(true)
      }
    },
    
    viewPolicyDetail(policy) {
      this.currentPolicy = policy
      this.showModal = true
    },
    
    closeModal() {
      this.showModal = false
      this.currentPolicy = {}
    },
    
    exportPolicies() {
      if (!this.selectedProvince) {
        alert('请先选择省份')
        return
      }
      
      if (this.filteredPolicies.length === 0) {
        alert('该省份暂无政策数据可导出')
        return
      }

      const exportData = this.filteredPolicies.map(policy => ({
        '政策名称': policy['政策名称'] || '',
        '地区': policy['省/直辖市/自治区'] || '',
        '地级市/自治州': policy['地级市/自治州'] || '',
        '政策分类': policy['政策分类'] || '',
        '执行时间': policy['执行时间'] || '',
        '结束时间': policy['结束时间'] || '',
        '政策主要内容': policy['政策主要内容'] || '',
        '原文链接': policy['原文链接'] || ''
      }))

      const ws = XLSX.utils.json_to_sheet(exportData)
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, '政策数据')
      
      const fileName = `${this.selectedProvince}政策数据_${new Date().getTime()}.xlsx`
      XLSX.writeFile(wb, fileName)
      
      alert(`成功导出${this.filteredPolicies.length}项政策数据`)
    },
    
    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
      if (this.trendChart) {
        this.trendChart.resize()
      }
      if (this.pieChart) {
        this.pieChart.resize()
      }
      if (this.comparisonBarChart) {
        this.comparisonBarChart.resize()
      }
      if (this.comparisonPieChart) {
        this.comparisonPieChart.resize()
      }
      if (this.wordCloudChart) {
        this.wordCloudChart.resize()
      }
      if (this.networkChart) {
        this.networkChart.resize()
      }
    },
    
    handleSearchInput() {
      if (!this.searchQuery.trim()) {
        this.filteredProvinces = []
        return
      }
      const query = this.searchQuery.trim().toLowerCase()
      const allProvinces = Object.values(this.provinceMapping)
      this.filteredProvinces = allProvinces.filter(province => 
        province.toLowerCase().includes(query)
      ).slice(0, 8)
    },
    
    hideSuggestions() {
      setTimeout(() => {
        this.showSuggestions = false
      }, 200)
    },
    
    selectProvince(provinceName) {
      this.searchQuery = provinceName
      this.showSuggestions = false
      this.selectedProvince = provinceName
      this.citySearchQuery = ''
      this.selectedCity = null
      this.filteredCities = []
      this.selectedCategory = ''
      this.updateAvailableCategories()
      this.filterPolicies(provinceName)
      this.highlightProvinceOnMap(provinceName)
    },
    
    highlightProvinceOnMap(provinceName) {
      if (!this.chart) return
      this.chart.dispatchAction({
        type: 'downplay'
      })
      this.chart.dispatchAction({
        type: 'unSelect'
      })
      this.chart.dispatchAction({
        type: 'select',
        name: provinceName
      })
    },
    
    getAvailableCities(provinceName) {
      const cities = new Set()
      this.policyData.forEach(policy => {
        const province = policy['省/直辖市/自治区'] || ''
        if (province === provinceName || province.includes(provinceName) || provinceName.includes(province)) {
          const city = policy['地级市/自治州']
          if (city && city.trim()) {
            cities.add(city.trim())
          }
        }
      })
      return Array.from(cities).sort()
    },
    
    handleCitySearchInput() {
      const query = this.citySearchQuery.trim().toUpperCase()
      if (query === 'ALL' || query === '') {
        this.filteredCities = ['ALL（显示全部）']
        return
      }
      const availableCities = this.getAvailableCities(this.selectedProvince)
      const searchQuery = this.citySearchQuery.trim().toLowerCase()
      this.filteredCities = availableCities.filter(city => 
        city.toLowerCase().includes(searchQuery)
      ).slice(0, 8)
      if (this.filteredCities.length === 0) {
        this.filteredCities = ['ALL（显示全部）']
      }
    },
    
    hideCitySuggestions() {
      setTimeout(() => {
        this.showCitySuggestions = false
      }, 200)
    },
    
    selectCity(city) {
      if (city === 'ALL（显示全部）') {
        this.citySearchQuery = ''
        this.selectedCity = null
      } else {
        this.citySearchQuery = city
        this.selectedCity = city
      }
      this.showCitySuggestions = false
      this.filterPoliciesByCity()
    },
    
    filterPoliciesByCity() {
      this.applyFilters()
    },
    
    filterPoliciesByCategory() {
      this.applyFilters()
    },
    
    applyFilters() {
      if (!this.selectedProvince) return
      
      this.loading = true
      setTimeout(() => {
        let filtered = this.policyData.filter(policy => {
          const province = policy['省/直辖市/自治区'] || ''
          return province === this.selectedProvince || 
                 province.includes(this.selectedProvince) || 
                 this.selectedProvince.includes(province)
        })
        
        if (this.selectedCity) {
          filtered = filtered.filter(policy => {
            const city = (policy['地级市/自治州'] || '').trim().toUpperCase()
            const selectedCityUpper = this.selectedCity.trim().toUpperCase()
            return city === selectedCityUpper || city === 'ALL' || city === ''
          })
        }
        
        if (this.selectedCategory) {
          filtered = filtered.filter(policy => {
            const category = policy['政策分类'] || ''
            return category === this.selectedCategory
          })
        }
        
        this.filteredPolicies = filtered
        this.loading = false
      }, 300)
    },
    
    updateAvailableCategories() {
      const categories = new Set()
      this.policyData.forEach(policy => {
        const province = policy['省/直辖市/自治区'] || ''
        if (province === this.selectedProvince || 
            province.includes(this.selectedProvince) || 
            this.selectedProvince.includes(province)) {
          const category = policy['政策分类']
          if (category && category.trim()) {
            categories.add(category.trim())
          }
        }
      })
      this.availableCategories = Array.from(categories).sort()
    },
    
    // 多维度对比方法
    selectComparisonDimension(dimension) {
      this.selectedDimension = dimension
      this.selectedComparisonItems = []
      this.comparisonSearchQuery = ''
    },
    
    getDimensionLabel(dimension) {
      const dim = this.availableDimensions.find(d => d.value === dimension)
      return dim ? dim.label : ''
    },
    
    getYearsList() {
      const years = new Set()
      this.policyData.forEach(policy => {
        const execTime = policy['执行时间']
        if (execTime) {
          const year = new Date(execTime).getFullYear()
          years.add(year.toString())
        }
      })
      return Array.from(years)
    },
    
    getCitiesList() {
      const cities = new Set()
      this.policyData.forEach(policy => {
        const city = policy['地级市/自治州']
        const province = policy['省/直辖市/自治区']
        if (city) {
          cities.add(`${province} - ${city}`)
        }
      })
      return Array.from(cities)
    },
    
    getComparisonItemCount(item) {
      let count = 0
      
      switch(this.selectedDimension) {
        case 'province':
          count = this.policyData.filter(p => {
            const province = p['省/直辖市/自治区']
            return province === item || this.provinceMapping[province] === item
          }).length
          break
        case 'category':
          count = this.policyData.filter(p => p['政策分类'] === item).length
          break
        case 'time':
          count = this.policyData.filter(p => {
            const execTime = p['执行时间']
            return execTime && new Date(execTime).getFullYear().toString() === item
          }).length
          break
        case 'city':
          count = this.policyData.filter(p => {
            const city = p['地级市/自治州']
            const province = p['省/直辖市/自治区']
            return city && `${province} - ${city}` === item
          }).length
          break
      }
      
      return count
    },
    
    getComparisonItemPercentage(item) {
      const count = this.getComparisonItemCount(item)
      const total = this.policyData.length || 1
      return ((count / total) * 100).toFixed(1)
    },
    
    getActivePolicyCount(item) {
      const now = new Date()
      let count = 0
      
      const filterPolicy = (policy) => {
        switch(this.selectedDimension) {
          case 'province':
            const province = policy['省/直辖市/自治区']
            return province === item || this.provinceMapping[province] === item
          case 'category':
            return policy['政策分类'] === item
          case 'time':
            const execTime = policy['执行时间']
            return execTime && new Date(execTime).getFullYear().toString() === item
          case 'city':
            const city = policy['地级市/自治州']
            const prov = policy['省/直辖市/自治区']
            return city && `${prov} - ${city}` === item
          default:
            return false
        }
      }
      
      count = this.policyData.filter(policy => {
        if (!filterPolicy(policy)) return false
        const endTime = policy['结束时间']
        if (!endTime) return true
        return new Date(endTime) >= now
      }).length
      
      return count
    },
    
    getExpiredPolicyCount(item) {
      const now = new Date()
      let count = 0
      
      const filterPolicy = (policy) => {
        switch(this.selectedDimension) {
          case 'province':
            const province = policy['省/直辖市/自治区']
            return province === item || this.provinceMapping[province] === item
          case 'category':
            return policy['政策分类'] === item
          case 'time':
            const execTime = policy['执行时间']
            return execTime && new Date(execTime).getFullYear().toString() === item
          case 'city':
            const city = policy['地级市/自治州']
            const prov = policy['省/直辖市/自治区']
            return city && `${prov} - ${city}` === item
          default:
            return false
        }
      }
      
      count = this.policyData.filter(policy => {
        if (!filterPolicy(policy)) return false
        const endTime = policy['结束时间']
        return endTime && new Date(endTime) < now
      }).length
      
      return count
    },
    
    getAverageDuration(item) {
      let totalDays = 0
      let count = 0
      
      const filterPolicy = (policy) => {
        switch(this.selectedDimension) {
          case 'province':
            const province = policy['省/直辖市/自治区']
            return province === item || this.provinceMapping[province] === item
          case 'category':
            return policy['政策分类'] === item
          case 'time':
            const execTime = policy['执行时间']
            return execTime && new Date(execTime).getFullYear().toString() === item
          case 'city':
            const city = policy['地级市/自治州']
            const prov = policy['省/直辖市/自治区']
            return city && `${prov} - ${city}` === item
          default:
            return false
        }
      }
      
      this.policyData.forEach(policy => {
        if (!filterPolicy(policy)) return
        
        const startTime = policy['执行时间']
        const endTime = policy['结束时间']
        
        if (startTime && endTime) {
          const start = new Date(startTime)
          const end = new Date(endTime)
          const days = Math.floor((end - start) / (1000 * 60 * 60 * 24))
          if (days > 0) {
            totalDays += days
            count++
          }
        }
      })
      
      if (count === 0) return '--'
      const avgDays = Math.floor(totalDays / count)
      const months = Math.floor(avgDays / 30)
      const days = avgDays % 30
      
      if (months > 0) {
        return `${months}个月${days > 0 ? days + '天' : ''}`
      }
      return `${days}天`
    },
    
    initComparisonCharts() {
      this.$nextTick(() => {
        this.initComparisonBarChart()
        this.initComparisonPieChart()
      })
    },
    
    initComparisonBarChart() {
      if (!this.$refs.comparisonBarChart) return
      
      if (this.comparisonBarChart) {
        this.comparisonBarChart.dispose()
      }
      
      this.comparisonBarChart = echarts.init(this.$refs.comparisonBarChart)
      
      const data = this.selectedComparisonItems.map(item => ({
        name: item,
        value: this.getComparisonItemCount(item)
      }))
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: '{b}: {c}项'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '8%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: data.map(d => d.name),
          axisLabel: {
            interval: 0,
            rotate: 30,
            fontSize: 11,
            color: '#666'
          },
          axisLine: {
            lineStyle: {
              color: '#e8e8e8'
            }
          },
          axisTick: {
            show: false
          }
        },
        yAxis: {
          type: 'value',
          name: '政策数量',
          nameTextStyle: {
            color: '#999',
            fontSize: 11
          },
          axisLabel: {
            color: '#666',
            fontSize: 11
          },
          axisLine: {
            show: false
          },
          axisTick: {
            show: false
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0'
            }
          }
        },
        series: [{
          name: '政策数量',
          type: 'bar',
          barWidth: '50%',
          data: data.map(d => ({
            value: d.value,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#1890ff' },
                { offset: 1, color: '#69c0ff' }
              ]),
              borderRadius: [4, 4, 0, 0]
            }
          })),
          label: {
            show: true,
            position: 'top',
            fontSize: 10,
            color: '#666',
            formatter: '{c}'
          }
        }]
      }
      
      this.comparisonBarChart.setOption(option)
    },
    
    initComparisonPieChart() {
      if (!this.$refs.comparisonPieChart) return
      
      if (this.comparisonPieChart) {
        this.comparisonPieChart.dispose()
      }
      
      this.comparisonPieChart = echarts.init(this.$refs.comparisonPieChart)
      
      const data = this.selectedComparisonItems.map(item => ({
        name: item,
        value: this.getComparisonItemCount(item)
      }))
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}项 ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: '0%',
          top: 'center',
          textStyle: {
            fontSize: 11,
            color: '#666'
          }
        },
        series: [{
          name: '政策占比',
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['35%', '50%'],
          avoidLabelOverlap: false,
          label: {
            show: false
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 12,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: data,
          color: ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1']
        }]
      }
      
      this.comparisonPieChart.setOption(option)
    },
    
    exportComparisonData() {
      if (this.selectedComparisonItems.length === 0) {
        alert('请先选择对比项目')
        return
      }
      
      const exportData = this.selectedComparisonItems.map(item => ({
        '对比项': item,
        '政策数量': this.getComparisonItemCount(item),
        '占比(%)': this.getComparisonItemPercentage(item),
        '有效政策': this.getActivePolicyCount(item),
        '已过期': this.getExpiredPolicyCount(item),
        '平均有效期': this.getAverageDuration(item)
      }))
      
      const ws = XLSX.utils.json_to_sheet(exportData)
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, '对比数据')
      
      const fileName = `多维度对比数据_${this.getDimensionLabel(this.selectedDimension)}_${new Date().getTime()}.xlsx`
      XLSX.writeFile(wb, fileName)
      
      alert(`成功导出${this.selectedComparisonItems.length}项对比数据`)
    },
    
    // 政策文本智能分析方法
    updateTextAnalysis() {
      this.$nextTick(() => {
        switch(this.selectedAnalysisType) {
          case 'keywords':
            this.analyzeKeywords()
            break
          case 'topics':
            this.analyzeTopics()
            break
          case 'summary':
            this.analyzeSummary()
            break
        }
      })
    },
    
    refreshAnalysis() {
      this.updateTextAnalysis()
    },
    
    analyzeKeywords() {
      const keywordData = {}
      const documentFrequency = {}
      const totalDocuments = this.policyData.length
      
      const keywordWeights = {
        policy: 3.5,
        amount: 3.0,
        target: 2.5,
        industry: 2.5,
        action: 2.0,
        time: 1.5,
        effect: 2.0,
        other: 1.0
      }
      
      const titleWeight = 1.5
      
      this.policyData.forEach(policy => {
        const title = policy['政策名称'] || ''
        const content = policy['政策主要内容'] || ''
        const policyType = policy['政策分类'] || ''
        
        const titleKeywords = this.extractKeywordsAdvanced(title, 'title')
        const contentKeywords = this.extractKeywordsAdvanced(content, 'content')
        const typeKeywords = this.extractKeywordsFromType(policyType)
        
        const docKeywords = new Set()
        
        titleKeywords.forEach(item => {
          const key = item.word
          docKeywords.add(key)
          const weight = (keywordWeights[item.type] || 1) * titleWeight
          
          if (!keywordData[key]) {
            keywordData[key] = {
              word: key,
              count: 0,
              type: item.type,
              weight: weight,
              category: item.category,
              sources: new Set()
            }
          }
          keywordData[key].count += weight
          keywordData[key].sources.add('title')
        })
        
        contentKeywords.forEach(item => {
          const key = item.word
          docKeywords.add(key)
          const weight = keywordWeights[item.type] || 1
          
          if (!keywordData[key]) {
            keywordData[key] = {
              word: key,
              count: 0,
              type: item.type,
              weight: weight,
              category: item.category,
              sources: new Set()
            }
          }
          keywordData[key].count += weight
          keywordData[key].sources.add('content')
        })
        
        typeKeywords.forEach(item => {
          const key = item.word
          docKeywords.add(key)
          const weight = keywordWeights[item.type] || 1
          
          if (!keywordData[key]) {
            keywordData[key] = {
              word: key,
              count: 0,
              type: item.type,
              weight: weight,
              category: item.category,
              sources: new Set()
            }
          }
          keywordData[key].count += weight
          keywordData[key].sources.add('type')
        })
        
        docKeywords.forEach(key => {
          documentFrequency[key] = (documentFrequency[key] || 0) + 1
        })
      })
      
      const sortedKeywords = Object.values(keywordData)
        .map(item => {
          const df = documentFrequency[item.word] || 1
          const idf = Math.log(totalDocuments / df)
          const tfidfScore = item.count * (1 + idf)
          const sourceBonus = item.sources.has('title') ? 1.2 : 1
          
          return {
            ...item,
            count: tfidfScore * sourceBonus,
            documentFrequency: df,
            sources: undefined
          }
        })
        .sort((a, b) => b.count - a.count)
        .slice(0, 30)
      
      this.topKeywords = sortedKeywords
      this.keywordStats = keywordData
      
      this.$nextTick(() => {
        this.initWordCloud()
        if (this.networkChart) {
          this.initNetworkGraph()
        }
      })
    },
    
    extractKeywordsFromType(policyType) {
      const keywords = []
      
      const typeMapping = {
        '汽车消费': [
          { word: '汽车消费', type: 'industry', category: '行业领域' },
          { word: '购车优惠', type: 'policy', category: '政策类型' }
        ],
        '家电消费': [
          { word: '家电消费', type: 'industry', category: '行业领域' },
          { word: '家电补贴', type: 'policy', category: '政策类型' }
        ],
        '文旅消费': [
          { word: '文旅消费', type: 'industry', category: '行业领域' },
          { word: '文旅优惠', type: 'policy', category: '政策类型' }
        ],
        '餐饮消费': [
          { word: '餐饮消费', type: 'industry', category: '行业领域' },
          { word: '餐饮补贴', type: 'policy', category: '政策类型' }
        ],
        '综合消费': [
          { word: '综合消费', type: 'industry', category: '行业领域' },
          { word: '消费券', type: 'policy', category: '政策类型' }
        ]
      }
      
      if (typeMapping[policyType]) {
        typeMapping[policyType].forEach(item => {
          keywords.push(item)
        })
      }
      
      return keywords
    },
    
    extractKeywordsAdvanced(text, source = 'content') {
      const keywords = []
      const extractedWords = new Set()
      
      const keywordPatterns = {
        policy: {
          category: '政策类型',
          priority: 1,
          patterns: [
            { pattern: /以旧换新补贴/g, word: '以旧换新补贴' },
            { pattern: /下乡补贴/g, word: '下乡补贴' },
            { pattern: /购车补贴/g, word: '购车补贴' },
            { pattern: /置换补贴/g, word: '置换补贴' },
            { pattern: /报废补贴/g, word: '报废补贴' },
            { pattern: /消费券/g, word: '消费券' },
            { pattern: /以旧换新/g, word: '以旧换新' },
            { pattern: /补贴政策/g, word: '补贴政策' },
            { pattern: /补贴/g, word: '补贴' },
            { pattern: /奖励政策/g, word: '奖励政策' },
            { pattern: /奖励/g, word: '奖励' },
            { pattern: /优惠政策/g, word: '优惠政策' },
            { pattern: /优惠/g, word: '优惠' },
            { pattern: /扶持政策/g, word: '扶持政策' },
            { pattern: /激励政策/g, word: '激励政策' }
          ]
        },
        amount: {
          category: '补贴金额',
          priority: 2,
          patterns: [
            { 
              pattern: /最高补贴(\d+)万元/g, 
              extractor: (match) => ({ word: `最高补贴${match[1]}万元`, display: '高额补贴' })
            },
            { 
              pattern: /最高(\d+)万元/g, 
              extractor: (match) => ({ word: `最高${match[1]}万元`, display: '高额补贴' })
            },
            { 
              pattern: /补贴(\d+)万元/g, 
              extractor: (match) => ({ word: `补贴${match[1]}万元`, display: '万元级补贴' })
            },
            { 
              pattern: /(\d+)万元补贴/g, 
              extractor: (match) => ({ word: `${match[1]}万元补贴`, display: '万元级补贴' })
            },
            { 
              pattern: /最高补贴(\d+)元/g, 
              extractor: (match) => {
                const amount = parseInt(match[1])
                if (amount >= 5000) return { word: `最高补贴${amount}元`, display: '千元级补贴' }
                return { word: `最高补贴${amount}元`, display: '百元级补贴' }
              }
            },
            { 
              pattern: /补贴(\d+)元/g, 
              extractor: (match) => {
                const amount = parseInt(match[1])
                if (amount >= 5000) return { word: `补贴${amount}元`, display: '千元级补贴' }
                return { word: `补贴${amount}元`, display: '百元级补贴' }
              }
            },
            { 
              pattern: /给予(\d+)元/g, 
              extractor: (match) => {
                const amount = parseInt(match[1])
                if (amount >= 5000) return { word: `给予${amount}元`, display: '千元级补贴' }
                return { word: `给予${amount}元`, display: '百元级补贴' }
              }
            }
          ]
        },
        target: {
          category: '政策对象',
          priority: 3,
          patterns: [
            { pattern: /农村居民/g, word: '农村居民' },
            { pattern: /城镇居民/g, word: '城镇居民' },
            { pattern: /城乡居民/g, word: '城乡居民' },
            { pattern: /消费者/g, word: '消费者' },
            { pattern: /居民/g, word: '居民' },
            { pattern: /企业/g, word: '企业' },
            { pattern: /个人/g, word: '个人' },
            { pattern: /单位/g, word: '单位' },
            { pattern: /家庭/g, word: '家庭' }
          ]
        },
        industry: {
          category: '行业领域',
          priority: 4,
          patterns: [
            { pattern: /新能源汽车/g, word: '新能源汽车' },
            { pattern: /新能源车/g, word: '新能源车' },
            { pattern: /新能源/g, word: '新能源' },
            { pattern: /电动汽车/g, word: '电动汽车' },
            { pattern: /电动车/g, word: '电动车' },
            { pattern: /汽车/g, word: '汽车' },
            { pattern: /家电/g, word: '家电' },
            { pattern: /家用电器/g, word: '家用电器' },
            { pattern: /充电设施/g, word: '充电设施' },
            { pattern: /充电桩/g, word: '充电桩' },
            { pattern: /零售/g, word: '零售' },
            { pattern: /餐饮/g, word: '餐饮' },
            { pattern: /文旅/g, word: '文旅' },
            { pattern: /旅游/g, word: '旅游' }
          ]
        },
        action: {
          category: '政策行动',
          priority: 5,
          patterns: [
            { pattern: /以旧换新/g, word: '以旧换新' },
            { pattern: /报废更新/g, word: '报废更新' },
            { pattern: /置换更新/g, word: '置换更新' },
            { pattern: /购买/g, word: '购买' },
            { pattern: /销售/g, word: '销售' },
            { pattern: /报废/g, word: '报废' },
            { pattern: /置换/g, word: '置换' },
            { pattern: /建设/g, word: '建设' },
            { pattern: /投资/g, word: '投资' },
            { pattern: /推广/g, word: '推广' },
            { pattern: /发放/g, word: '发放' }
          ]
        },
        effect: {
          category: '政策效果',
          priority: 6,
          patterns: [
            { pattern: /促进消费/g, word: '促进消费' },
            { pattern: /拉动消费/g, word: '拉动消费' },
            { pattern: /刺激消费/g, word: '刺激消费' },
            { pattern: /扩大消费/g, word: '扩大消费' },
            { pattern: /提振消费/g, word: '提振消费' },
            { pattern: /释放消费/g, word: '释放消费' }
          ]
        },
        time: {
          category: '时间期限',
          priority: 7,
          patterns: [
            { pattern: /有效期(\d+)年/g, extractor: (match) => ({ word: `有效期${match[1]}年`, display: '长期有效' }) },
            { pattern: /有效期/g, word: '有效期' },
            { pattern: /执行时间/g, word: '执行时间' },
            { pattern: /截止时间/g, word: '截止时间' },
            { pattern: /年内/g, word: '年内' }
          ]
        },
        other: {
          category: '其他',
          priority: 8,
          patterns: [
            { pattern: /财政支持/g, word: '财政支持' },
            { pattern: /财政/g, word: '财政' },
            { pattern: /资金支持/g, word: '资金支持' },
            { pattern: /资金/g, word: '资金' },
            { pattern: /绿色发展/g, word: '绿色发展' },
            { pattern: /绿色/g, word: '绿色' },
            { pattern: /环保/g, word: '环保' },
            { pattern: /创新/g, word: '创新' },
            { pattern: /数字化/g, word: '数字化' },
            { pattern: /智能/g, word: '智能' }
          ]
        }
      }
      
      const sortedTypes = Object.keys(keywordPatterns).sort(
        (a, b) => keywordPatterns[a].priority - keywordPatterns[b].priority
      )
      
      sortedTypes.forEach(type => {
        const categoryData = keywordPatterns[type]
        
        categoryData.patterns.forEach(item => {
          if (item.pattern.source.includes('以旧换新') && extractedWords.has('以旧换新补贴')) {
            return
          }
          if (item.pattern.source.includes('新能源') && extractedWords.has('新能源汽车')) {
            return
          }
          if (item.pattern.source.includes('汽车') && 
              (extractedWords.has('新能源汽车') || extractedWords.has('新能源车'))) {
            return
          }
          
          const matches = text.match(item.pattern)
          if (matches) {
            if (item.extractor) {
              matches.forEach(match => {
                const extracted = item.extractor(match)
                const word = extracted.display || extracted.word
                
                if (!extractedWords.has(word)) {
                  keywords.push({
                    word: word,
                    type: type,
                    category: categoryData.category
                  })
                  extractedWords.add(word)
                }
              })
            } else {
              const word = item.word
              if (!extractedWords.has(word)) {
                keywords.push({
                  word: word,
                  type: type,
                  category: categoryData.category
                })
                extractedWords.add(word)
              }
            }
          }
        })
      })
      
      return keywords
    },
    
    initWordCloud() {
      if (!this.$refs.wordCloudChart) return
      
      if (this.wordCloudChart) {
        this.wordCloudChart.dispose()
      }
      
      this.wordCloudChart = echarts.init(this.$refs.wordCloudChart)
      
      const data = this.topKeywords.slice(0, 15)
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: '{b}: {c}次'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '8%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: data.map(item => item.word),
          axisLabel: {
            interval: 0,
            rotate: 30,
            fontSize: 11,
            color: '#666'
          },
          axisLine: {
            lineStyle: {
              color: '#e8e8e8'
            }
          },
          axisTick: {
            show: false
          }
        },
        yAxis: {
          type: 'value',
          name: '出现次数',
          nameTextStyle: {
            color: '#999',
            fontSize: 11
          },
          axisLabel: {
            color: '#666',
            fontSize: 11
          },
          axisLine: {
            show: false
          },
          axisTick: {
            show: false
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0'
            }
          }
        },
        series: [{
          name: '关键词频次',
          type: 'bar',
          barWidth: '50%',
          data: data.map((item, index) => ({
            value: Math.round(item.count),
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#1890ff' },
                { offset: 1, color: '#69c0ff' }
              ]),
              borderRadius: [4, 4, 0, 0]
            }
          })),
          label: {
            show: true,
            position: 'top',
            fontSize: 10,
            color: '#666',
            formatter: '{c}'
          }
        }]
      }
      
      this.wordCloudChart.setOption(option)
    },
    
    analyzeTopics() {
      const topics = [
        {
          name: '新能源汽车',
          icon: 'fas fa-car',
          keywords: ['新能源', '汽车', '购车', '充电', '电动车'],
          count: 0,
          percentage: 0
        },
        {
          name: '消费补贴',
          icon: 'fas fa-hand-holding-usd',
          keywords: ['补贴', '消费券', '优惠', '奖励', '财政'],
          count: 0,
          percentage: 0
        },
        {
          name: '以旧换新',
          icon: 'fas fa-exchange-alt',
          keywords: ['以旧换新', '报废', '置换', '旧车'],
          count: 0,
          percentage: 0
        },
        {
          name: '农村市场',
          icon: 'fas fa-tractor',
          keywords: ['农村', '下乡', '乡村', '县域'],
          count: 0,
          percentage: 0
        },
        {
          name: '基础设施',
          icon: 'fas fa-charging-station',
          keywords: ['充电', '设施', '建设', '基础设施'],
          count: 0,
          percentage: 0
        },
        {
          name: '绿色消费',
          icon: 'fas fa-leaf',
          keywords: ['绿色', '环保', '节能', '低碳'],
          count: 0,
          percentage: 0
        }
      ]
      
      this.policyData.forEach(policy => {
        const content = policy['政策主要内容'] || ''
        
        topics.forEach(topic => {
          const hasKeyword = topic.keywords.some(kw => content.includes(kw))
          if (hasKeyword) {
            topic.count++
          }
        })
      })
      
      const total = this.policyData.length || 1
      topics.forEach(topic => {
        topic.percentage = Math.round((topic.count / total) * 100)
      })
      
      this.policyTopics = topics.sort((a, b) => b.count - a.count)
    },
    
    analyzeSummary() {
      const highlights = []
      
      const totalAmount = this.calculateTotalAmount()
      if (totalAmount > 0) {
        highlights.push({
          title: '补贴金额规模',
          content: `政策涉及补贴金额累计约${totalAmount}万元，体现了政府对促消费的大力支持。`
        })
      }
      
      const topProvince = this.getTopProvince()
      if (topProvince) {
        highlights.push({
          title: '政策活跃地区',
          content: `${topProvince}发布的促消费政策数量最多，显示出该地区对促消费工作的高度重视。`
        })
      }
      
      const topCategory = this.getTopCategory()
      if (topCategory) {
        highlights.push({
          title: '主要政策类型',
          content: `${topCategory}类政策占比最高，是当前促消费政策的主要形式。`
        })
      }
      
      const avgDuration = this.calculateAverageDuration()
      if (avgDuration > 0) {
        highlights.push({
          title: '政策有效期',
          content: `政策平均有效期约为${avgDuration}个月，体现了政策的持续性和稳定性。`
        })
      }
      
      highlights.push({
        title: '政策覆盖范围',
        content: `政策覆盖${this.coveredProvinces}个省份和${this.coveredCities}个城市，形成了较为完善的促消费政策网络。`
      })
      
      this.policyHighlights = highlights
    },
    
    calculateTotalAmount() {
      let total = 0
      this.policyData.forEach(policy => {
        const content = policy['政策主要内容'] || ''
        const matches = content.match(/(\d+)万元/g)
        if (matches) {
          matches.forEach(match => {
            const amount = parseInt(match)
            total += amount
          })
        }
      })
      return total
    },
    
    getTopProvince() {
      const counts = this.getProvinceCounts()
      const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1])
      return sorted.length > 0 ? sorted[0][0] : null
    },
    
    getTopCategory() {
      const stats = this.categoryStats
      const sorted = Object.entries(stats).sort((a, b) => b[1].count - a[1].count)
      return sorted.length > 0 ? sorted[0][0] : null
    },
    
    calculateAverageDuration() {
      let totalMonths = 0
      let count = 0
      
      this.policyData.forEach(policy => {
        const startTime = policy['执行时间']
        const endTime = policy['结束时间']
        
        if (startTime && endTime) {
          const start = new Date(startTime)
          const end = new Date(endTime)
          const months = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth())
          if (months > 0) {
            totalMonths += months
            count++
          }
        }
      })
      
      return count > 0 ? Math.round(totalMonths / count) : 0
    },
    
    handleSmartSearch() {
      if (!this.smartSearchQuery.trim()) {
        this.smartSearchResults = []
        return
      }
      
      const query = this.smartSearchQuery.toLowerCase().trim()
      const results = []
      
      this.policyData.forEach(policy => {
        const title = (policy['政策名称'] || '').toLowerCase()
        const content = (policy['政策主要内容'] || '').toLowerCase()
        const category = (policy['政策分类'] || '').toLowerCase()
        const province = (policy['省/直辖市/自治区'] || '').toLowerCase()
        const city = (policy['地级市/自治州'] || '').toLowerCase()
        
        let relevanceScore = 0
        let matched = false
        
        if (title.includes(query)) {
          relevanceScore += 10
          matched = true
        }
        if (content.includes(query)) {
          const matchCount = (content.match(new RegExp(query, 'g')) || []).length
          relevanceScore += matchCount * 2
          matched = true
        }
        if (category.includes(query)) {
          relevanceScore += 5
          matched = true
        }
        if (province.includes(query) || city.includes(query)) {
          relevanceScore += 3
          matched = true
        }
        
        if (matched) {
          results.push({
            ...policy,
            relevanceScore: relevanceScore
          })
        }
      })
      
      if (this.searchSortBy === 'relevance') {
        results.sort((a, b) => b.relevanceScore - a.relevanceScore)
      } else {
        results.sort((a, b) => {
          const dateA = new Date(a['执行时间'] || 0)
          const dateB = new Date(b['执行时间'] || 0)
          return dateB - dateA
        })
      }
      
      this.smartSearchResults = results
      this.searchCurrentPage = 1
      this.highlightNetworkNodes(this.smartSearchQuery)
    },
    
    clearSmartSearch() {
      this.smartSearchQuery = ''
      this.smartSearchResults = []
      this.searchCurrentPage = 1
      this.highlightNetworkNodes('')
    },
    
    applySuggestion(suggestion) {
      this.smartSearchQuery = suggestion
      this.handleSmartSearch()
    },
    
    highlightKeyword(text, keyword) {
      if (!text || !keyword) return text
      const regex = new RegExp(`(${keyword})`, 'gi')
      return text.replace(regex, '<mark class="highlight">$1</mark>')
    },
    
    truncateText(text, maxLength) {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    },
    
    initNetworkGraph() {
      if (!this.$refs.networkGraph) return
      
      if (this.networkChart) {
        this.networkChart.dispose()
      }
      
      this.networkChart = echarts.init(this.$refs.networkGraph)
      
      const graphData = this.buildNetworkData()
      
      if (!graphData.nodes || graphData.nodes.length === 0) {
        console.warn('No network data available')
        return
      }
      

      const echartLayout = this.networkLayout === 'radial' ? 'force' : this.networkLayout

      const option = {
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e8e8e8',
          borderWidth: 1,
          padding: [8, 12],
          textStyle: {
            color: '#333',
            fontSize: 12
          },
          formatter: (params) => {
            if (params.dataType === 'node') {
              return `<div style="font-weight: 600; margin-bottom: 4px;">${params.name}</div>
                      <div style="color: #666; font-size: 11px;">类型: ${this.getNodeTypeName(params.data.nodeType)}</div>
                      <div style="color: #666; font-size: 11px;">关联政策: ${params.data.policyCount || 0}项</div>`
            }
            return null
          }
        },
        series: [{
          type: 'graph',
          layout:echartLayout,
          symbolSize: 30,
          roam: true,
          draggable: true,
          label: {
            show: true,
            position: 'right',
            fontSize: 11,
            color: '#333',
            formatter: '{b}',
            distance: 5
          },
          edgeSymbol: ['none', 'arrow'],
          edgeSymbolSize: [2, 6],
          data: graphData.nodes,
          links: graphData.links,
          lineStyle: {
            color: '#d9d9d9',
            curveness: 0.1,
            opacity: 0.4,
            width: 1
          },
          emphasis: {
            focus: 'adjacency',
            itemStyle: {
              shadowBlur: 8,
              shadowColor: 'rgba(0, 0, 0, 0.2)'
            },
            lineStyle: {
              width: 2,
              color: '#3498db'
            }
          },
          categories: [
            { name: 'province', itemStyle: { color: '#3498db' } },
            { name: 'category', itemStyle: { color: '#e74c3c' } },
            { name: 'keyword', itemStyle: { color: '#2ecc71' } },
            { name: 'center', itemStyle: { color: '#f39c12' } }
          ],
          force: {
            repulsion: 300,
            edgeLength: [80, 150],
            gravity: 0.08,
            friction: 0.6
          },
          circular: {
            rotateLabel: true
          },
          radial: {
            rotateLabel: true,
            root: '政策网络'
          }
        }]
      }
      
      this.networkChart.setOption(option)
      
      this.networkChart.on('click', (params) => {
        if (params.dataType === 'node') {
          if (this.selectedNode && this.selectedNode.name === params.name) {
            this.selectedNode = null
            this.smartSearchQuery = ''
            this.smartSearchResults = []
            this.highlightNetworkNodes('')
          } else {
            this.selectedNode = {
              name: params.name,
              type: params.data.nodeType,
              policyCount: params.data.policyCount || 0,
              connections: params.data.connections || 0
            }
            if (params.data.nodeType === 'keyword' || params.data.nodeType === 'category' || params.data.nodeType === 'province') {
              this.smartSearchQuery = params.name
              this.handleSmartSearch()
              this.$nextTick(() => {
                const searchCard = document.querySelector('.smart-search-card')
                if (searchCard) {
                  searchCard.scrollIntoView({ behavior: 'smooth', block: 'start' })
                }
              })
            }
          }
        }
      })
    },
    
    buildNetworkData() {
      const nodes = []
      const links = []
      const nodeMap = new Map()
      
      const categoryColors = {
        center: '#f39c12',
        province: '#3498db',
        category: '#e74c3c',
        keyword: '#2ecc71'
      }
      
      if (this.networkLayout === 'radial') {
        nodes.push({
          id: 'center',
          name: '政策网络',
          nodeType: 'center',
          policyCount: this.policyData.length,
          category: 3,
          value: this.policyData.length,
          itemStyle: {
            color: categoryColors.center
          }
        })
        nodeMap.set('center', 0)
      }
      
      const provinceCounts = this.getProvinceCounts()
      Object.entries(provinceCounts).forEach(([name, count]) => {
        if (count > 0) {
          const nodeId = `province_${name}`
          nodeMap.set(nodeId, nodes.length)
          nodes.push({
            id: nodeId,
            name: name,
            nodeType: 'province',
            policyCount: count,
            category: 0,
            value: count,
            itemStyle: {
              color: categoryColors.province
            }
          })
        }
      })
      
      Object.entries(this.categoryStats).forEach(([name, stat]) => {
        const nodeId = `category_${name}`
        nodeMap.set(nodeId, nodes.length)
        nodes.push({
          id: nodeId,
          name: name,
          nodeType: 'category',
          policyCount: stat.count,
          category: 1,
          value: stat.count,
          itemStyle: {
            color: categoryColors.category
          }
        })
      })
      
      this.topKeywords.slice(0, 30).forEach((keyword) => {
        const nodeId = `keyword_${keyword.word}`
        nodeMap.set(nodeId, nodes.length)
        nodes.push({
          id: nodeId,
          name: keyword.word,
          nodeType: 'keyword',
          policyCount: Math.round(keyword.count),
          category: 2,
          value: keyword.count,
          itemStyle: {
            color: categoryColors.keyword
          }
        })
      })
      
      if (this.networkLayout === 'radial') {
        nodes.forEach(node => {
          if (node.id !== 'center') {
            links.push({
              id: `center-${node.id}`,
              source: 'center',
              target: node.id,
              value: 1
            })
          }
        })
      } else {
        this.policyData.forEach(policy => {
          const province = policy['省/直辖市/自治区']
          const category = policy['政策分类']
          
          if (province && category) {
            const provinceId = `province_${province}`
            const categoryId = `category_${category}`
            
            if (nodeMap.has(provinceId) && nodeMap.has(categoryId)) {
              const linkId = `${provinceId}-${categoryId}`
              if (!links.find(l => l.id === linkId)) {
                links.push({
                  id: linkId,
                  source: provinceId,
                  target: categoryId,
                  value: 1
                })
              }
            }
          }
        })
      }


      const totalPossibleLinks = nodes.length * (nodes.length - 1) / 2
      const density = totalPossibleLinks > 0 ? (links.length / totalPossibleLinks * 100).toFixed(2) : 0
      
      this.networkStats = {
        nodes: nodes.length,
        links: links.length,
        density: density + '%'
      }
      
      nodes.forEach(node => {
        node.connections = links.filter(l => l.source === node.id || l.target === node.id).length
      })
      
      return { nodes, links }
    },
    
    getNodeTypeName(type) {
      const names = {
        province: '省份',
        category: '政策分类',
        keyword: '关键词',
        center: '中心节点'
      }
      return names[type] || type
    },
    
    getNodeIcon(type) {
      const icons = {
        province: 'fas fa-map-marker-alt',
        category: 'fas fa-tag',
        keyword: 'fas fa-key',
        center: 'fas fa-network-wired'
      }
      return icons[type] || 'fas fa-circle'
    },
    
    highlightNetworkNodes(query) {
      if (!this.networkChart) return
      
      if (!query || !query.trim()) {
        const currentOption = this.networkChart.getOption()
        const nodes = currentOption.series[0].data
        
        const updatedNodes = nodes.map(node => ({
          ...node,
          itemStyle: {
            ...node.itemStyle,
            opacity: 1
          },
          label: {
            ...node.label,
            opacity: 1
          }
        }))
        
        this.networkChart.setOption({
          series: [{
            data: updatedNodes
          }]
        })
        return
      }
      
      const currentOption = this.networkChart.getOption()
      const nodes = currentOption.series[0].data
      const queryLower = query.toLowerCase().trim()
      
      const updatedNodes = nodes.map(node => {
        const isMatch = node.name.toLowerCase().includes(queryLower)
        return {
          ...node,
          itemStyle: {
            ...node.itemStyle,
            opacity: isMatch ? 1 : 0.2
          },
          label: {
            ...node.label,
            opacity: isMatch ? 1 : 0.3
          }
        }
      })
      
      this.networkChart.setOption({
        series: [{
          data: updatedNodes
        }]
      })
    },
    
    updateNetworkGraph() {
      this.initNetworkGraph()
    },
    
    resetNetworkGraph() {
      this.networkLayout = 'force'
      this.selectedNode = null
      this.initNetworkGraph()
    }
  }
}
</script>

<style scoped>
.policy-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

/* 数据统计仪表盘样式 */
.dashboard-section {
  margin-bottom: 20px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.total {
  background: #e8f4fd;
  color: #1890ff;
}

.stat-icon.new {
  background: #f6ffed;
  color: #52c41a;
}

.stat-icon.expiring {
  background: #fff7e6;
  color: #fa8c16;
}

.stat-icon.cities {
  background: #e6fffb;
  color: #13c2c2;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

/* 图表区域样式 */
.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid #e8e8e8;
}

.trend-card {
  grid-column: 1;
  grid-row: 1;
}

.pie-card {
  grid-column: 2;
  grid-row: 1;
}

.ranking-card {
  grid-column: 3;
  grid-row: 1 / 3;
  display: flex;
  flex-direction: column;
}

.category-stats-card {
  grid-column: 1 / 3;
  grid-row: 2;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid #e8e8e8;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.chart-title span {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.chart-title i {
  color: #3498db;
  font-size: 18px;
}

.chart-subtitle {
  font-size: 12px;
  color: #999;
}

.chart-container {
  height: 250px;

}

/* 排行榜样式 */
.ranking-list {
  flex: 1;
  padding: 12px 20px;
  overflow-y: auto;
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}

.ranking-item:last-child {
  border-bottom: none;
}

.ranking-item.top-three {
  background: linear-gradient(90deg, #fff9e6 0%, transparent 100%);
  margin: 0 -20px;
  padding: 10px 20px;
}

.ranking-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #999;
  background: #f0f0f0;
  margin-right: 12px;
  flex-shrink: 0;
}

.ranking-number.rank-1 {
  background: linear-gradient(135deg, #ffd700 0%, #ffb347 100%);
  color: white;
}

.ranking-number.rank-2 {
  background: linear-gradient(135deg, #c0c0c0 0%, #a8a8a8 100%);
  color: white;
}

.ranking-number.rank-3 {
  background: linear-gradient(135deg, #cd7f32 0%, #b87333 100%);
  color: white;
}

.ranking-name {
  flex: 0 0 80px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.ranking-bar-container {
  flex: 1;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  margin: 0 12px;
  overflow: hidden;
}

.ranking-bar {
  height: 100%;
  background: #1890ff;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.ranking-value {
  flex: 0 0 50px;
  font-size: 14px;
  color: #666;
  text-align: right;
}

.category-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  padding: 16px 20px;
}

.category-card {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  background: #f8f9fa;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.category-card:hover {
  background: #f0f4ff;
  transform: translateX(4px);
}

.category-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #f0f5ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2f54eb;
  font-size: 18px;
  margin-right: 12px;
}

.category-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.category-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.category-count {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.category-percentage {
  font-size: 16px;
  font-weight: 600;
  color: #667eea;
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

.header-controls {
  display: flex;
  gap: 10px;
}

.content-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.map-section {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  min-width: 600px;
}

.map-header {
  margin-bottom: 20px;
}

.map-header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.map-header-left {
  flex: 1;
}

.province-search {
  position: relative;
  margin-top: 15px;
}

.search-input {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.search-input:focus {
  border-color: #3498db;
}

.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-top: none;
  border-radius: 0 0 4px 4px;
  max-height: 250px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.suggestion-item {
  padding: 10px 15px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.suggestion-item:hover {
  background-color: #f5f5f5;
}

.filter-row {
  display: flex;
  gap: 15px;
  margin-top: 15px;
}

.city-search {
  position: relative;
  flex: 1;
  max-width: 290px;
}

.category-filter {
  flex: 1;
  max-width: 150px;
}

.category-select {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
  background: white;
  cursor: pointer;
  box-sizing: border-box;
}

.category-select:focus {
  border-color: #3498db;
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

.china-map {
  width: 100%;
  height: 500px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.map-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 15px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
}

.legend-color.color-1 {
  background: #e0f3f8;
}

.legend-color.color-2 {
  background: #abd9e9;
}

.legend-color.color-3 {
  background: #74add1;
}

.legend-color.color-4 {
  background: #4575b4;
}

.legend-text {
  font-size: 12px;
  color: #666;
}

.policy-section {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  min-width: 400px;
  max-width: 500px;
}

.policy-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.policy-list {
  max-height: 600px;
  overflow-y: auto;
}

.policy-list.expanded {
  max-height: 880px;
}

.loading-container,
.empty-container {
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
.empty-text {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.empty-icon {
  font-size: 48px;
  color: #ddd;
  margin-bottom: 15px;
}

.policy-cards {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.policy-card {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
  background: #fafafa;
  transition: all 0.3s;
}

.policy-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.policy-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.policy-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  flex: 1;
}

.policy-date {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
  margin-left: 10px;
}

.policy-card-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.policy-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item {
  display: flex;
  align-items: center;
  font-size: 12px;
}

.info-icon {
  width: 16px;
  color: #3498db;
  margin-right: 8px;
}

.info-label {
  color: #666;
  margin-right: 5px;
}

.info-value {
  color: #333;
  font-weight: 500;
}

.policy-content {
  margin-top: 5px;
}

.content-title {
  margin: 0 0 5px 0;
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.content-text {
  margin: 0;
  font-size: 12px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.policy-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
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
  justify-content: center;
}

.btn-gray {
  background: #f0f0f0;
  color: #333;
}

.btn-gray:hover {
  background: #e0e0e0;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover {
  background: #2980b9;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.mr-1 {
  margin-right: 4px;
}

.placeholder-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 500px;
}

.placeholder-content {
  text-align: center;
  padding: 40px;
}

.placeholder-icon {
  font-size: 64px;
  color: #ddd;
  margin-bottom: 20px;
}

.placeholder-title {
  margin: 0 0 10px 0;
  font-size: 18px;
  color: #666;
}

.placeholder-text {
  margin: 0;
  font-size: 14px;
  color: #999;
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
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 650px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.modal-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-icon {
  color: #3498db;
  font-size: 18px;
}

.modal-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 16px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.modal-close:hover {
  color: #333;
  background: #f0f0f0;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.detail-section {
  background: #fafafa;
  border-radius: 6px;
  padding: 12px 14px;
  border: 1px solid #e8e8e8;
}

.detail-section.policy-name-section {
  background: #e8f4fd;
  border-color: #d6e9f8;
  margin-bottom: 16px;
}

.detail-section.content-section {
  grid-column: 1 / -1;
}

.detail-title {
  margin: 0 0 8px 0;
  font-size: 13px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
}

.detail-title i {
  color: #3498db;
  font-size: 12px;
}

.detail-text {
  margin: 0;
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

.detail-text.policy-name {
  font-size: 15px;
  font-weight: 500;
  color: #333;
}

.detail-text.content-text {
  max-height: 200px;
  overflow-y: auto;
  padding-right: 8px;
}

.detail-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #3498db;
  text-decoration: none;
  font-size: 13px;
  padding: 6px 12px;
  background: #e8f4fd;
  border-radius: 4px;
  transition: all 0.2s;
}

.detail-link:hover {
  background: #3498db;
  color: white;
}

.modal-footer {
  padding: 12px 20px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  background: #fafafa;
}

@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 90vh;
  }
  
  .modal-header {
    padding: 12px 16px;
  }
  
  .modal-body {
    padding: 16px;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .detail-section {
    padding: 10px 12px;
  }
  
  .detail-section.policy-name-section {
    margin-bottom: 12px;
  }
  
  .detail-text.policy-name {
    font-size: 14px;
  }
  
  .detail-text.content-text {
    max-height: 150px;
  }
}

/* 响应式样式 */
@media (max-width: 1400px) {
  .charts-section {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto auto;
  }
  
  .trend-card {
    grid-column: 1;
    grid-row: 1;
  }
  
  .pie-card {
    grid-column: 2;
    grid-row: 1;
  }
  
  .category-stats-card {
    grid-column: 1 / 3;
    grid-row: 2;
  }
  
  .ranking-card {
    grid-column: 1 / 3;
    grid-row: 3;
  }
}

@media (max-width: 1200px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-section {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }
  
  .trend-card,
  .pie-card,
  .category-stats-card,
  .ranking-card {
    grid-column: 1;
    grid-row: auto;
  }
  
  .content-section {
    flex-direction: column;
  }
  
  .map-section {
    min-width: auto;
  }
}

@media (max-width: 768px) {
  .stat-cards {
    grid-template-columns: 1fr;
  }
  
  .header-section {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .header-controls {
    width: 100%;
    justify-content: flex-end;
  }
  
  .map-header-top {
    flex-direction: column;
    gap: 15px;
  }
  
  .map-header-top .header-controls {
    width: auto;
  }
  
  .category-cards-grid {
    grid-template-columns: 1fr;
  }
}

/* 时空动态可视化样式 - 简约企业级设计 */
.time-control-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
  border: 1px solid #e8e8e8;
  overflow: hidden;
  transition: all 0.3s ease;
}

.time-control-panel.is-time-playing {
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.15);
  border-color: #3498db;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.panel-title i {
  color: #3498db;
  font-size: 14px;
}

.btn-close {
  background: none;
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #f5f5f5;
  color: #666;
}

.panel-content {
  padding: 16px;
}

/* 时间轴部分 */
.time-axis-section {
  margin-bottom: 16px;
}

.time-axis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.time-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.time-range-value {
  font-size: 12px;
  color: #3498db;
  font-weight: 500;
}

.time-controls {
  display: flex;
  gap: 8px;
}

.btn-control {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 11px;
}

.btn-control:hover:not(:disabled) {
  border-color: #3498db;
  color: #3498db;
  background: #f0f7ff;
}

.btn-control:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-control.btn-primary {
  background: #3498db;
  border-color: #3498db;
  color: white;
}

.btn-control.btn-primary:hover:not(:disabled) {
  background: #2980b9;
  border-color: #2980b9;
}

.btn-control.btn-secondary {
  background: #f0f0f0;
  border-color: #d9d9d9;
  color: #666;
}

.btn-control.btn-secondary:hover:not(:disabled) {
  background: #e0e0e0;
  border-color: #ccc;
}

/* 时间滑块 */
.time-slider-container {
  position: relative;
  padding: 8px 0 48px;
}

.time-slider {
  position: absolute;
  width: 100%;
  height: 20px;
  opacity: 0;
  z-index: 2;
  cursor: pointer;
}

.time-slider-track {
  position: absolute;
  width: 100%;
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  top: 18px;
  z-index: 1;
}

.time-slider-progress {
  position: absolute;
  height: 100%;
  background: #3498db;
  border-radius: 2px;
  transition: width 0.15s ease;
}

.time-marks {
  position: relative;
  height: 18px;
  margin-top: 8px;
}

.time-mark {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.time-mark::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d9d9d9;
  transition: all 0.2s;
}

.time-mark.active::before {
  background: #3498db;
  transform: scale(1.2);
}

.mark-label {
  position: absolute;
  top: 16px;
  font-size: 10px;
  color: #999;
  white-space: nowrap;
  transform: translateX(-50%);
}

.time-mark:first-child .mark-label {
  transform: translateX(10%);
}

.time-mark:last-child .mark-label {
  transform: translateX(-40%);
}

.time-mark.active .mark-label {
  color: #3498db;
  font-weight: 500;
}

/* 状态信息 */
.status-section {
  margin-bottom: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.status-item {
  display: flex;
  flex-direction: column;
}

.status-label {
  font-size: 11px;
  color: #666;
  margin-bottom: 3px;
}

.status-value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.status-select {
  margin-top: 4px;
}

.speed-select {
  width: 100%;
  padding: 5px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: white;
  font-size: 11px;
  color: #333;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s;
}

.speed-select:focus {
  border-color: #3498db;
}

/* 时间点指示器 */
.time-indicator {
  padding: 10px 12px;
  background: #e8f4fd;
  border-radius: 6px;
  border-left: 3px solid #3498db;
}

.indicator-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.indicator-icon {
  color: #3498db;
  font-size: 14px;
}

.indicator-text {
  flex: 1;
}

.indicator-title {
  font-size: 12px;
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
}

.indicator-subtitle {
  font-size: 11px;
  color: #666;
}

/* 地图切换按钮 */
.map-container {
  position: relative;
}

.map-credits {
  position: absolute;
  bottom: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  font-size: 11px;
  color: #999;
  background: rgba(255, 255, 255, 0.8);
  padding: 4px 8px;
  border-radius: 4px;
}

.time-toggle-button {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
}

.btn-time-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.btn-time-toggle:hover {
  border-color: #3498db;
  color: #3498db;
  background: #f0f7ff;
}

.btn-time-toggle i {
  font-size: 13px;
}

/* 动画效果 */
@keyframes time-playing {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

.is-time-playing .panel-title i {
  animation: time-playing 1s infinite;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .status-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .time-axis-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .time-controls {
    width: 100%;
    justify-content: center;
  }
  
  .mark-label {
    font-size: 10px;
  }
  
  .btn-time-toggle span {
    display: none;
  }
  
  .btn-time-toggle {
    padding: 8px;
  }
}

/* 多维度对比卡片样式 */
.comparison-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-top: 20px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.comparison-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.comparison-title i {
  color: #3498db;
  font-size: 18px;
}

.comparison-content {
  padding: 20px;
}

.dimension-selector {
  margin-bottom: 24px;
}

.selector-header {
  margin-bottom: 12px;
}

.selector-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.selector-options {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.dimension-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
  font-size: 13px;
  color: #666;
}

.dimension-option:hover {
  border-color: #3498db;
  color: #3498db;
}

.dimension-option.active {
  border-color: #3498db;
  background: #e8f4fd;
  color: #3498db;
  font-weight: 500;
}

.dimension-option i {
  font-size: 14px;
}

.comparison-items-section {
  margin-bottom: 24px;
}

.items-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.items-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.items-hint {
  font-size: 12px;
  color: #999;
}

.items-selector {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.items-search {
  padding: 12px;
  background: #fafafa;
  border-bottom: 1px solid #e0e0e0;
}

.items-search .search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.items-search .search-input:focus {
  border-color: #3498db;
}

.items-list {
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
}

.item-checkbox {
  padding: 8px 12px;
  border-radius: 4px;
  transition: background 0.2s;
}

.item-checkbox:hover {
  background: #f5f5f5;
}

.item-checkbox.disabled {
  opacity: 0.5;
}

.item-checkbox label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
}

.item-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.checkbox-label {
  color: #333;
  font-weight: 500;
}

.checkbox-count {
  color: #999;
  font-size: 12px;
}

.comparison-results {
  border-top: 1px solid #e0e0e0;
  padding-top: 24px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.results-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.results-actions {
  display: flex;
  gap: 8px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.2s;
}

.btn-sm:hover {
  background: #2980b9;
}

.comparison-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  background: #fafafa;
  border-radius: 6px;
  padding: 16px;
  border: 1px solid #e0e0e0;
}

.chart-card .chart-header {
  margin-bottom: 12px;
}

.chart-card .chart-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.chart-container {
  height: 250px;
}

.comparison-table-section {
  background: #fafafa;
  border-radius: 6px;
  padding: 16px;
  border: 1px solid #e0e0e0;
}

.table-header {
  margin-bottom: 12px;
}

.table-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.comparison-table-container {
  overflow-x: auto;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.comparison-table th,
.comparison-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.comparison-table th {
  background: #f5f5f5;
  font-weight: 600;
  color: #666;
  font-size: 12px;
}

.comparison-table tbody tr:hover {
  background: #f9f9f9;
}

.comparison-table .item-name {
  font-weight: 500;
  color: #333;
}

.comparison-table .item-value {
  color: #3498db;
  font-weight: 600;
}

.comparison-table .item-percentage {
  color: #666;
}

.comparison-table .item-active {
  color: #27ae60;
}

.comparison-table .item-expired {
  color: #e74c3c;
}

.comparison-table .item-duration {
  color: #666;
}

@media (max-width: 1200px) {
  .comparison-charts {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .selector-options {
    flex-direction: column;
  }
  
  .dimension-option {
    width: 100%;
    justify-content: center;
  }
}

/* 政策文本智能分析卡片样式 */
.text-analysis-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-top: 20px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.analysis-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.analysis-title i {
  color: #9b59b6;
  font-size: 18px;
}

.analysis-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.analysis-select {
  padding: 6px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
  color: #333;
  background: white;
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
}

.analysis-select:focus {
  border-color: #3498db;
}

.analysis-content {
  padding: 20px;
}

/* 关键词分析样式 */
.keywords-analysis {
  display: block;
}

.analysis-section {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e8e8e8;
}

.analysis-section.full-width {
  grid-column: 1 / -1;
}

.analysis-section .section-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}

.keywords-chart {
  height: 350px;
}

/* 主题分析样式 */
.topics-analysis {
  margin-top: 0;
}

.topics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.topic-card {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s;
}

.topic-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.topic-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.topic-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
  color: white;
  font-size: 18px;
}

.topic-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.topic-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.topic-stats {
  display: flex;
  gap: 16px;
}

.topic-stats .stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.topic-stats .stat-label {
  font-size: 11px;
  color: #999;
}

.topic-stats .stat-number {
  font-size: 16px;
  font-weight: 600;
  color: #3498db;
}

.topic-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.topic-keyword {
  padding: 4px 8px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 11px;
  color: #666;
}

/* 文本摘要样式 */
.summary-analysis {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.summary-section {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e8e8e8;
}

.summary-section .section-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.summary-stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.summary-stat-card .stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  color: white;
  font-size: 18px;
}

.summary-stat-card .stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-stat-card .stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.summary-stat-card .stat-label {
  font-size: 11px;
  color: #999;
}

.policy-highlights {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.highlight-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.highlight-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
  color: white;
  font-size: 14px;
  flex-shrink: 0;
}

.highlight-content {
  flex: 1;
}

.highlight-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin: 0 0 6px 0;
}

.highlight-text {
  font-size: 12px;
  color: #666;
  margin: 0;
  line-height: 1.6;
}

@media (max-width: 1200px) {
  .keywords-analysis {
    grid-template-columns: 1fr;
  }
  
  .topics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .network-search-row {
    flex-direction: column;
  }
  
  .network-search-row .smart-search-card {
    width: 100%;
    max-height: none;
  }
}

@media (max-width: 768px) {
  .analysis-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .analysis-controls {
    width: 100%;
  }
  
  .analysis-select {
    flex: 1;
  }
  
  .topics-grid {
    grid-template-columns: 1fr;
  }
  
  .summary-stats {
    grid-template-columns: 1fr;
  }
}

.smart-search-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid #e8e8e8;
}

.search-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.search-card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.search-card-title i {
  color: #3498db;
  font-size: 18px;
}

.search-card-subtitle {
  font-size: 12px;
  color: #999;
}

.search-card-body {
  padding: 20px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input-wrapper .search-icon {
  position: absolute;
  left: 14px;
  color: #bbb;
  font-size: 14px;
}

.smart-search-input {
  width: 100%;
  padding: 10px 40px 10px 40px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.2s;
  outline: none;
  background: white;
}

.smart-search-input:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.1);
}

.smart-search-input::placeholder {
  color: #bbb;
}

.clear-search-btn {
  position: absolute;
  right: 10px;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 12px;
  transition: all 0.2s ease;
}

.clear-search-btn:hover {
  color: #666;
}

.search-suggestions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
}

.suggestion-label {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

.suggestion-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.suggestion-tag {
  padding: 3px 10px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s ease;
}

.suggestion-tag:hover {
  border-color: #3498db;
  color: #3498db;
}

.search-results {
  margin-top: 16px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.results-count {
  font-size: 13px;
  color: #666;
}

.results-count strong {
  color: #3498db;
}

.results-sort .sort-select {
  padding: 5px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  background: white;
  cursor: pointer;
  outline: none;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.3s;
}

.result-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.result-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  flex: 1;
  line-height: 1.4;
}

.result-title :deep(.highlight) {
  background: #fff3cd;
  color: #856404;
  padding: 0 2px;
  border-radius: 2px;
}

.result-category {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
  margin-left: 10px;
  padding: 2px 8px;
  background: #e8f4fd;
  color: #1890ff;
  border-radius: 4px;
}

.result-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.meta-item {
  display: flex;
  align-items: center;
  font-size: 12px;
}

.meta-item i {
  width: 16px;
  color: #3498db;
  margin-right: 8px;
  font-size: 12px;
}

.meta-item .info-label {
  color: #666;
  margin-right: 5px;
}

.meta-item .info-value {
  color: #333;
  font-weight: 500;
}

.result-content-wrapper {
  margin-top: 5px;
}

.content-title {
  margin: 0 0 5px 0;
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.result-content {
  margin: 0;
  font-size: 12px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-content :deep(.highlight) {
  background: #fff3cd;
  color: #856404;
  padding: 0 2px;
  border-radius: 2px;
}

.result-tags {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.result-tags .tag {
  padding: 4px 10px;
  background: #f0f0f0;
  color: #666;
  border-radius: 4px;
  font-size: 11px;
  transition: all 0.2s;
}

.result-tags .tag:hover {
  background: #3498db;
  color: white;
}

.no-results {
  text-align: center;
  padding: 30px 20px;
  color: #999;
}

.no-results i {
  font-size: 36px;
  color: #ddd;
  margin-bottom: 12px;
}

.no-results p {
  font-size: 14px;
  margin: 0 0 6px 0;
}

.no-results-hint {
  font-size: 12px;
  color: #bbb;
}

.results-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.pagination-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 12px;
  transition: all 0.2s ease;
}

.pagination-btn:hover:not(:disabled) {
  border-color: #3498db;
  color: #3498db;
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pagination-info {
  font-size: 13px;
  color: #666;
}

.search-placeholder {
  text-align: center;
  padding: 30px 20px;
}

.search-placeholder .placeholder-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 16px;
  background: #f5f7fa;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e8e8e8;
}

.search-placeholder .placeholder-icon i {
  font-size: 24px;
  color: #3498db;
}

.search-placeholder .placeholder-text {
  font-size: 14px;
  color: #999;
  margin: 0 0 16px 0;
}

.quick-search-tags {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-tag {
  padding: 6px 14px;
  background: #fafafa;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-tag:hover {
  background: #3498db;
  border-color: #3498db;
  color: white;
}

@media (max-width: 768px) {
  .smart-search-card {
    margin-bottom: 0;
  }
  
  .search-card-header {
    padding: 12px 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .search-card-body {
    padding: 16px;
  }
  
  .result-header {
    flex-direction: column;
    gap: 6px;
  }
  
  .result-meta {
    gap: 10px;
  }
  
  .quick-search-tags {
    gap: 6px;
  }
  
  .quick-tag {
    padding: 5px 10px;
    font-size: 11px;
  }
}

/* 政策关联网络图与智能搜索同行布局 */
.network-search-row {
  display: flex;
  gap: 20px;
  margin-top: 20px;
  margin-bottom: 30px;
  align-items: stretch;
}

.network-search-row .network-graph-card {
  flex: 1;
  min-width: 0;
  margin-top: 0;
}

.network-search-row .smart-search-card {
  width: 400px;
  flex-shrink: 0;
  margin-top: 0;
  display: flex;
  flex-direction: column;
  height: 864px;
  max-height: 864px;
}

.network-search-row .smart-search-card .search-card-body {
  flex: 1;
  overflow-y: auto;
}

/* 政策关联网络图样式 */
.network-graph-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-top: 20px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
}

.network-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.network-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 500;
  color: #333;
}

.network-title i {
  color: #3498db;
  font-size: 16px;
}

.network-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.network-select {
  padding: 5px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 12px;
  color: #333;
  background: white;
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
}

.network-select:focus {
  border-color: #3498db;
}

.network-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.network-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.network-container {
  height: 700px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.network-legend {
  display: flex;
  align-items: center;
  gap: 16px;
}

.legend-title {
  font-size: 12px;
  font-weight: 500;
  color: #333;
}

.legend-items {
  display: flex;
  align-items: center;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-node {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-node.province {
  background: #3498db;
}

.legend-node.category {
  background: #e74c3c;
}

.legend-node.keyword {
  background: #2ecc71;
}

.legend-label {
  font-size: 11px;
  color: #666;
}

.network-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 10px 14px;
  min-width: 120px;
}

.stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.stat-icon.nodes {
  background: rgba(52, 152, 219, 0.1);
  color: #3498db;
}

.stat-icon.links {
  background: rgba(46, 204, 113, 0.1);
  color: #2ecc71;
}

.stat-icon.density {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.network-stats .stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.network-stats .stat-label {
  font-size: 11px;
  color: #999;
}

.network-tooltip {
  position: absolute;
  background: white;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #e8e8e8;
  z-index: 100;
  min-width: 180px;
}

.tooltip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.tooltip-header i {
  color: #3498db;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tooltip-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.tooltip-label {
  color: #999;
}

.tooltip-value {
  color: #333;
  font-weight: 500;
}

@media (max-width: 768px) {
  .network-top-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .network-container {
    height: 450px;
  }
  
  .network-legend {
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .network-stats {
    gap: 8px;
  }
  
  .stat-card {
    padding: 8px 10px;
    min-width: 100px;
  }
  
  .stat-icon {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }
}
</style>
