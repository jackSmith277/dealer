<template>
  <div class="register-container">
    <div class="register-box">
      <h2>用户注册</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="username">用户名</label>
          <input type="text" id="username" v-model="registerForm.username" required>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <div class="password-input-container">
            <input 
              :type="showPassword ? 'text' : 'password'" 
              id="password" 
              v-model="registerForm.password" 
              required
            >
            <span class="password-toggle" @click="togglePasswordVisibility">
              👁️‍🗨️
            </span>
          </div>
        </div>
        <div class="form-group">
          <label for="confirmPassword">确认密码</label>
          <div class="password-input-container">
            <input 
              :type="showPassword ? 'text' : 'password'" 
              id="confirmPassword" 
              v-model="registerForm.confirmPassword" 
              required
            >
            <span class="password-toggle" @click="togglePasswordVisibility">
              👁️‍🗨️
            </span>
          </div>
        </div>
        <div class="form-group">
          <label for="role">角色</label>
          <select id="role" v-model="registerForm.role" required>
            <option value="dealer">经销商</option>
          </select>
        </div>
        <div class="form-group">
          <button type="submit" class="register-btn">注册</button>
        </div>
        <div class="login-link">
          <span>已有账号？</span>
          <a href="#" @click.prevent="navigateToLogin">立即登录</a>
        </div>
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        <div v-if="success" class="success-message">
          {{ success }}
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Register',
  data() {
    return {
      registerForm: {
        username: '',
        password: '',
        confirmPassword: '',
        role: 'dealer'
      },
      error: '',
      success: '',
      showPassword: false
    }
  },
  methods: {
    togglePasswordVisibility() {
      this.showPassword = !this.showPassword
    },
    async handleRegister() {
      // 表单验证
      if (this.registerForm.password !== this.registerForm.confirmPassword) {
        this.error = '两次输入的密码不一致'
        return
      }
      
      if (!this.registerForm.username || !this.registerForm.password) {
        this.error = '请填写完整的注册信息'
        return
      }
      
      try {
        // 调用后端API进行注册
        await axios.post('/api/register', {
          username: this.registerForm.username,
          password: this.registerForm.password,
          role: this.registerForm.role
        })
        
        // 注册成功
        this.error = ''
        this.success = '注册成功！请登录'
        
        // 3秒后跳转到登录页面
        setTimeout(() => {
          this.navigateToLogin()
        }, 3000)
      } catch (error) {
        // 注册失败
        this.error = error.response?.data?.error || '注册失败，请稍后重试'
        this.success = ''
        console.error('注册错误:', error)
      }
    },
    navigateToLogin() {
      if (this.$route.path !== '/login') {
        this.$router.push('/login')
      }
    }
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  height: 100vh;
  padding-right: 10%;
  background-image: url('~@/../public/7747D6BE4519DEA21FCB78B34BF0E444.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.register-box {
  background-color: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.register-box h2 {
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

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
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

.register-btn {
  width: 100%;
  padding: 12px;
  background-color: #67c23a;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.register-btn:hover {
  background-color: #85ce61;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.login-link a {
  color: #409EFF;
  text-decoration: none;
  margin-left: 5px;
}

.login-link a:hover {
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

.success-message {
  margin-top: 15px;
  padding: 10px;
  background-color: #f0f9eb;
  color: #67c23a;
  border-radius: 4px;
  font-size: 14px;
  text-align: center;
}
</style>