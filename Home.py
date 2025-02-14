import streamlit as st
import datetime as dt
import json


st.set_page_config(page_title="SolAttendance", page_icon="✅", layout="wide")

if "selected_teacher" not in st.session_state:
    st.session_state.selected_teacher = None
if "key" not in st.session_state:
    st.session_state.key = False
if "input_key" not in st.session_state:
    st.session_state.input_key = None


with open("./persons.json", "r", encoding="utf-8") as f:
    teachers_data = json.load(f)


def key_change(key):
    if key == "$sol25":
        st.session_state.key = True
        st.rerun()


teachers = [
    "최규리",
    "오창석",
    "박진경",
    "김우태",
    "정세나",
    "이수진",
    "백승찬",
    "이명재",
]

if st.session_state.key == True:
    with st.sidebar:
        for idx, teacher in enumerate(teachers):
            if st.button(teacher, key=f"sidebar_{idx}"):
                st.session_state.selected_teacher = teacher
    if not st.session_state.selected_teacher:
        # dataframe 표시
        teachers_data = sorted(
            teachers_data,
            key=lambda x: (dt.datetime.strptime(x["훈련시작일"], "%Y-%m-%d").date()),
        )
        teachers_data = sorted(
            list({d["강사"]: d for d in teachers_data}.values()),
            key=lambda x: (dt.datetime.strptime(x["훈련시작일"], "%Y-%m-%d").date()),
            reverse=True,
        )
        st.dataframe(teachers_data)
        pass
    else:
        # 출석 api 가져온거 표시
        pass

else:
    with st.sidebar:
        key = st.text_input(
            "키를 입력하여 주십시오.",
            value=st.session_state.input_key,
            type="password",
        )
        if key:
            key_change(key)
    st.warning("왼쪽에서 키를 입력하여 주십시오.")
