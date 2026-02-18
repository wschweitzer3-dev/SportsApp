#!/usr/bin/env python3
"""
Python Sports Simulator — Basketball League Edition
Uses only the Python standard library.

Run with:  python main.py
"""

import random
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Player:
    name: str
    position: str          # PG | SG | SF | PF | C
    rating: int            # 60-99 overall
    offense: int
    defense: int
    speed: int
    stamina: int
    # Season accumulators
    games_played: int = 0
    total_points: int = 0
    total_rebounds: int = 0
    total_assists: int = 0
    total_steals: int = 0
    total_blocks: int = 0

    @property
    def ppg(self) -> float:
        return self.total_points / max(1, self.games_played)

    @property
    def rpg(self) -> float:
        return self.total_rebounds / max(1, self.games_played)

    @property
    def apg(self) -> float:
        return self.total_assists / max(1, self.games_played)

    def reset_stats(self) -> None:
        self.games_played = 0
        self.total_points = 0
        self.total_rebounds = 0
        self.total_assists = 0
        self.total_steals = 0
        self.total_blocks = 0


@dataclass
class Team:
    name: str
    city: str
    players: List[Player] = field(default_factory=list)
    wins: int = 0
    losses: int = 0
    points_for: int = 0
    points_against: int = 0

    @property
    def full_name(self) -> str:
        return f"{self.city} {self.name}"

    @property
    def win_pct(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.0

    @property
    def team_rating(self) -> float:
        if not self.players:
            return 0.0
        return sum(p.rating for p in self.players) / len(self.players)

    def reset_record(self) -> None:
        self.wins = 0
        self.losses = 0
        self.points_for = 0
        self.points_against = 0
        for p in self.players:
            p.reset_stats()


# ---------------------------------------------------------------------------
# Game simulation
# ---------------------------------------------------------------------------

class GameSimulator:
    """Simulates individual basketball games possession by possession."""

    POSSESSIONS_PER_QUARTER = 24
    POSSESSIONS_OT = 8

    def simulate_game(
        self,
        home: Team,
        away: Team,
        verbose: bool = False,
    ) -> Tuple[int, int, Dict[str, Dict[str, int]]]:
        """
        Returns (home_score, away_score, box_score_dict).
        box_score_dict maps player_name -> {stat: value}.
        """
        stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        home_score = 0
        away_score = 0

        for qtr in range(1, 5):
            h_q, a_q = self._simulate_period(home, away, self.POSSESSIONS_PER_QUARTER, stats)
            home_score += h_q
            away_score += a_q
            if verbose:
                print(f"    Q{qtr}: {home.full_name} {home_score} — {away_score} {away.full_name}")

        # Overtime periods until someone leads
        ot = 0
        while home_score == away_score:
            ot += 1
            h_ot, a_ot = self._simulate_period(home, away, self.POSSESSIONS_OT, stats)
            home_score += h_ot
            away_score += a_ot
            if verbose:
                print(f"    OT{ot}: {home.full_name} {home_score} — {away_score} {away.full_name}")

        return home_score, away_score, dict(stats)

    def _simulate_period(
        self,
        home: Team,
        away: Team,
        possessions: int,
        stats: Dict,
    ) -> Tuple[int, int]:
        home_pts = 0
        away_pts = 0
        for _ in range(possessions):
            home_pts += self._possession(home, away.team_rating, stats)
            away_pts += self._possession(away, home.team_rating, stats)
        return home_pts, away_pts

    def _possession(self, team: Team, opp_rating: float, stats: Dict) -> int:
        if not team.players:
            return 0

        # Shooter selected weighted by offensive rating
        shooter = random.choices(team.players, weights=[p.offense for p in team.players], k=1)[0]

        rating_edge = shooter.offense - opp_rating * 0.80
        shot_prob = max(0.28, min(0.68, 0.44 + rating_edge * 0.0018))

        points = 0
        if random.random() < shot_prob:
            roll = random.random()
            if roll < 0.27:
                points = 3
            elif roll < 0.87:
                points = 2
            else:
                # And-one / foul shots
                points = sum(1 for _ in range(2) if random.random() < 0.76)

        stats[shooter.name]["points"] += points

        # Rebound (simple: random teammate)
        rebounder = random.choice(team.players)
        if random.random() < 0.42:
            stats[rebounder.name]["rebounds"] += 1

        # Assist on made field goals
        if points >= 2 and random.random() < 0.58:
            candidates = [p for p in team.players if p is not shooter]
            if candidates:
                stats[random.choice(candidates).name]["assists"] += 1

        # Steal (credited to defending team — tracked separately by caller if needed)
        if random.random() < 0.06:
            stats[random.choice(team.players).name]["steals"] += 1

        # Block
        if random.random() < 0.03:
            stats[random.choice(team.players).name]["blocks"] += 1

        return points


# ---------------------------------------------------------------------------
# League
# ---------------------------------------------------------------------------

class League:
    def __init__(self, teams: List[Team]) -> None:
        self.teams = teams
        self.simulator = GameSimulator()
        self.schedule: List[Tuple[Team, Team]] = []

    def generate_schedule(self, games_per_matchup: int = 2) -> None:
        self.schedule = []
        for i, t1 in enumerate(self.teams):
            for j, t2 in enumerate(self.teams):
                if i < j:
                    for _ in range(games_per_matchup):
                        # Alternate home/away each matchup
                        self.schedule.append((t1, t2))
                        self.schedule.append((t2, t1))
        random.shuffle(self.schedule)

    def simulate_season(self, show_progress: bool = True) -> None:
        total = len(self.schedule)
        for idx, (home, away) in enumerate(self.schedule):
            h_score, a_score, game_stats = self.simulator.simulate_game(home, away)

            home.points_for += h_score
            home.points_against += a_score
            away.points_for += a_score
            away.points_against += h_score

            if h_score > a_score:
                home.wins += 1
                away.losses += 1
            else:
                away.wins += 1
                home.losses += 1

            for team in (home, away):
                for player in team.players:
                    player.games_played += 1
                    ps = game_stats.get(player.name, {})
                    player.total_points   += ps.get("points",   0)
                    player.total_rebounds += ps.get("rebounds", 0)
                    player.total_assists  += ps.get("assists",  0)
                    player.total_steals   += ps.get("steals",   0)
                    player.total_blocks   += ps.get("blocks",   0)

            if show_progress and (idx + 1) % 50 == 0:
                print(f"    Progress: {idx + 1}/{total} games simulated...")

    def standings(self) -> List[Team]:
        return sorted(self.teams, key=lambda t: (-t.wins, -(t.points_for - t.points_against)))

    def stat_leaders(self, stat: str, top_n: int = 5) -> List[Tuple[Player, float, Team]]:
        rows = []
        for team in self.teams:
            for p in team.players:
                if p.games_played < 5:
                    continue
                val = {"points": p.ppg, "rebounds": p.rpg, "assists": p.apg}.get(stat, 0.0)
                rows.append((p, val, team))
        return sorted(rows, key=lambda x: -x[1])[:top_n]


# ---------------------------------------------------------------------------
# Playoff bracket
# ---------------------------------------------------------------------------

class PlayoffSimulator:
    def __init__(self, game_sim: GameSimulator) -> None:
        self.game_sim = game_sim

    def simulate_series(
        self,
        team1: Team,
        team2: Team,
        best_of: int = 7,
        verbose: bool = True,
    ) -> Team:
        needed = best_of // 2 + 1
        wins: Dict[str, int] = {team1.full_name: 0, team2.full_name: 0}
        game_num = 0

        while wins[team1.full_name] < needed and wins[team2.full_name] < needed:
            game_num += 1
            home, away = (team1, team2) if game_num % 2 == 1 else (team2, team1)
            h_score, a_score, _ = self.game_sim.simulate_game(home, away)
            winner_team = home if h_score > a_score else away
            wins[winner_team.full_name] += 1

            if verbose:
                w1 = wins[team1.full_name]
                w2 = wins[team2.full_name]
                result = f"{home.full_name} {h_score}–{a_score} {away.full_name}"
                series = f"Series: {team1.city} {w1}–{w2} {team2.city}"
                print(f"      G{game_num}: {result}  |  {series}")

        winner = team1 if wins[team1.full_name] >= needed else team2
        w1, w2 = wins[team1.full_name], wins[team2.full_name]
        if verbose:
            print(f"      >> {winner.full_name} wins {max(w1, w2)}–{min(w1, w2)} <<")
        return winner

    def run_bracket(self, seeds: List[Team]) -> Team:
        """
        Single-elimination bracket.  len(seeds) must be a power of two.
        Seeds are matched 1 vs 8, 2 vs 7, etc.
        """
        round_names = {1: "First Round", 2: "Conference Semifinals",
                       3: "Conference Finals", 4: "Championship"}
        current = list(seeds)
        round_num = 0

        while len(current) > 1:
            round_num += 1
            label = round_names.get(round_num, f"Round {round_num}")
            _banner(label)
            next_round: List[Team] = []
            half = len(current) // 2
            for i in range(half):
                t1 = current[i]
                t2 = current[len(current) - 1 - i]
                seed1, seed2 = i + 1, len(current) - i
                print(f"\n    #{seed1} {t1.full_name}  vs  #{seed2} {t2.full_name}")
                next_round.append(self.simulate_series(t1, t2, best_of=7, verbose=True))
            current = next_round

        return current[0]


# ---------------------------------------------------------------------------
# Player / team generation
# ---------------------------------------------------------------------------

_FIRST_NAMES = [
    "James", "Michael", "Kevin", "LeBron", "Steph", "Chris", "Anthony",
    "Kyrie", "Russell", "Giannis", "Joel", "Nikola", "Luka", "Jayson",
    "Damian", "Devin", "Trae", "Zion", "Donovan", "Ja", "Victor", "Cade",
    "Karl", "Paul", "Jimmy", "Pascal", "Jordan", "Marcus", "Tyrese", "Jalen",
    "Miles", "Terry", "Andre", "Draymond", "Kawhi", "Bradley", "Evan", "OG",
]

_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
    "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris",
    "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark",
    "Rodriguez", "Lewis", "Lee", "Walker", "Hall", "Young", "Allen",
    "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson", "Hill",
    "Carter", "Mitchell", "Perez", "Roberts", "Turner", "Phillips",
]

_TEAMS = [
    ("Lakers",    "Los Angeles"),  ("Celtics",   "Boston"),
    ("Warriors",  "Golden State"), ("Bulls",     "Chicago"),
    ("Heat",      "Miami"),        ("Nets",      "Brooklyn"),
    ("Bucks",     "Milwaukee"),    ("76ers",     "Philadelphia"),
    ("Suns",      "Phoenix"),      ("Nuggets",   "Denver"),
    ("Mavericks", "Dallas"),       ("Clippers",  "LA"),
    ("Knicks",    "New York"),     ("Raptors",   "Toronto"),
    ("Thunder",   "Oklahoma City"),("Spurs",     "San Antonio"),
]

_POS_TENDENCIES = {
    "PG": {"off": +6,  "def":  0, "spd": +8},
    "SG": {"off": +8,  "def": +2, "spd": +5},
    "SF": {"off": +4,  "def": +4, "spd": +2},
    "PF": {"off": +2,  "def": +7, "spd":  0},
    "C":  {"off": -2,  "def": +9, "spd": -5},
}


def _make_player(position: str, star: bool = False, solid: bool = False) -> Player:
    used = set()
    while True:
        name = f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"
        if name not in used:
            used.add(name)
            break

    if star:
        rating = random.randint(85, 99)
    elif solid:
        rating = random.randint(75, 84)
    else:
        rating = random.randint(60, 74)

    t = _POS_TENDENCIES[position]
    base = rating - 12

    def stat(bonus: int) -> int:
        return max(40, min(99, base + bonus + random.randint(-5, 14)))

    return Player(
        name=name,
        position=position,
        rating=rating,
        offense=stat(t["off"]),
        defense=stat(t["def"]),
        speed=stat(t["spd"]),
        stamina=random.randint(70, 95),
    )


def _make_team(name: str, city: str) -> Team:
    team = Team(name=name, city=city)
    for pos in ("PG", "SG", "SF", "PF", "C"):
        # Franchise player: 20 % chance of star
        roll = random.random()
        team.players.append(_make_player(pos, star=roll < 0.20, solid=0.20 <= roll < 0.50))
        # Backup: rarely solid
        team.players.append(_make_player(pos, star=False, solid=random.random() < 0.15))
    return team


def generate_league() -> List[Team]:
    return [_make_team(name, city) for name, city in _TEAMS]


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _banner(title: str, width: int = 62) -> None:
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def _print_standings(league: League) -> None:
    _banner("LEAGUE STANDINGS")
    header = f"  {'#':<3} {'Team':<30} {'W':>4} {'L':>4} {'PCT':>6}  {'PF':>5} {'PA':>5} {'DIFF':>6}"
    print(header)
    print("  " + "-" * 58)
    for rank, team in enumerate(league.standings(), 1):
        diff = team.points_for - team.points_against
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        print(
            f"  {rank:<3} {team.full_name:<30} {team.wins:>4} {team.losses:>4}"
            f" {team.win_pct:>6.3f}  {team.points_for:>5} {team.points_against:>5} {diff_str:>6}"
        )


def _print_stat_leaders(league: League) -> None:
    _banner("STATISTICAL LEADERS")
    categories = [
        ("Points",   "points",   "PPG"),
        ("Rebounds", "rebounds", "RPG"),
        ("Assists",  "assists",  "APG"),
    ]
    for cat_name, key, label in categories:
        print(f"\n  Top 5 — {cat_name} Per Game")
        print(f"  {'Player':<26} {'Team':<22} {'GP':>3}  {label:>5}")
        print("  " + "-" * 54)
        for player, val, team in league.stat_leaders(key):
            print(f"  {player.name:<26} {team.city:<22} {player.games_played:>3}  {val:>5.1f}")


def _print_box_score(
    home: Team,
    away: Team,
    h_score: int,
    a_score: int,
    stats: Dict[str, Dict[str, int]],
) -> None:
    print(f"\n  FINAL SCORE")
    print(f"  {'Team':<32} {'PTS':>4}")
    print("  " + "-" * 38)
    for team, score in ((home, h_score), (away, a_score)):
        marker = " *" if score > (a_score if team is home else h_score) else ""
        print(f"  {team.full_name:<32} {score:>4}{marker}")

    print(f"\n  BOX SCORE")
    print(f"  {'Player':<26} {'POS':>3} {'PTS':>4} {'REB':>4} {'AST':>4} {'STL':>4} {'BLK':>4}")
    print("  " + "-" * 50)
    for team in (home, away):
        print(f"\n  — {team.full_name} —")
        for p in sorted(team.players, key=lambda x: stats.get(x.name, {}).get("points", 0), reverse=True):
            ps = stats.get(p.name, {})
            print(
                f"  {p.name:<26} {p.position:>3}"
                f" {ps.get('points',0):>4} {ps.get('rebounds',0):>4}"
                f" {ps.get('assists',0):>4} {ps.get('steals',0):>4}"
                f" {ps.get('blocks',0):>4}"
            )


# ---------------------------------------------------------------------------
# Mode: single game
# ---------------------------------------------------------------------------

def _mode_single_game(teams: List[Team]) -> None:
    _banner("SINGLE GAME SIMULATION")
    print("\n  Available Teams:\n")
    for i, t in enumerate(teams, 1):
        print(f"    {i:>2}. {t.full_name:<32}  Rating: {t.team_rating:.1f}")

    def pick(label: str, exclude: int = -1) -> int:
        while True:
            raw = input(f"\n  Select {label} team number: ").strip()
            if not raw.isdigit():
                print("  Please enter a number.")
                continue
            idx = int(raw) - 1
            if idx < 0 or idx >= len(teams):
                print(f"  Enter a number from 1 to {len(teams)}.")
            elif idx == exclude:
                print("  Home and away teams must be different.")
            else:
                return idx

    h_idx = pick("HOME")
    a_idx = pick("AWAY", exclude=h_idx)
    home, away = teams[h_idx], teams[a_idx]

    print(f"\n  Simulating: {home.full_name} (home)  vs  {away.full_name} (away)\n")
    sim = GameSimulator()
    h_score, a_score, box = sim.simulate_game(home, away, verbose=True)
    _print_box_score(home, away, h_score, a_score, box)


# ---------------------------------------------------------------------------
# Mode: full season + playoffs
# ---------------------------------------------------------------------------

def _mode_full_season(teams: List[Team]) -> None:
    _banner("FULL SEASON SIMULATION")

    for t in teams:
        t.reset_record()

    league = League(teams)
    league.generate_schedule(games_per_matchup=2)
    total = len(league.schedule)
    print(f"\n  {len(teams)} teams  |  {total} regular-season games")
    print("  Simulating...")
    league.simulate_season(show_progress=True)
    print("  Regular season complete.\n")

    _print_standings(league)
    _print_stat_leaders(league)

    # Playoffs — top 8 seeds
    seeds = league.standings()[:8]
    _banner("PLAYOFFS — TOP 8 SEEDS")
    for i, t in enumerate(seeds, 1):
        print(f"  #{i}  {t.full_name:<32}  {t.wins}-{t.losses}")

    input("\n  Press Enter to simulate the playoffs...")

    playoff_sim = PlayoffSimulator(league.simulator)
    champion = playoff_sim.run_bracket(seeds)

    _banner("CHAMPION")
    print(f"\n  *** {champion.full_name.upper()} ARE CHAMPIONS! ***\n")


# ---------------------------------------------------------------------------
# Mode: view rosters
# ---------------------------------------------------------------------------

def _mode_rosters(teams: List[Team]) -> None:
    _banner("TEAM ROSTERS")
    for team in sorted(teams, key=lambda t: t.full_name):
        print(f"\n  {team.full_name}  (Avg Rating: {team.team_rating:.1f})")
        print(f"  {'Player':<26} {'POS':>3} {'OVR':>4} {'OFF':>4} {'DEF':>4} {'SPD':>4} {'STA':>4}")
        print("  " + "-" * 50)
        for p in team.players:
            print(
                f"  {p.name:<26} {p.position:>3}"
                f" {p.rating:>4} {p.offense:>4} {p.defense:>4}"
                f" {p.speed:>4} {p.stamina:>4}"
            )


# ---------------------------------------------------------------------------
# Mode: quick demo (no user input required)
# ---------------------------------------------------------------------------

def _mode_quick_demo(teams: List[Team]) -> None:
    _banner("QUICK DEMO — 1 GAME + MINI SEASON")

    # Pick two random teams and simulate a game
    home, away = random.sample(teams, 2)
    print(f"\n  Demo game: {home.full_name} vs {away.full_name}\n")
    sim = GameSimulator()
    h_score, a_score, box = sim.simulate_game(home, away, verbose=True)
    _print_box_score(home, away, h_score, a_score, box)

    # Mini 4-team season
    print("\n\n  Running mini 4-team season...")
    mini_teams = random.sample(teams, 4)
    for t in mini_teams:
        t.reset_record()
    mini_league = League(mini_teams)
    mini_league.generate_schedule(games_per_matchup=1)
    mini_league.simulate_season(show_progress=False)
    _print_standings(mini_league)
    _print_stat_leaders(mini_league)

    # 4-team playoff
    _banner("MINI PLAYOFFS")
    seeds = mini_league.standings()
    playoff_sim = PlayoffSimulator(mini_league.simulator)
    champion = playoff_sim.run_bracket(seeds)
    _banner("DEMO CHAMPION")
    print(f"\n  *** {champion.full_name.upper()} WIN THE MINI TITLE! ***\n")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    _banner("PYTHON SPORTS SIMULATOR  —  Basketball League Edition")
    print("\n  Standard library only. No third-party packages required.")
    print("  Generating league...")
    teams = generate_league()
    print(f"  {len(teams)} teams ready.\n")

    MENU = [
        ("1", "Simulate a single game",        lambda: _mode_single_game(teams)),
        ("2", "Run full season + playoffs",     lambda: _mode_full_season(teams)),
        ("3", "View team rosters",              lambda: _mode_rosters(teams)),
        ("4", "Quick demo (no input needed)",   lambda: _mode_quick_demo(teams)),
        ("5", "Regenerate league",              None),
        ("6", "Exit",                           None),
    ]

    while True:
        _banner("MAIN MENU")
        for key, label, _ in MENU:
            print(f"  {key}. {label}")

        choice = input("\n  Enter choice (1–6): ").strip()

        if choice == "1":
            _mode_single_game(teams)
            input("\n  Press Enter to return to menu...")
        elif choice == "2":
            _mode_full_season(teams)
            input("\n  Press Enter to return to menu...")
        elif choice == "3":
            _mode_rosters(teams)
            input("\n  Press Enter to return to menu...")
        elif choice == "4":
            _mode_quick_demo(teams)
            input("\n  Press Enter to return to menu...")
        elif choice == "5":
            teams = generate_league()
            print(f"\n  League regenerated — {len(teams)} new teams ready.")
            input("  Press Enter to continue...")
        elif choice == "6":
            print("\n  Thanks for playing!\n")
            sys.exit(0)
        else:
            print("  Invalid choice. Please enter 1–6.")


if __name__ == "__main__":
    main()
