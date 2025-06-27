import axios from 'axios';

// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// 创建 Axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 日志输出请求信息
    console.log(`📤 API请求: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ 请求配置错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log(`📥 API响应: ${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    console.error('❌ API错误:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default api; 