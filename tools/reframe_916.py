"""Subject-aware 9:16 reframing preview: faces+hands (pose) and held objects decide the crop;
if the key subjects cannot fit, a slow pan between both edges is planned."""
import cv2, sys, numpy as np
from ultralytics import YOLO
pose=YOLO('yolov8s-pose.pt'); det=YOLO('yolov8s.pt')
src,out=sys.argv[1],sys.argv[2]; times=[float(t) for t in sys.argv[3:]]
OBJ={'cup','bowl','cell phone','vase','cake','wine glass','book','potted plant','handbag'}
cap=cv2.VideoCapture(src); tiles=[]
for t in times:
    cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,f=cap.read(); H,W=f.shape[:2]; cw=int(H*9/16)
    r=pose(f,verbose=False)[0]
    people=[]
    for i,b in enumerate(r.boxes):
        if b.conf<0.35: continue
        kp=r.keypoints.data[i].cpu().numpy()  # 17x3
        head=[k for k in kp[0:5] if k[2]>0.4]; hands=[k for k in kp[9:11] if k[2]>0.4]
        bx=b.xyxy[0].cpu().numpy(); area=(bx[2]-bx[0])*(bx[3]-bx[1])
        hx=np.mean([k[0] for k in head]) if head else None
        people.append(dict(box=bx,area=area,head=hx,hands=[k[0] for k in hands]))
    objs=[]
    for b in det(f,verbose=False)[0].boxes:
        n=det.names[int(b.cls)]
        if n in OBJ and b.conf>0.3: x=b.xyxy[0].cpu().numpy(); objs.append((x[0],x[2],n))
    pts=[]   # x positions that MUST be in frame
    if people:
        mx=max(p['area'] for p in people)
        main=[p for p in people if p['area']>=0.3*mx]
        for p in main:
            if p['head'] is not None: pts += [p['head']-0.06*W, p['head']+0.06*W]
            pts += p['hands']
        if not any(p['head'] is not None for p in main):  # detail shot: hands/torso only
            pts += [x for p in main for x in p['hands']]
    # only keep objects that overlap a main person (ignores blurry background false hits)
    if people:
        objs=[o for o in objs if any(o[0]<p['box'][2] and o[1]>p['box'][0] for p in main)]
    for x0,x1,n in objs: pts += [x0,x1]
    if not pts: pts=[W/2]
    lo,hi=min(pts),max(pts); span=hi-lo
    if span<=cw: cx=(lo+hi)/2; mode='fits'
    elif span<=cw+0.12*W: cx=(lo+hi)/2; mode='fits (tight)'  # drop head padding instead of panning
    else:
        # cannot fit everyone: plan a slow pan from lo-edge to hi-edge
        cx=None; mode=f'PAN {span/cw:.1f}x wider'
    if cx is None: ls=[int(np.clip(lo-0.03*W,0,W-cw)), int(np.clip(hi+0.03*W-cw,0,W-cw))]
    else: ls=[int(np.clip(cx-cw/2,0,W-cw))]
    viz=f.copy()
    for p in people: b=p['box']; cv2.rectangle(viz,(int(b[0]),int(b[1])),(int(b[2]),int(b[3])),(0,255,255),2)
    for x in pts: cv2.line(viz,(int(x),0),(int(x),40),(255,0,255),6)
    for x0,x1,n in objs: cv2.putText(viz,n,(int(x0),H-60),0,1.5,(255,0,255),3)
    for l in ls: cv2.rectangle(viz,(l,0),(l+cw,H),(0,255,0) if mode.startswith('fits') else (0,140,255),6)
    s=540/H; viz=cv2.resize(viz,(int(W*s),540))
    cv2.putText(viz,f"{t:.1f}s {mode}",(10,30),0,0.9,(255,255,255),2)
    crops=[cv2.resize(f[:,l:l+cw],(int(cw*s),540)) for l in ls]
    row=[viz]+[np.hstack([np.full((540,10,3),255,np.uint8),c]) for c in crops]
    row=np.hstack(row); tiles.append(row)
w=max(t.shape[1] for t in tiles)
tiles=[np.hstack([t,np.zeros((540,w-t.shape[1],3),np.uint8)]) for t in tiles]
cv2.imwrite(out,np.vstack(tiles))
