import sys
import yaml
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout,
                             QPushButton, QLabel, QDoubleSpinBox, QVBoxLayout,
                             QHBoxLayout, QFrame, QTabWidget, QMessageBox,
                             QLineEdit, QFormLayout, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
import qtawesome as qta
from mqtt_client import MQTTClient
from setpoint_window import SetpointWindow
# Add this import at the top of the file with the other imports
from calibration_window import CalibrationWindow

class TunnelWidget(QFrame):
    def __init__(self, tunnel_id, mqtt_client, parent=None):
        super().__init__(parent)
        self.tunnel_id = tunnel_id
        self.mqtt_client = mqtt_client
        self.running = False
        self.defrosting = False
        self.setup_ui()
        self.connect_signals()
        
        # Ensure MQTT client is properly initialized
        if not hasattr(self.mqtt_client, 'client'):
            self.mqtt_client = MQTTClient()
            self.mqtt_client.temperature_updated.connect(self.update_temperature)
            self.mqtt_client.defrost_status_updated.connect(self.update_defrost_status)
            self.mqtt_client.tunnel_status_updated.connect(self.update_running_status)
            self.mqtt_client.connection_status.connect(self.handle_connection_status)
            self.mqtt_client.connect()

    def toggle_running(self):
        """Toggle the running state of the tunnel"""
        self.running = not self.running
        
        # Update button text and icon
        if self.running:
            self.start_button.setText("Iniciar")
            self.start_button.setIcon(qta.icon('fa5s.play'))
            self.start_button.setEnabled(False)
            self.stop_button.setText("Detener")
            self.stop_button.setIcon(qta.icon('fa5s.stop'))
            self.stop_button.setEnabled(True)
            self.running_status.setText("Estado: Encendido")
        else:
            self.start_button.setText("Iniciar")
            self.start_button.setIcon(qta.icon('fa5s.play'))
            self.start_button.setEnabled(True)
            self.stop_button.setText("Detener")
            self.stop_button.setIcon(qta.icon('fa5s.stop'))
            self.stop_button.setEnabled(False)
            self.running_status.setText("Estado: Apagado")
        
        # Send command to MQTT
        command_type = 'start' if self.running else 'stop'
        self.mqtt_client.send_command(self.tunnel_id, command_type)

    def toggle_defrost(self):
        """Toggle the defrost state of the tunnel"""
        self.defrosting = not self.defrosting
        
        # Update button text and icon
        if self.defrosting:
            self.defrost_button.setText("Descongelar ON")
            self.defrost_button.setIcon(qta.icon('fa5s.snowflake'))
            self.defrost_status.setText("Descongelamiento: Encendido")
            # Format tunnel number as two digits (XX) and set the command to XX,1,0 format for ON
            message = f"{self.tunnel_id:02d},1,0"
        else:
            self.defrost_button.setText("Descongelar OFF")
            self.defrost_button.setIcon(qta.icon('fa5s.snowflake'))
            self.defrost_status.setText("Descongelamiento: Apagado")
            # Format tunnel number as two digits (XX) and set the command to XX,0,0 format for OFF
            message = f"{self.tunnel_id:02d},0,0"
        
        # Update button state
        self.defrost_button.setChecked(self.defrosting)
        
        # Send command to MQTT
        command_type = 'defrost'
        self.mqtt_client.send_command(self.tunnel_id, command_type, message)

    def setup_ui(self):
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setAutoFillBackground(True)
        
        # Set widget style
        self.setStyleSheet('''
TunnelWidget {
    background-color: #ffffff;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.05);
}
QPushButton {
    background-color: #4caf50;
    border: none;
    border-radius: 12px;
    padding: 12px 25px;
    color: white;
    font-weight: 600;
    min-width: 180px;
    margin: 10px;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    transition: all 0.2s ease;
}
QPushButton:hover {
    background-color: #43a047;
    transform: translateY(-1px);
}
QPushButton:disabled {
    background-color: #a5d6a7;
    color: rgba(255, 255, 255, 0.7);
}
QPushButton:checked {
    background-color: #388e3c;
}
QPushButton#defrostButton {
    background-color: #81c784;
}
QPushButton#defrostButton:checked {
    background-color: #7cb342;
}
QLabel {
    padding: 10px;
    font-size: 18px;
    color: #212121;
    font-weight: 600;
    margin: 8px;
}
QLabel[temperature="true"] {
    font-size: 38px;
    font-weight: bold;
    color: #388e3c;
    margin: 12px 0;
    min-width: 140px;
    min-height: 55px;
}
QDoubleSpinBox {
    border: none;
    border-radius: 10px;
    padding: 12px;
    font-size: 16px;
    background-color: #ffffff;
    color: #212121;
    min-width: 180px;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
}
QDoubleSpinBox:hover {
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
}
QDoubleSpinBox:focus {
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.15);
}
QFrame {
    border: none;
    border-radius: 15px;
    background-color: #ffffff;
    padding: 20px;
    margin: 15px;
}
QFrame:hover {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}
''')

        # Create main layout
        layout = QVBoxLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel(f"Túnel {self.tunnel_id}")
        title.setFont(QFont('Arial', 100, QFont.Bold))
        title.setStyleSheet('font-size: 60px; font-weight: bold;')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(2)
        
        # Add setpoint labels container
        setpoint_container = QWidget()
        setpoint_layout = QHBoxLayout(setpoint_container)
        setpoint_layout.setContentsMargins(5, 0, 5, 0)
        setpoint_layout.setSpacing(10)
        
        # Tunnel setpoint label
        self.tunnel_setpoint_label = QLabel("Túnel: --.-°C")
        self.tunnel_setpoint_label.setAlignment(Qt.AlignCenter)
        self.tunnel_setpoint_label.setStyleSheet("""
            QLabel {
                color: #1B5E20;
                font-size: 16px;
                font-weight: bold;
                background-color: #E8F5E9;
                border-radius: 8px;
                padding: 8px 12px;
                margin: 5px;
            }
        """)
        setpoint_layout.addWidget(self.tunnel_setpoint_label)
        
        # Fruit setpoint label
        self.fruit_setpoint_label = QLabel("Fruta: --.-°C")
        self.fruit_setpoint_label.setAlignment(Qt.AlignCenter)
        self.fruit_setpoint_label.setStyleSheet("""
            QLabel {
                color: #6A1B9A;
                font-size: 16px;
                font-weight: bold;
                background-color: #F3E5F5;
                border-radius: 8px;
                padding: 8px 12px;
                margin: 5px;
            }
        """)
        setpoint_layout.addWidget(self.fruit_setpoint_label)
        
        layout.addWidget(setpoint_container)
        
        # Remove this redundant setpoint label
        # self.setpoint_label = QLabel("Setpoint: --.-°C")
        # self.setpoint_label.setAlignment(Qt.AlignCenter)
        # self.setpoint_label.setStyleSheet("""
        #     QLabel {
        #         color: #1B5E20;
        #         font-size: 16px;
        #         font-weight: bold;
        #         background-color: #E8F5E9;
        #         border-radius: 8px;
        #         padding: 8px 12px;
        #         margin: 5px;
        #     }
        # """)
        # layout.addWidget(self.setpoint_label)
        
        # Status Frame
        status_layout = QVBoxLayout()
        status_layout.setSpacing(10)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # Running status
        self.running_status = QLabel("Estado: Apagado")
        self.running_status.setStyleSheet('''
            color: #d32f2f;
            font-weight: bold;
            padding: 12px;
            border-radius: 8px;
            background-color: #ffebee;
            font-size: 16px;
            margin: 5px;
        ''')
        self.running_status.setFixedHeight(50)
        self.running_status.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.running_status)
        
        # Defrost status
        self.defrost_status = QLabel("Descongelamiento: Inactivo")
        self.defrost_status.setStyleSheet('''
            color: #d32f2f;
            font-weight: bold;
            padding: 12px;
            border-radius: 8px;
            background-color: #ffebee;
            font-size: 16px;
            margin: 5px;
        ''')
        self.defrost_status.setFixedHeight(50)
        self.defrost_status.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.defrost_status)
        
        layout.addLayout(status_layout)

        # Temperature Grid
        temp_grid = QGridLayout()
        temp_grid.setSpacing(15)
        
        # Output Temperature
        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setAlignment(Qt.AlignVCenter)
        
        output_label = QLabel("T. Salida:")
        output_label.setStyleSheet('''
            color: #388e3c;
            font-weight: bold;
            font-size: 18px;
            padding: 0px 6px;
            min-height: 40px;
            align-self: center;
        ''')
        output_layout.addWidget(output_label)
        
        self.temp_output = QLabel("--.-°C")
        self.temp_output.setProperty("temperature", "true")
        self.temp_output.setStyleSheet('''
            font-size: 32px;
            font-weight: bold;
            color: #388e3c;
            padding: 0px 8px;
            min-width: 110px;
            min-height: 40px;
        ''')
        output_layout.addWidget(self.temp_output)
        
        # External Temperature
        external_layout = QHBoxLayout()
        external_layout.setSpacing(10)
        external_layout.setContentsMargins(0, 0, 0, 0)
        external_layout.setAlignment(Qt.AlignVCenter)
        
        external_label = QLabel("T. Externa:")
        external_label.setStyleSheet('''
            color: #7cb342;
            font-weight: bold;
            font-size: 18px;
            padding: 0px 6px;
            min-height: 40px;
            align-self: center;
        ''')
        external_layout.addWidget(external_label)
        
        self.temp_external = QLabel("--.-°C")
        self.temp_external.setProperty("temperature", "true")
        self.temp_external.setStyleSheet('''
            font-size: 32px;
            font-weight: bold;
            color: #7cb342;
            padding: 0px 8px;
            min-width: 110px;
            min-height: 40px;
        ''')
        external_layout.addWidget(self.temp_external)
        
        # Internal Temperature
        internal_layout = QHBoxLayout()
        internal_layout.setSpacing(10)
        internal_layout.setContentsMargins(0, 0, 0, 0)
        internal_layout.setAlignment(Qt.AlignVCenter)
        
        internal_label = QLabel("T. Interna:")
        internal_label.setStyleSheet('''
            color: #43a047;
            font-weight: bold;
            font-size: 18px;
            padding: 0px 6px;
            min-height: 40px;
            align-self: center;
        ''')
        internal_layout.addWidget(internal_label)
        
        self.temp_internal = QLabel("--.-°C")
        self.temp_internal.setProperty("temperature", "true")
        self.temp_internal.setStyleSheet('''
            font-size: 32px;
            font-weight: bold;
            color: #43a047;
            padding: 0px 8px;
            min-width: 110px;
            min-height: 40px;
        ''')
        internal_layout.addWidget(self.temp_internal)
        
        temp_grid.addLayout(output_layout, 0, 0)
        temp_grid.addLayout(external_layout, 1, 0)
        temp_grid.addLayout(internal_layout, 2, 0)
        layout.addLayout(temp_grid)
        
        # Setpoint Button
        setpoint_button = QPushButton(qta.icon('fa5s.cog', color='#4caf50'), "Configurar Setpoint")
        setpoint_button.setStyleSheet("""
            QPushButton {
                background-color: #e8f5e9;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                color: #212121;
                font-weight: 600;
                min-width: 180px;
                font-size: 16px;
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #c8e6c9;
            }
            QPushButton:pressed {
                background-color: #4caf50;
                color: white;
            }
        """)
        setpoint_button.clicked.connect(lambda: self.open_setpoint_window(self.tunnel_id))
        layout.addWidget(setpoint_button)
        
        # Control Buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setAlignment(Qt.AlignCenter)
        
        # Start Button
        self.start_button = QPushButton(qta.icon('fa5s.play'), "Iniciar")
        self.start_button.setObjectName("startButton")
        self.start_button.setFixedHeight(70)
        self.start_button.setFixedWidth(200)
        button_layout.addWidget(self.start_button)
        
        # Stop Button
        self.stop_button = QPushButton(qta.icon('fa5s.stop'), "Detener")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setFixedHeight(70)
        self.stop_button.setFixedWidth(200)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        # Defrost Button
        self.defrost_button = QPushButton(qta.icon('fa5s.snowflake'), "Descongelar OFF")
        self.defrost_button.setObjectName("defrostButton")
        self.defrost_button.setFixedHeight(70)
        self.defrost_button.setFixedWidth(200)
        button_layout.addWidget(self.defrost_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        # Connect signals only once
        self.start_button.clicked.connect(self.toggle_running)
        self.stop_button.clicked.connect(self.toggle_running)
        self.defrost_button.clicked.connect(self.toggle_defrost)
    
    def start_tunnel(self):
        """Start the tunnel operation"""
        self.running = True
        self.start_button.setText("Detener")
        self.start_button.setIcon(qta.icon('fa5s.stop'))
        self.running_status.setText("Estado: Encendido")
        self.start_button.setChecked(True)
        
        # Send command to MQTT
        command = f"{self.tunnel_id},{1 if self.running else 0},1"
        self.mqtt_client.send_command(command)
    
    def stop_tunnel(self):
        """Stop the tunnel operation"""
        self.running = False
        self.start_button.setText("Iniciar")
        self.start_button.setIcon(qta.icon('fa5s.play'))
        self.running_status.setText("Estado: Apagado")
        self.start_button.setChecked(False)
        
        # Send command to MQTT
        command = f"{self.tunnel_id},{1 if self.running else 0},1"
        self.mqtt_client.send_command(command)
    
    def defrost_tunnel(self):
        is_checked = self.defrost_button.isChecked()
        self.defrost_button.setText("Descongelar ON" if is_checked else "Descongelar OFF")
        # Format tunnel number as two digits (XX) for the XX,1,0 format
        self.mqtt_client.send_command(self.tunnel_id, 'defrost', f"{self.tunnel_id:02d},1,0")
    
    def open_setpoint_window(self, tunnel_id):
        try:
            # Close existing window if it exists
            if hasattr(self, 'setpoint_window') and self.setpoint_window:
                self.setpoint_window.close()
                self.setpoint_window = None
            
            # Create and show new setpoint window
            self.setpoint_window = SetpointWindow(self.mqtt_client)
            self.setpoint_window.showFullScreen()
            
            # Connect signals for cleanup
            self.setpoint_window.destroyed.connect(lambda: setattr(self, 'setpoint_window', None))
            
        except Exception as e:
            # Handle cleanup in case of error
            if hasattr(self, 'setpoint_window') and self.setpoint_window:
                self.setpoint_window.close()
                self.setpoint_window = None
            QMessageBox.critical(self, "Error", f"Error al abrir la ventana de setpoints: {str(e)}")
    
    def open_calibration_window(self):
        try:
            # Close existing window if it exists
            if hasattr(self, 'calibration_window') and self.calibration_window:
                self.calibration_window.close()
                self.calibration_window = None
            
            # Create and show new calibration window
            self.calibration_window = CalibrationWindow(self.mqtt_client)
            self.calibration_window.showFullScreen()
            
            # Connect signals for cleanup
            self.calibration_window.destroyed.connect(lambda: setattr(self, 'calibration_window', None))
            
        except Exception as e:
            # Handle cleanup in case of error
            if hasattr(self, 'calibration_window') and self.calibration_window:
                self.calibration_window.close()
                self.calibration_window = None
            QMessageBox.critical(self, "Error", f"Error al abrir la ventana de calibración: {str(e)}")
    
    def update_temperature(self, output_temp, external_temp, internal_temp):
        self.temp_output.setText(f"{output_temp:.1f}°C")
        self.temp_external.setText(f"{external_temp:.1f}°C")
        self.temp_internal.setText(f"{internal_temp:.1f}°C")

    def update_running_status(self, is_running):
        status_text = "Estado: Encendido" if is_running else "Estado: Apagado"
        status_color = "#2e7d32" if is_running else "#d32f2f"
        status_bg = "#e8f5e9" if is_running else "#ffebee"
        self.running_status.setText(status_text)
        self.running_status.setStyleSheet(f"""
            color: {status_color}; 
            font-weight: bold; 
            padding: 12px; 
            background: {status_bg}; 
            border-radius: 8px; 
            font-size: 16px;
            margin: 5px;
        """)

    def update_defrost_status(self, is_defrosting):
        status_text = "Descongelamiento: Activo" if is_defrosting else "Descongelamiento: Inactivo"
        status_color = "#1565c0" if is_defrosting else "#d32f2f"
        status_bg = "#e3f2fd" if is_defrosting else "#ffebee"
        self.defrost_status.setText(status_text)
        self.defrost_status.setStyleSheet(f"""
            color: {status_color}; 
            font-weight: bold; 
            padding: 12px; 
            background: {status_bg}; 
            border-radius: 8px; 
            font-size: 16px;
            margin: 5px;
        """)

    def update_tunnel_setpoint(self, setpoint_value):
        """Update the tunnel setpoint display"""
        self.tunnel_setpoint_label.setText(f"Túnel: {setpoint_value:.1f}°C")
        
    def update_fruit_setpoint(self, setpoint_value):
        """Update the fruit setpoint display"""
        self.fruit_setpoint_label.setText(f"Fruta: {setpoint_value:.2f}°C")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Túneles de Enfriamiento")
        
        # Cross-platform fullscreen handling
        if sys.platform.startswith('linux'):
            # Linux-specific handling para pantalla de 21cm x 16cm
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            # Convertir cm a píxeles (aproximadamente 38 píxeles por cm en pantallas de 96 DPI)
            width_px = int(21 * 38)  # ~800px
            height_px = int(16 * 38)  # ~608px
            self.setFixedSize(width_px, height_px)
            self.setGeometry(0, 0, width_px, height_px)
        else:
            # Windows default behavior
            self.showFullScreen()
        
        # Initialize MQTT client with configuration
        self.mqtt_client = MQTTClient()
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
                self.mqtt_client.configure(config['mqtt'])
            self.mqtt_client.temperature_updated.connect(self.update_temperature)
            self.mqtt_client.defrost_status_updated.connect(self.update_defrost_status)
            self.mqtt_client.tunnel_status_updated.connect(self.update_running_status)
            self.mqtt_client.connection_status.connect(self.handle_connection_status)
            
            # Connect the message_received signal to our handler
            self.mqtt_client.message_received.connect(self.on_mqtt_message)
            
            # Configuration authentication
            self.is_config_authenticated = False
            self.config_access_code = self.mqtt_client.config.get('access_code', 'migiva')
            
            self.setup_ui()
            
            # Start connection after UI is set up
            self.mqtt_client.connect()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al inicializar el cliente MQTT: {str(e)}")

    def handle_connection_status(self, is_connected):
        """Handle MQTT connection status changes"""
        status_text = "Conectado" if is_connected else "Desconectado"
        status_color = "#4caf50" if is_connected else "#f44336"
        self.connection_status.setText(f"Estado MQTT: {status_text}")
        self.connection_status.setStyleSheet(f"""
            QLabel {{
                color: {status_color};
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                background-color: rgba(76, 175, 80, 0.1);
            }}
        """)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create status bar
        status_bar = QHBoxLayout()
        status_bar.setContentsMargins(20, 10, 20, 10)
        
        # Connection status label
        self.connection_status = QLabel("Estado MQTT: Desconectado")
        self.connection_status.setStyleSheet("""
            QLabel {
                color: #f44336;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                background-color: rgba(244, 67, 54, 0.1);
            }
        """)
        status_bar.addWidget(self.connection_status)
        
        # Add calibration button
        calibration_button = QPushButton(qta.icon('fa5s.sliders-h'), "Calibración")
        calibration_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
        """)
        calibration_button.clicked.connect(self.open_calibration_window)
        status_bar.addStretch()  # Add stretch to push connection status to the left and calibration button to the right
        status_bar.addWidget(calibration_button)
        
        # Add status bar to main layout
        main_layout.addLayout(status_bar)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Monitoring tab
        monitoring_tab = QWidget()
        grid_layout = QGridLayout(monitoring_tab)
        
        # Create carousel layout
        carousel_layout = QHBoxLayout()
        
        # Previous button
        prev_button = QPushButton(qta.icon('fa5s.chevron-left'), "")
        prev_button.setFixedWidth(50)
        carousel_layout.addWidget(prev_button)
        
        # Stacked widget for tunnel groups
        self.tunnel_stack = QStackedWidget()
        carousel_layout.addWidget(self.tunnel_stack)
        
        # Next button
        next_button = QPushButton(qta.icon('fa5s.chevron-right'), "")
        next_button.setFixedWidth(50)
        carousel_layout.addWidget(next_button)
        
        # Create tunnel widgets in groups of 3
        self.tunnel_widgets = []
        num_groups = (12 + 2) // 3  # Ceiling division to get number of groups
        
        for group in range(num_groups):
            group_widget = QWidget()
            group_layout = QHBoxLayout(group_widget)
            
            # Add 3 tunnels to this group
            for i in range(3):
                tunnel_index = group * 3 + i
                if tunnel_index < 12:  # Only create valid tunnel widgets
                    tunnel_widget = TunnelWidget(tunnel_index + 1, self.mqtt_client)
                    tunnel_widget.setMinimumWidth(300)  # Set minimum width for better spacing
                    tunnel_widget.setMinimumHeight(700)  # Set minimum height to accommodate vertical buttons
                    group_layout.addWidget(tunnel_widget)
                    self.tunnel_widgets.append(tunnel_widget)
            
            self.tunnel_stack.addWidget(group_widget)
        
        # Connect navigation buttons
        prev_button.clicked.connect(lambda: self.tunnel_stack.setCurrentIndex(
            (self.tunnel_stack.currentIndex() - 1) % self.tunnel_stack.count()))
        next_button.clicked.connect(lambda: self.tunnel_stack.setCurrentIndex(
            (self.tunnel_stack.currentIndex() + 1) % self.tunnel_stack.count()))
        
        # Add carousel to monitoring tab
        grid_layout.addLayout(carousel_layout, 0, 0, 1, 1)
        
        tab_widget.addTab(monitoring_tab, "Monitoreo")
        
        # Configuration tab
        config_tab = QWidget()
        config_layout = QFormLayout(config_tab)
        
        # Authentication Section
        auth_layout = QHBoxLayout()
        auth_label = QLabel("Clave de acceso:")
        auth_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.auth_input = QLineEdit()
        self.auth_input.setEchoMode(QLineEdit.Password)
        self.auth_input.setPlaceholderText("Ingrese clave de acceso")
        self.auth_button = QPushButton("Autenticar")
        self.auth_button.clicked.connect(self.authenticate)
        auth_layout.addWidget(auth_label)
        auth_layout.addWidget(self.auth_input)
        auth_layout.addWidget(self.auth_button)
        config_layout.addRow(auth_layout)
        
        # MQTT Broker settings
        self.broker_input = QLineEdit(self.mqtt_client.config['broker'])
        self.port_input = QLineEdit(str(self.mqtt_client.config['port']))
        
        # Access code
        self.access_code_input = QLineEdit()
        self.access_code_input.setEchoMode(QLineEdit.Password)
        self.access_code_input.setPlaceholderText("Ingrese clave de acceso")
        
        # Topic patterns
        self.send_topic_input = QLineEdit(self.mqtt_client.config['topics']['send'])
        self.receive_topic_input = QLineEdit(self.mqtt_client.config['topics']['receive'])
        
        # Command messages
        self.start_msg_input = QLineEdit('start')
        self.stop_msg_input = QLineEdit('stop')
        
        # Add fields to form layout
        config_layout.addRow("Broker:", self.broker_input)
        config_layout.addRow("Puerto:", self.port_input)
        config_layout.addRow("Clave de Acceso:", self.access_code_input)
        config_layout.addRow("Tópico Enviar:", self.send_topic_input)
        config_layout.addRow("Tópico Recibir:", self.receive_topic_input)
        config_layout.addRow("Mensaje Inicio:", self.start_msg_input)
        config_layout.addRow("Mensaje Detener:", self.stop_msg_input)
        
        # Save button
        save_button = QPushButton("Guardar Configuración")
        save_button.clicked.connect(self.save_config)
        config_layout.addRow(save_button)
        
        # Disable configuration fields until authenticated
        self.disable_config_fields()
        
        tab_widget.addTab(config_tab, "Configuración")
        
        # Add tabs to main layout
        main_layout.addWidget(tab_widget)
    
    def update_temperature(self, tunnel_id, output_temp, external_temp, internal_temp):
        if 1 <= tunnel_id <= 12:
            self.tunnel_widgets[tunnel_id - 1].update_temperature(output_temp, external_temp, internal_temp)
    
    def update_defrost_status(self, tunnel_id, is_defrosting):
        if 1 <= tunnel_id <= 12:
            self.tunnel_widgets[tunnel_id - 1].update_defrost_status(is_defrosting)

    def update_running_status(self, tunnel_id, is_running):
        if 1 <= tunnel_id <= 12:
            self.tunnel_widgets[tunnel_id - 1].update_running_status(is_running)
    
    def handle_connection_status(self, connected):
        # Update connection status label
        status_text = "Conectado" if connected else "Desconectado"
        status_color = "#4caf50" if connected else "#f44336"
        status_bg = "rgba(76, 175, 80, 0.1)" if connected else "rgba(244, 67, 54, 0.1)"
        self.connection_status.setText(f"Estado MQTT: {status_text}")
        self.connection_status.setStyleSheet(f"""
            QLabel {{
                color: {status_color};
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                background-color: {status_bg};
            }}
        """)
        
        # Show warning only when disconnected
        if not connected:
            QMessageBox.warning(self, "Error de Conexión",
                              "Se perdió la conexión con el broker MQTT.\n"
                              "Verifique la conexión y reinicie la aplicación.")
    
    def open_calibration_window(self):
        try:
            # Close existing window if it exists
            if hasattr(self, 'calibration_window') and self.calibration_window:
                self.calibration_window.close()
                self.calibration_window = None
            
            # Create and show new calibration window
            self.calibration_window = CalibrationWindow(self.mqtt_client)
            self.calibration_window.showFullScreen()
            
            # Connect signals for cleanup
            self.calibration_window.destroyed.connect(lambda: setattr(self, 'calibration_window', None))
            
        except Exception as e:
            # Handle cleanup in case of error
            if hasattr(self, 'calibration_window') and self.calibration_window:
                self.calibration_window.close()
                self.calibration_window = None
            QMessageBox.critical(self, "Error", f"Error al abrir la ventana de calibración: {str(e)}")
    
    def authenticate(self):
        input_code = self.auth_input.text()
        if input_code == 'migiva' or input_code == self.config_access_code:
            self.is_config_authenticated = True
            self.enable_config_fields()
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Autenticación Exitosa")
            msg.setText("<h3 style='color: #2e7d32;'>Acceso Concedido</h3>")
            msg.setInformativeText("Ahora puede configurar los parámetros del sistema.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #43a047;
                }
            """)
            msg.exec_()
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Error de Autenticación")
            msg.setText("<h3 style='color: #c62828;'>Clave de Acceso Incorrecta</h3>")
            msg.setInformativeText("Por favor, intente nuevamente con la clave correcta.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #e53935;
                }
            """)
            msg.exec_()
            self.auth_input.clear()

    def disable_config_fields(self):
        self.broker_input.setEnabled(False)
        self.port_input.setEnabled(False)
        self.access_code_input.setEnabled(False)
        self.send_topic_input.setEnabled(False)
        self.receive_topic_input.setEnabled(False)
        self.start_msg_input.setEnabled(False)
        self.stop_msg_input.setEnabled(False)
        
    def enable_config_fields(self):
        self.broker_input.setEnabled(True)
        self.port_input.setEnabled(True)
        self.access_code_input.setEnabled(True)
        self.send_topic_input.setEnabled(True)
        self.receive_topic_input.setEnabled(True)
        self.start_msg_input.setEnabled(True)
        self.stop_msg_input.setEnabled(True)
    
    def save_config(self):
        if not self.is_config_authenticated:
            QMessageBox.warning(self, "Error", "Debe autenticarse primero para guardar la configuración")
            return
            
        config = {
            'mqtt': {
                'broker': self.broker_input.text(),
                'port': int(self.port_input.text()),
                'access_code': self.access_code_input.text(),
                'topics': {
                    'send': self.send_topic_input.text(),
                    'receive': self.receive_topic_input.text()
                },
                'messages': {
                    'start': self.start_msg_input.text(),
                    'stop': self.stop_msg_input.text()
                }
            }
        }
        
        # Save to config file
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f)
        
        # Update MQTT client configuration
        self.mqtt_client.configure(config['mqtt'])
        
        QMessageBox.information(self, "Configuración", "Configuración guardada exitosamente.")
        
    def on_mqtt_message(self, topic, payload):
        try:
            # Check if this is a message from the A_ENVIAR topic
            if topic == self.mqtt_client.config['topics']['receive']:
                # Check if it's a setpoint message format (SXX,+/-XX.XX or FXX,+/-XX.XX)
                if (payload.startswith("S") or payload.startswith("F")) and len(payload) >= 9:
                    self.handle_setpoint_message(payload)
                    return
                
                # Handle the new comma-separated values format
                # Format: TXX,T.S,T.E,T.I,SP_Tunel,SP_Fruta,Estado_PID,Estado_Ventilador
                values = payload.split(',')
                
                # Process values in groups of 8
                for i in range(0, len(values), 8):
                    if i + 7 < len(values):  # Ensure we have a complete set of 8 values
                        try:
                            # Extract tunnel identifier (TXX format)
                            tunnel_identifier = values[i].strip()
                            if tunnel_identifier.startswith('T') and len(tunnel_identifier) >= 3:
                                tunnel_id = int(tunnel_identifier[1:])
                                
                                # Extract values
                                output_temp = float(values[i+1])
                                external_temp = float(values[i+2])
                                internal_temp = float(values[i+3])
                                tunnel_setpoint = float(values[i+4])
                                fruit_setpoint = float(values[i+5])
                                pid_status = values[i+6].strip().lower() in ('true', '1', 't', 'y', 'yes')
                                fan_status = values[i+7].strip().lower() in ('true', '1', 't', 'y', 'yes')
                                
                                # Determine defrost status: PID off (0) and fan on (1)
                                is_defrosting = not pid_status and fan_status
                                
                                # Update UI if tunnel_id is valid
                                if 1 <= tunnel_id <= 12:
                                    # Update temperatures
                                    self.tunnel_widgets[tunnel_id-1].update_temperature(output_temp, external_temp, internal_temp)
                                    
                                    # Update setpoints
                                    self.tunnel_widgets[tunnel_id-1].update_tunnel_setpoint(tunnel_setpoint)
                                    self.tunnel_widgets[tunnel_id-1].update_fruit_setpoint(fruit_setpoint)
                                    
                                    # Update running status based on PID status
                                    self.tunnel_widgets[tunnel_id-1].update_running_status(pid_status)
                                    
                                    # Update defrost status based on our logic
                                    self.tunnel_widgets[tunnel_id-1].update_defrost_status(is_defrosting)
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing tunnel data at index {i}: {e}")
        
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def handle_setpoint_message(self, payload):
        """Handle legacy setpoint message format"""
        try:
            # Check if it's a tunnel setpoint message (format: SXX,+/-XX.XX)
            if payload.startswith("S") and len(payload) >= 9:
                tunnel_id = int(payload[1:3])
                setpoint_str = payload[4:]
                setpoint_value = float(setpoint_str)
                if 1 <= tunnel_id <= 12:
                    # Update the corresponding tunnel widget's setpoint label
                    self.tunnel_widgets[tunnel_id-1].update_tunnel_setpoint(setpoint_value)
            
            # Check if it's a fruit setpoint message (format: FXX,+/-XX.XX)
            elif payload.startswith("F") and len(payload) >= 9:
                fruit_id = int(payload[1:3])
                setpoint_str = payload[4:]
                setpoint_value = float(setpoint_str)
                if 1 <= fruit_id <= 12:
                    # Update the corresponding tunnel widget's fruit setpoint label
                    self.tunnel_widgets[fruit_id-1].update_fruit_setpoint(setpoint_value)
        except (ValueError, IndexError) as e:
            print(f"Error parsing setpoint message: {e}")


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create light palette with lime accents
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.WindowText, QColor(51, 51, 51))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(51, 51, 51))
    palette.setColor(QPalette.Text, QColor(51, 51, 51))
    palette.setColor(QPalette.Button, QColor(154, 205, 50))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(154, 205, 50))
    palette.setColor(QPalette.Highlight, QColor(154, 205, 50))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()