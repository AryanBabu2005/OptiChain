"""
Classical Transportation Algorithms for OptiChain.
Implements:
1. Northwest Corner Method (NWCM)
2. Least Cost Method (LCM / Matrix Minimum)
3. Vogel's Approximation Method (VAM)
Includes automated balancing (dummy supply/demand) and degeneracy detection.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np

class TransportationSolver:
    @staticmethod
    def balance_problem(cost_matrix: np.ndarray, supply: np.ndarray, demand: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
        """
        Check if total supply == total demand.
        If unbalanced, add a dummy destination (if supply > demand) or dummy origin (if demand > supply)
        with zero transportation cost.
        """
        C = np.array(cost_matrix, dtype=float).copy()
        S = np.array(supply, dtype=float).copy()
        D = np.array(demand, dtype=float).copy()

        tot_s = np.sum(S)
        tot_d = np.sum(D)
        was_balanced = abs(tot_s - tot_d) < 1e-7

        if tot_s > tot_d + 1e-7:
            # Add dummy destination
            diff = tot_s - tot_d
            D = np.append(D, diff)
            dummy_col = np.zeros((C.shape[0], 1), dtype=float)
            C = np.hstack([C, dummy_col])
        elif tot_d > tot_s + 1e-7:
            # Add dummy origin
            diff = tot_d - tot_s
            S = np.append(S, diff)
            dummy_row = np.zeros((1, C.shape[1]), dtype=float)
            C = np.vstack([C, dummy_row])

        return C, S, D, was_balanced

    @staticmethod
    def northwest_corner(cost_matrix: np.ndarray, supply: np.ndarray, demand: np.ndarray) -> Dict[str, Any]:
        """
        Northwest Corner Method (NWCM) initialization.
        """
        C, S, D, balanced = TransportationSolver.balance_problem(cost_matrix, supply, demand)
        m, n = C.shape
        allocation = np.zeros((m, n), dtype=float)
        basic_cells = []

        rem_s = S.copy()
        rem_d = D.copy()

        i, j = 0, 0
        while i < m and j < n:
            alloc = min(rem_s[i], rem_d[j])
            allocation[i, j] = alloc
            basic_cells.append((i, j))

            rem_s[i] -= alloc
            rem_d[j] -= alloc

            if rem_s[i] <= 1e-7 and rem_d[j] <= 1e-7:
                # Tie: increment both, but record degeneracy cell if needed
                if i + 1 < m:
                    basic_cells.append((i + 1, j))
                i += 1
                j += 1
            elif rem_s[i] <= 1e-7:
                i += 1
            else:
                j += 1

        total_cost = float(np.sum(allocation * C))
        is_degenerate = len(basic_cells) < (m + n - 1)

        return {
            "method": "Northwest Corner Method",
            "allocation": allocation,
            "cost_matrix": C,
            "basic_cells": basic_cells,
            "total_cost": round(total_cost, 4),
            "is_degenerate": is_degenerate,
            "required_basis_size": m + n - 1,
            "actual_basis_size": len(basic_cells)
        }

    @staticmethod
    def least_cost(cost_matrix: np.ndarray, supply: np.ndarray, demand: np.ndarray) -> Dict[str, Any]:
        """
        Least Cost Method (Matrix Minimum) initialization.
        """
        C, S, D, balanced = TransportationSolver.balance_problem(cost_matrix, supply, demand)
        m, n = C.shape
        allocation = np.zeros((m, n), dtype=float)
        basic_cells = []

        rem_s = S.copy()
        rem_d = D.copy()

        active_rows = set(range(m))
        active_cols = set(range(n))

        while active_rows and active_cols:
            # Find minimum cost cell among active rows and columns
            min_c = float("inf")
            best_i, best_j = -1, -1

            for i in active_rows:
                for j in active_cols:
                    if C[i, j] < min_c:
                        min_c = C[i, j]
                        best_i, best_j = i, j

            alloc = min(rem_s[best_i], rem_d[best_j])
            allocation[best_i, best_j] = alloc
            basic_cells.append((best_i, best_j))

            rem_s[best_i] -= alloc
            rem_d[best_j] -= alloc

            if rem_s[best_i] <= 1e-7:
                active_rows.discard(best_i)
            if rem_d[best_j] <= 1e-7:
                active_cols.discard(best_j)

        total_cost = float(np.sum(allocation * C))
        is_degenerate = len(basic_cells) < (m + n - 1)

        return {
            "method": "Least Cost Method",
            "allocation": allocation,
            "cost_matrix": C,
            "basic_cells": basic_cells,
            "total_cost": round(total_cost, 4),
            "is_degenerate": is_degenerate,
            "required_basis_size": m + n - 1,
            "actual_basis_size": len(basic_cells)
        }

    @staticmethod
    def vogels_approximation(cost_matrix: np.ndarray, supply: np.ndarray, demand: np.ndarray) -> Dict[str, Any]:
        """
        Vogel's Approximation Method (VAM) initialization.
        Computes row and column penalties (difference between 2 lowest costs).
        """
        C, S, D, balanced = TransportationSolver.balance_problem(cost_matrix, supply, demand)
        m, n = C.shape
        allocation = np.zeros((m, n), dtype=float)
        basic_cells = []

        rem_s = S.copy()
        rem_d = D.copy()

        active_rows = set(range(m))
        active_cols = set(range(n))

        while active_rows and active_cols:
            # If only 1 row or 1 col remains, allocate least cost
            if len(active_rows) == 1:
                i = list(active_rows)[0]
                sorted_cols = sorted(list(active_cols), key=lambda j: C[i, j])
                for j in sorted_cols:
                    alloc = min(rem_s[i], rem_d[j])
                    allocation[i, j] = alloc
                    basic_cells.append((i, j))
                    rem_s[i] -= alloc
                    rem_d[j] -= alloc
                break
            elif len(active_cols) == 1:
                j = list(active_cols)[0]
                sorted_rows = sorted(list(active_rows), key=lambda i: C[i, j])
                for i in sorted_rows:
                    alloc = min(rem_s[i], rem_d[j])
                    allocation[i, j] = alloc
                    basic_cells.append((i, j))
                    rem_s[i] -= alloc
                    rem_d[j] -= alloc
                break

            # Calculate row penalties
            row_penalties = {}
            for i in active_rows:
                row_costs = sorted([C[i, j] for j in active_cols])
                penalty = (row_costs[1] - row_costs[0]) if len(row_costs) > 1 else row_costs[0]
                row_penalties[i] = penalty

            # Calculate column penalties
            col_penalties = {}
            for j in active_cols:
                col_costs = sorted([C[i, j] for i in active_rows])
                penalty = (col_costs[1] - col_costs[0]) if len(col_costs) > 1 else col_costs[0]
                col_penalties[j] = penalty

            max_row_pen = max(row_penalties.values()) if row_penalties else -1
            max_col_pen = max(col_penalties.values()) if col_penalties else -1

            if max_row_pen >= max_col_pen:
                # Pick row with maximum penalty
                best_i = max(row_penalties, key=row_penalties.get)
                # Find least cost column in this row
                best_j = min(active_cols, key=lambda j: C[best_i, j])
            else:
                best_j = max(col_penalties, key=col_penalties.get)
                best_i = min(active_rows, key=lambda i: C[i, best_j])

            alloc = min(rem_s[best_i], rem_d[best_j])
            allocation[best_i, best_j] = alloc
            basic_cells.append((best_i, best_j))

            rem_s[best_i] -= alloc
            rem_d[best_j] -= alloc

            if rem_s[best_i] <= 1e-7:
                active_rows.discard(best_i)
            if rem_d[best_j] <= 1e-7:
                active_cols.discard(best_j)

        total_cost = float(np.sum(allocation * C))
        is_degenerate = len(basic_cells) < (m + n - 1)

        return {
            "method": "Vogel's Approximation Method (VAM)",
            "allocation": allocation,
            "cost_matrix": C,
            "basic_cells": basic_cells,
            "total_cost": round(total_cost, 4),
            "is_degenerate": is_degenerate,
            "required_basis_size": m + n - 1,
            "actual_basis_size": len(basic_cells)
        }

    @staticmethod
    def compare_initializations(cost_matrix: np.ndarray, supply: np.ndarray, demand: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run NWCM, LCM, and VAM on identical inputs and return comparative summary.
        """
        nw = TransportationSolver.northwest_corner(cost_matrix, supply, demand)
        lc = TransportationSolver.least_cost(cost_matrix, supply, demand)
        vam = TransportationSolver.vogels_approximation(cost_matrix, supply, demand)

        return [
            {"method": "Northwest Corner (NWCM)", "cost": nw["total_cost"], "degenerate": nw["is_degenerate"]},
            {"method": "Least Cost Method (LCM)", "cost": lc["total_cost"], "degenerate": lc["is_degenerate"]},
            {"method": "Vogel's Approximation (VAM)", "cost": vam["total_cost"], "degenerate": vam["is_degenerate"]}
        ]
