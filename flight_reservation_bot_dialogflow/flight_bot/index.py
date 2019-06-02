from flask import Flask, request, jsonify, render_template ,make_response ,abort
from pydialogflow_fulfillment import DialogflowResponse, DialogflowRequest, SimpleResponse, Suggestions, SystemIntent, OutputContexts
from flask_assistant import ask,tell
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
CONNECTION_NAME = getenv('INSTANCE_CONNECTION_NAME','flook-new:us-central1-a:flook-db')
DB_USER = getenv('MYSQL_USER', 'root')
DB_PASSWORD = getenv('MYSQL_PASSWORD', 'pannu319')
DB_NAME = getenv('MYSQL_DATABASE', 'flights')

mysql_config = {
  'user': DB_USER,
  'password': DB_PASSWORD,
  'db': DB_NAME,
  'charset': 'utf8mb4',
  'cursorclass': pymysql.cursors.DictCursor,#default cursor class return tuple
  'autocommit': True
}
# GOOGLE_PROJECT_ID = "flook-new"
mysql_conn = pymysql.connect(host='104.198.195.131',user=DB_USER,password=DB_PASSWORD,db=DB_NAME,cursorclass=pymysql.cursors.DictCursor)

# output_context = "book_flight - select.number"
project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
# context = "projects/" + project_id + "/agent/sessions/" + "unique" + "/contexts/" + output_context.lower()
parameters = dialogflow.types.struct_pb2.Struct()
# parameters["foo"] = "bar"

# context_1 = dialogflow.types.context_pb2.Context(
#     name=output_context,
#     lifespan_count=2,
#     parameters=parameters
# )

    
@app.route('/')
def index():
#     return "index  page of Flook"
  return render_template('index.html')

def detect_intent_texts(project_id, session_id, text, language_code):
  session_client = dialogflow.SessionsClient()
  session = session_client.session_path(project_id, session_id)

  if text:
      text_input = dialogflow.types.TextInput(text=text, language_code=language_code)
      query_input = dialogflow.types.QueryInput(text=text_input)
      # query_parameter = dialogflow.types.QueryParameters(contexts=[context_1])
      query_parameter = dialogflow.types.QueryParameters(contexts=[])
      response = session_client.detect_intent(session=session, query_input=query_input)
      return response.query_result.intent.display_name,response.query_result.fulfillment_text,response.query_result.parameters,response,query_parameter


# create a route for webhook
@app.route('/webhook', methods=['GET', 'POST'])
def default_welcome():
  cursor = mysql_conn.cursor()
  if request.method == 'POST':
    dialogflow_request = DialogflowRequest(request.data)
    # params = dialogflow_request.get_paramters()
    # fulfillment_text = dialogflow_request.g
    req = json.loads((request.data).decode('utf-8'))
    # print(req)
    if dialogflow_request.get_intent_displayName() == "Default Welcome Intent":
      dialogflow_response = DialogflowResponse("Welcome to Flook.Your Smart flight reservation agent")
      print(dialogflow_response)
      dialogflow_response.add(SimpleResponse("Welcome to my test dialogflow webhook","Welcome to my test dialogflow webhook"))
      print(dialogflow_response.get_final_response())
      response_text = {"messages":dialogflow_response.get_final_response()}
      response = jsonify(response_text)
    # if dialogflow_request.get_intent_displayName() == "book_flight" or dialogflow_request.get_intent_displayName() == "book_flight - select.number":
    if dialogflow_request.get_intent_displayName() == "book_flight":
      params = dialogflow_request.get_paramters()
      print(params)
      print(dialogflow_request.get_intent_displayName())
      # if 'source' in params:
      #   if params['source'] == '':
      #     src = '' 
      #     fulfillment_text = req['queryResult']['fulfillmentText']
      #     response_text = { "message":  fulfillment_text }
      #   if type(params['source']) == dict:
      #     if params['source']['city'] != '':
      #         src = params['source']['city']
      #     if params['source']['city'] == '' and params['source']['admin-area'] == '' and params['source']['country'] != '':
      #         src = params['source']['country']
      #     if params['source']['city'] == '' and params['source']['admin-area'] != '' and params['source']['country'] == '':
      #         src = params['source']['admin-area']
      # if 'destination' in params:
      #   if params['destination'] == '': 
      #     dstn = ''
      #     fulfillment_text = req['queryResult']['fulfillmentText']
      #     response_text = { "message":  fulfillment_text }
      #   if type(params['destination']) == dict:
      #     if params['destination']['city'] != '':
      #         dstn = params['destination']['city']
      #     if params['destination']['city'] == '' and params['destination']['admin-area'] == '' and params['destination']['country'] != '':
      #         dstn = params['destination']['country']
      #     if params['destination']['city'] == '' and params['destination']['admin-area'] != '' and params['destination']['country'] == '':
      #         dstn = params['destination']['admin-area']
      #     if dstn == 'Bengaluru': dstn=dstn.replace('Bengaluru','Bangalore')
      # if 'dateofjourney' in params:      
      #   dt = params['dateofjourney']
      #   if dt == '':
      #     date_of_journey = ''
      #     fulfillment_text = req['queryResult']['fulfillmentText']
      #     response_text = { "message":  fulfillment_text }
      #   if dt != '':
      #     dot = re.search(r'\d{4}-\d{2}-\d{2}',dt)
      #     date_of_journey = dot.group()+' '+'00:00:00'
      
      # print("destination : "+dstn)
      
      if 'source' in params and 'destination' in params and 'dateofjourney' in params:
        if params['source'] == '':
          src = '' 
          fulfillment_text = req['queryResult']['fulfillmentText']
          response_text = { "message":  fulfillment_text }
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
          response_text = { "message":  fulfillment_text }
        if type(params['destination']) == dict:
          if params['destination']['city'] != '':
              dstn = params['destination']['city']
          if params['destination']['city'] == '' and params['destination']['admin-area'] == '' and params['destination']['country'] != '':
              dstn = params['destination']['country']
          if params['destination']['city'] == '' and params['destination']['admin-area'] != '' and params['destination']['country'] == '':
              dstn = params['destination']['admin-area']
          if dstn == 'Bengaluru': dstn=dstn.replace('Bengaluru','Bangalore')
        dt = params['dateofjourney']
        if dt == '':
          date_of_journey = ''
          fulfillment_text = req['queryResult']['fulfillmentText']
          response_text = { "message":  fulfillment_text }
        if dt != '':
          dot = re.search(r'\d{4}-\d{2}-\d{2}',dt)
          date_of_journey = dot.group()+' '+'00:00:00'
        if src != '' and dstn != '' and date_of_journey != '':
          print(src,dstn,date_of_journey)
          query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel=%s'
          # query = 'SELECT * from flights where source=%s AND date_of_travel=%s'
          cursor.execute(query,(src,dstn,date_of_journey))
          results = cursor.fetchall()
          app.logger.info(len(results))
          app.logger.info (results)
          if len(results) == 0:
            fulfillment_text = "No flights available"
            response_text = { "message":  fulfillment_text }
            # return jsonify(response_text)
          if len(results) == 1:
            fulfillment_text = "Your ticket has been booked"
            response_text = { "message":  fulfillment_text }
            # return jsonify(response_text)
          if len(results) > 1:
            fulfillment_text = str(results)
            response_text = { "message":  fulfillment_text}
            dialogflow_response = DialogflowResponse("Please select your flight")
            print(dialogflow_response)
            dialogflow_response.add(SimpleResponse("Please select your flight","Please select your flight"))
            dialogflow_response = DialogflowResponse()
            dialogflow_response.expect_user_response = True
            print (dialogflow_request.get_intent_displayName())
            print(dialogflow_request.get_single_ouputcontext('book_flight-followup'))
    if dialogflow_request.get_intent_displayName() == "book_flight - select.number":
      # params = dialogflow_request.get_paramters()
      params = dialogflow_request.get_single_ouputcontext('book_flight-followup')['parameters']
      print(params)
      print(dialogflow_request.get_single_ouputcontext('book_flight-followup'))
      src = params['source.original']
      dstn = params['destination.original']
      dt = params['dateofjourney']
      dot = re.search(r'\d{4}-\d{2}-\d{2}',dt)
      date_of_journey = dot.group()+' '+'00:00:00'
      selection = int(params['number'][0])
      query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel=%s'
      cursor.execute(query,(src,dstn,date_of_journey))
      results = cursor.fetchall()
      if selection <= len(results):
        fulfillment_text = "Your ticket has been booked"
        response_text = { "message":  fulfillment_text }
      if selection > len(results):
        fulfillment_text = "Invalid selection,booking cancelled"
        response_text = { "message":  fulfillment_text }
            
    return jsonify(response_text)

    # else:
    #     dialogflow_response = DialogflowResponse("Now that you are here. What can I help you with ?")
    #     dialogflow_response.add(Suggestions(["About","Sync","More info"]))
    #     response = jsonify(dialogflow_response.get_final_response())
    
  else:
    abort(404)
@app.route('/send_message', methods=['POST'])
def welcome():
  global mysql_conn
  message = request.form['message']
  app.logger.info("********************incoming message**********************")
  app.logger.info(message)
  intent = detect_intent_texts(project_id, "unique", message,'en')[0]
  fulfillment_text = detect_intent_texts(project_id, "unique", message, 'en')[1]
  app.logger.info("********************fulfillment_text**********************")
  app.logger.info(fulfillment_text)
  parameters = detect_intent_texts(project_id, "unique", message, 'en')[2]
  params = MessageToDict(parameters)
  app.logger.info("********************parameters**********************")
  app.logger.info(parameters)
  # print(detect_intent_texts(project_id, "unique", message, 'en')[3])
  app.logger.info('*****************contexts**************************')
  app.logger.info(detect_intent_texts(project_id, "unique", message, 'en')[4])
  response_text = { "message":  fulfillment_text }
  # if intent == 'book_flight':
  
  if intent == 'book_flight':   
    if type(params['source']) == str: src = params['source'] 
    if type(params['source']) == dict:
      if params['source']['city'] != '':
          src = params['source']['city']
      if params['source']['city'] == '' and params['source']['admin-area'] == '' and params['source']['country'] != '':
          src = params['source']['country']
      if params['source']['city'] == '' and params['source']['admin-area'] != '' and params['source']['country'] == '':
          src = params['source']['admin-area']
    if type(params['destination']) == dict:
      if params['destination']['city'] != '':
          dstn = params['destination']['city']
      if params['destination']['city'] == '' and params['destination']['admin-area'] == '' and params['destination']['country'] != '':
          dstn = params['destination']['country']
      if params['destination']['city'] == '' and params['destination']['admin-area'] != '' and params['destination']['country'] == '':
          dstn = params['destination']['admin-area']
    if type(params['destination']) == str: dstn = params['destination']
    # dstn = params['destination']['city']
    if dstn == 'Bengaluru': dstn=dstn.replace('Bengaluru','Bangalore')
    dt = params['dateofjourney']
    dot = re.search(r'\d{4}-\d{2}-\d{2}',dt)
    date_of_journey = dot.group()+' '+'00:00:00'
    print(src,dstn,date_of_journey)
    # print("destination : "+dstn)
    cursor = mysql_conn.cursor()
    if src != '' and dstn != '' and date_of_journey != '':
      query = 'SELECT * from flights where source=%s AND destination=%s AND date_of_travel=%s'
      # query = 'SELECT * from flights where source=%s AND date_of_travel=%s'
      cursor.execute(query,(src,dstn,date_of_journey))
      results = cursor.fetchall()
      app.logger.info(len(results))
      app.logger.info (results)
      if len(results) == 0:
        fulfillment_text = "No flights available"
        response_text = { "message":  fulfillment_text }
        # return jsonify(response_text)
      if len(results) == 1:
        fulfillment_text = "Your ticket has been booked"
        response_text = { "message":  fulfillment_text }
        # return jsonify(response_text)
      if len(results) > 1:
        fulfillment_text = str(results)
        response_text = { "message":  fulfillment_text}
        return ask('Please make your selecion from the above list')
        # response_text1 = { "message":  'Please make your selecion from the list'}
        # return jsonify(response_text)
        # return jsonify(response_text)
  
        


# run Flask app
if __name__ == "__main__":
    app.run(debug=True)