# Screenshots
![Image MainMenu](https://github.com/Mimaguel/logic-gate-academy/blob/c88118e8b1fdfcd4fe5173d66999870789f8c267/assets/Screenshots/1.png)
![Image Login](https://github.com/Mimaguel/logic-gate-academy/blob/559b9e0c9e0210a73735c3f5ba57d18ae9fcbc17/assets/Screenshots/2.png)
![Image BonusRound](https://github.com/Mimaguel/logic-gate-academy/blob/559b9e0c9e0210a73735c3f5ba57d18ae9fcbc17/assets/Screenshots/3.png)

# Logic Gate Academy
A desktop game that teaches **logic gates** (all seven: AND, OR, NOT, XOR,
NAND, NOR, XNOR), **binary numbers**, and **ASCII encoding**. Built with
**PySide6**, laid out in a **Qt Designer-editable `.ui` file**, styled with
an original bold red/black/white theme, animated, sound-effected, and
backed by an encrypted local database.

> **On the visual style:** the theme is an *original* design inspired by
> the general conventions of bold, high-contrast action-game UI (thick
> color-blocking, condensed display type, sharp panels, neon-red glow) -
> it is not a reproduction of any specific copyrighted game's assets.

## Getting started

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.10+. Dependencies: `PySide6` (GUI, charts, sound, fonts),
`cryptography` (encrypted storage), `fpdf2` (PDF report export).

## What's in this version

- **All 7 logic gates**, unlocked progressively: AND/OR/NOT at every
  difficulty, XOR/NAND join at Medium, NOR/XNOR join at Hard.
- **A full visual theme** - custom fonts (Bebas Neue + Rajdhani, both
  open-license via Google Fonts), a red/black/white palette, and small
  animations (page fade transitions, a pulsing glow on the main title,
  pop-in feedback messages).
- **Original sound effects** - click, navigate, correct, wrong, victory,
  and failure cues, all synthesized tones (see `generate_sounds.py`), not
  external audio samples. A mute toggle lives in the top-right corner.
- **A real local database** - accounts and leaderboard scores now persist
  between runs, stored as CSV (see `game/storage.py`) and encrypted at
  rest. Passwords are hashed (PBKDF2 + per-user salt), never stored in
  plain text.
- **Admin Reports & Charts** - a new Admin Dashboard screen with a bar
  chart (average score by difficulty) and pie chart (runs by difficulty),
  plus a one-click PDF report export.

## Editing the UI in Qt Designer

Everything you see on screen is defined in **`gui/main_window.ui`** - a
completely standard Qt Designer file. To change how any screen looks:

1. Open `gui/main_window.ui` in Qt Designer or Qt Creator.
2. Move things around, restyle, change text - whatever you want.
3. Save the file, then run `python main.py` again. No compile step - the
   app loads the `.ui` file fresh every time it starts.

**The one rule:** don't rename existing objectNames the Python code
depends on (see the [objectName reference](#objectname-reference) below)
unless you also update the matching name in `gui/main_window.py`. Adding
brand-new decorative widgets is always safe - the code only looks for the
names it needs.

Colors, fonts, and all styling live separately in **`gui/theme.py`** as a
QSS stylesheet string - edit that file to change the palette without
touching the `.ui` layout at all. Buttons and labels are tagged with a
custom `role` property (e.g. `role="primary"`, `role="danger"`) that the
stylesheet targets - add a new widget with an existing role and it
automatically picks up that style.

## Project structure

```
logic_gate_academy/
├── main.py
├── requirements.txt
├── generate_sounds.py        # regenerates assets/sounds/*.wav if you want different tones
├── generate_textures.py      # regenerates assets/images/*.png texture tiles
├── data/
│   ├── accounts.enc           # encrypted accounts database (CSV inside)
│   ├── accounts.key
│   ├── leaderboard.enc        # encrypted leaderboard database (CSV inside)
│   └── leaderboard.key
├── reports/                  # PDF reports land here when an admin exports one
├── assets/
│   ├── fonts/                 # Bebas Neue + Rajdhani (SIL Open Font License, via Google Fonts)
│   ├── sounds/                 # synthesized .wav UI sound effects
│   └── images/                  # small generated texture tiles
├── game/                     # MODEL layer - pure logic, ZERO Qt imports
│   ├── gates.py                # GateType enum (all 7) + LogicGate evaluation rules
│   ├── encoding.py              # binary <-> decimal <-> ASCII helpers
│   ├── challenges.py             # question generators, difficulty gate-pools, game-balance constants
│   ├── security.py                # PBKDF2 password hashing (stdlib only)
│   ├── storage.py                  # EncryptedCSVStore - generic encrypted-CSV persistence
│   ├── accounts.py                  # Player + AccountManager (persistent, hashed passwords)
│   ├── leaderboard.py                # ScoreEntry + Leaderboard (persistent, encrypted CSV)
│   ├── reports.py                     # leaderboard statistics + PDF report generation
│   ├── admin_auth.py                   # admin password check
│   └── content.py                       # tutorial pages + explanation text (Markdown)
└── gui/                      # VIEW + CONTROLLER layer - all the Qt code
    ├── main_window.ui          # <-- open THIS in Qt Designer
    ├── main_window.py           # loads the .ui, wires widgets to game/ logic, builds charts
    ├── theme.py                  # color palette, font loader, QSS stylesheet
    ├── effects.py                 # QPropertyAnimation helpers (fade, pop-in, glow pulse)
    └── sound.py                    # SoundManager (QSoundEffect wrapper)
```

**Why `game/` has zero Qt imports:** every file in `game/` takes plain
arguments and returns plain data - none of them know a GUI exists. That's
what makes them independently testable, and it's why adding the whole
persistence/reporting layer didn't require touching a single line of
`gui/` beyond wiring new buttons.

## The database, in detail

Both accounts and the leaderboard are stored as **CSV, encrypted as a
whole with Fernet** (AES-128 + a tamper-evident signature) before
touching disk - see `game/storage.py`'s `EncryptedCSVStore`, which both
`AccountManager` and `Leaderboard` build on. You get the simplicity of
CSV as an underlying format and the privacy of encryption at rest,
together. A random key is generated once per store (`data/accounts.key`,
`data/leaderboard.key`); losing that key file makes the corresponding
`.enc` file unreadable (by the app or anyone else).

Passwords are **never stored in plain text**, encrypted or not: each
account gets a random salt and a PBKDF2-HMAC-SHA256 hash (100,000
iterations), verified with a constant-time comparison. See
`game/security.py`.

Guests remain intentionally ephemeral and are never written to disk - a
guest is meant to be a "just let me play" option, not a saved identity.

## Sound & animation

- **Sound**: `gui/sound.py`'s `SoundManager` plays short `.wav` cues
  (`assets/sounds/`) via `QSoundEffect`. Buttons play a sound automatically
  based on their `role` property - "ghost"-role (back/cancel) buttons get
  a softer `nav` cue, everything else gets a punchier `click`, layered
  with contextual result sounds (`correct`/`wrong`/`victory`/`fail`) at
  the moment those outcomes happen. Toggle mute with the speaker icon in
  the top banner.
- **Animation**: `gui/effects.py` provides `fade_in` (used on every page
  change), `pop_in` (feedback messages), and `glow_pulse` (the looping
  neon glow on the main menu's title). All built on
  `QPropertyAnimation` + `QGraphicsEffect`, since QSS alone has no concept
  of transitions.

## Admin Reports & Charts

Main Menu → Admin Dashboard → **Reports & Charts**. Shows:
- A text summary (registered accounts, completed runs, average/highest
  score) computed by `game/reports.compute_stats()`.
- A bar chart of average score per difficulty and a pie chart of run
  counts per difficulty, both built with `PySide6.QtCharts`.
- An **Export PDF Report** button that writes a formatted report to
  `reports/leaderboard_report_<timestamp>.pdf` via `game/reports.py`
  (built with `fpdf2`).

## Security scope (please read before deploying this anywhere real)

This is a learning project. To be upfront about what its security
features do and don't cover:

- Passwords are hashed with salt (PBKDF2-SHA256, 100k iterations) -
  reasonable for a learning project, but not the same as a
  production-grade, memory-hard KDF like bcrypt/argon2.
- Both databases are encrypted, but each key file lives in the same
  folder as the data it protects - this stops casual viewing, not
  someone with full filesystem access.
- The admin password defaults to `admin123` (`game/admin_auth.py`) -
  override it with an `ADMIN_PASSWORD` environment variable before
  running; don't rely on the default for anything you care about.
- None of `data/*.enc`, `data/*.key`, or `reports/*.pdf` should be
  committed to source control - the included `.gitignore` already
  excludes them.

## objectName reference

Everything below is what `gui/main_window.py` looks up by name. Anything
not listed is purely decorative and safe to add, remove, or restyle
freely in Qt Designer.

- **Persistent top banner** (shown on every page): `lblBrandTitle`, `lblBrandStatus`, `btnMuteToggle`, `topBanner`, `topBannerAccent`
- **page_main_menu**: `lblMainTitle`, `lblMainSubtitle`, `btnStartChallenge`, `btnViewLeaderboard`, `btnTutorial`, `btnLearningMode`, `btnAdminDashboard`, `btnQuit`
- **page_login_menu**: `btnCreateAccount`, `btnLoginExisting`, `btnPlayGuest`, `btnLoginBack`
- **page_credentials**: `lblCredTitle`, `lblUsername`, `txtUsername`, `txtPassword`, `lblConfirm`, `txtConfirmPassword`, `lblCredStatus`, `btnCredSubmit`, `btnCredBack`
- **page_difficulty**: `lblDifficultyTitle`, `btnDifficultyEasy`, `btnDifficultyMedium`, `btnDifficultyHard`, `btnDifficultyBack`
- **page_challenge**: `lblChallengeHeader`, `lblLives`, `txtQuestion`, `btnAnswer0`, `btnAnswer1`, `lblChallengeFeedback`, `btnChallengeQuit`
- **page_bonus_round**: `lblBonusTitle`, `lblBonusCode`, `tblBonusReference`, `txtBonusGuess`, `btnBonusSubmit`, `lblBonusFeedback`, `btnBonusContinue`
- **page_leaderboard**: `lblLeaderboardTitle`, `tblLeaderboard`, `btnLeaderboardBack`
- **page_tutorial**: `lblTutorialHeading`, `lblTutorialProgress`, `txtTutorialBody`, `btnTutorialBack`, `btnTutorialNext`, `btnTutorialFinish`
- **page_learning_menu**: `btnPracticeGates`, `btnPracticeNumbers`, `btnExplainGates`, `btnExplainBinary`, `btnExplainAscii`, `btnLearningBack`
- **page_number_practice_menu**: `btnBinaryToDecimal`, `btnAsciiToBinary`, `btnNumberPracticeBack`
- **page_number_question**: `lblNumberQuestionTitle`, `lblNumberAttempts`, `lblNumberQuestionText`, `txtNumberAnswer`, `btnNumberSubmit`, `lblNumberFeedback`, `btnNumberBack`
- **page_explain**: `lblExplainTitle`, `txtExplainBody`, `btnExplainBack`
- **page_admin_dashboard**: `btnAdminViewLeaderboard`, `btnAdminViewAccounts`, `btnAdminReports`, `btnAdminReset`, `btnAdminBack`
- **page_admin_accounts**: `tblAdminAccounts`, `btnAdminAccountsBack`
- **page_admin_reset_confirm**: `txtResetConfirm`, `btnResetConfirm`, `btnResetCancel`, `lblResetFeedback`
- **page_admin_reports**: `txtReportsSummary`, `chartContainerBar`, `chartContainerPie`, `lblReportStatus`, `btnAdminReportsBack`, `btnGenerateReport`

## Extending the game

- **New gate type:** add it to `GateType` in `game/gates.py` (evaluate
  logic + truth table + description), then add it to the right tier(s) in
  `GATES_BY_DIFFICULTY` in `game/challenges.py`.
- **Rebalance difficulty:** `GATES_BY_DIFFICULTY`, `POINTS_PER_ROUND`,
  `STARTING_LIVES`, `BONUS_POINTS` are all constants at the top of
  `game/challenges.py`.
- **New chart on the reports page:** add a stat to
  `game/reports.LeaderboardStats` / `compute_stats()`, then build a
  `QChart` from it in `gui/main_window.py` the same way
  `_build_bar_chart`/`_build_pie_chart` do.
- **Different sound/font:** replace files in `assets/sounds/` or
  `assets/fonts/` (keeping the same filenames), or edit
  `generate_sounds.py` / `gui/theme.py`'s `FONT_FILES` list to point at
  new ones.
