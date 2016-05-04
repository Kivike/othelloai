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
	initialState = None
	tree = None
	playerIndex = -1
	moveIndex = 0
	game = None

	MAX_DEPTH = 4

	def __init__(self):
		threading.Thread.__init__(self);
		pass

	def requestMove(self, requester):
		pass

	def init(self, game, state, playerIndex, turnLength):
		self.initialState = state
		self.playerIndex = playerIndex
		self.controller = game
		self.turnLength = turnLength
		self.game = game

	@property
	def name(self):
		return "PeetuRoope"

	def cleanup(self):
		return

	def run(self):
		print "Starting algorithm PeetuRoope, own playerIndex: " + str(self.playerIndex)
		depthLimit = 1;

		# Run was called too soon sometimes
		while self.initialState == None:
			time.sleep(30)

		self.sendMove = False

		print "Possible moves"
		for move in self.initialState.getPossibleMoves(self.playerIndex):
			print move.toString()

		timer = GameTimer(self.turnLength).start()

		print "Current score: " + str(self.initialState.getMarkCount(self.playerIndex)) + "-" + str(self.initialState.getMarkCount(1 - self.playerIndex));

		while timer.isTimeLeft(0.1):
			print "Searching to depth " + str(depthLimit)
			rootNode = Node(self.initialState, None)
			self.recursiveCreateTree(rootNode, 0, depthLimit, self.playerIndex)

			# If playerIndex is 0, maximize on odd depths
			# If playerIndex is 1, maximize on even depths
			maximize = self.playerIndex != depthLimit % 2
			print "Depth " + str(depthLimit) + " max " + str(maximize)

			self.scoreLeafNodes(rootNode, maximize)

			#rootNode.printtree()

			if rootNode.getOptimalChild() == None:
				print "optimal child is none"
				# Something went wrong when creating the tree...
			else:
				self.bestMove = rootNode.getOptimalChild().getMove()

			# Gradually increase search depth
			depthLimit += 1

			if depthLimit > self.MAX_DEPTH:
				break

		print "Making move " + self.bestMove.toString()
		self.controller.doMove(self.bestMove)

	def isTimeLeft():
		return self.turnLength - (time.time() - startTime) > 0.1

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
			self.minMaxToRoot(node.parent, maximize);

	# Recursive minmax
	# Node parameter should be parent of leaf node
	def minMaxToRoot(self, node, maximize):
		for child in node.children:
			if node.score == 0:
				node.score = child.score
			elif child.score > node.score:
				if maximize:
					node.score = child.score
			else:
				if not maximize:
					node.score = child.score

		if node.parent != None:
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