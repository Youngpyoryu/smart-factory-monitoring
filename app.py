
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

st.title("스마트공장 생산 모니터링 시스템")

st.write(
    "공장의 생산량과 설비 상태를 확인하는 프로그램입니다."
)

st.info(
    "현재 표시되는 데이터는 교육용 가상 제조데이터입니다."
)


# ==================================================
# 2. CSV 파일 읽기
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
# 3. CSV 데이터 확인 및 전처리
# ==================================================

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

    # 필요한 컬럼이 있는지 확인
    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:

        st.error(
            f"CSV에 필요한 컬럼이 없습니다: {missing_columns}"
        )

        st.stop()

    # 날짜와 시간 형식으로 변환
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # 숫자 형식으로 변환
    number_columns = [
        "production_count",
        "defect_count",
        "temperature",
        "humidity"
    ]

    for col in number_columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # 생산량과 불량 수량에 잘못된 값이 있는지 확인
    if df[["production_count", "defect_count"]].isna().any().any():

        st.error(
            "생산량 또는 불량 수량에 잘못된 값이 있습니다."
        )

        st.stop()

    # 생산량과 불량 수량의 범위 확인
    if (
        (df["production_count"] < 0).any()
        or (df["defect_count"] < 0).any()
        or (df["defect_count"] > df["production_count"]).any()
    ):

        st.error(
            "생산량 또는 불량 수량이 올바르지 않습니다."
        )

        st.stop()

    # 날짜 변환 오류 안내
    if df["timestamp"].isna().any():

        st.warning(
            "일부 생산 시간이 날짜 형식으로 변환되지 않았습니다."
        )


# ==================================================
# 4. 사이드바 메뉴
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
# 5. 생산 현황 메뉴 (기존 기능 유지)
# ==================================================

if menu == "생산 현황":

    st.header("생산 현황")

    st.write(
        "공장의 주요 생산지표를 확인합니다."
    )

    if df is not None:

        # ------------------------------------------
        # 5-1. 설비번호 및 날짜 필터
        # ------------------------------------------

        st.subheader("생산 데이터 검색 조건")

        # CSV에서 설비번호 목록 자동 생성
        machines = ["전체"] + sorted(
            df["machine_id"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        # 설비 선택
        selected_machine = st.selectbox(
            "설비번호 선택",
            machines
        )

        # 날짜 데이터 확인
        valid_dates = df["timestamp"].dropna()

        if valid_dates.empty:

            st.error(
                "검색할 수 있는 날짜 데이터가 없습니다."
            )

            st.stop()

        # 전체 데이터의 시작 날짜와 종료 날짜
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        # 날짜 선택
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

        # 날짜 범위 확인
        if start_date > end_date:

            st.error(
                "시작 날짜가 종료 날짜보다 늦습니다."
            )

            st.stop()

        # ------------------------------------------
        # 5-2. 데이터 필터링
        # ------------------------------------------

        # 원본 데이터 변경 방지
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
                filtered["machine_id"].astype(str)
                == selected_machine
            ].copy()

        # 선택한 기록 개수 표시
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
        # 5-3. 주요 생산지표 계산
        # ------------------------------------------

        # 전체 생산량
        total = int(
            filtered["production_count"].sum()
        )

        # 불량 제품 수
        defect = int(
            filtered["defect_count"].sum()
        )

        # 정상 제품 수
        normal = total - defect

        # 전체 불량률
        defect_rate = (
            defect / total * 100
            if total > 0
            else 0
        )

        # 평균 공정 온도
        avg_temperature = (
            filtered["temperature"].mean()
        )

        # ------------------------------------------
        # 5-4. 주요 생산지표 표시
        # ------------------------------------------

        st.subheader("주요 생산지표")

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

        # 평균 공정 온도
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

        st.divider()

        # ------------------------------------------
        # 5-5. 생산 목표 달성률
        # ------------------------------------------

        st.subheader("생산 목표 달성률")

        st.write(
            "목표 생산량을 입력하면 현재 선택한 "
            "설비와 날짜의 생산량을 기준으로 계산합니다."
        )

        # 목표 생산량 입력
        target = st.number_input(
            "목표 생산량 입력",
            min_value=1,
            value=10000,
            step=100,
            format="%d"
        )

        # 실제 생산량
        actual = total

        # 목표 달성률 계산
        achievement_rate = actual / target * 100

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "목표 생산량",
                f"{target:,}개"
            )

        with col2:

            st.metric(
                "실제 생산량",
                f"{actual:,}개"
            )

        with col3:

            st.metric(
                "목표 달성률",
                f"{achievement_rate:.1f}%"
            )

        # 진행률 막대는 최대 100%
        progress_rate = min(
            achievement_rate / 100,
            1.0
        )

        st.progress(progress_rate)

        # 목표 달성 여부 표시
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
        # 5-6. 설비별 생산량 TOP 10 그래프
        # ------------------------------------------

        st.subheader("설비별 생산량 분석")

        st.write(
            "선택한 조건에서 생산량이 많은 "
            "상위 10개 설비를 비교합니다."
        )

        # 설비별 생산량 합계
        machine_data = (
            filtered.groupby("machine_id")[
                "production_count"
            ]
            .sum()
            .reset_index()
        )

        # 생산량 내림차순 정렬
        machine_data = machine_data.sort_values(
            "production_count",
            ascending=False
        )

        # 상위 10개
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

            # 막대 위 숫자 표시
            fig.update_traces(
                texttemplate="%{y:,.0f}",
                textposition="outside",
                hovertemplate=(
                    "설비번호: %{x}<br>"
                    "총생산량: %{y:,.0f}개"
                    "<extra></extra>"
                )
            )

            # 그래프 디자인
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
                yaxis=dict(
                    rangemode="tozero"
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            # 설비별 생산량 TOP 10 데이터 표
            st.write(
                "**설비별 생산량 TOP 10 데이터**"
            )

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

            st.warning(
                "설비별 생산량 데이터가 없습니다."
            )

        st.divider()

        # ------------------------------------------
        # 5-7. CSV 데이터 정보
        # ------------------------------------------

        st.subheader("CSV 데이터 정보")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "전체 데이터 개수",
                f"{len(df):,}건"
            )

        with col2:

            st.metric(
                "전체 컬럼 개수",
                f"{len(df.columns)}개"
            )

        # ------------------------------------------
        # 5-8. 전체 데이터 기록 기간
        # ------------------------------------------

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

            st.warning(
                "유효한 생산 시간 데이터가 없습니다."
            )

        st.divider()

        # ------------------------------------------
        # 5-9. 생산 기록 조회
        # ------------------------------------------

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
# 6. 품질 관리 메뉴 (기존 기능 유지)
# ==================================================

elif menu == "품질 관리":

    st.header("품질 관리")

    st.write(
        "제품의 품질과 불량률을 확인하는 화면입니다."
    )

    if df is not None:

        # ------------------------------------------
        # 6-1. 전체 품질 현황
        # ------------------------------------------

        st.subheader("전체 품질 현황")

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
        # 6-2. 설비별 품질 분석
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

        # 설비별 불량률 계산
        quality_data["defect_rate"] = (
            quality_data["defect_count"]
            /
            quality_data["production_count"].replace(
                0, float("nan")
            )
            * 100
        )

        # ------------------------------------------
        # 6-3. 품질 경고 기준 설정
        # ------------------------------------------

        st.subheader("품질 경고 기준 설정")

        st.write(
            "허용 불량률을 설정하면 설비별 "
            "품질 상태를 자동으로 판정합니다."
        )

        # 허용 불량률 슬라이더
        allowed_rate = st.slider(
            "허용 불량률 (%)",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=0.1
        )

        st.write(
            f"**현재 허용 불량률: {allowed_rate:.1f}%**"
        )

        # 기본 상태
        quality_data["quality_status"] = "계산 불가"

        # 정상 조건
        normal_condition = (
            (quality_data["production_count"] > 0)
            &
            (quality_data["defect_rate"] <= allowed_rate)
        )

        quality_data.loc[
            normal_condition,
            "quality_status"
        ] = "정상"

        # 경고 조건
        warning_condition = (
            (quality_data["production_count"] > 0)
            &
            (quality_data["defect_rate"] > allowed_rate)
        )

        quality_data.loc[
            warning_condition,
            "quality_status"
        ] = "경고"

        # 상태별 설비 개수
        normal_count = int(
            (quality_data["quality_status"] == "정상").sum()
        )

        warning_count = int(
            (quality_data["quality_status"] == "경고").sum()
        )

        unknown_count = int(
            (quality_data["quality_status"] == "계산 불가").sum()
        )

        # 품질 상태 표시
        st.subheader("품질 상태 현황")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "정상 설비",
                f"{normal_count:,}개"
            )

        with col2:

            st.metric(
                "경고 설비",
                f"{warning_count:,}개"
            )

        with col3:

            st.metric(
                "계산 불가 설비",
                f"{unknown_count:,}개"
            )

        # 경고 메시지
        if warning_count > 0:

            st.error(
                f"품질 경고: 허용 불량률 {allowed_rate:.1f}%를 "
                f"초과한 설비가 {warning_count:,}개 있습니다."
            )

        else:

            st.success(
                "정상: 허용 불량률을 초과한 설비가 없습니다."
            )

        st.divider()

        # ------------------------------------------
        # 6-4. 설비별 품질 분석 표
        # ------------------------------------------

        st.subheader("설비별 품질 분석 결과")

        quality_table = quality_data.copy()

        # 불량률 표시 형식
        quality_table["defect_rate"] = (
            quality_table["defect_rate"].apply(
                lambda x: f"{x:.2f}%"
                if pd.notna(x)
                else "계산 불가"
            )
        )

        # 컬럼 이름 변경
        quality_table = quality_table.rename(
            columns={
                "machine_id": "설비번호",
                "production_count": "총생산량",
                "defect_count": "불량 수량",
                "defect_rate": "불량률",
                "quality_status": "품질 상태"
            }
        )

        # 정수 변환
        quality_table["총생산량"] = (
            quality_table["총생산량"].astype(int)
        )

        quality_table["불량 수량"] = (
            quality_table["불량 수량"].astype(int)
        )

        # 정상은 초록색, 경고는 빨간색
        styled_table = quality_table.style.map(
            lambda value:
                "color: green; font-weight: bold"
                if value == "정상"
                else (
                    "color: red; font-weight: bold"
                    if value == "경고"
                    else "color: gray"
                ),
            subset=["품질 상태"]
        )

        st.dataframe(
            styled_table,
            use_container_width=True,
            hide_index=True
        )

        st.write(
            f"**분석된 전체 설비 수: {len(quality_table):,}개**"
        )

        st.divider()

        # ------------------------------------------
        # 6-5. 설비별 불량률 TOP 10 그래프
        # ------------------------------------------

        st.subheader("설비별 불량률 TOP 10")

        st.write(
            "불량률이 높은 상위 10개 설비를 비교합니다."
        )

        # 생산량이 0인 설비 제외
        quality_graph = quality_data[
            quality_data["production_count"] > 0
        ].copy()

        # 불량률 높은 순서로 정렬
        quality_graph = quality_graph.sort_values(
            "defect_rate",
            ascending=False
        )

        quality_top10 = quality_graph.head(10).copy()

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

            fig_quality.update_xaxes(
                categoryorder="array",
                categoryarray=quality_top10[
                    "machine_id"
                ].tolist()
            )

            fig_quality.update_traces(
                texttemplate="%{y:.2f}%",
                textposition="outside",
                hovertemplate=(
                    "설비번호: %{x}<br>"
                    "불량률: %{y:.2f}%"
                    "<extra></extra>"
                )
            )

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

            st.plotly_chart(
                fig_quality,
                use_container_width=True
            )

        else:

            st.warning(
                "불량률을 계산할 수 있는 설비가 없습니다."
            )

        st.divider()

        # ------------------------------------------
        # 6-6. 날짜별 불량률 변화 그래프
        # ------------------------------------------

        st.subheader("날짜별 불량률 변화")

        st.write(
            "날짜별 생산량과 불량 수량을 이용하여 "
            "불량률의 변화를 확인합니다."
        )

        # 원본 데이터 복사
        daily_df = df.copy()

        # 날짜 추출
        daily_df["date"] = daily_df["timestamp"].dt.date

        # 날짜가 없는 기록 제외
        daily_df = daily_df.dropna(
            subset=["date"]
        )

        # 날짜별 합계
        daily_data = (
            daily_df.groupby("date")[
                ["production_count", "defect_count"]
            ]
            .sum()
            .reset_index()
        )

        # 날짜별 불량률
        daily_data["defect_rate"] = (
            daily_data["defect_count"]
            /
            daily_data["production_count"].replace(
                0, float("nan")
            )
            * 100
        )

        # 날짜순 정렬
        daily_data = daily_data.sort_values(
            "date",
            ascending=True
        )

        # 날짜 형식 변환
        daily_data["date"] = pd.to_datetime(
            daily_data["date"]
        )

        if not daily_data.empty:

            fig_daily = px.line(
                daily_data,
                x="date",
                y="defect_rate",
                title="날짜별 불량률 변화",
                markers=True,
                labels={
                    "date": "날짜",
                    "defect_rate": "불량률(%)"
                }
            )

            fig_daily.update_traces(
                hovertemplate=(
                    "날짜: %{x|%Y-%m-%d}<br>"
                    "불량률: %{y:.2f}%"
                    "<extra></extra>"
                )
            )

            fig_daily.update_layout(
                xaxis_title="날짜",
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

            fig_daily.update_xaxes(
                tickformat="%Y-%m-%d"
            )

            st.plotly_chart(
                fig_daily,
                use_container_width=True
            )

            # 생산량이 0인 날짜 안내
            if (daily_data["production_count"] == 0).any():

                st.info(
                    "생산량이 0인 날짜는 불량률을 "
                    "계산할 수 없어 점이 표시되지 않습니다."
                )

        else:

            st.warning(
                "날짜별 불량률을 분석할 데이터가 없습니다."
            )

        st.divider()

        # ------------------------------------------
        # 6-7. 품질 순위 최소 생산량 설정
        # ------------------------------------------

        st.subheader("설비별 품질 순위")

        st.write(
            "일정 생산량 이상을 기록한 설비를 대상으로 "
            "불량률이 낮은 순서대로 순위를 계산합니다."
        )

        min_production = st.number_input(
            "품질 순위 최소 생산량",
            min_value=1,
            value=1000,
            step=100,
            format="%d"
        )

        st.write(
            f"**현재 최소 생산량 기준: {min_production:,}개**"
        )

        # 기준 이상인 설비만 선택
        ranking_data = quality_data[
            quality_data["production_count"] >= min_production
        ].copy()

        # 불량률 오름차순
        ranking_data = ranking_data.sort_values(
            ["defect_rate", "machine_id"],
            ascending=[True, True]
        ).reset_index(drop=True)

        # 순위 번호 추가
        ranking_data.insert(
            0,
            "rank",
            range(1, len(ranking_data) + 1)
        )

        st.metric(
            "최소 생산량 기준 만족 설비 수",
            f"{len(ranking_data):,}개"
        )

        # 순위표 데이터 정리
        ranking_table = ranking_data.copy()

        ranking_table["defect_rate"] = (
            ranking_table["defect_rate"].apply(
                lambda x: f"{x:.2f}%"
            )
        )

        ranking_table = ranking_table.rename(
            columns={
                "rank": "순위",
                "machine_id": "설비번호",
                "production_count": "총생산량",
                "defect_count": "불량 수량",
                "defect_rate": "불량률",
                "quality_status": "품질 상태"
            }
        )

        # 컬럼 순서
        ranking_table = ranking_table[
            [
                "순위",
                "설비번호",
                "총생산량",
                "불량 수량",
                "불량률",
                "품질 상태"
            ]
        ]

        # 정수 변환
        ranking_table["총생산량"] = (
            ranking_table["총생산량"].astype(int)
        )

        ranking_table["불량 수량"] = (
            ranking_table["불량 수량"].astype(int)
        )

        # ------------------------------------------
        # 6-8. 전체 설비 품질 순위표
        # ------------------------------------------

        st.subheader("전체 설비 품질 순위표")

        if not ranking_table.empty:

            styled_ranking = ranking_table.style.map(
                lambda value:
                    "color: green; font-weight: bold"
                    if value == "정상"
                    else (
                        "color: red; font-weight: bold"
                        if value == "경고"
                        else "color: gray"
                    ),
                subset=["품질 상태"]
            )

            st.dataframe(
                styled_ranking,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.warning(
                "최소 생산량 기준을 만족하는 설비가 없습니다."
            )

        st.divider()

        # ------------------------------------------
        # 6-9. 품질 우수 설비 TOP 10
        # ------------------------------------------

        st.subheader("품질 우수 설비 TOP 10")

        st.write(
            "최소 생산량 기준을 만족하는 설비 중 "
            "불량률이 가장 낮은 10개 설비입니다."
        )

        ranking_top10 = ranking_table.head(10).copy()

        if not ranking_top10.empty:

            styled_top10 = ranking_top10.style.map(
                lambda value:
                    "color: green; font-weight: bold"
                    if value == "정상"
                    else (
                        "color: red; font-weight: bold"
                        if value == "경고"
                        else "color: gray"
                    ),
                subset=["품질 상태"]
            )

            st.dataframe(
                styled_top10,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "표시할 품질 우수 설비가 없습니다."
            )

        st.divider()

        # ------------------------------------------
        # 6-10. 품질 순위 제외 설비
        # ------------------------------------------

        st.subheader("품질 순위 제외 설비")

        # 생산량이 0인 설비
        st.write("**생산량이 0인 설비**")

        zero_data = quality_data[
            quality_data["production_count"] == 0
        ].copy()

        if not zero_data.empty:

            zero_table = zero_data[
                [
                    "machine_id",
                    "production_count",
                    "defect_count"
                ]
            ].copy()

            zero_table = zero_table.rename(
                columns={
                    "machine_id": "설비번호",
                    "production_count": "총생산량",
                    "defect_count": "불량 수량"
                }
            )

            zero_table["불량률"] = "계산 불가"
            zero_table["품질 상태"] = "계산 불가"

            st.warning(
                f"생산량이 0인 설비: {len(zero_table):,}개"
            )

            st.dataframe(
                zero_table,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success(
                "생산량이 0인 설비가 없습니다."
            )

        # 최소 생산량 기준에 미달하는 설비
        st.write("**최소 생산량 기준 미달 설비**")

        low_production_data = quality_data[
            (quality_data["production_count"] > 0)
            &
            (quality_data["production_count"] < min_production)
        ].copy()

        if not low_production_data.empty:

            low_table = low_production_data[
                [
                    "machine_id",
                    "production_count",
                    "defect_count",
                    "defect_rate",
                    "quality_status"
                ]
            ].copy()

            low_table["defect_rate"] = (
                low_table["defect_rate"].apply(
                    lambda x: f"{x:.2f}%"
                )
            )

            low_table = low_table.rename(
                columns={
                    "machine_id": "설비번호",
                    "production_count": "총생산량",
                    "defect_count": "불량 수량",
                    "defect_rate": "불량률",
                    "quality_status": "품질 상태"
                }
            )

            st.warning(
                f"최소 생산량 기준 미달 설비: "
                f"{len(low_table):,}개"
            )

            st.dataframe(
                low_table,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success(
                "최소 생산량 기준에 미달하는 설비가 없습니다."
            )

    else:

        st.warning(
            "CSV 파일을 업로드하면 품질 분석 결과가 표시됩니다."
        )


# ==================================================
# 7. 설비 모니터링 메뉴
# ==================================================

elif menu == "설비 모니터링":

    st.header("설비 모니터링")

    st.write(
        "설비별 최신 공정 온도, 습도 및 "
        "가동 상태를 확인합니다."
    )

    if df is not None:

        # ------------------------------------------
        # 7-1. 설비번호 목록 자동 생성
        # ------------------------------------------

        st.subheader("설비 선택")

        # machine_id에서 설비번호 목록 가져오기
        machine_list = sorted(
            df["machine_id"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        # 설비가 없는 경우
        if len(machine_list) == 0:

            st.warning("조회할 설비가 없습니다.")

            st.stop()

        # ------------------------------------------
        # 7-2. 설비번호 선택
        # ------------------------------------------

        selected_machine_monitor = st.selectbox(
            "조회할 설비번호",
            machine_list
        )

        # ------------------------------------------
        # 7-3. 선택한 설비의 데이터 가져오기
        # ------------------------------------------

        # 선택한 설비의 기록만 가져오기
        machine_df = df[
            df["machine_id"].astype(str)
            == selected_machine_monitor
        ].copy()

        # timestamp가 없는 기록 제외
        machine_df = machine_df.dropna(
            subset=["timestamp"]
        )

        # ------------------------------------------
        # 7-4. 시간순 정렬
        # ------------------------------------------

        # 시간 기준 오름차순 정렬
        # 과거 기록부터 최근 기록 순서로 배치
        machine_df = machine_df.sort_values(
            "timestamp",
            ascending=True
        )

        # 유효한 기록이 없는 경우
        if machine_df.empty:

            st.warning(
                "선택한 설비에 유효한 생산 시간 기록이 없습니다."
            )

        else:

            # ======================================
            # 7-5. 선택한 설비의 최신 기록
            # ======================================

            # 시간순으로 정렬되어 있으므로
            # 마지막 행이 가장 최근 기록
            latest = machine_df.iloc[-1]

            # 최근 설비 정보 가져오기
            latest_machine = latest["machine_id"]

            latest_temperature = latest["temperature"]

            latest_humidity = latest["humidity"]

            latest_time = latest["timestamp"]

            latest_status = latest["operating_status"]

            st.divider()

            # --------------------------------------
            # 7-6. 설비 최신 상태 표시
            # --------------------------------------

            st.subheader("설비 최신 상태")

            st.write(
                f"**선택한 설비번호: {latest_machine}**"
            )

            # 온도와 습도를 가로로 배치
            col1, col2 = st.columns(2)

            with col1:

                # 최근 온도 표시
                if pd.notna(latest_temperature):

                    st.metric(
                        "최근 공정 온도",
                        f"{latest_temperature:.2f}℃"
                    )

                else:

                    st.metric(
                        "최근 공정 온도",
                        "데이터 없음"
                    )

            with col2:

                # 최근 습도 표시
                if pd.notna(latest_humidity):

                    st.metric(
                        "최근 습도",
                        f"{latest_humidity:.2f}%"
                    )

                else:

                    st.metric(
                        "최근 습도",
                        "데이터 없음"
                    )

            st.divider()

            # --------------------------------------
            # 7-7. 최근 기록 정보
            # --------------------------------------

            st.subheader("최근 기록 정보")

            st.write("**최근 기록 시간**")

            st.write(
                latest_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            st.write("**최근 가동 상태**")

            # 가동 상태가 없는 경우 처리
            if pd.notna(latest_status):

                st.write(str(latest_status))

            else:

                st.write("데이터 없음")

            st.divider()

            # ======================================
            # 7-8. 시간별 온도 변화 그래프 (추가)
            # ======================================

            st.subheader("시간별 온도 변화")

            st.write(
                "선택한 설비의 시간에 따른 "
                "공정 온도 변화를 확인합니다."
            )

            # 온도 데이터가 없는 기록 제외
            temperature_data = machine_df.dropna(
                subset=["temperature"]
            ).copy()

            # 온도 데이터가 있는 경우
            if not temperature_data.empty:

                # ----------------------------------
                # ① Plotly 온도 선그래프 생성
                # ----------------------------------

                fig_temp = px.line(
                    temperature_data,
                    x="timestamp",
                    y="temperature",
                    title="시간별 온도 변화",
                    markers=True,
                    labels={
                        "timestamp": "기록 시간",
                        "temperature": "공정 온도(℃)"
                    }
                )

                # ----------------------------------
                # ② 40℃ 기준선 추가
                # ----------------------------------

                fig_temp.add_hline(
                    y=40,
                    line_color="red",
                    line_dash="dash",
                    line_width=2
                )

                # ----------------------------------
                # ③ 마우스 정보 설정
                # ----------------------------------

                fig_temp.update_traces(
                    hovertemplate=(
                        "기록 시간: %{x|%Y-%m-%d %H:%M:%S}<br>"
                        "공정 온도: %{y:.2f}℃"
                        "<extra></extra>"
                    )
                )

                # ----------------------------------
                # ④ 그래프 디자인
                # ----------------------------------

                fig_temp.update_layout(
                    xaxis_title="기록 시간",
                    yaxis_title="공정 온도(℃)",
                    height=500,
                    margin=dict(
                        l=30,
                        r=30,
                        t=70,
                        b=30
                    ),
                    hovermode="closest"
                )

                # 시간 표시 형식
                fig_temp.update_xaxes(
                    tickformat="%m-%d %H:%M"
                )

                # ----------------------------------
                # ⑤ Streamlit에 그래프 출력
                # ----------------------------------

                st.plotly_chart(
                    fig_temp,
                    use_container_width=True
                )

                # 기준선 설명
                st.caption(
                    "빨간색 점선은 공정 온도 40℃ 기준선입니다."
                )

            else:

                st.warning(
                    "선택한 설비에 온도 데이터가 없습니다."
                )

            st.divider()

            # ======================================
            # 7-9. 시간별 습도 변화 그래프 (추가)
            # ======================================

            st.subheader("시간별 습도 변화")

            st.write(
                "선택한 설비의 시간에 따른 "
                "습도 변화를 확인합니다."
            )

            # 습도 데이터가 없는 기록 제외
            humidity_data = machine_df.dropna(
                subset=["humidity"]
            ).copy()

            # 습도 데이터가 있는 경우
            if not humidity_data.empty:

                # ----------------------------------
                # ① Plotly 습도 선그래프 생성
                # ----------------------------------

                fig_humidity = px.line(
                    humidity_data,
                    x="timestamp",
                    y="humidity",
                    title="시간별 습도 변화",
                    markers=True,
                    labels={
                        "timestamp": "기록 시간",
                        "humidity": "습도(%)"
                    }
                )

                # ----------------------------------
                # ② 마우스 정보 설정
                # ----------------------------------

                fig_humidity.update_traces(
                    hovertemplate=(
                        "기록 시간: %{x|%Y-%m-%d %H:%M:%S}<br>"
                        "습도: %{y:.2f}%"
                        "<extra></extra>"
                    )
                )

                # ----------------------------------
                # ③ 그래프 디자인
                # ----------------------------------

                fig_humidity.update_layout(
                    xaxis_title="기록 시간",
                    yaxis_title="습도(%)",
                    height=500,
                    margin=dict(
                        l=30,
                        r=30,
                        t=70,
                        b=30
                    ),
                    hovermode="closest",
                    yaxis=dict(
                        ticksuffix="%"
                    )
                )

                # 시간 표시 형식
                fig_humidity.update_xaxes(
                    tickformat="%m-%d %H:%M"
                )

                # ----------------------------------
                # ④ Streamlit에 그래프 출력
                # ----------------------------------

                st.plotly_chart(
                    fig_humidity,
                    use_container_width=True
                )

            else:

                st.warning(
                    "선택한 설비에 습도 데이터가 없습니다."
                )

    else:

        st.warning(
            "CSV 파일을 업로드하면 "
            "설비 모니터링 정보가 표시됩니다."
        )


# ==================================================
# 8. 데이터 관리 메뉴 (기존 기능 유지)
# ==================================================

elif menu == "데이터 관리":

    st.header("데이터 관리")

    st.write(
        "생산 데이터를 조회하고 관리하는 화면입니다."
    )

    st.info(
        "추후 데이터 검색과 입력 기능을 추가합니다."
    )
