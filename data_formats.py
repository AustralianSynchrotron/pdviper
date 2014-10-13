__author__ = 'jongl'
# this file contains some rudimentary attempts at reading alternative data formats from other
# detectors. The first attempt is the Bruker/Siemens V3 RAW format with others to come

# much of this code would be better served by using xylib which it is derived from.
# However I didn't want to include too many other dependencies since it is written in c++
# but has python wrappers.

# currently does no error checking and will probably fail ungracefully

import struct
import numpy

def read_header(f):
    head_string = f.read(4)
    if head_string == 'RAW1' and f.read(3) == '.01':
        return 'ver3'
    elif head_string =='RAW':
        return 'ver1'
    elif head_string =='RAW2':
        return 'ver2'
    else:
        return


meta_tags_v3 = [
        # tag, num_bytes, seek offset,stuct_unpackformat
        ('file status', 4, 1, 'I'),
        ('range_cnt', 4,0,'I'),
        ('MEASURE_DATE', 10, 0,'s'),
        ('MEASURE_TIME',10,0,'s'),
        ('USER',72,0,'s'),
        ('SITE', 218,0,'s'),
        ('SAMPLE_ID', 60, 0,'s'),
        ('COMMENT', 160,0,'s'),
        ('ANODE_MATERIAL', 4, 62 ,'s'),
        ('ALPHA_AVERAGE', 8,4,'d'),
        ('ALPHA1', 8,0,'d'),
        ('ALPHA2', 8,0,'d'),
        ('BETA',8,0,'d'),
        ('ALPHA_RATIO',8,0,'d'),
        ('measurement time', 4, 8, 'I')
    ]

block_meta_tags_v3=[
        ('header_len',4,0,'I'),
        ('STEPS',4,0,'I'),
        ('START_THETA',8,0,'d'),
        ('START_2THETA',8,0,'d'),
        ('HIGH_VOLTAGE',4,76,'f'),
        ('AMPLIFIER_GAIN',4,0,'f'),
        ('DISCRIMINATOR_1_LOWER_LEVEL',4,0,'f'),
        ('STEP_SIZE',8,64,'d'),
        ('TIME_PER_STEP',4,8,'f'),
        ('ROTATION_SPEED [rpm]',4,12,'f'),
        ('GENERATOR_VOLTAGE',4,12,'I'),
        ('GENERATOR_CURRENT',4,0,'I'),
        ('USED_LAMBDA',8,8,'d'),
        ('supplementary_headers_size',4,8,'I')]

def read_meta(tag_set, f):
    meta={}
    for name,num_bytes,seek_offset, unpack_format in tag_set:
        if seek_offset!=0:
            f.seek(seek_offset,1)# go seek_offset number of bytes forward from current position
        data = f.read(num_bytes)
        if unpack_format=='s':
            data = struct.unpack(str(num_bytes)+unpack_format,data)
            meta[name]=data[0].strip('\x00')
        else:
            data = struct.unpack(unpack_format,data)
            meta[name]=data[0]
    return meta

def read_block_data(start_theta,steps, step_size,f):
    pairs=[]
    end_theta=start_theta+steps*step_size
    theta=start_theta
    theta_range=numpy.arange(start_theta,end_theta,step_size)
    data_range=numpy.empty_like(theta_range)
    for i, theta in numpy.ndenumerate(theta_range):
        tmp_data=f.read(4)
        data_range[i] = struct.unpack('f',tmp_data)[0]
    stack= numpy.vstack((theta_range,data_range))
    stack = numpy.swapaxes(stack,0,1)
    return numpy.hstack((stack,numpy.zeros((theta_range.shape[0],1))))

def read_data_ver1(f):
    pass

def read_data_ver2(f):
    pass


def read_data_ver3(f):
    meta=read_meta(meta_tags_v3,f)
    range_cnt=meta['range_cnt']
    f.seek(712)
    for r in range(range_cnt):
        block_meta=read_meta(block_meta_tags_v3,f)
        meta["block{}".format(r)]=block_meta
        f.seek(712+304*(1+r))
        start2T=block_meta['START_2THETA']
        steps=block_meta['STEPS']
        stepsize=block_meta['STEP_SIZE']
        block_data=read_block_data(start2T,steps,stepsize,f)
    return block_data,meta


def read_raw(filename):
    f=open(filename, 'rb')
    file_format=read_header(f)
    xy_data,meta_data=read_data_ver3(f)
    return xy_data,meta_data