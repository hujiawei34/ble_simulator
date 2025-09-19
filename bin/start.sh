cwd=$(cd $(dirname $0); pwd)
project_root=$(dirname $cwd)
deploy_dir=$project_root/deploy
cd $deploy_dir
podman compose restart || podman compose up -d