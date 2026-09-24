#!/usr/bin/env python3
"""Reproducible multi-period wagon-maintenance allocation experiment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


BASE_DIR = Path(__file__).resolve().parent
MONTH_WEIGHTS = np.array(
    [0.075, 0.080, 0.085, 0.080, 0.090, 0.085,
     0.090, 0.080, 0.085, 0.085, 0.080, 0.085]
)
DAILY_UNAVAILABILITY_COST = 6.0
DAILY_RETENTION_COST = 3.0
FINAL_BACKLOG_MULTIPLIER = 4.0
WORKLOAD_SCALE = 1


@dataclass
class ModelSolution:
    name: str
    result: object
    allocation: pd.DataFrame
    backlog: pd.DataFrame
    capacity_use: pd.DataFrame
    runtime_seconds: float
    n_variables: int
    n_constraints: int


def largest_remainder(total: int, weights: np.ndarray) -> np.ndarray:
    raw = total * weights / weights.sum()
    base = np.floor(raw).astype(int)
    missing = total - int(base.sum())
    if missing:
        order = np.argsort(-(raw - base), kind="stable")
        base[order[:missing]] += 1
    return base


def load_inputs():
    demand = pd.read_csv(BASE_DIR / "scope_demand.csv")
    scope = pd.read_csv(BASE_DIR / "scope_parameters.csv")
    workshops = pd.read_csv(BASE_DIR / "workshops.csv")
    shares = pd.read_csv(BASE_DIR / "region_shares.csv")
    logistics = pd.read_csv(BASE_DIR / "logistics.csv")
    workshop_scope = pd.read_csv(BASE_DIR / "workshop_scope.csv")
    availability = pd.read_csv(BASE_DIR / "availability.csv")
    return demand, scope, workshops, shares, logistics, workshop_scope, availability


def build_monthly_demand(demand: pd.DataFrame, shares: pd.DataFrame) -> pd.DataFrame:
    rows = []
    region_weights = shares["share"].to_numpy(float)
    regions = shares["region"].tolist()
    for item in demand.itertuples(index=False):
        regional = largest_remainder(int(item.annual_demand), region_weights)
        for region, region_total in zip(regions, regional):
            monthly = largest_remainder(int(region_total), MONTH_WEIGHTS)
            group_id = f"{region}-{item.wagon_type}-{item.scope_family}"
            for month, value in enumerate(monthly, start=1):
                rows.append(
                    {
                        "month": month,
                        "group_id": group_id,
                        "origin_region": region,
                        "scope_type": item.scope_type,
                        "wagon_type": item.wagon_type,
                        "scope_family": item.scope_family,
                        "demand": int(value),
                    }
                )
    return pd.DataFrame(rows)


def build_capacity(workshops: pd.DataFrame, availability: pd.DataFrame) -> pd.DataFrame:
    capacity = availability.merge(workshops, on="workshop", how="left")
    capacity["maximum_hh"] = np.floor(
        capacity["nominal_maximum_hh"] * capacity["availability_factor"]
    ).astype(int)
    capacity["minimum_hh"] = np.minimum(
        capacity["minimum_hh"], capacity["maximum_hh"]
    ).astype(int)
    capacity["minimum_units"] = np.floor(
        capacity["minimum_hh"] * WORKLOAD_SCALE
    ).astype(int)
    capacity["maximum_units"] = np.floor(
        capacity["maximum_hh"] * WORKLOAD_SCALE
    ).astype(int)
    return capacity


def cost_table(
    scope: pd.DataFrame,
    workshops: pd.DataFrame,
    logistics: pd.DataFrame,
    workshop_scope: pd.DataFrame,
) -> pd.DataFrame:
    regions = logistics[["origin_region"]].drop_duplicates()
    table = (
        workshop_scope.merge(workshops, on="workshop", how="left")
        .merge(scope, on="scope_type", how="left")
        .merge(regions, how="cross")
        .merge(logistics, on=["origin_region", "workshop"], how="left")
    )
    table["transit_unavailability_cost"] = (
        table["transit_days"] * DAILY_UNAVAILABILITY_COST
    )
    table["retention_cost"] = (
        table["service_days"] * DAILY_RETENTION_COST
        + table["third_party"] * 5.0
    )
    table["composite_cost"] = (
        table["direct_cost"]
        + table["logistics_cost"]
        + table["transit_unavailability_cost"]
        + table["retention_cost"]
    )
    return table


def expand_instance(
    monthly_demand: pd.DataFrame,
    capacity: pd.DataFrame,
    factor: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if factor == 1:
        return monthly_demand.copy(), capacity.copy()
    demand_parts = []
    for replica in range(1, factor + 1):
        part = monthly_demand.copy()
        part["group_id"] = part["group_id"] + f"-G{replica:02d}"
        demand_parts.append(part)
    expanded_capacity = capacity.copy()
    expanded_capacity["minimum_hh"] *= factor
    expanded_capacity["maximum_hh"] *= factor
    expanded_capacity["minimum_units"] *= factor
    expanded_capacity["maximum_units"] *= factor
    return pd.concat(demand_parts, ignore_index=True), expanded_capacity


def solve_model(
    name: str,
    monthly_demand: pd.DataFrame,
    scope: pd.DataFrame,
    capacity: pd.DataFrame,
    costs: pd.DataFrame,
    *,
    use_composite_cost: bool = True,
    enforce_eligibility: bool = True,
    enforce_minimum: bool = True,
    integer: bool = True,
    time_limit: float = 120.0,
    mip_rel_gap: float = 1e-4,
) -> ModelSolution:
    scope_info = scope.set_index("scope_type").to_dict("index")
    cost_lookup = costs.set_index(
        ["origin_region", "scope_type", "workshop"]
    ).to_dict("index")
    demand_lookup = monthly_demand.set_index(
        ["month", "group_id", "origin_region", "scope_type"]
    )["demand"].to_dict()
    groups = sorted(
        monthly_demand[["group_id", "origin_region", "scope_type"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    workshops = sorted(capacity["workshop"].unique())
    months = sorted(monthly_demand["month"].unique())

    x_keys = []
    for month in months:
        for group_id, origin, scope_type in groups:
            for workshop in workshops:
                info = cost_lookup[(origin, scope_type, workshop)]
                if enforce_eligibility and int(info["eligible"]) == 0:
                    continue
                x_keys.append((month, group_id, origin, scope_type, workshop))
    q_keys = [
        (month, group_id, origin, scope_type)
        for month in months
        for group_id, origin, scope_type in groups
    ]
    all_keys = [("x",) + key for key in x_keys] + [("q",) + key for key in q_keys]
    index = {key: i for i, key in enumerate(all_keys)}

    cumulative_demand = {}
    for group_id, origin, scope_type in groups:
        running = 0
        for month in months:
            running += int(demand_lookup[(month, group_id, origin, scope_type)])
            cumulative_demand[(month, group_id, origin, scope_type)] = running

    variable_upper = np.full(len(all_keys), np.inf, dtype=float)
    for month, group_id, origin, scope_type, workshop in x_keys:
        variable_upper[index[("x", month, group_id, origin, scope_type, workshop)]] = (
            cumulative_demand[(month, group_id, origin, scope_type)]
        )
    for month, group_id, origin, scope_type in q_keys:
        variable_upper[index[("q", month, group_id, origin, scope_type)]] = (
            cumulative_demand[(month, group_id, origin, scope_type)]
        )

    objective = np.zeros(len(all_keys), dtype=float)
    for key in x_keys:
        month, group_id, origin, scope_type, workshop = key
        info = cost_lookup[(origin, scope_type, workshop)]
        cost_field = "composite_cost" if use_composite_cost else "direct_cost"
        objective[index[("x",) + key]] = float(info[cost_field])
    for key in q_keys:
        month, group_id, origin, scope_type = key
        penalty = float(scope_info[scope_type]["queue_penalty"])
        if month == months[-1]:
            penalty *= FINAL_BACKLOG_MULTIPLIER
        objective[index[("q",) + key]] = penalty

    row_idx, col_idx, values = [], [], []
    lower, upper = [], []
    row = 0

    # Demand/backlog flow: service + ending backlog - previous backlog = new demand.
    for month in months:
        for group_id, origin, scope_type in groups:
            for workshop in workshops:
                var_key = ("x", month, group_id, origin, scope_type, workshop)
                if var_key in index:
                    row_idx.append(row)
                    col_idx.append(index[var_key])
                    values.append(1.0)
            q_key = ("q", month, group_id, origin, scope_type)
            row_idx.append(row)
            col_idx.append(index[q_key])
            values.append(1.0)
            if month != months[0]:
                previous = ("q", month - 1, group_id, origin, scope_type)
                row_idx.append(row)
                col_idx.append(index[previous])
                values.append(-1.0)
            rhs = float(demand_lookup[(month, group_id, origin, scope_type)])
            lower.append(rhs)
            upper.append(rhs)
            row += 1

    capacity_lookup = capacity.set_index(["month", "workshop"]).to_dict("index")
    for month in months:
        for workshop in workshops:
            for group_id, origin, scope_type in groups:
                var_key = ("x", month, group_id, origin, scope_type, workshop)
                if var_key in index:
                    row_idx.append(row)
                    col_idx.append(index[var_key])
                    values.append(float(scope_info[scope_type]["workload_units"]))
            cap = capacity_lookup[(month, workshop)]
            lower.append(float(cap["minimum_units"]) if enforce_minimum else -np.inf)
            upper.append(float(cap["maximum_units"]))
            row += 1

    matrix = coo_matrix(
        (values, (row_idx, col_idx)), shape=(row, len(all_keys)), dtype=float
    ).tocsr()
    constraints = LinearConstraint(matrix, np.array(lower), np.array(upper))
    integrality = np.ones(len(all_keys), dtype=int) if integer else np.zeros(len(all_keys), dtype=int)
    start = perf_counter()
    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(np.zeros(len(all_keys)), variable_upper),
        constraints=constraints,
        options={"time_limit": time_limit, "mip_rel_gap": mip_rel_gap, "presolve": True},
    )
    runtime = perf_counter() - start
    if result.x is None:
        raise RuntimeError(f"{name}: solver failed: {result.message}")

    allocation_rows = []
    for key in x_keys:
        value = float(result.x[index[("x",) + key]])
        if value <= 1e-7:
            continue
        month, group_id, origin, scope_type, workshop = key
        info = cost_lookup[(origin, scope_type, workshop)]
        quantity = value
        allocation_rows.append(
            {
                "scenario": name,
                "month": month,
                "group_id": group_id,
                "origin_region": origin,
                "scope_type": scope_type,
                "wagon_type": scope_info[scope_type]["wagon_type"],
                "scope_family": scope_info[scope_type]["scope_family"],
                "workshop": workshop,
                "allocated_wagons": quantity,
                "total_hh": quantity * float(scope_info[scope_type]["hh_per_wagon"]),
                "direct_cost": quantity * float(info["direct_cost"]),
                "logistics_cost": quantity * float(info["logistics_cost"]),
                "unavailability_cost": quantity * float(info["transit_unavailability_cost"]),
                "retention_cost": quantity * float(info["retention_cost"]),
                "composite_cost": quantity * float(info["composite_cost"]),
                "local_assignment": int(origin == info["region"]),
            }
        )
    allocation = pd.DataFrame(allocation_rows)

    backlog_rows = []
    for key in q_keys:
        value = float(result.x[index[("q",) + key]])
        month, group_id, origin, scope_type = key
        backlog_rows.append(
            {
                "scenario": name,
                "month": month,
                "group_id": group_id,
                "origin_region": origin,
                "scope_type": scope_type,
                "wagon_type": scope_info[scope_type]["wagon_type"],
                "scope_family": scope_info[scope_type]["scope_family"],
                "queued_wagons": value,
            }
        )
    backlog = pd.DataFrame(backlog_rows)
    capacity_use = (
        allocation.groupby(["month", "workshop"], as_index=False)["total_hh"].sum()
        .merge(capacity, on=["month", "workshop"], how="right")
        .fillna({"total_hh": 0.0})
    )
    return ModelSolution(
        name=name,
        result=result,
        allocation=allocation,
        backlog=backlog,
        capacity_use=capacity_use,
        runtime_seconds=runtime,
        n_variables=len(all_keys),
        n_constraints=row,
    )


def run_local_first_heuristic(
    monthly_demand: pd.DataFrame,
    scope: pd.DataFrame,
    capacity: pd.DataFrame,
    costs: pd.DataFrame,
) -> ModelSolution:
    scope_info = scope.set_index("scope_type").to_dict("index")
    cost_lookup = costs.set_index(
        ["origin_region", "scope_type", "workshop"]
    ).to_dict("index")
    workshops = sorted(capacity["workshop"].unique())
    demand_lookup = monthly_demand.set_index(
        ["month", "group_id", "origin_region", "scope_type"]
    )["demand"].to_dict()
    groups = sorted(
        monthly_demand[["group_id", "origin_region", "scope_type"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    cap_lookup = capacity.set_index(["month", "workshop"]).to_dict("index")
    backlog_previous = {group: 0 for group in groups}
    allocation_rows, backlog_rows, capacity_rows = [], [], []
    start = perf_counter()

    for month in sorted(monthly_demand["month"].unique()):
        due = {
            group: backlog_previous[group]
            + int(demand_lookup[(month,) + group])
            for group in groups
        }
        remaining = {
            workshop: int(cap_lookup[(month, workshop)]["maximum_hh"])
            for workshop in workshops
        }
        used = {workshop: 0 for workshop in workshops}

        def assign(group, workshop, limit=None):
            group_id, origin, scope_type = group
            if due[group] <= 0:
                return 0
            info = cost_lookup[(origin, scope_type, workshop)]
            if int(info["eligible"]) == 0:
                return 0
            workload = int(scope_info[scope_type]["workload_units"])
            hh = float(scope_info[scope_type]["hh_per_wagon"])
            possible = remaining[workshop] // workload
            quantity = min(due[group], possible)
            if limit is not None:
                quantity = min(quantity, max(int(limit), 0))
            if quantity <= 0:
                return 0
            due[group] -= quantity
            remaining[workshop] -= quantity * workload
            used[workshop] += quantity * workload
            allocation_rows.append(
                {
                    "scenario": "local_first_heuristic",
                    "month": month,
                    "group_id": group_id,
                    "origin_region": origin,
                    "scope_type": scope_type,
                    "wagon_type": scope_info[scope_type]["wagon_type"],
                    "scope_family": scope_info[scope_type]["scope_family"],
                    "workshop": workshop,
                    "allocated_wagons": quantity,
                    "total_hh": quantity * hh,
                    "direct_cost": quantity * float(info["direct_cost"]),
                    "logistics_cost": quantity * float(info["logistics_cost"]),
                    "unavailability_cost": quantity * float(info["transit_unavailability_cost"]),
                    "retention_cost": quantity * float(info["retention_cost"]),
                    "composite_cost": quantity * float(info["composite_cost"]),
                    "local_assignment": int(origin == info["region"]),
                }
            )
            return quantity

        # First satisfy contractual/minimum workload using local and high-priority demand.
        for workshop in workshops:
            minimum = int(cap_lookup[(month, workshop)]["minimum_hh"])
            candidates = [g for g in groups if int(cost_lookup[(g[1], g[2], workshop)]["eligible"]) == 1]
            candidates.sort(
                key=lambda g: (
                    g[1] != cost_lookup[(g[1], g[2], workshop)]["region"],
                    -float(scope_info[g[2]]["queue_penalty"]),
                    float(cost_lookup[(g[1], g[2], workshop)]["composite_cost"]),
                )
            )
            for group in candidates:
                if used[workshop] >= minimum:
                    break
                workload = int(scope_info[group[2]]["workload_units"])
                units_needed = int(np.ceil((minimum - used[workshop]) / workload))
                assign(group, workshop, units_needed)

        # Then process urgent demand, preferring the local post and shorter movements.
        ordered_groups = sorted(
            groups,
            key=lambda g: (-float(scope_info[g[2]]["queue_penalty"]), g[2], g[1]),
        )
        for group in ordered_groups:
            group_id, origin, scope_type = group
            candidates = [
                workshop
                for workshop in workshops
                if int(cost_lookup[(origin, scope_type, workshop)]["eligible"]) == 1
            ]
            candidates.sort(
                key=lambda workshop: (
                    origin != cost_lookup[(origin, scope_type, workshop)]["region"],
                    float(cost_lookup[(origin, scope_type, workshop)]["logistics_cost"]),
                    float(cost_lookup[(origin, scope_type, workshop)]["composite_cost"]),
                )
            )
            for workshop in candidates:
                assign(group, workshop)
                if due[group] == 0:
                    break

        backlog_previous = due
        for group in groups:
            group_id, origin, scope_type = group
            backlog_rows.append(
                {
                    "scenario": "local_first_heuristic",
                    "month": month,
                    "group_id": group_id,
                    "origin_region": origin,
                    "scope_type": scope_type,
                    "wagon_type": scope_info[scope_type]["wagon_type"],
                    "scope_family": scope_info[scope_type]["scope_family"],
                    "queued_wagons": due[group],
                }
            )
        for workshop in workshops:
            cap = cap_lookup[(month, workshop)]
            capacity_rows.append(
                {
                    "month": month,
                    "workshop": workshop,
                    "total_hh": used[workshop],
                    **cap,
                }
            )

    runtime = perf_counter() - start
    allocation = pd.DataFrame(allocation_rows)
    backlog = pd.DataFrame(backlog_rows)
    capacity_use = pd.DataFrame(capacity_rows)
    return ModelSolution(
        name="local_first_heuristic",
        result=None,
        allocation=allocation,
        backlog=backlog,
        capacity_use=capacity_use,
        runtime_seconds=runtime,
        n_variables=0,
        n_constraints=0,
    )


def solution_summary(solution: ModelSolution, scope: pd.DataFrame) -> dict:
    allocation = solution.allocation
    backlog = solution.backlog
    scope_penalty = scope.set_index("scope_type")["queue_penalty"].to_dict()
    queue_cost = 0.0
    for row in backlog.itertuples(index=False):
        multiplier = FINAL_BACKLOG_MULTIPLIER if row.month == 12 else 1.0
        queue_cost += row.queued_wagons * scope_penalty[row.scope_type] * multiplier
    cost_columns = [
        "direct_cost", "logistics_cost", "unavailability_cost",
        "retention_cost", "composite_cost",
    ]
    sums = allocation[cost_columns].sum() if not allocation.empty else pd.Series(0.0, index=cost_columns)
    cap = solution.capacity_use
    min_binding = int(np.isclose(cap["total_hh"], cap["minimum_hh"], atol=1e-6).sum())
    max_binding = int(np.isclose(cap["total_hh"], cap["maximum_hh"], atol=1e-6).sum())
    min_violations = int((cap["total_hh"] + 1e-6 < cap["minimum_hh"]).sum())
    final_backlog = float(backlog.loc[backlog["month"] == 12, "queued_wagons"].sum())
    return {
        "scenario": solution.name,
        "serviced_wagons": float(allocation["allocated_wagons"].sum()),
        "cumulative_backlog_wagon_months": float(backlog["queued_wagons"].sum()),
        "final_backlog_wagons": final_backlog,
        "direct_cost": float(sums["direct_cost"]),
        "logistics_cost": float(sums["logistics_cost"]),
        "unavailability_cost": float(sums["unavailability_cost"]),
        "retention_cost": float(sums["retention_cost"]),
        "service_composite_cost": float(sums["composite_cost"]),
        "queue_cost": queue_cost,
        "total_system_cost": float(sums["composite_cost"] + queue_cost),
        "remote_wagons": float(
            allocation.loc[allocation["local_assignment"] == 0, "allocated_wagons"].sum()
        ),
        "minimum_binding_periods": min_binding,
        "maximum_binding_periods": max_binding,
        "minimum_violations": min_violations,
        "runtime_seconds": solution.runtime_seconds,
        "solver_status": "heuristic" if solution.result is None else str(solution.result.message),
        "solver_gap": np.nan if solution.result is None else float(getattr(solution.result, "mip_gap", 0.0) or 0.0),
        "variables": solution.n_variables,
        "constraints": solution.n_constraints,
    }


def save_figures(heuristic: ModelSolution, optimized: ModelSolution, summary: pd.DataFrame):
    plt.style.use("seaborn-v0_8-whitegrid")
    backlog = pd.concat([heuristic.backlog, optimized.backlog], ignore_index=True)
    backlog_month = backlog.groupby(["scenario", "month"], as_index=False)["queued_wagons"].sum()
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for scenario, frame in backlog_month.groupby("scenario"):
        label = "Local-first heuristic" if scenario == "local_first_heuristic" else "Optimized model"
        ax.plot(frame["month"], frame["queued_wagons"], marker="o", label=label)
    ax.set_xlabel("Month")
    ax.set_ylabel("Wagons in backlog")
    ax.set_xticks(range(1, 13))
    ax.legend()
    fig.tight_layout()
    fig.savefig(BASE_DIR / "backlog_by_month.png", dpi=220)
    plt.close(fig)

    cap = pd.concat(
        [heuristic.capacity_use.assign(scenario=heuristic.name), optimized.capacity_use.assign(scenario=optimized.name)],
        ignore_index=True,
    )
    cap_sum = cap.groupby(["scenario", "workshop"], as_index=False)["total_hh"].sum()
    pivot = cap_sum.pivot(index="workshop", columns="scenario", values="total_hh")
    pivot = pivot.rename(columns={"local_first_heuristic": "Heuristic", "full_milp": "Optimized"})
    ax = pivot.plot(kind="bar", figsize=(7.4, 4.8), rot=0)
    ax.set_ylabel("Annual person-hours used")
    ax.set_xlabel("Maintenance post")
    fig = ax.get_figure()
    fig.tight_layout()
    fig.savefig(BASE_DIR / "workshop_load.png", dpi=220)
    plt.close(fig)

    selected = summary[summary["scenario"].isin(["local_first_heuristic", "full_milp"])].copy()
    selected["label"] = selected["scenario"].map(
        {"local_first_heuristic": "Heuristic", "full_milp": "Optimized"}
    )
    components = selected.set_index("label")[
        ["direct_cost", "logistics_cost", "unavailability_cost", "retention_cost", "queue_cost"]
    ]
    ax = components.plot(kind="bar", stacked=True, figsize=(7.4, 4.8), rot=0)
    ax.set_ylabel("Normalized monetary units")
    ax.set_xlabel("")
    ax.legend(title="Cost component", fontsize=8)
    fig = ax.get_figure()
    fig.tight_layout()
    fig.savefig(BASE_DIR / "cost_components.png", dpi=220)
    plt.close(fig)


def main():
    demand, scope, workshops, shares, logistics, workshop_scope, availability = load_inputs()
    monthly_demand = build_monthly_demand(demand, shares)
    capacity = build_capacity(workshops, availability)
    costs = cost_table(scope, workshops, logistics, workshop_scope)

    monthly_demand.to_csv(BASE_DIR / "monthly_demand.csv", index=False)
    capacity.to_csv(BASE_DIR / "effective_capacity.csv", index=False)
    costs.to_csv(BASE_DIR / "composite_cost_matrix.csv", index=False)

    heuristic = run_local_first_heuristic(monthly_demand, scope, capacity, costs)
    full = solve_model("full_milp", monthly_demand, scope, capacity, costs)
    direct_only = solve_model(
        "direct_cost_only", monthly_demand, scope, capacity, costs,
        use_composite_cost=False,
    )
    no_eligibility = solve_model(
        "without_eligibility", monthly_demand, scope, capacity, costs,
        enforce_eligibility=False, time_limit=30.0, mip_rel_gap=0.02,
    )
    no_minimum = solve_model(
        "without_minimum_capacity", monthly_demand, scope, capacity, costs,
        enforce_minimum=False,
    )
    lp_relaxation = solve_model(
        "lp_relaxation", monthly_demand, scope, capacity, costs, integer=False,
    )

    solutions = [heuristic, full, direct_only, no_eligibility, no_minimum, lp_relaxation]
    summary = pd.DataFrame([solution_summary(solution, scope) for solution in solutions])
    summary.to_csv(BASE_DIR / "scenario_summary.csv", index=False)
    full.allocation.to_csv(BASE_DIR / "optimized_allocation.csv", index=False)
    full.backlog.to_csv(BASE_DIR / "optimized_backlog.csv", index=False)
    full.capacity_use.to_csv(BASE_DIR / "optimized_capacity_use.csv", index=False)
    heuristic.allocation.to_csv(BASE_DIR / "heuristic_allocation.csv", index=False)
    heuristic.backlog.to_csv(BASE_DIR / "heuristic_backlog.csv", index=False)
    lp_relaxation.allocation.to_csv(BASE_DIR / "lp_relaxation_allocation.csv", index=False)
    lp_relaxation.backlog.to_csv(BASE_DIR / "lp_relaxation_backlog.csv", index=False)
    summary.loc[
        summary["scenario"].isin(["local_first_heuristic", "full_milp"]),
        [
            "scenario", "direct_cost", "logistics_cost", "unavailability_cost",
            "retention_cost", "queue_cost", "total_system_cost",
        ],
    ].to_csv(BASE_DIR / "cost_component_summary.csv", index=False)

    full_obj = float(full.result.fun)
    lp_obj = float(lp_relaxation.result.fun)
    gap = 100.0 * (full_obj - lp_obj) / full_obj if full_obj else 0.0
    diagnostics = pd.DataFrame(
        [
            {"indicator": "annual_demand_wagons", "value": int(demand["annual_demand"].sum())},
            {"indicator": "annual_demand_hh", "value": int(
                demand.merge(scope, on="scope_type").eval("annual_demand * hh_per_wagon").sum()
            )},
            {"indicator": "annual_effective_capacity_hh", "value": int(capacity["maximum_hh"].sum())},
            {"indicator": "heavy_scope_hh", "value": int(
                demand.merge(scope, on="scope_type").query("heavy_scope == 1")
                .eval("annual_demand * hh_per_wagon").sum()
            )},
            {"indicator": "pm2_effective_capacity_hh", "value": int(
                capacity.loc[capacity["workshop"] == "PM2", "maximum_hh"].sum()
            )},
            {"indicator": "milp_objective", "value": full_obj},
            {"indicator": "lp_objective", "value": lp_obj},
            {"indicator": "lp_gap_percent", "value": gap},
        ]
    )
    diagnostics.to_csv(BASE_DIR / "diagnostics.csv", index=False)

    scale_rows = []
    for factor in [1, 5, 10]:
        scaled_demand, scaled_capacity = expand_instance(monthly_demand, capacity, factor)
        milp_solution = solve_model(
            f"scale_{factor}", scaled_demand, scope, scaled_capacity, costs,
            time_limit=30.0, mip_rel_gap=0.002,
        )
        lp_solution = solve_model(
            f"scale_{factor}_lp", scaled_demand, scope, scaled_capacity, costs,
            integer=False, time_limit=120.0,
        )
        scale_rows.append(
            {
                "scale_factor": factor,
                "variables": milp_solution.n_variables,
                "constraints": milp_solution.n_constraints,
                "milp_runtime_seconds": milp_solution.runtime_seconds,
                "lp_runtime_seconds": lp_solution.runtime_seconds,
                "milp_objective": float(milp_solution.result.fun),
                "lp_objective": float(lp_solution.result.fun),
                "lp_gap_percent": 100.0 * (
                    float(milp_solution.result.fun) - float(lp_solution.result.fun)
                ) / float(milp_solution.result.fun),
                "reported_mip_gap_percent": 100.0 * float(
                    getattr(milp_solution.result, "mip_gap", 0.0) or 0.0
                ),
            }
        )
    pd.DataFrame(scale_rows).to_csv(BASE_DIR / "scalability.csv", index=False)
    save_figures(heuristic, full, summary)

    print("Scenario summary")
    print(summary.to_string(index=False))
    print("\nDiagnostics")
    print(diagnostics.to_string(index=False))
    print("\nScalability")
    print(pd.DataFrame(scale_rows).to_string(index=False))


if __name__ == "__main__":
    main()