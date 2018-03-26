#! /usr/bin/env python
# Very basic script validate DNS traffic weightings
# from within the Akamai network.
#
""" Copyright 2015 Akamai Technologies, Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.

You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import json
import os
import sys
import argparse
import requests
import dns.resolver
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
parser.add_argument("url", help="The apex DNS entry you're testing")

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
print "Requesting locations that support the diagnostic-tools API.\n"
location_result = httpCaller.getResult('/diagnostic-tools/v2/ghost-locations/available')
location_count = len(location_result['locations'])
print "Testing from {} Akamai Network locations".format(location_count)

results = {}
results['Unknown'] = 0
newCurl = {}
#newCurl['url'] = 'http://mobile.ds.skyscanner.net/g/apps-day-view/dummy'
newCurl['url'] = args.url

for num in range(0, location_count):

    running = True
    region = 'Unknown'
    location = location_result['locations'][num]['id']
    sys.stdout.write("\r%d - %s               " % (num, location))
    sys.stdout.flush()
    # Wrapping the API requests in a while rule
    # This is because we see spurious 400s with no explanation
    # So when we hit that, we back off for 10 seconds and retry until
    # we get a result.
    # NB if there's actually a problem with authentication the script 
    # will get stuck here, infinitely

    while True:
        try:
            curl_result = httpCaller.postResult('/diagnostic-tools/v2/ghost-locations/%s/curl-results' % location, json.dumps(newCurl), verbose)
        except:
            print "Location: " + location + " failed"
            running = False 
            continue
        
        region = curl_result['curlResults']['responseHeaders']['X-Gateway-ServedBy']
        if region in results:
            results[region] += 1
        else:
            results[region] = 1

        break

print json.dumps(results)
    