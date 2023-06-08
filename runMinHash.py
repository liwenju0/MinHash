from __future__ import division
import os
import re
import random
import time
import binascii
from bisect import bisect_right
from heapq import heappop, heappush
import jieba
import zlib


class MinHash:
  def __init__(self, numHashes=5, docs=None, threshold=0.5) -> None:
    self.numHashes = numHashes
    if not docs:
      docs = []
    self.docs = docs
    self.estJSim = [0 for x in range(self.numElems)]
    self.docsAsShingleSets = self.shingling_docs(self.docs)
    self.maxShingleID = 2**32-1
    self.nextPrime = 4294967311
    self.threshold = threshold
    self.gen_similarities(times=10)


  

  def shingling_docs(self, docs):
    '''docs是一个list，每个元素是一个句子'''
    docsAsShingleSets = {}
    for docName, sent in enumerate(docs):
      words = list(sent)
      shinglesInDoc = set()
      for index in range(0, len(words) - 2):
        shingle = words[index] + " " + words[index + 1] + " " + words[index + 2]
        crc = zlib.crc32(shingle.encode("utf-8")) & 0xffffffff
        shinglesInDoc.add(crc)
      docsAsShingleSets[docName] = shinglesInDoc

    return docsAsShingleSets
  
  @property
  def numDocs(self):
    return len(self.docs)
  
  @property
  def numElems(self):
     return int(self.numDocs * (self.numDocs - 1) / 2)

  def getTriangleIndex(self, i, j):
    assert i != j
    if j < i:
      temp = i
      i = j
      j = temp
    
    # Calculate the index within the triangular array.
    # This fancy indexing scheme is taken from pg. 211 of:
    # http://infolab.stanford.edu/~ullman/mmds/ch6.pdf
    # But I adapted it for a 0-based index.
    # Note: The division by two should not truncate, it
    #       needs to be a float. 
    k = int(i * (self.numDocs - (i + 1) / 2.0) + j - i) - 1 
    return k

  def pickRandomCoeffs(self, k):
    # Create a list of 'k' random values.
    randList = []
    while k > 0:
      # Get a random shingle ID.
      randIndex = random.randint(0, self.maxShingleID) 
    
      # Ensure that each random number is unique.
      while randIndex in randList:
        randIndex = random.randint(0, self.maxShingleID) 
      
      # Add the random number to the list.
      randList.append(randIndex)
      k = k - 1
      
    return randList
  
  def gen_signatures(self):
    signatures = []
    for docName, doc in enumerate(self.docs):
      shingleIDSet = self.docsAsShingleSets[docName]
      signature = []
      for i in range(0, self.numHashes):
        minHashCode = self.nextPrime + 1
        for shingleID in shingleIDSet:
          # Evaluate the hash function.
          hashCode = (self.coeffA[i] * shingleID + self.coeffB[i]) % self.nextPrime 
          if hashCode < minHashCode:
            minHashCode = hashCode
        signature.append(minHashCode)
      signatures.append(signature)
    return signatures
  
  def gen_similarities(self, times=10):
    '''因为minHash在短文本上效果不稳定，所以这里采样计算多次求平均'''
    for ti in range(times):
      self.coeffA = self.pickRandomCoeffs(self.numHashes)
      self.coeffB = self.pickRandomCoeffs(self.numHashes)
      
      self.signatures = self.gen_signatures()
      for i in range(0, self.numDocs):
        signature1 = self.signatures[i]
        for j in range(i + 1, self.numDocs):
          signature2 = self.signatures[j]
          count = 0
          for k in range(0, self.numHashes):
            count = count + (signature1[k] == signature2[k])
          self.estJSim[self.getTriangleIndex(i, j)] += (count / self.numHashes)
    self.estJSim = [simi/times for simi in self.estJSim]
      

  def display(self):
    '''展示相同的文本'''
    for i in range(0, self.numDocs):  
      for j in range(i + 1, self.numDocs):
        estJ = self.estJSim[self.getTriangleIndex(i, j)]
        s1 = self.docsAsShingleSets[i]
        s2 = self.docsAsShingleSets[j]
        J = (len(s1.intersection(s2)) / len(s1.union(s2)))
        print("  %5s --> %5s  Minhash相似度： %.2f  Jacade距离：   %.2f" % (self.docs[i], self.docs[j], estJ, J))



if __name__ == "__main__":
  docs = [

    "我们在这类非常开心",
    "我们在这里非常开心",
    "如果记忆能被定格，你的高中会是怎样的一幅画？高考开始，愿你全力以赴大胜归来！",
    "如果记忆能被定格，你的高中会是怎样的？高考开始，全力以赴大胜归来！"
  ]
  
  hashes = MinHash(docs=docs)
  hashes.display()
          