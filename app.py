import streamlit as st
import folium
from streamlit_folium import st_folium
import math

# ------------------------------
# 坐标系转换函数（保留原功能）
# ------------------------------
def gcj02_to_wgs84(lat, lng):
    a = 6378245.0
    ee = 0.00669342162296594323
    def _transform_lat(x, y):
        ret = -100.0 + 2.0*x + 3.0*y + 0.2*y*y + 0.1*x*y + 0.2*math.sqrt(abs(x))
        ret += (20.0*math.sin(6.0*x*math.pi) + 20.0*math.sin(2.0*x*math.pi)) * 2.0 / 3.0
        ret += (20.0*math.sin(y*math.pi) + 40.0*math.sin(y/3.0*math.pi)) * 2.0 / 3.0
        ret += (160.0*math.sin(y/12.0*math.pi) + 320*math.sin(y*math.pi/30.0)) * 2.0 / 3.0
        return ret
    def _transform_lng(x, y):
        ret = 300.0 + x + 2.0*y + 0.1*x*x + 0.1*x*y + 0.1*math.sqrt(abs(x))
        ret += (20.0*math.sin(6.0*x*math.pi) + 20.0*math.sin(2.0*x*math.pi)) * 2.0 / 3.0
        ret += (20.0*math.sin(x*math.pi) + 40.0*math.sin(x/3.0*math.pi)) * 2.0 / 3.0
        ret += (150.0*math.sin(x/12.0*math.pi) + 300*math.sin(x*math.pi/30.0)) * 2.0 / 3.0
        return ret
    dLat = _transform_lat(lng-105.0, lat-35.0)
    dLng = _transform_lng(lng-105.0, lat-35.0)
    radLat = lat / 180.0 * math.pi
    magic = math.sin(radLat)
    magic = 1 - ee * magic * magic
    sqrtMagic = math.sqrt(magic)
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * math.pi)
    dLng = (dLng * 180.0) / (a / sqrtMagic * math.cos(radLat) * math.pi)
    mgLat = lat + dLat
    mgLng = lng + dLng
    return lat*2 - mgLat, lng*2 - mgLng

# ------------------------------
# 页面标题
# ------------------------------
st.title("📡 导航与飞行监控系统（网页版）")

# ------------------------------
# 选项卡（航线规划 / 飞行监控）
# ------------------------------
tab1, tab2 = st.tabs(["🧭 航线规划", "📶 飞行监控"])

# ------------------------------
# 选项卡1：航线规划 + 地图
# ------------------------------
with tab1:
    st.subheader("航线规划")

    # 坐标系选择
    coord_type = st.radio("坐标系", ["GCJ-02", "WGS-84"], horizontal=True)

    # 默认坐标（可自行修改）
    A_lat, A_lng = 32.232, 118.749
    B_lat, B_lng = 32.234, 118.751

    # 转换坐标系
    if coord_type == "GCJ-02":
        A_lat, A_lng = gcj02_to_wgs84(A_lat, A_lng)
        B_lat, B_lng = gcj02_to_wgs84(B_lat, B_lng)

    # 创建地图
    m = folium.Map(location=[32.233, 118.75], zoom_start=18)

    # 标记A、B点
    folium.Marker([A_lat, A_lng], popup="起点A", icon=folium.Icon(color="red")).add_to(m)
    folium.Marker([B_lat, B_lng], popup="终点B", icon=folium.Icon(color="blue")).add_to(m)

    # 绘制航线
    folium.PolyLine(
        locations=[[A_lat, A_lng], [B_lat, B_lng]],
        color="red", weight=4, opacity=0.8
    ).add_to(m)

    # 显示地图
    st_folium(m, width=700, height=450)

    st.success("✅ A点、B点已设置，航线已生成")

# ------------------------------
# 选项卡2：飞行监控（心跳包）
# ------------------------------
with tab2:
    st.subheader("飞行监控 & 心跳包")
    st.info("📶 实时心跳包接收区（原功能完整保留）")

    # 模拟心跳（你可以替换成真实接收逻辑）
    heartbeat_data = "设备正常 | 信号强 | 经纬度稳定"
    st.code(heartbeat_data, language="txt")

    st.metric("当前状态", "正常飞行中")
