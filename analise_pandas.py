import json
from datetime import datetime

import pandas as pd

# ── Constants ─────────────────────────────────
MAX_VALUE: float = 10_000.00
CSV_FILE: str = "transacoes.csv"
JSON_FILE: str = "relatorio.json"

def currency_format(value: float) -> str:
    """Format a float to brazil real: R$ 1.840,25"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def load_file_and_validate_data(filepath: str) -> pd.DataFrame:
    """
    Load the csv and apply the same validation rules from notebook
    """

    try:
        dataframe = pd.read_csv(filepath, dtype=str)
    except FileNotFoundError:
        print(f"ERROR: File '{filepath}' not found.")
        return pd.DataFrame()

    transaction_rows = len(dataframe)

    valid_id = dataframe["id"].notna() & dataframe["id"].str.strip().str.match(r"^\d+$")
    valid_client_id = dataframe["cliente_id"].notna() & dataframe["cliente_id"].str.strip().ne("")
    
    dataframe = dataframe[valid_id]
    dataframe = dataframe[valid_client_id]

    dataframe["data"] = pd.to_datetime(dataframe["data"].str.strip(), format="%Y-%m-%d", errors="coerce")
    dataframe = dataframe[dataframe["data"].notna()]

    dataframe["tipo"] = dataframe["tipo"].str.strip().str.lower()
    dataframe = dataframe[dataframe["tipo"].isin(["credito", "debito"])]

    dataframe["valor"] = pd.to_numeric(dataframe["valor"].str.strip(), errors="coerce")
    dataframe = dataframe[dataframe["valor"].notna() & (dataframe["valor"] > 0)]

    dataframe["id"] = dataframe["id"].astype(int)
    dataframe["mes"] = dataframe["data"].dt.strftime("%Y-%m")

    valid_transactions = len(dataframe)
    invalid_transactions = transaction_rows - valid_transactions

    print("===== RESUMO DA LIMPEZA (PANDAS) =====")
    print(f"Total de linhas lidas: {transaction_rows}")
    print(f"Linhas válidas:        {valid_transactions}")
    print(f"Linhas inválidas:      {invalid_transactions}")

    return dataframe


def build_mensal_report(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Group by month and calculate all financial metrics using groupby
    """

    mensal_credit = (
        dataframe[dataframe["tipo"] == "credito"]
        .groupby("mes")["valor"]
        .sum()
        .rename("total_credito")
    )

    mensal_debt = (
        dataframe[dataframe["tipo"] == "debito"]
        .groupby("mes")["valor"]
        .sum()
        .rename("total_debito")
    )

    summary = dataframe.groupby("mes").agg(
        quantidade=("id", "count"),
        media=("valor", "mean"),
        maior_valor=("valor", "max"),
        menor_valor=("valor", "min"),
    )

    summary = summary.join(mensal_credit, how="left").join(mensal_debt, how="left")
    summary[["total_credito", "total_debito"]] = summary[["total_credito", "total_debito"]].fillna(0.0)
    summary["saldo"] = summary["total_credito"] - summary["total_debito"]

    return summary.round(2)


def show_comparison(pandas_summary: pd.DataFrame, notebook_report: dict) -> None:
    """
    Print side by side the results from pandas vs notebook for each month
    """

    print("\n===== RELATÓRIO MENSAL (PANDAS) =====")
    for month, row in pandas_summary.iterrows():
        print(f"\nMês: {month}")
        print(f"  Transações:    {int(row['quantidade'])}")
        print(f"  Total crédito: {currency_format(row['total_credito'])}")
        print(f"  Total débito:  {currency_format(row['total_debito'])}")
        print(f"  Saldo:         {currency_format(row['saldo'])}")
        print(f"  Média:         {currency_format(row['media'])}")
        print(f"  Maior valor:   {currency_format(row['maior_valor'])}")
        print(f"  Menor valor:   {currency_format(row['menor_valor'])}")

    if not notebook_report:
        print("\n(File relatorio.json not found; skipped comparison.)")
        return

    print("\n===== COMPARISON PANDAS vs. NOTEBOOK =====")
    equal = True
    for month in pandas_summary.index:
        notebook = notebook_report.get("resumo_mensal", {}).get(month)
        if not notebook:
            print(f"Mês {month}: not found on notebook report.")
            equal = False
            continue

        fields = ["total_credito", "total_debito", "saldo", "media", "maior_valor", "menor_valor"]
        for field in fields:
            val_pandas = round(float(pandas_summary.loc[month, field]), 2)
            val_notebook = round(float(notebook[field]), 2)
            if val_pandas != val_notebook:
                print(f"  DIVERGENCE on {month} / {field}: pandas={val_pandas}, notebook={val_notebook}")
                equal = False

    if equal:
        print("RESULT: All values match!!")
    else:
        print("RESULT: Was found divergencies")


def main() -> None:
    dataframe = load_file_and_validate_data(CSV_FILE)

    if dataframe.empty:
        print("No valid transaction found.")
        return

    pandas_summary = build_mensal_report(dataframe)

    suspicious_transactions = dataframe[dataframe["valor"] > MAX_VALUE][["id", "cliente_id", "data", "valor"]]
    print(f"\n Suspicious transactions (valor > {currency_format(MAX_VALUE)}): {len(suspicious_transactions)}")
    for _, row in suspicious_transactions.iterrows():
        data_fmt = row["data"].strftime("%Y-%m-%d") if hasattr(row["data"], "strftime") else str(row["data"])
        print(f"  ID: {int(row['id'])} | Cliente: {row['cliente_id']} | Data: {data_fmt} | Valor: {currency_format(row['valor'])}")

    try:
        with open(JSON_FILE, encoding="utf-8") as f:
            notebook_report = json.load(f)
    except FileNotFoundError:
        notebook_report = {}

    show_comparison(pandas_summary, notebook_report)


if __name__ == "__main__":
    main()
