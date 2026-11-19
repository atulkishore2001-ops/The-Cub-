#!/usr/bin/env bash
# Cinematic grade v2 (ffmpeg filter fragments). Use: [in]$GRADE,$FINISH[out]  (FINISH needs split/blend -> use grade_chain)
# Base: warm WB, filmic S-curve with milky blacks & rolled highlights, teal shadows / golden highlights,
# tamed venue LEDs (green/cyan/blue/magenta), skin-safe saturation.
GRADE="format=gbrpf32le,colortemperature=temperature=5400:mix=0.5:pl=0.5,curves=master='0/0.045 0.10/0.075 0.25/0.20 0.50/0.50 0.75/0.80 0.90/0.90 1/0.95',colorbalance=rs=-0.06:gs=-0.01:bs=0.07:rm=0.04:gm=0.0:bm=-0.03:rh=0.05:gh=0.02:bh=-0.05:pl=1,huesaturation=colors=g:saturation=-0.55:intensity=-0.06,huesaturation=colors=c+b:saturation=-0.40:intensity=-0.03,huesaturation=colors=m:saturation=-0.25,vibrance=intensity=0.12,eq=contrast=1.06:saturation=0.96"
# Finish: highlight bloom/halation (warm), vignette, fine grain. Expects labelled input [g] and outputs [out].
FINISH="[g]format=gbrp,split[b][h];[h]curves=master='0/0 0.70/0 1/1',gblur=sigma=30,colorchannelmixer=rr=1:gg=0.6:bb=0.38[gl];[b][gl]blend=all_mode=screen:all_opacity=0.38,vignette=angle=PI/4.5:mode=forward,noise=alls=6:allf=t+u[out]"
export GRADE FINISH
