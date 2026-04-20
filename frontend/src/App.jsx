import React, { useState, useEffect } from 'react'
import { API_BASE } from './utils/api';



import { TrendingUp, TrendingDown, Shield, Settings, RefreshCw, Search, Filter, X, Bell, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'

import RiskMonitor from './components/RiskMonitor'

import StockDetailModal from './components/StockDetailModal'

import SettingsPanel from './components/SettingsPanel'



const TABS = [

  { id: 'dashboard', label: '股票池 · 交易信号', icon: TrendingUp },

  { id: 'risk', label: '风控监控', icon: Shield },

  { id: 'settings', label: '设置', icon: Settings },

]



const fmt = (v, suffix = '') => {

  if (v === null || v === undefined || v === '') return '--'

  const n = typeof v === 'number' ? v : parseFloat(v)

  if (isNaN(n)) return '--'

  return n.toFixed(2) + suffix

}



const getScoreColor = (score) => {

  if (score >= 85) return 'text-green-400'

  if (score >= 70) return 'text-blue-400'

  if (score >= 50) return 'text-yellow-400'

  return 'text-red-400'

}



const getScoreBg = (score) => {

  if (score >= 85) return 'bg-green-400/10 border-green-400/30'

  if (score >= 70) return 'bg-blue-400/10 border-blue-400/30'

  if (score >= 50) return 'bg-yellow-400/10 border-yellow-400/30'

  return 'bg-red-400/10 border-red-400/30'

}



const getSignalIcon = (signal) => {

  if (signal === 'BUY') return <TrendingUp className="w-5 h-5 text-green-400" />

  if (signal === 'SELL') return <TrendingDown className="w-5 h-5 text-red-400" />

  return <Bell className="w-5 h-5 text-yellow-400" />

}



// 因子中文名映射（兼容新旧两套因子名）

const FACTOR_LABELS = {

  roe: 'ROE 盈利能力',

  revenue_growth: '营收增速',

  profit_growth: '净利润增速',

  gross_margin: '毛利率',

  debt_ratio: '资产负债率',

  eps: '每股收益',

  safety_margin: '安全边际',

  earnings_quality: '盈利质量',

  moat: '护城河',

  financial_health: '财务健康',

  growth: '成长性',

  capital_allocation: '资本配置',

  cash_flow: '现金流质量',

  owner_earnings: '所有者收益',

}



// 价值投资检查清单组件



// 股票缩略卡片

function StockMiniCard({ stock, onClick }) {

  const signal = stock.signal || {}

  const score = stock.score || {}

  const data = stock.data || {}

  const totalScore = score.total_score || 0

  const signalType = signal.signal || 'HOLD'



  return (

    <div onClick={onClick} className={`p-3 rounded-lg cursor-pointer hover:scale-[1.02] transition border ${getScoreBg(totalScore)}`}>

      <div className="flex items-center justify-between mb-2">

        <div className="flex items-center gap-2">

          <p className="font-medium text-sm text-white">{stock.name}</p>

          {stock.is_portfolio && <span className="px-1.5 py-0.5 text-[10px] bg-primary/20 text-primary rounded">持</span>}

        </div>

        {getSignalIcon(signalType)}

      </div>

      <div className="flex items-center justify-between">

        <div>

          <p className="text-lg font-bold text-white">¥{fmt(data.price)}</p>

          <p className={`text-sm font-bold ${getScoreColor(totalScore)}`}>{fmt(totalScore)}分</p>

        </div>

        <div className="text-right">

          <p className={`text-sm font-bold ${signalType === 'BUY' ? 'text-green-400' : signalType === 'SELL' ? 'text-red-400' : 'text-yellow-400'}`}>

            {signalType || '--'}

          </p>

          <p className="text-xs text-gray-400">{stock.industry}</p>

        </div>

      </div>

    </div>

  )

}







// 信号分类列

function SignalColumn({ title, stocks, onStockClick, color, bgColor, icon: Icon }) {

  return (

    <div className={`rounded-lg border border-gray-600 ${bgColor}`}>

      <div className={`flex items-center gap-2 px-4 py-3 border-b border-gray-600 ${color}`}>

        {Icon && <Icon className="w-4 h-4" />}

        <span className="font-medium">{title}</span>

        <span className="text-xs opacity-60">({stocks.length})</span>

      </div>

      <div className="p-2 space-y-2 max-h-80 overflow-y-auto">

        {stocks.length === 0 ? (

          <p className="text-center text-gray-400 py-4 text-sm">暂无</p>

        ) : (

          stocks.map(stock => (

            <StockMiniCard key={stock.code} stock={stock} onClick={() => onStockClick(stock)} />

          ))

        )}

      </div>

    </div>

  )

}



export default function App() {

  const [tab, setTab] = useState('dashboard')

  const [stocks, setStocks] = useState([])

  const [loading, setLoading] = useState(false)

  const [detailStock, setDetailStock] = useState(null)

  const [total, setTotal] = useState(0)

  const [search, setSearch] = useState('')

  const [industries, setIndustries] = useState([])

  const [showByIndustry, setShowByIndustry] = useState(true)

  const [showFilters, setShowFilters] = useState(false)

  const [filters, setFilters] = useState({ minScore: 0, maxScore: 100, minPrice: '', maxPrice: '', signalType: '', rating: '' })

  const [tempFilters, setTempFilters] = useState(filters)



  const loadPool = async () => {

    setLoading(true)

    try {

      const res = await fetch(`${API_BASE}/api/pool`)

      const respData = await res.json()

      const pool = respData.pool || []

      setStocks(pool.map(s => ({ code: s.code, name: s.name, market: s.market, industry: s.industry })))

      setTotal(pool.length)

    } catch (e) { console.error(e) }

    setLoading(false)

  }



  const scanPool = async (p = 1, s = search, f = filters) => {

    setLoading(true)

    const controller = new AbortController()

    const timer = setTimeout(() => controller.abort(), 60000)

    try {

      const params = new URLSearchParams({

        page: p, page_size: 200,

        min_score: f.minScore || 0, max_score: f.maxScore || 100,

        search: s,

        min_price: f.minPrice || 0, max_price: f.maxPrice || 999999,

        signal_type: f.signalType || '', rating: f.rating || '',

        group_by_industry: showByIndustry

      })

      const res = await fetch(`${API_BASE}/api/scan?${params}`, { method: 'POST', signal: controller.signal })

      const respData = await res.json()

      if (respData.industries && respData.industries.length > 0) {

        setIndustries(respData.industries || [])

        setStocks(respData.industries.flatMap(ind => ind.stocks || []))

      } else {

        setIndustries([])

        setStocks(respData.results || [])

      }

      setTotal(respData.total || 0)

    } catch (e) {

      if (e.name !== 'AbortError') console.error(e)

      else console.warn('扫描超时(60s)，已取消')

    } finally { clearTimeout(timer) }

    setLoading(false)

  }



  useEffect(() => { scanPool() }, [])

  useEffect(() => {

    const t = setTimeout(() => scanPool(1, search, filters), 500)

    return () => clearTimeout(t)

  }, [search, filters])



  const applyFilters = () => { setFilters(tempFilters); setShowFilters(false) }

  const clearFilters = () => {

    const c = { minScore: 0, maxScore: 100, minPrice: '', maxPrice: '', signalType: '', rating: '' }

    setTempFilters(c); setFilters(c); setShowFilters(false)

  }

  const hasActiveFilters = () => filters.minScore > 0 || filters.maxScore < 100 || filters.minPrice || filters.maxPrice || filters.signalType || filters.rating



  const buyStocks = stocks.filter(s => s.signal?.signal === 'BUY').sort((a, b) => (b.score?.total_score || 0) - (a.score?.total_score || 0))

  const sellStocks = stocks.filter(s => s.signal?.signal === 'SELL').sort((a, b) => (b.score?.total_score || 0) - (a.score?.total_score || 0))

  const holdStocks = stocks.filter(s => !s.signal?.signal || s.signal?.signal === 'HOLD').sort((a, b) => (b.score?.total_score || 0) - (a.score?.total_score || 0))



  return (

    <div className="min-h-screen">

      <header className="border-b border-gray-700 px-6 py-4">

        <div className="max-w-7xl mx-auto flex items-center justify-between">

          <div className="flex items-center gap-3">
            <img src="/logo.svg" alt="LeyoQuant" className="h-10" />
            <div>

              <h1 className="text-xl font-bold">乐友量化投资系统</h1>

              <p className="text-xs text-gray-400">价值投资 · 量化评分 v1.0</p>

            </div>

          </div>

          <button onClick={() => scanPool()} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition disabled:opacity-50">

            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />

            {loading ? '扫描中...' : '刷新'}

          </button>

        </div>

      </header>



      <nav className="border-b border-gray-700 px-6">

        <div className="max-w-7xl mx-auto flex gap-1">

          {TABS.map(t => (

            <button key={t.id} onClick={() => setTab(t.id)}

              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition ${tab === t.id ? 'text-primary border-primary' : 'text-gray-400 border-transparent hover:text-gray-200'}`}>

              <t.icon className="w-4 h-4" />{t.label}

            </button>

          ))}

        </div>

      </nav>



      <main className="max-w-7xl mx-auto p-6">

        {tab === 'dashboard' && (

          <div className="space-y-6">

            {/* 搜索与筛选 */}

            <div className="card">

              <div className="flex items-center gap-4 flex-wrap">

                <div className="flex-1 min-w-[200px]">

                  <div className="relative">

                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />

                    <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="搜索股票代码或名称..." className="w-full pl-10 pr-4 py-2 bg-dark-200 rounded-lg border border-gray-600 focus:border-primary focus:outline-none" />

                  </div>

                </div>

                <button onClick={() => setShowFilters(!showFilters)} className={`flex items-center gap-2 px-4 py-2 rounded-lg ${hasActiveFilters() ? 'bg-primary/20 text-primary border border-primary/50' : 'bg-dark-200 text-gray-400'}`}>

                  <Filter className="w-4 h-4" />筛选{hasActiveFilters() && <span className="w-5 h-5 bg-primary rounded-full text-xs flex items-center justify-center text-dark-300">!</span>}

                </button>

                <div className="text-sm text-gray-400">共 <span className="text-white font-bold">{total}</span> 只股票</div>

              </div>

              {showFilters && (

                <div className="mt-4 pt-4 border-t border-gray-600">

                  <div className="grid grid-cols-6 gap-4">

                    <div><label className="block text-xs text-gray-400 mb-1">最低评分</label><input type="number" value={tempFilters.minScore} onChange={(e) => setTempFilters({...tempFilters, minScore: Number(e.target.value) || 0})} className="w-full px-3 py-2 bg-dark-200 rounded border text-gray-200 text-sm" /></div>

                    <div><label className="block text-xs text-gray-400 mb-1">最高评分</label><input type="number" value={tempFilters.maxScore} onChange={(e) => setTempFilters({...tempFilters, maxScore: Number(e.target.value) || 100})} className="w-full px-3 py-2 bg-dark-200 rounded border text-gray-200 text-sm" /></div>

                    <div><label className="block text-xs text-gray-400 mb-1">最低价格</label><input type="number" value={tempFilters.minPrice} onChange={(e) => setTempFilters({...tempFilters, minPrice: e.target.value})} className="w-full px-3 py-2 bg-dark-200 rounded border text-gray-200 text-sm" /></div>

                    <div><label className="block text-xs text-gray-400 mb-1">最高价格</label><input type="number" value={tempFilters.maxPrice} onChange={(e) => setTempFilters({...tempFilters, maxPrice: e.target.value})} className="w-full px-3 py-2 bg-dark-200 rounded border text-gray-200 text-sm" /></div>

                    <div><label className="block text-xs text-gray-400 mb-1">信号</label><select value={tempFilters.signalType} onChange={(e) => setTempFilters({...tempFilters, signalType: e.target.value})} className="w-full px-3 py-2 bg-dark-200 rounded border text-gray-200 text-sm"><option value="">全部</option><option value="BUY">买入</option><option value="HOLD">持有</option><option value="SELL">卖出</option></select></div>

                    <div><label className="block text-xs text-gray-400 mb-1">等级</label><select value={tempFilters.rating} onChange={(e) => setTempFilters({...tempFilters, rating: e.target.value})} className="w-full px-3 py-2 bg-dark-200 rounded border text-gray-200 text-sm"><option value="">全部</option><option value="A+">A+</option><option value="A">A</option><option value="B+">B+</option><option value="B">B</option></select></div>

                  </div>

                  <div className="flex gap-3 mt-4"><button onClick={applyFilters} className="px-4 py-2 bg-primary text-dark-300 rounded-lg text-sm">应用</button><button onClick={clearFilters} className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm">清除</button></div>

                </div>

              )}

            </div>



            {/* 三栏信号视图 */}

            <div className="grid grid-cols-3 gap-6">

              <SignalColumn title="买入 BUY" stocks={buyStocks} onStockClick={setDetailStock} color="text-green-400" bgColor="bg-green-400/10" icon={TrendingUp} />

              <SignalColumn title="卖出 SELL" stocks={sellStocks} onStockClick={setDetailStock} color="text-red-400" bgColor="bg-red-400/10" icon={TrendingDown} />

              <SignalColumn title="持有 HOLD" stocks={holdStocks} onStockClick={setDetailStock} color="text-yellow-400" bgColor="bg-yellow-400/10" icon={Bell} />

            </div>

          </div>

        )}

        {tab === 'risk' && <RiskMonitor />}

        {tab === 'settings' && <SettingsPanel />}

      </main>



      <footer className="border-t border-gray-700 px-6 py-4 text-center text-gray-400 text-sm">

        <p>⚠️ 所有交易信号仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>

      </footer>



      {detailStock && <StockDetailModal stock={detailStock} onClose={() => setDetailStock(null)} />}

    </div>

  )

}
