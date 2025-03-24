import streamlit as st
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
from wordcloud import WordCloud
import japanize_matplotlib
import calendar
import base64
from io import BytesIO
from janome.tokenizer import Tokenizer
import plotly.graph_objects as go
import requests

# 日本語フォントの設定
japanize_matplotlib.japanize()

# ページセットアップ  
st.set_page_config(  
    page_title="分析日記アプリ",  
    page_icon="📖",  
    layout="wide",  
    initial_sidebar_state="expanded",  
)  

# GitHub リポジトリ情報  
GITHUB_REPO = "isamikann/diary"  
GITHUB_FILE_PATH = "diary.json"  # JSON ファイルのパス  
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]  # Streamlit secrets に保存したトークン  
  
def get_file_sha(repo, path, token):  
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref=main"  
    headers = {"Authorization": f"token {token}"}  
    response = requests.get(url, headers=headers)  
    response.raise_for_status()  
    return response.json()["sha"]  

def update_github_file(repo, path, content, token, message="Update file"):  
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref=main"  
    sha = get_file_sha(repo, path, token)  
    headers = {"Authorization": f"token {token}"}  
    data = {  
        "message": message,  
        "content": content,  
        "sha": sha  
    }  
    response = requests.put(url, headers=headers, data=json.dumps(data))  
    response.raise_for_status()  
    return response.json()

def load_diary():  
    url = f"https://raw.githubusercontent.com/isamikann/diary/main/diary.json?ref=main" 
    response = requests.get(url)  
    response.raise_for_status()  
    return response.json()  
  
def save_diary(data):  
    encoded_content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode()  
    update_github_file(GITHUB_REPO, GITHUB_FILE_PATH, encoded_content, GITHUB_TOKEN)  

# 日記を追加・更新する関数（同じ日付のデータがあれば上書き）
def add_entry(date, content, weather, health, rating, activities=None, mood=None, memo=None, sleep_hours=None):
      diary = load_diary()  
      existing_entry = next((d for d in diary if d["date"] == date), None)  
        
      entry_data = {  
          "date": date,  
          "content": content,  
          "weather": weather,  
          "health": health,  
          "rating": rating,  
          "activities": activities or [],  
          "mood": mood or "",  
          "memo": memo or "",  
          "sleep_hours": sleep_hours or 7.0  
      }  
        
      if existing_entry:  
          for key, value in entry_data.items():  
              existing_entry[key] = value  
      else:  
          diary.append(entry_data)  
        
      save_diary(diary)  


# 📌 過去の日記を取得する関数（特定の日付）
def get_entry_by_date(date):
    diary = load_diary()
    return next((d for d in diary if d["date"] == date), None)

# テーマ設定関数  
def setup_page():  
    st.sidebar.title("📖 シンプル日記アプリ")  
    theme = st.sidebar.selectbox("🎨 テーマを選択", ["ライト", "ダーク", "カラフル", "シンプル"])  

    # 共通のスタイル設定  
    common_styles = """  
    .diary-entry { padding: 15px; border-radius: 5px; margin-bottom: 10px; background-color: rgba(240, 240, 240, 0.3); border-left: 5px solid #4CAF50; }  
    .rating-stars { color: gold; font-size: 20px; }  
    .main-content { padding: 20px; }  
    """  
  
    # テーマに基づいたスタイルを適用  
    if theme == "ダーク":  
        st.markdown("""  
        <style>  
        .main {background-color: #1E1E1E; color: #FFFFFF;}  
        .stButton>button {background-color: #4CAF50; color: white;}  
        .sidebar .sidebar-content {background-color: #333333; color: #FFFFFF;}  
        .stTextInput>label {color: #FFFFFF;}  
        .stSelectbox>label {color: #FFFFFF;}  
        .stSlider>div {color: #FFFFFF;}  
        h1, h2, h3, h4, h5, h6 {color: #FFFFFF;}  
        </style>  
        """, unsafe_allow_html=True)  
    elif theme == "カラフル":  
        st.markdown("""  
        <style>  
        .main {background-color: #F8F9FA;}  
        .stButton>button {background-color: #FF6B6B; color: white;}  
        .sidebar .sidebar-content {background-color: #4B9CD3; color: #FFFFFF;}  
        .stTextInput>label {color: #333333;}  
        .stSelectbox>label {color: #333333;}  
        .stSlider>div {color: #333333;}  
        h1, h2, h3, h4, h5, h6 {color: #5D5FEF;}  
        </style>  
        """, unsafe_allow_html=True)  
    elif theme == "シンプル":  
        st.markdown("""  
        <style>  
        .main {background-color: #FFFFFF; color: #333333;}  
        .stButton>button {background-color: #333333; color: white;}  
        .sidebar .sidebar-content {background-color: #FFFFFF; color: #333333;}  
        .stTextInput>label {color: #333333;}  
        .stSelectbox>label {color: #333333;}  
        .stSlider>div {color: #333333;}  
        h1, h2, h3, h4, h5, h6 {color: #333333; font-family: 'Helvetica', sans-serif;}  
        </style>  
        """, unsafe_allow_html=True)  
    else:  # default Light theme  
        st.markdown("""  
        <style>  
        .main {background-color: #FFFFFF; color: #000000;}  
        .stButton>button {background-color: #007BFF; color: white;}  
        .sidebar .sidebar-content {background-color: #F8F9FA; color: #000000;}  
        .stTextInput>label {color: #000000;}  
        .stSelectbox>label {color: #000000;}  
        .stSlider>div {color: #000000;}  
        h1, h2, h3, h4, h5, h6 {color: #000000;}  
        </style>  
        """, unsafe_allow_html=True)  
  
    return theme  

# スタイル適用
theme = setup_page()

# 📝 日記入力フォーム
def diary_form():
    st.header("✍️ 日記を書く")
    
    # 日付を選択
    selected_date = st.date_input("📆 日付を選択", datetime.today()).strftime("%Y-%m-%d")
    
    # 過去の日記があるかチェック
    existing_entry = get_entry_by_date(selected_date)
    content = existing_entry.get("content", "") if existing_entry else ""
    weather = existing_entry.get("weather", "晴れ") if existing_entry else "晴れ"
    health = existing_entry.get("health", "元気") if existing_entry else "元気"
    rating = existing_entry.get("rating", 3) if existing_entry else 3
    activities = existing_entry.get("activities", []) if existing_entry else []
    mood = existing_entry.get("mood", "") if existing_entry else ""
    memo = existing_entry.get("memo", "") if existing_entry else ""
    sleep_hours = existing_entry.get("sleep_hours", 7.0) if existing_entry else 7.0
    
    # 基本情報の入力
    col1, col2 = st.columns(2)
    
    with col1:
        weather = st.selectbox("🌤 天気", ["晴れ", "曇り", "雨", "雪", "霧", "台風"], index=["晴れ", "曇り", "雨", "雪", "霧", "台風"].index(weather))
        health = st.selectbox("😷 体調", ["元気", "普通", "少し疲れた", "体調不良", "絶好調", "眠い"], index=["元気", "普通", "少し疲れた", "体調不良", "絶好調", "眠い"].index(health) if health in ["元気", "普通", "少し疲れた", "体調不良", "絶好調", "眠い"] else 0)

    with col2:
        mood = st.selectbox("🧠 気分", ["選択しない", "幸せ", "充実", "退屈", "不安", "悲しい", "イライラ", "やる気満々", "リラックス", "達成感"], index=["選択しない", "幸せ", "充実", "退屈", "不安", "悲しい", "イライラ", "やる気満々", "リラックス", "達成感"].index(mood) if mood in ["選択しない", "幸せ", "充実", "退屈", "不安", "悲しい", "イライラ", "やる気満々", "リラックス", "達成感"] else 0)
        sleep_hours = st.number_input("😴 睡眠時間（時間）", min_value=0.0, max_value=24.0, value=sleep_hours, step=0.5)
        rating = st.slider("⭐ 今日の評価", 1, 5, rating)
        st.write(f"評価: {'⭐' * rating}")
    
    # 活動タグ
    activity_options = ["運動した", "読書した", "料理した", "友達と会った", "家族と過ごした", "勉強した", "映画/TVを見た", "創作活動をした", "ゲームをした", "休息した", "仕事をした", "新しいことを学んだ"]
    
    st.write("🏃‍♂️ 今日行った活動（複数選択可）")
    # 活動をグリッドレイアウトで表示
    cols = st.columns(3)
    selected_activities = []
    
    for i, activity in enumerate(activity_options):
        if cols[i % 3].checkbox(activity, activity in activities):
            selected_activities.append(activity)
    
    # 日記の内容
    st.write("📝 日記")
    
    # 振り返り質問のテンプレート（ヒント）
    reflection_template = st.checkbox("振り返りヒントを表示", False)
    if reflection_template:
        st.info("""
        ヒント：
        - 今日一番良かった出来事は？
        - 今日学んだことは？
        - 明日やりたいことは？
        - 今日の自分を褒めたいポイントは？
        """)
    
    content = st.text_area("今日の出来事や感想を書きましょう", value=content, height=150)
    
    # メモ欄（自由記述）
    memo = st.text_input("📌 メモ・アイデア・気づき（短く書き留めたいこと）", value=memo)
    
    # 保存ボタン
    if st.button("💾 保存する", key="save_diary"):
        if content.strip():
            add_entry(selected_date, content, weather, health, rating, selected_activities, mood, memo, sleep_hours) 
            st.success(f"✅ {selected_date} の日記を保存しました！")
            # アニメーション効果
            st.balloons()
        else:
            st.warning("⚠️ 日記の内容を入力してください。")

# 📚 過去の日記表示
def display_entries():
    st.header("📅 過去の日記")
    
    diary = load_diary()
    if len(diary) == 0:
        st.info("まだ日記がありません。")
        return
    
    # 表示方法の選択
    view_type = st.radio("表示方法", ["リスト表示", "カレンダー表示"], horizontal=True)
    
    if view_type == "カレンダー表示":
        display_calendar(diary)
        return
    
    # 検索・フィルター用コントロール
    with st.expander("🔍 検索・フィルター", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_input("🔍 キーワード検索", "")
            filter_weather = st.selectbox("🌤 天気で絞り込む", ["すべて"] + list(set(d.get("weather", "") for d in diary if "weather" in d)))
        
        with col2:
            filter_health = st.selectbox("😷 体調で絞り込む", ["すべて"] + list(set(d.get("health", "") for d in diary if "health" in d)))
            filter_rating = st.selectbox("⭐ 評価で絞り込む", ["すべて", "1", "2", "3", "4", "5"])
        
        # 活動タグでのフィルタリング
        all_activities = set()
        for entry in diary:
            if "activities" in entry and entry["activities"]:
                all_activities.update(entry["activities"])
        
        filter_activity = st.multiselect("🏃‍♂️ 活動で絞り込む", list(all_activities))
    
    # フィルタリング
    filtered_diary = diary.copy()
    
    # 検索とフィルター適用
    if search_query or filter_weather != "すべて" or filter_health != "すべて" or filter_rating != "すべて" or filter_activity:
        filtered_diary = [d for d in diary if 
            (not search_query or search_query.lower() in d.get("content", "").lower() or 
             search_query.lower() in d.get("memo", "").lower()) and
            (filter_weather == "すべて" or d.get("weather", "") == filter_weather) and
            (filter_health == "すべて" or d.get("health", "") == filter_health) and
            (filter_rating == "すべて" or str(d.get("rating", "")) == filter_rating) and
            (not filter_activity or any(activity in d.get("activities", []) for activity in filter_activity))
        ]
    
    # 並び順のオプション
    sort_option = st.selectbox("並び替え", ["日付順（新しい順）", "日付順（古い順）", "評価（高い順）", "評価（低い順）"])
    
    if sort_option == "日付順（新しい順）":
        filtered_diary = sorted(filtered_diary, key=lambda x: x["date"], reverse=True)
    elif sort_option == "日付順（古い順）":
        filtered_diary = sorted(filtered_diary, key=lambda x: x["date"])
    elif sort_option == "評価（高い順）":
        filtered_diary = sorted(filtered_diary, key=lambda x: x.get("rating", 0), reverse=True)
    elif sort_option == "評価（低い順）":
        filtered_diary = sorted(filtered_diary, key=lambda x: x.get("rating", 0))
    
    # データ表示
    if len(filtered_diary) == 0:
        st.warning("該当する日記が見つかりません。")
    else:
        st.success(f"{len(filtered_diary)}件の日記が見つかりました")
        
        for entry in filtered_diary:
            # カード風のデザイン
            with st.container():
                st.markdown(f"""
                <div class="diary-entry">
                    <h3>📆 {entry['date']}</h3>
                    <p>🌤 天気: {entry.get('weather', '未記入')} | 😷 体調: {entry.get('health', '未記入')} | 
                    <span class="rating-stars">{'⭐' * entry.get('rating', 0)}</span></p>
                    <p>📝 {entry.get('content', '').replace('\n', '<br>')}</p>
                """, unsafe_allow_html=True)
                
                # 活動タグがあれば表示
                if "activities" in entry and entry["activities"]:
                    activities_html = ' '.join([f'<span style="background-color: #E1F5FE; padding: 3px 8px; border-radius: 10px; margin-right: 5px;">{a}</span>' for a in entry["activities"]])
                    st.markdown(f"<p>🏃‍♂️ {activities_html}</p>", unsafe_allow_html=True)
                
                # 気分があれば表示
                if "mood" in entry and entry["mood"] and entry["mood"] != "選択しない":
                    st.markdown(f"<p>🧠 気分: {entry['mood']}</p>", unsafe_allow_html=True)
                
                # メモがあれば表示
                if "memo" in entry and entry["memo"]:
                    st.markdown(f"<p>📌 メモ: {entry['memo']}</p>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("---")
        
        # エクスポート機能
        if st.button("📋 表示中の日記をCSVエクスポート"):
            csv = export_to_csv(filtered_diary)
            st.download_button(
                label="📥 CSVをダウンロード",
                data=csv,
                file_name="my_diary_export.csv",
                mime="text/csv",
            )

# 📅 カレンダー表示
def display_calendar(diary):
    # データフレームに変換
    df = pd.DataFrame(diary)
    df["date"] = pd.to_datetime(df["date"])
    
    # 月を選択
    all_months = sorted(df["date"].dt.strftime("%Y-%m").unique())
    if not all_months:
        st.info("日記のデータがありません。")
        return
    
    default_month_index = 0  # 最新の月をデフォルトに
    selected_month = st.selectbox(
        "月を選択", 
        all_months, 
        index=default_month_index,
        format_func=lambda x: f"{x[:4]}年{x[5:]}月"
    )
    
    year, month = map(int, selected_month.split('-'))
    
    # 選択した月のカレンダーを作成
    cal = calendar.monthcalendar(year, int(month))
    
    # 月のデータを抽出
    month_data = df[df["date"].dt.strftime("%Y-%m") == selected_month]
    
    # カレンダーヘッダー
    cols = st.columns(7)
    days = ["月", "火", "水", "木", "金", "土", "日"]
    for i, day in enumerate(days):
        cols[i].markdown(f"<p style='text-align: center; font-weight: bold;'>{day}</p>", unsafe_allow_html=True)
    
    # カレンダー本体を表示
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                # 当月ではない日
                cols[i].markdown("<p style='text-align: center;'></p>", unsafe_allow_html=True)
            else:
                # 日付をフォーマット
                date_str = f"{year}-{month:02d}-{day:02d}"
                
                # その日のデータを取得
                day_data = month_data[month_data["date"].dt.strftime("%Y-%m-%d") == date_str]
                
                if not day_data.empty:
                    # データがある場合
                    rating = day_data.iloc[0].get("rating", 0)
                    weather = day_data.iloc[0].get("weather", "")
                    
                    # 天気アイコン
                    weather_icon = {
                        "晴れ": "☀️", "曇り": "☁️", "雨": "🌧️", 
                        "雪": "❄️", "霧": "🌫️", "台風": "🌀"
                    }.get(weather, "")
                    
                    cols[i].markdown(f"""
                    <div style='text-align: center; padding: 5px; background-color: rgba(144, 238, 144, 0.2); border-radius: 5px;'>
                        <p style='font-weight: bold; margin-bottom: 0;'>{day}</p>
                        <p style='margin: 0;'>{weather_icon}</p>
                        <p style='margin: 0; color: gold;'>{"⭐" * rating}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # データがない場合
                    cols[i].markdown(f"""
                    <div style='text-align: center; padding: 5px;'>
                        <p>{day}</p>
                    </div>
                    """, unsafe_allow_html=True)

# 📊 基本統計データ可視化
def show_statistics():
    st.header("📊 データ分析")
    
    diary = load_diary()
    if len(diary) == 0:
        st.info("まだデータがありません。")
        return
    
    if len(diary) < 3:
        st.warning("統計分析には最低3件のデータが必要です。もう少し日記を書いてみましょう。")
        return
    
    # DataFrame に変換
    df = pd.DataFrame(diary)
    
    # 日付を日時型に変換
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    # 曜日情報を追加
    df["weekday"] = df["date"].dt.day_name()
    # 日本語曜日に変換
    weekday_map = {
        "Monday": "月曜日", "Tuesday": "火曜日", "Wednesday": "水曜日", 
        "Thursday": "木曜日", "Friday": "金曜日", "Saturday": "土曜日", "Sunday": "日曜日"
    }
    df["weekday_jp"] = df["weekday"].map(weekday_map)
    
    # タブで分析項目を分ける
    tabs = st.tabs(["評価の推移", "天気と体調", "曜日と活動", "キーワード分析", "睡眠時間"])
    
    # タブ1: 評価の推移
    with tabs[0]:
        st.subheader("評価の推移")
        
        # Plotlyでインタラクティブなグラフを作成
        fig = px.line(df, x="date", y="rating", 
                    title="日々の評価の推移",
                    labels={"rating": "評価", "date": "日付"},
                    markers=True)
        
        # 7日間の移動平均を追加
        if len(df) >= 7:
            df["rolling_avg"] = df["rating"].rolling(window=7).mean()
            fig.add_scatter(x=df["date"], y=df["rolling_avg"], mode="lines", name="7日間移動平均")
        
        st.plotly_chart(fig, use_container_width=True)
        
        #評価を数える。
        rating_counts = df['rating'].value_counts().sort_index()
        #1~5でデータがない場合、０を追加する
        for i in range(1,6):
            if i not in rating_counts:
                rating_counts[i] = 0
        rating_counts = rating_counts.sort_index()
        
        fig = go.Figure(data=[go.Bar(x=rating_counts.index, y=rating_counts.values)])

        fig.update_layout(
            title='評価の分布',
            xaxis_title='評価',
            yaxis_title='日数',
            xaxis=dict(
                tickmode='linear',
                dtick=1,
                range=[0.5,5.5]
            ),
            yaxis=dict(
                tickmode='linear',
            )
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 評価の特徴
        st.subheader("評価の特徴")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("平均評価", f"{df['rating'].mean():.1f}")
        with col2:
            st.metric("最高評価の日数", len(df[df["rating"] == 5]))
        with col3:
            # 先週と今週の比較
            today = pd.Timestamp.today()
            last_week = df[(df["date"] >= today - timedelta(days=14)) & (df["date"] < today - timedelta(days=7))]
            this_week = df[(df["date"] >= today - timedelta(days=7)) & (df["date"] <= today)]
            
            if not last_week.empty and not this_week.empty:
                last_week_avg = last_week["rating"].mean()
                this_week_avg = this_week["rating"].mean()
                delta = this_week_avg - last_week_avg
                st.metric("先週比", f"{this_week_avg:.1f}", f"{delta:+.1f}")
            else:
                st.metric("先週比", "データ不足")
    
    # タブ2: 天気と体調
    with tabs[1]:
        st.subheader("天気と体調の影響")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 天気ごとの評価
            weather_avg = df.groupby("weather")["rating"].mean().sort_values(ascending=False)
            weather_count = df.groupby("weather").size()
            
            weather_fig = px.bar(
                x=weather_avg.index, 
                y=weather_avg.values,
                title="天気別の平均評価",
                labels={"x": "天気", "y": "平均評価"},
                text=[f"({count}日)" for count in weather_count[weather_avg.index]]
            )
            st.plotly_chart(weather_fig, use_container_width=True)
            
            # 最も評価が高い天気
            best_weather = weather_avg.idxmax()
            st.info(f"☀️ 評価が最も高い天気は「{best_weather}」です（平均{weather_avg.max():.1f}点）")
        
        with col2:
            # 体調ごとの評価
            health_avg = df.groupby("health")["rating"].mean().sort_values(ascending=False)
            health_count = df.groupby("health").size()
            
            health_fig = px.bar(
                x=health_avg.index, 
                y=health_avg.values,
                title="体調別の平均評価",
                labels={"x": "体調", "y": "平均評価"},
                text=[f"({count}日)" for count in health_count[health_avg.index]]
            )
            st.plotly_chart(health_fig, use_container_width=True)
            
            # 最も評価が高い体調
            best_health = health_avg.idxmax()
            st.info(f"💪 評価が最も高い体調は「{best_health}」です（平均{health_avg.max():.1f}点）")
        
        # 気分の分析（データがあれば）
        if "mood" in df.columns and df["mood"].notna().any() and (df["mood"] != "選択しない").any():
            st.subheader("気分の分析")
            mood_data = df[df["mood"] != "選択しない"]
            
            if not mood_data.empty:
                mood_avg = mood_data.groupby("mood")["rating"].mean().sort_values(ascending=False)
                mood_count = mood_data.groupby("mood").size()
                
                mood_fig = px.bar(
                    x=mood_avg.index, 
                    y=mood_avg.values,
                    title="気分別の平均評価",
                    labels={"x": "気分", "y": "平均評価"},
                    text=[f"({count}日)" for count in mood_count[mood_avg.index]]
                )
                st.plotly_chart(mood_fig, use_container_width=True)
                
                best_mood = mood_avg.idxmax()
                st.info(f"🧠 評価が最も高い気分は「{best_mood}」です（平均{mood_avg.max():.1f}点）")
    
    # タブ3: 曜日と活動
    with tabs[2]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("曜日別の評価")
            
            # 曜日順に並べ替え
            weekday_order = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
            weekday_avg = df.groupby("weekday_jp")["rating"].mean()
            weekday_avg = weekday_avg.reindex(weekday_order)
            
            weekday_fig = px.bar(
                x=weekday_avg.index, 
                y=weekday_avg.values,
                title="曜日別の平均評価",
                labels={"x": "曜日", "y": "平均評価"}
            )
            st.plotly_chart(weekday_fig, use_container_width=True)
            
            # 最も評価が高い曜日
            best_weekday = weekday_avg.idxmax()
            st.info(f"📅 評価が最も高い曜日は「{best_weekday}」です（平均{weekday_avg.max():.1f}点）")
        
        with col2:
            # 活動の分析
            st.subheader("活動と評価の関係")
            
            # 活動データが存在する場合
            if "activities" in df.columns:
                # 全活動リストを作成
                all_activities = []
                for acts in df["activities"]:
                    if isinstance(acts, list):
                        all_activities.extend(acts)
                
                # 活動ごとの集計
                activity_data = {}
                for activity in set(all_activities):
                    # その活動がある日のみ抽出
                    days_with_activity = df[df["activities"].apply(lambda x: activity in x if isinstance(x, list) else False)]
                    if not days_with_activity.empty:
                        avg_rating = days_with_activity["rating"].mean()
                        activity_data[activity] = {
                            "average": avg_rating,
                            "count": len(days_with_activity)
                        }
                
                # データを表示用に整形
                if activity_data:
                    activities_df = pd.DataFrame([
                        {"活動": activity, "平均評価": data["average"], "日数": data["count"]}
                        for activity, data in activity_data.items()
                    ]).sort_values("平均評価", ascending=False)
                    
                    activity_fig = px.bar(
                        activities_df,
                        x="活動", 
                        y="平均評価",
                        title="活動別の平均評価",
                        text=activities_df["日数"].apply(lambda x: f"({x}日)")
                    )
                    st.plotly_chart(activity_fig, use_container_width=True)
                    
                    # トップ3の活動
                    if len(activities_df) >= 3:
                        st.success("⭐ 評価が高い活動トップ3:")
                        for i, (_, row) in enumerate(activities_df.head(3).iterrows()):
                            st.write(f"{i+1}. **{row['活動']}** (平均{row['平均評価']:.1f}点, {row['日数']}日)")
                    elif len(activities_df) > 0:
                        st.success(f"⭐ 評価が最も高い活動は「{activities_df.iloc[0]['活動']}」です")
                else:
                    st.info("活動データがまだ十分にありません。")
            else:
                st.info("活動データが記録されていません。")
    
    # タブ4: キーワード分析
    with tabs[3]:
        st.subheader("日記のキーワード分析")
        
        # テキストデータを結合
        all_text = " ".join(df["content"].astype(str).tolist())
        
        if all_text.strip():
            # Janome の Tokenizer を作成
            t = Tokenizer()
            
            # 分かち書きされたテキストを格納するリスト
            wakati_text = []
            
            # ストップワード（除外したい単語）を定義
            japanese_stopwords = ["てる", "いる", "なる", "れる", "する", "ある", "こと", "これ", "さん", "して",   
                                  "くれる", "やる", "くる", "しまう", "いく", "ない", "のだ", "よう", "あり", "ため",  
                                  "ところ", "ます", "です", "から", "まで", "たり", "けど", "ので", "たい", "なる",   
                                  "もの", "それ", "その", "今日", "日", "は", "が", "の", "に", "を", "へ", "と", "も",  
                                  "で", "や", "し", "ながら", "なら", "けれど", "けど", "から", "まで", "たり", "だって",   
                                  "なのに", "だけど", "たり", "だ", "だが", "そして", "しかし", "だから", "また", "につい",  
                                  "すると", "なるほど", "ほんの", "たい", "です", "ます", "する", "くる", "れる", "いい",
                                  "られる"]  
            
            # 形態素解析で分かち書き
            for token in t.tokenize(all_text):
                # 品詞の取得
                part_of_speech = token.part_of_speech.split(',')[0]
                # 基本形の取得
                base_form = token.base_form
                
                # 名詞、動詞、形容詞のみを抽出
                if part_of_speech in ['名詞', '動詞', '形容詞'] and base_form not in japanese_stopwords:
                    # 除外したい単語以外を追加
                    wakati_text.append(base_form)
            
            # 分かち書きされたテキストを一つの文字列にする
            wakati_all_text = " ".join(wakati_text)
            
            if wakati_all_text.strip():  # 分かち書き後のテキストが空でないか確認
              
                # ワードクラウドの作成
                st.write("📝 よく使われる単語のワードクラウド")
                
                # 変更後
                wordcloud = WordCloud(
                    width=800, 
                    height=400, 
                    background_color='white',
                    font_path='./ipaexg.ttf',  # 日本語フォントのファイル名を指定
                    stopwords=set(japanese_stopwords), # ここではストップワードは不要のため空リストにしない
                    collocations=False,
                    max_words=100
                ).generate(wakati_all_text)

                # ワードクラウドの表示
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)
                
                # 頻出キーワードの分析
                st.write("📊 感情ごとの評価平均")
                
                # 感情キーワードのマッピング
                emotion_keywords = {
                    "ポジティブ": ["嬉しい", "楽しい", "幸せ", "わくわく", "最高", "喜び", "素晴らしい", "良い", "成功", "達成"],
                    "ネガティブ": ["悲しい", "辛い", "苦しい", "不安", "心配", "失敗", "残念", "怖い", "疲れる", "しんどい"],
                    "中立/その他": ["考える", "思う", "感じる", "予定", "明日", "今日", "昨日", "たぶん", "かもしれない"]
                }
                
                # 感情ごとのデータ収集
                emotion_ratings = {emotion: [] for emotion in emotion_keywords}
                
                for _, row in df.iterrows():
                    # 感情キーワードチェックのテキスト変更
                    wakati_content = [token.base_form for token in t.tokenize(row["content"]) if token.part_of_speech.split(',')[0] in ['名詞', '動詞', '形容詞']]
                    rating = row["rating"]
                    
                    for emotion, keywords in emotion_keywords.items():
                         if any(keyword in wakati_content for keyword in keywords):
                             emotion_ratings[emotion].append(rating)
                
                # 感情ごとの平均評価を計算
                emotion_avg = {emotion: np.mean(ratings) if ratings else 0 for emotion, ratings in emotion_ratings.items()}
                emotion_count = {emotion: len(ratings) for emotion, ratings in emotion_ratings.items()}
                
                # 感情ごとの平均評価をグラフ化
                fig = px.bar(
                    x=list(emotion_avg.keys()),
                    y=list(emotion_avg.values()),
                    title="感情表現ごとの平均評価",
                    labels={"x": "感情カテゴリ", "y": "平均評価"},
                    text=[f"({count}日)" for count in emotion_count.values()]
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 最も評価が高い感情カテゴリ
                if any(emotion_avg.values()):
                    best_emotion = max(emotion_avg.items(), key=lambda x: x[1])
                    if best_emotion[1] > 0:
                        st.info(f"💭 「{best_emotion[0]}」な表現をした日の平均評価が最も高いです（平均{best_emotion[1]:.1f}点）")
            else:
                st.info("単語抽出できませんでした")
        else:
            st.info("テキストデータがまだ十分にありません。")

    # タブ5: 睡眠時間
    with tabs[4]:
        st.subheader("睡眠時間と評価の関係")

        # 睡眠時間と評価の散布図
        sleep_rating_scatter = px.scatter(
            df, 
            x="sleep_hours", 
            y="rating", 
            title="睡眠時間と評価の関係",
            labels={"sleep_hours": "睡眠時間（時間）", "rating": "評価"}
        )
        st.plotly_chart(sleep_rating_scatter, use_container_width=True)
        
        # 睡眠時間と評価の相関係数
        correlation = df["sleep_hours"].corr(df["rating"])
        st.write(f"睡眠時間と評価の相関係数：{correlation:.2f}")

        # 睡眠時間ごとの平均評価
        sleep_avg = df.groupby("sleep_hours")["rating"].mean().sort_index()

        sleep_avg_fig = px.bar(
            x=sleep_avg.index, 
            y=sleep_avg.values,
            title="睡眠時間別の平均評価",
            labels={"x": "睡眠時間（時間）", "y": "平均評価"}
        )

        st.plotly_chart(sleep_avg_fig, use_container_width=True)

        # 睡眠時間と評価の分析情報
        if correlation > 0.5:
          st.info(f"相関係数{correlation:.2f}:睡眠時間が長いほど評価が高い傾向があります。")
        elif correlation < -0.5:
          st.info(f"相関係数{correlation:.2f}:睡眠時間が長いほど評価が低い傾向があります。")
        else:
          st.info(f"相関係数{correlation:.2f}:睡眠時間と評価に関連はあまりないようです。")

        # 最も評価が高い睡眠時間
        best_sleep_hours = sleep_avg.idxmax()
        st.info(f"🛌 評価が最も高い睡眠時間は「{best_sleep_hours}時間」です（平均{sleep_avg.max():.1f}点）")

def advanced_visualizations():
    st.subheader("🔍 高度な可視化分析")

    diary = load_diary()
    
    # DataFrame に変換
    df = pd.DataFrame(diary)
    
    # データの前処理
    df['date'] = pd.to_datetime(df['date'])
    df['weekday'] = df['date'].dt.day_name()
    df['month'] = df['date'].dt.month_name()
    
    # タブで分析項目を分ける
    viz_tabs = st.tabs(["時系列ヒートマップ", "相関マトリックス"])
    
    # タブ1: 時系列ヒートマップ
    with viz_tabs[0]:
        st.write("📅 週別・月別の評価ヒートマップ")
        
        # 日付から年と週番号を抽出
        df['year'] = df['date'].dt.isocalendar().year
        df['week'] = df['date'].dt.isocalendar().week
        
        # ピボットテーブルで週と曜日でデータを集計
        pivot_df = df.pivot_table(
            index=['year', 'week'], 
            columns='weekday', 
            values='rating', 
            aggfunc='mean'
        ).reset_index()
        
        # 年と週から日付文字列を作成
        def get_week_label(year, week):
            try:
                # その週の月曜日を取得
                monday = datetime.strptime(f'{year}-{week}-1', '%Y-%W-%w')
                return monday.strftime('%m/%d週')
            except:
                return f"{year}-W{week}"
        
        # ラベルを作成
        week_labels = [get_week_label(r['year'], r['week']) for i, r in pivot_df.iterrows()]
        
        # 曜日の順序を設定
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_df = pivot_df[['year', 'week'] + [day for day in weekday_order if day in pivot_df.columns]]
        
        # ヒートマップ用のデータを準備
        heatmap_data = pivot_df.iloc[:, 2:].values  # 年・週を除く
        
        # ヒートマップの作成
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=[day for day in weekday_order if day in pivot_df.columns],
            y=week_labels,
            colorscale='RdYlGn',  # 赤（低評価）から緑（高評価）のカラースケール
            zmin=1, zmax=5
        ))
        
        fig.update_layout(
            title='週別・曜日別の平均評価ヒートマップ',
            xaxis_title='曜日',
            yaxis_title='週',
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # インサイトの表示
        best_week_idx = np.argmax(pivot_df.iloc[:, 2:].mean(axis=1))
        best_week = week_labels[best_week_idx]
        st.info(f"📊 評価が最も高かった週は {best_week} でした。")
    
    # タブ2: 相関マトリックス
    with viz_tabs[1]:
        st.write("🔄 各要素間の相関関係")
        
        # 相関分析用のデータを準備
        corr_data = pd.DataFrame()
        corr_data['rating'] = df['rating']
        corr_data['sleep_hours'] = df['sleep_hours']
        
        # 天気をダミー変数に変換
        if 'weather' in df.columns:
            weather_dummies = pd.get_dummies(df['weather'], prefix='weather')
            corr_data = pd.concat([corr_data, weather_dummies], axis=1)
        
        # 体調をダミー変数に変換
        if 'health' in df.columns:
            health_dummies = pd.get_dummies(df['health'], prefix='health')
            corr_data = pd.concat([corr_data, health_dummies], axis=1)
        
        # 気分をダミー変数に変換
        if 'mood' in df.columns:
            mood_data = df[df['mood'] != '選択しない']
            if not mood_data.empty:
                mood_dummies = pd.get_dummies(mood_data['mood'], prefix='mood')
                # インデックスをリセットして結合
                mood_dummies.index = mood_data.index
                corr_data = pd.concat([corr_data, mood_dummies.reindex(corr_data.index, fill_value=0)], axis=1)
        
        # 活動をダミー変数に変換
        if 'activities' in df.columns:
            all_activities = set()
            for acts in df['activities']:
                if isinstance(acts, list):
                    all_activities.update(acts)
            
            for activity in all_activities:
                corr_data[f'activity_{activity}'] = df['activities'].apply(
                    lambda x: 1 if isinstance(x, list) and activity in x else 0
                )
        
        # 曜日をダミー変数に変換
        weekday_dummies = pd.get_dummies(df['weekday'], prefix='weekday')
        corr_data = pd.concat([corr_data, weekday_dummies], axis=1)
        
        # 相関行列を計算
        corr_matrix = corr_data.corr()
        
        # 相関マトリックスのヒートマップを作成
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',  # 赤青のカラースケール
            zmin=-1, zmax=1
        ))
        
        fig.update_layout(
            title='各要素間の相関関係',
            height=700,
            width=700
        )
        
        st.plotly_chart(fig)
        
        # 評価との相関が高い要素を表示
        rating_corr = corr_matrix['rating'].drop('rating').sort_values(ascending=False)
        
        st.write("⭐ 評価と最も関連性が高い要素:")
        for idx, (item, corr) in enumerate(rating_corr.head(5).items()):
            direction = "正の" if corr > 0 else "負の"
            strength = "強い" if abs(corr) > 0.5 else "やや"
            st.write(f"{idx+1}. **{item}**: {strength}{direction}相関 ({corr:.2f})")

# CSV形式でエクスポートする関数
def export_to_csv(diary_data):
    df = pd.DataFrame(diary_data)
    # sleep_hoursをcsvに追加
    if "sleep_hours" not in df.columns:
      df["sleep_hours"] = ""

    # エクスポートするカラムの順番を固定
    df = df[["date", "content", "weather", "health", "rating", "activities", "mood", "memo", "sleep_hours"]]
    return df.to_csv(index=False).encode('utf-8-sig')  # 日本語のためにUTF-8 with BOMを使用


# 習慣化支援（連続記録表示）機能
def habit_tracking():
    st.header("📊 習慣化支援・連続記録")
    
    diary = load_diary()
    if len(diary) == 0:
        st.info("まだ日記データがありません。")
        return
    
    # DataFrameに変換
    df = pd.DataFrame(diary)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    # 日付範囲を取得
    min_date = df["date"].min()
    max_date = df["date"].max()
    date_range = pd.date_range(start=min_date, end=max_date)
    
    # 連続記録の計算
    st.subheader("🔄 連続記録状況")
    
    # 現在の連続記録を計算
    current_streak = 0
    last_date = datetime.now().date()
    
    # 日付順にソート
    sorted_dates = sorted([pd.to_datetime(d["date"]).date() for d in diary], reverse=True)
    
    for i, date in enumerate(sorted_dates):
        if i == 0:
            current_streak = 1
        else:
            prev_date = sorted_dates[i-1]
            if (prev_date - date).days == 1:  # 連続している
                current_streak += 1
            else:
                break
    
    # 最長連続記録を計算
    all_dates = sorted([pd.to_datetime(d["date"]).date() for d in diary])
    longest_streak = 1
    current = 1
    
    for i in range(1, len(all_dates)):
        if (all_dates[i] - all_dates[i-1]).days == 1:
            current += 1
        else:
            longest_streak = max(longest_streak, current)
            current = 1
    
    longest_streak = max(longest_streak, current)
    
    # メトリクス表示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("現在の連続記録", f"{current_streak}日")
    
    with col2:
        st.metric("最長連続記録", f"{longest_streak}日")
    
    with col3:
        completion_rate = int(len(df) / len(date_range) * 100)
        st.metric("記録率", f"{completion_rate}%")
    
    # カレンダーヒートマップ表示
    st.subheader("📅 記録カレンダー")
    
    # 月を選択
    current_month = datetime.now().strftime("%Y-%m")
    all_months = sorted(df["date"].dt.strftime("%Y-%m").unique())
    
    if current_month in all_months:
        default_index = all_months.index(current_month)
    else:
        default_index = len(all_months) - 1 if all_months else 0
    
    selected_month = st.selectbox(
        "月を選択", 
        all_months if all_months else [current_month], 
        index=min(default_index, len(all_months)-1) if all_months else 0,
        format_func=lambda x: f"{x[:4]}年{x[5:]}月"
    )
    
    # 連続記録のカレンダー表示
    if all_months:
        year, month = map(int, selected_month.split('-'))
        cal = calendar.monthcalendar(year, int(month))
        
        # 月のデータを抽出
        month_data = df[df["date"].dt.strftime("%Y-%m") == selected_month]
        month_dates = set(month_data["date"].dt.strftime("%Y-%m-%d"))
        
        # カレンダーヘッダー
        cols = st.columns(7)
        days = ["月", "火", "水", "木", "金", "土", "日"]
        for i, day in enumerate(days):
            cols[i].markdown(f"<p style='text-align: center; font-weight: bold;'>{day}</p>", unsafe_allow_html=True)
        
        # カレンダー本体を表示
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    # 当月ではない日
                    cols[i].markdown("<p style='text-align: center;'></p>", unsafe_allow_html=True)
                else:
                    # 日付をフォーマット
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    
                    # 記録があるかチェック
                    has_entry = date_str in month_dates
                    
                    # 今日の日付かチェック
                    is_today = date_str == datetime.now().strftime("%Y-%m-%d")
                    
                    # 背景色決定
                    if has_entry and is_today:
                        bg_color = "rgba(255, 215, 0, 0.6)"  # 金色 (今日かつ記録あり)
                        icon = "✅"
                    elif has_entry:
                        bg_color = "rgba(144, 238, 144, 0.6)"  # 緑 (記録あり)
                        icon = "✅"
                    elif is_today:
                        bg_color = "rgba(255, 182, 193, 0.3)"  # ピンク (今日)
                        icon = "📝"
                    else:
                        bg_color = "rgba(211, 211, 211, 0.2)"  # 灰色 (記録なし)
                        icon = ""
                    
                    cols[i].markdown(f"""
                    <div style='text-align: center; padding: 5px; background-color: {bg_color}; border-radius: 5px;'>
                        <p style='font-weight: {"bold" if is_today else "normal"}; margin-bottom: 2px;'>{day}</p>
                        <p style='margin: 0;'>{icon}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # 習慣化のヒントとアドバイス
    with st.expander("💡 習慣化のヒントとアドバイス"):
        st.markdown("""
        ### 日記を習慣化するためのヒント
        
        1. **同じ時間に書く**: 毎日決まった時間（朝や就寝前など）に日記を書く習慣をつけましょう。
        2. **小さく始める**: 最初は1〜2行でもOK。続けることが大切です。
        3. **場所を決める**: 日記を書く専用の場所を決めておくと、その場所に行くだけで書く習慣が身につきます。
        4. **アラームを設定**: 日記を書く時間にスマートフォンのアラームを設定しましょう。
        5. **ご褒美システム**: 連続記録を達成したら自分へのご褒美を用意しましょう。
        6. **可視化する**: カレンダーに記録をつけて、視覚的に確認できるようにしましょう。
        7. **内容より継続**: 内容の質より、まず継続することを重視しましょう。
        
        最初の30日間が最も重要です。この期間を乗り越えると習慣化されやすくなります！
        """)

# 📊 週間サマリーレポート機能
def weekly_summary_report():
    st.header("📈 週間サマリーレポート")
    
    diary = load_diary()
    if len(diary) == 0:
        st.info("まだ日記データがありません。")
        return
    
    # DataFrameに変換
    df = pd.DataFrame(diary)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    # 週の選択
    # 利用可能な週を計算
    df['week_start'] = df['date'].dt.to_period('W').dt.start_time
    df['week_end'] = df['date'].dt.to_period('W').dt.end_time
    df['week_label'] = df['week_start'].dt.strftime('%Y/%m/%d') + ' - ' + df['week_end'].dt.strftime('%Y/%m/%d')
    
    available_weeks = sorted(df['week_label'].unique(), reverse=True)
    
    if not available_weeks:
        st.warning("週ごとのデータがありません。")
        return
    
    selected_week = st.selectbox("週を選択", available_weeks)
    
    # 選択された週の開始日と終了日
    week_range = selected_week.split(' - ')
    start_date = pd.to_datetime(week_range[0])
    end_date = pd.to_datetime(week_range[1])
    
    # その週のデータを取得
    week_data = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    if week_data.empty:
        st.warning("選択された週のデータがありません。")
        return
    
    # 1. 基本統計情報
    st.subheader("📊 基本統計")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        entry_count = len(week_data)
        max_count = 7  # 1週間の最大日数
        completion_rate = int((entry_count / max_count) * 100)
        st.metric("記録日数", f"{entry_count}/{max_count}日")
    
    with col2:
        avg_rating = week_data['rating'].mean()
        st.metric("平均評価", f"{avg_rating:.1f}点")
    
    with col3:
        # 前週との比較
        prev_week_start = start_date - timedelta(days=7)
        prev_week_end = end_date - timedelta(days=7)
        prev_week_data = df[(df['date'] >= prev_week_start) & (df['date'] <= prev_week_end)]
        
        if not prev_week_data.empty:
            prev_avg_rating = prev_week_data['rating'].mean()
            delta = avg_rating - prev_avg_rating
            st.metric("前週比", f"{avg_rating:.1f}", f"{delta:+.1f}")
        else:
            st.metric("前週比", "データなし")
    
    with col4:
        if 'sleep_hours' in week_data.columns:
            avg_sleep = week_data['sleep_hours'].mean()
            st.metric("平均睡眠時間", f"{avg_sleep:.1f}時間")
        else:
            st.metric("平均睡眠時間", "データなし")
    
    # 2. 気分と体調の分布
    st.subheader("😊 気分・体調の分布")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'health' in week_data.columns:
            health_counts = week_data['health'].value_counts()
            fig = px.pie(names=health_counts.index, values=health_counts.values, title="体調の分布")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'mood' in week_data.columns and (week_data['mood'] != '選択しない').any():
            mood_data = week_data[week_data['mood'] != '選択しない']
            if not mood_data.empty:
                mood_counts = mood_data['mood'].value_counts()
                fig = px.pie(names=mood_counts.index, values=mood_counts.values, title="気分の分布")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("気分のデータがありません。")
        else:
            st.info("気分のデータがありません。")
    
    # 3. 活動の集計
    st.subheader("🏃‍♂️ 活動の集計")
    
    if 'activities' in week_data.columns:
        # すべての活動リスト
        all_activities = []
        for acts in week_data['activities']:
            if isinstance(acts, list):
                all_activities.extend(acts)
        
        if all_activities:
            activity_counts = pd.Series(all_activities).value_counts()
            fig = px.bar(
                x=activity_counts.index, 
                y=activity_counts.values, 
                title="実施した活動",
                labels={"x": "活動内容", "y": "回数"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 最も多く行った活動
            most_common = activity_counts.idxmax()
            st.success(f"💪 今週最も多く行った活動は「{most_common}」です（{activity_counts.max()}回）")
        else:
            st.info("活動データがありません。")
    else:
        st.info("活動データがありません。")
    
    # 4. 日々の評価の推移
    st.subheader("📈 評価の推移")
    
    # 日付でソート
    week_data_sorted = week_data.sort_values('date')
    fig = px.line(
        week_data_sorted, 
        x='date', 
        y='rating',
        title="日々の評価の推移",
        labels={"rating": "評価", "date": "日付"},
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 5. 重要な出来事のハイライト
    st.subheader("✨ 週のハイライト")
    
    # 最高評価の日
    if not week_data.empty:
        best_day = week_data.loc[week_data['rating'].idxmax()]
        
        st.markdown(f"""
        ### 今週のベストデー: {best_day['date'].strftime('%Y/%m/%d')} ({best_day.get('rating', 'N/A')}点)
        
        **天気**: {best_day.get('weather', 'N/A')}  
        **体調**: {best_day.get('health', 'N/A')}
        
        **活動**: {', '.join(best_day.get('activities', [])) if isinstance(best_day.get('activities', []), list) else 'なし'}
        
        **記録内容**:  
        {best_day.get('content', '')}
        """)
    
    # 6. キーワード分析
    st.subheader("🔍 頻出キーワード")
    
    # テキストデータを結合
    all_text = " ".join(week_data["content"].astype(str).tolist())
    
    if all_text.strip():
        # Janome の Tokenizer を作成
        t = Tokenizer()
        
        # 分かち書きされたテキストを格納するリスト
        wakati_text = []
        
        # ストップワード（除外したい単語）を定義
        japanese_stopwords = ["てる", "いる", "なる", "れる", "する", "ある", "こと", "これ", "さん", "して", 
                            "くれる", "やる", "くる", "しまう", "いく", "ない", "のだ", "よう", "あり", "ため", 
                            "ところ", "ます", "です", "から", "まで", "たり", "けど", "ので", "たい", "なる", 
                            "もの", "それ", "その", "今日", "の", "られる", "日"]
        
        # 形態素解析で分かち書き
        for token in t.tokenize(all_text):
            # 品詞の取得
            part_of_speech = token.part_of_speech.split(',')[0]
            # 基本形の取得
            base_form = token.base_form
            
            # 名詞、動詞、形容詞のみを抽出
            if part_of_speech in ['名詞', '動詞', '形容詞'] and base_form not in japanese_stopwords:
                # 除外したい単語以外を追加
                wakati_text.append(base_form)
        
        # 出現回数をカウント
        word_counts = pd.Series(wakati_text).value_counts().head(10)
        
        # 棒グラフで表示
        fig = px.bar(
            x=word_counts.index, 
            y=word_counts.values,
            title="頻出キーワードTop10",
            labels={"x": "キーワード", "y": "出現回数"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("テキストデータがありません。")
    
    # 7. 次週に向けた目標設定（任意入力）
    st.subheader("🎯 次週の目標設定")
    
    # 目標データの保存キー（週ごと）
    goal_key = f"goal_{start_date.strftime('%Y%m%d')}"
    
    # 既存の目標データを取得
    # 本来はJSONファイルなどに保存するべきですが、簡易的にsession_stateを使用
    existing_goal = st.session_state.get(goal_key, "")
    
    # 目標の入力フィールド
    new_goal = st.text_area("次週に向けた目標・アクションプラン", value=existing_goal, height=100)
    
    if st.button("目標を保存", key="save_goal"):
        st.session_state[goal_key] = new_goal
        st.success("✅ 目標を保存しました！")
    
    # 8. レポートのエクスポート
    st.subheader("📋 レポートのエクスポート")
    
    if st.button("週間レポートをCSVでエクスポート"):
        # エクスポート用にデータを整形
        export_data = week_data.copy()
        
        # 日付を文字列に変換
        export_data['date'] = export_data['date'].dt.strftime('%Y-%m-%d')
        
        # CSVとしてエクスポート
        csv = export_data.to_csv(index=False).encode('utf-8-sig')
        
        st.download_button(
            label="📥 CSVをダウンロード",
            data=csv,
            file_name=f"weekly_summary_{start_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

# メイン関数
def main():
    # サイドバーメニュー  
    st.sidebar.markdown("### 📅 メニュー")  
    menu = st.sidebar.selectbox(  
        "選択してください",  
        ["日記", "データ分析", "レポート", "設定・ヘルプ"]  
    )  
      
    if menu == "日記":  
        diary_option = st.sidebar.radio(  
            "日記機能",  
            ["✍️ 新規日記を書く", "📅 過去の日記を表示"]  
        )  
        if diary_option == "✍️ 新規日記を書く":  
            diary_form()  
        elif diary_option == "📅 過去の日記を表示":  
            display_entries()  
      
    elif menu == "データ分析":  
        analysis_option = st.sidebar.radio(  
            "分析機能",  
            ["📊 統計分析", "🔍 高度な可視化分析"]  
        )  
        if analysis_option == "📊 統計分析":  
            show_statistics()  
        elif analysis_option == "🔍 高度な可視化分析":  
            advanced_visualizations()  
      
    elif menu == "レポート":  
        report_option = st.sidebar.radio(  
            "レポート機能",  
            ["📈 週間サマリー", "📊 習慣化支援・連続記録"]  
        )  
        if report_option == "📈 週間サマリー":  
            weekly_summary_report()  
        elif report_option == "📊 習慣化支援・連続記録":  
            habit_tracking()  
          
    elif menu == "設定・ヘルプ":
        st.header("⚙️ 設定・ヘルプ")
        
        with st.expander("📝 アプリについて", expanded=True):
            st.markdown("""
            ### シンプル日記アプリ
            
            このアプリは、日々の出来事や感情を記録するためのシンプルな日記アプリです。
            
            **主な機能:**
            - 天気、体調、気分、活動などを記録
            - 過去の日記の検索・閲覧
            - データ分析と可視化
            - CSVエクスポート
            
            **使い方:**
            1. サイドバーメニューから「日記を書く」を選択
            2. 日付、天気、体調などを入力
            3. 日記の内容を記入して保存
            4. 「過去の日記」で過去の記録を確認
            5. 「データ分析」で傾向を分析
            """)
        
        with st.expander("🔄 データのバックアップ"):
            st.write("日記データのバックアップ・復元")
            
            # データのエクスポート
            diary = load_diary()
            if diary:
                st.download_button(
                    "📥 データをJSONファイルとしてバックアップ",
                    data=json.dumps(diary, indent=4, ensure_ascii=False),
                    file_name="diary_backup.json",
                    mime="application/json",
                )
            
            # データのインポート
            st.write("バックアップデータの復元:")
            uploaded_file = st.file_uploader("JSONファイルをアップロード", type=["json"])
            
            if uploaded_file is not None:
                if st.button("ファイルから復元"):
                    try:
                        imported_data = json.loads(uploaded_file.getvalue().decode("utf-8"))
                        save_diary(imported_data)
                        st.success("データを正常に復元しました！")
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")
        
        with st.expander("💾 全データの削除"):
            st.warning("⚠️ 注意: すべての日記データを削除します。この操作は元に戻せません。")
            
            if st.button("すべてのデータを削除", key="delete_all"):
                if os.path.exists(JSON_FILE):
                    os.remove(JSON_FILE)
                    st.success("全データを削除しました。")
                    st.balloons()
                else:
                    st.info("データファイルが存在しません。")
        
        # フッター
        st.markdown("---")
        st.markdown("© 2025 分析日記アプリ ver.1.0")

if __name__ == "__main__":
    main()
