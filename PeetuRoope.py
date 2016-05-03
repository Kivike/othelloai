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

	MAX_DEPTH = 3

	def __init__(self):
		threading.Thread.__init__(self);
		pass

	def requestMove(self, requester):
		pass

	def init(self, game, state, playerIndex, turnLength):
		print "INITING"
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
		print "Starting algorithm PeetuRoope"
		depthLimit = 1;

		rootNode = Node(self.initialState, None)

		self.sendMove = False

		moves = self.initialState.getPossibleMoves(self.playerIndex)

		print "Possible moves"
		for move in moves:
			print move.toString()

		startTime = time.time()

		while self.turnLength - (time.time() - startTime) > 0.1:
			print "Searching to depth " + str(depthLimit)
			rootNode = Node(self.initialState, None)
			self.createTree(rootNode, depthLimit)
			self.scoreLeafNodes(rootNode)


			print str(len(rootNode.children)) + " " + str(len(rootNode.state.getPossibleMoves(self.playerIndex)))
			if rootNode.getOptimalChild() == None:
				print "optimal child is none"

				rootNode.printtree()
				time.sleep(5)
				#for move in rootNode.children:
				#	print "Score " + str(move.score)
			else:
				self.bestMove = rootNode.getOptimalChild().getMove()

			# Gradually increase search depth
			depthLimit += 1 

			if depthLimit > self.MAX_DEPTH:
				break

		print "Making move " + self.bestMove.toString()
		self.controller.doMove(self.bestMove)

	def createTree(self, rootNode, depth):
		moves = rootNode.state.getPossibleMoves(self.playerIndex)
		#moves = self.state.getPossibleMoves(self.playerIndex)
		#state = self.state

		for move in moves:
			possiblestate = rootNode.state.getNewInstance(move.x, move.y, move.player)
			moveNode = Node(possiblestate, move)
			rootNode.addChild(moveNode)

			self.recursiveTree(moveNode, 0, depth, self.playerIndex);
		#self.recursiveTree(Node(state, moves[0]), state, 0, 2, self.playerIndex)


	def recursiveTree(self, node, currentDepth, depthLimit, playerIndex):
		if currentDepth >= depthLimit:
			return

		currentDepth += 1

		moves = node.state.getPossibleMoves(playerIndex);

		for move in moves:
			newstate = node.state.getNewInstance(move.x, move.y, move.player)
			child = Node(newstate, move)
			node.addChild(child)
			self.recursiveTree(child, currentDepth, depthLimit, 1 - playerIndex)

	def scoreLeafNodes(self, node):
		if node.children:
			for child in node.children:
				self.scoreLeafNodes(child)
		else:
			node.score = node.state.getMarkCount(self.playerIndex);
			self.minMaxToRoot(node.parent, self.playerIndex % 2 == 1);

	def minMaxToRoot(self, node, maximize):
		for child in node.children:
			if child.score > node.score:
				if maximize:
					node.score = child.score
			else:
				if not maximize:
					node.score = child.score

		if node.parent != None:
			self.minMaxToRoot(node.parent, not maximize)




		