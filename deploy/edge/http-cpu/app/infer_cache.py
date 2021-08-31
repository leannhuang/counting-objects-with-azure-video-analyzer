# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from datetime import datetime, timezone
import os
import collections

CACHE_SIZE = os.environ.get('CACHE_SIZE', 200)
THRESHHOLD = os.environ.get('THRESHHOLD', 5)

class InferCache:
  def __init__(self, size, threshold):
    self.cache = collections.defaultdict(list)
    self.size = size
    self.threshold = threshold

  def append(self, ts, infer):
    self.cache[ts].append(infer)
    if len(self.cache) > self.size:
      # remove oldest data
      del self.cache[min(self.cache.keys())]

  def get(self, now):
    # pick the data closest to current time
    ts_now = datetime.timestamp(now) * (10 ** 9)
    closest = -1
    if self.cache:
      closest = min(self.cache.keys(), key=lambda ts_cache: abs(ts_now - ts_cache))
    if abs(ts_now - closest) > self.threshold * (10 ** 9):
      print("===============No bounding box shown======================")
      print(f'the most closet time with bbox in threshold: {datetime.utcfromtimestamp(closest // (10 ** 9))}') 
      closest = -1
      print('==========================================================')

    return self.cache[closest], closest

infer_cache = InferCache(CACHE_SIZE, THRESHHOLD)
