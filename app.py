import streamlit as st
import streamlit.components.v1 as components
import math
from datetime import datetime
import random
import time

# -------------------------- 页面基础配置 --------------------------
st.set_page_config(
    page_title="校园导航系统",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------- 自定义CSS（1:1还原图片样式） --------------------------
st.markdown("""
<style>
/* 全局样式 */
.stApp {
    background-color: #f5f7fa;
    max-width: 1200px;
    margin: 0 auto;
}

/* 标题样式 */
.main-title {
    font-size: 22px;
    font-weight: bold;
    color: #333;
    margin: 10px 0;
}

/* 模块分割线 */
.divider {
    margin: 15px 0;
    border-top: 1px solid #eee;
}

/* 状态标签 */
.status-box {
    background-color: #e6f4ea;
    color: #2e7d32;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 5px 0;
    font-size: 15px;
}

/* 单选按钮美化 */
.row-widget.stRadio > div {
    flex-direction: row;
    gap: 15px;
}

/* 坐标输入框样式 */
.css-1j3x20d {
    min-width: 120px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------- 坐标系转换工具函数 --------------------------
def gcj02_to_wgs84(lat, lng):
    """GCJ-02转WGS-84（国测局转地球坐标系）"""
    a = 6378245.0
    ee = 0.00669342162296594323
    dLat = _transform_lat(lng - 105.0, lat - 35.0)
    dLng = _transform_lng(lng - 105.0, lat - 35.0)
    radLat = lat / 180.0 * math.pi
    magic = math.sin(radLat)
    magic = 1 - ee * magic * magic
    sqrtMagic = math.sqrt(magic)
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * math.pi)
    dLng = (dLng * 180.0) / (a / sqrtMagic * math.cos(radLat) * math.pi)
    mgLat = lat + dLat
    mgLng = lng + dLng
    return round(lat * 2 - mgLat, 6), round(lng * 2 - mgLng, 6)

def _transform_lat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret

def _transform_lng(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret

# -------------------------- 校内坐标校验 --------------------------
def is_in_campus(lat, lng):
    """判断坐标是否在校内（匹配你图片的校园范围）"""
    CAMPUS_LAT_MIN, CAMPUS_LAT_MAX = 32.230, 32.240
    CAMPUS_LNG_MIN, CAMPUS_LNG_MAX = 118.745, 118.755
    return CAMPUS_LAT_MIN <= lat <= CAMPUS_LAT_MAX and CAMPUS_LNG_MIN <= lng <= CAMPUS_LNG_MAX

# -------------------------- 心跳包模拟函数 --------------------------
def get_heartbeat():
    """模拟实时心跳包数据"""
    return {
        "时间": datetime.now().strftime("%H:%M:%S"),
        "电压": round(random.uniform(11.5, 12.5), 2),
        "信号": random.randint(80, 100),
        "状态": "正常运行"
    }

# -------------------------- 地图HTML（3D+航线绘制） --------------------------
def map_html(lat_a, lng_a, lat_b, lng_b, coord_type, flight_height=50):
    # 坐标系转换
    if coord_type == "GCJ-02(高德/百度)":
        lat_a, lng_a = gcj02_to_wgs84(lat_a, lng_a)
        lat_b, lng_b = gcj02_to_wgs84(lat_b, lng_b)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>#map {{ height: 600px; width: 100%; border-radius: 8px; }}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{lat_a}, {lng_a}], 19);
            // 加载卫星底图（更贴近你图片的样式）
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{x}}/{{y}}', {{
                attribution: 'Tiles &copy; Esri'
            }}).addTo(map);
            
            // 绘制A点、B点、航线
            L.marker([{lat_a}, {lng_a}], {{icon: L.divIcon({{html: '<span style="color:red; font-size:24px;">📍</span>'}})}})
              .addTo(map).bindPopup("起点A");
            L.marker([{lat_b}, {lng_b}], {{icon: L.divIcon({{html: '<span style="color:green; font-size:24px;">▶️</span>'}})}})
              .addTo(map).bindPopup("终点B");
            L.polyline([[{lat_a}, {lng_a}], [{lat_b}, {lng_b}]], {{color: 'red', weight: 4, opacity: 0.7}}).addTo(map);
        </script>
    </body>
    </html>
    """

# -------------------------- 主界面渲染 --------------------------
st.markdown('<p class="main-title">🧭 导航</p>', unsafe_allow_html=True)
page = st.radio("", ["航线规划", "飞行监控"], index=0)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# 坐标系设置
st.markdown('<p class="main-title">⚙️ 坐标系设置</p>', unsafe_allow_html=True)
coord_type = st.radio("", ["WGS-84", "GCJ-02(高德/百度)"], index=1)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# -------------------------- 页面功能区 --------------------------
if page == "航线规划":
    col_map, col_ctrl = st.columns([2, 1])  # 地图:控制面板 = 2:1

    with col_ctrl:
        st.markdown("### 🎛️ 控制面板")
        st.markdown("#### 起点 A")
        st.caption(f"输入坐标系: {coord_type}")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            lat_a = st.number_input("纬度", value=32.2322, format="%.6f", step=0.0001)
        with col_a2:
            lng_a = st.number_input("经度", value=118.749, format="%.6f", step=0.0001)
        st.checkbox("设置A点", value=True, disabled=True)

        st.markdown("#### 终点 B")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            lat_b = st.number_input("纬度 ", value=32.2343, format="%.6f", step=0.0001)
        with col_b2:
            lng_b = st.number_input("经度 ", value=118.749, format="%.6f", step=0.0001)
        st.checkbox("设置B点", value=True, disabled=True)

        st.markdown("#### ✈️ 飞行参数")
        flight_height = st.slider("设定飞行高度(m)", min_value=10, max_value=200, value=50)

    with col_map:
        st.markdown("### 🗺️ 地图")
        # 坐标校验
        a_in = is_in_campus(lat_a, lng_a)
        b_in = is_in_campus(lat_b, lng_b)
        
        if a_in and b_in:
            st.success("✅ A、B点均在校内，可规划航线")
            # 渲染地图
            components.html(map_html(lat_a, lng_a, lat_b, lng_b, coord_type, flight_height), height=620)
        else:
            st.error("❌ 坐标超出校内范围，请重新输入！")

else:
    st.markdown("### 💓 飞行监控 & 心跳包")
    st.subheader("实时心跳包数据")
    
    # 实时刷新心跳包
    placeholder = st.empty()
    while True:
        data = get_heartbeat()
        with placeholder.container():
            st.metric("当前时间", data["时间"])
            c1, c2 = st.columns(2)
            c1.metric("电池电压(V)", data["电压"])
            c2.metric("信号强度(%)", data["信号"])
            st.success(f"设备状态：{data['状态']}")
        time.sleep(1)
