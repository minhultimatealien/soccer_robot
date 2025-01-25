#include <stdio.h>
#pragma pack(1)
int sum(){
    int a = 10;
    return a;
}
int main()
{
    typedef union{
        int a;
        //char b;
        int c;
    } str1;
    int b = 10;
    str1 myString;
    // myString.a = calloc(1,sizeof(int));
    // myString.a = sum();
    // myString.b = 'Minh';
    // myString.c = 126;
    // str1 * otherString;
    // otherString = &myString;
    // otherString->a = calloc(10,sizeof(int));
    // otherString -> a = sum();
    //printf("size : %d",sizeof(myString));
    //myString = {10;12};
    //myString.a = 10;
    //myString.c = 12;
    int *ptr;
    ptr = &sum;
    //printf("%d\n",sizeof(char));
    //printf("%d\n",myString.c);
    printf("%d",(*ptr)());
}