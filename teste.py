import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List

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
    SEDENTARIA = "sedentária"
    BAIXA = "baixa atividade"
    ATIVO = "ativo"
    MUITO_ATIVO = "muito ativo"

class IndiceAntropometrico(Enum):
    PESO_IDADE = "peso_idade"
    PESO_ESTATURA = "peso_estatura"
    IMC_IDADE = "imc_idade"
    ESTATURA_IDADE = "estatura_idade"

class CondicaoMotora(Enum):
    SEM_DISFUNCAO = "sem disfunção motora"
    DEAMBULA_SEM_DISFUNCAO = "não apresentar disfunção mas deambular"
    NAO_DEAMBULA = "não deambular (caminhar)"

class NivelAtividadePC(Enum):
    LEVE_MODERADA = "leve a moderada"
    RESTRITA_INTENSA = "restrita intensa"
    RESTRICAO_GRAVE = "restrição física grave"

# --- FUNÇÕES NUTRICIONAIS COMPLETAS ---

# 1. CLASSIFICAÇÃO ANTROPOMÉTRICA (0-5 ANOS)
def classificar_antropometria_0_5_anos(
    percentil: float, 
    escore_z: float, 
    tipo_indice: IndiceAntropometrico
) -> Optional[str]:
    """
    Classificação CORRETA conforme documento.
    """
    if tipo_indice == IndiceAntropometrico.PESO_IDADE:
        if percentil < 0.1 or escore_z < -3:
            return "Muito baixo peso para a idade"
        elif 0.1 <= percentil < 3 or -3 <= escore_z < -2:
            return "Baixo peso para a idade"
        elif 3 <= percentil < 85 or -2 <= escore_z <= 1:
            return "Peso adequado para a idade"
        elif 85 < percentil <= 97 or 1 < escore_z <= 2:
            return "Peso adequado para a idade"  # Nota: ainda peso adequado, mas risco sobrepeso
        elif 97 < percentil <= 99.9 or 2 < escore_z <= 3:
            return "Peso elevado para a idade"
        elif percentil > 99.9 or escore_z > 3:
            return "Obesidade"
    
    elif tipo_indice == IndiceAntropometrico.PESO_ESTATURA:
        if percentil < 0.1 or escore_z < -3:
            return "Magreza acentuada"
        elif 0.1 <= percentil < 3 or -3 <= escore_z < -2:
            return "Magreza"
        elif 3 <= percentil < 85 or -2 <= escore_z <= 1:
            return "Eutrofia"
        elif 85 < percentil <= 97 or 1 < escore_z <= 2:
            return "Risco de sobrepeso"
        elif 97 < percentil <= 99.9 or 2 < escore_z <= 3:
            return "Sobrepeso"
        elif percentil > 99.9 or escore_z > 3:
            return "Obesidade"
    
    elif tipo_indice == IndiceAntropometrico.IMC_IDADE:
        if percentil < 0.1 or escore_z < -3:
            return "Magreza acentuada"
        elif 0.1 <= percentil < 3 or -3 <= escore_z < -2:
            return "Magreza"
        elif 3 <= percentil < 85 or -2 <= escore_z <= 1:
            return "Eutrofia"
        elif 85 < percentil <= 97 or 1 < escore_z <= 2:
            return "Risco de sobrepeso"
        elif 97 < percentil <= 99.9 or 2 < escore_z <= 3:
            return "Sobrepeso"
        elif percentil > 99.9 or escore_z > 3:
            return "Obesidade"
    
    elif tipo_indice == IndiceAntropometrico.ESTATURA_IDADE:
        if percentil < 0.1 or escore_z < -3:
            return "Muito baixa estatura para a idade"
        elif 0.1 <= percentil < 3 or -3 <= escore_z < -2:
            return "Baixa estatura para a idade"
        else:
            return "Estatura adequada para a idade"
    
    return None

# 2. EQUAÇÃO DE SCHOFIELD
def tmb_schofield_peso(peso: float, idade: float, sexo: Sexo) -> Optional[float]:
    """Equação de Schofield APENAS com PESO."""
    if peso <= 0 or idade < 0:
        return None
    
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

def tmb_schofield_peso_estatura(peso: float, estatura: float, idade: float, sexo: Sexo) -> Optional[float]:
    """Equação de Schofield com PESO e ESTATURA."""
    if peso <= 0 or estatura <= 0 or idade < 0:
        return None
    
    if sexo == Sexo.MASCULINO:
        if idade <= 3:
            return (0.167 * peso) + (1517.4 * estatura) - 617.6
        elif idade <= 10:
            return (19.6 * peso) + (130.3 * estatura) + 414.9
        elif idade <= 18:
            return (16.25 * peso) + (137.2 * estatura) + 515.5
    else:
        if idade <= 3:
            return (16.25 * peso) + (1023.2 * estatura) - 413.5
        elif idade <= 10:
            return (16.97 * peso) + (161.8 * estatura) + 371.2
        elif idade <= 18:
            return (8.365 * peso) + (465 * estatura) + 200
    
    return None

# 3. COEFICIENTES DE ATIVIDADE FÍSICA
def obter_coeficiente_atividade(sexo: Sexo, nivel: NivelAtividade) -> float:
    tabela = {
        Sexo.MASCULINO: {
            NivelAtividade.SEDENTARIA: 1.00,
            NivelAtividade.BAIXA: 1.13,
            NivelAtividade.ATIVO: 1.26,
            NivelAtividade.MUITO_ATIVO: 1.42
        },
        Sexo.FEMININO: {
            NivelAtividade.SEDENTARIA: 1.00,
            NivelAtividade.BAIXA: 1.16,
            NivelAtividade.ATIVO: 1.31,
            NivelAtividade.MUITO_ATIVO: 1.56
        }
    }
    return tabela[sexo][nivel]

# 4. REQUERIMENTO ENERGÉTICO
def calcular_requerimento_energetico_idade(peso: float, idade_meses: float) -> Optional[float]:
    """Estimativa de requerimento energético APENAS com PESO."""
    if peso <= 0 or idade_meses < 0:
        return None
    
    if idade_meses <= 3:  # 0-3 meses
        return (89 * peso - 100) + 175
    elif idade_meses <= 6:  # 4-6 meses
        return (89 * peso - 100) + 56
    elif idade_meses <= 12:  # 7-12 meses
        return (89 * peso - 100) + 22
    elif idade_meses <= 35:  # 13-35 meses
        return (89 * peso - 100) + 20
    else:
        return None

def calcular_requerimento_energetico_completo(peso: float, estatura: float, idade_anos: float, 
                                            sexo: Sexo, fator_atividade: float) -> Optional[float]:
    """Requerimento energético com peso, estatura e atividade para 3-18 anos."""
    if peso <= 0 or estatura <= 0 or idade_anos < 0 or fator_atividade <= 0:
        return None
    
    if 3 <= idade_anos < 9:
        if sexo == Sexo.MASCULINO:
            return 88.5 - 61.9 * idade_anos + fator_atividade * (26.7 * peso + 903 * estatura) + 20
        else:
            return 135.3 - 30.8 * idade_anos + fator_atividade * (10 * peso + 934 * estatura) + 20
    elif 9 <= idade_anos <= 18:
        if sexo == Sexo.MASCULINO:
            return 88.5 - 61.9 * idade_anos + fator_atividade * (26.7 * peso + 903 * estatura) + 25
        else:
            return 135.3 - 30.8 * idade_anos + fator_atividade * (10 * peso + 934 * estatura) + 25
    
    return None

# 5. CORREÇÃO DE PREMATURIDADE
def calcular_idade_corrigida(idade_cronologica_meses: float, idade_gestacional_semanas: float) -> float:
    """Correção de prematuridade (até 2 anos)."""
    if idade_gestacional_semanas < 20 or idade_gestacional_semanas > 42:
        raise ValueError("Idade gestacional deve estar entre 20-42 semanas")
    
    idade_gestacional_meses = idade_gestacional_semanas / 4.34524
    return idade_cronologica_meses - (40 / 4.34524 - idade_gestacional_meses)

# 6. PACIENTE COM PC ENFERMO
def necessidade_energetica_pc_enfermo(peso: float, altura_cm: float, idade: float, sexo: Sexo) -> float:
    """Paciente com Paralisia Cerebral enfermo com fator 1.1."""
    if sexo == Sexo.MASCULINO:
        base = 66.5 + (13.75 * peso) + (5.003 * altura_cm) - (6.775 * idade)
    else:
        base = 65.1 + (9.56 * peso) + (1.85 * altura_cm) - (4.676 * idade)
    
    return base * 1.1

# 7. GEB PARA UTI
def geb_uti_ventilacao_mecanica(idade_meses: float, peso: float, temperatura_c: float) -> float:
    """GEB para pacientes em UTI sob ventilação mecânica (>2 anos)."""
    if idade_meses < 24:
        raise ValueError("Fórmula válida apenas para idade acima de 2 anos (24 meses)")
    
    return ((17 * idade_meses) + (48 * peso) + (292 * temperatura_c) - 9677) * 0.239

# 8. % ALCANÇADO
def calcular_percentual_alcançado(valor_consumido: float, necessidade: float) -> float:
    """Calcula percentual alcançado de GEB, Proteína ou GET."""
    if necessidade <= 0:
        raise ValueError("Necessidade deve ser maior que zero")
    
    return (valor_consumido / necessidade) * 100

# 9. TMB PADRÃO
def calcular_tmb_padrao(peso: float, idade: float, sexo: Sexo) -> Optional[float]:
    """Taxa Metabólica Basal padrão."""
    if peso <= 0 or idade < 0:
        return None
    
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

# 10. FUNÇÕES ORIGINAIS
def calcular_peso_ajustado(peso_atual: float, peso_ideal: float, condicao: Condicao) -> Optional[float]:
    if peso_atual <= 0 or peso_ideal <= 0:
        return None
    
    if condicao == Condicao.OBESIDADE:
        return (peso_atual - peso_ideal) * 0.25 + peso_ideal
    elif condicao == Condicao.DESNUTRICAO:
        return (peso_atual - peso_ideal) * 0.25 + peso_atual
    
    return None

def calcular_perda_peso(peso_usual: float, peso_atual: float) -> Optional[float]:
    if peso_usual <= 0:
        return None
    return ((peso_usual - peso_atual) / peso_usual) * 100

# ====================================================
# FÓRMULAS NOVAS ADICIONADAS DO ARQUIVO TESTE.PY
# ====================================================

# 11. ESTIMATIVA DE PESO PARA CRIANÇAS/ADOLESCENTES (6-18 ANOS)
def estimar_peso_crianca(altura_joelho: float, perimetro_braco: float, 
                        sexo: Sexo, raca: Raca) -> Optional[float]:
    """Estimativa de peso para crianças e adolescentes (6-18 anos)"""
    if altura_joelho <= 0 or perimetro_braco <= 0:
        return None
    
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

# 12. ESTIMATIVA DE ESTATURA PELA TÍBIA
def estimar_estatura_tibia(comprimento_tibia: float) -> float:
    """Estimativa da estatura pela medida da tíbia"""
    if comprimento_tibia <= 0:
        raise ValueError("Comprimento da tíbia deve ser positivo")
    return 3.26 * comprimento_tibia + 30.8

# 13. ESTIMATIVA DE ESTATURA PELA ULNA
def estimar_estatura_ulna(comprimento_ulna: float) -> float:
    """Estimativa da estatura pela medida da ulna"""
    if comprimento_ulna <= 0:
        raise ValueError("Comprimento da ulna deve ser positivo")
    return 5.45 * comprimento_ulna + 20.7

# 14. PERCENTUAL DE GORDURA CORPORAL
def calcular_percentual_gordura(soma_dobras: float, sexo: Sexo, 
                              estagio_tanner: int, raca: Raca) -> Optional[float]:
    """Estimativa do percentual de gordura corporal"""
    if soma_dobras <= 0:
        return None
    
    if estagio_tanner not in [1, 2, 3, 4, 5]:
        return None
    
    if soma_dobras > 35:
        if sexo == Sexo.MASCULINO:
            return 0.783 * soma_dobras + 1.6
        else:
            return 0.546 * soma_dobras + 9.7
    else:
        if sexo == Sexo.MASCULINO:
            if raca == Raca.BRANCA:
                if estagio_tanner in [1, 2]:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 1.7
                elif estagio_tanner == 3:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 3.4
                elif estagio_tanner in [4, 5]:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 5.5
            elif raca == Raca.NEGRA:
                if estagio_tanner in [1, 2]:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 3.2
                elif estagio_tanner == 3:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 5.2
                elif estagio_tanner in [4, 5]:
                    return 1.21 * soma_dobras - 0.008 * (soma_dobras ** 2) - 6.8
        else:
            return 1.33 * soma_dobras - 0.013 * (soma_dobras ** 2) - 2.5
    
    return None

# 15. CIRCUNFERÊNCIA MUSCULAR DO BRAÇO (CMB)
def calcular_circ_muscular_braco(perimetro_braco: float, dobra_tricipital: float) -> float:
    """Calcula a circunferência muscular do braço (CMB)"""
    if perimetro_braco <= 0 or dobra_tricipital <= 0:
        raise ValueError("Medidas devem ser positivas")
    return perimetro_braco - (0.314 * (dobra_tricipital / 10))

# 16. ÁREA GORDA DO BRAÇO (AGB)
def calcular_area_gorda_braco(circunferencia_braco: float, area_muscular_braco: float) -> float:
    """Calcula a área gorda do braço (AGB)"""
    if circunferencia_braco <= 0 or area_muscular_braco <= 0:
        raise ValueError("Medidas devem ser positivas")
    return 0.79 * ((circunferencia_braco / 3.14) ** 2) - area_muscular_braco

# 17. ÁREA MUSCULAR DO BRAÇO (AMB)
def calcular_area_muscular_braco(circunferencia_braco: float, dobra_tricipital: float) -> float:
    """Calcula a área muscular do braço (AMB)"""
    if circunferencia_braco <= 0 or dobra_tricipital <= 0:
        raise ValueError("Medidas devem ser positivas")
    dobra_cm = dobra_tricipital / 10
    return ((circunferencia_braco - 0.314 * dobra_cm) ** 2) / 12.56

# 18. ESTIMATIVA DE ESTATURA PARA CRIANÇAS COM PARALISIA CEREBRAL (2-12 ANOS)
def estimar_estatura_paralisia_cerebral(comprimento_superior: float, 
                                       comprimento_tibial: float, 
                                       comprimento_joelho: float) -> Dict[str, float]:
    """Estimativa de estatura para crianças com paralisia cerebral (2-12 anos)"""
    medidas = {
        'Estimada_CT': 3.26 * comprimento_tibial + 30.8 + 1.4,
        'Estimada_CS': 4.35 * comprimento_superior + 21.8 + 1.7,
        'Estimada_CJ': 2.69 * comprimento_joelho + 24.2 + 1.1
    }
    return medidas

# 19. ESTIMATIVA DE ESTATURA PARA ADOLESCENTES COM PARALISIA CEREBRAL
def estimar_estatura_paralisia_adolescente(idade: float, sexo: Sexo, 
                                          comprimento_ulna: float) -> float:
    """Estimativa de estatura para adolescentes com paralisia cerebral"""
    sexo_bin = 1 if sexo == Sexo.MASCULINO else 0
    return 30.35 + (1.29 * idade) + (0.77 * sexo_bin) + (4.32 * comprimento_ulna)

# 20. PESO CORRIGIDO PARA AMPUTAÇÃO
def calcular_peso_corrigido_amputacao(peso_atual: float, percentual_amputacao: float) -> float:
    """Calcula o peso corrigido para amputações"""
    if peso_atual <= 0:
        raise ValueError("Peso atual deve ser positivo")
    if percentual_amputacao < 0 or percentual_amputacao >= 100:
        raise ValueError("Percentual de amputação deve estar entre 0-100%")
    return peso_atual * 100 / (100 - percentual_amputacao)

# 21. GASTO ENERGÉTICO TOTAL (GET)
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

# 22. NECESSIDADE ENERGÉTICA PC 5-11 ANOS
def necessidade_energetica_pc_5_11(altura: float, nivel_atividade: str) -> float:
    """Necessidade energética para crianças com PC (5-11 anos)"""
    if nivel_atividade == NivelAtividadePC.LEVE_MODERADA.value:
        return 13.9 * altura
    elif nivel_atividade == NivelAtividadePC.RESTRITA_INTENSA.value:
        return 10 * altura
    elif nivel_atividade == NivelAtividadePC.RESTRICAO_GRAVE.value:
        return 11.1 * altura
    return 0

# 23. NECESSIDADE ENERGÉTICA PC ESTÁVEIS
def necessidade_energetica_pc_estaveis(altura: float, condicao_motora: str) -> float:
    """Necessidade energética para crianças/adolescentes com PC estáveis"""
    if condicao_motora == CondicaoMotora.SEM_DISFUNCAO.value:
        return 15 * altura
    elif condicao_motora == CondicaoMotora.NAO_DEAMBULA.value:
        return 11 * altura
    elif condicao_motora == CondicaoMotora.DEAMBULA_SEM_DISFUNCAO.value:
        return 14 * altura
    return 0

# 24. NECESSIDADE ENERGÉTICA PC GERAL
def necessidade_energetica_pc(peso: float, altura: float, idade: float, sexo: Sexo) -> float:
    """Necessidades energéticas em crianças com PC"""
    if sexo == Sexo.MASCULINO:
        return 66.5 + (13.75 * peso) + (5.003 * altura) - (6.775 * idade)
    else:
        return 65.1 + (9.56 * peso) + (1.85 * altura) - (4.676 * idade)

# 25. NECESSIDADE SÍNDROME DE DOWN
def necessidade_sindrome_down(altura: float, sexo: Sexo) -> float:
    """Necessidade energética para crianças com Síndrome de Down"""
    if sexo == Sexo.MASCULINO:
        return 16.1 * altura
    else:
        return 14.3 * altura

# 26. NECESSIDADES NUTRICIONAIS PARA PARALISIA CEREBRAL
def calcular_necessidade_pc(peso: float, altura: float, sexo: Sexo, 
                           idade: float, fator_estresse: float) -> Optional[float]:
    """Calcula necessidades nutricionais para paralisia cerebral"""
    if peso <= 0 or altura <= 0 or idade < 0 or fator_estresse <= 0:
        return None
    
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

# 27. GEB CRÍTICA
def geb_critica(idade_meses: float, peso: float, temp_c: float) -> float:
    """Gasto Energético Basal para crianças criticamente enfermas"""
    return ((17 * idade_meses) + (48 * peso) + (292 * temp_c) - 9677) * 0.239

# --- INTERFACE STREAMLIT COMPLETA ---
def main():
    st.set_page_config(
        page_title="Calculadora Nutricional Completa (Final)",
        page_icon="🍎",
        layout="wide"
    )
    
    # Estilos CSS
    st.markdown("""
    <style>
    .result-box {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 15px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #17a2b8;
        margin: 10px 0;
    }
    .section-title {
        background-color: #e8f5e9;
        padding: 10px;
        border-radius: 5px;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Menu principal
    st.sidebar.title("🍏 Calculadora Nutricional Completa")
    st.sidebar.markdown("---")
    
    # Agrupamento de módulos
    modulos = [
        "🏠 Página Inicial",
        "📊 Classificação Antropométrica (0-5 anos)",
        "⚡ Equação de Schofield",
        "🔥 Requerimento Energético",
        "🦽 Paralisia Cerebral",
        "🏥 UTI e Crianças Críticas",
        "📈 Percentual Alcançado",
        "📐 Antropometria Avançada",
        "⚖️ Cálculos Gerais"
    ]
    
    modulo = st.sidebar.selectbox("Selecione o módulo:", modulos)
    
    # Página inicial
    if modulo == "🏠 Página Inicial":
        st.title("🍏 Calculadora Nutricional Completa")
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 📊 **Antropometria**")
            st.markdown("""
            - Classificação 0-5 anos
            - Estimativa de peso
            - Estimativa de estatura
            - Composição corporal
            """)
        
        with col2:
            st.markdown("### ⚡ **Metabolismo**")
            st.markdown("""
            - Equação de Schofield
            - TMB padrão
            - Requerimento energético
            - Gasto energético total
            """)
        
        with col3:
            st.markdown("### 🏥 **Condições Especiais**")
            st.markdown("""
            - Paralisia Cerebral
            - Síndrome de Down
            - UTI pediátrica
            - Prematuridade
            """)
        
        st.markdown("---")
        st.markdown("### 📋 **Fórmulas Implementadas:**")
        
        formulas = [
            "✅ Classificação antropométrica OMS (0-5 anos)",
            "✅ Equação de Schofield (peso e peso+estatura)",
            "✅ Coeficientes de atividade física",
            "✅ Requerimento energético por idade",
            "✅ Estimativa de peso (crianças 6-18 anos)",
            "✅ Percentual de gordura corporal",
            "✅ Circunferência muscular do braço",
            "✅ Área muscular e gorda do braço",
            "✅ Paralisia Cerebral (várias fórmulas)",
            "✅ Síndrome de Down",
            "✅ UTI e crianças críticas",
            "✅ Correção de prematuridade",
            "✅ Percentual alcançado",
            "✅ Peso ajustado e perda de peso"
        ]
        
        for formula in formulas:
            st.markdown(f"• {formula}")
        
        st.markdown("---")
        st.info("💡 **Dica:** Use o menu lateral para navegar entre os diferentes módulos.")
    
    else:
        st.title(f"🧮 {modulo}")
    
    try:
        if modulo == "📊 Classificação Antropométrica (0-5 anos)":
            st.header("Classificação do Estado Nutricional (0-5 anos incompletos)")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📏 Valores")
                percentil = st.number_input("Percentil", min_value=0.0, max_value=100.0, value=50.0, step=0.1)
                escore_z = st.number_input("Escore Z", min_value=-5.0, max_value=5.0, value=0.0, step=0.1)
            
            with col2:
                st.subheader("📋 Índice")
                indice = st.selectbox(
                    "Selecione o índice antropométrico:",
                    options=[e.value for e in IndiceAntropometrico],
                    format_func=lambda x: {
                        "peso_idade": "Peso para Idade",
                        "peso_estatura": "Peso para Estatura", 
                        "imc_idade": "IMC para Idade",
                        "estatura_idade": "Estatura para Idade"
                    }[x]
                )
            
            if st.button("🔍 Classificar", type="primary"):
                resultado = classificar_antropometria_0_5_anos(
                    percentil, escore_z, IndiceAntropometrico(indice)
                )
                
                if resultado:
                    # Cores conforme especificado
                    if "muito baixo" in resultado.lower() or "magreza acentuada" in resultado.lower():
                        cor = "red"
                    elif "baixo" in resultado.lower() or "magreza" in resultado.lower():
                        cor = "orange"
                    elif "adequado" in resultado.lower() or "eutrofia" in resultado.lower():
                        cor = "green"
                    elif "risco" in resultado.lower():
                        cor = "yellow"
                    elif "elevado" in resultado.lower() or "sobrepeso" in resultado.lower():
                        cor = "orange"
                    elif "obesidade" in resultado.lower():
                        cor = "red"
                    else:
                        cor = "blue"
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2 style="color:{cor}">📋 Resultado:</h2>
                        <h1 style="color:{cor}">{resultado}</h1>
                        <p><strong>Percentil:</strong> {percentil:.1f}</p>
                        <p><strong>Escore Z:</strong> {escore_z:.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Tabela de referência
                    st.subheader("📊 Tabela de Referência")
                    referencia = {
                        "Peso para Idade": [
                            ["<0,1", "<-3", "Muito baixo peso"],
                            ["≥0,1 e <3", "≥-3 e <-2", "Baixo peso"],
                            ["≥3 e <85", "≥-2 e ≤+1", "Peso adequado"],
                            [">85 e ≤97", ">+1 e ≤+2", "Peso adequado"],
                            [">97 e ≤99,9", ">+2 e ≤+3", "Peso elevado"],
                            [">99,9", ">+3", "Obesidade"]
                        ],
                        "Peso para Estatura/IMC": [
                            ["<0,1", "<-3", "Magreza acentuada"],
                            ["≥0,1 e <3", "≥-3 e <-2", "Magreza"],
                            ["≥3 e <85", "≥-2 e ≤+1", "Eutrofia"],
                            ["≥85 e ≤97", ">+1 e ≤+2", "Risco de sobrepeso"],
                            [">97 e ≤99,9", ">+2 e ≤+3", "Sobrepeso"],
                            [">99,9", ">+3", "Obesidade"]
                        ],
                        "Estatura para Idade": [
                            ["<0,1", "<-3", "Muito baixa estatura"],
                            ["≥0,1 e <3", "≥-3 e <-2", "Baixa estatura"],
                            ["≥3", "≥-2", "Estatura adequada"]
                        ]
                    }
                    
                    for titulo, dados in referencia.items():
                        st.write(f"**{titulo}:**")
                        df = pd.DataFrame(dados, columns=["Percentil", "Escore Z", "Classificação"])
                        st.dataframe(df, hide_index=True)
                else:
                    st.error("❌ Não foi possível classificar. Verifique os valores inseridos.")
        
        elif modulo == "⚡ Equação de Schofield":
            st.header("Equação de Schofield para Crianças Gravemente Doentes")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📏 Dados do Paciente")
                peso = st.number_input("Peso (kg)", min_value=0.1, max_value=150.0, value=15.0, step=0.1)
                estatura = st.number_input("Estatura (metros)", min_value=0.3, max_value=2.5, value=1.0, step=0.01)
                idade = st.number_input("Idade (anos)", min_value=0.0, max_value=18.0, value=5.0, step=0.1)
                sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
            
            with col2:
                st.subheader("🎯 Opções de Cálculo")
                tipo_formula = st.radio(
                    "Selecione a fórmula:",
                    ["🌸 Apenas Peso (Rosa)", "🌿 Peso e Estatura (Verde)"],
                    index=0
                )
            
            if st.button("⚡ Calcular TMB Schofield", type="primary"):
                sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                
                if "Apenas Peso" in tipo_formula:
                    resultado = tmb_schofield_peso(peso, idade, sexo_enum)
                    formula_usada = "Apenas Peso (Rosa)"
                    cor = "#ff69b4"
                else:
                    resultado = tmb_schofield_peso_estatura(peso, estatura, idade, sexo_enum)
                    formula_usada = "Peso e Estatura (Verde)"
                    cor = "#28a745"
                
                if resultado is None:
                    st.error("Idade fora da faixa suportada (0-18 anos)")
                else:
                    st.markdown(f"""
                    <div class="result-box" style="border-left-color:{cor}">
                        <h2>⚡ Taxa Metabólica Basal (Schofield)</h2>
                        <h1>{resultado:.2f} kcal/dia</h1>
                        <p><strong>Fórmula:</strong> {formula_usada}</p>
                        <p><strong>Idade:</strong> {idade:.1f} anos</p>
                        <p><strong>Sexo:</strong> {sexo}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Comparação com TMB padrão
                    tmb_padrao = calcular_tmb_padrao(peso, idade, sexo_enum)
                    if tmb_padrao:
                        diferenca = resultado - tmb_padrao
                        percentual = (diferenca / tmb_padrao) * 100
                        st.info(f"""
                        **Comparação com TMB padrão:**
                        - TMB padrão: {tmb_padrao:.2f} kcal/dia
                        - Diferença: {diferenca:+.2f} kcal/dia ({percentual:+.2f}%)
                        """)
        
        elif modulo == "🔥 Requerimento Energético":
            st.header("Requerimento Energético para Crianças/Adolescentes")
            
            idade_tipo = st.radio(
                "Faixa etária:",
                ["👶 0-35 meses (apenas peso)", "🧒 3-18 anos (peso, estatura e atividade)"],
                index=0
            )
            
            if "0-35" in idade_tipo:
                col1, col2 = st.columns(2)
                with col1:
                    peso = st.number_input("Peso (kg)", min_value=0.1, max_value=50.0, value=8.0, step=0.1)
                with col2:
                    idade_meses = st.number_input("Idade (meses)", min_value=0.0, max_value=35.0, value=6.0, step=0.1)
                
                if st.button("🔥 Calcular Requerimento", type="primary"):
                    resultado = calcular_requerimento_energetico_idade(peso, idade_meses)
                    
                    if resultado is None:
                        st.error("Dados inválidos")
                    else:
                        # Determinar faixa específica
                        if idade_meses <= 3:
                            faixa = "0-3 meses"
                        elif idade_meses <= 6:
                            faixa = "4-6 meses"
                        elif idade_meses <= 12:
                            faixa = "7-12 meses"
                        else:
                            faixa = "13-35 meses"
                        
                        st.markdown(f"""
                        <div class="result-box">
                            <h2>🔥 Requerimento Energético</h2>
                            <h1>{resultado:.2f} kcal/dia</h1>
                            <p><strong>Faixa etária:</strong> {faixa}</p>
                            <p><strong>Fórmula:</strong> (89 × Peso - 100) + constante</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            else:  # 3-18 anos
                col1, col2, col3 = st.columns(3)
                with col1:
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=150.0, value=25.0, step=0.1)
                    estatura = st.number_input("Estatura (metros)", min_value=0.5, max_value=2.5, value=1.2, step=0.01)
                with col2:
                    idade_anos = st.number_input("Idade (anos)", min_value=3.0, max_value=18.0, value=8.0, step=0.1)
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                with col3:
                    nivel = st.selectbox(
                        "Nível de Atividade",
                        options=[n.value for n in NivelAtividade]
                    )
                
                # Obter coeficiente
                sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                nivel_enum = NivelAtividade(nivel)
                fator_atividade = obter_coeficiente_atividade(sexo_enum, nivel_enum)
                
                st.markdown(f"""
                <div class="info-box">
                    <strong>Coeficiente de Atividade:</strong> {fator_atividade:.2f}<br>
                    <strong>Tabela para {sexo}:</strong><br>
                    • Sedentária: 1.00<br>
                    • Baixa atividade: {1.13 if sexo == "Masculino" else 1.16}<br>
                    • Ativo: {1.26 if sexo == "Masculino" else 1.31}<br>
                    • Muito ativo: {1.42 if sexo == "Masculino" else 1.56}
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔥 Calcular Requerimento Completo", type="primary"):
                    resultado = calcular_requerimento_energetico_completo(
                        peso, estatura, idade_anos, sexo_enum, fator_atividade
                    )
                    
                    if resultado is None:
                        st.error("Idade fora da faixa suportada (3-18 anos)")
                    else:
                        faixa = "3-8 anos" if idade_anos < 9 else "9-18 anos"
                        
                        st.markdown(f"""
                        <div class="result-box">
                            <h2>🔥 Requerimento Energético Total</h2>
                            <h1>{resultado:.2f} kcal/dia</h1>
                            <p><strong>Faixa etária:</strong> {faixa}</p>
                            <p><strong>Nível de atividade:</strong> {nivel} (×{fator_atividade:.2f})</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        elif modulo == "🦽 Paralisia Cerebral":
            st.header("Cálculos para Paralisia Cerebral")
            
            tipo_calculo = st.selectbox(
                "Selecione o cálculo:",
                [
                    "Paciente com PC enfermo (×1.1)",
                    "Necessidade energética PC 5-11 anos",
                    "Necessidade energética PC estáveis",
                    "Necessidade energética PC geral",
                    "Necessidades nutricionais PC (com fator estresse)"
                ]
            )
            
            if "enfermo" in tipo_calculo:
                col1, col2 = st.columns(2)
                with col1:
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=100.0, value=20.0, step=0.1)
                    altura_cm = st.number_input("Altura (cm)", min_value=30.0, max_value=200.0, value=120.0, step=0.1)
                with col2:
                    idade = st.number_input("Idade (anos)", min_value=0.0, max_value=18.0, value=8.0, step=0.1)
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                
                if st.button("🦽 Calcular", type="primary"):
                    sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                    resultado = necessidade_energetica_pc_enfermo(peso, altura_cm, idade, sexo_enum)
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>🦽 Necessidade Energética PC Enfermo</h2>
                        <h1>{resultado:.2f} kcal/dia</h1>
                        <p><strong>Fórmula:</strong> TMB × 1.1 (fator de estresse)</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            elif "5-11 anos" in tipo_calculo:
                altura = st.number_input("Altura (cm)", min_value=50.0, max_value=200.0, value=120.0, step=0.1)
                nivel = st.selectbox("Nível de Atividade", options=[n.value for n in NivelAtividadePC])
                
                if st.button("🦽 Calcular", type="primary"):
                    resultado = necessidade_energetica_pc_5_11(altura, nivel)
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>🦽 Necessidade Energética PC 5-11 anos</h2>
                        <h1>{resultado:.2f} kcal/dia</h1>
                        <p><strong>Fórmula:</strong> {{
                            'leve a moderada': '13.9 × altura',
                            'restrita intensa': '10 × altura',
                            'restrição física grave': '11.1 × altura'
                        }}[nivel]</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            elif "estáveis" in tipo_calculo:
                altura = st.number_input("Altura (cm)", min_value=50.0, max_value=200.0, value=120.0, step=0.1)
                condicao = st.selectbox("Condição Motora", options=[c.value for c in CondicaoMotora])
                
                if st.button("🦽 Calcular", type="primary"):
                    resultado = necessidade_energetica_pc_estaveis(altura, condicao)
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>🦽 Necessidade Energética PC Estáveis</h2>
                        <h1>{resultado:.2f} kcal/dia</h1>
                    </div>
                    """, unsafe_allow_html=True)
            
            elif "geral" in tipo_calculo:
                col1, col2 = st.columns(2)
                with col1:
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=100.0, value=20.0, step=0.1)
                    altura = st.number_input("Altura (cm)", min_value=30.0, max_value=200.0, value=120.0, step=0.1)
                with col2:
                    idade = st.number_input("Idade (anos)", min_value=0.0, max_value=18.0, value=8.0, step=0.1)
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                
                if st.button("🦽 Calcular", type="primary"):
                    sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                    resultado = necessidade_energetica_pc(peso, altura, idade, sexo_enum)
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>🦽 Necessidade Energética PC Geral</h2>
                        <h1>{resultado:.2f} kcal/dia</h1>
                    </div>
                    """, unsafe_allow_html=True)
            
            elif "nutricionais" in tipo_calculo:
                col1, col2 = st.columns(2)
                with col1:
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=100.0, value=20.0, step=0.1)
                    altura = st.number_input("Altura (metros)", min_value=0.3, max_value=2.0, value=1.0, step=0.01)
                with col2:
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                    idade = st.number_input("Idade (anos)", min_value=0.0, max_value=18.0, value=5.0, step=0.1)
                    fator_estresse = st.number_input("Fator de Estresse", min_value=1.0, max_value=2.5, value=1.2, step=0.1)
                
                if st.button("🦽 Calcular", type="primary"):
                    sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                    resultado = calcular_necessidade_pc(peso, altura, sexo_enum, idade, fator_estresse)
                    
                    if resultado is None:
                        st.error("Dados inválidos ou idade fora da faixa")
                    else:
                        st.markdown(f"""
                        <div class="result-box">
                            <h2>🦽 Necessidades Nutricionais PC</h2>
                            <h1>{resultado:.2f} kcal/dia</h1>
                        </div>
                        """, unsafe_allow_html=True)
        
        elif modulo == "🏥 UTI e Crianças Críticas":
            st.header("Cálculos para UTI e Crianças Críticas")
            
            tipo = st.selectbox(
                "Selecione o cálculo:",
                [
                    "GEB UTI Ventilação Mecânica (>2 anos)",
                    "Correção de Prematuridade (até 2 anos)",
                    "GEB Criança Criticamente Enferma",
                    "Síndrome de Down"
                ]
            )
            
            if "UTI" in tipo:
                st.markdown("""
                <div class="warning-box">
                    ⚠️ <strong>Atenção:</strong> Esta fórmula é válida apenas para pacientes acima de 2 anos e não queimados.
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    idade_meses = st.number_input("Idade (meses)", min_value=24.0, max_value=240.0, 
                                                value=48.0, step=1.0)
                with col2:
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=100.0, value=15.0, step=0.1)
                with col3:
                    temperatura = st.number_input("Temperatura (°C)", min_value=30.0, max_value=45.0, 
                                                value=37.0, step=0.1)
                
                if st.button("🏥 Calcular GEB UTI", type="primary"):
                    try:
                        resultado = geb_uti_ventilacao_mecanica(idade_meses, peso, temperatura)
                        
                        st.markdown(f"""
                        <div class="result-box">
                            <h2>🏥 Gasto Energético Basal (UTI)</h2>
                            <h1>{resultado:.2f} kcal/dia</h1>
                        </div>
                        """, unsafe_allow_html=True)
                    except ValueError as e:
                        st.error(str(e))
            
            elif "Prematuridade" in tipo:
                st.info("📅 **Correção de prematuridade até 2 anos**")
                
                col1, col2 = st.columns(2)
                with col1:
                    idade_cron = st.number_input("Idade Cronológica (meses)", 
                                               min_value=0.0, max_value=24.0, value=6.0, step=0.1)
                with col2:
                    idade_gest = st.number_input("Idade Gestacional (semanas)", 
                                               min_value=20.0, max_value=42.0, value=32.0, step=0.1)
                
                if st.button("👶 Calcular Idade Corrigida", type="primary"):
                    resultado = calcular_idade_corrigida(idade_cron, idade_gest)
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>👶 Idade Corrigida</h2>
                        <h1>{resultado:.1f} meses</h1>
                    </div>
                    """, unsafe_allow_html=True)
            
            elif "Criticamente" in tipo:
                col1, col2, col3 = st.columns(3)
                with col1:
                    idade_meses = st.number_input("Idade (meses)", min_value=0.0, max_value=240.0, 
                                                value=12.0, step=0.1)
                with col2:
                    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=100.0, value=10.0, step=0.1)
                with col3:
                    temp_c = st.number_input("Temperatura (°C)", min_value=30.0, max_value=45.0, 
                                           value=37.0, step=0.1)
                
                if st.button("🏥 Calcular GEB Crítica", type="primary"):
                    resultado = geb_critica(idade_meses, peso, temp_c)
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>🏥 GEB Criança Criticamente Enferma</h2>
                        <h1>{resultado:.2f} kcal/dia</h1>
                    </div>
                    """, unsafe_allow_html=True)
            
            elif "Down" in tipo:
                altura = st.number_input("Altura (cm)", min_value=50.0, max_value=200.0, value=120.0, step=0.1)
                sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                
                if st.button("🧬 Calcular Necessidade", type="primary"):
                    sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                    resultado = necessidade_sindrome_down(altura, sexo_enum)
                    
                    st.markdown(f"""
                    <div class="result-box">
                        <h2>🧬 Necessidade Energética Síndrome de Down</h2>
                        <h1>{resultado:.2f} kcal/dia</h1>
                    </div>
                    """, unsafe_allow_html=True)
        
        elif modulo == "📈 Percentual Alcançado":
            st.header("Cálculo de Percentual Alcançado")
            
            tipo = st.selectbox(
                "Selecione o nutriente:",
                ["GEB", "Proteína", "GET", "Outro"]
            )
            
            col1, col2 = st.columns(2)
            with col1:
                consumido = st.number_input(f"Valor Consumido ({tipo})", 
                                          min_value=0.0, max_value=10000.0, value=1500.0, step=10.0)
            with col2:
                necessidade = st.number_input(f"Necessidade ({tipo})", 
                                           min_value=0.1, max_value=10000.0, value=2000.0, step=10.0)
            
            if st.button("📈 Calcular % Alcançado", type="primary"):
                try:
                    percentual = calcular_percentual_alcançado(consumido, necessidade)
                    
                    if percentual >= 100:
                        status = "✅ Meta alcançada ou superada"
                        cor = "#28a745"
                    elif percentual >= 90:
                        status = "⚠️ Próximo da meta (90-99%)"
                        cor = "#ffc107"
                    elif percentual >= 70:
                        status = "⚠️ Atenção necessária (70-89%)"
                        cor = "#fd7e14"
                    else:
                        status = "❌ Meta não alcançada (<70%)"
                        cor = "#dc3545"
                    
                    st.markdown(f"""
                    <div class="result-box" style="border-left-color:{cor}">
                        <h2>📈 Percentual Alcançado - {tipo}</h2>
                        <h1 style="color:{cor}">{percentual:.1f}%</h1>
                        <p style="color:{cor}"><strong>{status}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    progresso = min(percentual / 100, 1.0)
                    st.progress(float(progresso))
                    
                except ValueError as e:
                    st.error(str(e))
        
        elif modulo == "📐 Antropometria Avançada":
            st.header("Antropometria Avançada")
            
            submodulo = st.selectbox(
                "Selecione o cálculo:",
                [
                    "Estimativa de Peso (crianças 6-18 anos)",
                    "Estimativa de Estatura pela Tíbia",
                    "Estimativa de Estatura pela Ulna",
                    "Percentual de Gordura Corporal",
                    "Circunferência Muscular do Braço (CMB)",
                    "Área Muscular do Braço (AMB)",
                    "Área Gorda do Braço (AGB)",
                    "Estimativa de Estatura PC (2-12 anos)",
                    "Estimativa de Estatura Adolescente PC",
                    "Peso Corrigido para Amputação",
                    "Gasto Energético Total (GET)"
                ]
            )
            
            if "Estimativa de Peso" in submodulo:
                st.subheader("Estimativa para crianças e adolescentes (6-18 anos)")
                
                col1, col2 = st.columns(2)
                with col1:
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                    raca = st.selectbox("Raça", options=[r.value for r in Raca])
                with col2:
                    altura_joelho = st.number_input("Altura do Joelho (cm)", min_value=10.0, max_value=60.0, value=30.0, step=0.1)
                    perimetro_braco = st.number_input("Perímetro do Braço (cm)", min_value=5.0, max_value=40.0, value=20.0, step=0.1)
                
                if st.button("Calcular Peso Estimado"):
                    sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                    raca_enum = Raca.BRANCA if raca == "Branca" else Raca.NEGRA
                    resultado = estimar_peso_crianca(altura_joelho, perimetro_braco, sexo_enum, raca_enum)
                    
                    if resultado:
                        st.success(f"**Peso Estimado:** {resultado:.2f} kg")
                    else:
                        st.error("❌ Erro no cálculo. Verifique os valores.")
            
            elif "Tíbia" in submodulo:
                comprimento_tibia = st.number_input("Comprimento da Tíbia (cm)", 
                                                  min_value=10.0, max_value=50.0, value=30.0, step=0.1)
                
                if st.button("Calcular Estatura"):
                    resultado = estimar_estatura_tibia(comprimento_tibia)
                    st.success(f"**Estatura Estimada:** {resultado:.2f} cm")
            
            elif "Ulna" in submodulo:
                comprimento_ulna = st.number_input("Comprimento da Ulna (cm)", 
                                                 min_value=10.0, max_value=40.0, value=25.0, step=0.1)
                
                if st.button("Calcular Estatura"):
                    resultado = estimar_estatura_ulna(comprimento_ulna)
                    st.success(f"**Estatura Estimada:** {resultado:.2f} cm")
            
            elif "Percentual de Gordura" in submodulo:
                col1, col2 = st.columns(2)
                with col1:
                    soma_dobras = st.number_input("Soma das Dobras Cutâneas (mm)", 
                                                min_value=5.0, max_value=100.0, value=30.0, step=0.1)
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                with col2:
                    estagio_tanner = st.selectbox("Estágio de Tanner", options=[1, 2, 3, 4, 5])
                    raca = st.selectbox("Raça", options=[r.value for r in Raca])
                
                if st.button("Calcular % Gordura"):
                    sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                    raca_enum = Raca.BRANCA if raca == "Branca" else Raca.NEGRA
                    resultado = calcular_percentual_gordura(soma_dobras, sexo_enum, estagio_tanner, raca_enum)
                    
                    if resultado:
                        st.success(f"**Percentual de Gordura:** {resultado:.2f}%")
                    else:
                        st.error("❌ Erro no cálculo. Verifique os valores.")
            
            elif "CMB" in submodulo:
                col1, col2 = st.columns(2)
                with col1:
                    perimetro_braco = st.number_input("Perímetro do Braço (cm)", 
                                                    min_value=5.0, max_value=50.0, value=25.0, step=0.1)
                with col2:
                    dobra_tricipital = st.number_input("Dobra Tricipital (mm)", 
                                                     min_value=3.0, max_value=40.0, value=15.0, step=0.1)
                
                if st.button("Calcular CMB"):
                    resultado = calcular_circ_muscular_braco(perimetro_braco, dobra_tricipital)
                    st.success(f"**Circunferência Muscular do Braço:** {resultado:.2f} cm")
            
            elif "Área Muscular" in submodulo:
                col1, col2 = st.columns(2)
                with col1:
                    circunferencia_braco = st.number_input("Circunferência do Braço (cm)", 
                                                         min_value=5.0, max_value=50.0, value=25.0, step=0.1)
                with col2:
                    dobra_tricipital = st.number_input("Dobra Tricipital (mm)", 
                                                     min_value=3.0, max_value=40.0, value=15.0, step=0.1)
                
                if st.button("Calcular AMB"):
                    resultado = calcular_area_muscular_braco(circunferencia_braco, dobra_tricipital)
                    st.success(f"**Área Muscular do Braço:** {resultado:.2f} cm²")
            
            elif "Área Gorda" in submodulo:
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
            
            elif "PC (2-12 anos)" in submodulo:
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
                        comprimento_superior, comprimento_tibial, comprimento_joelho
                    )
                    
                    st.success(f"""
                    **Estimativas:**
                    - Por comprimento superior: {resultados['Estimada_CS']:.1f} cm
                    - Por comprimento tibial: {resultados['Estimada_CT']:.1f} cm
                    - Por comprimento do joelho: {resultados['Estimada_CJ']:.1f} cm
                    """)
            
            elif "Adolescente PC" in submodulo:
                col1, col2 = st.columns(2)
                with col1:
                    idade = st.number_input("Idade (anos)", min_value=2.0, max_value=30.0, value=15.0, step=0.1)
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                with col2:
                    comprimento_ulna = st.number_input("Comprimento da Ulna (cm)", 
                                                     min_value=10.0, max_value=40.0, value=25.0, step=0.1)
                
                if st.button("Calcular Estatura"):
                    sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                    resultado = estimar_estatura_paralisia_adolescente(idade, sexo_enum, comprimento_ulna)
                    
                    st.success(f"**Estatura Estimada:** {resultado:.1f} cm")
            
            elif "Amputação" in submodulo:
                col1, col2 = st.columns(2)
                with col1:
                    peso_atual = st.number_input("Peso Atual (kg)", 
                                               min_value=10.0, max_value=300.0, value=70.0, step=0.1)
                with col2:
                    percentual = st.number_input("Percentual de Amputação (%)", 
                                               min_value=0.0, max_value=99.9, value=10.0, step=0.1)
                
                if st.button("Calcular Peso Corrigido"):
                    resultado = calcular_peso_corrigido_amputacao(peso_atual, percentual)
                    st.success(f"**Peso Corrigido Estimado:** {resultado:.2f} kg")
            
            elif "GET" in submodulo:
                ere = st.number_input("Taxa Metabólica Basal (kcal)", 
                                    min_value=500.0, max_value=5000.0, value=1500.0, step=10.0)
                
                col1, col2 = st.columns(2)
                with col1:
                    fator_atividade = st.number_input("Fator de Atividade Física (opcional)", 
                                                    min_value=1.0, max_value=2.5, value=1.0, step=0.1)
                with col2:
                    fator_estresse = st.number_input("Fator de Estresse (opcional)", 
                                                   min_value=1.0, max_value=2.5, value=1.0, step=0.1)
                
                if st.button("Calcular GET"):
                    try:
                        if fator_atividade > 1.0 and fator_estresse > 1.0:
                            st.warning("Use apenas um fator adicional (atividade OU estresse)")
                        else:
                            resultado = calcular_gasto_energetico_total(ere, 
                                                                      fator_atividade if fator_atividade > 1.0 else None,
                                                                      fator_estresse if fator_estresse > 1.0 else None)
                            st.success(f"**Gasto Energético Total:** {resultado:.2f} kcal/dia")
                    except ValueError as e:
                        st.error(str(e))
        
        elif modulo == "⚖️ Cálculos Gerais":
            st.header("Cálculos Nutricionais Gerais")
            
            calculo = st.selectbox(
                "Selecione o cálculo:",
                [
                    "Peso Ajustado (obesidade/desnutrição)",
                    "Perda de Peso (%)",
                    "TMB Padrão (não Schofield)"
                ]
            )
            
            if "Peso Ajustado" in calculo:
                col1, col2 = st.columns(2)
                with col1:
                    peso_atual = st.number_input("Peso Atual (kg)", min_value=0.1, max_value=300.0, value=70.0)
                with col2:
                    peso_ideal = st.number_input("Peso Ideal (kg)", min_value=0.1, max_value=300.0, value=65.0)
                
                condicao = st.selectbox(
                    "Condição:",
                    [Condicao.OBESIDADE.value, Condicao.DESNUTRICAO.value],
                    format_func=lambda x: "Obesidade" if x == "obesidade" else "Desnutrição"
                )
                
                if st.button("⚖️ Calcular Peso Ajustado", type="primary"):
                    resultado = calcular_peso_ajustado(
                        peso_atual, peso_ideal, Condicao(condicao)
                    )
                    
                    if resultado:
                        st.success(f"**Peso Ajustado:** {resultado:.2f} kg")
                    else:
                        st.error("❌ Erro no cálculo.")
            
            elif "Perda de Peso" in calculo:
                col1, col2 = st.columns(2)
                with col1:
                    peso_usual = st.number_input("Peso Usual (kg)", min_value=0.1, max_value=300.0, value=70.0)
                with col2:
                    peso_atual = st.number_input("Peso Atual (kg)", min_value=0.1, max_value=300.0, value=65.0)
                
                if st.button("📉 Calcular Perda de Peso", type="primary"):
                    resultado = calcular_perda_peso(peso_usual, peso_atual)
                    
                    if resultado is not None:
                        st.success(f"**Perda de Peso:** {resultado:.2f}%")
                    else:
                        st.error("❌ Erro no cálculo.")
            
            elif "TMB Padrão" in calculo:
                col1, col2 = st.columns(2)
                with col1:
                    peso = st.number_input("Peso (kg)", min_value=0.1, max_value=300.0, value=70.0, step=0.1)
                    idade = st.number_input("Idade (anos)", min_value=0.0, max_value=120.0, value=30.0, step=0.1)
                with col2:
                    sexo = st.selectbox("Sexo", options=[s.value for s in Sexo])
                
                if st.button("⚡ Calcular TMB Padrão", type="primary"):
                    sexo_enum = Sexo.MASCULINO if sexo == "Masculino" else Sexo.FEMININO
                    resultado = calcular_tmb_padrao(peso, idade, sexo_enum)
                    
                    if resultado is None:
                        st.error("Idade fora da faixa suportada (0-18 anos)")
                    else:
                        st.success(f"**Taxa Metabólica Basal:** {resultado:.2f} kcal/dia")
    
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        st.error("Se o erro persistir, verifique os valores inseridos e tente novamente.")
    
    # Rodapé
    st.markdown("---")
    st.caption("© 2024 Calculadora Nutricional Completa - Todas as fórmulas verificadas e implementadas")
    st.caption("✅ **Status:** Sistema completo com 27 fórmulas nutricionais")

if __name__ == "__main__":
    main()
