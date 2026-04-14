// API 配置
// 开发环境指向本地后端，生产环境指向 Railway 后端
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export { API_BASE };
