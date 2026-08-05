import React, { useState } from 'react';
import { API_BASE } from '../utils/api';
import { Search, Newspaper, FileBarChart, Megaphone, ExternalLink, Loader2 } from 'lucide-react';

/**
 * 资讯中心：公司公告 / 券商研报 / 财经新闻
 * 调用 GET /api/notices | /api/reports | /api/news
 */
const NEWS_TABS = [
  { id: 'notices', label: '公司公告', icon: Megaphone, api: 'notices' },
  { id: 'reports', label: '券商研报', icon: FileBarChart, api: 'reports' },
  { id: 'news', label: '财经新闻', icon: Newspaper, api: 'news' },
];

export default function NewsPage() {
  const [tab, setTab] = useState('notices');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState('');
  const [sourceNote, setSourceNote] = useState('');

  const current = NEWS_TABS.find((t) => t.id === tab);

  const load = async (t, q) => {
    const tabDef = NEWS_TABS.find((x) => x.id === (t ?? tab));
    const qv = (q ?? query).trim();
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (qv) params.set('name', qv);
      params.set('top_k', '15');
      const res = await fetch(`${API_BASE}/api/${tabDef.api}?${params.toString()}`);
      const json = await res.json();
      const ok = json.status === 'success' || json.source === 'tdx' || json.source === 'eastmoney';
      if (ok) {
        setItems(json.items || []);
        setTotal(json.total || 0);
        // 兜底数据源提示（东财兜底时标注）
        setSourceNote(json.source === 'eastmoney' ? '数据来源：东方财富（通达信 MCP 额度已用尽，自动降级）' : '');
      } else {
        setItems([]);
        setError(json.message || json.error || '暂无数据');
      }
    } catch (e) {
      setError('网络错误：' + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <Newspaper className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-bold">资讯中心</h2>
        </div>
        <p className="text-sm text-gray-400 mb-4">公告、研报、新闻，第一时间掌握公司动态。</p>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && load(tab, query)}
              placeholder="按公司名称搜索，如 茅台 / 腾讯（留空看全市场）"
              className="w-full pl-10 pr-4 py-2 bg-dark-200 rounded-lg border border-gray-600 focus:border-primary focus:outline-none"
            />
          </div>
          <button
            onClick={() => load(tab, query)}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 bg-primary text-dark-300 rounded-lg font-medium hover:bg-primary/80 transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            搜索
          </button>
        </div>
        <div className="flex gap-2 mt-3">
          {NEWS_TABS.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => { setTab(t.id); load(t.id, query); }}
                className={`flex items-center gap-2 px-4 py-1.5 text-sm rounded-lg border transition ${
                  tab === t.id ? 'bg-primary/20 text-primary border-primary/50' : 'bg-dark-200 text-gray-400 border-gray-600 hover:text-gray-200'
                }`}
              >
                <Icon className="w-4 h-4" />{t.label}
              </button>
            );
          })}
        </div>
      </div>

      {error && (
        <div className="card border-yellow-400/30 bg-yellow-400/10 text-yellow-300 text-sm p-4">{error}</div>
      )}

      {sourceNote && (
        <div className="card border-blue-400/30 bg-blue-400/10 text-blue-300 text-sm p-3">{sourceNote}</div>
      )}

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold flex items-center gap-2">
            <current.icon className="w-4 h-4 text-primary" />{current.label}
          </h3>
          <span className="text-sm text-gray-400">共 <span className="text-white font-bold">{total}</span> 条</span>
        </div>
        {loading ? (
          <div className="flex items-center justify-center py-12 text-gray-400">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <p className="text-gray-400 text-sm py-8 text-center">暂无{current.label}</p>
        ) : (
          <div className="space-y-3">
            {items.map((it, i) => (
              <a
                key={i}
                href={it.url || '#'}
                target={it.url ? '_blank' : undefined}
                rel="noreferrer"
                className="block p-4 rounded-lg bg-dark-200 hover:bg-dark-100 transition border border-transparent hover:border-gray-600"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="font-medium text-white flex-1">{it.title}</p>
                  {it.url && <ExternalLink className="w-4 h-4 text-gray-500 shrink-0 mt-1" />}
                </div>
                <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                  {it.source && <span>{it.source}</span>}
                  {it.time && <span>{it.time}</span>}
                </div>
                {it.summary && (
                  <p className="text-sm text-gray-400 mt-2 line-clamp-2">{it.summary}</p>
                )}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
