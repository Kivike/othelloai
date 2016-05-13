from reversi.Node import Node
from reversi.Move import Move
from reversi.GameState import GameState
from reversi.VisualizeGraph import VisualizeGraph
from reversi.VisualizeGameTable import VisualizeGameTable
from reversi.ReversiAlgorithm import ReversiAlgorithm
import time, sys
import threading
import random

import profile

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
	# http://dhconnelly.github.io/paip-python/docs/paip/othello.html
	# Used by table evaluation
	SCORE_WEIGHTS_2 = [
		[ 120, 	-20,  20,  10,  10,   20, -20,  120],
		[-20, 	-40,  -5,  -5,  -5,   -5, -40,  -20],
		[ 20,  	 -5,  15,   3,   3,   15,  -5,   20],
		[ 10,  	 -5,   3,   3,   3,    3,  -5,   10],
		[ 10,  	 -5,   3,   3,   3,    3,  -5,   10],
		[ 20,  	 -5,  15,   3,   3,   15,  -5,   20],
		[-20, 	-40,  -5,  -5,  -5,   -5, -40,  -20],
		[ 120, 	-20,  20,  10,  10,   20, -20,   120]
	]

	SCORE_WEIGHTS = [
		[ 100, -1,  5,  2,  2,   5, -1,  100],
		[-1,  -10,  1,  1,  1,   1, -10,  -1],
		[ 5,    1,  1,  1,  1,   1,  1,    5],
		[ 2,    1,  1,  0,  0,   1,  1,    2],
		[ 2,    1,  1,  0,  0,   1,  1,    2],
		[ 5,    1,  1,  1,  1,   1,  1,    5],
		[-1,  -10,  1,  1,  1,   1, -10,  -1],
		[ 100, -1,  5,  2,  2,   5, -1,  100]
	]

	# Used by stable evaluation
	STABILITY_WEIGHT = 120

	# 5 15 - H0 	C01
	# 5 20 - H01	C01

	MOBILITY_WEIGHT = 50

	# Weight when using table evaluation
	MOBILITY_WEIGHT_TABLE = 30

	# Weight when checking stable discs
	MOBILITY_WEIGHT_STABLE = 30
	#####################################################################

	# Log messages for debugging
	DEBUG_LOG = True

	# This is the move that is updated while algorithm searches deeper
	# bestMove is given when time runs out
	bestMove = None
	
	# Flag to check when algorithms needs to stop
	running = False

	# The game state when algorithm starts
	initialState = None

	# 0 if we start, 1 if opponent starts
	playerIndex = -1
	opponentIndex = -1

	currentTurn = -1

	instance = None

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

	BITMAP = [1 << n for n in range(64)]

	evalFunc = None

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
		self.opponentIndex = 1 - playerIndex
		self.controller = game
		self.turnLength = turnLength

		# Check if running algo first time
		if HarryBotter.currentTurn == -1:
			HarryBotter.currentTurn = playerIndex

			self.createBitmap()
		else:
			HarryBotter.currentTurn += 2

		self.determineEvalFunc(HarryBotter.currentTurn, turnLength)

	def createBitmap(self):
		return
		BITMAP = [1 << n for n in range(64)]

	def getBitBoard(self, state):
		W = 0
		B = 0

		for x in range(8):
			for y in range(8):
				mark = state.getMarkAt(x, y)

				# Check for empty square
				if mark == -1:
					continue
				elif mark == 0:
					W |= HarryBotter.BITMAP[x * 8 + y]
				else:
					B |= HarryBotter.BITMAP[x * 8 + y]
		return (W, B)

	@property
	def name(self):
		return "HarryBotter"

	# Called when game ends
	def cleanup(self):
		pass

	def determineEvalFunc(self, turn, turnLength):
		if(turn < 7):
			self.evalFunc = self.greedyEvaluate
		elif(turn < 16):
			self.evalFunc = self.tableEvaluate
		elif(turn < 25):
			self.evalFunc = self.tableEvaluateMobility
		elif(turn < 50):
			self.evalFunc = self.stabilityEvaluate
		else:
			self.evalFunc = self.greedyEvaluate

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

			print "Moves: %d" % (self.initialState.getPossibleMoveCount(self.playerIndex))

		possibleMoveCount = self.initialState.getPossibleMoveCount(self.playerIndex)

		if possibleMoveCount == 0:
			# No possible moves, must skip turn
			self.running = False
			self.controller.doMove(None)
		elif possibleMoveCount == 1:
			# Only one possible move to make
			self.running = False
			self.controller.doMove(self.initialState.getPossibleMoves(self.playerIndex)[0])

		if self.evalFunc == self.stabilityEvaluate:
		#if HarryBotter.currentTurn > HarryBotter.STABLE_TURN and HarryBotter.currentTurn < HarryBotter.GREEDY_TURN:
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
		(W, B) = self.getBitBoard(self.initialState)

		for x in range(8):
			for y in range(8):
				if x % 7 != 0 and y % 7 != 0:
					continue

				if self.initialState.getMarkAt(x, y) == -1:
					continue

				if self.isPositionStableBit(self.initialState, W, B, x, y):
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
			return self.evalFunc(node)

		moves = node.state.getPossibleMoves(playerIndex)

		if len(moves) == 0:
			return self.evalFunc(node)
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
					score += HarryBotter.SCORE_WEIGHTS_2[move.x][move.y]
				else:
					score -= HarryBotter.SCORE_WEIGHTS_2[move.x][move.y]

		if move.player == self.playerIndex:
			score -= node.state.getPossibleMoveCount(self.opponentIndex) * HarryBotter.MOBILITY_WEIGHT_TABLE
		else:
			score -= node.parent.state.getPossibleMoveCount(self.opponentIndex) * HarryBotter.MOBILITY_WEIGHT_TABLE

 		return score

 	def tableEvaluateMobility(self, node):
 		score = 0
		move = node.getMove()

		for x in range(0, 8):
			for y in range(0, 8):
				mark = node.state.getMarkAt(x, y)

				if mark == -1:
					continue

				if mark == self.playerIndex:
					score += HarryBotter.SCORE_WEIGHTS_2[move.x][move.y]
				else:
					score -= HarryBotter.SCORE_WEIGHTS_2[move.x][move.y]

		if move.player == self.playerIndex:
			score -= node.state.getPossibleMoveCount(self.opponentIndex) * HarryBotter.MOBILITY_WEIGHT
		else:
			score -= node.parent.state.getPossibleMoveCount(self.opponentIndex) * HarryBotter.MOBILITY_WEIGHT

		return score

	# Evaluate score based on stable (unflippable) discs
	# Sacrifices speed for baccuracy
	def stabilityEvaluate(self, node):
		score = 0
		move = node.getMove()

		(W, B) = self.getBitBoard(node.state)

		for x in range(0, 8):
			for y in range(0, 8):
				weight = 0

				stability = False

				if x % 7 != 0 and y % 7 != 0:
					stability = self.isPositionStableBit(node.state, W, B, x, y)

				if stability:
					weight = HarryBotter.STABILITY_WEIGHT
				else:
					weight = HarryBotter.SCORE_WEIGHTS_2[x][y]

				if W & HarryBotter.BITMAP[x* 8 + y]:
					score += weight
				else:
					score -= weight

		if move.player == self.playerIndex:
			score += node.state.getPossibleMoveCount(self.playerIndex) * HarryBotter.MOBILITY_WEIGHT_STABLE
		else:
			score += node.parent.state.getPossibleMoveCount(self.playerIndex) * HarryBotter.MOBILITY_WEIGHT_STABLE

		return score

	# Only values mark count
	# Good for end game (last ~10 turns)
	def greedyEvaluate(self, node):
		return node.state.getMarkCount(self.playerIndex) - node.state.getMarkCount(self.opponentIndex)

	# Returns True if stable
	# Only call this on x,y where a disc exists!
	def isPositionStable(self, state, markx, marky):
		#if markx % 7 != 0 and marky % 7 != 0:
			# Stability is only checked for edges to save time
		#	return False

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

	def isPositionStableBit(self, state, W, B, markx, marky):
		if markx % 7 != 0 and marky % 7 != 0:
			# Stability is only checked for edges to save time
			return False

		if HarryBotter.stableDiscs[markx][marky] == True:
			# Already marked as stable
			return True

		ogMark = state.getMarkAt(markx, marky)

		if markx % 7 == 0:
			row = 0

			for y in range(marky, 8):
				row |= 1 << y

			if ogMark == 0:
				if W ^ row == 0:
					return True
			else:
				if B ^ row == 0:
					return True

			rowInvert = ~row

			if ogMark == 0:
				if W ^ rowInvert == 0:
					return True
			else:
				if B ^ rowInvert == 0:
					return True
		else:
			row = 0

			for x in range(markx, 8):
				row |= 1 << x

			if ogMark == 0:
				if W ^ row == 0:
					return True
			else:
				if B ^ row == 0:
					return True

			rowInvert = ~row

			if ogMark == 0:
				if W ^ rowInvert == 0:
					return True
			else:
				if B ^ rowInvert == 0:
					return True

		return False





