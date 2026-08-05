import React, { useState } from 'react';
import { API_BASE } from '../utils/api';
import { Search, FileText, Loader2, Table } from 'lucide-react';

/**
 * F10 财务报表页面
 * 调用 GET /api/financial-statement/{code}?stmt=income|balance|cashflow
 * 展示利润表 / 资产负债表 / 现金流量表（中文列名，多年期）
 */
const STMT_TABS = [
  { id: 'income', label: '利润表' },
  { id: 'balance', label: '资产负债表' },
  { id: 'cashflow', label: '现金流量表' },
];

export default function F10Page() {
  const [code, setCode] = useState('600519');
  const [stmt, setStmt] = useState('income');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const load = async (c, s) => {
    const cv = (c ?? code).trim();
    const sv = (s ?? stmt);
    if (!cv) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/financial-statement/${encodeURIComponent(cv)}?stmt=${sv}`);
      const json = await res.json();
      if (json.status === 'success' && json.rows?.length) {
        setData(json);
      } else {
        setData(null);
        setError(json.error || '暂无数据（该股票可能无此报表）');
      }
    } catch (e) {
      setError('网络错误：' + e.message);
    } finally {
      setLoading(false);
    }
  };

  // 列名特殊映射（美化显示）
  const prettyCol = (col) => {
    const map = {
      '截止日期': '报告期', 'TOTAL_OPERATE_INCOME': '营业总收入', 'PARENT_NETPROFIT': '归母净利润',
    };
    return map[col] || col;
  };

  // 数值格式化：大数字转亿
  const fmtVal = (v) => {
    if (v === null || v === undefined || v === '') return '--';
    const n = typeof v === 'number' ? v : parseFloat(String(v).replace(/,/g, ''));
    if (isNaN(n)) return String(v);
    if (Math.abs(n) >= 1e8) return (n / 1e8).toFixed(2) + '亿';
    if (Math.abs(n) >= 1e4) return (n / 1e4).toFixed(2) + '万';
    return n.toFixed(2);
  };

  // 取前若干列（避免太宽），优先 报告期 + 核心科目
  const displayCols = data?.columns || [];
  const CORE = ['截止日期', '营业总收入', '营业收入', '净利润', '归母净利润', '基本每股收益',
    '总资产', '净资产', '负债', '经营活动现金流', '资产负债率'];
  const cols = displayCols.length > 8
    ? displayCols.filter((c) => CORE.includes(c)).slice(0, 8).concat(displayCols.slice(0, 0))
    : displayCols;

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <FileText className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-bold">F10 财务报表</h2>
        </div>
        <p className="text-sm text-gray-400 mb-4">查看上市公司原始账本：利润表 / 资产负债表 / 现金流量表。</p>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && load()}
              placeholder="股票代码，如 600519"
              className="w-full pl-10 pr-4 py-2 bg-dark-200 rounded-lg border border-gray-600 focus:border-primary focus:outline-none"
            />
          </div>
          <button
            onClick={() => load()}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 bg-primary text-dark-300 rounded-lg font-medium hover:bg-primary/80 transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Table className="w-4 h-4" />}
            查询
          </button>
        </div>
        <div className="flex gap-2 mt-3">
          {STMT_TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => { setStmt(t.id); if (data || code) load(code, t.id); }}
              className={`px-4 py-1.5 text-sm rounded-lg border transition ${
                stmt === t.id ? 'bg-primary/20 text-primary border-primary/50' : 'bg-dark-200 text-gray-400 border-gray-600 hover:text-gray-200'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="card border-yellow-400/30 bg-yellow-400/10 text-yellow-300 text-sm p-4">{error}</div>
      )}

      {data && (
        <div className="card overflow-x-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold">{data.code} · {STMT_TABS.find((t) => t.id === data.stmt_type)?.label}</h3>
            <span className="text-xs text-gray-400">共 {data.count} 期 · 来源 {data.source}</span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-600">
                {cols.map((c) => (
                  <th key={c} className="text-left py-2 px-3 font-medium whitespace-nowrap">{prettyCol(c)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.slice(0, 12).map((row, i) => (
                <tr key={i} className="border-b border-gray-700/50 hover:bg-dark-100">
                  {cols.map((c) => (
                    <td key={c} className="py-2 px-3 whitespace-nowrap">{fmtVal(row[c])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {data.count > 12 && (
            <p className="text-xs text-gray-500 mt-2">仅显示最近 12 期，完整 {data.count} 期见原始数据</p>
          )}
        </div>
      )}
    </div>
  );
}
