#!/usr/bin/env python3
"""
通达信 MCP 数据提供者 (tongdaxin-mcp provider)

作为 leyo-quant 数据层的「统一入口」：
- 优先调用通达信 MCP (tdx-finance_qclaw) 获取行情与基本面数据
- mcporter 不可用时自动降级到原有新浪/东方财富实现
- 与 realtime_quote.py / financial_data.py 保持相同函数签名，
  main.py 只需切换 import 即可完成数据层替换

依赖：mcporter (已配置 tdx-finance_qclaw server)
      脚本通过 mcporter call 访问 tdx-finance_qclaw.<tool>

环境变量：
  LEYO_USE_TDX   = "0" 可强制关闭通达信、回退到旧实现
  LEYO_TDX_FALLBACK = "0" 可强制关闭降级（仅用通达信）
"""

import subprocess
import json
import re
import os
import time
from datetime import datetime


# ── 配置 ──────────────────────────────────────────────
_USE_TDX = os.environ.get("LEYO_USE_TDX", "1") != "0"
_USE_FALLBACK = os.environ.get("LEYO_TDX_FALLBACK", "1") != "0"
_MCPORTER_BIN = "mcporter"
# 单次 mcporter 调用超时(秒)
_CALL_TIMEOUT = 30
# 批量选股/财务并发已由调用方控制，这里控制单只重试
_MAX_RETRY = 1

# 懒加载旧实现，仅在降级时使用
_fallback_modules = {}


def _load_fallback(name):
    """懒加载 original 模块 (realtime_quote / financial_data)"""
    if name not in _fallback_modules:
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), name + ".py")
        spec = importlib.util.spec_from_file_location("_fb_" + name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _fallback_modules[name] = mod
    return _fallback_modules[name]


def _mcporter_available() -> bool:
    """快速探测 mcporter 是否可用"""
    if not _USE_TDX:
        return False
    try:
        # 仅探测二进制存在，不触发真实网络
        subprocess.run([_MCPORTER_BIN, "--version"],
                       capture_output=True, timeout=8)
        return True
    except Exception:
        return False


# ── mcporter 调用封装 ─────────────────────────────────
def _call_tdx(tool: str, args: dict) -> any:
    """调用 tdx-finance_qclaw.<tool>。

    注意：mcporter 的 `--output json` 返回的是 JS 对象字面量包裹
    (content:[{type:'text', text:'...'}])，并非纯 JSON，无法直接
    json.loads。因此改用**默认文本输出**，再按工具类型提取结构化数据：
      - tdx_quotes / tdx_kline：文本含 `详细信息:\n{...json...}` 块
      - tdx_indicator_select / tdx_lookup_stock / tdx_screener / wenda_*：
        文本首行即 JSON 数组
    失败抛出异常，由上层决定是否降级。
    """
    cmd = [_MCPORTER_BIN, "call",
           f"tdx-finance_qclaw.{tool}",
           "--args", json.dumps(args, ensure_ascii=False)]
    # 注意：mcporter 对 stdout 管道有 ~64KB 截断限制（TTY/文件则完整）。
    # 为避免大响应（如 K线 400 条≈176KB）被截断，将输出重定向到临时文件再读取。
    import tempfile
    tmpf = tempfile.NamedTemporaryFile(
        prefix="tdx_call_", suffix=".txt", delete=False, mode="w",
        encoding="utf-8")
    tmp_path = tmpf.name
    tmpf.close()
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            proc = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE,
                                  text=True, encoding="utf-8",
                                  errors="replace", timeout=_CALL_TIMEOUT)
        if proc.returncode != 0:
            err = (proc.stderr or "").strip()[:200]
            raise RuntimeError(f"mcporter {tool} failed: {err}")
        with open(tmp_path, "r", encoding="utf-8", errors="replace") as fh:
            out = fh.read().strip()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    if not out:
        raise RuntimeError(f"mcporter {tool} empty output")
    return _extract_structured(out, tool)


def _extract_structured(out: str, tool: str) -> any:
    """从 mcporter 默认文本输出中解析出结构化数据。"""
    # 1) tdx_quotes / tdx_kline 含标记行后接 JSON
    #    tdx_quotes 标记为 `详细信息:`，tdx_kline 标记为 `详细K线数据:`
    if tool in ("tdx_quotes", "tdx_kline"):
        idx = -1
        for marker in ("详细信息", "详细K线数据"):
            j = out.find(marker)
            if j != -1:
                idx = j
                break
        if idx != -1:
            json_start = out.find("{", idx)
            if json_start != -1:
                return _extract_json_from(out, json_start)
        # 没有 详细信息 块时，退化为整段找 JSON
        js = _find_first_json(out)
        if js is not None:
            return js
        raise RuntimeError(f"no JSON block in {tool} output")
    # 2) tdx_screener 返回数组（首行即 [...]），优先匹配数组
    if tool == "tdx_screener":
        js = _find_first_json(out, prefer="array")
        if js is None:
            raise RuntimeError(f"no JSON in {tool} output")
        return js
    # 3) 其余工具：首行即 JSON（对象优先，避免内嵌数组误判）
    js = _find_first_json(out)
    if js is None:
        raise RuntimeError(f"no JSON in {tool} output")
    return js


def _find_first_json(text: str, prefer: str = "object"):
    """在文本中找第一个完整 JSON 片段。
    prefer='object'（默认）：优先对象 {...}（主响应多为对象，避免内嵌数组误判）；
    prefer='array'：优先数组 [...]（如 tdx_screener 返回顶层数组）。
    """
    order = (("{", "}"), ("[", "]")) if prefer == "object" \
        else (("[", "]"), ("{", "}"))
    for opener, closer in order:
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == opener:
                    depth += 1
                elif ch == closer:
                    depth -= 1
                    if depth == 0:
                        frag = text[start:i + 1]
                        try:
                            return json.loads(frag)
                        except json.JSONDecodeError:
                            return None
        return None
    return None


def _extract_json_from(text: str, start: int) -> dict:
    """从 start（'{' 位置）向后配对括号提取 JSON 对象。"""
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    frag = text[start:i + 1]
                    return json.loads(frag)
    raise RuntimeError("unterminated JSON in tdx output")


# ── 代码检索 ──────────────────────────────────────────
def lookup_stock(query: str) -> dict:
    """通过名称/别名检索证券代码。
    返回 {"code": "600519", "setcode": "1", "name": "贵州茅台", "market": "A"}"""
    try:
        data = _call_tdx("tdx_lookup_stock", {"query": query})
        if isinstance(data, list) and data:
            item = data[0]
            code = str(item.get("code", ""))
            setcode = str(item.get("setcode", "1"))
            # 通达信 setcode: 1=沪 0=深 31=港股 ... 我们做 A股归一
            if setcode in ("0", "1"):
                return {"code": code, "setcode": setcode,
                        "name": item.get("name", query), "market": "A"}
            # 港股/其他
            return {"code": code, "setcode": setcode,
                    "name": item.get("name", query), "market": "HK"}
    except Exception:
        pass
    # 退化：按 A股默认沪市
    digits = re.sub(r"\D", "", query)
    if digits:
        return {"code": digits, "setcode": "1" if digits.startswith("6") else "0",
                "name": query, "market": "A"}
    return {"code": query, "setcode": "1", "name": query, "market": "A"}


def _setcode_of(code: str) -> str:
    """根据代码推断 setcode：6开头=沪(1)，0/3开头=深(0)，8/4=北交所(2)"""
    if code.startswith("6"):
        return "1"
    if code.startswith(("0", "3")):
        return "0"
    if code.startswith(("8", "4")):
        return "2"
    return "0"


# ── 实时行情 ──────────────────────────────────────────
def get_realtime_price(code: str) -> dict:
    """返回与 realtime_quote.get_realtime_price 相同结构"""
    if _mcporter_available():
        try:
            setcode = _setcode_of(code)
            data = _call_tdx("tdx_quotes",
                             {"code": code, "setcode": setcode})
            return _parse_tdx_quote(data, code, setcode)
        except Exception as e:
            if not _USE_FALLBACK:
                return {"error": str(e), "code": code}
    if _USE_FALLBACK:
        return _load_fallback("realtime_quote").get_realtime_price(code)
    return {"error": "tdx_unavailable", "code": code}


def get_batch_realtime_prices(codes: list) -> dict:
    """批量行情，保持与 realtime_quote 相同返回结构 {code: {...}}"""
    if _mcporter_available():
        try:
            results = {}
            # 逐只请求（通达信未提供批量接口，单只调用稳定）
            for code in codes:
                try:
                    setcode = _setcode_of(code)
                    data = _call_tdx("tdx_quotes",
                                     {"code": code, "setcode": setcode})
                    results[code] = _parse_tdx_quote(data, code, setcode)
                except Exception:
                    results[code] = {"error": "fetch_failed", "code": code}
            return results
        except Exception:
            if not _USE_FALLBACK:
                return {c: {"error": "tdx_unavailable", "code": c} for c in codes}
    if _USE_FALLBACK:
        return _load_fallback("realtime_quote").get_batch_realtime_prices(codes)
    return {c: {"error": "tdx_unavailable", "code": c} for c in codes}


def _parse_tdx_quote(data: dict, code: str, setcode: str) -> dict:
    """把 tdx_quotes 返回结构转成 leyo-quant 内部统一格式"""
    hq = (data.get("HQInfo") or {}) if isinstance(data, dict) else {}
    ext = (data.get("ExtInfo") or {}) if isinstance(data, dict) else {}
    base = (data.get("BaseInfo") or {}) if isinstance(data, dict) else {}
    # 股票名称在 BaseInfo.Name（已验证）
    name = (base.get("Name") or ext.get("Name") or data.get("Name")
            or (hq.get("Name") if isinstance(hq, dict) else None) or "")
    # HQInfo/ExtInfo 字段
    now = float(hq.get("Now", 0) or 0)
    prev_close = float(hq.get("Close", 0) or 0)  # Close 在 tdx 里是昨收
    open_p = float(hq.get("Open", 0) or 0)
    high = float(hq.get("MaxP", 0) or 0)
    low = float(hq.get("MinP", 0) or 0)
    # 成交量单位：通达信 Volume 为手
    volume = int(float(hq.get("Volume", 0) or 0))
    amount = float(hq.get("Amount", 0) or 0)
    change = now - prev_close
    change_pct = (change / prev_close * 100) if prev_close > 0 else 0.0
    return {
        "code": code,
        "name": name,
        "current_price": now,
        "open": open_p,
        "prev_close": prev_close,
        "high": high,
        "low": low,
        "volume": volume,
        "amount": amount,
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "source": "tdx",
    }


# ── 财务 / 基本面数据 ─────────────────────────────────
def get_financial_data(code: str) -> dict:
    """返回与 financial_data.get_financial_data 相同结构（供 score_from_financial 使用）"""
    if _mcporter_available():
        try:
            metrics = _fetch_indicator(code)
            if metrics:
                return _build_financial(metrics, code)
        except Exception as e:
            if not _USE_FALLBACK:
                return {"error": str(e), "code": code}
    if _USE_FALLBACK:
        return _load_fallback("financial_data").get_financial_data(code)
    return {"error": "tdx_unavailable", "code": code}


def get_batch_financial(codes: list) -> dict:
    """批量财务（带速率限制，与 financial_data 行为一致）"""
    results = {}
    for code in codes:
        results[code] = get_financial_data(code)
        time.sleep(0.2)
    return results


# 字段模糊匹配规则（key 子串 -> 内部字段名）
_INDICATOR_MAP = [
    ("净资产收益率ROE", "roe"),
    ("营业收入(同比增长率)", "revenue_growth"),
    ("归属母公司股东的净利润(同比增长率)", "profit_growth"),
    ("销售毛利率", "gross_margin"),
    ("资产负债率", "debt_ratio"),
    ("市盈率", "pe"),
    ("市净率", "pb"),
    ("每股收益", "eps"),
    ("每股净资产", "bps"),
]


def _fetch_indicator(code: str) -> dict:
    """用 tdx_indicator_select 拉取核心指标，返回 {内部字段: 数值}。
    分两段请求，避免长 message 被截断导致字段缺失。"""
    # 财务类（ROE/成长/盈利/偿债）
    msg_a = (f"{code}的ROE、营业收入同比增长率、"
             f"归属母公司净利润同比增长率、销售毛利率、资产负债率")
    # 估值与每股类（PE/PB/EPS/BPS）
    msg_b = f"{code}的市盈率、市净率、每股收益、每股净资产"

    out: dict = {}
    for msg in (msg_a, msg_b):
        try:
            data = _call_tdx("tdx_indicator_select",
                             {"message": msg, "rang": "AG"})
        except Exception:
            continue
        if not isinstance(data, list) or not data:
            continue
        row = data[0]
        for raw_key, val in row.items():
            for needle, field in _INDICATOR_MAP:
                if needle in raw_key:
                    try:
                        out[field] = float(val)
                    except (TypeError, ValueError):
                        pass
                    break
    return out


def _build_financial(metrics: dict, code: str) -> dict:
    """把指标字典组装成 financial_data 兼容结构"""
    now = datetime.now()
    return {
        "code": code,
        "name": "",
        "report_date": now.strftime("%Y-%m-%d"),
        "report_type": "通达信指标(最新报告期)",
        "revenue_growth": round(metrics.get("revenue_growth", 0.0), 2),
        "profit_growth": round(metrics.get("profit_growth", 0.0), 2),
        "roe": round(metrics.get("roe", 0.0), 2),
        "gross_margin": round(metrics.get("gross_margin", 0.0), 2),
        "net_margin": 0.0,
        "debt_ratio": round(metrics.get("debt_ratio", 0.0), 2),
        "eps": round(metrics.get("eps", 0.0), 2),
        "bps": round(metrics.get("bps", 0.0), 2),
        "total_revenue": 0.0,
        "net_profit": 0.0,
        "gross_profit": 0.0,
        "cash_flow_ratio": 0.0,
        "pe": round(metrics.get("pe", 0.0), 2),
        "pb": round(metrics.get("pb", 0.0), 2),
        "status": "success",
        "fetch_time": now.isoformat(),
        "source": "tdx",
    }


# ── 自然语言选股 (tdx_screener) ──────────────────────
_RANG_MAP = {
    "AG": "A股", "JJ": "基金", "ZS": "指数",
    "ZG-JJJL": "中国-基金", "GG-GP": "港股-股票",
}


def screen_stocks(message: str, rang: str = "AG", page_no: int = 1,
                  page_size: int = 20) -> dict:
    """自然语言条件选股。
    message 示例: "今天涨停" / "MACD金叉" / "主力净流入" / "3连板"
    返回 {total, rows:[{code,name,now_price,chg,涨停原因,连续涨停天数,...}]}
    """
    if _mcporter_available():
        try:
            data = _call_tdx("tdx_screener", {
                "message": message, "rang": rang,
                "pageNo": str(page_no), "pageSize": str(page_size),
            })
            if isinstance(data, list):
                rows = []
                for item in data:
                    rows.append({
                        "code": str(item.get("sec_code", "")),
                        "name": item.get("sec_name", ""),
                        "market": _RANG_MAP.get(rang, rang),
                        "now_price": _to_float(item.get("now_price")),
                        "chg": _to_float(item.get("chg")),
                        "reason": item.get("涨停原因", ""),
                        "limit_up_days": item.get("连续涨停天数", ""),
                        "boards": item.get("几天几板", ""),
                        "first_time": item.get("首次涨停时间", ""),
                        "last_time": item.get("最近涨停时间", ""),
                        "open_count": item.get("涨停打开次数", ""),
                        "amount_wan": _to_float(item.get("涨停成交额(万)")),
                        "raw": item,
                    })
                return {"total": len(rows), "rows": rows, "source": "tdx"}
        except Exception:
            pass
    return {"total": 0, "rows": [], "source": "none",
            "error": "tdx_unavailable"}


# ── 完整 F10 三表 (tdx_api_data) ─────────────────────
# entry + fixedTag 映射
_STATEMENT_ENTRIES = {
    "income": ("TdxShareCW.ph_agf10_cw_lyb", "00101"),      # 利润表(年报)
    "balance": ("TdxShareCW.ph_agf10_cw_zcfzb", "00101"),    # 资产负债表
    "cashflow": ("TdxShareCW.ph_agf10_cw_xjllb", "00101"),   # 现金流量表
}


def get_financial_statements(code: str, stmt_type: str = "income",
                             report_type: str = "00101") -> dict:
    """获取完整财务报表。
    stmt_type: income(利润表) / balance(资产负债表) / cashflow(现金流量表)
    report_type: 00101=年报(报告期) / 00102=单季度
    返回 {code, stmt_type, summary, columns, rows:[{截止日期, 营业总收入, ...}]}
    """
    if stmt_type not in _STATEMENT_ENTRIES:
        return {"error": "unknown_stmt_type", "code": code}
    entry, default_tag = _STATEMENT_ENTRIES[stmt_type]
    if _mcporter_available():
        try:
            data = _call_tdx("tdx_api_data", {
                "entry": entry, "fixedTag": report_type, "code": code,
            })
            # data 结构: {ok, response:{transformed:{summary, tables:[{name, rows}]}}}
            resp = data.get("response", {}) if isinstance(data, dict) else {}
            transformed = resp.get("transformed", {}) if isinstance(resp, dict) else {}
            tables = transformed.get("tables", []) if isinstance(transformed, dict) else []
            if tables:
                first = tables[0]
                rows_raw = first.get("rows", [])
                # 转成字典列表 + 提取列名
                rows = []
                columns = []
                for r in rows_raw:
                    if isinstance(r, dict):
                        if not columns:
                            columns = list(r.keys())
                        rows.append(r)
                return {
                    "code": code,
                    "stmt_type": stmt_type,
                    "summary": transformed.get("summary", ""),
                    "columns": columns,
                    "rows": rows,
                    "count": len(rows),
                    "source": "tdx",
                    "status": "success",
                }
            return {"code": code, "stmt_type": stmt_type,
                    "error": "empty", "source": "tdx"}
        except Exception as e:
            return {"code": code, "stmt_type": stmt_type,
                    "error": str(e), "source": "none"}
    return {"code": code, "stmt_type": stmt_type,
            "error": "tdx_unavailable", "source": "none"}


# ── 资讯模块 (wenda_*) ───────────────────────────────
def _query_wenda(tool: str, params: dict) -> dict:
    """通用 wenda_* 查询。返回 {total, items:[{title,time,url,source,summary}]}
    wenda 接口返回 [[表头],[行]...] 二维数组。
    """
    if _mcporter_available():
        try:
            data = _call_tdx(tool, params)
            if isinstance(data, list) and len(data) >= 2:
                # 第一行是表头
                header = data[0]
                items = []
                for row in data[1:]:
                    if not isinstance(row, list):
                        continue
                    item = {}
                    for i, h in enumerate(header):
                        key = {"标题": "title", "时间": "time", "链接": "url",
                               "来源": "source", "摘要": "summary"}.get(h, h)
                        item[key] = row[i] if i < len(row) else ""
                    items.append(item)
                return {"total": len(items), "items": items, "source": "tdx"}
        except Exception:
            pass
    return {"total": 0, "items": [], "source": "none",
            "error": "tdx_unavailable"}


def query_notices(name: str = "", code: str = "", bdate: str = "",
                  edate: str = "", keywords: str = "", top_k: int = 10) -> dict:
    """公司公告查询"""
    params = {"top_k": top_k}
    if name:
        params["name"] = name
    if code:
        params["symbol"] = code
    if bdate:
        params["bdate"] = bdate
    if edate:
        params["edate"] = edate
    if keywords:
        params["keywords"] = keywords
    return _query_wenda("wenda_notice_query", params)


def query_reports(name: str = "", code: str = "", bdate: str = "",
                  edate: str = "", keywords: str = "", top_k: int = 10) -> dict:
    """券商研报查询"""
    params = {"top_k": top_k}
    if name:
        params["name"] = name
    if code:
        params["symbol"] = code
    if bdate:
        params["bdate"] = bdate
    if edate:
        params["edate"] = edate
    if keywords:
        params["keywords"] = keywords
    return _query_wenda("wenda_report_query", params)


def query_news(name: str = "", code: str = "", keywords: str = "",
               top_k: int = 10) -> dict:
    """新闻资讯查询"""
    params = {"top_k": top_k}
    if name:
        params["name"] = name
    if code:
        params["symbol"] = code
    if keywords:
        params["keywords"] = keywords
    return _query_wenda("wenda_news_query", params)


# ── K线 (tdx_kline) — 供回测引擎使用 ─────────────────
_PERIOD_MAP = {
    "5m": "0", "15m": "1", "30m": "2", "60m": "3",
    "daily": "4", "weekly": "5", "monthly": "6",
}
_TQ_FLAG = {"none": "0", "qfq": "11", "hfq": "12"}  # 不复权/前复权/后复权


def get_kline(code: str, period: str = "daily", count: int = 240,
              fq: str = "qfq") -> dict:
    """通达信 K 线，替代回测引擎的新浪源。
    period: 5m/15m/30m/60m/daily/weekly/monthly
    fq: none/qfq/hfq
    返回 {code, period, fq, klines:[{date,open,close,high,low,volume,change_pct}], source}
    """
    if _mcporter_available():
        try:
            period_code = _PERIOD_MAP.get(period, "4")
            tq = _TQ_FLAG.get(fq, "11")
            data = _call_tdx("tdx_kline", {
                "code": code,
                "setcode": _setcode_of(code),
                "period": period_code,
                "wantNum": str(count),
                "tqFlag": tq,
            })
            klines = _parse_tdx_kline(data)
            if klines:
                return {"code": code, "period": period, "fq": fq,
                        "klines": klines, "count": len(klines),
                        "source": "tdx", "status": "success"}
        except Exception:
            pass
    return {"code": code, "error": "tdx_unavailable", "source": "none"}


def _parse_tdx_kline(data: dict) -> list:
    """解析 tdx_kline 返回。真实结构为 data.Rows（dict 数组），
    字段：Data(日期), Open/High/Low/Close(字符串数值), Volume(万股) 等。
    """
    if not isinstance(data, dict):
        return []
    rows = data.get("Rows", []) or []
    result = []
    for k in rows:
        if not isinstance(k, dict):
            continue
        try:
            open_p = float(k.get("Open", 0))
            close_p = float(k.get("Close", 0))
            high_p = float(k.get("High", 0))
            low_p = float(k.get("Low", 0))
        except (TypeError, ValueError):
            continue
        # Volume 单位是万股/手，原新浪接口用股，这里归一化 *100 近似
        try:
            vol = float(k.get("Volume", 0)) * 100
        except (TypeError, ValueError):
            vol = 0.0
        result.append({
            "date": str(k.get("Data", "")).split(" ")[0],
            "open": open_p,
            "close": close_p,
            "high": high_p,
            "low": low_p,
            "volume": vol,
        })
    # 计算涨跌幅
    for i in range(1, len(result)):
        prev = result[i-1]["close"]
        curr = result[i]["close"]
        result[i]["change_pct"] = round((curr-prev)/prev*100, 2) if prev > 0 else 0
    if result:
        result[0]["change_pct"] = 0
    return result


def _to_float(v):
    """安全转 float"""
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


# ── 模块自检 ──────────────────────────────────────────
# 探活缓存：避免每次访问都消耗 tdx 额度
_PROBE_CACHE = {"ts": 0, "ok": False}
_PROBE_TTL = 300  # 5 分钟内复用一次探活结果


def provider_status() -> dict:
    """返回当前数据层状态，便于前端/日志展示。

    关键点：mcporter 进程在 ≠ 通达信服务可用。免费额度耗尽时
    进程仍在，但调用会返回 'quota has been reached'。因此做**真实探活**：
    实际调用一次 tdx_quotes，成功才算 tdx 在线，否则标记降级。
    探活结果缓存 5 分钟，避免高频访问反复消耗额度。
    """
    global _PROBE_CACHE
    import time
    now = time.time()
    # 若关闭 tdx，直接返回兜底
    if not _USE_TDX or not _mcporter_available():
        return {
            "tdx_enabled": _USE_TDX,
            "fallback_enabled": _USE_FALLBACK,
            "mcporter_available": _mcporter_available(),
            "tdx_online": False,
            "provider": "fallback" if _USE_FALLBACK else "none",
        }
    # 命中缓存
    if now - _PROBE_CACHE["ts"] < _PROBE_TTL:
        tdx_ok = _PROBE_CACHE["ok"]
    else:
        tdx_ok = False
        try:
            data = _call_tdx("tdx_quotes",
                            {"code": "600519", "setcode": "1"})
            if isinstance(data, dict) and (data.get("BaseInfo") or data.get("HQInfo")):
                tdx_ok = True
        except Exception:
            tdx_ok = False
        _PROBE_CACHE = {"ts": now, "ok": tdx_ok}
    return {
        "tdx_enabled": _USE_TDX,
        "fallback_enabled": _USE_FALLBACK,
        "mcporter_available": _mcporter_available(),
        "tdx_online": tdx_ok,
        "provider": "tdx" if tdx_ok else ("fallback" if _USE_FALLBACK else "none"),
    }


if __name__ == "__main__":
    test = ["600519", "000858", "600126"]
    print("=== 行情 ===")
    for c in test:
        r = get_realtime_price(c)
        if r.get("status") == "success":
            print(f"{r['name']}({c}): {r['current_price']} ({r['change_pct']:+.2f}%) src={r.get('source')}")
        else:
            print(f"{c}: {r.get('error')}")
    print("\n=== 财务 ===")
    for c in test:
        f = get_financial_data(c)
        if f.get("error"):
            print(f"{c}: {f['error']}")
        else:
            print(f"{c}: ROE={f['roe']} 营收增速={f['revenue_growth']} 净利增速={f['profit_growth']} "
                  f"毛利率={f['gross_margin']} 负债率={f['debt_ratio']} PE={f.get('pe')} PB={f.get('pb')}")
    print("\n=== status ===", provider_status())
