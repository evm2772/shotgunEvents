import os
tools = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../tools'))
print tools
f ='/fd/souz_s/assets/piter_panton_bridge_rnd/subassets/bridge_section_land/textures/color/v01/builders_house_c_color.1011.tif'

basename = '%s.tx' % os.path.splitext(f)[0]
print basename