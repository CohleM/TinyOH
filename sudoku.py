import random

class Sudoku:
    def __init__(self):
        self.board = [[0]*9 for _ in range(9)]
        self.fill_values()

    def fill_values(self):
        random.shuffle(self.nums)
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    for num in self.nums:
                        if self.is_safe(i, j, num):
                            self.board[i][j] = num
                            if self.fill_values():
                                return True
                            self.board[i][j] = 0
                    return False
        return True

        def is_safe(self, row, col, num):
        return (num not in self.board[row] and
                num not in [self.board[x][col] for x in range(9)] and
                num not in [self.board[i][j] for i in range(3) for j in range(3) if i // 3 == row // 3 and j // 3 == col // 3])

    def print_board(self):
        for row in self.board:
            print(" ".join(map(str, row)))
    def __init__(self):
        self.board = [[0]*9 for _ in range(9)]
        self.fill_values()

    def fill_values(self):
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    num = random.randint(1, 9)
                    if self.is_safe(i, j, num):
                        self.board[i][j] = num
                        if self.fill_values():
                            return True
                        self.board[i][j] = 0
                    if all(self.board[x][j] != 0 for x in range(9)):
                        return False
            if all(self.board[i][y] != 0 for y in range(9)):
                return False
        return True

    def is_safe(self, row, col, num):
        for x in range(9):
            if self.board[row][x] == num or self.board[x][col] == num:
                return False
        startRow, startCol = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if self.board[i + startRow][j + startCol] == num:
                    return False
        return True

    def print_board(self):
        for row in self.board:
            print(" ".join(map(str, row)))

if __name__ == '__main__':
    sudoku_game = Sudoku()
    sudoku_game.print_board()