<template>
  <div class="top-navbar">
    <div class="navbar-left">
      <h1 class="system-title">基于大数据的单店经营决策与销量预测系统</h1>
    </div>
    
    <div class="navbar-right">
      <div class="user-info" @click="toggleUserMenu">
        <span class="user-name">{{ user.username || '用户' }}</span>
        <span class="user-avatar">👤</span>
        <span class="dropdown-arrow" :class="{ active: showUserMenu }">></span>
        
        <div class="user-dropdown" v-show="showUserMenu">
          <div v-if="user.role === 'dealer'" @click="$router.push('/dashboard/profile')">
            个人信息
          </div>
          <div v-if="user.role === 'admin'" @click="$router.push('/dashboard/admin/dealers')">
            经销商管理
          </div>
          <div class="dropdown-divider"></div>
          <div @click="logout">
            退出登录
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TopNavbar',
  data() {
    return {
      showUserMenu: false,
      user: JSON.parse(localStorage.getItem('user')) || {}
    }
  },
  methods: {
    toggleUserMenu() {
      this.showUserMenu = !this.showUserMenu
    },
    logout() {
      localStorage.removeItem('user')
      localStorage.removeItem('token')
      this.$router.push('/login')
    }
  },
  mounted() {
    // 点击外部关闭下拉菜单
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.user-info')) {
        this.showUserMenu = false
      }
    })
  }
}
</script>

<style scoped>
.top-navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  padding: 0 20px;
  background-color: #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  z-index: 100;
}

.system-title {
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
  margin: 0;
}

.navbar-right {
  display: flex;
  align-items: center;
}

.user-info {
  position: relative;
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: #f0f0f0;
}

.user-name {
  margin-right: 8px;
  font-size: 14px;
  color: #333;
}

.user-avatar {
  font-size: 16px;
  margin-right: 4px;
}

.dropdown-arrow {
  font-size: 12px;
  color: #666;
  transition: transform 0.3s;
}

.dropdown-arrow.active {
  transform: rotate(-90deg);
}

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background-color: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  min-width: 120px;
  z-index: 1000;
}

/* 使用 :not 排除分割线，避免给分割线加上内边距 */
.user-dropdown > div:not(.dropdown-divider) {
  padding: 8px 16px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: background-color 0.3s;
}

/* 同样排除分割线，避免鼠标经过分割线时出现 hover 背景色 */
.user-dropdown > div:not(.dropdown-divider):hover {
  background-color: #f0f0f0;
}

.dropdown-divider {
  height: 1px;
  background-color: #e8e8e8;
  padding: 0;
  cursor: default;
}
</style>