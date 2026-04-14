import React, { useState, useEffect } from 'react'
import { API_BASE } from '../utils/api';
import { TrendingUp, TrendingDown, Minus, Star, Shield, DollarSign, BarChart3, Target, Zap, RefreshCw, X, AlertTriangle, CheckCircle2, XCircle, Activity, ArrowUpRight, ArrowDownRight, BarChart2, PieChart, Bell, AlertCircle, Download, Upload, FileText, Lightbulb, Settings, Filter, Search, Plus, Trash2, Edit, CheckCircle, RotateCw, RotateCcw } from 'lucide-react'
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
function ValueChecklist({ checklist }) {
  if (!checklist) return null
  return (
    <div className="card">
      <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
        <span className="text-xl">🎯</span> 价值投资原则检查
      </h3>
      <div className="grid grid-cols-2 gap-3">
        {Object.entries(checklist).map(([key, item]) => (
          <div key={key} className={`p-3 rounded-lg border ${item.passed ? 'bg-green-400/5 border-green-400/20' : 'bg-red-400/5 border-red-400/20'}`}>
            <div className="flex items-center gap-2 mb-1">
              {item.passed
                ? <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
                : <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              }
              <span className="text-sm font-medium">{item.label}</span>
            </div>
            <p className="text-xs text-gray-400 ml-6">{item.detail}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// 持仓信息组件
function PortfolioInfo({ stock }) {
  if (!stock.is_portfolio) return null
  const data = stock.data || {}
  const avgCost = data.avg_cost || 0
  const currentPrice = data.price || 0
  const shares = data.shares || 0
  const pnlPct = avgCost > 0 ? ((currentPrice - avgCost) / avgCost * 100) : 0
  const pnlAmt = shares > 0 ? (currentPrice - avgCost) * shares : 0
  const marketValue = shares * currentPrice
  const isProfit = pnlPct >= 0

  return (
    <div className="card">
      <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
        <span className="text-xl">💼</span> 持仓详情
      </h3>
      <div className="grid grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold">{shares}</p>
          <p className="text-xs text-gray-500">持股数量</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold">¥{fmt(avgCost)}</p>
          <p className="text-xs text-gray-500">持仓成本</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold">¥{fmt(marketValue)}</p>
          <p className="text-xs text-gray-500">市值</p>
        </div>
        <div className="text-center">
          <p className={`text-2xl font-bold ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
            {isProfit ? '+' : ''}{fmt(pnlPct)}%
          </p>
          <p className="text-xs text-gray-500">盈亏 ({isProfit ? '+' : ''}¥{fmt(Math.abs(pnlAmt))})</p>
        </div>
      </div>
    </div>
  )
}

// 股票详情弹窗
// 技术分析面板
function TechnicalPanel({ code }) {
  const [ta, setTa] = useState(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState('indicators')

  useEffect(() => {
    if (!code) return
    setLoading(true)
    fetch(`${API_BASE}/api/backtest/recommend/${code}`).then(r => r.json()).then(d => {
      setTa(d)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [code])

  if (loading) return <div className="card"><p className="text-center text-gray-500 py-4">⏳ 加载技术分析数据...</p></div>
  if (!ta || ta.error) return <div className="card"><p className="text-center text-red-400 py-4">技术数据获取失败: {ta?.error || '未知错误'}</p></div>

  const ind = ta.indicators || {}
  const sig = ta.current_signal || ta.signal || {}
  const bts = ta.backtests || {}

  const maColor = (current, ma) => {
    if (!ma || ma <= 0) return 'text-gray-400'
    return current > ma ? 'text-green-400' : 'text-red-400'
  }

  const indCard = (label, value, unit = '') => (
    <div className="text-center p-2 bg-dark-100 rounded-lg">
      <p className="text-lg font-bold">{typeof value === 'number' ? value.toFixed(2) : value}{unit}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )

  const stratColor = (ret) => {
    if (ret > 10) return 'text-green-400'
    if (ret > 0) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="space-y-4">
      {/* 今日行情 */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-bold flex items-center gap-2"><span>📊</span> 技术指标</h3>
          <div className="flex items-center gap-2">
            {['indicators', 'signal', 'backtest', 'strategy'].map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-3 py-1 rounded text-xs ${tab === t ? 'bg-primary/20 text-primary' : 'bg-dark-100 text-gray-400'}`}>
                {t === 'indicators' ? '指标' : t === 'signal' ? '信号' : t === 'backtest' ? '回测' : '策略'}
              </button>
            ))}
          </div>
        </div>

        {/* K线行情 */}
        <div className="grid grid-cols-5 gap-2 mb-3">
          {indCard('今开', ind.today?.open)}
          {indCard('最高', ind.today?.high)}
          {indCard('最低', ind.today?.low)}
          {indCard('成交量(万)', ((ind.today?.volume || 0) / 10000).toFixed(0))}
          <div className="text-center p-2 bg-dark-100 rounded-lg">
            <p className={`text-lg font-bold ${(ind.today?.change_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {(ind.today?.change_pct || 0) >= 0 ? '+' : ''}{ind.today?.change_pct?.toFixed(2)}%
            </p>
            <p className="text-xs text-gray-500">涨跌幅</p>
          </div>
        </div>

        {tab === 'indicators' && (
          <div className="space-y-3">
            {/* 均线 */}
            <div>
              <p className="text-xs text-gray-500 mb-1">均线系统</p>
              <div className="grid grid-cols-5 gap-2">
                {[['MA5', ind.MA5], ['MA10', ind.MA10], ['MA20', ind.MA20], ['MA30', ind.MA30], ['MA60', ind.MA60]].map(([k, v]) => (
                  <div key={k} className={`text-center p-2 rounded-lg ${v && ind.today?.close > v ? 'bg-green-400/10' : v && ind.today?.close < v ? 'bg-red-400/10' : 'bg-dark-100'}`}>
                    <p className={`text-sm font-bold ${v ? maColor(ind.today?.close, v) : 'text-gray-500'}`}>{v ? v.toFixed(2) : '--'}</p>
                    <p className="text-xs text-gray-500">{k}</p>
                  </div>
                ))}
              </div>
            </div>
            {/* MACD */}
            <div>
              <p className="text-xs text-gray-500 mb-1">MACD</p>
              <div className="grid grid-cols-3 gap-2">
                <div className={`text-center p-2 rounded-lg ${(ind.DIF || 0) > 0 ? 'bg-green-400/10' : 'bg-red-400/10'}`}>
                  <p className="text-sm font-bold">{(ind.DIF || 0).toFixed(3)}</p><p className="text-xs text-gray-500">DIF</p>
                </div>
                <div className="text-center p-2 bg-dark-100 rounded-lg">
                  <p className="text-sm font-bold">{(ind.DEA || 0).toFixed(3)}</p><p className="text-xs text-gray-500">DEA</p>
                </div>
                <div className={`text-center p-2 rounded-lg ${(ind.MACD || 0) > 0 ? 'bg-green-400/10' : 'bg-red-400/10'}`}>
                  <p className={`text-sm font-bold ${(ind.MACD || 0) > 0 ? 'text-green-400' : 'text-red-400'}`}>{(ind.MACD || 0).toFixed(3)}</p>
                  <p className="text-xs text-gray-500">MACD柱</p>
                </div>
              </div>
            </div>
            {/* RSI */}
            <div>
              <p className="text-xs text-gray-500 mb-1">RSI</p>
              <div className="grid grid-cols-3 gap-2">
                {[['RSI6', ind.RSI6], ['RSI12', ind.RSI12], ['RSI24', ind.RSI24]].map(([k, v]) => {
                  let bg = 'bg-dark-100'
                  if (v < 30) bg = 'bg-green-400/10'
                  else if (v > 70) bg = 'bg-red-400/10'
                  else if (v >= 45 && v <= 65) bg = 'bg-green-400/10'
                  let color = 'text-gray-300'
                  if (v < 30) color = 'text-green-400'
                  else if (v > 70) color = 'text-red-400'
                  return (
                    <div key={k} className={`text-center p-2 rounded-lg ${bg}`}>
                      <p className={`text-sm font-bold ${color}`}>{v?.toFixed(1) || '--'}</p>
                      <p className="text-xs text-gray-500">{k}</p>
                    </div>
                  )
                })}
              </div>
            </div>
            {/* KDJ */}
            <div>
              <p className="text-xs text-gray-500 mb-1">KDJ</p>
              <div className="grid grid-cols-3 gap-2">
                {[['K', ind.KDJ_K], ['D', ind.KDJ_D], ['J', ind.KDJ_J]].map(([k, v]) => {
                  let color = 'text-gray-300'
                  if (v > 80 || v < 20) color = 'text-red-400'
                  else if (v >= 50 && v <= 80) color = 'text-green-400'
                  return (
                    <div key={k} className="text-center p-2 bg-dark-100 rounded-lg">
                      <p className={`text-sm font-bold ${color}`}>{v?.toFixed(1) || '--'}</p>
                      <p className="text-xs text-gray-500">KDJ_{k}</p>
                    </div>
                  )
                })}
              </div>
            </div>
            {/* 布林带 */}
            <div>
              <p className="text-xs text-gray-500 mb-1">布林带 (20日)</p>
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center p-2 bg-red-400/10 rounded-lg">
                  <p className="text-sm font-bold text-red-400">{(ind.BB_Upper || 0).toFixed(2)}</p>
                  <p className="text-xs text-gray-500">上轨</p>
                </div>
                <div className="text-center p-2 bg-dark-100 rounded-lg">
                  <p className="text-sm font-bold">{(ind.BB_Middle || 0).toFixed(2)}</p>
                  <p className="text-xs text-gray-500">中轨</p>
                </div>
                <div className="text-center p-2 bg-green-400/10 rounded-lg">
                  <p className="text-sm font-bold text-green-400">{(ind.BB_Lower || 0).toFixed(2)}</p>
                  <p className="text-xs text-gray-500">下轨</p>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">当前价格偏离中轨: {(ind.BB_Middle ? (((ind.today?.close - ind.BB_Middle) / ind.BB_Middle) * 100).toFixed(1) : '--')}%</p>
            </div>
          </div>
        )}

        {tab === 'signal' && (
          <div className="space-y-3">
            <div className={`p-3 rounded-lg border ${sig.signal === 'BUY' ? 'bg-green-400/10 border-green-400/30' : sig.signal === 'SELL' ? 'bg-red-400/10 border-red-400/30' : 'bg-yellow-400/10 border-yellow-400/30'}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-xl font-bold ${sig.signal === 'BUY' ? 'text-green-400' : sig.signal === 'SELL' ? 'text-red-400' : 'text-yellow-400'}`}>
                    技术信号: {sig.signal === 'BUY' ? '📈 买入' : sig.signal === 'SELL' ? '📉 卖出' : '➡️ 观望'}
                  </p>
                  <p className="text-sm text-gray-400">置信度: {sig.confidence}% · 信号强度: {sig.strength > 0 ? '+' : ''}{sig.strength}</p>
                </div>
                <div className={`text-3xl font-bold ${sig.signal === 'BUY' ? 'text-green-400' : sig.signal === 'SELL' ? 'text-red-400' : 'text-yellow-400'}`}>
                  {sig.technical_score}
                </div>
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-gray-500">指标信号明细</p>
              {sig.signals?.map((s, i) => (
                <div key={i} className={`flex items-center gap-2 text-sm p-1.5 rounded ${s[1].includes('+') ? 'text-green-400' : s[1].includes('-') ? 'text-red-400' : 'text-gray-400'}`}>
                  <span>{s[1].includes('+') ? '✅' : s[1].includes('-') ? '⚠️' : '➡️'}</span>
                  <span className="flex-1">{s[0]}</span>
                  <span className="text-xs opacity-60">{s[1]}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === 'backtest' && (
          <div className="space-y-3">
            {ta.best_strategy && (
              <div className="p-3 bg-primary/10 border border-primary/30 rounded-lg">
                <p className="text-sm text-primary">🏆 最优策略: {ta.best_strategy.name} | 年化 {ta.best_strategy.annualized_return}% | 胜率 {ta.best_strategy.win_rate}%</p>
              </div>
            )}
            <div className="space-y-2">
              {Object.entries(bts).map(([key, bt]) => (
                <div key={key} className={`p-3 rounded-lg border ${key === ta.best_strategy?.name ? 'border-green-400/30 bg-green-400/5' : 'border-gray-700 bg-dark-100'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{bt.strategy_name}</span>
                      {key === Object.keys(bts).find(k => bts[k] === Object.values(bts).reduce((a, b) => b.annualized_return > a.annualized_return ? b : a, bts.combo)) && <span className="text-xs bg-green-400/20 text-green-400 px-2 py-0.5 rounded">最优</span>}
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      <span>交易{bt.total_trades}次</span>
                      <span className={bt.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}>胜率{bt.win_rate}%</span>
                      <span className={stratColor(bt.annualized_return)}>年化{bt.annualized_return}%</span>
                      <span className="text-red-400">回撤{bt.max_drawdown}%</span>
                    </div>
                  </div>
                  {bt.recent_trades?.length > 0 && (
                    <div className="flex gap-2 text-xs overflow-x-auto pb-1">
                      {bt.recent_trades.slice(-6).map((t, i) => (
                        <div key={i} className={`px-2 py-1 rounded flex-shrink-0 ${t.type === 'BUY' ? 'bg-green-400/20 text-green-400' : t.type === 'SELL' || t.type === 'CLOSE' ? 'bg-red-400/20 text-red-400' : 'bg-gray-700'}`}>
                          {t.type === 'BUY' ? '买' : t.type === 'SELL' ? '卖' : '平'} ¥{t.price.toFixed(2)}
                          {t.profit_pct !== undefined ? `${t.profit_pct > 0 ? '+' : ''}${t.profit_pct}%` : ''}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-600">回测数据基于过去{ta.period_days}个交易日，历史表现不代表未来收益</p>
          </div>
        )}
      </div>
          {/* ===== 策略分析tab ===== */}
          {tab === 'strategy' && ta && !ta.error && (
            <div className="space-y-4">
              {/* 投资建议卡片 */}
              {ta.recommendation && (
                <div className={`p-4 rounded-lg border ${ta.current_signal?.type === 'BUY' ? 'bg-green-400/10 border-green-400/30' : ta.current_signal?.type === 'SELL' ? 'bg-red-400/10 border-red-400/30' : 'bg-yellow-400/10 border-yellow-400/30'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {ta.current_signal?.type === 'BUY' ? <TrendingUp className="w-5 h-5 text-green-400" /> :
                     ta.current_signal?.type === 'SELL' ? <TrendingDown className="w-5 h-5 text-red-400" /> :
                     <Minus className="w-5 h-5 text-yellow-400" />}
                    <span className={`font-bold text-lg ${ta.current_signal?.type === 'BUY' ? 'text-green-400' : ta.current_signal?.type === 'SELL' ? 'text-red-400' : 'text-yellow-400'}`}>
                      {ta.recommendation.verdict}
                    </span>
                    <span className="px-2 py-0.5 text-xs bg-dark-100 rounded">风险: {ta.recommendation.risk_level}</span>
                  </div>
                  <p className="text-sm text-gray-300">{ta.recommendation.action}</p>
                </div>
              )}

              {/* 关键指标 */}
              {ta.recommendation && (
                <div className="grid grid-cols-4 gap-2">
                  <div className="text-center p-3 bg-dark-100 rounded-lg">
                    <p className="text-2xl font-bold text-green-400">{ta.recommendation.expected_annualized || 0}%</p>
                    <p className="text-xs text-gray-500">历史年化收益</p>
                  </div>
                  <div className="text-center p-3 bg-dark-100 rounded-lg">
                    <p className="text-2xl font-bold text-blue-400">{ta.recommendation.historical_win_rate || 0}%</p>
                    <p className="text-xs text-gray-500">历史胜率</p>
                  </div>
                  <div className="text-center p-3 bg-dark-100 rounded-lg">
                    <p className="text-2xl font-bold text-yellow-400">{ta.recommendation.sharpe_ratio || 0}</p>
                    <p className="text-xs text-gray-500">夏普比率</p>
                  </div>
                  <div className="text-center p-3 bg-dark-100 rounded-lg">
                    <p className="text-2xl font-bold text-red-400">{ta.recommendation.stop_loss || -8}%</p>
                    <p className="text-xs text-gray-500">建议止损</p>
                  </div>
                </div>
              )}

              {/* 最优策略 */}
              {ta.optimal_config && (
                <div className="card">
                  <h4 className="font-bold mb-2 flex items-center gap-2"><Target className="w-4 h-4 text-primary" /> 最优参数配置</h4>
                  <div className="grid grid-cols-4 gap-2 text-sm">
                    <div className="text-center p-2 bg-green-400/10 rounded">
                      <p className="text-green-400 font-bold">{ta.optimal_config.stop_loss}%</p>
                      <p className="text-xs text-gray-500">止损</p>
                    </div>
                    <div className="text-center p-2 bg-red-400/10 rounded">
                      <p className="text-red-400 font-bold">{ta.optimal_config.take_profit}%</p>
                      <p className="text-xs text-gray-500">止盈</p>
                    </div>
                    <div className="text-center p-2 bg-blue-400/10 rounded">
                      <p className="text-blue-400 font-bold">&lt;{ta.optimal_config.rsi_buy_thresh}</p>
                      <p className="text-xs text-gray-500">RSI买入</p>
                    </div>
                    <div className="text-center p-2 bg-yellow-400/10 rounded">
                      <p className="text-yellow-400 font-bold">&gt;{ta.optimal_config.rsi_sell_thresh}</p>
                      <p className="text-xs text-gray-500">RSI卖出</p>
                    </div>
                  </div>
                </div>
              )}

              {/* 策略对比表 */}
              {ta.strategy_comparison && ta.strategy_comparison.length > 0 && (
                <div className="card">
                  <h4 className="font-bold mb-3 flex items-center gap-2"><BarChart3 className="w-4 h-4 text-primary" /> 策略有效性对比</h4>
                  <div className="space-y-2">
                    {ta.strategy_comparison.map((s, i) => (
                      <div key={s.strategy} className={`flex items-center gap-3 p-2 rounded-lg ${s.recommended ? 'bg-primary/10 border border-primary/30' : 'bg-dark-100'}`}>
                        <span className="w-6 h-6 rounded-full bg-dark-200 flex items-center justify-center text-xs font-bold">
                          {i + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={`text-sm font-bold ${s.recommended ? 'text-primary' : 'text-gray-300'}`}>
                              {s.strategy === 'combo' ? '综合策略' :
                               s.strategy === 'ma_cross' ? '均线交叉' :
                               s.strategy === 'macd_cross' ? 'MACD金叉死叉' :
                               s.strategy === 'rsi_reversal' ? 'RSI超跌反转' :
                               s.strategy === 'bollinger' ? '布林带' :
                               s.strategy === 'conservative' ? '保守策略' : s.strategy}
                            </span>
                            {s.recommended && <span className="text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded">推荐</span>}
                          </div>
                          <p className="text-xs text-gray-500">
                            基准 {s.benchmark_return?.toFixed(1) || 0}% · 超额 {s.excess_return >= 0 ? '+' : ''}{s.excess_return?.toFixed(1) || 0}%
                          </p>
                        </div>
                        <div className="text-right flex items-center gap-3">
                          <div className="text-center">
                            <p className={`text-sm font-bold ${s.annualized >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {s.annualized >= 0 ? '+' : ''}{s.annualized?.toFixed(1) || 0}%
                            </p>
                            <p className="text-xs text-gray-500">年化</p>
                          </div>
                          <div className="text-center">
                            <p className={`text-sm font-bold ${s.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                              {s.win_rate?.toFixed(0) || 0}%
                            </p>
                            <p className="text-xs text-gray-500">胜率</p>
                          </div>
                          <div className="text-center">
                            <p className={`text-sm font-bold ${s.sharpe >= 0 ? 'text-blue-400' : 'text-red-400'}`}>
                              {s.sharpe?.toFixed(2) || 0}
                            </p>
                            <p className="text-xs text-gray-500">夏普</p>
                          </div>
                          <div className="text-center">
                            <p className="text-sm font-bold text-red-400">
                              {s.max_dd?.toFixed(1) || 0}%
                            </p>
                            <p className="text-xs text-gray-500">最大回撤</p>
                          </div>
                          <div className="text-center hidden sm:block">
                            <p className="text-sm font-bold text-gray-300">
                              {s.pl_ratio ? `${s.pl_ratio}x` : '--'}
                            </p>
                            <p className="text-xs text-gray-500">盈亏比</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}


    </div>
  )
}




function StockDetailModal({ stock, onClose }) {
  if (!stock) return null
  const signal = stock.signal || {}
  const score = stock.score || {}
  const data = stock.data || {}
  const [sending, setSending] = useState(false)
  const [result, setResult] = useState(null)
  const [showTechnical, setShowTechnical] = useState(false)

  const sendToWeChat = async () => {
    setSending(true)
    try {
      const res = await fetch(`${API_BASE}/api/wechat/signal/${stock.code}`, { method: 'POST' })
      const resData = await res.json()
      setResult(resData)
    } catch (e) {
      setResult({ status: 'error', message: e.message })
    }
    setSending(false)
  }

  // 优先用 signal.strategy（新版个性化），降级用 signal.signal（简单判断）
  const signalType = signal.signal || 'HOLD'
  const totalScore = score.total_score || 0
  const rating = score.rating || ''

  // 从 signal.factor_scores 获取因子分（新），兼容旧 score.scores
  const factorScores = signal.factor_scores || score.scores || {}

  // 个性化策略（来自 signal_generator 的策略数组）
  const strategyItems = signal.strategy_items || (
    signalType === 'BUY'
      ? [`评分 ${totalScore}分，给予买入信号，财务数据良好，适合中长期持有`]
      : signalType === 'SELL'
      ? [`评分 ${totalScore}分，给予卖出信号，注意风险控制`]
      : [`评分 ${totalScore}分，维持观望，等待更明确信号`]
  )

  const actionColor = signalType === 'BUY' ? 'text-green-400' : signalType === 'SELL' ? 'text-red-400' : 'text-yellow-400'
  const actionBg = signalType === 'BUY' ? 'bg-green-400/10 border-green-400/30' : signalType === 'SELL' ? 'bg-red-400/10 border-red-400/30' : 'bg-yellow-400/10 border-yellow-400/30'

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-dark-300 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {/* 头部 */}
        <div className="sticky top-0 bg-dark-300 border-b border-gray-700 p-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            {getSignalIcon(signalType)}
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold">{stock.name}</h2>
                {stock.is_portfolio && <span className="px-2 py-0.5 text-xs bg-primary/20 text-primary rounded-full">持仓</span>}
              </div>
              <p className="text-sm text-gray-400">{stock.code} · {stock.industry}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className={`text-3xl font-bold ${getScoreColor(totalScore)}`}>{fmt(totalScore)}</div>
              <div className="text-sm text-gray-400">{rating}</div>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-dark-100 rounded-lg"><X className="w-6 h-6" /></button>
          </div>
        </div>

        <div className="p-6 space-y-5">
          {/* 信号与行动 */}
          <div className={`p-4 rounded-lg border ${actionBg}`}>
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                {getSignalIcon(signalType)}
                <div>
                  <p className={`text-2xl font-bold ${actionColor}`}>{signalType} — {signalType === 'BUY' ? '买入' : signalType === 'SELL' ? '卖出' : '持有'}</p>
                  <p className="text-sm text-gray-400">置信度: {signal.confidence || '--'}%</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {signal.upside !== undefined && signal.upside > 0 && (
                  <div className="text-center px-3 py-1 bg-dark-300/50 rounded-lg">
                    <p className="text-xl font-bold text-green-400">+{signal.upside}%</p>
                    <p className="text-xs text-gray-400">目标空间</p>
                  </div>
                )}
                {signal.target_price > 0 && (
                  <div className="text-center px-3 py-1 bg-dark-300/50 rounded-lg">
                    <p className="text-xl font-bold">¥{signal.target_price}</p>
                    <p className="text-xs text-gray-400">目标价</p>
                  </div>
                )}
                <button onClick={sendToWeChat} disabled={sending} className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition disabled:opacity-50">
                  {sending ? '发送中...' : '推送到微信'}
                </button>
              </div>
            </div>
            {result && (
              <div className={`mt-3 p-2 rounded ${result.status === 'ok' ? 'bg-green-400/20' : 'bg-red-400/20'}`}>
                <span className={result.status === 'ok' ? 'text-green-400' : 'text-red-400'}>
                  {result.status === 'ok' ? '✓ 推送成功' : `✗ ${result.message}`}
                </span>
              </div>
            )}
          </div>

          {/* 持仓信息（仅持仓股票显示） */}
          <PortfolioInfo stock={stock} />

          {/* 核心指标 */}
          <div className="grid grid-cols-4 gap-4">
            <div className="card text-center">
              <p className="text-2xl font-bold">¥{fmt(data.price)}</p>
              <p className="text-xs text-gray-400">当前价格</p>
            </div>
            <div className="card text-center">
              <p className={`text-2xl font-bold ${getScoreColor(totalScore)}`}>{fmt(totalScore)}</p>
              <p className="text-xs text-gray-400">综合评分</p>
            </div>
            <div className="card text-center">
              <p className="text-2xl font-bold text-green-400">{fmt(data.roe)}%</p>
              <p className="text-xs text-gray-400">ROE</p>
            </div>
            <div className="card text-center">
              <p className="text-2xl font-bold text-blue-400">{fmt(data.gross_margin)}%</p>
              <p className="text-xs text-gray-400">毛利率</p>
            </div>
          </div>

          {/* 买卖策略建议（个性化） */}
          <div className="card">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <span className="text-xl">📋</span> 价值投资策略
            </h3>
            <div className="space-y-2">
              {strategyItems.map((item, i) => (
                <p key={i} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className={actionColor}>•</span>{item}
                </p>
              ))}
            </div>
          </div>

          {/* 因子评分 */}
          {Object.keys(factorScores).length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <span className="text-xl">📊</span> 因子评分详情
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(factorScores).map(([key, val]) => {
                  const maxScore = val > 15 ? 25 : 20
                  const pct = Math.min((val / maxScore) * 100, 100)
                  const barColor = val >= maxScore * 0.7 ? 'bg-green-400' : val >= maxScore * 0.4 ? 'bg-yellow-400' : 'bg-red-400'
                  const textColor = val >= maxScore * 0.7 ? 'text-green-400' : val >= maxScore * 0.4 ? 'text-yellow-400' : 'text-red-400'
                  return (
                    <div key={key} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">{FACTOR_LABELS[key] || key}</span>
                        <span className={textColor}>{fmt(val)}分</span>
                      </div>
                      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${barColor} transition-all`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* 财务数据 */}
          <div className="card">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <span className="text-xl">💰</span> 财务数据
            </h3>
            <div className="grid grid-cols-4 gap-4 text-center">
              <div><p className="text-xl font-bold text-purple-400">{fmt(data.revenue_growth)}%</p><p className="text-xs text-gray-500">营收增速</p></div>
              <div><p className="text-xl font-bold text-orange-400">{fmt(data.profit_growth)}%</p><p className="text-xs text-gray-500">净利润增速</p></div>
              <div><p className="text-xl font-bold text-yellow-400">{fmt(data.debt_ratio)}%</p><p className="text-xs text-gray-500">资产负债率</p></div>
              <div><p className="text-xl font-bold text-cyan-400">¥{fmt(data.eps)}</p><p className="text-xs text-gray-500">每股收益</p></div>
            </div>
            {(data.report_type || data.report_date) && (
              <div className="mt-4 pt-4 border-t border-gray-700 text-center text-xs text-gray-500">
                {data.report_type} · {data.report_date} · 东方财富实时数据
              </div>
            )}
          </div>

          {/* 核心逻辑 */}
          {signal.reasons && signal.reasons.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <span className="text-xl">🧠</span> 核心投资逻辑
              </h3>
              <div className="space-y-2">
                {signal.reasons.map((r, i) => (
                  <p key={i} className="text-sm text-gray-300">• {r}</p>
                ))}
              </div>
            </div>
          )}

          {/* 价值投资检查清单 */}
          

          <ValueChecklist checklist={signal.checklist} />

          {/* 技术分析切换按钮 */}
          <div className="flex gap-2 justify-center border-t border-gray-700 pt-4">
            <button
              onClick={() => setShowTechnical(false)}
              className={`px-4 py-2 rounded-lg text-sm ${!showTechnical ? "bg-primary/20 text-primary border border-primary/50" : "bg-dark-100 text-gray-400 border border-gray-700"}`}
            >
              📋 基本面分析
            </button>
            <button
              onClick={() => setShowTechnical(true)}
              className={`px-4 py-2 rounded-lg text-sm ${showTechnical ? "bg-primary/20 text-primary border border-primary/50" : "bg-dark-100 text-gray-400 border border-gray-700"}`}
            >
              📈 技术分析与回测
            </button>
          </div>

          {/* 技术分析内容 */}
          {showTechnical && (
            <TechnicalPanel code={stock.code} />
          )}

        </div>
      </div>
    </div>
  )
}



export default StockDetailModal
