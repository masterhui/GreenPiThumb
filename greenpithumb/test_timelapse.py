import glob
import os


IMAGE_PATH = "/opt/greenpithumb-data/images/"
TIMELAPSE_NUM_DAYS = 24

jpg_count = len(glob.glob1(IMAGE_PATH,"reduced_*.jpg"))
#~ print "jpg_count =", jpg_count

print "Create sequentially numbered symlinks of most recent", TIMELAPSE_NUM_DAYS, "images in folder", IMAGE_PATH
i = 0
seq = 0
for filename in sorted(os.listdir(IMAGE_PATH)):
    if filename.startswith("reduced_"):        
        #~ print "i =", i, filename
        if i >= jpg_count - TIMELAPSE_NUM_DAYS:
            src = IMAGE_PATH + filename
            dst = IMAGE_PATH + str(seq) + ".jpg"
            seq += 1
            #~ print "Create symlink", src, dst
            try:
                os.symlink(src, dst)
            except OSError:
                pass
        i += 1

#~ command = 'gst-launch-1.0 multifilesrc location=%d.jpg index=1 caps="image/jpeg,framerate=4/1" ! jpegdec ! omxh264enc target-bitrate=6400000 control-rate=variable ! avimux ! filesink location=timelapse.avi'
command = 'gst-launch-1.0 multifilesrc location=%d.jpg index=1 caps="image/jpeg,framerate=4/1" ! jpegdec ! videoconvert ! videorate ! theoraenc ! oggmux ! filesink location=timelapse.ogg'

print "Create timlapse animation by calling", command
os.chdir(IMAGE_PATH)
os.system(command)
print "Timelapse creation DONE"

print "Delete symlinks"
os.system("find -type l -delete")
