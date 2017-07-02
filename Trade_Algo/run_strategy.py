
import numpy as np
import threading
import time
from datetime import datetime
import sys

# Broker ist noch eine dummy Klasse. Sollte folgende Funktionen beinhalten:
# buy_order, sell_order

'''
new class to test the run() thread within the the intersection class
'''

class run_strategy(threading.Thread):
    def __init__(self, myinput, broker, history, timeInterval):
        threading.Thread.__init__(self)
        self.time_series = []
        self.short_mean = []
        self.long_mean = []
        self.short_win = myinput.window_short     # sollte noch dynamische werden
        self.long_win = myinput.window_long
        self.Broker = broker
        self.series_name = myinput.series_name
        self.history = history
        self.__last_short = []
        self.__last_long = []

        self.iterations = 0
        self.daemon = True  # OK for main to exit even if instance is still running
        self.paused = True  # start out paused
        self.state = threading.Condition()
        self.timeInteval = timeInterval

        # IMPORTANT: Broker muss initialisiert werden!
        self.Broker.initialize()

    def eval_rollings(self):
        self.short_mean = self.history.getRollingMean(self.short_win)
        self.long_mean = self.history.getRollingMean(self.long_win)
        self.__last_short = np.array(self.short_mean)[-1]
        self.__last_long = np.array(self.long_mean)[-1]

    def intersect(self):
        # call the evaluation
        try:
            self.eval_rollings()
        except FileNotFoundError:
            print('Check the name of the data directory: XY_data')
            sys.exit(0)

        if self.__last_short > self.__last_long:
            ## das ist quasi das Kriterium, um zu checken ob wir Währung haben oder nicht,
            ## entsprechend sollten wir kaufen, oder halt nicht
            if self.Broker.asset_status is False and self.Broker.broker_status is False:
                self.Broker.buy_order()
                print('go long')
                print('long mean: ', self.__last_long)
                print('short mean: ', self.__last_short)
                print(' ')
            else:
                self.Broker.idle()
                print('keep calm and HODL')
                print('long mean: ', self.__last_long)
                print('short mean: ', self.__last_short)
                print(' ')

        elif self.__last_long > self.__last_short:
            if self.Broker.asset_status is True and self.Broker.broker_status is False:
                self.Broker.sell_order()
                print('go short')
                print('long mean: ', self.__last_long)
                print('short mean: ', self.__last_short)
                print(' ')
            else:
                self.Broker.idle()
                print('short, idle')
                print('long mean: ', self.__last_long)
                print('short mean: ', self.__last_short)
                print(' ')
        else:
            ## idle, soll nix machen
            self.Broker.idle()
            print('idle')
            print('long mean: ', self.__last_long)
            print('short mean: ', self.__last_short)
            print(' ')

    #*************************************************
    # this is the new run funciton. still to test...
    # not to use...


    # oder evtl as eigenen Thread das alles...
    def run(self):
        self.resume() # unpause self
        while True:
            try:    # das Programm soll nochmal aufgerufen werden, wenn ein Fehler geworfen wird.
                with self.state:
                    if self.paused:
                        self.state.wait()  # block until notified
                ###################
                self.intersect()
                ###################
                print('last intersect: ' + str(datetime.now()))
                time.sleep(self.timeInteval)
                self.iterations += 1
            except EmptyDataError:
                self.run()

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()  # unblock self if waiting

    def pause(self):
        with self.state:
            self.paused = True  # make self block and wait
            print('Strategy is currently paused!')