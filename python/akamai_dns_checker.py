#! /usr/bin/env python
# Very basic script validate DNS traffic weightings
# from within the Akamai network.

import logging
import json
import os
import argparse
import requests
import dns.resolver
import sys
import time
from http_calls import EdgeGridHttpCaller
from akamai.edgegrid import EdgeGridAuth, EdgeRc

section_name = "default"
debug = False
verbose = False
session = requests.Session()

logger = logging.getLogger(__name__)
parser = argparse.ArgumentParser(description='Process command line options.')
parser.add_argument('--verbose', '-v', default=False, action='count')
parser.add_argument('--debug', '-d', default=False, action='count')
parser.add_argument("apex", help="The apex DNS entry you're testing")

args = parser.parse_args()
arguments = vars(args)
rc_path = os.path.expanduser("~/.edgerc")

edgerc = EdgeRc(rc_path)
baseurl = 'https://%s' % edgerc.get(section_name, 'host')

# Set the config options
session.auth = EdgeGridAuth.from_edgerc(edgerc, section_name)

if hasattr(edgerc, "debug") or arguments['debug']:
    client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    debug = True

if hasattr(edgerc, "verbose") or arguments['verbose']:
    verbose = True

httpCaller = EdgeGridHttpCaller(session, debug, verbose, baseurl)

# Request a list of locations that support the diagnostic-tools
location_result = httpCaller.getResult('/diagnostic-tools/v2/ghost-locations/available')
location_count = len(location_result['locations'])
print "There are {} locations that can run dig in the Akamai Network".format(location_count)

# The apex entry we're investigating
apex_hostname = {"hostName": args.apex}
# The intermediate entries that the apex entry should be resolving to
# according to weight and/or geo mapping
intermediate_hostnames = ['gw-elb-an-GatewayL-1DEVREX4ACQ0G-64516277.eu-west-1.elb.amazonaws.com',
                                            'gw-elb-an-GatewayL-132R0P4ZEIMA4-1748283622.eu-central-1.elb.amazonaws.com',
                                            'gw-elb-an-GatewayL-1319URO4P1DEB-1559723615.ap-southeast-1.elb.amazonaws.com',
                                            'gw-elb-an-GatewayL-LLICG84YWAGQ-845349475.ap-northeast-1.elb.amazonaws.com']

lookup_counter = {}
endpointIPs = {}

# Get the IP addresses currently associated with the intermediate 
# hostnames to use as a lookup table later
for endpoint in intermediate_hostnames:
    resolver_result = dns.resolver.query(endpoint)
    for ipaddress in resolver_result.rrset:
        if ipaddress not in endpointIPs:
            endpointIPs[str(ipaddress)] = endpoint

resolvedIPs = []
resultsTable = {}
regionCounts = {}
unknowns = 0
retries = 0

# Run a dig in each Akamai ghost location and record the end IP address
# Only recording the first address as this is enough for region match
# Exponential backoff for bad repeated bad responses as API is rate limited
attempts = 0
for num in range(0, location_count):
#for num in range(0, 9):
    backoff = 2
    location = location_result['locations'][num]['id']
    while True:
        attempts += 1
        # sys.stdout.write("\r%d - %s               " % (num, location))
        # sys.stdout.flush()
        dig_result = httpCaller.getResultHeaders("/diagnostic-tools/v2/ghost-locations/%s/dig-info" % location, apex_hostname)
        if dig_result['statuscode'] != 200:
            retries += 1
            backoff = backoff * 2
            sys.stdout.write("\r%d - %s - Status Code: %s. Rate Limit Remaining: %s. Attempt: %s Retries: %s. Backoff %s                                      " % (num, location, str(dig_result['statuscode']), str(dig_result['ratelimit']), attempts, retries, backoff))
            sys.stdout.flush()
            time.sleep(backoff)
            
            continue
        
        elif dig_result['ratelimit'] is '0':
            retries += 1
            backoff = backoff * 2
            sys.stdout.write("\r%d - %s - Status Code: %s. Rate Limit Remaining: %s. Attempt: %s Retries: %s. Backoff %s                                      " % (num, location, str(dig_result['statuscode']), str(dig_result['ratelimit']), attempts, retries, backoff))
            continue

        else:
            backoff = 1 + (10 - (int(dig_result['ratelimit'])))
            sys.stdout.write("\r%d - %s - Status Code: %s. Rate Limit Remaining: %s. Attempt: %s Retries: %s. Backoff %s                                      " % (num, location, str(dig_result['statuscode']), str(dig_result['ratelimit']), attempts, retries, backoff))
            sys.stdout.flush()
            time.sleep(backoff)
            break


    # Get the resolved IP back from the the API
    # In our use, we only take the first A record found, as the others *should*
    # be in same region
    for i in dig_result['digInfo']['answerSection']:
        if i['recordType'] == 'A':
            if location in resultsTable:
                    resultsTable[location].append(i['value'])
            else:
                    resultsTable[location] = []
                    resultsTable[location].append(i['value'])

# Initialise a dictionary for tracking counts of hits per region
for region in intermediate_hostnames:
    regionCounts[region] = 0

# run through all the dig results and match to a region in the 
# lookup table and increment a counter for each matched intermediate

# results table now has a list of Akamai locations mapped to IP
# Take the first IP for each Akamai location and map it to an AWS region
for region, ipList in resultsTable.items():
    regionCounts[endpointIPs[ipList[0]]] += 1

print json.dumps(regionCounts)


# # display the results
# for region in intermediate_hostnames:
#     print region + ": " +  str(regionCounts[region]) + " - " + str(round((float(regionCounts[region]) / (float(location_count)) * 100), 2)) + "%"
# print "not attributed " + str(unknowns)


