from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from PyQt5 import QtCore, uic
from PyQt5.QtGui import QPixmap
import pyqtgraph as pg
import serial
import random

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("gy521_user_interface_artificial_horizon.ui", self)

        self.gyroPlotWidget = self.findChild(pg.PlotWidget, "gyroscrope_graph")
        self.accelerometerPlotWidget = self.findChild(pg.PlotWidget, "accelerometer_graph")
        self.horizonGraphicsView = self.findChild(QGraphicsView, "graphicsView")

        self.gyroPlotWidget.setTitle("Gyroscope Input")
        self.accelerometerPlotWidget.setTitle("Accelerometer Input")

        self.gyroPlotWidget.showGrid(x=True, y=True)
        self.accelerometerPlotWidget.showGrid(x=True, y=True)

        self.gyroPlotWidget.addLegend()
        self.accelerometerPlotWidget.addLegend()

        # self.gyroPlotWidget.setXRange(0, 95, padding=0)
        # self.accelerometerPlotWidget.setXRange(0, 95, padding=0)

        # Gyroscope Data 
        self.gyro_x = [0]
        self.gyro_y = [0]
        self.gyro_z = [0]
        self.gyro_t = [0]

        # Accelerometer Data
        self.accl_x = [0]
        self.accl_y = [0]
        self.accl_z = [0]
        self.accl_t = [0]

        # Styles for both x, y, and z lines. Using same styling for both graphs
        x_pen = pg.mkPen(color=(255, 0, 0), width=2, style=QtCore.Qt.SolidLine)
        y_pen = pg.mkPen(color=(0, 255, 0), width=2, style=QtCore.Qt.SolidLine)
        z_pen = pg.mkPen(color=(0, 0, 255), width=2, style=QtCore.Qt.SolidLine)

        self.gyro_x_line = self.gyroPlotWidget.plot(self.gyro_t, self.gyro_x, pen=x_pen, name="x")
        self.gyro_y_line = self.gyroPlotWidget.plot(self.gyro_t, self.gyro_y, pen=y_pen, name="y")
        self.gyro_z_line = self.gyroPlotWidget.plot(self.gyro_t, self.gyro_z, pen=z_pen, name="z")

        self.accl_x_line = self.accelerometerPlotWidget.plot(self.accl_t, self.accl_x, pen=x_pen, name="x")
        self.accl_y_line = self.accelerometerPlotWidget.plot(self.accl_t, self.accl_y, pen=y_pen, name="y")
        self.accl_z_line = self.accelerometerPlotWidget.plot(self.accl_t, self.accl_z, pen=z_pen, name="z")

        # Setting up the artificial horizon
        self.graphicsScene = QGraphicsScene()
        self.upDown = 0
        self.rotate = 0

        self.horizonGraphicsView.setScene(self.graphicsScene)
        self.horizonGraphicsView.setSceneRect(0, 0, 370, 555)

        horizonPixmap = QPixmap("horizon2_2.png")
        self.horizonPixmapItem = self.graphicsScene.addPixmap(horizonPixmap)
        self.horizonPixmapItem.setTransformOriginPoint(196, 280)
        self.horizonPixmapItem.setScale(1.8)
        
        # Setting up timer for updating graph data
        self.timer = QtCore.QTimer()
        self.timer.setInterval(5)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

        self.update_plot_data()

    def update_plot_data(self):
        if arduinoSerial.in_waiting:
            arduinoData = arduinoSerial.readline()
            line = arduinoData.decode(encoding="utf-8", errors="ignore").rstrip('\n')

            sensorDataArray = line.split()

            if len(sensorDataArray) == 4:
                if sensorDataArray[0] == 'G':
                    if len(self.gyro_t) > 95 :
                        self.gyro_t = self.gyro_t[1:]
                        self.gyro_x = self.gyro_x[1:]
                        self.gyro_y = self.gyro_y[1:]
                        self.gyro_z = self.gyro_z[1:]

                    self.gyro_t.append(self.gyro_t[-1] + 1)
                    gyro_x_data = float(sensorDataArray[1]) + gyro_x_calibratoin
                    # Ignoring very minor changes that were causing noise in the graph
                    if abs(gyro_x_data) < 0.02:
                        gyro_x_data = 0
                        self.rotate_left = 0

                    gyro_y_data = float(sensorDataArray[2])
                    if abs(gyro_y_data) < 0.02:
                        gyro_y_data = 0

                    gyro_z_data = float(sensorDataArray[3]) + gyro_z_calibration
                    if abs(gyro_z_data) < 0.02:
                        gyro_z_data = 0

                    self.gyro_x.append(gyro_x_data)
                    self.gyro_y.append(gyro_y_data)
                    self.gyro_z.append(gyro_z_data)

                    self.gyro_x_line.setData(self.gyro_t, self.gyro_x)
                    self.gyro_y_line.setData(self.gyro_t, self.gyro_y)
                    self.gyro_z_line.setData(self.gyro_t, self.gyro_z)

                elif sensorDataArray[0] == 'A':
                    if len(self.accl_t) > 95 :
                        self.accl_t = self.accl_t[1:]
                        self.accl_x = self.accl_x[1:]
                        self.accl_y = self.accl_y[1:]
                        self.accl_z = self.accl_z[1:]

                    self.accl_t.append(self.accl_t[-1] + 1)
                    self.accl_x.append(float(sensorDataArray[1]) + accl_x_calibration)
                    self.accl_y.append(float(sensorDataArray[2]))
                    self.accl_z.append(float(sensorDataArray[3]))

                    # Updating artificial horizon
                    self.rotate = round(float(sensorDataArray[2])) * 10
                    self.upDown = round(float(sensorDataArray[1]) + accl_x_calibration) * 10

                    # Updating accelerometer line graph
                    self.accl_x_line.setData(self.accl_t, self.accl_x)
                    self.accl_y_line.setData(self.accl_t, self.accl_y)
                    self.accl_z_line.setData(self.accl_t, self.accl_z)

        # Moving the artificial horizon
        self.horizonPixmapItem.setRotation(self.rotate)
        self.horizonPixmapItem.setY(self.upDown)


arduinoPort = "/dev/ttyUSB0"

gyro_x_calibratoin = 0.05
gyro_z_calibration = 0.02
accl_x_calibration = 0.5

arduinoSerial = serial.Serial()
arduinoSerial.baudrate = 9600
arduinoSerial.port = arduinoPort
arduinoSerial.open()

app = QApplication([])
window = MainWindow()
window.show()
app.exec_()