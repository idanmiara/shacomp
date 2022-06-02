import json
import math
import pickle
from collections import defaultdict
from pathlib import Path, PurePosixPath, PurePath
from typing import Sequence, Any

from tqdm import tqdm

from shacomp.exif_process import Exif, ExifStat, ExifRaw, fix_make_model, exif_parse_datetime
from shacomp.general_util import get_logger
from shacomp.lists import junk_filenames
from shacomp.sha_config import sha_ext, sha_len, Checksum

ShaDict = dict[Checksum, PurePath]
ExifDict = dict[Checksum, Exif | None]
ExifRawDict = dict[Checksum, ExifRaw | None]

logger = get_logger()


def to_posixpath(f: str) -> PurePath:
    return PurePosixPath(f.replace('\\', '/'))  # transform windows path to posix path


def get_sha_tuple(line: str) -> tuple[str, PurePath | None]:
    kv = line.split(' ', 1)
    k = kv[0]
    if len(kv) < 2 or len(k) != sha_len:
        return k, None
    name = kv[1][1:]

    return k, to_posixpath(name)


def is_non_junk_func(sha: str, path: PurePath) -> bool:
    spath = str(path)
    junk_dirs = [
        '@eaDir',
        'venv',
        'Vietnam-Suits',
        'בנות עירבוב',
        #'d/#recycle',
        #'d/Del',
    ]
    junk_dirs = [f'/{x}/' for x in junk_dirs]
    if any(j in spath for j in junk_dirs):
        return False
    return path.name.lower() not in junk_filenames


def load_sha_only_set(filename: Path,
                      keep_file_callback=is_non_junk_func,
                      encodings: Sequence[str] = ("utf-8-sig", "Windows-1255"),
                      count: int | None = None) -> ShaDict:
    for encoding in encodings:
        try:
            count = count or math.inf
            sha_dict = ShaDict()
            logger.info(f'Open {filename} with encoding {encoding}')
            with open(filename, "r", encoding=encoding) as f:
                for idx, line in enumerate(tqdm(f, desc=f'reading {filename}')):
                    if idx >= count:
                        break
                    line = line.strip()
                    if line == "":
                        continue
                    sha, path = get_sha_tuple(line)
                    if path is None:
                        logger.warning(f'Invalid line: {line} in file {filename}')
                    elif keep_file_callback(sha=sha, path=path):
                        sha_dict[sha] = path
            return sha_dict
        except UnicodeDecodeError:
            logger.warning(f'Open {filename} with encoding {encoding} failed, trying next encoding...')
            continue
    raise Exception(f'Could not find proper encoding for {filename}')


def save_lines_to_file(lines: Sequence[str | PurePath] | set[str | PurePath], filename: Path):
    with open(filename, "w", encoding="utf-8-sig") as f:
        count = len(lines)
        logger.info(f"Writing: {filename}: {count} lines")
        for line in tqdm(lines, desc=f'writing {filename}'):
            # line = "{0}\n".format(line)  #  *filename
            f.write(line)

def save_sha_dict_to_file(sha_dict: ShaDict, filename: Path):
    # sha_lines = [f"{k}  {v}\n" for k, v in sha_dict.items()]
    sha_lines = [f"{k}  {v}\n" for k, v in sorted(sha_dict.items(), key=lambda item: item[1])]
    save_lines_to_file(lines=sha_lines, filename=filename)


# def save_sha_dict_to_filelist_file(sha_dict: ShaDict, filename: Path):
#     # sha_lines = [f"{k}  {v}\n" for k, v in sha_dict.items()]
#     sha_lines = [f"{v}\n" for v in sorted(sha_dict.values())]
#     save_lines_to_file(lines=sha_lines, filename=filename)


def create_unique_sha_files(filenames: list[Path], out_filename: Path | None,
                            load_output_if_exists: bool = True,
                            count: int | None = None) -> ShaDict:
    logger.info(f'{filenames} -> {out_filename}')
    if load_output_if_exists and out_filename.is_file():
        sha_dict = load_sha_only_set(filename=out_filename, count=count)
    else:
        sha_dict = ShaDict()
        for filename in tqdm(filenames, desc='loading files'):
            sha_dict1 = load_sha_only_set(filename=filename, count=count)
            sha_dict = sha_dict | sha_dict1
        if out_filename:
            save_sha_dict_to_file(sha_dict=sha_dict, filename=out_filename)
    logger.info(f'count: {len(sha_dict)}')
    return sha_dict


def find_missing(masters: list[Path], copies: list[Path], out_root: Path):
    copy_dict = create_unique_sha_files(copies, out_filename=out_root / f'copies{sha_ext}')
    master_dict = create_unique_sha_files(masters, out_filename=out_root / f'master{sha_ext}')
    diff_dict = {k: v for k, v in copy_dict.items() if k not in master_dict.keys()}
    logger.info(len(diff_dict))
    save_sha_dict_to_file(sha_dict=diff_dict, filename=out_root / f'missing_from_master{sha_ext}')


def is_sha_file(sha: str, path: PurePath) -> bool:
    return path.suffix.lower() == sha_ext


def get_file_list(filename: Path, out_filename: Path) -> ShaDict:
    # get all unique sha files from input sha file
    if out_filename.is_file():
        sha_dict = load_sha_only_set(filename=out_filename)
    else:
        sha_dict = load_sha_only_set(filename=filename, keep_file_callback=is_sha_file)
        save_sha_dict_to_file(sha_dict=sha_dict, filename=out_filename)
    return sha_dict


def fix_unc(p: Path) -> Path:
    # for some reason I couldn't do Path(//host) / 'share' so I use
    s = str(p).replace('\\.\\', '\\')
    return Path(s)


def find_missing_compare():
    root = Path(r'c:\dev\sha')

    # new_root = Path('//diskitty18/.')
    # master = root / f'new\dk18_20220527{sha_ext}'
    # shas = get_file_list(filename=master, out_filename=root / f'sha_files_relevant{sha_ext}')
    # copies = list([fix_unc(new_root / filename) for filename in shas.values()])

    # copies = list((root / 'old').glob(rf'**\*{sha_ext}'))
    copies = [Path(fr'c:\dev\sha\dk18_20220527\dk10_20220531{sha_ext}')]
    print(copies)
    masters = list((root / 'new').glob(rf'**\*{sha_ext}'))
    find_missing(masters=masters, copies=copies, out_root=root)


def save_json(e: ExifDict, filename: Path):
    logger.info(f'saving {filename}')
    with open(filename, 'w') as fp:
        # json.dump(e, fp)
        json.dump(e, fp, indent=4, sort_keys=True, default=str)
        # json.dump(e, fp, indent=4, sort_keys=True)


def load_json(filename: Path) -> ExifDict:
    logger.info(f'loading {filename}')
    with open(filename, 'r') as fp:
        data = json.load(fp)
    e = {k: eval(v) for k, v in data.items()}
    return e


def unpickle_it(filename: Path) -> Any:
    logger.info(f'loading {filename}')
    return pickle.load(open(filename, 'rb'))


def pickle_it(data, filename: Path):
    logger.info(f'saving {filename}')
    pickle.dump(data, open(filename, 'wb'))


ExifStatDict = dict[ExifStat, ShaDict]


def generate_exif_raw(d: ShaDict, data_root: Path) -> tuple[ExifRawDict, ExifStatDict]:
    exif_dict = ExifRawDict()
    exif_stat: ExifStatDict = {k: ShaDict() for k in ExifStat}
    for idx, (sha, base_filename) in enumerate(tqdm(d.items())):
        filename = fix_unc(data_root / base_filename)
        if not filename.exists():
            raise Exception(f'Filename {filename} does not exist')
        # print(f'{idx}: {filename}')
        exif, stat = Exif.get_raw(filename)
        if exif is not None:
            exif_dict[sha] = exif
        exif_stat[stat][sha] = base_filename
    return exif_dict, exif_stat


def generate_exif(exif_raw_dict: ExifRawDict) -> ExifDict:
    exif_dict = ExifDict()
    for idx, (sha, exif_raw) in enumerate(tqdm(exif_raw_dict.items())):
        exif, stat = Exif.get(exif_raw)
        if exif is not None:
            exif_dict[sha] = exif
    return exif_dict


def fix_exif_make_model(exif_dict: ExifDict):
    for exif in exif_dict.values():
        exif.make, exif.model = fix_make_model(exif.make, exif.model)


def create_unique_lists(data_root: Path, input_root: Path, output_root: Path, name: str, dst_root: Path):
    filename = Path(input_root / f'{name}{sha_ext}')

    pickle_filename = output_root / f'{name}-unique.pickle'
    json_filename = output_root / f'{name}-unique.json'

    sha_dict = create_unique_sha_files([filename], out_filename=output_root / f'{name}-unique{sha_ext}', count=None)

    if json_filename.is_file():
        exif_dict = load_json(filename=json_filename)
        fix_exif_make_model(exif_dict)
        mm = set((e.make, e.model) for e in exif_dict.values() if e.make and e.model)
        mm1 = defaultdict(list)
        for maker, model in mm:
            mm1[maker].append(model)
        print(mm1)
    else:
        if pickle_filename.is_file():
            exif_raw_dict = unpickle_it(filename=pickle_filename)
        else:
            exif_raw_dict, exif_stat = generate_exif_raw(d=sha_dict, data_root=data_root)
            pickle_it(exif_raw_dict, filename=pickle_filename)
            for stat, sha_dict1 in exif_stat.items():
                save_sha_dict_to_file(sha_dict=sha_dict1, filename=output_root / f'{name}-{stat.name}{sha_ext}')

        exif_dict = generate_exif(exif_raw_dict)
        save_json(exif_dict, filename=json_filename)

    rename_all(sha_dict=sha_dict, exif_dict=exif_dict,
               src_root=Path('./'), dst_root=Path('./pic'),
               filename=output_root / f'{name}-rename{sha_ext}')


# def main4():
#     exif_filename: Path = Path(r"c:\dev\sha\exif dump\dk18a_20220527-pic-unique.json")
#     sha_filename: Path = Path(r"c:\dev\sha\exif dump\dk18a_20220527-pic-unique.json")
#     if exif_filename.suffix == '.json':
#         exif_dict = load_json(filename=exif_filename)
#     elif exif_filename.suffix == '.pickle':
#         exif_raw_dict = unpickle_it(filename=exif_filename)
#         exif_dict = generate_exif(exif_raw_dict)
#     else:
#         raise Exception(f'Unknown file type {exif_filename}')
#
#     rename_all()


def rename_all(sha_dict: ShaDict, exif_dict: ExifDict, src_root: Path, dst_root: Path, filename: Path):
    new_names = ShaDict()
    for sha, exif in tqdm(exif_dict.items()):
        base_name = sha_dict.get(sha)
        if base_name is None:
            continue
        try:
            t = exif_parse_datetime(exif.t_org)
            dst_dir = Path(t[:4])
        except Exception:
            logger.warning(f'Invalid timeframe {exif.t_org} for {sha} {base_name}')
            continue
        # logger.info(f'{sha} {base_name}')
        src = fix_unc(src_root / base_name)
        parts = [p for p in [t, exif.make, exif.model, sha] if p]
        dst_name = dst_dir / '_'.join(parts).replace(' ', '_')
        dst = fix_unc(dst_root / dst_name)
        new_names[sha] = dst
    save_sha_dict_to_file(sha_dict=new_names, filename=filename)


if __name__ == '__main__':
    data_root = Path('//diskitty18/.')
    dst_root = Path('//diskitty18/pic/.')
    output_root = Path(r'c:\dev\sha')
    name = 'dk18a_20220527-pic'
    input_root = Path('c:\dev\sha\dk18_20220527')

    # name = 'temp'
    # input_root = Path('c:\dev\sha')

    # sha_dict1 = load_sha_only_set(filename=Path(rf'c:\dev\sha\missing_from_master{sha_ext}'))
    # find_missing_compare()
    # create_unique_lists()
    create_unique_lists(data_root=data_root, input_root=input_root, name=name, output_root=output_root, dst_root=dst_root)

    # main4()
