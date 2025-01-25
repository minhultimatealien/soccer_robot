#include <stdio.h>

int SumOfElement(int *p, int size)
{
    int result = 0;
    printf("%d\n",p[0]);
    for(int i = 0; i < size; i++)
    {
        result +=  *p;
        p++;
        //printf("%d",result);
    }
    return result;
}

void main()
{
    int a[5][2] = {{5,4},{10,12},{100,1000},{8,19},{21,15}};
    int (*p)[2] = a;
    // for(int i = 0; i<5;i++)
    // {
    //     printf("%d\n",*(*p+i));
    // }
    printf("%d",*a);
}