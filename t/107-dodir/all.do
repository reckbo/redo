. ../skip-if-minimal-do.sh
rm -rf x do/log toto
mkdir -p x/y
redo x/y/z

[ -e x/y/z ] || exit 11
[ $(wc -l <do/log) -eq 1 ] || exit 12

redo toto

[ -e x/y/z ] || exit 21
[ $(wc -l <do/log) -eq 2 ] || exit 22

