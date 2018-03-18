#! /usr/bin/env python
# Very basic script validate DNS traffic weightings
# from within the Akamai network.

import logging
import json
import os
import argparse
import requests
import dns.resolver
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
intermediate_hostnames = ['gw51.skyscanner.net',
						                    'gw52.skyscanner.net',
						                    'gw53.skyscanner.net',
						                    'gw54.skyscanner.net']
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
regionCounts = {}
unknowns = 0

# Run a dig in each Akamai ghost location and record the end IP address
# Only recording the first address as this is enough for region match
for num in range(0, location_count):
    location = location_result['locations'][num]['id']
    try:
        dig_result = httpCaller.getResult("/diagnostic-tools/v2/ghost-locations/%s/dig-info" % location, apex_hostname)
    except:
        print "Problem  digging in location: " + location
        unknowns += 1
    # Get the resolved IP back from the the API
    resolvedIPs.append(dig_result['digInfo']['answerSection'][0]['value'])

# Initialise a dictionary for tracking counts of hits per region
for region in intermediate_hostnames:
    regionCounts[region] = 0

# run through all the dig results and match to a region in the 
# lookup table and increment a counter for each matched intermediate
for ip in resolvedIPs:
    if ip in endpointIPs:
        regionCounts[endpointIPs[ip]] += 1
    else:
        unknowns += 1

# display the results
for region in intermediate_hostnames:
    print region + ": " +  str(regionCounts[region]) + " - " + str(round((float(regionCounts[region]) / (float(location_count)) * 100), 2)) + "%"
print "not attributed " + str(unknowns)

