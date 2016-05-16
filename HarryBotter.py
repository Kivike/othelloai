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
	# Evaluation order: Table - Stable - Greedy

	####################################################################
	# FOLLOWING VALUES AFFECT HOW WELL THE BOT PLAYS				   #
	####################################################################
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
	STABILITY_WEIGHT = 120
	#####################################################################
	# Show log messages
	DEBUG_LOG = True

	mobilityWeight = 0

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

	START_DEPTH = 0
	# How deep will algorithm go? Time is usually more limiting unless
	# moves are limited
	MAX_DEPTH = 20

	# Depth is iteratively increased
	currentIterationDepth = 0

	stableDiscs = []

	evalFunc = None

	rootNode = None

	def __init__(self):
		threading.Thread.__init__(self);

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

			for i in range(8):
				HarryBotter.stableDiscs.append([False for k in range(8)])
		else:
			HarryBotter.currentTurn += 2

		self.determineEvalFunc(HarryBotter.currentTurn, turnLength)

	@property
	def name(self):
		return "HarryBotter"

	# Called when game ends
	def cleanup(self):
		pass

	# Select evaluation strategy based on turn
	def determineEvalFunc(self, turn, turnLength):
		if(turn < 12):
			self.evalFunc = self.tableEvaluate
			HarryBotter.mobilityWeight = 15
		elif(turn < 20):
			self.evalFunc = self.tableEvaluate
			HarryBotter.mobilityWeight = 45
		elif(turn < 30):
			self.evalFunc = self.stabilityEvaluate
			HarryBotter.mobilityWeight = 60
		elif(turn < 40):
			self.evalFunc = self.stabilityEvaluate
			HarryBotter.mobilityWeight = 30
		elif(turn < 52 - (self.turnLength * 0.5)):
			self.evalFunc = self.stabilityEvaluate
			HarryBotter.mobilityWeight = 15
		else:
			self.evalFunc = self.greedyEvaluate
			HarryBotter.mobilityWeight = 1

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

		self.rootNode = Node(self.initialState, None)

		while self.running:
			# Time how long each depth takes
			iterationStart = time.time();
			
			self.alphaBetaFromRoot(self.rootNode, 0, self.currentIterationDepth, -sys.maxint, sys.maxint, self.playerIndex, True)

			optimalChild = self.rootNode.getOptimalChild()

			if not self.running:
				break

			if optimalChild == None:
				print "optimal child is None"
				self.rootNode.printtree()
				self.printPossibleMoves(self.initialState)
				# Something went wrong when creating the tree...
			else:
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
		for x in range(8):
			for y in range(8):
				if x % 7 != 0 and y % 7 != 0:
					continue

				if self.initialState.getMarkAt(x, y) == -1:
					continue

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
			print "Made move %s (%d)" % (self.bestMove.toString(), 
				HarryBotter.SCORE_WEIGHTS[self.bestMove.x][self.bestMove.y])

		# doBestMove is called from two different threads, make sure it is
		# only called once per turn or error is thrown
		self.bestMove = None

	# Creates tree starting from root to given depth limit and then
	# recursively use minimax with alpha-beta pruning to score the nodes
	def alphaBetaFromRoot(self, node, currentIterationDepth, depthLimit, alpha, beta, playerIndex, maximize):
		if currentIterationDepth > depthLimit:
			return self.evalFunc(node)

		if not node.hasChildren():
			moves = node.state.getPossibleMoves(playerIndex)

			if len(moves) == 0:
				return self.evalFunc(node)
			else:
				# Shuffling boosts outcome greatly for some reason
				random.shuffle(moves)
				for move in moves:
					newstate = node.state.getNewInstance(move.x, move.y, move.player)
					node.addChild(Node(newstate, move))
		else:
			if currentIterationDepth < 3:
				# Sort by score order so that we check most scored nodes first
				node.children.sort(key = lambda x: x.score, reverse=True)

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
					#self.alphaBetaCuts += 1
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
					#self.alphaBetaCuts += 1
					break
			return node.score

	# Evaluate score based on existing table
	# Sacrifices accuracy for speed
	def tableEvaluate(self, node):
		score = 0
		ownPotential = 0
		opponentPotential = 0

		for x in range(8):
			for y in range(8):
				mark = node.state.getMarkAt(x, y)

				if mark == -1:
					#continue
					(ownP, oppP) = self.getPotentialMoves(node, x, y)
					ownPotential += ownP
					opponentPotential += oppP
				elif mark == self.playerIndex:
					score += HarryBotter.SCORE_WEIGHTS[x][y]
				else:
					score -= HarryBotter.SCORE_WEIGHTS[x][y]

		if ownPotential + opponentPotential != 0:
			potentialScore = (ownPotential - opponentPotential) / (ownPotential + opponentPotential) * HarryBotter.mobilityWeight
		else:
			potentialScore = 0

		return score + self.getMobilityScore(node) + potentialScore

	# Evaluate score based on stable (unflippable) discs
	# Sacrifices speed for baccuracy
	def stabilityEvaluate(self, node):
		score = 0
		ownPotential = 0
		opponentPotential = 0

		for x in range(8):
			for y in range(8):
				mark = node.state.getMarkAt(x, y)

				if mark == -1:
					(ownP, oppP) = self.getPotentialMoves(node, x, y)
					ownPotential += ownP
					opponentPotential += oppP
				else:
					weight = 0

					if x % 7 == 0 or y % 7 == 0:					
						if self.isPositionStable(node.state, x, y):
							weight = HarryBotter.STABILITY_WEIGHT
						else:
							weight = HarryBotter.SCORE_WEIGHTS[x][y]
					else:
						weight = HarryBotter.SCORE_WEIGHTS[x][y]

					if mark != self.playerIndex:
						score -= weight
					else:
						score += weight

		if ownPotential + opponentPotential != 0:
			potentialScore = (ownPotential - opponentPotential) / (ownPotential + opponentPotential) * HarryBotter.mobilityWeight
		else:
			potentialScore = 0

		return score + self.getMobilityScore(node) + potentialScore

	def getMobilityScore(self, node):
		ownMoves = node.state.getPossibleMoveCount(self.playerIndex)
		opponentMoves = node.state.getPossibleMoveCount(self.opponentIndex)

		if ownMoves == 0:
			return -100
		elif opponentMoves == 0:
			return 100

		return (ownMoves - opponentMoves) / (ownMoves + opponentMoves) * HarryBotter.mobilityWeight

	# Get discs around empty square
	def getPotentialMoves(self, node, ogx, ogy):
		ownMoves = 0
		opponentMoves = 0

		xmin = max(0, ogx - 1)
		xmax = min(8, ogx + 2)
		ymin = max(0, ogy - 1)
		ymax = min(8, ogy + 2)

		for x in range(xmin, xmax):
			for y in range(ymin, ymax):
				if HarryBotter.stableDiscs[x][y]:
					continue

				mark = node.state.getMarkAt(x, y)

				if mark == -1:
					continue

				if mark == self.playerIndex:
					opponentMoves += 1
				else:
					ownMoves += 1

		return (ownMoves, opponentMoves)

	# Only values mark count
	# Good for end game (last ~10 turns)
	def greedyEvaluate(self, node):
		ownMarks = node.state.getMarkCount(self.playerIndex)
		opponentMarks = node.state.getMarkCount(self.opponentIndex)

		return (ownMarks - opponentMarks) / (ownMarks + opponentMarks) * 100 + self.getMobilityScore(node)

	# Returns True if stable
	# Only call this on x,y where a disc exists!
	def isPositionStable(self, state, markx, marky):
		if HarryBotter.stableDiscs[markx][marky]:
			# Already marked as stable
			return True

		# Mark at origin
		ogMark = state.getMarkAt(markx, marky)

		if markx % 7 == 0:
			if state.getMarkAt(markx, 7) == ogMark:
				for y in range(marky, 7):
					if state.getMarkAt(markx, y) != ogMark:
						break
				return True
			if state.getMarkAt(markx, 0) == ogMark:
				for y in range(marky, 0, -1):
					if state.getMarkAt(markx, y) != ogMark:
						break
				return True
		else:
			if state.getMarkAt(7, marky) == ogMark:
				for x in range(markx, 7):
					if state.getMarkAt(x, marky) != ogMark:
						break
				return True

			if state.getMarkAt(0, marky) == ogMark:
				for x in range(markx, 0, -1):
					if state.getMarkAt(x, marky) != ogMark:
						break
				return True
		return False





