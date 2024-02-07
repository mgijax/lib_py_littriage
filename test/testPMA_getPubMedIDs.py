import PubMedAgent
import urllib.request, urllib.parse, urllib.error

#
# Test PubMedAgent.getPubMedIDs(doiList)
#
# Usage:
#
# source mgiconfig/master.config.csh
# testPMA_getgetPubMedIDs.py >& testPMA_getPubMedIDs.py.out
#

# 1.1038/sj.bjc.6690123 and 3kjab093cdejah5r  will be None
doiList = ['10.1038/sj.bjc.6690123', '1.1038/sj.bjc.6690123', '3kjab093cdejah5r', '10.1006/bbrc.1999.0184', '10.1038/nbt.1929']

#doiList = ['10.1097/FPC.0b013e3283369347.1234567890', '10.1038/nbt.1929', '10.1093/emboj/18.4.934', '10.1006/bbrc.1999.0243', '10.1006/bbrc.1999.0168', '10.1006/bbrc.1999.0163', '10.1006/bbrc.1999.0184', '10.1006/mgme.1998.2784', '10.1006/bbrc.1999.0283', '10.1016/S0002-9440(10)65297-2', '10.1038/sj.bjc.6690123', '10.1006/dbio.1998.9161', '10.1002/neu.480070610', '10.1006/geno.1998.5606', '10.1006/geno.1998.5701', '10.1006/cimm.1998.1429', '10.1006/geno.1998.5668', '10.1006/geno.1998.5705', '10.1006/abbi.1998.1091', '10.1006/viro.1998.9571']
#doiList = ['10.1097/FPC.0b013e3283369347.1234567890', '10.1038/sj.bjc.6690123', '10.1006/bbrc.1999.0184', '10.1038/nbt.1929']

print('Processing %s DOI IDs\n' % len(doiList))
pma = PubMedAgent.PubMedAgentMedline()
# test getPubMedIDs function
mapping = pma.getPubMedIDs(doiList)

for doiId in mapping:
    print('doiId: %s' % doiId)
    pmIds = mapping[doiId]
    for pmId in pmIds:
        print('  pmId: %s' % pmId)
