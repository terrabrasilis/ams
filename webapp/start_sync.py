import os
import sys
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
from sync import startSync

"""
Using to start the synchronization process from an external scheduler.
By default, use cron. It only needs once a day.
"""
startSync()