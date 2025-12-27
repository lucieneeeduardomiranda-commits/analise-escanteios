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
    .status-box { padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- Funções de Cálculo ---
def get_temporal_factor_ht(minuto, f_ini, f_meio, f_final, f_extras):
    if minuto <= 15: return f_ini
    elif 16 <= minuto <= 35: return f_meio
    elif 36 <= minuto <= 45: return f_final
    else: return f_extras 

def calcular_lambda_restante_ht(minutos_jogados, media_ht, f1, f2, f3, f4):
    tempo_base = 45
    tempo_limite = 48 
    taxa_base = media_ht / tempo_base
    lambda_restante = 0.0
    
    if minutos_jogados >= tempo_limite:
        return 0.0

    for minuto in range(minutos_jogados + 1, tempo_limite + 1):
        fator = get_temporal_factor_ht(minuto, f1, f2, f3, f4)
        lambda_restante += taxa_base * fator
    return lambda_restante

def neg_binomial_prob(k_count, mu, dispersion_param):
    if k_count < 0: return 0.0
    if mu <= 0: return 1.0 if k_count == 0 else 0.0
    n = dispersion_param
    p = n / (n + mu)
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
    linha = st.number_input("Linha Over HT", 0.5, 10.0, 4.5, 0.5)
    odd_o = st.number_input("Odd Over Atual", 1.01, 10.0, 1.85)
    
    ritmo = st.selectbox("Comportamento", ["Estudado (K: 2.2)", "Padrão (K: 1.8)", "Pressão (K: 1.3)"], index=1)
    k_map = {"Estudado (K: 2.2)": 2.2, "Padrão (K: 1.8)": 1.8, "Pressão (K: 1.3)": 1.3}
    k_val = k_map[ritmo]

    with st.expander("⚙️ Ajuste Fatores de Tempo"):
        f1 = st.slider("0-15 min", 0.5, 1.5, 0.80)
        f2 = st.slider("16-35 min", 0.5, 1.5, 1.00)
        f3 = st.slider("36-45 min", 0.5, 2.0, 1.30)
        f4 = st.slider("45+ min (Extras)", 0.5, 2.5, 1.50)

# --- Corpo Principal ---
st.title("⚽ Scanner de Escanteios HT (45'+3)")
st.info("Utilizando Médias Cruzadas: (Ataque A + Defesa B) / 2")

# Seção de Médias Cruzadas
col_casa, col_visitante = st.columns(2)

with col_casa:
    st.subheader("🏠 Time da Casa")
    m_favor_casa = st.number_input("Cantos A FAVOR (Casa)", 0.0, 10.0, 2.5)
    m_contra_casa = st.number_input("Cantos CONTRA (Casa)", 0.0, 10.0, 2.0)

with col_visitante:
    st.subheader("🚀 Time Visitante")
    m_favor_vis = st.number_input("Cantos A FAVOR (Fora)", 0.0, 10.0, 2.0)
    m_contra_vis = st.number_input("Cantos CONTRA (Fora)", 0.0, 10.0, 2.5)

# Cálculo da Expectativa Cruzada
exp_casa = (m_favor_casa + m_contra_vis) / 2
exp_vis = (m_favor_vis + m_contra_casa) / 2
media_ponderada = exp_casa + exp_vis

st.divider()

# Métricas de Expectativa
c_e1, c_e2, c_e3 = st.columns(3)
c_e1.metric("Exp. Individual Casa", f"{exp_casa:.2f}")
c_e2.metric("Exp. Individual Fora", f"{exp_vis:.2f}")
c_e3.metric("Expectativa Total HT", f"{media_ponderada:.2f}")

if st.button("CALCULAR PROBABILIDADES HT"):
    # Execução do Modelo
    lambda_r = calcular_lambda_restante_ht(minutos, media_ponderada, f1, f2, f3, f4)
    target_over = math.floor(linha) + 1 - atuais
    
    # Cálculo de Probabilidades
    is_half = (linha * 10) % 10 != 0
    if is_half:
        p_under = sum(neg_binomial_prob(k, lambda_r, k_val) for k in range(max(0, target_over)))
        p_over = 1.0 - p_under
        p_push = 0.0
    else:
        p_push = neg_binomial_prob(target_over, lambda_r, k_val)
        p_under = sum(neg_binomial_prob(k, lambda_r, k_val) for k in range(max(0, target_over)))
        p_over = 1.0 - p_push - p_under

    # Cálculos de EV e Odd Mínima
    p_perda_over = 1.0 - p_over - p_push
    ev_o = (p_over * (odd_o - 1)) - (p_perda_over * 1)
    odd_min_5 = calcular_odd_minima_ev5(p_over, p_perda_over)

    # --- EXIBIÇÃO ---
    st.divider()
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Probabilidade Over", f"{p_over:.1%}")
    col_res2.metric("Probabilidade Push", f"{p_push:.1%}" if not is_half else "N/A")
    col_res3.metric("Expectativa Restante", f"{lambda_r:.2f}")

    # Veredito e Odd Mínima
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.subheader("📊 Valor Esperado (EV)")
        if ev_o > 0.05:
            st.success(f"### ✅ EV POSITIVO: {ev_o:.3f}")
        elif ev_o > 0:
            st.warning(f"### ⚠️ EV NEUTRO: {ev_o:.3f}")
        else:
            st.error(f"### 🛑 EV NEGATIVO: {ev_o:.3f}")

    with col_v2:
        st.subheader("💰 Odd Mínima (EV +5%)")
        if odd_min_5:
            st.metric("Entrar apenas se Odd >", f"{odd_min_5:.2f}")
            if odd_o >= odd_min_5:
                st.success("A Odd atual possui valor!")
            else:
                st.error("Aguarde a Odd subir.")
        else:
            st.write("Cenário matematicamente improvável.")

    # Visualização da Distribuição
    with st.expander("📈 Distribuição de Probabilidade Exata"):
        probs = []
        for i in range(7):
            probs.append({"Cantos Extras": str(i), "Probabilidade": neg_binomial_prob(i, lambda_r, k_val)})
        
        df_probs = pd.DataFrame(probs)
        st.bar_chart(df_probs.set_index("Cantos Extras"))