#!/usr/bin/python

####################################################################################################################
# File name: autoVote.py                                                                                           #
# Author: cc001                                                                                                    #
# Last modified: 2016-05-03                                                                                        #
#                                                                                                                  #
# This is a script to vote automatically for Lisk delegates.                                                       #
# The accounts you want to vote for must be added to text files, defined in the file config.yml.                   #
# Put every delegatename, accountnumber, or publickey on its own line                                              #
# You can vote positive or negative ("un-vote") in one step, just add the accounts to the appropriate file.        #
#                                                                                                                  #
# Installation: make sure to have installed the imported modules time, httplib, socket, json, requests, os, yaml   #
# Example: For the in Ubuntu this is done with 'sudo apt-get install python-httplib2 python-requests python-yaml'  #
# You have to modify the file config.yaml to adapt it for your needs. See the instructions in config.yml           #
#                                                                                                                  #
# Usage: make sure this script is executable with 'chmod +x autoVote.py'                                           #
# Start the script with no parameters: './autoVote.py' to use the default config                                   #
# Or add the desired config section: './autoVote.py cc001'                                                         #
#                                                                                                                  #
# If you like this script, please vote for me as Delegate on test- and mainnet, Thanks!                            #
####################################################################################################################

import time
import httplib
import socket
import json, requests
import os
import sys
import yaml

numberOfVotesPerTransaction = 33;

def getMyVotes():
    myVotes = []
    query = config['node'] + "/api/accounts/delegates/?address=" + config['myAddress']
    answer = getAnswer(query)
    delegates = answer['delegates']
    for delegate in delegates:
        myVotes.append(delegate['publicKey'])
    return myVotes

def getVotingPublicKeysFromFile(positive):
    if positive:
        votingFileName = config['positiveVotingFilename']
        prefix = '+'
    else:
        votingFileName = config['negativeVotingFilename']
        prefix = '-'
    with open(votingFileName) as filename:
        votes = filename.read().splitlines()
    votes = filter(None, votes) # remove empty lines/entries
    
    return getPublicKeys(votes)
    

def getPublicKeys(votes):
    publicKeys = []
    notFoundVotes = []
    if votes:
        template = "{0:22}|{1:22}|{2:22}|{3:35}"
        print "\nFound:"
        print template.format("Vote", "Username", "Adress", "PublicKey") # header
        print "-------------------------------------------------------------------------------------------------------------------------------------"
      
        for vote in votes:
            found = False
            for delegate in allDelegates:
                if delegate['username'] == vote or delegate['address'] == vote or delegate['publicKey'] == vote:
                    print template.format(vote, delegate['username'], delegate['address'], delegate['publicKey'])
                    publicKeys.append(delegate['publicKey'])
                    found = True
                    break
            if not found:
                notFoundVotes.append(vote)
        
        if notFoundVotes:    
            print "\nNot found:"
            for notFound in notFoundVotes:
                print notFound
        print "\n"
        
    return publicKeys

def getDelegateName(publicKey):
    for delegate in allDelegates:
        if delegate['publicKey'] == publicKey:
            return delegate['username']

def generateVotingList():
    
    currentVotesPublicKeys = getMyVotes()
    
    print "POSITIVE VOTES"
    votingPublicKeysPos = getVotingPublicKeysFromFile(True)    
    
    #if votingPublicKeysPos and currentVotesPublicKeysPos:
    if votingPublicKeysPos and currentVotesPublicKeys:
        print "Removed the following positive votes, because you already voted for them:"
        for entry in list(set(votingPublicKeysPos) & set(currentVotesPublicKeys)):
            print getDelegateName(entry)
    finalVotesListPos = list(set(votingPublicKeysPos) - set(currentVotesPublicKeys)) 
    
    print "\nNEGATIVE VOTES"
    votingPublicKeysNeg = getVotingPublicKeysFromFile(False)
    
    if votingPublicKeysNeg and currentVotesPublicKeys:
        print "Removed the following negative votes, because you haven't voted for them:"
        for entry in list(set(votingPublicKeysNeg) - (set(currentVotesPublicKeys) & set(votingPublicKeysNeg))):
            print getDelegateName(entry)
    finalVotesListNeg = list(set(votingPublicKeysNeg) & set(currentVotesPublicKeys)) 

    print "\n"
    return ['+' + votePos for votePos in finalVotesListPos] + ['-' + voteNeg for voteNeg in finalVotesListNeg]


def sendVotings(payload):
    url = config['node'] + "/api/accounts/delegates"
    try:
        response = requests.put(url=url, data=payload)
        answer = json.loads(response.text)
    except requests.exceptions.RequestException as e:
        answer = []
    return answer

def getVotingPubKeys():
    publicKeys = []
    votesList = generateVotingList()
    
    print "Final list", votesList
    
    for votingname in votesList:
        prefix = votingname[0]
        name = votingname[1:]
        if prefix != '+' and prefix != '-':
            prefix = '+'
            name = votingname        
        publicKey = getPublicKey(name)
        if publicKey:
            publicKeys.append(str(prefix + publicKey))
        else:
            print "PublicKey for '" + name + "' not found"
    
    return publicKeys

def getAnswer(query):  
    answer = ""
    try:
        response = requests.get(url=query, timeout=0.5)
        answer = json.loads(response.text)
    except requests.exceptions.RequestException as e:
        answer = []
    except ValueError, e:
        print "Not allowed"
        answer = []
        
    return answer
    
def getAllDelegates():
    allDelegates = []
    limit = 100
    offset = 0
    totalCount = -1
    while totalCount == -1 or len(allDelegates) < totalCount:
        apiCall = "/api/delegates?limit=" + str(limit) + "&offset=" + str(offset) + "&orderBy=rate"
        query = config['node'] + apiCall
        answer = getAnswer(query)
        allDelegates.extend(answer['delegates'])
        if totalCount == -1:
            totalCount = answer['totalCount']
        offset = offset + limit
        
    return allDelegates
    
def help():
    print "You need to append the filename of your configuration"
    print "Example:", sys.argv[0], "configcc001.py"

def readConfig():
    global config
    with open("config.yml", 'r') as ymlfile:
        configuration = yaml.load(ymlfile)

    if len(sys.argv) == 1:
        configsection = "default"
        
    elif len(sys.argv) == 2:
        configsection = sys.argv[1]
    else:
        help
        exit(0)

    if not configsection in configuration:
        print "Unknown config section in config.yml:", configsection
        exit(0)

    config = configuration[configsection]

    if config['node'] == "REPLACE_ME" or config['mySecret'] == "REPLACE_ME" or config['mySecondSecret'] == "REPLACE_ME" or config['myAddress'] == "REPLACE_ME" or config['myPublicKey'] == "REPLACE_ME" or config['positiveVotingFilename'] == "REPLACE_ME" or config['negativeVotingFilename'] == "REPLACE_ME":
        print "Please read the instructions at the top of this file and adapt the configuration in config.yml accordingly"
        exit (0)

readConfig()
allDelegates = getAllDelegates()
finalVotingList = generateVotingList()

if finalVotingList:   
 
    print
    delegatesLength = len(finalVotingList)

    start = 0;    
    if delegatesLength > numberOfVotesPerTransaction:
        print "Splitting " + str(len(finalVotingList)) + " votes into chunks of " + str(numberOfVotesPerTransaction)

    while start < delegatesLength:
        shortDelegates = finalVotingList[start:start+numberOfVotesPerTransaction]

        payload = {
            "delegates[]": shortDelegates,
            "publicKey": config['myPublicKey'],
            "secret": config['mySecret']
        }
        if config['mySecondSecret']:
            payload['secondSecret'] = config['mySecondSecret']

        answer = sendVotings(payload)
        if answer['success']:
            print "Voted successfully for " + str(len(shortDelegates)) + " delegates"
        else:
            print "Error:", answer['error']
        start = start + numberOfVotesPerTransaction
        
else:
    print "No delegates to vote for found. Exit\n"

exit(0)