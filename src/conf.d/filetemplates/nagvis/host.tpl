define host {
label_text=%(name)s
url=/vigilo/supnavigator/SupNavigator.py/supPage?host=%(name)s
backend_id=%(sup_server)s
x=%(coord_x)d
y=%(coord_y)d
host_name=%(name)s
recognize_services=0
}
define host {
url=/vigilo/supnavigator/SupNavigator.py/supPage?host=%(name)s
backend_id=%(sup_server)s
x=%(coord_services_x)d
y=%(coord_services_y)d
host_name=%(name)s
label_show=0
}
define shape {
icon=metro.png
x=%(coord_metro_x)d
y=%(coord_metro_y)d
url=/vigilo/supnavigator/SupNavigator.py/fullHostPage?host=%(name)s
}

