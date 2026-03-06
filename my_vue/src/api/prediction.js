// 销量预测相关API接口
import service from './index.js'
import axios from 'axios'

/**
 * 获取经销商原始销量数据
 * @param {string} dealerCode - 经销商代码
 * @param {number} months - 月份数量（默认10个月）
 * @returns {Promise} 返回销量数据数组
 */
export function getOriginalSalesData(dealerCode, months = 10) {
  return service({
    url: '/sales/original', // 根据api.py的实际路由
    method: 'get',
    params: {
      dealer_code: dealerCode,
      months: months
    }
  })
}

/**
 * 获取预测销量结果
 * @param {Object} params - 预测参数
 * @param {string} params.dealer_code - 经销商代码
 * @param {string} params.dimension - 变化维度
 * @param {number} params.change_percentage - 变化百分比
 * @param {number} params.month - 预测月份
 * @param {number} params.month_for_radar - 雷达图月份
 * @returns {Promise} 返回预测结果（包含预测销量、销量变化数据、预测月份五力数据）
 */
export function getPredictionResult(params) {
  return service({
    url: '/sales/predict', // 根据api.py的实际路由
    method: 'post',
    data: {
      dealer_code: params.dealer_code,
      dimension: params.dimension,
      change_percentage: params.change_percentage,
      month: params.month,
      month_for_radar: params.month_for_radar
    }
  })
}

/**
 * 获取历史预测记录列表
 * @returns {Promise} 返回历史记录数组
 */
export function getPredictionHistory() {
  return axios({
    url: 'http://localhost:5000/api/prediction/history', // 直接请求本地后端服务器
    method: 'get'
  }).then(response => {
    console.log('获取历史记录响应:', response.data)
    return response.data
  }).catch(error => {
    console.error('获取历史记录失败:', error)
    throw error
  })
}

/**
 * 获取历史预测记录详情
 * @param {number} id - 历史记录ID
 * @returns {Promise} 返回历史记录详情
 */
export function getPredictionHistoryDetail(id) {
  return axios({
    url: `http://localhost:5000/api/prediction/history/${id}`, // 直接请求本地后端服务器
    method: 'get'
  }).then(response => {
    console.log('获取历史记录详情响应:', response.data)
    return response.data
  }).catch(error => {
    console.error('获取历史记录详情失败:', error)
    throw error
  })
}

/**
 * 保存预测历史记录
 * @param {Object} data - 预测记录数据
 * @returns {Promise} 返回保存结果
 */
export function savePredictionHistory(data) {
  return axios({
    url: 'http://localhost:5000/api/prediction/history', // 直接请求本地后端服务器
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