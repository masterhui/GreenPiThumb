IMAGE_PATH=$1
THRES=24

echo "Switch to directory $IMAGE_PATH" 
cd $IMAGE_PATH

echo "Generate symlinks of last $THRES images"
count=0
for x in reduced_*.jpg
do
	let "count=count+1"
done

seq=0
i=0
for x in reduced_*.jpg
do
	if ((i >= count-THRES )); then
		ln -s "$PWD/$x" "$seq.jpg"
		let "seq=seq+1"
	fi
	let "i=i+1"
done

echo "Generate timelapse animation"
gst-launch-1.0 multifilesrc location=%d.jpg index=1 caps="image/jpeg,framerate=4/1" ! jpegdec ! omxh264enc target-bitrate=6400000 control-rate=variable ! avimux ! filesink location=timelapse.avi

echo "Delete symlinks"
find -type l -delete
