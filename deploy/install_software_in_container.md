cat > /etc/apt/sources.list << 'EOF'
deb http://mirrors.aliyun.com/ubuntu/ noble main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ noble-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ noble-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ noble-backports main restricted universe multiverse
EOF

apt install nano vim kmod bluez python3 python3-pip  python3-bluez python3-full 

pip install -r requirements.txt --break-system-packages

podman commit ble-simulator ble_simulator_container:v1


podman login --username=hujiawei2727 crpi-qqo05szhq6ruqonk.cn-hangzhou.personal.cr.aliyuncs.com
podman tag localhost/ble_simulator_container:v1 crpi-qqo05szhq6ruqonk.cn-hangzhou.personal.cr.aliyuncs.com/hjw2727/ble_simulator:latest
podman push crpi-qqo05szhq6ruqonk.cn-hangzhou.personal.cr.aliyuncs.com/hjw2727/ble_simulator:latest