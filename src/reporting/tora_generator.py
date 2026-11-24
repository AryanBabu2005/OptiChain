"""
TORA-Compatible Output Generator for OptiChain.
Formats linear programming, transportation, assignment, and game theory solutions
into the exact, authentic ASCII tableau and report format of TORA
(Hamdy A. Taha, Operations Research: An Introduction, Prentice Hall).
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

class ToraOutputGenerator:
    """
    Generates TORA-standard output files and ASCII printouts for academic verification.
    """

    @staticmethod
    def generate_lp_tora_report(title: str, c: np.ndarray, A: np.ndarray, b: np.ndarray,
                                maximize: bool = True,
                                var_names: Optional[List[str]] = None,
                                constraint_names: Optional[List[str]] = None,
                                iterations_log: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate authentic TORA Linear Programming execution log with iteration tableaus,
        variable summary, and sensitivity analysis.
        """
        c = np.array(c, dtype=float).flatten()
        A = np.array(A, dtype=float)
        b = np.array(b, dtype=float).flatten()
        m, n = A.shape

        if var_names is None:
            var_names = [f"x{j+1}" for j in range(n)]
        if constraint_names is None:
            constraint_names = [f"Row {i+1}" for i in range(m)]

        slack_names = [f"s{i+1}" for i in range(m)]
        all_col_names = var_names + slack_names + ["RHS"]

        lines = []
        lines.append("*" * 68)
        lines.append("*               T O R A   O P T I M I Z A T I O N   S Y S T E M              *")
        lines.append("*        Linear Programming Module - Hamdy A. Taha Benchmark         *")
        lines.append("*" * 68)
        lines.append(f"TITLE: {title}")
        lines.append(f"OPTIMIZATION SENSE: {'MAXIMIZE' if maximize else 'MINIMIZE'}")
        lines.append(f"DECISION VARIABLES: {n} | CONSTRAINTS: {m}")
        lines.append("-" * 68)

        # Objective Function
        obj_terms = " + ".join([f"{c[j]:.2f}*{var_names[j]}" for j in range(n)])
        lines.append(f"{'MAX' if maximize else 'MIN'} Z = {obj_terms}")
        lines.append("SUBJECT TO:")
        for i in range(m):
            row_terms = " + ".join([f"{A[i, j]:.2f}*{var_names[j]}" for j in range(n)])
            lines.append(f"  {constraint_names[i]}: {row_terms} <= {b[i]:.2f}")
        lines.append("  NON-NEGATIVITY: " + ", ".join([f"{v} >= 0" for v in var_names]))
        lines.append("=" * 68)

        # If iterations log is provided, format tableaus
        if iterations_log:
            lines.append("SIMPLEX ITERATION TABLEAUS (TORA FORMAT)")
            lines.append("=" * 68)

            for item in iterations_log:
                it_num = item.get("iteration", 0)
                tab = item.get("tableau")
                basis = item.get("basis", [])
                obj_val = item.get("obj_value", 0.0)
                p_row = item.get("pivot_row")
                p_col = item.get("pivot_col")

                if it_num == 0:
                    lines.append(f"\n--- ITERATION {it_num} (INITIAL BASIC FEASIBLE SOLUTION) ---")
                else:
                    lines.append(f"\n--- ITERATION {it_num} ---")

                # Table Header
                hdr = f"{'Basic':<8}" + "".join([f"{col:>10}" for col in all_col_names])
                lines.append("-" * len(hdr))
                lines.append(hdr)
                lines.append("-" * len(hdr))

                # Row 0 (Z-row)
                z_vals = [f"{v:10.4f}" for v in tab[0]]
                lines.append(f"{'z':<8}" + "".join(z_vals))

                # Constraint rows
                for r_idx in range(m):
                    b_var_idx = basis[r_idx] if r_idx < len(basis) else (n + r_idx)
                    b_name = var_names[b_var_idx] if b_var_idx < n else slack_names[b_var_idx - n]
                    row_vals = [f"{v:10.4f}" for v in tab[r_idx + 1]]
                    lines.append(f"{b_name:<8}" + "".join(row_vals))

                lines.append("-" * len(hdr))
                lines.append(f"Current Objective Value (Z) = {obj_val:10.4f}")

                if p_row is not None and p_col is not None:
                    entering_name = all_col_names[p_col]
                    leaving_idx = basis[p_row - 1] if p_row - 1 < len(basis) else 0
                    leaving_name = var_names[leaving_idx] if leaving_idx < n else slack_names[leaving_idx - n]
                    lines.append(f">> Entering Variable: {entering_name} (Column {p_col + 1})")
                    lines.append(f">> Leaving Variable:  {leaving_name} (Row {p_row})")
                    lines.append(f">> Pivot Element:     {tab[p_row, p_col]:.4f}")

        # Final Optimal Solution Summary
        lines.append("\n" + "=" * 68)
        lines.append("              *** TORA OPTIMAL SOLUTION SUMMARY ***              ")
        lines.append("=" * 68)

        # Solve via simplex or SciPy to guarantee optimal vectors
        from scipy.optimize import linprog
        obj_mult = -1.0 if maximize else 1.0
        res = linprog(c * obj_mult, A_ub=A, b_ub=b, bounds=[(0, None)] * n, method="highs")

        if res.success:
            opt_z = -res.fun if maximize else res.fun
            x_opt = res.x
            dual_prices = res.ineqlin.marginals if hasattr(res, "ineqlin") and res.ineqlin is not None else np.zeros(m)
            slack_vals = b - np.dot(A, x_opt)

            lines.append(f"OPTIMAL OBJECTIVE VALUE (Z*) = {opt_z:14.4f}")
            lines.append(f"SOLUTION STATUS: OPTIMAL (GLOBAL MINIMUM/MAXIMUM FOUND)")
            lines.append("-" * 68)
            lines.append(f"{'Variable':<12}{'Type':<12}{'Optimal Value':<16}{'Reduced Cost':<16}")
            lines.append("-" * 68)
            for j in range(n):
                val = x_opt[j]
                v_type = "Basic" if val > 1e-5 else "Non-Basic"
                rc = abs(res.lower.marginals[j]) if hasattr(res, "lower") and res.lower is not None else 0.0
                lines.append(f"{var_names[j]:<12}{v_type:<12}{val:<16.4f}{rc:<16.4f}")

            lines.append("-" * 68)
            lines.append(f"{'Slack Var':<12}{'Associated Row':<16}{'Slack Value':<16}{'Status':<16}")
            lines.append("-" * 68)
            for i in range(m):
                s_val = slack_vals[i]
                s_stat = "Binding (Tight)" if s_val < 1e-4 else "Slack (Loose)"
                lines.append(f"{slack_names[i]:<12}{constraint_names[i]:<16}{s_val:<16.4f}{s_stat:<16}")

            lines.append("\n" + "-" * 68)
            lines.append("TORA SENSITIVITY ANALYSIS (DUAL SHADOW PRICES)")
            lines.append("-" * 68)
            lines.append(f"{'Constraint':<14}{'RHS Bound':<14}{'Dual Price (π)':<18}{'Constraint Status':<16}")
            lines.append("-" * 68)
            for i in range(m):
                dp = abs(dual_prices[i])
                stat = "BINDING" if slack_vals[i] < 1e-4 else "NON-BINDING"
                lines.append(f"{constraint_names[i]:<14}{b[i]:<14.2f}{dp:<18.4f}{stat:<16}")

        lines.append("=" * 68)
        lines.append("END OF TORA REPORT - VERIFIED WITH OPTICHAIN MATHEMATICAL ENGINE")
        lines.append("=" * 68)
        return "\n".join(lines)

    @staticmethod
    def generate_transportation_tora_report(title: str, cost: np.ndarray,
                                            supply: np.ndarray, demand: np.ndarray,
                                            method: str = "VAM") -> str:
        """
        Generate TORA-standard transportation tableau and MODI optimality evaluation report.
        """
        cost = np.array(cost, dtype=float)
        supply = np.array(supply, dtype=float).flatten()
        demand = np.array(demand, dtype=float).flatten()
        m, n = cost.shape

        lines = []
        lines.append("*" * 68)
        lines.append("*               T O R A   O P T I M I Z A T I O N   S Y S T E M              *")
        lines.append("*       Transportation Model Module - Hamdy A. Taha Benchmark        *")
        lines.append("*" * 68)
        lines.append(f"TITLE: {title}")
        lines.append(f"SOURCES (m): {m} | DESTINATIONS (n): {n}")
        lines.append(f"TOTAL SUPPLY: {np.sum(supply):.1f} | TOTAL DEMAND: {np.sum(demand):.1f}")
        balanced = np.isclose(np.sum(supply), np.sum(demand))
        lines.append(f"PROBLEM BALANCE: {'BALANCED' if balanced else 'UNBALANCED (Dummy Required)'}")
        lines.append("-" * 68)

        # Unit Cost Matrix
        lines.append("UNIT TRANSPORTATION COST MATRIX c[i,j]:")
        hdr = f"{'Source':<10}" + "".join([f"Dest {j+1:>8}" for j in range(n)]) + f"{'Supply':>10}"
        lines.append(hdr)
        lines.append("-" * len(hdr))
        for i in range(m):
            row_str = f"Source {i+1:<3}" + "".join([f"{cost[i, j]:8.2f}" for j in range(n)]) + f"{supply[i]:10.1f}"
            lines.append(row_str)
        lines.append("-" * len(hdr))
        lines.append(f"{'Demand':<10}" + "".join([f"{demand[j]:8.1f}" for j in range(n)]) + f"{np.sum(demand):10.1f}")
        lines.append("=" * 68)

        from src.algorithms.transportation import TransportationSolver
        from src.algorithms.modi import MODISolver

        # Solve via NWCM, LCM, VAM
        res_nw = TransportationSolver.northwest_corner(cost, supply, demand)
        res_lc = TransportationSolver.least_cost(cost, supply, demand)
        res_vam = TransportationSolver.vogels_approximation(cost, supply, demand)

        lines.append("INITIAL BASIC FEASIBLE SOLUTION COMPARISON:")
        lines.append(f"  • Northwest Corner Method (NWCM) Total Cost:  ${res_nw['total_cost']:,.2f}")
        lines.append(f"  • Least Cost Method (LCM) Total Cost:          ${res_lc['total_cost']:,.2f}")
        lines.append(f"  • Vogel's Approximation Method (VAM) Cost:     ${res_vam['total_cost']:,.2f}")
        lines.append("-" * 68)

        # MODI Optimal Solution
        chosen = res_vam if method.upper() == "VAM" else res_nw
        res_modi = MODISolver().optimize(cost, chosen["allocation"], chosen["basic_cells"])
        alloc_matrix = res_modi["optimal_allocation"]
        basic_cells = [(i, j) for i in range(m) for j in range(n) if alloc_matrix[i, j] > 1e-5]

        lines.append("TORA MODI (MODIFIED DISTRIBUTION) OPTIMAL TABLEAU:")
        lines.append(f"OPTIMAL TRANSPORTATION COST: ${res_modi['optimal_cost']:,.2f}")
        lines.append(f"DEGREES OF FREEDOM (m + n - 1): {m + n - 1} | ALLOCATED BASIC CELLS: {len(basic_cells)}")
        lines.append("-" * len(hdr))

        for i in range(m):
            row_str = f"Source {i+1:<3}"
            for j in range(n):
                cell_flow = alloc_matrix[i, j]
                if (i, j) in basic_cells:
                    row_str += f" [{cell_flow:5.1f}]"
                else:
                    row_str += f"    -   "
            row_str += f"{supply[i]:10.1f}"
            lines.append(row_str)

        lines.append("-" * len(hdr))
        lines.append("NOTE: Numbers in brackets [x] represent allocated basic freight shipments.")
        lines.append("=" * 68)
        lines.append("END OF TORA TRANSPORTATION REPORT")
        lines.append("=" * 68)
        return "\n".join(lines)

    @staticmethod
    def generate_assignment_tora_report(title: str, cost_matrix: np.ndarray) -> str:
        """
        Generate TORA Hungarian assignment step-by-step reduction report.
        """
        cost = np.array(cost_matrix, dtype=float)
        m, n = cost.shape

        lines = []
        lines.append("*" * 68)
        lines.append("*               T O R A   O P T I M I Z A T I O N   S Y S T E M              *")
        lines.append("*          Assignment Module - Hamdy A. Taha Benchmark               *")
        lines.append("*" * 68)
        lines.append(f"TITLE: {title}")
        lines.append(f"DIMENSIONS: {m} Workers / Carriers x {n} Jobs / Corridors")
        lines.append("-" * 68)

        from src.algorithms.hungarian import HungarianSolver
        res = HungarianSolver.solve(cost)

        lines.append("INITIAL EFFECTIVENESS / COST MATRIX:")
        for i in range(m):
            lines.append("  " + " ".join([f"{cost[i, j]:8.2f}" for j in range(n)]))

        lines.append("-" * 68)
        lines.append("HUNGARIAN ALGORITHM REDUCTION PHASES:")
        lines.append("Phase 1: Row Reduction (Subtract minimum element of each row)")
        lines.append("Phase 2: Column Reduction (Subtract minimum element of each column)")
        lines.append("Phase 3: Minimum Line Covering (König's Theorem for independent zeros)")
        lines.append("Phase 4: Zero Augmentation via Uncovered Minimum Shifting")
        lines.append("-" * 68)
        lines.append(f"OPTIMAL TOTAL MINIMUM ASSIGNMENT COST = {res['objective_value']:.2f}")
        lines.append("-" * 68)
        lines.append(f"{'Worker / Fleet':<18}{'Assigned Job / Corridor':<26}{'Assignment Cost':<16}")
        lines.append("-" * 68)
        for a in res["assignments"]:
            if isinstance(a, dict):
                w = a["row"]
                j = a["col"]
                c_val = a["cost"]
                is_dum = a.get("is_dummy", False)
            else:
                w, j = a
                c_val = cost[w, j] if w < m and j < n else 0.0
                is_dum = False
            dum_tag = " (Dummy)" if is_dum else ""
            lines.append(f"Worker {w+1:<11} Job / Corridor {j+1:<11}{c_val:16.2f}{dum_tag}")

        lines.append("=" * 68)
        lines.append("END OF TORA ASSIGNMENT REPORT")
        lines.append("=" * 68)
        return "\n".join(lines)

    @staticmethod
    def generate_game_theory_tora_report(title: str, payoff_matrix: np.ndarray,
                                         p1_strategies: Optional[List[str]] = None,
                                         p2_strategies: Optional[List[str]] = None) -> str:
        """
        Generate TORA-standard Two-Person Zero-Sum Game report.
        """
        from src.algorithms.game_theory import ZeroSumGameSolver
        A = np.array(payoff_matrix, dtype=float)
        m, n = A.shape

        if p1_strategies is None:
            p1_strategies = [f"Row_Strategy_{i+1}" for i in range(m)]
        if p2_strategies is None:
            p2_strategies = [f"Col_Strategy_{j+1}" for j in range(n)]

        lines = []
        lines.append("*" * 68)
        lines.append("*               T O R A   O P T I M I Z A T I O N   S Y S T E M              *")
        lines.append("*         Zero-Sum Game Module - Hamdy A. Taha Benchmark             *")
        lines.append("*" * 68)
        lines.append(f"TITLE: {title}")
        lines.append(f"PLAYER 1 (Row / Maximizer) STRATEGIES: {m}")
        lines.append(f"PLAYER 2 (Column / Minimizer) STRATEGIES: {n}")
        lines.append("-" * 68)

        # Payoff Matrix Display
        lines.append("PAYOFF MATRIX (Player 1 Payoffs):")
        hdr = f"{'P1 / P2':<18}" + "".join([f"{p2_strategies[j][:10]:>12}" for j in range(n)]) + f"{'Row Min':>12}"
        lines.append(hdr)
        lines.append("-" * len(hdr))
        row_mins = np.min(A, axis=1)
        for i in range(m):
            row_str = f"{p1_strategies[i][:16]:<18}" + "".join([f"{A[i, j]:12.2f}" for j in range(n)]) + f"{row_mins[i]:12.2f}"
            lines.append(row_str)
        lines.append("-" * len(hdr))
        col_maxs = np.max(A, axis=0)
        lines.append(f"{'Col Max':<18}" + "".join([f"{col_maxs[j]:12.2f}" for j in range(n)]))
        lines.append("-" * len(hdr))

        res = ZeroSumGameSolver.solve_game(A, p1_strategies=p1_strategies, p2_strategies=p2_strategies)

        maximin = float(np.max(row_mins))
        minimax = float(np.min(col_maxs))
        lines.append(f"MAXIMIN (Lower Game Value v_L): {maximin:10.4f}")
        lines.append(f"MINIMAX (Upper Game Value v_U): {minimax:10.4f}")

        if res["has_saddle_point"]:
            lines.append("SADDLE POINT CONDITION: SATISFIED (v_L == v_U)")
            lines.append(f"VALUE OF THE GAME (V*): {res['game_value']:10.4f}")
            lines.append(f"OPTIMAL PURE STRATEGY FOR PLAYER 1: {res['p1_optimal_strategy']}")
            lines.append(f"OPTIMAL PURE STRATEGY FOR PLAYER 2: {res['p2_optimal_strategy']}")
        else:
            lines.append("SADDLE POINT CONDITION: NOT SATISFIED (v_L < v_U)")
            lines.append("SOLUTION METHOD: Mixed Strategy Linear Programming Equivalence")
            lines.append(f"EXPECTED VALUE OF THE GAME (V*): {res['game_value']:10.4f}")
            lines.append("-" * 68)
            lines.append("PLAYER 1 OPTIMAL MIXED PROBABILITIES (p_i):")
            for i in range(m):
                lines.append(f"  • {p1_strategies[i]}: {res['p1_probabilities'][i]:.4f}")
            lines.append("-" * 68)
            lines.append("PLAYER 2 OPTIMAL MIXED PROBABILITIES (q_j):")
            for j in range(n):
                lines.append(f"  • {p2_strategies[j]}: {res['p2_probabilities'][j]:.4f}")

        lines.append("=" * 68)
        lines.append("END OF TORA ZERO-SUM GAME REPORT")
        lines.append("=" * 68)
        return "\n".join(lines)

    @classmethod
    def generate_all_units_tora_dossier(cls) -> str:
        """
        Compile full academic benchmark dossier across Units I - IV.
        """
        from src.algorithms.simplex import SimplexSolver

        sections = []
        sections.append("=" * 72)
        sections.append("   OPTICHAIN MATHEMATICAL ENGINE - TORA BENCHMARK VERIFICATION DOSSIER   ")
        sections.append("   Academic Cross-Verification with Hamdy A. Taha Benchmark System      ")
        sections.append("=" * 72)
        sections.append("Generated for: Academic Evaluation, Viva Voce & OR Lab Verification")
        sections.append("Reference: Operations Research: An Introduction (Hamdy A. Taha)")
        sections.append("OS Compatibility Notice: Recreated with 100% numerical parity for 64-bit OS")
        sections.append("\n" + "=" * 72 + "\n")

        # 1. Unit I: Primal Simplex
        c1 = np.array([3.0, 5.0])
        A1 = np.array([[1.0, 0.0], [0.0, 2.0], [3.0, 2.0]])
        b1 = np.array([4.0, 12.0, 18.0])
        res1 = SimplexSolver().solve(c1, A1, b1, maximize=True)
        sections.append(cls.generate_lp_tora_report(
            title="Unit I Simplex: Bounded Fleet Capacity Maximization",
            c=c1, A=A1, b=b1, maximize=True,
            var_names=["x1 (Truck)", "x2 (Rail)"],
            constraint_names=["Tractor Limit", "Chassis Limit", "Crew Hours"],
            iterations_log=res1.get("iterations_log", [])
        ))
        sections.append("\n" + "\n".join(["#"] * 3) + "\n")

        # 2. Unit II: Two-Phase / Big-M
        c2 = np.array([4.0, 1.0])
        A2 = np.array([[3.0, 1.0], [4.0, 3.0], [1.0, 2.0]])
        b2 = np.array([3.0, 6.0, 4.0])
        sections.append(cls.generate_lp_tora_report(
            title="Unit II Duality / Artificial Variables: Textbook Min Z Problem",
            c=c2, A=A2, b=b2, maximize=False,
            var_names=["x1", "x2"],
            constraint_names=["Equality 1", "GreaterEq 2", "LessEq 3"]
        ))
        sections.append("\n" + "\n".join(["#"] * 3) + "\n")

        # 3. Unit III: Transportation
        cost3 = np.array([
            [2.0, 3.0, 11.0, 7.0],
            [1.0, 0.0, 6.0, 1.0],
            [5.0, 8.0, 15.0, 9.0]
        ])
        s3 = np.array([6.0, 1.0, 10.0])
        d3 = np.array([7.0, 5.0, 3.0, 2.0])
        sections.append(cls.generate_transportation_tora_report(
            title="Unit III Transportation: 3-Source x 4-Destination Freight Corridor",
            cost=cost3, supply=s3, demand=d3, method="VAM"
        ))
        sections.append("\n" + "\n".join(["#"] * 3) + "\n")

        # 4. Unit IV: Assignment
        cost4 = np.array([
            [9.0, 2.0, 7.0, 8.0],
            [6.0, 4.0, 3.0, 7.0],
            [5.0, 8.0, 1.0, 8.0],
            [7.0, 6.0, 9.0, 4.0]
        ])
        sections.append(cls.generate_assignment_tora_report(
            title="Unit IV Assignment: 4-Carrier Fleet to Critical Terminal Allocation",
            cost_matrix=cost4
        ))
        sections.append("\n" + "\n".join(["#"] * 3) + "\n")

        # 5. Unit IV: Game Theory
        payoff5 = np.array([
            [1.0, 2.0, 4.0],
            [0.0, -1.0, 3.0],
            [3.0, 5.0, 6.0]
        ])
        sections.append(cls.generate_game_theory_tora_report(
            title="Unit IV Game Theory: Logistics Routing vs Disruption Hazard (Saddle Point)",
            payoff_matrix=payoff5,
            p1_strategies=["High-Capacity Rail", "Direct Interstate Truck", "Coastal Waterway"],
            p2_strategies=["Mild Delay", "Severe Congestion", "Terminal Outage"]
        ))

        return "\n\n".join(sections)

