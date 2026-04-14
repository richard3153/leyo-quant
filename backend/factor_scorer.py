#!/usr/bin/env python3
"""
因子评分模块（本地替代版）
基于 financial_data.score_from_financial 封装
"""

from financial_data import get_financial_data, score_from_financial


def calculate_total_score(data: dict) -> dict:
    """
    计算综合评分
    data: load_company_data 返回的数据
    返回: {total_score, rating, scores, reasons, financial_data}
    """
    code = data.get("code", "")
    
    # 如果数据中已有 source=eastmoney，直接用 financial_data 评分
    if data.get("source") == "eastmoney":
        fin_data = {
            "code": code,
            "roe": data.get("roe", 0),
            "revenue_growth": data.get("revenue_growth", 0),
            "profit_growth": data.get("profit_growth", 0),
            "gross_margin": data.get("gross_margin", 0),
            "debt_ratio": data.get("debt_ratio", 0),
            "eps": data.get("eps", 0),
            "report_date": data.get("report_date", ""),
            "report_type": data.get("report_type", ""),
        }
        return score_from_financial(fin_data)
    
    # fallback: 重新获取财务数据评分
    if code:
        fin = get_financial_data(code)
        if not fin.get("error"):
            return score_from_financial(fin)
    
    return {
        "total_score": 0,
        "rating": "C 较差",
        "scores": {},
        "reasons": ["财务数据不可用"],
        "financial_data": {}
    }
