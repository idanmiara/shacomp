ext_whitelist = [
    '.jpg',
    '.jpeg',
    '.cr2', #cannon raw
    '.thm',
    '.cxf', #picasa: CXF file retains the paths and positions of the photos used in the collage

    '.avi',
    '.mp4',
    '.mts',
    '.mpg',
    '.wmv',
    '.mov',
    '.3gp', # very old video format

    '.mxf', # video HD raw
    '.xml', # video HD raw stuff
    '.xmp', # video HD raw stuff

    '.vob', #dvd video
    '.ifo', #dvd info
    '.bup', #dvd info backup

    '.tif',
    '.bmp',
    '.tif',
    '.gif',

    # '.mp3',
    # '.ogg',
    # '.m4a',
    # '.aac',
    '.3ga', #from whatsapp
    '.amr',

    '.txt',
    '.pdf',
    '.doc',
    '.xls',
    '.pps',
    '.ppt',
    '.url',

    '.exe',
    '.rar',
    '.zip'
    ]

interchageable_ext_sets = [('.mp4', '.m4a'), ('.mpg', '.vob'), ('.doc', '.txt'), ('.bup'), ('.ifo')]


def is_interchangable_ext(ext1, ext2):
    if ext1==ext2:
        return True
    for s in interchageable_ext_sets:
        if (ext1 in s) and (ext2 in s):
            return True
    return False

zero_sha = 'cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e'

# theose are deleted already
sha_blacklist = {zero_sha}
                 # 'bb5f0e4cad47bb8455bb274d2b9757267d8cc78112dde9600543de13d39bd035b73848aef03b591c3024b108faccc22ce76e1946dcbdd72f6233edb93fe2693d', #VIDEO_TS.mpg/vob
                 # 'fb1c1762bb9e2e1b70daa666f65ef88f81e480f18ffcfedf4c4ea0d9cd2edc57889edf981ce1a46e340cda57283298fc8d0169001921481b0f1f1f72f5991dd6'} #VENDOR.DOC/TXT


junk = ["thumbs.db", "desktop.ini", "picasa.ini", ".picasa.ini", "picasa.ini1", ".picasa.ini1", ".nomedia", '.dropbox']
junk_ext = ['.tec', '.cpi', '.lnk', '.one', '.lst', '.accdb']
