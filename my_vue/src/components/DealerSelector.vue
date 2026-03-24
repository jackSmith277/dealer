<template>
  <div class="dealer-selector">
    <div class="selector-group">
      <div class="selector-row">
        <select v-model="localSelectedCode" @change="handleSelectionChange" class="dealer-select">
          <option value="">请选择经销商</option>
          <option v-for="dealer in dealers" :key="dealer['经销商代码']" :value="dealer['经销商代码']">
            {{ dealer['经销商代码'] }} - {{ dealer['省份'] || '未知地区' }}
          </option>
        </select>
      </div>
      <div class="manual-input-row">
        <input
          v-model="inputCode"
          placeholder="手动输入经销商代码"
          class="input"
          @input="handleCodeInput"
          @keyup.enter="applyManualDealer"
        />
        <div class="province-display" :class="{ 'has-province': matchedProvince }">
          <span class="province-label">省份：</span>
          <span class="province-value">{{ matchedProvince || '自动匹配' }}</span>
        </div>
        <button class="btn" @click="applyManualDealer">应用</button>
      </div>
      <p v-if="currentDealer['经销商代码']" class="current-tip">
        当前：{{ currentDealer['经销商代码'] }}（{{ currentDealer['省份'] || '未知省份' }}{{ currentDealer['城市'] ? ' - ' + currentDealer['城市'] : '' }}）
      </p>
      <p v-if="errorMessage" class="error-tip">
        {{ errorMessage }}
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DealerSelector',
  model: {
    prop: 'selectedCode',
    event: 'update:selectedCode'
  },
  props: {
    dealers: {
      type: Array,
      default: () => []
    },
    selectedCode: {
      type: String,
      default: ''
    },
    errorMessage: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      localSelectedCode: this.selectedCode,
      inputCode: '',
      matchedProvince: ''
    }
  },
  computed: {
    currentDealer() {
      return this.dealers.find((d) => d['经销商代码'] === this.localSelectedCode) || {}
    }
  },
  watch: {
    selectedCode: {
      handler(newVal) {
        this.localSelectedCode = newVal
        this.updateMatchedProvince(newVal)
      },
      immediate: true
    }
  },
  methods: {
    handleSelectionChange() {
      this.$emit('update:selectedCode', this.localSelectedCode)
      this.updateMatchedProvince(this.localSelectedCode)
      this.inputCode = this.localSelectedCode
    },
    handleCodeInput() {
      const code = (this.inputCode || '').trim()
      this.updateMatchedProvince(code)
    },
    updateMatchedProvince(code) {
      if (!code) {
        this.matchedProvince = ''
        return
      }
      const dealer = this.dealers.find((d) => String(d['经销商代码']) === code)
      if (dealer) {
        this.matchedProvince = dealer['省份'] || ''
      } else {
        this.matchedProvince = ''
      }
    },
    applyManualDealer() {
      const code = (this.inputCode || '').trim()

      if (!code) {
        this.$emit('update:error', '请输入经销商代码')
        return
      }

      const target = this.dealers.find((d) => String(d['经销商代码']) === code)

      if (!target) {
        this.$emit('update:error', '未找到对应经销商，请检查代码后重试')
        return
      }

      this.localSelectedCode = target['经销商代码']
      this.$emit('update:selectedCode', this.localSelectedCode)
      this.$emit('update:error', '')
      this.$emit('apply-manual', target)
    }
  }
}
</script>

<style scoped>
.dealer-selector {
  width: 100%;
  padding: 10px 0;
}

.selector-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.selector-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.manual-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.input {
  background: #ffffff;
  border: 1px solid #d9d9d9;
  color: #333;
  padding: 8px 12px;
  border-radius: 4px;
  flex: 1;
  min-width: 150px;
  font-size: 14px;
}

.input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.province-display {
  display: flex;
  align-items: center;
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 8px 12px;
  min-width: 140px;
}

.province-display.has-province {
  background: #e6f7ff;
  border-color: #91d5ff;
}

.province-label {
  color: #666;
  font-size: 14px;
  margin-right: 4px;
}

.province-value {
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

.province-display.has-province .province-value {
  color: #1890ff;
}

.btn {
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid #1890ff;
  background: #1890ff;
  color: #ffffff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  white-space: nowrap;
}

.btn:hover {
  background: #40a9ff;
  border-color: #40a9ff;
}

.current-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #666;
}

.error-tip {
  margin-top: 2px;
  font-size: 12px;
  color: #ff4d4f;
}

.dealer-select {
  width: 100%;
  padding: 8px 30px 8px 12px;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
  font-size: 14px;
  box-sizing: border-box;
  background-color: #ffffff;
  color: #333;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg fill='%23333' height='16' viewBox='0 0 24 24' width='16' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/></svg>");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 16px 16px;
  cursor: pointer;
}

.dealer-select:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}
</style>
