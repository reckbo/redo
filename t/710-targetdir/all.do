exec echo disabled

. ./clean.do
redo --source-dir src --target-dir dest all

[ -d dest ]       || exit 10
[ -e dest/a ]     || exit 11
[ -e dest/b ]     || exit 12
[ -e dest/sub/c ] || exit 13

. ./clean.do
( cd src
  redo --target-dir ../dest all
)

[ -d dest ]       || exit 20
[ -e dest/a ]     || exit 21
[ -e dest/b ]     || exit 22
[ -e dest/sub/c ] || exit 23

