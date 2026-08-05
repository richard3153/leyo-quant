import React, { useState, useEffect } from 'react';
import { API_BASE } from '../utils/api';
import { CheckCircle2, Database, AlertTriangle } from 'lucide-react';

/**
 * 数据来源徽标
 * 调用 /api/provider-status 显示当前数据层状态：
 *   - provider: tdx（通达信MCP）/ sina（新浪兜底）/ ecast（东方财富兜底）
 *   - fallback_enabled: 是否开启自动降级
 *
 * 巴菲特视角：知道自己看的数据从哪来，和知道数据本身一样重要。
 */
export default function DataProviderBadge() {
  const [status, setStatus] = useState(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/provider-status`);
        if (!res.ok) throw new Error('bad status');
        const data = await res.json();
        if (alive) {
          setStatus(data);
          setErr(false);
        }
      } catch (e) {
        if (alive) setErr(true);
      }
    };
    load();
    const timer = setInterval(load, 60000); // 每分钟刷新一次状态
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  if (err || !status) {
    return (
      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-700/40 text-gray-400 text-xs">
        <AlertTriangle className="w-3.5 h-3.5" />
        数据源未知
      </span>
    );
  }

  const provider = status.provider || 'unknown';
  const labelMap = {
    tdx: '通达信 MCP',
    fallback: '新浪兜底',
    none: '无数据源',
    unknown: '未知',
  };
  const colorMap = {
    tdx: 'bg-green-400/10 text-green-400 border-green-400/30',
    fallback: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/30',
    none: 'bg-red-400/10 text-red-400 border-red-400/30',
    unknown: 'bg-gray-700/40 text-gray-400 border-gray-600',
  };
  const cls = colorMap[provider] || colorMap.unknown;

  return (
    <span
      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs ${cls}`}
      title={
        `数据来源：${labelMap[provider] || provider}\n` +
        `降级兜底：${status.fallback_enabled ? '已开启' : '未开启'}\n` +
        `mcporter：${status.mcporter_available ? '可用' : '不可用'}`
      }
    >
      <CheckCircle2 className="w-3.5 h-3.5" />
      数据：{labelMap[provider] || provider}
    </span>
  );
}
