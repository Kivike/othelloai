from reversi.Node import Node
from reversi.Move import Move
from reversi.GameState import GameState
from reversi.VisualizeGraph import VisualizeGraph
from reversi.VisualizeGameTable import VisualizeGameTable
from reversi.ReversiAlgorithm import ReversiAlgorithm
import time, sys
import threading
from reversi.MainWindow import MainWindow

class MyAlgorithm(ReversiAlgorithm):

    # Constants
    DEPTH_LIMIT = 2 # Just an example value.

    # Variables
    initialized = False
    #volatile boolean
    running = False## Note: volatile for synchronization issues.
    controller = None
    initialState = None
    myIndex = 0
    selectedMove = None
    visualizeFlag = True
    movecount = 1


    def __init__(self):
        """
        constructor
        """
        threading.Thread.__init__(self)
        self.myIndex = 0

    def requestMove(self, requester):
        self.running = False
        requester.doMove(self.selectedMove)

    def init(self,  game, state, playerIndex, turnLength):
         self.initialState = state
         self.myIndex = playerIndex
         self.controller = game
         self.initialized = True


    @property
    def name(self):
        return "MyAlgorithm"

    def cleanup(self):
        return


    def run(self):
         print "starting algo ... "

         #implementation of the actual algorithm
         while not self.initialized:
             time.sleep(1)

         self.initialized = False
         self.running = True
         self.selectedMove = None

         currentDepth = 1

         while self.running and currentDepth < self.DEPTH_LIMIT:
              newMove = self.searchToDepth(currentDepth)

              #Check that there's a new move available
              if newMove != None:
                  self.selectedMove = newMove

              currentDepth += 1

         #if self.running: # Make a move if there is still time left.
         print "move selected is "
         print self.selectedMove
         self.controller.doMove(self.selectedMove)



    def searchToDepth(self, depth):
        """
        1. Create the tree of depth d (breadth first, depth first, beam search, alpha beta pruning, ...)
        2. Evaluate the leaf nodes
        3. If you think normal minimax search is enough, call the propagateScore method of the parent node of each leaf node
        4. Call the getOptimalChild method of the root node
        5. Return the move in the optimal child of the root node
        Don't forget the time constraint! -> Stop the algorithm when variable "running" becomes "false"
        or when you have reached the maximum search depth.
        :param depth: depth of the tree to be created
        :return: optimal move in the tree
        """

        root = Node(self.initialState, None)
        self.createTree(root)

        self.evaluateLeafNodes(root)

        root.printtree()

        optimalMove = root.getOptimalChild().getMove()
        print "optimal move ", optimalMove.toString()

        if self.visualizeFlag:
            vis_graph = VisualizeGraph()
            vis_graph.drawSearchTree(root, MyAlgorithm.movecount)
            MyAlgorithm.movecount = MyAlgorithm.movecount + 1

        return optimalMove

    def createTree(self, root):
        """
        creates tree as per dfs, bfs, etc.
        :param root: root of the tree
        """
        print "creating tree"
        moves = self.initialState.getPossibleMoves(self.myIndex)
        for move in moves:
            print "move ", move.toString()
            newstate = self.initialState.getNewInstance(move.x, move.y, move.player)
            print "newstate " , newstate
            child = Node(newstate, move)
            print "child ", child.toString()
            root.addChild(child)


    def evaluateLeafNodes(self, root):
        """
        propagates the scores in the tree from the lesf nodes to the root
        :param root: root node of the tree
        """
        if not root.children:
            #print root.state.toString()
            score = root.state.getMarkCount(self.myIndex) - root.state.getMarkCount(1 - self.myIndex)
            root.score = score
            print "score ",  root.score
            self.propagateScore(root.parent, True) # True or False depending on the depth, since we have depth 1, it is True
            #root.parent.propagateScore( True)
        else:
            for child in root.children:
                self.evaluateLeafNodes(child)


    def propagateScore(self, node, maximize):
        """
        Propagates the score calculated in a leaf node to the root of the tree.
        The result propagates through the tree according to the minimax principle.
        When the tree has been created and the leaf nodes have been scored,
        the propagateScore() method of all the nodes one level above the leaf nodes
        should be called. For example, for the tree shown below, the propagateScore()
        method of the nodes 1 and 2 should be called after scores have been given
        to all the leaf nodes. After calling the propagateScore() methods, the optimal
        move can be retrieved by calling the getOptimalChild() method of the root node.
        Note: There is no need to call propagateScore() on other tree levels than
        Level d - 1 as the method works recursively through the tree.
        +------+
        | Root |                            Level 0
        +------+
           |
          ...
           |
        +------------------+
            |                  |
        +-------+          +-------+
        |   1   |          |   2   |        Level d - 1
        +-------+          +-------+
            |                  |
            +--------+         +-------+
            |        |         |       |
         +-----+  +-----+   +-----+ +-----+
         | 1.1 |  | 1.2 |   | 2.1 | | 2.2 | Level d
         +-----+  +-----+   +-----+ +-----+

        :param node: node whose children will be inspected
        :param maximize:  If true, the bottommost level is maximization level. If false, the bottommost level is minimization level
        :return:
        """
        for child in node.children:
            node.score = node.children[0].score

        if node.parent != None:
            self.propagateScore(node.parent, not maximize)



if __name__ == '__main__':
    algo = MyAlgorithm()
    state = GameState()
    algo.init(None, state, 0, 1)
    algo.visualizeFlag = True
    algo.run()