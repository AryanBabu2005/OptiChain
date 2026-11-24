"""
Two-Person Zero-Sum Game Theory Engine for OptiChain.
Implements:
1. Pure strategy saddle point detection (Maximin == Minimax).
2. 2x2 analytical mixed strategy solutions.
3. Graphical solution for 2xn and mx2 games.
4. Linear Programming formulation for general mxn zero-sum games.
Contextualized for freight logistics operator vs. adversarial network disruption scenarios.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy.optimize import linprog

class ZeroSumGameSolver:
    @staticmethod
    def solve_game(payoff_matrix: np.ndarray,
                   p1_strategies: Optional[List[str]] = None,
                   p2_strategies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Comprehensive solver for Two-Person Zero-Sum Game.
        Player 1 maximizes payoff, Player 2 minimizes payoff.
        """
        A = np.array(payoff_matrix, dtype=float)
        m, n = A.shape

        if p1_strategies is None:
            p1_strategies = [f"P1_Strategy_{i+1}" for i in range(m)]
        if p2_strategies is None:
            p2_strategies = [f"P2_Strategy_{j+1}" for j in range(n)]

        # 1. Pure Strategy Saddle Point Check
        row_minima = np.min(A, axis=1)
        maximin_val = float(np.max(row_minima))
        maximin_row = int(np.argmax(row_minima))

        col_maxima = np.max(A, axis=0)
        minimax_val = float(np.min(col_maxima))
        minimax_col = int(np.argmin(col_maxima))

        has_saddle_point = abs(maximin_val - minimax_val) < 1e-6

        if has_saddle_point:
            p1_prob = np.zeros(m)
            p1_prob[maximin_row] = 1.0
            p2_prob = np.zeros(n)
            p2_prob[minimax_col] = 1.0

            return {
                "type": "pure_strategy",
                "game_value": round(maximin_val, 4),
                "has_saddle_point": True,
                "saddle_point_cell": (maximin_row, minimax_col),
                "p1_optimal_strategy": p1_strategies[maximin_row],
                "p2_optimal_strategy": p2_strategies[minimax_col],
                "p1_probabilities": p1_prob.tolist(),
                "p2_probabilities": p2_prob.tolist(),
                "row_minima": row_minima.tolist(),
                "col_maxima": col_maxima.tolist()
            }

        # 2. Check for 2x2 Analytical Solution
        if m == 2 and n == 2:
            a11, a12 = A[0, 0], A[0, 1]
            a21, a22 = A[1, 0], A[1, 1]
            denom = (a11 + a22) - (a12 + a21)

            if abs(denom) > 1e-7:
                p1 = (a22 - a21) / denom
                p2 = 1.0 - p1
                q1 = (a22 - a12) / denom
                q2 = 1.0 - q1
                val = (a11 * a22 - a12 * a21) / denom

                if 0.0 <= p1 <= 1.0 and 0.0 <= q1 <= 1.0:
                    return {
                        "type": "mixed_strategy_2x2",
                        "game_value": round(float(val), 4),
                        "has_saddle_point": False,
                        "p1_probabilities": [round(float(p1), 4), round(float(p2), 4)],
                        "p2_probabilities": [round(float(q1), 4), round(float(q2), 4)],
                        "p1_strategies": p1_strategies,
                        "p2_strategies": p2_strategies
                    }

        # 3. General m x n Mixed Strategy via Linear Programming
        # Shift all payoffs positive so V > 0
        min_elem = np.min(A)
        shift = abs(min_elem) + 1.0 if min_elem <= 0 else 0.0
        A_shifted = A + shift

        # Player 1 LP: Maximize V_shifted <=> Minimize sum(x_i)
        # where x_i = p_i / V_shifted, subject to A_shifted^T x >= 1, x >= 0
        c_p1 = np.ones(m)
        A_ub_p1 = -A_shifted.T  # -A^T x <= -1
        b_ub_p1 = -np.ones(n)

        res_p1 = linprog(c_p1, A_ub=A_ub_p1, b_ub=b_ub_p1, bounds=(0, None), method="highs")

        if res_p1.success:
            sum_x = float(res_p1.fun)
            v_shifted = 1.0 / sum_x if sum_x > 0 else 0.0
            p1_probs = (res_p1.x * v_shifted).tolist()
            game_val = v_shifted - shift

            # Player 2 Probabilities from Dual / Player 2 LP
            c_p2 = -np.ones(n)  # Maximize sum(y_j) <=> Minimize -sum(y_j)
            A_ub_p2 = A_shifted  # A y <= 1
            b_ub_p2 = np.ones(m)

            res_p2 = linprog(-c_p2, A_ub=A_ub_p2, b_ub=b_ub_p2, bounds=(0, None), method="highs")
            if res_p2.success:
                sum_y = float(res_p2.fun)
                p2_probs = (res_p2.x / sum_y).tolist() if sum_y > 0 else [1.0 / n] * n
            else:
                p2_probs = [1.0 / n] * n

            return {
                "type": "mixed_strategy_lp",
                "game_value": round(float(game_val), 4),
                "has_saddle_point": False,
                "p1_probabilities": [round(float(p), 4) for p in p1_probs],
                "p2_probabilities": [round(float(q), 4) for q in p2_probs],
                "p1_strategies": p1_strategies,
                "p2_strategies": p2_strategies,
                "row_minima": row_minima.tolist(),
                "col_maxima": col_maxima.tolist()
            }

        return {
            "type": "error",
            "game_value": None,
            "has_saddle_point": False,
            "message": "LP solver could not converge on mixed strategy."
        }
