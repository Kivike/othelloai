import subprocess
import sys, os
import time
import threading

sys.path.append("ReversiGame-0.0.0-py2.7.egg")

from reversi.CommandLineGame import CommandLineGame

class AlgoTest():
    firstPlayer = ""
    secondPlayer = ""

    # Max duration of one game is 60 * turnLength (in seconds)
    turnLength = 0

    def __init__(self, firstPlayer, secondPlayer, turnLength):
        self.firstPlayer = firstPlayer
        self.secondPlayer = secondPlayer
        self.turnLength = turnLength

    def run(self):
        args = []
        args.append("AlgoTester.py")
        args.append(self.firstPlayer)
        args.append(self.secondPlayer)
        args.append(str(self.turnLength))

        if len(args) == 4:
            try:
                commandgame = CommandLineGame(args)
            except IOError:
                print "Reversi >> IO error while trying to read user input."
            except KeyboardInterrupt:
                print "Reversi >> InterruptedException occurred (isn't it clear? :D)."
        else:
            print "Reversi >> Error: The number of given parameters is wrong. "
            print "Example: \"./run.sh LousyBlue CheapBlue 1\"."

class Tester(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        tests = []
        tests.append(AlgoTest("HarryBotter", "LousyBlue", 1))
        tests.append(AlgoTest("HarryBotter", "EstaraBot", 1))
        tests.append(AlgoTest("EstaraBot", "HarryBotter", 1))
        tests.append(AlgoTest("HarryBotter", "SparcPy", 1))
        tests.append(AlgoTest("SparcPy", "HarryBotter", 1))
        tests.append(AlgoTest("HarryBotter", "Crobot", 1))
        tests.append(AlgoTest("Crobot", "HarryBotter", 1))
        tests.append(AlgoTest("HarryBotter", "HAL", 1))
        tests.append(AlgoTest("HAL", "HarryBotter", 1))
        tests.append(AlgoTest("HarryBotter", "GonaBOT", 1))
        tests.append(AlgoTest("GonaBOT", "HarryBotter", 1))
        tests.append(AlgoTest("HarryBotter", "SavuAlgo", 1))
        tests.append(AlgoTest("SavuAlgo", "HarryBotter", 1))

        print "RUNNING %d TESTS" % (len(tests))

        for i in range(len(tests)):
            print "RUNNING TEST ", i

            tests[i].run()

        print "TESTS ENDED"

class TestThread(threading.Thread):
    def __init__(self, firstPlayer, secondPlayer, turnLength):
        threading.Thread.__init__(self)
        self.firstPlayer = firstPlayer
        self.secondPlayer = secondPlayer
        self.turnLength = turnLength

    def run(self):
        threadLock.acquire()

        args = []
        args.append("AlgoTester.py")
        args.append(self.firstPlayer)
        args.append(self.secondPlayer)
        args.append(str(self.turnLength))

        if len(args) == 4:
            try:
                commandgame = CommandLineGame(args)
            except IOError:
                print "Reversi >> IO error while trying to read user input."
            except KeyboardInterrupt:
                print "Reversi >> InterruptedException occurred (isn't it clear? :D)."
        else:
            print "Reversi >> Error: The number of given parameters is wrong. "
            print "Example: \"./run.sh LousyBlue CheapBlue 1\"."

        threadLock.release()

threadLock = threading.Lock()
threads = []

thread1 = TestThread("HarryBotter", "LousyBlue", 1)
thread1.run()

thread2 = TestThread("HarryBotter", "EstaraBot", 1)
thread2.run()

threads.append(thread1)
threads.append(thread2)

for t in threads:
    t.join()

print "EXITING MAIN THREAD"



