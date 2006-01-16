for i in `find * -type f -name "*.po"`
do
    echo "Input: $i"
    o=${i%.*}
    echo "Output: $o.mo"
    msgfmt $i -o $o.mo
done
