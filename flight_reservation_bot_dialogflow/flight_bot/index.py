from flask import Flask, request, jsonify, render_template ,make_response ,abort
from pydialogflow_fulfillment import DialogflowResponse, DialogflowRequest, SimpleResponse, Suggestions, SystemIntent, OutputContexts
from google.protobuf.json_format import MessageToDict
import os,logging
from os import getenv
import pymysql
from pymysql.err import OperationalError
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/home/pavan/flight_bot/flook-new-819290d434f4.json"
os.environ["DIALOGFLOW_PROJECT_ID"]="flook-new"
import dialogflow_v2 as dialogflow
import requests
import json
import pusher
import struct
from dateutil.parser import parse
import re
import ast
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
# TODO(developer): specify SQL connection details
# CONNECTION_NAME = getenv('INSTANCE_CONNECTION_NAME','flook-new:us-central1-a:flook-db')
# DB_USER = getenv('MYSQL_USER', 'root')
# DB_PASSWORD = getenv('MYSQL_PASSWORD', 'pannu319')
# DB_NAME = getenv('MYSQL_DATABASE', 'flights')

# GOOGLE_PROJECT_ID = "flook-new"
#connect to mysql server using host ip 
# mysql_conn = pymysql.connect(host='104.198.195.131',user=DB_USER,password=DB_PASSWORD,db=DB_NAME,cursorclass=pymysql.cursors.DictCursor) #connecting to mysql hosted on cloud
mysql_conn = pymysql.connect(host='127.0.0.1',user='root',password='admin',db='flights',cursorclass=pymysql.cursors.DictCursor) #connect to mysql hosted on localhost

project_id = os.getenv('DIALOGFLOW_PROJECT_ID')

# create a route for webhook
@app.route('/webhook', methods=['GET', 'POST'])
def default_welcome():
  cursor = mysql_conn.cursor()
  if request.method == 'POST':
    dialogflow_response = DialogflowResponse("Welcome to Flook.Your Smart flight reservation agent")
    dialogflow_response.add(SimpleResponse("Welcome to Flook.Your Smart flight reservation agent","Welcome to Flook.Your Smart flight reservation agent"))
    response_text = dialogflow_response.get_final_response()
    dialogflow_request = DialogflowRequest(request.data)
    req = json.loads((request.data).decode('utf-8'))
    if dialogflow_request.get_intent_displayName() == "Default Welcome Intent":
      dialogflow_response = DialogflowResponse("Welcome to Flook.Your Smart flight reservation agent")
      dialogflow_response.add(SimpleResponse("Welcome to my test dialogflow webhook","Welcome to my test dialogflow webhook"))
      response_text = dialogflow_response.get_final_response()
    
    if dialogflow_request.get_intent_displayName() == "book_flight":
      params = dialogflow_request.get_paramters()
      if 'source' in params and 'destination' in params and 'dateofjourney' in params:
        if params['source'] == '':
          src = '' 
          fulfillment_text = req['queryResult']['fulfillmentText']
          dialogflow_response = DialogflowResponse(fulfillment_text)
          dialogflow_response.add(SimpleResponse(fulfillment_text,fulfillment_text))
          response_text = dialogflow_response.get_final_response()
        if type(params['source']) == dict:
          if params['source']['city'] != '':
              src = params['source']['city']
          if params['source']['city'] == '' and params['source']['admin-area'] == '' and params['source']['country'] != '':
              src = params['source']['country']
          if params['source']['city'] == '' and params['source']['admin-area'] != '' and params['source']['country'] == '':
              src = params['source']['admin-area']
        if params['destination'] == '': 
          dstn = ''
          fulfillment_text = req['queryResult']['fulfillmentText']
          dialogflow_response = DialogflowResponse(fulfillment_text)
          dialogflow_response.add(SimpleResponse(fulfillment_text,fulfillment_text))
          response_text = dialogflow_response.get_final_response()
        if type(params['destination']) == dict:
          if params['destination']['city'] != '':
              dstn = params['destination']['city']
          if params['destination']['city'] == '' and params['destination']['admin-area'] == '' and params['destination']['country'] != '':
              dstn = params['destination']['country']
          if params['destination']['city'] == '' and params['destination']['admin-area'] != '' and params['destination']['country'] == '':
              dstn = params['destination']['admin-area']
          if dstn == 'Bengaluru': dstn=dstn.replace('Bengaluru','Bangalore')
        dt = params['dateofjourney']
        dt_modified = []
        if len(dt) == 0:
          date_of_journey = ''
          fulfillment_text = req['queryResult']['fulfillmentText']
          dialogflow_response = DialogflowResponse(fulfillment_text)
          dialogflow_response.add(SimpleResponse(fulfillment_text,fulfillment_text))
          response_text = dialogflow_response.get_final_response()
        if len(dt) == 1:
          dot = re.search(r'\d{4}-\d{2}-\d{2}',dt[0])
          date_of_journey = dot.group()+' '+'00:00:00'
        if len(dt) == 2:
          for i in dt:
            dot = re.search(r'\d{4}-\d{2}-\d{2}',i)
            date_of_journey = dot.group()+' '+'00:00:00'
            dt_modified.append(date_of_journey)
            
        if src != '' and dstn != '' and len(dt) != 0:
          print(src,dstn,date_of_journey)
          if len(dt) == 1:
            if params['qualifier'] == '':
              query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel=%s'
              cursor.execute(query,(src,dstn,date_of_journey))
              results = cursor.fetchall()
            if params['qualifier'] != '':
              qualifier = params['qualifier']
              if qualifier == 'direct':
                query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel=%s AND connection=%s'
                cursor.execute(query,(src,dstn,date_of_journey,'false'))
                results = cursor.fetchall()
                
              if qualifier == 'cheapest':
                query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel=%s AND connection=%s'
                cursor.execute(query,(src,dstn,date_of_journey,'true'))
                results = cursor.fetchall()  
          if len(dt) == 2:
            query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel between %s and %s'
            cursor.execute(query,(src,dstn,dt_modified[0],dt_modified[1]))
            results = cursor.fetchall()
          app.logger.info(len(results))
          app.logger.info (results)
          if len(results) == 0:
            dialogflow_response = DialogflowResponse("No flights available")
            dialogflow_response.add(SimpleResponse("No flights available","No flights available"))
            response_text = dialogflow_response.get_final_response()
          if len(results) == 1:
            dialogflow_response = DialogflowResponse("Your ticket has been booked")
            dialogflow_response.add(SimpleResponse("Your ticket has been booked","Your ticket has been booked"))
            response_text = dialogflow_response.get_final_response()
          if len(results) > 1:
            fulfillment_text = str(results)
            dialogflow_response = DialogflowResponse(fulfillment_text)
            dialogflow_response.add(SimpleResponse(fulfillment_text,fulfillment_text))
            response_text = dialogflow_response.get_final_response()
            dialogflow_response = DialogflowResponse("Please select your flight")
            dialogflow_response.add(SimpleResponse("Please select your flight","Please select your flight"))
            response_text = dialogflow_response.get_final_response()
            dialogflow_response = DialogflowResponse()
            dialogflow_response.expect_user_response = True
    if dialogflow_request.get_intent_displayName() == "book_flight - select.number":
      params = dialogflow_request.get_single_ouputcontext('book_flight-followup')['parameters']
      src = params['source.original']
      dstn = params['destination.original']
      dt = params['dateofjourney']
      dt_modified = []
      if len(dt) == 1:
        dot = re.search(r'\d{4}-\d{2}-\d{2}',dt[0])
        date_of_journey = dot.group()+' '+'00:00:00'
        if params['qualifier'] == '':
          query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel=%s'
          cursor.execute(query,(src,dstn,date_of_journey))
          results = cursor.fetchall()
          selection = int(params['number'][0])
          if selection <= len(results):
            dialogflow_response = DialogflowResponse("Your ticket has been booked")
            dialogflow_response.add(SimpleResponse("Your ticket has been booked","Your ticket has been booked"))
            response_text = dialogflow_response.get_final_response()
          if selection > len(results):
            dialogflow_response = DialogflowResponse("Invalid selection,booking cancelled")
            dialogflow_response.add(SimpleResponse("Invalid selection,booking cancelled","Invalid selection,booking cancelled"))
            response_text = dialogflow_response.get_final_response()
        if params['qualifier'] != '':
          qualifier = params['qualifier']
          if qualifier == 'direct':
            query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel=%s AND connection=%s'
            cursor.execute(query,(src,dstn,date_of_journey,'false'))
            results = cursor.fetchall()
            selection = int(params['number'][0])
            if selection <= len(results):
              dialogflow_response = DialogflowResponse("Your ticket has been booked")
              dialogflow_response.add(SimpleResponse("Your ticket has been booked","Your ticket has been booked"))
              response_text = dialogflow_response.get_final_response()
            if selection > len(results):
              dialogflow_response = DialogflowResponse("Invalid selection,booking cancelled")
              dialogflow_response.add(SimpleResponse("Invalid selection,booking cancelled","Invalid selection,booking cancelled"))
              response_text = dialogflow_response.get_final_response()
          if qualifier == 'cheapest':
            query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel=%s AND connection=%s'
            cursor.execute(query,(src,dstn,date_of_journey,'true'))
            results = cursor.fetchall()
            selection = int(params['number'][0])
            if selection <= len(results):
              dialogflow_response = DialogflowResponse("Your ticket has been booked")
              dialogflow_response.add(SimpleResponse("Your ticket has been booked","Your ticket has been booked"))
              response_text = dialogflow_response.get_final_response()
            if selection > len(results):
              dialogflow_response = DialogflowResponse("Invalid selection,booking cancelled")
              dialogflow_response.add(SimpleResponse("Invalid selection,booking cancelled","Invalid selection,booking cancelled"))
              response_text = dialogflow_response.get_final_response()
      if len(dt) == 2:
        for i in dt:
          dot = re.search(r'\d{4}-\d{2}-\d{2}',i)
          date_of_journey = dot.group()+' '+'00:00:00'
          dt_modified.append(date_of_journey)
          query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel between %s and %s'
          cursor.execute(query,(src,dstn,dt_modified[0],dt_modified[1]))
          results = cursor.fetchall()
          selection = int(params['number'][0])
          if selection <= len(results):
            dialogflow_response = DialogflowResponse("Your ticket has been booked")
            dialogflow_response.add(SimpleResponse("Your ticket has been booked","Your ticket has been booked"))
            response_text = dialogflow_response.get_final_response()
          if selection > len(results):
            dialogflow_response = DialogflowResponse("Invalid selection,booking cancelled")
            dialogflow_response.add(SimpleResponse("Invalid selection,booking cancelled","Invalid selection,booking cancelled"))
            response_text = dialogflow_response.get_final_response()
    
    return response_text
  else:
    abort(404)

# run Flask app
if __name__ == "__main__":
    app.run(debug=True)