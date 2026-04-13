#!/usr/bin/env python3
"""
技术分析模块
支持：MA、MACD、RSI、KDJ、布林带、成交量分析
"""

import urllib.request
import json
from datetime import datetime, timedelta
from typing import Optional


def get_kline_data(code: str, period: str = "daily", count: int = 120) -> dict:
    """
    获取K线数据
    period: daily(日K) / weekly(周K)
    使用新浪财经免费接口
    """
    # 确定市场前缀
    if code.startswith('6'):
        symbol = "sh" + code
    else:
        symbol = "sz" + code

    # period: 240=日K, 1440=周K
    scale = 240 if period == "daily" else 1440

    url = (
        f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php"
        f"/CN_MarketData.getKLineData"
        f"?symbol={symbol}&scale={scale}&ma=no&datalen={count}"
    )

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'http://finance.sina.com.cn',
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = json.loads(response.read())
            if not raw:
                return {"error": "no_kline_data", "code": code}

            result = []
            for k in raw:
                result.append({
                    "date": k.get("day", ""),
                    "open": float(k.get("open", 0)),
                    "close": float(k.get("close", 0)),
                    "high": float(k.get("high", 0)),
                    "low": float(k.get("low", 0)),
                    "volume": float(k.get("volume", 0)),
                    "change_pct": 0.0,  # 新浪接口无涨跌幅，手动计算
                })
            # 补充涨跌幅
            for i in range(1, len(result)):
                prev = result[i-1]["close"]
                curr = result[i]["close"]
                result[i]["change_pct"] = round((curr - prev) / prev * 100, 2) if prev > 0 else 0

            return {"code": code, "klines": result, "status": "success"}
    except Exception as e:
        return {"error": str(e), "code": code}


def _sma(data, period: int) -> list:
    """简单移动平均"""
    result = []
    for i in range(len(data)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(round(sum(data[i - period + 1:i + 1]) / period, 3))
    return result


def _ema(data, period: int) -> list:
    """指数移动平均"""
    k = 2.0 / (period + 1)
    result = []
    for i in range(len(data)):
        if i == 0:
            result.append(data[i])
        elif i < period - 1:
            result.append(None)
        else:
            if result[i - 1] is None:
                result.append(sum(data[i - period + 1:i + 1]) / period)
            else:
                result.append(data[i] * k + result[i - 1] * (1 - k))
    return [round(v, 3) if v is not None else None for v in result]


def _stddev(data, period: int) -> list:
    """标准差"""
    import math
    result = []
    for i in range(len(data)):
        if i < period - 1:
            result.append(None)
        else:
            window = data[i - period + 1:i + 1]
            mean = sum(window) / period
            variance = sum((x - mean) ** 2 for x in window) / period
            result.append(round(math.sqrt(variance), 3))
    return result


def calculate_indicators(klines: list) -> dict:
    """计算所有技术指标"""
    if not klines or len(klines) < 20:
        return {"error": "insufficient_data"}

    closes = [k["close"] for k in klines]
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]
    volumes = [k["volume"] for k in klines]
    n = len(klines)

    # === 移动平均线 ===
    ma5 = _sma(closes, 5)
    ma10 = _sma(closes, 10)
    ma20 = _sma(closes, 20)
    ma30 = _sma(closes, 30)
    ma60 = _sma(closes, 60)

    # === EMA ===
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)

    # === MACD ===
    dif = []
    macd = []
    dea = []
    macd_hist = []
    for i in range(n):
        if ema12[i] is None or ema26[i] is None:
            dif.append(None)
            macd.append(None)
            dea.append(None)
            macd_hist.append(None)
        else:
            d = round(ema12[i] - ema26[i], 3)
            dif.append(d)
            if i == 0 or dea[i - 1] is None:
                d_e = d
            else:
                d_e = round(d * 0.2 + dea[i - 1] * 0.8, 3)
            dea.append(d_e)
            m = round((d - d_e) * 2, 3)
            macd_hist.append(m)
            macd.append(round(m * 0.2 + (macd[i - 1] or 0) * 0.8 if i > 0 else m, 3))

    # === RSI ===
    def calc_rsi(data, period: int = 14) -> list:
        result = []
        for i in range(len(data)):
            if i < period:
                result.append(None)
            else:
                gains = sum(max(data[j] - data[j - 1], 0) for j in range(i - period + 1, i + 1))
                losses = sum(max(data[j - 1] - data[j], 0) for j in range(i - period + 1, i + 1))
                if losses == 0:
                    result.append(100)
                else:
                    rs = gains / losses
                    result.append(round(100 - 100 / (1 + rs), 2))
        return result

    rsi6 = calc_rsi(closes, 6)
    rsi12 = calc_rsi(closes, 12)
    rsi24 = calc_rsi(closes, 24)

    # === KDJ ===
    kdj_k = []
    kdj_d = []
    kdj_j = []
    RSV_period = 9
    for i in range(n):
        if i < RSV_period - 1:
            kdj_k.append(50)
            kdj_d.append(50)
            kdj_j.append(50)
        else:
            window_high = max(highs[i - RSV_period + 1:i + 1])
            window_low = min(lows[i - RSV_period + 1:i + 1])
            rsv = (closes[i] - window_low) / (window_high - window_low) * 100 if window_high != window_low else 50
            prev_k = kdj_k[-1] if kdj_k else 50
            prev_d = kdj_d[-1] if kdj_d else 50
            k = round(prev_k * 2 / 3 + rsv / 3, 2)
            d = round(prev_d * 2 / 3 + k / 3, 2)
            j = round(3 * k - 2 * d, 2)
            kdj_k.append(k)
            kdj_d.append(d)
            kdj_j.append(j)

    # === 布林带 ===
    bb_upper = []
    bb_middle = []
    bb_lower = []
    bb_period = 20
    for i in range(n):
        if i < bb_period - 1:
            bb_upper.append(None)
            bb_middle.append(None)
            bb_lower.append(None)
        else:
            window = closes[i - bb_period + 1:i + 1]
            middle = sum(window) / bb_period
            std = _stddev(closes, bb_period)[i]
            bb_middle.append(round(middle, 3))
            bb_upper.append(round(middle + 2 * std, 3))
            bb_lower.append(round(middle - 2 * std, 3))

    # === 成交量分析 ===
    vol_ma5 = _sma(volumes, 5)
    vol_ma10 = _sma(volumes, 10)

    # === 整合到每根K线 ===
    today = klines[-1]
    idx = n - 1

    # 当前指标值
    indicators = {
        "MA5": ma5[idx] if ma5[idx] else round(sum(closes[-5:])/5, 2),
        "MA10": ma10[idx] if ma10[idx] else round(sum(closes[-10:])/10, 2),
        "MA20": ma20[idx] if ma20[idx] else round(sum(closes[-20:])/20, 2),
        "MA30": ma30[idx] if ma30[idx] else round(sum(closes[-30:])/30, 2),
        "MA60": ma60[idx] if ma60[idx] else round(sum(closes[-60:])/60, 2),
        "DIF": dif[idx],
        "DEA": dea[idx],
        "MACD": macd_hist[idx],
        "RSI6": rsi6[idx],
        "RSI12": rsi12[idx],
        "RSI24": rsi24[idx],
        "KDJ_K": kdj_k[idx],
        "KDJ_D": kdj_d[idx],
        "KDJ_J": kdj_j[idx],
        "BB_Upper": bb_upper[idx],
        "BB_Middle": bb_middle[idx],
        "BB_Lower": bb_lower[idx],
        "Volume_MA5": vol_ma5[idx] if vol_ma5[idx] else round(sum(volumes[-5:])/5, 2),
    }

    # 幅移计算（K线与MA偏离度）
    ma_distances = {}
    for ma_name, ma_val in [("MA5", ma5[idx]), ("MA10", ma10[idx]), ("MA20", ma20[idx])]:
        if ma_val and ma_val > 0:
            ma_distances[ma_name] = round((closes[idx] - ma_val) / ma_val * 100, 2)

    return {
        "today": {
            "date": today["date"],
            "open": today["open"],
            "close": today["close"],
            "high": today["high"],
            "low": today["low"],
            "volume": today["volume"],
            "change_pct": today["change_pct"],
        },
        "indicators": indicators,
        "ma_distances": ma_distances,  # 当前价与各均线偏离%
        "klines": klines,  # 全部K线（供回测使用）
    }


def generate_buy_sell_signals(indicators: dict, current_price: float, ma_distances: dict) -> dict:
    """
    基于技术指标生成买卖信号
    价值投资风格：趋势优先，兼顾超买超卖，不追高
    """
    signals = []
    strength = 0  # 信号强度 -3~+3
    signal_type = "HOLD"
    confidence = 50

    ma5 = indicators.get("MA5", 0)
    ma10 = indicators.get("MA10", 0)
    ma20 = indicators.get("MA20", 0)
    ma60 = indicators.get("MA60", 0)
    dif = indicators.get("DIF", 0)
    dea = indicators.get("DEA", 0)
    macd_hist = indicators.get("MACD", 0)
    rsi6 = indicators.get("RSI6", 50)
    rsi12 = indicators.get("RSI12", 50)
    kdj_k = indicators.get("KDJ_K", 50)
    kdj_d = indicators.get("KDJ_D", 50)
    kdj_j = indicators.get("KDJ_J", 50)
    bb_upper = indicators.get("BB_Upper", 0)
    bb_lower = indicators.get("BB_Lower", 0)
    bb_middle = indicators.get("BB_Middle", 0)

    # === 均线系统信号 ===
    # 黄金交叉（短上穿长）= 看多
    if ma5 > ma10 > ma20:
        signals.append(("✅ 均线多头排列（MA5>MA10>MA20）", "+1"))
        strength += 1
    elif ma5 < ma10 < ma20:
        signals.append(("⚠️ 均线空头排列（MA5<MA10<MA20）", "-1"))
        strength -= 1

    # 价格与均线关系
    if current_price > ma5 > ma10:
        signals.append(("✅ 股价站稳5日/10日均线，趋势向上", "+1"))
        strength += 1
    elif current_price < ma5 < ma10:
        signals.append(("⚠️ 股价跌破5日/10日均线，趋势向下", "-1"))
        strength -= 1

    if ma5 > ma20 and ma10 > ma20:
        signals.append(("✅ 中期上升趋势（20日均线支撑）", "+1"))
        strength += 1
    elif ma5 < ma20 and ma10 < ma20:
        signals.append(("⚠️ 中期下降趋势（20日均线压制）", "-1"))
        strength -= 1

    # === MACD 信号 ===
    prev_macd = macd_hist * 0.8 if macd_hist else 0  # 估算前一交易日
    if dif > dea and dif > 0:
        signals.append(("✅ DIF>DEA且为正，MACD柱状图扩张，多头", "+1"))
        strength += 1
    elif dif < dea and dif < 0:
        signals.append(("⚠️ DIF<DEA且为负，MACD柱状图收缩，空头", "-1"))
        strength -= 1

    # MACD 金叉/死叉
    if dif > dea and dif > 0 and dif - dea > abs(prev_macd) * 0.5:
        signals.append(("✅ MACD 金叉突破，零轴上方动能强劲", "+2"))
        strength += 2
    elif dif < dea and dif < 0:
        signals.append(("⚠️ MACD 死叉，零轴下方谨慎", "-2"))
        strength -= 2

    # === RSI 信号 ===
    if rsi6 < 30 or rsi12 < 35:
        signals.append(("✅ RSI超卖（<35），存在反弹机会", "+1"))
        strength += 1
    elif rsi6 > 75 or rsi12 > 70:
        signals.append(("⚠️ RSI超买（>70），注意回调风险", "-1"))
        strength -= 1
    elif 45 <= rsi6 <= 65 and 45 <= rsi12 <= 65:
        signals.append(("✅ RSI处于健康区间（45-65），趋势健康", "+1"))
        strength += 1

    # === KDJ 信号 ===
    if kdj_k > kdj_d and kdj_j > 50 and kdj_j < 90:
        signals.append(("✅ KDJ 金叉且在强势区（50-90），买入信号", "+2"))
        strength += 2
    elif kdj_k > 80 or kdj_j > 90:
        signals.append(("⚠️ KDJ 超买区域（J>90），追高风险大", "-1"))
        strength -= 1
    elif kdj_k < kdj_d and kdj_j < 20:
        signals.append(("✅ KDJ 低位金叉，J值<20超卖，反弹概率大", "+2"))
        strength += 2
    elif kdj_k < kdj_d and (kdj_j > 80):
        signals.append(("⚠️ KDJ 高位死叉，注意减仓", "-2"))
        strength -= 2

    # === 布林带信号 ===
    if bb_lower > 0 and current_price < bb_lower:
        signals.append(("✅ 股价触及布林带下轨超卖区域，低估机会", "+2"))
        strength += 2
    elif bb_upper > 0 and current_price > bb_upper:
        signals.append(("⚠️ 股价突破布林带上轨，偏离过大有回调风险", "-1"))
        strength -= 1

    # 布林带开口判断
    if bb_upper and bb_lower and bb_middle:
        bb_width = (bb_upper - bb_lower) / bb_middle * 100
        if bb_width < 8:
            signals.append(("⚠️ 布林带极度收口（<8%），面临突破，做好止损", "-1"))
            strength -= 1

    # === 成交量信号 ===
    vol_ma5 = indicators.get("Volume_MA5", 0)
    # 注意：volume 是万股，要乘以10000转成股
    vol_today = indicators.get("today", {}).get("volume", 0)
    if vol_today > vol_ma5 * 1.5 and strength > 0:
        signals.append(("✅ 放量上涨（量能>1.5倍均量），量价配合良好", "+1"))
        strength += 1
    elif vol_today > vol_ma5 * 2 and strength < 0:
        signals.append(("⚠️ 放量下跌（量能>2倍均量），抛压沉重", "-1"))
        strength -= 1
    elif vol_today < vol_ma5 * 0.5 and abs(strength) < 2:
        signals.append(("➡️ 缩量整理，观望等待方向确认", "0"))
        # strength += 0（中性）

    # === 综合信号判定 ===
    if strength >= 3:
        signal_type = "BUY"
        confidence = min(95, 50 + strength * 10)
    elif strength <= -3:
        signal_type = "SELL"
        confidence = min(95, 50 + abs(strength) * 10)
    elif strength >= 1:
        signal_type = "BUY"
        confidence = 50 + strength * 8
    elif strength <= -1:
        signal_type = "SELL"
        confidence = 50 + abs(strength) * 8
    else:
        signal_type = "HOLD"
        confidence = 50

    # 价值投资原则：超跌不追高，价值与趋势结合
    # 如果估值很低（pe < 行业pe*0.7），降低卖出信号强度
    # 如果估值很高（pe > 行业pe*1.5），降低买入信号强度

    return {
        "signal": signal_type,
        "confidence": round(confidence, 1),
        "strength": strength,
        "signals": signals,
        "technical_score": round(50 + strength * 8, 1),  # 技术面评分 0-100
    }


def backtest(klines: list, strategy: str = "ma_cross") -> dict:
    """
    回测策略表现
    strategy: ma_cross(MACD金叉死叉) | rsi_reversal(RSI超买超卖) | bollinger(布林带)
    """
    if not klines or len(klines) < 60:
        return {"error": "insufficient_klines"}

    trades = []
    position = None  # {"date": ..., "price": ..., "type": "BUY"}
    wins = 0
    losses = 0
    total_profit = 0

    closes = [k["close"] for k in klines]
    n = len(klines)

    # 计算指标序列（用于回测）
    ma5 = _sma(closes, 5)
    ma10 = _sma(closes, 10)
    ma20 = _sma(closes, 20)

    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    dif = []
    dea = []
    macd_hist_list = []
    for i in range(n):
        if ema12[i] is None or ema26[i] is None:
            dif.append(None); dea.append(None); macd_hist_list.append(None)
        else:
            d = round(ema12[i] - ema26[i], 3)
            dif.append(d)
            dea.append(round(d * 0.2 + (dea[i-1] or d) * 0.8, 3) if i > 0 else d)
            macd_hist_list.append(round((d - dea[-1]) * 2, 3))

    rsi12 = [None] * n
    gains = []
    for i in range(1, n):
        gains.append(max(closes[i] - closes[i-1], 0))
        if i >= 12:
            avg_gain = sum(gains[i-12:i]) / 12
            avg_loss = sum(max(closes[j-1] - closes[j], 0) for j in range(i-11, i+1)) / 12
            rsi12[i] = 100 if avg_loss == 0 else round(100 - 100 / (1 + avg_gain / (avg_loss or 1)), 2)

    # === 回测信号 ===
    for i in range(20, n):
        date = klines[i]["date"]
        price = klines[i]["close"]
        vol = klines[i]["volume"]

        # 均线金叉/死叉
        ma_cross_buy = (ma5[i] and ma10[i] and ma20[i] and
                        ma5[i] > ma10[i] > ma20[i] and
                        ma5[i-1] <= ma10[i-1])
        ma_cross_sell = (ma5[i] and ma10[i] and ma20[i] and
                          ma5[i] < ma10[i] < ma20[i] and
                          ma5[i-1] >= ma10[i-1])

        # MACD 金叉/死叉
        macd_cross_buy = (dif[i] and dea[i] and dif[i-1] is not None and dea[i-1] is not None and
                           dif[i] > dea[i] and dif[i-1] <= dea[i-1] and dif[i] > 0)
        macd_cross_sell = (dif[i] and dea[i] and dif[i-1] is not None and dea[i-1] is not None and
                            dif[i] < dea[i] and dif[i-1] >= dea[i-1] and dif[i] < 0)

        # RSI 超买超卖
        rsi_buy = (rsi12[i] is not None and rsi12[i] < 35)
        rsi_sell = (rsi12[i] is not None and rsi12[i] > 70)

        # 布林带
        bb_period = 20
        if i >= bb_period:
            window = closes[i - bb_period + 1:i + 1]
            middle = sum(window) / bb_period
            import math
            std = math.sqrt(sum((x - middle) ** 2 for x in window) / bb_period)
            lower = middle - 2 * std
            upper = middle + 2 * std
            bb_buy = price < lower
            bb_sell = price > upper
        else:
            bb_buy = bb_sell = False

        if strategy == "ma_cross":
            buy_signal = ma_cross_buy
            sell_signal = ma_cross_sell
        elif strategy == "macd_cross":
            buy_signal = macd_cross_buy
            sell_signal = macd_cross_sell
        elif strategy == "rsi_reversal":
            buy_signal = rsi_buy
            sell_signal = rsi_sell
        elif strategy == "bollinger":
            buy_signal = bb_buy
            sell_signal = bb_sell
        elif strategy == "combo":
            # 综合：至少2个指标同时看多/看空
            buy_count = int(bool(ma_cross_buy)) + int(bool(macd_cross_buy)) + int(bool(rsi_buy)) + int(bool(bb_buy))
            sell_count = int(bool(ma_cross_sell)) + int(bool(macd_cross_sell)) + int(bool(rsi_sell)) + int(bool(bb_sell))
            buy_signal = buy_count >= 2
            sell_signal = sell_count >= 2
        else:
            buy_signal = sell_signal = False

        if not position and buy_signal:
            position = {"date": date, "price": price}
            trades.append({"type": "BUY", "date": date, "price": price})
        elif position and sell_signal:
            buy_price = position["price"]
            profit_pct = (price - buy_price) / buy_price * 100
            total_profit += profit_pct
            if profit_pct > 0:
                wins += 1
            else:
                losses += 1
            trades.append({"type": "SELL", "date": date, "price": price, "profit_pct": round(profit_pct, 2)})
            position = None

    # 如果最后还有持仓，按最后价格平仓（不计入统计）
    if position:
        final_price = closes[-1]
        profit_pct = (final_price - position["price"]) / position["price"] * 100
        trades.append({"type": "CLOSE", "date": klines[-1]["date"], "price": final_price,
                       "profit_pct": round(profit_pct, 2), "note": "期末平仓"})
        total_profit += profit_pct
        if profit_pct > 0: wins += 1
        else: losses += 1

    total_trades = wins + losses
    win_rate = round(wins / total_trades * 100, 1) if total_trades > 0 else 0

    # 计算最大回撤
    max_drawdown = 0
    peak = 0
    equity = 0
    for t in trades:
        if t["type"] == "BUY":
            equity = 100  # 重置
            peak = 100
        elif t["type"] in ("SELL", "CLOSE"):
            equity = equity * (1 + t["profit_pct"] / 100)
            peak = max(peak, equity)
            dd = (peak - equity) / peak * 100 if peak > 0 else 0
            max_drawdown = max(max_drawdown, dd)

    # 年化（假设日线，约250个交易日）
    years = n / 250
    annualized = round(total_profit / years, 2) if years > 0 else total_profit

    return {
        "strategy": strategy,
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_return": round(total_profit, 2),
        "annualized_return": annualized,
        "max_drawdown": round(max_drawdown, 2),
        "period_days": n,
        "period_years": round(years, 1),
        "avg_profit_per_trade": round(total_profit / total_trades, 2) if total_trades > 0 else 0,
        "recent_trades": trades[-10:] if len(trades) > 10 else trades,
    }


if __name__ == "__main__":
    # 测试贵州茅台
    code = "600519"
    print(f"📊 技术分析回测: {code}")

    kline_data = get_kline_data(code, count=250)
    if kline_data.get("error"):
        print(f"  错误: {kline_data['error']}")
    else:
        klines = kline_data["klines"]
        print(f"  K线数据: {len(klines)} 条")

        ta = calculate_indicators(klines)
        ind = ta["indicators"]
        today = ta["today"]
        print(f"\n  📌 最新日期: {today['date']}  收盘: ¥{today['close']} ({today['change_pct']:+.2f}%)")
        print(f"  MA: 5={ind['MA5']} 10={ind['MA10']} 20={ind['MA20']} 60={ind['MA60']}")
        print(f"  MACD: DIF={ind['DIF']} DEA={ind['DEA']} MACD柱={ind['MACD']}")
        print(f"  RSI: 6={ind['RSI6']} 12={ind['RSI12']} 24={ind['RSI24']}")
        print(f"  KDJ: K={ind['KDJ_K']} D={ind['KDJ_D']} J={ind['KDJ_J']}")
        print(f"  布林带: 上={ind['BB_Upper']} 中={ind['BB_Middle']} 下={ind['BB_Lower']}")

        sig = generate_buy_sell_signals(ind, today['close'], ta.get('ma_distances', {}))
        print(f"\n  📈 技术信号: {sig['signal']} (置信度 {sig['confidence']}%)")
        print(f"  信号明细:")
        for text, weight in sig["signals"]:
            print(f"    {text} [{weight}]")

        print(f"\n  📉 回测结果 (综合策略):")
        bt = backtest(klines, "combo")
        print(f"    总交易次数: {bt['total_trades']}  胜率: {bt['win_rate']}%")
        print(f"    总收益率: {bt['total_return']}%  年化: {bt['annualized_return']}%")
        print(f"    最大回撤: {bt['max_drawdown']}%")
        print(f"    近10笔交易: {bt['recent_trades'][:5]}")
