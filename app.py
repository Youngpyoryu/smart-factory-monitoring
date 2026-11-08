
import streamlit as st
import pandas as pd
import os

# --------------------------------------------------
# 1. 웹 프로그램 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="스마트공장 모니터링",
    page_icon="🏭",
    layout="wide"
)

# --------------------------------------------------
# 2. 프로그램 제목 및 설명
# --------------------------------------------------

st.title("스마트공장 생산 모니터링 시스템")

st.write("공장의 생산량과 설비 상태를 확인하는 프로그램입니다.")

st.info("현재 표시되는 데이터는 교육용 가상 제조데이터입니다.")

# --------------------------------------------------
# 3. CSV 파일 읽기
# --------------------------------------------------

file_name = "production_data.csv"

# 데이터를 저장할 변수
df = None

# CSV 파일이 존재하면 자동으로 읽기
if os.path.exists(file_name):

    df = pd.read_csv(file_name)

else:

    # CSV 파일이 없으면 업로드 기능 제공
    st.warning("CSV 파일이 없습니다. 파일을 업로드해주세요.")

    uploaded_file = st.file_uploader(
        "생산 데이터 CSV 파일 업로드",
        type=["csv"]
    )

    if uploaded_file is not None:

        df = pd.read_csv(uploaded_file)

# --------------------------------------------------
# 4. CSV 데이터 확인 및 전처리
# --------------------------------------------------

if df is not None:

    # 필요한 컬럼 목록
    required_columns = [
        "timestamp",
        "machine_id",
        "product_id",
        "production_count",
        "defect_count",
        "temperature",
        "humidity",
        "operating_status"
    ]

    # 누락된 컬럼 확인
    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        st.error(
            f"CSV에 필요한 컬럼이 없습니다: {missing_columns}"
        )

        st.stop()

    # 생산 시간을 날짜·시간 형식으로 변환
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # 숫자 컬럼 변환
    number_columns = [
        "production_count",
        "defect_count",
        "temperature"
    ]

    for col in number_columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # 생산량과 불량 수량에 잘못된 값이 있는지 확인
    if df[["production_count", "defect_count"]].isna().any().any():

        st.error("생산량 또는 불량 수량에 잘못된 값이 있습니다.")

        st.stop()

    # 잘못된 수량 확인
    if (
        (df["production_count"] < 0).any()
        or (df["defect_count"] < 0).any()
        or (df["defect_count"] > df["production_count"]).any()
    ):

        st.error("생산량 또는 불량 수량이 올바르지 않습니다.")

        st.stop()

    # 날짜 변환 오류 안내
    if df["timestamp"].isna().any():

        st.warning("일부 생산 시간이 날짜 형식으로 변환되지 않았습니다.")

# --------------------------------------------------
# 5. 사이드바 메뉴
# --------------------------------------------------

menu = st.sidebar.radio(
    "메뉴 선택",
    [
        "생산 현황",
        "품질 관리",
        "설비 모니터링",
        "데이터 관리"
    ]
)

# --------------------------------------------------
# 6. 생산 현황 메뉴
# --------------------------------------------------

if menu == "생산 현황":

    st.header("생산 현황")

    st.write("공장의 주요 생산지표를 확인합니다.")

    # CSV 데이터가 있는 경우
    if df is not None:

        # ------------------------------------------
        # 6-1. 주요 생산지표 계산
        # ------------------------------------------

        # 전체 생산량
        total = int(df["production_count"].sum())

        # 불량 제품 수
        defect = int(df["defect_count"].sum())

        # 정상 제품 수
        normal = total - defect

        # 전체 불량률
        # 생산량이 0이면 0으로 나누지 않도록 처리
        defect_rate = (
            defect / total * 100
            if total > 0
            else 0
        )

        # 평균 공정 온도
        avg_temperature = df["temperature"].mean()

        # ------------------------------------------
        # 6-2. 주요 생산지표 카드
        # ------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "총생산량",
                f"{total:,}개"
            )

        with col2:

            st.metric(
                "정상 제품",
                f"{normal:,}개"
            )

        with col3:

            st.metric(
                "불량 제품",
                f"{defect:,}개"
            )

        with col4:

            st.metric(
                "불량률",
                f"{defect_rate:.2f}%"
            )

        st.divider()

        # ------------------------------------------
        # 6-3. 평균 공정 온도
        # ------------------------------------------

        if pd.notna(avg_temperature):

            st.metric(
                "평균 공정 온도",
                f"{avg_temperature:.2f}℃"
            )

        else:

            st.metric(
                "평균 공정 온도",
                "데이터 없음"
            )

        st.success("CSV 데이터를 이용하여 생산지표를 자동 계산했습니다.")

        st.divider()

        # ------------------------------------------
        # 6-4. CSV 데이터 정보
        # ------------------------------------------

        st.subheader("CSV 데이터 정보")

        # 전체 데이터 개수
        total_rows = len(df)

        # 전체 컬럼 개수
        total_columns = len(df.columns)

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "전체 데이터 개수",
                f"{total_rows:,}건"
            )

        with col2:

            st.metric(
                "전체 컬럼 개수",
                f"{total_columns}개"
            )

        # ------------------------------------------
        # 6-5. 데이터 기록 기간
        # ------------------------------------------

        st.subheader("데이터 기록 기간")

        if df["timestamp"].notna().any():

            start_time = df["timestamp"].min()
            end_time = df["timestamp"].max()

            col1, col2 = st.columns(2)

            with col1:

                st.write("**데이터 시작 시간**")

                st.write(
                    start_time.strftime("%Y-%m-%d %H:%M")
                )

            with col2:

                st.write("**데이터 종료 시간**")

                st.write(
                    end_time.strftime("%Y-%m-%d %H:%M")
                )

        else:

            st.warning("유효한 생산 시간 데이터가 없습니다.")

        st.divider()

        # ------------------------------------------
        # 6-6. 처음 10개 데이터 표시
        # ------------------------------------------

        st.subheader("처음 10개 생산 기록")

        st.dataframe(
            df.head(10),
            use_container_width=True
        )

    else:

        st.warning("CSV 파일을 업로드하면 생산지표가 표시됩니다.")

# --------------------------------------------------
# 7. 품질 관리 메뉴
# --------------------------------------------------

elif menu == "품질 관리":

    st.header("품질 관리")

    st.write("제품의 품질과 불량률을 확인하는 화면입니다.")

    st.info("추후 설비별 불량률과 품질 경고 기능을 추가합니다.")

# --------------------------------------------------
# 8. 설비 모니터링 메뉴
# --------------------------------------------------

elif menu == "설비 모니터링":

    st.header("설비 모니터링")

    st.write("설비별 온도와 습도를 확인하는 화면입니다.")

    st.info("추후 설비 선택과 온도 경고 기능을 추가합니다.")

# --------------------------------------------------
# 9. 데이터 관리 메뉴
# --------------------------------------------------

elif menu == "데이터 관리":

    st.header("데이터 관리")

    st.write("생산 데이터를 조회하고 관리하는 화면입니다.")

    st.info("추후 데이터 검색과 입력 기능을 추가합니다.")
