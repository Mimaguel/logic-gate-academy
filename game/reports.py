"""
game/reports.py
=================
Statistics over leaderboard data (pure, no UI), plus a PDF export built
with fpdf2. The Admin Dashboard's charts are built from `compute_stats()`
in the GUI layer (QtCharts needs actual Qt objects, so that part can't
live here) - but the numbers themselves are computed here so they're
testable without a running Qt application.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .leaderboard import ScoreEntry


@dataclass
class LeaderboardStats:
    total_games: int
    average_score: float
    highest_score: int
    top_player: Optional[str]
    count_by_difficulty: Dict[str, int]
    average_score_by_difficulty: Dict[str, float]


def compute_stats(entries: List[ScoreEntry]) -> LeaderboardStats:
    if not entries:
        return LeaderboardStats(0, 0.0, 0, None, {}, {})

    total_games = len(entries)
    average_score = sum(e.score for e in entries) / total_games
    best = max(entries, key=lambda e: e.score)

    count_by_difficulty: Dict[str, int] = {}
    sum_by_difficulty: Dict[str, int] = {}
    for e in entries:
        count_by_difficulty[e.difficulty] = count_by_difficulty.get(e.difficulty, 0) + 1
        sum_by_difficulty[e.difficulty] = sum_by_difficulty.get(e.difficulty, 0) + e.score
    average_by_difficulty = {
        d: sum_by_difficulty[d] / count_by_difficulty[d] for d in count_by_difficulty
    }

    return LeaderboardStats(
        total_games=total_games,
        average_score=average_score,
        highest_score=best.score,
        top_player=best.username,
        count_by_difficulty=count_by_difficulty,
        average_score_by_difficulty=average_by_difficulty,
    )


def generate_pdf_report(entries: List[ScoreEntry], account_count: int, output_path: Path) -> Path:
    """Render a one-page-plus PDF summary of the leaderboard and save it
    to `output_path`. Returns the path for convenience."""
    from fpdf import FPDF

    stats = compute_stats(entries)
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Logic Gate Academy - Leaderboard Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 8, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Total registered accounts: {account_count}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Total completed challenge runs: {stats.total_games}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Average score: {stats.average_score:.1f}", new_x="LMARGIN", new_y="NEXT")
    top_line = f"Highest score: {stats.highest_score} (by {stats.top_player})" if stats.top_player else "Highest score: -"
    pdf.cell(0, 7, top_line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "By Difficulty", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    if stats.count_by_difficulty:
        for diff, count in stats.count_by_difficulty.items():
            avg = stats.average_score_by_difficulty[diff]
            pdf.cell(0, 7, f"{diff}: {count} run(s), average score {avg:.1f}", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 7, "No completed runs yet.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Full Leaderboard", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 15, 45)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(15, 7, "Rank", border=1, fill=True)
    pdf.cell(75, 7, "Player", border=1, fill=True)
    pdf.cell(35, 7, "Score", border=1, fill=True)
    pdf.cell(40, 7, "Difficulty", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    for i, e in enumerate(entries, start=1):
        pdf.cell(15, 7, str(i), border=1)
        pdf.cell(75, 7, e.username, border=1)
        pdf.cell(35, 7, str(e.score), border=1)
        pdf.cell(40, 7, e.difficulty, border=1, new_x="LMARGIN", new_y="NEXT")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path
