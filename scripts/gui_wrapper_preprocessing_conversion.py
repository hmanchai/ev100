import os
import glob
import shutil
import sys

import pandas as pd
import re
import csv
import gzip
import fnmatch
import time
from datetime import timedelta
import calendar
import logging
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QCheckBox, QGridLayout, QGroupBox, QVBoxLayout, QTabBar, QTabWidget

class Window(QWidget):

    def __init__(self, parent=None):
        window_height = 500
        window_width = 600

        super(Window, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()

        self.tabs.addTab(self.tab1, "Run")
        self.tabs.addTab(self.tab2, "Copy STIL Zip Files")
        self.tabs.addTab(self.tab3, "Velocity Conversion .do")
        self.tabs.addTab(self.tab4, "Generate PATS.txt")
        self.tabs.resize(window_width, window_height)

        self.run_tab(self.tab1)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        self.setWindowTitle("Vector Preprocessing and Conversion")
        self.resize(window_width, window_height)

    def run_tab(self, tab1):
        grid = QGridLayout()
        grid.addWidget(self.group_box_to_run("Scripts to Run"), 0, 0)
        grid.addWidget(self.logger_group_box(), 0, 1)
        grid.addWidget(QPushButton("Run"), 1, 0)
        tab1.setLayout(grid)

    def group_box_to_run(self, title):
        checkbox_run_titles = ["Copy STIL Zip Files", "Velocity Conversion .do", "Generate PATS.txt"]
        groupBox = QGroupBox(title)
        vbox = QVBoxLayout()
        vbox = self.add_checkboxes(checkbox_run_titles, vbox)
        vbox.addStretch(1)
        groupBox.setLayout(vbox)
        return groupBox

    def logger_group_box(self):
        groupBox = QGroupBox("Run Log")
        return groupBox

    def add_checkboxes(self, box_titles, vbox):
        for title in box_titles:
            check_box = QCheckBox(title)
            vbox.addWidget(check_box)
        return vbox
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    clock = Window()
    clock.show()
    sys.exit(app.exec_())