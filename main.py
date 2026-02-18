#!/usr/bin/env python3
"""
Python Sports Simulator
A complete NBA-style basketball season and playoff simulator.
Uses only Python standard library.
"""

import os
import random
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

# ── Name pools ────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "James", "Michael", "Kevin", "Anthony", "Steph", "Kobe", "Magic", "Larry",
    "Shaq", "Tim", "Dirk", "Hakeem", "Charles", "Karl", "John", "Scottie",
    "Allen", "Ray", "Dwyane", "Chris", "Paul", "Tony", "Manu", "Andre",
    "Marcus", "Tyler", "Jordan", "Jaylen", "Donovan", "Zion", "Luka",
    "Giannis", "Joel", "Nikola", "Kawhi", "Damian", "Bradley", "Kyle",
    "Jimmy", "Khris", "Pascal", "Bam", "Jamal", "Jayson", "Devin", "Shai",
    "Trae", "Ja", "LaMelo", "Evan", "Spencer", "Tyrese", "Franz", "Cade",
    "Jalen", "Paolo", "Victor", "Brandon", "Miles", "Obi", "Isaiah",
]

LAST_NAMES = [
    "Johnson", "Jordan", "Durant", "Davis", "Curry", "Bryant", "Bird",
    "ONeal", "Duncan", "Nowitzki", "Olajuwon", "Barkley", "Malone",
    "Stockton", "Pippen", "Iverson", "Allen", "Wade", "Paul", "Parker",
    "Ginobili", "Iguodala", "Smart", "Green", "Mitchell", "Williamson",
    "Doncic", "Antetokounmpo", "Embiid", "Jokic", "Leonard", "Lillard",
    "Beal", "Butler", "Middleton", "Siakam", "Adebayo", "Murray", "Brown",
    "Tatum", "Irving", "Harden", "Westbrook", "George", "Young", "Morant",
    "Ball", "Holiday", "Maxey", "Wagner", "Cunningham", "Barnes", "Bridges",
    "Herro", "White", "Thomas", "Walker", "Thompson", "Robinson", "Carter",
]

# ── Teams ─────────────────────────────────────────────────────────────────────

EAST_TEAMS = [
    ("Atlanta Hawks",        "ATL"),
    ("Boston Celtics",       "BOS"),
    ("Brooklyn Nets",        "BKN"),
    ("Charlotte Hornets",    "CHA"),
    ("Chicago Bulls",        "CHI"),
    ("Cleveland Cavaliers",  "CLE"),
    ("Detroit Pistons",      "DET"),
    ("Indiana Pacers",       "IND"),
    ("Miami Heat",           "MIA"),
    ("Milwaukee Bucks",      "MIL"),
    ("New York Knicks",      "NYK"),
    ("Orlando Magic",        "ORL"),
    ("Philadelphia 76ers",   "PHI"),
    ("Toronto Raptors",      "TOR"),
    ("Washington Wizards",   "WAS"),
]

WEST_TEAMS = [
    ("Dallas Mavericks",       "DAL"),
    ("Denver Nuggets",         "DEN"),
    ("Golden State Warriors",  "GSW"),
    ("Houston Rockets",        "HOU"),
    ("LA Clippers",            "LAC"),
    ("Los Angeles Lakers",     "LAL"),
    ("Memphis Grizzlies",      "MEM"),
    ("Minnesota Timberwolves", "MIN"),
    ("New Orleans Pelicans",   "NOP"),
    ("Oklahoma City Thunder",  "OKC"),
    ("Phoenix Suns",           "PHX"),
    ("Portland Trail Blazers", "POR"),
    ("Sacramento Kings",       "SAC"),
    ("San Antonio Spurs",      "SAS"),
    ("Utah Jazz",              "UTA"),
]

# Per-position skill biases
POS_BIAS = {
    "PG": {"shooting": 8,   "three": 6,   "passing": 20, "defense": 0,  "rebounding": -10, "athleticism": 5},
    "SG": {"shooting": 15,  "three": 12,  "passing": 2,  "defense": 2,  "rebounding": -5,  "athleticism": 8},
    "SF": {"shooting": 5,   "three": 2,   "passing": 0,  "defense": 8,  "rebounding": 5,   "athleticism": 10},
    "PF": {"shooting": -5,  "three": -10, "passing": -5, "defense": 12, "rebounding": 15,  "athleticism": 0},
    "C":  {"shooting": -15, "three": -20, "passing": -10,"defense": 15, "rebounding": 20,  "athleticism": -5},
}

ROSTER_SLOTS = ["PG","SG","SF","PF","C", "PG","SG","SF","PF","C", "SF","PF","C"]

WIDTH = 72


# ── Player ────────────────────────────────────────────────────────────────────

@dataclass
class Player:
    name: str
    position: str
    rating: int
    shooting: int
    three: int
    passing: int
    defense: int
    rebounding: int
    athleticism: int
    # per-game averages
    games: int = 0
    ppg: float = 0.0
    rpg: float = 0.0
    apg: float = 0.0
    fg_pct: float = 0.0
    three_pct: float = 0.0
    # accumulators
    _pts: int = field(default=0, repr=False)
    _reb: int = field(default=0, repr=False)
    _ast: int = field(default=0, repr=False)
    _fga: int = field(default=0, repr=False)
    _fgm: int = field(default=0, repr=False)
    _3pa: int = field(default=0, repr=False)
    _3pm: int = field(default=0, repr=False)

    def record_game(self, pts, reb, ast, fga, fgm, tpa, tpm):
        self.games += 1
        self._pts += pts; self._reb += reb; self._ast += ast
        self._fga += fga; self._fgm += fgm
        self._3pa += tpa; self._3pm += tpm
        g = self.games
        self.ppg = self._pts / g
        self.rpg = self._reb / g
        self.apg = self._ast / g
        self.fg_pct    = (self._fgm / self._fga * 100) if self._fga else 0.0
        self.three_pct = (self._3pm / self._3pa * 100) if self._3pa else 0.0


def generate_player(position):
    bias = POS_BIAS[position]
    base = random.randint(42, 78)
    def sk(b): return max(25, min(99, base + b + random.randint(-8, 8)))
    sh  = sk(bias["shooting"])
    th  = sk(bias["three"])
    pa  = sk(bias["passing"])
    de  = sk(bias["defense"])
    re  = sk(bias["rebounding"])
    at  = sk(bias["athleticism"])
    rating = (sh + th + pa + de + re + at) // 6
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    return Player(name=name, position=position, rating=rating,
                  shooting=sh, three=th, passing=pa,
                  defense=de, rebounding=re, athleticism=at)


# ── Team ──────────────────────────────────────────────────────────────────────

@dataclass
class Team:
    name: str
    abbr: str
    conference: str
    roster: List[Player] = field(default_factory=list)
    wins: int = 0
    losses: int = 0
    pf: float = 0.0
    pa: float = 0.0
    home_wins: int = 0
    home_losses: int = 0
    away_wins: int = 0
    away_losses: int = 0
    streak: int = 0
    _gp: int = field(default=0, repr=False)

    @property
    def win_pct(self):
        t = self.wins + self.losses
        return self.wins / t if t else 0.0

    @property
    def starters(self):
        return self.roster[:5]

    def record_result(self, scored, allowed, home):
        self._gp += 1
        self.pf = (self.pf * (self._gp - 1) + scored) / self._gp
        self.pa = (self.pa * (self._gp - 1) + allowed) / self._gp
        if scored > allowed:
            self.wins += 1
            self.streak = max(1, self.streak + 1)
            if home: self.home_wins += 1
            else:    self.away_wins += 1
        else:
            self.losses += 1
            self.streak = min(-1, self.streak - 1)
            if home: self.home_losses += 1
            else:    self.away_losses += 1


def build_team(name, abbr, conference):
    t = Team(name=name, abbr=abbr, conference=conference)
    t.roster = [generate_player(pos) for pos in ROSTER_SLOTS]
    return t


def build_all_teams():
    teams = []
    for name, abbr in EAST_TEAMS:
        teams.append(build_team(name, abbr, "East"))
    for name, abbr in WEST_TEAMS:
        teams.append(build_team(name, abbr, "West"))
    return teams


# ── Game Simulation ───────────────────────────────────────────────────────────

def _simulate_offense(offense, defense):
    players     = offense.starters
    opp_def_avg = statistics.mean(p.defense for p in defense.starters)

    box = {p.name: {"pts":0,"reb":0,"ast":0,"fga":0,"fgm":0,"tpa":0,"tpm":0}
           for p in offense.roster}

    total_pts   = 0
    possessions = random.randint(95, 110)

    for _ in range(possessions):
        ball_handler = random.choices(players, weights=[p.passing for p in players], k=1)[0]
        # Turnover rate: 10-18% based on passing skill
        if random.random() < max(0.08, 0.20 - ball_handler.passing / 700):
            continue  # turnover

        is_three = random.random() < (0.15 + ball_handler.three / 100 * 0.28)

        if random.random() < 0.60:
            shooter, passer = ball_handler, None
        else:
            shooter = random.choice(players)
            passer  = ball_handler if ball_handler is not shooter else None

        # Defense reduces shooting efficiency by up to 13 %
        def_factor = 1.0 - (opp_def_avg / 100.0) * 0.13

        if is_three:
            # skill 99 → ~41 %, skill 65 → ~36 %, skill 25 → ~30 %
            base_pct = 0.27 + (shooter.three / 100) * 0.14
        else:
            # skill 99 → ~62 %, skill 65 → ~56 %, skill 25 → ~48 %
            base_pct = 0.45 + (shooter.shooting / 100) * 0.17

        effective_pct = min(0.80, base_pct * def_factor)

        if is_three:
            box[shooter.name]["tpa"] += 1
        box[shooter.name]["fga"] += 1

        if random.random() < effective_pct:
            pts = 3 if is_three else 2
            if not is_three and random.random() < 0.14:  # and-one
                if random.random() < 0.75:
                    pts += 1
            total_pts += pts
            box[shooter.name]["pts"] += pts
            box[shooter.name]["fgm"] += 1
            if is_three:
                box[shooter.name]["tpm"] += 1
            if passer:
                box[passer.name]["ast"] += 1
        else:
            rebounder = random.choices(
                offense.roster,
                weights=[p.rebounding + random.randint(0, 15) for p in offense.roster], k=1
            )[0]
            box[rebounder.name]["reb"] += 1

    # Free throws: modelled as a game-wide pool (typical NBA ~18 FTA at ~75%)
    ft_skill = statistics.mean(p.shooting for p in players)
    ft_pct   = 0.62 + (ft_skill / 100) * 0.18   # range ~0.62–0.80
    ft_pts   = sum(1 for _ in range(random.randint(14, 22)) if random.random() < ft_pct)
    total_pts += ft_pts

    return total_pts, box


def simulate_game(home, away):
    home_pts, home_box = _simulate_offense(home, away)
    away_pts, away_box = _simulate_offense(away, home)

    home_pts += random.randint(2, 5)  # home-court advantage

    if home_pts == away_pts:          # overtime
        ot = random.randint(3, 12)
        if random.random() < 0.52: home_pts += ot
        else:                      away_pts += ot

    def record(team, box):
        for p in team.roster:
            b = box.get(p.name, {})
            p.record_game(b.get("pts",0), b.get("reb",0), b.get("ast",0),
                          b.get("fga",0), b.get("fgm",0), b.get("tpa",0), b.get("tpm",0))

    record(home, home_box)
    record(away, away_box)
    home.record_result(home_pts, away_pts, home=True)
    away.record_result(away_pts, home_pts, home=False)
    return home_pts, away_pts


# ── Season ────────────────────────────────────────────────────────────────────

def simulate_season(teams, games_per_team=82):
    schedule = [(h, a) for i, h in enumerate(teams) for j, a in enumerate(teams) if i != j]
    random.shuffle(schedule)
    schedule = schedule[: games_per_team * len(teams) // 2]

    total, bar_w = len(schedule), 42
    print(f"\n  Simulating {total} regular-season games ...\n")
    for idx, (home, away) in enumerate(schedule):
        simulate_game(home, away)
        pct    = (idx + 1) / total
        filled = int(bar_w * pct)
        print(f"\r  [{'#'*filled}{'-'*(bar_w-filled)}] {idx+1:>4}/{total}", end="", flush=True)
    print("\n\n  Regular season complete!")


# ── Playoffs ──────────────────────────────────────────────────────────────────

def simulate_series(a, b, n=7):
    needed = n // 2 + 1
    wa = wb = game = 0
    while wa < needed and wb < needed:
        game += 1
        home, away = (a, b) if game in (1, 2, 5, 7) else (b, a)
        hs, as_ = simulate_game(home, away)
        if hs > as_:
            if home is a: wa += 1
            else:         wb += 1
        else:
            if away is a: wa += 1
            else:         wb += 1
    return (a, b) if wa >= needed else (b, a)


def simulate_conference_playoffs(conf_teams, conf_name):
    seeds = sorted(conf_teams, key=lambda t: t.win_pct, reverse=True)[:8]
    print(f"\n  {conf_name.upper()} CONFERENCE SEEDS")
    _sep()
    for i, t in enumerate(seeds, 1):
        print(f"  {i:>2}. {t.name:<28} {t.wins}-{t.losses}")
    _sep()

    bracket    = list(seeds)
    rnd_names  = ["First Round", "Semifinals", "Conference Finals"]
    for rname in rnd_names:
        print(f"\n  -- {rname} --")
        n     = len(bracket)
        pairs = [(bracket[i], bracket[n-1-i]) for i in range(n // 2)]
        nxt   = []
        for a, b in pairs:
            winner, loser = simulate_series(a, b)
            print(f"     {winner.name} def. {loser.name}")
            nxt.append(winner)
        bracket = nxt
    return bracket[0]


def simulate_playoffs(teams):
    _header("PLAYOFFS")
    east = [t for t in teams if t.conference == "East"]
    west = [t for t in teams if t.conference == "West"]
    ec = simulate_conference_playoffs(east, "Eastern")
    wc = simulate_conference_playoffs(west, "Western")

    print(f"\n  {'='*60}")
    print(f"  NBA FINALS:  {ec.name}  vs  {wc.name}")
    print(f"  {'='*60}")

    champ, runner_up = simulate_series(ec, wc)
    print(f"\n  *** CHAMPION: {champ.name} ***")
    print(f"  Runner-up   : {runner_up.name}")
    mvp = max(champ.roster, key=lambda p: p.ppg)
    print(f"\n  Finals MVP  : {mvp.name} ({champ.abbr})")
    print(f"                {mvp.ppg:.1f} PPG / {mvp.rpg:.1f} RPG / {mvp.apg:.1f} APG")
    return champ


# ── Display helpers ───────────────────────────────────────────────────────────

def _sep(c="-"):  print("  " + c * WIDTH)
def _header(t):
    print(); print("  " + "=" * WIDTH); print(f"  {t:^{WIDTH}}"); print("  " + "=" * WIDTH)
def _clear():   os.system("cls" if os.name == "nt" else "clear")
def _pause():   input("\n  Press Enter to continue...")


def print_standings(teams):
    _header("STANDINGS")
    for conf in ("East", "West"):
        label = "EASTERN" if conf == "East" else "WESTERN"
        rows  = sorted([t for t in teams if t.conference == conf],
                       key=lambda t: t.win_pct, reverse=True)
        print(f"\n  {label} CONFERENCE")
        _sep()
        print(f"  {'#':<4} {'Team':<26} {'W':>4} {'L':>4}  {'PCT':>5}  "
              f"{'PF':>6}  {'PA':>6}  {'Home':>6}  {'Away':>6}  {'Strk':>4}")
        _sep()
        for i, t in enumerate(rows, 1):
            po   = "*" if i <= 8 else " "
            sign = "+" if t.streak > 0 else ""
            hw   = f"{t.home_wins}-{t.home_losses}"
            aw   = f"{t.away_wins}-{t.away_losses}"
            print(f"  {i:<3}{po} {t.name:<26} {t.wins:>4} {t.losses:>4}  "
                  f"{t.win_pct:.3f}  {t.pf:>6.1f}  {t.pa:>6.1f}  "
                  f"{hw:>6}  {aw:>6}  {sign}{t.streak:>3}")
        _sep()
        print("  * = Playoff position")


def print_stat_leaders(teams, attr, label, top_n=15):
    _header(f"{label} LEADERS")
    rows = [(p, t) for t in teams for p in t.roster if p.games >= 40]
    rows.sort(key=lambda x: getattr(x[0], attr), reverse=True)
    _sep()
    print(f"  {'#':<4} {'Player':<26} {'Team':<6} {'Pos':<5} {label:>8}")
    _sep()
    for i, (p, t) in enumerate(rows[:top_n], 1):
        print(f"  {i:<4} {p.name:<26} {t.abbr:<6} {p.position:<5} {getattr(p, attr):>8.1f}")
    _sep()


def print_team_roster(team):
    _header(f"{team.name}  ({team.abbr})  |  {team.wins}-{team.losses}")
    _sep()
    print(f"  {'Player':<26} {'Pos':<5} {'OVR':>4}  "
          f"{'PPG':>6}  {'RPG':>6}  {'APG':>6}  {'FG%':>6}  {'3P%':>6}")
    _sep()
    for i, p in enumerate(team.roster):
        tag = " (S)" if i < 5 else "    "
        print(f"  {p.name+tag:<26} {p.position:<5} {p.rating:>4}  "
              f"{p.ppg:>6.1f}  {p.rpg:>6.1f}  {p.apg:>6.1f}  "
              f"{p.fg_pct:>5.1f}%  {p.three_pct:>5.1f}%")
    _sep()
    print("  (S) = Starter")


def print_awards(teams):
    _header("SEASON AWARDS")
    eligible = [(p, t) for t in teams for p in t.roster if p.games >= 40]

    def leader(attr):
        return max(eligible, key=lambda x: getattr(x[0], attr))

    mvp_p, mvp_t = max(eligible, key=lambda x: x[0].ppg*1.5 + x[0].rpg*1.2 + x[0].apg*1.5)
    sc_p,  sc_t  = leader("ppg")
    rb_p,  rb_t  = leader("rpg")
    as_p,  as_t  = leader("apg")

    fg_eligible = [(p, t) for p, t in eligible if p._fga >= 300]
    fg_p, fg_t  = max(fg_eligible, key=lambda x: x[0].fg_pct) if fg_eligible else (None, None)

    best_team = max(teams, key=lambda t: t.win_pct)

    print(f"\n  MVP\n    {mvp_p.name} ({mvp_t.abbr}) — {mvp_p.ppg:.1f} PPG / {mvp_p.rpg:.1f} RPG / {mvp_p.apg:.1f} APG")
    print(f"\n  Scoring Champion\n    {sc_p.name} ({sc_t.abbr}) — {sc_p.ppg:.1f} PPG")
    print(f"\n  Rebounding Leader\n    {rb_p.name} ({rb_t.abbr}) — {rb_p.rpg:.1f} RPG")
    print(f"\n  Assists Leader\n    {as_p.name} ({as_t.abbr}) — {as_p.apg:.1f} APG")
    if fg_p:
        print(f"\n  Best FG% (min 300 FGA)\n    {fg_p.name} ({fg_t.abbr}) — {fg_p.fg_pct:.1f}%")
    print(f"\n  Best Record\n    {best_team.name} — {best_team.wins}-{best_team.losses} ({best_team.win_pct:.3f})")
    _sep()


def quick_matchup(teams):
    import copy
    _header("QUICK MATCHUP")
    srt = sorted(teams, key=lambda t: t.name)
    for i, t in enumerate(srt, 1):
        print(f"  [{i:>2}] {t.name:<30} ({t.abbr})  {t.wins}-{t.losses}")
    print()
    try:
        hi = int(input("  Select HOME team #: ").strip()) - 1
        ai = int(input("  Select AWAY team #: ").strip()) - 1
        if not (0 <= hi < len(srt) and 0 <= ai < len(srt)) or hi == ai:
            print("  Invalid selection."); return
    except ValueError:
        print("  Invalid input."); return

    ht, at = copy.deepcopy(srt[hi]), copy.deepcopy(srt[ai])
    hs, as_ = simulate_game(ht, at)
    print(f"\n  RESULT"); _sep()
    print(f"  {srt[hi].name:<30}  {hs:>3}")
    print(f"  {srt[ai].name:<30}  {as_:>3}"); _sep()
    print(f"  Winner: {srt[hi].name if hs > as_ else srt[ai].name}")


# ── Main ──────────────────────────────────────────────────────────────────────

MENU = """
  [1]  Standings
  [2]  Scoring leaders (PPG)
  [3]  Rebound leaders (RPG)
  [4]  Assist leaders  (APG)
  [5]  FG%% leaders
  [6]  Team roster & stats
  [7]  Season awards & MVP
  [8]  Quick one-off matchup
  [9]  Simulate playoffs
  [10] New season (re-roll & re-simulate)
  [0]  Quit
"""


def run_menu(teams):
    while True:
        _clear()
        _header("PYTHON SPORTS SIMULATOR  v1.0")

        el = max((t for t in teams if t.conference == "East"), key=lambda t: t.win_pct)
        wl = max((t for t in teams if t.conference == "West"), key=lambda t: t.win_pct)
        eligible = [(p, t) for t in teams for p in t.roster if p.games >= 40]
        if eligible:
            mp, mt = max(eligible, key=lambda x: x[0].ppg*1.5 + x[0].rpg*1.2 + x[0].apg*1.5)
            print(f"\n  East leader : {el.name} ({el.wins}-{el.losses})")
            print(f"  West leader : {wl.name} ({wl.wins}-{wl.losses})")
            print(f"  MVP cand.   : {mp.name} ({mt.abbr}) — {mp.ppg:.1f} PPG / {mp.rpg:.1f} RPG / {mp.apg:.1f} APG")
        print(MENU)
        choice = input("  Enter choice: ").strip()

        if   choice == "1":  _clear(); print_standings(teams);              _pause()
        elif choice == "2":  _clear(); print_stat_leaders(teams,"ppg","PPG");_pause()
        elif choice == "3":  _clear(); print_stat_leaders(teams,"rpg","RPG");_pause()
        elif choice == "4":  _clear(); print_stat_leaders(teams,"apg","APG");_pause()
        elif choice == "5":  _clear(); print_stat_leaders(teams,"fg_pct","FG%"); _pause()
        elif choice == "6":
            _clear()
            srt = sorted(teams, key=lambda t: t.name)
            for i, t in enumerate(srt, 1):
                print(f"  [{i:>2}] {t.name} ({t.abbr})  {t.wins}-{t.losses}")
            print()
            try:
                idx = int(input("  Select team #: ").strip()) - 1
                if 0 <= idx < len(srt): _clear(); print_team_roster(srt[idx])
                else: print("  Invalid.")
            except ValueError: print("  Invalid.")
            _pause()
        elif choice == "7":  _clear(); print_awards(teams);      _pause()
        elif choice == "8":  _clear(); quick_matchup(teams);     _pause()
        elif choice == "9":  _clear(); simulate_playoffs(teams); _pause()
        elif choice == "10":
            _clear()
            teams = build_all_teams()
            simulate_season(teams)
            _pause()
        elif choice == "0":
            print("\n  Goodbye!\n"); break
        else:
            print("  Unknown option."); _pause()


def splash():
    _clear()
    _header("PYTHON SPORTS SIMULATOR  v1.0")
    print("""
  NBA-style basketball season simulator — standard library only.

  Features:
    30 teams (15 East / 15 West)  *  13-player generated rosters
    82-game regular season        *  Full standings with streaks
    Stat leaders: PPG/RPG/APG/FG% *  Season awards & MVP
    8-team conference playoffs     *  Best-of-7 series
    Quick one-off matchup tool
""")
    print("  [1] Start  (random)")
    print("  [2] Set seed  (reproducible)")
    print("  [0] Quit")
    print()
    while True:
        c = input("  Choice: ").strip()
        if c == "1":
            return True
        elif c == "2":
            try:
                s = int(input("  Seed: ").strip())
                random.seed(s)
                print(f"  Seed = {s}")
                return True
            except ValueError:
                print("  Bad seed, using random.")
                return True
        elif c == "0":
            return False
        else:
            print("  Unknown option.")


def main():
    if not splash():
        print("\n  Goodbye!\n")
        return
    print("\n  Building rosters...")
    teams = build_all_teams()
    print(f"  {len(teams)} teams, {sum(len(t.roster) for t in teams)} players generated.")
    simulate_season(teams)
    run_menu(teams)


if __name__ == "__main__":
    main()
