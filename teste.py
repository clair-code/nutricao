import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, union
import json

# --- CONSTANTES E ENUMS ---
class Sexo(Enum):
    MASCULINO = "Masculino"
    FEMININO = "Feminino"

class Raca(Enum):
    BRANCA = "Branca"
    NEGRA = "Negra"

class Condicao(Enum):
    OBESIDADE = "obesidade"
    DESNUTRICAO = "desnutricao"

class NivelAtividade(Enum):
    LEVE_MODERADA = "leve a moderada"
    RESTRITA_INTENSA = "restrita intensa"
    RESTRICAO_GRAVE = "restrição física grave"

# --- FUNÇÕES NUTRICIONAIS ---
def calcular_peso_ajustado(peso_atual: float, peso_ideal: float, condicao: Condicao) -> Optional[float]:
    """Calcula o peso ajustado para obesidade ou desnutrição"""
    if peso_atual <= 0 or peso_ideal <= 0:
        raise ValueError("Pesos devem ser valores positivos")
    
    if condicao == Condicao.OBESIDADE:
        return (peso_atual - peso_ideal) * 0.25 + peso_ideal
    elif condicao == Condicao.DESNUTRICAO:
        return (peso_atual - peso_ideal) * 0.25 + peso_atual
    return None

def calcular_perda_peso(peso_usual: float, peso_atual: float) -> Optional[float]:
    """Calcula a porcentagem de perda de peso"""
    if peso_usual <= 0:
        raise ValueError("Peso usual deve ser maior que zero")
    return ((peso_usual - peso_atual) / peso_usual) * 100

def estimar_peso_crianca(altura_joelho: float, perimetro_braco: float, sexo: Sexo, raca: Raca) -> Optional[float]:
    """Estimativa de peso para crianças e adolescentes (6-18 anos)"""
    if altura_joelho <= 0 or perimetro_braco <= 0:
        raise ValueError("Medidas devem ser positivas")
    
    if sexo == Sexo.MASCULINO:
        if raca == Raca.BRANCA:
            return altura_joelho * 0.68 + perimetro_braco * 2.64 - 50.08
        elif raca == Raca.NEGRA:
            return altura_joelho * 0.59 + perimetro_braco * 2.73 - 48.32
    elif sexo == Sexo.FEMININO:
        if raca == Raca.BRANCA:
            return altura_joelho * 0.77 + perimetro_braco * 2.47 - 50.16
        elif raca == Raca.NEGRA:
            return altura_joelho * 0.71 + perimetro_braco * 2.59 - 50.43
    return None

def estimar_estatura_tibia(comprimento_tibia: float) -> float:
    """Estimativa da estatura pela medida da tíbia"""
    if comprimento_tibia <= 0:
        raise ValueError("Comprimento da tíbia deve ser positivo")
    return 3.26 * comprimento_tibia + 30.8

def estimar_estatura_ulna(comprimento_ulna: float) -> float:
    """Estimativa da estatura pela medida da ulna"""
    if comprimento_ulna <= 0:
        raise ValueError("Comprimento da ulna deve ser positivo")
    return 5.45 * comprimento_ulna + 20.7

def calcular_idade_corrigida(idade_cronologica_meses: float, idade_gestacional_semanas: float) -> float:
    """Correção de idade para prematuros"""
    if idade_gestacional_semanas < 20 or idade_gestacional_semanas > 42:
        raise ValueError("Idade gestacional deve estar entre 20-42 semanas")
    return idade_cronologica_meses - (40 - idade_gestacional_semanas) / 4.34524

def calcular_percentual_gordura(soma_dobras: float, sexo: Sexo, estagio_tanner: int, raca: Raca) -> float:
    """Estimativa do percentual de gordura corporal"""
    if soma_dobras <= 0:
        raise ValueError("Soma de dobras deve ser positiva")
    
    if estagio_tanner not in [1, 2, 3, 4, 5]:
        raise ValueError("Estágio de Tanner deve ser entre 1 e 5")
    
    if soma_dobras > 35:
        if sexo == Sexo.MASCULINO:
            return 0.783 * soma_dobras + 1.6
        else:
            return 0.546 * soma_dobras + 9.7
    else:
        if sexo == Sexo.MASCULINO:
            if raca == Raca.BRANCA:
                if estagio_tanner in [1, 2]:
                    return 1.21 * soma_dobras - 0.008 * soma_dobras**2 - 1.7
                elif estagio_tanner == 3:
                    return 1.21 * soma_dobras - 0.008 * soma_dobras**2 - 3.4
                elif estagio_tanner in [4, 5]:
                    return 1.21 * soma_dobras - 0.008 * soma_dobras**2 - 5.5
            elif raca == Raca.NEGRA:
                if estagio_tanner in [1, 2]:
                    return 1.21 * soma_dobras - 0.008 * soma_dobras**2 - 3.2
                elif estagio_tanner == 3:
                    return 1.21 * soma_dobras - 0.008 * soma_dobras**2 - 5.2
                elif estagio_tanner in [4, 5]:
                    return 1.21 * soma_dobras - 0.008 * soma_dobras**2 - 6.8
        else:
            return 1.33 * soma_dobras - 0.013 * soma_dobras**2 - 2.5

def calcular_circ_muscular_braco(perimetro_braco: float, dobra_tricipital: float) -> float:
    """Calcula a circunferência muscular do braço (CMB)"""
    if perimetro_braco <= 0 or dobra_tricipital <= 0:
        raise ValueError("Medidas devem ser positivas")
    return perimetro_braco - (0.314 * (dobra_tricipital / 10))

def calcular_area_gorda_braco(circunferencia_braco: float, area_muscular_braco: float) -> float:
    """Calcula a área gorda do braço (AGB)"""
    if circunferencia_braco <= 0 or area_muscular_braco <= 0:
        raise ValueError("Medidas devem ser positivas")
    return 0.79 * ((circunferencia_braco / 3.14) ** 2) - area_muscular_braco

def calcular_area_muscular_braco(circunferencia_braco: float, dobra_tricipital: float) -> float:
    """Calcula a área muscular do braço (AMB)"""
    if circunferencia_braco <= 0 or dobra_tricipital <= 0:
        raise ValueError("Medidas devem ser positivas")
    dobra_cm = dobra_tricipital / 10
    return ((circunferencia_braco - 0.314 * dobra_cm) ** 2) / 12.56

def estimar_estatura_paralisia_cerebral(comprimento_superior: float, comprimento_tibial: float, 
                                       comprimento_joelho: float) -> Dict[str, float]:
    """Estimativa de estatura para crianças com paralisia cerebral (2-12 anos)"""
    medidas = {
        'Estimada_CT': 3.26 * comprimento_tibial + 30.8 + 1.4,
        'Estimada_CS': 4.35 * comprimento_superior + 21.8 + 1.7,
        'Estimada_CJ': 2.69 * comprimento_joelho + 24.2 + 1.1
    }
    return medidas

def estimar_estatura_paralisia_adolescente(idade: float, sexo: Sexo, comprimento_ulna: float) -> float:
    """Estimativa de estatura para adolescentes com paralisia cerebral"""
    sexo_bin = 1 if sexo == Sexo.MASCULINO else 0
    return 30.35 + (1.29 * idade) + (0.77 * sexo_bin) + (4.32 * comprimento_ulna)

def calcular_peso_corrigido_amputacao(peso_atual: float, percentual_amputacao: float) -> float:
    """Calcula o peso corrigido para amputações"""
    if peso_atual <= 0:
        raise ValueError("Peso atual deve ser positivo")
    if percentual_amputacao < 0 or percentual_amputacao >= 100:
        raise ValueError("Percentual de amputação deve estar entre 0-100%")
    return peso_atual * 100 / (100 - percentual_amputacao)

def calcular_gasto_energetico_total(ere: float, fator_atividade: Optional[float] = None, 
                                  fator_estresse: Optional[float] = None) -> float:
    """Calcula o gasto energético total (GET)"""
    if ere <= 0:
        raise ValueError("ERE deve ser positivo")
    
    if fator_atividade and fator_estresse:
        raise ValueError("Use apenas fator de atividade OU fator de estresse")
    
    if fator_atividade:
        return ere * fator_atividade
    elif fator_estresse:
        return ere * fator_estresse
    return ere

def calcular_requerimento_energetico(idade: float, peso: float, estatura: float, 
                                    sexo: Sexo, fator_atividade: float) -> Optional[float]:
    """Calcula o requerimento energético para crianças e adolescentes"""
    if idade < 0 or peso <= 0 or estatura <= 0 or fator_atividade <= 0:
        raise ValueError("Valores devem ser positivos")
    
    if idade <= 0.25:  # 0-3 meses
        return 89 * peso - 100 + 175
    elif idade <= 0.5:  # 4-6 meses
        return 89 * peso - 100 + 56
    elif idade <= 1:    # 7-12 meses
        return 89 * peso - 100 + 22
    elif idade <= 2.92: # 13-35 meses (~3 anos)
        return 89 * peso - 100 + 20
    elif 3 <= idade < 9:
        if sexo == Sexo.MASCULINO:
            return 88.5 - 61.9 * idade + fator_atividade * (26.7 * peso + 903 * estatura) + 20
        else:
            return 135.3 - 30.8 * idade + fator_atividade * (10 * peso + 934 * estatura) + 20
    elif 9 <= idade <= 18:
        if sexo == Sexo.MASCULINO:
            return 88.5 - 61.9 * idade + fator_atividade * (26.7 * peso + 903 * estatura) + 25
        else:
            return 135.3 - 30.8 * idade + fator_atividade * (10 * peso + 934 * estatura) + 25
    return None

def calcular_tmb(peso: float, idade: float, sexo: Sexo) -> Optional[float]:
    """Calcula a taxa metabólica basal (TMB)"""
    if peso <= 0 or idade < 0:
        raise ValueError("Peso e idade devem ser positivos")
    
    if sexo == Sexo.MASCULINO:
        if idade <= 3:
            return 60.9 * peso - 54
        elif idade <= 10:
            return 22.7 * peso + 495
        elif idade <= 18:
            return 17.5 * peso + 651
    else:
        if idade <= 3:
            return 61 * peso - 51
        elif idade <= 10:
            return 22.5 * peso + 499
        elif idade <= 18:
            return 12.2 * peso + 746
    return None

def calcular_necessidade_pc(peso: float, altura: float, sexo: Sexo, 
                           idade: float, fator_estresse: float) -> Optional[float]:
    """Calcula necessidades nutricionais para paralisia cerebral"""
    if peso <= 0 or altura <= 0 or idade < 0 or fator_estresse <= 0:
        raise ValueError("Valores devem ser positivos")
    
    if sexo == Sexo.FEMININO:
        if idade <= 3:
            base = 16.25 * peso + 1023.2 * altura - 413.5
        elif idade <= 10:
            base = 16.97 * peso + 161.8 * altura + 371.2
        elif idade <= 18:
            base = 8.365 * peso + 465 * altura + 200
    else:
        if idade <= 3:
            base = 0.167 * peso + 1517.4 * altura - 617.6
        elif idade <= 10:
            base = 19.6 * peso + 130.3 * altura + 414.9
        elif idade <= 18:
            base = 16.25 * peso + 137.2 * altura + 515.5
    return base * fator_estresse

def necessidade_energetica_pc_5_11(altura: float, nivel_atividade: str) -> float:
    """Necessidade energética para crianças com PC (5-11 anos)"""
    if nivel_atividade == NivelAtividade.LEVE_MODERADA.value:
        return 13.9 * altura
    elif nivel_atividade == NivelAtividade.RESTRITA_INTENSA.value:
        return 10 * altura
    elif nivel_atividade == NivelAtividade.RESTRICAO_GRAVE.value:
        return 11.1 * altura
    return 0

def necessidade_energetica_pc_estaveis(altura: float, condicao_motora: str) -> float:
    """Necessidade energética para crianças/adolescentes com PC estáveis"""
    if condicao_motora == "sem disfunção motora":
        return 15 * altura
    elif condicao_motora == "não deambular (caminhar)":
        return 11 * altura
    elif condicao_motora == "não apresentar disfunção mas deambular":
        return 14 * altura
    return 0

def necessidade_energetica_pc(peso: float, altura: float, idade: float, sexo: Sexo) -> float:
    """Necessidades energéticas em crianças com PC"""
    if sexo == Sexo.MASCULINO:
        return 66.5 + (13.75 * peso) + (5.003 * altura) - (6.775 * idade)
    else:
        return 65.1 + (9.56 * peso) + (1.85 * altura) - (4.676 * idade)

def necessidade_sindrome_down(altura: float, sexo: Sexo) -> float:
    """Necessidade energética para crianças com Síndrome de Down"""
    if sexo == Sexo.MASCULINO:
        return 16.1 * altura
    else:
        return 14.3 * altura

def geb_critica(idade_meses: float, peso: float, temp_c: float) -> float:
    """Gasto Energético Basal para crianças criticamente enfermas"""
    return ((17 * idade_meses) + (48 * peso) + (292 * temp_c) - 9677) * 0.239

def tmb_schofield(peso: float, estatura: float, idade: float, sexo: Sexo) -> Optional[float]:
    """Equação de Schofield para crianças gravemente doentes"""
    if sexo == Sexo.MASCULINO:
        if idade <= 3:
            return 54.48 * peso - 30.33
        elif idade <= 10:
            return 22.7 * peso + 505
        elif idade <= 18:
            return 13.4 * peso + 693
    else:
        if idade <= 3:
            return 58.29 * peso - 31.05
        elif idade <= 10:
            return 20.3 * peso + 486
        elif idade <= 18:
            return 17.7 * peso + 659
    return None

# --- INTERFACE STREAMLIT ---
def main():
    st.set_page_config(
        page_title="Calculadora Nutricional Completa",
        page_icon="🍎",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Configuração de estilo
    st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .sidebar .sidebar-content {
        background-color: #e9ecef;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stAlert {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar com navegação
    with st.sidebar:
        st.title("🍏 Calculadora Nutricional")
        st.markdown("---")
        
        # Menu de navegação
        calculo_selecionado = st.selectbox(
            "Selecione o cálculo:",
            options=[
                "Peso Ajustado",
                "Perda de Peso (%)",
                "Estimativa de Peso (criança/adolescente)",
                "Estimativa de Estatura pela Tíbia",
                "Estimativa de Estatura pela Ulna",
                "Correção de Prematuridade",
                "Percentual de Gordura Corporal",
                "Circunferência Muscular do Braço (CMB)",
                "Área Gorda do Braço (AGB)",
                "Área Muscular do Braço (AMB)",
                "Estatura - Paralisia Cerebral (2-12 anos)",
                "Estatura Adolescente com Paralisia Cerebral",
                "Peso Corrigido para Amputação",
                "Gasto Energético Total (GET)",
                "Requerimento Energético Crianças/Adolescentes",
                "Taxa Metabólica Basal (TMB)",
                "Necessidades Nutricionais Paralisia Cerebral",
                "Necessidade Energética PC 5-11 anos",
                "Necessidade Energética PC Estável",
                "Necessidade Energética PC Geral",
                "Necessidade Energética Síndrome de Down",
                "GEB Criança Criticamente Enferma",
                "TMB Schofield para Crianças Gravemente Doentes"
            ],
            index=0
        )
        
        st.markdown("---")
        st.info("ℹ️ Preencha os campos abaixo para realizar os cálculos")
        
        # Histórico de cálculos
        st.markdown("---")
        st.subheader("📝 Histórico de Cálculos")
        
        if 'historico' not in st.session_state:
            st.session_state.historico = []
        
        if st.button("🧹 Limpar Histórico"):
            st.session_state.historico = []
        
        for item in reversed(st.session_state.historico[-5:]):
            st.sidebar.info(f"{item['tipo']}: {item['resultado']:.2f} ({item['data'].strftime('%d/%m %H:%M')})")
    
    # Página principal
    st.title("🧮 " + calculo_selecionado)
    
    # Container principal
    with st.container():
        try:
            if calculo_selecionado == "Peso Ajustado":
                col1, col2 = st.columns(2)
                with col1:
                    peso_atual = st.number_input("Peso Atual (kg)", min_value=0.1, max_value=300.0, value=70.0, step=0.1)
                with col2:
                    peso_ideal = st.number_input("Peso Ideal (kg)", min_value=0.1, max_value=300.0, value=65.0, step=0.1)
                
                condicao = st.selectbox("Condição", options=[c.value for c in Condicao], 
                                      format_func=lambda x: "Obesidade" if x == "obesidade" else "Desnutrição")
                
                if st.button("Calcular Peso Ajustado", type="primary"):
                    resultado = calcular_peso_ajustado(peso_atual, peso_ideal, Condicao(condicao))
                    st.success(f"**Peso Ajustado:** {resultado:.2f} kg")
                    
                    # Gráfico comparativo
                    dados = pd.DataFrame({
                        "Tipo": ["Atual", "Ideal", "Ajustado"],
                        "Peso (kg)": [peso_atual, peso_ideal, resultado]
                    })
                    
                    fig = px.bar(dados, x="Tipo", y="Peso (kg)", color="Tipo", 
                                title="Comparação de Pesos", text="Peso (kg)")
                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Adicionar ao histórico
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Perda de Peso (%)":
                col1, col2 = st.columns(2)
                with col1:
                    peso_usual = st.number_input("Peso Usual (kg)", min_value=0.1, max_value=300.0, value=70.0, step=0.1)
                with col2:
                    peso_atual = st.number_input("Peso Atual (kg)", min_value=0.1, max_value=300.0, value=65.0, step=0.1)
                
                if st.button("Calcular Perda de Peso", type="primary"):
                    resultado = calcular_perda_peso(peso_usual, peso_atual)
                    
                    # Interpretação do resultado
                    if resultado < 5:
                        classificacao = "Perda insignificante"
                        cor = "green"
                    elif 5 <= resultado < 10:
                        classificacao = "Perda moderada"
                        cor = "orange"
                    else:
                        classificacao = "Perda grave"
                        cor = "red"
                    
                    st.success(f"**Perda Percentual de Peso:** {resultado:.2f}%")
                    st.markdown(f"**Classificação:** <span style='color:{cor}'>{classificacao}</span>", unsafe_allow_html=True)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Estimativa de Peso (criança/adolescente)":
                st.subheader("Estimativa para crianças e adolescentes (6-18 anos)")
                
                col1, col2 = st.columns(2)
                with col1:
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                    raca = st.selectbox("Raça", options=[r.value for r in Raca])
                with col2:
                    altura_joelho = st.number_input("Altura do Joelho (cm)", min_value=10.0, max_value=60.0, value=30.0, step=0.1)
                    perimetro_braco = st.number_input("Perímetro do Braço (cm)", min_value=5.0, max_value=40.0, value=20.0, step=0.1)
                
                if st.button("Calcular Peso Estimado"):
                    resultado = estimar_peso_crianca(
                        altura_joelho, 
                        perimetro_braco, 
                        Sexo(sexo), 
                        Raca(raca)
                    )
                    st.success(f"**Peso Estimado:** {resultado:.2f} kg")
                    
                    # Tabela de referência
                    referencia = pd.DataFrame({
                        'Idade': ['6-8 anos', '9-11 anos', '12-14 anos', '15-18 anos'],
                        'Peso Esperado (kg)': ['20-25', '25-35', '35-50', '50-70']
                    })
                    st.dataframe(referencia, hide_index=True)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Estimativa de Estatura pela Tíbia":
                comprimento_tibia = st.number_input("Comprimento da Tíbia (cm)", 
                                                  min_value=10.0, max_value=50.0, value=30.0, step=0.1)
                
                if st.button("Calcular Estatura"):
                    resultado = estimar_estatura_tibia(comprimento_tibia)
                    st.success(f"**Estatura Estimada:** {resultado:.2f} cm")
                    
                    # Gráfico de crescimento
                    idades = list(range(2, 19))
                    estaturas = [3.26 * (comprimento_tibia * (i/10)) + 30.8 for i in idades]
                    
                    fig = px.line(
                        x=idades, 
                        y=estaturas,
                        title="Projeção de Crescimento",
                        labels={'x': 'Idade (anos)', 'y': 'Estatura (cm)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Estimativa de Estatura pela Ulna":
                comprimento_ulna = st.number_input("Comprimento da Ulna (cm)", 
                                                 min_value=10.0, max_value=40.0, value=25.0, step=0.1)
                
                if st.button("Calcular Estatura pela Ulna"):
                    resultado = estimar_estatura_ulna(comprimento_ulna)
                    st.success(f"**Estatura Estimada:** {resultado:.2f} cm")
                    
                    # Comparação com referência
                    st.info("""
                    **Referências:**
                    - Adulto masculino: 160-190 cm
                    - Adulto feminino: 150-175 cm
                    """)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Correção de Prematuridade":
                col1, col2 = st.columns(2)
                with col1:
                    idade_cronologica = st.number_input("Idade Cronológica (meses)", 
                                                       min_value=0.0, max_value=60.0, value=3.0, step=0.1)
                with col2:
                    idade_gestacional = st.number_input("Idade Gestacional (semanas)", 
                                                      min_value=20.0, max_value=42.0, value=32.0, step=0.1)
                
                if st.button("Calcular Idade Corrigida"):
                    resultado = calcular_idade_corrigida(idade_cronologica, idade_gestacional)
                    st.success(f"**Idade Corrigida:** {resultado:.2f} meses")
                    
                    # Tabela de marcos de desenvolvimento
                    st.info("""
                    **Marcos de Desenvolvimento por Idade:**
                    - 2 meses: Sorriso social
                    - 4 meses: Sustenta cabeça
                    - 6 meses: Senta sem apoio
                    - 9 meses: Engatinha
                    """)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Percentual de Gordura Corporal":
                col1, col2 = st.columns(2)
                with col1:
                    soma_dobras = st.number_input("Soma das Dobras Cutâneas (mm)", 
                                                min_value=5.0, max_value=100.0, value=30.0, step=0.1)
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                with col2:
                    estagio_tanner = st.selectbox("Estágio de Tanner", options=[1, 2, 3, 4, 5])
                    raca = st.selectbox("Raça", options=[r.value for r in Raca])
                
                if st.button("Calcular % Gordura"):
                    resultado = calcular_percentual_gordura(
                        soma_dobras, 
                        Sexo(sexo), 
                        estagio_tanner, 
                        Raca(raca)
                    )
                    
                    # Classificação
                    if sexo == Sexo.MASCULINO.value:
                        if resultado < 8: classificacao = "Muito baixo"
                        elif 8 <= resultado < 15: classificacao = "Normal"
                        elif 15 <= resultado < 20: classificacao = "Moderado"
                        else: classificacao = "Alto"
                    else:
                        if resultado < 15: classificacao = "Muito baixo"
                        elif 15 <= resultado < 25: classificacao = "Normal"
                        elif 25 <= resultado < 30: classificacao = "Moderado"
                        else: classificacao = "Alto"
                    
                    st.success(f"**Percentual de Gordura:** {resultado:.2f}%")
                    st.success(f"**Classificação:** {classificacao}")
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Circunferência Muscular do Braço (CMB)":
                col1, col2 = st.columns(2)
                with col1:
                    perimetro_braco = st.number_input("Perímetro do Braço (cm)", 
                                                    min_value=5.0, max_value=50.0, value=25.0, step=0.1)
                with col2:
                    dobra_tricipital = st.number_input("Dobra Tricipital (mm)", 
                                                     min_value=3.0, max_value=40.0, value=15.0, step=0.1)
                
                if st.button("Calcular CMB"):
                    resultado = calcular_circ_muscular_braco(perimetro_braco, dobra_tricipital)
                    
                    # Avaliação nutricional
                    if resultado < 15:
                        status = "Desnutrição grave"
                    elif 15 <= resultado < 20:
                        status = "Desnutrição moderada"
                    elif 20 <= resultado < 25:
                        status = "Normal"
                    else:
                        status = "Adequado"
                    
                    st.success(f"**Circunferência Muscular do Braço:** {resultado:.2f} cm")
                    st.success(f"**Avaliação:** {status}")
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Área Gorda do Braço (AGB)":
                col1, col2 = st.columns(2)
                with col1:
                    circunferencia_braco = st.number_input("Circunferência do Braço (cm)", 
                                                         min_value=5.0, max_value=50.0, value=25.0, step=0.1)
                with col2:
                    area_muscular = st.number_input("Área Muscular do Braço (cm²)", 
                                                  min_value=5.0, max_value=100.0, value=30.0, step=0.1)
                
                if st.button("Calcular AGB"):
                    resultado = calcular_area_gorda_braco(circunferencia_braco, area_muscular)
                    st.success(f"**Área Gorda do Braço:** {resultado:.2f} cm²")
                    
                    # Gráfico de composição
                    composicao = pd.DataFrame({
                        'Componente': ['Área Muscular', 'Área Gorda'],
                        'Valor (cm²)': [area_muscular, resultado]
                    })
                    
                    fig = px.pie(composicao, values='Valor (cm²)', names='Componente',
                                title="Composição do Braço")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Área Muscular do Braço (AMB)":
                col1, col2 = st.columns(2)
                with col1:
                    circunferencia_braco = st.number_input("Circunferência do Braço (cm)", 
                                                         min_value=5.0, max_value=50.0, value=25.0, step=0.1)
                with col2:
                    dobra_tricipital = st.number_input("Dobra Tricipital (mm)", 
                                                     min_value=3.0, max_value=40.0, value=15.0, step=0.1)
                
                if st.button("Calcular AMB"):
                    resultado = calcular_area_muscular_braco(circunferencia_braco, dobra_tricipital)
                    
                    # Classificação por percentis
                    percentil = min(int((resultado / 50) * 100), 100)
                    
                    st.success(f"**Área Muscular do Braço:** {resultado:.2f} cm²")
                    st.success(f"**Percentil Estimado:** {percentil}º")
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Estatura - Paralisia Cerebral (2-12 anos)":
                st.info("Para crianças com paralisia cerebral de 2 a 12 anos")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    comprimento_superior = st.number_input("Comprimento Superior (cm)", 
                                                          min_value=5.0, max_value=40.0, value=20.0, step=0.1)
                with col2:
                    comprimento_tibial = st.number_input("Comprimento Tibial (cm)", 
                                                        min_value=5.0, max_value=40.0, value=20.0, step=0.1)
                with col3:
                    comprimento_joelho = st.number_input("Comprimento do Joelho (cm)", 
                                                        min_value=5.0, max_value=30.0, value=15.0, step=0.1)
                
                if st.button("Calcular Estatura"):
                    resultados = estimar_estatura_paralisia_cerebral(
                        comprimento_superior,
                        comprimento_tibial,
                        comprimento_joelho
                    )
                    
                    st.success(f"""
                    **Estimativas:**
                    - Por comprimento superior: {resultados['Estimada_CS']:.1f} cm
                    - Por comprimento tibial: {resultados['Estimada_CT']:.1f} cm
                    - Por comprimento do joelho: {resultados['Estimada_CJ']:.1f} cm
                    """)
                    
                    # Média das estimativas
                    media = sum(resultados.values()) / len(resultados)
                    st.success(f"**Média das Estimativas:** {media:.1f} cm")
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': media,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Estatura Adolescente com Paralisia Cerebral":
                col1, col2 = st.columns(2)
                with col1:
                    idade = st.number_input("Idade (anos)", min_value=2.0, max_value=30.0, value=15.0, step=0.1)
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                with col2:
                    comprimento_ulna = st.number_input("Comprimento da Ulna (cm)", 
                                                     min_value=10.0, max_value=40.0, value=25.0, step=0.1)
                
                if st.button("Calcular Estatura"):
                    resultado = estimar_estatura_paralisia_adolescente(
                        idade,
                        Sexo(sexo),
                        comprimento_ulna
                    )
                    
                    st.success(f"**Estatura Estimada:** {resultado:.1f} cm")
                    
                    # Curva de crescimento
                    idades = list(range(2, 19))
                    estaturas = [30.35 + (1.29 * i) + (0.77 * (1 if sexo == Sexo.MASCULINO.value else 0)) + (4.32 * comprimento_ulna) for i in idades]
                    
                    fig = px.line(
                        x=idades, 
                        y=estaturas,
                        title="Projeção de Crescimento",
                        labels={'x': 'Idade (anos)', 'y': 'Estatura (cm)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Peso Corrigido para Amputação":
                st.subheader("Correção de Peso para Pacientes Amputados")
                
                col1, col2 = st.columns(2)
                with col1:
                    peso_atual = st.number_input("Peso Atual (kg)", 
                                               min_value=10.0, max_value=300.0, value=70.0, step=0.1)
                with col2:
                    membro_amputado = st.selectbox("Membro Amputado", 
                                                 ["Braço", "Antebraço", "Mão", "Coxa", "Perna", "Pé"])
                
                # Tabela de proporções padrão
                proporcoes = {
                    "Braço": 2.7,
                    "Antebraço": 1.6,
                    "Mão": 0.7,
                    "Coxa": 10.1,
                    "Perna": 4.4,
                    "Pé": 1.5
                }
                
                if st.button("Calcular Peso Corrigido"):
                    percentual = proporcoes[membro_amputado]
                    resultado = calcular_peso_corrigido_amputacao(peso_atual, percentual)
                    
                    st.success(f"**Peso Corrigido Estimado:** {resultado:.2f} kg")
                    st.info(f"**Percentual considerado:** {percentual}% ({membro_amputado})")
                    
                    # Gráfico comparativo
                    dados = pd.DataFrame({
                        "Tipo": ["Atual", "Corrigido"],
                        "Peso (kg)": [peso_atual, resultado]
                    })
                    
                    fig = px.bar(dados, x="Tipo", y="Peso (kg)", color="Tipo",
                                title="Comparação de Pesos", text="Peso (kg)")
                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Gasto Energético Total (GET)":
                st.subheader("Cálculo do Gasto Energético Total")
                
                ere = st.number_input("Taxa Metabólica Basal (kcal)", 
                                    min_value=500.0, max_value=5000.0, value=1500.0, step=10.0)
                
                st.markdown("**Fatores Adicionais (preencher apenas um)**")
                col1, col2 = st.columns(2)
                with col1:
                    fator_atividade = st.number_input("Fator de Atividade Física", 
                                                    min_value=1.0, max_value=2.5, value=1.2, step=0.1)
                with col2:
                    fator_estresse = st.number_input("Fator de Estresse", 
                                                   min_value=1.0, max_value=2.5, value=1.0, step=0.1)
                
                if st.button("Calcular GET"):
                    # Verifica qual fator usar
                    usar_atividade = fator_atividade > 1.0
                    usar_estresse = fator_estresse > 1.0
                    
                    if usar_atividade and usar_estresse:
                        st.warning("Preencha apenas um fator adicional (atividade OU estresse)")
                    else:
                        if usar_atividade:
                            resultado = calcular_gasto_energetico_total(ere, fator_atividade=fator_atividade)
                            tipo = "Atividade Física"
                            valor = fator_atividade
                        elif usar_estresse:
                            resultado = calcular_gasto_energetico_total(ere, fator_estresse=fator_estresse)
                            tipo = "Estresse"
                            valor = fator_estresse
                        else:
                            resultado = calcular_gasto_energetico_total(ere)
                            tipo = "Basal"
                            valor = 1.0
                        
                        st.success(f"**Gasto Energético Total:** {resultado:.2f} kcal")
                        st.info(f"**Fator aplicado:** {tipo} (x{valor:.2f})")
                        
                        st.session_state.historico.append({
                            'tipo': calculo_selecionado,
                            'resultado': resultado,
                            'data': datetime.now()
                        })

            elif calculo_selecionado == "Requerimento Energético Crianças/Adolescentes":
                st.subheader("Cálculo para Crianças e Adolescentes")
                
                col1, col2 = st.columns(2)
                with col1:
                    idade = st.number_input("Idade (anos)", min_value=0.0, max_value=18.0, value=5.0, step=0.1)
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=150.0, value=20.0, step=0.1)
                with col2:
                    estatura = st.number_input("Estatura (metros)", min_value=0.3, max_value=2.5, value=1.1, step=0.01)
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                    fator_atividade = st.number_input("Fator de Atividade", min_value=1.0, max_value=2.0, value=1.2, step=0.1)
                
                if st.button("Calcular Requerimento"):
                    resultado = calcular_requerimento_energetico(
                        idade, peso, estatura, Sexo(sexo), fator_atividade
                    )
                    
                    if resultado is None:
                        st.error("Idade fora da faixa suportada (0-18 anos)")
                    else:
                        st.success(f"**Requerimento Energético Estimado:** {resultado:.2f} kcal/dia")
                        
                        # Recomendações por faixa etária
                        st.info("""
                        **Referências Diárias:**
                        - 1-3 anos: 1,000-1,400 kcal
                        - 4-8 anos: 1,200-2,000 kcal
                        - 9-13 anos: 1,600-2,600 kcal
                        - 14-18 anos: 1,800-3,200 kcal
                        """)
                        
                        st.session_state.historico.append({
                            'tipo': calculo_selecionado,
                            'resultado': resultado,
                            'data': datetime.now()
                        })

            elif calculo_selecionado == "Taxa Metabólica Basal (TMB)":
                st.subheader("Cálculo da Taxa Metabólica Basal")
                
                col1, col2 = st.columns(2)
                with col1:
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.1)
                    idade = st.number_input("Idade (anos)", min_value=0.0, max_value=120.0, value=30.0, step=0.1)
                with col2:
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                
                if st.button("Calcular TMB"):
                    resultado = calcular_tmb(peso, idade, Sexo(sexo))
                    
                    if resultado is None:
                        st.error("Idade fora da faixa suportada (0-18 anos)")
                    else:
                        st.success(f"**Taxa Metabólica Basal:** {resultado:.2f} kcal/dia")
                        
                        # Comparação com Harris-Benedict para adultos
                        if idade > 18:
                            if Sexo(sexo) == Sexo.MASCULINO:
                                hb = 88.362 + (13.397 * peso) + (4.799 * 170) - (5.677 * idade)
                            else:
                                hb = 447.593 + (9.247 * peso) + (3.098 * 160) - (4.330 * idade)
                            
                            st.info(f"**Harris-Benedict estimado:** {hb:.2f} kcal/dia (para adulto)")
                        
                        st.session_state.historico.append({
                            'tipo': calculo_selecionado,
                            'resultado': resultado,
                            'data': datetime.now()
                        })

            elif calculo_selecionado == "Necessidades Nutricionais Paralisia Cerebral":
                st.subheader("Para Crianças com Paralisia Cerebral")
                
                col1, col2 = st.columns(2)
                with col1:
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=100.0, value=15.0, step=0.1)
                    altura = st.number_input("Altura (metros)", min_value=0.3, max_value=2.0, value=1.0, step=0.01)
                with col2:
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                    idade = st.number_input("Idade (anos)", min_value=0.0, max_value=18.0, value=5.0, step=0.1)
                    fator_estresse = st.number_input("Fator de Estresse", min_value=1.0, max_value=2.5, value=1.2, step=0.1)
                
                if st.button("Calcular Necessidades"):
                    resultado = calcular_necessidade_pc(
                        peso, altura, Sexo(sexo), idade, fator_estresse
                    )
                    
                    st.success(f"**Necessidade Energética Estimada:** {resultado:.2f} kcal/dia")
                    
                    # Recomendações por nível de atividade
                    st.info("""
                    **Referências:**
                    - PC leve: 13-15 kcal/cm altura
                    - PC moderada: 10-12 kcal/cm altura
                    - PC grave: 8-10 kcal/cm altura
                    """)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Necessidade Energética PC 5-11 anos":
                st.subheader("Para Crianças com PC (5-11 anos)")
                
                altura = st.number_input("Altura (cm)", min_value=50.0, max_value=200.0, value=120.0, step=0.1)
                nivel = st.selectbox("Nível de Atividade", 
                                   options=[n.value for n in NivelAtividade])
                
                if st.button("Calcular Necessidade"):
                    resultado = necessidade_energetica_pc_5_11(altura, nivel)
                    
                    st.success(f"**Necessidade Energética Estimada:** {resultado:.2f} kcal/dia")
                    
                    # Tabela de referência
                    referencia = pd.DataFrame({
                        'Nível de Atividade': [n.value for n in NivelAtividade],
                        'Fórmula': ['13.9 x altura', '10 x altura', '11.1 x altura']
                    })
                    st.dataframe(referencia, hide_index=True)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Necessidade Energética PC Estável":
                st.subheader("Para Crianças/Adolescentes com PC Estáveis")
                
                altura = st.number_input("Altura (cm)", min_value=50.0, max_value=200.0, value=120.0, step=0.1)
                condicao = st.selectbox("Condição Motora", 
                                      ["sem disfunção motora", 
                                       "não apresentar disfunção mas deambular", 
                                       "não deambular (caminhar)"])
                
                if st.button("Calcular Necessidade"):
                    resultado = necessidade_energetica_pc_estaveis(altura, condicao)
                    
                    st.success(f"**Necessidade Energética Estimada:** {resultado:.2f} kcal/dia")
                    
                    # Gráfico comparativo
                    condicoes = ["sem disfunção motora", "não apresentar disfunção mas deambular", "não deambular (caminhar)"]
                    valores = [15*altura, 14*altura, 11*altura]
                    
                    fig = px.bar(x=condicoes, y=valores, 
                                labels={'x': 'Condição Motora', 'y': 'kcal/dia'},
                                title="Comparação por Condição Motora")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Necessidade Energética PC Geral":
                st.subheader("Para Crianças com Paralisia Cerebral")
                
                col1, col2 = st.columns(2)
                with col1:
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=100.0, value=15.0, step=0.1)
                    altura = st.number_input("Altura (cm)", min_value=50.0, max_value=200.0, value=120.0, step=0.1)
                with col2:
                    idade = st.number_input("Idade (anos)", min_value=0.0, max_value=18.0, value=5.0, step=0.1)
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                
                if st.button("Calcular Necessidade"):
                    resultado = necessidade_energetica_pc(peso, altura, idade, Sexo(sexo))
                    
                    st.success(f"**Necessidade Energética Estimada:** {resultado:.2f} kcal/dia")
                    
                    # Fórmula exibida
                    if Sexo(sexo) == Sexo.MASCULINO:
                        formula = "66.5 + (13.75 × Peso) + (5.003 × Altura) - (6.775 × Idade)"
                    else:
                        formula = "65.1 + (9.56 × Peso) + (1.85 × Altura) - (4.676 × Idade)"
                    
                    st.info(f"**Fórmula utilizada:** {formula}")
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "Necessidade Energética Síndrome de Down":
                st.subheader("Para Crianças com Síndrome de Down (5-12 anos)")
                
                altura = st.number_input("Altura (cm)", min_value=50.0, max_value=200.0, value=120.0, step=0.1)
                sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                
                if st.button("Calcular Necessidade"):
                    resultado = necessidade_sindrome_down(altura, Sexo(sexo))
                    
                    st.success(f"**Necessidade Energética Estimada:** {resultado:.2f} kcal/dia")
                    
                    # Comparação com crianças típicas
                    if Sexo(sexo) == Sexo.MASCULINO:
                        tipico = 16.1 * altura * 1.15  # +15% para crianças típicas
                    else:
                        tipico = 14.3 * altura * 1.15
                    
                    st.info(f"**Comparação com criança típica:** ~{tipico:.2f} kcal/dia (+15%)")
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "GEB Criança Criticamente Enferma":
                st.subheader("Gasto Energético Basal para Crianças Enfermas")
                
                col1, col2 = st.columns(2)
                with col1:
                    idade_meses = st.number_input("Idade (meses)", min_value=0.0, max_value=240.0, value=12.0, step=0.1)
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=100.0, value=10.0, step=0.1)
                with col2:
                    temp_c = st.number_input("Temperatura (°C)", min_value=30.0, max_value=45.0, value=37.0, step=0.1)
                
                if st.button("Calcular GEB"):
                    resultado = geb_critica(idade_meses, peso, temp_c)
                    
                    st.success(f"**Gasto Energético Basal Estimado:** {resultado:.2f} kcal/dia")
                    
                    # Fórmula exibida
                    st.info("""
                    **Fórmula utilizada:**
                    [(17 × idade em meses) + (48 × peso em kg) + (292 × temperatura em °C) - 9677] × 0.239
                    """)
                    
                    st.session_state.historico.append({
                        'tipo': calculo_selecionado,
                        'resultado': resultado,
                        'data': datetime.now()
                    })

            elif calculo_selecionado == "TMB Schofield para Crianças Gravemente Doentes":
                st.subheader("TMB pela Equação de Schofield")
                
                col1, col2 = st.columns(2)
                with col1:
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=150.0, value=15.0, step=0.1)
                    estatura = st.number_input("Estatura (cm)", min_value=30.0, max_value=200.0, value=100.0, step=0.1)
                with col2:
                    idade = st.number_input("Idade (anos)", min_value=0.0, max_value=18.0, value=5.0, step=0.1)
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                
                if st.button("Calcular TMB Schofield"):
                    resultado = tmb_schofield(peso, estatura/100, idade, Sexo(sexo))
                    
                    if resultado is None:
                        st.error("Idade fora da faixa suportada (0-18 anos)")
                    else:
                        st.success(f"**Taxa Metabólica Basal (Schofield):** {resultado:.2f} kcal/dia")
                        
                        # Comparação com TMB normal
                        tmb_normal = calcular_tmb(peso, idade, Sexo(sexo))
                        if tmb_normal:
                            diferenca = resultado - tmb_normal
                            percentual = (diferenca / tmb_normal) * 100
                            st.info(f"**Comparação com TMB padrão:** {tmb_normal:.2f} kcal/dia ({diferenca:+.2f} kcal, {percentual:+.2f}%)")
                        
                        st.session_state.historico.append({
                            'tipo': calculo_selecionado,
                            'resultado': resultado,
                            'data': datetime.now()
                        })

        except ValueError as e:
            st.error(f"Erro nos dados de entrada: {str(e)}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {str(e)}")
    
    # Rodapé
    st.markdown("---")
    st.caption("© 2025 Calculadora Nutricional - Desenvolvido para profissionais de saúde")

if __name__ == "__main__":
    main()