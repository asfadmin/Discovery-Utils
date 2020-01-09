from flask import Flask, make_response
from flask import request
from flask import Response
from werkzeug.exceptions import RequestEntityTooLarge
from datetime import datetime
from urllib import parse
import logging
import json
import os
import sys

from WKTValidator import WKTValidator
from DateValidator import DateValidator
from FilesToWKT import FilesToWKT
from MissionList import MissionList
from CMR.Health import get_cmr_health

from submodules.Analytics.Analytics import analytics_pageview


# EB looks for an 'application' callable by default.
application = Flask(__name__)
application.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 # limit to 10 MB, primarily affects file uploads

########## API Endpoints ##########

# Validate and/or repair a WKT to ensure it meets CMR's requirements
@application.route('/services/utils/wkt', methods = ['GET', 'POST'])
def validate_wkt():
    return WKTValidator(request).get_response()

# Validate a date to ensure it meets our requirements
@application.route('/services/utils/date', methods = ['GET', 'POST'])
def validate_date():
    return DateValidator(request).get_response()

# Convert a set of shapefiles or a geojson file to WKT
@application.route('/services/utils/files_to_wkt', methods = ['POST'])
def filesToWKT():
    return FilesToWKT(request).get_response()

# Collect a list of missions from CMR for a given platform
@application.route('/services/utils/mission_list', methods = ['GET', 'POST'])
def missionList():
    return MissionList(request).get_response()

# Health check endpoint
@application.route('/health')
def health_check():
    cmr_health = get_cmr_health()
    api_health = {'ASFSearchAPI': {'ok?': True}, 'CMRSearchAPI': cmr_health}
    response = make_response(json.dumps(api_health, sort_keys=True, indent=2))
    response.mimetype = 'application/json; charset=utf-8'
    return response

# Send the API swagger docs
@application.route('/reference')
def reference():
    return application.send_static_file('./SearchAPIRef.yaml')

########## Helper functionality ##########

@application.errorhandler(RequestEntityTooLarge)
def handle_oversize_request(error):
    resp = Response(json.dumps({'error': {'type': 'VALUE', 'report': 'Selected file is too large.'} }, sort_keys=True, indent=2), status=413, mimetype='application/json')
    return resp

# Pre-flight operations
@application.before_request
def preflight():
    analytics_pageview()

# Cleanup operations
@application.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@application.teardown_request
def postflight(exc):
    pass

# Run a dev server
if __name__ == '__main__':
    if 'MATURITY' not in os.environ:
        os.environ['MATURITY'] = 'dev'
    sys.dont_write_bytecode = True  # prevent clutter
    application.debug = True        # enable debugging mode
    FORMAT = "[%(filename)18s:%(lineno)-4s - %(funcName)18s() ] %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=FORMAT) # enable debugging output
    application.run(threaded=True)  # run threaded to prevent a broken pipe error
