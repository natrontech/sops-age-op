
# SOPS + age + 1Password Python CLI

This Python script is a CLI wrapper for SOPS encryption/decryption using an age key stored in 1Password. It allows you to encrypt, decrypt, rotate, and manage secrets without copying private keys to your machine.

> ⚠️ All operations are performed in-place: files are encrypted/decrypted directly!

## Dependencies

- [age](https://age-encryption.org)
- [sops](https://github.com/getsops/sops)
- [1Password CLI (`op`)](https://developer.1password.com/docs/cli/get-started)
- Python 3.7+

## Usage

```bash
python3 sops_age_op.py --help
```

### Key Path Format

- `op://vault/title` (defaults to field `password`)
- `op://vault/title/field`
- `op://vault/title/section/field`

### Commands


#### Encrypt a file

```bash
python3 sops_age_op.py encrypt -k KEY_PATH FILE
```
or (field defaults to `password`):
```bash
python3 sops_age_op.py encrypt -k op://vault/title FILE
```

To use a custom .sops.yaml config (for creation_rules, etc):
```bash
python3 sops_age_op.py encrypt --sops-config path/to/.sops.yaml -k KEY_PATH FILE
```

#### Decrypt a file

```bash
python3 sops_age_op.py decrypt -k KEY_PATH FILE
```
or:
```bash
python3 sops_age_op.py decrypt -k op://vault/title FILE
```

#### Generate a new age key and store in 1Password

```bash
python3 sops_age_op.py create -k KEY_PATH [-t TAGS]
```
- The new key is stored as a 1Password item of type `Password`.
- The public key is printed after creation.


#### Rotate secrets to a new age key

Recursively re-encrypt all SOPS-encrypted files in a directory with a new age key:

```bash
python3 sops_age_op.py rotate -o OLD_KEY_PATH -n NEW_KEY_PATH -p /path/to/secrets
```
You can also specify a custom .sops.yaml config for rotation:
```bash
python3 sops_age_op.py rotate -o OLD_KEY_PATH -n NEW_KEY_PATH -p /path/to/secrets --sops-config path/to/.sops.yaml
```
- All files encrypted with the old public key will be decrypted and re-encrypted with the new key.

## 1Password Authentication

You must be signed in to 1Password CLI (`op`). Use:
```bash
eval $(op signin)
```
