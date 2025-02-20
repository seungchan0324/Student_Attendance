import requests
import streamlit as st
import datetime as dt
import xml.etree.ElementTree as ET
import json


st.set_page_config(page_title="SolAttendance", page_icon="✅", layout="wide")

if "selected_teacher" not in st.session_state:
    st.session_state.selected_teacher = {}
if "key" not in st.session_state:
    st.session_state.key = False
if "input_key" not in st.session_state:
    st.session_state.input_key = None

with open("./json/teachers_data.json", "r", encoding="utf-8") as f:
    teachers_data = json.load(f)
with open("./json/not_teachers_data.json", "r", encoding="utf-8") as f:
    not_teachers_data = json.load(f)


def key_change(key):
    if key == "$sol25":
        st.session_state.key = True
        st.rerun()


def deduplication_procedure(teachers_data):
    # 개강일 내림차순 정렬(최신순으로 보이기 위함)
    teachers_data = sorted(
        teachers_data,
        key=lambda x: (dt.datetime.strptime(x["훈련시작일"], "%Y-%m-%d").date()),
        reverse=True,
    )

    # 순서 유지하고 중복제거
    teachers = []
    seen_names = set()
    for item in teachers_data:
        if item["강사"] not in seen_names:
            teachers.append(item)
            seen_names.add(item["강사"])

    return teachers


def extract_attendance(procedure):
    url = "https://hrd.work24.go.kr/jsp/HRDP/HRDPO00/HRDPOA60/HRDPOA60_4.jsp"
    params = {
        "authKey": "cZWIhYgWESwlwL7TnsVukhU6jbMN9xDl",
        "returnType": "XML",
        "srchTrprId": procedure["과정ID"],
        "srchTrprDegr": procedure["회차"],
        "outType": "2",
    }
    headers = {
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    with requests.get(url, params=params, headers=headers) as response:
        response_str = response.text
    root = ET.fromstring(response_str)

    st_data = []
    for student in root.find("trneList").findall("trne_list"):
        st_data.append(
            {
                "훈련생 이름": student.find("trneeCstmrNm").text,
                "결석일수": int(student.find("absentCnt").text),
                "출석일수": int(student.find("atendCnt").text),
                "휴가일수": int(student.find("vcatnCnt").text),
                "훈련생 상태": student.find("trneeSttusNm").text,
            }
        )
    st_data = sorted(
        st_data,
        key=lambda x: x["훈련생 상태"],
        reverse=True,
    )
    st.dataframe(st_data)


def extract_today_attendance(procedure):
    url = "https://hrd.work24.go.kr/jsp/HRDP/HRDPO00/HRDPOA60/HRDPOA60_4.jsp"
    params = {
        "authKey": "cZWIhYgWESwlwL7TnsVukhU6jbMN9xDl",
        "returnType": "XML",
        "srchTrprId": procedure["과정ID"],
        "srchTrprDegr": procedure["회차"],
        "outType": "2",
        "srchTorgId": "student_detail",
        "atendMo": "",
    }
    headers = {
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    with requests.get(url, params=params, headers=headers) as response:
        response_str = response.text
    root = ET.fromstring(response_str)


if st.session_state.key == True:
    teachers = deduplication_procedure(teachers_data)
    with st.sidebar:
        for idx, teacher in enumerate(teachers):
            if st.button(teacher["강사"], key=f"sidebar_{idx}"):
                st.session_state.selected_teacher["과정ID"] = teacher["과정ID"]
                st.session_state.selected_teacher["회차"] = teacher["회차"]

    if not st.session_state.selected_teacher:

        st.dataframe(teachers)
        pass
    else:
        # 출석 api 가져온거 표시
        extract_attendance(st.session_state.selected_teacher)
        extract_today_attendance(st.session_state.selected_teacher)
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
