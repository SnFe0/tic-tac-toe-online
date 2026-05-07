def create_board(rows = 6, columns = 7):
    board = []
    for _ in range(rows):
        row = [0] * columns
        board.append(row)
    return board

def print_board(board):
    for rows in range(len(board)-1, -1, -1):
        for columns in board[rows]:
            if columns == 0:
                print('⚪', end=' ')
            if columns == 1:
                print('🔵', end=' ')
            if columns == 2:
                print('🔴', end=' ')
        print()
    print(end=' ')    
    for i in range(len(board[0])):
        print(i+1, end='  ')
    print('\n')

def make_move(board, column, player):
    if column < 0 or column > len(board[0]):
        return -1
    for row in range(len(board)):
        if board[row][column] == 0:
            board[row][column] = player
            return row
    return -1

def check_horizontal(board, row, player):
    count = 0
    for col in range(len(board[0])):
        if board[row][col] == player:
            count += 1
            if count >= 4:
                return True
        else:
            count = 0
    return False

def check_vertical(board, col, player):
    count = 0
    for row in range(len(board)-1, -1, -1):
        if board[row][col] == player:
            count += 1
            if count >= 4:
                return True
        else:
            count = 0
    return False

def check_diaogonal_left_right(board, column, row, player):
    p_row = row
    p_col = column
    for _ in range(row):
        p_row -= 1
        p_col -= 1
        if p_col == 0:
            break
    count = 0
    for _ in range(len(board[0])):
        if board[p_row][p_col] == player:
            count += 1
        else:
            count = 0
        if count >= 4:
            return True
        if p_row == len(board) - 1 or p_col == len(board[0]) - 1:
            return False
        p_row += 1
        p_col += 1
    return False

def check_diaogonal_right_left(board, column, row, player):
    p_row = row
    p_col = column
    if p_col != 6:
        for _ in range(row):
            p_row -= 1
            p_col += 1
            if p_col >= len(board[0]) - 1:
                break
    count = 0
    for _ in range(len(board[0])):
        if board[p_row][p_col] == player:
            count += 1
        else:
            count = 0
        if count >= 4:
            return True
        if p_row == len(board) - 1 or p_col == 0:
            return False
        p_row += 1
        p_col -= 1
    return False

def check_win(board, column, row, player):
    win = []
    win.append(check_vertical(board, column, player))
    win.append(check_horizontal(board, row, player))
    win.append(check_diaogonal_left_right(board, column, row, player))
    win.append(check_diaogonal_right_left(board, column, row, player))
    if True in win:
        return True
    return False

board = create_board()
player = 1
print_board(board)
while True:
    try:
        move = int(input(f'Игрок {player}, укажите столбец: '))
    except ValueError:
        move = -1
    if 0 < move and move <= len(board[0]):
        last_row = make_move(board, move-1, player)
        if last_row != -1:
            print_board(board)
            if check_win(board, move-1, last_row, player):
                print(f'Победил {player} игрок')
                break
            if player == 1:
                player = 2
            else:
                player = 1
        else:
            print('Невозможный ход')
    else:
        print(f'Неправильное значение, введите значение от 1 до {len(board[0])}')