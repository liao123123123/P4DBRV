#! /bin/bash

# find ./ -wholename  'assertion_*.txt' -delete

echo "Compiling the assertions...!!!"
bison -d DBRV.y
flex DBRV.l

echo "Checking if necessary files exist or not...!!!"
FILE1=./DBRV.tab.c
FILE2=./lex.yy.c

if [[ -f "$FILE1" && -f "$FILE2" ]]; then
    echo "All necessary files exist...!!!"
    g++ DBRV.tab.c lex.yy.c -lfl -o DBRV
    ./DBRV assertions
fi

if [ ! -f "$FILE1" ]; then
    echo "$FILE1 does not exist...!!!"
fi

if [ ! -f "$FILE2" ]; then
    echo "$FILE2 does not exist...!!!"
fi

# echo -e "\n\t Please provide <p4filename.p4>:"
# read p4_file_name
#
# echo -e "\n\t Please provide <dot file name>:"
# read dot_file_name
#
# echo -e "\n\t Please provide <json file name>:"
# read json_file_name
#
# echo -e "\n\t Please provide <control block name(eg: \"MyIngress\")>:"
# read ctrl_blk_name
#
# echo -e "\n\t Please provide <user metadata variable name>:"
# read meta_name
#
# echo -e "\n\t Please provide header file name (eg: header.p4 \"Please include path as well if required.\"):"
# read header_file

p4_file_name="forwarding.p4"
dot_file_name="MyIngress.dot"
json_file_name="forwarding.json"
ctrl_blk_name="MyIngress"
meta_name="meta"
header_file=""


path=$(pwd)
path="${path}/.."
path=$(find "${path}" -maxdepth 2 -name "${p4_file_name}")
path=$(dirname "${path}")
echo "$path"
cd "${path}"

sudo python3 p4_augmenter_bmv2_bfs.py "$p4_file_name" "$dot_file_name" "$json_file_name" "$ctrl_blk_name" "$meta_name"

sudo python3 assertion_augmenter.py "${p4_file_name%.p4}"_augmented.p4 "$ctrl_blk_name" "$meta_name" "$header_file"

# find ./ -wholename '*.pkl' -delete
