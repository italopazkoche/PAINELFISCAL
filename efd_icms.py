import streamlit as st
import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import conectar_mysql, formatar_moeda

def run_efd_icms():
    st.title("📑 Análise EFD ICMS - Bloco C100")

    try:
        conexao = conectar_mysql()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute("""
            SELECT chave_periodo, cnpj, razao_social, data_inicio, data_fim
            FROM efd_icms_bloco_0000
            ORDER BY data_fim DESC
        """)
        empresas = cursor.fetchall()
        df_empresas = pd.DataFrame(empresas)

        if df_empresas.empty:
            st.warning("Nenhuma empresa encontrada.")
            return

        df_empresas["mes"] = pd.to_datetime(df_empresas["data_fim"]).dt.strftime('%m/%Y')
        df_empresas["empresa"] = df_empresas["razao_social"] + " • " + df_empresas["cnpj"]

        empresa_sel = st.selectbox("Selecione a empresa:", df_empresas["empresa"].unique())
        meses_disponiveis = df_empresas[df_empresas["empresa"] == empresa_sel]["mes"].unique()
        mes_sel = st.selectbox("Selecione o mês:", meses_disponiveis)

        filtro = df_empresas[(df_empresas["empresa"] == empresa_sel) & (df_empresas["mes"] == mes_sel)]
        chave_periodo = filtro["chave_periodo"].values[0]

        cursor.execute("""
            SELECT 
                c.ind_oper, c.dt_doc, c.cod_part, c.cod_mod, c.cod_sit, c.ser, c.num_doc, c.chv_nfe,
                c.vl_doc, c.vl_desc, c.vl_merc, c.vl_out_da, c.vl_frt, c.vl_seg,
                c.vl_bc_icms, c.vl_icms, c.vl_bc_icms_st, c.vl_icms_st,
                c.vl_ipi, c.vl_pis, c.vl_cofins, c.vl_pis_st, c.vl_cofins_st,
                p.municipio, p.uf
            FROM efd_icms_bloco_c100 c
            LEFT JOIN efd_icms_bloco_0150 p 
                ON c.chave_periodo = p.chave_periodo AND c.cod_part = p.cod_part
            WHERE c.chave_periodo = %s
        """, (chave_periodo,))
        dados = cursor.fetchall()
        df = pd.DataFrame(dados)

        if df.empty:
            st.warning("Nenhum documento encontrado para o período selecionado.")
            return

        df["tipo_operacao"] = df["ind_oper"].astype(str).map({"0": "Entrada", "1": "Saída"}).fillna("Outro")

        df_entrada = df[df["tipo_operacao"] == "Entrada"].copy()
        df_saida = df[df["tipo_operacao"] == "Saída"].copy()

        campos_numericos = [
            "vl_doc", "vl_desc", "vl_merc", "vl_out_da", "vl_frt", "vl_seg",
            "vl_bc_icms", "vl_icms", "vl_bc_icms_st", "vl_icms_st",
            "vl_ipi", "vl_pis", "vl_cofins", "vl_pis_st", "vl_cofins_st"
        ]
        for col in campos_numericos:
            df_entrada[col] = pd.to_numeric(df_entrada[col], errors='coerce').fillna(0.0)
            df_saida[col] = pd.to_numeric(df_saida[col], errors='coerce').fillna(0.0)

        renomear = {
            "dt_doc": "Data", "cod_part": "Código Parceiro", "cod_mod": "Modelo", "cod_sit": "Situação",
            "ser": "Série", "num_doc": "Número", "chv_nfe": "Chave NFe",
            "vl_doc": "Valor Total", "vl_desc": "Desconto", "vl_merc": "Valor Mercadoria",
            "vl_out_da": "Outras Desp.", "vl_frt": "Frete", "vl_seg": "Seguro",
            "vl_bc_icms": "Base ICMS", "vl_icms": "ICMS", "vl_bc_icms_st": "Base ICMS ST", "vl_icms_st": "ICMS ST",
            "vl_ipi": "IPI", "vl_pis": "PIS", "vl_cofins": "COFINS",
            "vl_pis_st": "PIS ST", "vl_cofins_st": "COFINS ST",
            "municipio": "Município", "uf": "UF"
        }
        df_entrada.rename(columns=renomear, inplace=True)
        df_saida.rename(columns=renomear, inplace=True)

        # Totais
        total_docs = len(df)
        total_entrada = df_entrada["Valor Total"].sum()
        total_saida = df_saida["Valor Total"].sum()
        perc_entrada_saida = (total_entrada / total_saida * 100) if total_saida else 0

        diferenca_saida_entrada = total_saida - total_entrada
        qtd_fornecedores = df_entrada["Código Parceiro"].nunique()

        credito_icms = df_entrada["ICMS"].sum()
        credito_pis = df_entrada["PIS"].sum()
        credito_cofins = df_entrada["COFINS"].sum()
        debito_icms = df_saida["ICMS"].sum()
        debito_pis = df_saida["PIS"].sum()
        debito_cofins = df_saida["COFINS"].sum()

        saldo_icms = debito_icms - credito_icms
        saldo_pis = debito_pis - credito_pis
        saldo_cofins = debito_cofins - credito_cofins

        pct_icms_fat = f"{(saldo_icms / total_saida * 100):.2f}%" if total_saida else "0.00%"
        pct_pis_fat = f"{(saldo_pis / total_saida * 100):.2f}%" if total_saida else "0.00%"
        pct_cofins_fat = f"{(saldo_cofins / total_saida * 100):.2f}%" if total_saida else "0.00%"

        # 📊 Dados Gerais
        st.subheader("📊 Dados Gerais")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Documentos", total_docs)
        c2.metric("Valor Total Entrada", formatar_moeda(total_entrada))
        c3.metric("Valor Total Saída", formatar_moeda(total_saida))
        c4.metric("% Entrada/Saída", f"{perc_entrada_saida:.2f}%")

        d1, d2 = st.columns(2)
        d1.metric("Diferença (Saídas - Entradas)", formatar_moeda(diferenca_saida_entrada))
        d2.metric("Qtd. Fornecedores (Entradas)", f"{qtd_fornecedores}")

        st.markdown("### 💰 Saldo Débito - Crédito por Imposto")
        ic1, ic2, ic3 = st.columns(3)
        ic1.metric("Saldo ICMS", formatar_moeda(saldo_icms), pct_icms_fat)
        ic2.metric("Saldo PIS", formatar_moeda(saldo_pis), pct_pis_fat)
        ic3.metric("Saldo COFINS", formatar_moeda(saldo_cofins), pct_cofins_fat)

        # 📥 Entradas
        pct_icms = f"{(credito_icms / total_entrada * 100):.2f}%" if total_entrada else "0.00%"
        pct_pis = f"{(credito_pis / total_entrada * 100):.2f}%" if total_entrada else "0.00%"
        pct_cofins = f"{(credito_cofins / total_entrada * 100):.2f}%" if total_entrada else "0.00%"

        st.subheader("📥 Documentos de Entrada")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Total Entradas", formatar_moeda(total_entrada))
        e2.metric("Crédito ICMS", formatar_moeda(credito_icms), pct_icms)
        e3.metric("Crédito PIS", formatar_moeda(credito_pis), pct_pis)
        e4.metric("Crédito COFINS", formatar_moeda(credito_cofins), pct_cofins)
        st.dataframe(df_entrada[renomear.values()], use_container_width=True)

        # 📤 Saídas
        pct_deb_icms = f"{(debito_icms / total_saida * 100):.2f}%" if total_saida else "0.00%"
        pct_deb_pis = f"{(debito_pis / total_saida * 100):.2f}%" if total_saida else "0.00%"
        pct_deb_cofins = f"{(debito_cofins / total_saida * 100):.2f}%" if total_saida else "0.00%"

        st.subheader("📤 Documentos de Saída")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Saídas", formatar_moeda(total_saida))
        s2.metric("Débito ICMS", formatar_moeda(debito_icms), pct_deb_icms)
        s3.metric("Débito PIS", formatar_moeda(debito_pis), pct_deb_pis)
        s4.metric("Débito COFINS", formatar_moeda(debito_cofins), pct_deb_cofins)
        st.dataframe(df_saida[renomear.values()], use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexao' in locals() and conexao.is_connected():
            conexao.close()
