# Weighting discrepancy investigation

I have put together some rough scripts that use the diagnostics API to try and illustrate that we're seeing a discrepency between what is happening at a DNS level and where Akamai is routing traffic in practice.

This is based on the akamai open Python examples given [here](https://github.com/akamai/api-kickstart) :- 
[Code used to generate data](https://github.com/allycoops80/akamai-debug/tree/master/python)

**Mappings**:

    gw51.skyscanner.net - eu-west-1
    gw52.skyscanner.net - ap-southeast-1
    gw53.skyscanner.net - eu-central-1
    gw54.skyscanner.net - ap-northeast-1
   
   Validating DNS lookups against `gw-weight-apac-only.prod.aws.skyscnr.com`,  which is a a route53, weighted Round Robin entry, set 50-50 between  ap-southeast-1 and ap-northeast-1

`>> python akamai_dns_checker.py gw-weight-apac-only.prod.aws.skyscnr.com
There are 102 locations that can run dig in the Akamai Network
gw51.skyscanner.net: 0 - 0.0%
gw52.skyscanner.net: 44 - 43.14%
gw53.skyscanner.net: 0 - 0.0%
gw54.skyscanner.net: 58 - 56.86%
not attributed 0`

This is showing a 43 - 57 split in requests, so roughly what we would expect.

Now validate this against 