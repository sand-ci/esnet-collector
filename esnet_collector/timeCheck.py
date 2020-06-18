from datetime import datetime, timedelta
import sys, os

class TimeCheck(object):
    """Read and write a checkpoint file
    If class is instantiated without a filename, class works as expected but
    data is not stored to disk
    """

    _startTime = None
    _endTime   = None
    _fp = None

    def __init__(self, target=None):
        """
        Create a checkpoint file
        target - checkpoint filename (optionally null)
        """
        if target:
            try:
               fd = os.open(target, os.O_RDWR | os.O_CREAT)
               self._fp = os.fdopen(fd, 'r+')
               lines = self._fp.readlines()
               self._startTime = lines[0]
               self._endTime   = lines[1]
               print( "Resuming from start and end checkpoints in %s" % target)
            except IOError:
                raise IOError("Could not open checkpoint file %s" % target)
            except ValueError:
                print( "Failed to read checkpoint file %s" % target)
            except IndexError:
               print('no data')

    def get_startTime(self):
        return self._startTime
    def get_endTime(self):
        return self._endTime
    def set_startTime(self, startTime):
        self._startTime = int(startTime)
    
    startTime = property(get_startTime, set_startTime)              

    def set_endTime(self, endTime): 
        self._endTime = int(endTime)
        if(self._fp):
           self._fp.seek(0)
           self._fp.write(str(self._startTime) + "\n" + str(self._endTime))
           self._fp.truncate()

    endTime = property(get_endTime, set_endTime)           
