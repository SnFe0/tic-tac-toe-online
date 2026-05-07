import tkinter as tk
from tkinter import messagebox
from game_logic import create_board, make_move, check_win, check_draw, count_in_row

global_bg = '#00FA9A'

class ConnectFour:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("4 в ряд")
        self.root.geometry("800x700")
        self.root['bg'] = global_bg
        
        self.board = create_board()
        self.current_player = 1
        self.scores = {'1': 0,'2': 0}
        self.game_over = False

        if self.current_player == 2:
            self.root.after(1000, self.make_bot_move)

        self.selected_column = 3
        self.show_preview = True
        self.is_animating = False

        self.create_widgets()
        self.draw_board()
        self.setup_keyboard()

        self.reset_button = tk.Button(self.root, 
                                    text='Новая игра',
                                    font='Roboto 14',
                                    command=self.reset_game,
                                    state='disabled')

    def create_widgets(self):
        self.title_label = tk.Label(self.root, text='4 в ряд', font='Roboto 26', bg=global_bg)
        self.title_label.pack(pady=5)

        self.button_frame = tk.Frame(self.root)
        # self.button_frame.pack(pady=5)

        for col in range(len(self.board[0])):
            btn = tk.Button(self.button_frame, 
                            text=str(col+1), 
                            font='Roboto 16', 
                            width=4, height=1,
                            command=lambda c=col: self.button_click(c))
            btn.pack(side=tk.LEFT, padx=2)

        self.canvas_frame = tk.Frame(self.root, bg=global_bg)
        self.canvas_frame.pack(pady=5)

        self.score_label = tk.Label(self.canvas_frame, text=f'Игрок 1: {self.scores['1']}      Игрок 2: {self.scores['2']}',
                                     font='Roboto 16', bg=global_bg)
        self.score_label.pack()

        self.canvas = tk.Canvas(self.canvas_frame, width=500, height=400, bg="#8D00B1")
        self.canvas.pack(pady=10)

        self.status_label = tk.Label(self.root, 
                                     text = f'Ходит {self.current_player} игрок (синий)', 
                                     font = 'Arial 16',
                                     fg='blue',
                                     bg=global_bg)
        self.status_label.pack(pady=5)

        self.guide_frame = tk.Frame(self.root, width=600)
        self.guide_frame.pack()
        self.guide_label = tk.Label(self.guide_frame, text='<--/--> - влево/вправо\nspace/enter - сделать ход\nspace/r - новая игра\nesc - выход',
                                    bg=global_bg, font=('Roboto', 14))
        self.guide_frame.place(x=20, y=550)
        self.guide_label.pack()

    def draw_board(self):
        self.canvas.delete('all')

        cell_size = 65
        radius = 25

        for row in range(len(self.board)):
            for col in range(len(self.board[0])):

                flipped_row = 5 - row
                
                x = 22 + col * cell_size + cell_size / 2
                y = 8 + flipped_row * cell_size + cell_size / 2

                cell_value = self.board[row][col]
                if cell_value == 0:
                    color = 'white'
                elif cell_value == 1:
                    color = 'blue'
                else:
                    color = 'red'

                self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                                        fill=color, outline='black', width=2)
                
        if self.show_preview and not self.game_over:
            self.draw_preview()

    def draw_preview(self):
        CELL_SIZE = 65
        RADIUS = 25

        # 22 + col * cell_size + cell_size / 2
        x = 22 + self.selected_column * CELL_SIZE + CELL_SIZE // 2
        y = 30 
        color = "blue" if self.current_player == 1 else "red"
    
        self.canvas.create_oval(x-RADIUS, y-RADIUS, x+RADIUS, y+RADIUS,
                           fill='', outline=color, width=6,
                           dash=(4, 4), 
                           tags="preview")
    
        self.canvas.create_line(x, y+RADIUS+5, x, y+RADIUS+20,
                           arrow=tk.LAST, fill='black', width=2,
                           tags="preview")

    def button_click(self, column):
        if self.game_over or self.is_animating:
            return
        
        target_row = make_move(self.board, column, self.current_player)

        if target_row == -1:
            messagebox.showwarning('НЕВОЗМОЖНЫЙ ХОД', 'Столбец заполнен')
            return
        
        self.animate_falling(column, target_row, self.current_player)
        
    def reset_game(self):
        self.hide_reset_button()
        self.board = create_board()
        self.current_player = 1
        self.game_over = False
        self.draw_board()
        self.status_label.config(text="Ходит 1 игрок (синий)",
                                fg="blue", font=('Roboto', 16))
        self.draw_preview()
        
    def show_reset_button(self):
        if not self.reset_button.winfo_ismapped():  
            self.reset_button.pack(pady=10)  
            self.reset_button.config(state='normal')  
    
    def hide_reset_button(self):
        if self.reset_button.winfo_ismapped(): 
            self.reset_button.pack_forget()
            self.reset_button.config(state='disabled')    

    def setup_keyboard(self):
    # Биндим клавиши ко всему окну
        self.root.bind('<Key>', self.on_key_press)
    
    # Фокус на окно (чтобы клавиши работали)
        self.root.focus_set()
    
    def on_key_press(self, event):
        key = event.keysym  # имя клавиши
            
        if key == 'Left':
            # Стрелка влево
            self.selected_column = max(0, self.selected_column - 1)
            self.update_preview()
            
        elif key == 'Right':
            # Стрелка вправо
            self.selected_column = min(6, self.selected_column + 1)
            self.update_preview()
            
        elif key in ('Return', 'space'):
            # Enter или Space - сделать ход
            self.make_move_from_key(self.selected_column)
            self.draw_preview()

            if self.reset_button.winfo_ismapped():
                self.reset_game()
            
        elif key.lower() == 'r':
            # R - новая игра
            if self.reset_button.winfo_ismapped():
                self.reset_game()
                
        elif key == 'Escape':
            # Escape - выход
            self.root.quit()
    
    def make_move_from_key(self, column):
        if not self.game_over:
            self.button_click(column)  # используем существующую логику
        
    def update_preview(self):
        # Удаляем старый предпросмотр
        self.canvas.delete("preview")
        
        # Рисуем новый
        if self.show_preview and not self.game_over:
            self.draw_preview()

    def animate_falling(self, column, target_row, player):
        self.is_animating = True
        CELL_SIZE = 65
        RADIUS = 25

        start_x = 22 + self.selected_column * CELL_SIZE + CELL_SIZE // 2
        start_y = -50

        flipped_row = 5 - target_row
        end_x = start_x
        end_y = 8 + flipped_row * CELL_SIZE + CELL_SIZE // 2

        color = 'blue' if player == 1 else 'red'

        curent_y = start_y

        def update_animation():
            nonlocal curent_y

            self.canvas.delete('falling_cell')

            speed = 15

            if curent_y < end_y:
                curent_y += speed
                if curent_y > end_y:
                    curent_y = end_y

                self.canvas.create_oval(start_x - RADIUS, curent_y - RADIUS,
                                    start_x + RADIUS, curent_y + RADIUS,
                                    fill = color,
                                    outline='black',
                                    width = 2,
                                    tags='falling_cell')
            
                self.root.after(33, update_animation)

            else:
                self.board[target_row][column] = player

                self.draw_board()

                self.is_animating = False

                self.check_after_animation(column, target_row, player)

        update_animation()
    
    def check_after_animation(self, column, target_row, player):
        if check_win(self.board, column, target_row, self.current_player):
            self.game_over = True
            self.status_label.config(text=f'Победил игрок {self.current_player}')
            self.scores[str(self.current_player)] += 1
            self.score_label.config(text=f'Игрок 1: {self.scores['1']}      Игрок 2: {self.scores['2']}')
            messagebox.showwarning('ПОБЕДА', f'Победил игрок {self.current_player}')
            self.show_reset_button()
            return
        
        if check_draw(self.board):
            self.game_over = True
            self.status_label.config(text=f'Ничья')
            messagebox.showwarning('НИЧЬЯ', 'Ничья! Ходов не осталось')
            self.show_reset_button()
            return

        self.current_player = 2 if self.current_player == 1 else 1
        player_color = "синий" if self.current_player == 1 else "красный"
        self.status_label.config(text=f'Ходит {self.current_player} игрок ({player_color})',
                                fg="blue" if self.current_player == 1 else "red")
        
        self.draw_preview()
        count_in_row(self.board, column, target_row, self.current_player)

    def run(self):
        self.root.mainloop()        

if __name__ == "__main__":
    game = ConnectFour()
    game.run()