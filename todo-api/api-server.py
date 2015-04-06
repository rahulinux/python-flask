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
tasks = [{'id': 1}]

## Return Error 
@app.errorhandler(404)

def not_found(error):
    return make_response(jsonify({'error': 'Not found'}),404)

@app.errorhandler(503)

def server_busy(error):
    return make_response(jsonify({'error': 'Server Busy'}), 503)
    


##  Clean task if process end 
def clean_task():
      global tasks
      if len(tasks) == 1: scheduler.remove_all_jobs()
      for i, task in enumerate(tasks[1:],start=1):
         pid = task['pid']
         pid_not_found  = subprocess.Popen("ps -ef | awk '$2 ~ /%s/ && !/awk/'" % pid, shell=True, stdout=subprocess.PIPE).communicate()[0]
         if not pid_not_found:
             tasks.remove(tasks[i])
             print "task has been removed with pid : %s" % pid


## Get tasks

@app.route('/todo/api/v1.0/tasks/<int:task_id>',methods=['GET'])

def get_tasks(task_id):
    """ Return  running task, 
        if there is no running task then 
        return not found"""
    task = [ task for task in tasks if task['id'] == task_id ]
    if len(task) == 0:
       abort(404)
    return jsonify({'task': task[0]}) 



## Run command

def command(cmd):
     # Run cmd and Get pid details
     cmd = cmd + " & echo $! > /tmp/pid"
     os.system(cmd)
     pid = open("/tmp/pid").read().strip()
     status = subprocess.Popen("ps -ef | awk '/%s/ && !/awk/'" % pid, shell=True, 
                   stdout=subprocess.PIPE).communicate()[0].strip() 
    
     return pid,status



## Create Task 

@app.route('/todo/api/v1.0/tasks',methods=['POST'])

def create_task():
    if not request.json or not 'env' in request.json:
       abort(400)
    env = request.json['env']
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


    if sum( 1 for x in tasks[1:] if x['env'] == env and ( x['parser'] == 0 or x['fetcher'] == 0)) == 2:
       print "no env parser or fetcher is free"
       abort(503)
    elif sum( 1 for x in tasks[1:] if x['env'] == env) >= 1:
       print "no env is free"
       abort(503)
        
    

    pid, status = command("sleep 30") 
    task = {
        'id': tasks[-1]['id'] + 1,
        'pid': pid,
        'env': request.json['env'],
        'parser': parser,
        'fetcher': fetcher,
        'status': status 
    }
    tasks.append(task)
    scheduler.add_job(clean_task,'interval',seconds=2)
    return jsonify({'task':task}), 201



if __name__ == '__main__':
    app.run(debug=True)
