import requests
import json
import collections
import csv
import re
import time
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
import datetime as dt


class Use_API:

    with open("./json/과정_강사.json", "r", encoding="utf-8") as f:
        location_data = json.load(f)

    # apikey
    authKey = "9aa1c3c5-e44f-4ccc-a119-e0af76286b28"
    # returnType 절대절대 고정
    returnType = "JSON"
    # 1은 리스트 2는 상세(고정) 솔직히 뭐가 다른건지 모르겠음.
    outType = "2"
    # 페이지당 출력건수(고정)
    pageSize = "100"

    # 정렬방법, 정렬컬럼(고정)
    sort = "DESC"
    sortCol = "TOT_FXNUM"

    # 6개월 기준 취업률에 적혀 있는 문자별 상태값
    status_dict = {
        "A": "개설예정",
        "B": "진행중",
        "C": "미실시",
        "D": "수료자 없음",
    }

    # 지역, 직종, 훈련유형, 개강일, 종강일, 훈련과정명, 훈련기관명
    def __init__(
        self,
        srchTraStDt,
        srchTraEndDt,
        srchTraAreals,
        srchNcsls,
        crseTracseSels,
    ):
        # 훈련시작일 From, 훈련시작일 To
        self.srchTraStDt = str(srchTraStDt).replace("-", "")
        self.startDate = srchTraStDt
        self.srchTraEndDt = str(srchTraEndDt).replace("-", "")
        self.endDate = srchTraEndDt

        # 11만 쓰면 서울
        self.srchTraAreals = srchTraAreals
        # NCS 직종 대분류, 중분류, 소분류
        self.srchNcsls = srchNcsls
        # 훈련유형 K-digital 여긴 ,로 여러개 가능
        self.crseTracseSels = crseTracseSels
        if "None" in crseTracseSels:
            self.crseTracseSelstr = ""
        else:
            self.crseTracseSelstr = ",".join(crseTracseSels)

    # 1. 추가 정보 API 호출 (140시간 이상 체크)
    async def day_extractor(
        self,
        session,
        srchTrprId,
        trainstCstId,
        trprDegr,
    ):
        url = (
            f"https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L02.do"
            f"?authKey={self.authKey}&returnType=JSON&outType=2"
            f"&srchTrprId={srchTrprId}&srchTorgId={trainstCstId}&srchTrprDegr={trprDegr}"
        )
        async with session.get(url) as response:
            data = await response.json()
        try:
            for info in (data.get("inst_base_info"), []):
                return {
                    "과정명": info["trprNm"],
                    "훈련일수": info["trDcnt"],
                    "과정ID": srchTrprId,
                }
        except Exception as e:
            print("day_extractor 에러:", e, srchTrprId)
        return []

    # 2. 목록 API 호출 (페이지 단위) 및 배치화
    async def search_procedure_list_async(
        self,
        session,
        srchTraArea,
        srchNcs,
        crseTracseSe,
    ):
        # 초기화
        pageNum = 1

        srchList = []
        while True:
            url = (
                f"https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L01.do"
                f"?authKey={self.authKey}&returnType={self.returnType}&outType={self.outType}"
                f"&pageNum={pageNum}&pageSize={self.pageSize}"
                f"&srchTraStDt={self.srchTraStDt}&srchTraEndDt={self.srchTraEndDt}"
                f"&srchTraArea1={srchTraArea}&srchNcs1={srchNcs}&crseTracseSe={crseTracseSe}"
                f"&sort={self.sort}&sortCol={self.sortCol}&srchTraOrganNm=솔데스크"
            )
            tasks = []
            async with session.get(url) as response:
                data = await response.json()

            unique_dicts = list(
                {d["title"]: d for d in data.get("srchList", [])}.values()
            )

            for srch in unique_dicts:
                tasks.append(
                    self.fetch_detail_async(
                        session,
                        srch["trprId"],
                    )
                )

            results = await asyncio.gather(*tasks)

            for lst in results:
                srchList.extend(lst)

            if data.get("scn_cnt", 0) > 100 and data.get("scn_cnt", 0) / pageNum > 100:
                pageNum += 1
            else:
                break
        return srchList

    # 3. 상세 정보 API 호출 (개별 교육과정)
    async def fetch_detail_async(self, session, trprId):
        url = (
            f"https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L03.do"
            f"?authKey={self.authKey}&returnType=XML&outType=2"
            f"&srchTrprId={trprId}"
        )
        async with session.get(url) as response:
            response_str = await response.text()
        root = ET.fromstring(response_str)

        tasks = []
        for scn_list in root.findall("scn_list"):
            tasks.append(
                self.day_extractor(
                    session,
                    trprId,
                    scn_list.find("instIno").text,
                    scn_list.find("trprDegr").text,
                )
            )

        results = await asyncio.gather(*tasks)

        details = []
        for scn_list, procedure_list in zip(root.findall("scn_list"), results):
            if scn_list.find("trprDegr").text == "0":
                continue
            details.append(
                {
                    "과정ID": procedure_list["과정ID"],
                    "과정명": procedure_list["과정명"],
                    "회차": scn_list.find("trprDegr").text,
                    "훈련일수": procedure_list["훈련일수"],
                    "훈련시작일": scn_list.find("trStaDt").text,
                    "훈련종료일": scn_list.find("trEndDt").text,
                }
            )
        return details

    # 4. 전체 데이터 수집 비동기 프로세스
    async def start_data_collection_async(self, update_status):
        update_status("api 통신 시작...")
        # requests여러번 생성되는거 방지하는 역할
        async with aiohttp.ClientSession() as session:
            tasks = []
            for srchTraArea in self.srchTraAreals:
                for srchNcs in self.srchNcsls:
                    tasks.append(
                        self.search_procedure_list_async(
                            session,
                            srchTraArea,
                            srchNcs,
                            self.crseTracseSelstr,
                        )
                    )
            results = await asyncio.gather(*tasks)
            srchList = []
            for lst in results:
                srchList.extend(lst)

            # 과정명, 회차로 정렬
            data_set = sorted(srchList, key=lambda x: (x["과정명"], int(x["회차"])))

            for procedure in data_set:
                for course in self.location_data:
                    if (
                        course["과정명"] == procedure["과정명"]
                        and course["훈련시작일"] == procedure["훈련시작일"]
                        and course["훈련종료일"] == procedure["훈련종료일"]
                    ):
                        # 조건이 일치하면 procedure 딕셔너리에 강의장 정보를 추가
                        procedure["강의장"] = course["강의장"]
                        procedure["강사"] = course["메인강사"]
                        break
                    else:
                        procedure["강의장"] = "해당 정보 없음"
                        procedure["강사"] = "해당 정보 없음"

            update_status(f"총 과정 수 {len(data_set)}개를 저장하고 있습니다...")

            # json 파일로 저장
            with open("persons.json", "w", encoding="utf-8") as f:
                json.dump(data_set, f, ensure_ascii=False, indent=4)


async def main():
    start_time = time.time()
    api = Use_API(
        dt.datetime.strptime("2021-01-01", "%Y-%m-%d").date(),
        dt.datetime.strptime("2025-02-11", "%Y-%m-%d").date(),
        ["11110"],
        ["200101", "200102", "200103"],
        ["None"],
    )
    await api.start_data_collection_async(print)
    end_time = time.time()
    print("코드 실행 시간: {:.6f}초".format(end_time - start_time))


if __name__ == "__main__":
    asyncio.run(main())


# 서울 전체 k-digital 240101 ~ 240131 28.970319초 27.577818초
# 서울 전체 k-digital 240101 ~ 241231 439.235440초

# 동기식 및 배치화까지 적용 시킨 후
# 서울 전체 k-digital 240101 ~ 240131 2.311578초
# 서울 전체 k-digital 240101 ~ 241231 18.442422초
