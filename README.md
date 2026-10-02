# Wagon Maintenance Mix – Freight Railway Optimization

Research material on the allocation of freight-wagon maintenance among heterogeneous workshops, developed at the Universidade Católica de Petrópolis (UCP), Petrópolis, RJ, Brazil.

🌐 **Site:** https://carmonexus.github.io/wagon-maintenance/

---

## Português

### O problema

Uma ferrovia de carga mantém uma frota de milhares de vagões de tipos diferentes, distribuídos por várias regiões. A manutenção programada dessa frota precisa ser executada em postos (oficinas) heterogêneos: cada posto só é tecnicamente habilitado para alguns tipos de vagão, tem uma capacidade mensal limitada em homem-hora (HH) e fica a uma distância diferente de cada região.

Decidir **qual posto atende cada parcela da demanda regional em cada mês** envolve um compromisso entre:

- **custo de manutenção** próprio de cada posto;
- **custo logístico** de deslocar o vagão até o posto e de volta;
- **custo de indisponibilidade** do vagão durante o trânsito e a intervenção;
- **custo de retenção (backlog)** quando a demanda não é atendida no mês e se acumula para o mês seguinte.

A prática usual, uma heurística "posto local primeiro", respeita a capacidade de cada oficina mas ignora o efeito acumulado do backlog ao longo do horizonte. O trabalho formula o problema como um modelo de **programação linear inteira multiperíodo** que minimiza o custo total do sistema e mostra, numa instância anonimizada de 12 meses, 3 regiões e 3 postos, redução de 54 % no backlog acumulado e de 25 % no custo total em relação à heurística, com solução em menos de 1 s.

### Trabalhos

| Pasta | Conteúdo |
|---|---|
| [SBPO_2026/](SBPO_2026/) | Artigo e pôster apresentados no LVIII SBPO 2026: página FAQ (PT/EN), código do experimento reprodutível, dados anonimizados, resultados, pôster e slides. **Página:** https://carmonexus.github.io/wagon-maintenance/SBPO_2026/ |

## English

### The problem

A freight railway keeps a fleet of thousands of wagons of different types, spread across several regions. Scheduled maintenance must be carried out at heterogeneous workshops: each workshop is technically eligible for only some wagon types, has a limited monthly person-hour capacity and sits at a different distance from each region.

Deciding **which workshop serves each share of regional demand in each month** trades off:

- the **maintenance cost** of each workshop;
- the **logistics cost** of moving the wagon to the workshop and back;
- the **unavailability cost** of the wagon during transit and intervention;
- the **retention (backlog) cost** when demand is not met in the month and carries over to the next.

Common practice, a "local workshop first" heuristic, respects workshop capacity but ignores the cumulative effect of backlog over the horizon. The work formulates the problem as a **multi-period integer linear programming** model that minimizes total system cost and shows, on an anonymized instance with 12 months, 3 regions and 3 workshops, a 54 % reduction in cumulative backlog and 25 % in total cost against the heuristic, solved in under 1 s.

### Works

| Folder | Contents |
|---|---|
| [SBPO_2026/](SBPO_2026/) | Paper and poster presented at LVIII SBPO 2026: FAQ page (PT/EN), reproducible experiment code, anonymized data, results, poster and slides. **Page:** https://carmonexus.github.io/wagon-maintenance/SBPO_2026/ |

## License

Code and data are released under the [MIT License](LICENSE).
