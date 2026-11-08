
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

st.info("현재 표시되는 생산지표는 교육용 가상 데이터입니다.")

# --------------------------------------------------
# 3. CSV 파일 읽기
# --------------------------------------------------

# CSV 파일 이름
file_name = "production_data.csv"

# 데이터를 저장할 변수
df = None

# CSV 파일이 존재하는지 확인
if os.path.exists(file_name):

    # CSV 파일 읽기
    df = pd.read_csv(file_name)

else:

    # CSV 파일이 없으면 업로드 기능 제공
    st.warning("CSV 파일이 없습니다. 파일을 업로드해주세요.")

    uploaded_file = st.file_uploader(
        "생산 데이터 CSV 파일 업로드",
        type=["csv"]
    )

    # 사용자가 파일을 업로드한 경우
    if uploaded_file is not None:

        df = pd.read_csv(uploaded_file)

# --------------------------------------------------
# 4. CSV 데이터 확인 및 날짜 변환
# --------------------------------------------------

# CSV 데이터를 읽은 경우
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

    # CSV에 없는 컬럼 확인
    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    # 필요한 컬럼이 없으면 안내
    if missing_columns:

        st.error(
            f"CSV에 필요한 컬럼이 없습니다: {missing_columns}"
        )

        st.stop()

    # timestamp를 날짜와 시간 형식으로 변환
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # 날짜 변환에 실패한 데이터가 있는지 확인
    if df["timestamp"].isna().any():

        st.warning(
            "일부 생산 시간이 날짜 형식으로 변환되지 않았습니다."
        )

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

    # ----------------------------------------------
    # 기존 주요 생산지표 카드
    # ----------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총생산량", "1,000개")

    with col2:
        st.metric("정상 제품", "950개")

    with col3:
        st.metric("불량 제품", "50개")

    with col4:
        st.metric("불량률", "5.0%")

    st.divider()

    # 평균 공정 온도
    st.metric("평균 공정 온도", "38℃")

    st.write("다음 수업에서 CSV 데이터를 이용해 생산지표를 자동 계산합니다.")

    st.divider()

    # ----------------------------------------------
    # CSV 데이터 정보
    # ----------------------------------------------

    st.subheader("CSV 데이터 정보")

    # CSV 파일을 읽은 경우
    if df is not None:

        # 전체 데이터 개수
        total_rows = len(df)

        # 전체 컬럼 개수
        total_columns = len(df.columns)

        # 데이터 개수와 컬럼 개수 표시
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
        # 데이터 시작 시간과 종료 시간
        # ------------------------------------------

        st.subheader("데이터 기록 기간")

        # 유효한 날짜 데이터가 있는 경우
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

            st.warning(
                "유효한 생산 시간 데이터가 없습니다."
            )

        st.divider()

        # ------------------------------------------
        # 처음 10개 데이터 표시
        # ------------------------------------------

        st.subheader("처음 10개 생산 기록")

        st.dataframe(
            df.head(10),
            use_container_width=True
        )

        # CSV 연결 성공 안내
        st.success("CSV 파일을 정상적으로 읽었습니다.")

    else:

        st.warning("CSV 파일을 업로드하면 데이터 정보가 표시됩니다.")

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
