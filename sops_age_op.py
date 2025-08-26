#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import re
import json
from pathlib import Path


def run(cmd, input=None, capture_output=True, check=True, env=None, merge_err=False):
    if merge_err:
        result = subprocess.run(cmd, input=input, capture_output=True, text=True, check=check, env=env)
        return (result.stdout + "\n" + result.stderr).strip()
    else:
        result = subprocess.run(cmd, input=input, capture_output=capture_output, text=True, check=check, env=env)
        if capture_output:
            return result.stdout.strip()
        else:
            return None

def op_read(keypath):
    return run(["op", "read", keypath])

def op_item_get(vault, title):
    try:
        return run(["op", "item", "get", title, f"--vault={vault}"])
    except subprocess.CalledProcessError:
        return None

def op_item_create(vault, title, field, value, tags=None):
    cmd = ["op", "item", "create", "--category=password", f"--title={title}", f"--vault={vault}", f"{field}={value}"]
    if tags:
        cmd.insert(-1, f"--tags={tags}")
    return run(cmd)

def age_keygen():
    # Capture both stdout and stderr, as public key is printed to stderr
    return run(["age-keygen"], merge_err=True)

def parse_keypath(keypath):
    m = re.match(r"op://([^/]+)/([^/]+)(?:/(.+))?", keypath)
    if not m:
        raise ValueError(f"Invalid key path '{keypath}'")
    vault, title, field = m.group(1), m.group(2), m.group(3) or "password"
    return vault, title, field

def create_key(keypath, tags=None):
    vault, title, field = parse_keypath(keypath)
    if op_item_get(vault, title):
        print(f"Key vault:{vault} title:{title} already exists - will not overwrite", file=sys.stderr)
        sys.exit(1)
    newkey = age_keygen()
    op_item_create(vault, title, field, newkey, tags)
    print(f"Created vault:{vault}, title:{title}")
    # Extract and print public key
    if not newkey:
        print("Error: Failed to generate age key.", file=sys.stderr)
        return
    pubkey = None
    for line in newkey.splitlines():
        if line.strip().startswith("# public key:"):
            pubkey = line.split("# public key:",1)[1].strip()
            break
    if pubkey:
        print(f"Public key: {pubkey}")

def get_age_keys_from_1password(keypath):
    key = op_read(keypath)
    if not key:
        raise ValueError(f"Invalid keypath '{keypath}'")
    parts = key.strip().split()
    if len(parts) < 8:
        raise ValueError(f"Malformed age key in 1Password: {key}")
    pk = parts[6]
    sk = parts[7]
    return pk, sk

def sops_encrypt(file_path, pk):
    run(["sops", "--encrypt", "-a", pk, "-i", file_path], capture_output=False)

def sops_decrypt(file_path, sk):
    env = os.environ.copy()
    env["SOPS_AGE_KEY"] = sk
    run(["sops", "--decrypt", "-i", file_path], capture_output=False, env=env)

def is_sops_encrypted_with_pubkey(file_path, pubkey):
    try:
        with open(file_path, "r") as f:
            for _ in range(20):
                line = f.readline()
                if not line:
                    break
                if pubkey in line:
                    return True
        return False
    except Exception:
        return False

def rotate_secrets(path, old_keypath, new_keypath):
    old_pk, old_sk = get_age_keys_from_1password(old_keypath)
    new_pk, _ = get_age_keys_from_1password(new_keypath)
    for root, _, files in os.walk(path):
        for fname in files:
            fpath = os.path.join(root, fname)
            if not os.path.isfile(fpath):
                continue
            if is_sops_encrypted_with_pubkey(fpath, old_pk):
                print(f"Rotating secret in {fpath}")
                sops_decrypt(fpath, old_sk)
                sops_encrypt(fpath, new_pk)

def main():
    parser = argparse.ArgumentParser(description="SOPS encryption with age and 1Password")
    subparsers = parser.add_subparsers(dest="command")

    parser_create = subparsers.add_parser("create", help="Create a new age key in 1Password")
    parser_create.add_argument("-k", "--keypath", required=True)
    parser_create.add_argument("-t", "--tags", default=None)

    parser_encrypt = subparsers.add_parser("encrypt", help="Encrypt a file")
    parser_encrypt.add_argument("-k", "--keypath", required=True)
    parser_encrypt.add_argument("file")

    parser_decrypt = subparsers.add_parser("decrypt", help="Decrypt a file")
    parser_decrypt.add_argument("-k", "--keypath", required=True)
    parser_decrypt.add_argument("file")

    parser_rotate = subparsers.add_parser("rotate", help="Rotate secrets to a new age key")
    parser_rotate.add_argument("-o", "--old-keypath", required=True)
    parser_rotate.add_argument("-n", "--new-keypath", required=True)
    parser_rotate.add_argument("-p", "--path", required=True, help="Directory to search for sops-encrypted files")

    args = parser.parse_args()

    try:
        if args.command == "create":
            create_key(args.keypath, args.tags)
        elif args.command == "encrypt":
            keypath = args.keypath
            if re.match(r"^op://[^/]+/[^/]+$", keypath):
                keypath = keypath + "/password"
            pk, _ = get_age_keys_from_1password(keypath)
            sops_encrypt(args.file, pk)
        elif args.command == "decrypt":
            keypath = args.keypath
            if re.match(r"^op://[^/]+/[^/]+$", keypath):
                keypath = keypath + "/password"
            _, sk = get_age_keys_from_1password(keypath)
            sops_decrypt(args.file, sk)
        elif args.command == "rotate":
            rotate_secrets(args.path, args.old_keypath, args.new_keypath)
        else:
            parser.print_help()
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}\nKey path must be of the form 'op://vault/title[/field]'.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"External command failed: {' '.join(e.cmd)}", file=sys.stderr)
        if e.stderr:
            print(f"Error output: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(e.returncode if hasattr(e, 'returncode') else 1)

if __name__ == "__main__":
    main()
