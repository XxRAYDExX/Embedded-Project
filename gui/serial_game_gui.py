import tkinter as tk
from tkinter import ttk

from mock_server import MockGameServer




class TicTacToeGUI:
    """Tkinter GUI using a mock server; no real UART connection yet."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Serial Game Server — Tic-Tac-Toe")
        self.root.resizable(False, False)

        self.server = MockGameServer()
        self.connected = False
        self.game_active = False
        self.current_turn = "X"
        self.board = "........."
        self.buttons = []

        main = ttk.Frame(root, padding=16)
        main.grid(row=0, column=0, sticky="nsew")

        ttk.Label(
            main, text="Serial Game Server",
            font=("Segoe UI", 18, "bold")
        ).grid(row=0, column=0, columnspan=3, pady=(0, 4))

        ttk.Label(
            main, text="Tic-Tac-Toe (simulated server)",
            font=("Segoe UI", 10)
        ).grid(row=1, column=0, columnspan=3, pady=(0, 12))

        board_frame = ttk.Frame(main, padding=4)
        board_frame.grid(row=2, column=0, columnspan=3)

        for index in range(9):
            button = ttk.Button(
                board_frame,
                text=" ",
                width=6,
                command=lambda i=index: self.on_cell_clicked(i),
            )
            button.grid(
                row=index // 3,
                column=index % 3,
                padx=3, pady=3,
                ipadx=8, ipady=12,
                sticky="nsew",
            )
            self.buttons.append(button)

        self.status_var = tk.StringVar(value="Not connected")
        ttk.Label(
            main, textvariable=self.status_var,
            anchor="center", font=("Segoe UI", 10, "bold")
        ).grid(row=3, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        self.message_var = tk.StringVar(value="Click Connect to begin.")
        ttk.Label(
            main, textvariable=self.message_var,
            anchor="center", wraplength=310
        ).grid(row=4, column=0, columnspan=3, sticky="ew", pady=(4, 0))

        controls = ttk.Frame(main)
        controls.grid(row=5, column=0, columnspan=3, pady=(14, 0), sticky="ew")

        self.connect_button = ttk.Button(
            controls, text="Connect", command=self.connect
        )
        self.connect_button.grid(row=0, column=0, padx=3)

        self.new_game_button = ttk.Button(
            controls, text="New Game", command=self.new_game, state="disabled"
        )
        self.new_game_button.grid(row=0, column=1, padx=3)

        self.disconnect_button = ttk.Button(
            controls, text="Disconnect", command=self.disconnect, state="disabled"
        )
        self.disconnect_button.grid(row=0, column=2, padx=3)

        self.refresh_board(".........")

    def handle_response(self, response: str) -> None:
        """Update the GUI from a simulated server response."""
        if response == "OK":
            self.message_var.set("Connected to the simulated server.")
            return

        if response.startswith("OK:BOARD:"):
            board = response[len("OK:BOARD:"):]
            self.refresh_board(board)
            self.game_active = True
            self.current_turn = self.next_turn_from_board(board)
            self.status_var.set(f"Game in progress — {self.current_turn}'s turn")
            self.message_var.set("Move accepted by the simulated server.")
            self.update_controls()
            return

        if response.startswith("BOARD:"):
            board = response[len("BOARD:"):]
            self.refresh_board(board)
            self.message_var.set("Current board received from the server.")
            return

        if response.startswith("WIN:"):
            parts = response.split(":")
            if len(parts) == 3:
                player, board = parts[1], parts[2]
                self.refresh_board(board)
                self.game_active = False
                self.status_var.set(f"Game over — {player} wins!")
                self.message_var.set(f"WIN:{player} received from the simulated server.")
                self.update_controls()
            return

        if response.startswith("DRAW:"):
            board = response[len("DRAW:"):]
            self.refresh_board(board)
            self.game_active = False
            self.status_var.set("Game over — draw!")
            self.message_var.set("DRAW received from the simulated server.")
            self.update_controls()
            return

        if response == "OK:GAMEOVER":
            self.game_active = False
            self.status_var.set("Game over — resigned")
            self.message_var.set("The game has ended.")
            self.update_controls()
            return

        if response.startswith("NACK:"):
            messages = {
                "NACK:BADCMD": "Server rejected the command format.",
                "NACK:TIMEOUT": "Server discarded an incomplete command.",
                "NACK:NOGAME": "There is no active game.",
                "NACK:BADSTATE": "That command is not allowed in this state.",
                "NACK:RANGE": "Choose a cell numbered 0–8.",
                "NACK:OCCUPIED": "That cell is already occupied.",
                "NACK:NOTURN": "It is not that player's turn.",
            }
            self.message_var.set(messages.get(response, f"Server error: {response}"))
            return

        self.message_var.set(f"Unexpected server response: {response}")

    @staticmethod
    def next_turn_from_board(board: str) -> str:
        # In a continuing game, the counts tell us whose turn follows.
        # This is display logic for the mock; the real server remains authoritative.
        return "X" if board.count("X") == board.count("O") else "O"

    def refresh_board(self, board: str) -> None:
        if len(board) != 9 or any(char not in ".XO" for char in board):
            self.message_var.set("Invalid board received; display was not updated.")
            return

        self.board = board
        for index, value in enumerate(board):
            self.buttons[index].configure(text="" if value == "." else value)

        can_play = self.connected and self.game_active
        for index, button in enumerate(self.buttons):
            available = can_play and board[index] == "."
            button.configure(state="normal" if available else "disabled")

    def update_controls(self) -> None:
        self.connect_button.configure(
            state="disabled" if self.connected else "normal"
        )
        self.new_game_button.configure(
            state="normal" if self.connected and not self.game_active else "disabled"
        )
        self.disconnect_button.configure(
            state="normal" if self.connected and not self.game_active else "disabled"
        )
        can_play = self.connected and self.game_active
        for index, button in enumerate(self.buttons):
            available = can_play and self.board[index] == "."
            button.configure(state="normal" if available else "disabled")

    def connect(self) -> None:
        response = self.server.send_command("CONNECT")
        if response == "OK":
            self.connected = True
            self.status_var.set("Connected — no active game")
            self.handle_response(response)
        else:
            self.handle_response(response)
        self.update_controls()

    def new_game(self) -> None:
        response = self.server.send_command("NEW")
        self.handle_response(response)

    def on_cell_clicked(self, index: int) -> None:
        if not self.connected or not self.game_active:
            return

        # The mock server is used to simulate a round-trip request/response.
        # In the real system, the client should track confirmed server state.
        command = f"MOVE:{index}:{self.current_turn}"
        response = self.server.send_command(command)
        self.handle_response(response)

    def disconnect(self) -> None:
        response = self.server.send_command("DISCONNECT")
        self.handle_response(response)
        if response == "OK":
            self.connected = False
            self.game_active = False
            self.refresh_board(".........")
            self.status_var.set("Not connected")
            self.message_var.set("Disconnected from the simulated server.")
            self.update_controls()


def main() -> None:
    root = tk.Tk()
    TicTacToeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()