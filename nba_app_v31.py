import streamlit as st 
import pandas as pd 
import requests 
import numpy as np
import time
import random
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

ODDS_API_TEAMS = {k: k for k in TEAM_CN.keys()} 
ODDS_API_TEAMS["LA Clippers"] = "Los Angeles Clippers"

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
# 1. 終極數據引擎 (V31.6 強力偽裝與異常容錯)
# ---------------------------------------------------------

# 模擬隨機 Referer
def get_headers():
    refs = [
        "https://www.nba.com/",
        "https://stats.nba.com/teams/advanced/",
        "https://stats.nba.com/scores/"
    ]
    return {
        'Host': 'stats.nba.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': random.choice(refs),
        'Origin': 'https://www.nba.com',
        'Connection': 'keep-alive'
    }

# 🛡️ 帶有強力延時與隨機性的請求函數
def call_nba_api_stable(endpoint_class, **kwargs):
    for i in range(4): # 增加到 4 次重試
        try:
            time.sleep(random.uniform(2.0, 4.0)) # 隨機延時 2-4 秒，模擬真人行為
            return endpoint_class(**kwargs, headers=get_headers(), timeout=30).get_data_frames()[0]
        except Exception as e:
            if i == 3: raise e
            continue

@st.cache_data(ttl=600) 
def fetch_injury_raw(): 
    try: 
        r = requests.get("https://www.cbssports.com/nba/injuries/", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        return r.text.lower()
    except: return "" 

def get_injury_impact(team_name, raw_html_text): 
    if not raw_html_text: return 0, [], False, []
    mascot = team_name.split()[-1] 
    penalty, reports, has_gtd, out_players = 0, [], False, []
    search_key = "76ers" if mascot == "76ers" else mascot 
    if search_key in STAR_PLAYERS: 
        for player in STAR_PLAYERS[search_key]: 
            if player.lower() in raw_html_text: 
                idx = raw_html_text.find(player.lower()) 
                chunk = raw_html_text[idx:idx+250]
                if any(word in chunk for word in ["out", "expected to be out", "surgery"]): 
                    penalty += 5.0; reports.append(f"🚨 {player}(缺)"); out_players.append(player)
                elif any(word in chunk for word in ["questionable", "gtd", "decision"]): 
                    penalty += 2.5; reports.append(f"⚠️ {player}(?)"); has_gtd = True; out_players.append(player)
    return min(penalty, 9.5), reports, has_gtd, out_players 

@st.cache_data(ttl=1800) 
def fetch_nba_master(game_date_str): 
    game_date_obj = datetime.strptime(game_date_str, '%Y-%m-%d')
    date_api_format = game_date_obj.strftime('%m/%d/%Y') 
    yest_str = (game_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
    team_dict = {t["id"]: t["full_name"] for t in teams.get_teams()} 
    
    try:
        # Scoreboard 本身通常比較穩，先抓
        sb_inst = scoreboardv2.ScoreboardV2(game_date=game_date_str, headers=get_headers(), timeout=30)
        games = sb_inst.get_data_frames()[0].drop_duplicates(subset=['GAME_ID']) 
        line_score = sb_inst.get_data_frames()[1] 
        
        # 使用穩定請求函數抓取核心數據
        s_h = call_nba_api_stable(leaguedashteamstats.LeagueDashTeamStats, measure_type_detailed_defense="Advanced", location_nullable="Home", date_to_nullable=date_api_format)
        s_a = call_nba_api_stable(leaguedashteamstats.LeagueDashTeamStats, measure_type_detailed_defense="Advanced", location_nullable="Road", date_to_nullable=date_api_format)
        p_stats = call_nba_api_stable(leaguedashplayerstats.LeagueDashPlayerStats, measure_type_detailed_defense="Advanced", date_to_nullable=date_api_format)
        
        # B2B 邏輯保留
        y_sb = scoreboardv2.ScoreboardV2(game_date=yest_str, headers=get_headers(), timeout=30).get_data_frames()[0]
        b2b_data = {row["HOME_TEAM_ID"]: "Home" for _, row in y_sb.iterrows()}
        b2b_data.update({row["VISITOR_TEAM_ID"]: "Away" for _, row in y_sb.iterrows()})

        try: s_last5 = call_nba_api_stable(leaguedashteamstats.LeagueDashTeamStats, measure_type_detailed_defense="Advanced", last_n_games=5, date_to_nullable=date_api_format)
        except: s_last5 = pd.DataFrame()
            
        return team_dict, games, line_score, s_h, s_a, p_stats, b2b_data, s_last5
    except Exception as e:
        st.error(f"NBA API 通訊失敗 (V31.6 保護機制已啟動): {e}")
        return {}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}, pd.DataFrame()

@st.cache_data(ttl=900) 
def fetch_live_odds(api_key):
    if not api_key: return {}
    try:
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=spreads,totals&bookmakers=pinnacle"
        r = requests.get(url, timeout=10).json()
        odds_dict = {g.get('home_team'): {"spread": next((o['point'] for m in g.get('bookmakers', [{}])[0].get('markets', []) if m['key'] == 'spreads' for o in m['outcomes'] if o['name'] == g.get('home_team')), None), "total": next((m['outcomes'][0]['point'] for m in g.get('bookmakers', [{}])[0].get('markets', []) if m['key'] == 'totals'), None)} for g in r if g.get('bookmakers')}
        return odds_dict
    except: return {}

def calculate_weighted_pie(p_stats_df, team_id, out_players):
    active = p_stats_df[(p_stats_df["TEAM_ID"] == team_id) & (~p_stats_df["PLAYER_NAME"].isin(out_players)) & (p_stats_df["MIN"] > 15)]
    if active.empty: return 0
    top5 = active.nlargest(5, 'PIE')
    return (top5['PIE'] * top5['MIN']).sum() / top5['MIN'].sum()

def run_monte_carlo(h_s, a_s, game_pace, n_sims=10000):
    sim_pace = np.random.normal(loc=game_pace, scale=4.0, size=n_sims)
    h_p, a_p = np.random.normal(loc=h_s/game_pace, scale=0.12, size=n_sims), np.random.normal(loc=a_s/game_pace, scale=0.12, size=n_sims)
    return sim_pace * h_p - sim_pace * a_p, sim_pace * h_p + sim_pace * a_p

def calculate_ev(win_prob, decimal_odds=1.909):
    return (win_prob * (decimal_odds - 1)) - (1 - win_prob)

# ---------------------------------------------------------
# 2. UI 介面整合 (嚴格遵守增量更新原則)
# ---------------------------------------------------------
st.set_page_config(page_title="NBA AI 攻防大師 V31.6", layout="wide", page_icon="🏀") 

st.sidebar.header("🗓️ 系統控制台") 
target_date = st.sidebar.date_input("選擇日期", datetime.now() - timedelta(hours=8)) 
formatted_date = target_date.strftime('%Y-%m-%d') 

st.sidebar.divider()
api_key = st.secrets.get("ODDS_API_KEY", "")
if not api_key: api_key = st.sidebar.text_input("輸入 API 金鑰 (選填)", type="password")

st.title(f"🏀 NBA AI V31.6 職業戰略儀表板 ({formatted_date})") 

with st.spinner("⏳ 正在慢速同步 NBA 數據庫以避開防火牆偵測..."): 
    t_dict, games_df, line_df, s_h, s_a, p_stats, b2b_data, s_last5 = fetch_nba_master(formatted_date) 
    raw_inj = fetch_injury_raw() 
    live_odds = fetch_live_odds(api_key) if target_date >= (datetime.now() - timedelta(hours=24)).date() else {}

if games_df.empty: 
    st.info(f"📅 {formatted_date} 此日期暫無賽程數據。建議嘗試選擇 3/17 以對位台彩賽事。") 
else:
    match_data, all_ev_opportunities = [], []
    is_historical = target_date < (datetime.now() - timedelta(hours=8)).date() 

    for _, row in games_df.iterrows(): 
        h_id, a_id = row["HOME_TEAM_ID"], row["VISITOR_TEAM_ID"] 
        h_n_en, a_n_en = t_dict.get(h_id), t_dict.get(a_id) 
        h_n, a_n = TEAM_CN.get(h_n_en, h_n_en), TEAM_CN.get(a_n_en, a_n_en) 
        
        try: 
            h_pts_raw, a_pts_raw = line_df.loc[line_df['TEAM_ID'] == h_id, 'PTS'].values, line_df.loc[line_df['TEAM_ID'] == a_id, 'PTS'].values 
            h_act, a_act = (int(h_pts_raw[0]), int(a_pts_raw[0])) if len(h_pts_raw) > 0 else (0, 0)
            is_finished = (h_act + a_act > 150) 

            h_pen, h_rep, h_gtd, h_out = get_injury_impact(h_n_en, raw_inj) 
            a_pen, a_rep, a_gtd, a_out = get_injury_impact(a_n_en, raw_inj) 
            if is_historical: h_pen, a_pen = h_pen * 0.5, a_pen * 0.5 

            if h_id in b2b_data: h_pen += 3.5; h_rep.append("🔋主B2B")
            if a_id in b2b_data:
                y_l = b2b_data[a_id]
                a_pen += 5.5 if y_l == "Away" else 4.0
                a_rep.append("✈️客B2B" if y_l == "Away" else "🔋客B2B")
                if TEAM_ZONE.get(a_n_en) != TEAM_ZONE.get(h_n_en): a_pen += 1.5; a_rep.append("🌎跨區")

            h_d, a_d = s_h[s_h["TEAM_ID"] == h_id].iloc[0], s_a[s_a["TEAM_ID"] == a_id].iloc[0] 
            
            if not s_last5.empty:
                hl5, al5 = s_last5[s_last5["TEAM_ID"] == h_id], s_last5[s_last5["TEAM_ID"] == a_id]
                h_off = h_d["OFF_RATING"] * 0.7 + min(hl5.iloc[0]["OFF_RATING"], h_d["OFF_RATING"]*1.05) * 0.3 if not hl5.empty else h_d["OFF_RATING"]
                a_off = a_d["OFF_RATING"] * 0.7 + min(al5.iloc[0]["OFF_RATING"], a_d["OFF_RATING"]*1.05) * 0.3 if not al5.empty else a_d["OFF_RATING"]
                h_def = h_d["DEF_RATING"] * 0.7 + hl5.iloc[0]["DEF_RATING"] * 0.3 if not hl5.empty else h_d["DEF_RATING"]
                a_def = a_d["DEF_RATING"] * 0.7 + al5.iloc[0]["DEF_RATING"] * 0.3 if not al5.empty else a_d["DEF_RATING"]
            else: h_off, h_def, a_off, a_def = h_d["OFF_RATING"], h_d["DEF_RATING"], a_d["OFF_RATING"], a_d["DEF_RATING"]

            game_p = (2 * h_d["PACE"] * a_d["PACE"]) / (h_d["PACE"] + a_d["PACE"])
            h_pie, a_pie = calculate_weighted_pie(p_stats, h_id, h_out), calculate_weighted_pie(p_stats, a_id, a_out)
            elo = (h_d["W_PCT"] - a_d["W_PCT"]) * 6.0
            
            h_s = round((h_off*0.55 + a_def*0.45) * (game_p/100) + 2.5 - h_pen + (h_pie-12)*0.4 + elo/2, 1) 
            a_s = round((a_off*0.55 + h_def*0.45) * (game_p/100) - a_pen + (a_pie-12)*0.4 - elo/2, 1) 

            s_diff, s_total = run_monte_carlo(h_s, a_s, game_p)
            prob_h = np.mean(s_diff > 0)
            
            m_team = ODDS_API_TEAMS.get(h_n_en)
            m_spread = live_odds.get(m_team, {}).get("spread")
            comb_rep = " / ".join(h_rep + a_rep) if (h_rep + a_rep) else "✅ 完整"

            if m_spread is not None:
                p_c_h = np.mean(s_diff > -m_spread)
                ev_h, ev_a = calculate_ev(p_c_h), calculate_ev(1 - p_c_h)
                if ev_h > 0: all_ev_opportunities.append({"對戰": f"{a_n}@{h_n}", "類型":"讓分", "推薦":h_n, "過盤率":f"{p_c_h:.1%}", "EV":ev_h, "⚠️關鍵變數":comb_rep})
                if ev_a > 0: all_ev_opportunities.append({"對戰": f"{a_n}@{h_n}", "類型":"讓分", "推薦":a_n, "過盤率":f"{(1-p_c_h):.1%}", "EV":ev_a, "⚠️關鍵變數":comb_rep})

            match_data.append({"對戰組合": f"{a_n} @ {h_n}", "AI預測": f"{a_s}:{h_s}", "主勝率": f"{prob_h:.1%}", "讓分盤": m_spread if m_spread else "-", "實際比分": f"{a_act}:{h_act}" if is_finished else "-", "h_s": h_s, "a_s": a_s, "pace": game_p, "reports": h_rep + a_rep}) 
        except: continue 

    if all_ev_opportunities:
        st.header("🔥 今日 TOP 5 價值投注 (含關鍵變數雷達)")
        ev_df = pd.DataFrame(all_ev_opportunities).sort_values(by="EV", ascending=False).head(5)
        ev_df["EV"] = ev_df["EV"].apply(lambda x: f"+{x:.1%}")
        st.dataframe(ev_df, use_container_width=True)

    st.divider() 
    st.header("📊 完整賽事預測 (及歷史比分)") 
    if match_data: st.dataframe(pd.DataFrame(match_data)[["對戰組合", "AI預測", "主勝率", "讓分盤", "實際比分"]], use_container_width=True) 

    st.divider() 
    st.header("🔍 單場深度解析與手動測試儀") 
    if match_data:
        s_g = st.selectbox("請選擇場次：", match_data, format_func=lambda x: x["對戰組合"]) 
        col_a, col_b = st.columns(2) 
        with col_a: 
            st.subheader("📝 變數與陣容報告") 
            if s_g["reports"]: 
                for r in s_g["reports"]: st.warning(r) 
            else: st.success("✅ 無異常。") 
        with col_b: 
            st.subheader("🎲 蒙地卡羅動態模擬") 
            u_s = st.number_input("台彩讓分 (主隊讓分填負數)", value=-2.5, step=0.5) 
            sd, _ = run_monte_carlo(s_g['h_s'], s_g['a_s'], s_g['pace'])
            pc = np.mean(sd > -u_s)
            st.metric("預估過盤率", f"{pc:.1%}", delta=f"EV: {calculate_ev(pc):.1%}")

st.caption("NBA AI V31.6 - 終極穩定版：導入連線隨機時延與重試機制，全面對抗官網封鎖")