from game_objects import HoleCards, Action, ActionType, GameStatus, Board
from stats.equity import EquityCalculator
from ia.bet_curve_optimizer import BetCurveOptimizer
from ia.neural_network import NeuralNetwork
from player import Player

raise NotImplementedError('Not implemented yet')
class DecisionMaker(Player):
    def __init__(self, name: str, rl_model):
        super().__init__(name)
        self.equity_calculator = EquityCalculator()
        self.bet_optimizer = BetCurveOptimizer()
        self.rl_model = rl_model  # Modelo de RL
        self.opponent_model = NeuralNetwork.OpponentModel()

    def decide_action(self, hole_cards: HoleCards, board: Board, status: GameStatus) -> Action:
        equity = self.equity_calculator.calculate_equity(
            hole_cards=HoleCards(hole_cards),
            board=board
        )
        pot_size = self._calculate_pot_size(status)
        target_bet = (pot_size * equity) / (1 - equity) if equity < 1 else pot_size
        proxima_apuesta = self.bet_optimizer.generate_bet_curve(
            current_bet=status.bets[status.current_player],
            target_bet=target_bet,
            remaining_rounds=status.remaining_rounds
        )
        valid_actions = status.get_valid_actions()


        # Farol o All-in basado en RL
        state = self._build_state(hole_cards, board, status, equity, pot_size)
        rl_action = self.rl_model.predict_action(state)

        if rl_action == "ALL_IN" and ActionType.ALL_IN in valid_actions:
            return Action(ActionType.ALL_IN, None)
        elif rl_action == "BLUFF" and self._should_bluff(status):
            return Action(ActionType.RAISE, int(pot_size * 0.75))


        # Si estamos por debajo de la curva óptima, hacer raise
        if proxima_apuesta > 0 and ActionType.RAISE in valid_actions:
            return Action(ActionType.RAISE, int(proxima_apuesta))

        # Decisiones basadas en la fase del juego
        if status.game_phase == status.GamePhase.PREFLOP:
            return self._handle_preflop(equity, status, target_bet)

        elif status.game_phase == status.GamePhase.FLOP:
            return self._handle_flop(equity, status, target_bet)

        elif status.game_phase == status.GamePhase.TURN:
            return self._handle_turn(equity, status, target_bet)

        elif status.game_phase == status.GamePhase.RIVER:
            return self._handle_river(equity, status, target_bet)

        # Acción por defecto: check si es posible, sino fold
        if ActionType.CHECK in valid_actions:
            return Action(ActionType.CHECK, None)

        return Action(ActionType.FOLD, None)


    def _handle_preflop(self, equity: float, status: GameStatus, target_bet: float) -> Action:
        # Modelo Preflop
        total_opponent_bet = NeuralNetwork.PreflopModel(status.bets[1 - status.current_player])
        if total_opponent_bet > target_bet:
            return self._check_or_fold(status)
        return Action(ActionType.CALL, None)


    def _handle_flop(self, equity: float, status: GameStatus, target_bet: float) -> Action:
        # Modelo Flop
        total_opponent_bet = NeuralNetwork.FlopModel(
            player_first_bet=status.bets[1 - status.current_player],
            probs=self.equity_calculator.probabilities
        )
        return self._evaluate_action(total_opponent_bet, equity, status, target_bet)


    def _handle_turn(self, equity: float, status: GameStatus, target_bet: float) -> Action:
        # Modelo Turn
        total_opponent_bet = NeuralNetwork.TurnModel(
            player_first_bet=status.bets[1 - status.current_player],
            probs=self.equity_calculator.probabilities
        )
        return self._evaluate_action(total_opponent_bet, equity, status, target_bet)


    def _handle_river(self, equity: float, status: GameStatus, target_bet: float) -> Action:
        # Modelo River
        total_opponent_bet = NeuralNetwork.RiverModel(
            player_first_bet=status.bets[1 - status.current_player],
            probs=self.equity_calculator.probabilities
        )
        return self._evaluate_action(total_opponent_bet, equity, status, target_bet)


    def _evaluate_action(self, total_opponent_bet: float, equity: float, status: GameStatus, target_bet: float) -> Action:
        # Evaluar acción con margen y probabilidad
        margin_value = self._calculate_margin(equity, status)
        if total_opponent_bet > target_bet:
            return self._check_or_fold(status)

        if margin_value > 0 or (equity > 0.3 and status.bets[1 - status.current_player] < target_bet * 0.1):
            return Action(ActionType.CALL, None)

        return self._check_or_fold(status)


    def _check_or_fold(self, status: GameStatus) -> Action:
        # Realizar check si es posible, sino fold
        if ActionType.CHECK in status.get_valid_actions():
            return Action(ActionType.CHECK, None)
        return Action(ActionType.FOLD, None)


    def _calculate_pot_size(self, status: GameStatus) -> int:
        return sum(status.bets) + sum(
            min(bet, money)
            for bet, money in zip(status.bets, status.players_money)
        )


    def _calculate_margin(self, equity: float, status: GameStatus) -> float:
        total_money = sum(status.players_money) + self._calculate_pot_size(status)
        expected_gain = equity * total_money
        current_investment = status.bets[status.current_player]
        return expected_gain - current_investment


    def _build_state(self, hole_cards, board, status, equity, pot_size):
        return {
            "hole_cards": hole_cards,
            "board": board,
            "phase": status.game_phase,
            "equity": equity,
            "pot_size": pot_size,
            "bets": status.bets,
            "player_money": status.players_money,
            "opponent_behavior": self.opponent_model.get_behavior_features()
        }