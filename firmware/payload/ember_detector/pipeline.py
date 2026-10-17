"""Stored acquisition and shared preparation. Algorithm selection is a registry lookup."""
from pathlib import Path
import hashlib
import json
import math
import platform
import time
import cv2
import numpy as np
from .model import Decision, Result, Scene
from .registry import create


def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(data):return json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def bounded(value, low, high, name, integer=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
        raise ValueError('Invalid '+name)
    if integer and not isinstance(value,int):raise ValueError('Integer required: '+name)


def load_config(path):
    config=json.loads(Path(path).read_text())
    expected={'schema_version','algorithm','exploratory_jpeg','calibration_sha256','dark_policy',
              'reference_exposure_us','roi_margin_fraction','max_pixels','max_input_bytes','registration','detector'}
    if set(config)!=expected or config['schema_version']!=1:raise ValueError('Unsupported configuration schema/keys')
    if config['exploratory_jpeg'] is not True or config['dark_policy']!='none':
        raise ValueError('This input adapter requires explicit exploratory JPEG / no dark subtraction')
    if len(bytes.fromhex(config['calibration_sha256']))!=32:raise ValueError('Calibration hash')
    bounded(config['reference_exposure_us'],1,1000000,'reference exposure')
    bounded(config['roi_margin_fraction'],.1,.45,'ROI margin')
    for key in ('max_pixels','max_input_bytes'):bounded(config[key],1,20000000,key,True)
    reg=config['registration']
    reg_keys={'mode','max_features','min_inliers','min_inlier_fraction','max_error_px','min_overlap_fraction'}
    if reg.get('mode')=='normalized_orb_homography':
        reg_keys|={'contrast_percentiles','min_contrast_dn'}
        percentiles=reg.get('contrast_percentiles')
        if not isinstance(percentiles,list) or len(percentiles)!=2:raise ValueError('Contrast percentiles')
        for value in percentiles:bounded(value,0,100,'contrast percentile')
        if percentiles[0]>=percentiles[1]:raise ValueError('Contrast percentile order')
        bounded(reg.get('min_contrast_dn'),1,255,'minimum matching contrast')
    if set(reg)!=reg_keys:raise ValueError('Registration keys')
    if reg['mode'] not in ('prealigned','orb_homography','normalized_orb_homography'):raise ValueError('Registration mode')
    for key in ('max_features','min_inliers'):bounded(reg[key],4,10000,key,True)
    for key in ('min_inlier_fraction','min_overlap_fraction'):bounded(reg[key],.01,1,key)
    bounded(reg['max_error_px'],.01,10,'registration error')
    detector=create(config['algorithm'])
    detector.validate(config['detector'])
    return config


def matching_image(image, settings):
    """Stretch a COPY for feature matching; never normalize measured signals."""
    low,high=np.percentile(image,settings['contrast_percentiles'])
    if high-low<settings['min_contrast_dn']:raise ValueError('REGISTRATION_LOW_CONTRAST')
    stretched=np.clip((image.astype(np.float32)-low)*255/(high-low),0,255).astype('uint8')
    return stretched,[float(low),float(high)]


def align(source, target, settings):
    if settings['mode']=='prealigned':return np.eye(3),{'mode':'prealigned_asserted_by_profile'}
    # Contrast enhancement affects matching only, never the measured signals.
    contrast={}
    if settings['mode']=='normalized_orb_homography':
        source,contrast['source_dn']=matching_image(source,settings)
        target,contrast['target_dn']=matching_image(target,settings)
    clahe=cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8))
    orb=cv2.ORB_create(nfeatures=settings['max_features'])
    a,da=orb.detectAndCompute(clahe.apply(source),None)
    b,db=orb.detectAndCompute(clahe.apply(target),None)
    if da is None or db is None:raise ValueError('REGISTRATION_NO_FEATURES')
    pairs=cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(da,db,k=2)
    matches=[p[0] for p in pairs if len(p)==2 and p[0].distance<.75*p[1].distance]
    if len(matches)<settings['min_inliers']:raise ValueError('REGISTRATION_TOO_FEW_MATCHES')
    src=np.float32([a[m.queryIdx].pt for m in matches]);dst=np.float32([b[m.trainIdx].pt for m in matches])
    cv2.setRNGSeed(0)
    matrix,keep=cv2.findHomography(src,dst,cv2.RANSAC,settings['max_error_px'])
    if matrix is None or not np.isfinite(matrix).all():raise ValueError('REGISTRATION_FIT_FAILED')
    keep=keep.ravel().astype(bool);n=int(keep.sum())
    if n<settings['min_inliers'] or n/len(matches)<settings['min_inlier_fraction']:raise ValueError('REGISTRATION_WEAK_FIT')
    error=cv2.perspectiveTransform(src[keep,None,:],matrix)[:,0,:]-dst[keep]
    rms=float(np.sqrt(np.mean(np.sum(error**2,axis=1))))
    if rms>settings['max_error_px']:raise ValueError('REGISTRATION_ERROR')
    # A fit localized to one bright object does not establish scene alignment.
    spread=cv2.contourArea(cv2.convexHull(src[keep]))/(source.shape[0]*source.shape[1])
    if spread<.05:raise ValueError('REGISTRATION_LOCALIZED_FIT')
    quality=dict(mode=settings['mode'],inliers=n,matches=len(matches),rms_px=rms,
                 support_fraction=spread,source_to_reference=matrix.tolist())
    if contrast:quality['matching_contrast']=contrast
    return matrix,quality


def prepare(fixture, root, config, calibration):
    channels=fixture['channels'];ordered=sorted(channels.values(),key=lambda c:c['wavelength_nm'])
    if len(ordered)!=3 or len({c['port'] for c in ordered})!=3:raise ValueError('TRIPLET_REQUIRED')
    waves=tuple(c['wavelength_nm'] for c in ordered)
    if not all(isinstance(w,(int,float)) and math.isfinite(w) and w>0 for w in waves) or not waves[0]<waves[1]<waves[2]:raise ValueError('WAVELENGTH_ORDER')
    raw=[];corrected=[];masks=[];saturated=[];shape=None;root=Path(root).resolve()
    if digest(Path(calibration).read_bytes())!=config['calibration_sha256']:raise ValueError('CALIBRATION_HASH')
    with np.load(calibration,allow_pickle=False) as maps:
        for channel in ordered:
            path=(root/channel['path']).resolve()
            if not path.is_relative_to(root):raise ValueError('INPUT_PATH_ESCAPE')
            if path.stat().st_size>config['max_input_bytes']:raise ValueError('INPUT_TOO_LARGE')
            data=path.read_bytes()
            if digest(data)!=channel['sha256']:raise ValueError('INPUT_HASH')
            image=cv2.imdecode(np.frombuffer(data,dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
            if image is None:raise ValueError('IMAGE_DECODE')
            if image.size>config['max_pixels'] or list(image.shape[::-1])!=[channel['width'],channel['height']]:raise ValueError('IMAGE_DIMENSIONS')
            if shape is not None and image.shape!=shape:raise ValueError('CHANNEL_SHAPE')
            shape=image.shape
            exposure=channel.get('exposure_us')
            bounded(exposure,1,1000000,'exposure')
            gain=maps['gain_'+str(channel['port'])]
            if gain.shape!=shape or not np.isfinite(gain).all() or (gain<=0).any():raise ValueError('CALIBRATION_MAP')
            value=image.astype(np.float32)*gain*(config['reference_exposure_us']/exposure)
            valid=np.ones(shape,dtype=bool);margin=config['roi_margin_fraction'];h,w=shape
            valid[:math.ceil(h*margin)]=False;valid[h-math.ceil(h*margin):]=False
            valid[:,:math.ceil(w*margin)]=False;valid[:,w-math.ceil(w*margin):]=False
            sat=image>=250
            raw.append(image);corrected.append(value);masks.append(valid & ~sat);saturated.append(sat & valid)
    h,w=shape;registered=[];support=[];satmaps=[];fits=[]
    for i in range(3):
        matrix,quality=(np.eye(3),{'mode':'reference'}) if i==1 else align(raw[i],raw[1],config['registration'])
        fits.append(quality)
        registered.append(cv2.warpPerspective(corrected[i],matrix,(w,h),flags=cv2.INTER_LINEAR))
        # Linear-resampled validity requires every contributing pixel valid.
        support.append(cv2.warpPerspective(masks[i].astype('float32'),matrix,(w,h),flags=cv2.INTER_LINEAR)>=.999)
        satmaps.append(cv2.warpPerspective(saturated[i].astype('uint8'),matrix,(w,h),flags=cv2.INTER_NEAREST)>0)
    common=np.logical_and.reduce(support)
    reference_roi=np.ones(shape,dtype=bool);my=math.ceil(h*config['roi_margin_fraction']);mx=math.ceil(w*config['roi_margin_fraction'])
    reference_roi[:my]=False;reference_roi[-my:]=False;reference_roi[:,:mx]=False;reference_roi[:,-mx:]=False
    overlap=float(common.sum()/max(1,reference_roi.sum()))
    if overlap<config['registration']['min_overlap_fraction']:raise ValueError('INSUFFICIENT_OVERLAP')
    clipped=float((np.logical_or.reduce(satmaps)&reference_roi).sum()/max(1,reference_roi.sum()))
    return Scene(*registered,common,waves,clipped,int(reference_roi.sum())),dict(registration=fits,overlap_fraction=overlap)


def run(manifest_path, fixture_id, config, calibration):
    start=time.monotonic();manifest_path=Path(manifest_path)
    code=digest(b''.join(p.name.encode()+p.read_bytes() for p in sorted(Path(__file__).parent.glob('*.py')) if not p.name.startswith('.')))
    record=dict(schema_version=1,pipeline_version='0.2.0',code_sha256=code,
                dependencies={'numpy':np.__version__,'opencv':cv2.__version__,'python':platform.python_version(),'machine':platform.machine()},fixture_id=fixture_id,input_source='STORED_FIXTURE',camera_capture_performed=False,
                algorithm=config['algorithm'],config_sha256=digest(canonical(config)),
                calibration_sha256=config['calibration_sha256'],analysis_unix_ms=time.time_ns()//1000000,
                warnings=['EXPLORATORY_JPEG_LINEARITY_UNVERIFIED','OPTICAL_COMPATIBILITY_UNVERIFIED','GAIN_UNKNOWN','DARK_NOT_SUBTRACTED'])
    maps={}
    try:
        manifest=json.loads(manifest_path.read_text());record['manifest_sha256']=digest(manifest_path.read_bytes())
        selected=[f for f in manifest['fixtures'] if f['fixture_id']==fixture_id]
        if len(selected)!=1:raise ValueError('FIXTURE_NOT_UNIQUE_OR_MISSING')
        fixture=selected[0]
        # Labels stay outside the Scene and detector; evaluation joins afterward.
        record['inputs']={key:dict(path=c['path'],sha256=c['sha256'],exposure_us=c.get('exposure_us')) for key,c in fixture['channels'].items()}
        scene,quality=prepare(fixture,manifest_path.parent,config,calibration)
        record['preparation_ms']=round((time.monotonic()-start)*1000,3)
        try:
            result=create(config['algorithm']).detect(scene,config['detector'])
        except Exception as error:
            result=Result(Decision.UNKNOWN,'DETECTOR_FAILURE:'+type(error).__name__)
        if (not isinstance(result,Result) or not isinstance(result.decision,Decision) or
                not isinstance(result.reason,str) or not result.reason or
                not isinstance(result.metrics,dict) or not isinstance(result.regions,list)):
            raise ValueError('DETECTOR_CONTRACT')
        canonical({'metrics':result.metrics,'regions':result.regions})
        record.update(result=result.decision.name,reason=result.reason,metrics=dict(quality,**result.metrics),regions=result.regions)
        maps=result.maps
    except (ValueError,TypeError,KeyError,OSError,cv2.error) as error:
        record.update(result='UNKNOWN',reason=str(error))
    record['elapsed_ms']=round((time.monotonic()-start)*1000,3)
    return record,maps
