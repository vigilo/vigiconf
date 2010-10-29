# Full path to the pmacct executable.
pmacct: /usr/bin/pmacct

# Paths to the pipes used for inbound and outbound metering.
inbound: /tmp/acct_in.pipe
outbound: /tmp_acct_out.pipe

# Networks with the hosts that are metered.
%(hosts)s
