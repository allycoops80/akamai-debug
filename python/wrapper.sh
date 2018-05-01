echo "APAC Specific tests" 
python akamai_dns_checker.py gw-apac.skyscanner.net
python akamai_curl_checker.py https://gw-apac.skyscanner.net/apps-day-view/dummy
echo "Worldwide Endpoint Tests"
python akamai_dns_checker.py gw-geo.skyscanner.net
python akamai_curl_checker.py https://gw-geo.skyscanner.net/apps-day-view/dummy
python akamai_curl_checker.py https://mobile.ds.skyscanner.net/g/apps-day-view/dummy