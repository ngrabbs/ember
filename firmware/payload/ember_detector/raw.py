"""Bounded decoder for single-plane Pi payload DNGs."""
from io import BytesIO
import numpy as np


def decode_dng(data, max_pixels):
    try:
        import rawpy
        import tifffile
    except ImportError as error:
        raise ValueError('RAW_DEPENDENCIES_REQUIRED') from error
    try:
        with tifffile.TiffFile(BytesIO(data)) as tiff:
            page = tiff.pages[0]
            tags = page.tags
            if (len(tiff.pages) != 1 or 'DNGVersion' not in tags or
                    page.samplesperpixel != 1 or int(page.photometric) != 34892 or
                    not 1 <= page.imagewidth * page.imagelength <= max_pixels or
                    page.bitspersample != 10):
                raise ValueError('RAW_DNG_LAYOUT')
            black = float(tags['BlackLevel'].value)
            white = float(tags['WhiteLevel'].value)
            numerator, denominator = tags['ExposureTime'].value
            exposure = 1e6 * numerator / denominator
            if not 0 <= black < white <= 1023 or not 1 <= exposure <= 1000000:
                raise ValueError('RAW_DNG_METADATA')
            expected = (page.imagelength, page.imagewidth)
        with rawpy.imread(BytesIO(data)) as dng:
            image = dng.raw_image_visible.copy()
        if image.shape != expected or image.max() > 1023:
            raise ValueError('RAW_DNG_DIMENSIONS')
    except (rawpy.LibRawError, tifffile.TiffFileError, KeyError, TypeError, IndexError,
            OverflowError, ZeroDivisionError) as error:
        raise ValueError('RAW_DNG_DECODE') from error
    return image.astype(np.float32) - black, image >= white, exposure
