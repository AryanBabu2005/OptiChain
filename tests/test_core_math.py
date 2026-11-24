"""
Core Mathematical Optimization Tests for Syllabus Units I - IV.
"""

import pytest
import numpy as np
from src.algorithms.simplex import SimplexSolver
from src.algorithms.two_phase import TwoPhaseSimplex
from src.algorithms.big_m import BigMSimplex
from src.algorithms.dual_simplex import DualSimplexSolver
from src.algorithms.duality import DualityEngine
from src.algorithms.transportation import TransportationSolver
from src.algorithms.modi import MODISolver
from src.algorithms.hungarian import HungarianSolver
from src.algorithms.game_theory import ZeroSumGameSolver

class TestUnitISimplex:
    def test_bounded_maximization(self):
        # Max Z = 3x1 + 5x2 s.t. x1 <= 4, 2x2 <= 12, 3x1 + 2x2 <= 18, x1, x2 >= 0
        c = np.array([3, 5])
        A = np.array([[1, 0], [0, 2], [3, 2]])
        b = np.array([4, 12, 18])
        res = SimplexSolver().solve(c, A, b, maximize=True)
        assert res["status"] == "optimal"
        assert res["objective_value"] == 36.0
        assert res["x"] == [2.0, 6.0]

    def test_bounded_minimization(self):
        # Min Z = -3x1 - 5x2 s.t. x1 <= 4, 2x2 <= 12, 3x1 + 2x2 <= 18
        c = np.array([-3, -5])
        A = np.array([[1, 0], [0, 2], [3, 2]])
        b = np.array([4, 12, 18])
        res = SimplexSolver().solve(c, A, b, maximize=False)
        assert res["status"] == "optimal"
        assert res["objective_value"] == -36.0

    def test_unbounded_problem(self):
        # Max Z = 2x1 + x2 s.t. x1 - x2 <= 10, 2x1 <= 40 (x2 is unconstrained above)
        c = np.array([2, 1])
        A = np.array([[1, -1]])
        b = np.array([10])
        res = SimplexSolver().solve(c, A, b, maximize=True)
        assert res["status"] == "unbounded"

class TestUnitIIArtificialVariablesAndDuality:
    def test_two_phase_and_big_m_feasibility(self):
        # Min Z = 4x1 + x2 s.t. 3x1 + x2 = 3, 4x1 + 3x2 >= 6, x1 + 2x2 <= 4
        c = np.array([4, 1])
        A = np.array([[3, 1], [4, 3], [1, 2]])
        b = np.array([3, 6, 4])
        cts = ["==", ">=", "<="]

        # Two-Phase
        res_tp = TwoPhaseSimplex().solve(c, A, b, maximize=False, constraint_types=cts)
        assert res_tp["status"] == "optimal"
        assert abs(res_tp["objective_value"] - 3.4) < 1e-3

        # Big-M
        res_bm = BigMSimplex().solve(c, A, b, maximize=False, constraint_types=cts)
        assert res_bm["status"] == "optimal"
        assert abs(res_bm["objective_value"] - 3.4) < 1e-3

    def test_infeasible_problem_detection(self):
        # Infeasible: x1 + x2 <= 2 and x1 + x2 >= 4
        c = np.array([1, 1])
        A = np.array([[1, 1], [1, 1]])
        b = np.array([2, 4])
        cts = ["<=", ">="]

        res_tp = TwoPhaseSimplex().solve(c, A, b, maximize=True, constraint_types=cts)
        assert res_tp["status"] == "infeasible"

    def test_duality_and_complementary_slackness(self):
        c = np.array([2.0, 3.0])
        A_ub = np.array([[-1.0, -1.0], [-1.0, -2.0]])
        b_ub = np.array([-5.0, -6.0])

        engine = DualityEngine()
        verif = engine.verify_primal_dual(c, A_ub=A_ub, b_ub=b_ub)
        assert verif["success"] is True
        assert verif["strong_duality_holds"] is True
        assert verif["duality_gap"] < 1e-4
        for check in verif["complementary_slackness_checks"]:
            assert check["is_satisfied"] is True

class TestUnitIIITransportation:
    def test_transportation_initializations_and_modi(self):
        cost = np.array([
            [2, 3, 11, 7],
            [1, 0, 6, 1],
            [5, 8, 15, 9]
        ])
        supply = np.array([6, 1, 10])
        demand = np.array([7, 5, 3, 2])

        # NWCM
        res_nw = TransportationSolver.northwest_corner(cost, supply, demand)
        # LCM
        res_lc = TransportationSolver.least_cost(cost, supply, demand)
        # VAM
        res_vam = TransportationSolver.vogels_approximation(cost, supply, demand)

        assert res_nw["total_cost"] >= res_vam["total_cost"]

        # MODI optimization
        res_modi = MODISolver().optimize(cost, res_vam["allocation"], res_vam["basic_cells"])
        assert res_modi["is_optimal"] is True
        assert res_modi["optimal_cost"] <= res_vam["total_cost"]

    def test_unbalanced_transportation(self):
        cost = np.array([[2, 4], [3, 1]])
        supply = np.array([10, 20])  # sum = 30
        demand = np.array([15, 10])  # sum = 25 (unbalanced)
        C_b, S_b, D_b, balanced = TransportationSolver.balance_problem(cost, supply, demand)
        assert not balanced
        assert C_b.shape == (2, 3)  # Dummy destination added
        assert np.sum(S_b) == np.sum(D_b)

class TestUnitIVAssignmentAndGameTheory:
    def test_hungarian_assignment(self):
        # 4x4 Assignment
        cost = np.array([
            [9, 2, 7, 8],
            [6, 4, 3, 7],
            [5, 8, 1, 8],
            [7, 6, 9, 4]
        ])
        res = HungarianSolver.solve(cost)
        assert res["status"] == "optimal"
        assert res["objective_value"] == 13.0

        # Verify with brute force
        verif = HungarianSolver.brute_force_verify(cost)
        assert verif["verified"] is True
        assert verif["best_cost"] == 13.0

    def test_rectangular_assignment_with_dummies(self):
        cost = np.array([
            [10, 15, 9],
            [9, 18, 5]
        ])  # 2 workers, 3 tasks
        res = HungarianSolver.solve(cost)
        assert res["status"] == "optimal"
        assert res["num_dummy_assigned"] == 1

    def test_pure_strategy_saddle_point_game(self):
        payoff = np.array([
            [1, 2, 4],
            [0, -1, 3],
            [3, 5, 6]
        ])
        res = ZeroSumGameSolver.solve_game(payoff)
        assert res["type"] == "pure_strategy"
        assert res["has_saddle_point"] is True
        assert res["game_value"] == 3.0

    def test_mixed_strategy_game(self):
        # Matching Pennies: Payoffs +1, -1, -1, +1
        payoff = np.array([
            [1, -1],
            [-1, 1]
        ])
        res = ZeroSumGameSolver.solve_game(payoff)
        assert res["has_saddle_point"] is False
        assert abs(res["game_value"] - 0.0) < 1e-4
        assert abs(res["p1_probabilities"][0] - 0.5) < 1e-4
        assert abs(res["p2_probabilities"][0] - 0.5) < 1e-4
