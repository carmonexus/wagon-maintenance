# Wagon Maintenance – Freight Railways

Research material on freight-wagon maintenance — predictive vibration monitoring (ANPET 2026) and optimal allocation among heterogeneous workshops (SBPO 2026) — developed at the Universidade Católica de Petrópolis (UCP), Petrópolis, RJ, Brazil.

🌐 **Site:** https://carmonexus.github.io/wagon-maintenance/

---

## Português

### Visão geral

A manutenção de uma frota de vagões levanta duas perguntas complementares: **quando um vagão precisa de atenção** (detecção precoce de anomalias pela vibração, trabalho do ANPET 2026) e **onde e quando fazer a manutenção** (alocação entre oficinas, trabalho do SBPO 2026).

### Vibração vertical em vagões (ANPET 2026)

Irregularidades da via excitam a suspensão dos vagões, elevam os esforços dinâmicos na interface roda-trilho e aceleram o desgaste de rodeiros, trilhos e truques. Em casos severos, o processo evolui para falhas como a quebra de rodas em serviço. Detectar cedo essa condição exige uma referência do que é vibração "normal" para o vagão.

O trabalho modela a resposta vertical do vagão como um sistema **massa-mola-amortecedor de um grau de liberdade**, descrito por uma EDO de 2ª ordem, e resolve a equação analiticamente nos regimes:

- **transitório**, logo após o início da excitação (≈ 4 a 5 s);
- **permanente**, em que o vagão acompanha a frequência da via;
- **ressonante**, em que a frequência da via se aproxima da frequência natural do vagão e a amplitude cresce, limitada só pelo amortecimento.

A solução gera referências físicas (frequência natural ωₙ ≈ 1,22 Hz e limiar indicativo de alerta de 0,126 g) para um **monitoramento preditivo distribuído** com acelerômetros na via e identificação dos vagões por RFID. Cruzar as leituras de cada vagão em vários pontos permite separar defeito do vagão de defeito da via.

📁 [ANPET_2026/](ANPET_2026/): página FAQ (PT/EN), slides e link do artigo. **Página:** https://carmonexus.github.io/wagon-maintenance/ANPET_2026/

### Alocação da manutenção (SBPO 2026)

Uma ferrovia de carga mantém milhares de vagões de tipos diferentes, distribuídos por várias regiões. A manutenção programada é feita em postos heterogêneos: cada um é habilitado só para alguns tipos de vagão, tem capacidade mensal limitada em homem-hora e fica a uma distância diferente de cada região.

Decidir **qual posto atende cada parcela da demanda regional em cada mês** envolve um compromisso entre os custos de:

- **manutenção** de cada posto;
- **logística** de deslocar o vagão até o posto e de volta;
- **indisponibilidade** do vagão durante o trânsito e a intervenção;
- **retenção (backlog)**, quando a demanda não é atendida no mês e se acumula.

O trabalho formula o problema como um modelo de **programação linear inteira multiperíodo** que minimiza o custo total. Numa instância anonimizada de 12 meses, 3 regiões e 3 postos, reduziu em 54 % o backlog acumulado e em 25 % o custo total frente à heurística "posto local primeiro", com solução em menos de 1 s.

📁 [SBPO_2026/](SBPO_2026/): página FAQ (PT/EN), código do experimento reprodutível, dados anonimizados, resultados, pôster e slides. **Página:** https://carmonexus.github.io/wagon-maintenance/SBPO_2026/

## English

### Overview

Maintaining a wagon fleet raises two complementary questions: **when does a wagon need attention** (early anomaly detection through vibration, the ANPET 2026 work) and **where and when should maintenance be done** (allocation among workshops, the SBPO 2026 work).

### Vertical vibration in wagons (ANPET 2026)

Track irregularities excite wagon suspensions, raise dynamic wheel-rail forces and speed up wear of wheelsets, rails and bogies. In severe cases the process leads to failures such as wheels breaking in service. Detecting this condition early requires a reference for what "normal" vibration is for the wagon.

The work models the wagon's vertical response as a **single-degree-of-freedom mass-spring-damper**, described by a second-order ODE, and solves it analytically in the:

- **transient** regime, right after excitation starts (≈ 4 to 5 s);
- **steady-state** regime, where the wagon follows the track frequency;
- **resonant** regime, where the track frequency approaches the wagon's natural frequency and amplitude grows, limited only by damping.

The solution yields physical references (natural frequency ωₙ ≈ 1.22 Hz and an indicative 0.126 g alert threshold) for **distributed predictive monitoring** with wayside accelerometers and RFID wagon identification. Cross-checking each wagon's readings at several points separates wagon defects from track defects. The paper is written in Portuguese.

📁 [ANPET_2026/](ANPET_2026/): FAQ page (PT/EN), slides and paper link. **Page:** https://carmonexus.github.io/wagon-maintenance/ANPET_2026/

### Maintenance allocation (SBPO 2026)

A freight railway keeps thousands of wagons of different types, spread across several regions. Scheduled maintenance is done at heterogeneous workshops: each one is eligible for only some wagon types, has a limited monthly person-hour capacity and sits at a different distance from each region.

Deciding **which workshop serves each share of regional demand in each month** trades off the costs of:

- **maintenance** at each workshop;
- **logistics** of moving the wagon to the workshop and back;
- **unavailability** of the wagon during transit and intervention;
- **retention (backlog)**, when demand is not met in the month and carries over.

The work formulates the problem as a **multi-period integer linear programming** model that minimizes total cost. On an anonymized instance with 12 months, 3 regions and 3 workshops, it cut cumulative backlog by 54 % and total cost by 25 % against a "local workshop first" heuristic, solved in under 1 s.

📁 [SBPO_2026/](SBPO_2026/): FAQ page (PT/EN), reproducible experiment code, anonymized data, results, poster and slides. **Page:** https://carmonexus.github.io/wagon-maintenance/SBPO_2026/

## License

Code and data are released under the [MIT License](LICENSE).
