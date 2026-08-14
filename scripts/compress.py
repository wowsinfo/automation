"""Compress generated JSON files with zstd.

Produces ``wowsinfo.zst`` and ``lang.zst`` next to the JSON files and keeps
the original JSON files untouched. Run from the scripts folder after
generate.py, before the files are moved to the data repo.

Why zstd instead of LZMA/xz:
- The compressed size is nearly identical (zstd -19 is within a few percent
  of xz on this data).
- zstd decompression is ~5-10x faster than xz, and this file is decompressed
  on every app start, so decode speed matters more than the small size gain.
- zstd has first-class support in the Rust ecosystem (``zstd`` crate),
  Go (``klauspost/compress``), browsers and HTTP servers, so the app side
  stays simple.
- Level 19 is used because generation runs once per game update and is not
  time-critical, while the app only ever pays the fast decode side.

Usage:
    python compress.py
"""

import os
import zstandard as zstd

FILES = ['wowsinfo.json', 'lang.json']


def compress_file(path: str) -> str:
    """Compress a JSON file to ``<name>.zst`` and return the output path."""
    with open(path, 'rb') as f:
        data = f.read()

    compressed = zstd.ZstdCompressor(level=19).compress(data)
    output = os.path.splitext(path)[0] + '.zst'
    with open(output, 'wb') as f:
        f.write(compressed)
    return output


def main():
    for name in FILES:
        if not os.path.exists(name):
            print('Skipping missing {}'.format(name))
            continue
        output = compress_file(name)
        original = os.path.getsize(name)
        compressed = os.path.getsize(output)
        print('{} -> {} ({:.2f} MB -> {:.2f} MB, {:.1f}%)'.format(
            name, output, original / 1e6, compressed / 1e6,
            compressed / original * 100))


if __name__ == '__main__':
    main()
