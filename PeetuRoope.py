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
	tree = None
	
	def __init__(self):
		threading.Thread.__init__(self);
		pass

	def requestMove(self, requester):
		pass

	def init(self, game, state, playerIndex, turnLength):
		print "INITING"
		self.state = state
		self.playerIndex = playerIndex
		self.controller = game
		self.turnLength = turnLength


	@property
	def name(self):
		return "PeetuRoope"

	def cleanup(self):
		return

	def run(self):
		print "starting algo ... "

		self.createTree()

		self.sendMove = False
		moves = self.state.getPossibleMoves(self.playerIndex)
		self.bestMove = moves[0]

		for move in moves:
			print str(move.x) + " " + str(move.y)

		startTime = time.time()

		while self.turnLength - (time.time() - startTime) > 0.1:
			pass

		self.controller.doMove(self.bestMove)

	def createTree(self):
		moves = self.state.getPossibleMoves(self.playerIndex)
		state = self.state
		self.recursiveTree(Node(state, moves[0]), state, 0, 2, self.playerIndex)


	def recursiveTree(self, node, state, count, depth, playerIndex):
		count+=1
		if count >= depth:
			return;

		moves = state.getPossibleMoves(playerIndex);

		for move in moves:
			newstate = state.getNewInstance(move.x, move.y, move.player)
			child = Node(newstate, move)
			node.addChild(child)
			self.recursiveTree(child, newstate, count, depth, 1 - playerIndex)

		