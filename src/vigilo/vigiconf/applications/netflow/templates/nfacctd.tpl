!
! nfacctd configuration example
!
! Did you know CONFIG-KEYS contains the detailed list of all configuration keys
! supported by 'nfacctd' and 'pmacctd' ?
!
! debug: true
daemonize: true
nfacctd_port: %(port)s
aggregate[in]: src_net
aggregate[out]: dst_net
plugins: memory[in], memory[out]
imt_path[in]: %(inbound)s
imt_path[out]: %(outbound)s
imt_buckets: 65537
imt_mem_pools_size: 65536
imt_mem_pools_number: 0
networks_file : /etc/pmacct/network.lst

