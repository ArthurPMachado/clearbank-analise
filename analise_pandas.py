"""
analise_pandas.py – Requisito Opcional 1 (RO1)
Implementação alternativa da análise usando pandas.
Os resultados são comparados com os obtidos pela solução nativa do notebook.
"""

import json
from datetime import datetime

import pandas as pd

# ── Constantes (mesmas do notebook principal) ─────────────────────────────────
LIMITE_SUSPEITO: float = 10_000.00
ARQUIVO_CSV: str = "transacoes.csv"
ARQUIVO_JSON: str = "relatorio.json"


def formatar_moeda(valor: float) -> str:
    """Formata um float no padrão monetário brasileiro: R$ 1.840,25"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_e_validar_pandas(filepath: str) -> pd.DataFrame:
    """
    Carrega o CSV com pd.read_csv e aplica as mesmas regras de validação
    usadas na solução nativa do notebook.
    """
    try:
        df = pd.read_csv(filepath, dtype=str)
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{filepath}' não encontrado.")
        return pd.DataFrame()

    total_lidas = len(df)

    # Remover linhas com id vazio ou não numérico
    df = df[df["id"].notna() & df["id"].str.strip().str.match(r"^\d+$")]

    # Remover linhas com cliente_id vazio
    df = df[df["cliente_id"].notna() & df["cliente_id"].str.strip().ne("")]

    # Converter data e remover linhas com formato inválido
    df["data"] = pd.to_datetime(df["data"].str.strip(), format="%Y-%m-%d", errors="coerce")
    df = df[df["data"].notna()]

    # Manter apenas tipo credito ou debito
    df["tipo"] = df["tipo"].str.strip().str.lower()
    df = df[df["tipo"].isin(["credito", "debito"])]

    # Converter valor e remover linhas não numéricas ou <= 0
    df["valor"] = pd.to_numeric(df["valor"].str.strip(), errors="coerce")
    df = df[df["valor"].notna() & (df["valor"] > 0)]

    # Conversão de tipos finais
    df["id"] = df["id"].astype(int)
    df["mes"] = df["data"].dt.strftime("%Y-%m")

    validas = len(df)
    invalidas = total_lidas - validas

    print("===== RESUMO DA LIMPEZA (PANDAS) =====")
    print(f"Total de linhas lidas: {total_lidas}")
    print(f"Linhas válidas:        {validas}")
    print(f"Linhas inválidas:      {invalidas}")

    return df


def gerar_resumo_mensal_pandas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa por mês e calcula todas as métricas financeiras usando groupby.
    """
    credito_mensal = (
        df[df["tipo"] == "credito"]
        .groupby("mes")["valor"]
        .sum()
        .rename("total_credito")
    )

    debito_mensal = (
        df[df["tipo"] == "debito"]
        .groupby("mes")["valor"]
        .sum()
        .rename("total_debito")
    )

    resumo = df.groupby("mes").agg(
        quantidade=("id", "count"),
        media=("valor", "mean"),
        maior_valor=("valor", "max"),
        menor_valor=("valor", "min"),
    )

    resumo = resumo.join(credito_mensal, how="left").join(debito_mensal, how="left")
    resumo[["total_credito", "total_debito"]] = resumo[["total_credito", "total_debito"]].fillna(0.0)
    resumo["saldo"] = resumo["total_credito"] - resumo["total_debito"]

    return resumo.round(2)


def exibir_comparacao(resumo_pandas: pd.DataFrame, relatorio_nativo: dict) -> None:
    """
    Imprime lado a lado os resultados pandas vs. nativo para cada mês.
    """
    print("\n===== RELATÓRIO MENSAL (PANDAS) =====")
    for mes, row in resumo_pandas.iterrows():
        print(f"\nMês: {mes}")
        print(f"  Transações:    {int(row['quantidade'])}")
        print(f"  Total crédito: {formatar_moeda(row['total_credito'])}")
        print(f"  Total débito:  {formatar_moeda(row['total_debito'])}")
        print(f"  Saldo:         {formatar_moeda(row['saldo'])}")
        print(f"  Média:         {formatar_moeda(row['media'])}")
        print(f"  Maior valor:   {formatar_moeda(row['maior_valor'])}")
        print(f"  Menor valor:   {formatar_moeda(row['menor_valor'])}")

    if not relatorio_nativo:
        print("\n(Arquivo relatorio.json não encontrado; comparação pulada.)")
        return

    print("\n===== COMPARAÇÃO PANDAS vs. NATIVO =====")
    todos_iguais = True
    for mes in resumo_pandas.index:
        nativo = relatorio_nativo.get("resumo_mensal", {}).get(mes)
        if not nativo:
            print(f"Mês {mes}: não encontrado no relatório nativo.")
            todos_iguais = False
            continue

        campos = ["total_credito", "total_debito", "saldo", "media", "maior_valor", "menor_valor"]
        for campo in campos:
            val_pandas = round(float(resumo_pandas.loc[mes, campo]), 2)
            val_nativo = round(float(nativo[campo]), 2)
            if val_pandas != val_nativo:
                print(f"  DIVERGÊNCIA em {mes} / {campo}: pandas={val_pandas}, nativo={val_nativo}")
                todos_iguais = False

    if todos_iguais:
        print("RESULTADO: Todos os valores coincidem entre pandas e nativo.")
    else:
        print("RESULTADO: Foram encontradas divergências (verifique acima).")


def main() -> None:
    df = carregar_e_validar_pandas(ARQUIVO_CSV)

    if df.empty:
        print("Nenhuma transação válida encontrada. Encerrando.")
        return

    resumo_pandas = gerar_resumo_mensal_pandas(df)

    # Suspeitas via pandas
    suspeitas = df[df["valor"] > LIMITE_SUSPEITO][["id", "cliente_id", "data", "valor"]]
    print(f"\nTransações suspeitas (valor > {formatar_moeda(LIMITE_SUSPEITO)}): {len(suspeitas)}")
    for _, row in suspeitas.iterrows():
        data_fmt = row["data"].strftime("%Y-%m-%d") if hasattr(row["data"], "strftime") else str(row["data"])
        print(f"  ID: {int(row['id'])} | Cliente: {row['cliente_id']} | Data: {data_fmt} | Valor: {formatar_moeda(row['valor'])}")

    # Carregar relatório nativo para comparação
    try:
        with open(ARQUIVO_JSON, encoding="utf-8") as f:
            relatorio_nativo = json.load(f)
    except FileNotFoundError:
        relatorio_nativo = {}

    exibir_comparacao(resumo_pandas, relatorio_nativo)


if __name__ == "__main__":
    main()
