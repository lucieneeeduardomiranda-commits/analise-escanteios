# -*- coding: utf-8 -*-
import streamlit as st
import math
from scipy.stats import nbinom
import pandas as pd

# --- Configuração de Estilo ---
st.set_page_config(page_title="Scanner HT Pro v7.5", page_icon="⏱️", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 26px; color: #ffaa00; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #e67e22; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- Funções de Cálculo ---
def get_temporal_factor_ht(minuto, f_ini, f_meio, f_final, f_extras):
    if minuto <= 15: return f_ini
    elif 16 <= minuto <= 35: return f_meio
    elif 36 <= minuto <= 45: return f_final
    else: return f_extras 

def calcular_lambda_restante_ht(minutos_jogados, media_ht, f1, f2, f3, f4):
    tempo_base, tempo_limite = 45, 48 
    taxa_base = media_ht / tempo_base
    lambda_restante = 0.0
    if minutos_jogados >= tempo_limite: return 0.0
    for minuto in range(minutos_jogados + 1, tempo_limite + 1):
        fator = get_temporal_factor_ht(minuto, f1, f2, f3, f4)
        lambda_restante += taxa_base * fator
    return lambda_restante

def neg_binomial_prob(k_count, mu, dispersion_param):
    if k_count < 0: return 0.0
    if mu <= 0: return 1.0 if k_count == 0 else 0.0
    n, p = dispersion_param, dispersion_param / (dispersion_param + mu)
    return float(nbinom.pmf(k_count, n, p))

def calcular_odd_minima_ev5(prob_ganho, prob_perda):
    ev_alvo = 0.05
    if prob_ganho <= 0: return None
    return ((ev_alvo + prob_perda) / prob_ganho) + 1

# --- Interface - Barra Lateral ---
with st.sidebar:
    st.header("🎮 Parâmetros HT")
    minutos = st.slider("Minuto Atual (1ºT)", 0, 48, 20)
    atuais = st.number_input("Escanteios no Momento", 0, 15, 2)
    
    st.divider()
    st.subheader("🎯 Mercado")
    linha = st.number_input("Linha HT (Ex: 4.5)", 0.5, 10.0, 4.5, 0.5)
    
    # --- AQUI ESTÃO OS CAMPOS QUE VOCÊ PRECISAVA ---
    col_odds1, col_odds2 = st.columns(2)
    with col_odds1:
        odd_o = st.number_input("Odd Over", 1.01, 20.0, 1.85)
    with col_odds2:
        odd_u = st.number_input("Odd Under", 1.01, 20.0, 1.85)
    
    ritmo = st.selectbox("Comportamento", ["Estudado (K: 2.2)", "Padrão (K: 1.8)", "Pressão (K: 1.3)"], index=1)
    k_val = {"Estudado (K: 2.2)": 2.2, "Padrão (K: 1.8)": 1.8, "Pressão (K: 1.3)": 1.3}[ritmo]

    with st.expander("⚙️ Ajuste Fatores de Tempo"):
        f1, f2, f3, f4 = st.slider("0-15m", 0.5, 1.5, 0.8), st.slider("16-35m", 0.5, 1.5, 1.0), st.slider("36-45m", 0.5, 2.0, 1.3), st.slider("45+m", 0.5, 2.5, 1.5)

# --- Corpo Principal ---
st.title("⚽ Scanner de Escanteios HT")

col_casa, col_visitante = st.columns(2)
with col_casa:
    m_favor_casa = st.number_input("Cantos PRO (Casa)", 0.0, 10.0, 2.5)
    m_contra_casa = st.number_input("Cantos CONTRA (Casa)", 0.0, 10.0, 2.0)
with col_visitante:
    m_favor_vis = st.number_input("Cantos PRO (Fora)", 0.0, 10.0, 2.0)
    m_contra_vis = st.number_input("Cantos CONTRA (Fora)", 0.0, 10.0, 2.5)

media_ponderada = ((m_favor_casa + m_contra_vis) / 2) + ((m_favor_vis + m_contra_casa) / 2)

if st.button("CALCULAR PROBABILIDADES"):
    lambda_r = calcular_lambda_restante_ht(minutos, media_ponderada, f1, f2, f3, f4)
    target_over = math.floor(linha) + 1 - atuais
    
    is_half = (linha * 10) % 10 != 0
    p_under = sum(neg_binomial_prob(k, lambda_r, k_val) for k in range(max(0, target_over)))
    p_push = neg_binomial_prob(target_over, lambda_r, k_val) if not is_half else 0.0
    p_over = 1.0 - p_under - p_push

    # Cálculos de EV
    ev_over = (p_over * (odd_o - 1)) - ((1 - p_over - p_push) * 1)
    ev_under = (p_under * (odd_u - 1)) - ((1 - p_under - p_push) * 1)
    
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Prob. Over", f"{p_over:.1%}")
    res2.metric("Prob. Under", f"{p_under:.1%}")
    res3.metric("Prob. Push", f"{p_push:.1%}" if not is_half else "N/A")

    # --- VEREDITO OVER E UNDER ---
    st.subheader("🏁 Veredito do Mercado")
    v_col1, v_col2 = st.columns(2)
    
    with v_col1:
        st.write("**Mercado OVER**")
        st.info(f"EV: {ev_over:.3f}")
        st.metric("Odd Mínima Over", f"{calcular_odd_minima_ev5(p_over, 1-p_over-p_push):.2f}")
        
    with v_col2:
        st.write("**Mercado UNDER**")
        st.info(f"EV: {ev_under:.3f}")
        st.metric("Odd Mínima Under", f"{calcular_odd_minima_ev5(p_under, 1-p_under-p_push):.2f}")

    if ev_over > 0.05: st.success("✅ Oportunidade detectada no OVER")
    elif ev_under > 0.05: st.success("✅ Oportunidade detectada no UNDER")
    else: st.warning("⚠️ Sem valor claro no momento")