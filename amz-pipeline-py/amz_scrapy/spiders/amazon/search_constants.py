##############################################################################
# Copyright (c) BB Studio. All Rights Reserved.
##############################################################################

#
# Search index aliases
#

INDEX_ALL = 'aps'

INDEX_KINDLE = 'digital-text'

# For desktop search based on the nubmer of results Amazon
# shows in the top info bar:
#       1-48 of over 10,000 results for "chest box for boys"
# This excludes sponsored products which are typically 12
# for Desktop version.
MAX_PAGE_RESULTS = 48
