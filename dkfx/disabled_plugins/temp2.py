import re, fnmatch, os
from pprint import pprint


def textures_parser(root_folder):
    masks = ["*.bmp", "*.exr", "*.gif", "*.hdri", "*.jpeg", "*.jpg", "*.png", "*.psd", "*.tiff", "*.tif", "*.tga"]
    includes = '|'.join([fnmatch.translate(x) for x in masks])
    #print includes
    texture_paths = []
    for (dirpath, dirnames, filenames) in os.walk(root_folder):
        #files = [f for f in filenames if re.match(includes, f)]
        if dirnames:
            # find versions:
            version_dirs = [d for d in dirnames if re.match(r'v\d\d', d)]
            if version_dirs:
                version_dirs.sort() # for any case ;-)
                last_version_dir = os.path.join(dirpath, version_dirs[-1])
                print version_dirs, '--> ', last_version_dir
                for (dirpath, dirnames, filenames) in os.walk(last_version_dir):
                    files = [f for f in filenames if re.match(includes, f)]
                    print '\t\t\t', files
                    for f in files:
                        texture_paths.append(os.path.join(last_version_dir, f))

    #just_names = [os.path.basename(t) for t in texture_paths]
    #pprint (just_names)
    pprint (texture_paths)
    return texture_paths


if __name__ == "__main__":
    textures_parser('/mnt/storage/souz_s/assets/piter_panton_bridge_rnd/textures')