for i in `ls ${1}`
do
    cat ${1}/${i} | awk '{res[$5]++;} END{for (i in res){print i,res[i]}}' > ${2}/${i}
    # dec=`cat ${1}/${i} | awk '{sum += $5;} END{print sum/NR}'`
    # echo ${i}, ${dec} >> ${1}/../delayed_frames_decode.log
done