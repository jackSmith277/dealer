<template>
  <div class="login-container">
    <div class="login-box">
      <h2>系统登录</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="role">角色</label>
          <select id="role" v-model="loginForm.role" class="role-select">
            <option value="admin">管理员</option>
            <option value="dealer">经销商</option>
          </select>
        </div>
        <div class="form-group">
          <label for="username">用户名</label>
          <input type="text" id="username" v-model="loginForm.username" required>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <div class="password-input-container">
            <input 
              :type="showPassword ? 'text' : 'password'" 
              id="password" 
              v-model="loginForm.password" 
              required
            >
            <span class="password-toggle" @click="togglePasswordVisibility">
              👁️‍🗨️
            </span>
          </div>
        </div>
        <div class="form-group">
          <button type="submit" class="login-btn">登录</button>
        </div>
        <div class="register-link">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Login',
  data() {
    return {
      loginForm: {
        username: '',
        password: '',
        role: 'admin'
      },
      error: '',
      showPassword: false
    }
  },
  watch: {
    'loginForm.role'(newRole) {
      if (newRole === 'admin') {
        this.loginForm.username = 'admin'
        this.loginForm.password = 'admin123'
      } else {
        this.loginForm.username = '9210006'
        this.loginForm.password = 'dealer123'
      }
    }
  },
  created() {
    if (this.loginForm.role === 'admin') {
      this.loginForm.username = 'admin'
      this.loginForm.password = 'admin123'
    } else {
      this.loginForm.username = '9210006'
      this.loginForm.password = 'dealer123'
    }
  },
  methods: {
    togglePasswordVisibility() {
      this.showPassword = !this.showPassword
    },
    async handleLogin() {
      // 表单验证
      if (!this.loginForm.username || !this.loginForm.password) {
        this.error = '请填写完整的登录信息'
        return
      }
      
      try {
        // 调用后端API进行登录验证
        const response = await axios.post('/api/login', {
          username: this.loginForm.username,
          password: this.loginForm.password
        })
        
        //console.log('登录成功，后端返回:', response.data)
        
        // 登录成功
        this.$store.commit('setUser', response.data.user)
        this.$store.commit('setToken', response.data.token)
        
        // 存储用户信息到localStorage，用于路由守卫
        localStorage.setItem('user', JSON.stringify(response.data.user))
        //console.log('用户信息已存储到localStorage:', localStorage.getItem('user'))
        
        // 延迟导航，确保localStorage存储完成
        setTimeout(() => {
          //console.log('导航到仪表盘前检查localStorage:', localStorage.getItem('user'))
          //this.$router.push('/dashboard')
          //避免重复跳转报错
          if (this.$route.path !== '/dashboard/index') {
            this.$router.push('/dashboard/index')
          }
        }, 100)
      } catch (error) {
        // 登录失败
        console.error('登录错误:', error)
        this.error = error.response?.data?.error || '登录失败，请检查用户名和密码'
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f5f5;
}

.login-box {
  background-color: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.login-box h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.role-select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  background-color: white;
  cursor: pointer;
}

.role-select:focus {
  outline: none;
  border-color: #409EFF;
}

.password-input-container {
  position: relative;
  width: 100%;
}

.password-input-container input {
  padding-right: 40px;
}

.password-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  font-size: 16px;
  user-select: none;
}

.login-btn {
  width: 100%;
  padding: 12px;
  background-color: #409EFF;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.login-btn:hover {
  background-color: #66b1ff;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.register-link a {
  color: #409EFF;
  text-decoration: none;
  margin-left: 5px;
}

.register-link a:hover {
  text-decoration: underline;
}

.error-message {
  margin-top: 15px;
  padding: 10px;
  background-color: #fef0f0;
  color: #f56c6c;
  border-radius: 4px;
  font-size: 14px;
  text-align: center;
}
</style>