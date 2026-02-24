from types import ModuleType
from unittest.mock import MagicMock

import pytest

import src.notifier as notifier_module
from src.notifier import Notifier


pytestmark = [pytest.mark.unit]


def test_notify_returns_early_for_empty_payload():
    notifier = Notifier()
    notifier._send_desktop_notification = MagicMock()
    notifier._print_console_notification = MagicMock()
    notifier._copy_to_clipboard = MagicMock()
    notifier._play_sound = MagicMock()

    notifier.notify(None, "author")

    notifier._send_desktop_notification.assert_not_called()
    notifier._print_console_notification.assert_not_called()
    notifier._copy_to_clipboard.assert_not_called()
    notifier._play_sound.assert_not_called()


def test_notify_dispatches_channels_based_on_config():
    notifier = Notifier()
    notifier.config = {
        "desktop_notifications": True,
        "copy_to_clipboard": True,
        "sound_alert": True,
    }
    notifier._send_desktop_notification = MagicMock()
    notifier._print_console_notification = MagicMock()
    notifier._copy_to_clipboard = MagicMock()
    notifier._play_sound = MagicMock()

    notifier.notify({"signals": [{"ticker": "AAPL"}]}, "author")

    notifier._send_desktop_notification.assert_called_once()
    notifier._print_console_notification.assert_called_once()
    notifier._copy_to_clipboard.assert_called_once()
    notifier._play_sound.assert_called_once()


def test_signal_objs_handles_non_dict_payload():
    notifier = Notifier()
    assert notifier._signal_objs("bad") == []


def test_send_desktop_notification_returns_when_no_signals():
    notifier = Notifier()
    notifier_module.notification.notify = MagicMock()

    notifier._send_desktop_notification({"signals": []}, "author")

    notifier_module.notification.notify.assert_not_called()


def test_send_desktop_notification_uses_osascript_on_macos(monkeypatch):
    notifier = Notifier()
    fake_subprocess = ModuleType("subprocess")
    fake_subprocess.run = MagicMock()
    monkeypatch.setattr(notifier_module.sys, "platform", "darwin")
    monkeypatch.setitem(__import__("sys").modules, "subprocess", fake_subprocess)

    notifier._send_desktop_notification({"signals": [{"ticker": "AAPL", "action": "BUY", "confidence": 0.8}]}, "author")

    fake_subprocess.run.assert_called_once()


def test_send_desktop_notification_falls_back_to_plyer(monkeypatch):
    notifier = Notifier()
    monkeypatch.setattr(notifier_module.sys, "platform", "linux")
    notifier_module.notification.notify = MagicMock()

    notifier._send_desktop_notification({"signals": [{"ticker": "AAPL", "action": "BUY", "confidence": 0.9}]}, "author")

    notifier_module.notification.notify.assert_called_once()


def test_copy_to_clipboard_joins_tickers():
    notifier = Notifier()
    notifier_module.pyperclip.copy = MagicMock()

    notifier._copy_to_clipboard({"signals": [{"ticker": "AAPL"}, {"ticker": "TSLA"}]})

    notifier_module.pyperclip.copy.assert_called_once_with("AAPL, TSLA")


def test_copy_to_clipboard_no_tickers_no_copy_call():
    notifier = Notifier()
    notifier_module.pyperclip.copy = MagicMock()

    notifier._copy_to_clipboard({"signals": [{"action": "BUY"}]})

    notifier_module.pyperclip.copy.assert_not_called()


def test_play_sound_windows_uses_winsound(monkeypatch):
    notifier = Notifier()
    fake_winsound = ModuleType("winsound")
    fake_winsound.Beep = MagicMock()
    monkeypatch.setattr(notifier_module.sys, "platform", "win32")
    monkeypatch.setitem(__import__("sys").modules, "winsound", fake_winsound)

    notifier._play_sound()

    fake_winsound.Beep.assert_called_once_with(1000, 200)


def test_play_sound_macos_uses_afplay(monkeypatch):
    notifier = Notifier()
    fake_os = ModuleType("os")
    fake_os.system = MagicMock()
    monkeypatch.setattr(notifier_module.sys, "platform", "darwin")
    monkeypatch.setitem(__import__("sys").modules, "os", fake_os)

    notifier._play_sound()

    fake_os.system.assert_called_once()


def test_play_sound_linux_uses_paplay_or_bell(monkeypatch):
    notifier = Notifier()
    fake_os = ModuleType("os")
    fake_os.system = MagicMock()
    monkeypatch.setattr(notifier_module.sys, "platform", "linux")
    monkeypatch.setitem(__import__("sys").modules, "os", fake_os)

    notifier._play_sound()

    fake_os.system.assert_called_once()
