import itertools as it
import numpy as np
import random
import scipy.misc

class ReplicationScheme(object):
   def __init__(self, debug=False, simulation=False, trials=100,
                replicationFactor=3):
      self.debug = debug
      self.simulation = simulation
      self.trials = trials
      self.replicationFactor = replicationFactor

   def probabilityOfDataLoss(self, numNodes):
      if self.simulation:
         results = np.array([self.probabilityOfDataLossSimulation(numNodes)
                             for _ in range(self.trials)])
         if self.debug:
            print 'Average for %d in %s: %f' % (numNodes, self.__class__,
                                                results.mean())
         return results.mean()
      else:
         return self.probabilityOfDataLossComputation(numNodes)

   def probabilityOfDataLossSimulation(self, numNodes):
      raise NotImplementedError

   def probabilityOfDataLossComputation(self, numNodes):
      raise NotImplementedError

   def plotInfo(self):
      raise NotImplementedError

   @staticmethod
   def randomReplicationDataLoss(numNodes, chunksPerNode, replicationFactor):
      # compute the probability
      numFailedNodes = 0.01 * numNodes
      failedCombos = scipy.misc.comb(numFailedNodes, replicationFactor)
      totalCombos = scipy.misc.comb(numNodes, replicationFactor)
      probOfLosingChunk = failedCombos / totalCombos
      probOfDataLoss = 1.0 - (1.0 - probOfLosingChunk) ** (numNodes * chunksPerNode)

      return probOfDataLoss

   @staticmethod
   def copysetReplicationDataLoss(numNodes, chunksPerNode, replicationFactor,
                                  scatterWidth):
      # compute the probability
      numFailedNodes = 0.01 * numNodes
      failedCombos = scipy.misc.comb(numFailedNodes, replicationFactor)
      totalCopysets = scipy.misc.comb(numNodes, replicationFactor)
      numCopysets = (((scatterWidth + 1) / (replicationFactor - 1)) * numNodes /
                     replicationFactor)
      probOfDataLoss = 1.0 - (1.0 - numCopysets / totalCopysets) ** failedCombos

      return probOfDataLoss

   @staticmethod
   def simulationDataLoss(numNodes, chunksPerNode, replicationFactor,
                          chunkReplicationFunc):
      # setup other parameters, we only have cluster at 80% load to avoid
      # failed replication due to insufficient space on nodes' buddies
      totalChunks = int(0.8 * chunksPerNode * numNodes / replicationFactor)
      nodes = range(numNodes)

      # replicate chunks across the cluster, generating a copyset for each chunk
      copysets = set([tuple(sorted(chunkReplicationFunc()))
                      for _ in range(totalChunks)])

      # compute 1% of nodes that will fail
      failedNodes = sorted(random.sample(nodes, int(0.01 * numNodes)))

      # determine if failed nodes form a copyset that is replicated to
      lostData = not copysets.isdisjoint(
         it.combinations(failedNodes, replicationFactor))

      if lostData:
         # we lost data, so return data loss probability of 1.0
         return 1.0
      else:
         # we did not lose data, so return data loss probability of 0.0
         return 0.0

   @staticmethod
   def generateRandomReplicationFunc(numNodes, chunksPerNode, replicationFactor,
                                     scatterWidth):
      nodes = set(range(numNodes))
      # node capacities map
      capacities = {nodeId: chunksPerNode for nodeId in nodes}
      # generate buddy groups for each node
      buddies = {nodeId: random.sample(nodes - {nodeId}, scatterWidth)
                 for nodeId in nodes}

      def decrementCapacities(nodes):
         for node in nodes:
            capacities[node] -= 1
            if capacities[node] == 0:
               # remove the node if it is out of room
               del capacities[node]

      def chunkReplicationFunc():
         while True:
            # choose primary replica from nodes with capacity
            primary = random.choice(capacities.keys())

            # choose secondary replicas from the buddy group
            buddiesWithRoom = [buddy for buddy in buddies[primary]
                               if buddy in capacities]
            if len(buddiesWithRoom) < replicationFactor - 1:
               # no eligible buddies for this primary
               continue
            copyset = ([primary] +
                       random.sample(buddiesWithRoom, replicationFactor - 1))

            # decrement the capacities for each replica
            decrementCapacities(copyset)

            return copyset

      def simpleChunkReplicationFunc():
         copyset = random.sample(capacities.keys(), replicationFactor)
         # decrement the capacities for each replica
         decrementCapacities(copyset)
         return copyset

      if scatterWidth < numNodes - 1:
         return chunkReplicationFunc
      else:
         return simpleChunkReplicationFunc

class PlotInfo(object):
   def __init__(self, label, linestyle='-', linewidth=4, marker='o',
                markevery=1000, markersize=8, markeredgewidth=0.0,
                color='blue', clip_on=False):
      self.label = label
      self.linestyle = linestyle
      self.linewidth = linewidth
      self.marker = marker
      self.markevery = markevery
      self.markersize = markersize
      self.markeredgewidth = markeredgewidth
      self.color = color
      self.clip_on = clip_on
