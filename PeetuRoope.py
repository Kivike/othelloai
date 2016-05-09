from reversi.Node import Node
from reversi.Move import Move
from reversi.GameState import GameState
from reversi.VisualizeGraph import VisualizeGraph
from reversi.VisualizeGameTable import VisualizeGameTable
from reversi.ReversiAlgorithm import ReversiAlgorithm
import time, sys
import threading
import random

# Roope Rajala 2374556
# Peetu Nuottajarvi
class PeetuRoope(ReversiAlgorithm):
	DEBUG_LOG = True

	# This is the move that is updated while algorithm searches deeper
	# bestMove is given when time runs out
	bestMove = None
	
	# Flag to check when algorithms needs to stop
	running = False

	# The game state when algorithm starts
	initialState = None

	# 0 or 1
	playerIndex = -1

	currentTurn = 0

	START_DEPTH = 0
	# How deep will algorithm go? Time is usually more limiting
	MAX_DEPTH = 12

	currentIterationDepth = 0

	# Timer to see how long the game takes
	gameStartTime = -1

    # http://dhconnelly.github.io/paip-python/docs/paip/othello.html
	SCORE_WEIGHTS = [
	    [ 120, 	-20,  20,  10,  10,   20, -20,  120],
	    [-20, 	-40,  -5,  -5,  -5,   -5, -40,  -20],
	    [ 20,  	 -5,  15,   3,   3,   15,  -5,   20],
	    [ 10,  	 -5,   3,   3,   3,    3,  -5,   10],
	    [ 10,  	 -5,   3,   3,   3,    3,  -5,   10],
	    [ 20,  	 -5,  15,   3,   3,   15,  -5,   20],
	    [-20, 	-40,  -5,  -5,  -5,   -5, -40,  -20],
	    [ 120, 	-20,  25,  10,  10,   20, -20,   120]
	]

	def __init__(self):
		threading.Thread.__init__(self);
		pass

	def requestMove(self, requester):
		self.doBestMove()
		self.running = False

	def init(self, game, state, playerIndex, turnLength):
		self.initialState = state
		self.playerIndex = playerIndex
		self.controller = game
		self.turnLength = turnLength

		PeetuRoope.currentTurn += 1

		if PeetuRoope.gameStartTime == -1:
			PeetuRoope.gameStartTime  = time.time()

	@property
	def name(self):
		return "PeetuRoope"

	def cleanup(self):
		if self.DEBUG_LOG:
			gameDuration = '%.4f' % (time.time() - PeetuRoope.gameStartTime)
			print "The game took " + str(gameDuration) + " seconds"

	def run(self):
		print "Starting algorithm PeetuRoope, own playerIndex: " + str(self.playerIndex)
		self.currentIterationDepth = self.START_DEPTH

		# Run was called too soon sometimes
		while self.initialState == None:
			time.sleep(30)

		self.running = True
		self.bestMove = None

		print "Current score: " + str(self.initialState.getMarkCount(self.playerIndex)) + "-" + str(self.initialState.getMarkCount(1 - self.playerIndex));

		possibleMoveCount = len(self.initialState.getPossibleMoves(self.playerIndex))

		if possibleMoveCount == 0:
			# No possible moves, must skip turn
			self.running = False
			self.controller.doMove(None)
		elif possibleMoveCount == 1:
			# Only one possible move to make
			self.running = False
			self.controller.doMove(self.initialState.getPossibleMoves(self.playerIndex)[0])

		while self.running:
			# Time how long each depth takes
			iterationStart = time.time();

			rootNode = Node(self.initialState, None)

			self.alphaBetaFromRoot(rootNode, 0, self.currentIterationDepth, self.playerIndex, True)

			optimalChild = rootNode.getOptimalChild()

			if not self.running:
				break

			if optimalChild == None:
				print "optimal child is None"
				rootNode.printtree()
				self.printPossibleMoves(self.initialState)
				# Something went wrong when creating the tree...
			else:
				rootNode = optimalChild
				self.bestMove = optimalChild.getMove()

			# Gradually increase search depth
			self.currentIterationDepth += 1

			lastSearchTime = '%.4f' % (time.time() - iterationStart)

			if self.DEBUG_LOG:
				print "Searched to depth " + str(self.currentIterationDepth) + " in " + str(lastSearchTime) + " seconds"

			if self.currentIterationDepth >= self.MAX_DEPTH:
				break

		self.doBestMove()

	def printPossibleMoves(self, state):
		print "Possible moves"
		for move in state.getPossibleMoves(self.playerIndex):
			print move.toString()

	def doBestMove(self):
		if self.bestMove == None:
			return

		self.controller.doMove(self.bestMove)

		print "Made move " + self.bestMove.toString()
		self.bestMove = None


	# Creates tree starting from root to given depth limit and then
	# recursively use minmax to score the nodes
	def alphaBetaFromRoot(self, node, currentIterationDepth, depthLimit, playerIndex, maximize):
		if currentIterationDepth > depthLimit:
			return self.evaluateNodeScore(node)

		if not node.hasChildren():
			moves = node.state.getPossibleMoves(playerIndex)

			if len(moves) == 0:
				return self.evaluateNodeScore(node)
			else:
				random.shuffle(moves)

				for move in moves:
					newstate = node.state.getNewInstance(move.x, move.y, move.player)
					node.addChild(Node(newstate, move))

		currentIterationDepth += 1

		if maximize:
			node.score = -10000

			for child in node.children:
				child.score = self.alphaBetaFromRoot(child, currentIterationDepth, depthLimit, 1 - playerIndex, not maximize)

				if child.score > node.score:
					node.score = child.score

					if node.parent != None and node.score <= node.parent.score:
						# Cut off, we're not choosing this one anyway
						break
			return node.score
		else:
			node.score = 10000

			for child in node.children:
				child.score = self.alphaBetaFromRoot(child, currentIterationDepth, depthLimit, 1 - playerIndex, not maximize)

				if child.score < node.score:
					node.score = child.score

					if node.parent != None and node.score >= node.parent.score:
						# Cut off, we're not choosing this one anyway
						break
			return node.score

	def evaluateNodeScore(self, node):
		score = 0
		state = node.state
		move = node.getMove()

		for x in range(0, 8):
			for y in range(0, 8):
				weight = PeetuRoope.SCORE_WEIGHTS[x][y]

				if self.playerIndex != state.getMarkAt(x, y):
					score -= weight
				else:
					score += weight

		# Give score based on possible moves for the node
		score += len(node.children)

		return score