#!flask/bin/python

from flask import Flask
from flask import jsonify
from flask import abort
from flask import make_response
from flask import request 
from apscheduler.schedulers.background import BackgroundScheduler
import os
import subprocess
import time


app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()
tasks = []



## Return Error 

@app.errorhandler(404)

def not_found(error):
    return make_response(jsonify({'error': 'Not found'}),404)

@app.errorhandler(503)

def server_busy(error):
    return make_response(jsonify({'error': 'Server Busy'}), 503)
    


@scheduler.scheduled_job('interval', seconds=2)
##  Clean task if process end 
def clean_task():
      global tasks
      p = subprocess.Popen("ps -ef | awk '$0 ~ /%s/ && !/awk/'" % "sleep", shell=True, stdout=subprocess.PIPE).communicate()[0]
      if not p and tasks:
          print "task has been completed"
          print "cleaning the task"
          tasks = []
          scheduler.remove_all_jobs()


## Get tasks

@app.route('/todo/api/v1.0/tasks',methods=['GET'])

def get_tasks():
    """ Return  running task, 
        if there is no running task then 
        return not found""" 
    if len(tasks) == 0:
       abort(404)
    return jsonify({'task': tasks[0]}) 



## Run command

def command(cmd):
     # Run cmd in background
     process = cmd.split()[0]
     cmd = "nohup " + cmd + " &"
     os.system(cmd)
   
     # Get pid details  
     status = subprocess.Popen("ps -ef | awk '/%s/ && !/awk/'" % process, shell=True, 
                   stdout=subprocess.PIPE).communicate()[0].strip() 
     pid = status.split()[1]
    
     return pid,status



## Create Task 

@app.route('/todo/api/v1.0/tasks',methods=['POST'])

def create_task():
    if not request.json or not 'env' in request.json:
       abort(400)
    if not 'parser' and not 'fetcher' in request.json:
       abort(400)

    if not 'parser' in request.json: 
        parser = 0 
    else: 
        parser = request.json['parser']

    if not 'fetcher' in request.json:
        fetcher = 0
    else:
        fetcher = request.json['fetcher']

    # if task already running then return 503 server busy
    if len(tasks) > 0:
          abort(503)

    pid, status = command("sleep 10") 
    task = {
        'id': 1,
        'pid': pid,
        'env': request.json['env'],
        'parser': parser,
        'fetcher': fetcher,
        'status': status 
    }
    tasks.append(task)
    scheduler.add_job(clean_task,'interval',seconds=3)
    return jsonify({'task':task}), 201



if __name__ == '__main__':
    app.run(debug=True)
