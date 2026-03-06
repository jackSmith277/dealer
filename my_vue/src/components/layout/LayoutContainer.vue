<template>
  <div class="layout-container">
    <!-- 顶部导航栏 -->
    <TopNavbar />
    
    <div class="main-content">
      <!-- 左侧菜单 -->
      <SideMenu ref="sideMenu" @menu-toggle="handleMenuToggle" />
      
      <!-- 右侧内容区 -->
      <div class="right-content">
        <router-view />
      </div>
      
      <!-- 菜单展开按钮 -->
      <div v-if="menuHidden" class="menu-toggle-btn" @click="toggleSideMenu">
        ☰
      </div>
    </div>
  </div>
</template>

<script>
import TopNavbar from './TopNavbar.vue'
import SideMenu from './SideMenu.vue'

export default {
  name: 'LayoutContainer',
  components: {
    TopNavbar,
    SideMenu
  },
  data() {
    return {
      menuHidden: false
    }
  },
  methods: {
    toggleSideMenu() {
      this.menuHidden = false
      if (this.$refs.sideMenu) {
        this.$refs.sideMenu.isHidden = false
      }
    },
    handleMenuToggle(isHidden) {
      this.menuHidden = isHidden
    }
  },
  mounted() {
    // 初始化时检查菜单状态
    if (this.$refs.sideMenu) {
      this.menuHidden = this.$refs.sideMenu.isHidden
    }
  }
}
</script>

<style scoped>
.layout-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
  color: #333;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.right-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f5f5f5;
  margin: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* 菜单展开按钮 */
.menu-toggle-btn {
  position: fixed;
  left: 10px;
  top: 80px;
  width: 40px;
  height: 40px;
  background-color: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  cursor: pointer;
  z-index: 98;
  transition: all 0.3s;
}

.menu-toggle-btn:hover {
  background-color: #f5f5f5;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-content {
    position: relative;
  }
  
  .right-content {
    margin: 5px;
    padding: 15px;
  }
  
  .menu-toggle-btn {
    left: 5px;
    top: 70px;
    width: 36px;
    height: 36px;
    font-size: 16px;
  }
}
</style>