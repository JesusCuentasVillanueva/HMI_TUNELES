import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QGridLayout, QDoubleSpinBox,
                            QComboBox, QFrame, QMessageBox, QGroupBox, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
import qtawesome as qta

class SensorCalibrationWidget(QFrame):
    """Widget for calibrating a single sensor type"""
    
    def __init__(self, sensor_type, sensor_name, color_scheme, mqtt_client, parent=None):
        super().__init__(parent)
        self.sensor_type = sensor_type  # 'A', 'E', or 'I'
        self.sensor_name = sensor_name  # Display name
        self.color_scheme = color_scheme  # Dictionary with colors
        self.mqtt_client = mqtt_client
        self.calibration_values = [0.0] * 12  # One value per tunnel
        self.current_tunnel = 1
        
        self.setup_ui()
    
    def setup_ui(self):
        # Set frame style
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color_scheme['bg']};
                border-radius: 15px;
                border: 1px solid {self.color_scheme['border']};
                padding: 10px;
            }}
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel(f"Sensor {self.sensor_name}")
        header.setFont(QFont('Arial', 14, QFont.Bold))
        header.setStyleSheet(f"color: {self.color_scheme['text']}; margin-bottom: 5px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Description
        description = QLabel(f"Calibración para sensor tipo {self.sensor_type}")
        description.setFont(QFont('Arial', 10))
        description.setStyleSheet(f"color: {self.color_scheme['text']}; font-style: italic;")
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        
        # Current value display
        value_layout = QHBoxLayout()
        value_layout.setContentsMargins(5, 10, 5, 10)
        value_layout.setSpacing(10)
        
        value_label = QLabel("Valor:")
        value_label.setFont(QFont('Arial', 11))
        value_label.setStyleSheet(f"color: {self.color_scheme['text']};")
        value_layout.addWidget(value_label)
        
        self.value_spinbox = QDoubleSpinBox()
        self.value_spinbox.setRange(-10.0, 10.0)
        self.value_spinbox.setSingleStep(0.1)
        self.value_spinbox.setDecimals(1)
        self.value_spinbox.setFont(QFont('Arial', 12))
        self.value_spinbox.setStyleSheet(f"""
            QDoubleSpinBox {{
                border: 2px solid {self.color_scheme['border']};
                border-radius: 8px;
                padding: 5px;
                background-color: white;
                color: {self.color_scheme['text']};
                min-width: 100px;
                min-height: 30px;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                width: 20px;
                border-radius: 4px;
                background-color: {self.color_scheme['button']};
            }}
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {self.color_scheme['button_hover']};
            }}
        """)
        value_layout.addWidget(self.value_spinbox)
        
        # Apply button
        self.apply_button = QPushButton(qta.icon('fa5s.check'), "Aplicar")
        self.apply_button.setFont(QFont('Arial', 11))
        self.apply_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color_scheme['button']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 5px 10px;
                min-width: 80px;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: {self.color_scheme['button_hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.color_scheme['button_pressed']};
            }}
        """)
        self.apply_button.clicked.connect(self.apply_calibration)
        value_layout.addWidget(self.apply_button)
        
        layout.addLayout(value_layout)
        
        # Status message
        self.status_label = QLabel("Listo para calibrar")
        self.status_label.setFont(QFont('Arial', 10))
        self.status_label.setStyleSheet(f"""
            color: {self.color_scheme['text']};
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 8px;
            padding: 5px;
            font-style: italic;
            min-height: 15px;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def update_tunnel(self, tunnel_id):
        """Update the widget for the selected tunnel"""
        self.current_tunnel = tunnel_id
        self.value_spinbox.setValue(self.calibration_values[tunnel_id-1])
        self.status_label.setText(f"Listo para calibrar túnel {tunnel_id}")
    
    def apply_calibration(self):
        """Apply calibration for the current tunnel"""
        value = self.value_spinbox.value()
        self.calibration_values[self.current_tunnel-1] = value
        
        # Format the message: SXX,+/-XX.X
        tunnel_str = f"{self.current_tunnel:02d}"
        
        # Format the value with sign and proper decimal places
        if value >= 0:
            value_str = f"+{value:04.1f}"
        else:
            value_str = f"{value:05.1f}"
        
        # Construct the full message
        message = f"{self.sensor_type}{tunnel_str},{value_str}"
        
        # Send the message via MQTT
        try:
            self.mqtt_client.send_command(self.current_tunnel, 'calibration', message)
            self.status_label.setText(f"Calibración de {value:+.1f}°C aplicada al túnel {self.current_tunnel}")
            self.status_label.setStyleSheet("""
                color: #2e7d32;
                background-color: #e8f5e9;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            """)
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("""
                color: #c62828;
                background-color: #ffebee;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            """)

class CalibrationWindow(QMainWindow):
    """Window for calibrating temperature sensors"""
    
    def __init__(self, mqtt_client, parent=None):
        super().__init__(parent)
        self.mqtt_client = mqtt_client
        self.setWindowTitle("Calibración de Sensores")
        self.showFullScreen()
        
        # Define color schemes for each sensor type
        self.color_schemes = {
            'A': {  # Evaporator output (blue theme)
                'bg': '#e3f2fd',
                'border': '#2196f3',
                'text': '#0d47a1',
                'button': '#1976d2',
                'button_hover': '#1565c0',
                'button_pressed': '#0d47a1'
            },
            'E': {  # External box (green theme)
                'bg': '#e8f5e9',
                'border': '#4caf50',
                'text': '#1b5e20',
                'button': '#43a047',
                'button_hover': '#388e3c',
                'button_pressed': '#1b5e20'
            },
            'I': {  # Internal box (purple theme)
                'bg': '#f3e5f5',
                'border': '#9c27b0',
                'text': '#6a1b9a',
                'button': '#8e24aa',
                'button_hover': '#7b1fa2',
                'button_pressed': '#6a1b9a'
            }
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Set window background
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor('#f5f5f5'))
        self.setPalette(palette)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Title
        title = QLabel("Calibración de Sensores de Temperatura")
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setStyleSheet("""
            color: #212121;
            padding: 5px;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Tunnel selector
        tunnel_layout = QHBoxLayout()
        tunnel_label = QLabel("Túnel:")
        tunnel_label.setFont(QFont('Arial', 14))
        tunnel_label.setStyleSheet("color: #212121;")
        tunnel_layout.addWidget(tunnel_label)
        
        self.tunnel_selector = QComboBox()
        self.tunnel_selector.setFont(QFont('Arial', 14))
        self.tunnel_selector.setMinimumWidth(120)
        self.tunnel_selector.setStyleSheet("""
            QComboBox {
                border: 2px solid #bdbdbd;
                border-radius: 8px;
                padding: 5px;
                background-color: white;
                min-height: 30px;
            }
            QComboBox::drop-down {
                border: 0px;
                width: 25px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #bdbdbd;
                border-radius: 8px;
                background-color: white;
                selection-background-color: #e0e0e0;
            }
        """)
        
        # Add tunnels to selector
        for i in range(1, 13):
            self.tunnel_selector.addItem(f"Túnel {i}", i)
        
        tunnel_layout.addWidget(self.tunnel_selector)
        header_layout.addLayout(tunnel_layout)
        
        main_layout.addLayout(header_layout)
        
        # Sensor calibration widgets
        sensors_layout = QHBoxLayout()
        sensors_layout.setSpacing(15)
        
        # Evaporator output sensor (A)
        self.sensor_a_widget = SensorCalibrationWidget(
            'A', 
            'Salida del Evaporador', 
            self.color_schemes['A'],
            self.mqtt_client
        )
        sensors_layout.addWidget(self.sensor_a_widget)
        
        # External box sensor (E)
        self.sensor_e_widget = SensorCalibrationWidget(
            'E', 
            'Externo de Caja', 
            self.color_schemes['E'],
            self.mqtt_client
        )
        sensors_layout.addWidget(self.sensor_e_widget)
        
        # Internal box sensor (I)
        self.sensor_i_widget = SensorCalibrationWidget(
            'I', 
            'Interno de Caja', 
            self.color_schemes['I'],
            self.mqtt_client
        )
        sensors_layout.addWidget(self.sensor_i_widget)
        
        main_layout.addLayout(sensors_layout)
        
        # Information panel
        info_panel = QFrame()
        info_panel.setFrameStyle(QFrame.StyledPanel)
        info_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                padding: 10px;
                margin-top: 5px;
            }
        """)
        
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(5)
        
        info_title = QLabel("Información de Calibración")
        info_title.setFont(QFont('Arial', 12, QFont.Bold))
        info_title.setStyleSheet("color: #424242;")
        info_layout.addWidget(info_title)
        
        info_text = QLabel(
            "La calibración permite ajustar la lectura de los sensores para compensar desviaciones. "
            "Los valores positivos aumentan la temperatura mostrada, mientras que los negativos la disminuyen."
        )
        info_text.setWordWrap(True)
        info_text.setFont(QFont('Arial', 10))
        info_text.setStyleSheet("color: #616161; line-height: 1.3; margin-bottom: 5px;")
        info_layout.addWidget(info_text)
        
        # Add bullet points in a more structured way
        bullet_layout = QVBoxLayout()
        bullet_layout.setSpacing(3)
        
        sensor_types = [
            ("• Sensor A:", "Ubicado a la salida del evaporador"),
            ("• Sensor E:", "Ubicado en la parte externa de la caja de frutas"),
            ("• Sensor I:", "Ubicado en la parte interna de la caja de frutas")
        ]
        
        for bullet_title, bullet_desc in sensor_types:
            bullet_layout_item = QHBoxLayout()
            
            bullet_title_label = QLabel(bullet_title)
            bullet_title_label.setFont(QFont('Arial', 10))
            bullet_title_label.setStyleSheet("color: #424242; font-weight: bold;")
            bullet_layout_item.addWidget(bullet_title_label)
            
            bullet_desc_label = QLabel(bullet_desc)
            bullet_desc_label.setFont(QFont('Arial', 10))
            bullet_desc_label.setStyleSheet("color: #616161;")
            bullet_layout_item.addWidget(bullet_desc_label)
            
            bullet_layout_item.addStretch()
            bullet_layout.addLayout(bullet_layout_item)
        
        info_layout.addLayout(bullet_layout)
        main_layout.addWidget(info_panel)
        
        # Back button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        back_button = QPushButton(qta.icon('fa5s.arrow-left'), "Volver")
        back_button.setFont(QFont('Arial', 12))
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                min-width: 120px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """)
        back_button.clicked.connect(self.close)
        button_layout.addWidget(back_button)
        
        main_layout.addLayout(button_layout)
        
        # Connect tunnel selector to update values
        self.tunnel_selector.currentIndexChanged.connect(self.update_tunnel)
        
        # Initialize with first tunnel
        self.update_tunnel(0)
    
    def update_tunnel(self, index):
        """Update all sensor widgets with the selected tunnel"""
        tunnel_id = self.tunnel_selector.currentData()
        if tunnel_id and 1 <= tunnel_id <= 12:
            self.sensor_a_widget.update_tunnel(tunnel_id)
            self.sensor_e_widget.update_tunnel(tunnel_id)
            self.sensor_i_widget.update_tunnel(tunnel_id)