import json

with open('lookup.json') as json_data:
    ipTable = json.load(json_data)

with open('region_map.json') as json_data:
    lookupTable = json.load(json_data)

print json.dumps(ipTable)
for country in ipTable:
# 	print lookupTable[str(ipTable[country][0])]

