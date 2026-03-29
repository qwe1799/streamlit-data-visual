# app.py 最终纯净版
import streamlit as st
import time
import pandas as pd
import math
import folium
from streamlit_folium import st_folium

# 坐标转换工具函数
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
    return ret

def _transform_lng(x, y):
    ret = 300.0 + x + 2.0*y + 0.1*x*x + 0.1*x*y + 0.1*math.sqrt(abs(x))
    ret += (20.0*math.sin(6.0*x*pi) + 20.0*math.sin(2.0*x*pi)) * 2.0 / 3.0
    ret += (20.0*math.sin(x*pi) + 40.0*math.sin(x/3.0*pi)) * 2.0 / 3.0
    ret += (150.0*math.sin(x/12.0*pi) + 300*math.sin(x/30.0*pi)) * 2.0 / 3.0
    return ret

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

# 页面配置
st.set_page_config(page_title="无人机心跳监测", layout="wide")

# 初始化状态
if "heartbeat_data" not in st.session_state:
    st.session_state.heartbeat_data = []
    st.session_state.seq = 0
    st.session_state.last_receive_time = time.time()
    st.session_state.is_monitoring = False
    st.session_state.point_a = None
    st.session_state.point_b = None
    st.session_state.coord_system = "GCJ-02(高德/百度)"

# 侧边栏导航
st.sidebar.title("导航")
page = st.sidebar.radio("", ["航线规划", "飞行监控"], key="page")

# 航线规划
if page == "航线规划":
    st.title("🗺️ 航线规划")
    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("设置")
        coord = st.radio("坐标系", ["WGS-84", "GCJ-02(高德/百度)"], key="coord")
        st.session_state.coord_system = coord

        st.subheader("起点A")
        a_lat = st.number_input("A纬度", 32.2322, format="%.4f", key="a_lat")
        a_lng = st.number_input("A经度", 118.7490, format="%.4f", key="a_lng")
        if st.button("设置A点"):
            if coord == "GCJ-02(高德/百度)":
                wgs_lng, wgs_lat = gcj02_to_wgs84(a_lng, a_lat)
            else:
                wgs_lng, wgs_lat = a_lng, a_lat
            st.session_state.point_a = (wgs_lat, wgs_lng)

        st.subheader("终点B")
        b_lat = st.number_input("B纬度", 32.2343, format="%.4f", key="b_lat")
        b_lng = st.number_input("B经度", 118.7490, format="%.4f", key="b_lng")
        if st.button("设置B点"):
            if coord == "GCJ-02(高德/百度)":
                wgs_lng, wgs_lat = gcj02_to_wgs84(b_lng, b_lat)
            else:
                wgs_lng, wgs_lat = b_lng, b_lat
            st.session_state.point_b = (wgs_lat, wgs_lng)

        st.checkbox("A点已设", st.session_state.point_a is not None, disabled=True)
        st.checkbox("B点已设", st.session_state.point_b is not None, disabled=True)

    with col2:
        st.subheader("地图")
        center = st.session_state.point_a or (32.233, 118.749)
        m = folium.Map(location=center, zoom_start=17, tiles="OpenStreetMap")
        if st.session_state.point_a:
            folium.Marker(st.session_state.point_a, icon=folium.Icon(color="red"), popup="A").add_to(m)
        if st.session_state.point_b:
            folium.Marker(st.session_state.point_b, icon=folium.Icon(color="green"), popup="B").add_to(m)
        if st.session_state.point_a and st.session_state.point_b:
            folium.PolyLine([st.session_state.point_a, st.session_state.point_b], color="blue", weight=3).add_to(m)
        st_folium(m, width=900, height=600)

# 飞行监控
elif page == "飞行监控":
    st.title("✈️ 飞行监控")

    def simulate_heartbeat():
        st.session_state.seq += 1
        st.session_state.last_receive_time = time.time()
        st.session_state.heartbeat_data.append({
            "序号": st.session_state.seq,
            "时间": pd.Timestamp.now(),
            "正常": 1, "超时": 0
        })

    def check_timeout():
        if time.time() - st.session_state.last_receive_time > 3:
            st.session_state.heartbeat_data.append({
                "序号": st.session_state.seq,
                "时间": pd.Timestamp.now(),
                "正常": 0, "超时": 1
            })
            return True
        return False

    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("控制")
        if st.button("开始监测"):
            st.session_state.is_monitoring = True
        if st.button("停止监测"):
            st.session_state.is_monitoring = False

        if st.session_state.heartbeat_data:
            df = pd.DataFrame(st.session_state.heartbeat_data)
            st.metric("总心跳", len(df))
            st.metric("超时", df["超时"].sum())

    with col2:
        st.subheader("实时数据")
        placeholder = st.empty()
        while st.session_state.is_monitoring:
            simulate_heartbeat()
            timeout = check_timeout()
            df = pd.DataFrame(st.session_state.heartbeat_data)
            with placeholder:
                st.line_chart(df, x="时间", y=["正常", "超时"])
                st.dataframe(df.tail(10))
                if timeout:
                    st.error("⚠️ 连接超时！")
            time.sleep(1)
