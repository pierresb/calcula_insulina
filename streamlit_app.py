# -*- coding: utf-8 -*-
"""
Calcula Insulina — App Streamlit (protocolo + tendência Libre)

⚠️ Aviso: uso educativo. NÃO substitui orientação médica. Siga o plano do seu
profissional de saúde. Em hipoglicemia, trate primeiro.

Regras base (mg/dL), dose base = 12 UI:
- ≤ 70 → −6 UI (tratar hipo)
- 71–80 → −2 UI
- 81–130 → 0 UI (manter base)
- 131–160 → +1 UI
- 161–190 → +2 UI
- 191–220 → +3 UI
- 221–250 → +4 UI
- > 250 → +4 UI + 1 UI/30 mg/dL acima de 250

Correção adicional por **tendência Libre** (aplicada ao resultado acima; não aplicar se ≤ 70 mg/dL):
- **↑ (aumentando rápido)**: 70–180 → +2 UI; 181–250 → +2 UI; >250 → +3 UI
- **↗ (aumentando)**: 70–180 → +1 UI; 181–250 → +1 UI; >250 → +2 UI
- **→ (estável)**: sem ajuste
- **↘ (caindo)**: 70–180 → −2 UI; 181–250 → −1 UI; >250 → −1 UI
- **↓ (caindo rápido)**: 70–180 → −3 UI; 181–250 → −2 UI; >250 → −2 UI
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple, Literal

import streamlit as st

BASE_DOSE_UI = 12  # valor base fixo
Trend = Literal["↑", "↗", "→", "↘", "↓"]

@dataclass
class CalcOut:
    dose_recomendada: int
    delta_total: int
    delta_base: int
    delta_tendencia: int
    faixa_base: str
    faixa_tendencia: str


def regra_correcao(bg_mgdl: float) -> Tuple[int, str]:
    """Correção em UI baseada na glicemia (sem tendência)."""
    x = float(bg_mgdl)
    if x <= 70:  # hipo
        return (-6, "≤ 70 mg/dL → −6 UI (tratar hipo)")
    if 71 <= x <= 80:
        return (-2, "71–80 mg/dL → −2 UI")
    if 81 <= x <= 130:
        return (0, "81–130 mg/dL → 0 UI (manter base)")
    if 131 <= x <= 160:
        return (1, "131–160 mg/dL → +1 UI")
    if 161 <= x <= 190:
        return (2, "161–190 mg/dL → +2 UI")
    if 191 <= x <= 220:
        return (3, "191–220 mg/dL → +3 UI")
    if 221 <= x <= 250:
        return (4, "221–250 mg/dL → +4 UI")
    # x > 250 → +4 UI + 1 UI a cada 30 acima de 250
    extra = int(math.floor((x - 250.0) / 30.0))  # 251–280 => +1, 281–310 => +2, ...
    return (4 + max(0, extra), "> 250 mg/dL → +4 UI + 1 UI/30 mg/dL acima de 250")


def regra_tendencia(bg_mgdl: float, trend: Trend) -> Tuple[int, str]:
    """Correção adicional em UI baseada na tendência Libre. Não aplica se ≤ 70 mg/dL."""
    x = float(bg_mgdl)
    if x <= 70:
        return (0, "≤ 70 mg/dL → sem ajuste por tendência (tratar hipo)")

    def faixa(x: float) -> str:
        if 71 <= x <= 180:
            return "70–180"
        if 181 <= x <= 250:
            return "181–250"
        return ">250"

    bucket = faixa(x)

    if trend == "→":
        return (0, f"{bucket} e estável → 0 UI")

    if trend == "↑":  # aumentando rápido
        if bucket == "70–180":
            return (2, "+2 UI (↑, 70–180)")
        if bucket == "181–250":
            return (2, "+2 UI (↑, 181–250)")
        return (3, "+3 UI (↑, >250)")

    if trend == "↗":  # aumentando
        if bucket == "70–180":
            return (1, "+1 UI (↗, 70–180)")
        if bucket == "181–250":
            return (1, "+1 UI (↗, 181–250)")
        return (2, "+2 UI (↗, >250)")

    if trend == "↘":  # caindo
        if bucket == "70–180":
            return (-2, "−2 UI (↘, 70–180)")
        if bucket == "181–250":
            return (-1, "−1 UI (↘, 181–250)")
        return (-1, "−1 UI (↘, >250)")

    if trend == "↓":  # caindo rápido
        if bucket == "70–180":
            return (-3, "−3 UI (↓, 70–180)")
        if bucket == "181–250":
            return (-2, "−2 UI (↓, 181–250)")
        return (-2, "−2 UI (↓, >250)")

    return (0, "Tendência não reconhecida → 0 UI")


def calcular(bg_mgdl: float, trend: Trend) -> CalcOut:
    delta_base, faixa_base = regra_correcao(bg_mgdl)
    delta_tend, faixa_tend = regra_tendencia(bg_mgdl, trend)

    delta_total = delta_base + delta_tend
    dose = BASE_DOSE_UI + delta_total
    if dose < 0:
        dose = 0
    return CalcOut(
        dose_recomendada=int(dose),
        delta_total=int(delta_total),
        delta_base=int(delta_base),
        delta_tendencia=int(delta_tend),
        faixa_base=faixa_base,
        faixa_tendencia=faixa_tend,
    )


# ------------------------------ UI ------------------------------ #

st.set_page_config(page_title="Calcula Insulina — Protocolo", page_icon="💉", layout="centered")

st.title("💉 Calcula Insulina — protocolo + tendência")
st.caption(
    "Unidade: mg/dL. Dose base fixa: 12 UI. Correção por faixa + correção adicional pela **tendência** do Libre."
)

TREND_LABELS = {
    "↑ Aumentando rápido": "↑",
    "↗ Aumentando": "↗",
    "→ Estável": "→",
    "↘ Caindo": "↘",
    "↓ Caindo rápido": "↓",
}

with st.form("calc", clear_on_submit=False, border=True):
    col1, col2 = st.columns([1, 1])
    with col1:
        bg = st.number_input(
            "Glicemia (sensor Libre) — mg/dL",
            min_value=0.0,
            max_value=1000.0,
            value=110.0,
            step=10.0,
            help="Valor atual informado pelo Libre"
        )
    with col2:
        trend_label = st.radio(
            "Tendência Libre",
            list(TREND_LABELS.keys()),
            index=2,  # padrão: estável
            horizontal=True,
        )
    submitted = st.form_submit_button("Calcular dose", type="primary")

if submitted:
    trend = TREND_LABELS[trend_label]  # "↑", "↗", "→", "↘", "↓"
    out = calcular(bg, trend)  # type: ignore[arg-type]

    st.success("Cálculo realizado.")
    st.metric("Dose recomendada", f"{out.dose_recomendada} UI", delta=f"Δ {out.delta_total:+d} UI vs base")

    with st.expander("Detalhes", expanded=True):
        st.write(f"**Dose base:** {BASE_DOSE_UI} UI")
        st.write(f"**Correção por faixa:** {out.delta_base:+d} UI  —  {out.faixa_base}")
        st.write(f"**Correção por tendência:** {out.delta_tendencia:+d} UI  —  {out.faixa_tendencia}")
        st.write(f"**Δ total vs base:** {out.delta_total:+d} UI")
        st.write(f"**Resultado final:** **{out.dose_recomendada} UI**")

st.divider()

with st.expander("Tabela de referência", expanded=False):
    st.markdown(
        """
        **Faixas de glicemia (sem tendência)**  
        - **≤ 70** → −6 UI *(tratar hipoglicemia primeiro)*  
        - **71–80** → −2 UI  
        - **81–130** → 0 UI *(manter 12 UI)*  
        - **131–160** → +1 UI  
        - **161–190** → +2 UI  
        - **191–220** → +3 UI  
        - **221–250** → +4 UI  
        - **> 250** → +4 UI **+** 1 UI a cada 30 mg/dL acima de 250  

        **Ajustes por tendência (aplicados além do acima)**  
        - **↑ Aumentando rápido**: 70–180 → +2 UI; 181–250 → +2 UI; >250 → +3 UI  
        - **↗ Aumentando**: 70–180 → +1 UI; 181–250 → +1 UI; >250 → +2 UI  
        - **→ Estável**: 0 UI  
        - **↘ Caindo**: 70–180 → −2 UI; 181–250 → −1 UI; >250 → −1 UI  
        - **↓ Caindo rápido**: 70–180 → −3 UI; 181–250 → −2 UI; >250 → −2 UI  
        """
    )

st.caption("⚠️ Este app não substitui orientação médica. Em ≤ 70 mg/dL, trate hipo antes de qualquer dose.")
