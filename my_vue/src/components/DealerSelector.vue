<template>
  <div class="dealer-selector">
    <div class="selector-group">
      <div class="selector">
        <select v-model="localSelectedCode" @change="handleSelectionChange" class="dealer-select">
          <option value="">请选择经销商</option>
          <option v-for="dealer in dealers" :key="dealer['经销商代码']" :value="dealer['经销商代码']">
            {{ dealer['经销商代码'] }} - {{ dealer['省份'] || '未知地区' }}
          </option>
        </select>
        <div v-if="showManualInput" class="manual-input-row">
          <input
            v-model="inputCode"
            placeholder="输入经销商代码"
            class="input"
            @keyup.enter="applyManualDealer"
          />
          <select v-model="inputProvince" @change="applyManualDealer" class="province-select">
            <option value="">选择省份</option>
            <option v-for="province in provinces" :key="province" :value="province">
              {{ province }}
            </option>
          </select>
          <button class="btn" @click="applyManualDealer">查询</button>
        </div>
      </div>
      <p v-if="currentDealer['经销商代码']" class="current-tip">
        当前：{{ currentDealer['经销商代码'] }}（{{ currentDealer['省份'] || '未知省份' }}）
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
    showManualInput: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      localSelectedCode: this.selectedCode,
      inputCode: '',
      inputProvince: '',
      errorMessage: ''
    }
  },
  computed: {
    currentDealer() {
      return this.dealers.find((d) => d['经销商代码'] === this.localSelectedCode) || {}
    },
    provinces() {
      const provinceSet = new Set()
      this.dealers.forEach(dealer => {
        if (dealer['省份']) {
          provinceSet.add(dealer['省份'])
        }
      })
      return Array.from(provinceSet).sort()
    }
  },
  watch: {
    selectedCode: {
      handler(newVal) {
        this.localSelectedCode = newVal
      },
      immediate: true
    }
  },
  methods: {
    handleSelectionChange() {
      this.$emit('update:selectedCode', this.localSelectedCode)
    },
    applyManualDealer() {
      const code = (this.inputCode || '').trim()
      const province = (this.inputProvince || '').trim()

      if (!code && !province) {
        this.errorMessage = '请至少输入经销商代码或省份再查询'
        return
      }

      let target = null
      // 优先按代码精确匹配
      if (code) {
        target = this.dealers.find((d) => String(d['经销商代码']) === code)
      }
      // 若无结果且填了省份，则按省份模糊匹配第一条
      if (!target && province) {
        const lower = province.toLowerCase()
        target = this.dealers.find((d) => String(d['省份'] || '').toLowerCase().includes(lower))
      }

      if (!target) {
        this.errorMessage = '未找到对应经销商，请检查代码或省份后重试'
        return
      }

      this.localSelectedCode = target['经销商代码']
      this.$emit('update:selectedCode', this.localSelectedCode)
      this.errorMessage = ''
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
  gap: 6px;
}

.selector {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* 当showManualInput为true时，使用两行布局 */
:deep(.show-manual-input) .selector {
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
}

:deep(.show-manual-input) .selector > * {
  width: 100%;
}

:deep(.show-manual-input) .selector .dealer-select {
  margin: 0;
}

/* 手动输入行的样式 */
.manual-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.manual-input-row .input {
  flex: 1;
  min-width: 150px;
}

.manual-input-row .province-select {
  min-width: 120px;
}

.manual-input-row .btn {
  white-space: nowrap;
}

.input {
  background: #ffffff;
  border: 1px solid #d9d9d9;
  color: #333;
  padding: 8px 12px;
  border-radius: 4px;
  min-width: 150px;
  font-size: 14px;
}

.input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
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

/* 基础select样式 */
select {
  background: #ffffff;
  border: 1px solid #d9d9d9;
  color: #333;
  padding: 8px 12px;
  border-radius: 4px;
  min-width: 200px;
  font-size: 14px;
  cursor: pointer;
}

select:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

/* 适用于SalesPrediction页面的样式 */
.dealer-select {
  width: 100%;
  padding: 8px;
  margin: 4px 0 10px 0;
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
  padding-right: 30px;
  min-width: unset;
}

.dealer-select:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.province-select {
  background: #ffffff;
  border: 1px solid #d9d9d9;
  color: #333;
  padding: 8px 12px;
  border-radius: 4px;
  min-width: 120px;
  font-size: 14px;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg fill='%23333' height='16' viewBox='0 0 24 24' width='16' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/></svg>");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 16px 16px;
  padding-right: 30px;
}

.province-select:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}
</style>