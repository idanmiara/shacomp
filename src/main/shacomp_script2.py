import csv
import json
import math
import os
import pickle
from collections import defaultdict
from pathlib import Path, PurePosixPath, PurePath
from typing import Sequence, Any

from tqdm import tqdm

from shacomp.exif_process import Exif, ExifStat, ExifRaw, fix_make_model, exif_parse_datetime
from shacomp.general_util import get_logger
from shacomp.lists import all_junk_filenames, synology_hidden_dirs
from shacomp.sha_config import sha_ext, sha_len, Checksum

ShaDict = defaultdict[Checksum, list[PurePath]]
ShaDict1 = dict[Checksum, PurePath]
ShaTupleList = list[tuple[Checksum, PurePath]]
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
    junk_roots = [
        'backupz',
        'zbak',
        'zbackup',
        'test',
        'tmp',
        'backup',
    ]
    if any(spath.startswith(f'{j}/') for j in junk_roots):
        return False
    junk_dirnames = [
        *synology_hidden_dirs,
        '#recycle',
        'venv',
        # 'Vietnam-Suits',
        # 'בנות עירבוב',
        # 'התנתקות',
        # 'd/#recycle',
        # 'd/Del',
    ]
    junk_dirnames = [f'/{x}/' for x in junk_dirnames]
    if any(j in spath for j in junk_dirnames):
        return False
    return path.name.lower() not in all_junk_filenames


def load_sha_only_set(filename: Path,
                      keep_file_callback=None,
                      encodings: Sequence[str] = ("utf-8-sig", "Windows-1255"),
                      count: int | None = None,
                      only_first: bool = False) -> ShaDict:
    for encoding in encodings:
        try:
            count = count or math.inf
            # sha_dict = ShaDict()
            sha_dict = defaultdict(list)
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
                    elif keep_file_callback is None or keep_file_callback(sha=sha, path=path):
                        if not only_first or sha not in sha_dict:
                            sha_dict[sha].append(path)
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


def sha_dict_to_sha_tuple1(sha_dict: ShaDict, only_first: bool = False) -> ShaTupleList:
    # lst = [(k, v) for v in d for k, d in sha_dict.items()]
    lst = []
    if only_first:
        lst = [(k, d[0]) for k, d in sha_dict.items()]
    else:
        for k, d in sha_dict.items():
            for v in d:
                lst.append((k, v))
    return lst


def save_sha_dict_to_file(sha_dict: ShaDict, filename: Path, only_first: bool = False):
    # sha_lines = [f"{k}  {v}\n" for k, v in sha_dict.items()]
    # sha_lines = [f"{k}  {v}\n" for k, v in sorted(sha_dict.items(), key=lambda item: item[1])]
    sha_items = sha_dict_to_sha_tuple1(sha_dict, only_first=only_first)
    sha_lines = [f"{k}  {v}\n" for k, v in sorted(sha_items, key=lambda item: item[1])]
    save_lines_to_file(lines=sha_lines, filename=filename)


# def save_sha_dict_to_filelist_file(sha_dict: ShaDict, filename: Path):
#     # sha_lines = [f"{k}  {v}\n" for k, v in sha_dict.items()]
#     sha_lines = [f"{v}\n" for v in sorted(sha_dict.values())]
#     save_lines_to_file(lines=sha_lines, filename=filename)

def add_ending(f: Path, ending: str) -> Path:
    f = Path(f)
    return Path(str(f.with_suffix('')) + ending + f.suffix)


def create_clean_files(
        filenames: list[Path],
        count: int | None = None,
        keep_file_callback=None,
        overwrite: bool = False):

    for filename in filenames:
        unique_filename = add_ending(filename, '_unique')
        clean_filename = add_ending(filename, '_clean')

        if not overwrite and clean_filename.is_file() and unique_filename.is_file():
            continue
        sha_dict1 = load_sha_only_set(filename=filename, count=count,
                                      keep_file_callback=keep_file_callback, only_first=False)
        if overwrite or not clean_filename.is_file():
            save_sha_dict_to_file(sha_dict=sha_dict1, filename=clean_filename, only_first=False)
        if overwrite or not unique_filename.is_file():
            save_sha_dict_to_file(sha_dict=sha_dict1, filename=unique_filename, only_first=True)


def create_unique_sha_files(filenames: list[Path], out_filename: Path | None = None,
                            load_output_if_exists: bool = True,
                            count: int | None = None,
                            keep_file_callback=None,
                            only_first: bool = False) -> ShaDict:
    logger.info(f'{filenames} -> {out_filename}')
    if load_output_if_exists and out_filename is not None and out_filename.is_file():
        sha_dict = load_sha_only_set(filename=out_filename, count=count,
                                     keep_file_callback=keep_file_callback, only_first=only_first)
    else:
        # sha_dict = ShaDict()
        sha_dict = defaultdict(list)
        for filename in tqdm(filenames, desc='loading files'):
            unique_filename = add_ending(filename, '_unique')
            clean_filename = add_ending(filename, '_clean')

            file_to_load = \
                unique_filename if unique_filename.is_file() and only_first else \
                clean_filename if clean_filename.is_file() else \
                filename
            sha_dict1 = load_sha_only_set(filename=file_to_load, count=count,
                                          keep_file_callback=keep_file_callback, only_first=only_first)
            if not clean_filename.is_file() and not only_first:
                save_sha_dict_to_file(sha_dict=sha_dict1, filename=clean_filename, only_first=False)
            if not unique_filename.is_file():
                save_sha_dict_to_file(sha_dict=sha_dict1, filename=unique_filename, only_first=True)

            for k, d in sha_dict1.items():
                if not only_first or k not in sha_dict:
                    sha_dict[k].extend(d)
        if out_filename:
            save_sha_dict_to_file(sha_dict=sha_dict, filename=out_filename, only_first=only_first)
    logger.info(f'count: {len(sha_dict)}')
    return sha_dict


def find_missing(masters: list[Path], copies: list[Path], out_root: Path):
    master_dict = create_unique_sha_files(masters, keep_file_callback=is_non_junk_func,
                                          # out_filename=out_root / f'master{sha_ext}',
                                          only_first=True)
    copy_dict = create_unique_sha_files(copies, keep_file_callback=is_non_junk_func,
                                        # out_filename=out_root / f'copies{sha_ext}',
                                        only_first=True)
    diff_dict = {k: v for k, v in copy_dict.items() if k not in master_dict.keys()}
    logger.info(len(diff_dict))
    if len(copies) == 1 and len(masters) == 1:
        out_filename = f'{copies[0].stem}-missing_from-{masters[0].name}'
    else:
        out_filename = f'missing_from_master{sha_ext}'
    save_sha_dict_to_file(sha_dict=diff_dict, filename=out_root / out_filename)


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
    root_dk = root / 'dk'

    # new_root = Path('//diskitty18/.')
    # master = root / f'new\dk18_20220527{sha_ext}'
    # shas = get_file_list(filename=master, out_filename=root / f'sha_files_relevant{sha_ext}')
    # copies = list([fix_unc(new_root / filename) for filename in shas.values()])

    # copies = list((root / 'old').glob(rf'**\*{sha_ext}'))
    # masters = list((root / 'new').glob(rf'**\*{sha_ext}'))
    master_name = 'dk18_20220913'
    # master_name = 'test0'
    masters = [root_dk / f'{master_name}{sha_ext}']
    print(f'{masters=}')

    copy_names = ['dk18a_20220527']
    # copy_names = ['dk18b_20220527']
    # copy_names = ['dk10_20220531', 'dk08_20220601']
    # copy_names = ['dk09_20220527-idan']
    # copy_names = ['test1', 'test2']
    print(f'{copy_names=}')

    copies = [root_dk / f'{copy_name}{sha_ext}' for copy_name in copy_names]
    create_clean_files(filenames=masters + copies)

    # for copy in copies:
    #     find_missing(masters=masters, copies=[copy], out_root=root_dk)


def save_json(e: ExifDict, filename: Path):
    logger.info(f'saving {filename}')
    with open(filename, 'w', encoding="utf-8-sig") as fp:
        # json.dump(e, fp)
        json.dump(e, fp, indent=4, sort_keys=True, default=str)
        # json.dump(e, fp, indent=4, sort_keys=True)


def load_json(filename: Path) -> ExifDict:
    logger.info(f'loading {filename}')
    with open(filename, 'r', encoding="utf-8-sig") as fp:
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


def generate_exif_raw(sha_dict: ShaDict, data_root: Path) -> tuple[ExifRawDict, ExifStatDict]:
    exif_dict = ExifRawDict()
    exif_stat: ExifStatDict = {k: ShaDict() for k in ExifStat}
    for idx, (sha, base_filenames) in enumerate(tqdm(sha_dict.items())):
        base_filename = base_filenames[0]
        filename = fix_unc(data_root / base_filename)
        if not filename.exists():
            raise Exception(f'Filename {filename} does not exist')
        # print(f'{idx}: {filename}')
        exif, stat = Exif.get_raw(filename)
        if exif is not None:
            exif_dict[sha] = exif
        exif_stat[stat][sha] = [base_filename]
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


def full_process(src_root: Path, input_root: Path, output_root: Path, name: str):
    filename = Path(input_root / f'{name}{sha_ext}')

    pickle_filename = output_root / f'{name}-unique.pickle'
    json_filename = output_root / f'{name}-unique.json'

    sha_dict = create_unique_sha_files([filename], keep_file_callback=is_non_junk_func,
                                       out_filename=output_root / f'{name}-unique{sha_ext}', count=None)

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
            exif_raw_dict, exif_stat = generate_exif_raw(sha_dict=sha_dict, data_root=src_root)
            pickle_it(exif_raw_dict, filename=pickle_filename)
            for stat, sha_dict1 in exif_stat.items():
                save_sha_dict_to_file(sha_dict=sha_dict1, filename=output_root / f'{name}-{stat.name}{sha_ext}')

        exif_dict = generate_exif(exif_raw_dict)
        save_json(exif_dict, filename=json_filename)

    new_names = generate_new_names(sha_dict=sha_dict, exif_dict=exif_dict)
    save_sha_dict_to_file(sha_dict=new_names, filename=output_root / f'{name}-new_names{sha_ext}')

    rename_and_remove(sha_dict=sha_dict, new_names=new_names,
                      rename_filename=output_root / f'{name}-rename.csv',
                      remove_filename=output_root / f'{name}-remove.txt',
                      keep_filename=output_root / f'{name}-keep.txt', )
    # src_root=Path('./'), dst_root=Path('./pic'))


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

def save_list(lst: list, filename: Path, fmt='{x}\n'):
    logger.info(f'saving {filename}')
    with open(filename, 'w', encoding="utf-8-sig") as fp:
        for x in lst:
            fp.write(fmt.format(x=x))


def save_csv(lst: list, filename: Path):
    logger.info(f'saving {filename}')
    with open(filename, 'w', newline='', encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(lst)


def load_csv(filename: Path) -> list:
    logger.info(f'loading {filename}')
    with open(filename, newline='', encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        return list(reader)


def load_list(filename: Path) -> list:
    logger.info(f'loading {filename}')
    with open(filename, 'r', encoding="utf-8-sig") as fp:
        return [x.strip() for x in fp]


def rename_and_remove(sha_dict: ShaDict, new_names: ShaDict,
                      rename_filename: Path, remove_filename: Path, keep_filename: Path):
    to_rename = []
    to_remove = []
    to_keep = []
    for sha, old_names in sha_dict.items():
        if sha in new_names:
            new_name = new_names[sha][0]
            to_rename.append((old_names[0], new_name))
        else:
            to_keep.append(old_names[0])
        to_remove.extend(old_names[1:])

    save_csv(lst=to_rename, filename=rename_filename)
    save_list(lst=to_remove, filename=remove_filename)
    save_list(lst=to_keep, filename=keep_filename)


def generate_new_names(sha_dict: ShaDict, exif_dict: ExifDict) -> ShaDict:
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
        parts = [p for p in [t, exif.make, exif.model, sha] if p]
        dst_name = dst_dir / ('_'.join(parts).replace(' ', '_') + exif.ext)
        # dst = fix_unc(dst_root / dst_name)
        new_names[sha] = [dst_name]
    return new_names


def do_rename(filename: Path, src_data: Path, dst_root: Path):
    lst = load_csv(filename=filename)
    out_filename = Path(str(filename) + '_not_found.txt')
    with open(out_filename, 'w', encoding="utf-8-sig") as fp:
        for src, dst in tqdm(lst):
            src_filename = fix_unc(src_data / src)
            if not src_filename.is_file():
                fp.write(f'{src_filename}\n')
                print(src_filename)
                continue
            dst_filename = fix_unc(dst_root / dst)
            dir_name = dst_filename.parent
            if not dir_name.is_dir():
                dir_name.mkdir(parents=True)
            src_filename.rename(dst_filename)


def do_remove(filename: Path, src_data: Path):
    lst = load_list(filename=filename)
    out_filename = Path(str(filename) + '_not_found.txt')
    with open(out_filename, 'w', encoding="utf-8-sig") as fp:
        for src in tqdm(lst):
            src_filename = fix_unc(src_data / src)
            if not src_filename.is_file():
                fp.write(f'{src_filename}\n')
                print(src_filename)
                continue
            os.remove(src_filename)


def del_all_junk_filenames(sha_dict: ShaDict, src_root: Path,
                           junk_filenames: list[str], junk_dirnames: list[str]):
    # del_sha_dict = defaultdict(list)
    junk_dirnames = [f'/{x}/' for x in junk_dirnames]
    for sha, base_names in sha_dict.items():
        # names = list(set([Path(x).name.lower() for x in base_names]))
        # if names[0] in junk_filenames:
        #     if len(names) != 1:
        #         logger.warning(f'{base_names} has some junk names and some not')
        #         continue
        # if not all([Path(x).name] for x in base_names):
        #     continue
        for base_name in base_names:
            name = base_name.name.lower()
            spath = str(base_name)
            if name in junk_filenames or any(j in spath for j in junk_dirnames):
                src = fix_unc(src_root / base_name)
                # del_sha_dict[sha].append(base_name)
                if src.is_file():
                    logger.info(f'del {src}')
                    os.remove(src)


def main():
    src_root = Path('//diskitty18/.')
    dst_root = Path('//diskitty18/d/pic/.')
    output_root = Path(r'c:\dev\sha')
    name = 'dk18a_20220527-pic'
    input_root = Path('c:\dev\sha\dk_20220527')

    # name = 'temp'
    # input_root = Path('c:\dev\sha')

    if (del_junk := True):
        junk_dirnames = [
            *synology_hidden_dirs,
            'venv',
            'Vietnam-Suits',
            'בנות עירבוב',
        ]
        master_sha_filenames = [input_root / f'{name}{sha_ext}']
        sha_dict = create_unique_sha_files(filenames=master_sha_filenames)
        del_all_junk_filenames(sha_dict=sha_dict, src_root=src_root,
                               junk_filenames=all_junk_filenames, junk_dirnames=junk_dirnames)
        exit()


    # sha_dict1 = load_sha_only_set(filename=Path(master_sha)

    # create_unique_lists(src_root=src_root, input_root=input_root, name=name, output_root=output_root)

    # rename_filename = output_root / f'{name}-rename.csv'
    # do_rename(filename=rename_filename, src_data=src_root, dst_root=dst_root)

    remove_filename = output_root / f'{name}-remove.txt'
    do_remove(filename=remove_filename, src_data=src_root)

    # keep_filename = output_root / f'{name}-keep.txt'


if __name__ == '__main__':
    # main()
    find_missing_compare()
