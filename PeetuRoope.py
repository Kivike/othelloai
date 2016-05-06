from reversi.Node import Node
from reversi.Move import Move
from reversi.GameState import GameState
from reversi.VisualizeGraph import VisualizeGraph
from reversi.VisualizeGameTable import VisualizeGameTable
from reversi.ReversiAlgorithm import ReversiAlgorithm
import time, sys
import threading

class PeetuRoope(ReversiAlgorithm):
	# Visualization not implemented because it spams
	visualizeFlag = False

	# This is the move that is updated while algorithm searches deeper
	# bestMove is given when time runs out
	bestMove = None
	
	# Flag to check when algorithms needs to stop
	running = False

	# The game state when algorithm starts
	initialState = None

	# 0 or 1
	playerIndex = -1

	START_DEPTH = 2
	# How deep will algorithm go? Time is usually more limiting
	MAX_DEPTH = 10

	currentDepth = 0

	# Timer to see how long the game takes
	wholeGameTimer = None

	# Used to debug how far we got to search
	depthsSearched = []

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

		if PeetuRoope.wholeGameTimer == None:
			PeetuRoope.wholeGameTimer = GameTimer(0).start()

	@property
	def name(self):
		return "PeetuRoope"

	def cleanup(self):
		print "The game took " + str(PeetuRoope.wholeGameTimer.getTimePassed()) + " seconds"

		for i in range(0, len(self.depthsSearched)):
			print str(i) + " " + str(self.depthsSearched[i])

	def run(self):
		print "Starting algorithm PeetuRoope, own playerIndex: " + str(self.playerIndex)
		self.currentDepth = 1

		# Run was called too soon sometimes
		while self.initialState == None:
			time.sleep(30)

		self.running = True
		self.bestMove = None

		#printPossibleMoves(self.initialState)

		timer = GameTimer(self.turnLength).start()

		print "Current score: " + str(self.initialState.getMarkCount(self.playerIndex)) + "-" + str(self.initialState.getMarkCount(1 - self.playerIndex));

		lastSearchTime = 0

		# No possible moves, must skip turn
		if len(self.initialState.getPossibleMoves(self.playerIndex)) == 0:
			self.running = False
			self.controller.doMove(None)

		while self.running:
			sys.stdout.write("Searching to depth " + str(self.currentDepth))

			# Time how long each depth takes
			searchTimer = GameTimer(self.turnLength).start()

			rootNode = Node(self.initialState, None)

			self.recursiveCreateTree(rootNode, self.START_DEPTH, self.currentDepth, self.playerIndex)

			# If playerIndex is 0, maximize on odd depths
			# If playerIndex is 1, maximize on even depths
			maximize = self.playerIndex != self.currentDepth % 2

			self.scoreLeafNodes(rootNode, maximize)

			#rootNode.printtree()

			optimalChild = rootNode.getOptimalChild()

			if not self.running:
				break

			if optimalChild == None:
				print "optimal child is none"
				rootNode.printtree
				self.printPossibleMoves(self.initialState)
				# Something went wrong when creating the tree...
			else:
				rootNode = optimalChild
				self.bestMove = optimalChild.getMove()

			# Gradually increase search depth
			self.currentDepth += 1

			lastSearchTime = '%.4f' % searchTimer.getTimePassed()

			print " duration: " + str(lastSearchTime) + " seconds"

			if self.currentDepth > self.MAX_DEPTH:
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

		self.depthsSearched.append(self.currentDepth)

	# Create tree recursively
	#
	# Node parameter should be rootNode. The tree is created by adding all possible moves as child
	def recursiveCreateTree(self, node, currentDepth, depthLimit, playerIndex):
		if currentDepth >= depthLimit:
			return
		
		currentDepth += 1
	
		moves = node.state.getPossibleMoves(playerIndex);

		for move in moves:
			newstate = node.state.getNewInstance(move.x, move.y, move.player)
			child = Node(newstate, move)
			node.addChild(child)
			self.recursiveCreateTree(child, currentDepth, depthLimit, 1 - playerIndex)

	# Go to last nodes (leaf nodes) and call minmax to send score upwards the tree
	def scoreLeafNodes(self, node, maximize):
		if node.children:
			for child in node.children:
				self.scoreLeafNodes(child, maximize)
		else:
			node.score = node.state.getMarkCount(self.playerIndex);

			move = node.getMove()

			# Give corner moves extra points
			if move.x == 0:
				if move.y == 0 or move.y == 7:
					node.score += 3
				else:
					node.score += 1
			elif move.x == 7:
				if move.y == 0 or move.y == 7:
					node.score += 3
				else:
					node.score += 1

			self.minMaxToRoot(node.parent, maximize);

	# Recursive minmax
	# Node parameter should be parent of leaf node
	def minMaxToRoot(self, node, maximize):
		if node == None:
			return

		# If this node wouldn't be chosen anyway, discard it
		discardNode = False

		for child in node.children:
			if node.score == 0:
				node.score = child.score
			elif maximize:
				if child.score > node.score:
					node.score = child.score

					if node.parent != None and node.parent.score > child.score:			
						# Parent minimizes, it will not choose this node anyway
						# so might as well stop here
						discardNode = True
						break
			else:
				if child.score < node.score:
					node.score = child.score

					if node.parent != None and node.parent.score < child.score:
						# Parent maximizes, it will not choose this node anyway
						# so might as well stop here
						discardNode = True
						break

		if node.parent != None and not discardNode:
			# Continue until we reach root node
			self.minMaxToRoot(node.parent, not maximize)


# Own timer class since the game doesn't accept moves made after the signal
class GameTimer:
	turnLength = 0
	startTime = 0

	def __init__(self, turnLength):
		self.turnLength = turnLength

	def start(self):
		self.startTime = time.time()
		return self

	def isTimeLeft(self, howMuchTimeLeft):
		return self.turnLength - (time.time() - self.startTime) > howMuchTimeLeft

	def getTimePassed(self):
		return time.time() - self.startTime