"""
MODI (Modified Distribution / u-v Method) Optimization for Transportation Problems.
Tests optimality of basic feasible solutions and iteratively improves them
via stepping-stone closed loop shifts to achieve global optimality.
"""

from typing import Dict, Any, List, Tuple, Optional, Set
import numpy as np

class MODISolver:
    def __init__(self, max_iterations: int = 100):
        self.max_iter = max_iterations

    @staticmethod
    def _find_closed_loop(start: Tuple[int, int], basic_cells: Set[Tuple[int, int]]) -> Optional[List[Tuple[int, int]]]:
        """
        Find a closed loop starting at non-basic cell 'start' and alternating
        between horizontal and vertical moves among basic cells.
        """
        start_r, start_c = start
        all_cells = list(basic_cells) + [start]

        def get_neighbors(curr: Tuple[int, int], move_horizontal: bool) -> List[Tuple[int, int]]:
            r, c = curr
            if move_horizontal:
                return [cell for cell in all_cells if cell[0] == r and cell[1] != c]
            else:
                return [cell for cell in all_cells if cell[1] == c and cell[0] != r]

        # Depth-First Search for closed loop
        def dfs(path: List[Tuple[int, int]], move_horizontal: bool) -> Optional[List[Tuple[int, int]]]:
            curr = path[-1]
            neighbors = get_neighbors(curr, move_horizontal)

            for nxt in neighbors:
                if nxt == start and len(path) >= 4:
                    return path  # Found closed loop
                if nxt not in path and nxt in basic_cells:
                    res = dfs(path + [nxt], not move_horizontal)
                    if res is not None:
                        return res
            return None

        # Try starting horizontal or vertical
        loop = dfs([start], True)
        if loop is None:
            loop = dfs([start], False)
        return loop

    def optimize(self, cost_matrix: np.ndarray, initial_allocation: np.ndarray,
                 basic_cells: Optional[List[Tuple[int, int]]] = None) -> Dict[str, Any]:
        """
        Perform MODI optimization to optimality.
        """
        C = np.array(cost_matrix, dtype=float).copy()
        X = np.array(initial_allocation, dtype=float).copy()
        m, n = C.shape

        if basic_cells is None:
            b_cells = set((i, j) for i in range(m) for j in range(n) if X[i, j] > 1e-7)
        else:
            b_cells = set(basic_cells)

        # Ensure m + n - 1 basic cells
        while len(b_cells) < (m + n - 1):
            for i in range(m):
                for j in range(n):
                    if (i, j) not in b_cells:
                        b_cells.add((i, j))
                        break
                if len(b_cells) == (m + n - 1):
                    break

        iterations_log = []
        is_optimal = False

        for it in range(1, self.max_iter + 1):
            # Step 1: Solve u_i + v_j = C_{ij} for all (i, j) in b_cells
            u = [None] * m
            v = [None] * n
            u[0] = 0.0  # Convention

            changed = True
            while changed:
                changed = False
                for i, j in b_cells:
                    if u[i] is not None and v[j] is None:
                        v[j] = C[i, j] - u[i]
                        changed = True
                    elif v[j] is not None and u[i] is None:
                        u[i] = C[i, j] - v[j]
                        changed = True

            # If any disjoint components remain, fill with 0
            for i in range(m):
                if u[i] is None:
                    u[i] = 0.0
            for j in range(n):
                if v[j] is None:
                    v[j] = 0.0

            # Step 2: Compute opportunity costs Delta_{ij} = C_{ij} - (u_i + v_j) for non-basic cells
            delta = np.zeros((m, n), dtype=float)
            min_delta = 0.0
            entering_cell = None

            for i in range(m):
                for j in range(n):
                    if (i, j) not in b_cells:
                        delta[i, j] = C[i, j] - (u[i] + v[j])
                        if delta[i, j] < min_delta - 1e-7:
                            min_delta = delta[i, j]
                            entering_cell = (i, j)

            # Optimality check
            if min_delta >= -1e-7 or entering_cell is None:
                is_optimal = True
                break

            # Step 3: Find closed stepping stone loop for entering cell
            loop = self._find_closed_loop(entering_cell, b_cells)
            if loop is None or len(loop) < 4:
                # Loop could not be formed due to degeneracy, solution accepted
                break

            # Step 4: Determine theta (minimum along negative cells in loop)
            # Loop has alternating +/-: index 0 is +, 1 is -, 2 is +, 3 is -...
            theta = float("inf")
            leaving_cell = None

            for k in range(1, len(loop), 2):
                cell = loop[k]
                val = X[cell[0], cell[1]]
                if val < theta:
                    theta = val
                    leaving_cell = cell

            # Step 5: Shift allocation along loop
            for k, (r, c) in enumerate(loop):
                if k % 2 == 0:
                    X[r, c] += theta
                else:
                    X[r, c] -= theta

            # Update basis
            b_cells.add(entering_cell)
            if leaving_cell in b_cells:
                b_cells.remove(leaving_cell)

            current_cost = float(np.sum(X * C))
            iterations_log.append({
                "iteration": it,
                "entering_cell": entering_cell,
                "leaving_cell": leaving_cell,
                "theta": float(theta),
                "cost": round(current_cost, 4)
            })

        optimal_cost = float(np.sum(X * C))
        return {
            "status": "optimal" if is_optimal else "improved",
            "optimal_allocation": X,
            "optimal_cost": round(optimal_cost, 4),
            "iterations": len(iterations_log),
            "iterations_log": iterations_log,
            "is_optimal": is_optimal
        }
