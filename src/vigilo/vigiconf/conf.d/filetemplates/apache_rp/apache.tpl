<Proxy /vigilo/*>
    Order deny,allow
    Allow from all
#    Allow from .your-domain.com
    Deny from all
</Proxy>
<Location /vigilo/supnavigator/%(server)s/>
        ProxyPass http://%(server)s/
        ProxyPassReverse http://%(server)s/
</Location>
<Location /vigilo/supnavigator/%(server)s:8180/>
        ProxyPass http://%(server)s:8180/
        ProxyPassReverse http://%(server)s:8180/
</Location>

