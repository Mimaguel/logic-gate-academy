"""
gui/sound.py
=================
Plays the game's UI sound effects (assets/sounds/*.wav - see
generate_sounds.py for how they were synthesized; they're original
generated tones, not external audio samples).

Uses PySide6.QtMultimedia's QSoundEffect, which is designed exactly for
this: short, low-latency UI sound effects. `SoundManager` just loads each
.wav once at startup and exposes a `play(name)` method.
"""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

from .theme import SOUNDS_DIR

_CLIP_NAMES = ["click", "nav", "correct", "wrong", "victory", "fail"]


class SoundManager:
    def __init__(self, volume: float = 0.55, muted: bool = False) -> None:
        self.muted = muted
        self._effects: dict[str, QSoundEffect] = {}
        for name in _CLIP_NAMES:
            path = SOUNDS_DIR / f"{name}.wav"
            effect = QSoundEffect()
            if path.exists():
                effect.setSource(QUrl.fromLocalFile(str(path)))
            effect.setVolume(volume)
            self._effects[name] = effect

    def play(self, name: str) -> None:
        if self.muted:
            return
        effect = self._effects.get(name)
        if effect is not None:
            effect.play()

    def set_muted(self, muted: bool) -> None:
        self.muted = muted

    def toggle_muted(self) -> bool:
        self.muted = not self.muted
        return self.muted
