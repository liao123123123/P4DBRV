echo "Compiling the assertions...!!!"
bison -d DBRV.y
flex DBRV.l

echo "Checking if necessary files exist or not...!!!"
FILE1=./DBRV.tab.c
FILE2=./DBRV.yy.c

if [[ -f "$FILE1" && -f "$FILE2" ]]; then
    echo "All necessary files exist...!!!"
    g++ DBRV.tab.c lex.yy.c -lfl -o DBRV
    ./DBRV input_assertions
fi

if [ ! -f "$FILE1" ]; then
    echo "$FILE1 does not exist...!!!"
fi


if [ ! -f "$FILE2" ]; then
    echo "$FILE2 does not exist...!!!"
fi
