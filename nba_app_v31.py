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
# 1. 輕量化穩定數據引擎 (V32.4 最終強攻版)
# ---------------------------------------------------------

@st.cache_data(ttl=10800) 
def fetch_injury_raw(): 
    try: 
        # 模擬真人 User-Agent
        r = requests.get("https://www.cbssports.com/nba/injuries/", 
                         headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}, 
                         timeout=10)
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
    
    # 隨機身分列表
    ua_list = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    ]
    
    headers = {
        'Host': 'stats.nba.com',
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'x-nba-stats-origin': 'stats',
        'User-Agent': np.random.choice(ua_list),
        'x-nba-stats-token': 'true',
        'Referer': 'https://www.nba.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        with requests.Session() as session:
            # 隨機延遲 1-2.5 秒，避開機器人偵測
            time.sleep(np.random.uniform(1.0, 2.5))
            
            # 第一步：嘗試抓取當日賽程 (延長 timeout 到 30 秒)
            sb_url = f"https://stats.nba.com/stats/scoreboardv2?DayOffset=0&LeagueID=00&gameDate={date_api}"
            r = session.get(sb_url, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            res = data['resultSets']
            games_df = pd.DataFrame(res[0]['rowSet'], columns=res[0]['headers'])
            line_score = pd.DataFrame(res[1]['rowSet'], columns=res[1]['headers'])

            # 🛡️ 備援機制：今日無數據則嘗試前一日
            if games_df.empty:
                prev_date_api = (date_obj - timedelta(days=1)).strftime('%m/%d/%Y')
                sb_url_prev = f"https://stats.nba.com/stats/scoreboardv2?DayOffset=0&LeagueID=00&gameDate={prev_date_api}"
                r_prev = session.get(sb_url_prev, headers=headers, timeout=30)
                data_prev = r_prev.json()
                res_prev = data_prev['resultSets']
                games_df = pd.DataFrame(res_prev[0]['rowSet'], columns=res_prev[0]['headers'])
                line_score = pd.DataFrame(res_prev[1]['rowSet'], columns=res_prev[1]['headers'])
                st.sidebar.info(f"💡 今日 API 無回應，已載入美國時間昨日數據")

        time.sleep(1.5)
        
        # 獲取球隊統計數據 (同樣增加 timeout)
        ts = leaguedashteamstats.LeagueDashTeamStats(date_to_nullable=date_api, headers=headers, timeout=30)
        stats_df = ts.get_data_frames()[0]
        
        return games_df, line_score, stats_df
    except Exception as e:
        st.sidebar.error(f"⚠️ NBA 伺服器忙碌中 (Timeout)。請按 'C' 重試。")
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
# 3. UI 介面
# ---------------------------------------------------------
st.set_page_config(page_title="NBA AI V32.4 最終強攻版", layout="wide", page_icon="🏀") 

st.sidebar.header("🗓️ 歷史回測與實戰控制") 
target_date = st.sidebar.date_input("選擇賽事日期", datetime.now() - timedelta(hours=8)) 
formatted_date = target_date.strftime('%Y-%m-%d') 

st.sidebar.divider()
st.sidebar.markdown("### 🤖 自動化盤口分析")
api_key = st.sidebar.text_input("輸入 API 金鑰 (選填)", type="password")

st.title(f"🏀 NBA AI V32 職業盤: 蒙地卡羅與 EV 決策引擎 ({formatted_date})") 

with st.spinner("啟動穩定引擎：正在繞過防火牆並讀取數據..."): 
    games_df, line_df, stats_df = fetch_nba_lite(formatted_date) 
    raw_inj = fetch_injury_raw() 
    live_odds = fetch_live_odds(api_key) if api_key else {}

if games_df.empty: 
    st.info(f"📅 查無賽程。可能是 NBA API 暫時阻擋連線，請嘗試 Reboot App 或按 'C' 清除快取。") 
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
            h_pts_raw = line_df.loc[line_df['TEAM_ID'] == h_id, 'PTS'].values 
            a_pts_raw = line_df.loc[line_df['TEAM_ID'] == a_id, 'PTS'].values 
            h_act, a_act = (int(h_pts_raw[0]), int(a_pts_raw[0])) if len(h_pts_raw) > 0 and pd.notna(h_pts_raw[0]) else (0, 0)
            is_finished = (h_act > 0 and a_act > 0)

            h_d = stats_df[stats_df["TEAM_ID"] == h_id].iloc[0]
            a_d = stats_df[stats_df["TEAM_ID"] == a_id].iloc[0]
            
            h_pen, h_rep = get_injury_impact(h_n_en, raw_inj) 
            a_pen, a_rep = get_injury_impact(a_n_en, raw_inj) 
            
            proj_h = h_d["PTS"] + 2.5 - h_pen
            proj_a = a_d["PTS"] - a_pen

            sim_diff, _ = run_monte_carlo(proj_h, proj_a)
            prob_h = np.mean(sim_diff > 0)
            
            decision = f"⚠️ 五五波"
            if prob_h > 0.55: decision = f"主勝 ({prob_h:.1%})"
            elif prob_h < 0.45: decision = f"客勝 ({(1-prob_h):.1%})"

            hit_status = "無"
            if is_finished and "⚠️" not in decision:
                total_finished += 1
                if (prob_h > 0.5 and h_act > a_act) or (prob_h < 0.5 and a_act > h_act):
                    hit_status = "✅"; hit_count += 1
                else: hit_status = "❌"
            
            m_team = ODDS_API_TEAMS.get(h_n_en)
            m_spread = live_odds.get(m_team, {}).get("spread", "-")

            match_data.append({
                "對戰組合": f"{a_n} @ {h_n}", "AI淨勝分(客:主)": f"{proj_a:.1f} : {proj_h:.1f}", 
                "市場讓分(主)": m_spread, "最佳 EV 決策": decision, 
                "實際比分": f"{a_act} : {h_act}" if is_finished else "-", "勝負命中": hit_status,
                "reports": h_rep + a_rep, "proj_h": proj_h, "proj_a": proj_a
            }) 
        except: continue 

    df_display = pd.DataFrame(match_data)
    if not df_display.empty:
        st.dataframe(df_display[["對戰組合", "AI淨勝分(客:主)", "市場讓分(主)", "最佳 EV 決策", "實際比分", "勝負命中"]], use_container_width=True)

    if total_finished > 0:
        st.sidebar.divider()
        st.sidebar.metric("🎯 本日 EV 策略命中率", f"{(hit_count/total_finished):.1%}")

    st.divider() 
    st.header("🔍 蒙地卡羅深度解析儀") 
    if match_data:
        s_g = st.selectbox("請選擇分析場次：", match_data, format_func=lambda x: x["對戰組合"]) 
        col_a, col_b = st.columns(2) 
        
        with col_a: 
            st.subheader("📝 陣容報告") 
            if s_g["reports"]: 
                for r in s_g["reports"]: st.error(r) if "🚨" in r else st.warning(r)
            else: st.success("✅ 目前無重大傷病。") 
            
        with col_b: 
            st.subheader("🎲 動態 EV 模擬") 
            u_spread = st.number_input("主隊讓分", value=-4.5, step=0.5) 
            u_total = st.number_input("總分盤口", value=225.5, step=0.5) 
            
            sd, stotal = run_monte_carlo(s_g['proj_h'], s_g['proj_a'])
            pc_h, pc_a = np.mean(sd > -u_spread), np.mean(sd < -u_spread)
            po, pu = np.mean(stotal > u_total), np.mean(stotal < u_total)
            
            st.write(f"主過盤率: `{pc_h:.1%}` | EV: `{calculate_ev(pc_h):.1%}`")
            st.write(f"客過盤率: `{pc_a:.1%}` | EV: `{calculate_ev(pc_a):.1%}`")
            st.divider()
            st.write(f"大分率: `{po:.1%}` | 小分率: `{pu:.1%}`")

st.caption("NBA AI V32.4 - 最終強攻版：隨機變造身分、30秒超長等待、自動補償昨日數據")
