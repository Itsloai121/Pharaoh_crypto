<div align="center">

# 𓂀 Pharaoh Cryption

### A clean, fast terminal vault for AES-256-GCM text encryption.

**Encrypt locally. Keep your key. Decrypt whenever you need it.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Encryption](https://img.shields.io/badge/Cipher-AES--256--GCM-7c3aed)
![Interface](https://img.shields.io/badge/Interface-Textual%20TUI-5b4bdb)

</div>

---

## ✨ What is Pharaoh Cryption?

**Pharaoh Cryption** is a local Python terminal application that encrypts text using **AES-256-GCM**. It creates a new cryptographically secure 256-bit key for every encryption, then gives you two separate pieces of data:

1. **Encrypted text** — the ciphertext you can store or send.
2. **Decryption key** — the secret key required to recover the original text.

The key is **not** embedded in the ciphertext. Keep both pieces: without the matching key, the encrypted text cannot be decrypted.

The interface is built with [Textual](https://textual.textualize.io/) and includes a live session timer in the top-left corner, clear operation screens, result output, and save options for the key and ciphertext.

## 🔐 Security features

- **AES-256-GCM:** authenticated encryption using a 256-bit AES key.
- **Fresh key per encryption:** generated using the cryptographic library's secure random key generator.
- **Fresh 96-bit nonce:** generated for each message using the operating system's secure random source.
- **Tamper detection:** decryption fails if the ciphertext or key is incorrect or the encrypted data has been modified.
- **Separate key:** the decryption key is displayed separately and can be saved to its own file.
- **Local processing:** the application does not upload your text or keys to a server.
- **Safe file saving:** save operations refuse to overwrite an existing file. On POSIX systems, saved files are created with owner-only read/write permissions where supported.

> **Important:** This is a key-based encryption tool, not a password manager or password-based encryption system. There is no password recovery or key recovery service. If you lose the decryption key, the encrypted text cannot be recovered. Anyone who obtains the key can decrypt its matching ciphertext.

## 🖥️ Interface preview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ SESSION 00:03:42                                      𓂀 PHARAOH CRYPTION v1.0 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          𓂀  PHARAOH CRYPTION                               │
│          Private text encryption • AES-256-GCM • Local-only processing      │
│                                                                              │
│                           SELECT AN OPERATION                               │
│                                                                              │
│       E  •  Encrypt text                      D  •  Decrypt text              │
│       Save last key                            Save ciphertext              │
│                                                                              │
│  Ready. Your text is processed locally on this device.                      │
│                                                                              │
│  OUTPUT / RESULT                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Your result will appear here...                                         │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  TIP • Keep your decryption key private. Losing it means losing the text.   │
└──────────────────────────────────────────────────────────────────────────────┘
```

*The live interface adapts to your terminal size; this is a simplified preview.*

## ⚙️ Requirements

- Python **3.10 or newer**
- `pip`
- A modern terminal (Windows Terminal, PowerShell, macOS Terminal, or a Linux terminal)
- Internet access during installation to download the two Python dependencies

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/pharaoh-cryption.git
cd pharaoh-cryption
```

Replace `YOUR-USERNAME` with your GitHub username after you publish the repository.

### 2. Create and activate a virtual environment (recommended)

**Windows — PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Launch Pharaoh Cryption

From the repository directory:

```bash
python -m pharaoh_cryption
```

Or install the project itself and use its command:

```bash
python -m pip install -e .
pharaoh-cryption
```

## 🚀 How to use it

### Encrypt text

1. Launch the application.
2. Select **Encrypt text** or press `E`.
3. Type or paste your plaintext into the large input area. Multiline text is supported.
4. Select **Encrypt**.
5. The output panel displays the encrypted text and its separate decryption key.
6. Use **Save last key** and **Save ciphertext** to save them as separate files, or copy them from the output panel.

### Decrypt text

1. Select **Decrypt text** or press `D`.
2. Paste the complete `PHARAOH-AES256-GCM:v1:...` ciphertext.
3. Paste the matching `PHARAOH-KEY:v1:...` key.
4. Select **Decrypt**. The original text appears only after authentication succeeds.

### Save the key and ciphertext

After encryption, use the two save buttons to save the values independently. You can enter a relative or absolute file path. Existing files are never overwritten; choose a different name if the destination already exists.

**Suggested practice:** store the key in a secure location separate from the ciphertext. Do not commit key files to GitHub, send them in the same message as the ciphertext, or share them with anyone who should not read the original text.

## ⌨️ Keyboard shortcuts

| Key | Action |
|---|---|
| `E` | Open the encryption form |
| `D` | Open the decryption form |
| `C` | Clear the current output and in-session key references |
| `Q` | Quit the application |

The on-screen buttons are also clickable. In the output area, press `F7` to select all text, then `Ctrl+C` to copy it (clipboard behavior depends on your terminal). Use `Q` to quit the application.

## 🧪 Run tests

The encryption engine includes tests for successful round trips, empty input, fresh keys, incorrect keys, tampering, and malformed input.

```bash
python -m unittest discover -s tests -v
```

## 🧩 Ciphertext and key format

The output is versioned so future releases can distinguish formats:

- Ciphertext prefix: `PHARAOH-AES256-GCM:v1:`
- Key prefix: `PHARAOH-KEY:v1:`
- Encoding: URL-safe Base64
- Cipher: AES-256-GCM
- Nonce: 12 bytes (96 bits)
- Authentication tag: 16 bytes (128 bits)

The nonce and authentication tag are carried with the ciphertext. They are not secret; the 256-bit key is secret. The implementation uses authenticated associated data to bind the encrypted content to the Pharaoh Cryption format/version.

## ⚡ Performance notes

The application keeps the encryption path deliberately small: one key generation, one nonce generation, one AES-GCM operation, and Base64 encoding for transport. The `cryptography` package delegates AES-GCM to optimized native cryptographic backends where available. Actual throughput depends on the CPU, operating system, and installed cryptographic backend.

## ⚠️ Responsible use

Use Pharaoh Cryption to protect text that you own or are authorized to handle. Treat the decryption key like a password: anyone with the key and matching ciphertext can recover the plaintext. Do not use screenshots, terminal logs, shared computers, or public repositories to store secret keys.

## 📄 License

This project is released under the MIT License; see the [`LICENSE`](LICENSE) file.

---

<div align="center">

**𓂀 PHARAOH CRYPTION — Your text. Your key. Your control.**

</div>
