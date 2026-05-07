from game_logic import check_win, count_in_row, make_move

test_board = [[2, 2, 2, 0, 0, 0, 0], [0]*7, [0]*7, [0]*7, [0]*7, [0]*7, [0]*7]

def find_move(board):
    move_board = board
    for col in range(len(board[0])):
        for row in range(len(board)):
            if move_board[row][col] == 0:
                move_board[row][col] = 2
                win = check_win(board, col, row, player=2)
                board[row][col] = 0
                if win:
                    return col
                
    for col in range(len(board[0])):
        for row in range(len(board)):
            if move_board[row][col] == 0:
                move_board[row][col] = 2
                win = check_win(board, col, row, player=1)
                board[row][col] = 0
                if win:
                    return col
                
    return best_move(board)

def best_move(board):
    move_board = board
    moves = []
    for col in range(len(board[0])):
        row = make_move(move_board, col, player=2)
        print(row)
        print(count_in_row(move_board, col, row, player=2))
        if row != -1:
            count = max(count_in_row(move_board, col, row, player=2))
            if count == 1:
                moves.append(0)
            elif count == 2:
                moves.append(500)
            elif count == 3:
                moves.append(2000)
            elif count >= 4:
                moves.append(10000)
    return moves
                
print(best_move(test_board))