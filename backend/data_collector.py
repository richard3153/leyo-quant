#!/usr/bin/env python3
"""
数据采集模块（本地替代版）
整合 financial_data + realtime_quote 的数据
"""

from financial_data import get_financial_data
from realtime_quote import get_realtime_price


def load_company_data(code: str) -> dict:
    """
    获取公司综合数据
    返回：基础信息 + 财务指标 + 实时价格
    """
    # 获取财务数据
    fin = get_financial_data(code)
    if fin.get("error"):
        # 财务数据获取失败时，至少返回价格信息
        rt = get_realtime_price(code)
        if rt.get("status") == "success":
            return {
                "code": code,
                "name": rt.get("name", ""),
                "price": rt.get("current_price", 0),
                "prev_close": rt.get("prev_close", 0),
                "change_pct": rt.get("change_pct", 0),
                "roe": 0,
                "revenue_growth": 0,
                "profit_growth": 0,
                "gross_margin": 0,
                "debt_ratio": 0,
                "eps": 0,
                "bps": 0,
                "source": "fallback"
            }
        return {
            "code": code,
            "price": 0,
            "roe": 0,
            "revenue_growth": 0,
            "profit_growth": 0,
            "gross_margin": 0,
            "debt_ratio": 0,
            "eps": 0,
            "source": "error",
            "error": fin.get("error")
        }
    
    # 获取实时价格
    rt = get_realtime_price(code)
    current_price = rt.get("current_price", 0) if rt.get("status") == "success" else 0
    
    return {
        "code": code,
        "name": fin.get("name", rt.get("name", "")),
        "price": current_price,
        "prev_close": rt.get("prev_close", 0) if rt.get("status") == "success" else 0,
        "change_pct": rt.get("change_pct", 0) if rt.get("status") == "success" else 0,
        "roe": fin.get("roe", 0),
        "revenue_growth": fin.get("revenue_growth", 0),
        "profit_growth": fin.get("profit_growth", 0),
        "gross_margin": fin.get("gross_margin", 0),
        "net_margin": fin.get("net_margin", 0),
        "debt_ratio": fin.get("debt_ratio", 0),
        "eps": fin.get("eps", 0),
        "bps": fin.get("bps", 0),
        "total_revenue": fin.get("total_revenue", 0),
        "net_profit": fin.get("net_profit", 0),
        "report_date": fin.get("report_date", ""),
        "report_type": fin.get("report_type", ""),
        "source": "eastmoney",
        "fetch_time": fin.get("fetch_time", "")
    }
