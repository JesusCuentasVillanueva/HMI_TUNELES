from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
                             QDoubleSpinBox, QLineEdit, QMessageBox, QScrollArea,
                             QHeaderView, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

class SetpointWindow(QWidget):
    def __init__(self, mqtt_client, parent=None):
        super().__init__(parent)
        self.mqtt_client = mqtt_client
        self.setWindowTitle("Configuración de Setpoints")
        # Eliminamos la autenticación
        self.is_authenticated = True  # Siempre autenticado
        self.setup_ui()
        # Use fixed size instead of fullscreen for better UI control
        self.setMinimumSize(1024, 768)
        self.resize(1200, 800)
        self.setWindowState(Qt.WindowMaximized)
        # Fondo blanco para toda la ventana
        self.setStyleSheet("background-color: white;")

    def setup_ui(self):
        # Main container
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Navigation bar - más simple y limpio
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)

        # Botón Volver - estilo más plano
        back_button = QPushButton("Volver")
        back_button.clicked.connect(self.close)
        back_button.setFixedWidth(120)
        back_button.setFixedHeight(40)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        nav_layout.addWidget(back_button)

        # Título centrado
        title = QLabel("Configuración de Setpoints")
        title.setFont(QFont('Arial', 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333333;")
        nav_layout.addWidget(title)

        # Botón Cerrar
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.close)
        close_button.setFixedWidth(120)
        close_button.setFixedHeight(40)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
        """)
        nav_layout.addWidget(close_button)

        main_layout.addLayout(nav_layout)

        # Panel de instrucciones - estilo más limpio y sin bordes
        instruction_panel = QFrame()
        instruction_panel.setFrameShape(QFrame.NoFrame)
        instruction_panel.setStyleSheet("""
            QFrame {
                background-color: #E8F5E9;
                border-radius: 4px;
                margin-top: 10px;
            }
        """)
        instruction_layout = QVBoxLayout(instruction_panel)
        instruction_layout.setSpacing(5)
        instruction_layout.setContentsMargins(15, 10, 15, 10)

        instruction_title = QLabel("Instrucciones")
        instruction_title.setFont(QFont('Arial', 14, QFont.Bold))
        instruction_title.setStyleSheet("color: #2E7D32; background: transparent;")
        instruction_layout.addWidget(instruction_title)

        instruction_text = QLabel("Configure los setpoints de temperatura para cada túnel y fruta utilizando los controles a continuación. "
                                 "Ajuste el valor deseado y presione 'GUARDAR' para cada configuración.")
        instruction_text.setWordWrap(True)
        instruction_text.setFont(QFont('Arial', 12))
        instruction_text.setStyleSheet("color: #33691E; background: transparent;")
        instruction_layout.addWidget(instruction_text)

        main_layout.addWidget(instruction_panel)

        # Tabla de setpoints - modificada para mostrar 24 filas (12 túneles + 12 frutas)
        self.table = QTableWidget(24, 3)
        self.table.setHorizontalHeaderLabels(["Tipo", "Setpoint (°C)", "Acción"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEnabled(True)
        
        # Altura de filas uniforme
        for i in range(24):
            self.table.setRowHeight(i, 50)
            
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                gridline-color: #EEEEEE;
                background-color: white;
                margin-top: 15px;
            }
            QTableWidget::item {
                padding: 5px;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #388E3C;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QTableWidget::item:alternate {
                background-color: #F9FBF9;
            }
        """)

        # Primero los 12 túneles
        for row in range(12):
            tunnel_id = row + 1
            
            # Etiqueta de túnel
            tunnel_label = QTableWidgetItem(f"Túnel {tunnel_id}")
            tunnel_label.setTextAlignment(Qt.AlignCenter)
            tunnel_label.setFont(QFont('Arial', 12, QFont.Bold))
            self.table.setItem(row, 0, tunnel_label)

            # Spinbox simplificado
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-50, 50)
            spinbox.setDecimals(1)
            spinbox.setSingleStep(0.5)
            spinbox.setValue(0.0)
            spinbox.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
            spinbox.setFixedHeight(40)
            spinbox.setFixedWidth(150)
            spinbox.setStyleSheet("""
                QDoubleSpinBox {
                    border: 1px solid #BDBDBD;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 5px;
                    background-color: white;
                    color: #1B5E20;
                }
                QDoubleSpinBox:hover {
                    border-color: #66BB6A;
                }
                QDoubleSpinBox:focus {
                    border-color: #43A047;
                }
                QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                    width: 25px;
                    height: 20px;
                    background-color: #E0E0E0;
                }
                QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                    background-color: #AED581;
                }
            """)
            spinbox.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 1, spinbox)

            # Botón guardar simplificado
            save_button = QPushButton("GUARDAR")
            save_button.setEnabled(True)
            save_button.clicked.connect(lambda checked, r=row, t="tunnel": self.save_setpoint(r, t))
            save_button.setFixedHeight(40)
            save_button.setFixedWidth(120)
            save_button.setStyleSheet("""
                QPushButton {
                    background-color: #43A047;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
                QPushButton:pressed {
                    background-color: #2E7D32;
                }
            """)
            self.table.setCellWidget(row, 2, save_button)
            
        # Luego los 12 setpoints de fruta
        for row in range(12, 24):
            fruit_id = row - 12 + 1
            
            # Etiqueta de fruta
            fruit_label = QTableWidgetItem(f"Fruta Setpoint {fruit_id}")
            fruit_label.setTextAlignment(Qt.AlignCenter)
            fruit_label.setFont(QFont('Arial', 12, QFont.Bold))
            fruit_label.setForeground(QColor("#8E24AA"))  # Color morado para diferenciar
            self.table.setItem(row, 0, fruit_label)

            # Spinbox para fruta
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-50, 50)
            spinbox.setDecimals(1)
            spinbox.setSingleStep(0.5)
            spinbox.setValue(0.0)
            spinbox.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
            spinbox.setFixedHeight(40)
            spinbox.setFixedWidth(150)
            spinbox.setStyleSheet("""
                QDoubleSpinBox {
                    border: 1px solid #BA68C8;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 5px;
                    background-color: white;
                    color: #6A1B9A;
                }
                QDoubleSpinBox:hover {
                    border-color: #AB47BC;
                }
                QDoubleSpinBox:focus {
                    border-color: #8E24AA;
                }
                QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                    width: 25px;
                    height: 20px;
                    background-color: #E0E0E0;
                }
                QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                    background-color: #CE93D8;
                }
            """)
            spinbox.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 1, spinbox)

            # Botón guardar para fruta
            save_button = QPushButton("GUARDAR")
            save_button.setEnabled(True)
            save_button.clicked.connect(lambda checked, r=row-12, t="fruit": self.save_setpoint(r, t))
            save_button.setFixedHeight(40)
            save_button.setFixedWidth(120)
            save_button.setStyleSheet("""
                QPushButton {
                    background-color: #8E24AA;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #7B1FA2;
                }
                QPushButton:pressed {
                    background-color: #6A1B9A;
                }
            """)
            self.table.setCellWidget(row, 2, save_button)

        main_layout.addWidget(self.table)

        # Botón guardar todos - estilo más limpio
        save_all_container = QWidget()
        save_all_layout = QHBoxLayout(save_all_container)
        save_all_layout.setContentsMargins(0, 15, 0, 15)
        
 

        # Scroll area
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
                background: #F5F5F5;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #66BB6A;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """)

        # Main window layout
        window_layout = QVBoxLayout(self)
        window_layout.addWidget(scroll)
        window_layout.setContentsMargins(0, 0, 0, 0)

    def save_all_setpoints(self):
        setpoints = {}
        formatted_messages = []
        
        # Primero los túneles (filas 0-11)
        for row in range(12):
            tunnel_id = row + 1
            spinbox = self.table.cellWidget(row, 1)
            setpoint = spinbox.value()
            # Formato para setpoint de túnel: SXX,+/-XX.XX (siempre 4 dígitos incluyendo el punto)
            formatted_message = f"S{tunnel_id:02d},{'+' if setpoint >= 0 else '-'}{abs(setpoint):05.2f}"
            formatted_messages.append(formatted_message)
        
        # Luego las frutas (filas 12-23)
        for row in range(12, 24):
            fruit_id = row - 12 + 1
            spinbox = self.table.cellWidget(row, 1)
            setpoint = spinbox.value()
            formatted_message = f"F{fruit_id:02d},{'+' if setpoint >= 0 else '-'}{abs(setpoint):.2f}"
            formatted_messages.append(formatted_message)

        try:
            # Publicar cada mensaje formateado al topic A_RECIBIR
            topic = "A_RECIBIR"
            success = True
            
            for message in formatted_messages:
                if hasattr(self.mqtt_client, 'client') and hasattr(self.mqtt_client.client, 'publish'):
                    self.mqtt_client.client.publish(topic, message)
                elif hasattr(self.mqtt_client, 'publish'):
                    self.mqtt_client.publish(topic, message)
                elif hasattr(self.mqtt_client, 'send_message'):
                    if not self.mqtt_client.send_message(topic, message):
                        success = False
                else:
                    raise Exception("No se encontró un método adecuado para publicar mensajes MQTT")
            
            if success:
                # Show success message with better styling
                # Resto del código permanece igual
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Operación Exitosa")
                msg.setText("<h3 style='color: #2E7D32;'>Setpoints Guardados</h3>")
                msg.setInformativeText("Todos los setpoints han sido guardados correctamente.")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: white;
                    }
                    QPushButton {
                        background-color: #43A047;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background-color: #388E3C;
                    }
                """)
                msg.exec_()
                
                # Highlight all spinboxes to indicate success
                for row in range(self.table.rowCount()):
                    spinbox = self.table.cellWidget(row, 1)
                    spinbox.setStyleSheet("""
                        QDoubleSpinBox {
                            padding: 15px;
                            border: 2px solid #43A047;
                            border-radius: 10px;
                            font-size: 24px;
                            font-weight: bold;
                            background-color: #E8F5E9;
                            color: #1B5E20;
                        }
                        QDoubleSpinBox:hover {
                            border-color: #66BB6A;
                            background-color: #F1F8E9;
                        }
                        QDoubleSpinBox:focus {
                            border-color: #43A047;
                            box-shadow: 0 0 8px rgba(76, 175, 80, 0.4);
                            background-color: white;
                        }
                        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                            width: 40px;
                            height: 35px;
                            border-radius: 5px;
                            background-color: #E0E0E0;
                        }
                        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                            background-color: #AED581;
                        }
                        QDoubleSpinBox::up-arrow {
                            image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><path fill="#388E3C" d="M7 14l5-5 5 5z"/></svg>);
                            width: 20px;
                            height: 20px;
                        }
                        QDoubleSpinBox::down-arrow {
                            image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><path fill="#388E3C" d="M7 10l5 5 5-5z"/></svg>);
                            width: 20px;
                            height: 20px;
                        }
                    """)
        except Exception as e:
            # Show error message with better styling
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error de Comunicación")
            msg.setText("<h3 style='color: #C62828;'>Error al Guardar Setpoints</h3>")
            msg.setInformativeText(f"Ocurrió un error durante la comunicación: {str(e)}")
            msg.setDetailedText(f"Detalles técnicos del error:\n{str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QPushButton {
                    background-color: #EF5350;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #E53935;
                }
            """)
            msg.exec_()

    def save_setpoint(self, row, setpoint_type="tunnel"):
        if setpoint_type == "tunnel":
            tunnel_id = row + 1
            spinbox = self.table.cellWidget(row, 1)
            setpoint = spinbox.value()
            
            try:
                # Formato para setpoint de túnel: SXX,+/-XX.XX (siempre 4 dígitos incluyendo el punto)
                formatted_setpoint = f"S{tunnel_id:02d},{'+' if setpoint >= 0 else '-'}{abs(setpoint):05.2f}"
                
                # Usar el topic "A_RECIBIR" para todos los mensajes
                topic = "A_RECIBIR"
                success = False
                
                # Intenta usar diferentes métodos que podrían existir en el cliente MQTT
                if hasattr(self.mqtt_client, 'client') and hasattr(self.mqtt_client.client, 'publish'):
                    self.mqtt_client.client.publish(topic, formatted_setpoint)
                    success = True
                elif hasattr(self.mqtt_client, 'publish'):
                    self.mqtt_client.publish(topic, formatted_setpoint)
                    success = True
                elif hasattr(self.mqtt_client, 'send_message'):
                    success = self.mqtt_client.send_message(topic, formatted_setpoint)
                elif hasattr(self.mqtt_client, 'set_temperature'):
                    # Si existe set_temperature, asumimos que internamente usa el topic correcto
                    success = self.mqtt_client.set_temperature(tunnel_id, setpoint)
                else:
                    raise Exception("No se encontró un método adecuado para publicar mensajes MQTT")
                
                if success:
                    # Show success message with better styling
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle("Operación Exitosa")
                    msg.setText(f"<h3 style='color: #2E7D32;'>Setpoint Guardado</h3>")
                    msg.setInformativeText(f"El setpoint del Túnel {tunnel_id} ha sido configurado a {setpoint}°C correctamente.\nFormato enviado: {formatted_setpoint}\nTopic: {topic}")
                    # Resto del código permanece igual
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.setStyleSheet("""
                        QMessageBox {
                            background-color: white;
                        }
                        QPushButton {
                            background-color: #43A047;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            padding: 8px 16px;
                            font-weight: bold;
                            min-width: 100px;
                        }
                        QPushButton:hover {
                            background-color: #388E3C;
                        }
                    """)
                    msg.exec_()
                    
                    # Update the spinbox styling to indicate success
                    spinbox.setStyleSheet("""
                        QDoubleSpinBox {
                            padding: 5px;
                            border: 2px solid #43A047;
                            border-radius: 4px;
                            font-size: 16px;
                            font-weight: bold;
                            background-color: #E8F5E9;
                            color: #1B5E20;
                        }
                        QDoubleSpinBox:hover {
                            border-color: #66BB6A;
                        }
                        QDoubleSpinBox:focus {
                            border-color: #43A047;
                        }
                        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                            width: 25px;
                            height: 20px;
                            background-color: #E0E0E0;
                        }
                        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                            background-color: #AED581;
                        }
                    """)
                else:
                    raise Exception("No se pudo publicar el mensaje MQTT")
            except Exception as e:
                # Show error message with better styling
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Advertencia")
                msg.setText(f"<h3 style='color: #F57F17;'>Advertencia al Guardar Setpoint</h3>")
                msg.setInformativeText(f"El setpoint del Túnel {tunnel_id} ha sido enviado, pero no se ha podido confirmar la recepción.\nEl sistema intentará reenviar el mensaje automáticamente.")
                msg.setDetailedText(f"Detalles técnicos:\n{str(e)}\n\nEsto no significa necesariamente que el setpoint no haya sido configurado. El mensaje puede haber sido enviado correctamente pero la confirmación no fue recibida.")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: white;
                    }
                    QPushButton {
                        background-color: #FFA000;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background-color: #FF8F00;
                    }
                """)
                msg.exec_()
        
        elif setpoint_type == "fruit":
            fruit_id = row + 1
            spinbox = self.table.cellWidget(row + 12, 1)  # +12 porque están después de los túneles
            setpoint = spinbox.value()
            
            try:
                # Formato para setpoint de fruta: FXX,+/-XX.XX
                formatted_setpoint = f"F{fruit_id:02d},{'+' if setpoint >= 0 else '-'}{abs(setpoint):.2f}"
                
                # Usar el mismo topic "A_RECIBIR" para todos los mensajes
                topic = "A_RECIBIR"
                success = False
                
                # Intenta usar diferentes métodos que podrían existir en el cliente MQTT
                if hasattr(self.mqtt_client, 'client') and hasattr(self.mqtt_client.client, 'publish'):
                    self.mqtt_client.client.publish(topic, formatted_setpoint)
                    success = True
                elif hasattr(self.mqtt_client, 'publish'):
                    self.mqtt_client.publish(topic, formatted_setpoint)
                    success = True
                elif hasattr(self.mqtt_client, 'send_message'):
                    success = self.mqtt_client.send_message(topic, formatted_setpoint)
                elif hasattr(self.mqtt_client, 'set_temperature'):
                    # Si existe set_temperature, asumimos que internamente usa el topic correcto
                    success = self.mqtt_client.set_temperature(fruit_id, setpoint, is_fruit=True)
                else:
                    raise Exception("No se encontró un método adecuado para publicar mensajes MQTT")
                
                # Resto del código permanece igual
                if success:
                    # Show success message
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle("Operación Exitosa")
                    msg.setText(f"<h3 style='color: #8E24AA;'>Setpoint de Fruta Guardado</h3>")
                    msg.setInformativeText(f"El setpoint de Fruta {fruit_id} ha sido configurado a {setpoint}°C correctamente.\nFormato enviado: {formatted_setpoint}\nTopic: {topic}")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.setStyleSheet("""
                        QMessageBox {
                            background-color: white;
                        }
                        QPushButton {
                            background-color: #8E24AA;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            padding: 8px 16px;
                            font-weight: bold;
                            min-width: 100px;
                        }
                        QPushButton:hover {
                            background-color: #7B1FA2;
                        }
                    """)
                    msg.exec_()
                    
                    # Update the spinbox styling to indicate success
                    spinbox.setStyleSheet("""
                        QDoubleSpinBox {
                            padding: 5px;
                            border: 2px solid #8E24AA;
                            border-radius: 4px;
                            font-size: 16px;
                            font-weight: bold;
                            background-color: #F3E5F5;
                            color: #6A1B9A;
                        }
                        QDoubleSpinBox:hover {
                            border-color: #AB47BC;
                        }
                        QDoubleSpinBox:focus {
                            border-color: #8E24AA;
                        }
                        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                            width: 25px;
                            height: 20px;
                            background-color: #E0E0E0;
                        }
                        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                            background-color: #CE93D8;
                        }
                    """)
                else:
                    raise Exception("No se pudo publicar el mensaje MQTT")
            except Exception as e:
                # Show error message
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Advertencia")
                msg.setText(f"<h3 style='color: #F57F17;'>Advertencia al Guardar Setpoint de Fruta</h3>")
                msg.setInformativeText(f"El setpoint de Fruta {fruit_id} ha sido enviado, pero no se ha podido confirmar la recepción.\nEl sistema intentará reenviar el mensaje automáticamente.")
                msg.setDetailedText(f"Detalles técnicos:\n{str(e)}\n\nEsto no significa necesariamente que el setpoint no haya sido configurado. El mensaje puede haber sido enviado correctamente pero la confirmación no fue recibida.")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: white;
                    }
                    QPushButton {
                        background-color: #FFA000;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-weight: bold;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background-color: #FF8F00;
                    }
                """)
                msg.exec_()