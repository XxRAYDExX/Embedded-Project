#include "game.h"
#include <string.h>
void game_init(Game *g) {
    memcpy(g->board,".........",10);
    g->turn='X'; g->status=IDLE;
}
void game_new(Game *g) {
    memcpy(g->board,".........",10);
    g->turn='X'; g->status=IN_PROGRESS;
}
char game_winner(const Game *g) {
    static const uint8_t lines[8][3]={
        {0,1,2},{3,4,5},{6,7,8},{0,3,6},
        {1,4,7},{2,5,8},{0,4,8},{2,4,6}
    };
    for (unsigned k=0;k<8;k++) {
        char c=g->board[lines[k][0]];
        if(c!='.' && c==g->board[lines[k][1]] && c==g->board[lines[k][2]]) return c;
    }
    return '.';
}
int game_full(const Game *g) {
    for(unsigned i=0;i<9;i++) if(g->board[i]=='.') return 0;
    return 1;
}
