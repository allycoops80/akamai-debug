#! /usr/bin/env python
# Very basic script validate DNS traffic weightings of gateway 
# endpoints from inside the Akamai network.
# 100 lookups from random locations, giving a count of where lookups 
# are being pointed to. 
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
import requests, logging, json, sys, os
from http_calls import EdgeGridHttpCaller
from random import randint
from akamai.edgegrid import EdgeGridAuth,EdgeRc
import urllib
import argparse
import logging
import time

section_name="default"
debug = False
verbose = False
session = requests.Session()

logger = logging.getLogger(__name__)
parser = argparse.ArgumentParser(description='Process command line options.')
parser.add_argument('--verbose', '-v', default=False, action='count')
parser.add_argument('--debug', '-d', default=False, action='count')

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

httpCaller = EdgeGridHttpCaller(session, debug,verbose, baseurl)

# Request locations that support the diagnostic-tools
print
print ("Requesting locations that support the diagnostic-tools API.\n")

location_result = httpCaller.getResult('/diagnostic-tools/v2/ghost-locations/available')

# Select a random location to host our request
location_count = len(location_result['locations'])

print("There are {} locations that can run dig in the Akamai Network".format(location_count))
rand_location = randint(0, location_count-1)
location = location_result['locations'][rand_location]['id']
print ("We will make our call from " + location + "\n")

# Request the dig request the {OPEN} Developer Site IP information
dig_parameters = { "hostName":"gw-weight-apac-only.prod.aws.skyscnr.com"}

total = 0
southeast = 0
northeast = 0
notrecognised = 0


for num in range(1,100):
	print("There are {} locations that can run dig in the Akamai Network".format(location_count))
	rand_location = randint(0, location_count-1)
	location = location_result['locations'][rand_location]['id']
	print ("We will make our call from " + location + "\n")
	dig_result = httpCaller.getResult("/diagnostic-tools/v2/ghost-locations/%s/dig-info" % location,dig_parameters)
	# Get the resolved IP back from the the API
	ipaddress = dig_result['digInfo']['answerSection'][0]['value']

	if ipaddress == '52.199.27.69':
		print "northeast"
		northeast += 1
	elif ipaddress == '52.199.227.76':
		print "northeast"
		northeast += 1
	elif ipaddress == '52.76.187.185':
		print "southeast"
		southeast += 1
	elif ipaddress == '13.250.195.87':
		print "southeast"
		southeast += 1
	else:
		print "Not recognised" + ipaddress
	total += 1
	time.sleep(1)

print "northeast: " + str(northeast)
print "southeast: " + str(southeast)
print "not recognised" + str(notrecognised)
print "total: " + str(total)
