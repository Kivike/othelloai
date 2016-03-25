import subprocess
import sys, os

sys.path.append("ReversiGame-0.0.0-py2.7.egg")
print sys.path

print os.getcwd()

from reversi.MainWindow import MainWindow
MainWindow()