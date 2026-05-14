import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ТА СТИЛІЗАЦІЯ ---
st.set_page_config(page_title="Аграрний Турнір", page_icon="🌱", layout="wide")

def local_css():
    st.markdown(f"""
    <style>
    /* Основні кольори аграрного коледжу */
    :root {{
        --primary-green: #2E7D32;
        --light-green: #E8F5E9;
        --accent-yellow: #FBC02D;
    }}
    
    /* Фон та заголовки */
    .stApp {{
        background-color: #fdfdfd;
    }}
    
    h1, h2, h3 {{
        color: var(--primary-green) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    /* Кастомні картки для турнірів */
    .tournament-card {{
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid var(--primary-green);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}

    /* Кнопки */
    .stButton>button {{
        border-radius: 20px;
        border: 2px solid var(--primary-green);
        background-color: white;
        color: var(--primary-green);
        transition: 0.3s;
    }}
    
    .stButton>button:hover {{
        background-color: var(--primary-green);
        color: white;
        border: 2px solid var(--primary-green);
    }}

    /* Сайдбар */
    [data-testid="stSidebar"] {{
        background-color: var(--light-green);
    }}
    
    /* Статуси */
    .status-badge {{
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- ФУНКЦІЇ ЗБЕРЕЖЕННЯ ДАНИХ ---
DB_FILE = "tournament_db.json"

def save_data():
    data = {
        "tournaments": st.session_state.tournaments,
        "teams": st.session_state.teams,
        "tasks": st.session_state.tasks,
        "submissions": st.session_state.submissions,
        "evaluations": st.session_state.evaluations,
        "jury_list": st.session_state.get('jury_list', []),
        "organizers": st.session_state.get('organizers', [])
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, default=str, indent=4)

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# --- 2. ІНІЦІАЛІЗАЦІЯ ДАНИХ ---
if 'db_initialized' not in st.session_state:
    saved = load_data()
    if saved:
        for key in saved: st.session_state[key] = saved[key]
    else:
        st.session_state.tournaments = [
            {"id": 0, "name": "Агро-Інновації 2026", "desc": "Конкурс цифрових рішень для фермерства", "reg_start": "2026-04-01", "reg_end": "2026-05-01", "status": "Registration"}
        ]
        st.session_state.teams = []
        st.session_state.tasks = []
        st.session_state.submissions = []
        st.session_state.evaluations = []
        st.session_state.jury_list = []
        st.session_state.organizers = []
    st.session_state.db_initialized = True

# --- 3. ДОПОМІЖНІ ФУНКЦІЇ ---
def get_t_status(t):
    if 'status' in t: return t['status']
    now = datetime.now().date()
    start = datetime.strptime(str(t['reg_start']), '%Y-%m-%d').date()
    end = datetime.strptime(str(t['reg_end']), '%Y-%m-%d').date()
    if now < start: return "Upcoming"
    if start <= now <= end: return "Registration"
    return "Running"

# --- 4. ГОЛОВНА СТОРІНКА (ВХІД) ---
def show_login_page():
    st.markdown("<h1 style='text-align: center;'>🌱 Система управління турнірами</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Вітаємо у цифровому кабінеті нашого коледжу!</p>", unsafe_allow_html=True)
    
    st.write("---")
    
    # Використовуємо контейнери для красивого розміщення
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🔴 АДМІНІСТРАТОР", use_container_width=True):
                st.session_state.role = "Admin"; st.rerun()
        with col2:
            if st.button("🟢 УЧАСНИК", use_container_width=True):
                st.session_state.role = "Team"; st.rerun()
        with col3:
            if st.button("🔵 ЖУРІ", use_container_width=True):
                st.session_state.role = "Jury"; st.rerun()
        with col4:
            if st.button("🟡 ОРГАНІЗАТОР", use_container_width=True):
                st.session_state.role = "Organizer"; st.rerun()

    st.image("https://img.freepik.com/free-vector/organic-flat-farming-concept_23-2148421008.jpg", use_container_width=True)

# --- БЛОК 8: ЗАГАЛЬНИЙ ОГЛЯД ТУРНІРІВ ---
def tournaments_overview():
    st.title("🌐 Наші Турніри")
    status_filter = st.selectbox("Фільтрувати змагання:", ["Всі", "Upcoming", "Registration", "Running", "Finished"])
    
    for t in st.session_state.tournaments:
        status = get_t_status(t)
        if status_filter == "Всі" or status_filter == status:
            st.markdown(f"""
            <div class="tournament-card">
                <h3>🌿 {t['name']}</h3>
                <p>{t['desc']}</p>
                <p><b>📅 Дедлайн реєстрації:</b> {t['reg_end']}</p>
                <span style="background-color: #C8E6C9; padding: 5px 15px; border-radius: 20px; font-weight: bold; color: #2E7D32;">{status}</span>
            </div>
            """, unsafe_allow_html=True)

# --- БЛОК 7: ТАБЛИЦЯ ЛІДЕРІВ ---
def leaderboard():
    st.title("🏆 Результати змагань")
    if not st.session_state.evaluations:
        st.info("Результати будуть опубліковані після оцінювання.")
        return
    df = pd.DataFrame(st.session_state.evaluations)
    df = df.sort_values(by="total", ascending=False).reset_index(drop=True)
    df.index += 1
    # Кольорове оформлення таблиці
    st.dataframe(df[['team', 'tech', 'func', 'total']].style.highlight_max(axis=0, color='#C8E6C9'), use_container_width=True)

# --- БЛОК 9: ПРОФІЛЬ ---
def user_profile():
    st.title("👤 Мій Кабінет")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/201/201630.png", width=150)
    with col2:
        st.write(f"**Ваша роль:** {st.session_state.role}")
        if st.session_state.role == "Team" and st.session_state.teams:
            st.write("### Ваші активні команди:")
            for team in st.session_state.teams:
                st.success(f"🌽 {team['name']} (Капітан: {team['captain']})")

# --- ПАНЕЛЬ ОРГАНІЗАТОРА ---
def organizer_page():
    st.title("🟡 Кабінет Організатора")
    is_registered = any(org.get('role_id') == "demo" for org in st.session_state.organizers)
    
    if not is_registered:
        with st.form("reg_org"):
            st.subheader("Реєстрація організатора змагань")
            name = st.text_input("ПІБ")
            org_name = st.text_input("Кафедра / Організація")
            email = st.text_input("Email")
            if st.form_submit_button("Підтвердити"):
                st.session_state.organizers.append({"name": name, "org": org_name, "email": email, "role_id": "demo"})
                save_data(); st.success("Ви зареєстровані!"); st.rerun()
    else:
        st.success("Ви маєте доступ до перегляду всіх процесів.")
        st.info("Скористайтеся бічним меню для доступу до таблиці лідерів.")

# --- ПАНЕЛЬ АДМІНІСТРАТОРА ---
def admin_page():
    st.title("🛠 Налаштування Системи")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🌱 Турніри", "🚜 Команди", "📝 Завдання", "📊 Звіти", "👨‍⚖️ Журі"])
    
    with tab1:
        st.subheader("Створити нову подію")
        with st.form("create_t"):
            name = st.text_input("Назва конкурсу")
            desc = st.text_area("Мета та умови")
            c1, c2 = st.columns(2)
            s_d = c1.date_input("Початок реєстрації", datetime.now())
            e_d = c2.date_input("Дедлайн", datetime.now() + timedelta(days=7))
            if st.form_submit_button("Опублікувати турнір"):
                st.session_state.tournaments.append({"id": len(st.session_state.tournaments), "name": name, "desc": desc, "reg_start": str(s_d), "reg_end": str(e_d), "status": "Registration"})
                save_data(); st.success("Турнір з'явився у списку!"); st.rerun()
        
        st.divider()
        for idx, t in enumerate(st.session_state.tournaments):
            with st.expander(f"Редагувати: {t['name']}"):
                new_st = st.selectbox("Змінити статус", ["Upcoming", "Registration", "Running", "Finished"], 
                                      index=["Upcoming", "Registration", "Running", "Finished"].index(get_t_status(t)),
                                      key=f"st_{idx}")
                if st.button("Оновити статус", key=f"btn_st_{idx}"):
                    st.session_state.tournaments[idx]['status'] = new_st
                    save_data(); st.rerun()
                if st.button("🗑 Видалити турнір", key=f"del_t_{idx}"):
                    st.session_state.tournaments.pop(idx); save_data(); st.rerun()

    with tab2:
        if st.session_state.teams:
            for idx, team in enumerate(st.session_state.teams):
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**{team['name']}**")
                c2.write(f"👤 {team['captain']}")
                if c3.button("Видалити", key=f"del_team_{idx}"):
                    st.session_state.teams.pop(idx); save_data(); st.rerun()
        else: st.info("Команди ще не зареєстровані.")

    with tab3:
        if st.session_state.tournaments:
            t_names = [t['name'] for t in st.session_state.tournaments]
            target_t = st.selectbox("Вибрати турнір для завдання:", t_names)
            with st.form("create_task"):
                title = st.text_input("Назва кейсу/завдання")
                content = st.text_area("Детальні інструкції")
                if st.form_submit_button("🚀 Надіслати учасникам"):
                    sel_t = next(t for t in st.session_state.tournaments if t['name'] == target_t)
                    st.session_state.tasks.append({"t_id": sel_t['id'], "title": title, "desc": content, "deadline": str(datetime.now().date())})
                    save_data(); st.success("Завдання опубліковано!")

    with tab4:
        st.subheader("Подані роботи студентів")
        if st.session_state.submissions:
            st.table(pd.DataFrame(st.session_state.submissions))
        else: st.info("Роботи ще не надходили.")

    with tab5:
        st.subheader("Формування складу журі")
        with st.form("add_jury"):
            j_name = st.text_input("ПІБ викладача/експерта")
            j_expert = st.text_input("Напрямок (Агрономія, ТВППТ, ТТ тощо)")
            if st.form_submit_button("Додати"):
                st.session_state.jury_list.append({"name": j_name, "expert": j_expert})
                save_data(); st.success("Склад журі оновлено!")

# --- БЛОК 6: ПАНЕЛЬ ЖУРІ ---
def jury_page():
    st.title("⚖️ Оцінювання проєктів")
    if not st.session_state.submissions:
        st.info("Чекаємо на завантаження робіт учасниками.")
        return
    for sub in st.session_state.submissions:
        with st.container(border=True):
            st.subheader(f"🌾 Команда: {sub['team']}")
            st.write(f"🔗 [Переглянути код]({sub['github']}) | 🎥 [Відеопрезентація]({sub['video']})")
            with st.form(key=f"eval_{sub['team']}"):
                c1, c2 = st.columns(2)
                tech = c1.slider("Технічна реалізація", 0, 100, 70)
                func = c2.slider("Корисність для галузі", 0, 100, 70)
                comment = st.text_area("Порада студентам")
                if st.form_submit_button("Надіслати оцінку"):
                    st.session_state.evaluations = [e for e in st.session_state.evaluations if e['team'] != sub['team']]
                    st.session_state.evaluations.append({"team": sub['team'], "tech": tech, "func": func, "total": (tech+func)/2, "comment": comment})
                    save_data(); st.success("Оцінку збережено!")

# --- ПАНЕЛЬ КОМАНДИ ---
def team_page():
    st.title("🚀 Кабінет Учасника")
    
    with st.expander("🆕 Створити нову команду"):
        active_t = [t for t in st.session_state.tournaments if get_t_status(t) == "Registration"]
        if not active_t: 
            st.warning("Наразі реєстрація на нові турніри закрита.")
        else:
            with st.form("reg_new_team"):
                t_choice = st.selectbox("Турнір", [t['name'] for t in active_t])
                team_n = st.text_input("Назва вашої команди")
                cap = st.text_input("ПІБ капітана")
                if st.form_submit_button("Зареєструватися"):
                    t_obj = next(t for t in active_t if t['name'] == t_choice)
                    st.session_state.teams.append({"t_id": t_obj['id'], "name": team_n, "captain": cap})
                    save_data(); st.success("Успіх! Вас додано до списку учасників."); st.rerun()

    if st.session_state.teams:
        st.divider()
        team_names = [team['name'] for team in st.session_state.teams]
        if 'active_team_index' not in st.session_state: st.session_state.active_team_index = 0
            
        selected_team_name = st.selectbox("Вибрати активний профіль:", team_names, index=st.session_state.active_team_index)
        st.session_state.active_team_index = team_names.index(selected_team_name)
        my_team = st.session_state.teams[st.session_state.active_team_index]
        
        st.info(f"Ви працюєте від імені команди: **{my_team['name']}**")
        
        task = next((t for t in st.session_state.tasks if t['t_id'] == my_team['t_id']), None)
        if task:
            st.subheader(f"📋 Завдання: {task['title']}")
            st.write(task['desc'])
            old_sub = next((s for s in st.session_state.submissions if s['team'] == my_team['name']), None)
            with st.form("sub"):
                git = st.text_input("Посилання на проєкт", value=old_sub['github'] if old_sub else "")
                vid = st.text_input("Посилання на відео", value=old_sub['video'] if old_sub else "")
                if st.form_submit_button("Здати проєкт"):
                    if old_sub: old_sub.update({"github": git, "video": vid})
                    else: st.session_state.submissions.append({"team": my_team['name'], "github": git, "video": vid, "status": "Submitted"})
                    save_data(); st.success("Роботу успішно надіслано на перевірку журі!")
    else: st.info("Ви ще не зареєстрували жодної команди.")

# --- 7. ЛОГІКА ЗАПУСКУ ---
if 'role' not in st.session_state:
    show_login_page()
else:
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.role}")
        st.image("https://cdn-icons-png.flaticon.com/512/188/188333.png", width=80)
        st.divider()
        
        menu = ["🌐 Турніри", "📊 Таблиця лідерів", "👤 Профіль"]
        if st.session_state.role == "Admin": menu.insert(0, "🛠 Адмін-панель")
        if st.session_state.role == "Team": menu.insert(0, "🚀 Моя Команда")
        if st.session_state.role == "Jury": menu.insert(0, "⚖️ Оцінювання")
        if st.session_state.role == "Organizer": menu.insert(0, "🟡 Організатор")
        
        choice = st.radio("Навігація:", menu)
        
        st.sidebar.write("---")
        if st.sidebar.button("🚪 Вийти з системи"):
            del st.session_state.role; st.rerun()

    # Відображення вибраної сторінки
    if choice == "🛠 Адмін-панель": admin_page()
    elif choice == "🚀 Моя Команда": team_page()
    elif choice == "⚖️ Оцінювання": jury_page()
    elif choice == "🟡 Організатор": organizer_page()
    elif choice == "🌐 Турніри": tournaments_overview()
    elif choice == "📊 Таблиця лідерів": leaderboard()
    elif choice == "👤 Профіль": user_profile()
