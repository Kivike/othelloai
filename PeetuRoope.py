from reversi.Node import Node
from reversi.Move import Move
from reversi.GameState import GameState
from reversi.VisualizeGraph import VisualizeGraph
from reversi.VisualizeGameTable import VisualizeGameTable
from reversi.ReversiAlgorithm import ReversiAlgorithm
import time, sys
import threading

class PeetuRoope(ReversiAlgorithm):
	visualizeFlag = False
	bestMove = None
	sendMove = False
	
	def __init__(self):
		threading.Thread.__init__(self);
		pass

	def requestMove(self, requester):
		self.sendMove = True

	def init(self, game, state, playerIndex, turnLength):
		print "INITING"
		self.state = state
		self.playerIndex = playerIndex
		self.controller = game


	@property
	def name(self):
		return "PeetuRoope"

	def cleanup(self):
		return

	def run(self):
		print "starting algo ... "
		self.sendMove = False
		moves = self.state.getPossibleMoves(self.playerIndex)
		self.bestMove = moves[0]

		for move in moves:
			print str(move.x) + " " + str(move.y)

		while not self.sendMove:
			pass

		self.controller.doMove(self.bestMove)

		