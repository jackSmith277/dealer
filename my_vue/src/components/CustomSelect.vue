<template>
  <div class="custom-select-wrapper" @click.stop>
    <button
      class="select-trigger"
      type="button"
      @click.stop="toggleDropdown"
      :class="{ open: showDropdown }"
    >
      <span class="select-text">{{ displayText }}</span>
      <span class="arrow">▼</span>
    </button>
    
    <div class="select-dropdown" v-if="showDropdown" @click.stop>
      <div
        v-for="option in options"
        :key="option.value"
        class="select-option"
        :class="{ active: modelValue === option.value }"
        @click.stop="selectOption(option)"
      >
        {{ option.label }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CustomSelect',
  model: {
    prop: 'modelValue',
    event: 'update:modelValue'
  },
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    options: {
      type: Array,
      required: true,
      validator: (arr) => arr.every(item => 'value' in item && 'label' in item)
    },
    placeholder: {
      type: String,
      default: '请选择'
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      showDropdown: false
    }
  },
  computed: {
    displayText() {
      if (!this.modelValue) {
        return this.placeholder
      }
      const selected = this.options.find(opt => opt.value === this.modelValue)
      return selected ? selected.label : this.placeholder
    }
  },
  mounted() {
    document.addEventListener('click', this.closeDropdown)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeDropdown)
  },
  methods: {
    toggleDropdown() {
      this.showDropdown = !this.showDropdown
    },
    selectOption(option) {
      this.$emit('update:modelValue', option.value)
      this.showDropdown = false
    },
    closeDropdown: function(event) {
      // 检查点击是否在组件外部
      if (this.$el && !this.$el.contains(event.target)) {
        this.showDropdown = false
      }
    }
  }
}
</script>

<style scoped>
.custom-select-wrapper {
  position: relative;
  width: 100%;
}

.select-trigger {
  width: 100%;
  padding: 10px 12px;
  background-color: #ffffff;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.3s;
  box-sizing: border-box;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  height: 40px;
}

.select-trigger:hover {
  border-color: #40a9ff;
}

.select-trigger:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.select-text {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow {
  font-size: 10px;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}

.select-trigger.open .arrow {
  transform: rotate(180deg);
}

.select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: #ffffff;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 9999;
  margin-top: 2px;
}

.select-option {
  padding: 10px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 14px;
  color: #333;
}

.select-option:hover {
  background-color: #f5f5f5;
}

.select-option.active {
  background-color: #e6f7ff;
  color: #1890ff;
  font-weight: 600;
}
</style>
