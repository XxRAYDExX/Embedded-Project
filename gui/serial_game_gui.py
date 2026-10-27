import tkinter as tk
from tkinter import ttk

from serial_client import SerialGameClient


POLL_INTERVAL_MS = 200


class TicTacToeGUI:
    """GUI for the STM32 Serial Tic-Tac-Toe server."""

    BG = "#111827"
    PANEL = "#1f2937"
    PANEL_LIGHT = "#273449"

    TEXT = "#f9fafb"
    MUTED = "#9ca3af"

    ACCENT = "#3b82f6"
    ACCENT_HOVER = "#2563eb"

    X_COLOR = "#60a5fa"
    O_COLOR = "#f87171"

    SUCCESS = "#34d399"
    WARNING = "#fbbf24"
    ERROR = "#f87171"

    CELL_BG = "#374151"
    CELL_HOVER = "#4b5563"

    CELL_SIZE = 130
    SYMBOL_MARGIN = 15
    SYMBOL_WIDTH = 11

    def __init__(self, root: tk.Tk):
        self.root = root

        self.root.title(
            "STM32 Serial Game Server — Tic-Tac-Toe"
        )

        self.root.configure(
            bg=self.BG
        )

        self.root.resizable(
            False,
            False
        )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self.server = None

        self.connected = False
        self.game_active = False

        self.current_turn = "X"

        self.board = "........."

        self.cells = []

        self.create_styles()
        self.create_interface()

        self.refresh_board(
            "........."
        )

        self.update_controls()

    # ==================================================
    # STYLES
    # ==================================================

    def create_styles(self):
        style = ttk.Style()

        try:
            style.theme_use(
                "clam"
            )
        except tk.TclError:
            pass

        style.configure(
            "Main.TFrame",
            background=self.BG
        )

        style.configure(
            "Panel.TFrame",
            background=self.PANEL
        )

        style.configure(
            "Title.TLabel",
            background=self.BG,
            foreground=self.TEXT,
            font=(
                "Segoe UI",
                22,
                "bold"
            )
        )

        style.configure(
            "Subtitle.TLabel",
            background=self.BG,
            foreground=self.MUTED,
            font=(
                "Segoe UI",
                10
            )
        )

        style.configure(
            "PanelTitle.TLabel",
            background=self.PANEL,
            foreground=self.TEXT,
            font=(
                "Segoe UI",
                11,
                "bold"
            )
        )

        style.configure(
            "Status.TLabel",
            background=self.PANEL,
            foreground=self.TEXT,
            font=(
                "Segoe UI",
                11,
                "bold"
            )
        )

        style.configure(
            "Message.TLabel",
            background=self.PANEL,
            foreground=self.MUTED,
            font=(
                "Segoe UI",
                9
            )
        )

        style.configure(
            "Normal.TButton",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            padding=8
        )

        style.configure(
            "Primary.TButton",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            padding=8,
            background=self.ACCENT,
            foreground="white"
        )

        style.map(
            "Primary.TButton",
            background=[
                (
                    "active",
                    self.ACCENT_HOVER
                ),
                (
                    "disabled",
                    "#374151"
                )
            ],
            foreground=[
                (
                    "disabled",
                    "#6b7280"
                )
            ]
        )

        style.configure(
            "Port.TEntry",
            fieldbackground=self.PANEL_LIGHT,
            foreground=self.TEXT,
            insertcolor=self.TEXT,
            padding=6
        )

    # ==================================================
    # INTERFACE
    # ==================================================

    def create_interface(self):
        outer = ttk.Frame(
            self.root,
            style="Main.TFrame",
            padding=22
        )

        outer.grid(
            row=0,
            column=0
        )

        # ==================================================
        # HEADER
        # ==================================================

        header = ttk.Frame(
            outer,
            style="Main.TFrame"
        )

        header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 16)
        )

        ttk.Label(
            header,
            text="Serial Game Server",
            style="Title.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Label(
            header,
            text="STM32F051 • UART • Tic-Tac-Toe",
            style="Subtitle.TLabel"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 0)
        )

        # ==================================================
        # LEFT SIDE - GAME
        # ==================================================

        game_panel = ttk.Frame(
            outer,
            style="Panel.TFrame",
            padding=18
        )

        game_panel.grid(
            row=1,
            column=0,
            sticky="n",
            padx=(0, 12)
        )

        game_header = ttk.Frame(
            game_panel,
            style="Panel.TFrame"
        )

        game_header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 14)
        )

        ttk.Label(
            game_header,
            text="Game Board",
            style="PanelTitle.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.turn_label = tk.Label(
            game_header,
            text="NO GAME",
            bg=self.PANEL_LIGHT,
            fg=self.MUTED,
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            padx=10,
            pady=4
        )

        self.turn_label.grid(
            row=0,
            column=1,
            padx=(35, 0)
        )

        # ==================================================
        # PERFECT-SQUARE TIC-TAC-TOE BOARD
        # ==================================================

        board_frame = tk.Frame(
            game_panel,
            bg=self.PANEL
        )

        board_frame.grid(
            row=1,
            column=0
        )

        for index in range(9):
            cell = tk.Canvas(
                board_frame,
                width=self.CELL_SIZE,
                height=self.CELL_SIZE,
                bg=self.CELL_BG,
                highlightthickness=0,
                bd=0,
                cursor="arrow"
            )

            cell.grid(
                row=index // 3,
                column=index % 3,
                padx=4,
                pady=4
            )

            cell.bind(
                "<Button-1>",
                lambda event, i=index:
                    self.on_cell_clicked(i)
            )

            cell.bind(
                "<Enter>",
                lambda event, i=index:
                    self.on_cell_enter(i)
            )

            cell.bind(
                "<Leave>",
                lambda event, i=index:
                    self.on_cell_leave(i)
            )

            self.cells.append(
                cell
            )

        # ==================================================
        # RIGHT SIDE
        # ==================================================

        right_column = ttk.Frame(
            outer,
            style="Main.TFrame"
        )

        right_column.grid(
            row=1,
            column=1,
            sticky="ns"
        )

        # ==================================================
        # CONNECTION
        # ==================================================

        connection_panel = ttk.Frame(
            right_column,
            style="Panel.TFrame",
            padding=16
        )

        connection_panel.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        ttk.Label(
            connection_panel,
            text="Connection",
            style="PanelTitle.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.connection_indicator = tk.Label(
            connection_panel,
            text="● DISCONNECTED",
            bg=self.PANEL,
            fg=self.ERROR,
            font=(
                "Segoe UI",
                9,
                "bold"
            )
        )

        self.connection_indicator.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(8, 12)
        )

        ttk.Label(
            connection_panel,
            text="Serial Port",
            style="Message.TLabel"
        ).grid(
            row=2,
            column=0,
            sticky="w"
        )

        self.port_var = tk.StringVar(
            value="COM6"
        )

        self.port_entry = ttk.Entry(
            connection_panel,
            textvariable=self.port_var,
            width=20,
            style="Port.TEntry"
        )

        self.port_entry.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(5, 0)
        )

        # ==================================================
        # STATUS
        # ==================================================

        status_panel = ttk.Frame(
            right_column,
            style="Panel.TFrame",
            padding=16
        )

        status_panel.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(12, 0)
        )

        ttk.Label(
            status_panel,
            text="Game Status",
            style="PanelTitle.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.status_var = tk.StringVar(
            value="Not connected"
        )

        ttk.Label(
            status_panel,
            textvariable=self.status_var,
            style="Status.TLabel",
            wraplength=220
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(10, 0)
        )

        self.message_var = tk.StringVar(
            value="Connect to the STM32 to begin."
        )

        ttk.Label(
            status_panel,
            textvariable=self.message_var,
            style="Message.TLabel",
            wraplength=220
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=(7, 0)
        )

        # ==================================================
        # CONTROLS
        # ==================================================

        controls_panel = ttk.Frame(
            right_column,
            style="Panel.TFrame",
            padding=16
        )

        controls_panel.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(12, 0)
        )

        ttk.Label(
            controls_panel,
            text="Controls",
            style="PanelTitle.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 10)
        )

        self.connect_button = ttk.Button(
            controls_panel,
            text="Connect",
            command=self.connect,
            style="Primary.TButton"
        )

        self.connect_button.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=3
        )

        self.new_game_button = ttk.Button(
            controls_panel,
            text="New Game",
            command=self.new_game,
            style="Normal.TButton"
        )

        self.new_game_button.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=3
        )

        self.disconnect_button = ttk.Button(
            controls_panel,
            text="Disconnect",
            command=self.disconnect,
            style="Normal.TButton"
        )

        self.disconnect_button.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=3
        )

    # ==================================================
    # DRAWING X AND O
    # ==================================================

    def draw_cell(self, index):
        cell = self.cells[index]

        cell.delete(
            "all"
        )

        value = self.board[index]

        margin = self.SYMBOL_MARGIN

        size = self.CELL_SIZE

        if value == "X":
            cell.create_line(
                margin,
                margin,
                size - margin,
                size - margin,
                fill=self.X_COLOR,
                width=self.SYMBOL_WIDTH,
                capstyle=tk.ROUND
            )

            cell.create_line(
                size - margin,
                margin,
                margin,
                size - margin,
                fill=self.X_COLOR,
                width=self.SYMBOL_WIDTH,
                capstyle=tk.ROUND
            )

        elif value == "O":
            cell.create_oval(
                margin,
                margin,
                size - margin,
                size - margin,
                outline=self.O_COLOR,
                width=self.SYMBOL_WIDTH
            )

    def redraw_board(self):
        for index in range(9):
            self.draw_cell(
                index
            )

    # ==================================================
    # HOVER EFFECT
    # ==================================================

    def cell_available(self, index):
        return (
            self.connected
            and self.game_active
            and self.board[index] == "."
        )

    def on_cell_enter(self, index):
        if self.cell_available(index):
            self.cells[index].configure(
                bg=self.CELL_HOVER,
                cursor="hand2"
            )

    def on_cell_leave(self, index):
        self.cells[index].configure(
            bg=self.CELL_BG
        )

        if self.cell_available(index):
            self.cells[index].configure(
                cursor="hand2"
            )
        else:
            self.cells[index].configure(
                cursor="arrow"
            )

    # ==================================================
    # SERVER RESPONSES
    # ==================================================

    def handle_response(
        self,
        response: str
    ) -> None:

        if response is None:
            return

        if response == "OK":
            self.message_var.set(
                "Connected successfully to the STM32."
            )
            return

        if response.startswith(
            "OK:BOARD:"
        ):
            board = response[
                len("OK:BOARD:"):
            ]

            self.game_active = True

            self.refresh_board(
                board
            )

            self.current_turn = (
                self.next_turn_from_board(
                    board
                )
            )

            self.update_game_display()

            self.message_var.set(
                "Move accepted by STM32."
            )

            self.update_controls()

            return

        if response.startswith(
            "BOARD:"
        ):
            board = response[
                len("BOARD:"):
            ]

            self.refresh_board(
                board
            )

            self.current_turn = (
                self.next_turn_from_board(
                    board
                )
            )

            self.update_game_display()

            return

        if response.startswith(
            "WIN:"
        ):
            parts = response.split(
                ":"
            )

            if len(parts) == 3:
                player = parts[1]
                board = parts[2]

                self.game_active = False

                self.refresh_board(
                    board
                )

                self.status_var.set(
                    f"Game Over — {player} wins"
                )

                self.turn_label.configure(
                    text=f"{player} WINS",
                    fg=self.SUCCESS
                )

                self.message_var.set(
                    f"{player} has won the game. "
                    "Result confirmed by STM32."
                )

                self.update_controls()

            return

        if response.startswith(
            "DRAW:"
        ):
            board = response[
                len("DRAW:"):
            ]

            self.game_active = False

            self.refresh_board(
                board
            )

            self.status_var.set(
                "Game Over — Draw"
            )

            self.turn_label.configure(
                text="DRAW",
                fg=self.WARNING
            )

            self.message_var.set(
                "The STM32 confirmed a draw."
            )

            self.update_controls()

            return

        if response == "OK:GAMEOVER":
            self.game_active = False

            self.status_var.set(
                "Game Over — Resigned"
            )

            self.turn_label.configure(
                text="GAME OVER",
                fg=self.WARNING
            )

            self.message_var.set(
                "The game has ended."
            )

            self.update_controls()

            return

        if response.startswith(
            "NACK:"
        ):
            messages = {
                "NACK:BADCMD":
                    "Invalid command.",

                "NACK:TIMEOUT":
                    "Incomplete command timed out.",

                "NACK:NOGAME":
                    "There is no active game.",

                "NACK:BADSTATE":
                    "That action is not allowed right now.",

                "NACK:RANGE":
                    "That cell is outside the board.",

                "NACK:OCCUPIED":
                    "That cell is already occupied.",

                "NACK:NOTURN":
                    "It is not that player's turn."
            }

            self.message_var.set(
                messages.get(
                    response,
                    response
                )
            )

            return

        self.message_var.set(
            f"Unexpected STM32 response: {response}"
        )

    # ==================================================
    # BOARD
    # ==================================================

    @staticmethod
    def next_turn_from_board(
        board: str
    ) -> str:

        if (
            board.count("X")
            ==
            board.count("O")
        ):
            return "X"

        return "O"

    def refresh_board(
        self,
        board: str
    ) -> None:

        if (
            len(board) != 9
            or any(
                char not in ".XO"
                for char in board
            )
        ):
            self.message_var.set(
                "Invalid board received."
            )

            return

        self.board = board

        self.redraw_board()

        self.update_controls()

    def update_game_display(self):
        if not self.game_active:
            return

        self.status_var.set(
            f"Game in progress — "
            f"{self.current_turn}'s turn"
        )

        if self.current_turn == "X":
            self.turn_label.configure(
                text="X TURN",
                fg=self.X_COLOR
            )

        else:
            self.turn_label.configure(
                text="O TURN",
                fg=self.O_COLOR
            )

    # ==================================================
    # CONTROLS
    # ==================================================

    def update_controls(self):
        self.connect_button.configure(
            state=(
                "disabled"
                if self.connected
                else "normal"
            )
        )

        self.port_entry.configure(
            state=(
                "disabled"
                if self.connected
                else "normal"
            )
        )

        self.new_game_button.configure(
            state=(
                "normal"
                if (
                    self.connected
                    and
                    not self.game_active
                )
                else "disabled"
            )
        )

        self.disconnect_button.configure(
            state=(
                "normal"
                if (
                    self.connected
                    and
                    not self.game_active
                )
                else "disabled"
            )
        )

        for index, cell in enumerate(
            self.cells
        ):
            if self.cell_available(index):
                cell.configure(
                    cursor="hand2"
                )
            else:
                cell.configure(
                    cursor="arrow",
                    bg=self.CELL_BG
                )

    # ==================================================
    # CONNECT
    # ==================================================

    def connect(self):
        try:
            self.server = SerialGameClient(
                self.port_var.get().strip()
            )

            self.server.open()

        except ConnectionError as error:
            self.server = None

            self.message_var.set(
                str(error)
            )

            return

        response = self.send(
            "CONNECT"
        )

        if response == "OK":
            self.connected = True

            self.connection_indicator.configure(
                text="● CONNECTED",
                fg=self.SUCCESS
            )

            self.status_var.set(
                "Connected — Ready"
            )

            self.turn_label.configure(
                text="READY",
                fg=self.SUCCESS
            )

            self.handle_response(
                response
            )

            self.update_controls()

            self.root.after(
                POLL_INTERVAL_MS,
                self.poll_hardware_event
            )

        else:
            self.handle_response(
                response
            )

            self.server.close()

            self.server = None

            self.update_controls()

    # ==================================================
    # HARDWARE RESET POLLING
    # ==================================================

    def poll_hardware_event(self):
        if (
            not self.connected
            or self.server is None
        ):
            return

        response = self.send(
            "POLL"
        )

        if response is None:
            if self.connected:
                self.root.after(
                    POLL_INTERVAL_MS,
                    self.poll_hardware_event
                )

            return

        if response.startswith(
            "EVENT:RESET:"
        ):
            board = response[
                len("EVENT:RESET:"):
            ]

            self.game_active = True

            self.current_turn = "X"

            self.refresh_board(
                board
            )

            self.status_var.set(
                "Game reset — X's turn"
            )

            self.turn_label.configure(
                text="X TURN",
                fg=self.X_COLOR
            )

            self.message_var.set(
                "Physical STM32 button pressed — "
                "game reset successfully."
            )

            self.update_controls()

        elif response != "EVENT:NONE":
            self.handle_response(
                response
            )

        if self.connected:
            self.root.after(
                POLL_INTERVAL_MS,
                self.poll_hardware_event
            )

    # ==================================================
    # GAME COMMANDS
    # ==================================================

    def new_game(self):
        response = self.send(
            "NEW"
        )

        self.handle_response(
            response
        )

    def on_cell_clicked(
        self,
        index: int
    ):
        if not self.cell_available(
            index
        ):
            return

        command = (
            f"MOVE:{index}:"
            f"{self.current_turn}"
        )

        response = self.send(
            command
        )

        self.handle_response(
            response
        )

    # ==================================================
    # DISCONNECT
    # ==================================================

    def disconnect(self):
        response = self.send(
            "DISCONNECT"
        )

        self.handle_response(
            response
        )

        if response == "OK":
            self.server.close()

            self.server = None

            self.connected = False
            self.game_active = False
            self.current_turn = "X"

            self.refresh_board(
                "........."
            )

            self.connection_indicator.configure(
                text="● DISCONNECTED",
                fg=self.ERROR
            )

            self.status_var.set(
                "Not connected"
            )

            self.turn_label.configure(
                text="NO GAME",
                fg=self.MUTED
            )

            self.message_var.set(
                "Disconnected from STM32."
            )

            self.update_controls()

    # ==================================================
    # UART
    # ==================================================

    def send(
        self,
        command
    ):
        try:
            return self.server.send_command(
                command
            )

        except (
            ConnectionError,
            TimeoutError,
            ValueError,
            RuntimeError
        ) as error:
            self.message_var.set(
                f"Serial link error: {error}"
            )

            return None

    # ==================================================
    # WINDOW CLOSE
    # ==================================================

    def on_close(self):
        if self.server is not None:
            try:
                if self.connected:

                    if self.game_active:
                        try:
                            self.server.send_command(
                                "RESIGN"
                            )
                        except Exception:
                            pass

                    try:
                        self.server.send_command(
                            "DISCONNECT"
                        )
                    except Exception:
                        pass

                self.server.close()

            except Exception:
                pass

        self.root.destroy()


def main():
    root = tk.Tk()

    TicTacToeGUI(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()