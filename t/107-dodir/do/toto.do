# $PWD must be in do dir and $1 and $2 must reference parent directory

[ ${PWD##*/} = "do" ] || exit 101
[ $1 = "../toto" ] || exit 102
[ $2 = "../toto" ] || exit 103

echo $$ >>log
echo $$ >$3
