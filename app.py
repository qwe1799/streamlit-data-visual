import streamlit as st
import time
import pandas as pd
import numpy as np
import math
import folium
from streamlit_folium import st_folium

# ======================== 坐标转换工具函数（修复语法错误核心区）========================
x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626
a = 6378245.0
ee = 0.00669342162296594323

def out_of_china(lng, lat):
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False

def _transform_lat(x, y):
    ret = -100.0 + 2.0*x + 3.0*y + 0.2*y*y + 0.1*x*y + 0.2*math.sqrt(abs(x))
    ret += (20.0*math.sin(6.0*x*pi) + 20.0*math.sin(2.0*x*pi)) * 2.0 / 3.0
    ret += (20.0*math.sin(y*pi) + 40.0*math.sin(y/3.0*pi)) * 2.0 / 3.0
    ret += (160.0*math.sin(y/12.0*pi) + 320*math.sin(y*pi/30.0)) * 2.0 / 3.0
    return ret  # 修复：此处单独换行，避免和import拼接

def _transform_lng(x, y):
    ret = 300.0 + x + 2.0*y + 0.1*x*x + 0.1*x*y + 0.1*math.sqrt(abs(x))
    ret += (20.0*math.sin(6.0*x*pi) + 20.0*math.sin(2.0*x*pi)) * 2.0 / 3.0
    ret += (20.0*math.sin(x*pi) + 40.0*math.sin(x/3.0*pi)) * 2.0 / 3.0
    ret += (150.0*math.sin(x/12.0*pi) + 300*math.sin(x/30.0*pi)) * 2.0 / 3.0
    return ret  # 修复：此处单独换行，避免和import拼接

def wgs84_to_gcj02(lng, lat):
    if out_of_china(lng, lat):
        return lng, lat
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    mglat = lat + dlat
    mglng = lng + dlng
    return (mglng, mglat)

def gcj02_to_wgs84(lng, lat):
    if out_of_china(lng, lat):
        return lng, lat
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    mglat = lat + dlat
    mglng = lng + dlng
    return (lng * 2 - mglng, lat * 2 - mglat)

# ======================== Streamlit 页面核心逻辑 ========================
st.set_page_config(
    page_title="无人机心跳监测与航线规划",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化会话状态
if "heartbeat_data" not in st.session_state:
    st.session_state.heartbeat_data = []
    st.session_state.seq = 0
    st.session_state.last_receive_time = time.time()
    st.session_state.is_monitoring = False
    st.session_state.point_a = None
    st.session_state.point_b = None
    st.session_state.obstacles = []
    st.session_state.coord_system = "GCJ-02"

# 侧边栏导航
st.sidebar.title("功能导航")
page = st.sidebar.radio("选择功能", ["心跳监测", "航线规划"])

# ------------------------ 心跳监测页面 ------------------------
if page == "心跳监测":
    st.title("📡 无人机心跳监测")
    st.divider()

    # 心跳模拟与断线检测函数
    def simulate_heartbeat():
        st.session_state.seq += 1
        current_time = pd.Timestamp.now()
        st.session_state.last_receive_time = time.time()
        st.session_state.heartbeat_data.append({
            "序号": st.session_state.seq,
            "时间": current_time,
            "状态": "正常"
        })

    def check_timeout():
        current_time = time.time()
        if current_time - st.session_state.last_receive_time > 3:
            st.session_state.heartbeat_data.append({
                "序号": st.session_state.seq,
                "时间": pd.Timestamp.now(),
                "状态": "超时"
            })
            return True
        return False

    # 界面布局
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("控制面板")
        if not st.session_state.is_monitoring:
            if st.button("🚀 开始监测", type="primary"):
                st.session_state.is_monitoring = True
        else:
            if st.button("🛑 停止监测"):
                st.session_state.is_monitoring = False

        # 统计信息
        if st.session_state.heartbeat_data:
            df = pd.DataFrame(st.session_state.heartbeat_data)
            total = len(df)
            timeout = len(df[df["状态"] == "超时"])
            st.metric("总心跳包数", total)
            st.metric("超时次数", timeout)

    with col2:
        st.subheader("心跳数据实时展示")
        placeholder = st.empty()
        while st.session_state.is_monitoring:
            simulate_heartbeat()
            is_timeout = check_timeout()
            df = pd.DataFrame(st.session_state.heartbeat_data)
            
            with placeholder.container():
                # 折线图
                st.line_chart(df, x="时间", y="序号", color="状态", use_container_width=True)
                # 最新10条数据
                st.dataframe(df.tail(10), use_container_width=True)
                # 超时告警
                if is_timeout:
                    st.error("⚠️ 断线警告：3秒未收到心跳包！")
            time.sleep(1)
        
        # 停止监测后展示历史数据
        if st.session_state.heartbeat_data:
            df = pd.DataFrame(st.session_state.heartbeat_data)
            st.line_chart(df, x="时间", y="序号", color="状态", use_container_width=True)
            st.dataframe(df.tail(10), use_container_width=True)

# ------------------------ 航线规划页面 ------------------------
elif page == "航线规划":
    st.title("📝 无人机航线规划")
    st.divider()

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("参数设置")
        # 坐标系选择
        st.session_state.coord_system = st.radio(
            "输入坐标系",
            ["WGS-84", "GCJ-02(高德/百度)"],
            index=1
        )
        # A点设置
        st.subheader("起点A")
        a_lat = st.number_input("纬度", value=32.2322, format="%.4f", key="a_lat")
        a_lng = st.number_input("经度", value=118.7490, format="%.4f", key="a_lng")
        if st.button("设置A点"):
            if st.session_state.coord_system == "GCJ-02":
                wgs_lng, wgs_lat = gcj02_to_wgs84(a_lng, a_lat)
            else:
                wgs_lng, wgs_lat = a_lng, a_lat
            st.session_state.point_a = (wgs_lat, wgs_lng)
            st.success("A点设置成功！")
        
        # B点设置
        st.subheader("终点B")
        b_lat = st.number_input("纬度", value=32.2343, format="%.4f", key="b_lat")
        b_lng = st.number_input("经度", value=118.7490, format="%.4f", key="b_lng")
        if st.button("设置B点"):
            if st.session_state.coord_system == "GCJ-02":
                wgs_lng, wgs_lat = gcj02_to_wgs84(b_lng, b_lat)
            else:
                wgs_lng, wgs_lat = b_lng, b_lat
            st.session_state.point_b = (wgs_lat, wgs_lng)
            st.success("B点设置成功！")
        
        # 飞行高度
        flight_alt = st.slider("飞行高度(m)", 0, 100, 30, key="flight_alt")

    with col2:
        st.subheader("地图可视化")
        # 初始化地图中心
        center = st.session_state.point_a if st.session_state.point_a else (32.233, 118.749)
        m = folium.Map(location=center, zoom_start=18)
        
        # 绘制A/B点
        if st.session_state.point_a:
            folium.Marker(st.session_state.point_a, popup="起点A", icon=folium.Icon(color="red")).add_to(m)
        if st.session_state.point_b:
            folium.Marker(st.session_state.point_b, popup="终点B", icon=folium.Icon(color="green")).add_to(m)
        
        # 绘制AB连线
        if st.session_state.point_a and st.session_state.point_b:
            folium.PolyLine(
                [st.session_state.point_a, st.session_state.point_b],
                color="blue", weight=3, dash_array="5,5"
            ).add_to(m)
        
        # 渲染地图
        st_folium(m, width=800, height=500, use_container_width=True)
