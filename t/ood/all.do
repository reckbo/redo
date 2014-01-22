rm a
redo a

[ "$(redo-targets)" == "a" ] || { echo "redo-targets failed"; exit 1; }

[ "$(redo-sources | sort | xargs)" == "a.do all.do b" ] || { echo "redo-sources failed"; exit 1; }

touch b

[ "$(redo-ood)" == "a" ] || { echo "redo-ood failed"; exit 1; }
