{\rtf1\ansi\ansicpg950\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww28900\viewh15800\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st \
import pandas as pd \
import requests \
import numpy as np\
from bs4 import BeautifulSoup \
from nba_api.stats.endpoints import leaguedashteamstats, scoreboardv2, leaguedashplayerstats \
from nba_api.stats.static import teams \
from datetime import datetime, timedelta \
\
# ------------------------ \
# 0 \uc0\u26680 \u24515 \u37197 \u32622 \u33287 \u20013 \u33521 \u23565 \u29031 \u24235  \
# ------------------------ \
TEAM_CN = \{ \
    "Atlanta Hawks": "\uc0\u32769 \u40441 ", "Boston Celtics": "\u22622 \u29246 \u25552 \u20811 ", "Brooklyn Nets": "\u31811 \u32178 ", \
    "Charlotte Hornets": "\uc0\u40643 \u34562 ", "Chicago Bulls": "\u20844 \u29275 ", "Cleveland Cavaliers": "\u39438 \u22763 ", \
    "Dallas Mavericks": "\uc0\u29544 \u34892 \u20448 ", "Denver Nuggets": "\u37329 \u22602 ", "Detroit Pistons": "\u27963 \u22622 ", \
    "Golden State Warriors": "\uc0\u21191 \u22763 ", "Houston Rockets": "\u28779 \u31661 ", "Indiana Pacers": "\u28316 \u39340 ", \
    "LA Clippers": "\uc0\u24555 \u33351 ", "Los Angeles Lakers": "\u28246 \u20154 ", "Memphis Grizzlies": "\u28784 \u29066 ", \
    "Miami Heat": "\uc0\u29105 \u28779 ", "Milwaukee Bucks": "\u20844 \u40575 ", "Minnesota Timberwolves": "\u28784 \u29436 ", \
    "New Orleans Pelicans": "\uc0\u40284 \u40344 ", "New York Knicks": "\u23612 \u20811 ", "Oklahoma City Thunder": "\u38647 \u38662 ", \
    "Orlando Magic": "\uc0\u39764 \u34899 ", "Philadelphia 76ers": "76\u20154 ", "Phoenix Suns": "\u22826 \u38525 ", \
    "Portland Trail Blazers": "\uc0\u25299 \u33618 \u32773 ", "Sacramento Kings": "\u22283 \u29579 ", "San Antonio Spurs": "\u39340 \u21050 ", \
    "Toronto Raptors": "\uc0\u26292 \u40845 ", "Utah Jazz": "\u29237 \u22763 ", "Washington Wizards": "\u24043 \u24107 " \
\} \
\
TEAM_ZONE = \{\
    "Atlanta Hawks": "East", "Boston Celtics": "East", "Brooklyn Nets": "East",\
    "Charlotte Hornets": "East", "Chicago Bulls": "East", "Cleveland Cavaliers": "East",\
    "Detroit Pistons": "East", "Indiana Pacers": "East", "Miami Heat": "East",\
    "Milwaukee Bucks": "East", "New York Knicks": "East", "Orlando Magic": "East",\
    "Philadelphia 76ers": "East", "Toronto Raptors": "East", "Washington Wizards": "East",\
    "Dallas Mavericks": "West", "Denver Nuggets": "West", "Golden State Warriors": "West",\
    "Houston Rockets": "West", "LA Clippers": "West", "Los Angeles Lakers": "West",\
    "Memphis Grizzlies": "West", "Minnesota Timberwolves": "West", "New Orleans Pelicans": "West",\
    "Oklahoma City Thunder": "West", "Phoenix Suns": "West", "Portland Trail Blazers": "West",\
    "Sacramento Kings": "West", "San Antonio Spurs": "West", "Utah Jazz": "West"\
\}\
\
ODDS_API_TEAMS = \{\
    "Atlanta Hawks": "Atlanta Hawks", "Boston Celtics": "Boston Celtics", "Brooklyn Nets": "Brooklyn Nets",\
    "Charlotte Hornets": "Charlotte Hornets", "Chicago Bulls": "Chicago Bulls", "Cleveland Cavaliers": "Cleveland Cavaliers",\
    "Dallas Mavericks": "Dallas Mavericks", "Denver Nuggets": "Denver Nuggets", "Detroit Pistons": "Detroit Pistons",\
    "Golden State Warriors": "Golden State Warriors", "Houston Rockets": "Houston Rockets", "Indiana Pacers": "Indiana Pacers",\
    "LA Clippers": "Los Angeles Clippers", "Los Angeles Lakers": "Los Angeles Lakers", "Memphis Grizzlies": "Memphis Grizzlies",\
    "Miami Heat": "Miami Heat", "Milwaukee Bucks": "Milwaukee Bucks", "Minnesota Timberwolves": "Minnesota Timberwolves",\
    "New Orleans Pelicans": "New Orleans Pelicans", "New York Knicks": "New York Knicks", "Oklahoma City Thunder": "Oklahoma City Thunder",\
    "Orlando Magic": "Orlando Magic", "Philadelphia 76ers": "Philadelphia 76ers", "Phoenix Suns": "Phoenix Suns",\
    "Portland Trail Blazers": "Portland Trail Blazers", "Sacramento Kings": "Sacramento Kings", "San Antonio Spurs": "San Antonio Spurs",\
    "Toronto Raptors": "Toronto Raptors", "Utah Jazz": "Utah Jazz", "Washington Wizards": "Washington Wizards"\
\}\
\
STAR_PLAYERS = \{ \
    "Lakers": ["LeBron James", "Anthony Davis", "D'Angelo Russell", "Austin Reaves"],  \
    "Nuggets": ["Nikola Jokic", "Jamal Murray", "Aaron Gordon", "Michael Porter Jr."], \
    "Celtics": ["Jayson Tatum", "Jaylen Brown", "Kristaps Porzingis", "Derrick White", "Jrue Holiday"],  \
    "Mavericks": ["Luka Doncic", "Kyrie Irving", "Dereck Lively"], \
    "Thunder": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],  \
    "Timberwolves": ["Anthony Edwards", "Rudy Gobert", "Karl-Anthony Towns"], \
    "Bucks": ["Giannis Antetokounmpo", "Damian Lillard", "Khris Middleton"],  \
    "Warriors": ["Stephen Curry", "Draymond Green", "Jonathan Kuminga", "Andrew Wiggins"], \
    "Suns": ["Kevin Durant", "Devin Booker", "Bradley Beal"], \
    "76ers": ["Joel Embiid", "Tyrese Maxey", "Paul George"], \
    "Clippers": ["Kawhi Leonard", "James Harden"], \
    "Heat": ["Jimmy Butler", "Bam Adebayo"], \
    "Kings": ["De'Aaron Fox", "Domantas Sabonis"] \
\} \
\
PLAYER_CN = \{ \
    "LeBron James": "\uc0\u35449 \u22982 \u26031 ", "Anthony Davis": "\u25140 \u32173 \u26031 ", "D'Angelo Russell": "\u32645 \u32032 ", "Austin Reaves": "\u37324 \u22827 \u26031 ", \
    "Nikola Jokic": "\uc0\u32004 \u22522 \u22855 ", "Jamal Murray": "\u33707 \u29790 ", "Aaron Gordon": "\u39640 \u30331 ", "Michael Porter Jr.": "\u23567 \u27874 \u29305 ", \
    "Jayson Tatum": "\uc0\u22612 \u22294 \u22982 ", "Jaylen Brown": "\u24067 \u26391 ", "Kristaps Porzingis": "\u27874 \u36763 \u21513 \u26031 ", "Derrick White": "\u25079 \u29305 ", "Jrue Holiday": "\u21704 \u21202 \u25140 ", \
    "Luka Doncic": "\uc0\u21776 \u35199 \u22855 ", "Kyrie Irving": "\u21380 \u25991 ", "Dereck Lively": "\u33802 \u22827 \u21033 ", \
    "Shai Gilgeous-Alexander": "\uc0\u20126 \u27511 \u23665 \u22823 ", "Chet Holmgren": "\u38669 \u22982 \u26684 \u20523 ", "Jalen Williams": "\u23041 \u24265 \u26031 ", \
    "Anthony Edwards": "\uc0\u24859 \u24503 \u33775 \u33586 ", "Rudy Gobert": "\u25096 \u35997 \u29246 ", "Karl-Anthony Towns": "\u21776 \u26031 ", \
    "Giannis Antetokounmpo": "\uc0\u23383 \u27597 \u21733 ", "Damian Lillard": "\u37324 \u25289 \u24503 ", "Khris Middleton": "\u31859 \u24503 \u29246 \u38931 ", \
    "Stephen Curry": "\uc0\u26607 \u29790 ", "Draymond Green": "\u26684 \u26519 ", "Jonathan Kuminga": "\u24235 \u26126 \u21152 ", "Andrew Wiggins": "\u23041 \u37329 \u26031 ", \
    "Kevin Durant": "\uc0\u26460 \u34349 \u29305 ", "Devin Booker": "\u24067 \u20811 ", "Bradley Beal": "\u27604 \u29246 ", \
    "Joel Embiid": "\uc0\u24681 \u27604 \u24503 ", "Tyrese Maxey": "\u39340 \u20811 \u35199 ", "Paul George": "\u21932 \u27835 ", \
    "Kawhi Leonard": "\uc0\u38647 \u32013 \u24503 ", "James Harden": "\u21704 \u30331 ", \
    "Jimmy Butler": "\uc0\u24052 \u29305 \u21202 ", "Bam Adebayo": "\u38463 \u24503 \u24052 \u32004 ", \
    "De'Aaron Fox": "\uc0\u31119 \u20811 \u26031 ", "Domantas Sabonis": "\u27801 \u27874 \u23612 \u26031 " \
\} \
\
# ------------------------ \
# 1 \uc0\u20663 \u20853 \u12289 \u25976 \u25818 \u33287 \u30436 \u21475 \u24341 \u25806  \
# ------------------------ \
@st.cache_data(ttl=600) \
def fetch_injury_raw(): \
    headers = \{"User-Agent": "Mozilla/5.0"\} \
    try: \
        r = requests.get("https://www.cbssports.com/nba/injuries/", headers=headers, timeout=10) \
        return BeautifulSoup(r.text, 'html.parser').get_text(separator=' ', strip=True).lower() \
    except: return "" \
\
def get_injury_impact(team_name, raw_text): \
    mascot = team_name.split()[-1] \
    penalty, reports, has_gtd = 0, [], False \
    out_players = [] \
    search_key = "76ers" if mascot == "76ers" else mascot \
    t_cn = TEAM_CN.get(team_name, team_name) \
    \
    if search_key in STAR_PLAYERS: \
        for player in STAR_PLAYERS[search_key]: \
            full_name = player.lower() \
            if full_name in raw_text: \
                idx = raw_text.find(full_name) \
                chunk = raw_text[idx:idx+150] \
                p_cn = PLAYER_CN.get(player, player) \
                if "out" in chunk or "expected to be out" in chunk: \
                    penalty += 5.0  \
                    reports.append(f"\uc0\u55357 \u57000  [\{t_cn\}] \{p_cn\} - \u30906 \u23450 \u32570 \u38499 ") \
                    out_players.append(player) \
                elif any(word in chunk for word in ["questionable", "gtd", "decision"]): \
                    penalty += 2.5 \
                    reports.append(f"\uc0\u9888 \u65039  [\{t_cn\}] \{p_cn\} - \u20986 \u25136 \u25104 \u30097 (GTD)") \
                    has_gtd = True \
                    out_players.append(player) \
    \
    penalty = min(penalty, 8.5) \
    return penalty, reports, has_gtd, out_players \
\
@st.cache_data(ttl=3600) \
def fetch_nba_master(game_date_str): \
    game_date_obj = datetime.strptime(game_date_str, '%Y-%m-%d')\
    date_api_format = game_date_obj.strftime('%m/%d/%Y') \
    yest_str = (game_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')\
\
    team_dict = \{t["id"]: t["full_name"] for t in teams.get_teams()\} \
    \
    sb = scoreboardv2.ScoreboardV2(game_date=game_date_str) \
    games = sb.get_data_frames()[0].drop_duplicates(subset=['GAME_ID']) \
    line_score = sb.get_data_frames()[1] \
    \
    sb_yest = scoreboardv2.ScoreboardV2(game_date=yest_str)\
    yest_games = sb_yest.get_data_frames()[0]\
    \
    b2b_data = \{\}\
    for _, y_row in yest_games.iterrows():\
        b2b_data[y_row["HOME_TEAM_ID"]] = "Home"\
        b2b_data[y_row["VISITOR_TEAM_ID"]] = "Away"\
    \
    s_h = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense="Advanced", location_nullable="Home", date_to_nullable=date_api_format).get_data_frames()[0] \
    s_a = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense="Advanced", location_nullable="Road", date_to_nullable=date_api_format).get_data_frames()[0] \
    p_stats = leaguedashplayerstats.LeagueDashPlayerStats(measure_type_detailed_defense="Advanced", date_to_nullable=date_api_format).get_data_frames()[0] \
    \
    try:\
        s_last5 = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense="Advanced", last_n_games=5, date_to_nullable=date_api_format).get_data_frames()[0]\
    except:\
        s_last5 = pd.DataFrame()\
\
    return team_dict, games, line_score, s_h, s_a, p_stats, b2b_data, s_last5\
\
@st.cache_data(ttl=900) \
def fetch_live_odds(api_key):\
    if not api_key: return \{\}\
    try:\
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey=\{api_key\}&regions=us&markets=spreads,totals&bookmakers=pinnacle"\
        r = requests.get(url, timeout=10).json()\
        odds_dict = \{\}\
        for game in r:\
            home = game.get('home_team')\
            bookies = game.get('bookmakers', [])\
            if not bookies: continue\
            markets = bookies[0].get('markets', [])\
            spread_val, total_val = None, None\
            \
            for m in markets:\
                if m['key'] == 'spreads':\
                    for outcome in m['outcomes']:\
                        if outcome['name'] == home: spread_val = outcome['point']\
                elif m['key'] == 'totals':\
                    total_val = m['outcomes'][0]['point']\
                    \
            odds_dict[home] = \{"spread": spread_val, "total": total_val\}\
        return odds_dict\
    except:\
        return \{\}\
\
def calculate_weighted_pie(p_stats_df, team_id, out_players):\
    active_players = p_stats_df[(p_stats_df["TEAM_ID"] == team_id) & (~p_stats_df["PLAYER_NAME"].isin(out_players))]\
    core_players = active_players[active_players["MIN"] > 15] \
    if core_players.empty: return 0\
    top5 = core_players.nlargest(5, 'PIE')\
    weighted_pie = (top5['PIE'] * top5['MIN']).sum() / top5['MIN'].sum()\
    return weighted_pie\
\
def run_monte_carlo(h_s, a_s, game_pace, n_sims=10000):\
    sim_pace = np.random.normal(loc=game_pace, scale=4.0, size=n_sims)\
    h_ppp_mean = h_s / game_pace\
    a_ppp_mean = a_s / game_pace\
    sim_h_ppp = np.random.normal(loc=h_ppp_mean, scale=0.12, size=n_sims)\
    sim_a_ppp = np.random.normal(loc=a_ppp_mean, scale=0.12, size=n_sims)\
    sim_h_score = sim_pace * sim_h_ppp\
    sim_a_score = sim_pace * sim_a_ppp\
    return sim_h_score - sim_a_score, sim_h_score + sim_a_score\
\
def calculate_ev(win_prob, decimal_odds=1.909):\
    return (win_prob * (decimal_odds - 1)) - (1 - win_prob)\
\
# ------------------------ \
# 2 \uc0\u20027 \u20171 \u38754 \u33287 \u23526 \u25136 \u20998 \u26512  \
# ------------------------ \
st.set_page_config(page_title="NBA AI \uc0\u25915 \u38450 \u22823 \u24107  V31.0", layout="wide", page_icon="\u55356 \u57280 ") \
st.sidebar.header("\uc0\u55357 \u56787 \u65039  \u27511 \u21490 \u22238 \u28204 \u33287 \u23526 \u25136 \u25511 \u21046 ") \
target_date = st.sidebar.date_input("\uc0\u36984 \u25799 \u36093 \u20107 \u26085 \u26399 ", datetime.now() - timedelta(hours=8)) \
formatted_date = target_date.strftime('%Y-%m-%d') \
\
st.sidebar.divider()\
st.sidebar.markdown("### \uc0\u55358 \u56598  \u33258 \u21205 \u21270 \u30436 \u21475  API")\
st.sidebar.caption("\uc0\u21069 \u24448  The Odds API \u20813 \u36027 \u35387 \u20874 \u65292 \u21363 \u21487 \u35299 \u37782  V31 \u32887 \u26989 \u25136 \u30053 \u20736 \u34920 \u26495 \u12290 ")\
api_key = st.sidebar.text_input("\uc0\u36664 \u20837  API \u37329 \u38000 ", type="password")\
\
st.title(f"\uc0\u55356 \u57280  NBA AI V31 \u32887 \u26989 \u25136 \u30053 \u20736 \u34920 \u26495  (\{formatted_date\})") \
\
with st.spinner("\uc0\u21855 \u21205 \u38647 \u36948 \u65306 \u25475 \u25551 \u24066 \u22580 \u30436 \u21475 \u12289 \u22519 \u34892 \u33945 \u22320 \u21345 \u32645 \u27169 \u25836 \u33287  EV \u36939 \u31639 \u20013 ..."): \
    t_dict, games_df, line_df, s_h, s_a, p_stats, b2b_data, s_last5 = fetch_nba_master(formatted_date) \
    raw_inj = fetch_injury_raw() \
    live_odds = fetch_live_odds(api_key) if target_date == (datetime.now() - timedelta(hours=8)).date() else \{\}\
\
if games_df.empty: \
    st.info("\uc0\u55357 \u56517  \u27492 \u26085 \u26399 \u26283 \u28961 \u36093 \u31243 \u25976 \u25818 \u65292 \u35531 \u22039 \u35430 \u36984 \u25799 \u20854 \u20182 \u26085 \u26399 \u12290 ") \
else: \
    match_data = [] \
    all_ev_opportunities = [] # \uc0\u55357 \u57057 \u65039  V31.0 \u26680 \u24515 \u65306 \u29992 \u20358 \u25910 \u38598 \u30070 \u26085 \u25152 \u26377 \u30436 \u21475 \u32173 \u24230 \u30340 \u27491  EV \u27161 \u30340 \
    is_historical = target_date < (datetime.now() - timedelta(hours=8)).date() \
\
    for _, row in games_df.iterrows(): \
        h_id, a_id = row["HOME_TEAM_ID"], row["VISITOR_TEAM_ID"] \
        h_n_en, a_n_en = t_dict.get(h_id), t_dict.get(a_id) \
        h_n, a_n = TEAM_CN.get(h_n_en, h_n_en), TEAM_CN.get(a_n_en, a_n_en) \
        \
        try: \
            h_pts_raw = line_df.loc[line_df['TEAM_ID'] == h_id, 'PTS'].values \
            a_pts_raw = line_df.loc[line_df['TEAM_ID'] == a_id, 'PTS'].values \
            h_act = int(float(h_pts_raw[0])) if len(h_pts_raw) > 0 and pd.notna(h_pts_raw[0]) else 0 \
            a_act = int(float(a_pts_raw[0])) if len(a_pts_raw) > 0 and pd.notna(a_pts_raw[0]) else 0 \
        except: \
            h_act, a_act = 0, 0 \
            \
        is_finished = (h_act > 0 and a_act > 0 and (h_act + a_act) > 150) \
\
        h_pen, h_rep, h_gtd, h_out_players = get_injury_impact(h_n_en, raw_inj) \
        a_pen, a_rep, a_gtd, a_out_players = get_injury_impact(a_n_en, raw_inj) \
        \
        if is_historical: \
            h_pen, a_pen = h_pen * 0.5, a_pen * 0.5 \
\
        h_is_b2b = h_id in b2b_data\
        a_is_b2b = a_id in b2b_data\
        has_fatigue = h_is_b2b or a_is_b2b\
        \
        if h_is_b2b:\
            h_pen += 3.5  \
            h_rep.append(f"\uc0\u55357 \u56587  [\{h_n\}] \u20027 \u22580 \u32972 \u38752 \u32972  (\u39636 \u33021 \u19979 \u28369 )")\
        if a_is_b2b:\
            yest_loc = b2b_data[a_id]\
            if yest_loc == "Away":\
                a_pen += 5.5\
                a_rep.append(f"\uc0\u9992 \u65039  [\{a_n\}] \u36899 \u32396 \u23458 \u22580 \u32972 \u38752 \u32972  (\u22196 \u37325 \u39131 \u34892 \u30130 \u21214 )")\
            else:\
                a_pen += 4.0\
                a_rep.append(f"\uc0\u55357 \u56587  [\{a_n\}] \u23458 \u22580 \u32972 \u38752 \u32972  (\u39636 \u33021 \u19979 \u28369 )")\
\
            if TEAM_ZONE.get(a_n_en) != TEAM_ZONE.get(h_n_en):\
                a_pen += 1.5\
                a_rep.append(f"\uc0\u55356 \u57102  [\{a_n\}] \u36328 \u21312 \u26178 \u24046 \u20316 \u25136  (\u30130 \u21214 \u21152 \u21127 )")\
\
        try: \
            h_d = s_h[s_h["TEAM_ID"] == h_id].iloc[0] \
            a_d = s_a[s_a["TEAM_ID"] == a_id].iloc[0] \
            \
            if not s_last5.empty:\
                h_l5 = s_last5[s_last5["TEAM_ID"] == h_id]\
                a_l5 = s_last5[s_last5["TEAM_ID"] == a_id]\
                \
                if not h_l5.empty and not a_l5.empty:\
                    h_l5_off = h_l5.iloc[0]["OFF_RATING"]\
                    if h_l5_off > h_d["OFF_RATING"] * 1.08: h_l5_off = h_d["OFF_RATING"] * 1.05 \
                    a_l5_off = a_l5.iloc[0]["OFF_RATING"]\
                    if a_l5_off > a_d["OFF_RATING"] * 1.08: a_l5_off = a_d["OFF_RATING"] * 1.05 \
                    \
                    h_off = (h_d["OFF_RATING"] * 0.7) + (h_l5_off * 0.3)\
                    h_def = (h_d["DEF_RATING"] * 0.7) + (h_l5.iloc[0]["DEF_RATING"] * 0.3)\
                    a_off = (a_d["OFF_RATING"] * 0.7) + (a_l5_off * 0.3)\
                    a_def = (a_d["DEF_RATING"] * 0.7) + (a_l5.iloc[0]["DEF_RATING"] * 0.3)\
                else:\
                    h_off, h_def = h_d["OFF_RATING"], h_d["DEF_RATING"]\
                    a_off, a_def = a_d["OFF_RATING"], a_d["DEF_RATING"]\
            else:\
                h_off, h_def = h_d["OFF_RATING"], h_d["DEF_RATING"]\
                a_off, a_def = a_d["OFF_RATING"], a_d["DEF_RATING"]\
            \
            pace_h = h_d["PACE"]\
            pace_a = a_d["PACE"]\
            game_pace = (2 * pace_h * pace_a) / (pace_h + pace_a)\
            \
            h_base_rating = (h_off * 0.65) + (a_def * 0.35) \
            a_base_rating = (a_off * 0.65) + (h_def * 0.35) \
            \
            h_win_pct = h_d["W_PCT"]\
            a_win_pct = a_d["W_PCT"]\
            elo_edge = (h_win_pct - a_win_pct) * 4.5 \
            \
            h_pie = calculate_weighted_pie(p_stats, h_id, h_out_players)\
            a_pie = calculate_weighted_pie(p_stats, a_id, a_out_players)\
            \
            h_edge = (h_pie - 12) * 0.4 if h_pie > 12 else 0 \
            a_edge = (a_pie - 12) * 0.4 if a_pie > 12 else 0 \
            \
            h_s = round((h_base_rating * (game_pace/100)) + 2.5 - h_pen + h_edge + (elo_edge / 2), 1) \
            a_s = round((a_base_rating * (game_pace/100)) - a_pen + a_edge - (elo_edge / 2), 1) \
            \
            sim_diff, sim_total = run_monte_carlo(h_s, a_s, game_pace)\
            \
            api_team_name = ODDS_API_TEAMS.get(h_n_en)\
            market_spread = None\
            market_total = None\
            \
            if live_odds and api_team_name in live_odds:\
                market_spread = live_odds[api_team_name].get("spread")\
                market_total = live_odds[api_team_name].get("total")\
\
            # \uc0\u55357 \u57057 \u65039  V31.0 \u26680 \u24515 \u65306 \u33258 \u21205 \u35336 \u31639 \u20840 \u24066 \u22580  EV\u65292 \u20006 \u33936 \u38598 \u22823 \u26044  0 \u30340 \u20729 \u20540 \u27161 \u30340 \
            if market_spread is not None:\
                prob_cover_h = np.mean(sim_diff > -market_spread)\
                prob_cover_a = np.mean(sim_diff < -market_spread)\
                ev_h = calculate_ev(prob_cover_h)\
                ev_a = calculate_ev(prob_cover_a)\
                \
                if ev_h > 0:\
                    all_ev_opportunities.append(\{\
                        "\uc0\u23565 \u25136 \u32068 \u21512 ": f"\{a_n\} @ \{h_n\}", "\u19979 \u27880 \u39006 \u22411 ": "\u35731 \u20998 \u30436 ", "\u33674 \u23478 \u38283 \u30436 ": f"\u20027  \{market_spread\}", \
                        "\uc0\u25512 \u34214 \u19979 \u27880 ": f"\u20027 \u38538  (\{h_n\})", "\u33945 \u22320 \u21345 \u32645 \u36942 \u30436 \u29575 ": f"\{prob_cover_h:.1%\}", "\u26399 \u26395 \u20540  (EV)": ev_h\
                    \})\
                if ev_a > 0:\
                    all_ev_opportunities.append(\{\
                        "\uc0\u23565 \u25136 \u32068 \u21512 ": f"\{a_n\} @ \{h_n\}", "\u19979 \u27880 \u39006 \u22411 ": "\u35731 \u20998 \u30436 ", "\u33674 \u23478 \u38283 \u30436 ": f"\u23458  \{-market_spread\}", \
                        "\uc0\u25512 \u34214 \u19979 \u27880 ": f"\u23458 \u38538  (\{a_n\})", "\u33945 \u22320 \u21345 \u32645 \u36942 \u30436 \u29575 ": f"\{prob_cover_a:.1%\}", "\u26399 \u26395 \u20540  (EV)": ev_a\
                    \})\
\
            if market_total is not None:\
                prob_over = np.mean(sim_total > market_total)\
                prob_under = np.mean(sim_total < market_total)\
                ev_over = calculate_ev(prob_over)\
                ev_under = calculate_ev(prob_under)\
                \
                if ev_over > 0:\
                    all_ev_opportunities.append(\{\
                        "\uc0\u23565 \u25136 \u32068 \u21512 ": f"\{a_n\} @ \{h_n\}", "\u19979 \u27880 \u39006 \u22411 ": "\u22823 \u23567 \u20998 ", "\u33674 \u23478 \u38283 \u30436 ": f"\u32317 \u20998  \{market_total\}", \
                        "\uc0\u25512 \u34214 \u19979 \u27880 ": "\u22823 \u20998  (Over)", "\u33945 \u22320 \u21345 \u32645 \u36942 \u30436 \u29575 ": f"\{prob_over:.1%\}", "\u26399 \u26395 \u20540  (EV)": ev_over\
                    \})\
                if ev_under > 0:\
                    all_ev_opportunities.append(\{\
                        "\uc0\u23565 \u25136 \u32068 \u21512 ": f"\{a_n\} @ \{h_n\}", "\u19979 \u27880 \u39006 \u22411 ": "\u22823 \u23567 \u20998 ", "\u33674 \u23478 \u38283 \u30436 ": f"\u32317 \u20998  \{market_total\}", \
                        "\uc0\u25512 \u34214 \u19979 \u27880 ": "\u23567 \u20998  (Under)", "\u33945 \u22320 \u21345 \u32645 \u36942 \u30436 \u29575 ": f"\{prob_under:.1%\}", "\u26399 \u26395 \u20540  (EV)": ev_under\
                    \})\
\
            # \uc0\u29992 \u26044 \u32317 \u34920 \u39023 \u31034 \u30340 \u26368 \u20339 \u25512 \u34214 \
            best_bet_str = "\uc0\u28961 \u30436 \u21475 \u36039 \u35338 "\
            if market_spread is not None:\
                if ev_h >= ev_a and ev_h > 0: best_bet_str = f"\uc0\u20027 \u38538  (-\{market_spread\}) | EV: +\{ev_h:.1%\}"\
                elif ev_a > ev_h and ev_a > 0: best_bet_str = f"\uc0\u23458 \u38538  (+\{market_spread\}) | EV: +\{ev_a:.1%\}"\
                else: best_bet_str = "\uc0\u9888 \u65039  \u36000  EV (\u24314 \u35696 \u36991 \u38283 )"\
            else:\
                home_win_prob = np.mean(sim_diff > 0)\
                if abs(h_s - a_s) <= 1.0: best_bet_str = "\uc0\u9888 \u65039 \u20116 \u20116 \u27874 (\u36991 \u38283 )"\
                else: best_bet_str = f"\uc0\u20027 \u21213  (\{home_win_prob:.1%\})" if home_win_prob > 0.5 else f"\u23458 \u21213  (\{1-home_win_prob:.1%\})"\
\
            hit = "\uc0\u24453 \u23450 " \
            if is_finished: \
                if "\uc0\u36991 \u38283 " in best_bet_str or "\u28961 \u30436 \u21475 \u36039 \u35338 " in best_bet_str:\
                    hit = "\uc0\u28961 "  \
                else:\
                    if market_spread is not None:\
                        if "\uc0\u20027 \u38538 " in best_bet_str and (h_act - a_act > -market_spread): hit = "\u9989 "\
                        elif "\uc0\u23458 \u38538 " in best_bet_str and (h_act - a_act < -market_spread): hit = "\u9989 "\
                        else: hit = "\uc0\u10060 "\
                    else:\
                        hit = "\uc0\u9989 " if (h_s > a_s and h_act > a_act) or (h_s < a_s and h_act < a_act) else "\u10060 " \
\
            match_data.append(\{ \
                "\uc0\u23565 \u25136 \u32068 \u21512 ": f"\{a_n\} @ \{h_n\}", \
                "AI\uc0\u28136 \u21213 \u20998 (\u23458 :\u20027 )": f"\{a_s\} : \{h_s\}", \
                "\uc0\u24066 \u22580 \u35731 \u20998 (\u20027 )": market_spread if market_spread is not None else "-",\
                "\uc0\u26368 \u20339  EV \u27770 \u31574 ": best_bet_str,\
                "\uc0\u23526 \u38555 \u27604 \u20998 ": f"\{a_act\} : \{h_act\}" if is_finished else "-", \
                "\uc0\u21213 \u36000 \u21629 \u20013 ": hit, \
                "h_name": h_n, "a_name": a_n, \
                "h_s": h_s, "a_s": a_s,  \
                "game_pace": game_pace,\
                "reports": h_rep + a_rep\
            \}) \
        except Exception as e: \
            continue \
\
    # \uc0\u55357 \u57057 \u65039  V31.0 \u20736 \u34920 \u26495  UI \u35373 \u35336 \
    if all_ev_opportunities:\
        st.header("\uc0\u55357 \u56613  \u20170 \u26085  TOP 5 \u20729 \u20540 \u25237 \u27880  (\u20840 \u30436 \u21475 \u33258 \u21205 \u25475 \u25551 )")\
        st.caption("\uc0\u36889 \u26159 \u19968 \u24373 \u30001 \u33945 \u22320 \u21345 \u32645 \u31995 \u32113 \u33258 \u21205 \u25475 \u25551 \u20170 \u26085 \u25152 \u26377 \u12300 \u35731 \u20998 \u12301 \u33287 \u12300 \u22823 \u23567 \u20998 \u12301 \u30436 \u21475 \u24460 \u65292 \u25214 \u20986 \u30340 \u26368 \u20855 \u25976 \u23416 \u26399 \u26395 \u20540  (EV) \u30340 \u19979 \u27880 \u27161 \u30340 \u12290 ")\
        # \uc0\u25490 \u24207 \u20006 \u21462 \u21069  5 \u21517 \
        ev_df = pd.DataFrame(all_ev_opportunities)\
        ev_df = ev_df.sort_values(by="\uc0\u26399 \u26395 \u20540  (EV)", ascending=False).head(5)\
        # \uc0\u23559  EV \u36681 \u28858 \u30334 \u20998 \u27604 \u39023 \u31034 \
        ev_df["\uc0\u26399 \u26395 \u20540  (EV)"] = ev_df["\u26399 \u26395 \u20540  (EV)"].apply(lambda x: f"+\{x:.1%\}")\
        \
        # \uc0\u25918 \u22823 \u39023 \u31034 \u65292 \u35069 \u36896 \u25805 \u30436 \u26700 \u35222 \u35258 \
        st.dataframe(ev_df, use_container_width=True, height=215)\
    elif api_key:\
        st.warning("\uc0\u9888 \u65039  \u20170 \u26085 \u33674 \u23478 \u38283 \u30436 \u26997 \u24230 \u31934 \u28310 \u65292 \u31995 \u32113 \u26410 \u25475 \u25551 \u21040 \u20219 \u20309 \u22823 \u26044  0% EV \u30340 \u36093 \u20107 \u65292 \u24314 \u35696 \u20170 \u26085 \u31354 \u25163 \u35264 \u26395 \u12290 ")\
\
    st.divider() \
    st.header("\uc0\u55357 \u56522  \u23436 \u25972 \u36093 \u20107 \u25976 \u25818 \u33287 \u24066 \u22580 \u30436 \u21475  (\u21253 \u21547 \u27511 \u21490 \u22238 \u28204 )") \
    if match_data:\
        display_df = pd.DataFrame(match_data)[["\uc0\u23565 \u25136 \u32068 \u21512 ", "AI\u28136 \u21213 \u20998 (\u23458 :\u20027 )", "\u24066 \u22580 \u35731 \u20998 (\u20027 )", "\u26368 \u20339  EV \u27770 \u31574 ", "\u23526 \u38555 \u27604 \u20998 ", "\u21213 \u36000 \u21629 \u20013 "]]\
        st.dataframe(display_df, use_container_width=True) \
\
    st.divider() \
    st.header("\uc0\u55357 \u56589  \u21934 \u22580 \u28145 \u24230 \u35299 \u26512 \u33287 \u25163 \u21205 \u28204 \u35430 \u20736 ") \
    if match_data:\
        s_game = st.selectbox("\uc0\u35531 \u36984 \u25799 \u35201 \u28145 \u20837 \u20998 \u26512 \u30340 \u22580 \u27425 \u65306 ", match_data, format_func=lambda x: x["\u23565 \u25136 \u32068 \u21512 "]) \
        \
        col_a, col_b = st.columns(2) \
        with col_a: \
            st.subheader("\uc0\u55357 \u56541  \u35722 \u25976 \u33287 \u38499 \u23481 \u22577 \u21578 ") \
            if s_game["reports"]: \
                for r in s_game["reports"]: \
                    if "\uc0\u9992 \u65039 " in r or "\u55356 \u57102 " in r or "\u55357 \u56587 " in r: st.error(r)  \
                    else: st.warning(r) \
            else: \
                st.success("\uc0\u9989  \u28961 \u30064 \u24120 \u35722 \u25976 \u24178 \u25854 \u12290 ") \
                \
        with col_b: \
            st.subheader("\uc0\u55356 \u57266  \u36305 \u19968 \u33836 \u27425 \u65281 \u21205 \u24907  EV \u27169 \u25836 ") \
            u_spread = st.number_input(f"\uc0\u35531 \u36664 \u20837 \u21488 \u24425 \u38283 \u32102 \u20027 \u38538 \u30340 \u35731 \u20998  (\u20363 : -4.5)", value=-4.5, step=0.5) \
            u_total = st.number_input(f"\uc0\u35531 \u36664 \u20837 \u22823 \u23567 \u20998 \u32317 \u20998 \u30436 \u21475  (\u20363 : 225.5)", value=225.5, step=0.5) \
            \
            sim_diff, sim_total = run_monte_carlo(s_game['h_s'], s_game['a_s'], s_game['game_pace'])\
            \
            prob_cover_h = np.mean(sim_diff > -u_spread)\
            prob_cover_a = np.mean(sim_diff < -u_spread)\
            prob_over = np.mean(sim_total > u_total)\
            prob_under = np.mean(sim_total < u_total)\
            \
            ev_h = calculate_ev(prob_cover_h)\
            ev_a = calculate_ev(prob_cover_a)\
            ev_over = calculate_ev(prob_over)\
            ev_under = calculate_ev(prob_under)\
            \
            st.write("\uc0\u9654 \u65039  **\u35731 \u20998 \u30436  10,000 \u27425 \u27169 \u25836 \u32080 \u26524 \u65306 **")\
            st.write(f"\uc0\u20027 \u38538  (\{u_spread\}) \u36942 \u30436 \u29575 : `\{prob_cover_h:.1%\}` \u10145 \u65039  EV: `\{ev_h:.1%\}`")\
            st.write(f"\uc0\u23458 \u38538  (\{-u_spread\}) \u36942 \u30436 \u29575 : `\{prob_cover_a:.1%\}` \u10145 \u65039  EV: `\{ev_a:.1%\}`")\
            \
            st.divider()\
            \
            st.write("\uc0\u9654 \u65039  **\u22823 \u23567 \u20998  10,000 \u27425 \u27169 \u25836 \u32080 \u26524 \u65306 **")\
            st.write(f"\uc0\u22823 \u20998  (> \{u_total\}) \u27231 \u29575 : `\{prob_over:.1%\}` \u10145 \u65039  EV: `\{ev_over:.1%\}`")\
            st.write(f"\uc0\u23567 \u20998  (< \{u_total\}) \u27231 \u29575 : `\{prob_under:.1%\}` \u10145 \u65039  EV: `\{ev_under:.1%\}`")\
                \
st.caption("NBA AI V31.0 - \uc0\u33775 \u29246 \u34903 \u37327 \u21270 \u32066 \u31471 \u27231 \u65306 \u20840 \u30436 \u21475 \u33258 \u21205 \u21270 \u25475 \u25551 \u33287 \u27491  EV TOP 5 \u25136 \u30053 \u20736 \u34920 \u26495 ")}