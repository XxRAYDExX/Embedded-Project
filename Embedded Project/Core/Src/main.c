/* USER CODE BEGIN Header */

/**

  ******************************************************************************

  * @file           : main.c

  * @brief          : Main program body

  ******************************************************************************

  * @attention

  *

  * Copyright (c) 2026 STMicroelectronics.

  * All rights reserved.

  *

  * This software is licensed under terms that can be found in the LICENSE file

  * in the root directory of this software component.

  * If no LICENSE file comes with this software, it is provided AS-IS.

  *

  ******************************************************************************

  */

/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/

#include "main.h"

/* Private includes ----------------------------------------------------------*/

/* USER CODE BEGIN Includes */

#include <string.h>

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/

/* USER CODE BEGIN PTD */

typedef enum

{

    SERVER_IDLE,

    SERVER_IN_PROGRESS,

    SERVER_GAME_OVER

} ServerState;

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/

/* USER CODE BEGIN PD */

#define RX_BUFFER_SIZE 64
#define FRAME_TIMEOUT_MS 1000U
#define MAX_MOVES 9U

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/

/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

UART_HandleTypeDef huart1;

/* USER CODE BEGIN PV */

uint8_t rx_byte;

char rx_buffer[RX_BUFFER_SIZE];

uint8_t rx_index = 0;

uint8_t discard_frame = 0;

uint8_t frame_active = 0;

uint32_t last_rx_tick = 0;

uint8_t connected = 0;

uint8_t local_reset_pending = 0;

ServerState server_state = SERVER_IDLE;

char board[9] =

{

    '.', '.', '.',

    '.', '.', '.',

    '.', '.', '.'

};

char current_turn = 'X';

/* Authoritative record of accepted moves, oldest first. */
uint8_t move_indices[MAX_MOVES];
char move_players[MAX_MOVES];
uint8_t move_count = 0;

/* Undo must not revive a game ended through RESIGN. */
uint8_t game_resigned = 0;

uint32_t last_button_time = 0;

uint32_t last_led_toggle = 0;

GPIO_PinState previous_button_state = GPIO_PIN_SET;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/

void SystemClock_Config(void);

static void MX_GPIO_Init(void);

static void MX_USART1_UART_Init(void);

/* USER CODE BEGIN PFP */

static void Send_Response(const char *response);

static void Send_Board_Response(const char *prefix);
static void Send_History_Response(void);

static void Reset_Board(void);

static void Local_New_Game(void);

static void Update_Hardware(void);

static uint8_t Has_Won(char player);

static uint8_t Is_Draw(void);

static uint8_t Parse_Move(

    const char *command,

    int *index,

    char *player,

    uint8_t *has_player

);

static void Process_Command(const char *command);

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/

/* USER CODE BEGIN 0 */

static void Send_Response(const char *response)

{

    HAL_UART_Transmit(

        &huart1,

        (uint8_t *)response,

        strlen(response),

        HAL_MAX_DELAY

    );

}

static void Send_Board_Response(const char *prefix)

{

    char response[32];

    uint8_t prefix_length = (uint8_t)strlen(prefix);

    memcpy(

        response,

        prefix,

        prefix_length

    );

    memcpy(

        response + prefix_length,

        board,

        9

    );

    response[prefix_length + 9] = '\r';

    response[prefix_length + 10] = '\n';

    response[prefix_length + 11] = '\0';

    Send_Response(response);

}

static void Send_History_Response(void)
{
    /* 8-byte prefix + 9 two-character moves + 8 commas + CRLF + NUL. */
    char response[40];
    uint8_t pos = 0;

    if (move_count == 0U)
    {
        Send_Response("HISTORY:EMPTY\r\n");
        return;
    }

    memcpy(response, "HISTORY:", 8);
    pos = 8;

    for (uint8_t i = 0; i < move_count; i++)
    {
        if (i != 0U)
        {
            response[pos++] = ',';
        }
        response[pos++] = move_players[i];
        response[pos++] = (char)('0' + move_indices[i]);
    }

    response[pos++] = '\r';
    response[pos++] = '\n';
    response[pos] = '\0';
    Send_Response(response);
}

static void Reset_Board(void)
{

    for (uint8_t i = 0; i < 9; i++)

    {

        board[i] = '.';

    }

    current_turn = 'X';
    move_count = 0;
    game_resigned = 0;

}

static void Local_New_Game(void)

{

    Reset_Board();

    if (connected)

    {

        server_state = SERVER_IN_PROGRESS;

        local_reset_pending = 1;

    }

    else

    {

        server_state = SERVER_IDLE;

    }

}

static void Update_Hardware(void)

{

    GPIO_PinState button_state;

    uint32_t now = HAL_GetTick();

    uint16_t all_leds =

        GPIO_PIN_0 |

        GPIO_PIN_1 |

        GPIO_PIN_2 |

        GPIO_PIN_3 |

        GPIO_PIN_4 |

        GPIO_PIN_5 |

        GPIO_PIN_6 |

        GPIO_PIN_7;

    /*

     * Read SW0 on PA0.

     *

     * Released = HIGH

     * Pressed  = LOW

     */

    button_state =

        HAL_GPIO_ReadPin(

            GPIOA,

            GPIO_PIN_0

        );

    /*

     * Detect the physical button press.

     */

    if (button_state == GPIO_PIN_RESET &&

        previous_button_state == GPIO_PIN_SET)

    {

        /*

         * Basic debounce protection.

         */

        if ((now - last_button_time) >= 200U)

        {

            Local_New_Game();

            last_button_time = now;

        }

    }

    previous_button_state =

        button_state;

    /*

     * IDLE:

     *

     * All LEDs are OFF.

     */

    if (server_state == SERVER_IDLE)

    {

        HAL_GPIO_WritePin(

            GPIOB,

            all_leds,

            GPIO_PIN_RESET

        );

    }

    /*

     * IN_PROGRESS:

     *

     * X turn = all LEDs ON

     * O turn = all LEDs OFF

     */

    else if (server_state == SERVER_IN_PROGRESS)

    {

        if (current_turn == 'X')

        {

            HAL_GPIO_WritePin(

                GPIOB,

                all_leds,

                GPIO_PIN_SET

            );

        }

        else

        {

            HAL_GPIO_WritePin(

                GPIOB,

                all_leds,

                GPIO_PIN_RESET

            );

        }

    }

    /*

     * GAME_OVER:

     *

     * All LEDs blink together.

     */

    else if (server_state == SERVER_GAME_OVER)

    {

        if ((now - last_led_toggle) >= 300U)

        {

            HAL_GPIO_TogglePin(

                GPIOB,

                all_leds

            );

            last_led_toggle = now;

        }

    }

}

static uint8_t Has_Won(char player)

{

    static const uint8_t win_lines[8][3] =

    {

        {0, 1, 2},

        {3, 4, 5},

        {6, 7, 8},

        {0, 3, 6},

        {1, 4, 7},

        {2, 5, 8},

        {0, 4, 8},

        {2, 4, 6}

    };

    for (uint8_t i = 0; i < 8; i++)

    {

        uint8_t a = win_lines[i][0];

        uint8_t b = win_lines[i][1];

        uint8_t c = win_lines[i][2];

        if (board[a] == player &&

            board[b] == player &&

            board[c] == player)

        {

            return 1;

        }

    }

    return 0;

}

static uint8_t Is_Draw(void)

{

    for (uint8_t i = 0; i < 9; i++)

    {

        if (board[i] == '.')

        {

            return 0;

        }

    }

    return 1;

}

static uint8_t Parse_Move(

    const char *command,

    int *index,

    char *player,

    uint8_t *has_player

)

{

    const char *p;

    int sign = 1;

    int value = 0;

    *has_player = 0;

    *player = '\0';

    if (strncmp(command, "MOVE:", 5) != 0)

    {

        return 0;

    }

    p = command + 5;

    if (*p == '-')

    {

        sign = -1;

        p++;

    }

    if (*p < '0' || *p > '9')

    {

        return 0;

    }

    while (*p >= '0' && *p <= '9')

    {

        if (value < 1000)

        {

            value =

                (value * 10) +

                (*p - '0');

        }

        p++;

    }

    *index = value * sign;

    /*

     * Official protocol:

     *

     * MOVE:<index>

     */

    if (*p == '\0')

    {

        return 1;

    }

    /*

     * Also accepts:

     *

     * MOVE:<index>:X

     * MOVE:<index>:O

     */

    if (*p == ':' &&

        (p[1] == 'X' || p[1] == 'O') &&

        p[2] == '\0')

    {

        *has_player = 1;

        *player = p[1];

        return 1;

    }

    return 0;

}

static void Process_Command(const char *command)

{

    /*

     * CONNECT

     */

    if (strcmp(command, "CONNECT") == 0)

    {

        if (server_state != SERVER_IDLE)

        {

            Send_Response(

                "NACK:BADSTATE\r\n"

            );

            return;

        }

        connected = 1;

        local_reset_pending = 0;

        Send_Response(

            "OK\r\n"

        );

        return;

    }

    /*

     * All remaining commands require

     * an established connection.

     */

    if (!connected)

    {

        Send_Response(

            "NACK:BADCMD\r\n"

        );

        return;

    }

    /*

     * POLL

     *

     * The GUI checks this command

     * for hardware button events.

     */

    if (strcmp(command, "POLL") == 0)

    {

        if (local_reset_pending)

        {

            local_reset_pending = 0;

            Send_Board_Response(

                "EVENT:RESET:"

            );

        }

        else

        {

            Send_Response(

                "EVENT:NONE\r\n"

            );

        }

        return;

    }

    /*

     * NEW

     */

    if (strcmp(command, "NEW") == 0)

    {

        if (server_state ==

            SERVER_IN_PROGRESS)

        {

            Send_Response(

                "NACK:BADSTATE\r\n"

            );

            return;

        }

        Reset_Board();

        local_reset_pending = 0;

        server_state =

            SERVER_IN_PROGRESS;

        Send_Board_Response(

            "OK:BOARD:"

        );

        return;

    }

    /*

     * STATE

     */

    if (strcmp(command, "STATE") == 0)

    {

        if (server_state ==

            SERVER_IDLE)

        {

            Send_Response(

                "NACK:NOGAME\r\n"

            );

            return;

        }

        Send_Board_Response(

            "BOARD:"

        );

        return;

    }

    /*
     * HISTORY: report all accepted moves on the STM32.
     * Each move is encoded as <player><index>, e.g. X4,O0,X8.
     * The GUI uses HISTORY:EMPTY if there are no moves.
     */
    if (strcmp(command, "HISTORY") == 0)
    {
        if (server_state == SERVER_IDLE)
        {
            Send_Response("NACK:NOGAME\r\n");
            return;
        }
        Send_History_Response();
        return;
    }

    /*
     * UNDO: remove the latest accepted move (including a
     * winning/drawing move), restore the player who made it,
     * and resume an active game. A resigned game is final.
     */
    if (strcmp(command, "UNDO") == 0)
    {
        if (server_state == SERVER_IDLE)
        {
            Send_Response("NACK:NOGAME\r\n");
            return;
        }
        if (game_resigned)
        {
            Send_Response("NACK:BADSTATE\r\n");
            return;
        }
        if (move_count == 0U)
        {
            Send_Response("NACK:NOMOVE\r\n");
            return;
        }

        --move_count;
        board[move_indices[move_count]] = '.';
        current_turn = move_players[move_count];
        server_state = SERVER_IN_PROGRESS;
        Send_Board_Response("OK:BOARD:");
        return;
    }

    /*

     * RESIGN

     */

    if (strcmp(command, "RESIGN") == 0)

    {

        if (server_state !=

            SERVER_IN_PROGRESS)

        {

            Send_Response(

                "NACK:NOGAME\r\n"

            );

            return;

        }

        server_state =

            SERVER_GAME_OVER;
        game_resigned = 1;

        Send_Response(

            "OK:GAMEOVER\r\n"

        );

        return;

    }

    /*

     * DISCONNECT

     */

    if (strcmp(command, "DISCONNECT") == 0)

    {

        if (server_state ==

            SERVER_IN_PROGRESS)

        {

            Send_Response(

                "NACK:BADSTATE\r\n"

            );

            return;

        }

        connected = 0;

        local_reset_pending = 0;

        server_state =

            SERVER_IDLE;

        Reset_Board();

        Send_Response(

            "OK\r\n"

        );

        return;

    }

    /*

     * MOVE

     */

    if (strncmp(command, "MOVE:", 5) == 0)

    {

        int index;

        char requested_player;

        uint8_t has_player;

        if (server_state !=

            SERVER_IN_PROGRESS)

        {

            Send_Response(

                "NACK:NOGAME\r\n"

            );

            return;

        }

        if (!Parse_Move(

                command,

                &index,

                &requested_player,

                &has_player))

        {

            Send_Response(

                "NACK:BADCMD\r\n"

            );

            return;

        }

        /*

         * Range validation.

         */

        if (index < 0 ||

            index > 8)

        {

            Send_Response(

                "NACK:RANGE\r\n"

            );

            return;

        }

        /*

         * Occupied-cell validation.

         */

        if (board[index] != '.')

        {

            Send_Response(

                "NACK:OCCUPIED\r\n"

            );

            return;

        }

        /*

         * If the client includes a player,

         * verify it against the current

         * authoritative STM32 turn.

         */

        if (has_player &&

            requested_player !=

            current_turn)

        {

            Send_Response(

                "NACK:NOTURN\r\n"

            );

            return;

        }

        /*

         * STM32 chooses the actual mark.

         */

        /* Move history is only appended after every validation passes. */
        if (move_count >= MAX_MOVES)
        {
            Send_Response("NACK:BADSTATE\r\n");
            return;
        }

        board[index] = current_turn;
        move_indices[move_count] = (uint8_t)index;
        move_players[move_count] = current_turn;
        ++move_count;

        /*

         * Win detection.

         */

        if (Has_Won(current_turn))

        {

            char prefix[7];

            prefix[0] = 'W';

            prefix[1] = 'I';

            prefix[2] = 'N';

            prefix[3] = ':';

            prefix[4] =

                current_turn;

            prefix[5] = ':';

            prefix[6] = '\0';

            server_state =

                SERVER_GAME_OVER;

            Send_Board_Response(

                prefix

            );

            return;

        }

        /*

         * Draw detection.

         */

        if (Is_Draw())

        {

            server_state =

                SERVER_GAME_OVER;

            Send_Board_Response(

                "DRAW:"

            );

            return;

        }

        /*

         * Change player.

         */

        if (current_turn == 'X')

        {

            current_turn = 'O';

        }

        else

        {

            current_turn = 'X';

        }

        Send_Board_Response(

            "OK:BOARD:"

        );

        return;

    }

    /*

     * Any other command is invalid.

     */

    Send_Response(

        "NACK:BADCMD\r\n"

    );

}

/* USER CODE END 0 */

/**

  * @brief  The application entry point.

  * @retval int

  */

int main(void)

{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */

  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */

  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */

  MX_GPIO_Init();

  MX_USART1_UART_Init();

  /* USER CODE BEGIN 2 */

  Reset_Board();

  previous_button_state =

      HAL_GPIO_ReadPin(

          GPIOA,

          GPIO_PIN_0

      );

  /* USER CODE END 2 */

  /* Infinite loop */

  /* USER CODE BEGIN WHILE */

  while (1)

  {

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */

    HAL_StatusTypeDef uart_status;

    /*

     * Update the physical hardware

     * on every loop.

     */

    Update_Hardware();

    uart_status =

        HAL_UART_Receive(

            &huart1,

            &rx_byte,

            1,

            20

        );

    /*

     * A byte was received.

     */

    if (uart_status == HAL_OK)

    {

        /*

         * We previously received an

         * oversized frame.

         */

        if (discard_frame)

        {

            last_rx_tick =

                HAL_GetTick();

            if (rx_byte == '\n')

            {

                discard_frame = 0;

                frame_active = 0;

                rx_index = 0;

            }

        }

        /*

         * Newline completes a frame.

         */

        else if (rx_byte == '\n')

        {

            rx_buffer[rx_index] =

                '\0';

            Process_Command(

                rx_buffer

            );

            rx_index = 0;

            frame_active = 0;

        }

        /*

         * Accept CRLF.

         */

        else if (rx_byte == '\r')

        {

            if (frame_active)

            {

                last_rx_tick =

                    HAL_GetTick();

            }

        }

        /*

         * Normal command character.

         */

        else

        {

            if (rx_index <

                RX_BUFFER_SIZE - 1)

            {

                rx_buffer[rx_index] =

                    (char)rx_byte;

                rx_index++;

                frame_active = 1;

                last_rx_tick =

                    HAL_GetTick();

            }

            /*

             * Frame is too large.

             */

            else

            {

                Send_Response(

                    "NACK:BADCMD\r\n"

                );

                rx_index = 0;

                discard_frame = 1;

                frame_active = 1;

                last_rx_tick =

                    HAL_GetTick();

            }

        }

    }

    /*

     * UART polling timeout.

     */

    else if (uart_status ==

             HAL_TIMEOUT)

    {

        /*

         * Check unfinished frame timeout.

         */

        if (frame_active)

        {

            if ((HAL_GetTick() -

                 last_rx_tick)

                >= FRAME_TIMEOUT_MS)

            {

                if (!discard_frame)

                {

                    Send_Response(

                        "NACK:TIMEOUT\r\n"

                    );

                }

                rx_index = 0;

                frame_active = 0;

                discard_frame = 0;

            }

        }

    }

  }

  /* USER CODE END 3 */

}

/**

  * @brief System Clock Configuration

  * @retval None

  */

void SystemClock_Config(void)

{

  RCC_OscInitTypeDef RCC_OscInitStruct = {0};

  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  RCC_OscInitStruct.OscillatorType =

      RCC_OSCILLATORTYPE_HSI;

  RCC_OscInitStruct.HSIState =

      RCC_HSI_ON;

  RCC_OscInitStruct.HSICalibrationValue =

      RCC_HSICALIBRATION_DEFAULT;

  RCC_OscInitStruct.PLL.PLLState =

      RCC_PLL_NONE;

  if (HAL_RCC_OscConfig(

          &RCC_OscInitStruct)

      != HAL_OK)

  {

    Error_Handler();

  }

  RCC_ClkInitStruct.ClockType =

      RCC_CLOCKTYPE_HCLK |

      RCC_CLOCKTYPE_SYSCLK |

      RCC_CLOCKTYPE_PCLK1;

  RCC_ClkInitStruct.SYSCLKSource =

      RCC_SYSCLKSOURCE_HSI;

  RCC_ClkInitStruct.AHBCLKDivider =

      RCC_SYSCLK_DIV1;

  RCC_ClkInitStruct.APB1CLKDivider =

      RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(

          &RCC_ClkInitStruct,

          FLASH_LATENCY_0)

      != HAL_OK)

  {

    Error_Handler();

  }

  PeriphClkInit.PeriphClockSelection =

      RCC_PERIPHCLK_USART1;

  PeriphClkInit.Usart1ClockSelection =

      RCC_USART1CLKSOURCE_PCLK1;

  if (HAL_RCCEx_PeriphCLKConfig(

          &PeriphClkInit)

      != HAL_OK)

  {

    Error_Handler();

  }

}

/**

  * @brief USART1 Initialization Function

  * @param None

  * @retval None

  */

static void MX_USART1_UART_Init(void)

{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */

  huart1.Instance =

      USART1;

  huart1.Init.BaudRate =

      115200;

  huart1.Init.WordLength =

      UART_WORDLENGTH_8B;

  huart1.Init.StopBits =

      UART_STOPBITS_1;

  huart1.Init.Parity =

      UART_PARITY_NONE;

  huart1.Init.Mode =

      UART_MODE_TX_RX;

  huart1.Init.HwFlowCtl =

      UART_HWCONTROL_NONE;

  huart1.Init.OverSampling =

      UART_OVERSAMPLING_16;

  huart1.Init.OneBitSampling =

      UART_ONE_BIT_SAMPLE_DISABLE;

  huart1.AdvancedInit.AdvFeatureInit =

      UART_ADVFEATURE_NO_INIT;

  if (HAL_UART_Init(

          &huart1)

      != HAL_OK)

  {

    Error_Handler();

  }

  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**

  * @brief GPIO Initialization Function

  * @param None

  * @retval None

  */

static void MX_GPIO_Init(void)

{

  /* USER CODE BEGIN MX_GPIO_Init_1 */

  GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */

  __HAL_RCC_GPIOA_CLK_ENABLE();

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*

   * D0 through D7 are PB0 through PB7.

   * Start with all LEDs OFF.

   */

  HAL_GPIO_WritePin(

      GPIOB,

      GPIO_PIN_0 |

      GPIO_PIN_1 |

      GPIO_PIN_2 |

      GPIO_PIN_3 |

      GPIO_PIN_4 |

      GPIO_PIN_5 |

      GPIO_PIN_6 |

      GPIO_PIN_7,

      GPIO_PIN_RESET

  );

  /*

   * SW0 / PA0.

   *

   * Active-low input.

   */

  GPIO_InitStruct.Pin =

      GPIO_PIN_0;

  GPIO_InitStruct.Mode =

      GPIO_MODE_INPUT;

  GPIO_InitStruct.Pull =

      GPIO_PULLUP;

  HAL_GPIO_Init(

      GPIOA,

      &GPIO_InitStruct

  );

  /*

   * D0 - D7

   *

   * PB0 - PB7

   */

  GPIO_InitStruct.Pin =

      GPIO_PIN_0 |

      GPIO_PIN_1 |

      GPIO_PIN_2 |

      GPIO_PIN_3 |

      GPIO_PIN_4 |

      GPIO_PIN_5 |

      GPIO_PIN_6 |

      GPIO_PIN_7;

  GPIO_InitStruct.Mode =

      GPIO_MODE_OUTPUT_PP;

  GPIO_InitStruct.Pull =

      GPIO_NOPULL;

  GPIO_InitStruct.Speed =

      GPIO_SPEED_FREQ_LOW;

  HAL_GPIO_Init(

      GPIOB,

      &GPIO_InitStruct

  );

  /* USER CODE END MX_GPIO_Init_2 */

}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**

  * @brief  This function is executed in case of error occurrence.

  * @retval None

  */

void Error_Handler(void)

{

  /* USER CODE BEGIN Error_Handler_Debug */

  __disable_irq();

  while (1)

  {

  }

  /* USER CODE END Error_Handler_Debug */

}

#ifdef USE_FULL_ASSERT

/**

  * @brief Reports the name of the source file and source line number

  * where the assert_param error has occurred.

  */

void assert_failed(

    uint8_t *file,

    uint32_t line

)

{

  /* USER CODE BEGIN 6 */

  /* User can add implementation here. */

  /* USER CODE END 6 */

}

#endif /* USE_FULL_ASSERT */
