# Optimization of Wagon Maintenance Mix Allocation in Freight Railways Using Integer Linear Programming

**LVIII SBPO 2026 – Simpósio Brasileiro de Pesquisa Operacional · Poster session**

Carmo Crediney Melo · José Cristiano Pereira · Luciano Moreira da Silva Varricchio · Prudente José Tavares Aguiar · Felipe Machado Lopes · Bruno Malhano de Oliveira Jordão
Universidade Católica de Petrópolis (UCP), Petrópolis, RJ, Brazil

📄 **FAQ page (PT/EN):** https://carmonexus.github.io/wagon-maintenance/
🖼️ **Poster:** [Portuguese](poster/poster_SBPO2026.pdf) · [English](poster/poster_SBPO2026_EN.pdf)

---

## Português

Este repositório contém o código-fonte, os dados de entrada anonimizados e todos os resultados do experimento reprodutível apresentado no artigo. O modelo de programação linear inteira multiperíodo distribui a demanda regional de manutenção de vagões entre postos heterogêneos, considerando tipo de vagão, elegibilidade técnica, capacidade efetiva em homem-hora (HH), custos compostos (manutenção, logística, indisponibilidade e retenção) e backlog.

**Principais resultados na instância de teste (1.004 intervenções, 12 meses, 3 regiões, 3 postos):**

| Indicador | Heurística local | Ótimo PLI |
|---|---|---|
| Vagões atendidos | 965 | 995 |
| Backlog final (vagões) | 39 | 9 |
| Backlog acumulado | — | −54,4 % |
| Custo total do sistema | — | −25,4 % |
| Tempo de solução (1.152 variáveis) | — | < 1 s |

Instância 10× maior (11.520 variáveis) resolvida em menos de 6 s com HiGHS via SciPy.

### Como reproduzir

```bash
pip install -r requirements.txt
cd experiment
python run_experiment.py              # resolve MILP, heurística, relaxação LP e escalabilidade; grava os CSV e PNG
python gerar_figuras_modelagem_en.py  # figura didática das curvas de isocusto
```

Os valores monetários são normalizados e as regiões são anonimizadas. Não há dados proprietários no repositório.

## English

This repository holds the source code, anonymized input data and all outputs of the reproducible experiment reported in the paper. A multi-period integer linear programming model allocates regional wagon-maintenance demand among heterogeneous posts, taking into account wagon type, technical eligibility, effective person-hour capacity, composite costs (maintenance, logistics, transit unavailability and retention) and backlog.

**Main results on the test instance (1,004 interventions, 12 months, 3 regions, 3 posts):**

| Indicator | Local-first heuristic | ILP optimum |
|---|---|---|
| Serviced wagons | 965 | 995 |
| Final backlog (wagons) | 39 | 9 |
| Cumulative backlog | — | −54.4 % |
| Total system cost | — | −25.4 % |
| Solve time (1,152 variables) | — | < 1 s |

A 10× instance (11,520 variables) solves in under 6 s with HiGHS through SciPy.

### How to reproduce

```bash
pip install -r requirements.txt
cd experiment
python run_experiment.py              # MILP, heuristic, LP relaxation and scalability; writes CSV and PNG outputs
python gerar_figuras_modelagem_en.py  # didactic isocost-curve figure
```

See [experiment/README.md](experiment/README.md) for a description of the model, the baseline heuristic and each output file.

## Repository layout

```
index.html          FAQ page served by GitHub Pages (linked from the poster QR code)
experiment/         run_experiment.py, input CSVs, result CSVs and figures
poster/             poster PDF (90 x 140 cm) and preview
requirements.txt    Python dependencies
```

## Citation

Melo, C. C.; Pereira, J. C.; Varricchio, L. M. S.; Aguiar, P. J. T.; Lopes, F. M.; Jordão, B. M. O. (2026). *Optimization of Wagon Maintenance Mix Allocation in Freight Railways Using Integer Linear Programming.* In: Anais do LVIII Simpósio Brasileiro de Pesquisa Operacional (SBPO 2026).

## License

Code and data are released under the [MIT License](LICENSE).
