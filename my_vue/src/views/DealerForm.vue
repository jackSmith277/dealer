<template>
  <div class="dealer-form-container">
    <div class="dealer-form-header">
      <h1>{{ isEdit ? '编辑经销商' : '添加经销商' }}</h1>
      <div class="header-actions">
        <button class="back-btn" @click="$router.push('/admin/dealers')">
          ← 返回列表
        </button>
      </div>
    </div>
    
    <div class="dealer-form-content">
      <div v-if="loading" class="loading">
        {{ isEdit ? '加载中...' : '准备中...' }}
      </div>
      
      <div v-else-if="error" class="error-message">
        {{ error }}
      </div>
      
      <div v-else>
        <form @submit.prevent="saveDealer" class="dealer-form">
          <!-- 基本信息 -->
          <div class="form-section">
            <h2>基本信息</h2>
            <div class="form-grid">
              <div class="form-group">
                <label for="dealer_name">经销商名称 *</label>
                <input 
                  type="text" 
                  id="dealer_name" 
                  v-model="formData.dealer_name" 
                  required
                >
              </div>
              
              <div class="form-group">
                <label for="dealer_type">经销商类型 *</label>
                <select id="dealer_type" v-model="formData.dealer_type" required>
                  <option value="">请选择</option>
                  <option value="4S店">4S店</option>
                  <option value="二级网点">二级网点</option>
                  <option value="授权经销商">授权经销商</option>
                </select>
              </div>
              
              <div class="form-group">
                <label for="brand">主营品牌 *</label>
                <input 
                  type="text" 
                  id="brand" 
                  v-model="formData.brand" 
                  required
                >
              </div>
              
              <div class="form-group">
                <label for="level">经销商等级 *</label>
                <select id="level" v-model="formData.level" required>
                  <option value="">请选择</option>
                  <option value="A级">A级</option>
                  <option value="B级">B级</option>
                  <option value="C级">C级</option>
                </select>
              </div>
              
              <div class="form-group">
                <label for="region">所属地区 *</label>
                <input 
                  type="text" 
                  id="region" 
                  v-model="formData.region" 
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
                <label for="contact_name">联系人 *</label>
                <input 
                  type="text" 
                  id="contact_name" 
                  v-model="formData.contact_name" 
                  required
                >
              </div>
              
              <div class="form-group">
                <label for="contact_phone">联系电话 *</label>
                <input 
                  type="text" 
                  id="contact_phone" 
                  v-model="formData.contact_phone" 
                  required
                >
              </div>
              
              <div class="form-group form-group-full">
                <label for="address">详细地址 *</label>
                <input 
                  type="text" 
                  id="address" 
                  v-model="formData.address" 
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
                <label for="username">登录账号 *</label>
                <input 
                  type="text" 
                  id="username" 
                  v-model="formData.username" 
                  :disabled="isEdit"
                  required
                >
                <small v-if="isEdit" class="help-text">账号不可修改</small>
              </div>
              
              <div class="form-group password-group">
                <label for="password">登录密码 * {{ isEdit ? '(不填则不修改)' : '' }}</label>
                <div class="password-input-container">
                  <input 
                    :type="passwordVisible ? 'text' : 'password'" 
                    id="password" 
                    v-model="formData.password"
                    :required="!isEdit"
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
              
              <div class="form-group">
                <label for="status">账号状态</label>
                <select id="status" v-model="formData.status">
                  <option value="1">启用</option>
                  <option value="0">禁用</option>
                </select>
              </div>
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div class="form-actions">
            <button type="submit" class="save-btn" :disabled="saving">
              {{ saving ? '保存中...' : '保存' }}
            </button>
            <button type="button" class="cancel-btn" @click="$router.push('/admin/dealers')">
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
  name: 'DealerForm',
  data() {
    return {
      formData: {
        username: '',
        password: '',
        dealer_name: '',
        dealer_type: '',
        brand: '',
        level: '',
        region: '',
        contact_name: '',
        contact_phone: '',
        address: '',
        status: 1
      },
      loading: true,
      saving: false,
      error: '',
      isEdit: false,
      passwordVisible: false
    }
  },
  computed: {
    dealerId() {
      return this.$route.params.id
    }
  },
  mounted() {
    this.isEdit = !!this.dealerId
    if (this.isEdit) {
      this.loadDealerData()
    } else {
      this.loading = false
    }
  },
  methods: {
    async loadDealerData() {
      this.loading = true
      this.error = ''
      
      try {
        const token = this.$store.state.token
        const response = await axios.get(`http://localhost:5000/api/users/${this.dealerId}`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        })
        
        const user = response.data
        const dealer = user.dealer
        
        if (!dealer) {
          this.error = '经销商信息不存在'
          return
        }
        
        this.formData = {
          username: user.username,
          password: '', // 编辑时密码为空，不修改
          dealer_name: dealer.dealer_name,
          dealer_type: dealer.dealer_type,
          brand: dealer.brand,
          level: dealer.level,
          region: dealer.region,
          contact_name: dealer.contact_name,
          contact_phone: dealer.contact_phone,
          address: dealer.address,
          status: user.status
        }
      } catch (err) {
        this.error = err.response?.data?.error || '加载经销商信息失败'
      } finally {
        this.loading = false
      }
    },
    
    async saveDealer() {
      this.saving = true
      this.error = ''
      
      try {
        const token = this.$store.state.token
        
        if (this.isEdit) {
          // 编辑经销商
          // 先更新用户状态
          if (this.formData.password) {
            // 如果修改了密码
            await axios.put(`http://localhost:5000/api/users/${this.dealerId}`, {
              password: this.formData.password,
              status: this.formData.status
            }, {
              headers: {
                Authorization: `Bearer ${token}`
              }
            })
          } else if (this.formData.status !== undefined) {
            // 只更新状态
            await axios.put(`http://localhost:5000/api/users/${this.dealerId}`, {
              status: this.formData.status
            }, {
              headers: {
                Authorization: `Bearer ${token}`
              }
            })
          }
          
          // 更新经销商信息
          await axios.put(`http://localhost:5000/api/dealers/${this.dealerId}`, {
            dealer_name: this.formData.dealer_name,
            dealer_type: this.formData.dealer_type,
            brand: this.formData.brand,
            level: this.formData.level,
            region: this.formData.region,
            contact_name: this.formData.contact_name,
            contact_phone: this.formData.contact_phone,
            address: this.formData.address
          }, {
            headers: {
              Authorization: `Bearer ${token}`
            }
          })
        } else {
          // 添加经销商
          await axios.post('http://localhost:5000/api/dealers', {
            username: this.formData.username,
            password: this.formData.password,
            dealer_name: this.formData.dealer_name,
            dealer_type: this.formData.dealer_type,
            brand: this.formData.brand,
            level: this.formData.level,
            region: this.formData.region,
            contact_name: this.formData.contact_name,
            contact_phone: this.formData.contact_phone,
            address: this.formData.address
          }, {
            headers: {
              Authorization: `Bearer ${token}`
            }
          })
        }
        
        alert(this.isEdit ? '经销商更新成功' : '经销商添加成功')
        this.$router.push('/admin/dealers')
      } catch (err) {
        this.error = err.response?.data?.error || (this.isEdit ? '更新失败' : '添加失败')
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.dealer-form-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  color: #333;
  background-color: #ffffff;
  min-height: 100vh;
}

.dealer-form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e8e8e8;
}

.dealer-form-header h1 {
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

.dealer-form-content {
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

.dealer-form {
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

.help-text {
  margin-top: 5px;
  font-size: 12px;
  color: #999;
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