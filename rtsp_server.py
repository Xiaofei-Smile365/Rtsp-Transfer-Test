import cv2
import gi 
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0') 
from gi.repository import Gst, GstRtspServer, GObject
_width='1280'
_height='720'

class SensorFactory(GstRtspServer.RTSPMediaFactory):
  global camera
  def __init__(self, **properties): 
    super(SensorFactory, self).__init__(**properties) 
    #self.cap = cv2.VideoCapture(0)
    #self.cap = cv2.VideoCapture("rtsp://....")
    self.cap = camera
    self.number_frames = 0 
    self.fps = 30
    self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds 
    self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                         'caps=video/x-raw,format=BGR,width='+_width+',height='+_height+',framerate={}/1 ' \
                         '! videoconvert ! video/x-raw,format=I420 ' \
                         '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                         '! rtph264pay config-interval=1 name=pay0 pt=96'.format(self.fps)

  def on_need_data(self, src, lenght):
    if self.cap.isOpened():
      ret, frame = self.cap.read()
      if ret:
        data = frame.tostring() 
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        buf.duration = self.duration
        timestamp = self.number_frames * self.duration
        buf.pts = buf.dts = int(timestamp)
        buf.offset = timestamp
        self.number_frames += 1
        retval = src.emit('push-buffer', buf) 

        print('pushed buffer, frame {}, duration {} ns, durations {} s'.format(self.number_frames, self.duration, self.duration / Gst.SECOND)) 

        if retval != Gst.FlowReturn.OK: 
          print(retval) 

  def do_create_element(self, url): 
    return Gst.parse_launch(self.launch_string) 

  def do_configure(self, rtsp_media): 
    self.number_frames = 0 
    appsrc = rtsp_media.get_element().get_child_by_name('source') 
    appsrc.connect('need-data', self.on_need_data)
  
 


class GstServer(GstRtspServer.RTSPServer): 
  def __init__(self, **properties): 
    super(GstServer, self).__init__(**properties) 
    self.set_address = '192.168.1.101'
    self.set_service = '8554'
    self.factory = SensorFactory() 
    self.factory.set_shared(True) 
    self.get_mount_points().add_factory("/test", self.factory) 
    self.attach(None) 



def open_cam_usb_GSTREAMER(dev, width, height):
    """Open a USB webcam."""
    gst_str = ('v4l2src device=/dev/video{} ! '
               'video/x-raw, width=(int){}, height=(int){} !'#, framerate=(fraction){}/1 ! '
               'videoconvert ! video/x-raw, format=(string)BGR ! appsink').format(dev, width, height)#, str(capture_fps))
    
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

def open_cam_usb_V4L2(dev, width, height):
    """Open a USB webcam."""
    _cap = cv2.VideoCapture()
    _cap.open(dev,apiPreference = cv2.CAP_V4L2)
    # 設定影像的尺寸大小
    _cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    _cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    #_cap.set(cv2.CAP_PROP_FPS, 10)
    return _cap

camera = None
#camera = open_cam_usb_GSTREAMER(0,1280,720)
camera = open_cam_usb_V4L2(0,int(_width),int(_height))
GObject.threads_init() 
Gst.init(None) 

server = GstServer() 

#import socket
#ip = socket.gethostbyname(socket.gethostname())
#print("rtsp://" + ip + ":8554/test")

loop = GObject.MainLoop() 
loop.run()
