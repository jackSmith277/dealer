<template>
  <div class="profile-container">
    <div class="profile-header">
      <h1>个人信息管理</h1>
      <div class="header-actions">
        <button class="back-btn" @click="$router.push('/dashboard')">
          ← 返回仪表盘
        </button>
      </div>
    </div>
    
    <div class="profile-content">
      <div v-if="loading" class="loading">
        加载中...
      </div>
      
      <div v-else-if="error" class="error-message">
        {{ error }}
      </div>
      
      <div v-else>
        <form @submit.prevent="updateProfile" class="profile-form">
          <!-- 基本信息 -->
          <div class="form-section">
            <h2>基本信息</h2>
            <div class="form-grid">
              <div class="form-group">
                <label for="dealer_name">经销商名称</label>
                <input 
                  type="text" 
                  id="dealer_name" 
                  v-model="profile.dealer_name" 
                  required
                >
              </div>
              
              <div class="form-group">
                <label for="dealer_type">经销商类型</label>
                <select id="dealer_type" v-model="profile.dealer_type" required>
                  <option value="4S店">4S店</option>
                  <option value="二级网点">二级网点</option>
                  <option value="授权经销商">授权经销商</option>
                </select>
              </div>
              
              <div class="form-group">
                <label for="brand">主营品牌</label>
                <input 
                  type="text" 
                  id="brand" 
                  v-model="profile.brand" 
                  required
                >
              </div>
              
              <div class="form-group">
                <label for="level">经销商等级</label>
                <select id="level" v-model="profile.level" required>
                  <option value="A级">A级</option>
                  <option value="B级">B级</option>
                  <option value="C级">C级</option>
                </select>
              </div>
              
              <div class="form-group">
                <label for="region">所属地区</label>
                <input 
                  type="text" 
                  id="region" 
                  v-model="profile.region" 
                  required
                >
              </div>
            </div>
          </div>
          
          <!-- 联系信息 -->
          <div class="form-section">
            <h2>联系信息</h2>
            <div class="form-grid">
              <div class="form-group">
                <label for="contact_name">联系人</label>
                <input 
                  type="text" 
                  id="contact_name" 
                  v-model="profile.contact_name" 
                  required
                >
              </div>
              
              <div class="form-group">
                <label for="contact_phone">联系电话</label>
                <input 
                  type="text" 
                  id="contact_phone" 
                  v-model="profile.contact_phone" 
                  required
                >
              </div>
              
              <div class="form-group form-group-full">
                <label for="address">详细地址</label>
                <input 
                  type="text" 
                  id="address" 
                  v-model="profile.address" 
                  required
                  style="width: 100%;"
                >
              </div>
            </div>
          </div>
          
          <!-- 账号信息 -->
          <div class="form-section">
            <h2>账号信息</h2>
            <div class="form-grid">
              <div class="form-group">
                <label for="username">登录账号</label>
                <input 
                  type="text" 
                  id="username" 
                  :value="user.username" 
                  disabled
                >
              </div>
              
              <div class="form-group">
                <label for="role">账号角色</label>
                <input 
                  type="text" 
                  id="role" 
                  :value="user.role" 
                  disabled
                >
              </div>
              
              <div class="form-group password-group">
                <label for="password">登录密码 (不填则不修改)</label>
                <div class="password-input-container">
                  <input 
                    :type="passwordVisible ? 'text' : 'password'" 
                    id="password" 
                    v-model="password"
                  >
                  <button 
                    type="button" 
                    class="password-toggle-btn"
                    @click="passwordVisible = !passwordVisible"
                  >
                    {{ passwordVisible ? '👁️' : '👁️‍🗨️' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div class="form-actions">
            <button type="submit" class="save-btn" :disabled="saving">
              {{ saving ? '保存中...' : '保存修改' }}
            </button>
            <button type="button" class="cancel-btn" @click="$router.push('/dashboard')">
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Profile',
  data() {
    return {
      profile: {
        dealer_name: '',
        dealer_type: '',
        brand: '',
        level: '',
        region: '',
        contact_name: '',
        contact_phone: '',
        address: ''
      },
      loading: true,
      saving: false,
      error: '',
      password: '',
      passwordVisible: false
    }
  },
  computed: {
    user() {
      return this.$store.state.user || {}
    }
  },
  mounted() {
    this.loadProfile()
  },
  methods: {
    async loadProfile() {
      this.loading = true
      this.error = ''
      
      try {
        const token = this.$store.state.token
        const response = await axios.get(
          `http://localhost:5000/api/dealers/${this.user.id}`,
          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        )
        
        this.profile = {
          dealer_name: response.data.dealer_name,
          dealer_type: response.data.dealer_type,
          brand: response.data.brand,
          level: response.data.level,
          region: response.data.region,
          contact_name: response.data.contact_name,
          contact_phone: response.data.contact_phone,
          address: response.data.address
        }
      } catch (err) {
        this.error = err.response?.data?.error || '加载个人信息失败'
      } finally {
        this.loading = false
      }
    },
    
    async updateProfile() {
      this.saving = true
      this.error = ''
      
      try {
        const token = this.$store.state.token
        
        // 先更新经销商信息
        await axios.put(
          `http://localhost:5000/api/dealers/${this.user.id}`,
          this.profile,
          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        )
        
        // 如果填写了密码，更新密码
        if (this.password) {
          await axios.put(
            `http://localhost:5000/api/users/${this.user.id}`,
            { password: this.password },
            {
              headers: {
                Authorization: `Bearer ${token}`
              }
            }
          )
        }
        
        alert('个人信息更新成功')
      } catch (err) {
        this.error = err.response?.data?.error || '更新个人信息失败'
      } finally {
        this.saving = false
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    }
  }
}
</script>

<style scoped>
.profile-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  color: #333;
  background-color: #ffffff;
  min-height: 100vh;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.profile-header h1 {
  font-size: 24px;
  margin: 0;
  color: #333;
}

.back-btn {
  padding: 8px 16px;
  background-color: #ffffff;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background-color: #f5f5f5;
  border-color: #1890ff;
  color: #1890ff;
}

.profile-content {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.loading {
  text-align: center;
  padding: 50px;
  font-size: 18px;
  color: #999;
}

.error-message {
  background-color: #fff1f0;
  border: 1px solid #ffccc7;
  color: #cf1322;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.profile-form {
  width: 100%;
}

.form-section {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.form-section h2 {
  font-size: 18px;
  margin: 0 0 20px 0;
  color: #333;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group-full {
  grid-column: 1 / -1;
}

.form-group label {
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}

.form-group input,
.form-group select {
  padding: 10px;
  background-color: #ffffff;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.form-group input:disabled {
  background-color: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}

.form-actions {
  display: flex;
  gap: 15px;
  margin-top: 30px;
  justify-content: flex-end;
}

.save-btn {
  padding: 12px 24px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.save-btn:hover:not(:disabled) {
  background-color: #40a9ff;
}

.save-btn:disabled {
  background-color: #d9d9d9;
  cursor: not-allowed;
}

.cancel-btn {
  padding: 12px 24px;
  background-color: #ffffff;
  color: #666;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.cancel-btn:hover {
  background-color: #f5f5f5;
}

.password-group {
  position: relative;
}

.password-input-container {
  position: relative;
  display: flex;
}

.password-input-container input {
  flex: 1;
  padding-right: 40px;
}

.password-toggle-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: #999;
  font-size: 16px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.password-toggle-btn:hover {
  color: #666;
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .save-btn,
  .cancel-btn {
    width: 100%;
  }
}
</style>