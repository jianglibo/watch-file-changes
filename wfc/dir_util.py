
import re
from typing import Union, List

from pathlib import Path


def list_dir_order_by_digits(target_dir: Union[str, Path], ext_no_dot='zip') -> List[Path]:
    target_path: Path
    if isinstance(target_dir, str):
        target_path = Path(target_dir)
    else:
        target_path = target_dir
    target_ptn = re.compile(r'(\d+)\.%s$' % ext_no_dot)
    paths: List[Path] = list(filter(lambda p: target_ptn.match(p.name), target_path.iterdir()))
    def custom_sort(item: Path):
        m = target_ptn.match(item.name)
        if m is None:
            return 0
        return int(m.group(1))
    paths.sort(key=custom_sort)
    return paths
