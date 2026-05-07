# four_gui.py
import tkinter as tk
from tkinter import messagebox, simpledialog
import socket
import threading
from game_logic import create_board, check_win, check_draw, make_move

global_bg = '#00FA9A'

class ConnectFourOnline:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("4 в ряд - Онлайн")
        self.root.geometry("800x700")
        self.root['bg'] = global_bg
        
        # Выбор режима
        self.choose_mode()
        
    def choose_mode(self):
        """Выбор: создать игру или подключиться"""
        choice_frame = tk.Frame(self.root, bg=global_bg)
        choice_frame.pack(expand=True)
        
        tk.Label(
            choice_frame,
            text="Выберите режим:",
            font=('Roboto', 20),
            bg=global_bg
        ).pack(pady=20)
        
        # Кнопка "Создать игру"
        tk.Button(
            choice_frame,
            text="Создать игру (Хост)",
            font=('Roboto', 16),
            width=20,
            height=2,
            command=self.create_host_game,
            bg='lightblue'
        ).pack(pady=10)
        
        # Кнопка "Подключиться"
        tk.Button(
            choice_frame,
            text="Подключиться к игре",
            font=('Roboto', 16),
            width=20,
            height=2,
            command=self.create_client_game,
            bg='lightgreen'
        ).pack(pady=10)
    
    def create_host_game(self):
        """Создает игру как хост"""
        # Спрашиваем порт
        port = simpledialog.askinteger("Порт", "Введите порт (например 5555):", 
                                      parent=self.root, minvalue=1024, maxvalue=65535)
        if not port:
            return
            
        # Очищаем окно
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Запускаем сервер в отдельном потоке
        self.is_host = True
        self.player_number = 1
        self.port = port
        
        # Создаем игру
        self.setup_game()
        
        # Показываем IP для подключения
        import socket as s
        hostname = s.gethostname()
        ip = s.gethostbyname(hostname)
        
        info_label = tk.Label(
            self.root,
            text=f"Ожидание подключения...\n"
                 f"Ваш IP: {ip}\n"
                 f"Порт: {port}\n"
                 f"Сообщите эти данные второму игроку",
            font=('Roboto', 12),
            bg=global_bg
        )
        info_label.pack(pady=10)
        
        # Запускаем сервер
        threading.Thread(target=self.start_server, daemon=True).start()
    
    def create_client_game(self):
        """Подключается к игре как клиент"""
        # Спрашиваем IP и порт
        ip = simpledialog.askstring("IP", "Введите IP сервера:", parent=self.root)
        if not ip:
            return
            
        port = simpledialog.askinteger("Порт", "Введите порт:", 
                                      parent=self.root, minvalue=1024, maxvalue=65535)
        if not port:
            return
            
        # Очищаем окно
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Настраиваем клиент
        self.is_host = False
        self.player_number = 2
        self.host_ip = ip
        self.port = port
        
        # Создаем игру
        self.setup_game()
        
        # Пытаемся подключиться
        if not self.connect_to_server():
            messagebox.showerror("Ошибка", "Не удалось подключиться к серверу")
            self.root.quit()
    
    def setup_game(self):
        """Настраивает игровое поле"""
        self.board = create_board()
        self.current_player = 1  # всегда начинает игрок 1
        self.game_over = False
        self.is_animating = False
        self.selected_column = 3
        
        # Сокет для общения
        self.socket = None
        
        # Создаем виджеты
        self.create_widgets()
        self.draw_board()
        self.setup_keyboard()
        
        # Кнопка новой игры
        self.reset_button = tk.Button(
            self.root,
            text='Новая игра',
            font='Roboto 14',
            command=self.reset_game,
            state='disabled'
        )
        
        # Если мы клиент, отключаем управление пока не подключимся
        if not self.is_host and self.player_number == 2:
            self.status_label.config(text="Подключение...", fg="gray")
    
    def create_widgets(self):
        """Создает интерфейс"""
        title_text = "4 в ряд - Онлайн"
        if self.is_host:
            title_text += " (Хост)"
        else:
            title_text += " (Клиент)"
            
        self.title_label = tk.Label(
            self.root, 
            text=title_text, 
            font='Roboto 26', 
            bg=global_bg
        )
        self.title_label.pack(pady=5)
        
        self.status_label = tk.Label(
            self.root,
            text=f'Игрок {self.player_number} - Ожидание...',
            font='Arial 16',
            fg='blue' if self.player_number == 1 else 'red',
            bg=global_bg
        )
        self.status_label.pack(pady=5)
        
        self.canvas = tk.Canvas(self.root, width=500, height=400, bg="#8D00B1")
        self.canvas.pack(pady=10)
        
        # Подсказки
        guide_text = ''
        if self.is_host:
            guide_text = 'Вы - Хост (синий)\n'
        else:
            guide_text = 'Вы - Клиент (красный)\n'
        guide_text += '←/→ - выбор столбца\nEnter - сделать ход\nESC - выход'
        
        self.guide_label = tk.Label(
            self.root,
            text=guide_text,
            bg=global_bg,
            font=('Roboto', 12),
            anchor='w',
            justify=tk.LEFT
        )
        self.guide_label.pack(anchor='w', padx=20, pady=5)
    
    # ... остальные методы (draw_board, draw_preview, animate_falling) ...
    # Они такие же как в обычной игре
    
    def button_click(self, column):
        """Обработчик хода"""
        if (self.game_over or self.is_animating or 
            self.current_player != self.player_number):
            return
        
        # Делаем локальный ход
        target_row = self.make_move(column, self.player_number)
        
        if target_row == -1:
            messagebox.showwarning('НЕВОЗМОЖНЫЙ ХОД', 'Столбец заполнен')
            return
        
        # Анимируем
        self.status_label.config(text="Фишка падает...", fg="gray")
        self.animate_falling(column, target_row, self.player_number)
        
        # Отправляем ход другому игроку
        if self.socket:
            try:
                self.socket.send(f"MOVE|{column}".encode())
            except:
                messagebox.showerror("Ошибка", "Потеряно соединение")
    
    def make_move(self, column, player):
        """Делает ход на локальной доске"""
        for row in range(6):
            if self.board[row][column] == 0:
                self.board[row][column] = player
                return row
        return -1
    
    def start_server(self):
        """Запускает сервер"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', self.port))
        server_socket.listen(1)
        
        # Обновляем статус в GUI потоке
        self.root.after(0, lambda: self.status_label.config(
            text=f"Ожидание подключения игрока 2...",
            fg="blue"
        ))
        
        # Принимаем подключение
        conn, addr = server_socket.accept()
        self.socket = conn
        
        # Обновляем статус
        self.root.after(0, lambda: self.status_label.config(
            text=f"Игрок 2 подключен! Ходит игрок 1",
            fg="blue"
        ))
        
        # Запускаем прием сообщений
        threading.Thread(target=self.receive_messages, daemon=True).start()
    
    def connect_to_server(self):
        """Подключается к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host_ip, self.port))
            
            # Обновляем статус
            self.status_label.config(
                text="Подключено! Ожидание хода игрока 1",
                fg="red"
            )
            
            # Запускаем прием сообщений
            threading.Thread(target=self.receive_messages, daemon=True).start()
            return True
            
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def receive_messages(self):
        """Принимает сообщения от другого игрока"""
        while True:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                    
                self.process_network_message(data)
                    
            except Exception as e:
                print(f"Ошибка приема: {e}")
                break
        
        # Если соединение разорвано
        self.root.after(0, lambda: messagebox.showerror(
            "Ошибка", "Соединение потеряно"
        ))
    
    def process_network_message(self, data):
        """Обрабатывает сетевое сообщение"""
        if data.startswith("MOVE|"):
            # Получили ход от другого игрока
            _, column = data.split("|")
            column = int(column)
            
            # Определяем номер игрока
            other_player = 1 if self.player_number == 2 else 2
            
            # Делаем ход на нашей доске
            self.root.after(0, lambda: self.process_opponent_move(column, other_player))
            
        elif data.startswith("CHAT|"):
            # Чат сообщение
            _, message = data.split("|", 1)
            print(f"Чат: {message}")
    
    def process_opponent_move(self, column, player):
        """Обрабатывает ход противника"""
        target_row = self.make_move(column, player)
        
        if target_row != -1:
            self.status_label.config(text="Ход противника...", fg="gray")
            self.animate_falling(column, target_row, player)
    
    def check_after_animation(self, column, target_row, player):
        """Проверяет результат после хода"""
        if check_win(self.board, column, target_row, player):
            self.game_over = True
            winner = "Вы" if player == self.player_number else "Противник"
            messagebox.showinfo('ПОБЕДА', f'Победил {winner}!')
            
            color = "green" if player == self.player_number else "red"
            self.status_label.config(
                text=f'Победил {winner}!',
                fg=color
            )
            self.show_reset_button()
            return
        
        if check_draw(self.board):
            self.game_over = True
            messagebox.showinfo('НИЧЬЯ', 'Ничья! Ходов не осталось')
            self.status_label.config(text='Ничья!', fg="orange")
            self.show_reset_button()
            return
        
        # Меняем текущего игрока
        self.current_player = 2 if self.current_player == 1 else 1
        
        # Обновляем статус
        if self.current_player == self.player_number:
            self.status_label.config(
                text=f'Ваш ход ({"синий" if self.player_number == 1 else "красный"})',
                fg="blue" if self.player_number == 1 else "red"
            )
            self.draw_preview()
        else:
            self.status_label.config(
                text=f'Ход противника...',
                fg="gray"
            )
    
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


if __name__ == "__main__":
    game = ConnectFourOnline()
    game.root.mainloop()