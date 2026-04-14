import React, { useState, useEffect, useRef } from 'react'
import { API_BASE } from '../utils/api';
import StockDetailModal from './StockDetailModal'
import { Plus, Trash2, RefreshCw, DollarSign, TrendingUp, TrendingDown, AlertCircle, Download, Upload, FileText, Lightbulb, Target, Shield, RotateCw, Edit, CheckCircle, XCircle } from 'lucide-react'

// 格式化数字：保留2位小数
const fmt = (v, suffix = '') => {
  if (v === null || v === undefined || v === '') return '--'
  const n = typeof v === 'number' ? v : parseFloat(v)
  if (isNaN(n)) return '--'
  return n.toFixed(2) + suffix
}

export default function RiskMonitor() {
  const [risk, setRisk] = useState(null)
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newPosition, setNewPosition] = useState({
    code: '',
    name: '',
    shares: '',
    avg_cost: '',
    current_price: ''
  })
  const [newCash, setNewCash] = useState('')
  const fileInputRef = useRef(null)
  
  // 编辑持仓状态
  const [editingPosition, setEditingPosition] = useState(null)
  const [editValues, setEditValues] = useState({ shares: '', avg_cost: '' })
  const [detailStock, setDetailStock] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    fetchRisk()
  }, [])

  // 获取持仓股票的完整评分数据（用于详情弹窗）
  const fetchPositionDetail = async (code) => {
    setDetailLoading(true)
    try {
      // 并行获取基本面和技术面数据
      const [scanRes, techRes] = await Promise.all([
        fetch(`${API_BASE}/api/scan?min_score=0&search=${encodeURIComponent(code)}`, { method: 'POST' }),
        fetch(`${API_BASE}/api/technical/${code}?count=250`)
      ])
      const scanData = await scanRes.json()
      const techData = await techRes.json()
      
      // 从扫描结果中找到该股票
      let stockInfo = null
      if (scanData.results) {
        stockInfo = scanData.results.find(s => s.code === code)
      }
      if (!stockInfo && scanData.industries) {
        for (const ind of scanData.industries) {
          const found = (ind.stocks || []).find(s => s.code === code)
          if (found) { stockInfo = found; break }
        }
      }
      
      // 合并数据
      const detail = stockInfo || { code, name: code, industry: '持仓', is_portfolio: true, data: {}, score: {}, signal: {} }
      // 持仓成本等数据
      const pfPos = portfolio?.positions?.find(p => p.code === code)
      if (pfPos) {
        detail.is_portfolio = true
        detail.data = { ...detail.data, avg_cost: pfPos.avg_cost, shares: pfPos.shares, price: pfPos.current_price }
        detail.data.avg_cost = pfPos.avg_cost
        detail.data.shares = pfPos.shares
      }
      
      // 技术数据
      if (!techData.error) {
        detail.technical = techData
      }
      
      setDetailStock(detail)
    } catch (e) {
      console.error('获取详情失败:', e)
    }
    setDetailLoading(false)
  }

  const fetchRisk = async () => {
    setLoading(true)
    try {
      const [riskRes, portfolioRes] = await Promise.all([
        fetch(`${API_BASE}/api/risk/check`),
        fetch(`${API_BASE}/api/portfolio`)
      ])
      const riskData = await riskRes.json()
      const pf = await portfolioRes.json()
      
      // 获取实时行情
      const codes = (pf.positions || []).map(p => p.code).join(',')
      if (codes) {
        try {
          const realtimeRes = await fetch(`${API_BASE}/api/realtime/batch?codes=${encodeURIComponent(codes)}`)
          const realtimeData = await realtimeRes.json()
          
          if (realtimeData.results) {
            pf.positions = (pf.positions || []).map(pos => {
              const rt = realtimeData.results[pos.code]
              if (rt && rt.current_price) {
                const newPrice = rt.current_price
                const oldPrice = pos.avg_cost || 0
                return {
                  ...pos,
                  current_price: newPrice,
                  change_pct: rt.change_pct || 0,
                  market_value: pos.shares * newPrice,
                  pnl_pct: oldPrice > 0 ? ((newPrice - oldPrice) / oldPrice * 100) : 0
                }
              }
              return pos
            })
            
            const totalValue = pf.cash + pf.positions.reduce((sum, p) => sum + (p.market_value || 0), 0)
            pf.total_value = totalValue
          }
        } catch (e) {
          console.error('实时行情获取失败:', e)
        }
      }
      
      setRisk(riskData)
      setPortfolio(pf)
      setNewCash(String(pf.cash || 1000000))
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const updateCash = async () => {
    try {
      const formData = new FormData()
      formData.append('cash', parseFloat(newCash) || 0)
      
      const res = await fetch(`${API_BASE}/api/portfolio/cash`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.status === 'ok') {
        setPortfolio(prev => ({ ...prev, cash: data.cash, total_value: data.total_value }))
        setRisk(prev => ({ ...prev, cash: data.cash, total_value: data.total_value }))
      }
    } catch (e) {
      console.error(e)
      alert('更新失败')
    }
  }

  const addPosition = async () => {
    if (!newPosition.code || !newPosition.name || !newPosition.shares || !newPosition.avg_cost || !newPosition.current_price) {
      alert('请填写完整信息')
      return
    }

    try {
      const res = await fetch(`${API_BASE}/api/portfolio/add?code=${newPosition.code}&name=${encodeURIComponent(newPosition.name)}&shares=${newPosition.shares}&avg_cost=${newPosition.avg_cost}&current_price=${newPosition.current_price}`, {
        method: 'POST'
      })
      const data = await res.json()
      if (data.status === 'ok') {
        setShowAddForm(false)
        setNewPosition({ code: '', name: '', shares: '', avg_cost: '', current_price: '' })
        fetchRisk()
      }
    } catch (e) {
      console.error(e)
      alert('添加失败')
    }
  }

  const deletePosition = async (code) => {
    if (!confirm('确定删除该持仓？')) return
    
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/delete/${code}`, { method: 'POST' })
      const data = await res.json()
      
      if (data.status === 'ok') {
        alert('删除成功')
        fetchRisk()  // 刷新数据
      } else {
        alert('删除失败: ' + (data.message || '未知错误'))
      }
    } catch (e) {
      alert('删除失败: ' + e.message)
    }
  }
  
  const savePosition = async (code) => {
    const shares = parseInt(editValues.shares) || 0
    const avg_cost = parseFloat(editValues.avg_cost) || 0
    
    if (shares <= 0 || avg_cost <= 0) {
      alert('请输入有效的持股数和成本价')
      return
    }
    
    try {
      const formData = new FormData()
      formData.append('shares', shares)
      formData.append('avg_cost', avg_cost)
      
      const res = await fetch(`${API_BASE}/api/portfolio/update/${code}`, { 
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      
      if (data.status === 'ok') {
        alert('更新成功')
        setEditingPosition(null)
        setEditValues({ shares: '', avg_cost: '' })
        fetchRisk()  // 刷新数据
      } else {
        alert('更新失败: ' + (data.message || '未知错误'))
      }
    } catch (e) {
      alert('更新失败: ' + e.message)
    }
  }

  // 同步持仓价格和评分
  const syncPortfolio = async () => {
    setSyncing(true)
    try {
      // 先获取实时行情
      const pf = portfolio || { positions: [], cash: 1000000 }
      const codes = (pf.positions || []).map(p => p.code).join(',')
      
      if (!codes) {
        alert('暂无持仓')
        setSyncing(false)
        return
      }
      
      const realtimeRes = await fetch(`${API_BASE}/api/realtime/batch?codes=${encodeURIComponent(codes)}`)
      const realtimeData = await realtimeRes.json()
      
      // 更新持仓价格
      const updatedPositions = (pf.positions || []).map(pos => {
        const rt = realtimeData.results?.[pos.code]
        if (rt && rt.status === 'success' && rt.current_price > 0) {
          const newPrice = rt.current_price
          const avgCost = pos.avg_cost || 0
          return {
            ...pos,
            current_price: newPrice,
            change_pct: rt.change_pct || 0,
            market_value: pos.shares * newPrice,
            pnl_pct: avgCost > 0 ? ((newPrice - avgCost) / avgCost * 100) : 0
          }
        }
        return pos
      })
      
      // 重新计算总市值
      const totalValue = (pf.cash || 0) + updatedPositions.reduce((sum, p) => sum + (p.market_value || 0), 0)
      
      // 保存到后端
      const saveRes = await fetch(`${API_BASE}/api/portfolio/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cash: pf.cash || 0,
          positions: updatedPositions
        })
      })
      const saveData = await saveRes.json()
      
      if (saveData.status === 'ok') {
        setPortfolio({
          ...pf,
          positions: updatedPositions,
          total_value: totalValue
        })
        alert(`同步完成！\n更新 ${updatedPositions.length} 只持仓\n组合总值 ¥${totalValue.toLocaleString()}`)
        fetchRisk()
      } else {
        alert('保存失败：' + (saveData.message || '未知错误'))
      }
    } catch (e) {
      alert('同步失败：' + e.message)
    }
    setSyncing(false)
  }

  const exportPortfolio = () => {
    if (!portfolio) return
    
    const exportData = {
      cash: portfolio.cash || 0,
      positions: portfolio.positions || []
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `portfolio_${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const downloadTemplate = () => {
    const template = {
      "cash": 1000000,
      "positions": [
        {
          "code": "600519",
          "name": "贵州茅台",
          "shares": 100,
          "avg_cost": 1600.00,
          "current_price": 1680.50
        },
        {
          "code": "000858",
          "name": "五粮液",
          "shares": 200,
          "avg_cost": 140.00,
          "current_price": 145.20
        }
      ]
    }
    
    const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'portfolio_template.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const importPortfolio = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      
      if (!data.positions || !Array.isArray(data.positions)) {
        alert('文件格式错误：缺少 positions 数组')
        return
      }
      
      for (const pos of data.positions) {
        if (!pos.code || !pos.name || !pos.shares || !pos.avg_cost || !pos.current_price) {
          alert('文件格式错误：持仓数据不完整')
          return
        }
      }
      
      const res = await fetch(`${API_BASE}/api/portfolio/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      
      const result = await res.json()
      if (result.status === 'ok') {
        alert(`导入成功：${data.positions.length} 条持仓，现金 ¥${data.cash || 0}`)
        fetchRisk()
      } else {
        alert('导入失败：' + (result.message || '未知错误'))
      }
    } catch (e) {
      alert('导入失败：' + e.message)
    }
    
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // 生成持仓建议
  const generateSuggestions = () => {
    const suggestions = []
    
    if (!portfolio || positions.length === 0) {
      return [{
        type: 'info',
        title: '开始构建投资组合',
        content: '建议从评分≥80分的优质股票开始，分散配置在3-5只不同行业的标的。'
      }]
    }
    
    const cashRatio = (portfolio.cash || 0) / totalValue * 100
    const positionCount = positions.length
    
    // 现金建议
    if (cashRatio < 10) {
      suggestions.push({
        type: 'warning',
        title: '现金储备不足',
        content: `当前现金占比${cashRatio.toFixed(1)}%，低于10%的安全线。建议保留一定现金应对市场波动。`
      })
    } else if (cashRatio > 50) {
      suggestions.push({
        type: 'info',
        title: '现金比例较高',
        content: `当前现金占比${cashRatio.toFixed(1)}%，可考虑逢低加仓优质标的。`
      })
    }
    
    // 分散度建议
    if (positionCount === 1) {
      suggestions.push({
        type: 'warning',
        title: '持仓过于集中',
        content: '仅持有1只股票，风险过于集中。建议分散到3-5只不同行业的标的。'
      })
    } else if (positionCount > 10) {
      suggestions.push({
        type: 'info',
        title: '持仓较为分散',
        content: `持有${positionCount}只股票，注意跟踪精力。投资大师说："分散是无知的保护伞"。`
      })
    }
    
    // 单票权重建议
    positions.forEach(([code, pos]) => {
      const weight = (pos.shares * pos.current_price) / totalValue * 100
      if (weight > 25) {
        suggestions.push({
          type: 'warning',
          title: `${pos.name} 持仓过重`,
          content: `权重${weight.toFixed(2)}%，超过单票25%上限。考虑适当减仓控制风险。`
        })
      }
      
      // 止损建议
      if (pos.pnl_pct < -15) {
        suggestions.push({
          type: 'danger',
          title: `${pos.name} 触发止损`,
          content: `亏损${Math.abs(pos.pnl_pct).toFixed(1)}%，已超过-15%止损线。建议严格执行止损纪律。`
        })
      } else if (pos.pnl_pct < -10) {
        suggestions.push({
          type: 'warning',
          title: `${pos.name} 接近止损`,
          content: `亏损${Math.abs(pos.pnl_pct).toFixed(1)}%，接近-15%止损线，需密切关注。`
        })
      }
      
      // 盈利建议
      if (pos.pnl_pct > 50) {
        suggestions.push({
          type: 'success',
          title: `${pos.name} 盈利丰厚`,
          content: `盈利${pos.pnl_pct.toFixed(1)}%，可考虑分批止盈锁定收益。投资格言："在别人贪婪时恐惧"。`
        })
      }
    })
    
    // 价值投资原则建议
    if (suggestions.length === 0) {
      suggestions.push({
        type: 'success',
        title: '组合状态良好',
        content: '当前组合符合价值投资原则，继续保持耐心，长期持有优质标的。'
      })
    }
    
    return suggestions
  }

  if (loading) {
    return (
      <div className="card text-center py-12 text-gray-400">
        <DollarSign className="w-12 h-12 mx-auto mb-4 animate-pulse" />
        <p>加载风控数据中...</p>
      </div>
    )
  }

  const positions = Object.entries(risk?.positions || {})
  const totalValue = risk?.total_value || portfolio?.total_value || portfolio?.cash || 1000000
  const suggestions = generateSuggestions()

  return (
    <div className="space-y-6">
      {/* 投资建议 */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Lightbulb className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-medium">投资建议</h3>
        </div>
        <div className="space-y-3">
          {suggestions.map((s, i) => (
            <div 
              key={i} 
              className={`p-3 rounded-lg ${
                s.type === 'danger' ? 'bg-red-400/10 border border-red-400/30' :
                s.type === 'warning' ? 'bg-yellow-400/10 border border-yellow-400/30' :
                s.type === 'success' ? 'bg-green-400/10 border border-green-400/30' :
                'bg-blue-400/10 border border-blue-400/30'
              }`}
            >
              <div className="flex items-start gap-2">
                {s.type === 'danger' && <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />}
                {s.type === 'warning' && <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5 shrink-0" />}
                {s.type === 'success' && <Target className="w-4 h-4 text-green-400 mt-0.5 shrink-0" />}
                {s.type === 'info' && <Lightbulb className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />}
                <div>
                  <p className={`font-medium ${
                    s.type === 'danger' ? 'text-red-400' :
                    s.type === 'warning' ? 'text-yellow-400' :
                    s.type === 'success' ? 'text-green-400' : 'text-blue-400'
                  }`}>{s.title}</p>
                  <p className="text-sm text-gray-300 mt-1">{s.content}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 现金管理 */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-yellow-400" />
            资金管理
          </h3>
        </div>
        
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-2">可用现金</label>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">¥</span>
              <input
                type="number"
                value={newCash}
                onChange={(e) => setNewCash(e.target.value)}
                className="flex-1 px-3 py-2 bg-dark-200 rounded-lg border border-gray-700 focus:border-primary focus:outline-none"
              />
            </div>
          </div>
          <button
            onClick={updateCash}
            className="px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition"
          >
            更新
          </button>
        </div>
      </div>

      {/* 持仓管理 */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            持仓管理
          </h3>
          <div className="flex items-center gap-2">
            {/* 同步按钮 */}
            <button
              onClick={syncPortfolio}
              disabled={syncing || positions.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
              title="同步最新价格和评分"
            >
              <RotateCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? '同步中...' : '同步价格'}
            </button>
            <button
              onClick={downloadTemplate}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-400 hover:text-white transition"
              title="下载模板"
            >
              <FileText className="w-4 h-4" />
              模板
            </button>
            <button
              onClick={exportPortfolio}
              disabled={positions.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-blue-400 hover:text-blue-300 transition disabled:opacity-50 disabled:cursor-not-allowed"
              title="导出持仓"
            >
              <Download className="w-4 h-4" />
              导出
            </button>
            <label className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-green-400 hover:text-green-300 cursor-pointer transition">
              <Upload className="w-4 h-4" />
              导入
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                onChange={importPortfolio}
                className="hidden"
              />
            </label>
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition"
            >
              <Plus className="w-4 h-4" />
              添加
            </button>
          </div>
        </div>

        {/* 添加持仓表单 */}
        {showAddForm && (
          <div className="mb-4 p-4 bg-dark-200 rounded-lg space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">股票代码</label>
                <input
                  type="text"
                  value={newPosition.code}
                  onChange={(e) => setNewPosition({...newPosition, code: e.target.value})}
                  placeholder="600519"
                  className="w-full px-3 py-2 bg-dark-300 rounded border border-gray-700 focus:border-primary focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">股票名称</label>
                <input
                  type="text"
                  value={newPosition.name}
                  onChange={(e) => setNewPosition({...newPosition, name: e.target.value})}
                  placeholder="贵州茅台"
                  className="w-full px-3 py-2 bg-dark-300 rounded border border-gray-700 focus:border-primary focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">持仓股数</label>
                <input
                  type="number"
                  value={newPosition.shares}
                  onChange={(e) => setNewPosition({...newPosition, shares: e.target.value})}
                  placeholder="100"
                  className="w-full px-3 py-2 bg-dark-300 rounded border border-gray-700 focus:border-primary focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">成本价</label>
                <input
                  type="number"
                  step="0.01"
                  value={newPosition.avg_cost}
                  onChange={(e) => setNewPosition({...newPosition, avg_cost: e.target.value})}
                  placeholder="1650.00"
                  className="w-full px-3 py-2 bg-dark-300 rounded border border-gray-700 focus:border-primary focus:outline-none text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">现价</label>
                <input
                  type="number"
                  step="0.01"
                  value={newPosition.current_price}
                  onChange={(e) => setNewPosition({...newPosition, current_price: e.target.value})}
                  placeholder="1680.00"
                  className="w-full px-3 py-2 bg-dark-300 rounded border border-gray-700 focus:border-primary focus:outline-none text-sm"
                />
              </div>
              <div className="flex items-end gap-2">
                <button
                  onClick={addPosition}
                  className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
                >
                  确认添加
                </button>
                <button
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 持仓列表 */}
        {positions.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>暂无持仓</p>
            <p className="text-sm mt-1">点击「导入」或「添加」开始管理持仓</p>
          </div>
        ) : (
          <div className="space-y-2">
            {positions.map(([code, pos]) => {
              const weight = (pos.shares * pos.current_price) / totalValue * 100
              const changeColor = (pos.change_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              const changeSign = (pos.change_pct || 0) >= 0 ? '+' : ''
              const mktVal = pos.market_value || pos.shares * pos.current_price
              
              // 检查是否在编辑状态
              const isEditing = editingPosition === code
              
              return (
                <div key={code} className="flex items-center justify-between p-3 bg-dark-200 rounded-lg hover:bg-dark-100 cursor-pointer transition" onClick={() => fetchPositionDetail(code)}>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{pos.name}</p>
                      <span className="text-xs text-gray-500">{code}</span>
                      <span className={`text-xs ${changeColor}`}>
                        {changeSign}{fmt(pos.change_pct)}%
                      </span>
                      {weight > 25 && <span className="text-xs text-yellow-400">⚠️过重</span>}
                      {pos.pnl_pct < -15 && <span className="text-xs text-red-400">🛑止损</span>}
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-400">
                      {isEditing ? (
                        <>
                          <div className="flex items-center gap-1">
                            <input
                              type="number"
                              value={editValues.shares}
                              onChange={(e) => setEditValues({...editValues, shares: e.target.value})}
                              className="w-20 px-2 py-1 bg-dark-300 rounded border border-gray-600 text-white text-sm"
                            />
                            <span>股</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span>成本:</span>
                            <input
                              type="number"
                              step="0.01"
                              value={editValues.avg_cost}
                              onChange={(e) => setEditValues({...editValues, avg_cost: e.target.value})}
                              className="w-20 px-2 py-1 bg-dark-300 rounded border border-gray-600 text-white text-sm"
                            />
                          </div>
                        </>
                      ) : (
                        <>
                          <span>{pos.shares}股</span>
                          <span>成本: ¥{fmt(pos.avg_cost)}</span>
                        </>
                      )}
                      <span className="text-white">¥{fmt(pos.current_price)}</span>
                      <span>权重: {fmt(weight)}%</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-medium">¥{fmt(mktVal)}</p>
                      <p className={`text-sm ${pos.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {pos.pnl_pct >= 0 ? '+' : ''}{fmt(pos.pnl_pct)}%
                      </p>
                    </div>
                    {isEditing ? (
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => savePosition(code)}
                          className="p-2 text-green-400 hover:bg-green-400/20 rounded transition"
                          title="保存"
                        >
                          <CheckCircle className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => { setEditingPosition(null); setEditValues({ shares: '', avg_cost: '' }) }}
                          className="p-2 text-gray-400 hover:bg-gray-400/20 rounded transition"
                          title="取消"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => { 
                          setEditingPosition(code)
                          setEditValues({ shares: pos.shares, avg_cost: pos.avg_cost })
                        }}
                        className="p-2 text-blue-400 hover:bg-blue-400/20 rounded transition"
                        title="编辑"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => deletePosition(code)}
                      className="p-2 text-red-400 hover:bg-red-400/20 rounded transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* 风控状态 */}
      <div className="grid grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-gray-400 text-sm">组合总值</p>
          <p className="text-2xl font-bold mt-1">¥{fmt(totalValue)}</p>
        </div>
        <div className="card text-center">
          <p className="text-gray-400 text-sm">可用现金</p>
          <p className="text-2xl font-bold text-yellow-400 mt-1">¥{fmt(portfolio?.cash || risk?.cash || 0)}</p>
        </div>
        <div className="card text-center">
          <p className="text-gray-400 text-sm">持仓数</p>
          <p className="text-2xl font-bold text-blue-400 mt-1">{positions.length}</p>
        </div>
        <div className="card text-center">
          <p className="text-gray-400 text-sm">现金占比</p>
          <p className="text-2xl font-bold text-purple-400 mt-1">
            {totalValue > 0 ? ((portfolio?.cash || risk?.cash || 0) / totalValue * 100).toFixed(1) : 0}%
          </p>
        </div>
      </div>

      {/* 持仓详情弹窗 */}
      {(detailStock || detailLoading) && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setDetailStock(null)}>
          <div className="bg-dark-300 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            {detailLoading ? (
              <div className="p-8 text-center text-gray-400">
                <p className="text-lg">⏳ 正在加载分析数据...</p>
                <p className="text-sm mt-2">获取基本面评分 + 技术分析...</p>
              </div>
            ) : (
              <StockDetailModal stock={detailStock} onClose={() => setDetailStock(null)} />
            )}
          </div>
        </div>
      )}
    </div>
  )
}