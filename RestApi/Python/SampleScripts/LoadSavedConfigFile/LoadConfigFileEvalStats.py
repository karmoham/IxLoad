# Description
#   A sample Python REST API script to:
#      - Load a saved configuration file
#      - Enable port analyzer
#      - Set runtime stats
#      - Run traffic
#      - Get stats and evaluate for user defined expected stat values.
#      - Retrieve port capture files to local folder.
#      - Get test result
#
#   Supports both Windows and Linux gateway Server. If connecting to a
#
#   If the saved config file is located on a remote pc, this script could upload it to the gateway.
#   Otherwise, the saved config file must be already in the IxLoad API gateway server.
#
# Requirements
#    IxL_RestApi.py
#
# IxL_RestApi.py and sample scripts by: Hubert Gee

import os, sys, time, signal, traceback, platform

# Insert the Modules path to env in order to import IxL_RestApi.py
currentDir = os.path.abspath(os.path.dirname(__file__))

# Automatically create the os path to the IxL_RestApi.py module for this script to use
if platform.system() == 'Windows':
    sys.path.insert(0, (currentDir.replace('SampleScripts\\LoadSavedConfigFile', 'Modules')))
else:
    sys.path.insert(0, (currentDir.replace('SampleScripts/LoadSavedConfigFile', 'Modules')))

from IxL_RestApi import *

# Choices of IxLoad Gateway server OS: linux or windows
serverOs = 'linux'

# Which IxLoad version are you using for your test?
# To view all the installed versions, go on a web browser and enter:
#    http://<server ip>:8080/api/v0/applicationTypes
ixLoadVersion = '9.10.115.43'

# Do you want to delete the session at the end of the test or if the test failed?
deleteSession = True
forceTakePortOwnership = True

# API-Key: Use your user API-Key if you want added security
apiKey = None

# The saved config file to load
rxfFile = 'IxL_Http_910_update1.rxf'

if serverOs == 'windows':
    apiServerIp = '192.168.129.6'

    # Where to store all of the csv result files in Windows
    resultsDir = 'c:\\Results'

    # Where to upload the config file or where to tell IxLoad the location if you're not uploading it.
    rxfFileOnServer = 'C:\\Results\\{}'.format(rxfFile)

if serverOs == 'linux':
    apiServerIp = '192.168.129.24'

    # Leave the 2 lines as default. For your reference only.
    resultsDir = '/mnt/ixload-share/Results'
    rxfFileOnServer = '/mnt/ixload-share/{}'.format(rxfFile)

# Where to put the downloaded csv results
saveResultsInPath = currentDir

# On the local host where you are running this script.
# The path to the saved config file. In this example, get it from the current folder
if platform.system() == 'Linux':
    localConfigFileToUpload = '{}/{}'.format(currentDir, rxfFile)
else:
    localConfigFileToUpload = '{}\\{}'.format(currentDir, rxfFile)

# The path where you want to download the csv result files to.  This is mostly used if using a Linux Gateway server.
# If you're using IxLoad in Windows, SSH must be installed.  Otherwise, this variable will be ignored.
scpDestPath = currentDir

# For IxLoad versions prior to 8.50 that doesn't have the rest api to download results.
# Set to True if you want to save run time stat results to CSV files.
saveStatsToCsvFile = False

apiServerIpPort = 8443 ;# http=8080.  https=8443 (https is supported starting 8.50)

licenseServerIp = '192.168.129.6'

# licenseModel choices: 'Subscription Mode' or 'Perpetual Mode'
licenseModel = 'Subscription Mode'

# To assign ports for testing.  Format = (cardId,portId)
# Traffic1@Network1 are activity names.
# To get the Activity names, got to: /ixload/test/activeTest/communityList
communityPortList1 = {
    'chassisIp': '192.168.129.15',
    'Traffic1@Network1': [(1,1)],
}

communityPortList2 = {
    'chassisIp': '192.168.129.15',
    'Traffic2@Network2': [(1,2)],
}

# Stat names to display at run time.
# To see how to get the stat names, go to the link below for step-by-step guidance:
#     https://www.openixia.com/tutorials?subject=ixLoad/getStatName&page=fromApiBrowserForRestApi.html
#
# What this does:
#    Get run time stats and evaluate the stats with an operator and the expected value.
#    Due to stats going through ramp up and ramp down, stats will fluctuate.
#    Once the stat hits and maintains the expected threshold value, the stat is marked as passed.
#
#    If evaluating stats at run time is not what you need, use PollStats() instead shown
#    in sample script LoadConfigFile.py
#
# operator options:  None, >, <, <=, >=
statsDict = {
    'HTTPClient': [{'caption': 'TCP Connections Established', 'operator': '>', 'expect': 60},
                   {'caption': 'HTTP Simulated Users',        'operator': '>', 'expect': 100},
                   {'caption': 'HTTP Connections',            'operator': '>', 'expect': 300},
                   {'caption': 'HTTP Transactions',           'operator': '>', 'expect': 190},
                   {'caption': 'HTTP Connection Attempts',    'operator': '>', 'expect': 300}
               ],
    'HTTPServer': [{'caption': 'TCP Connections Established',    'operator': '>=', 'expect': 1000},
                   {'caption': 'TCP Connection Requests Failed', 'operator': '<', 'expect': 1}
               ]
}

try:
    restObj = Main(apiServerIp=apiServerIp,
                   apiServerIpPort=apiServerIpPort,
                   osPlatform=serverOs,
                   deleteSession=deleteSession,
                   pollStatusInterval=1,
                   apiKey=apiKey,
                   generateRestLogFile=True)

    # sessionId is an opened existing session that you like to connect to instead of starting a new session.
    restObj.connect(ixLoadVersion, sessionId=None, timeout=120)

    restObj.configLicensePreferences(licenseServerIp=licenseServerIp, licenseModel=licenseModel)

    # The folder to store the results on the IxLoad Gateway server.
    restObj.setResultDir(resultsDir, createTimestampFolder=True)

    # uploadConfigFile: None or path to the config file on your local host
    restObj.loadConfigFile(rxfFileOnServer, uploadConfigFile=localConfigFileToUpload)

    restObj.assignChassisAndPorts([communityPortList1, communityPortList2])
    if forceTakePortOwnership:
        restObj.enableForceOwnership()

    restObj.enableAnalyzerOnAssignedPorts()

    # Optional: Modify the sustain time
    restObj.configTimeline(name='Timeline1', sustainTime=12)

    # Example on how to use the configActivityAttribute function to modify
    # some of its attributes.
    restObj.configActivityAttributes(communityName='Traffic1@Network1',
                                     activityName='HTTPClient1',
                                     attributes={'userObjectiveValue': 100})

    runTestOperationsId = restObj.runTraffic()

    restObj.pollStatsAndCheckStatResults(statsDict,
                                         csvFile=saveStatsToCsvFile,
                                         csvFilePrependName=None,
                                         pollStatInterval=2,
                                         exitAfterPollingIteration=None)


    testResult = restObj.getTestResults()

    restObj.waitForActiveTestToUnconfigure()
    restObj.downloadResults(targetPath=saveResultsInPath)
    restObj.retrievePortCaptureFileForAssignedPorts(currentDir)

    if deleteSession:
        restObj.deleteSessionId()

except (IxLoadRestApiException, Exception) as errMsg:
    print('\n%s' % traceback.format_exc())
    if deleteSession:
        restObj.abortActiveTest()
        restObj.deleteSessionId()

    sys.exit(errMsg)

except KeyboardInterrupt:
    print('\nCTRL-C detected.')
    if deleteSession:
        restObj.abortActiveTest()
        restObj.deleteSessionId()

