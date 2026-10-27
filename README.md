# STM32 Serial Tic-Tac-Toe Game Server

An embedded Tic-Tac-Toe game implemented for the **EEE3095S Serial Game Server** project.

The **STM32F051** microcontroller is the game server: it stores the board, controls turns, validates moves, and detects wins and draws. A **Python/Tkinter** desktop GUI sends commands over a USB serial connection and displays only the board state confirmed by the STM32.

## Requirements

### Hardware
- UCT STM32F051 development board with on-board **ST-Link Virtual COM Port**
- USB cable suitable for the board's ST-Link connection
- Windows PC (the instructions below use Windows COM ports)

### Software
- **STM32CubeIDE** (to build and flash the firmware)
- **Python 3** (to run the desktop GUI and tests)
- **pySerial** Python package
- **Tkinter** (normally included with the standard Python installer on Windows)

No separate USB-to-UART adapter is needed when using the board's on-board ST-Link Virtual COM Port.

## Project Files

Locate the following files in the repository:

| File | Purpose |
| --- | --- |
| `main.c` (or a source-only export such as `main_with_hardware.c`) | STM32 firmware game server; inside a CubeIDE project it normally belongs in `Core/Src/` |
| STM32CubeIDE project files (`.project`, `.cproject`, `.ioc`), **if included** | Reproducible firmware build and board configuration |
| `serial_game_gui.py` | Desktop Tkinter Tic-Tac-Toe GUI |
| `serial_client.py` | Python serial communication helper |
| `test.py` | Automated firmware and protocol test harness |

**Important:** Keep `serial_game_gui.py` and `serial_client.py` in the same directory, or otherwise ensure Python can import `serial_client`.

## 1. Build and Flash the STM32 Firmware

1. Connect the UCT STM32 development board to your PC using the **ST-Link USB connection**.
2. Open **STM32CubeIDE**.
3. Select **File > Open Projects from File System** (or import an existing STM32CubeIDE project).
4. Choose the folder in this repository that contains the firmware project's `.project` file.
5. Select the imported project in **Project Explorer**.
6. Select **Project > Build Project** (or click the hammer/build icon).
7. Check the build console for a successful build without errors.
8. Use the project's **Debug/Run** configuration to program the STM32 through ST-Link. If CubeIDE starts a debugging session, press **Resume** to let the firmware run.

After flashing, leave the board connected by USB. The STM32 firmware should now be running.

## 2. Install the Python Dependency

Open **PowerShell** or **Command Prompt** in the folder containing `serial_game_gui.py` and `serial_client.py`.

Check that Python is available:

```powershell
python --version
```

Install pySerial:

```powershell
python -m pip install pyserial
```

On Windows, if `python` is not recognized, try `py -3` in place of `python`:

```powershell
py -3 -m pip install pyserial
```

Tkinter comes with most Windows Python installations. You can check it by running:

```powershell
python -m tkinter
```

A small Tkinter test window should appear.

## 3. Find the Board's COM Port

1. Keep the STM32 board connected through its **ST-Link USB** connection.
2. Open **Windows Device Manager**.
3. Expand **Ports (COM & LPT)**.
4. Find the **STMicroelectronics STLink Virtual COM Port** (or similarly named device).
5. Note its port number, such as `COM6`. Your number may be different.

Close other applications using that port, including serial terminals and the STM32CubeIDE serial monitor, before starting the GUI or tests.

## 4. Run the Tic-Tac-Toe GUI

In the directory containing the Python scripts, run:

```powershell
python serial_game_gui.py
```

Then:

1. Enter the board's COM port (for example, `COM6`) in the GUI's **Port** text field.
2. Click **Connect**. The GUI should report a successful connection.
3. Click **New Game** to request a new board from the STM32.
4. Click an empty cell to submit a move. **X plays first**, followed by **O**.
5. Continue until the STM32 reports a win or a draw. The GUI will display the result and disable further moves.
6. Click **New Game** to play another round.

You can click **Disconnect** when no game is in progress. To exit during an active game, close the GUI window; the application attempts to resign and disconnect cleanly before closing the serial port.

**The STM32 is authoritative:** clicking a cell does not directly change the game state. The GUI redraws the board after receiving a valid reply from the microcontroller.

## 5. Test the Hardware Reset Button and LEDs

With the GUI connected:

- **SW0 button (PA0):** press the physical button to reset/start a game on the STM32. The GUI detects the reset on its next `POLL` request and redraws the empty board with X to move.
- **LEDs D0–D7 (PB0–PB7):**
  - All **off** in `IDLE`
  - All **on** during X's turn
  - All **off** during O's turn
  - **Blink together** after the game ends

The GUI polls for hardware reset events approximately every **200 ms** while connected.

## 6. Run the Automated Tests

The test harness communicates **directly with the real STM32 board**; it does not require the GUI.

1. Ensure the firmware is flashed and running.
2. **Close the GUI** and any other application using the board's COM port.
3. In a terminal in the folder containing `test.py`, run:

```powershell
python test.py COM6
```

Replace `COM6` with the port found in Device Manager.

The tests exercise connection handling, legal moves, invalid moves, turn enforcement, wins and draws, and serial-input recovery (including malformed, oversized, and incomplete commands). The final project report records **66/66 checks passed** on the tested firmware version.

The test script uses **pySerial**; it is not necessary to install `pytest` to run this command.

## Serial Communication

| Setting | Value |
| --- | --- |
| Peripheral | STM32 USART1 |
| TX / RX pins | PA9 (TX), PA10 (RX) |
| Connection | On-board ST-Link Virtual COM Port over USB |
| Baud rate | 115200 |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Flow control | None |
| Message framing | ASCII text, newline-terminated |

Examples of the implemented command/response protocol:

```text
PC -> STM32: CONNECT
STM32 -> PC: OK

PC -> STM32: NEW
STM32 -> PC: OK:BOARD:.........

PC -> STM32: MOVE:4:X
STM32 -> PC: OK:BOARD:....X....

PC -> STM32: POLL
STM32 -> PC: EVENT:NONE
```

The STM32 can also return specific rejection messages such as `NACK:RANGE`, `NACK:OCCUPIED`, `NACK:NOTURN`, `NACK:BADSTATE`, and `NACK:NOGAME`. The GUI displays appropriate error messages without changing the confirmed board.