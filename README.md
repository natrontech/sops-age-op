# Simple CLI for SOPS with age and 1password

This simple bash script is a wrapper for SOPS encryption with a age key saved in 1password.
You can directly encrypt and decrypt files without copy the public/private key onto the machine.
The script uses the 1password-host integration, where you have to be logged in (see Dependencies).

> ⚠️  At the moment, the script only supports the [in-place](https://github.com/getsops/sops#encrypt-or-decrypt-a-file-in-place) parameter of SOPS and will therefore encrypt/decrypt a file directly in place! 


## Dependencies

- [age](https://age-encryption.org)
- [sops](https://github.com/getsops/sops)
- [1password cli](https://developer.1password.com/docs/cli/get-started) (`op`)

## Usage

```bash
sops-age-op --help
```

- `KEY_PATH` is the path to the key in the 1password vault in one of the following formats:
  - `op://vault/title` (in this case, the defualt field name is `password`)
  - `op://vault/title/field`
  - `op://vault/title/section/field`

### Encryption

Encrypt a file:

```bash
./sops-age-op -e -k KEY_PATH [ FILE ]
```

### Decryption

Decrypt a sops file:

```bash
./sops-age-op -d -k KEY_PATH [ FILE ]
```

### Generate a new key

Generate a new age key and store it in the 1password vault. The type of the new item will be `Password`.

```bash
./sops-age-op -c -k KEY_PATH
```
