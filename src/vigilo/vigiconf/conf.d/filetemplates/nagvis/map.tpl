# confid:%(confid)s

define global {
allowed_user=csadm
allowed_for_config=csadm
iconset=std_big
map_image=blank.png
label_x=+97
label_y=+8
only_hard_states=1
recognize_services=1
label_show=1
}

define textbox {
text=%(hostgroupName)s
x=100
y=25
w=255
}

