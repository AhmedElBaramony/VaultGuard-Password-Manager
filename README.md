# VaultGuard

A password vault with client-side encryption and TOTP multi-factor authentication over TLS.

Credentials are encrypted on the client with AES-256-GCM under a key derived from a master password via Argon2id, then written to a single vault file guarded by a SHA-256 integrity hash. Unlocking the vault requires both the master password and a six-digit time-based one-time password validated by a dedicated HTTPS server. The project ships desktop and mobile-style graphical clients built with CustomTkinter, along with equivalent command-line clients.

Built for CSE451 Computer and Network Security.

## 🔐 Security design

**Key derivation.** Argon2id via `argon2-cffi`, configured with a time cost of 3, 64 MiB of memory, 4 lanes of parallelism, a 16-byte random salt and a 32-byte output. The same parameters are used both for the stored master-password hash and for deriving the vault encryption key. The salt is stored alongside the ciphertext; the master password itself is never written to disk.

**Encryption.** AES-256-GCM from the `cryptography` package. Each save generates a fresh 96-bit nonce. GCM authenticates the ciphertext, so tampering surfaces as a decryption failure rather than silent corruption.

**Integrity.** Two independent SHA-256 checks. `VaultFileManager` hashes the raw ciphertext bytes and stores the digest next to the hex-encoded payload, verifying it on every load. `CryptoManager` separately hashes the inner record — password hash, salt and encrypted blob — over a key-sorted JSON serialisation, and compares it with `hmac.compare_digest` to avoid a timing side channel.

**Multi-factor authentication.** TOTP as specified in RFC 6238, using `pyotp` with a 60-second interval. Verification allows a window of ±1 interval to tolerate clock drift. Each registered user gets a random base32 shared secret.

**Transport.** The MFA server runs over HTTPS. Development uses Werkzeug's `adhoc` SSL context, which generates a self-signed certificate at startup; clients therefore disable certificate verification and suppress the corresponding urllib3 warning. This is appropriate for local development only.

## 📦 Prerequisites

- Python 3.11 or newer, built with Tk support
- The packages listed in `requirements.txt`

Two platform notes matter on macOS:

- Homebrew's Python is frequently built **without Tk**. If `python3 -c "import tkinter"` fails with `No module named '_tkinter'`, the graphical clients cannot start. Either install Tk support (`brew install python-tk`) or create the virtual environment with an interpreter that already has it. The test suite and the MFA server do not need Tk.
- **Port 5000 is claimed by AirPlay Receiver** on recent macOS versions, and the MFA server binds to it. Disable AirPlay Receiver under System Settings → General → AirDrop & Handoff, or free the port another way, otherwise the server exits with `Address already in use`.

## 🚀 Setup

macOS and Linux:

```bash
./install_deps.sh
```

Windows:

```
install_deps.bat
```

Both create a virtual environment in `.venv` and install everything in `requirements.txt`.

## ▶️ Running

The graphical stack starts the MFA server, the mobile authenticator and the vault client together:

```bash
./start_gui.sh          # macOS and Linux
start_gui.bat           # Windows
```

The console stack is equivalent, minus the GUI:

```bash
./scripts/start_system.sh
./scripts/run_app.sh          # vault client on its own
python src/cli/mobile_auth_app.py   # mobile authenticator on its own
```

First run, in order:

1. In the mobile authenticator, register a username. The server returns a base32 secret; the app stores it in `data/mobile_users.json`.
2. Select that user to display the current six-digit code and its countdown.
3. In the vault client, enter a master password, the same username, and the current code. A vault file is created on first unlock.

## 🧪 Tests

```bash
./run_tests.sh          # macOS and Linux
run_tests.bat           # Windows
```

Twenty-four tests across five modules, all runnable without a display:

| Module | Tests | Covers |
| --- | --- | --- |
| `tests/test_crypto.py` | 3 | AES-256-GCM round trip, ciphertext differs from plaintext, tampering rejected |
| `tests/test_argon2.py` | 8 | Argon2id hashing, verification, key derivation, salt handling |
| `tests/test_mfa.py` | 6 | TOTP generation and verification at a 60-second interval |
| `tests/test_vault.py` | 4 | Vault file read/write and SHA-256 integrity failure detection |
| `tests/test_integration.py` | 3 | Encrypt, save, reload and decrypt end to end |

Individual suites run through `unittest`:

```bash
python -m unittest tests.test_crypto
```

## 🗂️ Layout

```
.
├── src/
│   ├── auth/
│   │   ├── mfa_server.py         Flask HTTPS server: registration, OTP issue and verification
│   │   └── mfa_client.py         Client-side login helper used by the CLI vault
│   ├── core/
│   │   ├── crypto_manager.py     Argon2id KDF, AES-256-GCM, SHA-256 integrity
│   │   └── vault_file_manager.py Vault file read/write and checksum verification
│   ├── gui/
│   │   ├── vault_gui.py          Desktop vault client
│   │   └── mobile_auth_gui.py    Mobile-style authenticator
│   └── cli/
│       ├── main.py               Console vault client
│       └── mobile_auth_app.py    Console authenticator
├── data/                         Runtime state, resolved relative to the repository root
│   ├── vault.dat                 Encrypted credentials plus integrity hash
│   ├── mfa_db.json               Server-side TOTP secrets
│   └── mobile_users.json         Secrets cached by the mobile authenticator
├── docs/
│   ├── VaultGuard_Report.tex     Project report
│   └── verification_matrix.md    Requirement-to-implementation mapping
├── scripts/                      Console launchers
└── tests/
```

Modules import each other as `src.core.crypto_manager` and similar, so entry points insert the repository root onto `sys.path` before importing. Paths under `data/` are resolved from the module location rather than the working directory, which means the launchers can be invoked from anywhere.

## 🌐 Server API

The MFA server listens on port 5000 over HTTPS and exposes four routes.

| Route | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Liveness check |
| `/register` | POST | Registers a username, returns a new base32 TOTP secret |
| `/login` | POST | Validates a username and OTP pair |
| `/get-otp` | GET | Returns the current OTP and seconds remaining for a username |

`/get-otp-simulation` remains as a deprecated alias for `/get-otp`. Secrets are persisted to `data/mfa_db.json` and reloaded at startup.

## 🖥️ Client features

The desktop client lists stored credentials as cards and supports adding, editing, deleting and copying entries, then re-encrypts the vault on exit. The console client covers viewing, adding, editing and copying; it has no delete operation. Clipboard support comes from `pyperclip`, and the console client falls back to printing the password if that package is unavailable.

## ⚠️ Limitations

- Single user, single machine. There is no synchronisation or sharing.
- Self-signed certificates only; clients do not verify the server's identity.
- No account recovery. A forgotten master password means the vault cannot be decrypted.
- The server prints registration secrets and issued OTPs to its console, which is convenient for demonstration and unsuitable for anything else.
- No password strength enforcement.

## 🛠️ Troubleshooting

**Could not connect to MFA server.** The server must be running before either client attempts to authenticate; `start_gui.sh` and `start_system.sh` handle the ordering. If it failed to start, check whether port 5000 is already in use.

**Invalid or expired OTP.** Codes last 60 seconds, with one interval of tolerance either side. Confirm the username matches the one registered in the authenticator and that the two machines agree on the time.

**CustomTkinter not found.** Run the dependency installer. If the error instead names `_tkinter`, the interpreter lacks Tk support — see the prerequisites above.

**Failed to decrypt vault.** Either the master password is wrong or the file no longer matches its integrity hash. Deleting `data/vault.dat` starts a new empty vault and discards the stored credentials permanently.

## Contributors

- Ali Tarek
- Omar Tamer
- Fatma Ayman
- Ahmed El-Baramouny
- Ahmed Mohamed

## License

Coursework for CSE451 Computer and Network Security, for educational use.
