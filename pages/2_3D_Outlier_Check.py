import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import (
    get_leaf_df, delete_leaf_by_id, log_outlier_action, SPECIES_LIST
)

if not st.session_state.get('logged_in', False):
    st.warning("🔒 서비스를 이용하려면 먼저 로그인해 주세요.")
    st.stop()

col_t1, col_t2 = st.columns([4, 1])
with col_t1:
    st.title("📐 2. 3차원 산점도 시각화 및 공유 DB 이상치 검증")
with col_t2:
    st.write("")
    if st.button("🔄 실시간 새로고침", use_container_width=True):
        st.rerun()

st.markdown("학급 공유 DB의 모든 데이터를 3차원 공간에 시각화하고, 군집에서 벗어난 **조작된 가짜 데이터(이상치)**를 모둠원과 함께 색출하여 정제합니다.")

df = get_leaf_df()
fake_cnt = int(df['가짜여부'].sum())
if fake_cnt > 0:
    st.error(f"🚨 긴급 미션! 현재 학급 공유 DB에 **의심스러운 이상치 데이터 {fake_cnt}개**가 감지되었습니다! 3D 그래프를 회전시켜 찾아내고 아래에서 제거하세요!")
else:
    st.success("✅ 현재 학급 공유 DB가 깨끗한 상태입니다! 각 수종의 3차원 군집 분포를 탐색해 보세요.")

fig = px.scatter_3d(
    df,
    x='가로',
    y='세로',
    z='잎자루',
    color='종',
    hover_name='개체명',
    hover_data={'ID': True, '가로': True, '세로': True, '잎자루': True, '작성자': True, '가짜여부': False},
    title="학급 공유 DB 나뭇잎 특징량 3차원 산점도 (마우스로 드래그하여 회전/확대)",
    height=560,
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig.update_traces(marker=dict(size=6, opacity=0.85, line=dict(width=0.5, color='DarkSlateGrey')))
fig.update_layout(
    margin=dict(l=0, r=0, b=0, t=40),
    scene=dict(
        xaxis_title='가로 길이 X (cm)',
        yaxis_title='세로 길이 Y (cm)',
        zaxis_title='잎자루 길이 Z (cm)'
    )
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("🔍 이상치(조작된 데이터) 직접 색출 및 삭제")
st.write("3D 산점도에서 발견한 **비정상적인 좌표값(또는 ID)**을 가진 데이터를 아래에서 선택하여 삭제하세요. 삭제 결과는 학급 공유 DB에 즉시 반영됩니다.")

col_stat, col_del = st.columns([1.3, 1], gap="large")

with col_stat:
    st.markdown("**📌 수목 종별 정상 범위 참고 (평균 · 최소 · 최대)**")
    clean_only = df[~df['가짜여부']]
    summary = clean_only.groupby('종')[['가로', '세로', '잎자루']].agg(['mean', 'min', 'max']).round(2)
    summary.columns = ['가로_평균', '가로_최소', '가로_최대', '세로_평균', '세로_최소', '세로_최대', '잎자루_평균', '잎자루_최소', '잎자루_최대']
    st.dataframe(summary, use_container_width=True)

with col_del:
    st.markdown("**🗑️ 의심 데이터 선택 및 공유 DB에서 제거**")
    filter_sp = st.selectbox("종 필터링", ["전체"] + SPECIES_LIST)
    filtered_df = df if filter_sp == "전체" else df[df['종'] == filter_sp]

    filtered_rev = filtered_df.iloc[::-1]
    options = [
        f"[ID:{row['ID']}] {row['개체명']} ({row['종']}) - 가로:{row['가로']}, 세로:{row['세로']}, 잎자루:{row['잎자루']} | 작성:{row['작성자']}"
        for _, row in filtered_rev.iterrows()
    ]
    selected_option = st.selectbox("삭제할 데이터 항목 선택", options)

    if st.button("🗑️ 선택한 데이터 삭제하기", type="primary", use_container_width=True):
        if selected_option:
            target_id = int(selected_option.split(']')[0].replace('[ID:', ''))
            target_row = df[df['ID'] == target_id].iloc[0]
            is_fake_target = bool(target_row['가짜여부'])
            target_name = target_row['개체명']
            delete_leaf_by_id(target_id)
            log_outlier_action(
                userid=st.session_state.get('userid', ''),
                username=st.session_state.get('username', ''),
                target_name=target_name,
                is_true_fake=is_fake_target
            )
            if is_fake_target:
                st.success(f"🎉 정답입니다! 조작된 가짜 데이터 '{target_name}'을(를) 공유 DB에서 정확히 색출하여 제거했습니다!")
                st.balloons()
            else:
                st.warning(f"⚠️ '{target_name}' 데이터는 정상 데이터였습니다. 좌표를 다시 신중하게 확인해 보세요!")
            st.rerun()
