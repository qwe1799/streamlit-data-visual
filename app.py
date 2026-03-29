import streamlit as st

# 页面配置
st.set_page_config(
    page_title="无人机心跳监测与航线规划",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义导航（隐藏默认侧边栏，自定义菜单）
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# 侧边栏导航
st.sidebar.title("导航")
page = st.sidebar.radio("功能页面", ["航线规划", "飞行监控"])

# 页面路由
if page == "航线规划":
    st.switch_page("pages/1_航线规划.py")
else:
    st.switch_page("pages/2_飞行监控.py")

# 主页欢迎页
st.title("无人机通信监测平台")
st.markdown("""
### 功能说明
1. **航线规划**：设置A/B点、坐标系转换、障碍物标注
2. **飞行监控**：心跳包实时展示、掉线检测与告警
""")# 参考公开算法实现坐标转换
import math

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
    return retimport streamlit as st
import folium
from streamlit_folium import st_folium
from utils.coord import gcj02_to_wgs84, wgs84_to_gcj02

# 初始化会话状态
if "point_a" not in st.session_state:
    st.session_state.point_a = None
if "point_b" not in st.session_state:
    st.session_state.point_b = None
if "obstacles" not in st.session_state:
    st.session_state.obstacles = []
if "coord_system" not in st.session_state:
    st.session_state.coord_system = "GCJ-02"

st.title("📝 航线规划")
st.divider()

# 左侧：控制面板
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("控制面板")
    
    # 坐标系选择
    st.radio(
        "输入坐标系",
        ["WGS-84", "GCJ-02(高德/百度)"],
        index=1,
        key="coord_system",
        on_change=lambda: st.session_state.update({"point_a": None, "point_b": None})
    )
    
    # A点设置
    st.subheader("起点A")
    a_lat = st.number_input("纬度", value=32.2322, format="%.4f")
    a_lng = st.number_input("经度", value=118.7490, format="%.4f")
    if st.button("设置A点"):
        # 坐标转换：统一转为WGS-84用于地图显示
        if st.session_state.coord_system == "GCJ-02":
            wgs_lat, wgs_lng = gcj02_to_wgs84(a_lng, a_lat)
        else:
            wgs_lat, wgs_lng = a_lat, a_lng
        st.session_state.point_a = (wgs_lat, wgs_lng)
        st.success("A点设置成功")
    
    # B点设置
    st.subheader("终点B")
    b_lat = st.number_input("纬度", value=32.2343, format="%.4f")
    b_lng = st.number_input("经度", value=118.7490, format="%.4f")
    if st.button("设置B点"):
        if st.session_state.coord_system == "GCJ-02":
            wgs_lat, wgs_lng = gcj02_to_wgs84(b_lng, b_lat)
        else:
            wgs_lat, wgs_lng = b_lat, b_lng
        st.session_state.point_b = (wgs_lat, wgs_lng)
        st.success("B点设置成功")
    
    # 飞行参数
    st.subheader("飞行参数")
    flight_alt = st.slider("设定飞行高度(m)", 0, 100, 30)
    st.session_state.flight_alt = flight_alt

# 右侧：地图显示
with col2:
    st.subheader("地图")
    
    # 初始化地图（默认学校位置）
    if st.session_state.point_a:
        center = st.session_state.point_a
    else:
        center = (32.233, 118.749)  # 学校中心坐标
    
    m = folium.Map(location=center, zoom_start=18)
    
    # 绘制A点
    if st.session_state.point_a:
        folium.Marker(
            st.session_state.point_a,
            popup="起点A",
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(m)
    
    # 绘制B点
    if st.session_state.point_b:
        folium.Marker(
            st.session_state.point_b,
            popup="终点B",
            icon=folium.Icon(color="green", icon="flag")
        ).add_to(m)
    
    # 绘制AB连线
    if st.session_state.point_a and st.session_state.point_b:
        folium.PolyLine(
            locations=[st.session_state.point_a, st.session_state.point_b],
            color="blue",
            weight=3,
            dash_array="5,5"
        ).add_to(m)
    
    # 绘制障碍物（多边形）
    for obs in st.session_state.obstacles:
        folium.Polygon(
            locations=obs,
            color="orange",
            fill=True,
            fill_color="orange",
            fill_opacity=0.3
        ).add_to(m)
    
    # 地图渲染
    map_data = st_folium(m, width=800, height=500)
    
    # 障碍物添加（点击地图添加顶点）
    st.subheader("障碍物标注")
    if st.button("添加障碍物顶点"):
        if map_data["last_clicked"]:
            lat = map_data["last_clicked"]["lat"]
            lng = map_data["last_clicked"]["lng"]
            if "current_obs" not in st.session_state:
                st.session_state.current_obs = []
            st.session_state.current_obs.append((lat, lng))
            st.info(f"添加顶点：({lat:.4f}, {lng:.4f})")
    
    if st.button("完成障碍物"):
        if len(st.session_state.get("current_obs", [])) >= 3:
            st.session_state.obstacles.append(st.session_state.current_obs)
            del st.session_state.current_obs
            st.success("障碍物添加完成")
        else:
            st.warning("障碍物至少需要3个顶点")
    
    # 显示系统状态
    st.subheader("系统状态")
    st.checkbox("A点已设", value=st.session_state.point_a is not None, disabled=True)
    st.checkbox("B点已设", value=st.session_state.point_b is not None, disabled=True)import streamlit as st
import time
import pandas as pd
import numpy as np

st.title("📡 飞行监控")
st.divider()

# 初始化心跳数据
if "heartbeat_data" not in st.session_state:
    st.session_state.heartbeat_data = []
    st.session_state.seq = 0
    st.session_state.last_receive_time = time.time()
    st.session_state.is_monitoring = False

# 心跳模拟与掉线检测
def simulate_heartbeat():
    st.session_state.seq += 1
    current_time = pd.Timestamp.now()
    st.session_state.last_receive_time = time.time()
    st.session_state.heartbeat_data.append({
        "seq": st.session_state.seq,
        "time": current_time,
        "status": "正常"
    })

def check_timeout():
    current_time = time.time()
    if current_time - st.session_state.last_receive_time > 3:
        st.session_state.heartbeat_data.append({
            "seq": st.session_state.seq,
            "time": pd.Timestamp.now(),
            "status": "超时"
        })
        return True
    return False

# 控制面板
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("控制")
    if not st.session_state.is_monitoring:
        if st.button("开始监控"):
            st.session_state.is_monitoring = True
    else:
        if st.button("停止监控"):
            st.session_state.is_monitoring = False
    
    st.subheader("统计")
    if st.session_state.heartbeat_data:
        df = pd.DataFrame(st.session_state.heartbeat_data)
        total = len(df)
        timeout = len(df[df["status"] == "超时"])
        st.metric("总心跳包", total)
        st.metric("超时次数", timeout)

with col2:
    st.subheader("心跳包实时展示")
    # 定时更新
    placeholder = st.empty()
    while st.session_state.is_monitoring:
        simulate_heartbeat()
        timeout = check_timeout()
        df = pd.DataFrame(st.session_state.heartbeat_data)
        
        with placeholder.container():
            # 折线图
            st.line_chart(df, x="time", y="seq", color="status", use_container_width=True)
            
            # 数据表格
            st.dataframe(df.tail(10), use_container_width=True)
            
            # 超时告警
            if timeout:
                st.error("⚠️ 连接超时！3秒未收到心跳包")
        
        time.sleep(1)
    
    # 停止状态显示
    if not st.session_state.is_monitoring and st.session_state.heartbeat_data:
        df = pd.DataFrame(st.session_state.heartbeat_data)
        st.line_chart(df, x="time", y="seq", color="status", use_container_width=True)
        st.dataframe(df.tail(10), use_container_width=True)
