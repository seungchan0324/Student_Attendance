import requests
import xml.etree.ElementTree as ET
import datetime as dt


class Student_status:

    AUTH_KEY = "cZWIhYgWESwlwL7TnsVukhU6jbMN9xDl"
    URL = "https://hrd.work24.go.kr/jsp/HRDP/HRDPO00/HRDPOA60/HRDPOA60_4.jsp"
    PARAMS_TEMPLATE = {
        "authKey": AUTH_KEY,
        "returnType": "XML",
        "srchTrprId": "AIG20240000459267",
        "srchTrprDegr": "1",
        "outType": "2",
        "srchTorgId": "student_detail",
        "atendMo": None,
    }

    def __init__(
        self,
        target_date: dt.date = None,
    ):
        self.target_date = target_date or dt.date.today()
        self.year_month = self.target_date.strftime("%Y%m")
        self.missing_people = {
            "지각": [],
            "결석": [],
            "조퇴": [],
            "휴가": [],
        }

    def get_check_in_status(self, time: int):
        slots = [
            (941, 1031, "1교시"),
            (1031, 1131, "2교시"),
            (1131, 1231, "3교시"),
            (1231, 1321, "4교시"),
            (1321, 1430, "점심시간"),
        ]

        for check_in, check_out, text in slots:
            if check_in <= time < check_out:
                return text
        return False

    def fetch_data(self):
        params = self.PARAMS_TEMPLATE.copy()
        params["atendMo"] = self.year_month
        headers = {
            "Referer": self.URL,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        }
        response = requests.get(self.URL, params=params, headers=headers)
        return ET.fromstring(response.text)

    def get_check_in_info(self, day_info: ET.Element):
        try:
            check_in_time = int(day_info.find("lpsilTime"))
            check_in_status = self.get_check_in_status(check_in_time)
            return check_in_time, check_in_status
        except (TypeError, ValueError):
            return None, None

    def parse_data(self, root: ET.Element):
        target_date_str = self.target_date.strftime("%Y%m%d")

        for day_info in root.find("atabList").findall("atab_list"):
            if day_info.find("atendDe").text != target_date_str:
                continue

            name = day_info.find("cstmrNm").text
            status = day_info.find("atendSttusNm").text

            if status in ("지각", "결석"):
                check_in_time, check_in_status = self.get_check_in_info(day_info)
                if check_in_time is None:
                    self.missing_people["결석"].append(name)
                else:
                    if check_in_status:
                        self.missing_people["지각"].append(
                            {
                                "이름": name,
                                "체크인": check_in_status,
                            }
                        )
                    elif check_in_time == 0:
                        self.missing_people["결석"].append(name)
            elif status == "조퇴":
                self.missing_people["조퇴"].append(name)
            elif status == "휴가":
                self.missing_people["휴가"].append(name)
        return self.missing_people

    def get_attendance_info(self):
        root = self.fetch_data()
        return self.parse_data(root)


if __name__ == "__main__":
    attendance = Student_status()
    missing_people = attendance.get_attendance_info()
    print(missing_people)


# def get_check_in_status(time):
#     # (시작 시간, 종료 시간, 상태 메시지) 튜플 리스트
#     slots = [
#         (941, 1031, "1교시"),
#         (1031, 1131, "2교시"),
#         (1131, 1231, "3교시"),
#         (1231, 1321, "4교시"),
#         (1321, 1430, "점심시간"),
#     ]

#     for start, end, status in slots:
#         if start <= time < end:
#             return status
#     return False


# x = dt.datetime.now()
# x_year = x.date().year
# x_month = x.date().month
# x_month_str = ("0" + str(x_month)) if len(str(x_month)) == 1 else x_month
# x_day = x.date().day
# x_day_str = ("0" + str(x_day)) if len(str(x_day)) == 1 else str(x_day)
# year_month = str(x_year) + x_month_str
# print(year_month)
# url = "https://hrd.work24.go.kr/jsp/HRDP/HRDPO00/HRDPOA60/HRDPOA60_4.jsp"
# params = {
#     "authKey": "cZWIhYgWESwlwL7TnsVukhU6jbMN9xDl",
#     "returnType": "XML",
#     "srchTrprId": "AIG20240000459267",
#     "srchTrprDegr": "1",
#     "outType": "2",
#     "srchTorgId": "student_detail",
#     "atendMo": year_month,
# }
# headers = {
#     "Referer": url,
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
# }
# with requests.get(url, params=params, headers=headers) as response:
#     response_str = response.text
# root = ET.fromstring(response_str)
# missing_people = {
#     "지각": [],
#     "결석": [],
#     "조퇴": [],
#     "휴가": [],
# }
# for day_info in root.find("atabList").findall("atab_list"):
#     if day_info.find("atendDe").text == year_month + x_day_str:
#         name = day_info.find("cstmrNm").text
#         status = day_info.find("atendSttusNm").text

#         if status == "지각":
#             check_in_time = int(day_info.find("lpsilTime").text)
#             check_in_status = get_check_in_status(check_in_time)
#             missing_people["지각"].append(
#                 {
#                     "이름": name,
#                     "체크인": check_in_status,
#                 }
#             )
#         elif status == "결석":
#             try:
#                 check_in_time = int(day_info.find("lpsilTime").text)
#                 check_in_status = get_check_in_status(check_in_time)
#             except AttributeError:
#                 missing_people["결석"].append(name)

#             if check_in_status and check_in_time != 0:
#                 missing_people["지각"].append(
#                     {
#                         "이름": name,
#                         "체크인": check_in_status,
#                     }
#                 )
#             elif check_in_time == 0:
#                 missing_people["결석"].append(name)

#         elif status == "조퇴":
#             missing_people["조퇴"].append(name)
#         elif status == "휴가":
#             missing_people["휴가"].append(name)


# print(missing_people)
