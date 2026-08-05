#!/usr/bin/env python3
"""
乐友量化回测引擎 v2.0
- 完整止损/止盈机制
- 多策略参数优化
- 基准对比（买入持有）
- 风险指标（夏普比率、最大回撤）
- 策略有效性评分
"""

import urllib.request
import json
import math
import random
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from collections import defaultdict


# ============================================================
# 数据获取
# ============================================================

def get_kline_data_enhanced(code: str, period: str = "daily",
                            count: int = 500, fq: str = "qfq") -> dict:
    """增强版K线获取：优先通达信 tdx_kline（支持前复权/多周期/港股美股），
    失败自动降级到原生新浪 get_kline_data。供回测路由调用。
    period 映射: daily->daily, weekly->weekly, 其余按新浪默认日线处理。
    """
    try:
        from tdx_provider import get_kline as _tdx_kline
        tdx_period = "daily" if period in ("daily", "day", "d") else "weekly" \
            if period in ("weekly", "w") else period
        r = _tdx_kline(code, period=tdx_period, count=count, fq=fq)
        if r.get("status") == "success" and r.get("klines"):
            klines = r["klines"]
            return {"code": code, "klines": klines, "status": "success",
                    "source": "tdx"}
    except Exception:
        pass
    # 降级到新浪
    return get_kline_data(code, period=period, count=count)


def get_kline_data(code: str, period: str = "daily", count: int = 500) -> dict:
    """获取K线数据"""
    if code.startswith('6'):
        symbol = "sh" + code
    else:
        symbol = "sz" + code

    scale = 240 if period == "daily" else 1440

    url = (f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php"
           f"/CN_MarketData.getKLineData?symbol={symbol}&scale={scale}&ma=no&datalen={count}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'http://finance.sina.com.cn',
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read())
            if not raw:
                return {"error": "no_data", "code": code}

            result = []
            for k in raw:
                result.append({
                    "date": k.get("day", ""),
                    "open": float(k.get("open", 0)),
                    "close": float(k.get("close", 0)),
                    "high": float(k.get("high", 0)),
                    "low": float(k.get("low", 0)),
                    "volume": float(k.get("volume", 0)),
                })

            # 补充涨跌幅
            for i in range(1, len(result)):
                prev = result[i-1]["close"]
                curr = result[i]["close"]
                result[i]["change_pct"] = round((curr - prev) / prev * 100, 2) if prev > 0 else 0
            if result:
                result[0]["change_pct"] = 0

            return {"code": code, "klines": result, "status": "success"}
    except Exception as e:
        return {"error": str(e), "code": code}


# ============================================================
# 技术指标计算
# ============================================================

def sma(data: list, period: int) -> list:
    result = []
    for i in range(len(data)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(round(sum(data[i - period + 1:i + 1]) / period, 3))
    return result


def ema(data: list, period: int) -> list:
    k = 2.0 / (period + 1)
    result = []
    for i in range(len(data)):
        if i == 0:
            result.append(data[i])
        elif i < period - 1:
            result.append(None)
        else:
            prev = result[i - 1]
            result.append(data[i] * k + prev * (1 - k) if prev else data[i])
    return [round(v, 3) if v else None for v in result]


def calc_rsi(data: list, period: int = 14) -> list:
    result = [None] * period
    gains, losses = [], []
    for i in range(1, len(data)):
        delta = data[i] - data[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
        if i >= period:
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            if avg_loss == 0:
                result.append(100)
            else:
                rs = avg_gain / avg_loss
                result.append(round(100 - 100 / (1 + rs), 2))
    return result


def calc_bollinger(data: list, period: int = 20, std_dev: float = 2.0) -> Tuple[list, list, list]:
    upper, middle, lower = [], [], []
    for i in range(len(data)):
        if i < period - 1:
            upper.append(None); middle.append(None); lower.append(None)
        else:
            window = data[i - period + 1:i + 1]
            mid = sum(window) / period
            std = math.sqrt(sum((x - mid) ** 2 for x in window) / period)
            middle.append(round(mid, 3))
            upper.append(round(mid + std_dev * std, 3))
            lower.append(round(mid - std_dev * std, 3))
    return upper, middle, lower


def calc_kdj(highs: list, lows: list, closes: list, period: int = 9) -> Tuple[list, list, list]:
    k, d, j_val = [50], [50], [50]
    for i in range(1, len(closes)):
        if i < period - 1:
            k.append(50); d.append(50); j_val.append(50)
        else:
            wh = max(highs[i - period + 1:i + 1])
            wl = min(lows[i - period + 1:i + 1])
            rsv = (closes[i] - wl) / (wh - wl) * 100 if wh != wl else 50
            k_prev, d_prev = k[-1], d[-1]
            k_new = round(k_prev * 2 / 3 + rsv / 3, 2)
            d_new = round(d_prev * 2 / 3 + k_new / 3, 2)
            k.append(k_new); d.append(d_new)
            j_val.append(round(3 * k_new - 2 * d_new, 2))
    return k, d, j_val


def calc_macd(closes: list, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[list, list, list]:
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    dif, dea, macd_hist = [], [], []
    for i in range(len(closes)):
        if ema_fast[i] is None or ema_slow[i] is None:
            dif.append(None); dea.append(None); macd_hist.append(None)
        else:
            d = round(ema_fast[i] - ema_slow[i], 3)
            dif.append(d)
            if i == 0 or dea[i-1] is None:
                dea.append(d)
            else:
                dea.append(round(d * 2 / (signal + 1) + dea[-1] * (1 - 2 / (signal + 1)), 3))
            macd_hist.append(round((d - dea[-1]) * 2, 3))
    return dif, dea, macd_hist


def compute_all_indicators(klines: list) -> dict:
    """计算所有技术指标"""
    if not klines or len(klines) < 30:
        return {"error": "insufficient_data"}

    closes = [k["close"] for k in klines]
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]
    volumes = [k["volume"] for k in klines]
    n = len(klines)

    dif, dea, macd_hist = calc_macd(closes)
    kdj_k, kdj_d, kdj_j = calc_kdj(highs, lows, closes)
    bb_upper, bb_middle, bb_lower = calc_bollinger(closes)
    rsi6, rsi12, rsi14 = calc_rsi(closes, 6), calc_rsi(closes, 12), calc_rsi(closes, 14)
    ma5 = sma(closes, 5)
    ma10 = sma(closes, 10)
    ma20 = sma(closes, 20)
    ma30 = sma(closes, 30)
    ma60 = sma(closes, 60)
    vol_ma5 = sma(volumes, 5)

    idx = n - 1
    today = klines[idx]

    return {
        "closes": closes,
        "highs": highs,
        "lows": lows,
        "volumes": volumes,
        "klines": klines,
        "today": {
            "date": today["date"], "close": today["close"],
            "high": today["high"], "low": today["low"],
            "volume": today["volume"],
            "change_pct": today.get("change_pct", 0),
        },
        "indicators": {
            "MA5": ma5[idx], "MA10": ma10[idx], "MA20": ma20[idx],
            "MA30": ma30[idx], "MA60": ma60[idx],
            "DIF": dif[idx], "DEA": dea[idx], "MACD": macd_hist[idx],
            "RSI6": rsi6[idx], "RSI12": rsi12[idx], "RSI14": rsi14[idx],
            "KDJ_K": kdj_k[idx], "KDJ_D": kdj_d[idx], "KDJ_J": kdj_j[idx],
            "BB_Upper": bb_upper[idx], "BB_Middle": bb_middle[idx], "BB_Lower": bb_lower[idx],
            "Volume_MA5": vol_ma5[idx],
        },
        # 用于回测的完整序列
        "_series": {
            "ma5": ma5, "ma10": ma10, "ma20": ma20,
            "dif": dif, "dea": dea, "macd_hist": macd_hist,
            "rsi6": rsi6, "rsi12": rsi12, "rsi14": rsi14,
            "kdj_k": kdj_k, "kdj_d": kdj_d, "kdj_j": kdj_j,
            "bb_upper": bb_upper, "bb_middle": bb_middle, "bb_lower": bb_lower,
            "vol_ma5": vol_ma5,
        }
    }


# ============================================================
# 回测引擎 v2.0（带止损/止盈）
# ============================================================

def backtest_v2(klines: list, strategy: str = "combo",
                stop_loss: float = -8.0,
                take_profit: float = 20.0,
                rsi_buy_thresh: int = 35,
                rsi_sell_thresh: int = 70,
                bb_std: float = 2.0) -> dict:
    """
    回测 v2.0 - 包含止损/止盈的完整回测
    """
    if not klines or len(klines) < 60:
        return {"error": "insufficient_klines", "total_trades": 0}

    closes = [k["close"] for k in klines]
    volumes = [k["volume"] for k in klines]
    n = len(klines)

    # 预计算指标序列
    ma5, ma10, ma20 = sma(closes, 5), sma(closes, 10), sma(closes, 20)
    dif, dea, macd_hist = calc_macd(closes)
    rsi12 = calc_rsi(closes, 12)
    bb_upper, bb_middle, bb_lower = calc_bollinger(closes, std_dev=bb_std)
    vol_ma5 = sma(volumes, 5)

    trades = []
    position = None  # {"date": str, "price": float, "high": float}
    wins, losses = 0, 0
    total_profit = 0.0
    consecutive_wins = 0
    consecutive_losses = 0

    # 权益曲线
    equity = 100.0
    peak = 100.0
    drawdowns = []
    returns = []  # 每日收益率（用于夏普比率）

    # 买入持有基准
    bh_start = closes[60] if len(closes) > 60 else closes[0]
    bh_end = closes[-1]
    bh_return = round((bh_end - bh_start) / bh_start * 100, 2)

    for i in range(60, n):
        date = klines[i]["date"]
        price = closes[i]
        vol = volumes[i]

        if i > 60:
            ret = (closes[i] - closes[i-1]) / closes[i-1]
            returns.append(ret)

        # ---- 生成信号 ----
        m_buy = (ma5[i] and ma10[i] and ma20[i] and
                 ma5[i] > ma10[i] > ma20[i] and
                 ma5[i-1] <= ma10[i-1])
        m_sell = (ma5[i] and ma10[i] and ma20[i] and
                  ma5[i] < ma10[i] < ma20[i] and
                  ma5[i-1] >= ma10[i-1])

        macd_buy = (dif[i] and dea[i] and dif[i-1] is not None and dea[i-1] is not None and
                    dif[i] > dea[i] and dif[i-1] <= dea[i-1] and dif[i] > 0)
        macd_sell = (dif[i] and dea[i] and dif[i-1] is not None and dea[i-1] is not None and
                     dif[i] < dea[i] and dif[i-1] >= dea[i-1] and dif[i] < 0)

        rsi_buy = (rsi12[i] is not None and rsi12[i] < rsi_buy_thresh)
        rsi_sell = (rsi12[i] is not None and rsi12[i] > rsi_sell_thresh)

        bb_buy = (bb_lower[i] and price < bb_lower[i])
        bb_sell = (bb_upper[i] and price > bb_upper[i])

        vol_surge = (vol_ma5[i] and vol > vol_ma5[i] * 1.5)

        if strategy == "ma_cross":
            buy_sig, sell_sig = m_buy, m_sell
        elif strategy == "macd_cross":
            buy_sig, sell_sig = macd_buy, macd_sell
        elif strategy == "rsi_reversal":
            buy_sig, sell_sig = rsi_buy, rsi_sell
        elif strategy == "bollinger":
            buy_sig, sell_sig = bb_buy, bb_sell
        elif strategy == "vol_surge":
            buy_sig, sell_sig = (m_buy and vol_surge), (m_sell and vol_surge)
        elif strategy == "combo":
            buy_sig = int(m_buy) + int(macd_buy) + int(rsi_buy) + int(bb_buy) >= 2
            sell_sig = int(m_sell) + int(macd_sell) + int(rsi_sell) + int(bb_sell) >= 2
        elif strategy == "conservative":
            # 保守策略：需要多个条件同时满足
            buy_sig = m_buy and macd_buy and rsi_buy
            sell_sig = m_sell or macd_sell or rsi_sell
        else:
            buy_sig, sell_sig = False, False

        # ---- 止损/止盈检查 ----
        if position:
            profit_pct = (price - position["price"]) / position["price"] * 100
            stop_triggered = profit_pct <= stop_loss
            tp_triggered = profit_pct >= take_profit
            sell_triggered = sell_sig and (i - position.get("buy_idx", i)) >= 3

            if stop_triggered:
                # 止损
                total_profit += profit_pct
                trades.append({"type": "STOP_LOSS", "date": date, "price": price,
                               "profit_pct": round(profit_pct, 2)})
                losses += 1
                consecutive_losses += 1
                consecutive_wins = 0
                position = None
            elif tp_triggered:
                # 止盈
                total_profit += profit_pct
                trades.append({"type": "TAKE_PROFIT", "date": date, "price": price,
                               "profit_pct": round(profit_pct, 2)})
                wins += 1
                consecutive_wins += 1
                consecutive_losses = 0
                position = None
            elif sell_triggered:
                # 趋势信号卖出
                total_profit += profit_pct
                trades.append({"type": "SELL", "date": date, "price": price,
                               "profit_pct": round(profit_pct, 2)})
                if profit_pct > 0:
                    wins += 1; consecutive_wins += 1; consecutive_losses = 0
                else:
                    losses += 1; consecutive_losses += 1; consecutive_wins = 0
                position = None
        else:
            # 无持仓，按信号买入
            if buy_sig:
                position = {"date": date, "price": price, "buy_idx": i}

    # 期末平仓
    if position:
        profit_pct = (closes[-1] - position["price"]) / position["price"] * 100
        total_profit += profit_pct
        trades.append({"type": "CLOSE", "date": klines[-1]["date"], "price": closes[-1],
                       "profit_pct": round(profit_pct, 2), "note": "期末平仓"})
        if profit_pct > 0:
            wins += 1
        else:
            losses += 1

    # ---- 统计指标 ----
    total_trades = wins + losses
    win_rate = round(wins / total_trades * 100, 1) if total_trades > 0 else 0
    years = (n - 60) / 250
    annualized = round(total_profit / years, 2) if years > 0 else 0

    # 夏普比率
    if len(returns) > 30:
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        std_ret = math.sqrt(variance)
        if std_ret > 0:
            sharpe = round(mean_ret / std_ret * math.sqrt(252), 2)
        else:
            sharpe = 0
    else:
        sharpe = 0

    # 最大回撤（重建权益曲线）
    peak = 100.0
    max_dd = 0.0
    equity = 100.0
    equity_curve = [100.0]
    for t in trades:
        if t["type"] in ("STOP_LOSS", "TAKE_PROFIT", "SELL", "CLOSE"):
            equity *= (1 + t["profit_pct"] / 100)
            equity_curve.append(equity)
            peak = max(peak, equity)
            dd = (peak - equity) / peak * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)

    # 超额收益
    excess_return = round(annualized - bh_return, 2)

    # 盈亏比
    profit_trades = [t for t in trades if t["type"] in ("STOP_LOSS", "TAKE_PROFIT", "SELL", "CLOSE") and t.get("profit_pct", 0) > 0]
    loss_trades = [t for t in trades if t["type"] in ("STOP_LOSS", "TAKE_PROFIT", "SELL", "CLOSE") and t.get("profit_pct", 0) < 0]
    avg_win = sum(t["profit_pct"] for t in profit_trades) / len(profit_trades) if profit_trades else 0
    avg_loss = sum(t["profit_pct"] for t in loss_trades) / len(loss_trades) if loss_trades else 0
    profit_loss_ratio = round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0

    # 最大连续盈亏
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    cur_w, cur_l = 0, 0
    for t in trades:
        if t["type"] in ("STOP_LOSS", "TAKE_PROFIT", "SELL", "CLOSE"):
            if t["profit_pct"] > 0:
                cur_w += 1; cur_l = 0
                max_consecutive_wins = max(max_consecutive_wins, cur_w)
            else:
                cur_l += 1; cur_w = 0
                max_consecutive_losses = max(max_consecutive_losses, cur_l)

    return {
        "strategy": strategy,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "rsi_thresholds": {"buy": rsi_buy_thresh, "sell": rsi_sell_thresh},
        "benchmark": {
            "name": "买入持有",
            "return": bh_return,
            "period_years": round(years, 1),
        },
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_return": round(total_profit, 2),
        "annualized_return": annualized,
        "excess_return": excess_return,
        "max_drawdown": round(max_dd, 2),
        "sharpe_ratio": sharpe,
        "profit_loss_ratio": profit_loss_ratio,
        "avg_win_pct": round(avg_win, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "max_consecutive_wins": max_consecutive_wins,
        "max_consecutive_losses": max_consecutive_losses,
        "period_days": n - 60,
        "period_years": round(years, 1),
        "recent_trades": trades[-8:] if trades else [],
        "equity_curve": equity_curve[-20:] if equity_curve else [100],
    }


# ============================================================
# 参数优化（网格搜索）
# ============================================================

def optimize_parameters(klines: list, strategy: str = "combo") -> dict:
    """
    网格搜索最优止损/止盈参数
    """
    if not klines or len(klines) < 120:
        return {"error": "insufficient_data_for_optimization"}

    best = None
    best_score = -999

    configs = []

    # 止损范围: -5% ~ -15%
    stop_losses = [-5, -7, -8, -10, -12]
    # 止盈范围: 10% ~ 40%
    take_profits = [15, 20, 25, 30, 40]
    # RSI 阈值
    rsi_buys = [25, 30, 35, 40]
    rsi_sells = [60, 65, 70, 75]

    for sl in stop_losses:
        for tp in take_profits:
            if tp <= abs(sl) * 2:  # 止盈至少是止损的2倍
                continue
            for rb in rsi_buys:
                for rs in rsi_sells:
                    if rs <= rb:
                        continue
                    bt = backtest_v2(klines, strategy, sl, tp, rb, rs)
                    if bt.get("total_trades", 0) >= 5:
                        # 综合评分 = 年化收益 * 0.4 + 胜率 * 0.3 + 夏普比率 * 10 * 0.2 - 最大回撤 * 0.1
                        score = (bt["annualized_return"] * 0.4 +
                                 bt["win_rate"] * 0.3 +
                                 bt["sharpe_ratio"] * 10 * 0.2 -
                                 bt["max_drawdown"] * 0.1)
                        configs.append({**bt, "score": round(score, 2)})
                        if score > best_score:
                            best_score = score
                            best = bt.copy()
                            best["score"] = round(score, 2)
                            best["optimal_config"] = {
                                "stop_loss": sl, "take_profit": tp,
                                "rsi_buy_thresh": rb, "rsi_sell_thresh": rs
                            }

    # 按年化收益排序所有配置
    configs.sort(key=lambda x: x["annualized_return"], reverse=True)

    return {
        "optimal": best,
        "top_configs": configs[:5],  # Top 5 配置
        "total_configs_tested": len(configs),
        "strategy": strategy,
    }


# ============================================================
# 多股票策略有效性对比
# ============================================================

def compare_strategies_across_stocks(codes: List[str], strategies: List[str]) -> dict:
    """测试多只股票 × 多策略"""
    results = []
    strategy_summary = defaultdict(lambda: {"wins": 0, "count": 0, "annualized_sum": 0, "sharpe_sum": 0})

    for code in codes:
        kd = get_kline_data(code, count=400)
        if kd.get("error"):
            continue

        klines = kd["klines"]
        if len(klines) < 120:
            continue

        ta = compute_all_indicators(klines)
        if "error" in ta:
            continue

        stock_result = {"code": code, "klines_count": len(klines), "strategies": {}}

        for strat in strategies:
            bt = backtest_v2(klines, strat)
            stock_result["strategies"][strat] = {
                "annualized": bt.get("annualized_return", 0),
                "win_rate": bt.get("win_rate", 0),
                "sharpe": bt.get("sharpe_ratio", 0),
                "max_dd": bt.get("max_drawdown", 0),
                "total_trades": bt.get("total_trades", 0),
                "excess_return": bt.get("excess_return", 0),
                "pl_ratio": bt.get("profit_loss_ratio", 0),
            }
            # 汇总
            s = strategy_summary[strat]
            s["count"] += 1
            s["annualized_sum"] += bt.get("annualized_return", 0)
            s["sharpe_sum"] += bt.get("sharpe_ratio", 0)
            if bt.get("win_rate", 0) >= 50:
                s["wins"] += 1

        results.append(stock_result)

    # 策略平均表现
    summary = {}
    for strat, s in strategy_summary.items():
        count = s["count"]
        summary[strat] = {
            "avg_annualized": round(s["annualized_sum"] / count, 2),
            "avg_sharpe": round(s["sharpe_sum"] / count, 2),
            "win_rate_over_50": f"{round(s['wins'] / count * 100, 1)}%",
            "stocks_tested": count,
        }

    # 最优策略推荐
    best_strategy = max(summary.items(), key=lambda x: x[1]["avg_annualized"])

    return {
        "stocks_tested": len(results),
        "strategies": strategies,
        "strategy_summary": summary,
        "best_strategy": {"name": best_strategy[0], "stats": best_strategy[1]},
        "stock_results": results[:20],  # 最多返回20只
    }


# ============================================================
# 单股票深度回测 + 策略建议
# ============================================================

def analyze_and_recommend(code: str) -> dict:
    """单股票完整分析 + 最优策略推荐"""
    kd = get_kline_data(code, count=500)
    if kd.get("error"):
        return {"error": kd["error"], "code": code}

    klines = kd["klines"]
    ta = compute_all_indicators(klines)
    today = ta["today"]
    ind = ta["indicators"]

    strategies = ["ma_cross", "macd_cross", "rsi_reversal", "bollinger", "combo", "conservative"]
    opt_results = {}
    best_for_stock = None
    best_annualized = -999

    for strat in strategies:
        bt = backtest_v2(klines, strat)
        opt_results[strat] = bt
        if bt.get("annualized_return", -999) > best_annualized:
            best_annualized = bt["annualized_return"]
            best_for_stock = strat

    # 参数优化
    opt_config = optimize_parameters(klines, "combo")
    opt = opt_config.get("optimal")

    # 当前技术信号
    sig = generate_signal(ta)

    # 策略对比
    strategy_comparison = []
    for strat, bt in sorted(opt_results.items(), key=lambda x: x[1].get("annualized_return", 0), reverse=True):
        strategy_comparison.append({
            "strategy": strat,
            "annualized": bt.get("annualized_return", 0),
            "win_rate": bt.get("win_rate", 0),
            "sharpe": bt.get("sharpe_ratio", 0),
            "max_dd": bt.get("max_drawdown", 0),
            "total_trades": bt.get("total_trades", 0),
            "excess_return": bt.get("excess_return", 0),
            "pl_ratio": bt.get("profit_loss_ratio", 0),
            "benchmark_return": bt.get("benchmark", {}).get("return", 0),
            "recommended": strat == best_for_stock,
        })

    # 生成投资建议
    recommendation = generate_recommendation(sig, opt, best_for_stock, today, ind)

    return {
        "code": code,
        "today": today,
        "indicators": ind,
        "current_signal": sig,
        "strategy_comparison": strategy_comparison,
        "optimal_config": opt.get("optimal_config") if opt else None,
        "optimal_performance": {
            "annualized": opt.get("annualized_return") if opt else None,
            "win_rate": opt.get("win_rate") if opt else None,
            "sharpe": opt.get("sharpe_ratio") if opt else None,
            "max_drawdown": opt.get("max_drawdown") if opt else None,
        },
        "best_strategy": best_for_stock,
        "recommendation": recommendation,
    }


def generate_signal(ta: dict) -> dict:
    """生成当前技术信号"""
    ind = ta["indicators"]
    today = ta["today"]
    price = today["close"]

    strength = 0
    signals_text = []

    ma5, ma10, ma20 = ind["MA5"], ind["MA10"], ind["MA20"]
    dif, dea, macd_h = ind["DIF"], ind["DEA"], ind["MACD"]
    rsi6, rsi12 = ind["RSI6"], ind["RSI12"]
    kj, kd, jj = ind["KDJ_K"], ind["KDJ_D"], ind["KDJ_J"]
    bbu, bbm, bbl = ind["BB_Upper"], ind["BB_Middle"], ind["BB_Lower"]

    if ma5 and ma10 and ma20:
        if ma5 > ma10 > ma20:
            strength += 1
            signals_text.append("均线多头排列")
        elif ma5 < ma10 < ma20:
            strength -= 1
            signals_text.append("均线空头排列")

    if dif is not None and dea is not None:
        if dif > dea and dif > 0:
            strength += 1
            signals_text.append("MACD多头")
        elif dif < dea and dif < 0:
            strength -= 1
            signals_text.append("MACD空头")

    if rsi6 and rsi12:
        if rsi6 < 30 or rsi12 < 35:
            strength += 1
            signals_text.append("RSI超卖")
        elif rsi6 > 75 or rsi12 > 70:
            strength -= 1
            signals_text.append("RSI超买")

    if kj and kd and jj:
        if kj > kd and jj > 50 and jj < 90:
            strength += 1
            signals_text.append("KDJ金叉")
        elif kj < kd and jj < 20:
            strength += 1
            signals_text.append("KDJ超卖反弹")

    if bbl and bbu:
        if price < bbl:
            strength += 1
            signals_text.append("触及布林下轨超卖")
        elif price > bbu:
            strength -= 1
            signals_text.append("突破布林上轨偏热")

    if strength >= 2:
        sig_type = "BUY"
    elif strength <= -2:
        sig_type = "SELL"
    elif strength == 1:
        sig_type = "BUY" if ind.get("RSI6", 50) < 50 else "HOLD"
    elif strength == -1:
        sig_type = "SELL" if ind.get("RSI6", 50) > 50 else "HOLD"
    else:
        sig_type = "HOLD"

    return {
        "type": sig_type,
        "strength": strength,
        "signals": signals_text,
        "confidence": min(90, 50 + abs(strength) * 15),
    }


def generate_recommendation(sig: dict, opt: dict, best_strat: str, today: dict, ind: dict) -> dict:
    """生成投资建议"""
    price = today["close"]
    sl = opt.get("optimal_config", {}).get("stop_loss", -8) if opt else -8
    tp = opt.get("optimal_config", {}).get("take_profit", 20) if opt else 20
    ann = opt.get("annualized_return", 0) if opt else 0
    wr = opt.get("win_rate", 0) if opt else 0
    sh = opt.get("sharpe_ratio", 0) if opt else 0

    if sig["type"] == "BUY":
        if ann > 15 and sh > 1:
            verdict = "强烈推荐"
            risk_level = "低"
            allocation = "20-30%"
        elif ann > 8:
            verdict = "适度买入"
            risk_level = "中"
            allocation = "15-20%"
        else:
            verdict = "谨慎买入"
            risk_level = "中高"
            allocation = "10-15%"
        action = f"建议仓位 {allocation}，止损设{sl}%，止盈设{tp}%，历史胜率{wr}%，年化收益{ann}%"
    elif sig["type"] == "SELL":
        verdict = "建议减仓"
        risk_level = "高"
        action = "趋势走弱，建议减仓或观望，不建议新买入"
    else:
        verdict = "观望"
        risk_level = "中"
        action = f"趋势不明，建议等待确认信号，历史年化{ann}%，夏普比率{sh}"

    return {
        "verdict": verdict,
        "risk_level": risk_level,
        "action": action,
        "best_strategy": best_strat,
        "expected_annualized": ann,
        "historical_win_rate": wr,
        "stop_loss": sl,
        "take_profit": tp,
        "sharpe_ratio": sh,
        "key_metrics": {
            "rsi": ind.get("RSI12"),
            "kdj_j": ind.get("KDJ_J"),
            "macd_hist": ind.get("MACD"),
            "ma20_distance": round((price - ind.get("MA20", 0)) / ind.get("MA20", 1) * 100, 2) if ind.get("MA20") else None,
        }
    }


# ============================================================
# 主程序测试
# ============================================================

if __name__ == "__main__":
    test_codes = ["600519", "000858", "600036", "000001", "600276"]

    print("=" * 60)
    print("🎯 乐友量化回测引擎 v2.0")
    print("=" * 60)

    # 1. 多股票 × 多策略对比
    print("\n📊 策略有效性对比（5只股票）")
    comp = compare_strategies_across_stocks(test_codes,
        ["ma_cross", "macd_cross", "rsi_reversal", "bollinger", "combo", "conservative"])
    print(f"\n测试股票数: {comp['stocks_tested']}")
    print(f"\n推荐策略: {comp['best_strategy']['name']}")
    print(f"  平均年化: {comp['best_strategy']['stats']['avg_annualized']}%")
    print(f"  平均夏普: {comp['best_strategy']['stats']['avg_sharpe']}")
    print(f"  跑赢50%股票占比: {comp['best_strategy']['stats']['win_rate_over_50']}")

    print("\n各策略平均表现:")
    for strat, s in sorted(comp["strategy_summary"].items(), key=lambda x: x[1]["avg_annualized"], reverse=True):
        print(f"  {strat:15s}: 年化{s['avg_annualized']:6.1f}%  夏普{s['avg_sharpe']:5.2f}  胜率>50%: {s['win_rate_over_50']}")

    # 2. 单股票深度分析
    print("\n" + "=" * 60)
    print("📈 单股票深度分析: 贵州茅台(600519)")
    result = analyze_and_recommend("600519")
    print(f"\n当前信号: {result['current_signal']['type']} (置信度 {result['current_signal']['confidence']}%)")
    print(f"信号依据: {', '.join(result['current_signal']['signals'])}")
    print(f"\n最优策略: {result['best_strategy']}")
    print(f"推荐配置: 止损{result['optimal_config']}")
    print(f"历史年化: {result['optimal_performance']['annualized']}%  胜率: {result['optimal_performance']['win_rate']}%")
    print(f"\n投资建议: {result['recommendation']['verdict']} - {result['recommendation']['action']}")
    print(f"\n策略对比:")
    for s in result["strategy_comparison"]:
        rec = "⭐" if s["recommended"] else "  "
        print(f"  {rec}{s['strategy']:15s}: 年化{s['annualized']:6.1f}% 胜率{s['win_rate']:5.1f}% 夏普{s['sharpe']:5.2f} 最大回撤{s['max_dd']:5.1f}%")
