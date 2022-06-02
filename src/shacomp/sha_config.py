from typing import NamedTuple

Checksum = str

class ChecksumDetails(NamedTuple):
    ext: str
    len: int


SHA: dict[str, ChecksumDetails] = {
    'sha512': ChecksumDetails(ext='.sha512', len=128),
    'sha256': ChecksumDetails(ext='.sha256', len=64),
}
sha = 'sha256'
sha_ext = SHA[sha].ext
sha_len = SHA[sha].len
