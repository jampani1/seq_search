"""
Data Processing Script for Bioinformatics Hub
==============================================

Processa dados brutos de:
- PHI-base (efetores)
- Sol Genomics GFF (genes N. benthamiana)

Gera JSON estruturado para visualizacao.
"""

import csv
import gzip
import json
import re
from pathlib import Path
from collections import defaultdict

# Paths
RAW_DIR = Path(__file__).parent.parent / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "processed"
PROCESSED_DIR.mkdir(exist_ok=True)


def process_gff(gff_path: Path) -> dict:
    """
    Processa GFF de N. benthamiana.
    Extrai genes com suas posicoes e cromossomos.
    """
    print(f"[*] Processando GFF: {gff_path.name}")

    genes = {}
    gene_count = 0

    with gzip.open(gff_path, 'rt') as f:
        for line in f:
            if line.startswith('#'):
                continue

            parts = line.strip().split('\t')
            if len(parts) < 9:
                continue

            chrom, source, feature, start, end, score, strand, frame, attributes = parts

            if feature != 'gene':
                continue

            # Parse attributes
            attr_dict = {}
            for attr in attributes.split(';'):
                if '=' in attr:
                    key, value = attr.split('=', 1)
                    attr_dict[key] = value

            gene_id = attr_dict.get('ID', '')
            gene_name = attr_dict.get('Name', gene_id)

            genes[gene_id] = {
                'id': gene_id,
                'name': gene_name,
                'chromosome': chrom,
                'start': int(start),
                'end': int(end),
                'strand': strand,
                'source': source
            }
            gene_count += 1

    print(f"    [OK] {gene_count} genes extraidos")
    return genes


def process_phibase(csv_path: Path) -> dict:
    """
    Processa PHI-base CSV.
    Extrai efetores relevantes para Solanaceae/plantas.
    """
    print(f"[*] Processando PHI-base: {csv_path.name}")

    effectors = []
    host_counts = defaultdict(int)
    pathogen_counts = defaultdict(int)

    # Hosts de interesse (Solanaceae e modelo)
    target_hosts = {
        'nicotiana', 'tobacco', 'benthamiana',
        'solanum', 'tomato', 'potato', 'lycopersicum', 'tuberosum',
        'arabidopsis', 'plant'
    }

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        # Skip first header line (contains extra commas)
        next(f)

        reader = csv.DictReader(f)

        for row in reader:
            try:
                host = row.get('Host species', '').lower()
                pathogen = row.get('Pathogen species', '')
                gene_name = row.get('Gene', '')
                phenotype = row.get('Mutant Phenotype', '')
                function = row.get('Gene Function', '')

                # Filtrar por hosts de interesse
                is_target = any(h in host for h in target_hosts)

                if is_target and gene_name:
                    effector = {
                        'record_id': row.get('Record ID', ''),
                        'gene': gene_name,
                        'protein_id': row.get('Protein ID', ''),
                        'pathogen': pathogen,
                        'pathogen_id': row.get('Pathogen ID', ''),
                        'host': row.get('Host species', ''),
                        'disease': row.get('Disease', ''),
                        'phenotype': phenotype,
                        'function': function,
                        'go_annotation': row.get('GO annotation', ''),
                        'pathway': row.get('Pathway', ''),
                        'host_target': row.get('Host target', ''),
                        'interaction_phenotype': row.get('Interaction phenotype', ''),
                        'pmid': row.get('PMID', '')
                    }
                    effectors.append(effector)
                    host_counts[row.get('Host species', 'Unknown')] += 1
                    pathogen_counts[pathogen] += 1

            except Exception as e:
                continue

    print(f"    [OK] {len(effectors)} efetores relevantes para plantas")
    print(f"    Top patogenos: {dict(sorted(pathogen_counts.items(), key=lambda x: -x[1])[:5])}")

    return {
        'effectors': effectors,
        'host_stats': dict(host_counts),
        'pathogen_stats': dict(pathogen_counts)
    }


def create_defense_network() -> dict:
    """
    Cria rede de defesa curada manualmente baseada na literatura.
    Genes core de PTI/ETI bem caracterizados.
    """
    print("[*] Criando rede de defesa curada...")

    # Genes de defesa bem caracterizados
    defense_genes = [
        # PRRs
        {"id": "FLS2", "name": "Flagellin Sensing 2", "category": "PRR", "location": "membrane", "description": "Receptor de flagelina bacteriana"},
        {"id": "EFR", "name": "EF-Tu Receptor", "category": "PRR", "location": "membrane", "description": "Receptor de EF-Tu bacteriano"},
        {"id": "CERK1", "name": "Chitin Elicitor Receptor Kinase 1", "category": "PRR", "location": "membrane", "description": "Receptor de quitina fungica"},
        {"id": "BAK1", "name": "BRI1-Associated Kinase 1", "category": "PRR", "location": "membrane", "description": "Co-receptor universal de PRRs"},

        # RLCKs
        {"id": "BIK1", "name": "Botrytis-Induced Kinase 1", "category": "RLCK", "location": "membrane", "description": "Quinase ativada por PRRs"},

        # MAPK Cascade
        {"id": "MEKK1", "name": "MAPKKK 1", "category": "MAPK", "location": "cytoplasm", "description": "MAPKKK da cascata MPK4"},
        {"id": "MKK1", "name": "MAP Kinase Kinase 1", "category": "MAPK", "location": "cytoplasm", "description": "MAPKK upstream de MPK4"},
        {"id": "MKK4", "name": "MAP Kinase Kinase 4", "category": "MAPK", "location": "cytoplasm", "description": "MAPKK upstream de MPK3/6"},
        {"id": "MKK5", "name": "MAP Kinase Kinase 5", "category": "MAPK", "location": "cytoplasm", "description": "MAPKK upstream de MPK3/6"},
        {"id": "MPK3", "name": "MAP Kinase 3", "category": "MAPK", "location": "cytoplasm", "description": "MAPK de defesa, fosforila WRKYs"},
        {"id": "MPK4", "name": "MAP Kinase 4", "category": "MAPK", "location": "cytoplasm", "description": "MAPK regulador negativo"},
        {"id": "MPK6", "name": "MAP Kinase 6", "category": "MAPK", "location": "cytoplasm", "description": "MAPK de defesa, fosforila WRKYs"},

        # ROS
        {"id": "RBOHD", "name": "Respiratory Burst Oxidase D", "category": "Oxidase", "location": "membrane", "description": "NADPH oxidase, produz ROS"},

        # Transcription Factors
        {"id": "WRKY33", "name": "WRKY33", "category": "TF", "location": "nucleus", "description": "TF de defesa, alvo de MPK3/6"},
        {"id": "WRKY22", "name": "WRKY22", "category": "TF", "location": "nucleus", "description": "TF responsivo a PTI"},
        {"id": "WRKY29", "name": "WRKY29", "category": "TF", "location": "nucleus", "description": "TF responsivo a flagelina"},
        {"id": "MYC2", "name": "MYC2", "category": "TF", "location": "nucleus", "description": "TF master de JA signaling"},
        {"id": "NPR1", "name": "NPR1", "category": "TF", "location": "nucleus", "description": "Receptor de SA, ativa PR genes"},
        {"id": "TGA1", "name": "TGA1", "category": "TF", "location": "nucleus", "description": "TF que interage com NPR1"},

        # SA pathway
        {"id": "ICS1", "name": "Isochorismate Synthase 1", "category": "Biosynthesis", "location": "chloroplast", "description": "Biossintese de SA"},
        {"id": "EDS5", "name": "Enhanced Disease Susceptibility 5", "category": "Transporter", "location": "chloroplast", "description": "Exportador de SA do cloroplasto"},

        # JA pathway
        {"id": "LOX2", "name": "Lipoxygenase 2", "category": "Biosynthesis", "location": "chloroplast", "description": "Biossintese de JA"},
        {"id": "AOS", "name": "Allene Oxide Synthase", "category": "Biosynthesis", "location": "chloroplast", "description": "Biossintese de JA"},
        {"id": "COI1", "name": "Coronatine Insensitive 1", "category": "Receptor", "location": "nucleus", "description": "Receptor de JA-Ile"},
        {"id": "JAZ1", "name": "Jasmonate ZIM-domain 1", "category": "Repressor", "location": "nucleus", "description": "Repressor de JA signaling"},

        # Defense genes
        {"id": "PR1", "name": "Pathogenesis-Related 1", "category": "Defense", "location": "apoplast", "description": "Marcador de SA, antimicrobiano"},
        {"id": "PR2", "name": "Pathogenesis-Related 2", "category": "Defense", "location": "apoplast", "description": "Beta-1,3-glucanase"},
        {"id": "PR5", "name": "Pathogenesis-Related 5", "category": "Defense", "location": "apoplast", "description": "Thaumatin-like protein"},
        {"id": "PDF1.2", "name": "Plant Defensin 1.2", "category": "Defense", "location": "apoplast", "description": "Defensina, marcador de JA"},
        {"id": "FRK1", "name": "FLG22-induced Receptor Kinase 1", "category": "Defense", "location": "membrane", "description": "Marcador de PTI"},

        # NLRs
        {"id": "NRC2", "name": "NLR Required for Cell death 2", "category": "NLR", "location": "cytoplasm", "description": "Helper NLR"},
        {"id": "NRC3", "name": "NLR Required for Cell death 3", "category": "NLR", "location": "cytoplasm", "description": "Helper NLR"},
        {"id": "NRC4", "name": "NLR Required for Cell death 4", "category": "NLR", "location": "cytoplasm", "description": "Helper NLR"},
        {"id": "NRG1", "name": "N Requirement Gene 1", "category": "NLR", "location": "cytoplasm", "description": "Helper NLR tipo TNL"},

        # Effector targets
        {"id": "RIN4", "name": "RPM1-Interacting protein 4", "category": "Target", "location": "membrane", "description": "Alvo de AvrRpm1/AvrB/AvrRpt2"},
        {"id": "C14", "name": "Cysteine Protease 14", "category": "Target", "location": "apoplast", "description": "Alvo de AVRblb2"},
    ]

    # Interacoes bem documentadas
    interactions = [
        # PTI signaling
        {"source": "FLS2", "target": "BAK1", "type": "activation", "weight": 0.95, "evidence": "experimental"},
        {"source": "EFR", "target": "BAK1", "type": "activation", "weight": 0.95, "evidence": "experimental"},
        {"source": "CERK1", "target": "BAK1", "type": "activation", "weight": 0.90, "evidence": "experimental"},
        {"source": "BAK1", "target": "BIK1", "type": "activation", "weight": 0.90, "evidence": "experimental"},
        {"source": "BIK1", "target": "RBOHD", "type": "activation", "weight": 0.85, "evidence": "phosphorylation"},
        {"source": "BIK1", "target": "MKK4", "type": "activation", "weight": 0.80, "evidence": "experimental"},

        # MAPK cascade
        {"source": "MEKK1", "target": "MKK1", "type": "activation", "weight": 0.90, "evidence": "experimental"},
        {"source": "MKK1", "target": "MPK4", "type": "activation", "weight": 0.90, "evidence": "phosphorylation"},
        {"source": "MKK4", "target": "MPK3", "type": "activation", "weight": 0.90, "evidence": "phosphorylation"},
        {"source": "MKK4", "target": "MPK6", "type": "activation", "weight": 0.90, "evidence": "phosphorylation"},
        {"source": "MKK5", "target": "MPK3", "type": "activation", "weight": 0.90, "evidence": "phosphorylation"},
        {"source": "MKK5", "target": "MPK6", "type": "activation", "weight": 0.90, "evidence": "phosphorylation"},

        # MAPK to TFs
        {"source": "MPK3", "target": "WRKY33", "type": "activation", "weight": 0.88, "evidence": "phosphorylation"},
        {"source": "MPK6", "target": "WRKY33", "type": "activation", "weight": 0.88, "evidence": "phosphorylation"},
        {"source": "MPK4", "target": "WRKY33", "type": "repression", "weight": -0.70, "evidence": "experimental"},

        # TF to genes
        {"source": "WRKY33", "target": "PR1", "type": "activation", "weight": 0.75, "evidence": "ChIP"},
        {"source": "WRKY29", "target": "FRK1", "type": "activation", "weight": 0.80, "evidence": "ChIP"},
        {"source": "NPR1", "target": "TGA1", "type": "activation", "weight": 0.85, "evidence": "experimental"},
        {"source": "TGA1", "target": "PR1", "type": "activation", "weight": 0.85, "evidence": "ChIP"},
        {"source": "TGA1", "target": "PR2", "type": "activation", "weight": 0.80, "evidence": "ChIP"},
        {"source": "TGA1", "target": "PR5", "type": "activation", "weight": 0.80, "evidence": "ChIP"},

        # SA pathway
        {"source": "ICS1", "target": "EDS5", "type": "activation", "weight": 0.90, "evidence": "biochemical"},
        {"source": "EDS5", "target": "NPR1", "type": "activation", "weight": 0.85, "evidence": "genetic"},

        # JA pathway
        {"source": "LOX2", "target": "AOS", "type": "activation", "weight": 0.90, "evidence": "biochemical"},
        {"source": "COI1", "target": "JAZ1", "type": "repression", "weight": -0.95, "evidence": "degradation"},
        {"source": "JAZ1", "target": "MYC2", "type": "repression", "weight": -0.90, "evidence": "experimental"},
        {"source": "MYC2", "target": "PDF1.2", "type": "activation", "weight": 0.85, "evidence": "ChIP"},

        # SA-JA crosstalk
        {"source": "NPR1", "target": "MYC2", "type": "repression", "weight": -0.70, "evidence": "genetic"},

        # NLR network
        {"source": "NRC2", "target": "NRC3", "type": "activation", "weight": 0.80, "evidence": "genetic"},
        {"source": "NRC3", "target": "NRC4", "type": "activation", "weight": 0.80, "evidence": "genetic"},
        {"source": "NRG1", "target": "NRC2", "type": "activation", "weight": 0.75, "evidence": "genetic"},
    ]

    print(f"    [OK] {len(defense_genes)} genes, {len(interactions)} interacoes")

    return {
        "genes": defense_genes,
        "interactions": interactions
    }


def main():
    print("=" * 50)
    print("PROCESSAMENTO DE DADOS - Bioinformatics Hub")
    print("=" * 50)
    print()

    # 1. Processar GFF
    gff_path = RAW_DIR / "Niben_gene_models.gff.gz"
    if gff_path.exists():
        genes = process_gff(gff_path)
        with open(PROCESSED_DIR / "nbenthamiana_genes.json", 'w') as f:
            json.dump(genes, f, indent=2)
        print(f"    Salvo: nbenthamiana_genes.json")

    # 2. Processar PHI-base
    phibase_path = RAW_DIR / "phi-base_current.csv"
    if phibase_path.exists():
        phibase_data = process_phibase(phibase_path)
        with open(PROCESSED_DIR / "phibase_plant_effectors.json", 'w') as f:
            json.dump(phibase_data, f, indent=2)
        print(f"    Salvo: phibase_plant_effectors.json")

    # 3. Criar rede de defesa curada
    defense_network = create_defense_network()
    with open(PROCESSED_DIR / "defense_network.json", 'w') as f:
        json.dump(defense_network, f, indent=2)
    print(f"    Salvo: defense_network.json")

    print()
    print("=" * 50)
    print("PROCESSAMENTO CONCLUIDO!")
    print("=" * 50)

    # Summary
    print(f"\nArquivos gerados em: {PROCESSED_DIR}")
    for f in PROCESSED_DIR.glob("*.json"):
        size = f.stat().st_size / 1024
        print(f"  - {f.name}: {size:.1f} KB")


if __name__ == "__main__":
    main()
