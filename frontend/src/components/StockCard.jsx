import React from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

// 格式化数字：保留2位小数
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
  if (signal === 'BUY') return <TrendingUp className="w-4 h-4 text-green-400" />
  if (signal === 'SELL') return <TrendingDown className="w-4 h-4 text-red-400" />
  return <Minus className="w-4 h-4 text-yellow-400" />
}

export default function StockCard({ stock, onClick }) {
  const score = stock.score?.total_score || 0
  const signal = stock.signal || {}
  const data = stock.data || {}
  const rating = stock.score?.rating || '未评分'

  const factors = stock.score?.scores || {}
  const factorKeys = Object.keys(factors)

  return (
    <div
      className={`card cursor-pointer hover:scale-[1.02] transition-transform ${getRatingBg(score)}`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            {getSignalIcon(signal.signal)}
            <span className="text-lg font-bold">{stock.name}</span>
          </div>
          <p className="text-gray-500 text-sm">{stock.code} · {stock.industry}</p>
        </div>
        <div className="text-right">
          <p className={`text-2xl font-bold ${getRatingColor(score)}`}>{score}</p>
          <p className="text-xs text-gray-500">{rating}</p>
        </div>
      </div>

      {/* Score Bar */}
      <div className="score-bar mb-4">
        <div
          className={`score-bar-fill ${
            score >= 85 ? 'bg-green-400' :
            score >= 70 ? 'bg-blue-400' :
            score >= 50 ? 'bg-yellow-400' : 'bg-red-400'
          }`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">价格</span>
          <span className="font-medium">¥{fmt(data.price)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">ROE</span>
          <span className="font-medium text-green-400">{fmt(data.roe)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">毛利率</span>
          <span className="font-medium text-blue-400">{fmt(data.gross_margin)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">资产负债率</span>
          <span className="font-medium text-yellow-400">{fmt(data.debt_ratio)}%</span>
        </div>
      </div>

      {/* Factor Scores Mini Chart */}
      {factorKeys.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-800">
          <div className="grid grid-cols-4 gap-1">
            {factorKeys.slice(0, 4).map(key => (
              <div key={key} className="text-center">
                <div className={`text-xs font-bold ${getRatingColor(factors[key])}`}>
                  {fmt(factors[key])}
                </div>
                <div className="text-[10px] text-gray-500 truncate">
                  {key.replace('_', ' ').slice(0, 6)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reasons */}
      {signal.reasons?.length > 0 && (
        <div className="mt-3 space-y-1">
          {signal.reasons.slice(0, 2).map((reason, i) => (
            <p key={i} className="text-xs text-gray-400">• {reason}</p>
          ))}
        </div>
      )}
    </div>
  )
}
