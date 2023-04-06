cd ../online_data/actions
for filter in w22w w32w w30w w20w
do
    echo ${filter}
    cd 60fps
    cat ../../cut_${filter}_60fps_flowlist.log | xargs -i wc -l {} > ../../results/${filter}/framenum-60fps.log
    cat ../../results/${filter}/native/stall_sessions_100.log | awk '{if($3>0.05){print $1}}' | xargs -i wc -l {} > ../../results/${filter}/framenum-60fps-stutter.log
    cd ../afr_0.002_0.033_0.250
    cat ../../cut_${filter}_60fps_flowlist.log | xargs -i wc -l {} > ../../results/${filter}/framenum-afr.log
    cat ../../results/${filter}/native/stall_sessions_100.log | awk '{if($3>0.05){print $1}}' | xargs -i wc -l {} > ../../results/${filter}/framenum-afr-stutter.log
    cd ..
    paste -d" " ../results/${filter}/framenum-60fps.log ../results/${filter}/framenum-afr.log | awk '{print $2,$1,$3,($1-$3)/$3}' > ../results/${filter}/framenum-60fps-afr.log
    paste -d" " ../results/${filter}/framenum-60fps-stutter.log ../results/${filter}/framenum-afr-stutter.log | awk '{print $2,$1,$3,($1-$3)/$3}' > ../results/${filter}/framenum-60fps-afr-stutter.log
done

# cat ../online_data/cut_w30w_flowlist.log | sort | xargs -i wc -l ../online_data/logs/afr_0.002_0.033_0.250/{} > w30w_afr_0.002_0.033_0.250_wc.log
# cat ../online_data/cut_w30w_flowlist.log | sort | xargs -i wc -l ../online_data/logs/native/{} > w30w_native_wc.log
