set -e

cd "${POKER_BOT_PATH}"

pid=$(pgrep -f run.py)

if [ -n "$pid" ]; then 
	kill -9 "$pid";
fi

git checkout dev || true
git pull

nohup python3 run.py > log 2>&1 &
