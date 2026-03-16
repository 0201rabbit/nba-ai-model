import streamlit as st 
import pandas as pd 
import requests 
import numpy as np
from bs4 import BeautifulSoup 
from nba_api.stats.endpoints import leaguedashteamstats, scoreboardv2, leaguedashplayerstats 
from nba_api.stats.static import teams 
from datetime import datetime, timedelta 

# ------------------------ 
# 0 核心配置與中英對照庫 
# ------------------------ 
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

PLAYER_CN = { 
    "LeBron James": "詹姆斯", "Anthony Davis": "戴維斯", "D'Angelo Russell": "羅素", "Austin Reaves": "里夫斯", 
    "Nikola Jokic": "約基奇", "Jamal Murray": "莫瑞", "Aaron Gordon": "高登", "Michael Porter Jr.": "小波特", 
    "Jayson Tatum": "塔圖姆", "Jaylen Brown": "布朗", "Kristaps Porzingis": "波辛吉斯", "Derrick White": "懷特", "Jrue Holiday": "哈勒戴", 
    "Luka Doncic": "唐西奇", "Kyrie Irving": "厄文", "Dereck Lively": "萊夫利", 
    "Shai Gilgeous-Alexander": "亞歷山大", "Chet Holmgren": "霍姆格倫", "Jalen Williams": "威廉斯", 
    "Anthony Edwards": "愛德華茲", "Rudy Gobert": "戈貝爾", "Karl-Anthony Towns": "唐斯", 
    "Giannis Antetokounmpo": "字母哥", "Damian Lillard": "里拉德", "Khris Middleton": "米德爾頓", 
    "Stephen Curry": "柯瑞", "Draymond Green": "格林", "Jonathan Kuminga": "庫明加", "Andrew Wiggins": "威金斯", 
    "Kevin Durant": "杜蘭特", "Devin Booker": "布克", "Bradley Beal": "比爾", 
    "Joel Embiid": "恩比德", "Tyrese Maxey": "馬克西", "Paul George": "喬治", 
    "Kawhi Leonard": "雷納德", "James Harden": "哈登", 
    "Jimmy Butler": "巴特勒", "Bam Adebayo": "阿德巴約", 
    "De'Aaron Fox": "福克斯", "Domantas Sabonis": "沙波尼斯" 
} 

# ------------------------ 
# 1 傷兵、數據與盤口引擎 
# ------------------------ 
@st.cache_data(ttl=600) 
def fetch_injury_raw(): 
    headers = {"User-Agent": "Mozilla/5.0"} 
    try: 
        r = requests.get("https://www.cbssports.com/nba/injuries/", headers=headers, timeout=10) 
        return BeautifulSoup(r.text, 'html.parser').get_text(separator=' ', strip=True).lower() 
    except: return "" 

def get_injury_impact(team_name, raw_text): 
    mascot = team_name.split()[-1] 
    penalty, reports, has_gtd = 0, [], False 
    out_players = [] 
    search_key = "76ers" if mascot == "76ers" else mascot 
    t_cn = TEAM_CN.get(team_name, team_name) 
    
    if search_key in STAR_PLAYERS: 
        for player in STAR_PLAYERS[search_key]: 
            full_name = player.lower() 
            if full_name in raw_text: 
                idx = raw_text.find(full_name) 
                chunk = raw_text[idx:idx+150] 
                p_cn = PLAYER_CN.get(player, player) 
                if "out" in chunk or "expected to be out" in chunk: 
                    penalty += 5.0  
                    reports.append(f"🚨 [{t_cn}] {p_cn} - 確定缺陣") 
                    out_players.append(player) 
                elif any(word in chunk for word in ["questionable", "gtd", "decision"]): 
                    penalty += 2.5 
                    reports.append(f"⚠️ [{t_cn}] {p_cn} - 出戰成疑(GTD)") 
                    has_gtd = True 
                    out_players.append(player) 
    
    penalty = min(penalty, 8.5) 
    return penalty, reports, has_gtd, out_players 

@st.cache_data(ttl=3600) 
def fetch_nba_master(game_date_str): 
    game_date_obj = datetime.strptime(game_date_str, '%Y-%m-%d')
    date_api_format = game_date_obj.strftime('%m/%d/%Y') 
    yest_str = (game_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')

    team_dict = {t["id"]: t["full_name"] for t in teams.get_teams()} 
    
    sb = scoreboardv2.ScoreboardV2(game_date=game_date_str) 
    games = sb.get_data_frames()[0].drop_duplicates(subset=['GAME_ID']) 
    line_score = sb.get_data_frames()[1] 
    
    sb_yest = scoreboardv2.ScoreboardV2(game_date=yest_str)
    yest_games = sb_yest.get_data_frames()[0]
    
    b2b_data = {}
    for _, y_row in yest_games.iterrows():
        b2b_data[y_row["HOME_TEAM_ID"]] = "Home"
        b2b_data[y_row["VISITOR_TEAM_ID"]] = "Away"
    
    s_h = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense="Advanced", location_nullable="Home", date_to_nullable=date_api_format).get_data_frames()[0] 
    s_a = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense="Advanced", location_nullable="Road", date_to_nullable=date_api_format).get_data_frames()[0] 
    p_stats = leaguedashplayerstats.LeagueDashPlayerStats(measure_type_detailed_defense="Advanced", date_to_nullable=date_api_format).get_data_frames()[0] 
    
    try:
        s_last5 = leaguedashteamstats.LeagueDashTeamStats(measure_type_detailed_defense="Advanced", last_n_games=5, date_to_nullable=date_api_format).get_data_frames()[0]
    except:
        s_last5 = pd.DataFrame()

    return team_dict, games, line_score, s_h, s_a, p_stats, b2b_data, s_last5

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
    except:
        return {}

def calculate_weighted_pie(p_stats_df, team_id, out_players):
    active_players = p_stats_df[(p_stats_df["TEAM_ID"] == team_id) & (~p_stats_df["PLAYER_NAME"].isin(out_players))]
    core_players = active_players[active_players["MIN"] > 15] 
    if core_players.empty: return 0
    top5 = core_players.nlargest(5, 'PIE')
    weighted_pie = (top5['PIE'] * top5['MIN']).sum() / top5['MIN'].sum()
    return weighted_pie

def run_monte_carlo(h_s, a_s, game_pace, n_sims=10000):
    sim_pace = np.random.normal(loc=game_pace, scale=4.0, size=n_sims)
    h_ppp_mean = h_s / game_pace
    a_ppp_mean = a_s / game_pace
    sim_h_ppp = np.random.normal(loc=h_ppp_mean, scale=0.12, size=n_sims)
    sim_a_ppp = np.random.normal(loc=a_ppp_mean, scale=0.12, size=n_sims)
    sim_h_score = sim_pace * sim_h_ppp
    sim_a_score = sim_pace * sim_a_ppp
    return sim_h_score - sim_a_score, sim_h_score + sim_a_score

def calculate_ev(win_prob, decimal_odds=1.909):
    return (win_prob * (decimal_odds - 1)) - (1 - win_prob)

# ------------------------ 
# 2 主介面與實戰分析 
# ------------------------ 
st.set_page_config(page_title="NBA AI 攻防大師 V31.0", layout="wide", page_icon="🏀") 
st.sidebar.header("🗓️ 歷史回測與實戰控制") 
target_date = st.sidebar.date_input("選擇賽事日期", datetime.now() - timedelta(hours=8)) 
formatted_date = target_date.strftime('%Y-%m-%d') 

st.sidebar.divider()
st.sidebar.markdown("### 🤖 自動化盤口 API")
st.sidebar.caption("前往 The Odds API 免費註冊，即可解鎖 V31 職業戰略儀表板。")
api_key = st.sidebar.text_input("輸入 API 金鑰", type="password")

st.title(f"🏀 NBA AI V31 職業戰略儀表板 ({formatted_date})") 

with st.spinner("啟動雷達：掃描市場盤口、執行蒙地卡羅模擬與 EV 運算中..."): 
    t_dict, games_df, line_df, s_h, s_a, p_stats, b2b_data, s_last5 = fetch_nba_master(formatted_date) 
    raw_inj = fetch_injury_raw() 
    live_odds = fetch_live_odds(api_key) if target_date == (datetime.now() - timedelta(hours=8)).date() else {}

if games_df.empty: 
    st.info("📅 此日期暫無賽程數據，請嘗試選擇其他日期。") 
else: 
    match_data = [] 
    all_ev_opportunities = [] # 🛡️ V31.0 核心：用來收集當日所有盤口維度的正 EV 標的
    is_historical = target_date < (datetime.now() - timedelta(hours=8)).date() 

    for _, row in games_df.iterrows(): 
        h_id, a_id = row["HOME_TEAM_ID"], row["VISITOR_TEAM_ID"] 
        h_n_en, a_n_en = t_dict.get(h_id), t_dict.get(a_id) 
        h_n, a_n = TEAM_CN.get(h_n_en, h_n_en), TEAM_CN.get(a_n_en, a_n_en) 
        
        try: 
            h_pts_raw = line_df.loc[line_df['TEAM_ID'] == h_id, 'PTS'].values 
            a_pts_raw = line_df.loc[line_df['TEAM_ID'] == a_id, 'PTS'].values 
            h_act = int(float(h_pts_raw[0])) if len(h_pts_raw) > 0 and pd.notna(h_pts_raw[0]) else 0 
            a_act = int(float(a_pts_raw[0])) if len(a_pts_raw) > 0 and pd.notna(a_pts_raw[0]) else 0 
        except: 
            h_act, a_act = 0, 0 
            
        is_finished = (h_act > 0 and a_act > 0 and (h_act + a_act) > 150) 

        h_pen, h_rep, h_gtd, h_out_players = get_injury_impact(h_n_en, raw_inj) 
        a_pen, a_rep, a_gtd, a_out_players = get_injury_impact(a_n_en, raw_inj) 
        
        if is_historical: 
            h_pen, a_pen = h_pen * 0.5, a_pen * 0.5 

        h_is_b2b = h_id in b2b_data
        a_is_b2b = a_id in b2b_data
        has_fatigue = h_is_b2b or a_is_b2b
        
        if h_is_b2b:
            h_pen += 3.5  
            h_rep.append(f"🔋 [{h_n}] 主場背靠背 (體能下滑)")
        if a_is_b2b:
            yest_loc = b2b_data[a_id]
            if yest_loc == "Away":
                a_pen += 5.5
                a_rep.append(f"✈️ [{a_n}] 連續客場背靠背 (嚴重飛行疲勞)")
            else:
                a_pen += 4.0
                a_rep.append(f"🔋 [{a_n}] 客場背靠背 (體能下滑)")

            if TEAM_ZONE.get(a_n_en) != TEAM_ZONE.get(h_n_en):
                a_pen += 1.5
                a_rep.append(f"🌎 [{a_n}] 跨區時差作戰 (疲勞加劇)")

        try: 
            h_d = s_h[s_h["TEAM_ID"] == h_id].iloc[0] 
            a_d = s_a[s_a["TEAM_ID"] == a_id].iloc[0] 
            
            if not s_last5.empty:
                h_l5 = s_last5[s_last5["TEAM_ID"] == h_id]
                a_l5 = s_last5[s_last5["TEAM_ID"] == a_id]
                
                if not h_l5.empty and not a_l5.empty:
                    h_l5_off = h_l5.iloc[0]["OFF_RATING"]
                    if h_l5_off > h_d["OFF_RATING"] * 1.08: h_l5_off = h_d["OFF_RATING"] * 1.05 
                    a_l5_off = a_l5.iloc[0]["OFF_RATING"]
                    if a_l5_off > a_d["OFF_RATING"] * 1.08: a_l5_off = a_d["OFF_RATING"] * 1.05 
                    
                    h_off = (h_d["OFF_RATING"] * 0.7) + (h_l5_off * 0.3)
                    h_def = (h_d["DEF_RATING"] * 0.7) + (h_l5.iloc[0]["DEF_RATING"] * 0.3)
                    a_off = (a_d["OFF_RATING"] * 0.7) + (a_l5_off * 0.3)
                    a_def = (a_d["DEF_RATING"] * 0.7) + (a_l5.iloc[0]["DEF_RATING"] * 0.3)
                else:
                    h_off, h_def = h_d["OFF_RATING"], h_d["DEF_RATING"]
                    a_off, a_def = a_d["OFF_RATING"], a_d["DEF_RATING"]
            else:
                h_off, h_def = h_d["OFF_RATING"], h_d["DEF_RATING"]
                a_off, a_def = a_d["OFF_RATING"], a_d["DEF_RATING"]
            
            pace_h = h_d["PACE"]
            pace_a = a_d["PACE"]
            game_pace = (2 * pace_h * pace_a) / (pace_h + pace_a)
            
            h_base_rating = (h_off * 0.65) + (a_def * 0.35) 
            a_base_rating = (a_off * 0.65) + (h_def * 0.35) 
            
            h_win_pct = h_d["W_PCT"]
            a_win_pct = a_d["W_PCT"]
            elo_edge = (h_win_pct - a_win_pct) * 4.5 
            
            h_pie = calculate_weighted_pie(p_stats, h_id, h_out_players)
            a_pie = calculate_weighted_pie(p_stats, a_id, a_out_players)
            
            h_edge = (h_pie - 12) * 0.4 if h_pie > 12 else 0 
            a_edge = (a_pie - 12) * 0.4 if a_pie > 12 else 0 
            
            h_s = round((h_base_rating * (game_pace/100)) + 2.5 - h_pen + h_edge + (elo_edge / 2), 1) 
            a_s = round((a_base_rating * (game_pace/100)) - a_pen + a_edge - (elo_edge / 2), 1) 
            
            sim_diff, sim_total = run_monte_carlo(h_s, a_s, game_pace)
            
            api_team_name = ODDS_API_TEAMS.get(h_n_en)
            market_spread = None
            market_total = None
            
            if live_odds and api_team_name in live_odds:
                market_spread = live_odds[api_team_name].get("spread")
                market_total = live_odds[api_team_name].get("total")

            # 🛡️ V31.0 核心：自動計算全市場 EV，並蒐集大於 0 的價值標的
            if market_spread is not None:
                prob_cover_h = np.mean(sim_diff > -market_spread)
                prob_cover_a = np.mean(sim_diff < -market_spread)
                ev_h = calculate_ev(prob_cover_h)
                ev_a = calculate_ev(prob_cover_a)
                
                if ev_h > 0:
                    all_ev_opportunities.append({
                        "對戰組合": f"{a_n} @ {h_n}", "下注類型": "讓分盤", "莊家開盤": f"主 {market_spread}", 
                        "推薦下注": f"主隊 ({h_n})", "蒙地卡羅過盤率": f"{prob_cover_h:.1%}", "期望值 (EV)": ev_h
                    })
                if ev_a > 0:
                    all_ev_opportunities.append({
                        "對戰組合": f"{a_n} @ {h_n}", "下注類型": "讓分盤", "莊家開盤": f"客 {-market_spread}", 
                        "推薦下注": f"客隊 ({a_n})", "蒙地卡羅過盤率": f"{prob_cover_a:.1%}", "期望值 (EV)": ev_a
                    })

            if market_total is not None:
                prob_over = np.mean(sim_total > market_total)
                prob_under = np.mean(sim_total < market_total)
                ev_over = calculate_ev(prob_over)
                ev_under = calculate_ev(prob_under)
                
                if ev_over > 0:
                    all_ev_opportunities.append({
                        "對戰組合": f"{a_n} @ {h_n}", "下注類型": "大小分", "莊家開盤": f"總分 {market_total}", 
                        "推薦下注": "大分 (Over)", "蒙地卡羅過盤率": f"{prob_over:.1%}", "期望值 (EV)": ev_over
                    })
                if ev_under > 0:
                    all_ev_opportunities.append({
                        "對戰組合": f"{a_n} @ {h_n}", "下注類型": "大小分", "莊家開盤": f"總分 {market_total}", 
                        "推薦下注": "小分 (Under)", "蒙地卡羅過盤率": f"{prob_under:.1%}", "期望值 (EV)": ev_under
                    })

            # 用於總表顯示的最佳推薦
            best_bet_str = "無盤口資訊"
            if market_spread is not None:
                if ev_h >= ev_a and ev_h > 0: best_bet_str = f"主隊 (-{market_spread}) | EV: +{ev_h:.1%}"
                elif ev_a > ev_h and ev_a > 0: best_bet_str = f"客隊 (+{market_spread}) | EV: +{ev_a:.1%}"
                else: best_bet_str = "⚠️ 負 EV (建議避開)"
            else:
                home_win_prob = np.mean(sim_diff > 0)
                if abs(h_s - a_s) <= 1.0: best_bet_str = "⚠️五五波(避開)"
                else: best_bet_str = f"主勝 ({home_win_prob:.1%})" if home_win_prob > 0.5 else f"客勝 ({1-home_win_prob:.1%})"

            hit = "待定" 
            if is_finished: 
                if "避開" in best_bet_str or "無盤口資訊" in best_bet_str:
                    hit = "無"  
                else:
                    if market_spread is not None:
                        if "主隊" in best_bet_str and (h_act - a_act > -market_spread): hit = "✅"
                        elif "客隊" in best_bet_str and (h_act - a_act < -market_spread): hit = "✅"
                        else: hit = "❌"
                    else:
                        hit = "✅" if (h_s > a_s and h_act > a_act) or (h_s < a_s and h_act < a_act) else "❌" 

            match_data.append({ 
                "對戰組合": f"{a_n} @ {h_n}", 
                "AI淨勝分(客:主)": f"{a_s} : {h_s}", 
                "市場讓分(主)": market_spread if market_spread is not None else "-",
                "最佳 EV 決策": best_bet_str,
                "實際比分": f"{a_act} : {h_act}" if is_finished else "-", 
                "勝負命中": hit, 
                "h_name": h_n, "a_name": a_n, 
                "h_s": h_s, "a_s": a_s,  
                "game_pace": game_pace,
                "reports": h_rep + a_rep
            }) 
        except Exception as e: 
            continue 

    # 🛡️ V31.0 儀表板 UI 設計
    if all_ev_opportunities:
        st.header("🔥 今日 TOP 5 價值投注 (全盤口自動掃描)")
        st.caption("這是一張由蒙地卡羅系統自動掃描今日所有「讓分」與「大小分」盤口後，找出的最具數學期望值 (EV) 的下注標的。")
        # 排序並取前 5 名
        ev_df = pd.DataFrame(all_ev_opportunities)
        ev_df = ev_df.sort_values(by="期望值 (EV)", ascending=False).head(5)
        # 將 EV 轉為百分比顯示
        ev_df["期望值 (EV)"] = ev_df["期望值 (EV)"].apply(lambda x: f"+{x:.1%}")
        
        # 放大顯示，製造操盤桌視覺
        st.dataframe(ev_df, use_container_width=True, height=215)
    elif api_key:
        st.warning("⚠️ 今日莊家開盤極度精準，系統未掃描到任何大於 0% EV 的賽事，建議今日空手觀望。")

    st.divider() 
    st.header("📊 完整賽事數據與市場盤口 (包含歷史回測)") 
    if match_data:
        display_df = pd.DataFrame(match_data)[["對戰組合", "AI淨勝分(客:主)", "市場讓分(主)", "最佳 EV 決策", "實際比分", "勝負命中"]]
        st.dataframe(display_df, use_container_width=True) 

    st.divider() 
    st.header("🔍 單場深度解析與手動測試儀") 
    if match_data:
        s_game = st.selectbox("請選擇要深入分析的場次：", match_data, format_func=lambda x: x["對戰組合"]) 
        
        col_a, col_b = st.columns(2) 
        with col_a: 
            st.subheader("📝 變數與陣容報告") 
            if s_game["reports"]: 
                for r in s_game["reports"]: 
                    if "✈️" in r or "🌎" in r or "🔋" in r: st.error(r)  
                    else: st.warning(r) 
            else: 
                st.success("✅ 無異常變數干擾。") 
                
        with col_b: 
            st.subheader("🎲 跑一萬次！動態 EV 模擬") 
            u_spread = st.number_input(f"請輸入台彩開給主隊的讓分 (例: -4.5)", value=-4.5, step=0.5) 
            u_total = st.number_input(f"請輸入大小分總分盤口 (例: 225.5)", value=225.5, step=0.5) 
            
            sim_diff, sim_total = run_monte_carlo(s_game['h_s'], s_game['a_s'], s_game['game_pace'])
            
            prob_cover_h = np.mean(sim_diff > -u_spread)
            prob_cover_a = np.mean(sim_diff < -u_spread)
            prob_over = np.mean(sim_total > u_total)
            prob_under = np.mean(sim_total < u_total)
            
            ev_h = calculate_ev(prob_cover_h)
            ev_a = calculate_ev(prob_cover_a)
            ev_over = calculate_ev(prob_over)
            ev_under = calculate_ev(prob_under)
            
            st.write("▶️ **讓分盤 10,000 次模擬結果：**")
            st.write(f"主隊 ({u_spread}) 過盤率: `{prob_cover_h:.1%}` ➡️ EV: `{ev_h:.1%}`")
            st.write(f"客隊 ({-u_spread}) 過盤率: `{prob_cover_a:.1%}` ➡️ EV: `{ev_a:.1%}`")
            
            st.divider()
            
            st.write("▶️ **大小分 10,000 次模擬結果：**")
            st.write(f"大分 (> {u_total}) 機率: `{prob_over:.1%}` ➡️ EV: `{ev_over:.1%}`")
            st.write(f"小分 (< {u_total}) 機率: `{prob_under:.1%}` ➡️ EV: `{ev_under:.1%}`")
                
st.caption("NBA AI V31.0 - 華爾街量化終端機：全盤口自動化掃描與正 EV TOP 5 戰略儀表板")