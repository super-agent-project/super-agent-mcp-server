"""
File   : test_weather_server.py
Desc   : 测试高德地图天气查询工具
cd super-agent-mcp-server
uv run pytest tests/test_weather_server.py
Date   : 2025/12/22
Author : Tianyu Chen
"""
import sys
from pathlib import Path
import asyncio
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
from server.weather_server import get_amap_weather_now, get_amap_weather_forecast

@pytest.mark.asyncio
async def test_get_amap_weather_now():
    # 测试自动定位天气查询
    weather_auto = await get_amap_weather_now("CURRENT_USER_LOCATION")
    assert isinstance(weather_auto, str)
    assert "天气" in weather_auto
    # assert "天气" in weather_auto or "无法定位" in weather_auto

    await asyncio.sleep(1)

    # 测试指定城市天气查询
    weather_beijing = await get_amap_weather_now("北京")
    assert isinstance(weather_beijing, str)
    assert "北京" in weather_beijing

    await asyncio.sleep(1)

    # 测试无效城市名称
    weather_invalid = await get_amap_weather_now("12345")
    assert isinstance(weather_invalid, str)
    assert "无法定位" in weather_invalid

@pytest.mark.asyncio
async def test_get_amap_weather_forecast():
    # 测试自动定位天气预报查询
    forecast_auto = await get_amap_weather_forecast("CURRENT_USER_LOCATION")
    assert isinstance(forecast_auto, str)
    assert "未来几天天气预报" in forecast_auto
    # assert "未来几天天气预报" in forecast_auto or "无法定位" in forecast_auto

    await asyncio.sleep(1)

    # 测试指定城市天气预报查询
    forecast_shanghai = await get_amap_weather_forecast("上海")
    assert isinstance(forecast_shanghai, str)
    assert "上海" in forecast_shanghai

    await asyncio.sleep(1)

    # 测试无效城市名称
    forecast_invalid = await get_amap_weather_forecast("ABCDE")
    assert isinstance(forecast_invalid, str)
    assert "无法定位" in forecast_invalid
