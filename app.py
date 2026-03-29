import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QRadioButton,
                             QButtonGroup, QLabel, QStackedWidget,
                             QMainWindow, QApplication)
from PyQt5.QtWebEngineWidgets import QWebEngineView
import sys

# ===================== 坐标系转换工具类 =====================
def gcj02_to_wgs84(lat, lng):
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
    return lat * 2 - mgLat, lng * 2 - mgLng

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

# ===================== 航线规划页面 =====================
class NavigationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 页面切换按钮
        self.btn_group = QButtonGroup(self)
        self.route_plan_btn = QRadioButton("航线规划")
        self.flight_monitor_btn = QRadioButton("飞行监控")
        self.btn_group.addButton(self.route_plan_btn, 0)
        self.btn_group.addButton(self.flight_monitor_btn, 1)
        self.route_plan_btn.setChecked(True)

        layout.addWidget(QLabel("导航功能"))
        layout.addWidget(self.route_plan_btn)
        layout.addWidget(self.flight_monitor_btn)

        # 坐标系切换
        layout.addWidget(QLabel("坐标系选择"))
        self.coord_group = QButtonGroup(self)
        self.wgs_btn = QRadioButton("WGS-84")
        self.gcj_btn = QRadioButton("GCJ-02")
        self.coord_group.addButton(self.wgs_btn, 0)
        self.coord_group.addButton(self.gcj_btn, 1)
        self.gcj_btn.setChecked(True)
        layout.addWidget(self.wgs_btn)
        layout.addWidget(self.gcj_btn)

        # 状态提示
        layout.addWidget(QLabel("系统状态"))
        self.status_a = QLabel("✅ A点已设置")
        self.status_b = QLabel("✅ B点已设置")
        layout.addWidget(self.status_a)
        layout.addWidget(self.status_b)

        # 地图组件
        self.map_view = QWebEngineView()
        self.map_view.setHtml(self.get_map_html())
        layout.addWidget(self.map_view)

        self.setLayout(layout)

    def get_map_html(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style> #map { height:400px; } </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([32.233, 118.75], 19);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
                var A = L.marker([32.232, 118.749]).addTo(map).bindPopup("起点A");
                var B = L.marker([32.234, 118.751]).addTo(map).bindPopup("终点B");
                L.polyline([[32.232,118.749],[32.234,118.751]],{color:"red",weight:3}).addTo(map);
            </script>
        </body>
        </html>
        """

# ===================== 飞行监控页面（心跳包） =====================
class FlightMonitorPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("=== 飞行监控 ==="))
        layout.addWidget(QLabel("实时心跳包显示区域"))
        self.heart_label = QLabel("等待心跳包数据...")
        layout.addWidget(self.heart_label)
        self.setLayout(layout)

    def update_heartbeat(self, data):
        self.heart_label.setText(f"[实时心跳] {data}")

# ===================== 主窗口 =====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("导航与飞行监控系统")
        self.setGeometry(100,100,900,700)

        # 堆栈窗口
        self.stack = QStackedWidget()
        self.nav_page = NavigationPage()
        self.monitor_page = FlightMonitorPage()
        self.stack.addWidget(self.nav_page)
        self.stack.addWidget(self.monitor_page)

        self.setCentralWidget(self.stack)

        # 绑定切换
        self.nav_page.btn_group.buttonClicked.connect(self.switch_page)

    def switch_page(self, btn):
        if btn == self.nav_page.route_plan_btn:
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)

# ===================== 启动程序 =====================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
