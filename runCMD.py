import subprocess
import sys, os

sys.path.append("ReversiGame-0.0.0-py2.7.egg")
#print sys.path

#print os.getcwd()

from reversi.CommandLineGame import CommandLineGame
# Check argument count
if CommandLineGame.DEBUG_VERSION:
    print "Reversi >> Argument count: " , len(sys.argv)

if len(sys.argv) == 4:
    try:
        commandgame = CommandLineGame(sys.argv)
    except IOError:
        print "Reversi >> IO error while trying to read user input."
    except KeyboardInterrupt:
        print "Reversi >> InterruptedException occurred (isn't it clear? :D)."
else:
    print "Reversi >> Error: The number of given parameters is wrong. "
    print "Example: \"./run.sh LousyBlue CheapBlue 1\"."

    sys.exit() # Exit program.