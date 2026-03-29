import streamlit as st
import time
import pandas as pd
import math
import folium
from streamlit_folium import st_folium

# ======================== 坐标转换工具函数 ========================
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

# ======================== 页面初始化 ========================
st.set_page_config(
    page_title="无人机心跳监测与航线规划",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化全局会话状态（提前初始化所有需要的key，避免赋值报错）
init_keys = [
    "heartbeat_data", "seq", "last_receive_time", "is_monitoring",
    "point_a", "point_b", "coord_system"
]
for key in init_keys:
    if key not in st.session_state:
        if key == "heartbeat_data":
            st.session_state[key] = []
        elif key == "seq":
            st.session_state[key] = 0
        elif key == "last_receive_time":
            st.session_state[key] = time.time()
        elif key == "is_monitoring":
            st.session_state[key] = False
        elif key == "coord_system":
            st.session_state[key] = "GCJ-02(高德/百度)"  # 初始化默认值
        else:
            st.session_state[key] = None

# ======================== 侧边栏导航 ========================
st.sidebar.title("📌 导航")
st.sidebar.subheader("功能页面")
page = st.sidebar.radio(
    "",
    ["航线规划", "飞行监控"],
    index=0,
    format_func=lambda x: "🗺️ 航线规划" if x == "航线规划" else "✈️ 飞行监控"
)

# ======================== 1. 航线规划页面（地图显示） ========================
if page == "航线规划":
    st.title("🗺️ 航线规划")
    st.divider()

    col_sidebar, col_map = st.columns([1, 3])

    with col_sidebar:
        st.subheader("⚙️ 坐标系设置")
        # 关键修复：将session_state赋值直接整合到st.radio的key中，无需手动赋值
        st.radio(
            "输入坐标系",
            ["WGS-84", "GCJ-02(高德/百度)"],
            index=1,
            key="coord_system"  # 直接用key绑定session_state，自动更新
        )

        st.divider()

        # 起点A设置
        st.subheader("📍 起点A")
        a_lat = st.number_input("纬度", value=32.2322, format="%.4f")
        a_lng = st.number_input("经度", value=118.7490, format="%.4f")
        if st.button("设置A点", use_container_width=True):
            if st.session_state.coord_system == "GCJ-02(高德/百度)":
                wgs_lng, wgs_lat = gcj02_to_wgs84(a_lng, a_lat)
            else:
                wgs_lng, wgs_lat = a_lng, a_lat
            st.session_state.point_a = (wgs_lat, wgs_lng)
            st.success("A点已设")

        # 终点B设置
        st.subheader("📍 终点B")
        b_lat = st.number_input("纬度", value=32.2343, format="%.4f")
        b_lng = st.number_input("经度", value=118.7490, format="%.4f")
        if st.button("设置B点", use_container_width=True):
            if st.session_state.coord_system == "GCJ-02(高德/百度)":
                wgs_lng, wgs_lat = gcj02_to_wgs84(b_lng, b_lat)
            else:
                wgs_lng, wgs_lat = b_lng, b_lat
            st.session_state.point_b = (wgs_lat, wgs_lng)
            st.success("B点已设")

        st.divider()

        # 系统状态展示
        st.subheader("📊 系统状态")
        st.checkbox("A点已设", value=st.session_state.point_a is not None, disabled=True)
        st.checkbox("B点已设", value=st.session_state.point_b is not None, disabled=True)

    with col_map:
        st.subheader("🗺️ 地图")
        # 初始化地图（高德瓦片源，国内稳定）
        map_center = st.session_state.point_a if st.session_state.point_a else (32.233, 118.749)
        m = folium.Map(
            location=map_center,
            zoom_start=18,
            tiles='http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            attr='高德地图'
        )

        # 绘制起点A
        if st.session_state.point_a:
            folium.Marker(
                location=st.session_state.point_a,
                popup="起点A",
                icon=folium.Icon(color="red", icon="flag")
            ).add_to(m)

        # 绘制终点B
        if st.session_state.point_b:
            folium.Marker(
                location=st.session_state.point_b,
                popup="终点B",
                icon=folium.Icon(color="green", icon="play")
            ).add_to(m)

        # 绘制AB航线
        if st.session_state.point_a and st.session_state.point_b:
            folium.PolyLine(
                locations=[st.session_state.point_a, st.session_state.point_b],
                color="blue",
                weight=3,
                dash_array="5,5"
            ).add_to(m)

        # 渲染地图
        st_folium(m, width=900, height=600, use_container_width=False)

# ======================== 2. 飞行监控页面（心跳包显示） ========================
elif page == "飞行监控":
    st.title("✈️ 飞行监控")
    st.divider()

    # 心跳模拟与断线检测
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

    col_ctrl, col_chart = st.columns([1, 3])
    with col_ctrl:
        st.subheader("🔧 控制")
        if not st.session_state.is_monitoring:
            if st.button("🚀 开始监测", type="primary", use_container_width=True):
                st.session_state.is_monitoring = True
        else:
            if st.button("🛑 停止监测", use_container_width=True):
                st.session_state.is_monitoring = False

        st.subheader("📊 统计")
        if st.session_state.heartbeat_data:
            df = pd.DataFrame(st.session_state.heartbeat_data)
            st.metric("总心跳包数", len(df))
            st.metric("超时次数", len(df[df["状态"] == "超时"]))

    with col_chart:
        st.subheader("📈 心跳包实时展示")
        placeholder = st.empty()
        while st.session_state.is_monitoring:
            simulate_heartbeat()
            is_timeout = check_timeout()
            df = pd.DataFrame(st.session_state.heartbeat_data)
            
            with placeholder.container():
                st.line_chart(df, x="时间", y="序号", color="状态", use_container_width=True)
                st.dataframe(df.tail(10), use_container_width=True)
                if is_timeout:
                    st.error("⚠️ 连接超时！3秒未收到心跳包")
            time.sleep(1)
        
        if st.session_state.heartbeat_data:
            df = pd.DataFrame(st.session_state.heartbeat_data)
            st.line_chart(df, x="时间", y="序号", color="状态", use_container_width=True)
            st.dataframe(df.tail(10), use_container_width=True)
