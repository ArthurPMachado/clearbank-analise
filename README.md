# ClearBank – Análise Financeira de Transações

Projeto de análise de dados financeiros desenvolvido para a fintech **ClearBank**.  
Processa um arquivo CSV de transações mensais, valida os dados, gera métricas financeiras, identifica transações suspeitas, exporta um relatório em JSON e um grafico de barras empilhado sobre o credito e debito mensal

## Estrutura do Projeto

```
ftr-analise-financeira/
├── desafio-final.ipynb   # Notebook principal com toda a solução
├── transacoes.csv        # Arquivo de entrada com os dados das transações
├── relatorio.json        # Gerado pelo notebook após execução
├── grafico.png           # Gerado pelo notebook usando matplotlib
├── analise_pandas.py     # Análise alternativa com pandas
└── README.md             # Este arquivo
```

## Pré-requisitos

- Python 3.10 ou superior
- Jupyter Notebook ou Google Colab
- Para a geração do gráfico e analise alternativa com pandas é necessario instalar os pacotes: `pip install pandas matplotlib`

## Como Executar

### Jupyter Notebook (local)

1. Certifique-se de que `transacoes.csv` está na mesma pasta do notebook.
2. Abra o terminal na pasta do projeto e execute:
   ```bash
   jupyter notebook desafio-final.ipynb
   ```
3. No Jupyter, clique em **Kernel → Restart & Run All** para executar todas as células em ordem.

### Google Colab

1. Faça upload do notebook `desafio-final.ipynb` e do arquivo `transacoes.csv` no Colab.
2. Clique em **Runtime → Run all** (ou `Ctrl+F9`).

### Análise com pandas

Após executar o notebook principal (para gerar o `relatorio.json`), execute:

```bash
python analise_pandas.py
```

## O que o notebook gera

| Arquivo | Descrição |
|---------|-----------|
| `relatorio.json` | Relatório completo com métricas mensais e transações suspeitas |
| `grafico.png` | Gráfico de barras empilhadas com crédito e débito por mês |

### Exemplo de saída no terminal

```
===== RESUMO DA LIMPEZA =====
Total de linhas lidas: 30
Linhas válidas:        24
Linhas inválidas:      6

===== RELATÓRIO MENSAL =====

Mês: 2026-01
  Transações:    4
  Total crédito: R$ 16.000,00
  Total débito:  R$ 719,90
  Saldo:         R$ 15.280,10
  ...

===== TRANSAÇÕES SUSPEITAS =====
ID: 5 | Cliente: CLI004 | Data: 2026-01-28 | Valor: R$ 12.500,00
```

## Regras de Validação

Linhas do CSV são descartadas silenciosamente quando:

- `id` está vazio ou não é numérico
- `cliente_id` está vazio
- `data` não está no formato `AAAA-MM-DD`
- `tipo` é diferente de `credito` ou `debito`
- `valor` não é numérico ou é menor ou igual a zero

## Tecnologias Utilizadas

- **Python 3.14.5+** – linguagem principal
- **csv** (nativo) – leitura do arquivo de transações
- **datetime** (nativo) – manipulação e validação de datas
- **json** (nativo) – exportar o relatório
- **pandas** – análise alternativa (opcional)
- **matplotlib** – geração de gráfico (opcional)
