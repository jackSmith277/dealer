// API 接口统一管理
import axios from 'axios'

// 创建axios实例
const service = axios.create({
    baseURL: '/api', // 使用相对路径，通过开发服务器代理转发
    timeout: 15000, // 增加超时时间到15秒
    headers: {
        'Content-Type': 'application/json'
    }
})

// 请求拦截器
service.interceptors.request.use(
    config => {
        console.log('API请求:', config.method.toUpperCase(), config.url, config.params || config.data)
        return config
    },
    error => {
        console.error('请求错误:', error)
        return Promise.reject(error)
    }
)

// 响应拦截器
service.interceptors.response.use(
    response => {
        console.log('API响应:', response.config.method.toUpperCase(), response.config.url, response.data)
        return response.data
    },
    error => {
        console.error('响应错误:', error)
        // 检查是否是网络错误或服务器错误
        if (error.response) {
            console.error('服务器响应错误:', error.response.status, error.response.data)
            // 如果是502错误，可能是服务器暂时不可用
            if (error.response.status === 502) {
                console.error('服务器网关错误，请稍后重试')
            }
        } else if (error.request) {
            console.error('网络错误:', error.message)
        } else {
            console.error('配置错误:', error.message)
        }
        return Promise.reject(error)
    }
)

export default service