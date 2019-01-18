# type(a)
# vars(a)
# inspect.getmembers(a, inspect.isfunction)
# https://www.tutorialspoint.com/python/python_lists.htm
# https://www.python-course.eu/lambda.php

import os
from typing import AnyStr, Dict, Iterable, List, NamedTuple, Text, Union, Any

import psutil
from wfc.custom_json_coder import CustomJSONEncoder
from flask import json
from yaml import Dumper, Loader, dump, load

import base64
import codecs
import hashlib
import io
import re
import shutil
import subprocess
import tempfile
import urllib.request
from functools import partial
from wfc.global_static import Configuration, LINE_END, LINE_START, Software
from pathlib import Path
from wfc.values import DiskFree, FileHash, MemoryFree


def split_url(url: str, parent: bool = False) -> str:
    parts = url.split('://', 1)
    if len(parts) == 2:
        has_protocol = True
        [before_protocol, after_protocol] = parts
    else:
        has_protocol = False
        after_protocol = parts[0]

    idx = after_protocol.rfind('/')
    if idx == -1:
        return (url, '')[parent]
    else:
        if parent:
            after_protocol = after_protocol[0:idx+1]
            return (after_protocol, "%s://%s" % (before_protocol, after_protocol))[has_protocol]
        return after_protocol[idx+1:]


def get_software_package_path(package_dir: Path, softwares: List[Software], software_name=None) -> Path:
    if not software_name:
        software = softwares[0]
        if not software.LocalName:
            software_name = split_url(software.PackageUrl)
        else:
            software_name = software.LocalName
    return package_dir.joinpath(software_name)


def get_software_packages(target_dir: Path, softwares: List[Software]):
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
    for software in softwares:
        url = software.PackageUrl
        ln = software.LocalName
        if not ln:
            ln = split_url(url, False)
        lf = os.path.join(target_dir, ln)
        if not os.path.exists(lf):
            print("start downloading...")
            downloading_file = urllib.request.urlopen(url)
            with open(lf, 'wb') as output:
                output.write(downloading_file.read())


def get_filecontent_str(config_file: Path, encoding="utf-8") -> Text:
    with config_file.open(encoding=encoding) as f:
        return f.read()


def get_filecontent_lines(config_file, encoding="utf-8"):
    with io.open(config_file, 'rb') as opened_file:
        if opened_file.read(3) == codecs.BOM_UTF8:
            encoding = 'utf-8-sig'
    try:
        f = io.open(config_file, mode="r", encoding=encoding)
        return f.readlines()
    except UnicodeDecodeError:
        f = io.open(config_file, mode="r", encoding='utf-16')
        return f.readlines()
    finally:
        f.close()


def get_configuration_yml(config_file: Union[str, Path], encoding="utf-8") -> Configuration:
    config_path: Path
    if isinstance(config_file, str):
        config_path = Path(config_file)
    else:
        config_path = config_file
    if not config_path.exists():
        raise ValueError("config file %s doesn't exists." % config_file)

    with io.open(config_path, mode='r', encoding=encoding) as y_stream:
        return Configuration(load(y_stream, Loader=Loader))


def get_configration(config_file: str, encoding="utf-8") -> dict:
    """Get Configuration object."""
    cfp = Path(config_file)
    if cfp.is_file() and cfp.exists():
        content = get_filecontent_str(cfp, encoding=encoding)
        j = json.loads(content)
        # PyGlobal.configuration = BorgConfiguration(j)
        return j
    raise ValueError("config file %s doesn't exists." % config_file)


def get_filehashes(files, mode="SHA256") -> List[FileHash]:
    return [get_one_filehash(h, mode) for h in files]


def get_one_filehash(file_to_hash: Union[Path, str], mode="SHA256") -> FileHash:
    h = hashlib.new(mode)
    fp: Path
    if isinstance(file_to_hash, str):
        fp = Path(file_to_hash)
    else:
        fp = file_to_hash

    with fp.open('rb') as f:
        block = f.read(512)
        while block:
            h.update(block)
            block = f.read(512)
    return FileHash(mode, str.upper(h.hexdigest()), str(fp.absolute()), fp.stat().st_size)


def get_dir_filehashes(dir_to_hash: Union[Path, str], mode="SHA256") -> List[FileHash]:
    dir_path: Path
    if isinstance(dir_to_hash, str):
        dir_path = Path(dir_to_hash)
    else:
        dir_path = dir_to_hash
    l: List[FileHash] = []
    for current_dir_name, _, files_in_current_dir in os.walk(dir_path, topdown=False):
        pf: List[Path] = [Path(current_dir_name, fn)
                          for fn in files_in_current_dir]
        pf1 = partial(get_one_filehash, mode=mode)
        l.extend(map(pf1, pf))
    return l


def send_lines_to_client(content: Union[Dict, str, bytes]):
    print(LINE_START)
    if isinstance(content, str):
        print(content)
    elif isinstance(content, bytes):
        print(content.decode())
    else:
        value = CustomJSONEncoder().encode(content)
        # print(json.dumps(content, cls=CustomJSONEncoder))
        print(value)
    print(LINE_END)


def get_diskfree() -> Iterable[DiskFree]:
    """
    "Used":  0,
    "Free":  256335872,
    "Percent":  "0.0%",
    "FreeMegabyte":  "244.5",
    "Name":  "/dev/shm",
    "UsedMegabyte":  "0.0"
    """
    mps = filter(lambda dv: dv.fstype, psutil.disk_partitions())
    mps = map(lambda dv: dv.mountpoint, mps)

    def format_result(name):
        du = psutil.disk_usage(name)
        used = du.used
        free = du.total - used
        percent = str(du.percent) + '%'
        free_megabyte = str(free / 1024)
        used_megabyte = str(used / 1024)
        return DiskFree(name, used, free, percent, free_megabyte, used_megabyte)
    return map(format_result, mps)


def parse_pair(pair_str: str, separator=';') -> Dict[str, Any]:
    """Get a string like below:
    year=*; month=*; day=1, week=*; day_of_week=*; hour=*; minute=20; second=0
    """
    pairs: List[str] = pair_str.split(separator)
    d: Dict[str, Any] = {}
    all_digits = re.compile(r'^\d+$')
    quoted = re.compile(r'^[\'"]{1}(.*)[\'"]{1}$')
    for pair in pairs:
        k, v = pair.split('=')
        k = k.strip()
        m = quoted.match(k)
        if m:
            k = m.group(1)

        v = v.strip()
        if v.startswith('0') and len(v) > 1:
            d[k] = v
        elif all_digits.match(v):
            d[k] = int(v)
        else:
            m = quoted.match(v)
            if m:
                d[k] = m.group(1)
            else:
                d[k] = v
    return d


def get_memoryfree() -> MemoryFree:
    """Format:
    total=8268038144L, available=1243422720L, percent=85.0, used=7024615424L, free=1243422720L
    """
    r = psutil.virtual_memory()
    percent = str(r.percent) + '%'
    free_megabyte = str(r.free / 1024)
    used_megabyte = str(r.used / 1024)
    return MemoryFree(r.used, r.free, percent, free_megabyte, used_megabyte, r.total)
    # return [{"Name": '', "Used": r.used, "Percent": percent,
    # "Free": r.free, "Freem": freem, "Usedm": usedm, "Total": r.total}]


def get_maxbackupnumber(path: Path) -> int:

    if not path.parent.exists():
        path.mkdir(parents=True)

    re_str = path.name + r'\.(\d+)$'

    def sl(fn):
        m = re.match(re_str, fn)
        return int(m.group(1)) if m else 0
    numbers = [sl(x) for x in os.listdir(path.parent)]
    numbers.sort()
    numbers.reverse()
    return numbers[0]


def get_next_backup(path: Path) -> Path:
    mn = 1 + get_maxbackupnumber(path)
    return Path(path.parent, "%s.%s" % (path.name, mn))


def get_maxbackup(path: Path) -> Path:
    mn = get_maxbackupnumber(path)
    if mn:
        return Path(path.parent, "%s.%s" % (path.name, mn))
    return path


def backup_localdirectory(path: Path, keep_origin=True) -> Path:
    if not path.exists():
        raise ValueError("%s doesn't exists." % path)
    m = re.match(r'^(.*?)\.\d+$', str(path))
    if m:
        nx = get_next_backup(Path(m.group(1)))
    else:
        nx = get_next_backup(path)

    if path.is_file():
        if keep_origin:
            shutil.copy(path, nx)
        else:
            shutil.move(path, nx)
    else:
        if keep_origin:
            shutil.copytree(path, nx)
        else:
            shutil.move(path, nx)
    return nx


def get_file_frombase64(base64_str, out_file: str = None) -> Path:
    decoded_str = base64.b64decode(base64_str)
    if out_file is None:
        tf = tempfile.TemporaryFile()
        with tf:
            tf.write(decoded_str)
        return Path(tf.name)
    else:
        tp = Path(out_file)
        with tp.open('w') as fd:
            fd.write(decoded_str)
        return tp


def un_protect_password_by_openssl_publickey(base64_str, openssl, private_key) -> AnyStr:
    in_file = get_file_frombase64(base64_str)
    tf = tempfile.TemporaryFile()
    tf.close()
    subprocess.call([openssl, 'pkeyutl', '-decrypt', '-inkey',
                     private_key, '-in', in_file, '-out', tf.name])
    tp = Path(tf.name)
    with tp.open() as fd:
        return fd.read()


def get_lines(path_or_lines: Union[Path, List[str]]) -> List[str]:
    if isinstance(path_or_lines, Path):
        with path_or_lines.open() as fd:
            lines = [line.strip() for line in fd.readlines()]
    else:
        lines = [line.strip() for line in path_or_lines]
    return lines


def get_block_config_value(path_or_lines, block_name, key):
    lines = get_lines(path_or_lines)
    block_found = False
    for line in lines:
        if block_found:
            m = re.match(r'^\s*(\[.*\])\s*$', line)
            if m:  # block had found, but found another block again. so value is None
                return None
            else:
                m = re.match(r'^\s*%s=(.+)$' % key, line)
                if m:
                    return m.group(1)
        else:
            if line == block_name:
                block_found = True


def update_block_config_file(path_or_lines, key, value=None, block_name="mysqld"):
    lines = get_lines(path_or_lines)
    if block_name[0] != '[':
        block_name = "[%s]" % block_name

    block_idx = -1
    next_block_idx = -1
    for idx, line in enumerate(lines):
        if block_idx != -1:
            m = re.match(r'^\s*(\[.*\])\s*$', line)
            if m:
                next_block_idx = idx
                break
        else:
            if line == block_name:
                block_idx = idx
    block_before = []
    block_found = []
    block_after = []

    if block_idx == -1:
        block_after = lines[:]
    else:
        block_before = lines[:block_idx]
        if next_block_idx == -1:
            block_found = lines[block_idx:]
        else:
            block_found = lines[block_idx: next_block_idx]
            block_after = lines[:next_block_idx]
    block_found_len = len(block_found)
    if block_found_len == 0:
        block_found.append(block_name)
        block_found.append("%s=%s" % (key, value))
    elif block_found_len == 1:
        block_found.append("%s=%s" % (key, value))
    else:
        processed = False
        for idx, line in enumerate(block_found):
            m = re.match(r'^\s*#+\s*%s=(.+)$' % key, line)
            if m:
                if value:  # found comment outed line.
                    block_found[idx] = "%s=%s" % (key, value)
                processed = True
                break
            m = re.match(r'^\s*%s=(.+)$' % key, line)
            if m:
                if not value:
                    block_found[idx] = "#%s" % line
                processed = True
                break
        if not processed and value:
            block_found.append("%s=%s" % (key, value))
    block_before.extend(block_found)
    block_before.extend(block_after)
    return block_before


def subprocess_checkout_print_error(cmd_list: List[str], env: Dict[str, str] = None, shell=False) -> str:
    # assert Path(cmd_list[0]).exists()
    return subprocess.run(cmd_list,
                            env=env,
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            shell=shell,
                            universal_newlines=True).stdout


def clone_namedtuple(nt: NamedTuple, **kwargs) -> NamedTuple:
    di: dict = nt._asdict()
    di.update(kwargs)
    return type(nt)(**di)


def common_action_handler(action, args):
    if action == 'DirFileHashes':
        send_lines_to_client(get_dir_filehashes(args[0]))
    elif action == 'FileHashes':
        send_lines_to_client(get_filehashes(args))
    elif action == 'FileHash':
        send_lines_to_client(get_one_filehash(args[0]))
    elif action == 'Echo':
        send_lines_to_client(' '.join(args))
    elif action == 'DiskFree':
        send_lines_to_client(get_diskfree())
    elif action == 'MemoryFree':
        send_lines_to_client(get_memoryfree())
