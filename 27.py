import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="Tournament System", page_icon="🏆", layout="wide")

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
            {"id": 0, "name": "Python Masters", "desc": "Бекенд змагання", "reg_start": "2026-04-01", "reg_end": "2026-05-01", "status": "Registration"}
        ]
        st.session_state.teams = []
        st.session_state.tasks = []
        st.session_state.submissions = [
            {"team": "CyberKnights", "github": "https://github.com/test1", "video": "https://vid.eo/1", "status": "Submitted"},
            {"team": "DataWizards", "github": "https://github.com/test2", "video": "https://vid.eo/2", "status": "Submitted"}
        ]
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
    st.title("🏆 Tournament Management System")
    st.subheader("Виберіть вашу роль для входу:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔴 Адміністратор (Admin)", use_container_width=True):
            st.session_state.role = "Admin"; st.rerun()
        if st.button("🟢 Учасник/Команда (Team)", use_container_width=True):
            st.session_state.role = "Team"; st.rerun()
    with col2:
        if st.button("🔵 Журі (Jury)", use_container_width=True):
            st.session_state.role = "Jury"; st.rerun()
        if st.button("🟡 Організатор (Organizer)", use_container_width=True):
            st.session_state.role = "Organizer"; st.rerun()

# --- БЛОК 8: ЗАГАЛЬНИЙ ОГЛЯД ТУРНІРІВ ---
def tournaments_overview():
    st.title("🌐 Огляд турнірів")
    status_filter = st.selectbox("Фільтр за статусом:", ["Всі", "Upcoming", "Registration", "Running", "Finished"])
    
    for t in st.session_state.tournaments:
        status = get_t_status(t)
        if status_filter == "Всі" or status_filter == status:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.subheader(t['name'])
                c1.write(t['desc'])
                c2.info(f"Статус: {status}")
                c2.write(f"📅 Реєстрація до: {t['reg_end']}")

# --- БЛОК 7: ТАБЛИЦЯ ЛІДЕРІВ ---
def leaderboard():
    st.title("🏆 Таблиця лідерів")
    if not st.session_state.evaluations:
        st.info("Оцінювання ще не розпочато.")
        return
    df = pd.DataFrame(st.session_state.evaluations)
    df = df.sort_values(by="total", ascending=False).reset_index(drop=True)
    df.index += 1
    st.table(df[['team', 'tech', 'func', 'total']])

# --- БЛОК 9: ПРОФІЛЬ ---
def user_profile():
    st.title("👤 Мій профіль")
    st.write(f"**Ваша роль:** {st.session_state.role}")
    if st.session_state.role == "Team" and st.session_state.teams:
        st.write("### Ваші команди:")
        for team in st.session_state.teams:
            st.write(f"- **Команда:** {team['name']} | **Капітан:** {team['captain']}")

# --- ПАНЕЛЬ ОРГАНІЗАТОРА ---
def organizer_page():
    st.title("🟡 Кабінет Організатора")
    is_registered = any(org.get('role_id') == "demo" for org in st.session_state.organizers)
    
    if not is_registered:
        st.subheader("Форма реєстрації організатора")
        with st.form("reg_org"):
            name = st.text_input("Повне ім'я")
            org_name = st.text_input("Назва організації")
            email = st.text_input("Email")
            if st.form_submit_button("Зареєструватися"):
                st.session_state.organizers.append({"name": name, "org": org_name, "email": email, "role_id": "demo"})
                save_data(); st.success("Ви зареєстровані як організатор!"); st.rerun()
    else:
        st.success("Ви успішно авторизовані як організатор.")
        st.info("Ви можете переглядати огляд турнірів та таблицю лідерів у бічному меню.")

# --- ПАНЕЛЬ АДМІНІСТРАТОРА ---
def admin_page():
    st.title("🛠 Панель Адміністратора")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏆 Турніри", "👥 Команди", "📝 Завдання", "📊 Сабміти", "👨‍⚖️ Журі"])
    
    with tab1:
        st.subheader("Створити новий турнір")
        with st.form("create_t"):
            name = st.text_input("Назва")
            desc = st.text_area("Опис")
            c1, c2 = st.columns(2)
            s_d = c1.date_input("Початок", datetime.now())
            e_d = c2.date_input("Кінець", datetime.now() + timedelta(days=7))
            if st.form_submit_button("Зберегти"):
                st.session_state.tournaments.append({"id": len(st.session_state.tournaments), "name": name, "desc": desc, "reg_start": str(s_d), "reg_end": str(e_d), "status": "Registration"})
                save_data(); st.success("Турнір створено!"); st.rerun()
        
        st.divider()
        st.subheader("Керування та видалення")
        for idx, t in enumerate(st.session_state.tournaments):
            col_t, col_st, col_del = st.columns([2, 1, 1])
            col_t.write(f"**{t['name']}**")
            new_st = col_st.selectbox("Статус", ["Upcoming", "Registration", "Running", "Finished"], 
                                      index=["Upcoming", "Registration", "Running", "Finished"].index(get_t_status(t)),
                                      key=f"st_{idx}")
            if new_st != t.get('status'):
                st.session_state.tournaments[idx]['status'] = new_st
                save_data(); st.toast("Оновлено")
            if col_del.button("Видалити", key=f"del_t_{idx}"):
                st.session_state.tournaments.pop(idx)
                save_data(); st.rerun()

    with tab2:
        st.subheader("Керування командами")
        if st.session_state.teams:
            for idx, team in enumerate(st.session_state.teams):
                col_name, col_cap, col_act = st.columns([2, 2, 1])
                col_name.write(f"**{team['name']}**")
                col_cap.write(f"Капітан: {team['captain']}")
                if col_act.button("Видалити", key=f"del_team_{idx}"):
                    st.session_state.teams.pop(idx)
                    save_data(); st.rerun()
        else: st.info("Команд ще немає.")

    with tab3:
        if st.session_state.tournaments:
            t_names = [t['name'] for t in st.session_state.tournaments]
            target_t = st.selectbox("Турнір:", t_names)
            with st.form("create_task"):
                title = st.text_input("Назва завдання"); content = st.text_area("Опис")
                if st.form_submit_button("🚀 Запустити"):
                    sel_t = next(t for t in st.session_state.tournaments if t['name'] == target_t)
                    st.session_state.tasks.append({"t_id": sel_t['id'], "title": title, "desc": content, "deadline": str(datetime.now().date())})
                    save_data(); st.success("Завдання опубліковано!")

    with tab4:
        st.subheader("Всі подані роботи")
        if st.session_state.submissions:
            st.dataframe(pd.DataFrame(st.session_state.submissions), use_container_width=True)
        else: st.info("Сабмітів ще немає.")

    with tab5:
        st.subheader("Додати нового члена журі")
        with st.form("add_jury"):
            j_name = st.text_input("ПІБ Судді")
            j_expert = st.text_input("Експертиза (напр. Python/AI)")
            if st.form_submit_button("Додати журі"):
                st.session_state.jury_list.append({"name": j_name, "expert": j_expert})
                save_data(); st.success(f"Журі {j_name} додано!")
        
        if st.session_state.get('jury_list'):
            st.write("### Список журі:")
            st.table(pd.DataFrame(st.session_state.jury_list))

# --- БЛОК 6: ПАНЕЛЬ ЖУРІ ---
def jury_page():
    st.title("⚖️ Оцінювання")
    if not st.session_state.submissions:
        st.info("Немає робіт для перевірки.")
        return
    for sub in st.session_state.submissions:
        with st.expander(f"Проєкт команди: {sub['team']}"):
            st.write(f"🔗 [GitHub Link]({sub['github']}) | 🎥 [Video Demo]({sub['video']})")
            with st.form(key=f"eval_{sub['team']}"):
                tech = st.slider("Технічна частина", 0, 100, 50)
                func = st.slider("Функціональність", 0, 100, 50)
                comment = st.text_area("Коментар")
                if st.form_submit_button("Зберегти оцінку"):
                    st.session_state.evaluations = [e for e in st.session_state.evaluations if e['team'] != sub['team']]
                    st.session_state.evaluations.append({"team": sub['team'], "tech": tech, "func": func, "total": (tech+func)/2, "comment": comment})
                    save_data(); st.success("Оцінено!")

# --- ПАНЕЛЬ КОМАНДИ ---
def team_page():
    st.title("🚀 Кабінет Команди")
    
    with st.expander("➕ Додати/Зареєструвати нову команду"):
        active_t = [t for t in st.session_state.tournaments if get_t_status(t) == "Registration"]
        if not active_t: 
            st.warning("Немає активних турнірів для реєстрації.")
        else:
            with st.form("reg_new_team"):
                t_choice = st.selectbox("Виберіть турнір", [t['name'] for t in active_t])
                team_n = st.text_input("Назва команди")
                cap = st.text_input("Капітан")
                if st.form_submit_button("Створити команду"):
                    t_obj = next(t for t in active_t if t['name'] == t_choice)
                    st.session_state.teams.append({"t_id": t_obj['id'], "name": team_n, "captain": cap})
                    save_data(); st.success("Команду створено!"); st.rerun()

    if st.session_state.teams:
        st.divider()
        st.subheader("🔄 Перемикання між профілями команд")
        
        team_names = [team['name'] for team in st.session_state.teams]
        if 'active_team_index' not in st.session_state:
            st.session_state.active_team_index = 0
            
        selected_team_name = st.selectbox("Виберіть активну команду:", team_names, index=st.session_state.active_team_index)
        st.session_state.active_team_index = team_names.index(selected_team_name)
        my_team = st.session_state.teams[st.session_state.active_team_index]
        
        st.info(f"Активний профіль: **{my_team['name']}**")
        
        task = next((t for t in st.session_state.tasks if t['t_id'] == my_team['t_id']), None)
        if task:
            st.subheader(f"📋 {task['title']}"); st.write(task['desc'])
            old_sub = next((s for s in st.session_state.submissions if s['team'] == my_team['name']), None)
            with st.form("sub"):
                git = st.text_input("GitHub", value=old_sub['github'] if old_sub else "")
                vid = st.text_input("Video", value=old_sub['video'] if old_sub else "")
                if st.form_submit_button("Здати роботу"):
                    if old_sub: old_sub.update({"github": git, "video": vid})
                    else: st.session_state.submissions.append({"team": my_team['name'], "github": git, "video": vid, "status": "Submitted"})
                    save_data(); st.success(f"Роботу команди {my_team['name']} здано!")
    else: st.info("У вас поки немає зареєстрованих команд.")

# --- 7. ЛОГІКА ЗАПУСКУ ---
if 'role' not in st.session_state:
    show_login_page()
else:
    st.sidebar.title(f"Ви: {st.session_state.role}")
    menu = ["🌐 Турніри", "📊 Таблиця лідерів", "👤 Профіль"]
    if st.session_state.role == "Admin": menu.insert(0, "🛠 Адмін-панель")
    if st.session_state.role == "Team": menu.insert(0, "🚀 Моя Команда")
    if st.session_state.role == "Jury": menu.insert(0, "⚖️ Оцінювання")
    if st.session_state.role == "Organizer": menu.insert(0, "🟡 Організатор")
    
    choice = st.sidebar.radio("Навігація", menu)
    if st.sidebar.button("Вийти"):
        del st.session_state.role; st.rerun()
    
    if choice == "🛠 Адмін-панель": admin_page()
    elif choice == "🚀 Моя Команда": team_page()
    elif choice == "⚖️ Оцінювання": jury_page()
    elif choice == "🟡 Організатор": organizer_page()
    elif choice == "🌐 Турніри": tournaments_overview()
    elif choice == "📊 Таблиця лідерів": leaderboard()
    elif choice == "👤 Профіль": user_profile()
