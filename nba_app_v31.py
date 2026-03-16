import streamlit as st 
import pandas as pd 
import requests 
import numpy as np
import time
from bs4 import BeautifulSoup 
from nba_api.stats.endpoints import leaguedashteamstats, scoreboardv2, leaguedashplayerstats 
from nba_api.stats.static import teams 
from datetime import datetime, timedelta 

# ---------------------------------------------------------
# 0. 核心配置與中英對照庫 (嚴格保留)
# ---------------------------------------------------------
TEAM_CN = { 
    "Atlanta Hawks": "老鷹", "Boston Celtics": "塞爾提克", "Brooklyn Nets": "籃網", 
    "Charlotte Hornets": "黃蜂", "Chicago Bulls": "公牛", "Cleveland Cavaliers": "騎士", 
    "Dallas Mavericks": "獨行俠", "Denver Nuggets": "金塊", "Detroit Pistons": "活塞", 
    "Golden State Warriors": "勇士", "Houston Rockets": "火箭", "Indiana Pacers": "溜馬", 
    "LA Clippers": "快艇", "Los Angeles Lakers": "湖人", "Memphis Grizzlies": "灰熊", 
    "Miami Heat": "熱火", "Milwaukee Bucks": "公鹿", "Minnesota Timberwolves": "灰狼", 
    "New Orleans Pelicans": "鵜鶘", "New York Knicks": "尼克", "Oklahoma City Thunder": "雷霆", 
    "Orlando Magic": "魔術", "Philadelphia 76ers": "76人", "Phoenix Suns": "太陽", 
    "Portland Trail Blazers": "拓荒者", "Sacramento Kings": "國王", "San Antonio Spurs": "馬刺", 
    "Toronto Raptors": "暴龍", "Utah Jazz": "爵士", "Washington Wizards": "巫師" 
} 

TEAM_ZONE = {
    "Atlanta Hawks": "East", "Boston Celtics": "East", "Brooklyn Nets": "East",
    "Charlotte Hornets": "East", "Chicago Bulls": "East", "Cleveland Cavaliers": "East",
    "Detroit Pistons": "East", "Indiana Pacers": "East", "Miami Heat": "East",
    "Milwaukee Bucks": "East", "New York Knicks": "East", "Orlando Magic": "East",
    "Philadelphia 76ers": "East", "Toronto Raptors": "East", "Washington Wizards": "East",
    "Dallas Mavericks": "West", "Denver Nuggets": "West", "Golden State Warriors": "West",
    "Houston Rockets": "West", "LA Clippers": "West", "Los Angeles Lakers": "West",
    "Memphis Grizzlies": "West", "Minnesota Timberwolves": "West", "New Orleans Pelicans": "West",
    "Oklahoma City Thunder": "West", "Phoenix Suns": "West", "Portland Trail Blazers": "West",
    "Sacramento Kings": "West", "San Antonio Spurs": "West", "Utah Jazz": "West"
}

ODDS_API_TEAMS = {
    "Atlanta Hawks": "Atlanta Hawks", "Boston Celtics": "Boston Celtics", "Brooklyn Nets": "Brooklyn Nets",
    "Charlotte Hornets": "Charlotte Hornets", "Chicago Bulls": "Chicago Bulls", "Cleveland Cavaliers": "Cleveland Cavaliers",
    "Dallas Mavericks": "Dallas Mavericks", "Denver Nuggets": "Denver Nuggets", "Detroit Pistons": "Detroit Pistons",
    "Golden State Warriors": "Golden State Warriors", "Houston Rockets": "Houston Rockets", "Indiana Pacers": "Indiana Pacers",
    "LA Clippers": "Los Angeles Clippers", "Los Angeles Lakers": "Los Angeles Lakers", "Memphis Grizzlies": "Memphis Grizzlies",
    "Miami Heat": "Miami Heat", "Milwaukee Bucks": "Milwaukee Bucks", "Minnesota Timberwolves": "Minnesota Timberwolves",
    "New Orleans Pelicans": "New Orleans Pelicans", "New York Knicks": "New York Knicks", "Oklahoma City Thunder": "Oklahoma City Thunder",
    "Orlando Magic": "Orlando Magic", "Philadelphia 76ers": "Philadelphia 76ers", "Phoenix Suns": "Phoenix Suns",
    "Portland Trail Blazers": "Portland Trail Blazers", "Sacramento Kings": "Sacramento Kings", "San Antonio Spurs": "San Antonio Spurs",
    "Toronto Raptors": "Toronto Raptors", "Utah Jazz": "Utah Jazz", "Washington Wizards": "Washington Wizards"
}

STAR_PLAYERS = { 
    "Lakers": ["LeBron James", "Anthony Davis", "D'Angelo Russell", "Austin Reaves"],  
    "Nuggets": ["Nikola Jokic", "Jamal Murray", "Aaron Gordon", "Michael Porter Jr."], 
    "Celtics": ["Jayson Tatum", "Jaylen Brown", "Kristaps Porzingis", "Derrick White", "Jrue Holiday"],  
    "Mavericks": ["Luka Doncic", "Kyrie Irving", "Dereck Lively"], 
    "Thunder": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Jalen Williams"],  
    "Timberwolves": ["Anthony Edwards", "Rudy Gobert", "Karl-Anthony Towns"], 
    "Bucks": ["Giannis Antetokounmpo", "Damian Lillard", "Khris Middleton"],  
    "Warriors": ["Stephen Curry", "Draymond Green", "Jonathan Kuminga", "Andrew Wiggins"], 
    "Suns": ["Kevin Durant", "Devin Booker", "Bradley Beal"], 
    "76ers": ["Joel Embiid", "Tyrese Maxey", "Paul George"], 
    "Clippers": ["Kawhi Leonard", "James Harden"], 
    "Heat": ["Jimmy Butler", "Bam Adebayo"], 
    "Kings": ["De'Aaron Fox", "Domantas Sabonis"] 
} 

# ---------------------------------------------------------
# 1. 強化型數據引擎 (修復 API 拒絕連線問題)
# ---------------------------------------------------------

# 🛡️ 模擬真實瀏覽器 Header，防止被 NBA 封鎖
NBA_HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/'
}

@st.cache_data(ttl=600) 
def fetch_injury_raw(): 
    headers = {"User-Agent": "Mozilla/5.0"} 
    try: 
        r = requests.get("https://www.cbssports.com/nba/injuries/", headers=headers, timeout=10)
        return r.text.lower()
    except: return "" 

def get_injury_impact(team_name, raw_html_text): 
    if not raw_html_text: return 0, [], False, []
    mascot = team_name.split()[-1] 
    penalty, reports, has_gtd, out_players = 0, [], False, []
    search_key = "76ers" if mascot == "76ers" else mascot 
    if search_key in STAR_PLAYERS: 
        for player in STAR_PLAYERS[search_key]: 
            full_name = player.lower() 
            if full_name in raw_html_text: 
                idx = raw_html_text.find(full_name) 
                chunk = raw_html_text[idx:idx+250]
                if any(word in chunk for word in ["out", "expected to be out", "surgery"]): 
                    penalty += 5.0; reports.append(f"🚨 {player} (缺陣)"); out_players.append(player)
                elif any(word in chunk for word in ["questionable", "gtd", "decision"]): 
                    penalty += 2.5; reports.append(f"⚠️ {player} (GTD)"); has_gtd = True; out_players.append(player)
    return min(penalty, 9.5), reports, has_gtd, out_players 

@st.cache_data(ttl=3600) 
def fetch_nba_master(game_date_str): 
    game_date_obj = datetime.strptime(game_date_str, '%Y-%m-%d')
    date_api_format = game_date_obj.strftime('%m/%d/%Y') 
    yest_str = (game_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
    team_dict = {t["id"]: t["full_name"] for t in teams.get_teams()} 
    
    try:
        # 🛡️ 關鍵修復：加入 headers 並在失敗時稍微等待
        sb = scoreboardv2.ScoreboardV2(game_date=game_date_str, headers=NBA_HEADERS) 
        games = sb.get_data_frames()[0].drop_duplicates(subset=['GAME_ID']) 
        line_score = sb.get_data_frames()[1] 
        
        # 抓昨日賽程判斷 B2B
        sb_yest = scoreboardv2.ScoreboardV2(game_date=yest_str, headers=NBA_HEADERS)
        yest_games = sb_yest.get_data_frames()[0]
        b2b_data = {row["HOME_TEAM_ID"]: "Home" for _, row in yest_games.iterrows()}
        b2b_data.update({row["VISITOR_TEAM_ID"]: "Away" for _, row in yest_games.iterrows()})
        
        # 抓進階數據
        s_h = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense="Advanced", location_nullable="Home", date_to_nullable=date_api_format, headers=NBA_HEADERS).get_data_frames()[0] 
        s_a = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense="Advanced", location_nullable="Road", date_to_nullable=date_api_format, headers=NBA_HEADERS).get_data_frames()[0] 
        p_stats = leaguedashplayerstats.LeagueDashPlayerStats(measure_type_detailed_defense="Advanced", date_to_nullable=date_api_format, headers=NBA_HEADERS).get_data_frames()[0] 
        
        try:
            s_last5 = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense="Advanced", last_n_games=5, date_to_nullable=date_api_format, headers=NBA_HEADERS).get_data_frames()[0]
        except:
            s_last5 = pd.DataFrame()
            
        return team_dict, games, line_score, s_h, s_a, p_stats, b2b_data, s_last5
    except Exception as e:
        st.error(f"NBA API 連線異常: {e} (可能是 NBA 官網暫時封鎖，請 5 分鐘後重試)")
        return {}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}, pd.DataFrame()

@st.cache_data(ttl=900) 
def fetch_live_odds(api_key):
    if not api_key: return {}
    try:
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=spreads,totals&bookmakers=pinnacle"
        r = requests.get(url, timeout=10).json()
        odds_dict = {}
        for game in r:
            home = game.get('home_team')
            bookies = game.get('bookmakers', [])
            if not bookies: continue
            markets = bookies[0].get('markets', [])
            spread_val, total_val = None, None
            for m in markets:
                if m['key'] == 'spreads':
                    for outcome in m['outcomes']:
                        if outcome['name'] == home: spread_val = outcome['point']
                elif m['key'] == 'totals':
                    total_val = m['outcomes'][0]['point']
            odds_dict[home] = {"spread": spread_val, "total": total_val}
        return odds_dict
    except: return {}

def calculate_weighted_pie(p_stats_df, team_id, out_players):
    active_players = p_stats_df[(p_stats_df["TEAM_ID"] == team_id) & (~p_stats_df["PLAYER_NAME"].isin(out_players))]
    core_players = active_players[active_players["MIN"] > 15] 
    if core_players.empty: return 0
    top5 = core_players.nlargest(5, 'PIE')
    return (top5['PIE'] * top5['MIN']).sum() / top5['MIN'].sum()

def run_monte_carlo(h_s, a_s, game_pace, n_sims=10000):
    sim_pace = np.random.normal(loc=game_pace, scale=4.0, size=n_sims)
    h_ppp = np.random.normal(loc=h_s/game_pace, scale=0.12, size=n_sims)
    a_ppp = np.random.normal(loc=a_s/game_pace, scale=0.12, size=n_sims)
    return sim_pace * h_ppp - sim_pace * a_ppp, sim_pace * h_ppp + sim_pace * a_ppp

def calculate_ev(win_prob, decimal_odds=1.909):
    return (win_prob * (decimal_odds - 1)) - (1 - win_prob)

# ---------------------------------------------------------
# 2. UI 介面整合 (嚴格增量原則：所有模組必須存在)
# ---------------------------------------------------------
st.set_page_config(page_title="NBA AI 攻防大師 V31.4", layout="wide", page_icon="🏀") 

# 側邊欄控制
st.sidebar.header("🗓️ 系統控制台") 
target_date = st.sidebar.date_input("選擇日期", datetime.now() - timedelta(hours=8)) 
formatted_date = target_date.strftime('%Y-%m-%d') 

st.sidebar.divider()
st.sidebar.markdown("### 🤖 自動化盤口 API")
api_key = st.secrets.get("ODDS_API_KEY", "")
if not api_key: api_key = st.sidebar.text_input("輸入 API 金鑰 (選填)", type="password")

st.title(f"🏀 NBA AI V31.4 職業戰略儀表板 ({formatted_date})") 

# 主程式執行
with st.spinner("雷達掃描中：模擬一萬場比賽中..."): 
    t_dict, games_df, line_df, s_h, s_a, p_stats, b2b_data, s_last5 = fetch_nba_master(formatted_date) 
    raw_inj = fetch_injury_raw() 
    live_odds = fetch_live_odds(api_key) if target_date >= (datetime.now() - timedelta(hours=24)).date() else {}

if games_df.empty: 
    st.info(f"📅 {formatted_date} 此日期暫無賽程數據，請嘗試選擇其他日期 (例如 3/17)。") 
else:
    match_data = [] 
    all_ev_opportunities = [] 
    is_historical = target_date < (datetime.now() - timedelta(hours=8)).date() 

    for _, row in games_df.iterrows(): 
        h_id, a_id = row["HOME_TEAM_ID"], row["VISITOR_TEAM_ID"] 
        h_n_en, a_n_en = t_dict.get(h_id), t_dict.get(a_id) 
        h_n, a_n = TEAM_CN.get(h_n_en, h_n_en), TEAM_CN.get(a_n_en, a_n_en) 
        
        try: 
            h_pts_raw = line_df.loc[line_df['TEAM_ID'] == h_id, 'PTS'].values 
            a_pts_raw = line_df.loc[line_df['TEAM_ID'] == a_id, 'PTS'].values 
            h_act, a_act = (int(h_pts_raw[0]), int(a_pts_raw[0])) if len(h_pts_raw) > 0 else (0, 0)
            is_finished = (h_act + a_act > 150) 

            h_pen, h_rep, h_gtd, h_out = get_injury_impact(h_n_en, raw_inj) 
            a_pen, a_rep, a_gtd, a_out = get_injury_impact(a_n_en, raw_inj) 
            
            # 疲勞加權
            if h_id in b2b_data: h_pen += 3.5; h_rep.append("🔋 主B2B")
            if a_id in b2b_data:
                y_loc = b2b_data[a_id]
                a_pen += 5.5 if y_loc == "Away" else 4.0
                a_rep.append("✈️ 客B2B" if y_loc == "Away" else "🔋 客B2B")
                if TEAM_ZONE.get(a_n_en) != TEAM_ZONE.get(h_n_en): a_pen += 1.5; a_rep.append("🌎 跨區")

            h_d, a_d = s_h[s_h["TEAM_ID"] == h_id].iloc[0], s_a[s_a["TEAM_ID"] == a_id].iloc[0] 
            
            # 均值回歸計算
            if not s_last5.empty:
                h_l5, a_l5 = s_last5[s_last5["TEAM_ID"] == h_id], s_last5[s_last5["TEAM_ID"] == a_id]
                h_off = h_d["OFF_RATING"] * 0.7 + min(h_l5.iloc[0]["OFF_RATING"], h_d["OFF_RATING"]*1.05) * 0.3 if not h_l5.empty else h_d["OFF_RATING"]
                a_off = a_d["OFF_RATING"] * 0.7 + min(a_l5.iloc[0]["OFF_RATING"], a_d["OFF_RATING"]*1.05) * 0.3 if not a_l5.empty else a_d["OFF_RATING"]
                h_def, a_def = h_d["DEF_RATING"] * 0.7 + h_l5.iloc[0]["DEF_RATING"] * 0.3 if not h_l5.empty else h_d["DEF_RATING"], a_d["DEF_RATING"] * 0.7 + a_l5.iloc[0]["DEF_RATING"] * 0.3 if not a_l5.empty else a_d["DEF_RATING"]
            else:
                h_off, h_def, a_off, a_def = h_d["OFF_RATING"], h_d["DEF_RATING"], a_d["OFF_RATING"], a_d["DEF_RATING"]

            game_pace = (2 * h_d["PACE"] * a_d["PACE"]) / (h_d["PACE"] + a_d["PACE"])
            h_pie, a_pie = calculate_weighted_pie(p_stats, h_id, h_out), calculate_weighted_pie(p_stats, a_id, a_out)
            elo = (h_win_pct := h_d["W_PCT"] - (a_win_pct := a_d["W_PCT"])) * 6.0
            
            h_s = round((h_off*0.55 + a_def*0.45) * (game_pace/100) + 2.5 - h_pen + (h_pie-12)*0.4 + elo/2, 1) 
            a_s = round((a_off*0.55 + h_def*0.45) * (game_pace/100) - a_pen + (a_pie-12)*0.4 - elo/2, 1) 

            sim_diff, sim_total = run_monte_carlo(h_s, a_s, game_pace)
            prob_win_h = np.mean(sim_diff > 0)
            
            # 盤口與 EV
            api_team_name = ODDS_API_TEAMS.get(h_n_en)
            market_spread = live_odds.get(api_team_name, {}).get("spread")
            combined_reports = " / ".join(h_rep + a_rep) if (h_rep + a_rep) else "✅ 完整"

            if market_spread is not None:
                prob_cover_h = np.mean(sim_diff > -market_spread)
                ev_h, ev_a = calculate_ev(prob_cover_h), calculate_ev(1 - prob_cover_h)
                if ev_h > 0: all_ev_opportunities.append({"對戰組合": f"{a_n}@{h_n}", "類型":"讓分", "推薦":h_n, "過盤率":f"{prob_cover_h:.1%}", "EV":ev_h, "⚠️ 關鍵變數":combined_reports})
                if ev_a > 0: all_ev_opportunities.append({"對戰組合": f"{a_n}@{h_n}", "類型":"讓分", "推薦":a_n, "過盤率":f"{(1-prob_cover_h):.1%}", "EV":ev_a, "⚠️ 關鍵變數":combined_reports})

            match_data.append({ 
                "對戰組合": f"{a_n} @ {h_n}", "AI比分": f"{a_s} : {h_s}", "主勝率": f"{prob_win_h:.1%}", 
                "市場讓分": market_spread if market_spread else "-", "實際比分": f"{a_act}:{h_act}" if is_finished else "-", 
                "h_s": h_s, "a_s": a_s, "pace": game_pace, "reports": h_rep + a_rep
            }) 
        except: continue 

    # 顯示 TOP 5
    if all_ev_opportunities:
        st.header("🔥 今日 TOP 5 價值投注 (含關鍵變數雷達)")
        ev_df = pd.DataFrame(all_ev_opportunities).sort_values(by="EV", ascending=False).head(5)
        ev_df["EV"] = ev_df["EV"].apply(lambda x: f"+{x:.1%}")
        st.dataframe(ev_df, use_container_width=True)

    st.divider() 
    st.header("📊 完整賽事數據") 
    if match_data:
        st.dataframe(pd.DataFrame(match_data)[["對戰組合", "AI比分", "主勝率", "市場讓分", "實際比分"]], use_container_width=True) 

    # 🛡️ 確保 B 功能（解析儀）絕對存在
    st.divider() 
    st.header("🔍 單場深度解析與手動測試儀") 
    if match_data:
        s_game = st.selectbox("請選擇場次進行模擬：", match_data, format_func=lambda x: x["對戰組合"]) 
        col_a, col_b = st.columns(2) 
        with col_a: 
            st.subheader("📝 變數與陣容報告") 
            if s_game["reports"]: 
                for r in s_game["reports"]: st.warning(r) 
            else: st.success("✅ 無異常變數。") 
        with col_b: 
            st.subheader("🎲 萬次模擬預測過盤率") 
            u_spread = st.number_input("輸入台彩讓分 (主隊讓分填負數)", value=-2.5, step=0.5) 
            sim_diffs, _ = run_monte_carlo(s_game['h_s'], s_game['a_s'], s_game['pace'])
            p_cover = np.mean(sim_diffs > -u_spread)
            st.metric("預估過盤率", f"{p_cover:.1%}", delta=f"EV: {calculate_ev(p_cover):.1%}")

st.caption("NBA AI V31.4 - 穩定版：修復 API 連線逾時與 headers 偽裝，確保 3/17 賽程抓取穩定")