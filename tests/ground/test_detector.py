"""Analytical detector correctness, replaceability and invalid-input behavior."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'firmware/payload'))
try:
    import numpy as np
    import cv2
except ImportError:
    raise unittest.SkipTest('Install firmware/payload/requirements-detector.txt')
from ember_detector.model import Scene,Result,Decision
from ember_detector.spectral import SpectralExcess
from ember_detector.registry import register,create
from ember_detector.pipeline import load_config,canonical,digest,run


class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.config=load_config(ROOT/'firmware/payload/config/stored-images.json')
        self.settings=self.config['detector']

    def scene(self):
        low=np.full((24,24),100,dtype='float32');high=np.full_like(low,130)
        on=(low+2*high)/3
        return Scene(low,on,high,np.ones_like(low,dtype=bool),(750,770,780))

    def test_known_continuum_and_injected_region(self):
        scene=self.scene();detector=SpectralExcess()
        self.assertEqual(detector.detect(scene,self.settings).decision,Decision.NO_FIRE)
        scene.on[8:12,8:12]=240
        result=detector.detect(scene,self.settings)
        self.assertEqual(result.decision,Decision.FIRE)
        self.assertEqual(result.regions[0]['area_px'],16)
        self.assertAlmostEqual(result.regions[0]['median_k'],1,places=6)

    def test_dark_invalid_and_clipped_are_not_negative(self):
        scene=self.scene();scene.valid[:]=False
        self.assertEqual(SpectralExcess().detect(scene,self.settings).decision,Decision.UNKNOWN)
        scene=self.scene();scene.saturated_fraction=.5
        self.assertEqual(SpectralExcess().detect(scene,self.settings).decision,Decision.UNKNOWN)
        scene=self.scene();scene.low[:]=0;scene.high[:]=0
        result=SpectralExcess().detect(scene,self.settings)
        self.assertEqual(result.decision,Decision.UNKNOWN)
        self.assertTrue(np.isnan(result.maps['k']).all())

    def test_area_filter_rejects_isolated_hot_pixel(self):
        scene=self.scene();scene.on[4,4]=240
        self.assertEqual(SpectralExcess().detect(scene,self.settings).decision,Decision.NO_FIRE)

    def test_guarded_plugin_rejects_a_shifted_background_edge(self):
        from ember_detector.guarded import GuardedSpectral
        scene=self.scene()
        scene.low[:]=scene.high[:]=100
        scene.low[:,12:]=scene.high[:,12:]=200
        scene.on[:]=100;scene.on[:,11:]=200
        self.assertEqual(SpectralExcess().detect(scene,self.settings).decision,Decision.FIRE)
        guarded=dict(self.settings,alignment_guard_px=2)
        self.assertEqual(GuardedSpectral().detect(scene,guarded).decision,Decision.NO_FIRE)
        scene.on[8:12,6:10]=250
        self.assertEqual(GuardedSpectral().detect(scene,guarded).decision,Decision.FIRE)

    def test_registry_and_configuration(self):
        class Alternate:
            algorithm_id='test_detector'
            @staticmethod
            def validate(settings):
                if settings!={'test_option':True}:raise ValueError('settings')
            def detect(self,scene,settings):return Result(Decision.UNKNOWN,'ALTERNATE_IMPLEMENTATION')
        register('test_detector',Alternate)
        self.assertEqual(create('test_detector').detect(self.scene(),{}).reason,'ALTERNATE_IMPLEMENTATION')
        with self.assertRaises(ValueError):create('unavailable')
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'config.json';cfg=dict(self.config,algorithm='test_detector',detector={'test_option':True})
            p.write_text(json.dumps(cfg));self.assertEqual(load_config(p)['algorithm'],'test_detector')
            cfg['algorithm']='typo';p.write_text(json.dumps(cfg))
            with self.assertRaises(ValueError):load_config(p)
            cfg=dict(self.config);cfg['detector']=dict(self.settings,k_threshold=-1);p.write_text(json.dumps(cfg))
            with self.assertRaises(ValueError):load_config(p)
            cfg=json.loads(json.dumps(self.config));cfg['registration']['max_features']=2000.0;p.write_text(json.dumps(cfg))
            with self.assertRaises(ValueError):load_config(p)
            cfg=json.loads(json.dumps(self.config));cfg['detector']['connectivity']=8.0;p.write_text(json.dumps(cfg))
            with self.assertRaises(ValueError):load_config(p)

    def test_pipeline_uses_hashes_and_does_not_pass_label_to_detector(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);image=np.full((32,32),100,dtype='uint8')
            calibration=root/'cal.npz';np.savez(calibration,**{'gain_'+str(p):np.ones((32,32),dtype='float32') for p in range(3)})
            cfg=json.loads(json.dumps(self.config));cfg['calibration_sha256']=digest(calibration.read_bytes());cfg['registration']['mode']='prealigned'
            channels={}
            for port,wavelength in enumerate([750,770,780]):
                path=root/(str(port)+'.png');cv2.imwrite(str(path),image)
                channels[str(wavelength)]=dict(path=path.name,sha256=digest(path.read_bytes()),width=32,height=32,port=port,wavelength_nm=wavelength,exposure_us=100)
            fixture=dict(fixture_id='test',label='FIRE',channels=channels)
            manifest=root/'manifest.json';manifest.write_text(json.dumps({'fixtures':[fixture]}))
            result,_=run(manifest,'test',cfg,calibration)
            self.assertEqual(result['result'],'NO_FIRE')
            self.assertFalse(result['camera_capture_performed'])
            self.assertNotIn('label',result)
            fixture['label']='NO_FIRE';manifest.write_text(json.dumps({'fixtures':[fixture]}))
            self.assertEqual(run(manifest,'test',cfg,calibration)[0]['result'],'NO_FIRE')
            (root/'0.png').write_bytes(b'corrupt')
            result,_=run(manifest,'test',cfg,calibration)
            self.assertEqual(result['result'],'UNKNOWN');self.assertEqual(result['reason'],'INPUT_HASH')
            self.assertEqual(run(manifest,'absent',cfg,calibration)[0]['result'],'UNKNOWN')


if __name__=='__main__':unittest.main()
