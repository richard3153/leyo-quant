// API 配置
// 开发环境：localhost:8000
// 生产环境（Vercel）：空字符串 → 请求走相对路径 /api/*，由 vercel.json rewrites 代理到 Railway
const API_BASE = import.meta.env.VITE_API_BASE
  || (import.meta.env.MODE === 'production' ? '' : 'http://localhost:8000');

export { API_BASE };
