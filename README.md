# STM32 Tic-Tac-Toe firmware

Application-level STM32F051 HAL C modules, matched to the root `README.md` protocol and existing GUI. See `CUBEIDE_SETUP.md` for integration and board configuration.

## Verification
- Host game/protocol: `gcc -std=c11 -Wall -Wextra -Werror game.c protocol.c test_host.c -o test_host && ./test_host`
- Real STM32 UART: `python test_serial.py COM5` (replace COM5 with actual port; requires pyserial)

Hardware has not been tested or flashed in this environment. The uploaded ZIP contains no `.ioc` or firmware base, so generate the CubeIDE project for your exact board before integrating.
