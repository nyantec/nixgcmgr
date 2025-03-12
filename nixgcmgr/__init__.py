import argparse
import pwd
import datetime
import os
from typing import Dict, Tuple, TypeGuard, Optional

NIX_GCROOTS_DIR = '/nix/var/nix/gcroots/auto/'

def yes_or_no(text: str, *, default: bool) -> bool:
    """Ask a yes/no question via raw_input() and return their answer.

     - `question` is a string that is presented to the user.
     - `default` is the presumed answer if the user just hits <Enter>.
        It must be True, False or None (meaning an answer is required).

    Returns the answer.
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default is True:
        prompt = " [Y/n] "
    elif default is False:
        prompt = " [y/N] "

    while True:
        choice = input(f"{text}? {prompt}").lower()
        if default is not None and choice == "":
            return default
        elif choice in valid:
            return valid[choice]


def try_stat_link(link: str) -> Tuple[str, Tuple[str, Optional[os.stat_result]]]:
    path = os.path.join(NIX_GCROOTS_DIR, link)
    target = os.readlink(path)
    lstat = None
    try:
        lstat = os.lstat(target)
    except (PermissionError, FileNotFoundError):
        pass
    return (link, (target, lstat))


# We can declare a type-guard here, but the function does a bit more.
# It actually also filters links for which we do not have permissions.
def filter_not_ours(
        data: Tuple[str, Tuple[str, Optional[os.stat_result]]]
) -> TypeGuard[Tuple[str, Tuple[str, os.stat_result]]]:
    if data[1][1] is None:
        return False
    if data[1][0].startswith('/nix/var/nix/profiles/'):
        # We don't clean profiles yet.
        return False
    uid = os.getuid()
    if uid != 0 and data[1][1].st_uid != uid:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='nixgcmgr',
        description='a tool to manage Nix GC root symlinks'
    )
    parser.add_argument('-a', '--max-age', default=30, type=int,
                        help='Max age beyond which a symlink is deleted')
    parser.add_argument('-y', '--noconfirm', action="store_true",
                        help='Do not ask for confirmation')
    parser.add_argument('-d', '--dry-run', action="store_true",
                        help="Don't actually delete anything, just print what would be deleted")

    args = parser.parse_args()

    links: Dict[str, Tuple[str, os.stat_result]] = dict(
        filter(
            filter_not_ours,
            map(
                try_stat_link,
                os.listdir(NIX_GCROOTS_DIR)
            )
        )
    );

    now = datetime.datetime.now()
    whoami = os.getuid()

    for gcroot, (target, lstat) in links.items():
        ctime = datetime.datetime.fromtimestamp(lstat.st_ctime)
        ago = (now - ctime).days

        print(f" - {gcroot} -> {target}")
        if lstat.st_uid != whoami:
            username = pwd.getpwuid(lstat.st_uid).pw_name
            print(f"   - owned by:   {username}")
        print(f"   - created at: {ctime} ({ago} days ago)")
        if (args.dry_run or not args.noconfirm) and ago < args.max_age:
            print( "   - inegligible for deletion")
        print()

        if ago >= args.max_age and not args.dry_run:
            if args.noconfirm or yes_or_no("Delete", default=False):
                os.unlink(target)
            print()


