#!/usr/bin/env python3
import argparse
import getpass
import os
import re
import sys
import tempfile

from grep_data import *

COOKIE_FILE = os.path.join(tempfile.gettempdir(), "elearning_cookies.pkl")
TESTID_RE = re.compile(r"TestID=(\d+)")
NUMONLY_RE = re.compile(r"^\d+$")
INVALTOK_RE = re.compile(r"[<>:;,?\"*|/\\]+")

Cookie = load_cookies(COOKIE_FILE)

# Parser definitions
root_parser = argparse.ArgumentParser(
    description="A simple program to dump testpapers from njmu elearning.")
subparsers = root_parser.add_subparsers(dest="command")
subparsers.required = True

login_parser = subparsers.add_parser("login")
login_parser.add_argument("-u", "--user", dest="username")

download_parser = subparsers.add_parser("download")
download_parser.add_argument("testpaper", help="Testpaper URL or TestID")
download_parser.add_argument(
    "-o",
    "--output",
    dest="output",
    help="Output filename, use `{id}` as TestID, `{name}` as testpaper name.")

args = root_parser.parse_args()

if __name__ == "__main__":
    try:
        if args.command == "login":
            if args.username:
                username = args.username
            else:
                username = input("Username: ")

            password = getpass.getpass("Password: ")
            Cookie = login(username, password)
            save_cookies(Cookie, COOKIE_FILE)

        elif args.command == "download":
            if NUMONLY_RE.match(args.testpaper):
                paper, el, ec = get_all_data(args.testpaper, Cookie)
            elif TESTID_RE.search(args.testpaper):
                match = TESTID_RE.search(args.testpaper)
                paper, el, ec = get_all_data(match.group(), Cookie)
            else:
                raise ValueError(
                    "Unrecognizable testpaper argument: %s" % args.testpaper)
            res = parse_result(el, ec)
            txt = render_to_text(res)

            if args.output:
                path, fn = os.path.split(args.output)
                fn = fn.format(
                    id=paper.get("PaperID", "-1"),
                    name=paper.get("Papername", "UNK"))
                fn = INVALTOK_RE.sub("_", fn)
                f = open(os.path.join(path, fn), "a")
            else:
                f = sys.stdout

            f.write(txt)
            f.close()

        else:
            root_parser.print_help()

    except Exception as e:
        print(e)
        exit(1)
    exit(0)
