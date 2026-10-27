#include "protocol.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void check(Game*g,const char*command,const char*expected){
 char out[40];protocol_handle(g,command,out,sizeof(out));
 if(strcmp(out,expected)){fprintf(stderr,"%s: got %s expected %s\n",command,out,expected);assert(0);}
}
int main(void){
 Game g;game_init(&g);
 check(&g,"CONNECT","OK");
 check(&g,"MOVE:0:X","NACK:NOGAME");
 check(&g,"NEW","OK:BOARD:.........");
 check(&g,"MOVE:0:O","NACK:NOTURN");
 check(&g,"MOVE:0:X","OK:BOARD:X........");
 check(&g,"MOVE:0:O","NACK:OCCUPIED");
 check(&g,"MOVE:9:O","NACK:RANGE");
 check(&g,"MOVE:3:O","OK:BOARD:X..O.....");
 check(&g,"MOVE:1:X","OK:BOARD:XX.O.....");
 check(&g,"MOVE:4:O","OK:BOARD:XX.OO....");
 check(&g,"MOVE:2:X","WIN:X:XXXOO....");
 check(&g,"MOVE:5:O","NACK:NOGAME");
 check(&g,"STATE","BOARD:XXXOO....");
 check(&g,"DISCONNECT","OK");
 check(&g,"NEW","OK:BOARD:.........");
 check(&g,"MOVE:0:X","OK:BOARD:X........");
 check(&g,"MOVE:1:O","OK:BOARD:XO.......");
 check(&g,"MOVE:2:X","OK:BOARD:XOX......");
 check(&g,"MOVE:4:O","OK:BOARD:XOX.O....");
 check(&g,"MOVE:3:X","OK:BOARD:XOXXO....");
 check(&g,"MOVE:5:O","OK:BOARD:XOXXOO...");
 check(&g,"MOVE:7:X","OK:BOARD:XOXXOO.X.");
 check(&g,"MOVE:6:O","OK:BOARD:XOXXOOOX.");
 check(&g,"MOVE:8:X","DRAW:XOXXOOOXX");
 puts("All host protocol tests passed");
}
