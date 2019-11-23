set -e

cd ${POKER_BOT_PATH}

pid=$(ps -ef | grep run.py | grep -v grep | awk '{print $2}')

if [ -n "$pid" ]; then 
	kill -9 $pid; 
fi

git checkout dev
git pull

nohup python3 run.py > log 2>&1 &
