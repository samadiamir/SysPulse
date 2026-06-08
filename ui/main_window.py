from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
)

# from ui.dashboard_page import DashboardPage
# from ui.performance_page import PerformancePage
# from ui.hardware_page import HardwarePage
# from ui.health_page import HealthPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SysPulse")
        self.resize(1200, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        self.dashboard_btn = QPushButton("Dashboard")
        self.performance_btn = QPushButton("Performance")
        self.hardware_btn = QPushButton("Hardware")
        self.health_btn = QPushButton("Health")

        sidebar = QWidget()
        sidebar_layout = QHBoxLayout(sidebar)

        sidebar_layout.addWidget(self.dashboard_btn)
        sidebar_layout.addWidget(self.performance_btn)
        sidebar_layout.addWidget(self.hardware_btn)
        sidebar_layout.addWidget(self.health_btn)

        sidebar_layout.show()
