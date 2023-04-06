for i in {0.5,0.9,0.95,0.99,0.999,0.9999}
do
    awk '{print $3}' $1 | sort -n | awk '{all[NR] = $0} END{print all[int(NR*"'${i}'" - 0.5)]}'
done