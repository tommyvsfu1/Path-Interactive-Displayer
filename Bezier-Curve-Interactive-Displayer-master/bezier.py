# !/usr/bin/env python3 
# -*- coding: utf-8 -*- 
# @Author: dong 
# @Date: 2018-05-19 16:24:33 
# @Env: python 3.6 
# @Github: https://github.com/PerpetualSmile 

import numpy as np
import sys
from PyQt5 import Qt
from PyQt5 import QtCore,QtWidgets,QtGui
import PyQt5
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QDialog, QMessageBox, QTableWidgetItem, QTextBrowser
import matplotlib
from matplotlib import pyplot as plt
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D
from matplotlib.artist import Artist
from matplotlib.mlab import dist_point_to_segment
from matplotlib.ticker import MultipleLocator

import ui
import table_ui
import about_ui


B = np.array([[-1, 3, -3, 1],
              [3, -6,  3, 0],
              [-3, 3,  0, 0],
              [1,  0,  0, 0]], dtype=float)

Bspline = 1/6 * np.array([[-1, 3, -3, 1],
                    [3, -6,  3, 0],
                    [-3, 0,  3, 0],
                    [1,  4,  1, 0]],dtype=float)


P = np.array([[1, 4], [2, 9], [5, 9], [6, 4]], dtype=float)
TList = [np.array([t**3, t**2, t, 1], dtype=float) for t in np.arange(0.0, 1.01, 0.01)] # sampling


class MainWindow(ui.Ui_MainWindow):
    showverts = True
    epsilon = 10  # max pixel distance to count as a vertex hit
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)
        MainWindow = QtWidgets.QMainWindow()
        super().setupUi(MainWindow)
        self.flag = False
        self.figure_list = []
        self.initial_button()
        self.action_connect()
        self.initial_figure()
        self.Dialog = QtWidgets.QDialog()
        self.ui_2 = table_ui.Ui_Form()
        self.ui_2.setupUi(self.Dialog)
        self.Dialog2 = QtWidgets.QDialog()
        self.ui_3 = about_ui.Ui_Dialog()
        self.ui_3.setupUi(self.Dialog2)
        MainWindow.show()
        sys.exit(app.exec_())

    def initial_button(self):
        '初始化按钮的值'
        # blue point & red point(x,y)
        self.doubleSpinBox_1.setValue(P[0,0])
        self.doubleSpinBox_2.setValue(P[0,1])
        self.doubleSpinBox_3.setValue(P[1,0])
        self.doubleSpinBox_4.setValue(P[1,1])
        
        
        self.doubleSpinBox_5.setValue(P[2,0])
        self.doubleSpinBox_6.setValue(P[2,1])
        self.doubleSpinBox_7.setValue(P[3,0])
        self.doubleSpinBox_8.setValue(P[3,1])

    def reset(self):
        '重置事件'
        self.figure_list = []
        self.doubleSpinBox_1.setValue(1)
        self.doubleSpinBox_2.setValue(4)
        self.doubleSpinBox_3.setValue(2)
        self.doubleSpinBox_4.setValue(9)
        self.doubleSpinBox_5.setValue(5)
        self.doubleSpinBox_6.setValue(9)
        self.doubleSpinBox_7.setValue(6)
        self.doubleSpinBox_8.setValue(4)
        self.draw_curves()
        self.ui_2.tableWidget.setRowCount(len(self.figure_list))



    def action_connect(self):
        '按钮绑定到对应函数'
        self.doubleSpinBox_1.valueChanged.connect(self.draw_curves)
        self.doubleSpinBox_2.valueChanged.connect(self.draw_curves)
        self.doubleSpinBox_3.valueChanged.connect(self.draw_curves)
        self.doubleSpinBox_4.valueChanged.connect(self.draw_curves)
        self.doubleSpinBox_5.valueChanged.connect(self.draw_curves)
        self.doubleSpinBox_6.valueChanged.connect(self.draw_curves)
        self.doubleSpinBox_7.valueChanged.connect(self.draw_curves)
        self.doubleSpinBox_8.valueChanged.connect(self.draw_curves)
        self.radioButton.clicked.connect(self.draw_curves)
        self.radioButton_2.clicked.connect(self.draw_curves)
        self.radioButton_linear.clicked.connect(self.draw_curves)
        self.checkBox.clicked.connect(self.draw_curves)
        self.checkBox_2.clicked.connect(self.draw_curves)
        self.checkBox_3.clicked.connect(self.draw_curves)
        self.horizontalSlider.valueChanged.connect(self.draw_curves)
        self.lineEdit.textChanged.connect(self.draw_curves)
        self.pushButton.clicked.connect(self.reset)
        self.action.triggered.connect(self.show_information)
        self.pushButton_2.clicked.connect(self.fix)


    def initial_figure(self):
        '初始化图形'
        self.figure = plt.figure(frameon=False)
        self.canvas = FigureCanvas(self.figure)
        self.ntb =NavigationToolbar(self.canvas, None)

        # verticalLayout_13 就是顯示畫面的widget
        self.verticalLayout_13.addWidget(self.ntb)
        self.verticalLayout_13.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(2,1,1, facecolor='#FFFFFF', )
        self.ax_curvature = self.figure.add_subplot(2,1,2, facecolor='#FFFFFF', )
        self.ax_curvature.get_shared_x_axes().join(self.ax, self.ax_curvature)

        poly = Polygon(P, animated=True, closed=False)
        self.poly = poly
        self.ax.add_patch(poly)
        canvas = poly.figure.canvas
        self._ind = None  # the active vert
        canvas.mpl_connect('button_press_event', self.button_press_callback)
        canvas.mpl_connect('button_release_event', self.button_release_callback)
        canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)

        self.draw_curves()
        self.figure.tight_layout()


    def fix(self):
        '固定当前图形，并生成新的图形'
        global P
        lw = self.horizontalSlider.value()
        ms = self.horizontalSlider.value()
        mark = self.lineEdit.text()
        curves = self.radioButton.isChecked()
        self.figure_list.append((P.copy(), lw, ms, mark, curves))
        S = P.copy()

        # 曲线光滑拼接
        if self.radioButton.isChecked(): # Bezier button 
            self.doubleSpinBox_1.setValue(S[3, 0])
            self.doubleSpinBox_2.setValue(S[3, 1])
            self.doubleSpinBox_3.setValue(S[3, 0]*2 - S[2, 0])
            self.doubleSpinBox_4.setValue(S[3, 1]*2 - S[2, 1])
            self.doubleSpinBox_5.setValue(S[3, 0]*2 - S[1, 0])
            self.doubleSpinBox_6.setValue(S[3, 1]*2 - S[1, 1])
            self.doubleSpinBox_7.setValue(S[3, 0]*2 - S[0, 0])
            self.doubleSpinBox_8.setValue(S[3, 1]*2 - S[0, 1])
        elif self.radioButton_2.isChecked(): # B-spline button
            self.doubleSpinBox_1.setValue(S[1, 0])
            self.doubleSpinBox_2.setValue(S[1, 1])
            self.doubleSpinBox_3.setValue(S[2, 0])
            self.doubleSpinBox_4.setValue(S[2, 1])
            self.doubleSpinBox_5.setValue(S[3, 0])
            self.doubleSpinBox_6.setValue(S[3, 1])
            self.doubleSpinBox_7.setValue(S[0, 0])
            self.doubleSpinBox_8.setValue(S[0, 1])
        elif self.radioButton_linear.isChecked(): # Linear
            self.doubleSpinBox_1.setValue(S[0, 0])
            self.doubleSpinBox_2.setValue(S[0, 1])
            self.doubleSpinBox_3.setValue(S[1, 0])
            self.doubleSpinBox_4.setValue(S[1, 1])
            self.doubleSpinBox_5.setValue(S[2, 0])
            self.doubleSpinBox_6.setValue(S[2, 1])
            self.doubleSpinBox_7.setValue(S[3, 0])
            self.doubleSpinBox_8.setValue(S[3, 1])        

        self.initial_button()
        self.draw_curves()
        self.show_table()


    def show_table(self):
        '显示之前的图形的信息'
        self.Dialog.show()
        i = 0
        self.ui_2.tableWidget.setRowCount(len(self.figure_list))
        for s in self.figure_list:
            s = s[0]
            temp1 = QTableWidgetItem(str('({:.2f}, {:.2f})'.format(s[0, 0], s[0, 1])))
            temp2 = QTableWidgetItem(str('({:.2f}, {:.2f})'.format(s[1, 0], s[1, 1])))
            temp3 = QTableWidgetItem(str('({:.2f}, {:.2f})'.format(s[2, 0], s[2, 1])))
            temp4 = QTableWidgetItem(str('({:.2f}, {:.2f})'.format(s[3, 0], s[3, 1])))
            self.ui_2.tableWidget.setItem(i, 0, temp1)
            self.ui_2.tableWidget.setItem(i, 1, temp2)
            self.ui_2.tableWidget.setItem(i, 2, temp3)
            self.ui_2.tableWidget.setItem(i, 3, temp4)
            i += 1
        self.Dialog.exec_()


    def update_points(self):
        '更新保存当前可交互坐标点的全局变量'
        P[0, 0] = self.doubleSpinBox_1.value()
        P[0, 1] = self.doubleSpinBox_2.value()
        P[1, 0] = self.doubleSpinBox_3.value()
        P[1, 1] = self.doubleSpinBox_4.value()
        P[2, 0] = self.doubleSpinBox_5.value()
        P[2, 1] = self.doubleSpinBox_6.value()
        P[3, 0] = self.doubleSpinBox_7.value()
        P[3, 1] = self.doubleSpinBox_8.value()


    def draw_curves(self):
        '绘制当前可交互图形'
        self.update_points()

        # change to ax setting(equal to plt.xlim)
        #previousx = plt.xlim()
        #previousy = plt.ylim()
        previousx = self.ax.get_xlim()
        previousy = self.ax.get_ylim()
        #plt.cla()
        self.ax.clear() # clear previous ax before drawing new ax
        #########################################

        if self.figure_list:
            for p in self.figure_list:
                self.draw_previous_figure(p)

        lw = self.horizontalSlider.value()
        ms = self.horizontalSlider.value()
        mark = self.lineEdit.text()

        if self.checkBox_2.isChecked(): # checkBox_2 is whether to draw control point
            self.ax.plot(P[0, 0], P[0, 1], 'bo', markersize=7)
            self.ax.plot(P[1, 0], P[1, 1], 'ro', markersize=7)
            self.ax.plot(P[2, 0], P[2, 1], 'go', markersize=7)
            self.ax.plot(P[3, 0], P[3, 1], 'yo', markersize=7)


        ######Path Algorithm#######################################
        if self.radioButton.isChecked():
            xt, yt = [], []
            for T in TList:
                xt.append(T.dot(B).dot(P[:, 0]))
                yt.append(T.dot(B).dot(P[:, 1]))
            try:
                self.ax.plot(xt, yt, mark, linewidth=lw, markersize=ms)
            except Exception as e:
                self.ax.plot(xt, yt, '-', linewidth=lw, markersize=ms)

            if self.checkBox.isChecked():
                self.ax.plot(P[:2, 0], P[:2, 1], 'b--', linewidth=1)
                self.ax.plot(P[2:, 0], P[2:, 1], 'r--', linewidth=1)
        elif self.radioButton_2.isChecked():
            xt, yt = [], []
            for T in TList:
                xt.append(T.dot(Bspline).dot(P[:, 0]))
                yt.append(T.dot(Bspline).dot(P[:, 1]))
            try:
                self.ax.plot(xt, yt, mark, linewidth=lw, markersize=ms)
            except Exception as e:
                self.ax.plot(xt, yt, '-', linewidth=lw, markersize=ms)
            if self.checkBox.isChecked():
                self.ax.plot(P[:2, 0], P[:2, 1], 'b--', linewidth=1)
                self.ax.plot(P[2:, 0], P[2:, 1], 'r--', linewidth=1)
                self.ax.plot(P[1:3, 0], P[1:3, 1], 'y--', linewidth=1)
        elif self.radioButton_linear.isChecked():
            xt, yt = [], []
            for control_point_index in range(P.shape[0]):
                xt.append(P[control_point_index,0])
                yt.append(P[control_point_index,1])
                self.ax.plot(xt, yt, mark, linewidth=lw, markersize=ms)           
        ############################################################

        if self.checkBox_3.isChecked(): # checkbox3 is whether to draw grid
            self.ax.grid(linestyle='-', linewidth=0.5)
        
        #plt.axis('equal')
        self.ax.set_aspect('auto')
        self.ax_curvature.set_aspect('auto')
        if self.flag:
            # change to ax setting(equal to plt.xlim)
            #plt.xlim(previousx)
            #plt.ylim(previousy)
            self.ax.set_xlim(previousx)
            self.ax.set_ylim(previousy)
            #########################################

        self.flag = True
        self.canvas.draw()

    def draw_curvature_2d(self):
        '繪製曲率圖形'
        pass

    def draw_previous_figure(self, s):
        '绘制已经fix的图形'
        lw = s[1]
        ms = s[2]
        mark = s[3]
        curves = s[4]
        s = s[0]
        if self.checkBox_2.isChecked():
            self.ax.plot(s[0, 0], s[0, 1], 'ko', markersize=7)
            self.ax.plot(s[1, 0], s[1, 1], 'ko', markersize=7)
            self.ax.plot(s[2, 0], s[2, 1], 'ko', markersize=7)
            self.ax.plot(s[3, 0], s[3, 1], 'ko', markersize=7)

        if self.radioButton.isChecked():
            xt, yt = [], []
            for T in TList:
                xt.append(T.dot(B).dot(s[:, 0]))
                yt.append(T.dot(B).dot(s[:, 1]))
            try:
                self.ax.plot(xt, yt, mark, linewidth=lw, markersize=ms)
            except Exception as e:
                self.ax.plot(xt, yt, '-', linewidth=lw, markersize=ms)

            if self.checkBox.isChecked():
                self.ax.plot(s[:2, 0], s[:2, 1], 'k--', linewidth=1)
                self.ax.plot(s[2:, 0], s[2:, 1], 'k--', linewidth=1)
        elif self.radioButton_2.isChecked():
            xt, yt = [], []
            for T in TList:
                xt.append(T.dot(Bspline).dot(s[:, 0]))
                yt.append(T.dot(Bspline).dot(s[:, 1]))
            try:
                self.ax.plot(xt, yt, mark, linewidth=lw, markersize=ms)
            except Exception as e:
                self.ax.plot(xt, yt, '-', linewidth=lw, markersize=ms)
            if self.checkBox.isChecked():
                self.ax.plot(s[:2, 0], s[:2, 1], 'k--', linewidth=1)
                self.ax.plot(s[2:, 0], s[2:, 1], 'k--', linewidth=1)
                self.ax.plot(s[1:3, 0], s[1:3, 1], 'k--', linewidth=1)
        elif self.radioButton_linear.isChecked():
            xt, yt = [], []
            for ii in range(P.shape[0]):
                xt.append(P[ii,0])
                yt.append(P[ii,1])
                self.ax.plot(xt, yt, mark, linewidth=lw, markersize=ms) 

    def get_ind_under_point(self, event):
        '计算鼠标点是否在某个点的范围内'
        xy = np.asarray(self.poly.xy)
        xyt = self.poly.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.sqrt((xt - event.x)**2 + (yt - event.y)**2)
        indseq = np.nonzero(np.equal(d, np.amin(d)))[0]
        ind = indseq[0]

        if d[ind] >= self.epsilon:
            ind = None
        return ind

    def button_press_callback(self, event):
        '鼠标按下事件处理'
        if not self.showverts:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self._ind = self.get_ind_under_point(event)

    def button_release_callback(self, event):
        '鼠标松开事件处理'
        if not self.showverts:
            return
        if event.button != 1:
            return
        self._ind = None


    def motion_notify_callback(self, event):
        '鼠标移动事件处理'
        if not self.showverts:
            return
        if self._ind is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        x, y = event.xdata, event.ydata
        self.poly.xy[self._ind] = x, y
        P = np.array(self.poly.xy)
        index = self._ind
        if index == 0:
            self.doubleSpinBox_1.setValue(P[0, 0])
            self.doubleSpinBox_2.setValue(P[0, 1])
        elif index == 1:
            self.doubleSpinBox_3.setValue(P[1, 0])
            self.doubleSpinBox_4.setValue(P[1, 1])
        elif index == 2:
            self.doubleSpinBox_5.setValue(P[2, 0])
            self.doubleSpinBox_6.setValue(P[2, 1])
        elif index == 3:
            self.doubleSpinBox_7.setValue(P[3, 0])
            self.doubleSpinBox_8.setValue(P[3, 1])

    def show_information(self):
        self.Dialog2.show()


if __name__ == '__main__':
    MainWindow()
