#!/usr/bin/env python3
"""
实时行情获取模块
使用新浪财经免费 API 获取 A 股实时行情
"""

import urllib.request
import re
import json
from datetime import datetime


def get_realtime_price(code: str) -> dict:
    """从新浪财经获取 A 股实时行情"""
    if code.startswith('6'):
        full_code = "sh" + code
    else:
        full_code = "sz" + code
    
    url = "http://hq.sinajs.cn/list=" + full_code
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://finance.sina.com.cn'
            }
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode('gbk')
            
            pattern = 'hq_str_' + full_code + '="(.+?)"'
            match = re.search(pattern, content)
            
            if not match:
                return {"error": "not_found", "code": code}
            
            data = match.group(1).split(',')
            
            if len(data) < 10:
                return {"error": "data_error", "code": code}
            
            name = data[0]
            open_price = float(data[1]) if data[1] else 0
            prev_close = float(data[2]) if data[2] else 0
            current_price = float(data[3]) if data[3] else 0
            high = float(data[4]) if data[4] else 0
            low = float(data[5]) if data[5] else 0
            volume = int(float(data[8])) if data[8] else 0
            amount = float(data[9]) if data[9] else 0
            
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            
            return {
                "code": code,
                "name": name,
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": volume,
                "amount": amount,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
    except Exception as e:
        return {"error": str(e), "code": code}


def get_batch_realtime_prices(codes: list) -> dict:
    """批量获取实时行情"""
    results = {}
    
    if not codes:
        return results
    
    # 构造批量请求
    full_codes = []
    for code in codes:
        if code.startswith('6'):
            full_codes.append("sh" + code)
        else:
            full_codes.append("sz" + code)
    
    url = "http://hq.sinajs.cn/list=" + ",".join(full_codes)
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'http://finance.sina.com.cn'
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('gbk')
            
            for code in codes:
                if code.startswith('6'):
                    full_code = "sh" + code
                else:
                    full_code = "sz" + code
                
                pattern = 'hq_str_' + full_code + '="(.+?)"'
                match = re.search(pattern, content)
                
                if match:
                    data_list = match.group(1).split(',')
                    if len(data_list) >= 10:
                        try:
                            current_price = float(data_list[3]) if data_list[3] else 0
                            prev_close = float(data_list[2]) if data_list[2] else 0
                            change = current_price - prev_close
                            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                            
                            results[code] = {
                                "code": code,
                                "name": data_list[0],
                                "current_price": current_price,
                                "change": round(change, 2),
                                "change_pct": round(change_pct, 2),
                                "status": "success"
                            }
                        except Exception as e:
                            results[code] = {"error": str(e), "code": code}
                    else:
                        results[code] = {"error": "data_error", "code": code}
                else:
                    results[code] = {"error": "not_found", "code": code}
    except Exception as e:
        for code in codes:
            if code not in results:
                results[code] = {"error": str(e), "code": code}
    
    return results


if __name__ == "__main__":
    test_codes = ["600519", "000858", "601318", "600036", "600126"]
    
    print("测试实时行情:")
    print("-" * 50)
    
    # 单条测试
    for code in test_codes[:3]:
        data = get_realtime_price(code)
        if data.get("status") == "success":
            print(f"{data['name']} ({code}): {data['current_price']} ({data['change_pct']:+.2f}%)")
        else:
            print(f"{code}: {data.get('error')}")
    
    print("\n批量测试:")
    batch = get_batch_realtime_prices(test_codes)
    for code, data in batch.items():
        if data.get("status") == "success":
            print(f"{data['name']}: {data['current_price']} ({data['change_pct']:+.2f}%)")
        else:
            print(f"{code}: {data.get('error')}")
