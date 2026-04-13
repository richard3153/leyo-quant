#!/usr/bin/env python3
"""
真实财务数据获取模块
数据来源：东方财富 (emweb.securities.eastmoney.com)
"""

import urllib.request
import json
from datetime import datetime
import time


def get_financial_data(code: str) -> dict:
    """
    从东方财富获取股票真实财务数据
    返回：营收增速、净利润增速、ROE、毛利率、资产负债率、每股收益等
    """
    # 确定市场前缀
    if code.startswith('6'):
        mkt = 'SH'
    else:
        mkt = 'SZ'
    
    url = f"https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew?type=0&code={mkt}{code}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://emweb.securities.eastmoney.com',
        'Accept-Encoding': 'identity'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = json.loads(response.read())
            
            if not raw.get('data') or len(raw['data']) == 0:
                return {"error": "no_data", "code": code}
            
            # 取最新一期财务数据
            d = raw['data'][0]
            
            # 处理 None 值
            def safe(val, default=0):
                return val if val is not None else default
            
            return {
                "code": code,
                "name": d.get('SECURITY_NAME_ABBR', ''),
                "report_date": str(d.get('REPORT_DATE', ''))[:10],
                "report_type": d.get('REPORT_DATE_NAME', ''),
                
                # 成长性指标（保留2位小数）
                "revenue_growth": round(safe(d.get('TOTALOPERATEREVETZ', 0)), 2),
                "profit_growth": round(safe(d.get('PARENTNETPROFITTZ', 0)), 2),
                
                # 盈利能力
                "roe": round(safe(d.get('ROEJQ', 0)), 2),
                "gross_margin": round(safe(d.get('XSMLL', 0)), 2),
                "net_margin": round(safe(d.get('XSJLL', 0)), 2),
                
                # 财务结构
                "debt_ratio": round(safe(d.get('ZCFZL', 0)), 2),
                
                # 每股指标
                "eps": round(safe(d.get('EPSJB', 0)), 2),
                "bps": round(safe(d.get('BPS', 0)), 2),
                
                # 运营能力
                "total_revenue": round(safe(d.get('TOTALOPERATEREVE', 0)), 2),
                "net_profit": round(safe(d.get('PARENTNETPROFIT', 0)), 2),
                "gross_profit": round(safe(d.get('MLR', 0)), 2),
                
                # 现金流
                "cash_flow_ratio": round(safe(d.get('XJLLB', 0)), 2),
                
                # 更新状态
                "status": "success",
                "fetch_time": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {"error": str(e), "code": code}


def get_batch_financial(codes: list) -> dict:
    """批量获取财务数据（带速率限制）"""
    results = {}
    for code in codes:
        result = get_financial_data(code)
        results[code] = result
        time.sleep(0.3)  # 避免请求过快
    return results


def get_valuation(code: str) -> dict:
    """
    获取实时估值数据（PE、PB）
    使用新浪财经接口
    """
    import re
    
    if code.startswith('6'):
        full_code = "sh" + code
    else:
        full_code = "sz" + code
    
    url = f"http://hq.sinajs.cn/list={full_code}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'http://finance.sina.com.cn'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode('gbk')
            pattern = 'hq_str_' + full_code + '="(.+?)"'
            match = re.search(pattern, content)
            
            if not match:
                return {"error": "not_found", "code": code}
            
            data = match.group(1).split(',')
            if len(data) < 32:
                return {"error": "data_error", "code": code}
            
            # 新浪数据中的估值字段（第57-58位左右）
            current_price = float(data[3]) if data[3] else 0
            prev_close = float(data[2]) if data[2] else 0
            
            return {
                "code": code,
                "current_price": current_price,
                "prev_close": prev_close,
                "status": "success"
            }
    except Exception as e:
        return {"error": str(e), "code": code}


def score_from_financial(fin_data: dict) -> dict:
    """
    基于真实财务数据计算评分
    参考价值投资理念
    """
    if fin_data.get("error"):
        return {"error": fin_data["error"], "total_score": 0}
    
    scores = {}
    reasons = []
    
    # 1. ROE 评分 (25分) - 盈利能力核心指标
    roe = fin_data.get("roe", 0)
    if roe >= 20:
        scores["roe"] = 25
        reasons.append(f"ROE高达{roe:.1f}%，盈利能力极强")
    elif roe >= 15:
        scores["roe"] = 20
        reasons.append(f"ROE {roe:.1f}%，盈利能力优秀")
    elif roe >= 10:
        scores["roe"] = 12
        reasons.append(f"ROE {roe:.1f}%，盈利能力良好")
    elif roe >= 5:
        scores["roe"] = 6
        reasons.append(f"ROE {roe:.1f}%，盈利能力一般")
    else:
        scores["roe"] = 0
        reasons.append(f"ROE {roe:.1f}%，盈利能力较弱")
    
    # 2. 营收增速 (20分) - 成长性
    rev_growth = fin_data.get("revenue_growth", 0)
    if rev_growth >= 20:
        scores["revenue_growth"] = 20
        reasons.append(f"营收增长{rev_growth:.1f}%，成长性极佳")
    elif rev_growth >= 10:
        scores["revenue_growth"] = 16
        reasons.append(f"营收增长{rev_growth:.1f}%，成长性良好")
    elif rev_growth >= 0:
        scores["revenue_growth"] = 10
        reasons.append(f"营收增长{rev_growth:.1f}%，保持增长")
    elif rev_growth >= -10:
        scores["revenue_growth"] = 4
        reasons.append(f"营收下降{abs(rev_growth):.1f}%，需关注")
    else:
        scores["revenue_growth"] = 0
        reasons.append(f"营收下降{abs(rev_growth):.1f}%，经营承压")
    
    # 3. 净利润增速 (20分) - 成长性核心
    profit_growth = fin_data.get("profit_growth", 0)
    if profit_growth >= 20:
        scores["profit_growth"] = 20
        reasons.append(f"净利润增长{profit_growth:.1f}%，盈利能力强")
    elif profit_growth >= 10:
        scores["profit_growth"] = 16
        reasons.append(f"净利润增长{profit_growth:.1f}%，盈利良好")
    elif profit_growth >= 0:
        scores["profit_growth"] = 10
        reasons.append(f"净利润增长{profit_growth:.1f}%，盈利稳定")
    elif profit_growth >= -10:
        scores["profit_growth"] = 4
        reasons.append(f"净利润下降{abs(profit_growth):.1f}%，盈利承压")
    else:
        scores["profit_growth"] = 0
        reasons.append(f"净利润下降{abs(profit_growth):.1f}%，盈利下滑")
    
    # 4. 毛利率 (15分) - 护城河指标
    gross_margin = fin_data.get("gross_margin", 0)
    if gross_margin >= 50:
        scores["gross_margin"] = 15
        reasons.append(f"毛利率{gross_margin:.1f}%，具有定价权")
    elif gross_margin >= 30:
        scores["gross_margin"] = 12
        reasons.append(f"毛利率{gross_margin:.1f}%，竞争力较强")
    elif gross_margin >= 15:
        scores["gross_margin"] = 8
        reasons.append(f"毛利率{gross_margin:.1f}%，一般水平")
    elif gross_margin > 0:
        scores["gross_margin"] = 4
        reasons.append(f"毛利率{gross_margin:.1f}%，偏低")
    else:
        scores["gross_margin"] = 0
        reasons.append("毛利率数据缺失")
    
    # 5. 资产负债率 (10分) - 财务健康
    debt_ratio = fin_data.get("debt_ratio", 0)
    if debt_ratio <= 30:
        scores["debt_ratio"] = 10
        reasons.append(f"资产负债率{debt_ratio:.1f}%，财务稳健")
    elif debt_ratio <= 50:
        scores["debt_ratio"] = 8
        reasons.append(f"资产负债率{debt_ratio:.1f}%，财务健康")
    elif debt_ratio <= 70:
        scores["debt_ratio"] = 5
        reasons.append(f"资产负债率{debt_ratio:.1f}%，尚可接受")
    else:
        scores["debt_ratio"] = 0
        reasons.append(f"资产负债率{debt_ratio:.1f}%，债务压力较大")
    
    # 6. 每股收益 (10分) - 股东回报
    eps = fin_data.get("eps", 0)
    if eps >= 5:
        scores["eps"] = 10
        reasons.append(f"每股收益{eps:.2f}元，回报丰厚")
    elif eps >= 2:
        scores["eps"] = 7
        reasons.append(f"每股收益{eps:.2f}元，回报良好")
    elif eps >= 0.5:
        scores["eps"] = 4
        reasons.append(f"每股收益{eps:.2f}元，回报一般")
    elif eps > 0:
        scores["eps"] = 2
        reasons.append(f"每股收益{eps:.2f}元，盈利微薄")
    else:
        scores["eps"] = 0
        reasons.append("每股收益为负，亏损状态")
    
    # 计算总分
    total_score = sum(scores.values())
    
    # 评级
    if total_score >= 85:
        rating = "A+ 优秀"
    elif total_score >= 70:
        rating = "A 良好"
    elif total_score >= 55:
        rating = "B+ 合格"
    elif total_score >= 40:
        rating = "B 一般"
    else:
        rating = "C 较差"
    
    return {
        "total_score": round(total_score, 1),
        "rating": rating,
        "scores": scores,
        "reasons": reasons,
        "financial_data": {
            "roe": roe,
            "revenue_growth": rev_growth,
            "profit_growth": profit_growth,
            "gross_margin": gross_margin,
            "debt_ratio": debt_ratio,
            "eps": eps,
            "report_date": fin_data.get("report_date", ""),
            "report_type": fin_data.get("report_type", "")
        }
    }


if __name__ == "__main__":
    test_codes = ["600519", "000858", "601318", "600036", "000651", "002594"]
    
    print("=" * 60)
    print("乐友量化投资系统 - 真实财务数据评分")
    print("=" * 60)
    
    for code in test_codes:
        print(f"\n获取 {code} 财务数据...")
        fin = get_financial_data(code)
        
        if fin.get("error"):
            print(f"  错误: {fin['error']}")
            continue
        
        result = score_from_financial(fin)
        
        print(f"  股票: {fin.get('name', '')} ({code})")
        print(f"  报告期: {fin.get('report_type', '')} ({fin.get('report_date', '')})")
        print(f"  ROE: {fin.get('roe', 0):.2f}% | 营收增速: {fin.get('revenue_growth', 0):.2f}% | 净利润增速: {fin.get('profit_growth', 0):.2f}%")
        print(f"  毛利率: {fin.get('gross_margin', 0):.2f}% | 资产负债率: {fin.get('debt_ratio', 0):.2f}% | 每股收益: {fin.get('eps', 0):.2f}")
        print(f"  ─────────────────────────────────")
        print(f"  综合评分: {result['total_score']} 分 ({result['rating']})")
        for r in result['reasons']:
            print(f"    ✓ {r}")
