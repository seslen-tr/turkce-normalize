"""
Komut satırı: ``python -m turkce_normalize "metin"``

Metin verilmezse standart girdiden satır satır okur::

    echo "Toplantı 14:30'da." | python -m turkce_normalize
"""
from __future__ import annotations

import argparse
import sys

from . import __version__, normalize


def main(argv=None) -> int:
    ayristirici = argparse.ArgumentParser(
        prog="python -m turkce_normalize",
        description="Türkçe metni TTS için okunur hale getirir.",
    )
    ayristirici.add_argument("metin", nargs="*", help="normalize edilecek metin (yoksa stdin)")
    ayristirici.add_argument("--cografi-kapali", action="store_true",
                             help="koordinat, ölçek, pafta kurallarını uygulama")
    ayristirici.add_argument("--version", action="version", version=__version__)
    secenek = ayristirici.parse_args(argv)

    # Windows konsolunda Türkçe karakterler bozulmasın
    for akis in (sys.stdout, sys.stdin):
        if hasattr(akis, "reconfigure"):
            try:
                akis.reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass

    cografi = not secenek.cografi_kapali
    if secenek.metin:
        print(normalize(" ".join(secenek.metin), cografi=cografi))
    else:
        for satir in sys.stdin:
            print(normalize(satir, cografi=cografi))
    return 0


if __name__ == "__main__":
    sys.exit(main())
