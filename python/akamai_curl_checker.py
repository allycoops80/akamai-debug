#! /usr/bin/env python
# Very basic script validate DNS traffic weightings
# from within the Akamai network.
#


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
newCurl['url'] = args.url

attempts = 0
retries = 0


for num in range(0, location_count):
#for num in range(0, 4):
    running = True
    region = 'Unknown'
    location = location_result['locations'][num]['id']
    # Wrapping the API requests in a while rule
    # This is because we see spurious 400s with no explanation
    # So when we hit that, we back off for 10 seconds and retry until
    # we get a result.
    # NB if there's actually a problem with authentication the script
    # will get stuck here, infinitely
    attempts = 0
    while True:
        attempts += 1
        curl_result = httpCaller.postResultHeaders(
            '/diagnostic-tools/v2/ghost-locations/%s/curl-results' \
            % location, json.dumps(newCurl), verbose)
        if curl_result['statuscode'] != 200:
            retries += 1
            backoff = backoff * 2
            sys.stdout.write("\r%d - %s - Status Code: %s. Rate Limit Remaining: %s. Attempt: %s Retries: %s. Backoff %s"
                             % (num, location, str(curl_result['statuscode']), 
                                str(curl_result['ratelimit']), attempts, retries, backoff))
            sys.stdout.flush()
            time.sleep(backoff)
            continue
        elif curl_result['ratelimit'] is '0':
            retries += 1
            backoff = backoff * 2
            sys.stdout.write("\r%d - %s - Status Code: %s. Rate Limit Remaining: %s. Attempt: %s Retries: %s. Backoff %s"
                             % (num, location, str(curl_result['statuscode']), 
                                str(curl_result['ratelimit']), attempts, retries, backoff))
            continue
        else:
            backoff = 1 + (16 - (int(curl_result['ratelimit'])))
            sys.stdout.write("\r%d - %s - Status Code: %s. Rate Limit Remaining: %s. Attempt: %s Retries: %s. Backoff %s"
                             % (num, location, str(curl_result['statuscode']), 
                                str(curl_result['ratelimit']), attempts, retries, backoff))
            sys.stdout.flush()
            time.sleep(backoff)
            break
        
    region = curl_result['curlResults']['responseHeaders']['X-Gateway-ServedBy']
    if region in results:
        results[region] += 1
    else:
        results[region] = 1

print json.dumps(results)
    