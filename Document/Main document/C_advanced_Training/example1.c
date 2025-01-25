#include <stdio.h>
#include <stdint.h>

void increment(int*ptr){
    (*ptr)++;
}

int main()
{
   int *pInt;
   int **ppInt1;
   int **ppInt2;

   pInt = (int*)malloc(sizeof(int));
   ppInt1 = (int**)malloc(10*sizeof(int));
   ppInt2 = (int**)malloc(10*sizeof(int));

   free(pInt);
   free(ppInt1);
   free(*ppInt2);
   return 0;

    
}
//Pointer is devoted to change the value of global or local variable when they are declared in different funtion 
//from the plus funtion ( derefrecing). Beacause the addfress of the variable in the pluss funtion is diffrent from
//the address of variable declared in main function, so we need to pass the address of the variable if we want to modify
//their value