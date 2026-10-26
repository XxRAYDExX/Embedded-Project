"""Python mock of the STM32 authoritative Tic-Tac-Toe server.

This is for GUI development only. It simulates the serial protocol in memory;
it does not communicate with the STM32 over UART.
"""

class MockGameServer:
    """
    Temporary Python simulation of the STM32 server.
    Replace this class with UART communication after the GUI is working.
    """

    WIN_LINES = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    )

    def __init__(self):
        self.connected = False
        self.state = "IDLE"
        self.board = ["."] * 9
        self.current_turn = "X"

    def send_command(self, command: str) -> str:
        """Accept one protocol command and return one simulated response."""
        if command == "CONNECT":
            self.connected = True
            return "OK"

        if not self.connected:
            return "NACK:BADCMD"

        if command == "DISCONNECT":
            if self.state == "IN_PROGRESS":
                return "NACK:BADSTATE"
            self.connected = False
            self.state = "IDLE"
            return "OK"

        if command == "NEW":
            if self.state == "IN_PROGRESS":
                return "NACK:BADSTATE"
            self.board = ["."] * 9
            self.current_turn = "X"
            self.state = "IN_PROGRESS"
            return f"OK:BOARD:{self.board_string()}"

        if command == "STATE":
            if self.state == "IDLE":
                return "NACK:NOGAME"
            return f"BOARD:{self.board_string()}"

        if command == "RESIGN":
            if self.state != "IN_PROGRESS":
                return "NACK:NOGAME"
            self.state = "GAME_OVER"
            return "OK:GAMEOVER"

        if command.startswith("MOVE:"):
            if self.state != "IN_PROGRESS":
                return "NACK:NOGAME"

            parts = command.split(":")
            if len(parts) != 3 or parts[0] != "MOVE" or parts[2] not in ("X", "O"):
                return "NACK:BADCMD"

            try:
                index = int(parts[1])
            except ValueError:
                return "NACK:BADCMD"

            player = parts[2]

            if not 0 <= index <= 8:
                return "NACK:RANGE"
            if self.board[index] != ".":
                return "NACK:OCCUPIED"
            if player != self.current_turn:
                return "NACK:NOTURN"

            self.board[index] = player
            board = self.board_string()

            if self.has_won(player):
                self.state = "GAME_OVER"
                return f"WIN:{player}:{board}"

            if "." not in self.board:
                self.state = "GAME_OVER"
                return f"DRAW:{board}"

            self.current_turn = "O" if player == "X" else "X"
            return f"OK:BOARD:{board}"

        return "NACK:BADCMD"

    def board_string(self) -> str:
        return "".join(self.board)

    def has_won(self, player: str) -> bool:
        return any(
            all(self.board[index] == player for index in line)
            for line in self.WIN_LINES
        )

