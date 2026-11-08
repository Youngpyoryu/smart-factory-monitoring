
import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==================================================
# 1. 웹 프로그램 기본 설정
# ==================================================

st.set_page_config(
    page_title="스마트공장 모니터링",
    page_icon="🏭",
    layout="wide"
)

# ==================================================
# 2. 프로그램 제목 및 설명
# ==================================================

st.title("스마트공장 생산 모니터링 시스템")

st.write("공장의 생산량과 설비 상태를 확인하는 프로그램입니다.")

st.info("현재 표시되는 데이터는 교육용 가상 제조데이터입니다.")


# ==================================================
# 3. CSV 파일 읽기
# ==================================================

file_name = "production_data.csv"

df = None

# CSV 파일이 있으면 자동으로 읽기
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


# ==================================================
# 4. CSV 데이터 확인 및 전처리
# ==================================================

if df is not None:

    # 필요한 컬럼 확인
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

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        st.error(f"CSV에 필요한 컬럼이 없습니다: {missing_columns}")
        st.stop()

    # 생산 시간을 날짜와 시간 형식으로 변환
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

    # 생산량 및 불량 수량 범위 확인
    if (
        (df["production_count"] < 0).any()
        or (df["defect_count"] < 0).any()
        or (df["defect_count"] > df["production_count"]).any()
    ):

        st.error("생산량 또는 불량 수량이 올바르지 않습니다.")
        st.stop()

    # 날짜 형식 오류 안내
    if df["timestamp"].isna().any():

        st.warning("일부 생산 시간이 날짜 형식으로 변환되지 않았습니다.")


# ==================================================
# 5. 사이드바 메뉴
# ==================================================

menu = st.sidebar.radio(
    "메뉴 선택",
    [
        "생산 현황",
        "품질 관리",
        "설비 모니터링",
        "데이터 관리"
    ]
)


# ==================================================
# 6. 생산 현황 메뉴 (기존 기능 유지)
# ==================================================

if menu == "생산 현황":

    st.header("생산 현황")

    st.write("공장의 주요 생산지표를 확인합니다.")

    if df is not None:

        # ------------------------------------------
        # 6-1. 설비번호 및 날짜 필터
        # ------------------------------------------

        st.subheader("생산 데이터 검색 조건")

        # 설비번호 목록 자동 생성
        machines = ["전체"] + sorted(
            df["machine_id"].dropna().astype(str).unique().tolist()
        )

        selected_machine = st.selectbox(
            "설비번호 선택",
            machines
        )

        # 날짜 데이터 확인
        valid_dates = df["timestamp"].dropna()

        if valid_dates.empty:

            st.error("검색할 수 있는 날짜 데이터가 없습니다.")
            st.stop()

        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        # 시작 날짜와 종료 날짜 선택
        col1, col2 = st.columns(2)

        with col1:

            start_date = st.date_input(
                "시작 날짜",
                value=min_date
            )

        with col2:

            end_date = st.date_input(
                "종료 날짜",
                value=max_date
            )

        # 날짜 범위 검사
        if start_date > end_date:

            st.error("시작 날짜가 종료 날짜보다 늦습니다.")
            st.stop()

        # ------------------------------------------
        # 6-2. 데이터 필터링
        # ------------------------------------------

        # 원본 CSV를 변경하지 않도록 복사
        filtered = df.copy()

        # 날짜 조건 적용
        filtered = filtered[
            (filtered["timestamp"].dt.date >= start_date)
            &
            (filtered["timestamp"].dt.date <= end_date)
        ].copy()

        # 설비번호 조건 적용
        if selected_machine != "전체":

            filtered = filtered[
                filtered["machine_id"].astype(str) == selected_machine
            ].copy()

        st.write(
            f"**선택한 조건의 생산 기록: {len(filtered):,}건**"
        )

        if filtered.empty:

            st.warning(
                "선택한 날짜와 설비에 해당하는 데이터가 없습니다."
            )

            st.stop()

        st.divider()

        # ------------------------------------------
        # 6-3. 주요 생산지표 계산
        # ------------------------------------------

        total = int(filtered["production_count"].sum())

        defect = int(filtered["defect_count"].sum())

        normal = total - defect

        # 생산량이 0이면 0으로 나누지 않음
        defect_rate = (
            defect / total * 100
            if total > 0
            else 0
        )

        avg_temperature = filtered["temperature"].mean()

        # ------------------------------------------
        # 6-4. 주요 생산지표 표시
        # ------------------------------------------

        st.subheader("주요 생산지표")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("총생산량", f"{total:,}개")

        with col2:
            st.metric("정상 제품", f"{normal:,}개")

        with col3:
            st.metric("불량 제품", f"{defect:,}개")

        with col4:
            st.metric("불량률", f"{defect_rate:.2f}%")

        st.divider()

        # 평균 공정 온도 표시
        if pd.notna(avg_temperature):

            st.metric(
                "평균 공정 온도",
                f"{avg_temperature:.2f}℃"
            )

        else:

            st.metric("평균 공정 온도", "데이터 없음")

        st.divider()

        # ------------------------------------------
        # 6-5. 생산 목표 달성률
        # ------------------------------------------

        st.subheader("생산 목표 달성률")

        st.write(
            "목표 생산량을 입력하면 현재 선택한 "
            "설비와 날짜의 생산량을 기준으로 계산합니다."
        )

        target = st.number_input(
            "목표 생산량 입력",
            min_value=1,
            value=10000,
            step=100,
            format="%d"
        )

        # 현재 필터의 생산량 사용
        actual = total

        achievement_rate = actual / target * 100

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("목표 생산량", f"{target:,}개")

        with col2:
            st.metric("실제 생산량", f"{actual:,}개")

        with col3:
            st.metric(
                "목표 달성률",
                f"{achievement_rate:.1f}%"
            )

        # 진행률은 최대 100%까지만 표시
        progress_rate = min(
            achievement_rate / 100,
            1.0
        )

        st.progress(progress_rate)

        if achievement_rate >= 100:

            st.success(
                f"생산 목표를 달성했습니다! "
                f"현재 달성률은 {achievement_rate:.1f}%입니다."
            )

        else:

            remaining = target - actual

            st.info(
                f"목표 달성까지 {remaining:,}개의 "
                "추가 생산이 필요합니다."
            )

        st.divider()

        # ------------------------------------------
        # 6-6. 설비별 생산량 TOP 10 그래프
        # ------------------------------------------

        st.subheader("설비별 생산량 분석")

        st.write(
            "선택한 조건에서 생산량이 많은 "
            "상위 10개 설비를 비교합니다."
        )

        machine_data = (
            filtered.groupby("machine_id")["production_count"]
            .sum()
            .reset_index()
        )

        # 생산량 내림차순 정렬
        machine_data = machine_data.sort_values(
            "production_count",
            ascending=False
        )

        top10 = machine_data.head(10).copy()

        if not top10.empty:

            fig = px.bar(
                top10,
                x="machine_id",
                y="production_count",
                title="설비별 생산량 TOP 10",
                text="production_count",
                labels={
                    "machine_id": "설비번호",
                    "production_count": "총생산량"
                }
            )

            # 생산량 순서 유지
            fig.update_xaxes(
                categoryorder="array",
                categoryarray=top10["machine_id"].tolist()
            )

            # 막대 위 생산량과 마우스 정보 표시
            fig.update_traces(
                texttemplate="%{y:,.0f}",
                textposition="outside",
                hovertemplate=(
                    "설비번호: %{x}<br>"
                    "총생산량: %{y:,.0f}개"
                    "<extra></extra>"
                )
            )

            fig.update_layout(
                xaxis_title="설비번호",
                yaxis_title="총생산량",
                height=500,
                margin=dict(
                    l=30,
                    r=30,
                    t=70,
                    b=30
                ),
                yaxis=dict(rangemode="tozero")
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            # 생산량 TOP 10 표 유지
            st.write("**설비별 생산량 TOP 10 데이터**")

            top10_table = top10.rename(
                columns={
                    "machine_id": "설비번호",
                    "production_count": "총생산량"
                }
            )

            st.dataframe(
                top10_table.reset_index(drop=True),
                use_container_width=True
            )

        else:

            st.warning("설비별 생산량 데이터가 없습니다.")

        st.divider()

        # ------------------------------------------
        # 6-7. CSV 데이터 정보
        # ------------------------------------------

        st.subheader("CSV 데이터 정보")

        total_rows = len(df)
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

        # 전체 데이터 기록 기간
        st.subheader("전체 데이터 기록 기간")

        valid_dates = df["timestamp"].dropna()

        if not valid_dates.empty:

            start_time = valid_dates.min()
            end_time = valid_dates.max()

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

        # 생산 기록 조회
        st.subheader("선택한 조건의 생산 기록")

        st.dataframe(
            filtered.head(10),
            use_container_width=True
        )

    else:

        st.warning(
            "CSV 파일을 업로드하면 생산지표가 표시됩니다."
        )


# ==================================================
# 7. 품질 관리 메뉴
# ==================================================

elif menu == "품질 관리":

    st.header("품질 관리")

    st.write("제품의 품질과 불량률을 확인하는 화면입니다.")

    if df is not None:

        # ------------------------------------------
        # 7-1. 전체 품질 현황
        # ------------------------------------------

        st.subheader("전체 품질 현황")

        # CSV 전체 데이터 기준
        quality_total = int(
            df["production_count"].sum()
        )

        quality_defect = int(
            df["defect_count"].sum()
        )

        # 전체 불량률 계산
        if quality_total > 0:

            quality_rate = (
                quality_defect / quality_total * 100
            )

            quality_rate_text = f"{quality_rate:.2f}%"

        else:

            quality_rate_text = "계산 불가"

        # 전체 품질지표 카드
        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "전체 생산량",
                f"{quality_total:,}개"
            )

        with col2:

            st.metric(
                "전체 불량 수량",
                f"{quality_defect:,}개"
            )

        with col3:

            st.metric(
                "전체 불량률",
                quality_rate_text
            )

        st.divider()

        # ------------------------------------------
        # 7-2. 설비별 데이터 그룹화
        # ------------------------------------------

        st.subheader("설비별 품질 분석")

        st.write(
            "설비별 총생산량과 불량 수량을 이용하여 "
            "설비별 불량률을 계산합니다."
        )

        # 설비별 생산량과 불량 수량 합계
        quality_data = (
            df.groupby("machine_id")[
                ["production_count", "defect_count"]
            ]
            .sum()
            .reset_index()
        )

        # ------------------------------------------
        # 7-3. 설비별 불량률 계산
        # ------------------------------------------

        # 생산량이 0이면 계산하지 않도록 NaN 처리
        quality_data["defect_rate"] = (
            quality_data["defect_count"]
            /
            quality_data["production_count"].replace(
                0, float("nan")
            )
            * 100
        )

        # ------------------------------------------
        # 7-4. 기존 설비별 품질 관리 표
        # ------------------------------------------

        # 원본 계산값을 유지하기 위해 복사
        quality_table = quality_data.copy()

        # 불량률을 소수점 둘째 자리까지 표시
        # 생산량이 0이면 '계산 불가' 표시
        quality_table["defect_rate"] = (
            quality_table["defect_rate"].apply(
                lambda x: f"{x:.2f}%"
                if pd.notna(x)
                else "계산 불가"
            )
        )

        # 컬럼 이름을 한글로 변경
        quality_table = quality_table.rename(
            columns={
                "machine_id": "설비번호",
                "production_count": "총생산량",
                "defect_count": "불량 수량",
                "defect_rate": "불량률"
            }
        )

        # 생산량과 불량 수량을 정수로 변환
        quality_table["총생산량"] = (
            quality_table["총생산량"].astype(int)
        )

        quality_table["불량 수량"] = (
            quality_table["불량 수량"].astype(int)
        )

        # 기존 품질 관리 표 출력
        st.dataframe(
            quality_table,
            use_container_width=True,
            hide_index=True
        )

        # 분석된 전체 설비 개수
        st.write(
            f"**분석된 전체 설비 수: {len(quality_table):,}개**"
        )

        st.divider()

        # ==========================================
        # 7-5. 설비별 불량률 TOP 10 그래프 (추가)
        # ==========================================

        st.subheader("설비별 불량률 TOP 10")

        st.write(
            "불량률이 높은 상위 10개 설비를 비교합니다."
        )

        # ------------------------------------------
        # ① 생산량이 0인 설비 제외
        # ------------------------------------------

        # quality_data에는 숫자 형태의 불량률이 있음
        quality_graph = quality_data[
            quality_data["production_count"] > 0
        ].copy()

        # ------------------------------------------
        # ② 불량률이 높은 순서로 정렬
        # ------------------------------------------

        quality_graph = quality_graph.sort_values(
            "defect_rate",
            ascending=False
        )

        # ------------------------------------------
        # ③ 상위 10개 설비 선택
        # ------------------------------------------

        quality_top10 = quality_graph.head(10).copy()

        # ------------------------------------------
        # ④ Plotly 막대그래프 생성
        # ------------------------------------------

        if not quality_top10.empty:

            fig_quality = px.bar(
                quality_top10,
                x="machine_id",
                y="defect_rate",
                title="설비별 불량률 TOP 10",
                text="defect_rate",
                labels={
                    "machine_id": "설비번호",
                    "defect_rate": "불량률(%)"
                }
            )

            # --------------------------------------
            # ⑤ 불량률 내림차순 유지
            # --------------------------------------

            fig_quality.update_xaxes(
                categoryorder="array",
                categoryarray=quality_top10[
                    "machine_id"
                ].tolist()
            )

            # --------------------------------------
            # ⑥ 막대 위에 불량률 표시
            # --------------------------------------

            fig_quality.update_traces(
                texttemplate="%{y:.2f}%",
                textposition="outside",
                hovertemplate=(
                    "설비번호: %{x}<br>"
                    "불량률: %{y:.2f}%"
                    "<extra></extra>"
                )
            )

            # --------------------------------------
            # ⑦ 그래프 디자인
            # --------------------------------------

            fig_quality.update_layout(
                xaxis_title="설비번호",
                yaxis_title="불량률(%)",
                height=500,
                margin=dict(
                    l=30,
                    r=30,
                    t=70,
                    b=30
                ),
                yaxis=dict(
                    rangemode="tozero",
                    ticksuffix="%"
                )
            )

            # --------------------------------------
            # ⑧ Streamlit에 그래프 출력
            # --------------------------------------

            st.plotly_chart(
                fig_quality,
                use_container_width=True
            )

        else:

            st.warning(
                "불량률을 계산할 수 있는 설비가 없습니다."
            )

    else:

        st.warning(
            "CSV 파일을 업로드하면 품질 분석 결과가 표시됩니다."
        )


# ==================================================
# 8. 설비 모니터링 메뉴 (기존 기능 유지)
# ==================================================

elif menu == "설비 모니터링":

    st.header("설비 모니터링")

    st.write("설비별 온도와 습도를 확인하는 화면입니다.")

    st.info(
        "추후 설비 선택과 온도 경고 기능을 추가합니다."
    )


# ==================================================
# 9. 데이터 관리 메뉴 (기존 기능 유지)
# ==================================================

elif menu == "데이터 관리":

    st.header("데이터 관리")

    st.write("생산 데이터를 조회하고 관리하는 화면입니다.")

    st.info(
        "추후 데이터 검색과 입력 기능을 추가합니다."
    )
