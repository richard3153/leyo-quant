import React, { useState, useEffect } from 'react'
import { API_BASE } from '../utils/api';
import { TrendingUp, TrendingDown, Minus, X, Send, CheckCircle, XCircle, Bell } from 'lucide-react'

const fmt = (v, suffix = '') => {
  if (v === null || v === undefined || v === '') return '--'
  const n = typeof v === 'number' ? v : parseFloat(v)
  if (isNaN(n)) return '--'
  return n.toFixed(2) + suffix
}

const getRatingColor = (score) => {
  if (score >= 85) return 'text-green-400'
  if (score >= 70) return 'text-blue-400'
  if (score >= 50) return 'text-yellow-400'
  return 'text-red-400'
}

const getRatingBg = (score) => {
  if (score >= 85) return 'bg-green-400/10 border-green-400/30'
  if (score >= 70) return 'bg-blue-400/10 border-blue-400/30'
  if (score >= 50) return 'bg-yellow-400/10 border-yellow-400/30'
  return 'bg-red-400/10 border-red-400/30'
}

const getSignalIcon = (signal) => {
  if (signal === 'BUY') return <TrendingUp className="w-5 h-5 text-green-400" />
  if (signal === 'SELL') return <TrendingDown className="w-5 h-5 text-red-400" />
  return <Minus className="w-5 h-5 text-yellow-400" />
}

// 股票详情弹窗
function StockDetailModal({ stock, onClose, onSendWeChat }) {
  if (!stock) return null
  
  const signal = stock.signal || {}
  const score = stock.score || {}
  const data = stock.data || {}
  const [sending, setSending] = useState(false)
  const [result, setResult] = useState(null)
  
  const sendToWeChat = async () => {
    setSending(true)
    setResult(null)
    try {
      const res = await fetch(`${API_BASE}/api/wechat/signal/${stock.code}`, { method: 'POST' })
      const resData = await res.json()
      setResult(resData)
      if (onSendWeChat) onSendWeChat(resData)
    } catch (e) {
      setResult({ status: 'error', message: e.message })
    }
    setSending(false)
  }
  
  // 买卖策略
  const getStrategy = () => {
    const signalType = signal.signal
    const scoreVal = score.total_score || 0
    
    if (signalType === 'BUY') {
      return {
        action: '买入',
        color: 'text-green-400',
        bg: 'bg-green-400/10 border-green-400/30',
        strategy: [
          `建议分批建仓，首次买入仓位控制在总资金的20%-30%`,
          `若股价回调至支撑位（如20日均线），可加仓至50%`,
          `设置止损位：亏损超过10%果断离场`,
          `目标价位：当前价格的130%-150%，达到后分批止盈`,
          `评分 ${scoreVal}分，${score.rating || ''}，财务数据良好，适合中长期持有`
        ]
      }
    } else if (signalType === 'SELL') {
      return {
        action: '卖出',
        color: 'text-red-400',
        bg: 'bg-red-400/10 border-red-400/30',
        strategy: [
          `建议分批减仓，优先卖出盈利较多的仓位`,
          `若股价反弹至压力位（如60日均线），继续减仓`,
          `若已持仓亏损，建议止损位设在成本价的-8%`,
          `避免在低位割肉，可保留20%仓位等待反弹`,
          `评分 ${scoreVal}分，${score.rating || ''}，注意风险控制`
        ]
      }
    } else {
      return {
        action: '持有',
        color: 'text-yellow-400',
        bg: 'bg-yellow-400/10 border-yellow-400/30',
        strategy: [
          `维持现有仓位，不新增也不减仓`,
          `密切关注季报数据，如ROE持续下降需警惕`,
          `若股价突破重要压力位（如年线），可考虑加仓`,
          `若股价跌破关键支撑位（如30日均线），考虑减仓`,
          `评分 ${scoreVal}分，${score.rating || ''}，建议观望等待更明确信号`
        ]
      }
    }
  }
  
  const strategy = getStrategy()
  
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-dark-300 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="sticky top-0 bg-dark-300 border-b border-gray-700 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getSignalIcon(signal.signal)}
            <div>
              <h2 className="text-xl font-bold">{stock.name}</h2>
              <p className="text-sm text-gray-400">{stock.code} · {stock.industry}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className={`text-3xl font-bold ${getRatingColor(score.total_score || 0)}`}>
                {fmt(score.total_score)}
              </div>
              <div className="text-sm text-gray-400">{score.rating || '暂无评级'}</div>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-dark-100 rounded-lg transition">
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6 space-y-6">
          {/* 信号概览 */}
          <div className={`p-4 rounded-lg border ${strategy.bg}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {getSignalIcon(signal.signal)}
                <div>
                  <p className={`text-2xl font-bold ${strategy.color}`}>{signal.signal} - {strategy.action}</p>
                  <p className="text-sm text-gray-400">置信度: {signal.confidence || '--'}%</p>
                </div>
              </div>
              <button
                onClick={sendToWeChat}
                disabled={sending}
                className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
                {sending ? '发送中...' : '推送到微信'}
              </button>
            </div>
            {result && (
              <div className={`mt-3 p-2 rounded ${result.status === 'ok' ? 'bg-green-400/20' : 'bg-red-400/20'}`}>
                <span className={result.status === 'ok' ? 'text-green-400' : 'text-red-400'}>
                  {result.status === 'ok' ? '✓ 推送成功' : `✗ ${result.message}`}
                </span>
              </div>
            )}
          </div>
          
          {/* 关键指标 */}
          <div className="grid grid-cols-4 gap-4">
            <div className="card text-center">
              <p className="text-2xl font-bold">¥{fmt(data.price)}</p>
              <p className="text-xs text-gray-400">当前价格</p>
            </div>
            <div className="card text-center">
              <p className={`text-2xl font-bold ${getRatingColor(score.total_score || 0)}`}>{fmt(score.total_score)}</p>
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
          
          {/* 买卖策略 */}
          <div className="card">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Bell className="w-5 h-5 text-primary" />
              买卖策略建议
            </h3>
            <div className="space-y-2">
              {strategy.strategy.map((item, i) => (
                <p key={i} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className={strategy.color}>•</span>
                  {item}
                </p>
              ))}
            </div>
          </div>
          
          {/* 因子评分 */}
          <div className="card">
            <h3 className="text-lg font-bold mb-4">因子评分（东方财富实时数据）</h3>
            <div className="grid grid-cols-2 gap-4">
              {score.scores && Object.entries(score.scores).map(([key, value]) => {
                const labels = {
                  roe: 'ROE 净资产收益率',
                  revenue_growth: '营收增速',
                  profit_growth: '净利润增速',
                  gross_margin: '毛利率',
                  debt_ratio: '资产负债率',
                  eps: '每股收益',
                  safety_margin: '安全边际',
                  profit_quality: '盈利质量',
                  moat: '护城河',
                  financial_health: '财务健康',
                  growth: '成长性',
                  capital_allocation: '资本配置'
                }
                return (
                  <div key={key} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">{labels[key] || key}</span>
                      <span className={value >= 15 ? 'text-green-400' : value >= 8 ? 'text-yellow-400' : 'text-red-400'}>
                        {fmt(value)}分
                      </span>
                    </div>
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${value >= 15 ? 'bg-green-400' : value >= 8 ? 'bg-yellow-400' : 'bg-red-400'}`}
                        style={{ width: `${Math.min(value * 4, 100)}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
          
          {/* 财务数据 */}
          <div className="card">
            <h3 className="text-lg font-bold mb-4">财务数据详情</h3>
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-xl font-bold text-purple-400">{fmt(data.revenue_growth)}%</p>
                <p className="text-xs text-gray-500">营收增速</p>
              </div>
              <div>
                <p className="text-xl font-bold text-orange-400">{fmt(data.profit_growth)}%</p>
                <p className="text-xs text-gray-500">净利润增速</p>
              </div>
              <div>
                <p className="text-xl font-bold text-yellow-400">{fmt(data.debt_ratio)}%</p>
                <p className="text-xs text-gray-500">资产负债率</p>
              </div>
              <div>
                <p className="text-xl font-bold text-cyan-400">¥{fmt(data.eps)}</p>
                <p className="text-xs text-gray-500">每股收益</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-700 text-center text-xs text-gray-500">
              {data.report_type || '最新财报'} · {data.report_date || ''} · 数据来源：东方财富
            </div>
          </div>
          
          {/* 核心逻辑 */}
          {score.reasons && score.reasons.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold mb-4">核心逻辑</h3>
              <div className="space-y-2">
                {score.reasons.map((reason, i) => (
                  <p key={i} className="text-sm text-gray-300">• {reason}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// 股票缩略图卡片
function StockMiniCard({ stock, onClick }) {
  const signal = stock.signal || {}
  const score = stock.score || {}
  const data = stock.data || {}
  
  return (
    <div
      onClick={onClick}
      className={`p-3 rounded-lg cursor-pointer hover:scale-[1.02] transition border ${getRatingBg(score.total_score || 0)}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div>
          <p className="font-medium text-sm">{stock.name}</p>
          <p className="text-xs text-gray-500">{stock.code}</p>
        </div>
        {getSignalIcon(signal.signal)}
      </div>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-lg font-bold">¥{fmt(data.price)}</p>
          <p className={`text-sm font-bold ${getRatingColor(score.total_score || 0)}`}>
            {fmt(score.total_score)}分
          </p>
        </div>
        <div className="text-right">
          <p className={`text-sm font-bold ${
            signal.signal === 'BUY' ? 'text-green-400' :
            signal.signal === 'SELL' ? 'text-red-400' : 'text-yellow-400'
          }`}>
            {signal.signal || '--'}
          </p>
          <p className="text-xs text-gray-500">{stock.industry}</p>
        </div>
      </div>
    </div>
  )
}

// 信号列表列
function SignalColumn({ title, signal, stocks, onStockClick, color, bgColor, icon: Icon }) {
  return (
    <div className="space-y-3">
      <div className={`flex items-center gap-2 p-2 rounded-lg ${bgColor}`}>
        <Icon className={`w-5 h-5 ${color}`} />
        <h3 className={`font-bold ${color}`}>{title}</h3>
        <span className="text-xs text-gray-400">({stocks.length}只)</span>
      </div>
      <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-2">
        {stocks.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            暂无
          </div>
        ) : (
          stocks.map(stock => (
            <StockMiniCard
              key={stock.code}
              stock={stock}
              onClick={() => onStockClick(stock)}
            />
          ))
        )}
      </div>
    </div>
  )
}

export default function SignalPanel({ stocks, selectedCode, onSelect }) {
  const [detailStock, setDetailStock] = useState(null)
  
  // 按信号分类
  const buyStocks = stocks.filter(s => s.signal?.signal === 'BUY').sort((a, b) => (b.score?.total_score || 0) - (a.score?.total_score || 0))
  const sellStocks = stocks.filter(s => s.signal?.signal === 'SELL').sort((a, b) => (b.score?.total_score || 0) - (a.score?.total_score || 0))
  const holdStocks = stocks.filter(s => s.signal?.signal === 'HOLD' || !s.signal?.signal).sort((a, b) => (b.score?.total_score || 0) - (a.score?.total_score || 0))
  
  if (stocks.length === 0) {
    return (
      <div className="card text-center py-12 text-gray-400">
        <Bell className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>暂无信号数据，请先扫描股票池</p>
      </div>
    )
  }
  
  return (
    <>
      <div className="grid grid-cols-3 gap-6">
        <SignalColumn
          title="买入信号 BUY"
          signal="BUY"
          stocks={buyStocks}
          onStockClick={setDetailStock}
          color="text-green-400"
          bgColor="bg-green-400/10"
          icon={TrendingUp}
        />
        <SignalColumn
          title="卖出信号 SELL"
          signal="SELL"
          stocks={sellStocks}
          onStockClick={setDetailStock}
          color="text-red-400"
          bgColor="bg-red-400/10"
          icon={TrendingDown}
        />
        <SignalColumn
          title="持有信号 HOLD"
          signal="HOLD"
          stocks={holdStocks}
          onStockClick={setDetailStock}
          color="text-yellow-400"
          bgColor="bg-yellow-400/10"
          icon={Minus}
        />
      </div>
      
      {/* 股票详情弹窗 */}
      {detailStock && (
        <StockDetailModal
          stock={detailStock}
          onClose={() => setDetailStock(null)}
        />
      )}
    </>
  )
}
