import traceback
import requests
import xlrd
from PyQt5.QtWidgets import QTableWidgetItem
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from PyQt5 import QtWidgets, uic
import PyQt5
import time
import json
import matplotlib.style as mplstyle
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pyqtgraph as pg
from pattern.web import Bing, plaintext
from pattern.web import Twitter, plaintext
from pattern.graph import Graph
import traceback


# main class def
class StockWindow:
    # constructor, doesn't really take any arguments
    # all of the attributes of the window file are defined in the .ui file
    def __init__(self):
        # file which records errors (exceptions)
        self.file_name = 'StockV4 Error Log.txt'
        self.file_for_err = open(self.file_name, 'a')

        # Application main window
        self.app = QtWidgets.QApplication([])

        # Loads the UI from a .ui file
        self.sw = uic.loadUi("StockLookup.ui")

        # this is the window in which we have our graph
        self.sw.figure = plt.figure(num=None, figsize=(100, 80), dpi=80, facecolor='w', edgecolor='k')
        self.sw.canvas = FigureCanvas(self.sw.figure)
        self.sw.vertL.addWidget(self.sw.canvas)
        self.ax = self.sw.figure.add_subplot(1, 1, 1)

        # this part of the main constructor simply initializes the main buttons
        # gets the info from the APIs, etc
        self.variations_names = ["1 Month", "3 Months", "6 Months", "Year to Date", "1 Year", "2 Years", "5 Years"]
        self.variations_simple = ["1m", "3m", "6m", "ytd", "1y", "2y", "5y"]

        # these following lines of code make an API call for all the available stock handles for this API
        # it then parses it as a JSON file, and adds them to the array of names
        self.res = requests.get("https://api.iextrading.com/1.0/tops")
        self.rsps = json.loads(self.res.text)
        self.arrOfNms = []

        # adds to the array of names
        for i in self.rsps:
            symbol_handle = i['symbol']
            self.arrOfNms.append(symbol_handle)

        # the past step isn't necessary, but i wanted to then sort the array, sp when the names are added to
        # the list, they are in alphabetical order
        self.arrOfNms.sort()

        # populates the list of Company names with the company names
        for i in self.arrOfNms:
            self.sw.listWidget.addItem(str(i))

        # adds the different time frames for historical data
        self.sw.comboBox.addItems(self.variations_names)

        # links the different buttons to the desired functions
        # these first two lines make sure than whenever a line is selected,
        # the functions actual and historical are run, thus updating the
        # information in the UI
        # In previous versions, there was a "run" button, which i removed
        # I prefer the information to be updated as the names are clicked
        self.sw.listWidget.itemClicked.connect(self.actual)
        self.sw.listWidget.itemClicked.connect(self.historical)

        # these lines are for the buttons
        self.sw.hist_btn.clicked.connect(self.historical)
        self.sw.clear_btn.clicked.connect(self.clear_button)
        self.sw.line_search.textEdited.connect(self.search)
        self.sw.live_btn.clicked.connect(self.live_up)

        # run the app
        self.sw.show()
        self.app.exec()

    # Function for the "Actual" button
    def actual(self):
        # try catch block
        try:
            # variable to store the status code
            # since we use an api, anything other than 200 is probably not good
            sts = "Status cd: "

            # gets the symbol from the selected item in the list
            sym = str((self.sw.listWidget.currentItem().text()))
            res = requests.get("https://api.iextrading.com/1.0/stock/" + sym +
                               "/batch?types=quote,news,chart&range=1m&last=10")
            rsps = json.loads(res.text)
            price = rsps['quote']['latestPrice']
            close = rsps['quote']['close']
            td_hl = str(rsps['quote']['high']) + " | " + str(rsps['quote']['low'])
            wk_hl52 = str(rsps['quote']['week52High']) + " | " + str(rsps['quote']['week52Low'])
            vol = rsps['quote']['latestVolume']
            change = "$" + str(rsps['quote']['change']) + " | %" + str(rsps['quote']['changePercent'])
            div = str(int(float(rsps['quote']['ytdChange']) * 100)) + "%"
            self.sw.line_open.setText("$ " + str(price))
            self.sw.line_close.setText("$ " + str(close))
            self.sw.td_high_low.setText("$ " + str(td_hl))
            self.sw.line_52wk.setText("$ " + str(wk_hl52))
            self.sw.line_vol.setText(str(vol))
            self.sw.line_change.setText(str(change))
            self.sw.line_div.setText(str(div))
            s = str(self.sw.listWidget.currentItem().text())
        except Exception:
            self.file_for_err.write(traceback.print_exc())
            self.sw.line_open.setText("Something went wrong.")

    def historical(self):
        try:
            sym = str((self.sw.listWidget.currentItem().text()))
            tm = self.variations_simple[self.sw.comboBox.currentIndex()]
            res = requests.get("https://api.iextrading.com/1.0/stock/" + sym + "/chart/" + tm)
            rsps = json.loads(res.text)
            close = []
            opn = []
            indi = [x for x in range(len(rsps))]
            low = []

            for i in range(len(rsps)):
                close.append(float(rsps[i]['close']))
                opn.append(float(rsps[i]['open']))
                low.append(float(rsps[i]['low']))

            self.ax.clear()
            self.ax.set_title(
                "Stock prices for " + sym.upper() + " for " + self.variations_names[self.sw.comboBox.currentIndex()])
            self.ax.plot(indi, close, color='blue', label='Close')
            self.ax.plot(indi, opn, color='green', label="Open")
            self.ax.plot(indi, low, color="red", label="Low")
            self.ax.grid()
            self.ax.legend(loc="upper right")
            self.sw.canvas.draw()
        except Exception:
            self.file_for_err.write(str(traceback.print_exc()) + '\n')
            self.file_for_err.write(str(rsps) + '\n' + 'end of error \n')
            self.clear_button()
            self.sw.line_open.setText("Error.")

    def clear_button(self):
        clearr = ""
        self.sw.line_open.setText(clearr)
        self.sw.line_close.setText(clearr)
        self.sw.td_high_low.setText(clearr)
        self.sw.line_52wk.setText(clearr)
        self.sw.line_vol.setText(clearr)
        self.sw.line_change.setText(clearr)
        self.sw.line_div.setText(clearr)

    def search(self):
        print('search')
        self.sw.listWidget.clear()
        hey = str(self.sw.line_search.text().upper())
        ln = len(hey)
        for i in range(len(self.arrOfNms)):
            hey2 = str(self.arrOfNms[i])
            if hey == hey2[:ln]:
                self.sw.listWidget.addItem(str(self.arrOfNms[i]))
            else:
                continue

    def live_up(self):
        print()


# TODO Add functionality where:
# 1. When the list is formed, the information is compiled in a database, thus eliminating
#    the need for constant api calls. This would be only for the constant data, and
#     would be saved once a day.
# 2. History for past api calls (i.e. past searches)
# 3. Open error log in the GUI
# 4. better graophs


a = StockWindow()
