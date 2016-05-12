from reversi.Node import Node
from reversi.Move import Move
from reversi.GameState import GameState
from reversi.VisualizeGraph import VisualizeGraph
from reversi.VisualizeGameTable import VisualizeGameTable
from reversi.ReversiAlgorithm import ReversiAlgorithm
import time, sys
import threading
import random

# Ohello/Reversi AI algorithm
# Bot uses alpha-beta pruning algorithm with
# different score evaluation for different parts of game (early, mid, end)
#
# Roope Rajala 			2374556
# Peetu Nuottajarvi 	2374491
class HarryBotter(ReversiAlgorithm):
	# Evaluation order: Greedy - Table - Stable - Greedy

	####################################################################
	# FOLLOWING VALUES AFFECT HOW WELL THE BOT PLAYS				   #
	####################################################################
	# When to switch to table look up evaluation
	TABLE_TURN = 8

	# When to switch to stable evaluation
	STABLE_TURN = 18 # 18

	# When to switch to greedy evaluation
	# Greedy gets to greater depths so make sure MAX_DEPTH is enough
	GREEDY_TURN = 52 # 50

	# http://dhconnelly.github.io/paip-python/docs/paip/othello.html
	# Used by table evaluation
	SCORE_WEIGHTS = [
		[ 120, 	-20,  20,  10,  10,   20, -20,  120],
		[-20, 	-40,  -5,  -5,  -5,   -5, -40,  -20],
		[ 20,  	 -5,  15,   3,   3,   15,  -5,   20],
		[ 10,  	 -5,   3,   3,   3,    3,  -5,   10],
		[ 10,  	 -5,   3,   3,   3,    3,  -5,   10],
		[ 20,  	 -5,  15,   3,   3,   15,  -5,   20],
		[-20, 	-40,  -5,  -5,  -5,   -5, -40,  -20],
		[ 120, 	-20,  20,  10,  10,   20, -20,   120]
	]

	# Used by stable evaluation
	STABILITY_WEIGHT = 115

	# 5 15 - H0 	C01
	# 5 20 - H01	C01

	# Weight when using table evaluation
	MOBILITY_WEIGHT_TABLE = 5

	# Weight when checking stable discs
	MOBILITY_WEIGHT_STABLE = 20
	#####################################################################

	# Set true for development
	DEBUG_LOG = False

	# This is the move that is updated while algorithm searches deeper
	# bestMove is given when time runs out
	bestMove = None
	
	# Flag to check when algorithms needs to stop
	running = False

	# The game state when algorithm starts
	initialState = None

	# 0 if we start, 1 if opponent starts
	playerIndex = -1

	currentTurn = -1

	START_DEPTH = 0
	# How deep will algorithm go? Time is usually more limiting unless
	# moves are limited
	MAX_DEPTH = 20

	# Depth is iteratively increased
	currentIterationDepth = 0

	# 2D 8x8 array representing the game board
	# ONLY STABILITY FOR CORNERS TO SAVE TIME
	# True = stable
	# False = flippable
	stableDiscs = []

	def __init__(self):
		threading.Thread.__init__(self);

		for x in range(0, 8):
			HarryBotter.stableDiscs.append([False for y in range(8)])

	def requestMove(self, requester):
		self.doBestMove()
		self.running = False

	# Called when own turn starts
	def init(self, game, state, playerIndex, turnLength):
		self.initialState = state
		self.playerIndex = playerIndex
		self.controller = game
		self.turnLength = turnLength

		# Check if running algo first time
		if HarryBotter.currentTurn == -1:
			HarryBotter.currentTurn = playerIndex

			HarryBotter.GREEDY_TURN -= turnLength
		else:
			HarryBotter.currentTurn += 2

	@property
	def name(self):
		return "HarryBotter"

	# Called when game ends
	def cleanup(self):
		pass

	def run(self):
		self.currentIterationDepth = self.START_DEPTH

		# Run was called too soon sometimes
		while self.initialState == None:
			time.sleep(30)

		self.running = True
		self.bestMove = None

		if HarryBotter.DEBUG_LOG:
			# Own score - opponent score
			print "Current score: %d - %d" % (self.initialState.getMarkCount(self.playerIndex), 
			  	self.initialState.getMarkCount(1 - self.playerIndex));

		possibleMoveCount = self.initialState.getPossibleMoveCount(self.playerIndex)

		if possibleMoveCount == 0:
			# No possible moves, must skip turn
			self.running = False
			self.controller.doMove(None)
		elif possibleMoveCount == 1:
			# Only one possible move to make
			self.running = False
			self.controller.doMove(self.initialState.getPossibleMoves(self.playerIndex)[0])

		if HarryBotter.currentTurn > HarryBotter.STABLE_TURN and HarryBotter.currentTurn < HarryBotter.GREEDY_TURN:
			# Only update stable discs when using stable evaluation
			self.updateStableDiscs()

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

			if HarryBotter.DEBUG_LOG:
				lastSearchTime = '%.4f' % (time.time() - iterationStart)
				print "Searched to depth %d in %s seconds" % (self.currentIterationDepth, lastSearchTime)

			if self.currentIterationDepth >= self.MAX_DEPTH:
				break

		self.doBestMove()

	# Update unflippable (stable) discs
	def updateStableDiscs(self):
		for x in range(0,8):
			for y in range(0,8):
				if self.isPositionStable(self.initialState, x, y):
					HarryBotter.stableDiscs[x][y] = True

	# Prints 8x8 board where x is stable and o is flippable
	# Differs from the actual board by rotation, but the board is symmetric
	def printStableDiscs(self):
		stableString = ''

		for x in range(0, 8):
			stableString.join("\n")
			for y in range(0, 8):
				if HarryBotter.stableDiscs[x][y]:
					stableString.join('x')
				else:
					stableString.join('o')

		print stableString

	def printPossibleMoves(self, state):
		print "Possible moves"
		for move in state.getPossibleMoves(self.playerIndex):
			print move.toString()

	def doBestMove(self):
		if self.bestMove == None:
			return

		self.controller.doMove(self.bestMove)

		if HarryBotter.DEBUG_LOG:
			print "Made move " + self.bestMove.toString()

		# doBestMove is called from two different threads, make sure it is
		# only called once per turn or error is thrown
		self.bestMove = None


	# Creates tree starting from root to given depth limit and then
	# recursively use minimax with alpha-beta pruning to score the nodes
	def alphaBetaFromRoot(self, node, currentIterationDepth, depthLimit, alpha, beta, playerIndex, maximize):
		if currentIterationDepth > depthLimit:
			return self.evaluateNodeScore(node)

		if not node.hasChildren():
			moves = node.state.getPossibleMoves(playerIndex)

			if len(moves) == 0:
				return self.evaluateNodeScore(node)
			else:
				# Shuffling boosts outcome greatly for some reason
				random.shuffle(moves)

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
		if(HarryBotter.currentTurn < HarryBotter.TABLE_TURN):
			return self.greedyEvaluate(node)
		elif(HarryBotter.currentTurn < HarryBotter.STABLE_TURN):
			return self.tableEvaluate(node)
		elif(HarryBotter.currentTurn < HarryBotter.GREEDY_TURN):
			return self.stabilityEvaluate(node)
		else:
			return self.greedyEvaluate(node)

	# Evaluate score based on existing table
	# Sacrifices accuracy for speed
	def tableEvaluate(self, node):
		score = 0
		move = node.getMove()

		for x in range(0, 8):
			for y in range(0, 8):
				mark = node.state.getMarkAt(x, y)

				if mark == -1:
					continue

				if mark == self.playerIndex:
					score += HarryBotter.SCORE_WEIGHTS[move.x][move.y]
				else:
					score -= HarryBotter.SCORE_WEIGHTS[move.x][move.y]

		return score + self.getMobilityScore(node.state, HarryBotter.MOBILITY_WEIGHT_TABLE)

	# Calculate score based on move count
	def getMobilityScore(self, state, weight):
		return (state.getPossibleMoveCount(self.playerIndex) - state.getPossibleMoveCount(1 - self.playerIndex)) * weight
		#return state.getPossibleMoveCount(self.playerIndex) * weight * 0.5

	# Evaluate score based on stable (unflippable) discs
	# Sacrifices speed for baccuracy
	def stabilityEvaluate(self, node):
		score = 0
		move = node.getMove()

		for x in range(0, 8):
			for y in range(0, 8):
				mark = node.state.getMarkAt(x, y)
				# Check for empty square
				if mark == -1:
					continue

				weight = 0

				stability = self.isPositionStable(node.state, x, y)

				if stability:
					weight = HarryBotter.STABILITY_WEIGHT
				else:
					weight = HarryBotter.SCORE_WEIGHTS[x][y]

				if self.playerIndex == mark:
					score += weight
				else:
					score -= weight

		return score + self.getMobilityScore(node.state, HarryBotter.MOBILITY_WEIGHT_STABLE)

	# Only values mark count
	# Good for end game (last ~10 turns)
	def greedyEvaluate(self, node):
		return node.state.getMarkCount(self.playerIndex) - node.state.getMarkCount(1 - self.playerIndex)

	# Returns True if stable
	# Only call this on x,y where a disc exists!
	def isPositionStable(self, state, markx, marky):
		if markx != 0 and marky != 0 and markx != 7 and marky != 7:
			# Stability is only checked for edges to save time
			return False

		if HarryBotter.stableDiscs[markx][marky] == True:
			# Already marked as stable
			return True

		# Mark at origin
		ogMark = state.getMarkAt(markx, marky)

		if markx == 0 or markx == 7:
			for y in range(marky, 8):
				mark = state.getMarkAt(markx, y)
				if mark != ogMark:
					break

				if y == 7:
					# Reached corner, stable
					return True

			for y in range(marky, -1, -1):
				mark = state.getMarkAt(markx, y)
				if mark != ogMark:
					break

				if y == 0:
					# Reached corner, stable
					return True
		else:
			for x in range(markx, 8):
				mark = state.getMarkAt(x, marky)
				if mark != ogMark:
					break

				if x == 7:
					# Reached corner, stable
					return True

			for x in range(markx, -1, -1):
				mark = state.getMarkAt(x, marky)
				if mark != ogMark:
					break

				if x == 0:
					# Reached corner, stable
					return True
		return False