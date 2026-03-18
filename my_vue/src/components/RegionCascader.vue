<template>
  <div class="region-cascader">
    <div class="cascader-wrapper">
      <!-- 省份选择 -->
      <div class="cascader-column">
        <div class="custom-select">
          <button
            class="select-trigger"
            type="button"
            @click="toggleProvinceDropdown"
            :class="{ open: showProvinceDropdown }"
          >
            <span v-if="selectedProvince === '全部地区'">全部地区</span>
            <span v-else-if="selectedProvince && selectedCity && selectedCity !== '全部城市'">{{ selectedProvince }}{{ selectedCity }}</span>
            <span v-else-if="selectedProvince && selectedCity === '全部城市'">{{ selectedProvince }}</span>
            <span v-else-if="selectedProvince">{{ selectedProvince }}</span>
            <span v-else>选择省份</span>
            <span class="arrow">▼</span>
          </button>
          
          <!-- 省份和城市面板容器 -->
          <div class="panels-container" v-if="showProvinceDropdown">
            <!-- 省份下拉面板 -->
            <div class="select-dropdown">
              <div
                class="select-option"
                :class="{ active: selectedProvince === '全部地区' }"
                @click="selectAllRegion"
              >
                全部地区
              </div>
              <div
                v-for="province in provinces"
                :key="province.code"
                class="select-option"
                :class="{ active: selectedProvince === province.name }"
                @click="selectProvince(province)"
              >
                {{ province.name }}
              </div>
            </div>

            <!-- 城市下拉面板 - 在省份面板右边 -->
            <div class="city-panel" v-if="selectedProvince && selectedProvince !== '全部地区' && cities.length > 0">
              <div
                class="city-option"
                :class="{ active: selectedCity === '全部城市' }"
                @click="selectAllCity"
              >
                全部城市
              </div>
              <div
                v-for="city in cities"
                :key="city.code"
                class="city-option"
                :class="{ active: selectedCity === city.name }"
                @click="selectCity(city)"
              >
                {{ city.name }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import regionData from '@/assets/中国省加市.json'

export default {
  name: 'RegionCascader',
  model: {
    prop: 'modelValue',
    event: 'update:modelValue'
  },
  props: {
    modelValue: {
      type: Object,
      default: () => ({ province: '', city: '' })
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      selectedProvince: this.modelValue.province || '',
      selectedCity: this.modelValue.city || '',
      provinces: [],
      cities: [],
      showProvinceDropdown: false,
      showCityDropdown: false
    }
  },
  watch: {
    modelValue(newVal) {
      this.selectedProvince = newVal.province || ''
      this.selectedCity = newVal.city || ''
    },
    selectedProvince() {
      this.updateCities()
      this.selectedCity = ''
      this.emitChange()
    },
    selectedCity() {
      this.emitChange()
    }
  },
  mounted() {
    this.provinces = regionData.children || []
    this.updateCities()
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    toggleProvinceDropdown() {
      this.showProvinceDropdown = !this.showProvinceDropdown
      this.showCityDropdown = false
      
      if (!this.showProvinceDropdown) {
        this.emitChange()
      }
    },
    selectProvince(province) {
      this.selectedProvince = province.name
      this.updateCities()
      this.emitChange()
    },
    selectAllRegion() {
      this.selectedProvince = '全部地区'
      this.selectedCity = ''
      this.cities = []
      this.showProvinceDropdown = false
      this.emitChange()
    },
    selectAllCity() {
      this.selectedCity = '全部城市'
      this.showProvinceDropdown = false
      this.emitChange()
    },
    selectCity(city) {
      this.selectedCity = city.name
      this.emitChange()
    },
    updateCities() {
      if (this.selectedProvince) {
        const provinceItem = this.provinces.find(p => p.name === this.selectedProvince)
        if (provinceItem && provinceItem.children) {
          this.cities = provinceItem.children
        } else {
          this.cities = []
        }
      } else {
        this.cities = []
      }
    },
    emitChange() {
      this.$emit('update:modelValue', {
        province: this.selectedProvince,
        city: this.selectedCity
      })
    },
    handleClickOutside(event) {
      if (!this.$el.contains(event.target)) {
        this.showProvinceDropdown = false
        this.showCityDropdown = false
        this.emitChange()
      }
    }
  }
}
</script>

<style scoped>
.region-cascader {
  width: 100%;
}

.cascader-wrapper {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.cascader-column {
  flex: 0 0 auto;
  width: 140px;
  position: relative;
}

.custom-select {
  position: relative;
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

.select-trigger:disabled {
  background-color: #f5f5f5;
  color: #999;
  cursor: not-allowed;
  border-color: #d9d9d9;
}

.arrow {
  font-size: 10px;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}

.select-trigger.open .arrow {
  transform: rotate(180deg);
}

.panels-container {
  position: absolute;
  top: 100%;
  left: 0;
  display: flex;
  gap: 0;
  z-index: 9999;
  margin-top: 2px;
}

.select-dropdown {
  background-color: #ffffff;
  border: 1px solid #d9d9d9;
  border-radius: 4px 0 0 4px;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 140px;
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

.city-panel {
  background-color: #ffffff;
  border: 1px solid #d9d9d9;
  border-left: none;
  border-radius: 0 4px 4px 0;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 120px;
}

.city-option {
  padding: 10px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 14px;
  color: #333;
  white-space: nowrap;
}

.city-option:hover {
  background-color: #f5f5f5;
}

.city-option.active {
  background-color: #e6f7ff;
  color: #1890ff;
  font-weight: 600;
}

@media (max-width: 768px) {
  .cascader-wrapper {
    flex-direction: column;
    align-items: stretch;
  }

  .cascader-column {
    width: 100%;
  }

  .panels-container {
    position: static;
    flex-direction: column;
    gap: 0;
    margin-top: 8px;
  }

  .select-dropdown {
    border-radius: 4px;
    min-width: unset;
  }

  .city-panel {
    border-left: 1px solid #d9d9d9;
    border-radius: 4px;
    min-width: unset;
  }
}
</style>
