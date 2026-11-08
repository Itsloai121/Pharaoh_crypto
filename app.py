"""Textual terminal interface for Pharaoh Cryption."""

from __future__ import annotations

import os
import time
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label, Static, TextArea

from . import __version__
from .crypto import (
    PharaohCryptionError,
    decrypt_text,
    encrypt_text,
)


class OperationScreen(ModalScreen[dict[str, str] | None]):
    """Modal form used to enter plaintext or ciphertext and a key."""

    CSS = """
    OperationScreen {
        align: center middle;
        background: $background 70%;
    }

    #operation-dialog {
        width: 92%;
        max-width: 104;
        height: 86%;
        border: round #8b5cf6;
        background: #111322;
        padding: 1 2;
    }

    #dialog-heading {
        height: 2;
        color: #c4b5fd;
        text-style: bold;
        content-align: left middle;
    }

    #dialog-description {
        height: 2;
        color: #a7a9c2;
    }

    #message-label, #key-label {
        height: 1;
        color: #ddd6fe;
        text-style: bold;
        margin-top: 1;
    }

    #message-input {
        height: 1fr;
        min-height: 7;
        border: round #514477;
    }

    #key-input {
        margin-top: 1;
        border: round #514477;
    }

    #dialog-actions {
        height: 3;
        margin-top: 1;
        align: right middle;
    }

    #dialog-actions Button {
        margin-left: 1;
        min-width: 16;
    }
    """

    def __init__(self, mode: str) -> None:
        super().__init__()
        if mode not in {"encrypt", "decrypt"}:
            raise ValueError("mode must be 'encrypt' or 'decrypt'")
        self.mode = mode

    def compose(self) -> ComposeResult:
        encrypting = self.mode == "encrypt"
        heading = "ENCRYPT TEXT  /  AES-256-GCM" if encrypting else "DECRYPT TEXT  /  AES-256-GCM"
        description = (
            "Enter the text you want to protect. Multiline input is supported."
            if encrypting
            else "Paste the complete PHARAOH ciphertext and its matching key."
        )
        field_label = "PLAINTEXT" if encrypting else "ENCRYPTED TEXT"
        placeholder = (
            "Type or paste your text here..."
            if encrypting
            else "Paste PHARAOH-AES256-GCM:v1:... here..."
        )

        with Vertical(id="operation-dialog"):
            yield Label(heading, id="dialog-heading")
            yield Static(description, id="dialog-description")
            yield Label(field_label, id="message-label")
            yield TextArea(placeholder=placeholder, id="message-input", soft_wrap=True)
            if not encrypting:
                yield Label("DECRYPTION KEY", id="key-label")
                yield Input(
                    placeholder="Paste PHARAOH-KEY:v1:... here...",
                    id="key-input",
                )
            with Horizontal(id="dialog-actions"):
                yield Button("Cancel", id="cancel", variant="default")
                yield Button(
                    "Encrypt" if encrypting else "Decrypt",
                    id="submit-operation",
                    variant="success" if encrypting else "primary",
                )

    def on_mount(self) -> None:
        self.query_one("#message-input", TextArea).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        if event.button.id != "submit-operation":
            return

        message = self.query_one("#message-input", TextArea).text
        result = {"text": message}
        if self.mode == "decrypt":
            result["key"] = self.query_one("#key-input", Input).value.strip()
        self.dismiss(result)


class SavePathScreen(ModalScreen[str | None]):
    """Small modal used to choose a new output file path."""

    CSS = """
    SavePathScreen {
        align: center middle;
        background: $background 70%;
    }
    #save-dialog {
        width: 82%;
        max-width: 84;
        height: 15;
        border: round #8b5cf6;
        background: #111322;
        padding: 1 2;
    }
    #save-heading {
        color: #c4b5fd;
        text-style: bold;
        height: 2;
    }
    #save-help {
        color: #a7a9c2;
        height: 2;
    }
    #save-path {
        margin-top: 1;
    }
    #save-actions {
        height: 3;
        margin-top: 1;
        align: right middle;
    }
    #save-actions Button {
        margin-left: 1;
        min-width: 14;
    }
    """

    def __init__(self, suggested_name: str, description: str) -> None:
        super().__init__()
        self.suggested_name = suggested_name
        self.description = description

    def compose(self) -> ComposeResult:
        with Vertical(id="save-dialog"):
            yield Label("SAVE OUTPUT", id="save-heading")
            yield Static(self.description, id="save-help")
            yield Input(value=self.suggested_name, id="save-path")
            with Horizontal(id="save-actions"):
                yield Button("Cancel", id="cancel-save")
                yield Button("Save", id="confirm-save", variant="success")

    def on_mount(self) -> None:
        field = self.query_one("#save-path", Input)
        field.focus()
        field.cursor_position = len(field.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-save":
            self.dismiss(None)
        elif event.button.id == "confirm-save":
            path = self.query_one("#save-path", Input).value.strip()
            if not path:
                self.notify("Enter a file path first.", severity="warning")
                return
            self.dismiss(path)


class PharaohCryptionApp(App[None]):
    """Main full-screen TUI application."""

    TITLE = "PHARAOH CRYPTION"
    SUB_TITLE = "AES-256-GCM TEXT VAULT"
    BINDINGS = [
        ("e", "encrypt", "Encrypt"),
        ("d", "decrypt", "Decrypt"),
        ("c", "clear", "Clear"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        background: #090b16;
        color: #ececf6;
    }

    #topbar {
        dock: top;
        height: 3;
        padding: 0 2;
        background: #17152b;
        border-bottom: heavy #7c3aed;
    }

    #uptime {
        width: 1fr;
        color: #c4b5fd;
        text-style: bold;
        content-align: left middle;
    }

    #brand {
        width: auto;
        color: #f5f3ff;
        text-style: bold;
        content-align: right middle;
    }

    #page {
        width: 100%;
        height: 1fr;
        padding: 1 3;
        overflow-y: auto;
    }

    #hero {
        height: auto;
        min-height: 7;
        border: round #6d28d9;
        background: #121326;
        padding: 1 2;
        margin-bottom: 1;
    }

    #hero-title {
        color: #ddd6fe;
        text-style: bold;
        text-align: center;
        width: 100%;
        height: 2;
    }

    #hero-subtitle {
        color: #aaaac3;
        text-align: center;
        width: 100%;
        height: 2;
    }

    #action-title {
        color: #c4b5fd;
        text-style: bold;
        height: 1;
        margin: 1 0;
    }

    #actions {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1 2;
        height: 9;
        margin-bottom: 1;
    }

    #actions Button {
        width: 100%;
        height: 3;
        border: round #514477;
    }

    #encrypt {
        background: #4c1d95;
    }

    #decrypt {
        background: #312e81;
    }

    #save-key, #save-ciphertext {
        background: #20243a;
    }

    #status {
        height: 2;
        color: #a5b4fc;
        padding: 0 1;
    }

    #output-heading {
        height: 1;
        color: #c4b5fd;
        text-style: bold;
        margin-bottom: 1;
    }

    #output {
        height: 1fr;
        min-height: 8;
        border: round #514477;
        background: #0e1020;
    }

    #bottom-note {
        height: 1;
        color: #777a96;
        text-align: center;
        margin-top: 1;
    }

    Footer {
        background: #17152b;
        color: #bdb6d8;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.started_at = time.monotonic()
        self.last_ciphertext: str | None = None
        self.last_key: str | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Static("SESSION 00:00:00", id="uptime")
            yield Static(f"𓂀  PHARAOH CRYPTION  v{__version__}", id="brand")

        with Vertical(id="page"):
            with Vertical(id="hero"):
                yield Label("𓂀  PHARAOH CRYPTION", id="hero-title")
                yield Static(
                    "Private text encryption  •  AES-256-GCM  •  Local-only processing",
                    id="hero-subtitle",
                )
            yield Label("SELECT AN OPERATION", id="action-title")
            with Vertical(id="actions"):
                yield Button("E  •  Encrypt text", id="encrypt", variant="success")
                yield Button("D  •  Decrypt text", id="decrypt", variant="primary")
                yield Button("Save last key", id="save-key", disabled=True)
                yield Button("Save ciphertext", id="save-ciphertext", disabled=True)
            yield Static("Ready. Your text is processed locally on this device.", id="status", markup=False)
            yield Label("OUTPUT / RESULT", id="output-heading")
            yield TextArea(
                "Your result will appear here.\n\n"
                "Encrypt: creates a new 256-bit key and authenticated ciphertext.\n"
                "Decrypt: requires the exact ciphertext and its matching key.",
                id="output",
                read_only=True,
                soft_wrap=True,
            )
            yield Static(
                "TIP  •  Keep your decryption key private. Losing it means losing access to the text.",
                id="bottom-note",
            )
        yield Footer()

    def on_mount(self) -> None:
        self.update_uptime()
        self.set_interval(1.0, self.update_uptime)

    def update_uptime(self) -> None:
        elapsed = max(0, int(time.monotonic() - self.started_at))
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.query_one("#uptime", Static).update(
            f"SESSION {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "encrypt": self.action_encrypt,
            "decrypt": self.action_decrypt,
            "save-key": self.action_save_key,
            "save-ciphertext": self.action_save_ciphertext,
        }
        action = actions.get(event.button.id or "")
        if action is not None:
            action()

    def action_encrypt(self) -> None:
        self.push_screen(OperationScreen("encrypt"), self.finish_encrypt)

    def action_decrypt(self) -> None:
        self.push_screen(OperationScreen("decrypt"), self.finish_decrypt)

    def clear_saved_material(self) -> None:
        """Drop in-session references to any previously generated key and token."""

        self.last_ciphertext = None
        self.last_key = None
        self.query_one("#save-key", Button).disabled = True
        self.query_one("#save-ciphertext", Button).disabled = True

    def action_clear(self) -> None:
        self.clear_saved_material()
        self.query_one("#output", TextArea).text = "Output cleared."
        self.query_one("#status", Static).update("Ready for your next operation.")
        self.query_one("#save-key", Button).disabled = True
        self.query_one("#save-ciphertext", Button).disabled = True
        self.notify("Output and in-session key references cleared.")

    def finish_encrypt(self, result: dict[str, str] | None) -> None:
        if result is None:
            return
        self.clear_saved_material()
        try:
            encrypted = encrypt_text(result["text"])
        except (TypeError, ValueError) as exc:
            self.show_error(f"Encryption failed: {exc}")
            return

        self.last_ciphertext = encrypted.ciphertext
        self.last_key = encrypted.key
        output = (
            "PHARAOH ENCRYPTED TEXT\n"
            "=" * 72
            + "\n"
            + encrypted.ciphertext
            + "\n\nDECRYPTION KEY  (KEEP THIS SECRET)\n"
            + "=" * 72
            + "\n"
            + encrypted.key
            + "\n\n"
            "The key is separate from the ciphertext. Save both if you need to decrypt later."
        )
        self.query_one("#output", TextArea).text = output
        self.query_one("#status", Static).update(
            "SUCCESS • Encryption complete. A fresh 256-bit key was generated."
        )
        self.query_one("#save-key", Button).disabled = False
        self.query_one("#save-ciphertext", Button).disabled = False
        self.notify("Encryption complete. Store the key somewhere safe.", severity="information")

    def finish_decrypt(self, result: dict[str, str] | None) -> None:
        if result is None:
            return
        self.clear_saved_material()
        try:
            plaintext = decrypt_text(result["text"], result["key"])
        except PharaohCryptionError as exc:
            self.show_error(str(exc))
            return
        except (TypeError, ValueError) as exc:
            self.show_error(f"Decryption failed: {exc}")
            return

        self.query_one("#output", TextArea).text = (
            "DECRYPTED TEXT\n"
            "=" * 72
            + "\n"
            + plaintext
        )
        self.query_one("#status", Static).update(
            "SUCCESS • Authentication passed. Text decrypted successfully."
        )
        self.notify("Decryption successful.", severity="information")

    def show_error(self, message: str) -> None:
        self.query_one("#output", TextArea).text = f"OPERATION FAILED\n{'=' * 72}\n{message}"
        self.query_one("#status", Static).update(f"ERROR • {message}")
        self.notify(message, severity="error", timeout=6)

    def action_save_key(self) -> None:
        if not self.last_key:
            self.notify("There is no key to save. Encrypt some text first.", severity="warning")
            return
        self.push_screen(
            SavePathScreen(
                "pharaoh_decryption_key.key",
                "Choose a new file path. Existing files will never be overwritten.",
            ),
            self.finish_save_key,
        )

    def action_save_ciphertext(self) -> None:
        if not self.last_ciphertext:
            self.notify("There is no ciphertext to save. Encrypt some text first.", severity="warning")
            return
        self.push_screen(
            SavePathScreen(
                "pharaoh_ciphertext.txt",
                "Choose a new file path. Existing files will never be overwritten.",
            ),
            self.finish_save_ciphertext,
        )

    def finish_save_key(self, path: str | None) -> None:
        if path is None or self.last_key is None:
            return
        self._save_output(path, self.last_key, is_secret=True)

    def finish_save_ciphertext(self, path: str | None) -> None:
        if path is None or self.last_ciphertext is None:
            return
        self._save_output(path, self.last_ciphertext, is_secret=False)

    def _save_output(self, path_text: str, content: str, *, is_secret: bool) -> None:
        """Create a new file without overwriting and use private permissions."""

        path = Path(path_text).expanduser()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        # 0o600 gives the owner read/write access only on POSIX systems.
        # Windows filesystems may apply their own ACL semantics.
        try:
            descriptor = os.open(path, flags, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file:
                file.write(content)
                file.write("\n")
        except FileExistsError:
            self.notify("That file already exists. Choose another name; nothing was overwritten.", severity="error")
            return
        except OSError as exc:
            self.notify(f"Could not save file: {exc}", severity="error", timeout=6)
            return

        label = "Secret key" if is_secret else "Ciphertext"
        self.query_one("#status", Static).update(f"SAVED • {label} saved to: {path}")
        self.notify(f"{label} saved successfully.", severity="information")


def run() -> None:
    """Launch the terminal application."""

    PharaohCryptionApp().run()
