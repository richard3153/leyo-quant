#!/usr/bin/env python3
"""
风险管理系统（本地替代版）
持仓管理与风控检查
"""

import json
from pathlib import Path
from typing import Optional


class Portfolio:
    """模拟投资组合"""
    
    def __init__(self, cash: float = 1000000):
        self.cash = cash
        self.positions = {}  # code -> Position
    
    def load_from_file(self, filepath: str):
        """从文件加载持仓"""
        path = Path(filepath)
        if not path.exists():
            return
        with open(path) as f:
            data = json.load(f)
        self.cash = data.get("cash", 1000000)
        self.positions = {}
        for pos in data.get("positions", []):
            code = pos.get("code", "")
            self.positions[code] = Position(
                code=code,
                name=pos.get("name", ""),
                shares=pos.get("shares", 0),
                avg_cost=pos.get("avg_cost", 0),
                current_price=pos.get("current_price", pos.get("avg_cost", 0)),
            )
    
    def save_to_file(self, filepath: str):
        """保存持仓到文件"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "cash": self.cash,
            "positions": [
                {
                    "code": p.code,
                    "name": p.name,
                    "shares": p.shares,
                    "avg_cost": p.avg_cost,
                    "current_price": p.current_price,
                    "market_value": p.market_value,
                    "pnl_pct": p.pnl_pct,
                    "pnl_amount": p.pnl_amount,
                }
                for p in self.positions.values()
            ],
            "total_value": self.get_total_value()
        }
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_position(self, code: str, name: str, shares: int, avg_cost: float, current_price: float):
        """添加或更新持仓"""
        if code in self.positions:
            # 加仓：重新计算平均成本
            old = self.positions[code]
            total_shares = old.shares + shares
            total_cost = old.shares * old.avg_cost + shares * avg_cost
            new_avg_cost = total_cost / total_shares if total_shares > 0 else avg_cost
            self.positions[code] = Position(code, name, total_shares, new_avg_cost, current_price)
        else:
            self.positions[code] = Position(code, name, shares, avg_cost, current_price)
    
    def remove_position(self, code: str):
        """删除持仓"""
        if code in self.positions:
            del self.positions[code]
    
    def get_total_value(self) -> float:
        """计算总市值"""
        total = self.cash
        for p in self.positions.values():
            total += p.market_value
        return total
    
    def get_position(self, code: str):
        return self.positions.get(code)


class Position:
    """单个持仓"""
    
    def __init__(self, code: str, name: str, shares: int, avg_cost: float, current_price: float):
        self.code = code
        self.name = name
        self.shares = shares
        self.avg_cost = avg_cost
        self.current_price = current_price
        self.market_value = shares * current_price
        self.pnl_amount = (current_price - avg_cost) * shares
        self.pnl_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0


def check_portfolio_risk(portfolio: Portfolio) -> dict:
    """检查组合风险"""
    if not portfolio.positions:
        return {
            "status": "ok",
            "risk_level": "low",
            "message": "无持仓，无需风控检查",
            "total_value": portfolio.cash,
            "cash": portfolio.cash,
            "positions_value": 0,
            "cash_ratio": 100,
        }
    
    total_value = portfolio.get_total_value()
    positions_value = total_value - portfolio.cash
    cash_ratio = portfolio.cash / total_value * 100
    
    # 单只股票集中度
    max_concentration = 0
    max_stock = ""
    for p in portfolio.positions.values():
        conc = p.market_value / total_value * 100
        if conc > max_concentration:
            max_concentration = conc
            max_stock = f"{p.name}({p.code})"
    
    # 单只亏损
    losers = [p for p in portfolio.positions.values() if p.pnl_pct < -10]
    
    # 整体盈利/亏损
    total_pnl = sum(p.pnl_amount for p in portfolio.positions.values())
    
    risk_level = "low"
    if max_concentration > 40 or cash_ratio < 10:
        risk_level = "high"
    elif max_concentration > 25 or cash_ratio < 20:
        risk_level = "medium"
    
    return {
        "status": "ok",
        "risk_level": risk_level,
        "total_value": round(total_value, 2),
        "cash": round(portfolio.cash, 2),
        "positions_value": round(positions_value, 2),
        "cash_ratio": round(cash_ratio, 2),
        "max_concentration": round(max_concentration, 2),
        "max_stock": max_stock,
        "total_pnl": round(total_pnl, 2),
        "losers_count": len(losers),
        "losers": [{"code": p.code, "name": p.name, "pnl_pct": round(p.pnl_pct, 2)} for p in losers[:5]],
        "position_count": len(portfolio.positions),
    }


def check_buy(portfolio: Portfolio, code: str, price: float, amount: float = 100000) -> dict:
    """买入风控检查"""
    max_single = portfolio.get_total_value() * 0.2  # 单只不超过20%
    
    if amount > max_single:
        return {
            "status": "warning",
            "message": f"单笔买入 {amount:.0f} 元超过限制 ({max_single:.0f} 元，20%上限)",
            "suggest_amount": max_single,
            "passed": False
        }
    
    if portfolio.cash < amount:
        return {
            "status": "warning",
            "message": f"现金不足，需要 {amount:.0f} 元，当前现金 {portfolio.cash:.0f} 元",
            "suggest_amount": portfolio.cash,
            "passed": False
        }
    
    # 集中度检查
    shares = int(amount / price)
    new_position_value = shares * price
    total = portfolio.get_total_value()
    new_concentration = new_position_value / total * 100
    
    if new_concentration > 30:
        return {
            "status": "warning",
            "message": f"买入后集中度 {new_concentration:.1f}% 超过30%警戒线",
            "concentration_after": round(new_concentration, 2),
            "passed": False
        }
    
    return {
        "status": "ok",
        "message": "风控检查通过",
        "shares": shares,
        "amount": shares * price,
        "concentration_after": round(new_concentration, 2),
        "passed": True
    }
