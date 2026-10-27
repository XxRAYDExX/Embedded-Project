#ifndef GAME_H
#define GAME_H
#include <stdint.h>
typedef enum { IDLE, IN_PROGRESS, GAME_OVER } GameStatus;
typedef struct { char board[10]; char turn; GameStatus status; } Game;
void game_init(Game *g);
void game_new(Game *g);
char game_winner(const Game *g);
int game_full(const Game *g);
#endif
