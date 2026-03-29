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
        time.sleep(1)
