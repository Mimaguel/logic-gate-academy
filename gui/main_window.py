"""
gui/main_window.py
=================
Loads `main_window.ui` (a Qt Designer file) and connects every
button/field in it to the game logic in `game/`. Also applies the visual
theme (gui/theme.py), wires sound effects (gui/sound.py), and drives the
small animations (gui/effects.py) that make navigation and feedback feel
alive rather than instant/flat.

Design note: this file intentionally does NOT subclass QMainWindow.
Since the .ui file's top-level widget already *is* a QMainWindow, the
cleanest approach with QUiLoader is to load it directly and drive it
from a plain Python object (`AppController`) that just holds references
to widgets and game-state.
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QFile, QIODevice, Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QPushButton, QTableWidgetItem, QWidget
from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QPieSeries, QValueAxis

from game import admin_auth, content, encoding, reports
from game.accounts import AccountManager, Player
from game.challenges import (
    BONUS_POINTS,
    NUMBER_CHALLENGE_MAX_ATTEMPTS,
    POINTS_PER_ROUND,
    ROUNDS_PER_CHALLENGE,
    STARTING_LIVES,
    Difficulty,
    generate_ascii_question,
    generate_binary_question,
    generate_round,
    is_valid_binary_answer,
)
from game.leaderboard import Leaderboard

from . import effects, theme
from .sound import SoundManager

_GUI_DIR = Path(__file__).resolve().parent
UI_PATH = _GUI_DIR / "main_window.ui"
_PROJECT_ROOT = _GUI_DIR.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_REPORTS_DIR = _PROJECT_ROOT / "reports"

DEFAULT_LEADERBOARD_SAVE_PATH = _DATA_DIR / "leaderboard.enc"
DEFAULT_LEADERBOARD_KEY_PATH = _DATA_DIR / "leaderboard.key"
DEFAULT_ACCOUNTS_SAVE_PATH = _DATA_DIR / "accounts.enc"
DEFAULT_ACCOUNTS_KEY_PATH = _DATA_DIR / "accounts.key"

_FEEDBACK_COLORS = {
    "success": theme.GREEN,
    "error": theme.RED_GLOW,
    "warning": theme.YELLOW,
    "info": theme.GRAY,
}


def load_main_window():
    """Load and return the QMainWindow defined by main_window.ui."""
    loader = QUiLoader()
    ui_file = QFile(str(UI_PATH))
    ui_file.open(QIODevice.ReadOnly)
    window = loader.load(ui_file)
    ui_file.close()
    if window is None:
        raise RuntimeError(f"Failed to load {UI_PATH}: {loader.errorString()}")
    return window


class AppController:
    """Owns the game's model objects and wires the loaded .ui widgets to
    them. One instance per running application."""

    def __init__(
        self,
        window,
        leaderboard_save_path: Path = DEFAULT_LEADERBOARD_SAVE_PATH,
        leaderboard_key_path: Path = DEFAULT_LEADERBOARD_KEY_PATH,
        accounts_save_path: Path = DEFAULT_ACCOUNTS_SAVE_PATH,
        accounts_key_path: Path = DEFAULT_ACCOUNTS_KEY_PATH,
        muted: bool = False,
    ):
        self.window = window
        self._widget_cache: dict[str, QWidget] = {}

        # -- visuals & audio ------------------------------------------------
        theme.load_fonts()
        self.window.setStyleSheet(theme.build_stylesheet())
        self.sound = SoundManager(muted=muted)

        # -- model layer -------------------------------------------------
        self.accounts = AccountManager(accounts_save_path, accounts_key_path)
        self.leaderboard = Leaderboard(save_path=leaderboard_save_path, key_path=leaderboard_key_path)

        # -- session / navigation state ------------------------------------
        self.current_player: Player | None = None
        self.pending_login_mode: str = "create"      # "create" | "login" | "admin"
        self.difficulty_context: str = "challenge"    # "challenge" | "practice"
        self.leaderboard_return_page: str = "page_main_menu"
        self.admin_authenticated = False

        # scored/practice challenge state
        self.current_difficulty: Difficulty | None = None
        self.challenge_is_practice = False
        self.challenge_round_number = 1
        self.challenge_lives = 0
        self.challenge_score = 0
        self.challenge_collected_bits: list[int] = []
        self.challenge_current_round = None

        # bonus round state
        self.bonus_ascii_value: int | None = None
        self.bonus_code = ""

        # number-practice state
        self.number_kind = "binary"   # "binary" | "ascii"
        self.number_data = None
        self.number_attempts_left = NUMBER_CHALLENGE_MAX_ATTEMPTS

        # tutorial state
        self.tutorial_index = 0

        self._connect_signals()
        self._wire_click_sounds()
        self._start_hero_glow()
        self.goto("page_main_menu")

    # -- widget lookup / navigation ---------------------------------------

    def _w(self, name: str) -> QWidget:
        widget = self._widget_cache.get(name)
        if widget is None:
            widget = self.window.findChild(QWidget, name)
            if widget is None:
                raise RuntimeError(f"main_window.ui has no widget named {name!r}")
            self._widget_cache[name] = widget
        return widget

    def goto(self, page_name: str) -> None:
        page_widget = self._w(page_name)
        self._w("stack").setCurrentWidget(page_widget)
        effects.fade_in(page_widget, duration=220)

    def _set_feedback(self, label_name: str, text: str, kind: str = "info") -> None:
        """Set a feedback label's text + color together, with a small
        pop-in animation so results don't just silently appear."""
        label = self._w(label_name)
        color = _FEEDBACK_COLORS.get(kind, theme.WHITE)
        label.setStyleSheet(
            f'QLabel {{ color: {color}; font-family: "Rajdhani SemiBold"; font-size: 16px; min-height: 24px; }}'
        )
        label.setText(text)
        if text:
            effects.pop_in(label, duration=240)

    def _start_hero_glow(self) -> None:
        effects.glow_pulse(self._w("lblMainTitle"), color=theme.RED)

    def _wire_click_sounds(self) -> None:
        """Attach a UI sound to every button in the app based on its
        `role` property - "ghost" (back/cancel-style) buttons get the
        softer `nav` cue, everything else gets the punchier `click`."""
        for btn in self.window.findChildren(QPushButton):
            role = btn.property("role")
            sound_name = "nav" if role == "ghost" else "click"
            btn.clicked.connect(lambda checked=False, s=sound_name: self.sound.play(s))

    # -- wiring -------------------------------------------------------------

    def _connect_signals(self) -> None:
        w = self._w

        # Top banner
        w("btnMuteToggle").clicked.connect(self._toggle_mute)

        # Main Menu
        w("btnStartChallenge").clicked.connect(lambda: self.goto("page_login_menu"))
        w("btnViewLeaderboard").clicked.connect(
            lambda: self._show_leaderboard(self.leaderboard.top(10), "LEADERBOARD", "page_main_menu")
        )
        w("btnTutorial").clicked.connect(self._open_tutorial)
        w("btnLearningMode").clicked.connect(lambda: self.goto("page_learning_menu"))
        w("btnAdminDashboard").clicked.connect(self._go_admin_login)
        w("btnQuit").clicked.connect(self.window.close)

        # Login menu
        w("btnCreateAccount").clicked.connect(self._go_create_account)
        w("btnLoginExisting").clicked.connect(self._go_login_existing)
        w("btnPlayGuest").clicked.connect(self._go_guest)
        w("btnLoginBack").clicked.connect(lambda: self.goto("page_main_menu"))

        # Credentials
        w("btnCredSubmit").clicked.connect(self._submit_credentials)
        w("btnCredBack").clicked.connect(self._credentials_back)
        w("txtUsername").returnPressed.connect(self._submit_credentials)
        w("txtPassword").returnPressed.connect(self._submit_credentials)
        w("txtConfirmPassword").returnPressed.connect(self._submit_credentials)

        # Difficulty
        w("btnDifficultyEasy").clicked.connect(lambda: self._choose_difficulty(Difficulty.EASY))
        w("btnDifficultyMedium").clicked.connect(lambda: self._choose_difficulty(Difficulty.MEDIUM))
        w("btnDifficultyHard").clicked.connect(lambda: self._choose_difficulty(Difficulty.HARD))
        w("btnDifficultyBack").clicked.connect(self._difficulty_back)

        # Challenge
        w("btnAnswer0").clicked.connect(lambda: self._submit_challenge_answer(0))
        w("btnAnswer1").clicked.connect(lambda: self._submit_challenge_answer(1))
        w("btnChallengeQuit").clicked.connect(lambda: self.goto("page_main_menu"))

        # Bonus round
        w("btnBonusSubmit").clicked.connect(self._submit_bonus_guess)
        w("txtBonusGuess").returnPressed.connect(self._submit_bonus_guess)
        w("btnBonusContinue").clicked.connect(lambda: self.goto("page_main_menu"))

        # Leaderboard
        w("btnLeaderboardBack").clicked.connect(lambda: self.goto(self.leaderboard_return_page))

        # Tutorial
        w("btnTutorialNext").clicked.connect(self._tutorial_next)
        w("btnTutorialBack").clicked.connect(self._tutorial_back)
        w("btnTutorialFinish").clicked.connect(lambda: self.goto("page_main_menu"))

        # Learning Mode menu
        w("btnPracticeGates").clicked.connect(self._open_practice_gates)
        w("btnPracticeNumbers").clicked.connect(lambda: self.goto("page_number_practice_menu"))
        w("btnExplainGates").clicked.connect(
            lambda: self._show_explain("LOGIC GATES", content.gate_reference_markdown())
        )
        w("btnExplainBinary").clicked.connect(
            lambda: self._show_explain("BINARY NUMBERS", content.BINARY_EXPLANATION_MARKDOWN)
        )
        w("btnExplainAscii").clicked.connect(
            lambda: self._show_explain("ASCII", content.ASCII_EXPLANATION_MARKDOWN)
        )
        w("btnLearningBack").clicked.connect(lambda: self.goto("page_main_menu"))

        # Number practice menu
        w("btnBinaryToDecimal").clicked.connect(lambda: self._start_number_question("binary"))
        w("btnAsciiToBinary").clicked.connect(lambda: self._start_number_question("ascii"))
        w("btnNumberPracticeBack").clicked.connect(lambda: self.goto("page_learning_menu"))

        # Number question
        w("btnNumberSubmit").clicked.connect(self._submit_number_answer)
        w("txtNumberAnswer").returnPressed.connect(self._submit_number_answer)
        w("btnNumberBack").clicked.connect(lambda: self.goto("page_number_practice_menu"))

        # Explain
        w("btnExplainBack").clicked.connect(lambda: self.goto("page_learning_menu"))

        # Admin dashboard
        w("btnAdminViewLeaderboard").clicked.connect(self._admin_view_leaderboard)
        w("btnAdminViewAccounts").clicked.connect(self._admin_view_accounts)
        w("btnAdminReports").clicked.connect(self._open_admin_reports)
        w("btnAdminReset").clicked.connect(self._admin_open_reset_confirm)
        w("btnAdminBack").clicked.connect(self._admin_back_to_main)

        # Admin accounts
        w("btnAdminAccountsBack").clicked.connect(lambda: self.goto("page_admin_dashboard"))

        # Admin reset confirm
        w("btnResetConfirm").clicked.connect(self._admin_confirm_reset)
        w("btnResetCancel").clicked.connect(lambda: self.goto("page_admin_dashboard"))
        w("txtResetConfirm").returnPressed.connect(self._admin_confirm_reset)

        # Admin reports
        w("btnAdminReportsBack").clicked.connect(lambda: self.goto("page_admin_dashboard"))
        w("btnGenerateReport").clicked.connect(self._export_pdf_report)

    # -- sound --------------------------------------------------------------

    def _toggle_mute(self) -> None:
        muted = self.sound.toggle_muted()
        self._w("btnMuteToggle").setText("\U0001F507 MUTED" if muted else "\U0001F50A SOUND")

    # -- Login / accounts ---------------------------------------------------

    def _go_admin_login(self) -> None:
        self._configure_credentials_page("admin")
        self.goto("page_credentials")

    def _go_create_account(self) -> None:
        self._configure_credentials_page("create")
        self.goto("page_credentials")

    def _go_login_existing(self) -> None:
        self._configure_credentials_page("login")
        self.goto("page_credentials")

    def _go_guest(self) -> None:
        self.current_player = self.accounts.play_as_guest()
        self._configure_difficulty_page("challenge")
        self.goto("page_difficulty")

    def _configure_credentials_page(self, mode: str) -> None:
        self.pending_login_mode = mode
        titles = {"create": "Create Account", "login": "Login", "admin": "Admin Login"}
        self._w("lblCredTitle").setText(titles[mode])

        show_username = mode in ("create", "login")
        show_confirm = mode == "create"
        self._w("lblUsername").setVisible(show_username)
        self._w("txtUsername").setVisible(show_username)
        self._w("lblConfirm").setVisible(show_confirm)
        self._w("txtConfirmPassword").setVisible(show_confirm)

        self._w("txtUsername").clear()
        self._w("txtPassword").clear()
        self._w("txtConfirmPassword").clear()
        self._w("lblCredStatus").setText("")

    def _submit_credentials(self) -> None:
        mode = self.pending_login_mode
        password = self._w("txtPassword").text()

        if mode == "admin":
            if admin_auth.check_admin_password(password):
                self.admin_authenticated = True
                self.goto("page_admin_dashboard")
            else:
                self._w("lblCredStatus").setText("Incorrect admin password.")
                self.sound.play("wrong")
            return

        username = self._w("txtUsername").text()
        if mode == "create":
            confirm = self._w("txtConfirmPassword").text()
            player, error = self.accounts.create_account(username, password, confirm)
        else:
            player, error = self.accounts.login(username, password)

        if error:
            self._w("lblCredStatus").setText(error)
            self.sound.play("wrong")
            return

        self.current_player = player
        self._configure_difficulty_page("challenge")
        self.goto("page_difficulty")

    def _credentials_back(self) -> None:
        if self.pending_login_mode == "admin":
            self.goto("page_main_menu")
        else:
            self.goto("page_login_menu")

    # -- Difficulty -----------------------------------------------------------

    def _configure_difficulty_page(self, context: str) -> None:
        self.difficulty_context = context
        title = "CHOOSE A DIFFICULTY" if context == "challenge" else "PRACTICE DIFFICULTY"
        self._w("lblDifficultyTitle").setText(title)

    def _choose_difficulty(self, difficulty: Difficulty) -> None:
        self._start_new_challenge(difficulty, is_practice=self.difficulty_context == "practice")

    def _difficulty_back(self) -> None:
        if self.difficulty_context == "challenge":
            self.goto("page_login_menu")
        else:
            self.goto("page_learning_menu")

    def _open_practice_gates(self) -> None:
        self._configure_difficulty_page("practice")
        self.goto("page_difficulty")

    # -- Challenge (scored 7-round run, and practice single-question) -------

    def _start_new_challenge(self, difficulty: Difficulty, is_practice: bool) -> None:
        self.current_difficulty = difficulty
        self.challenge_is_practice = is_practice
        if not is_practice:
            self.challenge_round_number = 1
            self.challenge_lives = STARTING_LIVES
            self.challenge_score = 0
            self.challenge_collected_bits = []
        self.challenge_current_round = generate_round(difficulty)
        self.goto("page_challenge")
        self._render_challenge_round()

    def _render_challenge_round(self) -> None:
        difficulty = self.current_difficulty
        if self.challenge_is_practice:
            self._w("lblChallengeHeader").setText(f"PRACTICE - {difficulty.label.upper()}")
            self._w("lblLives").setText("Unlimited retries - no lives lost")
        else:
            self._w("lblChallengeHeader").setText(
                f"ROUND {self.challenge_round_number} OF {ROUNDS_PER_CHALLENGE} ({difficulty.label.upper()})"
            )
            self._w("lblLives").setText(f"Lives remaining: {self.challenge_lives}")

        self._w("txtQuestion").setPlainText(self.challenge_current_round.question_text(difficulty) + "\n\nEnter 0 or 1.")
        self._set_feedback("lblChallengeFeedback", "")
        self._w("btnAnswer0").setEnabled(True)
        self._w("btnAnswer1").setEnabled(True)
        self._w("btnChallengeQuit").setText("Quit to Main Menu")
        self._w("btnChallengeQuit").setVisible(self.challenge_is_practice)

    def _submit_challenge_answer(self, value: int) -> None:
        rnd = self.challenge_current_round
        correct = value == rnd.expected

        if self.challenge_is_practice:
            if correct:
                self._set_feedback("lblChallengeFeedback", "Correct!", "success")
                self.sound.play("correct")
                self._w("btnAnswer0").setEnabled(False)
                self._w("btnAnswer1").setEnabled(False)
                QTimer.singleShot(700, self._next_practice_round)
            else:
                self._set_feedback("lblChallengeFeedback", "Incorrect. Try again.", "error")
                self.sound.play("wrong")
            return

        if correct:
            self.challenge_collected_bits.append(value)
            self.challenge_score += POINTS_PER_ROUND[self.current_difficulty]
            self.challenge_round_number += 1
            self.sound.play("correct")
            if self.challenge_round_number > ROUNDS_PER_CHALLENGE:
                self._enter_bonus_round()
                return
            self.challenge_current_round = generate_round(self.current_difficulty)
            self._render_challenge_round()
            self._set_feedback("lblChallengeFeedback", f"Correct! Score: {self.challenge_score}", "success")
        else:
            self.challenge_lives -= 1
            if self.challenge_lives <= 0:
                self._fail_challenge()
            else:
                self._w("lblLives").setText(f"Lives remaining: {self.challenge_lives}")
                self._set_feedback("lblChallengeFeedback", "Incorrect, try again.", "error")
                self.sound.play("wrong")

    def _next_practice_round(self) -> None:
        self.challenge_current_round = generate_round(self.current_difficulty)
        self._render_challenge_round()

    def _fail_challenge(self) -> None:
        self._set_feedback("lblChallengeFeedback", "Out of lives - the run ends here.", "error")
        self.sound.play("fail")
        self._w("btnAnswer0").setEnabled(False)
        self._w("btnAnswer1").setEnabled(False)
        self._w("btnChallengeQuit").setText("Back to Main Menu")
        self._w("btnChallengeQuit").setVisible(True)

    # -- Bonus round ------------------------------------------------------------

    def _enter_bonus_round(self) -> None:
        code = "".join(str(b) for b in self.challenge_collected_bits)
        ascii_value = encoding.binary_to_decimal(code)
        ascii_range = encoding.find_ascii_range(ascii_value)
        self.bonus_ascii_value = ascii_value
        self.bonus_code = code

        self._w("lblBonusCode").setText(f"Your binary code is {code} (decimal {ascii_value}).")
        self._set_feedback("lblBonusFeedback", "")
        table = self._w("tblBonusReference")

        if ascii_range is not None:
            rows = ascii_range.characters()
            table.setRowCount(len(rows))
            for r, (code_val, char) in enumerate(rows):
                table.setItem(r, 0, QTableWidgetItem(str(code_val)))
                table.setItem(r, 1, QTableWidgetItem(repr(char)))
            table.setVisible(True)
            self._w("txtBonusGuess").setVisible(True)
            self._w("txtBonusGuess").setEnabled(True)
            self._w("txtBonusGuess").clear()
            self._w("btnBonusSubmit").setVisible(True)
            self._w("btnBonusSubmit").setEnabled(True)
            self._w("btnBonusContinue").setVisible(False)
        else:
            table.setVisible(False)
            self._w("txtBonusGuess").setVisible(False)
            self._w("btnBonusSubmit").setVisible(False)
            self._w("btnBonusContinue").setVisible(True)
            self._set_feedback(
                "lblBonusFeedback",
                f"You built the binary code {code}. Great work, {self.current_player.username}!",
                "success",
            )
            self.sound.play("victory")
            self.leaderboard.add(self.current_player.username, self.challenge_score, self.current_difficulty.label)

        self.goto("page_bonus_round")

    def _submit_bonus_guess(self) -> None:
        guess = self._w("txtBonusGuess").text()
        if guess == chr(self.bonus_ascii_value):
            self.challenge_score += BONUS_POINTS
            self.leaderboard.add(self.current_player.username, self.challenge_score, self.current_difficulty.label)
            self._set_feedback(
                "lblBonusFeedback",
                f"Congratulations, {self.current_player.username}! Final score: {self.challenge_score}",
                "success",
            )
            self.sound.play("victory")
            self._w("txtBonusGuess").setEnabled(False)
            self._w("btnBonusSubmit").setEnabled(False)
            self._w("btnBonusContinue").setVisible(True)
        else:
            self._set_feedback("lblBonusFeedback", "Not quite - try again.", "error")
            self.sound.play("wrong")
            self._w("txtBonusGuess").clear()

    # -- Leaderboard -------------------------------------------------------------

    def _show_leaderboard(self, entries, title: str, return_page: str) -> None:
        self.leaderboard_return_page = return_page
        self._w("lblLeaderboardTitle").setText(title)
        table = self._w("tblLeaderboard")
        table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            table.setItem(row, 1, QTableWidgetItem(entry.username))
            table.setItem(row, 2, QTableWidgetItem(str(entry.score)))
            table.setItem(row, 3, QTableWidgetItem(entry.difficulty))
        self.goto("page_leaderboard")

    # -- Tutorial -----------------------------------------------------------------

    def _open_tutorial(self) -> None:
        self.tutorial_index = 0
        self._render_tutorial_page()
        self.goto("page_tutorial")

    def _render_tutorial_page(self) -> None:
        page = content.TUTORIAL_PAGES[self.tutorial_index]
        is_last = self.tutorial_index == len(content.TUTORIAL_PAGES) - 1
        self._w("lblTutorialHeading").setText(f"Tutorial - {page.heading}")
        self._w("lblTutorialProgress").setText(f"Page {self.tutorial_index + 1} / {len(content.TUTORIAL_PAGES)}")
        self._w("txtTutorialBody").setMarkdown(page.body)
        self._w("btnTutorialNext").setVisible(not is_last)
        self._w("btnTutorialBack").setEnabled(self.tutorial_index > 0)
        self._w("btnTutorialFinish").setVisible(is_last)

    def _tutorial_next(self) -> None:
        if self.tutorial_index < len(content.TUTORIAL_PAGES) - 1:
            self.tutorial_index += 1
        self._render_tutorial_page()

    def _tutorial_back(self) -> None:
        self.tutorial_index = max(0, self.tutorial_index - 1)
        self._render_tutorial_page()

    # -- Learning Mode: explanations ------------------------------------------------

    def _show_explain(self, title: str, markdown_text: str) -> None:
        self._w("lblExplainTitle").setText(title)
        self._w("txtExplainBody").setMarkdown(markdown_text)
        self.goto("page_explain")

    # -- Learning Mode: number practice ----------------------------------------------

    def _start_number_question(self, kind: str) -> None:
        self.number_kind = kind
        self.number_attempts_left = NUMBER_CHALLENGE_MAX_ATTEMPTS

        if kind == "binary":
            self.number_data = generate_binary_question()
            self._w("lblNumberQuestionTitle").setText("BINARY -> DECIMAL")
            self._w("lblNumberQuestionText").setText(
                f"What is the decimal equivalent of {self.number_data.binary_string}?"
            )
        else:
            self.number_data = generate_ascii_question()
            self._w("lblNumberQuestionTitle").setText("ASCII -> BINARY")
            self._w("lblNumberQuestionText").setText(
                f"What is the 7-bit binary form of {self.number_data.decimal_value} "
                f"(the character '{self.number_data.character}')?"
            )

        self._w("lblNumberAttempts").setText(f"Attempts remaining: {self.number_attempts_left}")
        self._set_feedback("lblNumberFeedback", "")
        self._w("txtNumberAnswer").clear()
        self._w("txtNumberAnswer").setEnabled(True)
        self.goto("page_number_question")

    def _submit_number_answer(self) -> None:
        raw = self._w("txtNumberAnswer").text().strip()

        if self.number_kind == "binary":
            try:
                value = int(raw)
            except ValueError:
                self._set_feedback("lblNumberFeedback", "Please enter a whole number.", "warning")
                return
            correct = value == self.number_data.decimal_value
            reveal = str(self.number_data.decimal_value)
        else:
            if not is_valid_binary_answer(raw):
                self._set_feedback("lblNumberFeedback", "Please enter exactly 7 binary digits (0/1).", "warning")
                return
            correct = raw == self.number_data.binary_value
            reveal = self.number_data.binary_value

        if correct:
            self._set_feedback("lblNumberFeedback", "Correct!", "success")
            self.sound.play("correct")
            self._w("txtNumberAnswer").setEnabled(False)
            QTimer.singleShot(800, lambda: self.goto("page_number_practice_menu"))
            return

        self.number_attempts_left -= 1
        if self.number_attempts_left <= 0:
            self._set_feedback("lblNumberFeedback", f"Out of attempts - the answer was {reveal}.", "error")
            self.sound.play("fail")
            self._w("txtNumberAnswer").setEnabled(False)
            QTimer.singleShot(1400, lambda: self.goto("page_number_practice_menu"))
        else:
            self._w("lblNumberAttempts").setText(f"Attempts remaining: {self.number_attempts_left}")
            self._set_feedback("lblNumberFeedback", "Incorrect, try again.", "error")
            self.sound.play("wrong")
            self._w("txtNumberAnswer").clear()

    # -- Admin dashboard -----------------------------------------------------------

    def _admin_view_leaderboard(self) -> None:
        self._show_leaderboard(self.leaderboard.all(), "FULL LEADERBOARD (ADMIN)", "page_admin_dashboard")

    def _admin_view_accounts(self) -> None:
        usernames = self.accounts.list_usernames()
        table = self._w("tblAdminAccounts")
        table.setRowCount(len(usernames))
        for row, name in enumerate(usernames):
            table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            table.setItem(row, 1, QTableWidgetItem(name))
        self.goto("page_admin_accounts")

    def _admin_open_reset_confirm(self) -> None:
        self._w("txtResetConfirm").clear()
        self._set_feedback("lblResetFeedback", "")
        self.goto("page_admin_reset_confirm")

    def _admin_confirm_reset(self) -> None:
        if self._w("txtResetConfirm").text().strip().upper() == "YES":
            self.leaderboard.clear()
            self._set_feedback("lblResetFeedback", "Leaderboard cleared.", "success")
            self.sound.play("correct")
            QTimer.singleShot(800, lambda: self.goto("page_admin_dashboard"))
        else:
            self._set_feedback("lblResetFeedback", "Please type YES to confirm, or press Cancel.", "warning")

    def _admin_back_to_main(self) -> None:
        self.admin_authenticated = False
        self.goto("page_main_menu")

    # -- Admin dashboard: reports & charts --------------------------------------------

    def _open_admin_reports(self) -> None:
        entries = self.leaderboard.all()
        stats = reports.compute_stats(entries)
        self._render_reports_summary(stats)
        self._render_reports_charts(stats)
        self._set_feedback("lblReportStatus", "")
        self.goto("page_admin_reports")

    def _render_reports_summary(self, stats: reports.LeaderboardStats) -> None:
        lines = [
            "# Leaderboard Statistics",
            f"**Registered accounts:** {self.accounts.account_count()}",
            f"**Completed challenge runs:** {stats.total_games}",
        ]
        if stats.total_games:
            lines.append(f"**Average score:** {stats.average_score:.1f}")
            lines.append(f"**Highest score:** {stats.highest_score} (by {stats.top_player})")
        else:
            lines.append("_No completed runs yet - play a challenge to see stats here._")
        self._w("txtReportsSummary").setMarkdown("\n\n".join(lines))

    def _render_reports_charts(self, stats: reports.LeaderboardStats) -> None:
        self._build_bar_chart(stats)
        self._build_pie_chart(stats)

    def _clear_container(self, container: QWidget) -> None:
        layout = container.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _style_chart(self, chart: QChart) -> None:
        chart.setBackgroundVisible(True)
        chart.setBackgroundBrush(QColor(theme.PANEL))
        chart.setBackgroundPen(QColor(theme.PANEL_LIGHT))
        chart.legend().setVisible(False)
        chart.setTitleBrush(QColor(theme.WHITE))

    def _style_chart_view(self, chart_view: QChartView) -> None:
        from PySide6.QtGui import QBrush
        chart_view.setBackgroundBrush(QBrush(QColor(theme.PANEL)))
        chart_view.setStyleSheet("border: none;")

    def _style_axis(self, axis) -> None:
        axis.setLabelsColor(QColor(theme.WHITE))
        axis.setLinePen(QColor(theme.PANEL_LIGHT))
        axis.setGridLineColor(QColor(theme.PANEL_LIGHT))

    def _build_bar_chart(self, stats: reports.LeaderboardStats) -> None:
        container = self._w("chartContainerBar")
        self._clear_container(container)

        categories = list(stats.average_score_by_difficulty.keys()) or ["No data"]
        values = list(stats.average_score_by_difficulty.values()) or [0]

        bar_set = QBarSet("Average Score")
        for v in values:
            bar_set.append(v)
        bar_set.setColor(QColor(theme.RED))

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Average Score by Difficulty")
        self._style_chart(chart)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self._style_axis(axis_x)
        self._style_axis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._style_chart_view(chart_view)
        container.layout().addWidget(chart_view)

    def _build_pie_chart(self, stats: reports.LeaderboardStats) -> None:
        container = self._w("chartContainerPie")
        self._clear_container(container)

        series = QPieSeries()
        if stats.count_by_difficulty:
            for diff, count in stats.count_by_difficulty.items():
                series.append(f"{diff} ({count})", count)
        else:
            series.append("No data", 1)

        palette = [theme.RED, theme.YELLOW, theme.GREEN, theme.GRAY]
        for i, sl in enumerate(series.slices()):
            sl.setBrush(QColor(palette[i % len(palette)]))
            sl.setLabelVisible(True)
            sl.setLabelColor(QColor(theme.WHITE))
            sl.setPen(QColor(theme.BLACK))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Runs by Difficulty")
        self._style_chart(chart)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._style_chart_view(chart_view)
        container.layout().addWidget(chart_view)

    def _export_pdf_report(self) -> None:
        entries = self.leaderboard.all()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = _REPORTS_DIR / f"leaderboard_report_{timestamp}.pdf"
        try:
            reports.generate_pdf_report(entries, self.accounts.account_count(), output_path)
            self._set_feedback("lblReportStatus", f"Report saved: {output_path}", "success")
            self.sound.play("correct")
        except Exception as exc:  # noqa: BLE001 - surfaced to the admin, not swallowed
            self._set_feedback("lblReportStatus", f"Failed to generate report: {exc}", "error")
            self.sound.play("wrong")


def main() -> None:
    import sys

    app = QApplication(sys.argv)
    window = load_main_window()
    controller = AppController(window)  # noqa: F841 - keeps AppController alive via closure/refs
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
