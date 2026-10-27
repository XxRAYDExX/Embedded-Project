# STM32F051 CubeIDE setup (hardware-specific steps)

**The uploaded repository had no `.ioc`, `main.c`, board schematic, or existing firmware.** These files are application modules, not a compiled `.elf`/`.bin` or a complete generated CubeIDE project.

1. In STM32CubeIDE, create a new STM32 project for the **exact MCU** printed on your UCT STM32F051 board. Use HAL and enable the ST-LINK debug interface.
2. Inspect the board schematic to determine which UART is connected to the ST-LINK virtual COM port. Some ST-LINK versions do **not** provide a VCP connection; use a USB-UART adapter if needed. Configure that UART as **115200, 8 data bits, no parity, 1 stop bit**, asynchronous, with RX interrupts enabled. Enable its global interrupt in NVIC. Confirm TX/RX alternate functions and shared ground.
3. Configure the on-board LED as GPIO output and the button as GPIO input with appropriate pull resistor. In a `/* USER CODE BEGIN Includes */` region in `main.c`, add:

   ```c
   #include "serial_server.h"
   #include "hardware_app.h"
   ```
4. Copy all `.c` files except `test_host.c` into `Core/Src` and all `.h` files into `Core/Inc`. In `/* USER CODE BEGIN 2 */` after `MX_USARTx_UART_Init()` and `MX_GPIO_Init()`, add:

   ```c
   server_init(&huartX);  /* replace X with actual configured UART */
   hardware_app_init();
   ```
5. Inside `while (1)` in `/* USER CODE BEGIN 3 */`, call:

   ```c
   server_poll();
   hardware_app_poll();
   ```

   Avoid long blocking delays in this loop.
6. Map the **real** pins in `main.h` (or a board-specific header included by `hardware_app.c`):

   ```c
   #define BOARD_LED_GPIO_Port GPIOx
   #define BOARD_LED_Pin GPIO_PIN_y
   #define BOARD_LED_ACTIVE_HIGH 1
   #define BOARD_BUTTON_GPIO_Port GPIOx
   #define BOARD_BUTTON_Pin GPIO_PIN_z
   #define BOARD_BUTTON_PRESSED GPIO_PIN_RESET
   ```

   Replace x/y/z with the actual pin definitions. If these macros are omitted, the firmware builds with LED/button support disabled. This is **not** sufficient for the assignment until configured.
7. Ensure `stm32f0xx_it.c` calls `HAL_UART_IRQHandler(&huartX)` from the configured USART IRQ handler (CubeMX normally generates this). Do not define a second `HAL_UART_RxCpltCallback` elsewhere.
8. Build and flash. Open the PC COM port at 115200 baud, send `CONNECT\n` and verify `OK\n`, then `NEW\n` and `OK:BOARD:.........\n`. Close the serial terminal before launching the Python GUI.
9. Run the supplied `test_serial.py` against the COM port for real-board validation.

**Notes:** The serial receive ISR buffers bytes, and the main loop processes complete lines. Sending replies uses HAL blocking transmit with a bounded timeout. Reset is an unsolicited `EVT:RESET` event and the GUI may need to handle it. The Python GUI and mock server were left unchanged.
