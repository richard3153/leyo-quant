"""
乐友量化系统 - FastAPI 后端
"""

from fastapi import FastAPI, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
from pathlib import Path
from typing import List

app = FastAPI(title="乐友量化投资系统", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 本地模块路径（与 main.py 同目录）
BACKEND_DIR = Path(__file__).parent

# ─── 股票池 (仅A股) ────────────────────────────────────────

STOCK_POOL = [
    {"code": "600519", "name": "贵州茅台", "market": "A", "industry": "白酒"},
    {"code": "000858", "name": "五粮液", "market": "A", "industry": "白酒"},
    {"code": "000568", "name": "泸州老窖", "market": "A", "industry": "白酒"},
    {"code": "002304", "name": "洋河股份", "market": "A", "industry": "白酒"},
    {"code": "000799", "name": "酒鬼酒", "market": "A", "industry": "白酒"},
    {"code": "603369", "name": "今世缘", "market": "A", "industry": "白酒"},
    {"code": "000596", "name": "古井贡酒", "market": "A", "industry": "白酒"},
    {"code": "600809", "name": "山西汾酒", "market": "A", "industry": "白酒"},
    {"code": "600036", "name": "招商银行", "market": "A", "industry": "银行"},
    {"code": "000001", "name": "平安银行", "market": "A", "industry": "银行"},
    {"code": "601166", "name": "兴业银行", "market": "A", "industry": "银行"},
    {"code": "600000", "name": "浦发银行", "market": "A", "industry": "银行"},
    {"code": "601398", "name": "工商银行", "market": "A", "industry": "银行"},
    {"code": "601288", "name": "农业银行", "market": "A", "industry": "银行"},
    {"code": "601939", "name": "建设银行", "market": "A", "industry": "银行"},
    {"code": "601328", "name": "交通银行", "market": "A", "industry": "银行"},
    {"code": "600016", "name": "民生银行", "market": "A", "industry": "银行"},
    {"code": "601318", "name": "中国平安", "market": "A", "industry": "保险"},
    {"code": "601601", "name": "中国太保", "market": "A", "industry": "保险"},
    {"code": "601628", "name": "中国人寿", "market": "A", "industry": "保险"},
    {"code": "601336", "name": "新华保险", "market": "A", "industry": "保险"},
    {"code": "600900", "name": "长江电力", "market": "A", "industry": "水电"},
    {"code": "600028", "name": "中国石化", "market": "A", "industry": "石化"},
    {"code": "601857", "name": "中国石油", "market": "A", "industry": "石油"},
    {"code": "600019", "name": "宝钢股份", "market": "A", "industry": "钢铁"},
    {"code": "601600", "name": "中国铝业", "market": "A", "industry": "有色金属"},
    {"code": "000333", "name": "美的集团", "market": "A", "industry": "家电"},
    {"code": "000651", "name": "格力电器", "market": "A", "industry": "家电"},
    {"code": "600690", "name": "海尔智家", "market": "A", "industry": "家电"},
    {"code": "002050", "name": "三花智控", "market": "A", "industry": "家电"},
    {"code": "000404", "name": "长虹美菱", "market": "A", "industry": "家电"},
    {"code": "002242", "name": "九阳股份", "market": "A", "industry": "家电"},
    {"code": "600887", "name": "伊利股份", "market": "A", "industry": "乳业"},
    {"code": "000895", "name": "双汇发展", "market": "A", "industry": "肉制品"},
    {"code": "603288", "name": "海天味业", "market": "A", "industry": "调味品"},
    {"code": "002507", "name": "涪陵榨菜", "market": "A", "industry": "食品加工"},
    {"code": "300146", "name": "汤臣倍健", "market": "A", "industry": "保健品"},
    {"code": "603517", "name": "绝味食品", "market": "A", "industry": "食品"},
    {"code": "002329", "name": "皇氏集团", "market": "A", "industry": "乳业"},
    {"code": "600276", "name": "恒瑞医药", "market": "A", "industry": "医药"},
    {"code": "000538", "name": "云南白药", "market": "A", "industry": "中药"},
    {"code": "300760", "name": "迈瑞医疗", "market": "A", "industry": "医疗器械"},
    {"code": "300122", "name": "智飞生物", "market": "A", "industry": "生物疫苗"},
    {"code": "603259", "name": "药明康德", "market": "A", "industry": "医药外包"},
    {"code": "600196", "name": "复星医药", "market": "A", "industry": "医药"},
    {"code": "000661", "name": "长春高新", "market": "A", "industry": "生物制药"},
    {"code": "002007", "name": "华兰生物", "market": "A", "industry": "生物制药"},
    {"code": "300015", "name": "爱尔眼科", "market": "A", "industry": "医疗服务"},
    {"code": "300003", "name": "乐普医疗", "market": "A", "industry": "医疗器械"},
    {"code": "002219", "name": "恒心医疗", "market": "A", "industry": "医疗器械"},
    {"code": "688180", "name": "君实生物", "market": "A", "industry": "生物制药"},
    {"code": "000625", "name": "长安汽车", "market": "A", "industry": "汽车"},
    {"code": "002594", "name": "比亚迪", "market": "A", "industry": "新能源车"},
    {"code": "601633", "name": "长城汽车", "market": "A", "industry": "汽车"},
    {"code": "600104", "name": "上汽集团", "market": "A", "industry": "汽车"},
    {"code": "601238", "name": "广汽集团", "market": "A", "industry": "汽车"},
    {"code": "000572", "name": "海马汽车", "market": "A", "industry": "汽车"},
    {"code": "600166", "name": "福田汽车", "market": "A", "industry": "汽车"},
    {"code": "002126", "name": "银轮股份", "market": "A", "industry": "汽车零部件"},
    {"code": "000002", "name": "万科A", "market": "A", "industry": "房地产"},
    {"code": "001979", "name": "招商蛇口", "market": "A", "industry": "房地产"},
    {"code": "600048", "name": "保利发展", "market": "A", "industry": "房地产"},
    {"code": "600606", "name": "绿地控股", "market": "A", "industry": "房地产"},
    {"code": "001914", "name": "新城控股", "market": "A", "industry": "房地产"},
    {"code": "600383", "name": "金地集团", "market": "A", "industry": "房地产"},
    {"code": "000725", "name": "京东方A", "market": "A", "industry": "面板"},
    {"code": "002475", "name": "立讯精密", "market": "A", "industry": "消费电子"},
    {"code": "600588", "name": "用友网络", "market": "A", "industry": "软件"},
    {"code": "002415", "name": "海康威视", "market": "A", "industry": "安防"},
    {"code": "300750", "name": "宁德时代", "market": "A", "industry": "新能源"},
    {"code": "300496", "name": "中科创达", "market": "A", "industry": "软件"},
    {"code": "002049", "name": "紫光国微", "market": "A", "industry": "半导体"},
    {"code": "688981", "name": "中芯国际", "market": "A", "industry": "半导体"},
    {"code": "603986", "name": "兆易创新", "market": "A", "industry": "半导体"},
    {"code": "002230", "name": "科大讯飞", "market": "A", "industry": "人工智能"},
    {"code": "300033", "name": "同花顺", "market": "A", "industry": "互联网金融"},
    {"code": "002236", "name": "大华股份", "market": "A", "industry": "安防"},
    {"code": "600438", "name": "通威股份", "market": "A", "industry": "光伏"},
    {"code": "601012", "name": "隆基绿能", "market": "A", "industry": "光伏"},
    {"code": "002129", "name": "中环股份", "market": "A", "industry": "光伏"},
    {"code": "300274", "name": "阳光电源", "market": "A", "industry": "光伏"},
    {"code": "601615", "name": "明阳智能", "market": "A", "industry": "风电"},
    {"code": "002459", "name": "晶澳科技", "market": "A", "industry": "光伏"},
    {"code": "600030", "name": "中信证券", "market": "A", "industry": "证券"},
    {"code": "601211", "name": "国泰君安", "market": "A", "industry": "证券"},
    {"code": "600837", "name": "海通证券", "market": "A", "industry": "证券"},
    {"code": "000776", "name": "广发证券", "market": "A", "industry": "证券"},
    {"code": "600999", "name": "招商证券", "market": "A", "industry": "证券"},
    {"code": "601390", "name": "中国中铁", "market": "A", "industry": "基建"},
    {"code": "601668", "name": "中国建筑", "market": "A", "industry": "建筑"},
    {"code": "601186", "name": "中国铁建", "market": "A", "industry": "基建"},
    {"code": "601669", "name": "中国电建", "market": "A", "industry": "基建"},
    {"code": "601618", "name": "中国中冶", "market": "A", "industry": "基建"},
    {"code": "600170", "name": "上海建工", "market": "A", "industry": "建筑"},
    {"code": "002352", "name": "顺丰控股", "market": "A", "industry": "物流"},
    {"code": "601888", "name": "中国中免", "market": "A", "industry": "免税"},
    {"code": "300059", "name": "东方财富", "market": "A", "industry": "互联网金融"},
    {"code": "600109", "name": "国金证券", "market": "A", "industry": "证券"},
    {"code": "002027", "name": "分众传媒", "market": "A", "industry": "传媒"},
    {"code": "601088", "name": "中国神华", "market": "A", "industry": "煤炭"},
    {"code": "601225", "name": "陕西煤业", "market": "A", "industry": "煤炭"},
    {"code": "601899", "name": "紫金矿业", "market": "A", "industry": "有色金属"},
    {"code": "600547", "name": "山东黄金", "market": "A", "industry": "黄金"},
    {"code": "000630", "name": "铜陵有色", "market": "A", "industry": "有色金属"},
    {"code": "600111", "name": "北方稀土", "market": "A", "industry": "稀土"},
    {"code": "002460", "name": "赣锋锂业", "market": "A", "industry": "锂矿"},
    {"code": "000063", "name": "中兴通讯", "market": "A", "industry": "通信设备"},
    {"code": "600050", "name": "中国联通", "market": "A", "industry": "通信"},
    {"code": "601728", "name": "中国电信", "market": "A", "industry": "通信"},
    {"code": "600941", "name": "中国移动", "market": "A", "industry": "通信"},
    {"code": "300498", "name": "温氏股份", "market": "A", "industry": "农业养殖"},
    {"code": "002714", "name": "牧原股份", "market": "A", "industry": "农业养殖"},
    {"code": "002555", "name": "三七互娱", "market": "A", "industry": "游戏"},
    {"code": "300058", "name": "蓝色光标", "market": "A", "industry": "传媒"},
    {"code": "603444", "name": "吉比特", "market": "A", "industry": "游戏"},
    {"code": "002558", "name": "巨人网络", "market": "A", "industry": "游戏"},
    {"code": "300124", "name": "汇川技术", "market": "A", "industry": "工业自动化"},
    {"code": "002024", "name": "苏宁易购", "market": "A", "industry": "零售"},
    {"code": "601933", "name": "永辉超市", "market": "A", "industry": "零售"},
    {"code": "002263", "name": "大东方", "market": "A", "industry": "零售"},
    {"code": "603195", "name": "公牛集团", "market": "A", "industry": "电工"},
    {"code": "002572", "name": "索菲亚", "market": "A", "industry": "家居"},
    {"code": "603833", "name": "欧派家居", "market": "A", "industry": "家居"}
]


@app.get("/api/provider-status")
def get_provider_status():
    """数据层状态：当前行情/财务数据来源（通达信 MCP 或兜底）"""
    try:
        from tdx_provider import provider_status
        return provider_status()
    except Exception as e:
        return {"provider": "unknown", "error": str(e)}


@app.get("/api/pool")
def get_pool():
    """获取股票池"""
    return {"pool": STOCK_POOL}


@app.get("/api/analyze/{code}")
def analyze_stock(code: str):
    """分析单只股票（数据采集 + 评分 + 信号）"""
    import importlib.util
    
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    data_collector = load_module("data_collector", BACKEND_DIR / "data_collector.py")
    factor_scorer = load_module("factor_scorer", BACKEND_DIR / "factor_scorer.py")
    signal_generator = load_module("signal_generator", BACKEND_DIR / "signal_generator.py")

    data = data_collector.load_company_data(code)
    score = factor_scorer.calculate_total_score(data)
    signal = signal_generator.generate_signal(code, data)

    return {
        "code": code,
        "data": data,
        "score": score,
        "signal": signal,
    }


@app.get("/api/technical/{code}")
def get_technical_analysis(code: str, period: str = "daily", count: int = 120):
    """
    获取股票技术分析数据
    - 实时K线（新浪财经）
    - MA/MACD/RSI/KDJ/布林带指标
    - 买卖信号与强度
    - 历史回测表现
    """
    from technical_analysis import (
        calculate_indicators, generate_buy_sell_signals, backtest
    )
    from backtest_engine import get_kline_data_enhanced

    kd = get_kline_data_enhanced(code, period=period, count=count)
    if kd.get("error"):
        return {"error": kd["error"], "code": code}

    klines = kd["klines"]
    ta = calculate_indicators(klines)

    today = ta["today"]
    indicators = ta["indicators"]

    sig = generate_buy_sell_signals(indicators, today["close"], ta.get("ma_distances", {}))

    strategies = ["combo", "macd_cross", "ma_cross", "rsi_reversal", "bollinger"]
    backtests = {}
    for strat in strategies:
        bt = backtest(klines, strat)
        name_map = {"combo":"综合策略","macd_cross":"MACD金叉死叉","ma_cross":"均线交叉","rsi_reversal":"RSI超买超卖","bollinger":"布林带"}
        backtests[strat] = {
            "strategy_name": name_map.get(strat, strat),
            "total_trades": bt.get("total_trades", 0),
            "wins": bt.get("wins", 0),
            "losses": bt.get("losses", 0),
            "win_rate": bt.get("win_rate", 0),
            "total_return": bt.get("total_return", 0),
            "annualized_return": bt.get("annualized_return", 0),
            "max_drawdown": bt.get("max_drawdown", 0),
            "avg_profit_per_trade": bt.get("avg_profit_per_trade", 0),
            "recent_trades": bt.get("recent_trades", []),
        }

    best_strat = max(backtests.items(), key=lambda x: x[1]["annualized_return"])

    return {
        "code": code,
        "today": today,
        "indicators": indicators,
        "ma_distances": ta.get("ma_distances", {}),
        "signal": sig,
        "backtests": backtests,
        "best_strategy": {
            "name": best_strat[1]["strategy_name"],
            "annualized_return": best_strat[1]["annualized_return"],
            "win_rate": best_strat[1]["win_rate"],
        },
        "period_days": len(klines),
        "klines_count": len(klines),
        "kline_source": kd.get("source", "sina"),  # 数据来源标记
    }


# 回测引擎 v2 - 深度策略分析
# ============================================================

@app.get("/api/backtest/{code}")
def deep_backtest(code: str, strategy: str = "combo",
                  stop_loss: float = -8, take_profit: float = 20,
                  rsi_buy: int = 35, rsi_sell: int = 70,
                  count: int = 400):
    """
    深度回测接口
    - 可自定义止损/止盈参数
    - 返回完整统计指标
    - 与买入持有基准对比
    """
    from backtest_engine import (
        backtest_v2, optimize_parameters, compute_all_indicators,
        get_kline_data_enhanced,
    )

    kd = get_kline_data_enhanced(code, period="daily", count=count)
    if kd.get("error"):
        return {"error": kd["error"], "code": code}

    klines = kd["klines"]
    ta = compute_all_indicators(klines)
    if "error" in ta:
        return {"error": ta["error"], "code": code}

    # 运行回测
    bt = backtest_v2(klines, strategy, stop_loss, take_profit, rsi_buy, rsi_sell)

    # 参数优化
    opt = optimize_parameters(klines, strategy)

    # 当前信号
    sig = ta.get("_series", {})
    from backtest_engine import generate_signal
    current_sig = generate_signal(ta)

    return {
        "code": code,
        "today": ta["today"],
        "indicators": ta["indicators"],
        "current_signal": current_sig,
        "backtest": {
            "strategy": strategy,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "total_trades": bt.get("total_trades", 0),
            "wins": bt.get("wins", 0),
            "losses": bt.get("losses", 0),
            "win_rate": bt.get("win_rate", 0),
            "total_return": bt.get("total_return", 0),
            "annualized_return": bt.get("annualized_return", 0),
            "excess_return": bt.get("excess_return", 0),
            "max_drawdown": bt.get("max_drawdown", 0),
            "sharpe_ratio": bt.get("sharpe_ratio", 0),
            "profit_loss_ratio": bt.get("profit_loss_ratio", 0),
            "avg_win_pct": bt.get("avg_win_pct", 0),
            "avg_loss_pct": bt.get("avg_loss_pct", 0),
            "max_consecutive_wins": bt.get("max_consecutive_wins", 0),
            "max_consecutive_losses": bt.get("max_consecutive_losses", 0),
            "period_years": bt.get("period_years", 0),
            "benchmark_return": bt.get("benchmark", {}).get("return", 0),
            "recent_trades": bt.get("recent_trades", []),
            "equity_curve": bt.get("equity_curve", []),
        },
        "optimal": {
            "config": opt.get("optimal", {}).get("optimal_config"),
            "annualized": opt.get("optimal", {}).get("annualized_return"),
            "win_rate": opt.get("optimal", {}).get("win_rate"),
            "sharpe": opt.get("optimal", {}).get("sharpe_ratio"),
            "max_drawdown": opt.get("optimal", {}).get("max_drawdown"),
        },
        "kline_source": kd.get("source", "sina"),  # 数据来源标记
    }


@app.post("/api/backtest/compare")
def compare_strategies(codes: List[str] = Body([]), strategies: List[str] = Body([])):
    """
    多股票 × 多策略对比
    """
    from backtest_engine import compare_strategies_across_stocks
    if not codes:
        return {"error": "请提供股票代码列表", "codes_provided": len(codes)}
    if not strategies:
        strategies = ["ma_cross", "macd_cross", "rsi_reversal", "bollinger", "combo", "conservative"]
    return compare_strategies_across_stocks(codes, strategies)


@app.get("/api/backtest/recommend/{code}")
def backtest_recommend(code: str):
    """
    单股票完整分析 + 最优策略推荐
    """
    from backtest_engine import analyze_and_recommend
    return analyze_and_recommend(code)




@app.post("/api/scan")
def scan_pool(
    min_score: float = 0, max_score: float = 100,
    page: int = 1, page_size: int = 20, search: str = "",
    # 筛选参数
    min_price: float = 0, max_price: float = 999999,
    signal_type: str = "",  # BUY / SELL / HOLD / 空=全部
    rating: str = "",  # A+ / A / B+ / B / C / 空=全部
    min_roe: float = -999, max_roe: float = 999,
    min_gross_margin: float = -999, max_gross_margin: float = 999,
    min_debt_ratio: float = -999, max_debt_ratio: float = 999,
    group_by_industry: bool = False,  # 是否按板块分组
):
    """扫描整个股票池，支持多维度筛选和板块分组

    优化：批量获取实时行情（1次请求），并发获取财务数据（10线程）
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # ── 模块加载 ────────────────────────────────────────
    import importlib.util
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    try:
        # 数据层统一入口：tdx_provider 优先通达信 MCP，失败自动降级东方财富/新浪
        from tdx_provider import get_financial_data
        from financial_data import score_from_financial
        USE_REAL_FINANCIAL = True
    except ImportError:
        USE_REAL_FINANCIAL = False
        data_collector = load_module("data_collector", BACKEND_DIR / "data_collector.py")
        factor_scorer = load_module("factor_scorer", BACKEND_DIR / "factor_scorer.py")

    signal_generator = load_module("signal_generator", BACKEND_DIR / "signal_generator.py")

    # ── 收集所有待处理股票 ────────────────────────────────
    processed_codes = set()
    stock_list = []

    # 持仓股票
    portfolio_data = {}
    if PORTFOLIO_FILE.exists():
        try:
            with open(PORTFOLIO_FILE) as f:
                pf = json.load(f)
                for pos in pf.get("positions", []):
                    if isinstance(pos, dict) and pos.get("code"):
                        code = pos.get("code", "")
                        portfolio_data[code] = {
                            "name": pos.get("name", ""),
                            "current_price": pos.get("current_price", 0)
                        }
                        stock_list.append({
                            "code": code, "name": pos.get("name", ""),
                            "market": "A", "industry": "持仓",
                            "is_portfolio": True,
                            "portfolio_price": pos.get("current_price", 0)
                        })
                        processed_codes.add(code)
        except Exception:
            pass

    # 预设股票池
    for stock in STOCK_POOL:
        code = stock["code"]
        if code in processed_codes:
            continue
        stock_list.append({
            "code": code,
            "name": stock.get("name", ""),
            "market": stock.get("market", "A"),
            "industry": stock.get("industry", "未知"),
            "is_portfolio": False,
            "portfolio_price": 0
        })
        processed_codes.add(code)

    # ── 搜索过滤 ────────────────────────────────────────
    if search:
        s_upper = search.upper()
        stock_list = [s for s in stock_list
                      if s_upper in s["code"].upper() or search in s["name"]]

    all_codes = [s["code"] for s in stock_list]

    # ── 批量获取实时行情（1次请求） ─────────────────────
    from tdx_provider import get_batch_realtime_prices
    prices_map = get_batch_realtime_prices(all_codes)

    # ── 并发获取财务数据并评分（10线程） ─────────────────
    def score_one(stock_info):
        code = stock_info["code"]
        try:
            if USE_REAL_FINANCIAL:
                fin_data = get_financial_data(code)
                score_result = score_from_financial(fin_data)
                rt = prices_map.get(code, {})
                current_price = rt.get("current_price", 0) if isinstance(rt, dict) else 0

                score = {
                    "total_score": score_result["total_score"],
                    "rating": score_result["rating"],
                    "scores": score_result["scores"],
                    "reasons": score_result["reasons"],
                    "financial": score_result["financial_data"]
                }
                data = {
                    "price": current_price or stock_info["portfolio_price"],
                    "roe": fin_data.get("roe", 0),
                    "revenue_growth": fin_data.get("revenue_growth", 0),
                    "profit_growth": fin_data.get("profit_growth", 0),
                    "gross_margin": fin_data.get("gross_margin", 0),
                    "debt_ratio": fin_data.get("debt_ratio", 0),
                    "eps": fin_data.get("eps", 0),
                    "report_date": fin_data.get("report_date", ""),
                    "report_type": fin_data.get("report_type", ""),
                    "source": "eastmoney"
                }
            else:
                data = data_collector.load_company_data(code)
                if stock_info["portfolio_price"]:
                    data["price"] = stock_info["portfolio_price"]
                score = factor_scorer.calculate_total_score(data)

            return {
                "code": code,
                "name": stock_info["name"],
                "market": stock_info["market"],
                "industry": stock_info["industry"],
                "is_portfolio": stock_info["is_portfolio"],
                "data": data,
                "score": score,
            }
        except Exception as e:
            return None

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(score_one, s): s for s in stock_list}
        for future in as_completed(futures):
            r = future.result()
            if r:
                results.append(r)

    # 持仓优先，其余按评分降序
    results.sort(key=lambda x: (
        not x.get("is_portfolio", False),
        -(x.get("score", {}).get("total_score", 0) if isinstance(x.get("score"), dict) else 0)
    ))

    # ── 信号生成 ─────────────────────────────────────────
    for r in results:
        try:
            r["signal"] = signal_generator.generate_signal(r["code"], r["data"])
        except Exception:
            r["signal"] = {}

    # ── 多维度筛选 ───────────────────────────────────────
    filtered_results = []
    for r in results:
        s = r.get("score", {})
        d = r.get("data", {})
        sig = r.get("signal", {})

        total_score = s.get("total_score", 0) if isinstance(s, dict) else 0
        price = d.get("price", 0) if isinstance(d, dict) else 0
        roe = d.get("roe", 0) if isinstance(d, dict) else 0
        gross_margin = d.get("gross_margin", 0) if isinstance(d, dict) else 0
        debt_ratio = d.get("debt_ratio", 0) if isinstance(d, dict) else 0
        rating_val = s.get("rating", "") if isinstance(s, dict) else ""
        signal_val = sig.get("signal", "") if isinstance(sig, dict) else ""

        if total_score < min_score or total_score > max_score:
            continue
        if price < min_price or price > max_price:
            continue
        if signal_type and signal_val != signal_type:
            continue
        if rating:
            if rating == "A+" and not rating_val.startswith("A+"):
                continue
            elif rating == "A" and not (rating_val.startswith("A") and not rating_val.startswith("A+")):
                continue
            elif rating == "B+" and not rating_val.startswith("B+"):
                continue
            elif rating == "B" and not (rating_val.startswith("B") and not rating_val.startswith("B+")):
                continue
            elif rating == "C" and not rating_val.startswith("C"):
                continue
        if roe < min_roe or roe > max_roe:
            continue
        if gross_margin < min_gross_margin or gross_margin > max_gross_margin:
            continue
        if debt_ratio < min_debt_ratio or debt_ratio > max_debt_ratio:
            continue

        filtered_results.append(r)

    # ── 搜索补全 ─────────────────────────────────────────
    if search and len(search) >= 4 and filtered_results == []:
        s_upper = search.upper()
        is_code_like = search.isdigit() or s_upper.isalnum() or any(c.isdigit() for c in search)
        if is_code_like:
            try:
                from tdx_provider import get_realtime_price
                rt = get_realtime_price(search)
                if rt.get("status") == "success" and rt.get("current_price", 0) > 0:
                    if USE_REAL_FINANCIAL:
                        fin_data = get_financial_data(search)
                        score_result = score_from_financial(fin_data)
                        score = {
                            "total_score": score_result["total_score"],
                            "rating": score_result["rating"],
                            "scores": score_result["scores"],
                            "reasons": score_result["reasons"],
                            "financial": score_result["financial_data"]
                        }
                        data = {
                            "price": rt.get("current_price", 0),
                            "roe": fin_data.get("roe", 0),
                            "revenue_growth": fin_data.get("revenue_growth", 0),
                            "profit_growth": fin_data.get("profit_growth", 0),
                            "gross_margin": fin_data.get("gross_margin", 0),
                            "debt_ratio": fin_data.get("debt_ratio", 0),
                            "eps": fin_data.get("eps", 0),
                            "report_date": fin_data.get("report_date", ""),
                            "report_type": fin_data.get("report_type", ""),
                            "source": "eastmoney"
                        }
                    else:
                        data = data_collector.load_company_data(search)
                        score = factor_scorer.calculate_total_score(data)
                    signal = signal_generator.generate_signal(search, data)
                    filtered_results.append({
                        "code": search.upper(),
                        "name": rt.get("name", search),
                        "market": "A",
                        "industry": "搜索",
                        "is_portfolio": False,
                        "data": data,
                        "score": score,
                        "signal": signal,
                    })
            except Exception:
                pass

    # ── 分页 & 板块分组 ──────────────────────────────────
    total = len(filtered_results)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = filtered_results[start_idx:end_idx]

    industries = {}
    for r in filtered_results:
        ind = r.get("industry", "其他")
        if ind not in industries:
            industries[ind] = []
        industries[ind].append(r)

    for ind in industries:
        industries[ind].sort(key=lambda x: x.get("score", {}).get("total_score", 0)
                            if isinstance(x.get("score"), dict) else 0, reverse=True)

    sorted_industries = sorted(industries.keys(), key=lambda ind:
        sum(x.get("score", {}).get("total_score", 0) for x in industries[ind]) / len(industries[ind])
        if industries[ind] else 0, reverse=True)

    industry_groups = [{"name": ind, "stocks": industries[ind], "count": len(industries[ind])}
                       for ind in sorted_industries]

    return {
        "results": paginated_results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
        "industries": industry_groups if group_by_industry else [],
        "filters": {
            "min_score": min_score, "max_score": max_score,
            "min_price": min_price, "max_price": max_price,
            "signal_type": signal_type, "rating": rating,
            "search": search, "group_by_industry": group_by_industry
        }
    }

# ─── 风控 ───────────────────────────────────────────────

@app.get("/api/risk/check")
def risk_check():
    """组合风险检查"""
    import importlib.util
    
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    risk_manager = load_module("risk_manager", BACKEND_DIR / "risk_manager.py")
    Portfolio = risk_manager.Portfolio
    check_portfolio_risk = risk_manager.check_portfolio_risk

    portfolio = Portfolio()
    portfolio.load_from_file("/tmp/portfolio.json")
    result = check_portfolio_risk(portfolio)
    result["positions"] = {
        code: {
            "name": p.name,
            "shares": p.shares,
            "avg_cost": p.avg_cost,
            "current_price": p.current_price,
            "market_value": p.market_value,
            "pnl_pct": p.pnl_pct,
        }
        for code, p in portfolio.positions.items()
    }
    return result


@app.post("/api/risk/buy")
def risk_buy(code: str, price: float, amount: float = 100000):
    """买入风控检查"""
    import importlib.util
    
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    risk_manager = load_module("risk_manager", BACKEND_DIR / "risk_manager.py")
    Portfolio = risk_manager.Portfolio
    check_buy = risk_manager.check_buy

    portfolio = Portfolio()
    portfolio.load_from_file("/tmp/portfolio.json")
    result = check_buy(portfolio, code, price, amount=amount)
    return result


# ─── 持仓管理 ────────────────────────────────────────────

PORTFOLIO_FILE = Path("/tmp/portfolio.json")

@app.get("/api/portfolio")
def get_portfolio():
    """获取持仓"""
    if PORTFOLIO_FILE.exists():
        with open(PORTFOLIO_FILE) as f:
            return json.load(f)
    return {"cash": 1000000, "positions": [], "total_value": 1000000}


@app.post("/api/portfolio/add")
def add_position(code: str, name: str, shares: int, avg_cost: float, current_price: float):
    """添加持仓"""
    import importlib.util
    
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    risk_manager = load_module("risk_manager", BACKEND_DIR / "risk_manager.py")
    Portfolio = risk_manager.Portfolio

    portfolio = Portfolio()
    portfolio.load_from_file(str(PORTFOLIO_FILE))
    portfolio.add_position(code, name, shares, avg_cost, current_price)
    PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
    portfolio.save_to_file(str(PORTFOLIO_FILE))
    return {"status": "ok", "total_value": portfolio.get_total_value()}


@app.get("/api/portfolio/sync")
def sync_portfolio_prices():
    """同步持仓股票的现价和评分"""
    import importlib.util
    
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    if not PORTFOLIO_FILE.exists():
        return {"status": "error", "message": "无持仓数据"}
    
    try:
        with open(PORTFOLIO_FILE) as f:
            portfolio_data = json.load(f)
        
        data_collector = load_module("data_collector", BACKEND_DIR / "data_collector.py")
        factor_scorer = load_module("factor_scorer", BACKEND_DIR / "factor_scorer.py")
        
        updated_positions = []
        sync_results = []
        
        for pos in portfolio_data.get("positions", []):
            code = pos.get("code", "")
            
            # 尝试从数据源获取最新价格
            try:
                data = data_collector.load_company_data(code)
                score = factor_scorer.calculate_total_score(data)
                
                # 更新现价（如果有真实数据）
                new_price = data.get("price", pos.get("current_price", 0))
                pos["current_price"] = new_price
                pos["market_value"] = pos.get("shares", 0) * new_price
                pos["pnl_pct"] = ((new_price - pos.get("avg_cost", 0)) / pos.get("avg_cost", 1)) * 100 if pos.get("avg_cost", 0) > 0 else 0
                pos["score"] = score.get("total_score", 0)
                pos["rating"] = score.get("rating", "")
                
                sync_results.append({
                    "code": code,
                    "name": pos.get("name", ""),
                    "old_price": pos.get("current_price", 0),
                    "new_price": new_price,
                    "score": score.get("total_score", 0),
                    "status": "updated"
                })
            except Exception as e:
                sync_results.append({
                    "code": code,
                    "name": pos.get("name", ""),
                    "status": "error",
                    "message": str(e)
                })
            
            updated_positions.append(pos)
        
        # 重新计算总市值
        portfolio_data["positions"] = updated_positions
        total_value = portfolio_data.get("cash", 0)
        for pos in updated_positions:
            total_value += pos.get("market_value", 0)
        portfolio_data["total_value"] = total_value
        
        # 保存更新后的数据
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump(portfolio_data, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "ok",
            "total_value": total_value,
            "sync_results": sync_results,
            "updated_count": len([r for r in sync_results if r.get("status") == "updated"])
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/portfolio/delete/{code}")
def delete_position(code: str):
    """删除持仓"""
    try:
        if not PORTFOLIO_FILE.exists():
            return {"status": "error", "message": "无持仓数据"}
        
        with open(PORTFOLIO_FILE) as f:
            data = json.load(f)
        
        # 查找并删除持仓
        positions = data.get("positions", [])
        original_count = len(positions)
        positions = [p for p in positions if p.get("code", "").upper() != code.upper()]
        
        if len(positions) == original_count:
            return {"status": "error", "message": f"未找到持仓 {code}"}
        
        data["positions"] = positions
        
        # 重新计算总市值
        total_value = data.get("cash", 0)
        for p in positions:
            total_value += p.get("market_value", p.get("shares", 0) * p.get("current_price", 0))
        data["total_value"] = total_value
        
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {"status": "ok", "message": f"已删除持仓 {code}", "positions_count": len(positions)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/portfolio/update/{code}")
def update_position(code: str, shares: int = Form(...), avg_cost: float = Form(...)):
    """更新持仓（持股数、成本价）"""
    try:
        if not PORTFOLIO_FILE.exists():
            return {"status": "error", "message": "无持仓数据"}
        
        with open(PORTFOLIO_FILE) as f:
            data = json.load(f)
        
        # 查找并更新持仓
        updated = False
        positions = data.get("positions", [])
        for pos in positions:
            if pos.get("code", "").upper() == code.upper():
                pos["shares"] = shares
                pos["avg_cost"] = avg_cost
                # 重新计算市值和盈亏
                current_price = pos.get("current_price", avg_cost)
                pos["market_value"] = shares * current_price
                pos["pnl_pct"] = ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0
                updated = True
                break
        
        if not updated:
            return {"status": "error", "message": f"未找到持仓 {code}"}
        
        data["positions"] = positions
        
        # 重新计算总市值
        total_value = data.get("cash", 0)
        for p in positions:
            total_value += p.get("market_value", p.get("shares", 0) * p.get("current_price", 0))
        data["total_value"] = total_value
        
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "ok", 
            "message": f"已更新持仓 {code}",
            "positions_count": len(positions),
            "total_value": total_value
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/portfolio/cash")
def update_cash(cash: float = Form(...)):
    """更新现金"""
    try:
        if PORTFOLIO_FILE.exists():
            with open(PORTFOLIO_FILE) as f:
                data = json.load(f)
        else:
            data = {"cash": 1000000, "positions": [], "total_value": 1000000}
        
        data["cash"] = cash
        
        # 重新计算总市值
        total_value = cash
        for pos in data.get("positions", []):
            shares = pos.get("shares", 0)
            current_price = pos.get("current_price", 0)
            total_value += shares * current_price
        data["total_value"] = total_value
        
        PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {"status": "ok", "cash": cash, "total_value": total_value}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/portfolio/import")
def import_portfolio(data: dict = Body(...)):
    """导入持仓"""
    try:
        cash = data.get("cash", 0)
        positions = data.get("positions", [])
        
        if not isinstance(positions, list):
            return {"status": "error", "message": "positions 必须是数组"}
        
        # 构建持仓数据
        portfolio_data = {
            "cash": cash,
            "positions": positions,
            "total_value": cash
        }
        
        # 计算总市值
        for pos in positions:
            shares = pos.get("shares", 0)
            current_price = pos.get("current_price", 0)
            portfolio_data["total_value"] += shares * current_price
        
        # 保存到文件
        PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump(portfolio_data, f, ensure_ascii=False, indent=2)
        
        return {"status": "ok", "positions_count": len(positions), "cash": cash}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── 微信通知 ────────────────────────────────────────────

WECHAT_CONFIG = Path("/tmp/wechat_config.json")

@app.get("/api/wechat/config")
def get_wechat_config():
    """获取微信配置"""
    if WECHAT_CONFIG.exists():
        with open(WECHAT_CONFIG) as f:
            return json.load(f)
    return {"enabled": False, "webhook_url": "", "mention": ""}


@app.post("/api/wechat/config")
def set_wechat_config(webhook_url: str = Form(""), mention: str = Form("")):
    """保存微信配置"""
    config = {
        "enabled": bool(webhook_url),
        "webhook_url": webhook_url,
        "mention": mention,
    }
    with open(WECHAT_CONFIG, "w") as f:
        json.dump(config, f)
    return {"status": "ok", **config}


@app.post("/api/wechat/send")
def wechat_send(content: str = Form("")):
    """发送微信通知"""
    if not WECHAT_CONFIG.exists():
        return {"status": "error", "message": "未配置微信webhook"}

    with open(WECHAT_CONFIG) as f:
        config = json.load(f)

    if not config.get("webhook_url"):
        return {"status": "error", "message": "webhook_url 为空"}

    import urllib.request
    import urllib.parse

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content + (f"\n> @{config.get('mention', '')}" if config.get("mention") else "")
        }
    }

    try:
        req = urllib.request.Request(
            config["webhook_url"],
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/wechat/signal/{code}")
def wechat_signal(code: str):
    """推送交易信号到微信"""
    import importlib.util
    import datetime
    
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    data_collector = load_module("data_collector", BACKEND_DIR / "data_collector.py")
    factor_scorer = load_module("factor_scorer", BACKEND_DIR / "factor_scorer.py")
    signal_generator = load_module("signal_generator", BACKEND_DIR / "signal_generator.py")

    data = data_collector.load_company_data(code)
    score = factor_scorer.calculate_total_score(data)
    signal = signal_generator.generate_signal(code, data)

    # 构建消息
    emoji = {"BUY": "📈", "HOLD": "➡️", "SELL": "📉"}.get(signal["signal"], "❓")
    score_value = int(signal.get("score", 0))
    stars = "★" * max(1, score_value // 20)

    content = f"""### {emoji} 乐友量化信号 - {signal['signal']}

> **{signal['name']}** ({code})

**评级:** {stars} {score_value}/100

**置信度:** {signal.get('confidence', 0)}%

**当前价格:** ¥{data.get('price', 0)}

**核心逻辑:**
"""

    reasons = signal.get("reasons", [])
    for reason in reasons:
        content += f"> • {reason}\n"

    content += f"""
> ---
> ⏰ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
> 🎯 由乐友量化系统生成
"""

    # 发送
    if not WECHAT_CONFIG.exists():
        return {"status": "error", "message": "未配置微信webhook", "content": content}
    with open(WECHAT_CONFIG) as f:
        config = json.load(f)
    if not config.get("webhook_url"):
        return {"status": "error", "message": "webhook_url 为空", "content": content}

    import urllib.request
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }
    req = urllib.request.Request(
        config["webhook_url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
        return {"status": "ok", "result": result, "content": content}


# ─── 实时行情 API ──────────────────────────────────────

@app.get("/api/realtime/portfolio")
def get_portfolio_realtime():
    """获取持仓股票实时行情"""
    try:
        if not PORTFOLIO_FILE.exists():
            return {"error": "无持仓数据", "results": {}}
        
        with open(PORTFOLIO_FILE) as f:
            portfolio = json.load(f)
        
        codes = [pos.get("code") for pos in portfolio.get("positions", []) if pos.get("code")]
        
        from tdx_provider import get_batch_realtime_prices
        results = get_batch_realtime_prices(codes)
        
        # 更新持仓现价
        for pos in portfolio.get("positions", []):
            code = pos.get("code")
            if code in results and "current_price" in results[code]:
                realtime = results[code]
                pos["current_price"] = realtime["current_price"]
                pos["change_pct"] = realtime.get("change_pct", 0)
                pos["market_value"] = pos.get("shares", 0) * realtime["current_price"]
                if pos.get("avg_cost", 0) > 0:
                    pos["pnl_pct"] = ((realtime["current_price"] - pos["avg_cost"]) / pos["avg_cost"]) * 100
        
        # 重新计算总市值
        total_value = portfolio.get("cash", 0)
        for pos in portfolio.get("positions", []):
            total_value += pos.get("market_value", 0)
        portfolio["total_value"] = total_value
        
        # 保存更新后的数据
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump(portfolio, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "ok",
            "total_value": total_value,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/realtime/batch")
def get_batch_prices(codes: str = ""):
    """批量获取实时行情，codes用逗号分隔"""
    try:
        code_list = [c.strip() for c in codes.split(",") if c.strip()]
        from tdx_provider import get_batch_realtime_prices
        results = get_batch_realtime_prices(code_list)
        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/realtime/{code}")
def get_realtime_price(code: str):
    """获取单只股票实时行情"""
    try:
        from tdx_provider import get_realtime_price as fetch_price
        result = fetch_price(code)
        return result
    except Exception as e:
        return {"error": str(e), "code": code}



# ─── 通达信增强：自然语言选股 / F10三表 / 资讯 ──────────
@app.get("/api/screener")
def api_screener(message: str, rang: str = "AG", page_no: int = 1,
                 page_size: int = 20):
    """自然语言条件选股。message示例: 今天涨停 / MACD金叉 / 3连板"""
    try:
        from tdx_provider import screen_stocks
        return screen_stocks(message, rang=rang, page_no=page_no,
                             page_size=page_size)
    except Exception as e:
        return {"error": str(e), "rows": []}


@app.get("/api/financial-statement/{code}")
def api_financial_statement(code: str, stmt: str = "income",
                           report_type: str = "00101"):
    """完整财务报表。stmt: income(利润表)/balance(资产)/cashflow(现金流)"""
    try:
        from tdx_provider import get_financial_statements
        return get_financial_statements(code, stmt_type=stmt,
                                        report_type=report_type)
    except Exception as e:
        return {"error": str(e), "code": code}


@app.get("/api/notices")
def api_notices(name: str = "", code: str = "", bdate: str = "",
                edate: str = "", keywords: str = "", top_k: int = 10):
    """公司公告查询"""
    try:
        from tdx_provider import query_notices
        return query_notices(name=name, code=code, bdate=bdate,
                             edate=edate, keywords=keywords, top_k=top_k)
    except Exception as e:
        return {"error": str(e), "items": []}


@app.get("/api/reports")
def api_reports(name: str = "", code: str = "", bdate: str = "",
                edate: str = "", keywords: str = "", top_k: int = 10):
    """券商研报查询"""
    try:
        from tdx_provider import query_reports
        return query_reports(name=name, code=code, bdate=bdate,
                             edate=edate, keywords=keywords, top_k=top_k)
    except Exception as e:
        return {"error": str(e), "items": []}


@app.get("/api/news")
def api_news(name: str = "", code: str = "", keywords: str = "",
             top_k: int = 10):
    """新闻资讯查询"""
    try:
        from tdx_provider import query_news
        return query_news(name=name, code=code, keywords=keywords,
                          top_k=top_k)
    except Exception as e:
        return {"error": str(e), "items": []}


# ─── 前端静态文件 ────────────────────────────────────────

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print("\n🎯 乐友量化投资系统 v1.0")
    print("📡 API: http://localhost:8000")
    print("📖 文档: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
