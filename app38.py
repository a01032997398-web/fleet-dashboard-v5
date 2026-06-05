import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.graph_objects as go

# ─────────────────────────────────────────
# 1. 보유 수량 및 전술 변수 설정
# ─────────────────────────────────────────
REAL_SEC_COUNT   = 868
REAL_SEC_P_COUNT = 7248

VOO_COUNT  = 104
QQQM_COUNT = 398
SCHD_COUNT = 735
IONQ_COUNT = 215

CORE_TARGET_KRW  = 20 * 1e8    # 코어 20억
SELL_TRIGGER_KRW = 21.5 * 1e8  # 매도 트리거 21.5억

# ★ [신규 탑재] 20회 스위칭 카운터 (스위칭 1회 완료 시마다 아래 숫자를 1씩 올리십시오)
COMPLETED_SWITCHES = 0

# ─────────────────────────────────────────
# 2. 데이터 수집
# ─────────────────────────────────────────
def get_naver_price(code):
    try:
        url = f"https://finance.naver.com/item/sise.naver?code={code}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        return int(soup.select_one(".no_today .blind").text.replace(",", ""))
    except:
        return 0

@st.cache_data(ttl=300)
def get_global_data():
    tickers = ["VOO", "QQQM", "SCHD", "IONQ", "USDKRW=X"]
    data = yf.download(tickers, period="2d", auto_adjust=True)['Close'].ffill().iloc[-1]
    
    # SCHD 배당률 정보 추가 수집 (Yahoo Finance API Info)
    try:
        schd_info = yf.Ticker("SCHD").info
        div_yield = schd_info.get('trailingAnnualDividendYield', 0.0345) * 100 
    except:
        div_yield = 3.45
        
    return data, div_yield

# ─────────────────────────────────────────
# 3. 페이지 & 데이터 로드
# ─────────────────────────────────────────
st.set_page_config(page_title="Herrsong v5.6", layout="wide", page_icon="🎖️")

# ─────────────────────────────────────────
# 사이드바: 평균단가 직접 입력
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 평균단가 설정")
    st.caption("실제 매입 평균단가를 입력하세요")

    st.markdown("**🇰🇷 국내주식 (원)**")
    SEC_AVG_PRICE   = st.number_input("삼전 본주 평균단가",
                                      min_value=10_000, max_value=500_000,
                                      value=68_284, step=100, format="%d")
    SEC_P_AVG_PRICE = st.number_input("삼전우 평균단가",
                                      min_value=10_000, max_value=500_000,
                                      value=62_207, step=100, format="%d")

    st.markdown("**🇺🇸 미국 ETF (USD)**")
    voo_avg  = st.number_input("VOO 평균단가",  min_value=1.0, value=634.91,  step=0.01, format="%.2f")
    qqqm_avg = st.number_input("QQQM 평균단가", min_value=1.0, value=253.16,  step=0.01, format="%.2f")
    schd_avg = st.number_input("SCHD 평균단가", min_value=1.0, value=32.27,   step=0.01, format="%.2f")
    ionq_avg = st.number_input("IONQ 평균단가", min_value=1.0, value=32.05,   step=0.01, format="%.2f")

ETF_AVG = {
    "VOO":  {"qty": VOO_COUNT,  "avg_usd": voo_avg},
    "QQQM": {"qty": QQQM_COUNT, "avg_usd": qqqm_avg},
    "SCHD": {"qty": SCHD_COUNT, "avg_usd": schd_avg},
    "IONQ": {"qty": IONQ_COUNT, "avg_usd": ionq_avg},
}

with st.spinner("실시간 자산 가치 산정 중..."):
    p_sec   = get_naver_price("005930")
    p_sec_p = get_naver_price("005935")
    g_data, schd_div_yield = get_global_data()
    usd_krw = float(g_data["USDKRW=X"])

us_prices = {t: float(g_data[t]) for t in ["VOO","QQQM","SCHD","IONQ"]}

sec_total_krw = (p_sec * REAL_SEC_COUNT) + (p_sec_p * REAL_SEC_P_COUNT)
sec_eval_bn   = sec_total_krw / 1e8
us_total_usd  = sum(ETF_AVG[t]["qty"] * us_prices[t] for t in us_prices)
us_total_krw  = us_total_usd * usd_krw
disparity_pct = (p_sec - p_sec_p) / p_sec * 100 if p_sec > 0 else 0

# ─────────────────────────────────────────
# v5.6 컬러 코딩 (환율 & SCHD 배당률)
# ─────────────────────────────────────────
if usd_krw >= 1450:
    fx_color = "#ef4444"
elif usd_krw <= 1350:
    fx_color = "#22c55e"
else:
    fx_color = "inherit"

if schd_div_yield >= 3.55:
    schd_color = "#22c55e"
elif schd_div_yield >= 3.40:
    schd_color = "#3b82f6"
else:
    schd_color = "inherit"

# ─────────────────────────────────────────
# 4. 헤더 & KPI
# ─────────────────────────────────────────
st.title("🎖️ Herrsong 통합 전략 통제실 v5.6")
st.markdown(
    f"<span style='font-size:0.9em; color:gray;'>"
    f"업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"삼전: {p_sec:,}원 | 삼전우: {p_sec_p:,}원 | "
    f"<span style='color:{fx_color}; font-weight:bold;'>환율: {usd_krw:,.0f}원</span> | "
    f"괴리율: {disparity_pct:.1f}% | "
    f"<span style='color:{schd_color}; font-weight:bold;'>SCHD 배당률: {schd_div_yield:.2f}%</span>"
    f"</span>",
    unsafe_allow_html=True
)

k1, k2, k3 = st.columns(3)
k1.metric("삼전 합산", f"{sec_eval_bn:.2f}억",
          f"코어까지 {(CORE_TARGET_KRW - sec_total_krw)/1e8:.2f}억 잔여")
k2.metric("미국 ETF", f"${us_total_usd:,.0f}",
          f"{us_total_krw/1e8:.2f}억")
k3.metric("총 자산", f"{(sec_total_krw + us_total_krw)/1e8:.2f}억")

st.divider()

# ─────────────────────────────────────────
# 5. 탭 구성
# ─────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["코어 게이지", "종목별 수익률", "삼전우 시나리오", "❄️ 배당 스노우볼"])

# ══════════════════════════════════════════
# TAB 1: 코어 게이지 & 조타수
# ══════════════════════════════════════════
with tab1:
    col_g, col_b = st.columns([3, 2])

    with col_g:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=sec_eval_bn,
            delta={
                'reference': 15.0,
                'increasing': {'color': '#22c55e'},
                'decreasing': {'color': '#ef4444'},
                'suffix': '억'
            },
            number={'suffix': '억', 'font': {'size': 48}},
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "삼성전자 20억 코어 달성률", 'font': {'size': 20}},
            gauge={
                'axis': {
                    'range': [10, 25],
                    'tickwidth': 1,
                    'ticksuffix': '억',
                    'tickvals': [10, 12.5, 15, 17.5, 20, 22.5, 25],
                },
                'bar': {'color': "#3b82f6"},
                'steps': [
                    {'range': [10, 15], 'color': '#fef3c7'},
                    {'range': [15, 20], 'color': '#dbeafe'},
                    {'range': [20, 25], 'color': '#bbf7d0'},
                ],
                'threshold': {
                    'line': {'color': 'red', 'width': 4},
                    'thickness': 0.85,
                    'value': 20.0
                }
            }
        ))
        fig_gauge.update_layout(height=380, margin=dict(t=60, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        st.markdown("### 🏁 삼전 코어 돌파 마일스톤")
        
        milestones = [21.0, 22.0, 23.0, 24.0, 25.0]
        m_cols = st.columns(len(milestones))
        
        for idx, target_bn in enumerate(milestones):
            with m_cols[idx]:
                if sec_eval_bn >= target_bn:
                    st.markdown(
                        f"<div style='text-align: center; border: 2px solid #22c55e; "
                        f"border-radius: 8px; padding: 10px; background-color: #152b1e;'>"
                        f"<span style='font-size: 1.2em;'>🟢</span><br>"
                        f"<b style='color:#22c55e;'>{target_bn}억</b><br>"
                        f"<span style='font-size: 0.8em; color: gray;'>달성 완료</span>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='text-align: center; border: 1px solid #444; "
                        f"border-radius: 8px; padding: 10px; background-color: #1e1e1e;'>"
                        f"<span style='font-size: 1.2em;'>⚪</span><br>"
                        f"<b style='color:#888;'>{target_bn}억</b><br>"
                        f"<span style='font-size: 0.8em; color: gray;'>진격 중</span>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )

        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("#### 🔄 1억 커팅 앤 스위칭 진척도 (목표: 달러 비중 50%)")

        switch_amount_krw = COMPLETED_SWITCHES * 100_000_000
        schd_yield = 0.035
        annual_dividend_krw = switch_amount_krw * schd_yield
        monthly_dividend_krw = annual_dividend_krw / 12

        progress_ratio = COMPLETED_SWITCHES / 20.0
        st.progress(progress_ratio)

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("타격 진척도", f"{COMPLETED_SWITCHES} / 20 회")
        with col_s2:
            st.metric("달러 이전 자산", f"{COMPLETED_SWITCHES}억 원")
        with col_s3:
            st.metric("🌊 추가 확정 월 배당", f"약 {int(monthly_dividend_krw):,} 원")

        st.info(f"💡 **조타수 브리핑:** 현재 **{COMPLETED_SWITCHES}억 원**이 안전하게 달러 요새로 스위칭되었습니다. 목표 달성 시점까지 **{20 - COMPLETED_SWITCHES}회** 남았습니다.")

    with col_b:
        st.markdown("### 🧭 조타수 브리핑")

        core_pct           = sec_total_krw / CORE_TARGET_KRW * 100
        target_p_for_core  = (CORE_TARGET_KRW - p_sec * REAL_SEC_COUNT) / REAL_SEC_P_COUNT
        target_p_for_sell  = (SELL_TRIGGER_KRW - p_sec * REAL_SEC_COUNT) / REAL_SEC_P_COUNT

        st.metric("코어 달성률",
                  f"{core_pct:.1f}%",
                  f"{sec_eval_bn:.2f}억 / 20억")
        st.metric("20억 달성 필요 삼전우가",
                  f"{target_p_for_core:,.0f}원",
                  f"현재 대비 {target_p_for_core - p_sec_p:+,.0f}원")
        st.metric("21.5억 매도트리거 삼전우가",
                  f"{target_p_for_sell:,.0f}원",
                  f"현재 대비 {target_p_for_sell - p_sec_p:+,.0f}원")

        st.divider()

        st.markdown("**🚦 매도 트리거 상태**")

        triggers = [
            ("본주 3억 트리거", p_sec >= 346000, f"단가 34.6만 (3억) 기준 | 현재 {p_sec:,}원"),
            ("가격 트리거", sec_total_krw >= SELL_TRIGGER_KRW, f"21.5억 기준 | 현재 {sec_eval_bn:.2f}억"),
            ("괴리율 트리거", disparity_pct <= 18, f"18% 이하 기준 | 현재 {disparity_pct:.1f}%"),
            ("코어 달성", sec_total_krw >= CORE_TARGET_KRW, f"20억 기준 | 현재 {sec_eval_bn:.2f}억")
        ]
        
        for name, ok, note in triggers:
            icon = "🟢" if ok else "🔴"
            st.markdown(f"{icon} **{name}** — {note}")

# ══════════════════════════════════════════
# TAB 2: 종목별 수익률 테이블
# ══════════════════════════════════════════
with tab2:
    st.markdown("### 📋 종목별 손익 현황")

    st.markdown("#### 🇰🇷 국내주식")
    kr_items = [
        ("삼성전자 본주", REAL_SEC_COUNT,   p_sec,   SEC_AVG_PRICE),
        ("삼성전자우",    REAL_SEC_P_COUNT, p_sec_p, SEC_P_AVG_PRICE),
    ]
    kr_rows = []
    for name, qty, cur, avg in kr_items:
        eval_krw = cur * qty
        cost_krw = avg * qty
        profit   = eval_krw - cost_krw
        pct      = profit / cost_krw * 100
        kr_rows.append({
            "종목":       name,
            "수량":       f"{qty:,}주",
            "현재가":     f"{cur:,}원",
            "평균단가":   f"{avg:,}원",
            "평가액":     f"{eval_krw/1e8:.2f}억",
            "손익":       f"{profit/1e8:+.2f}억",
            "수익률":     f"{pct:+.1f}%",
        })

    df_kr = pd.DataFrame(kr_rows)
    def color_pct(val):
        c = "#22c55e" if "+" in val else "#ef4444"
        return f"color: {c}; font-weight: bold"

    st.dataframe(
        df_kr.style.map(color_pct, subset=["수익률", "손익"]),
        hide_index=True, use_container_width=True
    )

    total_eval = sum(r["수량_raw"] * r["cur"] for r in [
        {"수량_raw": REAL_SEC_COUNT, "cur": p_sec},
        {"수량_raw": REAL_SEC_P_COUNT, "cur": p_sec_p},
    ])
    total_cost = (SEC_AVG_PRICE * REAL_SEC_COUNT) + (SEC_P_AVG_PRICE * REAL_SEC_P_COUNT)
    total_profit = total_eval - total_cost
    st.info(
        f"**삼전 합산** | 평가액 {total_eval/1e8:.2f}억 | "
        f"총손익 {total_profit/1e8:+.2f}억 | "
        f"수익률 {total_profit/total_cost*100:+.1f}%"
    )

    st.divider()

    st.markdown("#### 🇺🇸 미국 ETF")
    etf_rows = []
    for ticker, info in ETF_AVG.items():
        cur  = us_prices[ticker]
        avg  = info["avg_usd"]
        qty  = info["qty"]
        eval_usd  = cur * qty
        cost_usd  = avg * qty
        profit_usd = eval_usd - cost_usd
        pct        = profit_usd / cost_usd * 100
        etf_rows.append({
            "티커":       ticker,
            "수량":       f"{qty}주",
            "현재가":     f"${cur:.2f}",
            "평균단가":   f"${avg:.2f}",
            "평가액":     f"${eval_usd:,.0f}",
            "손익":       f"${profit_usd:+,.0f}",
            "수익률":     f"{pct:+.1f}%",
            "평가액(억)": f"{eval_usd * usd_krw / 1e8:.2f}",
        })

    df_etf = pd.DataFrame(etf_rows)
    st.dataframe(
        df_etf.style.map(color_pct, subset=["수익률", "손익"]),
        hide_index=True, use_container_width=True
    )

    etf_eval  = sum(ETF_AVG[t]["qty"] * us_prices[t] for t in ETF_AVG)
    etf_cost  = sum(ETF_AVG[t]["qty"] * ETF_AVG[t]["avg_usd"] for t in ETF_AVG)
    etf_profit = etf_eval - etf_cost
    st.info(
        f"**ETF 합산** | 평가액 ${etf_eval:,.0f} ({etf_eval*usd_krw/1e8:.2f}억) | "
        f"총손익 ${etf_profit:+,.0f} | "
        f"수익률 {etf_profit/etf_cost*100:+.1f}%"
    )

# ══════════════════════════════════════════
# TAB 3: 삼전우 목표가별 시나리오
# ══════════════════════════════════════════
with tab3:
    st.markdown("### 🎯 삼전우 목표가별 합산 시나리오")
    st.caption(f"삼전 본주 {p_sec:,}원 고정 | 삼전우 7,248주 기준")

    base = (p_sec_p // 10_000) * 10_000
    price_range = range(max(100_000, base - 50_000), base + 110_000, 10_000)

    rows = []
    for sp in price_range:
        total_bn = (p_sec * REAL_SEC_COUNT + sp * REAL_SEC_P_COUNT) / 1e8
        disp     = (p_sec - sp) / p_sec * 100 if p_sec > 0 else 0
        delta_p  = sp - p_sec_p

        if total_bn >= 21.5:
            status = "🔴 매도 실행"
        elif total_bn >= 20.0:
            status = "🟡 코어 달성 (대기)"
        else:
            status = "🔵 코어 진입 중"

        rows.append({
            "삼전우 가격":    f"{sp:,}원",
            "현재 대비":      f"{delta_p:+,}원",
            "괴리율":         f"{disp:.1f}%",
            "삼전 합산(억)":  f"{total_bn:.2f}",
            "상태":           status,
        })

    df_s = pd.DataFrame(rows)

    def highlight_current(row):
        cur_str = f"{p_sec_p:,}원"
        if row["삼전우 가격"] == cur_str:
            return ['background-color: #1e3a5f; font-weight: bold'] * len(row)
        return [''] * len(row)

    st.dataframe(
        df_s.style.apply(highlight_current, axis=1),
        hide_index=True, use_container_width=True, height=480
    )

    st.divider()

    st.markdown("#### 📌 핵심 목표가 요약")
    c1, c2, c3 = st.columns(3)

    target_core = (CORE_TARGET_KRW - p_sec * REAL_SEC_COUNT) / REAL_SEC_P_COUNT
    target_sell = (SELL_TRIGGER_KRW - p_sec * REAL_SEC_COUNT) / REAL_SEC_P_COUNT
    c1.metric("현재 삼전우",     f"{p_sec_p:,}원")
    c2.metric("20억 코어 달성가", f"{target_core:,.0f}원", f"{target_core - p_sec_p:+,.0f}원")
    c3.metric("21.5억 매도트리거", f"{target_sell:,.0f}원", f"{target_sell - p_sec_p:+,.0f}원")

    chart_prices = list(price_range)
    chart_vals   = [(p_sec * REAL_SEC_COUNT + sp * REAL_SEC_P_COUNT) / 1e8 for sp in chart_prices]

    fig_line = go.Figure()
    fig_line.add_scatter(x=chart_prices, y=chart_vals, mode="lines+markers", name="삼전 합산",
                         line=dict(color="#3b82f6", width=2), marker=dict(size=6))
    fig_line.add_hline(y=20.0, line_dash="dash", line_color="red", annotation_text="20억 코어", annotation_position="right")
    fig_line.add_hline(y=21.5, line_dash="dot", line_color="orange", annotation_text="21.5억 매도트리거", annotation_position="right")
    fig_line.add_vline(x=p_sec_p, line_dash="dash", line_color="gray", annotation_text=f"현재 {p_sec_p:,}원")
    fig_line.update_layout(title="삼전우 가격 → 삼전 합산 평가액", xaxis_title="삼전우 주가 (원)", yaxis_title="삼전 합산 (억)", height=360, margin=dict(t=50, b=20))
    st.plotly_chart(fig_line, use_container_width=True)

# ══════════════════════════════════════════
# TAB 4: 배당 스노우볼(DRIP) 시뮬레이터
# ══════════════════════════════════════════
with tab4:
    st.subheader("❄️ 40억 함대 배당 재투자(DRIP) 시뮬레이터")
    st.markdown("배당금 전액 재투자 시, **100만 불 요새** 완성과 **자녀 각 5억 독립 시점**을 예측합니다.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        current_usd = st.number_input("현재 달러 ETF 평가액 ($)", value=229292, step=1000)
    with c2:
        monthly_add = st.number_input("매월 추가 투입액 ($)", value=3000, step=500)
    with c3:
        cagr = st.slider("예상 연평균 수익률 (배당+성장) %", 5.0, 15.0, 10.0, 0.5)

    years = 15
    data = []
    accumulated = current_usd
    
    for year in range(1, years + 1):
        accumulated = accumulated * (1 + cagr / 100) + (monthly_add * 12)
        data.append({"연차": year, "예상 자산($)": int(accumulated)})
        
    df = pd.DataFrame(data)
    df.set_index("연차", inplace=True)
    
    st.line_chart(df["예상 자산($)"])
    st.info(f"💡 현재 속도(연 {cagr}% 팽창) 유지 시, 배당 복리만으로 **100만 불($1,000,000) 요새** 달성 및 **자녀 독립 시드(각 5억 원)** 분리가 가능한 시점을 시각적으로 추적합니다.")

# ══════════════════════════════════════════
# 👑 80억 그랜드 마스터플랜 비전 (영구 각인)
# ══════════════════════════════════════════
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("## 👑 80억 그랜드 마스터플랜 비전 (2026~2030)")

col_v1, col_v2 = st.columns(2)

with col_v1:
    st.markdown("""
    <div style='background-color: #1e293b; padding: 20px; border-radius: 10px; height: 260px; border-left: 5px solid #3b82f6;'>
    <h4 style='margin-top: 0px;'>⚔️ 1단계: 40억 기동 함대 완성</h4>
    <ul style='line-height: 2.0;'>
        <li><b>국내 방어선:</b> 삼성전자 등 국내 주식 <b>20억 영구 고수</b></li>
        <li><b>달러 보급선:</b> 기계적 스위칭으로 미국 배당 ETF <b>100만 불 달성</b></li>
        <li><b>승계 전리품:</b> 마르지 않는 현금흐름으로 <b>자녀 각 5억 원 시드 조달</b></li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

with col_v2:
    st.markdown("""
    <div style='background-color: #1e293b; padding: 20px; border-radius: 10px; height: 260px; border-left: 5px solid #eab308;'>
    <h4 style='margin-top: 0px;'>🗺️ 2단계: 80억 실물 제국 타임라인</h4>
    <ul style='line-height: 1.8;'>
        <li><b>2026~2027:</b> 경부고속도로 착공 ➔ 서초 일대 기대감 선반영</li>
        <li><b>2028:</b> 롯데칠성 부지 착공 ➔ 주변 부동산 본격 상승</li>
        <li><b>2029~2030:</b> 연금 수령 시작 + ETF 배당 복리(DRIP) 무한 궤도</li>
        <li><b style='color:#facc15;'>2030: 법인 전환 완성 + 부동산 개발 효과 ➔ 80억대 후반 달성</b></li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

st.caption("⚓ **조타수의 맹세:** 어떠한 시장의 폭풍우가 몰아쳐도, 이 나침반이 가리키는 사령관님의 최종 목적지는 결코 변하지 않습니다.")
