cd ../online_data
dec_a=6
dec_b=12
dec_c=18
dec_d=24
dec_e=30

for dec_th in ${dec_a} ${dec_b} ${dec_c} ${dec_d} ${dec_e}
do
    rm dec_dist/sess_${dec_th}ms_unsorted.tmp
done
cat cut_wc5w_flowlist.log | xargs -i awk '{
    if ($5 > '"${dec_a}"') {
        cnt_a++
    }
    if ($5 > '"${dec_b}"') {
        cnt_b++
    }
    if ($5 > '"${dec_c}"') {
        cnt_c++
    }
    if ($5 > '"${dec_d}"') {
        cnt_d++
    }
    if ($5 > '"${dec_e}"') {
        cnt_e++
    }
} END {
    print FILENAME, cnt_a/NR >> "dec_dist/sess_"'${dec_a}'"ms_unsorted.tmp"
    print FILENAME, cnt_b/NR >> "dec_dist/sess_"'${dec_b}'"ms_unsorted.tmp"
    print FILENAME, cnt_c/NR >> "dec_dist/sess_"'${dec_c}'"ms_unsorted.tmp"
    print FILENAME, cnt_d/NR >> "dec_dist/sess_"'${dec_d}'"ms_unsorted.tmp"
    print FILENAME, cnt_e/NR >> "dec_dist/sess_"'${dec_e}'"ms_unsorted.tmp"
}' cut/{} 

for dec_th in ${dec_a} ${dec_b} ${dec_c} ${dec_d} ${dec_e}
do
    awk '{print $2}' dec_dist/sess_${dec_th}ms_unsorted.tmp | sort -gk1 > dec_dist/sess_${dec_th}ms.tmp
    awk -vstep=$(awk 'END{printf("%.4f\n", NR/10000)}' dec_dist/sess_${dec_th}ms.tmp | bc) 'BEGIN {
        cnt = 1
    } {
        sum += $1
        if (NR >= int(cnt*step)) {
            print cnt, $0
            cnt = cnt + 1 + int(NR-cnt*step)
        }
    } END {
        printf("Avg %.3f\n", sum/NR)
    }' dec_dist/sess_${dec_th}ms.tmp > dec_dist/sess_${dec_th}ms.log
    rm dec_dist/sess_${dec_th}ms.tmp
done