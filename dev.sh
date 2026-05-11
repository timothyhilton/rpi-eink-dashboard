rsync -av --delete --exclude .git --exclude .venv --exclude venv \
  ./ tim@192.168.1.165:~/project/rpi-eink-dashboard/

ssh tim@192.168.1.165 "cd ~/project/rpi-eink-dashboard && . venv/bin/activate && python main.py"
