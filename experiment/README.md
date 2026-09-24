# Revised reproducible experiment

This experiment represents the review-requested version of the wagon-maintenance allocation model.

It includes:

- twelve monthly periods and backlog carry-over;
- three anonymized operating regions;
- technical eligibility: VR1/VR2 and VMC at all posts, VR4/VRG only at PM2;
- direct, logistics, transit-unavailability, and retention costs;
- effective monthly capacity reductions caused by professional leave or equipment repair;
- minimum and maximum person-hour constraints;
- an integer queue variable with a monthly penalty;
- a fair local-first heuristic subject to the same eligibility and capacity rules;
- LP-relaxation and scalability tests.

## Baseline heuristic

The comparison uses a deterministic local-first heuristic under the same
eligibility, minimum-capacity, maximum-capacity, and backlog rules as the MILP.
For each month, it:

1. combines new demand with backlog from the previous month;
2. fills minimum post workloads with eligible high-priority demand;
3. sends remaining demand first to its local eligible post;
4. considers other eligible posts by increasing logistics and composite cost;
5. carries unallocated demand to the next month.

The implementation is `run_local_first_heuristic` in `run_experiment.py`.

Run from this directory with the preinstalled Python packages:

```bash
python run_experiment.py
```

The script writes all result tables and figures in this directory. No virtual environment or package installation is required.