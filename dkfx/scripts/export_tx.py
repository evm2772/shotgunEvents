import pymel.core as pm
import maya.cmds as cmds
import traceback
import sys



storage_textures_dir = sys.argv[1]
panasas_textures_dir = sys.argv[2]


try:
    from setup_tools import append_path_to_env_var

    append_path_to_env_var('LD_LIBRARY_PATH', '/opt/solidangle/mtoa/2018/bin')

    pm.loadPlugin('mtoa')
    pm.colorManagementPrefs(e=1, renderingSpaceName="ACEScg")
    pm.colorManagementPrefs(e=1, viewTransformName="Rec 709 gamma")
    from mtoa import txManager_no_gui as txm
    reload(txm)
    txm.do(storage_textures_dir)

except Exception as ex:
    print traceback.format_exc()


