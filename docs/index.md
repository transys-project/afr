
## Abstract

Emerging high quality real-time communication (RTC) applications stream ultra-high-definition (UHD) videos with high frame rate (HFR). They use edge computing, which enables high bandwidth and low latency streaming. Our measurements, from the cloud gaming platform of one of the largest gaming companies, show that, in this setting, the client-side decoder is often the cause for high latency that hurts user's experience. We therefore propose an Adaptive Frame Rate (AFR) controller that helps achieve ultra-low latency by coordinating the frame rate with network fluctuation and decoder capacity. AFR's design addresses two key challenges: (1) queue measurements do not provide timely feedback for the control loop and (2) multiple factors control the decoder queue, and different actions must be taken depending on why the queue accumulates. Trace-driven simulations and large-scale deployments in the wild demonstrate that AFR can reduce the tail queuing delay by up to 7.4× and the stuttering events measured by end-to-end delay by 34% on average. AFR has been deployed in production in our cloud gaming service for over one year.

## Paper

### Enabling High Quality Real-Time Communications with Adaptive Frame-Rate

Zili Meng, Tingfeng Wang, Yixin Shen, Bo Wang, Mingwei Xu, Rui Han, Honghao Liu, Venkat Arun, Hongxin Hu, Xue Wei.<br>Proceedings of the 2023 USENIX NSDI Conference<br>[[PDF]](https://zilimeng.com/papers/afr-nsdi23.pdf)

### Citation

```
@inproceedings{meng2023enabling,
  title={Enabling High Quality Real-Time Communications with Adaptive Frame-Rate},
  author={Meng, Zili and Wang, Tingfeng and Shen, Yixin and Wang, Bo and Xu, Mingwei and Han, Rui and Liu, Honghao and Arun, Venkat and Hu, Hongxin and Wei, Xue},
  booktitle={Proc. USENIX NSDI},
  year={2023}
}
```

## Code

[GitHub](https://github.com/transys-project/afr/)

## Supporters

The research is supported by the National Natural Science Foundation of China (No. 62002196, 61832013, and
62221003) and the Tsinghua-Tencent Collaborative Grant. 

## Contact
For any questions, please send an email to [zilim@ieee.org](mailto:zilim@ieee.org).

<script src="//t1.extreme-dm.com/f.js" id="eXF-zilimeng-0" async defer></script>