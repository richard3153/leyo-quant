import React, { useState } from 'react';
import { API_BASE } from '../utils/api';
import { Search, TrendingUp, TrendingDown, Loader2, Sparkles } from 'lucide-react';

/**
 * 自然语言选股页面
 * 调用 GET /api/screener?message=xxx
 * 巴菲特视角：好公司 + 好价格，让机器替你翻遍全市场，你只负责做判断。
 */
export default function ScreenerPage() {
  const [query, setQuery] = useState('今天涨停');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const EXAMPLES = [
    '今天涨停', '连续涨停', '低价股', '高ROE', '业绩增长', '破净股',
  ];

  const run = async (msg) => {
    const q = (msg ?? query).trim();
    if (!q) return;
    setLoading(true);
    setError('');
    setData(null);
    try {
      const res = await fetch(`${API_BASE}/api/screener?message=${encodeURIComponent(q)}&page_size=20`);
      const json = await res.json();
      const ok = json.status === 'success' || json.source === 'tdx' || json.source === 'eastmoney';
      if (ok && json.rows?.length) {
        setData(json);
        setError('');
      } else if (ok) {
        setData(json);
        setError('');
      } else {
        setData(null);
        setError(json.message || '查询失败');
      }
    } catch (e) {
      setError('网络错误：' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const stocks = data?.rows || [];

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-bold">自然语言选股</h2>
        </div>
        <p className="text-sm text-gray-400 mb-4">用大白话描述你想要的股票，通达信全市场扫描。</p>
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && run()}
            placeholder="例如：今天涨停 / 高ROE低估值 / 连续涨停"
            className="flex-1 px-4 py-2 bg-dark-200 rounded-lg border border-gray-600 focus:border-primary focus:outline-none"
          />
          <button
            onClick={() => run()}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 bg-primary text-dark-300 rounded-lg font-medium hover:bg-primary/80 transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            选股
          </button>
        </div>
        <div className="flex gap-2 mt-3 flex-wrap">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => { setQuery(ex); run(ex); }}
              className="px-3 py-1 text-xs bg-dark-200 border border-gray-600 rounded-full text-gray-300 hover:border-primary hover:text-primary transition"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="card border-red-400/30 bg-red-400/10 text-red-300 text-sm p-4">
          {error}
        </div>
      )}

      {data && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold">选股结果</h3>
            <span className="text-sm text-gray-400">共 <span className="text-white font-bold">{data.total}</span> 只</span>
          </div>
          {stocks.length === 0 ? (
            <p className="text-gray-400 text-sm py-8 text-center">没有匹配的股票</p>
          ) : (
            <div className="space-y-2">
              {stocks.map((s, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-dark-200 hover:bg-dark-100 transition">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white">{s.sec_name || s.name}</span>
                      <span className="text-xs text-gray-400">{s.sec_code || s.code}</span>
                      {(s.连板数 || s.连续涨停天数) && (
                        <span className="px-1.5 py-0.5 text-[10px] bg-red-400/20 text-red-300 rounded">{s.连板数 || s.连续涨停天数}连板</span>
                      )}
                    </div>
                    {s.涨停原因 && (
                      <p className="text-xs text-gray-400 mt-1 truncate">{s.涨停原因}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-white">{s.now_price ?? s.price}</p>
                    <p className={`text-sm font-bold ${(s.chg ?? 0) >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {(s.chg ?? 0) >= 0 ? '+' : ''}{s.chg ?? '--'}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
