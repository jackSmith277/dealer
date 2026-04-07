// 销量预测相关API接口
import service from './index.js'
import axios from 'axios'

/**
 * 获取经销商原始销量数据
 * @param {string} dealerCode - 经销商代码
 * @param {number} months - 月份数量（默认10个月）
 * @returns {Promise} 返回销量数据数组
 */
const BASE_URL = ''
const ASSPIS_BASE_URL = '/api'

export function getOriginalSalesData(dealerCode, months = 10) {
  return axios({
    url: `${ASSPIS_BASE_URL}/sales/original`,
    method: 'get',
    params: {
      dealer_code: dealerCode,
      months: months
    }
  }).then(response => {
    console.log('获取原始销量数据响应:', response.data)
    return response.data
  }).catch(error => {
    console.error('获取原始销量数据失败:', error)
    throw error
  })
}

export function getPredictionResult(params) {
  return axios({
    url: `${ASSPIS_BASE_URL}/sales/predict`,
    method: 'post',
    data: {
      dealer_code: params.dealer_code,
      dimension: params.dimension,
      change_percentage: params.change_percentage,
      base_year: params.base_year || 2024,
      base_month: params.base_month,
      month_for_radar: params.month_for_radar
    }
  }).then(response => {
    console.log('预测结果响应:', response.data)
    return response.data
  }).catch(error => {
    console.error('预测失败:', error)
    throw error
  })
}

export function getQuantileForecast(params) {
  return axios({
    url: `${ASSPIS_BASE_URL}/forecast/quantiles`,
    method: 'post',
    data: {
      dealer_code: params.dealer_code,
      base_year: params.base_year || 2024,
      base_month: params.base_month,
      horizons: params.horizons,
      quantiles: params.quantiles || [0.1, 0.5, 0.9],
      scenarios: params.scenarios
    }
  }).then(response => {
    console.log('分位数预测响应:', response.data)
    return response.data
  }).catch(error => {
    console.error('分位数预测失败:', error)
    throw error
  })
}

/**
 * 获取历史预测记录列表
 * @returns {Promise} 返回历史记录数组
 */
export function getPredictionHistory() {
  const token = localStorage.getItem('token')
  return axios({
    url: `${BASE_URL}/api/prediction/history`,
    method: 'get',
    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
  }).then(response => {
    console.log('获取历史记录响应:', response.data)
    return response.data
  }).catch(error => {
    console.error('获取历史记录失败:', error)
    throw error
  })
}

export function getPredictionHistoryDetail(id) {
  return axios({
    url: `${BASE_URL}/api/prediction/history/${id}`,
    method: 'get'
  }).then(response => {
    console.log('获取历史记录详情响应:', response.data)
    return response.data
  }).catch(error => {
    console.error('获取历史记录详情失败:', error)
    throw error
  })
}

export function savePredictionHistory(data) {
  return axios({
    url: `${BASE_URL}/api/prediction/history`,
    method: 'post',
    headers: {
      'Content-Type': 'application/json'
    },
    data: data
  }).then(response => {
    console.log('保存历史记录响应:', response.data)
    return response.data
  }).catch(error => {
    console.error('保存历史记录失败:', error)
    throw error
  })
}