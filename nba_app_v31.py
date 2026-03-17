import streamlit as st 
import pandas as pd 
import requests 
import numpy as np
import time
from nba_api.stats.endpoints import leaguedashteamstats
from datetime import datetime, timedelta 

# ---------------------------------------------------------
# 0. 核心配置與對照庫
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

ODDS_API_TEAMS = {k: k for k in TEAM_CN.keys()} 
ODDS_API_TEAMS["LA Clippers"] = "Los Angeles Clippers"

STAR_PLAYERS = { 
    "Lakers": ["LeBron James", "Anthony Davis", "D'Angelo Russell"],  
    "Nuggets": ["Nikola Jokic", "Jamal Murray", "Aaron Gordon"], 
    "Celtics": ["Jayson Tatum", "Jaylen Brown", "Kristaps Porzingis"],  
    "Mavericks": ["Luka Doncic", "Kyrie Irving"], 
    "Thunder": ["Shai Gilgeous-Alexander", "Jalen Williams", "Chet Holmgren"],  
    "Timberwolves": ["Anthony Edwards", "Rudy Gobert", "Karl-Anthony Towns"], 
    "Bucks": ["Giannis Antetokounmpo", "Damian Lillard"],  
    "Warriors": ["Stephen Curry", "Draymond Green"], 
    "Suns": ["Kevin Durant", "Devin Booker", "Bradley Beal"], 
    "76ers": ["Joel Embiid", "Tyrese Maxey"], 
    "Clippers": ["Kawhi Leonard", "James Harden"], 
    "Heat": ["Jimmy Butler", "Bam Adebayo"], 
    "Kings": ["De'Aaron Fox", "Domantas Sabonis"] 
} 

# ---------------------------------------------------------
# 1. 強效穩定數據引擎
# ---------------------------------------------------------

@st.cache_data(ttl=10800) 
def fetch_injury_raw(): 
    try: 
        r = requests.get("https://www.cbssports.com/nba/injuries/", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return r.text.lower()
    except: return ""

def get_injury_impact(team_name, raw_text): 
    if not raw_text: return 0, []
    penalty, reports = 0, []
    mascot = team_name.split()[-1] 
    search_key = "76ers" if mascot == "76ers" else mascot 
    if search_key in STAR_PLAYERS: 
        for player in STAR_PLAYERS[search_key]: 
            if player.lower() in raw_text: 
                idx = raw_text.find(player.lower())
                chunk = raw_text[idx:idx+250]
                if any(word in chunk for word in ["out", "expected to be out", "surgery", "unavailable"]): 
                    penalty += 5.0; reports.append(f"🚨 [{TEAM_CN.get(team_name, mascot)}] {player} - 確定缺陣")
                elif any(word in chunk for word in ["questionable", "gtd", "decision", "doubtful"]): 
                    penalty += 2.5; reports.append(f"⚠️ [{TEAM_CN.get(team_name, mascot)}] {player} - 出戰成疑")
    return min(penalty, 9.5), reports

@st.cache_data(ttl=3600) 
def fetch_nba_lite(game_date_str): 
    date_obj = datetime.strptime(game_date_str, '%Y-%m-%d')
    date_api = date_obj.strftime('%m/%d/%Y') 
    
    headers = {
        'Host': 'stats.nba.com',
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'x-nba-stats-origin': 'stats',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'x-nba-stats-token': 'true',
        'Referer': 'https://www.nba.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        # 直接調用底層 Scoreboard API
        sb_url = f"https://stats.nba.com/stats/scoreboardv2?DayOffset=0&LeagueID=00&gameDate={date_api}"
        with requests.Session() as session:
            r = session.get(sb_url, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()
            res = data['resultSets']
            games_df = pd.DataFrame(res[0]['rowSet'], columns=res[0]['headers'])
            line_score = pd.DataFrame(res[1]['rowSet'], columns=res[1]['headers'])

        time.sleep(1.0)
        
        # 獲取球隊進階數據
        ts = leaguedashteamstats.LeagueDashTeamStats(date_to_nullable=date_api, headers=headers, timeout=20)
        stats_df = ts.get_data_frames()[0]
        
        return games_df, line_score, stats_df
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=900) 
def fetch_live_odds(api_key):
    if not api_key: return {}
    try:
        url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=spreads,totals&bookmakers=pinnacle"
        r = requests.get(url, timeout=10).json()
        odds_dict = {g.get('home_team'): {"spread": next((o['point'] for m in g.get('bookmakers', [{}])[0].get('markets', []) if m['key'] == 'spreads' for o in m['outcomes'] if o['name'] == g.get('home_team')), None), "total": next((m['outcomes'][0]['point'] for m in g.get('bookmakers', [{}])[0].get('markets', []) if m['key'] == 'totals'), None)} for g in r if g.get('bookmakers')}
        return odds_dict
    except: return {}

# ---------------------------------------------------------
# 2. 蒙地卡羅萬次模擬引擎
# ---------------------------------------------------------
def run_monte_carlo(h_pts, a_pts, n_sims=10000):
    sim_h = np.random.normal(loc=h_pts, scale=12.0, size=n_sims)
    sim_a = np.random.normal(loc=a_pts, scale=12.0, size=n_sims)
    return sim_h - sim_a, sim_h + sim_a

def calculate_ev(win_prob, odds=1.90):
    return (win_prob * (odds - 1)) - (1 - win_prob)

# ---------------------------------------------------------
# 3. UI 介面設定
# ---------------------------------------------------------
st.set_page_config(page_title="NBA AI V32.2 終極穩定版", layout="wide", page_icon="🏀") 

st.sidebar.header("🗓️ 歷史回測與實戰控制") 
target_date = st.sidebar.date_input("選擇賽事日期", datetime.now() - timedelta(hours=8)) 
formatted_date = target_date.strftime('%Y-%m-%d') 

st.sidebar.divider()
st.sidebar.markdown("### 🤖 自動化盤口分析")
api_key = st.sidebar.text_input("輸入 The Odds API 金鑰", type="password")

st.title(f"🏀 NBA AI V32 職業盤: 蒙地卡羅與 EV 決策引擎 ({formatted_date})") 

with st.spinner("啟動終極引擎：正在突破 NBA 伺服器防護並抓取數據..."): 
    games_df, line_df, stats_df = fetch_nba_lite(formatted_date) 
    raw_inj = fetch_injury_raw() 
    live_odds = fetch_live_odds(api_key) if api_key else {}

if games_df.empty: 
    st.warning(f"📅 找不到 {formatted_date} 的賽程數據。")
    st.info("💡 貼心提醒：\n1. 如果是台灣早上時間，請手動將日期切換至昨天。\n2. 若確定日期正確，可能是 NBA 伺服器流量過載，請按 'C' 清除快取後重整。")
else:
    match_data, hit_count, total_finished = [], 0, 0
    t_dict = dict(zip(stats_df['TEAM_ID'], stats_df['TEAM_NAME'])) if not stats_df.empty else {}

    st.header("📊 蒙地卡羅 EV 決策總表 (10,000 次模擬)")
    
    for _, row in games_df.iterrows(): 
        h_id, a_id = row["HOME_TEAM_ID"], row["VISITOR_TEAM_ID"] 
        h_n_en, a_n_en = t_dict.get(h_id, ""), t_dict.get(a_id, "")
        if not h_n_en or not a_n_en: continue

        h_n, a_n = TEAM_CN.get(h_n_en, h_n_en), TEAM_CN.get(a_n_en, a_n_en) 
        
        try: 
            # 解析比分
            h_pts_raw = line_df.loc[line_df['TEAM_ID'] == h_id, 'PTS'].values 
            a_pts_raw = line_df.loc[line_df['TEAM_ID'] == a_id, 'PTS'].values 
            h_act, a_act = (int(h_pts_raw[0]), int(a_pts_raw[0])) if len(h_pts_raw) > 0 and pd.notna(h_pts_raw[0]) else (0, 0)
            is_finished = (h_act > 0 and a_act > 0)

            # 基礎實力
            h_d = stats_df[stats_df["TEAM_ID"] == h_id].iloc[0]
            a_d = stats_df[stats_df["TEAM_ID"] == a_id].iloc[0]
            
            # 傷兵評估
            h_pen, h_rep = get_injury_impact(h_n_en, raw_inj) 
            a_pen, a_rep = get_injury_impact(a_n_en, raw_inj) 
            
            # 預測分組 (主場優勢 +2.5)
            proj_h = h_d["PTS"] + 2.5 - h_pen
            proj_a = a_d["PTS"] - a_pen

            # 蒙地卡羅模擬
            sim_diff, _ = run_monte_carlo(proj_h, proj_a)
            prob_h = np.mean(sim_diff > 0)
            
            # 決策判斷
            decision = "⚠️ 五五波 (避開)"
            if prob_h > 0.58: decision = f"主勝 ({prob_h:.1%})"
            elif prob_h < 0.42: decision = f"客勝 ({(1-prob_h):.1%})"

            # 命中率統計
            hit_status = "無"
            if is_finished and "⚠️" not in decision:
                total_finished += 1
                if (prob_h > 0.5 and h_act > a_act) or (prob_h < 0.5 and a_act > h_act):
                    hit_status = "✅"; hit_count += 1
                else: hit_status = "❌"
            
            # 市場賠率與讓分
            m_team = ODDS_API_TEAMS.get(h_n_en)
            m_spread = live_odds.get(m_team, {}).get("spread", "-")

            match_data.append({
                "對戰組合": f"{a_n} @ {h_n}", 
                "AI預期分差": f"{proj_a:.1f} : {proj_h:.1f}", 
                "市場讓分": m_spread, 
                "最佳決策": decision, 
                "實際比分": f"{a_act} : {h_act}" if is_finished else "進行中", 
                "勝負命中": hit_status,
                "reports": h_rep + a_rep, "proj_h": proj_h, "proj_a": proj_a
            }) 
        except: continue 

    # 顯示主表格
    df_display = pd.DataFrame(match_data)
    if not df_display.empty:
        st.dataframe(df_display[["對戰組合", "AI預期分差", "市場讓分", "最佳決策", "實際比分", "勝負命中"]], use_container_width=True)

    # 側邊欄即時戰果
    if total_finished > 0:
        st.sidebar.divider()
        st.sidebar.metric("🎯 本日 EV 策略命中率", f"{(hit_count/total_finished):.1%}")

    st.divider() 
    st.header("🔍 蒙地卡羅深度解析儀 (單場演算)") 
    if match_data:
        s_g = st.selectbox("請選擇場次進行一萬次深度演算：", match_data, format_func=lambda x: x["對戰組合"]) 
        col_a, col_b = st.columns(2) 
        
        with col_a: 
            st.subheader("📝 陣容即時情報") 
            if s_g["reports"]: 
                for r in s_g["reports"]: st.error(r) if "🚨" in r else st.warning(r)
            else: st.success("✅ 目前該場次暫無重大星級球員缺陣。") 
            
        with col_b: 
            st.subheader("🎲 自定義 EV 試算") 
            u_spread = st.number_input("輸入主隊目前讓分 (如 -4.5)", value=-4.5, step=0.5) 
            u_total = st.number_input("輸入總分盤口 (如 225.5)", value=225.5, step=0.5) 
            
            sd, stotal = run_monte_carlo(s_g['proj_h'], s_g['proj_a'])
            pc_h, pc_a = np.mean(sd > -u_spread), np.mean(sd < -u_spread)
            po, pu = np.mean(stotal > u_total), np.mean(stotal < u_total)
            
            st.write(f"▶️ **讓分盤結果：**")
            st.write(f"主過盤率: `{pc_h:.1%}` | EV: `{calculate_ev(pc_h):.1%}`")
            st.write(f"客過盤率: `{pc_a:.1%}` | EV: `{calculate_ev(pc_a):.1%}`")
            st.divider()
            st.write(f"▶️ **大小分結果：**")
            st.write(f"大分率: `{po:.1%}` | 小分率: `{pu:.1%}`")

st.caption("NBA AI V32.2 - 已修正 V32 變數錯誤並優化 Header 穿透性。")
