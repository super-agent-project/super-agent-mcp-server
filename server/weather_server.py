"""
File   : weather_server.py
Desc   : 高德地图天气查询工具
Date   : 2025/12/22
Author : Tianyu Chen
"""

import os
import asyncio
import aiohttp
from typing import Optional, Tuple
from dotenv import load_dotenv
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP


# Initialize FastMCP server
mcp = FastMCP("weather", host="0.0.0.0", port=8001, stateless_http=True)

load_dotenv()

# 请确保环境变量中已配置 AMAP_KEY
AMAP_KEY = os.getenv("AMAP_KEY", "你的高德Web服务Key")

async def _fetch_json(url: str) -> dict:
    """
    [内部辅助函数] 异步发送 GET 请求并返回 JSON
    """
    timeout = aiohttp.ClientTimeout(total=5)  # 设置超时时间 5秒
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            # 确保 HTTP 状态码正常
            response.raise_for_status()
            return await response.json()


async def _resolve_adcode(city_name: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    [内部辅助函数] 异步解析城市名称或自动定位，获取行政区划代码(adcode)。
    """
    if not AMAP_KEY:
        return None, None

    try:
        # 1. 自动定位 (IP)
        if not city_name or city_name == "CURRENT_USER_LOCATION":
            url = f"https://restapi.amap.com/v3/ip?key={AMAP_KEY}"
            res = await _fetch_json(url)
            if res['status'] == '1':
                return res['adcode'], res['city']
        
        # 2. 指定城市解析 (地理编码)
        else:
            url = f"https://restapi.amap.com/v3/geocode/geo?address={city_name}&key={AMAP_KEY}"
            res = await _fetch_json(url)
            if res['status'] == '1' and res['geocodes']:
                return res['geocodes'][0]['adcode'], res['geocodes'][0]['formatted_address']
    except Exception as e:
        print(f"位置解析错误: {e}")
        pass
    
    return None, None

@mcp.tool()
async def get_amap_weather_now(city_name: str = None) -> str:
    """
    获取当前城市的天气情况。

    Args:
        city_name (str): 城市名称。如果为 None，则使用 IP 地址进行定位。

    Returns:
        str: 天气信息字符串，包含天气、气温、湿度、风力、更新时间。
    """
    # 注意：这里需要 await 调用异步函数
    adcode, display_name = await _resolve_adcode(city_name)
    if not adcode:
        return f"无法定位或找不到城市 '{city_name}'，请提供更详细的城市名称。"

    try:
        url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={AMAP_KEY}&extensions=base"
        res = await _fetch_json(url)

        if res['status'] == '1' and res['lives']:
            data = res['lives'][0]
            return (f"【{data['province']} {data['city']}】实时天气：\n"
                    f"天气现象：{data['weather']}\n"
                    f"当前气温：{data['temperature']}℃\n"
                    f"空气湿度：{data['humidity']}%\n"
                    f"风向风力：{data['winddirection']}风 {data['windpower']}级\n"
                    f"更新时间：{data['reporttime']}")
        else:
            return f"天气查询失败: {res.get('info', '未知错误')}"
    except Exception as e:
        return f"接口请求异常: {str(e)}"

@mcp.tool()
async def get_amap_weather_forecast(city_name: str = None) -> str:
    """
    获取未来几天（含今天）的天气预报情况。

    Args:
        city_name (str): 城市名称。如果为 None，则使用 IP 地址进行定位。

    Returns:
        str: 天气预报信息字符串，包含预报日期、天气、气温范围。
    """
    adcode, display_name = await _resolve_adcode(city_name)
    if not adcode:
        return f"无法定位或找不到城市 '{city_name}'，请提供更详细的城市名称。"

    try:
        url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={AMAP_KEY}&extensions=all"
        res = await _fetch_json(url)

        if res['status'] == '1' and res['forecasts']:
            data = res['forecasts'][0]
            result = [f"【{data['province']} {data['city']}】未来几天天气预报："]

            week_map = {'1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '日'}
            
            for cast in data['casts']:
                week_str = week_map.get(cast['week'], cast['week'])
                
                day_w = cast['dayweather']
                night_w = cast['nightweather']
                
                if day_w == night_w:
                    weather_str = day_w
                else:
                    weather_str = f"{day_w}转{night_w}"

                day_info = (f"\n📅 {cast['date']} (周{week_str}): "
                            f"{weather_str}, "
                            f"{cast['nighttemp']}℃ ~ {cast['daytemp']}℃")
                result.append(day_info)
            
            return "".join(result)
        else:
            return f"预报查询失败: {res.get('info', '未知错误')}"
    except Exception as e:
        return f"接口请求异常: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='streamable-http')
