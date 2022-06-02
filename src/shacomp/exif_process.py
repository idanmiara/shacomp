from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Union, Any

import piexif


class ExifStat(IntEnum):
    UnknownErr = 0
    FileNotFound = 1
    Unsupported = 2
    NoExif = 3
    NoDateTime = 4
    InvalidDateTime = 5
    ValidExif = 6


ExifRaw = dict

def is_timestamp_valid(t: str) -> bool:
    try:
        datetime.strptime(t, "%Y:%m:%d %H:%M:%S")
        return True
    except Exception:
        return False

@dataclass
class Exif:
    # class MyExif(NamedTuple):
    # File Type                       : JPEG
    # Date/Time Original              : 2020:04:24 12:07:46
    # Create Date                     : 2020:04:24 12:07:46
    # Make                            : samsung
    # Camera Model Name               : SM-G975F
    # Image Size                      : 2944x2208
    # GPS Latitude                    : 32 deg 34' 13.22" N
    # GPS Longitude                   : 34 deg 56' 29.58" E
    type: str
    t_org: str
    t_dig: str
    t_img: str
    make: str
    model: str
    x: int
    y: int
    w: int
    h: int
    lat: float | None = None
    lon: float | None = None

    # all: dict | None = None

    @classmethod
    def is_supported(cls, filename: Path):
        return filename.suffix.lower() in ['.jpg', '.jpeg']

    @classmethod
    def get_raw(cls, filename: Path) -> tuple[Union[ExifRaw, None], ExifStat]:
        try:
            if not filename.is_file():
                return None, ExifStat.FileNotFound
            if not cls.is_supported(filename):
                return None, ExifStat.Unsupported
            exif_dict = piexif.load(str(filename))
            if not exif_dict:
                return None, ExifStat.NoExif

            # for ifd in ("0th", "Exif", "GPS", "1st"):
            #     for tag in exif_dict[ifd]:
            #         print(f'{ifd}: {tag}: {piexif.TAGS[ifd][tag]["name"]}: {exif_dict[ifd][tag]}')

            # 0th: 271: Make: b'Canon'
            # 0th: 272: Model: b'Canon PowerShot A720 IS'
            # 0th: 306: DateTime: b'2008:05:30 16:29:54'
            # Exif: 36867: DateTimeOriginal: b'2008:05:30 16:29:54'
            # Exif: 36868: DateTimeDigitized: b'2008:05:30 16:29:54'
            # Exif: 40962: PixelXDimension: 3264
            # Exif: 40963: PixelYDimension: 2448

            # exif_dict = exif_dict_decode(exif_dict)
            if not any(d for d in exif_dict.values()):
                return None, ExifStat.NoExif

            return exif_dict, ExifStat.ValidExif
        except Exception:
            return None, ExifStat.UnknownErr

    @classmethod
    def get(cls, exif_dict: ExifRaw) -> tuple[Union['Exif', None], ExifStat]:
        try:
            _0th = exif_dict.get('0th', {})
            exif = exif_dict.get('Exif', {})

            t_org = exif_decode(exif.get(piexif.ExifIFD.DateTimeOriginal))
            t_dig = exif_decode(exif.get(piexif.ExifIFD.DateTimeDigitized))
            t_img = exif_decode(_0th.get(piexif.ImageIFD.DateTime))

            if not (t_org or t_dig or t_img):
                return None, ExifStat.NoDateTime
            if not is_timestamp_valid(t_org) and not is_timestamp_valid(t_org) and not is_timestamp_valid(t_org):
                return None, ExifStat.InvalidDateTime

            gps = exif_dict.get('GPS', {})
            make, model = fix_make_model(
                exif_decode(_0th.get(piexif.ImageIFD.Make)),
                exif_decode(_0th.get(piexif.ImageIFD.Model)))
            e = cls(
                type='jpg',

                t_org=t_org,
                t_dig=t_dig,
                t_img=t_img,

                make=make,
                model=model,
                w=_0th.get(piexif.ImageIFD.ImageWidth),
                h=_0th.get(piexif.ImageIFD.ImageLength),

                x=exif.get(piexif.ExifIFD.PixelXDimension),
                y=exif.get(piexif.ExifIFD.PixelYDimension),

                lat=parse_gps(gps.get(piexif.GPSIFD.GPSLatitude)),
                lon=parse_gps(gps.get(piexif.GPSIFD.GPSLongitude)),
                # all=exif_dict,
            )
            return e, ExifStat.ValidExif
        except Exception:
            return None, ExifStat.UnknownErr


makers = {
    'Hewlett-Packard': 'HP',
    'Samsung': 'Samsung',
    'FUJIFILM': 'Fujifilm',
    'FUJI': 'Fujifilm',
    'NIKON': 'Nikon',
    'OLYMPUS': 'Olympus',
}
makers = {str(k).lower(): v for k, v in makers.items()}


def nice_model(model: str) -> str:
    spam_words = ('SAMSUNG-',)
    for spam in spam_words:
        model = model.replace(spam, '')
    return model


def nice_make(make: str) -> str:
    # makes = ['Canon', 'HP', 'NIKON CORPORATION', 'OLYMPUS OPTICAL CO.,LTD', 'Google', 'FUJIFILM', 'SONY', 'Panasonic', 'SAMSUNG',
    #  'samsung', 'MOTOROLA', 'Hewlett-Packard', 'EASTMAN KODAK COMPANY', 'Apple', 'NIKON', 'SANYO Electric Co.,Ltd',
    #  'OLYMPUS_IMAGING_CORP.', 'KONICA MINOLTA', 'LGE', 'PENTAX Corporation', 'OLYMPUS IMAGING CORP.', 'DSCimg',
    #  'CASIO COMPUTER CO.,LTD.', 'Research In Motion', 'Minolta Co., Ltd.', 'Samsung Techwin', 'OLYMPUS CORPORATION',
    #  'Toshiba', 'LG Electronics', 'Nokia', 'Microtek', 'DIGITAL', 'AgfaPhoto GmbH', 'Xiaomi', 'Hewlett-Packard Company',
    #  'Sony Ericsson', 'Zoran Corporation', 'FUJI PHOTO FILM CO., LTD.']

    spam_words = (
        'CORPORATION', 'CO.,LTD', 'CO,', 'LTD', 'EASTMAN', 'COMPANY', 'Electric', 'IMAGING', 'CORP', 'Electronics',
        'COMPUTER', 'PHOTO', 'FILM', 'OPTICAL')

    parts = make.split(sep=' ')
    maker_parts = []
    for part in parts:
        if part not in spam_words:
            part = makers.get(part.lower(), part)
            maker_parts.append(part)
    make = ' '.join(maker_parts)
    return make


def tag_friendly(s: str) -> str:
    return s.replace(' ', '-').replace('_', '-')


def fix_make_model(make: str | None, model: str | None) -> tuple[str | None, str | None]:
    make = fix_make_model_base(make)
    model = fix_make_model_base(model)
    if make:
        make = nice_make(make)
        if model:
            model = nice_make(model)
            model_parts = model.split(' ')
            make_parts = [s.lower() for s in make.split(' ')]
            new_parts = []
            for part in model_parts:
                if part.lower() not in make_parts:
                    new_parts.append(part)
            model = ' '.join(new_parts)
            model = nice_model(model)
    make = tag_friendly(make)
    model = tag_friendly(model)
    return make, model


def filename_friendly(s: str, keep=(' ','.','_','-')) -> str:
    s = "".join(c for c in s if c.isalnum() or c in keep).rstrip()
    return s


def fix_make_model_base(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip().strip('\x00').replace('_', ' ')
    s = filename_friendly(s)
    return s


def exif_parse_datetime(s: str) -> str:
    obj = datetime.strptime(s, "%Y:%m:%d %H:%M:%S")
    s = obj.strftime("%Y.%m.%d-%H.%M.%S")
    return s


def exif_decode(s: str | bytes) -> str | None:
    if not s:
        return None
    if isinstance(s, bytes):
        return s.decode("utf-8")
        # return s.decode("ascii")
    return s


OrgExifDict = dict[dict[str, Any]]


def exif_dict_decode(d: OrgExifDict):
    for tags in d.values():
        for k, tag in tags.items():
            if isinstance(tag, bytes):
                tags[k] = tag.decode("ascii")


# GPS Latitude                    : 32 deg 33' 56.49" N
# GPS Longitude                   : 34 deg 56' 12.15" E
# ((32, 1), (33, 1), (56494080, 1000000))

def parse_gps(p) -> float | None:
    if not p:
        return None
    d = p[0][0] / p[0][1]
    m = p[1][0] / p[1][1]
    s = p[2][0] / p[2][1]
    dms = d + m / 60 + s / 3600
    return dms

# import piexif
# import pyheif
#
# # from exif import Image
# #
# # with open('grand_canyon.jpg', 'rb') as image_file:
# #     my_image = Image(image_file)
# #     my_image.has_exif
# #     my_image.list_all()
#
# exif_dict = piexif.load("foo1.jpg")
# for ifd in ("0th", "Exif", "GPS", "1st"):
#     for tag in exif_dict[ifd]:
#         print(piexif.TAGS[ifd][tag]["name"], exif_dict[ifd][tag])
#
#
#
# # Using a file path:
# heif_file = pyheif.read("IMG_7424.HEIC")
# # Or using bytes directly:
# heif_file = pyheif.read(open("IMG_7424.HEIC", "rb").read())
