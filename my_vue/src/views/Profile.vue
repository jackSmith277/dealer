<template>
  <div class="profile-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">个人信息管理</h1>
          <p class="page-subtitle">管理您的账户信息和经销商资料</p>
        </div>
        <div class="header-right">
          <button class="btn btn-outline" @click="$router.push('/dashboard')">
            <span class="btn-icon">←</span>
            返回仪表盘
          </button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="profile-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p class="loading-text">加载个人信息中...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="error-state">
        <div class="error-icon">
          <i class="fas fa-exclamation-circle"></i>
        </div>
        <div class="error-content">
          <h3>加载失败</h3>
          <p>{{ error }}</p>
          <button class="btn btn-primary" @click="loadProfile">
            重试
          </button>
        </div>
      </div>

      <!-- 表单内容 -->
      <div v-else class="profile-form-container">
        <form @submit.prevent="updateProfile" class="profile-form">
          <!-- 整体表单卡片 -->
          <div class="form-card unified-card">
            <div class="card-header unified-header">
              <h2 class="card-title">
                <span class="card-icon">�</span>
                个人信息管理
              </h2>
              <p class="card-description">管理您的经销商信息和账户设置</p>
            </div>
            
            <div class="card-body unified-body">
              <!-- 基本信息部分 -->
              <div class="form-section">
                <h3 class="section-title">
                  <span class="section-icon">📋</span>
                  基本信息
                </h3>
                <div class="form-grid">
                  <div class="form-group">
                    <label for="dealer_name" class="form-label">
                      <span class="label-text">经销商名称</span>
                      <span class="required">*</span>
                    </label>
                    <input 
                      type="text" 
                      id="dealer_name" 
                      v-model="profile.dealer_name" 
                      class="form-input"
                      placeholder="请输入经销商名称"
                      required
                    >
                  </div>
                  
                  <div class="form-group">
                    <label for="dealer_type" class="form-label">
                      <span class="label-text">经销商类型</span>
                      <span class="required">*</span>
                    </label>
                    <CustomSelect 
                      v-model="profile.dealer_type" 
                      :options="dealerTypeOptions"
                      placeholder="请选择类型"
                    />
                  </div>
                  
                  <div class="form-group">
                    <label for="brand" class="form-label">
                      <span class="label-text">主营品牌</span>
                      <span class="required">*</span>
                    </label>
                    <input 
                      type="text" 
                      id="brand" 
                      v-model="profile.brand" 
                      class="form-input"
                      placeholder="请输入主营品牌"
                      required
                    >
                  </div>
                  
                  <div class="form-group">
                    <label for="level" class="form-label">
                      <span class="label-text">经销商等级</span>
                      <span class="required">*</span>
                    </label>
                    <CustomSelect 
                      v-model="profile.level" 
                      :options="levelOptions"
                      placeholder="请选择等级"
                    />
                  </div>
                  
                  <div class="form-group">
                    <label for="region" class="form-label">
                      <span class="label-text">所属地区</span>
                      <span class="required">*</span>
                    </label>
                    <div class="region-selector-wrapper">
                      <RegionCascader 
                        :modelValue="profile.region"
                        @update:modelValue="profile.region = $event"
                        class="region-selector"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- 联系信息部分 -->
              <div class="form-section">
                <h3 class="section-title">
                  <span class="section-icon">📞</span>
                  联系信息
                </h3>
                <div class="form-grid">
                  <div class="form-group">
                    <label for="contact_name" class="form-label">
                      <span class="label-text">联系人</span>
                      <span class="required">*</span>
                    </label>
                    <input 
                      type="text" 
                      id="contact_name" 
                      v-model="profile.contact_name" 
                      class="form-input"
                      placeholder="请输入联系人姓名"
                      required
                    >
                  </div>
                  
                  <div class="form-group">
                    <label for="contact_phone" class="form-label">
                      <span class="label-text">联系电话</span>
                      <span class="required">*</span>
                    </label>
                    <input 
                      type="text" 
                      id="contact_phone" 
                      v-model="profile.contact_phone" 
                      class="form-input"
                      placeholder="请输入联系电话"
                      required
                    >
                  </div>
                  
                  <div class="form-group form-group-full">
                    <label for="address" class="form-label">
                      <span class="label-text">详细地址</span>
                      <span class="required">*</span>
                    </label>
                    <input 
                      type="text" 
                      id="address" 
                      v-model="profile.address" 
                      class="form-input"
                      placeholder="请输入详细地址"
                      required
                    >
                  </div>
                </div>
              </div>

              <!-- 账号信息部分 -->
              <div class="form-section">
                <h3 class="section-title">
                  <span class="section-icon">🔐</span>
                  账号信息
                </h3>
                <div class="form-grid">
                  <div class="form-group">
                    <label for="username" class="form-label">
                      <span class="label-text">登录账号</span>
                    </label>
                    <div class="form-input-disabled">
                      {{ user.username || '未设置' }}
                    </div>
                  </div>
                  
                  <div class="form-group">
                    <label for="role" class="form-label">
                      <span class="label-text">账号角色</span>
                    </label>
                    <div class="form-input-disabled">
                      {{ user.role === 'dealer' ? '经销商' : user.role === 'admin' ? '管理员' : '未知角色' }}
                    </div>
                  </div>
                  
                  <div class="form-group password-group">
                    <label for="password" class="form-label">
                      <span class="label-text">登录密码</span>
                      <span class="help-text">(不填则不修改)</span>
                    </label>
                    <div class="password-input-container">
                      <input 
                        :type="passwordVisible ? 'text' : 'password'" 
                        id="password" 
                        v-model="password"
                        class="form-input"
                        placeholder="请输入新密码"
                      >
                      <button 
                        type="button" 
                        class="password-toggle-btn"
                        @click="passwordVisible = !passwordVisible"
                        :title="passwordVisible ? '隐藏密码' : '显示密码'"
                      >
                        <span class="toggle-icon">{{ passwordVisible ? '👁️' : '👁️‍🗨️' }}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- 操作按钮 -->
          <div class="form-actions">
            <div class="actions-container">
              <button type="submit" class="btn btn-primary" :disabled="saving">
                <span v-if="saving" class="btn-loading"></span>
                {{ saving ? '保存中...' : '保存修改' }}
              </button>
              <button type="button" class="btn btn-secondary" @click="$router.push('/dashboard')">
                取消
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import RegionCascader from '@/components/RegionCascader.vue'
import CustomSelect from '@/components/CustomSelect.vue'

export default {
  name: 'Profile',
  components: {
    RegionCascader,
    CustomSelect
  },
  data() {
    return {
      profile: {
        dealer_name: '',
        dealer_type: '',
        brand: '',
        level: '',
        region: { province: '', city: '' },
        contact_name: '',
        contact_phone: '',
        address: ''
      },
      dealerTypeOptions: [
        { value: '4S店', label: '4S店' },
        { value: '二级网点', label: '二级网点' },
        { value: '授权经销商', label: '授权经销商' }
      ],
      levelOptions: [
        { value: 'A级', label: 'A级' },
        { value: 'B级', label: 'B级' },
        { value: 'C级', label: 'C级' }
      ],
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
          region: {
            province: response.data.province || '',
            city: response.data.city || ''
          },
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
        
        const dealerData = {
          dealer_name: this.profile.dealer_name,
          dealer_type: this.profile.dealer_type,
          brand: this.profile.brand,
          level: this.profile.level,
          province: this.profile.region.province,
          city: this.profile.region.city,
          contact_name: this.profile.contact_name,
          contact_phone: this.profile.contact_phone,
          address: this.profile.address
        }
        
        console.log('发送的数据:', dealerData)
        
        // 先更新经销商信息
        const response = await axios.put(
          `http://localhost:5000/api/dealers/${this.user.id}`,
          dealerData,
          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        )
        
        console.log('更新响应:', response.data)
        
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
        console.error('更新失败:', err)
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
/* 基础容器 */
.profile-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 24px;
}

/* 页面头部 */
.page-header {
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 24px;
  overflow: hidden;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32px 40px;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.3;
}

.page-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.header-right {
  flex-shrink: 0;
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  gap: 8px;
  min-height: 40px;
}

.btn-primary {
  background-color: #2563eb;
  color: white;
  border-color: #2563eb;
}

.btn-primary:hover:not(:disabled) {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.btn-primary:disabled {
  background-color: #93c5fd;
  border-color: #93c5fd;
  cursor: not-allowed;
  opacity: 0.7;
}

.btn-secondary {
  background-color: #ffffff;
  color: #4b5563;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background-color: #f9fafb;
  border-color: #9ca3af;
  transform: translateY(-1px);
}

.btn-outline {
  background-color: transparent;
  color: #4b5563;
  border: 1px solid #d1d5db;
}

.btn-outline:hover {
  background-color: #f9fafb;
  border-color: #9ca3af;
}

.btn-icon {
  font-size: 16px;
  line-height: 1;
}

.btn-loading {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 主要内容区域 */
.profile-content {
  width: 100%;
  margin: 0 auto;
  transition: all 0.3s ease;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid #e5e7eb;
  border-radius: 50%;
  border-top-color: #2563eb;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

.loading-text {
  font-size: 16px;
  color: #6b7280;
  margin: 0;
}

/* 错误状态 */
.error-state {
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: 40px;
  text-align: center;
}

.error-icon {
  font-size: 48px;
  color: #ef4444;
  margin-bottom: 20px;
}

.error-content h3 {
  font-size: 20px;
  color: #1f2937;
  margin: 0 0 12px 0;
}

.error-content p {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 24px 0;
  line-height: 1.5;
}

/* 表单容器 */
.profile-form-container {
  width: 100%;
}

/* 整体表单卡片 */
.form-card.unified-card {
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: visible;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}

.form-card.unified-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

/* 整体卡片头部 */
.card-header.unified-header {
  padding: 32px 40px;
  border-bottom: 1px solid #f3f4f6;
  background-color: #f9fafb;
}

.card-header.unified-header .card-title {
  font-size: 20px;
  margin-bottom: 8px;
}

.card-header.unified-header .card-description {
  font-size: 14px;
  color: #6b7280;
}

/* 整体卡片内容 */
.card-body.unified-body {
  padding: 40px;
}

/* 表单部分 */
.form-section {
  margin-bottom: 40px;
  padding-bottom: 32px;
  border-bottom: 1px solid #f3f4f6;
}

.form-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 24px 0;
}

.section-icon {
  font-size: 18px;
  line-height: 1;
}

/* 地区选择器包装 */
.region-selector-wrapper {
  width: 100%;
}

.region-selector-wrapper .region-cascader {
  width: 100%;
}

.card-header {
  padding: 24px 32px;
  border-bottom: 1px solid #f3f4f6;
  background-color: #f9fafb;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.card-icon {
  font-size: 20px;
  line-height: 1;
}

.card-description {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.card-body {
  padding: 32px;
}

/* 表单网格 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group-full {
  grid-column: 1 / -1;
}

/* 表单标签 */
.form-label {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.label-text {
  line-height: 1.5;
}

.required {
  color: #ef4444;
  font-size: 12px;
}

.help-text {
  font-size: 12px;
  color: #9ca3af;
  font-weight: normal;
  margin-left: 4px;
}

/* 表单输入 */
.form-input,
.form-select {
  padding: 12px 16px;
  background-color: #ffffff;
  color: #1f2937;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s ease;
  width: 100%;
  box-sizing: border-box;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-input::placeholder {
  color: #9ca3af;
}

.form-input:disabled,
.form-select:disabled {
  background-color: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
  border-color: #e5e7eb;
}

.form-group :deep(.custom-select-wrapper) {
  width: 100%;
}

.form-group :deep(.custom-select-wrapper .select-trigger) {
  padding: 12px 16px;
  background-color: #ffffff;
  color: #1f2937;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  height: 46px;
}

.form-group :deep(.custom-select-wrapper .select-trigger:hover) {
  border-color: #2563eb;
}

.form-group :deep(.custom-select-wrapper .select-trigger:focus) {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-group :deep(.custom-select-wrapper .select-dropdown) {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.form-group :deep(.custom-select-wrapper .select-option) {
  padding: 10px 16px;
  font-size: 14px;
  color: #1f2937;
}

.form-group :deep(.custom-select-wrapper .select-option:hover) {
  background-color: #f3f4f6;
}

.form-group :deep(.custom-select-wrapper .select-option.active) {
  background-color: #eff6ff;
  color: #2563eb;
}

.form-group :deep(.region-cascader) {
  width: 100%;
}

.form-group :deep(.region-cascader .cascader-wrapper) {
  display: block;
}

.form-group :deep(.region-cascader .cascader-column) {
  width: 100%;
}

.form-group :deep(.region-cascader .select-trigger) {
  padding: 12px 16px;
  background-color: #ffffff;
  color: #1f2937;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  height: 46px;
}

.form-group :deep(.region-cascader .select-trigger:hover) {
  border-color: #2563eb;
}

.form-group :deep(.region-cascader .select-trigger:focus) {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-group :deep(.region-cascader .select-dropdown),
.form-group :deep(.region-cascader .city-panel) {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.form-group :deep(.region-cascader .select-option),
.form-group :deep(.region-cascader .city-option) {
  padding: 10px 16px;
  font-size: 14px;
  color: #1f2937;
}

.form-group :deep(.region-cascader .select-option:hover),
.form-group :deep(.region-cascader .city-option:hover) {
  background-color: #f3f4f6;
}

.form-group :deep(.region-cascader .select-option.active),
.form-group :deep(.region-cascader .city-option.active) {
  background-color: #eff6ff;
  color: #2563eb;
}

/* 禁用输入框样式 */
.form-input-disabled {
  padding: 12px 16px;
  background-color: #f9fafb;
  color: #6b7280;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  min-height: 44px;
  display: flex;
  align-items: center;
}

/* 地区选择器 */
.region-selector {
  width: 100%;
}

/* 密码输入组 */
.password-group {
  position: relative;
}

.password-input-container {
  position: relative;
  display: flex;
}

.password-input-container .form-input {
  padding-right: 48px;
}

.password-toggle-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: #9ca3af;
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.password-toggle-btn:hover {
  background-color: #f3f4f6;
  color: #6b7280;
}

.toggle-icon {
  line-height: 1;
}

/* 表单操作 */
.form-actions {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #f3f4f6;
}

.actions-container {
  display: flex;
  gap: 16px;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  body.sidebar-collapsed .profile-content,
  body:not(.sidebar-collapsed) .profile-content {
    width: 100%;
    margin-left: 0;
  }
  
  .card-header.unified-header,
  .card-body.unified-body {
    padding: 24px;
  }
}

@media (max-width: 768px) {
  .profile-container {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 20px 24px;
  }
  
  .header-right {
    width: 100%;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
  
  .card-header.unified-header {
    padding: 20px 24px;
  }
  
  .card-header.unified-header .card-title {
    font-size: 18px;
  }
  
  .card-body.unified-body {
    padding: 24px;
  }
  
  .form-section {
    margin-bottom: 32px;
    padding-bottom: 24px;
  }
  
  .section-title {
    font-size: 15px;
    margin-bottom: 20px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .actions-container {
    flex-direction: column;
  }
  
  .actions-container .btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 20px;
  }
  
  .card-header.unified-header .card-title {
    font-size: 16px;
  }
  
  .section-title {
    font-size: 14px;
  }
  
  .form-input,
  .form-select,
  .form-input-disabled {
    padding: 10px 14px;
    font-size: 13px;
  }
  
  .card-header.unified-header,
  .card-body.unified-body {
    padding: 16px;
  }
  
  .form-section {
    margin-bottom: 24px;
    padding-bottom: 20px;
  }
}
</style>