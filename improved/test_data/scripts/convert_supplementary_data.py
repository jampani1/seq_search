#!/usr/bin/env python3
"""
Conversor de Dados Suplementares -> Formato API GRN
===================================================

Este script extrai dados do Excel suplementar (PMC9409688) e converte
para o formato JSON aceito pela API de Gene Regulatory Networks.

Dados extraídos:
- Table S2: Informações das amostras RNA-seq
- Table S3: Genes do módulo MEpurple (GO enrichment)
- Table S4: Genes com match no PHI-base
- Table S5: Efetores candidatos

Uso:
    python convert_supplementary_data.py

Output:
    - real_expression_data.json (para API /grn/{id}/expression)
    - real_genes_modules.json (lista de genes por módulo)
    - real_effectors.json (efetores candidatos)
"""

import json
import re
from pathlib import Path

import pandas as pd

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "sporisorium_scitamineum"
EXCEL_FILE = DATA_DIR / "supplementary_data.xlsx"
OUTPUT_DIR = DATA_DIR


def extract_genes_from_go_terms(df):
    """Extrai lista única de genes da coluna de GO terms."""
    genes = set()

    # A coluna com genes é a última (Unnamed: 7)
    gene_col = df.columns[-1]

    for value in df[gene_col].dropna():
        if isinstance(value, str) and value.startswith('SPSC_'):
            # Split por vírgula e limpa
            for gene in value.split(','):
                gene = gene.strip()
                if gene.startswith('SPSC_'):
                    genes.add(gene)

    return sorted(genes)


def extract_phi_genes(df):
    """Extrai genes com match no PHI-base."""
    genes_info = []

    for _, row in df.iterrows():
        gene_col = row.iloc[1]  # Gene column
        if pd.isna(gene_col) or not isinstance(gene_col, str):
            continue

        # Pode ter múltiplos genes separados por ;
        for gene in str(gene_col).split(';'):
            gene = gene.strip()
            if gene.startswith('SPSC_'):
                genes_info.append({
                    'gene_id': gene,
                    'phi_id': str(row.iloc[0]) if pd.notna(row.iloc[0]) else None,
                    'pathogen': str(row.iloc[2]) if pd.notna(row.iloc[2]) else None,
                    'phenotype': str(row.iloc[3]) if pd.notna(row.iloc[3]) else None,
                    'function': str(row.iloc[5]) if pd.notna(row.iloc[5]) else None,
                })

    return genes_info


def extract_effector_candidates(df):
    """Extrai efetores candidatos."""
    effectors = []

    for _, row in df.iterrows():
        gene_id = row.iloc[0]
        if pd.isna(gene_id) or not str(gene_id).startswith('SPSC_'):
            continue

        effectors.append({
            'gene_id': str(gene_id),
            'annotation': str(row.iloc[1]) if pd.notna(row.iloc[1]) else None,
            'protein_length': int(row.iloc[2]) if pd.notna(row.iloc[2]) else None,
            'cysteine_percent': float(row.iloc[3]) if pd.notna(row.iloc[3]) else None,
            'signal_peptide_prob': float(row.iloc[4]) if pd.notna(row.iloc[4]) else None,
            'location': str(row.iloc[6]) if pd.notna(row.iloc[6]) else None,
            'tm_domains': int(row.iloc[7]) if pd.notna(row.iloc[7]) else 0,
        })

    return effectors


def extract_sample_info(df):
    """Extrai informações das amostras."""
    samples = []

    for _, row in df.iterrows():
        sample_name = row.iloc[0]
        if pd.isna(sample_name) or sample_name == 'Sample':
            continue

        samples.append({
            'name': str(sample_name),
            'raw_reads': int(row.iloc[2]) if pd.notna(row.iloc[2]) else None,
            'clean_reads': int(row.iloc[3]) if pd.notna(row.iloc[3]) else None,
            'q30': float(row.iloc[4]) if pd.notna(row.iloc[4]) else None,
            'gc_content': float(row.iloc[5]) if pd.notna(row.iloc[5]) else None,
        })

    return samples


def generate_expression_matrix(genes, samples):
    """
    Gera matriz de expressão simulada baseada nos padrões do estudo.

    Padrões observados:
    - Genes do módulo MEpurple: induzidos durante infecção (aumentam com tempo)
    - Genes do módulo MEdarkturquoise: expressão mais estável
    """
    import random
    random.seed(42)  # Reprodutibilidade

    matrix = []

    for i, gene in enumerate(genes):
        row = []

        # Determinar padrão baseado no índice (simular módulos)
        is_induced = i < len(genes) // 2  # Primeira metade = induzido

        for sample in samples:
            # Extrair timepoint do nome da amostra
            if '0h' in sample['name']:
                time_factor = 1.0
            elif '24h' in sample['name']:
                time_factor = 3.0 if is_induced else 1.1
            elif '72h' in sample['name']:
                time_factor = 8.0 if is_induced else 1.2
            elif '168h' in sample['name']:
                time_factor = 15.0 if is_induced else 1.3
            else:
                time_factor = 1.0

            # Valor base + variação + ruído
            base_value = random.uniform(0.5, 2.0)
            noise = random.uniform(0.8, 1.2)

            expression = base_value * time_factor * noise
            row.append(round(expression, 2))

        matrix.append(row)

    return matrix


def main():
    print("=" * 60)
    print("Conversor de Dados Suplementares -> Formato API GRN")
    print("=" * 60)
    print()

    if not EXCEL_FILE.exists():
        print(f"ERRO: Arquivo não encontrado: {EXCEL_FILE}")
        print("Execute primeiro o download dos dados suplementares.")
        return

    # Carregar Excel
    print(f"Carregando: {EXCEL_FILE}")
    xl = pd.ExcelFile(EXCEL_FILE)
    print(f"Sheets encontrados: {xl.sheet_names}")
    print()

    # ===========================================
    # 1. Extrair informações das amostras (Table S2)
    # ===========================================
    print("[1/4] Extraindo informações das amostras...")
    df_samples = pd.read_excel(xl, sheet_name='Table S2', header=None)
    samples = extract_sample_info(df_samples)
    print(f"      Amostras encontradas: {len(samples)}")

    # ===========================================
    # 2. Extrair genes do módulo MEpurple (Table S3)
    # ===========================================
    print("[2/4] Extraindo genes do módulo MEpurple...")
    df_go = pd.read_excel(xl, sheet_name='Table S3', header=None)
    mepurple_genes = extract_genes_from_go_terms(df_go)
    print(f"      Genes MEpurple: {len(mepurple_genes)}")

    # ===========================================
    # 3. Extrair genes PHI-base (Table S4)
    # ===========================================
    print("[3/4] Extraindo genes com match no PHI-base...")
    df_phi = pd.read_excel(xl, sheet_name='Table S4', header=None)
    phi_genes = extract_phi_genes(df_phi)
    print(f"      Genes PHI-base: {len(phi_genes)}")

    # ===========================================
    # 4. Extrair efetores candidatos (Table S5)
    # ===========================================
    print("[4/4] Extraindo efetores candidatos...")
    df_effectors = pd.read_excel(xl, sheet_name='Table S5', header=None)
    effectors = extract_effector_candidates(df_effectors)
    print(f"      Efetores candidatos: {len(effectors)}")

    print()

    # ===========================================
    # Combinar genes únicos
    # ===========================================
    all_genes = set(mepurple_genes)
    for eg in phi_genes:
        all_genes.add(eg['gene_id'])
    for ef in effectors:
        all_genes.add(ef['gene_id'])

    all_genes = sorted(all_genes)
    print(f"Total de genes únicos: {len(all_genes)}")

    # ===========================================
    # Gerar matriz de expressão
    # ===========================================
    print("Gerando matriz de expressão...")
    sample_names = [s['name'] for s in samples]
    expression_matrix = generate_expression_matrix(all_genes, samples)

    # ===========================================
    # Salvar arquivos JSON
    # ===========================================
    print()
    print("Salvando arquivos...")

    # 1. Expression data (para API)
    expression_output = {
        "metadata": {
            "source": "PMC9409688 - Tao et al. 2022",
            "organism": "Sporisorium scitamineum",
            "description": "Gene expression during sugarcane infection",
            "note": "Expression values simulated based on study patterns"
        },
        "network_config": {
            "name": "S. scitamineum Real Data GRN",
            "organism": "Sporisorium scitamineum",
            "method": "correlation",
            "threshold": 0.7,
            "expression_source": "PMC9409688"
        },
        "genes": all_genes,
        "samples": sample_names,
        "expression_matrix": expression_matrix
    }

    output_file = OUTPUT_DIR / "real_expression_data.json"
    with open(output_file, 'w') as f:
        json.dump(expression_output, f, indent=2)
    print(f"  -> {output_file}")

    # 2. Genes por módulo
    modules_output = {
        "MEpurple": {
            "genes": mepurple_genes,
            "description": "Genes induced during infection, ER stress response"
        },
        "phi_base_matches": phi_genes,
        "statistics": {
            "total_mepurple": len(mepurple_genes),
            "total_phi_matches": len(phi_genes),
            "total_unique_genes": len(all_genes)
        }
    }

    output_file = OUTPUT_DIR / "real_genes_modules.json"
    with open(output_file, 'w') as f:
        json.dump(modules_output, f, indent=2)
    print(f"  -> {output_file}")

    # 3. Efetores candidatos
    effectors_output = {
        "source": "PMC9409688 Table S5",
        "total": len(effectors),
        "effectors": effectors
    }

    output_file = OUTPUT_DIR / "real_effectors.json"
    with open(output_file, 'w') as f:
        json.dump(effectors_output, f, indent=2)
    print(f"  -> {output_file}")

    # ===========================================
    # Resumo
    # ===========================================
    print()
    print("=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Amostras RNA-seq:     {len(samples)}")
    print(f"Genes MEpurple:       {len(mepurple_genes)}")
    print(f"Genes PHI-base:       {len(phi_genes)}")
    print(f"Efetores candidatos:  {len(effectors)}")
    print(f"Total genes únicos:   {len(all_genes)}")
    print()
    print("Arquivos gerados:")
    print("  - real_expression_data.json  (para /api/v1/grn/{id}/expression)")
    print("  - real_genes_modules.json    (genes por módulo)")
    print("  - real_effectors.json        (efetores candidatos)")
    print()
    print("Próximo passo:")
    print("  python test_grn_api.py --use-real-data")


if __name__ == "__main__":
    main()
