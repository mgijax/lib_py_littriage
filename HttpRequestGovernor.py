# Purpose: provides a class for managing the frequency with which we can make HTTP requests,
#    to ensure a configurable amount of "niceness" when reading from other sites
# Notes:
#    1. The initial version of this library is intended to meet the needs for working with
#    the PLOS API, which has limits on the number of requests per minute, hour, and day.  It
#    should, however, be directly applicable for other sites as well.
#    2. This library is only intended to manage the request frequency within a single Python
#    process.  If you use this library in multiple processes, they are wholly unaware of each
#    other's traffic.
# Usage: Instantiate an HttpRequestGovernor object, overriding any default parameters desired,
#    then use the get() method to pass along the URL for the next request.  The governor keeps
#    track of the various timings and will sleep until it's okay to issue another request.
#    You can also ask the governor to report on its statistics so far.

import time
import urllib.request, urllib.error, urllib.parse
import runCommand

# constants for convenience
SECONDS_PER_MINUTE = 60.0
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR

# default settings are conservative, not maxing out what PLOS allows
DEFAULT_PER_REQUEST = 6     # min seconds between requests
DEFAULT_PER_MINUTE = 8      # max requests per minute
DEFAULT_PER_HOUR = 280      # max requests per hour
DEFAULT_PER_DAY = 6700      # max requests per day

def readURL (url):
    # Purpose: given constraints on reading from https connections in python 2.7, we're just going
    #    to shell out and use curl for this
    # Returns: str.returned
    # Throws: Exception if we have problems reading from 'url'

    stdout, stderr, statusCode = runCommand.runCommand("curl '%s'" % url)
    if statusCode != 0:
        raise Exception('Failed to read from url (code %s)' % statusCode)
    return stdout


class HttpRequestGovernor:
    def __init__ (self, secPerRequest = DEFAULT_PER_REQUEST,   # min seconds since last request
            requestsPerMinute = DEFAULT_PER_REQUEST,           # max requests per minute
            requestsPerHour = DEFAULT_PER_HOUR,                # max requests per hour
            requestsPerDay = DEFAULT_PER_DAY                   # max requests per day
            ):
        # Purpose: constructor
        # Notes: If you don't need a limit for any of the parameters, set it to be 0.  The
        #    governor will only consider non-zero limits.
        
        self.secondsPerRequest = secPerRequest
        self.requestsPerMinute = requestsPerMinute
        self.requestsPerHour = requestsPerHour
        self.requestsPerDay = requestsPerDay

        self.lastRequestTime = None             # time (in seconds) at which last request was made
        self.requestsThisMinute = []            # times (in seconds) of requests in the last minute
        self.requestsThisHour = []              # times (in seconds) of requests in the last hour
        self.requestsThisDay = []               # times (in seconds) of requests in the last day
        self.timesWaited = []                   # list of times slept (in seconds)
        self.requestCount = 0                   # number of requests so far
        return
    
    def _trimBefore (self, timeList, startTime):
        # Purpose: (private) remove any items from timeList that occurred before 'startTime'
        # Returns: sublist of 'timeList' that contains items no older than 'startTime', ordered
        #    from oldest to newest
        # Assumes: 'timeList' is ordered from oldest to newest
        
        listLength = len(timeList)
        i = 0
        while (i < listLength) and (timeList[i] < startTime):
            i = i + 1
        return timeList[i:]

    def getWaitTime (self):
        # Purpose: get the amount of time that we need to wait before making the next request
        # Returns: float number of milliseconds
        # Throws: nothing
        # Notes: This method is needed internally, but is also made available externally in
        #    case you'd like the information for some reason.  You don't need to do anything
        #    with it, unless you'd like your script to do something in the meantime, rather
        #    than just going to sleep with a call to get().
        
        waitTime = 0.0
        now = time.time()
        
        if self.lastRequestTime:
            if self.secondsPerRequest > 0.0:
                if (now - self.lastRequestTime) < self.secondsPerRequest:
                    waitTime = self.secondsPerRequest - (now - self.lastRequestTime)
            
            if self.requestsPerMinute:
                minuteAgo = now - SECONDS_PER_MINUTE
                self.requestsThisMinute = self._trimBefore(self.requestsThisMinute, minuteAgo)

                if len(self.requestsThisMinute) > self.requestsPerMinute:
                    waitTime = max(waitTime, (self.requestsThisMinute[0] + SECONDS_PER_MINUTE) - now)

            if self.requestsPerHour:
                hourAgo = now - SECONDS_PER_HOUR
                self.requestsThisHour = self._trimBefore(self.requestsThisHour, hourAgo)

                if len(self.requestsThisHour) > self.requestsPerHour:
                    waitTime = max(waitTime, (self.requestsThisHour[0] + SECONDS_PER_HOUR) - now)

            if self.requestsPerDay:
                dayAgo = now - SECONDS_PER_DAY
                self.requestsThisDay = self._trimBefore(self.requestsThisDay, dayAgo)

                if len(self.requestsThisDay) > self.requestsPerDay:
                    waitTime = max(waitTime, (self.requestsThisDay[0] + SECONDS_PER_DAY) - now)

        self.lastRequestTime = now + waitTime
        self.requestsThisMinute.append(self.lastRequestTime)
        self.requestsThisHour.append(self.lastRequestTime)
        self.requestsThisDay.append(self.lastRequestTime)

        return waitTime
    
    def get (self, url):
        # Purpose: wait until we can make a request of the given URL (within our throttling constraints)
        #   then return the results.
        # Returns: response string
        # Throws: Exception if there are problems reading from url
        
        waitTime = self.getWaitTime()
        if (waitTime > 0):
            time.sleep(waitTime)
            
        self.timesWaited.append(waitTime)
        self.requestCount = self.requestCount + 1
        
        try:
            response = readURL(url)
        except Exception as e:
            raise Exception('The server could not fulfill the request: %s' % str(e))
        return response
    
    def getStatistics (self):
        # Purpose: get a list of statitical data about governor performance so far
        
        if self.requestCount == 0:
            return [ 'No requests yet' ]

        stats = [
            'Number of requests: %d' % self.requestCount,
            'Average wait time:  %6.3f sec' % (sum(self.timesWaited) / self.requestCount),
            'Maximum wait time:  %6.3f sec' % max(self.timesWaited),
            ]
        return stats
