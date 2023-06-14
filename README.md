# GROUP Streamer
It's a JPEG Streamer with V4L2 controls primarily to be used with Logitech® Group PTZ Video Confrence Camera

# Install
Install the dependencies via apt:
```shell
sudo apt install git libsdl2-2.0-0 libturbojpeg ustreamer python3 pip
```
```shell
sudo pip install regex-spm
```

Clone the repo
```shell
git clone --recurse-submodules https://github.com/wijayamin/groupstreamer.git
cd groupstreamer
```

Make them executable
```shell
chmod +x main.py
```

Run the groupstreamer
```shell
./main.py
```

# Auto-run When the device plugged in
Create an udev rule that triggers when a `/dev/video1` device is availabel:
1. Create a new rule file `/etc/udev/rules.d/99-group-video1.rules`:
    ```shell
    KERNEL=="video1", SUBSYSTEM=="video4linux", RUN+="/path/to/groupstreamer/main.py"

    ```
2. Reload the udev rules:
    ```css
    sudo udevadm control --reload-rules
    ```