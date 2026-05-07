def create_board(rows = 6, columns = 7):
    return [[0 for _ in range(columns)] for _ in range(rows)]

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
    print('  '.join(str(i+1) for i in range(len(board[0]))))
    print('\n')

def make_move(board, column, player):
    if column < 0 or column >= len(board[0]):
        return -1
    for row in range(len(board)):
        if board[row][column] == 0:
            # board[row][column] = player
            return row
    return -1

def count_in_row(board, column, row, player):
    # 1. Горизонталь (влево-вправо через точку)
    count = 1  # текущая фишка
    # Влево от точки
    left = column - 1
    while left >= 0 and board[row][left] == player:
        count += 1
        left -= 1
    # Вправо от точки
    right = column + 1
    while right < 7 and board[row][right] == player:
        count += 1
        right += 1
    print(count)

def check_draw(board):
    return all(cell != 0 for cell in board[len(board) - 1])

def check_win(board, column, row, player):
    p_row = row
    count = 0
    for col in range(len(board[0])):
        if board[p_row][col] == player:
            count += 1
            if count >= 4:
                return True
        else:
            count = 0

    p_col = column
    count = 0
    for o_row in range(len(board)-1, -1, -1):
        if board[o_row][p_col] == player:
            count += 1
            if count >= 4:
                return True
        else:
            count = 0      

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
            break
        p_row += 1
        p_col += 1

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
            break
        p_row += 1
        p_col -= 1

    return False