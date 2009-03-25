; <?php return 1; ?>
; confid:%(confid)s
; the line above is to prevent
; viewing this file from web.
; DON'T REMOVE IT!

; ----------------------------
; Default NagVis Configuration File
; At delivery everything here is commented out. The default values are set in the NagVis code.
; You can make your changes here, it'll overwrite the default settings.
; ----------------------------

; ----------------------------
; !!! The Sections/Variables with a leading ";" won't be recognized by NagVis (commented out) !!!
; ----------------------------

; global options
[global]
; select language (english,german,french,...)
;language="english"
; rotate maps (0/1)
;rotatemaps=0
; maps to rotate
;maps="demo,demo2"
; show header (0/1)
;displayheader=1
; refresh time of pages
;refreshtime=60
refreshtime=30

; default values for the maps
[defaults]
; default backend (id of the default backend)
;backend="ndomy_1"
; default icons
;icons="std_medium"
; recognize service states in host/hostgroup objects
;recognizeservices=1
; recognize only hard states (not soft)
;onlyhardstates=0
; background color of maps
;backgroundcolor="#fff"
; header template
;headertemplate="default"
; hover template
;hovertemplate="default"
; hover menu open delay (seconds)
;hoverdelay=0
; show map in lists (dropdowns, index page, ...)
;showinlists=1
; use gdlibs (if set to 0 lines will not work, all other types should work fine)
;usegdlibs=1
; target for the icon links
;urltarget="_self"
usegdlibs=1
icons="std_big"
recognizeservices=1
onlyhardstates=1
headertemplate="default"

; options for the wui
[wui]
; auto update frequency
;autoupdatefreq=25
; map lock time (minutes)
;maplocktime=5
; Users which are allowed to change the NagVis configuration (comma seperated list)
allowedforconfig=EVERYONE

; path options
[paths]
; absolute physical NagVis path
;base="/usr/share/nagvis/htdocs/"
; absolute html NagVis path
htmlbase="/vigilo/nagvis"
; absolute html NagVis cgi path
htmlcgi="/nagios3/cgi-bin"

; options for the NDO-Backend

