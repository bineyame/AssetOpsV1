# The shipped, read-only Site store.
#
# It ships empty on purpose. M1 ships zero canonical Sites: the shipped
# content that ships is the template catalog, and every Site in the product
# is one a user created, so first run has a genuinely empty Sites index.
#
# This directory is not pointless. It is one half of the single globally
# unique site_id space; the disjointness rule between the shipped and user
# stores is enforced against it, with fixture stores in tests rather than
# with a Site nobody configured standing in the index.
#
# Nothing writes here. The writable user store lives outside every shipped
# configuration root and is gitignored.
