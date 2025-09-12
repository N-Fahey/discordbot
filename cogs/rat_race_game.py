import random

class Rat:
    def __init__(self, chance_to_move: float = 0.3, positions_per_move: int = 5, icon: str = "🐭"):
        self.chance_to_move = chance_to_move
        self.icon = icon
        self.positions_per_move = positions_per_move

    def has_moved(self):
        if random.random() < self.chance_to_move:
            return True
        return False
    
    def __repr__(self):
        return self.icon
    
    def __str__(self):
        return self.icon
    

class RatRace:
    def __init__(self, lane_length: int, rats):
        self.lane_length = lane_length
        self.rats = rats

        self.board = [[rat, 0] for rat in rats]
        self.winners = None

    def play(self):
        while True:
            self.do_turn()
            winners = self.check_for_winners()

            if winners:
                self.winners = winners
                break
    
    def do_turn(self):
        for index, (rat, position) in enumerate(self.board):
            if rat.has_moved():
                self.board[index] = [rat, position + rat.positions_per_move]

    def check_for_winners(self):
        return [index for index, lane_status in enumerate(self.board) if lane_status[1] >= self.lane_length]

    def construct_lane_str(self, rat, lane_pos):
        lane_str = "-" * self.lane_length
        lane_str = lane_str[:lane_pos] + rat.icon + lane_str[lane_pos + 1:]
        return lane_str

    def __repr__(self):
        res = ""
        for rat, lane_pos in self.board:
            res += self.construct_lane_str(rat, lane_pos)
            res += "\n"
        return res

