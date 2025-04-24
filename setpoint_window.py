from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
                             QDoubleSpinBox, QLineEdit, QMessageBox, QScrollArea,
                             QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class SetpointWindow(QWidget):
    def __init__(self, mqtt_client, parent=None):
        super().__init__(parent)
        self.mqtt_client = mqtt_client
        self.setWindowTitle("Configuración de Setpoints")
        self.is_authenticated = False
        self.access_code = mqtt_client.access_code
        self.setup_ui()
        # Use fixed size instead of fullscreen for better UI control
        self.setMinimumSize(1024, 768)
        self.resize(1200, 800)
        self.setWindowState(Qt.WindowMaximized)

    def setup_ui(self):
        # Main container
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Navigation bar
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)

        back_button = QPushButton("Volver")
        back_button.clicked.connect(self.close)
        back_button.setFixedWidth(140)
        back_button.setFixedHeight(50)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        nav_layout.addWidget(back_button)

        title = QLabel("Configuración de Setpoints")
        title.setFont(QFont('Arial', 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333333; margin: 10px 0;")
        nav_layout.addWidget(title)

        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)
        close_button.setFixedWidth(140)
        close_button.setFixedHeight(50)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #E53935;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:pressed {
                background-color: #C62828;
            }
        """)
        nav_layout.addWidget(close_button)

        main_layout.addLayout(nav_layout)

        # Authentication section
        self.auth_frame = QWidget()
        self.auth_frame.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 15px;
                padding: 30px;
                border: 2px solid #e0e0e0;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
        """)
        auth_layout = QVBoxLayout(self.auth_frame)
        auth_layout.setSpacing(15)

        auth_label = QLabel("Autenticación")
        auth_label.setFont(QFont('Arial', 18, QFont.Bold))
        auth_label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        auth_layout.addWidget(auth_label)

        self.auth_input = QLineEdit()
        self.auth_input.setEchoMode(QLineEdit.Password)
        self.auth_input.setPlaceholderText("Ingrese clave de acceso")
        self.auth_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 16px;
                margin: 10px 0;
                min-width: 250px;
            }
            QLineEdit:focus {
                border-color: #4caf50;
                box-shadow: 0 0 5px rgba(76, 175, 80, 0.3);
            }
        """)
        auth_layout.addWidget(self.auth_input)

        self.auth_button = QPushButton("Ingresar")
        self.auth_button.clicked.connect(self.authenticate)
        self.auth_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
                font-weight: bold;
                font-size: 16px;
                min-width: 120px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #43a047;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:pressed {
                background-color: #388e3c;
            }
        """)
        auth_layout.addWidget(self.auth_button)

        main_layout.addWidget(self.auth_frame)

        # Setpoints table
        self.table = QTableWidget(12, 3)
        self.table.setHorizontalHeaderLabels(["Túnel", "Setpoint (°C)", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEnabled(False)
        # Set row height for better visibility of controls
        for i in range(12):
            self.table.setRowHeight(i, 70)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 15px;
                gridline-color: #e0e0e0;
                margin: 20px;
                padding: 10px;
            }
            QTableWidget::item {
                padding: 15px;
                font-size: 16px;
            }
            QHeaderView::section {
                background-color: #4caf50;
                color: white;
                padding: 18px;
                border: none;
                font-weight: bold;
                font-size: 17px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QTableWidget::item:alternate {
                background-color: #f5f5f5;
            }
            QTableWidget::item:selected {
                background-color: #e8f5e9;
                color: #2e7d32;
            }
        """)

        for row in range(12):
            tunnel_id = row + 1
            tunnel_label = QTableWidgetItem(f"Túnel {tunnel_id}")
            tunnel_label.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, tunnel_label)

            spinbox = QDoubleSpinBox()
            spinbox.setRange(-50, 50)
            spinbox.setDecimals(1)
            spinbox.setSingleStep(0.5)
            spinbox.setValue(0.0)  # Set default value
            spinbox.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
            spinbox.setFixedHeight(70)  # Increased height for better touch interaction
            spinbox.setFixedWidth(220)  # Increased width for better visibility
            spinbox.setStyleSheet("""
                QDoubleSpinBox {
                    padding: 15px;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    font-size: 22px;  /* Increased font size */
                    font-weight: bold;
                    background-color: #f9f9f9;
                }
                QDoubleSpinBox:hover {
                    border-color: #81c784;
                    background-color: #f0f7f0;
                    transition: all 0.3s ease;
                }
                QDoubleSpinBox:focus {
                    border-color: #4caf50;
                    box-shadow: 0 0 8px rgba(76, 175, 80, 0.4);
                    background-color: white;
                }
                QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                    width: 35px;  /* Wider buttons */
                    height: 35px;  /* Taller buttons */
                    border-radius: 5px;
                    background-color: #e0e0e0;
                    margin-right: 5px;  /* Add some margin */
                }
                QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                    background-color: #c8e6c9;
                }
                QDoubleSpinBox::up-arrow {
                    image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><path fill="#4caf50" d="M7 14l5-5 5 5z"/></svg>);
                    width: 20px;  /* Larger arrows */
                    height: 20px;
                }
                QDoubleSpinBox::down-arrow {
                    image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><path fill="#4caf50" d="M7 10l5 5 5-5z"/></svg>);
                    width: 20px;  /* Larger arrows */
                    height: 20px;
                }
            """)
            spinbox.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 1, spinbox)

            save_button = QPushButton("Guardar")
            save_button.setEnabled(False)
            save_button.clicked.connect(lambda checked, r=row: self.save_setpoint(r))
            save_button.setFixedHeight(70)  # Match the height of the spinbox
            save_button.setFixedWidth(200)  # Consistent width
            save_button.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 15px 25px;
                    font-weight: bold;
                    font-size: 18px;  /* Increased font size */
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                QPushButton:hover {
                    background-color: #43a047;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                    transform: translateY(-2px);
                    transition: all 0.2s ease;
                }
                QPushButton:pressed {
                    background-color: #388e3c;
                    transform: translateY(0px);
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
                }
                QPushButton:disabled {
                    background-color: #c8e6c9;
                    color: #a5d6a7;
                    box-shadow: none;
                }
            """)
            # Add a tooltip to explain the button's function
            save_button.setToolTip("Guardar el setpoint para este túnel")
            self.table.setCellWidget(row, 2, save_button)

        main_layout.addWidget(self.table)

        # Save all button
        save_all_button = QPushButton("Guardar Todos los Setpoints")
        save_all_button.setFixedHeight(60)
        save_all_button.clicked.connect(self.save_all_setpoints)
        save_all_button.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px;
                font-weight: bold;
                font-size: 18px;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin: 20px 0;
            }
            QPushButton:hover {
                background-color: #1b5e20;
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
                transform: translateY(-3px);
                transition: all 0.3s ease;
            }
            QPushButton:pressed {
                background-color: #1b5e20;
                transform: translateY(0px);
                box-shadow: 0 3px 6px rgba(0, 0, 0, 0.2);
            }
            QPushButton:disabled {
                background-color: #a5d6a7;
                color: #e8f5e9;
                box-shadow: none;
            }
        """)
        main_layout.addWidget(save_all_button)

        # Scroll area setup
        scroll = QScrollArea()
        scroll.setWidget(main_container)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 14px;
                margin: 0px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: #4caf50;
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Main window layout
        window_layout = QVBoxLayout(self)
        window_layout.addWidget(scroll)
        window_layout.setContentsMargins(0, 0, 0, 0)

    def authenticate(self):
        input_code = self.auth_input.text()
        # Check if input matches the default access code 'migiva' or the configured access code
        if input_code == 'migiva' or (self.access_code and input_code == self.access_code):
            self.is_authenticated = True
            self.table.setEnabled(True)
            for row in range(self.table.rowCount()):
                button = self.table.cellWidget(row, 2)
                if button:
                    button.setEnabled(True)
            
            # Show success message with better styling
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Autenticación Exitosa")
            msg.setText("<h3 style='color: #2e7d32;'>Acceso Concedido</h3>")
            msg.setInformativeText("Ahora puede configurar los setpoints para todos los túneles.")
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
            
            self.auth_input.clear()
            self.auth_frame.setVisible(False)
        else:
            # Show error message with better styling
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

    def save_all_setpoints(self):
        if not self.is_authenticated:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Acceso Restringido")
            msg.setText("<h3 style='color: #f57c00;'>Autenticación Requerida</h3>")
            msg.setInformativeText("Debe autenticarse primero para guardar los setpoints.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QPushButton {
                    background-color: #ff9800;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #f57c00;
                }
            """)
            msg.exec_()
            return

        setpoints = {}
        for row in range(self.table.rowCount()):
            tunnel_id = row + 1
            spinbox = self.table.cellWidget(row, 1)
            setpoint = spinbox.value()
            setpoints[f"tunnel_{tunnel_id}_setpoint"] = setpoint

        try:
            self.mqtt_client.publish("setpoints", setpoints)
            
            # Show success message with better styling
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Operación Exitosa")
            msg.setText("<h3 style='color: #2e7d32;'>Setpoints Guardados</h3>")
            msg.setInformativeText("Todos los setpoints han sido guardados correctamente.")
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
        except Exception as e:
            # Show error message with better styling
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error de Comunicación")
            msg.setText("<h3 style='color: #c62828;'>Error al Guardar Setpoints</h3>")
            msg.setInformativeText(f"Ocurrió un error durante la comunicación: {str(e)}")
            msg.setDetailedText(f"Detalles técnicos del error:\n{str(e)}")
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

    def save_setpoint(self, row):
        if not self.is_authenticated:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Acceso Restringido")
            msg.setText("<h3 style='color: #f57c00;'>Autenticación Requerida</h3>")
            msg.setInformativeText("Debe autenticarse primero para guardar el setpoint.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QPushButton {
                    background-color: #ff9800;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #f57c00;
                }
            """)
            msg.exec_()
            return

        tunnel_id = row + 1
        spinbox = self.table.cellWidget(row, 1)
        setpoint = spinbox.value()

        try:
            # Use the set_temperature method from mqtt_client to ensure correct format (S01,+/-0000)
            success = self.mqtt_client.set_temperature(tunnel_id, setpoint)
            
            if success:
                # Show success message with better styling
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Operación Exitosa")
                msg.setText(f"<h3 style='color: #2e7d32;'>Setpoint Guardado</h3>")
                msg.setInformativeText(f"El setpoint del Túnel {tunnel_id} ha sido configurado a {setpoint}°C correctamente.\nFormato enviado: S{tunnel_id:02d},{'+' if setpoint >= 0 else '-'}{abs(setpoint):.1f}")
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
                
                # Update the spinbox styling to indicate success
                spinbox.setStyleSheet("""
                    QDoubleSpinBox {
                        padding: 15px;
                        border: 2px solid #4caf50;
                        border-radius: 10px;
                        font-size: 18px;
                        font-weight: bold;
                        min-width: 200px;
                        min-height: 50px;
                        background-color: #e8f5e9;
                    }
                    QDoubleSpinBox:hover {
                        border-color: #81c784;
                        background-color: #f0f7f0;
                    }
                    QDoubleSpinBox:focus {
                        border-color: #4caf50;
                        box-shadow: 0 0 8px rgba(76, 175, 80, 0.4);
                        background-color: white;
                    }
                    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                        width: 30px;
                        height: 25px;
                        border-radius: 5px;
                        background-color: #e0e0e0;
                    }
                    QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                        background-color: #c8e6c9;
                    }
                    QDoubleSpinBox::up-arrow {
                        image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><path fill="#4caf50" d="M7 14l5-5 5 5z"/></svg>);
                        width: 16px;
                        height: 16px;
                    }
                    QDoubleSpinBox::down-arrow {
                        image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><path fill="#4caf50" d="M7 10l5 5 5-5z"/></svg>);
                        width: 16px;
                        height: 16px;
                    }
                """)
            else:
                raise Exception("No se pudo publicar el mensaje MQTT")
        except Exception as e:
            # Show error message with better styling
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)  # Changed from Critical to Warning
            msg.setWindowTitle("Advertencia")
            msg.setText(f"<h3 style='color: #f57c00;'>Advertencia al Guardar Setpoint</h3>")
            msg.setInformativeText(f"El setpoint del Túnel {tunnel_id} ha sido enviado, pero no se ha podido confirmar la recepción.\nEl sistema intentará reenviar el mensaje automáticamente.")
            msg.setDetailedText(f"Detalles técnicos:\n{str(e)}\n\nEsto no significa necesariamente que el setpoint no haya sido configurado. El mensaje puede haber sido enviado correctamente pero la confirmación no fue recibida.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QPushButton {
                    background-color: #ff9800;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #f57c00;
                }
            """)
            msg.exec_()