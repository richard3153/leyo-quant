#!/usr/bin/env python3
"""
交易信号生成模块（本地替代版）
基于技术分析 + 财务评分综合判断
"""

from datetime import datetime


def generate_signal(code: str, data: dict) -> dict:
    """
    生成交易信号
    data: load_company_data 返回的数据
    返回: {signal, name, score, confidence, reasons}
    """
    reasons = []
    score = 50  # 基础分
    
    # === 财务面评分 ===
    roe = data.get("roe", 0)
    rev_growth = data.get("revenue_growth", 0)
    profit_growth = data.get("profit_growth", 0)
    gross_margin = data.get("gross_margin", 0)
    debt_ratio = data.get("debt_ratio", 0)
    eps = data.get("eps", 0)
    price = data.get("price", 0)
    change_pct = data.get("change_pct", 0)
    
    # ROE 评分
    if roe >= 20:
        score += 15
        reasons.append(f"ROE {roe:.1f}% 极高，盈利能力突出")
    elif roe >= 15:
        score += 10
        reasons.append(f"ROE {roe:.1f}% 优秀")
    elif roe >= 10:
        score += 5
        reasons.append(f"ROE {roe:.1f}% 良好")
    elif roe > 0:
        pass  # 不加减分
    else:
        score -= 10
        reasons.append(f"ROE 为负，盈利能力弱")
    
    # 营收增长
    if rev_growth >= 20:
        score += 10
        reasons.append(f"营收增长 {rev_growth:.1f}%，成长性极佳")
    elif rev_growth >= 10:
        score += 6
        reasons.append(f"营收增长 {rev_growth:.1f}%，成长良好")
    elif rev_growth >= 0:
        score += 2
    elif rev_growth >= -10:
        score -= 5
        reasons.append(f"营收下滑 {abs(rev_growth):.1f}%")
    else:
        score -= 10
        reasons.append(f"营收大幅下滑 {abs(rev_growth):.1f}%")
    
    # 净利润增长
    if profit_growth >= 20:
        score += 10
        reasons.append(f"净利润增长 {profit_growth:.1f}%")
    elif profit_growth >= 10:
        score += 6
    elif profit_growth >= 0:
        score += 2
    elif profit_growth >= -10:
        score -= 5
    else:
        score -= 10
        reasons.append(f"净利润下滑 {abs(profit_growth):.1f}%")
    
    # 毛利率（护城河）
    if gross_margin >= 50:
        score += 8
        reasons.append(f"毛利率 {gross_margin:.1f}%，护城河深厚")
    elif gross_margin >= 30:
        score += 5
        reasons.append(f"毛利率 {gross_margin:.1f}%，竞争力强")
    elif gross_margin > 0:
        score += 1
    else:
        score -= 5
    
    # 资产负债率
    if debt_ratio <= 30:
        score += 5
        reasons.append(f"资产负债率 {debt_ratio:.1f}%，财务稳健")
    elif debt_ratio <= 50:
        score += 3
    elif debt_ratio <= 70:
        pass
    else:
        score -= 5
        reasons.append(f"资产负债率 {debt_ratio:.1f}%，债务偏高")
    
    # 每股收益
    if eps >= 3:
        score += 5
        reasons.append(f"EPS {eps:.2f} 元，回报丰厚")
    elif eps >= 1:
        score += 3
    elif eps > 0:
        score += 1
    else:
        score -= 5
        reasons.append("EPS 为负，亏损状态")
    
    # === 价格动量 ===
    if change_pct > 3:
        score -= 3
        reasons.append(f"今日涨幅 {change_pct:.1f}%，追高需谨慎")
    elif change_pct < -3:
        score += 3
        reasons.append(f"今日下跌 {change_pct:.1f}%，可能存在机会")
    
    # 限制分数范围
    score = max(0, min(100, score))
    
    # === 综合信号判定 ===
    if score >= 75:
        signal = "BUY"
        name = "强烈买入"
        confidence = min(90, score + 5)
    elif score >= 60:
        signal = "BUY"
        name = "建议买入"
        confidence = min(80, score)
    elif score >= 45:
        signal = "HOLD"
        name = "持有观望"
        confidence = 55
    elif score >= 30:
        signal = "SELL"
        name = "建议卖出"
        confidence = min(80, 100 - score)
    else:
        signal = "SELL"
        name = "强烈卖出"
        confidence = min(90, 100 - score + 5)
    
    return {
        "signal": signal,
        "name": name,
        "score": score,
        "confidence": round(confidence, 1),
        "reasons": reasons,
        "timestamp": datetime.now().isoformat()
    }
