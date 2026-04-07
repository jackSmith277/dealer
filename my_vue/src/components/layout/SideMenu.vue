<template>
  <div class="side-menu" :class="{ hidden: isHidden }">
    <div class="menu-header">
      <div class="menu-toggle" @click="toggleMenu">
        {{ isHidden ? '☰' : '✕' }}
      </div>
    </div>
    
    <div class="menu-content">
      <ul class="menu-list">
        <!-- 系统首页 -->
        <li class="menu-item">
          <div 
            class="menu-item-header" 
            :class="{ 'menu-active': $route.path === '/dashboard/index' }"
            @click="$router.push('/dashboard/index')"
          >
            <span class="menu-icon">🏠</span>
            <span class="menu-title">系统首页</span>
          </div>
        </li>
        
        <!-- 信息管理 -->
        <li class="menu-item">
          <div class="menu-item-header" @click="toggleSubMenu('info')">
            <span class="menu-icon">📋</span>
            <span class="menu-title">信息管理</span>
            <span class="menu-arrow" :class="{ active: expandedSubMenus.includes('info') }">></span>
          </div>
          <ul class="sub-menu" v-show="expandedSubMenus.includes('info')">
            <li 
              v-if="user.role === 'dealer' " 
              class="sub-menu-item"
              :class="{ active: $route.path === '/dashboard/profile' }"
              @click="$router.push('/dashboard/profile')"
            >
              <span class="sub-menu-title">个人信息</span>
            </li>
            <li 
              v-if="user.role === 'admin' " 
              class="sub-menu-item"
              :class="{ active: $route.path === '/dashboard/admin/dealers' }"
              @click="$router.push('/dashboard/admin/dealers')"
            >
              <span class="sub-menu-title">经销商列表</span>
            </li>
          </ul>
        </li>
        
        <!-- 仪表盘 -->
        <li class="menu-item">
          <div class="menu-item-header" @click="toggleSubMenu('dashboard')">
            <span class="menu-icon">📊</span>
            <span class="menu-title">仪表盘</span>
            <span class="menu-arrow" :class="{ active: expandedSubMenus.includes('dashboard') }">></span>
          </div>
          <ul class="sub-menu" v-show="expandedSubMenus.includes('dashboard')">
            <li 
              class="sub-menu-item"
              :class="{ active: $route.path === '/dashboard' }"
              @click="$router.push('/dashboard')"
            >
              <span class="sub-menu-title">销量驱动</span>
            </li>
            <li 
              class="sub-menu-item"
              :class="{ active: $route.path === '/dashboard/radar' }"
              @click="$router.push('/dashboard/radar')"
            >
              <span class="sub-menu-title">五力雷达</span>
            </li>
            <li 
              class="sub-menu-item"
              :class="{ active: $route.path === '/dashboard/policy' }"
              @click="$router.push('/dashboard/policy')"
            >
              <span class="sub-menu-title">政策展示</span>
            </li>
            <li 
              class="sub-menu-item"
              :class="{ active: $route.path === '/dashboard/comment' }"
              @click="$router.push('/dashboard/comment')"
            >
              <span class="sub-menu-title">试驾评价</span>
            </li>
          </ul>
        </li>
        
        <!-- 数据分析 -->
        <li class="menu-item">
          <div class="menu-item-header" @click="toggleSubMenu('analysis')">
            <span class="menu-icon">📈</span>
            <span class="menu-title">数据分析</span>
            <span class="menu-arrow" :class="{ active: expandedSubMenus.includes('analysis') }">></span>
          </div>
          <ul class="sub-menu" v-show="expandedSubMenus.includes('analysis')">
            <li 
              class="sub-menu-item"
              :class="{ active: $route.path === '/dashboard/prediction' }"
              @click="$router.push('/dashboard/prediction')"
            >
              <span class="sub-menu-title">销量预测</span>
            </li>
            <li 
              class="sub-menu-item"
              :class="{ active: $route.path === '/dashboard/advanced-prediction' }"
              @click="$router.push('/dashboard/advanced-prediction')"
            >
              <span class="sub-menu-title">高级销量预测</span>
            </li>
          </ul>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SideMenu',
  data() {
    return {
      collapsed: false,
      isHidden: false,
      expandedSubMenus: ['dashboard'], // 默认展开仪表盘
      user: JSON.parse(localStorage.getItem('user')) || {}
    }
  },
  methods: {
    toggleMenu() {
      if (this.isHidden) {
        this.isHidden = false
      } else {
        this.isHidden = true
      }
      // 触发菜单状态变化事件
      this.$emit('menu-toggle', this.isHidden)
    },
    toggleSubMenu(key) {
      if (this.expandedSubMenus.includes(key)) {
        this.expandedSubMenus = this.expandedSubMenus.filter(item => item !== key)
      } else {
        this.expandedSubMenus.push(key)
      }
    }
  },
  mounted() {
    const path = this.$route.path
    if (path.includes('/profile') || path.includes('/admin/dealers')) {
      this.expandedSubMenus = ['info']
    } else if (path.includes('/prediction')) {
      this.expandedSubMenus = ['analysis']
    } else if (path.includes('/dashboard') || path.includes('/radar') || path.includes('/history') || path.includes('/analysis-reports') || path.includes('/policy') || path.includes('/comment')) {
      this.expandedSubMenus = ['dashboard']
    }
  },
  watch: {
    '$route.path'(newPath) {
      if (newPath.includes('/profile') || newPath.includes('/admin/dealers')) {
        this.expandedSubMenus = ['info']
      } else if (newPath.includes('/prediction')) {
        this.expandedSubMenus = ['analysis']
      } else if (newPath.includes('/dashboard') || newPath.includes('/radar') || newPath.includes('/history') || newPath.includes('/analysis-reports') || newPath.includes('/policy') || newPath.includes('/comment')) {
        this.expandedSubMenus = ['dashboard']
      }
    }
  }
}
</script>

<style scoped>
.side-menu {
  width: 240px;
  height: 100%;
  background-color: #ffffff;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
  overflow: hidden;
}

.side-menu.hidden {
  width: 0;
  box-shadow: none;
}

.side-menu.hidden .menu-header,
.side-menu.hidden .menu-content {
  display: none;
}

.menu-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 16px;
  border-bottom: 1px solid #f0f0f0;
}

.menu-toggle {
  font-size: 16px;
  cursor: pointer;
  color: #666;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.menu-toggle:hover {
  background-color: #f0f0f0;
}

.menu-content {
  height: calc(100% - 60px);
  overflow-y: auto;
}

.menu-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.menu-item {
  margin: 8px 0;
}

.menu-item-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.3s;
  border-radius: 4px;
  margin: 0 8px;
}

.menu-item-header:hover {
  background-color: #f0f8ff;
}

.menu-item-header.menu-active {
  background-color: #e6f7ff;
  color: #1890ff;
}

.menu-item-header.menu-active .menu-title {
  color: #1890ff;
}

.menu-icon {
  font-size: 16px;
  margin-right: 12px;
  width: 20px;
  text-align: center;
}

.menu-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.menu-arrow {
  font-size: 12px;
  color: #999;
  transition: transform 0.3s;
}

.menu-arrow.active {
  transform: rotate(90deg);
}

.sub-menu {
  list-style: none;
  padding: 0;
  margin: 4px 0;
}

.sub-menu-item {
  padding: 10px 16px 10px 48px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 13px;
  color: #666;
  border-radius: 4px;
  margin: 0 8px;
}

.sub-menu-item:hover {
  background-color: #f5f5f5;
  color: #1890ff;
}

.sub-menu-item.active {
  background-color: #e6f7ff;
  color: #1890ff;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .side-menu {
    position: fixed;
    left: 0;
    top: 60px;
    z-index: 99;
    height: calc(100vh - 60px);
    transform: translateX(0);
    transition: transform 0.3s;
  }
  
  .side-menu.hidden {
    transform: translateX(-100%);
    width: 240px;
  }
  
  .side-menu.hidden .menu-header,
  .side-menu.hidden .menu-content {
    display: block;
  }
}
</style>