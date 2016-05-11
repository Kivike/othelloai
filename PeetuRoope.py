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

	START_DEPTH = 1
	# How deep will algorithm go? Time is usually more limiting
	MAX_DEPTH = 10

	currentIterationDepth = 0

	# Timer to see how long the game takes
	gameStartTime = -1

	# 8x8 array
	# True = stable
	stableDiscs = []

    # http://dhconnelly.github.io/paip-python/docs/paip/othello.html
	SCORE_WEIGHTS = [
	    [ 120, 	-20,  20,  10,  10,   20, -20,  120],
	    [-20, 	-500,  -5,  -5,  -5,   -5, -500,  -120],
	    [ 20,  	 -5,  15,   3,   3,   15,  -5,   50],
	    [ 10,  	 -5,   3,   3,   3,    3,  -5,   10],
	    [ 10,  	 -5,   3,   3,   3,    3,  -5,   10],
	    [ 20,  	 -5,  15,   3,   3,   15,  -5,   20],
	    [-20, 	-500,  -5,  -5,  -5,   -5, -500,  -120],
	    [ 120, 	-20,  20,  10,  10,   20, -20,   120]
	]

	STABILITY_WEIGHT = {
		"stable" 	: 120,
		"danger" 	: -120,
		"neutral" 	: 10,
		"edge"		: 15
	}

	MOBILITY_WEIGHT = 30

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

			for x in range(0, 8):
				PeetuRoope.stableDiscs.append([False for x in range(8)])

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

			self.alphaBetaFromRoot(rootNode, 0, self.currentIterationDepth, -sys.maxint, sys.maxint, self.playerIndex, True)

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

		#self.printPossibleMoves(self.initialState)
		print "Made move " + self.bestMove.toString()
		self.bestMove = None


	# Creates tree starting from root to given depth limit and then
	# recursively use minmax to score the nodes
	def alphaBetaFromRoot(self, node, currentIterationDepth, depthLimit, alpha, beta, playerIndex, maximize):
		if currentIterationDepth > depthLimit:
			return self.evaluateNodeScore(node)

		if not node.hasChildren():
			moves = node.state.getPossibleMoves(playerIndex)

			if len(moves) == 0:
				return self.evaluateNodeScore(node)
			else:
				#random.shuffle(moves)

				for move in moves:
					newstate = node.state.getNewInstance(move.x, move.y, move.player)
					node.addChild(Node(newstate, move))

		currentIterationDepth += 1

		if maximize:
			node.score = -sys.maxint

			for child in node.children:
				child.score = self.alphaBetaFromRoot(child, currentIterationDepth, depthLimit, 
					alpha, beta, 1 - playerIndex, not maximize)

				if child.score > node.score:
					node.score = child.score

				if child.score > alpha:
					alpha = child.score

				if beta <= alpha:
					break
			return node.score
		else:
			node.score = sys.maxint

			for child in node.children:
				child.score = self.alphaBetaFromRoot(child, currentIterationDepth, depthLimit,
					alpha, beta, 1 - playerIndex, not maximize)

				if child.score < node.score:
					node.score = child.score

				if child.score < beta:
					beta = child.score

				if beta <= alpha:
					break
			return node.score

	def evaluateNodeScore(self, node):
		if(self.currentTurn < 5):
			return self.greedyEvaluate(node)
		elif(self.currentTurn < 25):
			return self.weightedEvaluate(node)
		else:
			return self.greedyEvaluate(node)


	def weightedEvaluate(self, node):
		score = 0
		state = node.state
		move = node.getMove()

		#return state.getMarkCount(move.player)

		for x in range(0, 8):
			for y in range(0, 8):
				mark = state.getMarkAt(x, y)
				# Check for empty square
				if mark == -1:
					continue

				edge = x == 0 or x == 7 or y == 0 or y == 7

				weight = 0

				stability = self.isPositionStable(node, x, y, edge, mark)

				if stability == 1:
					# Own stable
					weight = PeetuRoope.STABILITY_WEIGHT["stable"]
				elif stability == -1:
					# Opponent stable
					weight = -PeetuRoope.STABILITY_WEIGHT["danger"]
				else:
					# Flippable, seemingly not dangerous
					if edge:
						weight = PeetuRoope.STABILITY_WEIGHT["edge"]
					else:
						weight = PeetuRoope.STABILITY_WEIGHT["neutral"]

				if self.playerIndex == mark:
					score += weight
				else:
					score -= weight


		# Give score based on possible moves for the node
		#score -= node.state.getPossibleMoveCount(1 - move.player) * PeetuRoope.MOBILITY_WEIGHT

		return score

	def greedyEvaluate(self, node):
		return node.state.getMarkCount(self.playerIndex)

	# Returns 1 if stable
	# Returns 0 if not stable / neutral / flippable
	# Returns -1 if dangerous
	def isPositionStable(self, node, x, y, edge, player):
		if PeetuRoope.stableDiscs[x][y] == True:
			return 1

		# Only check stability for edges and corners
		if not edge:
			return 0

		dangerInOneDirection = False

		if x == 0 or x == 7:
			for y in range(y, 8):
				mark = node.state.getMarkAt(x, y)
				if mark != player:
					if mark != -1:
						dangerInOneDirection = True
					break

				if y == 7:
					PeetuRoope.stableDiscs[x][y] = player
					return 1

			for y in range(y, -1, -1):
				mark = node.state.getMarkAt(x, y)
				if mark != player:
					if mark != -1:
						dangerInOneDirection = True
					break

				if y == 0:
					PeetuRoope.stableDiscs[x][y] = True
					return 1
		else:
			for x in range(x, 8):
				mark = node.state.getMarkAt(x, y)
				if mark != player:
					if mark != -1:
						dangerInOneDirection = True
					break

				if x == 7:
					PeetuRoope.stableDiscs[x][y] = True
					return 1

			for x in range(x, -1, -1):
				mark = node.state.getMarkAt(x, y)
				if mark != player:
					if mark != -1:
						dangerInOneDirection = True
					break

				if x == 0:
					PeetuRoope.stableDiscs[x][y] = True
					return 1

		if dangerInOneDirection:
			# Opponent could flip this next turn
			return -1
		else:
			# Flippable but not dangerous
			return 0