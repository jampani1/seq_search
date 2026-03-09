#!/usr/bin/env python3
"""
Teste Completo da API de Gene Regulatory Networks
==================================================

Este script testa todo o fluxo da API GRN:
1. Criar uma nova rede
2. Upload de dados de expressão
3. Inferir a rede
4. Consultar o grafo
5. Buscar vizinhos de um gene
6. Encontrar caminho entre genes
7. Obter estatísticas

Uso:
    python test_grn_api.py [--api-url http://localhost:8000]

Requisitos:
    pip install requests rich
"""

import json
import sys
import argparse
from pathlib import Path

try:
    import requests
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
except ImportError:
    print("Instalando dependências...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "rich"])
    import requests
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint

console = Console()


def load_expression_data():
    """Carrega matriz de expressão do arquivo JSON."""
    # Tentar carregar do arquivo
    json_path = Path(__file__).parent.parent / "sporisorium_scitamineum" / "sample_expression_matrix.json"

    if json_path.exists():
        with open(json_path) as f:
            data = json.load(f)
        return {
            "genes": data["genes"],
            "samples": data["samples"],
            "expression_matrix": data["expression_matrix"],
        }

    # Fallback: dados inline
    return {
        "genes": [
            "SPSC_04270", "SPSC_03768", "SPSC_06609", "SPSC_00576", "SPSC_06362",
            "SPSC_05923", "SPSC_01958", "SPSC_04676", "SPSC_02155", "SPSC_04321",
            "SPSC_00606", "SPSC_02450", "SPSC_05681", "SPSC_01622", "SPSC_00571"
        ],
        "samples": [
            "ctrl_0h_1", "ctrl_0h_2", "ctrl_0h_3",
            "inf_12h_1", "inf_12h_2", "inf_12h_3",
            "inf_24h_1", "inf_24h_2", "inf_24h_3",
            "inf_48h_1", "inf_48h_2", "inf_48h_3"
        ],
        "expression_matrix": [
            [1.2, 1.1, 1.3, 5.8, 6.2, 5.5, 12.3, 11.8, 12.9, 25.6, 24.8, 26.1],
            [0.8, 0.9, 0.7, 4.2, 4.5, 4.0, 9.8, 10.2, 9.5, 21.3, 20.8, 22.1],
            [1.0, 1.2, 0.9, 5.1, 5.4, 4.8, 11.2, 10.8, 11.5, 23.4, 22.9, 24.2],
            [0.5, 0.6, 0.4, 3.8, 4.1, 3.5, 8.9, 9.2, 8.6, 18.7, 18.2, 19.4],
            [0.7, 0.8, 0.6, 4.5, 4.8, 4.2, 10.1, 9.8, 10.4, 20.9, 20.4, 21.6],
            [2.1, 2.3, 1.9, 8.5, 9.0, 8.1, 18.2, 17.6, 18.9, 35.8, 34.9, 36.5],
            [1.5, 1.6, 1.4, 6.2, 6.6, 5.9, 13.5, 13.0, 14.1, 27.8, 27.1, 28.6],
            [0.9, 1.0, 0.8, 4.8, 5.1, 4.5, 10.6, 10.2, 11.0, 22.1, 21.5, 22.8],
            [1.8, 2.0, 1.6, 7.2, 7.6, 6.8, 15.4, 14.9, 16.0, 31.2, 30.5, 32.1],
            [1.1, 1.2, 1.0, 5.5, 5.8, 5.2, 11.8, 11.4, 12.3, 24.5, 23.9, 25.2],
            [3.5, 3.2, 3.8, 3.8, 3.5, 4.1, 4.2, 3.9, 4.5, 4.8, 4.5, 5.1],
            [2.8, 2.5, 3.1, 3.0, 2.7, 3.3, 3.4, 3.1, 3.7, 3.9, 3.6, 4.2],
            [4.2, 3.9, 4.5, 4.5, 4.2, 4.8, 4.9, 4.6, 5.2, 5.5, 5.2, 5.8],
            [2.1, 1.9, 2.3, 2.2, 2.0, 2.4, 2.4, 2.2, 2.6, 2.8, 2.6, 3.0],
            [5.5, 5.1, 5.9, 5.8, 5.4, 6.2, 6.2, 5.8, 6.6, 6.8, 6.4, 7.2],
        ]
    }


def test_api(api_url: str):
    """Executa todos os testes da API GRN."""

    console.print(Panel.fit(
        "[bold cyan]Teste da API de Gene Regulatory Networks[/bold cyan]\n"
        f"API URL: {api_url}",
        border_style="cyan"
    ))

    # =========================================
    # 1. CRIAR REDE
    # =========================================
    console.print("\n[bold yellow]1. Criando nova rede...[/bold yellow]")

    network_data = {
        "name": "S. scitamineum Infection GRN",
        "description": "Gene regulatory network during sugarcane smut infection",
        "organism": "Sporisorium scitamineum",
        "method": "correlation",
        "threshold": 0.7,
        "expression_source": "PMC9409688"
    }

    try:
        resp = requests.post(f"{api_url}/api/v1/grn/", json=network_data)
        resp.raise_for_status()
        network = resp.json()
        network_id = network["id"]

        console.print(f"  [green]✓[/green] Rede criada: ID={network_id}")
        console.print(f"    Nome: {network['name']}")
        console.print(f"    Status: {network['status']}")

    except requests.exceptions.ConnectionError:
        console.print(f"  [red]✗ Erro: Não foi possível conectar à API[/red]")
        console.print(f"    Verifique se o backend está rodando em {api_url}")
        console.print("\n    Para iniciar o backend:")
        console.print("      cd backend")
        console.print("      uvicorn app.main:app --reload")
        return False

    except requests.exceptions.HTTPError as e:
        console.print(f"  [red]✗ Erro HTTP: {e.response.status_code}[/red]")
        console.print(f"    {e.response.text}")
        return False

    # =========================================
    # 2. UPLOAD EXPRESSÃO + INFERIR
    # =========================================
    console.print("\n[bold yellow]2. Upload de dados de expressão e inferência...[/bold yellow]")

    expression_data = load_expression_data()
    expression_data["network_id"] = network_id

    try:
        resp = requests.post(
            f"{api_url}/api/v1/grn/{network_id}/expression",
            json=expression_data
        )
        resp.raise_for_status()
        network = resp.json()

        console.print(f"  [green]✓[/green] Inferência concluída!")
        console.print(f"    Status: {network['status']}")
        console.print(f"    Nodes: {network['node_count']}")
        console.print(f"    Edges: {network['edge_count']}")

        if network['status'] == 'failed':
            console.print(f"    [red]Erro: {network.get('error_message', 'Unknown')}[/red]")
            return False

    except requests.exceptions.HTTPError as e:
        console.print(f"  [red]✗ Erro HTTP: {e.response.status_code}[/red]")
        console.print(f"    {e.response.text}")
        return False

    # =========================================
    # 3. BUSCAR GRAFO (CYTOSCAPE FORMAT)
    # =========================================
    console.print("\n[bold yellow]3. Buscando grafo (formato Cytoscape.js)...[/bold yellow]")

    try:
        resp = requests.get(f"{api_url}/api/v1/grn/{network_id}/graph")
        resp.raise_for_status()
        graph = resp.json()

        nodes = graph.get("elements", {}).get("nodes", [])
        edges = graph.get("elements", {}).get("edges", [])

        console.print(f"  [green]✓[/green] Grafo obtido!")
        console.print(f"    Nodes: {len(nodes)}")
        console.print(f"    Edges: {len(edges)}")

        if edges:
            console.print("\n    Top 5 arestas (por peso):")
            sorted_edges = sorted(edges, key=lambda e: abs(e["data"].get("weight", 0)), reverse=True)
            for i, edge in enumerate(sorted_edges[:5]):
                d = edge["data"]
                console.print(f"      {d['source']} -> {d['target']} (weight={d.get('weight', 0):.3f})")

    except requests.exceptions.HTTPError as e:
        console.print(f"  [red]✗ Erro: {e.response.text}[/red]")

    # =========================================
    # 4. ESTATÍSTICAS
    # =========================================
    console.print("\n[bold yellow]4. Obtendo estatísticas da rede...[/bold yellow]")

    try:
        resp = requests.get(f"{api_url}/api/v1/grn/{network_id}/statistics")
        resp.raise_for_status()
        stats = resp.json()

        table = Table(title="Estatísticas da Rede")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="green")

        table.add_row("Nodes", str(stats.get("node_count", 0)))
        table.add_row("Edges", str(stats.get("edge_count", 0)))
        table.add_row("Density", f"{stats.get('density', 0):.4f}")
        table.add_row("Avg Degree", f"{stats.get('avg_degree', 0):.2f}")
        table.add_row("Max In-Degree", str(stats.get("max_in_degree", 0)))
        table.add_row("Max Out-Degree", str(stats.get("max_out_degree", 0)))

        console.print(table)

        if stats.get("top_regulators"):
            console.print("\n    Top Reguladores (hubs):")
            for reg in stats["top_regulators"][:5]:
                console.print(f"      {reg['gene']}: out-degree={reg['out_degree']}")

    except requests.exceptions.HTTPError as e:
        console.print(f"  [red]✗ Erro: {e.response.text}[/red]")

    # =========================================
    # 5. VIZINHOS DE UM GENE
    # =========================================
    test_gene = "SPSC_04270"  # Mig1 - master regulator
    console.print(f"\n[bold yellow]5. Buscando vizinhos de {test_gene}...[/bold yellow]")

    try:
        resp = requests.get(
            f"{api_url}/api/v1/grn/{network_id}/neighbors/{test_gene}",
            params={"depth": 1, "direction": "both"}
        )
        resp.raise_for_status()
        subnetwork = resp.json()

        console.print(f"  [green]✓[/green] Subrede obtida!")
        console.print(f"    Gene central: {subnetwork['center_gene']}")
        console.print(f"    Vizinhos: {len(subnetwork['nodes']) - 1}")
        console.print(f"    Arestas: {len(subnetwork['edges'])}")

        if subnetwork['nodes']:
            console.print("\n    Genes na vizinhança:")
            for node in subnetwork['nodes'][:10]:
                console.print(f"      - {node['id']} ({node['label']})")

    except requests.exceptions.HTTPError as e:
        console.print(f"  [red]✗ Erro: {e.response.text}[/red]")

    # =========================================
    # 6. CAMINHO ENTRE GENES
    # =========================================
    source_gene = "SPSC_04270"
    target_gene = "SPSC_01958"
    console.print(f"\n[bold yellow]6. Buscando caminho: {source_gene} -> {target_gene}...[/bold yellow]")

    try:
        resp = requests.get(
            f"{api_url}/api/v1/grn/{network_id}/path",
            params={"source": source_gene, "target": target_gene, "max_hops": 5}
        )
        resp.raise_for_status()
        path_result = resp.json()

        if path_result["path_found"]:
            console.print(f"  [green]✓[/green] Caminho encontrado!")
            console.print(f"    Comprimento: {path_result['path_length']}")
            console.print(f"    Caminho: {' -> '.join(path_result['path'])}")
        else:
            console.print(f"  [yellow]![/yellow] Nenhum caminho encontrado")

    except requests.exceptions.HTTPError as e:
        console.print(f"  [red]✗ Erro: {e.response.text}[/red]")

    # =========================================
    # 7. LISTAR TODAS AS REDES
    # =========================================
    console.print("\n[bold yellow]7. Listando todas as redes...[/bold yellow]")

    try:
        resp = requests.get(f"{api_url}/api/v1/grn/")
        resp.raise_for_status()
        result = resp.json()

        table = Table(title="Redes Disponíveis")
        table.add_column("ID", style="cyan")
        table.add_column("Nome", style="white")
        table.add_column("Status", style="green")
        table.add_column("Nodes", style="yellow")
        table.add_column("Edges", style="yellow")

        for net in result.get("items", []):
            table.add_row(
                str(net["id"]),
                net["name"][:30],
                net["status"],
                str(net["node_count"]),
                str(net["edge_count"])
            )

        console.print(table)
        console.print(f"    Total: {result.get('total', 0)} redes")

    except requests.exceptions.HTTPError as e:
        console.print(f"  [red]✗ Erro: {e.response.text}[/red]")

    # =========================================
    # RESULTADO FINAL
    # =========================================
    console.print(Panel.fit(
        "[bold green]Todos os testes concluídos![/bold green]\n\n"
        f"Network ID: {network_id}\n"
        f"Visualize em: [cyan]frontend/grn_viewer.html[/cyan]\n\n"
        "Próximos passos:\n"
        "  1. Abra grn_viewer.html no browser\n"
        "  2. Configure Network ID = {network_id}\n"
        "  3. Clique em 'Carregar'",
        border_style="green"
    ))

    return True


def main():
    parser = argparse.ArgumentParser(description="Teste da API GRN")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="URL da API (default: http://localhost:8000)"
    )
    args = parser.parse_args()

    success = test_api(args.api_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
