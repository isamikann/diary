import streamlit as st  
  
# ページの設定  
st.set_page_config(  
    page_title="分析日記アプリ",  
    page_icon="📖",  
    layout="wide",  
    initial_sidebar_state="expanded",  
)  
  
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
  
# GitHub リポジトリ情報  
GITHUB_REPO = "isamikann/diary"  
GITHUB_FILE_PATH = "diary.json"  
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]  
  
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
  
@st.cache_data  
def load_diary():  
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_FILE_PATH}?ref=main"  
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
  
# 🎨 サイドバーとスタイル設定  
def setup_page():  
    # サイドバーにアプリタイトルとテーマ選択  
    st.sidebar.title("📖 シンプル日記アプリ")  
    theme = st.sidebar.selectbox("🎨 テーマを選択", ["ライト", "ダーク", "カラフル", "シンプル"])  
  
    # テーマに基づいたスタイルを適用  
    if theme == "ダーク":  
        st.markdown("""  
        <style>  
        .main {background-color: #1E1E1E; color: #FFFFFF;}  
        .stButton>button {background-color: #4CAF50; color: white;}  
        </style>  
        """, unsafe_allow_html=True)  
    elif theme == "カラフル":  
        st.markdown("""  
        <style>  
        .main {background-color: #F8F9FA;}  
        .stButton>button {background-color: #FF6B6B; color: white;}  
        h1, h2, h3 {color: #5D5FEF;}  
        </style>  
        """, unsafe_allow_html=True)  
    elif theme == "シンプル":  
        st.markdown("""  
        <style>  
        .main {background-color: #FFFFFF; color: #333333;}  
        .stButton>button {background-color: #333333; color: white;}  
        h1, h2, h3 {color: #333333; font-family: 'Helvetica', sans-serif;}  
        </style>  
        """, unsafe_allow_html=True)  
      
    # 共通のスタイルを適用  
    st.markdown("""  
    <style>  
    .diary-entry {  
        padding: 15px;  
        border-radius: 5px;  
        margin-bottom: 10px;  
        background-color: rgba(240, 240, 240, 0.3);  
        border-left: 5px solid #4CAF50;  
    }  
    .rating-stars {  
        color: gold;  
        font-size: 20px;  
    }  
    </style>  
    """, unsafe_allow_html=True)  
      
    return theme  
  
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
    cols = st.columns(3)  
    selected_activities = []  
    for i, activity in enumerate(activity_options):  
        if cols[i % 3].checkbox(activity, activity in activities):  
            selected_activities.append(activity)  
      
    # 日記の内容  
    st.write("📝 日記")  
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
      
    view_type = st.radio("表示方法", ["リスト表示", "カレンダー表示"], horizontal=True)  
    if view_type == "カレンダー表示":  
        display_calendar(diary)  
        return  
      
    with st.expander("🔍 検索・フィルター", expanded=False):  
        col1, col2 = st.columns(2)  
        with col1:  
            search_query = st.text_input("🔍 キーワード検索", "")  
            filter_weather = st.selectbox("🌤 天気で絞り込む", ["すべて"] + list(set(d.get("weather", "") for d in diary if "weather" in d)))  
        with col2:  
            filter_health = st.selectbox("😷 体調で絞り込む", ["すべて"] + list(set(d.get("health", "") for d in diary if "health" in d)))  
            filter_rating = st.selectbox("⭐ 評価で絞り込む", ["すべて", "1", "2", "3", "4", "5"])  
        all_activities = set()  
        for entry in diary:  
            if "activities" in entry and entry["activities"]:  
                all_activities.update(entry["activities"])  
        filter_activity = st.multiselect("🏃‍♂️ 活動で絞り込む", list(all_activities))  
      
    filtered_diary = diary.copy()  
    if search_query or filter_weather != "すべて" or filter_health != "すべて" or filter_rating != "すべて" or filter_activity:  
        filtered_diary = [d for d in diary if   
            (not search_query or search_query.lower() in d.get("content", "").lower() or search_query.lower() in d.get("memo", "").lower()) and  
            (filter_weather == "すべて" or d.get("weather", "") == filter_weather) and  
            (filter_health == "すべて" or d.get("health", "") == filter_health) and  
            (filter_rating == "すべて" or str(d.get("rating", "")) == filter_rating) and  
            (not filter_activity or any(activity in d.get("activities", []) for activity in filter_activity))  
        ]  
      
    sort_option = st.selectbox("並び替え", ["日付順（新しい順）", "日付順（古い順）", "評価（高い順）", "評価（低い順）"])  
    if sort_option == "日付順（新しい順）":  
        filtered_diary = sorted(filtered_diary, key=lambda x: x["date"], reverse=True)  
    elif sort_option == "日付順（古い順）":  
        filtered_diary = sorted(filtered_diary, key=lambda x: x["date"])  
    elif sort_option == "評価（高い順）":  
        filtered_diary = sorted(filtered_diary, key=lambda x: x.get("rating", 0), reverse=True)  
    elif sort_option == "評価（低い順）":  
        filtered_diary = sorted(filtered_diary, key=lambda x: x.get("rating", 0))  
      
    if len(filtered_diary) == 0:  
        st.warning("該当する日記が見つかりません。")  
    else:  
        st.success(f"{len(filtered_diary)}件の日記が見つかりました")  
        for entry in filtered_diary:  
            with st.container():  
                st.markdown(f"""  
                <div class="diary-entry">  
                    <h3>📆 {entry['date']}</h3>  
                    <p>🌤 天気: {entry.get('weather', '未記入')} | 😷 体調: {entry.get('health', '未記入')} |   
                    <span class="rating-stars">{'⭐' * entry.get('rating', 0)}</span></p>  
                    <p>📝 {entry.get('content', '').replace('\n', '<br>')}</p>  
                """, unsafe_allow_html=True)  
                if "activities" in entry and entry["activities"]:  
                    activities_html = ' '.join([f'<span style="background-color: #E1F5FE; padding: 3px 8px; border-radius: 10px; margin-right: 5px;">{a}</span>' for a in entry["activities"]])  
                    st.markdown(f"<p>🏃‍♂️ {activities_html}</p>", unsafe_allow_html=True)  
                if "mood" in entry and entry["mood"] and entry["mood"] != "選択しない":  
                    st.markdown(f"<p>🧠 気分: {entry['mood']}</p>", unsafe_allow_html=True)  
                if "memo" in entry and entry["memo"]:  
                    st.markdown(f"<p>📌 メモ: {entry['memo']}</p>", unsafe_allow_html=True)  
                st.markdown("</div>", unsafe_allow_html=True)  
                st.markdown("---")  
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
    df = pd.DataFrame(diary)  
    df["date"] = pd.to_datetime(df["date"])  
    all_months = sorted(df["date"].dt.strftime("%Y-%m").unique())  
    if not all_months:  
        st.info("日記のデータがありません。")  
        return  
    default_month_index = 0  
    selected_month = st.selectbox(  
        "月を選択",   
        all_months,   
        index=default_month_index,  
        format_func=lambda x: f"{x[:4]}年{x[5:]}月"  
    )  
    year, month = map(int, selected_month.split('-'))  
    cal = calendar.monthcalendar(year, int(month))  
    month_data = df[df["date"].dt.strftime("%Y-%m") == selected_month]  
    cols = st.columns(7)  
    days = ["月", "火", "水", "木", "金", "土", "日"]  
    for i, day in enumerate(days):  
        cols[i].markdown(f"<p style='text-align: center; font-weight: bold;'>{day}</p>", unsafe_allow_html=True)  
    for week in cal:  
        cols = st.columns(7)  
        for i, day in enumerate(week):  
            if day == 0:  
                cols[i].markdown("<p style='text-align: center;'></p>", unsafe_allow_html=True)  
            else:  
                date_str = f"{year}-{month:02d}-{day:02d}"  
                day_data = month_data[month_data["date"].dt.strftime("%Y-%m-%d") == date_str]  
                if not day_data.empty:  
                    rating = day_data.iloc[0].get("rating", 0)  
                    weather = day_data.iloc[0].get("weather", "")  
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
                    cols[i
